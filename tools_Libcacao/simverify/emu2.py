#!/usr/bin/env python3
"""emu2：32-bit ARM Thumb .so 的有狀態 Unicorn 差分模擬器（emu.py 的改良版）。

與 emu.py 的差異：
  * 自己解析符號：.so 內自定義的符號（含 PLT 自呼叫、g_* 資料）一律綁回自身，其餘才建 stub。
  * 執行 DT_INIT_ARRAY（C++ 全域建構子），一個 Machine 可連續呼叫多個函數（保留全域狀態）。
  * 結構化輸入：呼叫端以 Machine.alloc() 在 TESTMEM 配置並填欄位，不再塞亂數指標。
  * 完整的外呼模型（libc / pthread / socket / ashmem / hw_get_module / gralloc1 device ...）：
      - 全部「事件」(名稱+正規化參數+必要的記憶體快照) 依序記錄，兩個版本逐一比對。
      - 可在第 k 次呼叫某 import 時注入失敗（fault injection）。
  * 指標正規化：TESTMEM/HEAP/MMAP/WORLD/CODE/STUB 各自轉成 (區域, 序號, 位移)，避免位址差異造成雜訊。
"""
import hashlib
import os
import random
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import SoImage  # noqa: E402  (沿用 relocation/APS2 解析)

from unicorn import (UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_THUMB, UC_PROT_ALL, Uc, UcError)
from unicorn import arm_const as A

BASE = 0x10000000
TEST = 0x20000000
TEST_SZ = 0x200000
STACK = 0x30000000
STACK_SZ = 0x100000
HEAP = 0x40000000
HEAP_SZ = 0x800000
MMAP = 0x50000000
MMAP_SZ = 0x1000000
WORLD = 0x60000000
WORLD_SZ = 0x20000
STUBS = 0x70000000
STUBS_SZ = 0x10000
RET_MAGIC = 0x7f000000

MAX_INSNS = 400000

# ---- gralloc1 function id -> (name) ----
G1 = {1: "dump", 2: "createDescriptor", 3: "destroyDescriptor", 4: "setConsumerUsage",
      5: "setDimensions", 6: "setFormat", 7: "setProducerUsage", 8: "getBackingStore",
      9: "getConsumerUsage", 10: "getDimensions", 11: "getFormat", 12: "getProducerUsage",
      13: "getStride", 14: "allocate", 15: "retain", 16: "release", 17: "getNumFlexPlanes",
      18: "lock", 19: "lockFlex", 20: "unlock", 21: "setLayerCount", 22: "getLayerCount",
      0x1000: "perform"}

ALIAS = {
    "__open_2": "open", "__read_chk": "read", "__write_chk": "write",
    "__aeabi_memcpy": "memcpy", "__aeabi_memcpy4": "memcpy", "__memcpy_chk": "memcpy",
    "__aeabi_memclr": "memclr", "__aeabi_memclr8": "memclr", "__aeabi_memclr4": "memclr",
    "_Znwj": "new", "_Znaj": "new", "_ZdlPv": "delete", "_ZdaPv": "delete",
    "__FD_SET_chk": "fdset", "__FD_ISSET_chk": "fdisset",
}
# 不進事件序列（純記憶體語意，效果由記憶體快照比對）
SILENT = {"memcpy", "memclr", "memset", "strlen", "strnlen", "__strlcpy_chk", "strlcpy",
          "__stack_chk_fail", "__cxa_atexit", "__cxa_finalize", "__errno", "__register_atfork",
          "atoi", "strerror", "fdset", "fdisset", "pthread_self"}


def canon(sym):
    s = sym.split("@")[0]
    return ALIAS.get(s, s)


class Fault(Exception):
    pass


