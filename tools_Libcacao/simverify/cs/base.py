#!/usr/bin/env python3
"""Unicorn 差分模擬 harness：載入 ELF .so，逐函數以相同種子輸入執行，記錄結果軌跡。

用法（程式庫）：
    from emu import SoImage, run_function, list_funcs
    img = SoImage(path)
    trace = run_function(img, "_ZN...", seed)
軌跡 = dict(ret, fault, calls=[(import_name, args_norm)], mem_hash)
"""
import hashlib
import random
import struct
import sys

from elftools.elf.elffile import ELFFile
from unicorn import (UC_ARCH_ARM, UC_ARCH_ARM64, UC_HOOK_CODE, UC_HOOK_MEM_UNMAPPED,
                     UC_MODE_ARM, UC_MODE_THUMB, UC_PROT_ALL, Uc, UcError)
from unicorn import arm_const as A
from unicorn import arm64_const as A64

BASE = 0x10000000
STUB_BASE = 0x70000000       # import stub 區（每個 16 bytes）
RET_MAGIC = 0x7f000000       # 函數返回位址
ARENA = 0x20000000           # 隨機參數物件區（所有指標型參數指向此）
ARENA_SZ = 0x40000
STACK = 0x30000000
STACK_SZ = 0x100000
HEAP = 0x40000000
HEAP_SZ = 0x400000
MAX_INSNS = 200000


def sleb(buf, pos):
    r = 0
    shift = 0
    while True:
        b = buf[pos]
        pos += 1
        r |= (b & 0x7f) << shift
        shift += 7
        if not b & 0x80:
            if b & 0x40:
                r -= 1 << shift
            return r, pos