class Machine:
    def __init__(self, path, fail=None, world=None, seed=0):
        self.img = SoImage(path)
        self.path = path
        self.fail = dict(fail or {})
        self.w = dict(world or {})       # 場景參數：props / select 腳本 / recv 腳本 ...
        self.events = []
        self.obs = []
        self.counts = {}
        self.fault = None
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.uc.reg_write(A.UC_ARM_REG_C1_C0_2, self.uc.reg_read(A.UC_ARM_REG_C1_C0_2) | (0xf << 20))
        self.uc.reg_write(A.UC_ARM_REG_FPEXC, 0x40000000)
        self.stubs = {}      # addr -> name ; name -> addr
        self.defs = {}
        self.test_ptr = TEST + 0x100
        self.heap_ptr = HEAP + 0x1000
        self.allocs = []     # (addr,size,live)
        self.mmap_ptr = MMAP
        self.mmaps = []
        self.next_fd = 100
        self.threads = []
        self.world_ptr = WORLD + 0x1000
        self.gdesc = 1
        self.rng = random.Random(0xC0FFEE + seed)
        self.sel = list(self.w.get("select", []))
        self.recvq = list(self.w.get("recv", []))
        self.readq = list(self.w.get("read", []))
        self.clock_n = 0
        self.tag_alloc = {}
        self.heap_base = 0
        self.cbs = {}
        self._map()
        self._load_syms()
        self._reloc()
        self._init_world()
        self._run_init()

    # ------------------------------------------------------------------ memory
    def _map(self):
        uc = self.uc
        sz = (self.img.size + 0xfff) & ~0xfff
        self.code_end = BASE + sz
        uc.mem_map(BASE, sz + 0x1000, UC_PROT_ALL)
        for v, m, data in self.img.segs:
            uc.mem_write(BASE + v, data)
        for a, s in ((TEST, TEST_SZ), (STACK, STACK_SZ), (HEAP, HEAP_SZ), (MMAP, MMAP_SZ),
                     (WORLD, WORLD_SZ), (STUBS, STUBS_SZ), (RET_MAGIC, 0x1000)):
            uc.mem_map(a, s, UC_PROT_ALL)
        nop = b"\x00\xbf" * (STUBS_SZ // 2)
        uc.mem_write(STUBS, nop)
        uc.mem_write(RET_MAGIC, b"\x00\xbf" * 0x800)
        uc.hook_add(UC_HOOK_CODE, self._code_hook, begin=STUBS, end=STUBS + STUBS_SZ)
        uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, u: uc.emu_stop(), begin=RET_MAGIC, end=RET_MAGIC + 0x1000)

    def rd(self, a, n):
        return bytes(self.uc.mem_read(a, n))

    def wr(self, a, b):
        self.uc.mem_write(a, bytes(b))

    def r32(self, a):
        return struct.unpack("<I", self.rd(a, 4))[0]

    def w32(self, a, v):
        self.wr(a, struct.pack("<I", v & 0xffffffff))

    def cstr(self, a, mx=256):
        if a == 0:
            return None
        out = b""
        while len(out) < mx:
            c = self.rd(a + len(out), 1)
            if c == b"\0":
                break
            out += c
        return out.decode("latin1")

    # test-side allocation ------------------------------------------------
    def alloc(self, n, fill=None, align=16):
        n = max(n, 4)
        p = (self.test_ptr + align - 1) & ~(align - 1)
        self.test_ptr = p + n
        if self.test_ptr > TEST + TEST_SZ:
            raise Fault("TESTMEM exhausted")
        if fill:
            self.wr(p, bytes([fill]) * n)
        return p

    def alloc_str(self, s):
        p = self.alloc(len(s) + 1)
        self.wr(p, s.encode() + b"\0")
        return p

    def walloc(self, n, align=16):
        p = (self.world_ptr + align - 1) & ~(align - 1)
        self.world_ptr = p + n
        return p

    # lib heap ------------------------------------------------------------
    def _malloc(self, n, zero=True):
        n = max((n + 15) & ~15, 16)
        p = self.heap_ptr
        if p + n > HEAP + HEAP_SZ:
            return 0
        self.heap_ptr += n + 16
        self.allocs.append([p, n, True])
        if zero:
            self.wr(p, b"\0" * n)
        return p

    # ------------------------------------------------------------------ symbols
    def _load_syms(self):
        dyn = self.img.elf.get_section_by_name(".dynsym")
        self.exports = {}
        for s in dyn.iter_symbols():
            if s["st_shndx"] != "SHN_UNDEF" and s.name:
                self.defs[s.name] = (s["st_value"], s["st_info"]["type"], s["st_size"])
                if s["st_info"]["type"] == "STT_FUNC":
                    self.exports[s.name] = s["st_value"]

    def stub(self, name):
        if name not in self.stubs:
            a = STUBS + 0x20 + 8 * (len(self.stubs) // 2)
            self.stubs[name] = a
            self.stubs[a] = name
        return self.stubs[name] | 1

    def _reloc(self):
        w = self.uc
        data_syms = {"__stack_chk_guard": WORLD + 0x20, "stderr": WORLD + 0x24}
        for off, t, sym, add in self.img.relocs:
            where = BASE + off
            cur = self.r32(where)
            if t == "RELR" or t == 23:
                self.w32(where, BASE + (cur if add is None else add))
            elif t in (21, 22, 2):
                if not sym:
                    self.w32(where, BASE + cur)
                    continue
                base = sym.split("@")[0]
                if sym in self.defs or base in self.defs:
                    v = self.defs.get(sym) or self.defs[base]
                    val = BASE + v[0]
                else:
                    if base in data_syms:
                        val = data_syms[base]
                    else:
                        val = self.stub(sym)
                if t == 2:
                    val += (cur if add is None else add)
                self.w32(where, val)
            elif t in (0,):
                pass

    def _init_world(self):
        self.w32(WORLD + 0x20, 0xabadcafe)     # __stack_chk_guard
        self.w32(WORLD + 0x24, WORLD + 0x28)   # stderr
        self.w32(WORLD + 0x10, 0)              # errno
        self.errno_cell = WORLD + 0x10
        # fake gralloc module / device
        self.g_mod = WORLD + 0x100
        self.g_methods = WORLD + 0x200
        self.g_dev = WORLD + 0x300
        self.w32(self.g_mod + 0, 0x4d504f48)
        self.w32(self.g_mod + 20, self.g_methods)
        self.w32(self.g_methods, self.stub("gralloc.open"))
        self.w32(self.g_dev + 0, 0x48574454)
        self.w32(self.g_dev + 8, self.g_mod)
        self.w32(self.g_dev + 60, self.stub("gralloc.close"))
        self.w32(self.g_dev + 64, self.stub("gralloc.getCapabilities"))
        self.w32(self.g_dev + 68, self.stub("gralloc.getFunction"))
        self.strerr = WORLD + 0x400

    def _run_init(self):
        d = self.img.elf.get_section_by_name(".dynamic")
        tags = {t.entry.d_tag: t.entry.d_val for t in d.iter_tags()}
        ctors = []
        if "DT_INIT" in tags:
            ctors.append(BASE + tags["DT_INIT"])
        if "DT_INIT_ARRAY" in tags:
            n = tags["DT_INIT_ARRAYSZ"] // 4
            for i in range(n):
                v = self.r32(BASE + tags["DT_INIT_ARRAY"] + 4 * i)
                if v not in (0, 0xffffffff):
                    ctors.append(v)
        self.nctors = len(ctors)
        for c in ctors:
            self._exec(c if c & 1 else c | 1, [])
        self.events.clear()
        self.counts.clear()

    # ------------------------------------------------------------------ normalization
    def norm(self, v):
        v &= 0xffffffff
        if BASE <= v < self.code_end:
            return "C"
        if TEST <= v < TEST + TEST_SZ:
            return ("T", v - TEST)
        if HEAP <= v < HEAP + HEAP_SZ:
            for i, (p, n, live) in enumerate(self.allocs):
                if p <= v < p + n:
                    return ("H", i - self.heap_base, v - p)
            return ("H?", v - HEAP)
        if MMAP <= v < MMAP + MMAP_SZ:
            for i, (p, n) in enumerate(self.mmaps):
                if p <= v < p + n:
                    return ("M", i, v - p)
            return ("M?", v - MMAP)
        if WORLD <= v < WORLD + WORLD_SZ:
            return ("W", v - WORLD)
        if STUBS <= v < STUBS + STUBS_SZ:
            return ("S", self.stubs.get(v & ~1, "?"))
        if STACK <= v < STACK + STACK_SZ:
            return "STK"
        return v

    def snap_words(self, a, nbytes):
        if a == 0:
            return None
        n = (nbytes + 3) // 4
        try:
            raw = self.rd(a, 4 * n)
        except UcError:
            return "UNMAPPED"
        return [self.norm(x) for x in struct.unpack("<%dI" % n, raw)]

    # ------------------------------------------------------------------ arg access (AAPCS)
    class Args:
        def __init__(self, m, start=0):
            self.m = m
            self.i = start
            self.sp = m.uc.reg_read(A.UC_ARM_REG_SP)
            self.regs = [m.uc.reg_read(r) for r in (A.UC_ARM_REG_R0, A.UC_ARM_REG_R1,
                                                    A.UC_ARM_REG_R2, A.UC_ARM_REG_R3)]

        def u32(self):
            i = self.i
            self.i += 1
            if i < 4:
                return self.regs[i]
            return self.m.r32(self.sp + 4 * (i - 4))

        def u64(self):
            if self.i % 2:
                self.i += 1
            lo = self.u32()
            hi = self.u32()
            return lo | (hi << 32)

    def _code_hook(self, uc, addr, size, ud):
        name = self.stubs.get(addr & ~1)
        if name is None:
            return
        lr = uc.reg_read(A.UC_ARM_REG_LR)
        base = canon(name)
        k = self.counts.get(base, 0)
        self.counts[base] = k + 1
        args = Machine.Args(self)
        try:
            ret, jump = self._model(base, name, args, k)
        except UcError as e:
            self.fault = "stubmem:%s:%s" % (base, e)
            uc.emu_stop()
            return
        if isinstance(ret, tuple):
            lo, hi = ret
            uc.reg_write(A.UC_ARM_REG_R0, lo & 0xffffffff)
            uc.reg_write(A.UC_ARM_REG_R1, hi & 0xffffffff)
        else:
            uc.reg_write(A.UC_ARM_REG_R0, (ret or 0) & 0xffffffff)
        target = jump if jump is not None else lr
        uc.reg_write(A.UC_ARM_REG_PC, target)

    def ev(self, *a):
        self.events.append(tuple(a))

    # ------------------------------------------------------------------ stub model
    def failret(self, base):
        return {"malloc": 0, "calloc": 0, "mmap": 0xffffffff, "dup": 0xffffffff, "pipe": 0xffffffff,
                "ashmem_create_region": 0xffffffff, "ashmem_set_prot_region": 0xffffffff,
                "hw_get_module": 0xffffffff, "sendmsg": 0xffffffff, "recvmsg": 0xffffffff,
                "pthread_create": 11, "socket_local_client": 0xffffffff, "android_get_control_socket": 0xffffffff,
                "listen": 0xffffffff, "accept": 0xffffffff, "open": 0xffffffff, "write": 0xffffffff,
                "munmap": 0xffffffff, "select": 0xffffffff, "pthread_cond_timedwait": 110,
                "gralloc.open": 0xffffffff, "pthread_mutex_init": 22, "clock_gettime": 0xffffffff,
                "prctl": 0xffffffff, "read": 0xffffffff, "close": 0xffffffff, "unlink": 0xffffffff,
                "pthread_join": 22}.get(base, 1)

    def _model(self, base, raw, a, k):
        uc = self.uc
        inj = self.fail.get((base, k))

        def log(*x):
            if base not in SILENT:
                self.ev(base, *x)

        # ---- memory / string primitives (silent) ----
        if base in ("memcpy",):
            d, s, n = a.u32(), a.u32(), a.u32()
            if n and n < 0x100000:
                self.wr(d, self.rd(s, n))
            return d, None
        if base in ("memclr",):
            d, n = a.u32(), a.u32()
            if n and n < 0x100000:
                self.wr(d, b"\0" * n)
            return d, None
        if base == "memset":
            d, c, n = a.u32(), a.u32(), a.u32()
            if n and n < 0x100000:
                self.wr(d, bytes([c & 0xff]) * n)
            return d, None
        if base in ("strlen",):
            s = self.cstr(a.u32(), 4096)
            return len(s or ""), None
        if base == "strnlen":
            p, n = a.u32(), a.u32()
            s = self.cstr(p, n) or ""
            return min(len(s), n), None
        if base in ("__strlcpy_chk", "strlcpy"):
            d, s, n = a.u32(), a.u32(), a.u32()
            src = (self.cstr(s, 4096) or "").encode("latin1")
            if n:
                self.wr(d, src[:n - 1] + b"\0")
            return len(src), None
        if base == "atoi":
            s = self.cstr(a.u32()) or ""
            m = re.match(r"\s*[-+]?\d+", s)
            return int(m.group(0)) & 0xffffffff if m else 0, None
        if base in ("__stack_chk_fail",):
            self.fault = "stack_chk_fail"
            uc.emu_stop()
            return 0, None
        if base in ("__cxa_atexit", "__cxa_finalize", "__register_atfork"):
            return 0, None
        if base == "__errno":
            return self.errno_cell, None
        if base == "strerror":
            e = a.u32()
            self.wr(self.strerr, ("ERR%d" % e).encode() + b"\0")
            return self.strerr, None
        if base == "fdset":
            fd, p, _ = a.u32(), a.u32(), a.u32()
            if p:
                b = self.rd(p + fd // 8, 1)[0] | (1 << (fd % 8))
                self.wr(p + fd // 8, bytes([b]))
            return 0, None
        if base == "fdisset":
            fd, p, _ = a.u32(), a.u32(), a.u32()
            return (self.rd(p + fd // 8, 1)[0] >> (fd % 8)) & 1, None
        if base == "pthread_self":
            return 0x5000, None

        # ---- allocation ----
        if base in ("malloc", "new"):
            n = a.u32()
            r = 0 if (inj is not None and base == "malloc") else self._malloc(n)
            log(n, "ret0" if r == 0 else "ok")
            return r, None
        if base == "calloc":
            n, m = a.u32(), a.u32()
            r = 0 if inj is not None else self._malloc(n * m)
            log(n * m, "ret0" if r == 0 else "ok")
            return r, None
        if base in ("free", "delete"):
            p = a.u32()
            if p:
                st = "?"
                for e in self.allocs:
                    if e[0] == p:
                        st = "ok" if e[2] else "dbl"
                        e[2] = False
                        break
                else:
                    st = "bad"
                log(self.norm(p), st)
            else:
                log("null")
            return 0, None

        # ---- logging ----
        if base == "__android_log_print":
            prio, tag, fmt = a.u32(), a.u32(), a.u32()
            self.ev("log", prio, self.cstr(tag), self.fmt(self.cstr(fmt, 512), a))
            return 1, None
        if base == "__vsnprintf_chk":
            dst, mx, fl, sl, fmt, ap = a.u32(), a.u32(), a.u32(), a.u32(), a.u32(), a.u32()
            va = _VaMem(self, ap)
            s = self.fmt(self.cstr(fmt, 512), va)
            b = s.encode("latin1")
            if mx:
                self.wr(dst, b[:mx - 1] + b"\0")
            return len(b), None

        # ---- libunwind noise (orig static libunwind) ----
        if base in ("fprintf", "fflush", "abort", "dladdr", "dl_iterate_phdr"):
            log()
            return 0, None

        # ---- clocks ----
        if base == "clock_gettime":
            clk, ts = a.u32(), a.u32()
            self.clock_n += 1
            sec = 1000 + clk * 100 + self.clock_n
            ns = 111111111 * (clk + 1) + self.clock_n * 1000
            self.wr(ts, struct.pack("<II", sec, ns))
            log(clk)
            if inj is not None:
                return self.failret(base), None
            return 0, None
        if base == "getpagesize":
            return 4096, None
        if base == "gettid":
            log()
            return 1234, None
        if base == "prctl":
            op, a1 = a.u32(), a.u32()
            log(op, self.cstr(a1) if op == 15 else a1)
            return 0, None
        if base == "setpriority":
            log(a.u32(), a.u32(), a.u32())
            return 0, None
        if base == "property_get":
            key, val, dflt = a.u32(), a.u32(), a.u32()
            kk = self.cstr(key)
            v = self.w.get("props", {}).get(kk, self.cstr(dflt) or "")
            self.wr(val, v.encode() + b"\0")
            log(kk, self.cstr(dflt))
            return len(v), None

        # ---- pthread ----
        if base.startswith("pthread_"):
            return self._pthread(base, a, k, inj)

        # ---- fd / mmap / ashmem ----
        if base == "dup":
            fd = a.u32()
            log(fd)
            if inj is not None:
                self.w32(self.errno_cell, 24)
                return 0xffffffff, None
            self.next_fd += 1
            return self.next_fd, None
        if base == "close":
            log(a.u32())
            return 0, None
        if base == "pipe":
            p = a.u32()
            log()
            if inj is not None:
                self.w32(self.errno_cell, 24)
                return 0xffffffff, None
            self.next_fd += 2
            self.wr(p, struct.pack("<II", self.next_fd - 1, self.next_fd))
            return 0, None
        if base == "ashmem_create_region":
            nm, sz = a.u32(), a.u32()
            log(self.cstr(nm), sz)
            if inj is not None:
                return 0xffffffff, None
            self.next_fd += 1
            return self.next_fd, None
        if base == "ashmem_set_prot_region":
            fd, prot = a.u32(), a.u32()
            log(fd, prot)
            return (0xffffffff if inj is not None else 0), None
        if base == "mmap":
            ad, ln, pr, fl, fd, off = [a.u32() for _ in range(6)]
            log(self.norm(ad) if ad else 0, ln, pr, fl, fd, off)
            if inj is not None:
                self.w32(self.errno_cell, 12)
                return 0xffffffff, None
            p = self.mmap_ptr
            ln2 = (ln + 0xfff) & ~0xfff
            self.mmap_ptr += ln2 + 0x1000
            self.mmaps.append((p, ln2))
            return p, None
        if base == "munmap":
            ad, ln = a.u32(), a.u32()
            log(self.norm(ad), ln)
            if inj is not None:
                self.w32(self.errno_cell, 22)
                return 0xffffffff, None
            return 0, None
        if base == "open":
            p, fl = a.u32(), a.u32()
            log(self.cstr(p), fl)
            if inj is not None:
                self.w32(self.errno_cell, 2)
                return 0xffffffff, None
            self.next_fd += 1
            return self.next_fd, None
        if base == "unlink":
            log(self.cstr(a.u32()))
            return 0, None
        if base == "write":
            fd, p, n = a.u32(), a.u32(), a.u32()
            log(fd, self.rd(p, min(n, 64)).hex() if n else "", n)
            if inj is not None:
                return 0xffffffff, None
            return n, None
        if base == "read":
            fd, p, n = a.u32(), a.u32(), a.u32()
            log(fd, n)
            if self.readq:
                d = self.readq.pop(0)
                if isinstance(d, int):
                    return d & 0xffffffff, None
                d = d[:n]
                self.wr(p, d)
                return len(d), None
            return 0, None

        # ---- sockets ----
        if base == "socket_local_client":
            nm, ns, ty = a.u32(), a.u32(), a.u32()
            log(self.cstr(nm), ns, ty)
            if inj is not None:
                return 0xffffffff, None
            self.next_fd += 1
            return self.next_fd, None
        if base == "android_get_control_socket":
            log(self.cstr(a.u32()))
            if inj is not None:
                return 0xffffffff, None
            self.next_fd += 1
            return self.next_fd, None
        if base == "listen":
            log(a.u32(), a.u32())
            return (0xffffffff if inj is not None else 0), None
        if base == "accept":
            log(a.u32())
            if inj is not None:
                return 0xffffffff, None
            self.next_fd += 1
            return self.next_fd, None
        if base == "select":
            n, r, w_, e, tv = [a.u32() for _ in range(5)]
            log(n, self.snap_words(r, 16) if r else None, self.snap_words(w_, 16) if w_ else None, tv)
            if inj is not None:
                return 0xffffffff, None
            if self.sel:
                s = self.sel.pop(0)
                if isinstance(s, int):
                    return s & 0xffffffff, None
                rd_bits, ret = s
                if r:
                    self.wr(r, b"\0" * 128)
                    for fd in rd_bits:
                        b = self.rd(r + fd // 8, 1)[0] | (1 << (fd % 8))
                        self.wr(r + fd // 8, bytes([b]))
                return ret, None
            return 1, None
        if base == "sendmsg":
            fd, mh, fl = a.u32(), a.u32(), a.u32()
            iov, niov, ctl, ctll = self.r32(mh + 8), self.r32(mh + 12), self.r32(mh + 16), self.r32(mh + 20)
            parts = []
            tot = 0
            for i in range(niov):
                b, l = self.r32(iov + 8 * i), self.r32(iov + 8 * i + 4)
                parts.append((l, self.rd(b, min(l, 48)).hex() if l else ""))
                tot += l
            c = self.rd(ctl, min(ctll, 64)).hex() if ctl and ctll else None
            log(fd, fl, niov, ctll, parts, c)
            if inj is not None:
                self.w32(self.errno_cell, 32)
                return 0xffffffff, None
            return tot, None
        if base == "recvmsg":
            fd, mh, fl = a.u32(), a.u32(), a.u32()
            iov, niov, ctl, ctll = self.r32(mh + 8), self.r32(mh + 12), self.r32(mh + 16), self.r32(mh + 20)
            log(fd, fl, niov, [self.r32(iov + 8 * i + 4) for i in range(niov)], ctll)
            if inj is not None:
                return 0xffffffff, None
            if self.recvq:
                d = self.recvq.pop(0)
                if isinstance(d, int):
                    return d & 0xffffffff, None
                data, fds = d
                off = 0
                for i in range(niov):
                    b, l = self.r32(iov + 8 * i), self.r32(iov + 8 * i + 4)
                    chunk = data[off:off + l]
                    self.wr(b, chunk)
                    off += len(chunk)
                if fds and ctl:
                    n = len(fds)
                    self.w32(ctl, 12 + 4 * n)
                    self.w32(ctl + 4, 1)
                    self.w32(ctl + 8, 1)
                    for j, f in enumerate(fds):
                        self.w32(ctl + 12 + 4 * j, f)
                    self.w32(mh + 20, 12 + 4 * n)
                return len(data), None
            return 0, None

        # ---- hw / gralloc ----
        if base == "hw_get_module":
            idp, out = a.u32(), a.u32()
            log(self.cstr(idp))
            if inj is not None or self.w.get("hw_fail"):
                return 0xffffffff, None
            self.w32(out, self.g_mod)
            return 0, None
        if base.startswith("gralloc."):
            return self._gralloc(base, a, k, inj)
        if base.startswith("g1."):
            return self._g1(base[3:], a, k, inj)
        if base.startswith("cb."):
            log(*[self.norm(a.u32()) for _ in range(3)])
            return self.cbs.get(base, 0), None
        # ---- chokoballpal 用到的 Android / cammw_util 外呼 ----
        if base.startswith("_ZN7android13GraphicBufferC1"):
            this, w_, h_, f_, lc, us, st, hnd, ko = [a.u32() for _ in range(9)]
            log(self.norm(this), w_, h_, f_, lc, hex(us), st, self.hsnap(hnd) if hnd else None, ko)
            return this, None
        if base.startswith("_ZNK7android13GraphicBuffer9initCheck"):
            a.u32()
            log()
            return self.w.get("initcheck", 0), None
        if base.startswith("_ZNK7android13GraphicBuffer15getNativeBuffer"):
            t = a.u32()
            log(self.norm(t))
            return WORLD + 0x5000, None
        if base.startswith("_ZNK7android7RefBase9incStrong") or base.startswith("_ZNK7android7RefBase9decStrong"):
            t = a.u32()
            log(self.norm(t))
            return 0, None
        if base.startswith("_ZN7android13sp_report_race"):
            log()
            return 0, None
        if base == "cammw_util_shmem_alloc_buf":
            ty, fl, sz, out = a.u32(), a.u32(), a.u32(), a.u32()
            log(ty, hex(fl), sz, self.norm(out))
            rc = self.w.get("alloc_rc", 0)
            if inj is not None:
                rc = 0xffffffff
            if rc == 0:
                self.wr(out, struct.pack("<4I", 0x1111, 0x2222, 0x3333, 0x4444))
            return rc, None
        if base == "cammw_util_shmem_attach_image_buf":
            args = [a.u32() for _ in range(8)]
            src, p2, p3, fmt, src5, w_, h_, out = args
            log(self.snap_words(src, 20), p2, p3, hex(fmt), self.snap_words(src5, 12) if src5 else None, w_, h_, self.norm(out))
            rc = self.w.get("attach_rc", 0)
            if inj is not None:
                rc = 5
            if rc == 0:
                hp = self.mk_handle(0x11)
                self.wr(out, b"\0" * 0x68)
                self.w32(out + 0xc, hp)
            return rc, None
        if base in ("cammw_util_shmem_free_buf", "cammw_util_shmem_detach_image_buf"):
            p = a.u32()
            log(self.norm(p), self.snap_words(p, 0x18) if p else None)
            return 0, None
        if base == "cammw_util_shmem_clean_buf":
            p, md = a.u32(), a.u32()
            log(self.norm(p), md, self.snap_words(p, 0x18) if p else None)
            return self.w.get("clean_rc", 0), None
        if base in ("cammw_util_shmem_register_buf", "cammw_util_shmem_unregister_buf"):
            log(a.u32(), a.u32(), a.u32())
            return 0, None
        # unknown import
        log(*[self.norm(a.u32()) for _ in range(4)])
        return 0, None

    # --- pthread ---
    def _pthread(self, base, a, k, inj):
        def log(*x):
            self.ev(base, *x)
        if base == "pthread_mutex_init":
            m = a.u32()
            log(self.norm(m), self.norm(a.u32()) if True else 0)
            return (22 if inj is not None else 0), None
        if base in ("pthread_mutex_lock", "pthread_mutex_unlock", "pthread_mutex_destroy",
                    "pthread_cond_signal", "pthread_cond_destroy"):
            log(self.norm(a.u32()))
            return 0, None
        if base == "pthread_cond_init":
            log(self.norm(a.u32()), a.u32())
            return 0, None
        if base == "pthread_cond_wait":
            _c, _m = a.u32(), a.u32()
            self.last_mutex_arg = _m
            log(self.norm(_c), self.norm(_m))
            if self.w.get("wait_effect"):
                sess = _m - 0x6c
                self.wr(sess + 0x75, b"\x01")
                self.w32(sess + 0x7c, 9)
                self.w32(sess + 0x80, 5)
                self.wr(sess + 0x84, b"REPLY")
                return 0, None
            if k >= 2:
                self.fault = "blocked"
                self.uc.emu_stop()
            return 0, None
        if base == "pthread_cond_timedwait":
            c, m, ts = a.u32(), a.u32(), a.u32()
            log(self.norm(c), self.norm(m), self.snap_words(ts, 8))
            if self.w.get("session_signal"):
                sess = m - 0x6c
                self.wr(sess + 0x75, b"\x01")
                self.w32(sess + 0x78, 0)
                self.w32(sess + 0x80, 0)
                return 0, None
            return (110 if (inj is not None or k >= 2) else self.w.get("timedwait", 0)), None
        if base == "pthread_create":
            t, at, fn, arg = a.u32(), a.u32(), a.u32(), a.u32()
            log(self.norm(t), at, self.norm(arg))
            if inj is not None:
                return 11, None
            tid = 0x5001 + len(self.threads)
            self.w32(t, tid)
            self.threads.append((fn, arg, tid))
            return 0, None
        if base == "pthread_join":
            log(a.u32() - 0x5000, a.u32())
            return 0, None
        if base == "pthread_detach":
            log(a.u32() - 0x5000)
            return 0, None
        if base == "pthread_equal":
            x, y = a.u32(), a.u32()
            self.ev(base)
            return int(x == y), None
        if base == "pthread_once":
            once, fn = a.u32(), a.u32()
            self.ev(base)
            if self.r32(once) == 0:
                self.w32(once, 1)
                return 0, fn
            return 0, None
        self.ev(base, "?")
        return 0, None

    # --- gralloc module/device ---
    def _gralloc(self, base, a, k, inj):
        if base == "gralloc.open":
            mod, nm, out = a.u32(), a.u32(), a.u32()
            self.ev("g.open", self.norm(mod), self.cstr(nm))
            if inj is not None or self.w.get("g_open_fail"):
                return 0xffffffff, None
            self.w32(out, self.g_dev)
            return 0, None
        if base == "gralloc.close":
            self.ev("g.close")
            return 0, None
        if base == "gralloc.getCapabilities":
            self.ev("g.getCaps")
            return 0, None
        if base == "gralloc.getFunction":
            dev, fid = a.u32(), a.u32()
            self.ev("g.getFunction", self.norm(dev), fid)
            if fid in G1 and fid not in self.w.get("g_missing", ()):
                return self.stub("g1." + G1[fid]), None
            return 0, None

    def mk_handle(self, fmt, w=64, h=48, fd=0, size=None, offset=0, ints=25):
        p = self.walloc(160)
        base = self.walloc(0x1000)
        self.next_fd += 2
        self.wr(p, b"\0" * 160)
        self.w32(p + 0, 12)
        self.w32(p + 4, 2)
        self.w32(p + 8, ints)
        self.w32(p + 12, self.next_fd - 1)       # fd
        self.w32(p + 16, self.next_fd)           # fd_metadata
        self.w32(p + 20, 0x6d736d67)            # magic 'gmsm'
        self.w32(p + 24, 0x20000000)            # flags
        self.w32(p + 28, w)
        self.w32(p + 32, h)
        self.w32(p + 36, w)
        self.w32(p + 40, h)
        self.w32(p + 44, fmt)
        self.w32(p + 48, 1)
        self.w32(p + 52, size if size is not None else w * h * 3 // 2)
        self.w32(p + 56, offset)
        self.w32(p + 60, 0)
        self.w32(p + 64, MMAP + 0x800000)
        return p

    def hsnap(self, h):
        if not h:
            return None
        w = self.snap_words(h, 116)
        if isinstance(w, list) and w[2] in (24, 25):
            w[2] = "N"
        return w

    def _g1(self, name, a, k, inj):
        rc = 0
        if inj is not None:
            rc = self.w.get("g1_failrc", 1)
        ev = lambda *x: self.ev("g1." + name, *x)
        dev = a.u32()
        if name == "createDescriptor":
            out = a.u32()
            ev()
            if rc == 0:
                self.gdesc += 1
                self.wr(out, struct.pack("<Q", 0x1000 + self.gdesc))
            return rc, None
        if name == "destroyDescriptor":
            ev(a.u64())
            return rc, None
        if name == "setConsumerUsage" or name == "setProducerUsage":
            d = a.u64()
            ev(d, hex(a.u64()))
            return rc, None
        if name == "setDimensions":
            d = a.u64()
            ev(d, a.u32(), a.u32())
            return rc, None
        if name == "setFormat":
            d = a.u64()
            ev(d, a.u32())
            return rc, None
        if name == "allocate":
            n, descs, out = a.u32(), a.u32(), a.u32()
            ds = [struct.unpack("<Q", self.rd(descs + 8 * i, 8))[0] for i in range(n)] if descs else None
            ev(n, ds)
            if rc == 0:
                fmt = self.w.get("alloc_fmt", 0x21)
                hp = self.mk_handle(fmt, ints=self.w.get("ints", 25))
                self.w32(out, hp)
                self.last_alloc_handle = hp
            return rc, None
        if name in ("retain", "release", "unlock", "getNumFlexPlanes", "getFormat"):
            h = a.u32()
            extra = ()
            if name == "unlock":
                f = a.u32()
                extra = (self.snap_words(f, 4),)
                if rc == 0 and f:
                    self.w32(f, 0xffffffff)
            if name == "getFormat":
                o = a.u32()
                if rc == 0:
                    self.w32(o, 0x11)
            ev(self.hsnap(h), *extra)
            return rc, None
        if name == "lock":
            h = a.u32()
            pu, cu, rect, out, fence = a.u64(), a.u64(), a.u32(), a.u32(), a.u32()
            ev(self.hsnap(h), hex(pu), hex(cu), self.snap_words(rect, 16), fence & 0xffffffff)
            if rc == 0 and out:
                self.w32(out, MMAP + 0x900000)
            return rc, None
        if name == "lockFlex":
            h = a.u32()
            pu, cu, rect, lay, fence = a.u64(), a.u64(), a.u32(), a.u32(), a.u32()
            planes = self.r32(lay + 8) if lay else 0
            ev(hex(pu), hex(cu), self.snap_words(rect, 16), fence & 0xffffffff,
               self.r32(lay + 4) if lay else None, "planes_null" if planes == 0 else "planes_ok")
            if rc == 0 and lay and planes:
                r = self.w.get("flex", None)
                if r is None:
                    r = (7, [(MMAP + 0x900000, 1, 8, 8, 1, 640, 1, 1),
                             (MMAP + 0x900000 + 640 * 480, 2, 8, 8, 2, 640, 2, 2),
                             (MMAP + 0x900000 + 640 * 480 + 1, 4, 8, 8, 2, 640, 2, 2)])
                self.w32(lay, r[0])
                self.w32(lay + 4, len(r[1]))
                for i, p in enumerate(r[1]):
                    self.wr(planes + 32 * i, struct.pack("<8I", *p))
            return rc, None
        if name == "perform":
            op = a.u32()
            vals = [a.u32() for _ in range(9)]
            ev(op, vals[:3] + vals[4:6])
            if op == 5:
                # GET_ATTRIBUTES: (w, h, fmt, prod u64, cons u64, &aw, &ah, &tile)
                pass
            # 回填對齊後尺寸
            w_, h_ = vals[0], vals[1]
            # layout: op,w,h,fmt,prod(2 words aligned),cons(2 words),p1,p2,p3
            a2 = Machine.Args(self, 1)
            ww, hh, ff = a2.u32(), a2.u32(), a2.u32()
            pr, co, p1, p2, p3 = a2.u64(), a2.u64(), a2.u32(), a2.u32(), a2.u32()
            if rc == 0:
                for ptr, v in ((p1, (ww + 31) & ~31), (p2, (hh + 31) & ~31), (p3, 0)):
                    if ptr:
                        self.w32(ptr, v)
            return rc, None
        ev(*[a.u32() for _ in range(3)])
        return rc, None

    # --- printf ---
    def fmt(self, f, a):
        if f is None:
            return None
        out = []
        i = 0
        pat = re.compile(r"%([-+ #0]*)(\d+|\*)?(?:\.(\d+))?(hh|h|ll|l|z|j|t)?([diuxXcspoe%])")
        while i < len(f):
            m = pat.match(f, i) if f[i] == "%" else None
            if not m:
                out.append(f[i])
                i += 1
                continue
            fl, wd, pr, ln, cv = m.groups()
            i = m.end()
            if cv == "%":
                out.append("%")
                continue
            if wd == "*":
                wd = str(a.u32())
            if ln == "ll":
                v = a.u64()
            else:
                v = a.u32()
            if cv in "di":
                sz = 64 if ln == "ll" else 32
                if v >= 1 << (sz - 1):
                    v -= 1 << sz
                if ln == "h":
                    v = ((v + 0x8000) & 0xffff) - 0x8000
            if cv == "s":
                s = self.cstr(v, 512)
                s = "(null)" if s is None else s
                spec = "%" + fl + (wd or "") + ("." + pr if pr else "") + "s"
                out.append(spec % s)
            elif cv == "p":
                out.append("0x%x" % v)
            elif cv == "c":
                out.append(chr(v & 0xff))
            else:
                spec = "%" + fl + (wd or "") + ("." + pr if pr else "") + cv
                out.append(spec % v)
        return "".join(out)

    # ------------------------------------------------------------------ execution
    def _exec(self, entry, args):
        uc = self.uc
        sp = STACK + STACK_SZ - 0x400
        regs = [A.UC_ARM_REG_R0, A.UC_ARM_REG_R1, A.UC_ARM_REG_R2, A.UC_ARM_REG_R3]
        stackargs = args[4:]
        sp -= (len(stackargs) * 4 + 7) & ~7
        for i, v in enumerate(stackargs):
            self.w32(sp + 4 * i, v)
        for r in (A.UC_ARM_REG_R4, A.UC_ARM_REG_R5, A.UC_ARM_REG_R6, A.UC_ARM_REG_R7, A.UC_ARM_REG_R8,
                  A.UC_ARM_REG_R9, A.UC_ARM_REG_R10, A.UC_ARM_REG_R11, A.UC_ARM_REG_R12):
            uc.reg_write(r, 0x11110000 + r)
        for i, r in enumerate(regs):
            uc.reg_write(r, args[i] & 0xffffffff if i < len(args) else 0)
        uc.reg_write(A.UC_ARM_REG_SP, sp)
        uc.reg_write(A.UC_ARM_REG_LR, RET_MAGIC | 1)
        uc.reg_write(A.UC_ARM_REG_CPSR, uc.reg_read(A.UC_ARM_REG_CPSR) | 0x20)
        self.fault = None
        try:
            uc.emu_start(entry | 1, RET_MAGIC, count=MAX_INSNS)
        except UcError as e:
            self.fault = "uc:%s" % e
        else:
            if self.fault is None and uc.reg_read(A.UC_ARM_REG_PC) != RET_MAGIC and \
                    uc.reg_read(A.UC_ARM_REG_PC) != RET_MAGIC + 2:
                # 達到指令上限或被 stub 中止
                if uc.reg_read(A.UC_ARM_REG_PC) not in (RET_MAGIC, RET_MAGIC + 2):
                    self.fault = self.fault or "insn_limit"
        r0 = uc.reg_read(A.UC_ARM_REG_R0)
        r1 = uc.reg_read(A.UC_ARM_REG_R1)
        csr = {r: uc.reg_read(r) for r in (A.UC_ARM_REG_R4, A.UC_ARM_REG_R5, A.UC_ARM_REG_R6, A.UC_ARM_REG_R7,
                                          A.UC_ARM_REG_R8, A.UC_ARM_REG_R9, A.UC_ARM_REG_R10, A.UC_ARM_REG_R11)}
        self.csr_ok = all(v == 0x11110000 + r for r, v in csr.items()) or self.fault is not None
        return r0, r1

    def call(self, name, *args, ret64=False, label=None, dump=()):
        """呼叫匯出函數；記錄 (label, ret, fault, events 起訖) 與測試記憶體快照。"""
        if isinstance(name, str):
            if name not in self.exports:
                raise Fault("no export " + name)
            entry = BASE + self.exports[name]
        else:
            entry = name
        e0 = len(self.events)
        r0, r1 = self._exec(entry, list(args))
        ret = self.norm(r0) if not ret64 else (r0, r1)
        evs = self.events[e0:]
        o = {"call": label or (name if isinstance(name, str) else hex(name)), "ret": ret,
             "fault": self.fault, "events": evs, "csr_ok": self.csr_ok}
        if dump:
            o["dump"] = [self.snap_words(p, n) for p, n in dump]
        self.obs.append(o)
        return r0

    def warm(self, hot=False):
        """先觸發一次惰性初始化（cammw_util_init），之後的事件/堆索引與初始化噪音脫鉤。"""
        o = self.alloc(0x70)
        self._exec(BASE + self.exports["cammw_util_shmem_alloc_buf"], [2, 0, 1, o])
        if hot:
            sv = (self.w.get("alloc_fmt"), self.w.get("flex"))
            self.w["alloc_fmt"] = 0x21
            self.w["flex"] = None
            self._exec(BASE + self.exports["cammw_util_shmem_alloc_buf"], [1, 0, 0x1000, o])
            self._exec(BASE + self.exports["cammw_util_shmem_free_buf"], [o])
            if sv[0] is None:
                self.w.pop("alloc_fmt", None)
            else:
                self.w["alloc_fmt"] = sv[0]
            self.w["flex"] = sv[1]
            if sv[1] is None:
                self.w.pop("flex", None)
        self.heap_base = len(self.allocs)
        self.events.clear()
        self.counts.clear()
        self.obs.clear()
        self.fault = None

    def dump_test(self):
        n = self.test_ptr - TEST
        return self.snap_words(TEST, n)

    def run_threads(self, which=None):
        """依序執行 pthread_create 登記的 routine（每個執行一次，腳本化 I/O 決定何時結束）。"""
        out = []
        pend = list(self.threads)
        self.threads = []
        for fn, arg, tid in pend:
            if which is not None and which(fn, arg) is False:
                continue
            e0 = len(self.events)
            r0, _ = self._exec(fn, [arg])
            out.append({"call": "thread#%x" % tid, "ret": self.norm(r0), "fault": self.fault,
                        "events": self.events[e0:]})
        self.obs.extend(out)
        return out

    def cb_stub(self, name, ret=0):
        self.cbs["cb." + name] = ret
        return self.stub("cb." + name)


class _VaMem:
    def __init__(self, m, p):
        self.m = m
        self.p = p

    def u32(self):
        v = self.m.r32(self.p)
        self.p += 4
        return v

    def u64(self):
        if self.p % 8:
            self.p += 4
        lo, hi = self.u32(), self.u32()
        return lo | (hi << 32)