class SoImage:
    def __init__(self, path):
        self.path = path
        self.f = open(path, "rb")
        self.elf = ELFFile(self.f)
        self.is64 = self.elf["e_machine"] == "EM_AARCH64"
        self.ptr = 8 if self.is64 else 4
        self.segs = [(s["p_vaddr"], s["p_memsz"], s.data()) for s in self.elf.iter_segments()
                     if s["p_type"] == "PT_LOAD"]
        self.size = max(v + m for v, m, _ in self.segs)
        self.funcs = {}          # name -> (addr, size)
        self._load_syms()
        self.imports = []        # 依序的 import 名稱（供 stub 配置）
        self.relocs = []         # (offset, kind, symname, addend)
        self._collect_relocs()

    def _load_syms(self):
        for sec in self.elf.iter_sections():
            if sec.name in (".dynsym", ".symtab"):
                for s in sec.iter_symbols():
                    if s["st_info"]["type"] == "STT_FUNC" and s["st_shndx"] != "SHN_UNDEF" and s["st_size"] > 0:
                        self.funcs.setdefault(s.name, (s["st_value"], s["st_size"]))

    def _symname(self, symtab, idx):
        return symtab.get_symbol(idx).name if idx else ""

    def _collect_relocs(self):
        dyn = self.elf.get_section_by_name(".dynsym")
        # 標準 REL/RELA/PLT 節
        for sec in self.elf.iter_sections():
            if hasattr(sec, "iter_relocations") and sec.header["sh_type"] in ("SHT_REL", "SHT_RELA"):
                if sec.name.startswith(".rel") and sec.name != ".rel.dyn" and sec.name != ".rela.dyn" \
                        and not sec.name.startswith(".rel.plt") and not sec.name.startswith(".rela.plt"):
                    continue
                for r in sec.iter_relocations():
                    t = r["r_info_type"]
                    sym = dyn.get_symbol(r["r_info_sym"]).name if r["r_info_sym"] else ""
                    add = r["r_addend"] if "r_addend" in r.entry else None
                    self.relocs.append((r["r_offset"], t, sym, add))
        # Android packed (APS2) 與 RELR
        d = self.elf.get_section_by_name(".dynamic")
        tags = {t.entry.d_tag: t.entry.d_val for t in d.iter_tags() if not isinstance(t.entry.d_val, str)}
        if "DT_ANDROID_RELA" in tags or "DT_ANDROID_REL" in tags:
            key = "DT_ANDROID_RELA" if "DT_ANDROID_RELA" in tags else "DT_ANDROID_REL"
            self._parse_aps2(self._read_vaddr(tags[key], tags[key + "SZ"]), key.endswith("RELA"), dyn)
        if "DT_RELR" in tags:
            self._parse_relr(self._read_vaddr(tags["DT_RELR"], tags["DT_RELRSZ"]))

    def _read_vaddr(self, va, n):
        for v, m, data in self.segs:
            if v <= va < v + len(data):
                return data[va - v:va - v + n]
        raise ValueError("vaddr not in segs")

    def _parse_aps2(self, buf, rela, dyn):
        assert buf[:4] == b"APS2", buf[:4]
        pos = 4
        n, pos = sleb(buf, pos)
        off, pos = sleb(buf, pos)
        left = n
        addend = 0
        while left > 0:
            cnt, pos = sleb(buf, pos)
            flags, pos = sleb(buf, pos)
            by_info, by_delta, by_add, has_add = flags & 1, flags & 2, flags & 4, flags & 8
            gdelta = ginfo = None
            if by_delta:
                gdelta, pos = sleb(buf, pos)
            if by_info:
                ginfo, pos = sleb(buf, pos)
            if has_add and by_add:
                d, pos = sleb(buf, pos)
                addend += d
            if rela and not has_add:
                addend = 0
            for _ in range(cnt):
                if by_delta:
                    off += gdelta
                else:
                    d, pos = sleb(buf, pos)
                    off += d
                if by_info:
                    info = ginfo
                else:
                    info, pos = sleb(buf, pos)
                if rela and has_add and not by_add:
                    d, pos = sleb(buf, pos)
                    addend += d
                if self.is64:
                    t, si = info & 0xffffffff, info >> 32
                else:
                    t, si = info & 0xff, info >> 8
                self.relocs.append((off & ((1 << 64) - 1), t, dyn.get_symbol(si).name if si else "",
                                    addend if rela else None))
            left -= cnt

    def _parse_relr(self, buf):
        fmt = "<Q" if self.is64 else "<I"
        w = self.ptr
        where = 0
        for i in range(0, len(buf), w):
            e = struct.unpack_from(fmt, buf, i)[0]
            if e & 1 == 0:
                self.relocs.append((e, "RELR", "", None))
                where = e + w
            else:
                bits = e >> 1
                a = where
                while bits:
                    if bits & 1:
                        self.relocs.append((a, "RELR", "", None))
                    bits >>= 1
                    a += w
                where += w * (w * 8 - 1)


# ---- 架構常數 ----
def regs(is64):
    if is64:
        return [getattr(A64, "UC_ARM64_REG_X%d" % i) for i in range(31)], A64.UC_ARM64_REG_SP, A64.UC_ARM64_REG_PC
    return [getattr(A, "UC_ARM_REG_R%d" % i) for i in range(13)], A.UC_ARM_REG_SP, A.UC_ARM_REG_PC


class Emu:
    """單一 .so 的一次執行環境。"""

    def __init__(self, img: SoImage, seed: int):
        self.img = img
        self.rng = random.Random(seed)
        self.is64 = img.is64
        self.uc = Uc(UC_ARCH_ARM64, UC_MODE_ARM) if self.is64 else Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.rregs, self.sp, self.pc = regs(self.is64)
        self.calls = []
        self.heap_ptr = HEAP
        self.stubs = {}
        self.fault = None
        self._map()
        self._reloc()

    # -- 記憶體 --
    def _map(self):
        uc = self.uc
        sz = (self.img.size + 0xfff) & ~0xfff
        uc.mem_map(BASE, sz + 0x1000, UC_PROT_ALL)
        for v, m, data in self.img.segs:
            uc.mem_write(BASE + v, data)
        uc.mem_map(ARENA, ARENA_SZ, UC_PROT_ALL)
        uc.mem_map(STACK, STACK_SZ, UC_PROT_ALL)
        uc.mem_map(HEAP, HEAP_SZ, UC_PROT_ALL)
        uc.mem_map(STUB_BASE, 0x20000, UC_PROT_ALL)
        uc.mem_map(RET_MAGIC, 0x1000, UC_PROT_ALL)
        stub_code = b"\x1f\x20\x03\xd5" * 4 if self.is64 else b"\x00\xbf" * 8
        uc.mem_write(STUB_BASE, stub_code * 0x1000)
        uc.mem_write(RET_MAGIC, stub_code * 8)
        uc.hook_add(UC_HOOK_CODE, self._code_hook, begin=STUB_BASE, end=STUB_BASE + 0x20000)
        uc.hook_add(UC_HOOK_CODE, self._ret_hook, begin=RET_MAGIC, end=RET_MAGIC + 0x1000)

    def seed_arena(self):
        """所有種子相同的 arena：每 8 位元組字一半為小整數、一半為指向 arena 內的指標。"""
        r = random.Random(0xC0FFEE ^ self.seed_val)
        buf = bytearray()
        w = self.img.ptr
        for i in range(ARENA_SZ // w):
            k = r.random()
            if k < 0.35:
                v = ARENA + (r.randrange(0, ARENA_SZ // 2) & ~(w - 1))
            elif k < 0.6:
                v = r.randrange(0, 64)
            elif k < 0.7:
                v = 0
            else:
                v = r.getrandbits(w * 8)
            buf += v.to_bytes(w, "little")
        self.uc.mem_write(ARENA, bytes(buf))

    # -- 重定位 --
    def _stub_for(self, name):
        if name not in self.stubs:
            addr = STUB_BASE + 16 * (len(self.stubs) + 1)
            self.stubs[name] = addr
            self.stubs[addr] = name
        return self.stubs[name]

    def _reloc(self):
        uc = self.uc
        w = self.img.ptr
        for off, t, sym, add in self.img.relocs:
            where = BASE + off
            rd = lambda: int.from_bytes(bytes(uc.mem_read(where, w)), "little")
            wr = lambda v: uc.mem_write(where, (v & ((1 << (8 * w)) - 1)).to_bytes(w, "little"))
            if t == "RELR" or t in (23, 1027):         # RELATIVE
                a = add if add is not None else rd()
                wr(BASE + a if t != "RELR" or True else a) if t != "RELR" else wr(rd() + BASE)
            elif t in (21, 22, 257 + 0, 1025, 1026):   # GLOB_DAT / JUMP_SLOT / ABS
                if t == 21 and not sym:
                    continue
                if sym in self.img.funcs and False:
                    pass
                a = self._stub_for(sym) | (0 if self.is64 else 1)
                wr(a)
            elif t == 2:                                 # ARM R_ARM_ABS32
                if sym in self.img.funcs:
                    wr(BASE + self.img.funcs[sym][0])
                else:
                    wr((self._stub_for(sym) | 1) + (add or 0))
            elif t == 1025 or t == 257:
                wr(self._stub_for(sym) + (add or 0))
            # 其他型態忽略

    # -- stub 呼叫模型 --
    def _arg(self, i):
        if self.is64:
            return self.uc.reg_read(self.rregs[i])
        if i < 4:
            return self.uc.reg_read(self.rregs[i])
        sp = self.uc.reg_read(self.sp)
        return int.from_bytes(bytes(self.uc.mem_read(sp + 4 * (i - 4), 4)), "little")

    def _norm(self, v):
        if BASE <= v < BASE + self.img.size:
            return "CODE"
        if STUB_BASE <= v < STUB_BASE + 0x20000:
            return "STUB"
        return v

    def _code_hook(self, uc, addr, size, ud):
        name = self.stubs.get(addr & ~1)
        if name is None:
            return
        args = [self._arg(i) for i in range(4)]
        self.calls.append((name, tuple(self._norm(a) for a in args)))
        ret = self._model(name, args)
        lr = uc.reg_read(self.rregs[30] if self.is64 else A.UC_ARM_REG_LR)
        r0 = self.rregs[0]
        uc.reg_write(r0, ret & ((1 << (8 * self.img.ptr)) - 1))
        if self.is64:
            uc.reg_write(self.pc, lr)
        else:
            uc.reg_write(self.pc, lr & ~1)
            cpsr = uc.reg_read(A.UC_ARM_REG_CPSR)
            uc.reg_write(A.UC_ARM_REG_CPSR, (cpsr | 0x20) if lr & 1 else (cpsr & ~0x20))

    def _ret_hook(self, uc, addr, size, ud):
        uc.emu_stop()

    def _malloc(self, n):
        n = (n + 15) & ~15
        p = self.heap_ptr
        self.heap_ptr += max(n, 16)
        if self.heap_ptr > HEAP + HEAP_SZ:
            self.heap_ptr = HEAP
            p = HEAP
        return p

    def _model(self, name, a):
        uc = self.uc
        base = name.split("@")[0]
        if base in ("malloc", "_Znwj", "_Znaj", "_Znwm", "_Znam", "calloc"):
            n = a[0] * a[1] if base == "calloc" else a[0]
            p = self._malloc(min(n, 0x10000))
            uc.mem_write(p, b"\0" * min(n, 0x10000, HEAP + HEAP_SZ - p))
            return p
        if base in ("free", "_ZdlPv", "_ZdaPv", "_ZdlPvj", "_ZdlPvm"):
            return 0
        if base == "memcpy" or base == "memmove":
            if a[2] <= 0x20000:
                uc.mem_write(a[0], bytes(uc.mem_read(a[1], a[2])))
            return a[0]
        if base == "memset":
            if a[2] <= 0x20000:
                uc.mem_write(a[0], bytes([a[1] & 0xff]) * a[2])
            return a[0]
        if base == "strlen":
            n = 0
            while bytes(uc.mem_read(a[0] + n, 1)) != b"\0" and n < 4096:
                n += 1
            return n
        if base in ("__cxa_atexit", "__cxa_finalize", "__stack_chk_fail"):
            return 0
        # 其餘外呼：回傳 0，等待結果由軌跡比對
        return 0

    # -- 執行 --
    def run(self, addr, args, thumb):
        uc = self.uc
        self.seed_val = getattr(self, "seed_val", 0)
        uc.reg_write(self.sp, STACK + STACK_SZ - 0x1000)
        for i, v in enumerate(args[: (8 if self.is64 else 4)]):
            uc.reg_write(self.rregs[i], v)
        if self.is64:
            uc.reg_write(self.rregs[30], RET_MAGIC)
            start = BASE + addr
        else:
            uc.reg_write(A.UC_ARM_REG_LR, RET_MAGIC | 1)
            start = BASE + (addr & ~1)
            if thumb:
                start |= 1
        try:
            uc.emu_start(start, RET_MAGIC, count=MAX_INSNS)
        except UcError as e:
            self.fault = str(e)
        r0 = uc.reg_read(self.rregs[0])
        mem = hashlib.sha1(bytes(uc.mem_read(ARENA, ARENA_SZ)) + bytes(uc.mem_read(HEAP, 0x10000))).hexdigest()
        return {"ret": self._norm(r0), "fault": self.fault, "calls": self.calls, "mem": mem}


def make_args(is64, rng):
    n = 8 if is64 else 4
    out = []
    for _ in range(n):
        k = rng.random()
        if k < 0.5:
            out.append(ARENA + (rng.randrange(0, ARENA_SZ // 2) & ~7))
        elif k < 0.85:
            out.append(rng.randrange(0, 32))
        else:
            out.append(rng.getrandbits(32))
    return out


def run_function(img: SoImage, name: str, seed: int):
    addr, _ = img.funcs[name]
    thumb = bool(addr & 1) if not img.is64 else False
    e = Emu(img, seed)
    e.seed_val = 1                     # arena 內容與 seed 無關：兩個版本必須看到相同內容
    e.seed_arena()
    rng = random.Random(seed)
    args = make_args(img.is64, rng)
    return e.run(addr, args, thumb)


def list_funcs(img: SoImage):
    return sorted(img.funcs)


if __name__ == "__main__":
    img = SoImage(sys.argv[1])
    print(len(img.funcs), "funcs", len(img.relocs), "relocs")
    for n in list_funcs(img)[:5]:
        print(n, run_function(img, n, 1))
