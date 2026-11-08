#!/usr/bin/env python3
"""libimageprocessorjni 專用 Unicorn 差分模擬 harness（emu.py 的強化版）。

重點：
  * 真實的 JNIEnv / JavaVM 函數表（每個 JNI 函數一個具名 stub，依簽名解 varargs）
  * libc / libutils(VectorImpl, SortedVectorImpl) / libgui(Surface) / cacao client 的行為模型
  * 假 ANativeWindow / ANativeWindowBuffer / native_handle / Cacao::Process 物件
  * 協同式 green-thread（pthread_create / cond_wait / join），可跑 video worker thread
  * 追蹤事件正規化：堆積位址以「首次出現順序」標號，與配置順序無關
"""
import bisect
import hashlib
import io
import lzma
import os
import random
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from elftools.elf.elffile import ELFFile
from unicorn import (UC_ARCH_ARM, UC_ARCH_ARM64, UC_HOOK_BLOCK, UC_HOOK_CODE, UC_MODE_ARM, UC_MODE_THUMB,
                     UC_PROT_ALL, Uc, UcError)
from unicorn import arm_const as A
from unicorn import arm64_const as A64

from emu import SoImage

BASE = 0x10000000
ENV_BASE = 0x20000000
ENV_SZ = 0x800000
STK_BASE = 0x30000000
STK_SZ = 0x100000
MAX_THREADS = 8
HEAP_BASE = 0x40000000
HEAP_SZ = 0x4000000
TLS_BASE = 0x60000000
TLS_SZ = 0x2000
STUB_BASE = 0x70000000
STUB_SZ = 0x40000
RET_MAGIC = 0x7f000000
MAX_INSNS = 3000000

JNI_NAMES = None


def _jni_names():
    global JNI_NAMES
    if JNI_NAMES is None:
        names = ["reserved0", "reserved1", "reserved2", "reserved3", "GetVersion", "DefineClass", "FindClass"]
        p = "/home/h/Android/Sdk/ndk/21.4.7075529/sysroot/usr/include/jni.h"
        t = open(p).read()
        i = t.index("struct JNINativeInterface {")
        j = t.index("};", i)
        names = [a or b for a, b in re.findall(r"\(\*\s*(\w+)\)|void\s*\*\s*(reserved\d)", t[i:j])]
        JNI_NAMES = names
    return JNI_NAMES


def _jni_ret_kind(name):
    """JNI 函數名 -> 回傳型別 (v/i/l/d/p)。"""
    if name.startswith("Call") or name.startswith("CallStatic") or name.startswith("CallNonvirtual"):
        m = re.match(r"Call(?:Static|Nonvirtual)?(\w+?)Method[VA]?$", name)
        t = m.group(1)
        return {"Void": "v", "Object": "p", "Boolean": "i", "Byte": "i", "Char": "i", "Short": "i",
                "Int": "i", "Long": "l", "Float": "d", "Double": "d"}[t]
    return None


class Lib:
    """載入 .so（含 .gnu_debugdata 內的 local 符號）。"""

    def __init__(self, path):
        self.path = path
        self.img = SoImage(path)
        self.is64 = self.img.is64
        self.w = 8 if self.is64 else 4
        self.size = (self.img.size + 0xfff) & ~0xfff
        self.syms = {}      # 名稱 -> (addr(含thumb bit), size)
        self.exports = set()
        self.dynsyms = {}   # 名稱 -> (addr, size, type)
        e = self.img.elf
        dyn = e.get_section_by_name(".dynsym")
        for s in dyn.iter_symbols():
            if s["st_shndx"] != "SHN_UNDEF" and s["st_value"]:
                self.dynsyms[s.name] = (s["st_value"], s["st_size"], s["st_info"]["type"])
                if s["st_info"]["type"] == "STT_FUNC" and s["st_size"] > 0:
                    self.syms[s.name] = (s["st_value"], s["st_size"])
                    self.exports.add(s.name)
        dd = e.get_section_by_name(".gnu_debugdata")
        self.localdata = {}
        if dd is not None:
            e2 = ELFFile(io.BytesIO(lzma.decompress(dd.data())))
            st = e2.get_section_by_name(".symtab")
            for s in st.iter_symbols():
                if s["st_info"]["type"] == "STT_FUNC" and s["st_size"] > 0:
                    self.syms.setdefault(s.name, (s["st_value"], s["st_size"]))
                elif s["st_info"]["type"] == "STT_OBJECT" and s["st_size"] > 0:
                    self.localdata[s.name] = (s["st_value"], s["st_size"])
        # 位址 -> 函數名 (排序)
        items = sorted((a & ~1, n) for n, (a, sz) in self.syms.items())
        self._starts = [a for a, n in items]
        self._names = [n for a, n in items]
        self._sizes = {n: sz for n, (a, sz) in self.syms.items()}
        self.text_lo = min(a for a, _ in items)
        self.text_hi = max((a & ~1) + self._sizes[n] for a, n in items)

    def func_at(self, off):
        """lib 內偏移 -> (函數名, 函數內偏移) 或 None"""
        i = bisect.bisect_right(self._starts, off) - 1
        if i < 0:
            return None
        n = self._names[i]
        if off - self._starts[i] < self._sizes[n] + 8:
            return n, off - self._starts[i]
        return None

    def name_at_exact(self, off):
        i = bisect.bisect_left(self._starts, off & ~1)
        if i < len(self._starts) and self._starts[i] == (off & ~1):
            return self._names[i]
        return None


# ------------------------------------------------------------------ 參數配置 (AAPCS)
def layout_args(is64, spec):
    """spec: 字串，每字元一個參數 (p=指標/字長, i=int32, l=int64, d=double)。
    回傳 [(kind, loc)]; loc=('r',idx) | ('s',off) | ('r2',idx) | ('v',idx)。"""
    out = []
    if is64:
        ngrn = nsrn = 0
        nsaa = 0
        for c in spec:
            if c == "d":
                if nsrn < 8:
                    out.append((c, ("v", nsrn)))
                    nsrn += 1
                    continue
            else:
                if ngrn < 8:
                    out.append((c, ("r", ngrn)))
                    ngrn += 1
                    continue
            out.append((c, ("s", nsaa)))
            nsaa += 8
    else:
        ncrn = 0
        nsaa = 0
        for c in spec:
            big = c in "ld"
            if big and ncrn % 2:
                ncrn += 1
            if ncrn + (2 if big else 1) <= 4:
                out.append((c, ("r2", ncrn) if big else ("r", ncrn)))
                ncrn += 2 if big else 1
                continue
            ncrn = 4
            if big and nsaa % 8:
                nsaa += 4
            out.append((c, ("s2", nsaa) if big else ("s", nsaa)))
            nsaa += 8 if big else 4
    return out


class Thread:
    def __init__(self, tid, stack_top, tls):
        self.tid = tid
        self.sp0 = stack_top
        self.tls = tls
        self.ctx = None
        self.state = "unused"
        self.start = None       # (addr, arg)
        self.resume_pc = None
        self.wait = None        # ('cond', addr) / ('join', tid)
        self.retval = 0
        self.is_main = False
        self.pending = None


class Fault(Exception):
    pass


class Machine:
    def __init__(self, lib: Lib, seed=0, policy=None):
        self.lib = lib
        self.is64 = lib.is64
        self.w = lib.w
        self.seed = seed
        self.rng = random.Random(seed)
        self.policy = policy or {}
        self.uc = Uc(UC_ARCH_ARM64, UC_MODE_ARM) if self.is64 else Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        if not self.is64:
            self.uc.ctl_set_cpu_model(A.UC_CPU_ARM_MAX)
        self.R = [getattr(A64 if self.is64 else A, ("UC_ARM64_REG_X%d" if self.is64 else "UC_ARM_REG_R%d") % i)
                  for i in range(31 if self.is64 else 13)]
        self.SP = A64.UC_ARM64_REG_SP if self.is64 else A.UC_ARM_REG_SP
        self.PC = A64.UC_ARM64_REG_PC if self.is64 else A.UC_ARM_REG_PC
        self.LR = A64.UC_ARM64_REG_X30 if self.is64 else A.UC_ARM_REG_LR
        self.events = []
        self.weak = []          # 弱通道：記憶體內容、配置大小等
        self.unmodeled = {}
        self.stubs = {}         # 名稱 -> addr
        self.stub_by_addr = {}
        self.stub_data = {}     # addr -> 附加資訊(如 vcall 類別/slot)
        self.env_ptr_alloc = ENV_BASE
        self.heap_ptr = HEAP_BASE
        self.allocs = []        # (start, size, kind) 依 start 排序
        self.alloc_starts = []
        self.labels = {}
        self.label_cnt = {}
        self.threads = []
        self.cur = None
        self.fault = None
        self.stop_reason = None
        self.ctx_ptr = None
        self.log_lines = []
        self.method_ids = {}    # id -> (cls, name, sig, static)
        self.field_ids = {}
        self.class_names = {}   # handle -> name
        self.objects = {}       # jobject handle -> desc
        self.strings = {}       # jstring handle -> python str
        self.next_handle = 0xA0000100
        self.guards = {}
        self.vimpl_log = True
        self.vtables = {}
        self.call_counts = {}
        self.insn_count = 0
        self.lazies = []
        self.mute = False
        self.cov = set()
        self._map()
        self._build_env()
        self._reloc()

    # ------------------------------------------------------------ 記憶體
    def _map(self):
        uc = self.uc
        uc.mem_map(BASE, self.lib.size + 0x2000, UC_PROT_ALL)
        for v, m, data in self.lib.img.segs:
            uc.mem_write(BASE + v, bytes(data))
        uc.mem_map(ENV_BASE, ENV_SZ, UC_PROT_ALL)
        uc.mem_map(STK_BASE, STK_SZ * MAX_THREADS, UC_PROT_ALL)
        uc.mem_map(HEAP_BASE, HEAP_SZ, UC_PROT_ALL)
        uc.mem_map(TLS_BASE, TLS_SZ * MAX_THREADS, UC_PROT_ALL)
        uc.mem_map(STUB_BASE, STUB_SZ, UC_PROT_ALL)
        uc.mem_map(RET_MAGIC, 0x1000, UC_PROT_ALL)
        if self.is64:
            nop = b"\x1f\x20\x03\xd5"
        else:
            nop = b"\x00\xbf\x00\xbf"
        uc.mem_write(STUB_BASE, nop * (STUB_SZ // 4))
        uc.mem_write(RET_MAGIC, nop * 8)
        uc.hook_add(UC_HOOK_CODE, self._stub_hook, begin=STUB_BASE, end=STUB_BASE + STUB_SZ)
        uc.hook_add(UC_HOOK_CODE, self._ret_hook, begin=RET_MAGIC, end=RET_MAGIC + 0x1000)
        uc.hook_add(UC_HOOK_BLOCK, self._blk_hook, begin=BASE, end=BASE + self.lib.size)
        if self.is64:
            uc.reg_write(A64.UC_ARM64_REG_CPACR_EL1, 0x300000)
        else:
            uc.reg_write(A.UC_ARM_REG_C1_C0_2, 0xf00000)
            uc.reg_write(A.UC_ARM_REG_FPEXC, 0x40000000)
        # 主執行緒
        for i in range(MAX_THREADS):
            th = Thread(i, STK_BASE + STK_SZ * (i + 1) - 0x100, TLS_BASE + TLS_SZ * i)
            self.threads.append(th)
            # TLS canary
            self.uc.mem_write(th.tls + 0x28, struct.pack("<Q", 0x5eed5eedcafef00d))
        self.threads[0].is_main = True

    def rd(self, addr, n):
        return bytes(self.uc.mem_read(addr, n))

    def wr(self, addr, data):
        self.uc.mem_write(addr, bytes(data))

    def rdw(self, addr):
        return int.from_bytes(self.rd(addr, self.w), "little")

    def wrw(self, addr, v):
        self.wr(addr, (v & ((1 << (8 * self.w)) - 1)).to_bytes(self.w, "little"))

    def rd32(self, addr):
        return int.from_bytes(self.rd(addr, 4), "little")

    def wr32(self, addr, v):
        self.wr(addr, (v & 0xffffffff).to_bytes(4, "little"))

    def rdstr(self, addr, maxn=300):
        if not addr:
            return None
        out = b""
        try:
            while len(out) < maxn:
                c = self.rd(addr + len(out), 1)
                if c == b"\0":
                    break
                out += c
        except UcError:
            return "<bad:%x>" % addr
        return out.decode("utf-8", "replace")

    def env_alloc(self, size, kind="env", fill=None):
        size = (size + 15) & ~15
        p = self.env_ptr_alloc
        self.env_ptr_alloc += size
        assert self.env_ptr_alloc < ENV_BASE + ENV_SZ
        self._register_alloc(p, size, kind, env=True)
        return p

    def _register_alloc(self, p, size, kind, env=False):
        i = bisect.bisect_left(self.alloc_starts, p)
        self.alloc_starts.insert(i, p)
        self.allocs.insert(i, (p, size, kind, env))

    def malloc(self, n, kind="H"):
        n = max((n + 15) & ~15, 16)
        p = self.heap_ptr
        self.heap_ptr += n + 16
        if self.heap_ptr > HEAP_BASE + HEAP_SZ:
            raise Fault("heap exhausted")
        self._register_alloc(p, n, kind)
        if self.policy.get("fill") is not None and kind in ("H", "obj"):
            self.wr(p, bytes([self.policy["fill"]]) * n)
        return p

    # ------------------------------------------------------------ 正規化
    def norm(self, v, depth=0):
        """位址 -> 可比較的標籤。"""
        if v is None:
            return None
        if v == 0:
            return 0
        if HEAP_BASE <= v < HEAP_BASE + HEAP_SZ or ENV_BASE <= v < ENV_BASE + ENV_SZ:
            i = bisect.bisect_right(self.alloc_starts, v) - 1
            if i >= 0:
                s, sz, kind, env = self.allocs[i]
                if v - s <= sz + 16:
                    lab = self.labels.get(s)
                    if lab is None:
                        k = "H" if not env else kind
                        c = self.label_cnt.get(k, 0) + 1
                        self.label_cnt[k] = c
                        lab = "%s%d" % (k, c)
                        self.labels[s] = lab
                    off = v - s
                    return lab if off == 0 else "%s+%d" % (lab, off)
            return "env?"
        if STK_BASE <= v < STK_BASE + STK_SZ * MAX_THREADS:
            return "STK"
        if STUB_BASE <= v < STUB_BASE + STUB_SZ:
            return "S:" + self.stub_by_addr.get(v & ~1, "?")
        if BASE <= v < BASE + self.lib.size:
            off = v - BASE
            if self.ctx_ptr and self.ctx_ptr <= v < self.ctx_ptr + 0x1000:
                return "CTX" if v == self.ctx_ptr else "CTX+"
            if self.lib.text_lo <= off < self.lib.text_hi:
                n = self.lib.name_at_exact(off)
                if n:
                    return "F:" + self._canon(n)
                return "CODE"
            return "IMG"
        if TLS_BASE <= v < TLS_BASE + TLS_SZ * MAX_THREADS:
            return "TLS"
        if v >= 0xA0000000 and v < 0xA1000000:
            return self.hname(v)
        if v == RET_MAGIC:
            return "RET"
        return v

    def hname(self, h):
        if h in self.class_names:
            return "CLS:" + self.class_names[h]
        if h in self.strings:
            return "STR:" + self.strings[h]
        if h in self.objects:
            return self.objects[h]
        return "H?%x" % h

    @staticmethod
    def _canon(n):
        n = re.sub(r"^_ZN14imageprocessorL", "_ZN14imageprocessor", n)
        n = n.replace("_ZL", "_Z")
        return n

    def ev(self, chan, *items):
        if self.mute:
            return
        self.events.append((chan,) + tuple(items))

    # ------------------------------------------------------------ 環境建構
    def _build_env(self):
        # JNIEnv/JavaVM
        names = _jni_names()
        tab = self.env_alloc(self.w * 240, "jnitab")
        for i, n in enumerate(names):
            self.wrw(tab + i * self.w, self.stub("JNI_" + n))
        self.env_obj = self.env_alloc(self.w * 2, "JNIEnv")
        self.wrw(self.env_obj, tab)
        self.env_ptr = self.env_obj
        vm_names = ["reserved0", "reserved1", "reserved2", "DestroyJavaVM", "AttachCurrentThread",
                    "DetachCurrentThread", "GetEnv", "AttachCurrentThreadAsDaemon"]
        vtab = self.env_alloc(self.w * 8, "vmtab")
        for i, n in enumerate(vm_names):
            self.wrw(vtab + i * self.w, self.stub("VM_" + n))
        self.vm_obj = self.env_alloc(self.w * 2, "JavaVM")
        self.wrw(self.vm_obj, vtab)
        # 通用 vtable (給 Process/一般假物件)
        self.univ_vt = self._make_vtable("Obj", 96)
        # stack canary
        self.canary = self.env_alloc(16, "canary")
        self.wr(self.canary, struct.pack("<Q", 0x5eed5eedcafef00d))
        self.sF = self.env_alloc(0x400, "sF")
        # 各類 vtable
        self.vt_objectbase = self._make_vtable("ObjectBase", 8)
        self.vt_imagebuf = self._make_vtable("ImageBuf", 20)

    def _make_vtable(self, cls, nslots):
        base = self.env_alloc(self.w * (nslots + 2), "vt_" + cls)
        for k in range(nslots):
            a = self.stub("%s::v%d" % (cls, k))
            self.wrw(base + self.w * k, a)
        self.vtables[cls] = base
        return base

    def fake_obj(self, cls="Obj", size=0x100):
        p = self.env_alloc(size, cls)
        vt = self.vtables.get(cls)
        if vt is None:
            vt = self._make_vtable(cls, 48)
        self.wrw(p, vt)
        return p

    # ------------------------------------------------------------ stub 與重定位
    def stub(self, name):
        a = self.stubs.get(name)
        if a is None:
            a = STUB_BASE + 16 * (len(self.stubs) + 1)
            self.stubs[name] = a
            self.stub_by_addr[a] = name
        return a | (0 if self.is64 else 1)

    def _reloc(self):
        lib = self.lib
        elf = lib.img.elf
        dyn = elf.get_section_by_name(".dynsym")
        w = self.w
        for off, t, sym, add in lib.img.relocs:
            where = BASE + off
            cur = self.rdw(where)
            def put(v):
                self.wrw(where, v)
            if t == "RELR":
                put(cur + BASE)
            elif t in (23, 1027):       # RELATIVE
                put(BASE + (add if add is not None else cur))
            elif t in (21, 22, 1025, 1026):   # GLOB_DAT / JUMP_SLOT
                put(self._sym_addr(sym) + (add or 0 if t == 1025 else 0))
            elif t == 1031:             # TLSDESC
                self.wrw(where, self.stub("__tlsdesc"))
                self.wrw(where + 8, 0x100 + (add or 0))
            elif t == 17:               # TLS_DTPMOD32
                put(1)
            elif t == 18:               # TLS_DTPOFF32 (S + A)
                d = lib.dynsyms.get(sym)
                put((d[0] if d else 0) + cur)
            elif t in (2, 257):         # ABS32 / ABS64
                a = self._sym_addr(sym)
                put(a + (add if add is not None else cur))
            else:
                raise Fault("unknown reloc %r %r" % (t, sym))

    def _sym_addr(self, name):
        d = self.lib.dynsyms.get(name)
        if d is not None:
            return BASE + d[0]
        if name in ("__stack_chk_guard",):
            return self.canary
        if name == "__sF":
            return self.sF
        if name.startswith("_ZTV") or name.startswith("_ZTI") or name.startswith("_ZTS"):
            vt = self._make_vtable(name, 24)
            return vt
        return self.stub(name)

    # ------------------------------------------------------------ 暫存器 / 參數
    def get_args(self, spec):
        uc = self.uc
        lay = layout_args(self.is64, spec)
        sp = uc.reg_read(self.SP)
        out = []
        for c, loc in lay:
            k = loc[0]
            if k == "r":
                v = uc.reg_read(self.R[loc[1]])
            elif k == "v":
                v = uc.reg_read(getattr(A64, "UC_ARM64_REG_D%d" % loc[1]))
                if isinstance(v, tuple):
                    v = v[0]
            elif k == "r2":
                v = uc.reg_read(self.R[loc[1]]) | (uc.reg_read(self.R[loc[1] + 1]) << 32)
            elif k == "s":
                v = int.from_bytes(self.rd(sp + loc[1], 8 if self.is64 else 4), "little")
            else:
                v = int.from_bytes(self.rd(sp + loc[1], 8), "little")
            if c == "i":
                v &= 0xffffffff
            elif c == "d":
                pass
            elif c == "p":
                v &= (1 << (8 * self.w)) - 1
            out.append(v)
        return out

    def set_args(self, spec, vals):
        uc = self.uc
        lay = layout_args(self.is64, spec)
        sp = uc.reg_read(self.SP)
        # 先計算 stack 區大小
        smax = 0
        for (c, loc), v in zip(lay, vals):
            if loc[0] in ("s", "s2"):
                smax = max(smax, loc[1] + (8 if loc[0] == "s2" or self.is64 else 4))
        sp -= (smax + 15) & ~15
        uc.reg_write(self.SP, sp)
        for (c, loc), v in zip(lay, vals):
            k = loc[0]
            if c == "d" and not isinstance(v, int):
                v = struct.unpack("<Q", struct.pack("<d", float(v)))[0]
            if k == "r":
                uc.reg_write(self.R[loc[1]], v & ((1 << (8 * self.w)) - 1))
            elif k == "v":
                uc.reg_write(getattr(A64, "UC_ARM64_REG_D%d" % loc[1]), v)
            elif k == "r2":
                uc.reg_write(self.R[loc[1]], v & 0xffffffff)
                uc.reg_write(self.R[loc[1] + 1], (v >> 32) & 0xffffffff)
            elif k == "s":
                self.wr(sp + loc[1], (v & ((1 << (8 * (8 if self.is64 else 4))) - 1)).to_bytes(8 if self.is64 else 4, "little"))
            else:
                self.wr(sp + loc[1], (v & ((1 << 64) - 1)).to_bytes(8, "little"))

    def ret_val(self, v, wide=False):
        uc = self.uc
        if v is None:
            v = 0
        if wide and not self.is64:
            uc.reg_write(self.R[0], v & 0xffffffff)
            uc.reg_write(self.R[1], (v >> 32) & 0xffffffff)
        else:
            uc.reg_write(self.R[0], v & ((1 << (8 * self.w)) - 1))

    # ------------------------------------------------------------ stub 執行
    def _stub_hook(self, uc, addr, size, ud):
        name = self.stub_by_addr.get(addr & ~1)
        if name is None:
            return
        lr = uc.reg_read(self.LR)
        self.call_counts[name] = self.call_counts.get(name, 0) + 1
        h = HANDLERS.get(name)
        if h is None:
            h = self._resolve_generic(name)
        try:
            r = h(self, name)
        except StopCall:
            return
        except UcError as e:
            self.fault = "stub-mem:%s:%s" % (name, e)
            uc.emu_stop()
            return
        if r is not None:
            wide = False
            if isinstance(r, tuple):
                r, wide = r
            self.ret_val(r, wide)
        self.do_return(lr)

    def do_return(self, lr):
        self.uc.reg_write(self.PC, lr)

    def _resolve_generic(self, name):
        base = name.split("@")[0]
        h = HANDLERS.get(base)
        if h:
            return h
        if name.startswith("JNI_"):
            return h_jni
        if name.startswith("VM_"):
            return h_vm
        if name.startswith("Surface+"):
            return _surface_stub
        if name.startswith("anwb+"):
            return _anwb_stub
        if "::v" in name:
            return h_vcall
        self.unmodeled[name] = self.unmodeled.get(name, 0) + 1
        return h_default

    def _blk_hook(self, uc, addr, size, ud):
        self.cov.add(addr)

    def _ret_hook(self, uc, addr, size, ud):
        th = self.cur
        th.state = "done"
        th.retval = uc.reg_read(self.R[0])
        uc.emu_stop()

    # ------------------------------------------------------------ 執行 / 排程
    def _setup_thread(self, th, addr, args_spec, vals):
        uc = self.uc
        uc.reg_write(self.SP, th.sp0)
        if self.is64:
            uc.reg_write(A64.UC_ARM64_REG_TPIDR_EL0, th.tls)
            for i in range(31):
                uc.reg_write(self.R[i], 0)
            uc.reg_write(self.LR, RET_MAGIC)
            start = addr
        else:
            for i in range(13):
                uc.reg_write(self.R[i], 0)
            uc.reg_write(self.LR, RET_MAGIC)     # ARM mode ret (bx lr -> even)
            start = addr
        self.set_args(args_spec, vals)
        th.resume_pc = start

    def _run_thread(self, th):
        """跑到 done / blocked / fault。"""
        uc = self.uc
        prev = self.cur
        self.cur = th
        try:
            if th.ctx is not None and th.state == "runnable":
                uc.context_restore(th.ctx)
            th.state = "running"
            self.stop_reason = None
            try:
                uc.emu_start(th.resume_pc, 0, count=MAX_INSNS)
            except UcError as e:
                pc = uc.reg_read(self.PC)
                self.fault = "%s@%s" % (e, self._where(pc))
                th.state = "done"
                return "fault"
            if th.state == "running":
                # 未完成也未封鎖 -> 達到指令上限 或 stub 要求中斷
                if self.fault:
                    th.state = "done"
                    return "fault"
                th.state = "done"
                self.fault = "timeout"
                return "timeout"
            return th.state
        finally:
            self.cur = prev

    def _where(self, pc):
        if BASE <= pc < BASE + self.lib.size:
            f = self.lib.func_at(pc - BASE)
            return "%s+%d" % (f[0], f[1]) if f else "IMG+%x" % (pc - BASE)
        return "%x" % pc

    def service(self, fn, ret=0):
        """在 stub 內需要巢狀執行 guest 時：封鎖目前 thread，由排程迴圈代跑 fn 後再繼續。"""
        th = self.cur
        th.pending = fn
        lr = self.uc.reg_read(self.LR)
        self.block_current(("service",), lr, ret)
        raise StopCall()

    def _drive(self, th):
        while True:
            st = self._run_thread(th)
            if th.state == "blocked" and th.wait and th.wait[0] == "service":
                fn, th.pending = th.pending, None
                fn()
                th.state = "runnable"
                th.wait = None
                continue
            return st

    def block_current(self, wait, lr, ret=0):
        """stub 呼叫中：令目前 thread 封鎖，之後從 lr 繼續。"""
        th = self.cur
        self.ret_val(ret)
        self.uc.reg_write(self.PC, lr)
        th.ctx = self.uc.context_save()
        th.resume_pc = lr
        th.state = "blocked"
        th.wait = wait
        self.uc.emu_stop()

    def pump(self):
        """執行其他 runnable thread 直到全部封鎖/結束。"""
        guard = 0
        while guard < 200:
            guard += 1
            cand = [t for t in self.threads[1:] if t.state == "runnable"]
            if not cand:
                return
            t = cand[0]
            self._drive(t)
            if self.fault:
                return

    def wake(self, kind, key, all_=False):
        n = 0
        for t in self.threads:
            if t.state == "blocked" and t.wait and t.wait[0] == kind and t.wait[1] == key:
                t.state = "runnable"
                t.wait = None
                n += 1
                if not all_:
                    break
        return n

    def call(self, name_or_addr, spec, vals, label=None, record_ret=True):
        """從主執行緒呼叫 guest 函數，之後 pump 其他 thread。回傳 (ret, status)。"""
        if isinstance(name_or_addr, str):
            addr = BASE + self.lib.syms[name_or_addr][0]
        else:
            addr = BASE + name_or_addr
        th = self.threads[0]
        th.state = "new"
        th.ctx = None
        fl = self.policy.get("fill")
        if fl is not None:
            self.wr(th.sp0 - 0x40000, bytes([fl]) * 0x40000)
        self._setup_thread(th, addr, spec, vals)
        self.ev("call", label or (name_or_addr if isinstance(name_or_addr, str) else "?"))
        st = self._drive(th)
        # main 若在 cond_wait/join 封鎖：嘗試跑其他 thread 看能否喚醒
        guard = 0
        while th.state == "blocked" and guard < 50 and not self.fault:
            guard += 1
            self.pump()
            if th.state == "blocked" and th.wait and th.wait[0] == "join":
                tt = self.threads[th.wait[1]]
                if tt.state == "done":
                    th.state = "runnable"
            if th.state == "runnable":
                st = self._drive(th)
            else:
                if not any(t.state == "runnable" for t in self.threads[1:]):
                    break
        if th.state == "blocked":
            self.ev("status", "DEADLOCK-main")
            st = "deadlock"
        ret = th.retval if th.state == "done" else None
        if not self.fault and st != "deadlock":
            self.pump()
        if self.fault:
            self.ev("status", "FAULT:" + re.split(r"[ @(]", self.fault)[0] + ":" + (self.fault.split("(")[1].split(")")[0] if "(" in self.fault else ""))
        if record_ret:
            self.ev("ret", self.norm_ret(ret) if ret is not None else None)
        return ret, st

    def run_quiet(self, addr, spec, vals):
        """不記錄事件地在主執行緒空間跑一個 guest 函式 (供 serialize 等純函式使用)。"""
        th = self.threads[MAX_THREADS - 1]
        save_fault = self.fault
        self.mute = True
        th.state = "new"
        th.ctx = None
        self._setup_thread(th, addr, spec, vals)
        try:
            self._run_thread(th)
        finally:
            self.mute = False
        ok = th.state == "done" and not self.fault
        self.fault = save_fault
        return th.retval if ok else None

    def resolve_lazies(self):
        for lz in self.lazies:
            if lz.val is None:
                try:
                    lz.val = self._canon_obj(lz)
                except Exception as e:  # noqa
                    lz.val = ("ERR", repr(e)[:60])
        self.lazies = []

    def _canon_obj(self, lz):
        m = self
        w = self.w
        ptr, data = lz.ptr, lz.data
        if lz.kind == "vec":
            storage = int.from_bytes(data[w:2 * w], "little")
            cnt = int.from_bytes(data[2 * w:3 * w], "little")
            items = []
            if storage and cnt < 64:
                for k in range(cnt):
                    try:
                        items.append(m.norm(m.rdw(storage + k * w)))
                    except UcError:
                        items.append("?")
            return ("VEC", cnt, tuple(items))
        vt0 = int.from_bytes(data[:w], "little")
        cname = m.class_of(ptr)
        cands = []
        if BASE <= vt0 < BASE + self.lib.size:
            cands.append((vt0, 0))
            vt1 = int.from_bytes(data[w:2 * w], "little")
            if BASE <= vt1 < BASE + self.lib.size:
                cands.append((vt1, w))
        for vt, adj in cands:
            for k in range(0, 14):
                try:
                    f = m.rdw(vt + k * w)
                except UcError:
                    break
                if not (BASE <= f < BASE + self.lib.size):
                    continue
                fn = self.lib.func_at((f & ~1) - BASE)
                if fn and re.search(r"9serializeEPN", fn[0]):
                    scratch = m.env_alloc(len(data) + 32, "scratch")
                    m.wr(scratch, data)
                    sd = m.env_alloc(0x1a0, "sd")
                    buf = m.env_alloc(0x2000, "sdbuf")
                    m.wr32(sd + 0x184, 0x2000)
                    m.wrw(sd + 0x188, buf)
                    m.wr32(sd + 0x18c, 0)
                    r = m.run_quiet(f, "pp", [scratch + adj, sd])
                    off = m.rd32(sd + 0x18c)
                    if r is not None and r < 0x80000000 and off <= 0x2000:
                        return ("SER", cname, bytes(m.rd(buf, off)).hex())
        words = []
        for i in range(0, min(len(data), 0x40) - w + 1, w):
            v = int.from_bytes(data[i:i + w], "little")
            words.append(m.norm(v) if v > 0xffff else v)
        return ("RAW", cname, tuple(words))

    def norm_ret(self, v):
        return self.norm(v)

    # ------------------------------------------------------------ vtable 呼叫 (guest 內的虛擬函式)
    def guest_vslot(self, obj, slot):
        vt = self.rdw(obj)
        return self.rdw(vt + slot * self.w)


class StopCall(Exception):
    pass


# ====================================================================== handlers
HANDLERS = {}


def H(*names):
    def deco(f):
        for n in names:
            HANDLERS[n] = f
        return f
    return deco


def pol(m, key, choices, p=None, rand=False):
    """policy 抽樣：以 (seed,key,第n次) 做雜湊，與全域呼叫順序無關。
    happy 模式下，非 rand 的抽樣一律取 choices[0]（成功路徑）。"""
    if m.policy.get("happy") and not rand:
        return choices[0]
    n = m.call_counts.get("_pol_" + key, 0) + 1
    m.call_counts["_pol_" + key] = n
    d = hashlib.md5(("%d:%s:%d" % (m.seed, key, n)).encode()).digest()
    x = int.from_bytes(d[:4], "little") / 2 ** 32
    if p is None:
        return choices[int.from_bytes(d[4:8], "little") % len(choices)]
    acc = 0
    for c, pp in zip(choices, p):
        acc += pp
        if x < acc:
            return c
    return choices[-1]


def h_default(m, name):
    a = m.get_args("pppp")
    m.ev("call", "UNMODELED:" + name, tuple(m.norm(x) for x in a))
    return 0


# ---- 記憶體配置
@H("_Znwj", "_Znwm", "_Znaj", "_Znam")
def h_new(m, name):
    (n,) = m.get_args("p")
    m.weak.append(("new", n))
    return m.malloc(n)


@H("_ZdlPv", "_ZdaPv", "free")
def h_delete(m, name):
    (p,) = m.get_args("p")
    m.ev("free", m.norm(p))
    return 0


@H("malloc")
def h_malloc(m, name):
    (n,) = m.get_args("p")
    return m.malloc(n)


@H("calloc")
def h_calloc(m, name):
    a, b = m.get_args("pp")
    return m.malloc(a * b)


@H("memcpy", "memmove", "__aeabi_memcpy", "__aeabi_memcpy4", "__aeabi_memcpy8", "__aeabi_memmove",
   "__aeabi_memmove4", "__aeabi_memmove8")
def h_memcpy(m, name):
    d, s, n = m.get_args("ppp")
    if n and n < 0x100000:
        m.wr(d, m.rd(s, n))
    m.weak.append(("memcpy", n))
    return d


@H("memset")
def h_memset(m, name):
    d, c, n = m.get_args("pip")
    if n and n < 0x100000:
        m.wr(d, bytes([c & 0xff]) * n)
    m.weak.append(("memset", c & 0xff, n))
    return d


@H("__aeabi_memset", "__aeabi_memset4", "__aeabi_memset8")
def h_aeabi_memset(m, name):
    d, n, c = m.get_args("ppi")
    if n and n < 0x100000:
        m.wr(d, bytes([c & 0xff]) * n)
    m.weak.append(("memset", c & 0xff, n))
    return d


@H("__aeabi_memclr", "__aeabi_memclr4", "__aeabi_memclr8")
def h_aeabi_memclr(m, name):
    d, n = m.get_args("pp")
    if n and n < 0x100000:
        m.wr(d, b"\0" * n)
    m.weak.append(("memset", 0, n))
    return 0


@H("strcmp")
def h_strcmp(m, name):
    a, b = m.get_args("pp")
    sa, sb = m.rdstr(a), m.rdstr(b)
    m.ev("call", "strcmp", sa, sb)
    return (sa > sb) - (sa < sb)


@H("strncpy")
def h_strncpy(m, name):
    d, s, n = m.get_args("ppp")
    src = (m.rdstr(s, n) or "").encode()[:n]
    m.wr(d, src + b"\0" * (n - len(src)))
    m.ev("call", "strncpy", m.norm(d), src.decode("utf-8", "replace"), n)
    return d


@H("strlen")
def h_strlen(m, name):
    (s,) = m.get_args("p")
    return len((m.rdstr(s) or "").encode())


@H("__errno")
def h_errno(m, name):
    if not hasattr(m, "errno_p"):
        m.errno_p = m.env_alloc(8, "errno")
    return m.errno_p


@H("abort", "__libcpp_verbose_abort", "_ZNSt3__122__libcpp_verbose_abortEPKcz", "__cxa_pure_virtual",
   "__stack_chk_fail", "__cxa_throw", "__cxa_bad_cast", "_Unwind_Resume", "__cxa_call_unexpected",
   "_ZSt28__throw_bad_array_new_lengthB8nn190000v", "__cxa_rethrow", "terminate")
def h_abort(m, name):
    m.ev("status", "ABORT:" + name)
    m.fault = "abort:" + name
    m.uc.emu_stop()
    raise StopCall()


@H("__cxa_atexit", "__cxa_finalize", "__register_atfork", "__cxa_end_catch", "__cxa_begin_catch")
def h_zero(m, name):
    return 0


@H("__cxa_guard_acquire")
def h_guard_acq(m, name):
    (g,) = m.get_args("p")
    if m.rd(g, 1) != b"\0":
        return 0
    m.ev("guard", "acquire")
    return 1


@H("__cxa_guard_release")
def h_guard_rel(m, name):
    (g,) = m.get_args("p")
    m.wr(g, b"\x01")
    return 0


@H("close")
def h_close(m, name):
    (fd,) = m.get_args("i")
    m.ev("call", "close", fd)
    return 0


@H("setpriority")
def h_setprio(m, name):
    a = m.get_args("iii")
    m.ev("call", "setpriority", tuple(a))
    return 0


@H("__tlsdesc")
def h_tlsdesc(m, name):
    (d,) = m.get_args("p")
    return m.rdw(d + m.w)


@H("__tls_get_addr")
def h_tls_get_addr(m, name):
    (ti,) = m.get_args("p")
    off = m.rdw(ti + m.w)
    return m.cur.tls + 0x100 + off


@H("fflush", "fprintf", "dladdr", "dl_iterate_phdr", "_Unwind_Backtrace", "pthread_attr_init",
   "pthread_attr_setdetachstate", "pthread_attr_destroy")
def h_misc_zero(m, name):
    return 0


# ---- pthread
@H("pthread_mutex_init", "pthread_mutex_destroy", "pthread_mutex_lock", "pthread_mutex_unlock",
   "pthread_cond_init", "pthread_cond_destroy")
def h_pt_sync(m, name):
    (p,) = m.get_args("p")
    m.ev("sync", name, "T%d" % m.cur.tid)
    return 0


@H("pthread_cond_signal", "pthread_cond_broadcast")
def h_pt_signal(m, name):
    (p,) = m.get_args("p")
    m.ev("sync", name, "T%d" % m.cur.tid)
    m.wake("cond", p, all_=(name == "pthread_cond_broadcast"))
    return 0


@H("pthread_cond_wait")
def h_pt_cwait(m, name):
    c, mu = m.get_args("pp")
    m.ev("sync", name, "T%d" % m.cur.tid)
    lr = m.uc.reg_read(m.LR)
    if m.cur.is_main:
        # 主執行緒：嘗試先讓其他 thread 跑；無法在 hook 內遞迴，所以封鎖
        pass
    m.block_current(("cond", c), lr)
    raise StopCall()


@H("pthread_create")
def h_pt_create(m, name):
    tp, attr, fn, arg = m.get_args("pppp")
    tid = None
    for t in m.threads[1:]:
        if t.start is None:
            tid = t.tid
            break
    if tid is None:
        return 11
    th = m.threads[tid]
    th.start = (fn, arg)
    if m.policy.get("fill") is not None:
        m.wr(th.sp0 - 0x40000, bytes([m.policy["fill"]]) * 0x40000)
    saved = m.uc.context_save()
    m._setup_thread(th, fn, "p", [arg])
    th.ctx = m.uc.context_save()
    m.uc.context_restore(saved)
    th.state = "runnable"
    m.wrw(tp, 0x7000 + tid)
    m.ev("thread", "create", m.norm(fn), m.norm(arg))
    return 0


@H("pthread_join")
def h_pt_join(m, name):
    t, rv = m.get_args("pp")
    tid = (t & 0xfff) if t else 0
    m.ev("sync", name, "T%d" % m.cur.tid)
    lr = m.uc.reg_read(m.LR)
    if 0 < tid < len(m.threads):
        tt = m.threads[tid]
        if tt.state != "done":
            m.block_current(("join", tid), lr)
            raise StopCall()
    return 0


@H("pthread_exit")
def h_pt_exit(m, name):
    m.cur.state = "done"
    m.ev("thread", "exit", "T%d" % m.cur.tid)
    m.uc.emu_stop()
    raise StopCall()


# ---- android log / printf
def vfmt(m, fmt, va):
    out = []
    i = 0
    while i < len(fmt):
        c = fmt[i]
        if c != "%":
            out.append(c)
            i += 1
            continue
        j = i + 1
        flags = ""
        while j < len(fmt) and fmt[j] in "-+ #0":
            flags += fmt[j]
            j += 1
        width = ""
        while j < len(fmt) and (fmt[j].isdigit() or fmt[j] == "*"):
            width += fmt[j]
            j += 1
        if width == "*":
            width = str(va("i"))
        prec = None
        if j < len(fmt) and fmt[j] == ".":
            j += 1
            prec = ""
            while j < len(fmt) and (fmt[j].isdigit() or fmt[j] == "*"):
                prec += fmt[j]
                j += 1
            if prec == "*":
                prec = str(va("i"))
        lm = ""
        while j < len(fmt) and fmt[j] in "hlzjtLq":
            lm += fmt[j]
            j += 1
        if j >= len(fmt):
            break
        cv = fmt[j]
        spec = "%" + flags + width + ("." + prec if prec is not None else "")
        if cv == "%":
            out.append("%")
        elif cv in "di":
            if lm in ("ll", "j", "q"):
                v = va("l")
                v = v - (1 << 64) if v >> 63 else v
            elif lm in ("l", "z", "t"):
                v = va("p")
                v = v - (1 << (8 * m.w)) if v >> (8 * m.w - 1) else v
            else:
                v = va("i")
                v = v - (1 << 32) if v >> 31 else v
            out.append((spec + "d") % v)
        elif cv in "uxXo":
            if lm in ("ll", "j", "q"):
                v = va("l")
            elif lm in ("l", "z", "t"):
                v = va("p")
            else:
                v = va("i")
            out.append((spec + cv.replace("u", "d")) % v)
        elif cv == "c":
            out.append(chr(va("i") & 0xff))
        elif cv == "s":
            p = va("p")
            s = m.rdstr(p) if p else "(null)"
            out.append((spec + "s") % s)
        elif cv == "p":
            p = va("p")
            out.append("<%s>" % (m.norm(p),))
        elif cv in "feEgG":
            v = va("d")
            d = struct.unpack("<d", struct.pack("<Q", v & ((1 << 64) - 1)))[0]
            out.append((spec + cv) % d)
        else:
            out.append(fmt[i:j + 1])
        i = j + 1
    return "".join(out)


class VaReader:
    """依 AAPCS 從 stub 呼叫的暫存器/堆疊讀 varargs。"""

    def __init__(self, m, nfixed_spec):
        self.m = m
        self.spec = nfixed_spec
        self.vals = []
        self.idx = 0
        # 先讀固定參數位置，之後逐一以 layout 延伸
        self.cur_spec = nfixed_spec

    def __call__(self, kind):
        m = self.m
        spec = self.cur_spec + kind
        v = m.get_args(spec)[-1]
        self.cur_spec = spec
        return v


@H("__android_log_print")
def h_logprint(m, name):
    prio, tag, fmt = m.get_args("ipp")
    f = m.rdstr(fmt)
    va = VaReader(m, "ipp")
    s = vfmt(m, f, va)
    m.ev("log", prio, m.rdstr(tag), s)
    return 1


@H("__vsnprintf_chk", "snprintf", "__snprintf_chk")
def h_snprintf(m, name):
    if name == "snprintf":
        d, n, fmt = m.get_args("ppp")
        va = VaReader(m, "ppp")
    elif name == "__snprintf_chk":
        d, n, fl, sz, fmt = m.get_args("ppiip")
        va = VaReader(m, "ppiip")
    else:
        m.ev("call", name)
        return 0
    s = vfmt(m, m.rdstr(fmt), va)
    b = s.encode()[: max(n - 1, 0)]
    if n:
        m.wr(d, b + b"\0")
    return len(s)


# ---- libutils VectorImpl / SortedVectorImpl 模型
def _vlayout(m):
    w = m.w
    return dict(vptr=0, storage=w, count=2 * w, flags=3 * w if not m.is64 else 3 * w, itemsize=0)


class VI:
    def __init__(self, m, this):
        self.m = m
        self.t = this
        w = m.w
        self.o_st = w
        self.o_cnt = 2 * w
        self.o_fl = 3 * w
        self.o_is = 4 * w if m.is64 else 4 * w
        # 32-bit: vptr0 storage4 count8 flags12 itemsize16 ; 64-bit: 0, 8, 16, 24, 32
        if m.is64:
            self.o_fl = 24
            self.o_is = 32
        else:
            self.o_fl = 12
            self.o_is = 16

    storage = property(lambda s: s.m.rdw(s.t + s.o_st), lambda s, v: s.m.wrw(s.t + s.o_st, v))
    count = property(lambda s: s.m.rdw(s.t + s.o_cnt), lambda s, v: s.m.wrw(s.t + s.o_cnt, v))
    isz = property(lambda s: s.m.rdw(s.t + s.o_is))

    def item(self, i):
        return self.m.rd(self.storage + i * self.isz, self.isz)

    def insert(self, idx, itembytes, n):
        m = self.m
        cnt, isz = self.count, self.isz
        old = [self.item(i) for i in range(cnt)]
        new = old[:idx] + [itembytes] * n + old[idx:]
        buf = m.malloc(max(isz * len(new), 16), "vec")
        m.wr(buf, b"".join(new))
        self.storage = buf
        self.count = len(new)
        return idx

    def remove(self, idx, n):
        cnt = self.count
        old = [self.item(i) for i in range(cnt)]
        new = old[:idx] + old[idx + n:]
        isz = self.isz
        buf = self.m.malloc(max(isz * len(new), 16), "vec")
        self.m.wr(buf, b"".join(new))
        self.storage = buf
        self.count = len(new)

    def key(self, b):
        return int.from_bytes(b[:4], "little")


@H("_ZN7android10VectorImplC2Ejj", "_ZN7android10VectorImplC2Emj", "_ZN7android16SortedVectorImplC2Ejj",
   "_ZN7android16SortedVectorImplC2Emj")
def h_vimpl_ctor(m, name):
    this, isz, fl = m.get_args("ppi")
    v = VI(m, this)
    v.storage = 0
    v.count = 0
    m.wr(this + v.o_fl, struct.pack("<I", fl))
    m.wrw(this + v.o_is, isz)
    m.ev("vec", "ctor", m.norm(this), isz, fl)
    return this


@H("_ZN7android10VectorImplD2Ev", "_ZN7android16SortedVectorImplD2Ev")
def h_vimpl_dtor(m, name):
    (this,) = m.get_args("p")
    v = VI(m, this)
    m.ev("vec", "dtor", m.norm(this), v.count)
    return 0


@H("_ZN7android10VectorImpl13finish_vectorEv")
def h_vimpl_finish(m, name):
    (this,) = m.get_args("p")
    v = VI(m, this)
    m.ev("vec", "finish", m.norm(this), v.count)
    v.storage = 0
    v.count = 0
    return 0


@H("_ZN7android10VectorImpl5clearEv")
def h_vimpl_clear(m, name):
    (this,) = m.get_args("p")
    v = VI(m, this)
    m.ev("vec", "clear", m.norm(this), v.count)
    v.storage = 0
    v.count = 0
    return 0


@H("_ZN7android10VectorImpl4pushEPKv")
def h_vimpl_push(m, name):
    this, item = m.get_args("pp")
    v = VI(m, this)
    ib = m.rd(item, v.isz) if item else b"\0" * v.isz
    m.ev("vec", "push", m.norm(this), _items_norm(m, ib))
    return v.insert(v.count, ib, 1)


@H("_ZN7android10VectorImpl8insertAtEPKvjj", "_ZN7android10VectorImpl8insertAtEPKvmm")
def h_vimpl_insert(m, name):
    this, item, idx, n = m.get_args("pppp")
    v = VI(m, this)
    ib = m.rd(item, v.isz) if item else b"\0" * v.isz
    m.ev("vec", "insertAt", m.norm(this), _items_norm(m, ib), idx, n)
    return v.insert(idx, ib, n)


@H("_ZN7android10VectorImpl13removeItemsAtEjj", "_ZN7android10VectorImpl13removeItemsAtEmm")
def h_vimpl_remove(m, name):
    this, idx, n = m.get_args("ppp")
    v = VI(m, this)
    m.ev("vec", "removeItemsAt", m.norm(this), idx, n)
    v.remove(idx, n)
    return idx


def _items_norm(m, ib):
    ws = [int.from_bytes(ib[i:i + m.w], "little") for i in range(0, len(ib) - m.w + 1, m.w)]
    return tuple(m.norm(x) if x > 0xffff else x for x in ws)


def _sorted_find(m, v, item):
    ib = m.rd(item, v.isz)
    k = v.key(ib)
    lo, hi = 0, v.count
    while lo < hi:
        mid = (lo + hi) // 2
        if v.key(v.item(mid)) < k:
            lo = mid + 1
        else:
            hi = mid
    found = lo < v.count and v.key(v.item(lo)) == k
    return lo, found, ib


@H("_ZN7android16SortedVectorImpl3addEPKv")
def h_svimpl_add(m, name):
    this, item = m.get_args("pp")
    v = VI(m, this)
    idx, found, ib = _sorted_find(m, v, item)
    m.ev("vec", "sadd", m.norm(this), _items_norm(m, ib), found)
    if found:
        v.remove(idx, 1)
    v.insert(idx, ib, 1)
    return idx


@H("_ZN7android16SortedVectorImpl6removeEPKv")
def h_svimpl_remove(m, name):
    this, item = m.get_args("pp")
    v = VI(m, this)
    idx, found, ib = _sorted_find(m, v, item)
    m.ev("vec", "sremove", m.norm(this), _items_norm(m, ib), found)
    if found:
        v.remove(idx, 1)
        return idx
    return (-2) & ((1 << (8 * m.w)) - 1)


@H("_ZNK7android16SortedVectorImpl7indexOfEPKv")
def h_svimpl_indexof(m, name):
    this, item = m.get_args("pp")
    v = VI(m, this)
    idx, found, ib = _sorted_find(m, v, item)
    m.ev("vec", "indexOf", m.norm(this), _items_norm(m, ib), found)
    return idx if found else (-2) & ((1 << (8 * m.w)) - 1)


# ---- RefBase / sp / IInterface
@H("_ZNK7android7RefBase9incStrongEPKv", "_ZNK7android7RefBase9decStrongEPKv")
def h_refbase(m, name):
    this, id_ = m.get_args("pp")
    m.ev("call", name.split("RefBase")[1][:12], m.norm(this))
    return 0


@H("_ZN7android14sp_report_raceEv")
def h_sp_race(m, name):
    m.ev("call", "sp_report_race")
    return 0


@H("_ZN7android10IInterface8asBinderERKNS_2spIS0_EE")
def h_asbinder(m, name):
    # 回傳 sp<IBinder>（物件回傳）：ARM32 以 r0 傳 sret；AArch64 以 x8
    if m.is64:
        sret = m.uc.reg_read(A64.UC_ARM64_REG_X8)
        (spi,) = m.get_args("p")
    else:
        sret, spi = m.get_args("pp")
    ptr = m.rdw(spi) if spi else 0
    binder = m.get_binder_for(ptr)
    m.wrw(sret, binder)
    m.ev("call", "IInterface::asBinder", m.norm(ptr))
    return sret


def _get_binder_for(self, ptr):
    if not hasattr(self, "_binders"):
        self._binders = {}
    if ptr not in self._binders:
        self._binders[ptr] = self.fake_obj("IBinder", 64)
    return self._binders[ptr]


Machine.get_binder_for = _get_binder_for


# ---- Surface / ANativeWindow 模型
def _fill_anw(m, p, size=0x100):
    """把 Surface 物件的 ANativeWindow 函式指標區填入具名 stub。"""
    for off in range(0, size, m.w):
        m.wrw(p + off, m.stub("Surface+0x%x" % off))
    # 少數欄位當資料：magic/version/flags 保持為 0
    if m.is64:
        for off in (0, 8, 56, 64, 72, 80):
            pass


@H("_ZN7android7SurfaceC1ERKNS_2spINS_22IGraphicBufferProducerEEEb",
   "_ZN7android7SurfaceC1ERKNS_2spINS_22IGraphicBufferProducerEEEbRKNS1_INS_7IBinderEEE")
def h_surface_ctor(m, name):
    a = m.get_args("pppip")
    this, spp, ctl = a[0], a[1], a[2] & 0xff
    prod = m.rdw(spp) if spp else 0
    extra = None
    if name.endswith("RKNS1_INS_7IBinderEEE"):
        extra = m.norm(m.rdw(a[3]) if False else a[3])
        ctl = a[2] & 0xff
    m.surface_init(this)
    m.surfaces[this] = prod
    m.ev("call", "Surface::ctor", m.norm(prod), ctl)
    return this


def _surface_init(self, this):
    if not hasattr(self, "surfaces"):
        self.surfaces = {}
    # 區域大小：RefBase(ptr*?) + ANativeWindow
    for off in range(0, 0x100, self.w):
        self.wrw(this + off, self.stub("Surface+0x%x" % off))


Machine.surface_init = _surface_init


@H("_ZNK7android7Surface25getIGraphicBufferProducerEv")
def h_surf_getprod(m, name):
    # 回傳 sp<IGraphicBufferProducer>（非 trivial 型別 -> sret）
    if m.is64:
        sret = m.uc.reg_read(A64.UC_ARM64_REG_X8)
        (this,) = m.get_args("p")
    else:
        sret, this = m.get_args("pp")
    if not hasattr(m, "surfaces"):
        m.surfaces = {}
    prod = m.surfaces.get(this)
    if prod is None:
        prod = m.fake_obj("IGBP", 64)
        m.surfaces[this] = prod
    m.wrw(sret, prod)
    m.ev("call", "Surface::getIGBP", m.norm(this))
    return sret


ANW_FUNCS = ["setSwapInterval", "dequeueBuffer_DEPRECATED", "lockBuffer_DEPRECATED", "queueBuffer_DEPRECATED",
             "query", "perform", "cancelBuffer_DEPRECATED", "dequeueBuffer", "queueBuffer", "cancelBuffer"]
ANW_ARGS = {"setSwapInterval": "i", "dequeueBuffer_DEPRECATED": "p", "lockBuffer_DEPRECATED": "p",
            "queueBuffer_DEPRECATED": "p", "query": "ip", "perform": "", "cancelBuffer_DEPRECATED": "p",
            "dequeueBuffer": "pp", "queueBuffer": "pi", "cancelBuffer": "pi"}
PERFORM_OPS = {0: "i", 1: "", 2: "", 3: "p", 4: "i", 5: "iii", 6: "i", 7: "l", 8: "ii", 9: "i", 10: "i",
               11: "pp", 12: "", 13: "i", 14: "i", 15: "ii", 16: "p", 17: "i", 18: "p", 19: "i", 20: "p",
               30: "l"}


def _surface_stub(m, name):
    """ANativeWindow 函式指標 stub；name = Surface+0xNN。"""
    off = int(name.split("+")[1], 16)
    base, step = m.anw_offs()
    fn = None
    if off >= base and (off - base) % step == 0 and (off - base) // step < len(ANW_FUNCS):
        fn = ANW_FUNCS[(off - base) // step]
    a = m.get_args("pppppp")
    win = a[0]
    if fn is None:
        m.ev("anw", name)
        return 0
    spec = ANW_ARGS[fn]
    if not hasattr(m, "pools"):
        m.pools = {}
    pool = m.pools.setdefault(win, {"all": [], "free": [], "count": 4})
    if fn == "perform":
        op = a[1] & 0xffffffff
        sp = "i" + PERFORM_OPS.get(op, "i")
        vals = m.get_args("p" + sp)[1:]
        m.ev("anw", fn, m.norm(win), tuple(m.norm(x) if (c == "p" and x > 0xffff) else x for c, x in zip(sp, vals)))
        if op == 4 and len(vals) > 1:
            pool["count"] = vals[1] & 0xffffffff
        return 0
    vals = m.get_args("p" + spec)[1:]
    m.ev("anw", fn, m.norm(win), tuple(m.norm(x) if (c == "p" and x > 0xffff) else x for c, x in zip(spec, vals)))
    if fn in ("dequeueBuffer", "dequeueBuffer_DEPRECATED"):
        if pol(m, "dequeue_ret", [0, 0xfffffff4]) != 0:
            return 0xfffffff4
        if pool["free"]:
            b = pool["free"].pop(0)
        elif len(pool["all"]) < max(pool["count"], 1):
            b = m.new_anwb()
            pool["all"].append(b)
        else:
            return 0xfffffff5          # -EAGAIN
        if vals[0]:
            m.wrw(vals[0], b)
        if fn == "dequeueBuffer" and len(vals) > 1 and vals[1]:
            m.wr32(vals[1], 0xffffffff)
        return 0
    if fn in ("cancelBuffer", "cancelBuffer_DEPRECATED", "queueBuffer", "queueBuffer_DEPRECATED"):
        b = vals[0]
        if b in pool["all"] and b not in pool["free"]:
            pool["free"].append(b)
        return 0
    if fn == "query":
        what, outp = vals[0] & 0xffffffff, vals[1]
        if outp:
            m.wr32(outp, (what * 7 + 13) % 29)
        return 0
    return 0


def _anwb_stub(m, name):
    m.ev("anwb", name)
    return 0


def _anw_offs(self):
    # 依 ABI：以 ANativeWindow 版面推算
    if self.is64:
        # common 56 + flags..oem -> setSwapInterval 112
        base = 128      # 實測: perform 在 0xa8 (= base + 5*8)
        step = 8
    else:
        base = 76       # 實測: perform 在 0x60 (= base + 5*4)
        step = 4
    return base, step


def _anw_dequeue_offs(self):
    base, step = _anw_offs(self)
    # dequeueBuffer_DEPRECATED = base+1*step ; dequeueBuffer = base+7*step
    return [base + 1 * step, base + 7 * step]


def _anw_query_offs(self):
    base, step = _anw_offs(self)
    return [base + 4 * step]


Machine.anw_offs = _anw_offs
Machine.anw_dequeue_offs = _anw_dequeue_offs
Machine.anw_query_offs = _anw_query_offs


def _new_anwb(self):
    # ANativeWindowBuffer 版面
    w = self.w
    p = self.env_alloc(0x100, "anwb")
    n = self.call_counts.get("_anwb", 0) + 1
    self.call_counts["_anwb"] = n
    if self.is64:
        o = dict(width=56, height=60, stride=64, format=68, usage_dep=72, layerCount=80, handle=96, usage=104)
    else:
        o = dict(width=32, height=36, stride=40, format=44, usage_dep=48, layerCount=52, handle=60, usage=64)
    wd = 640 + 16 * (n % 4)
    ht = 480 + 16 * (n % 3)
    self.wr32(p + o["width"], wd)
    self.wr32(p + o["height"], ht)
    self.wr32(p + o["stride"], wd + 32)
    self.wr32(p + o["format"], 0x11 if n % 2 else 0x23)
    self.wrw(p + o["layerCount"], 1)
    h = self.env_alloc(64, "nhandle")
    self.wr32(h, 12)
    self.wr32(h + 4, 1)
    self.wr32(h + 8, 2)
    self.wr32(h + 12, 100 + n)
    self.wrw(p + o["handle"], h)
    self.wr(p + o["usage"], struct.pack("<Q", 0x933))
    for off in range(0, 32 if not self.is64 else 56, self.w):
        self.wrw(p + off, self.stub("anwb+0x%x" % off))
    return p


Machine.new_anwb = _new_anwb


# ---- cacao client
@H("_ZN5cacao10ObjectBaseC2Ev")
def h_ob_ctor(m, name):
    (this,) = m.get_args("p")
    m.wrw(this, m.vt_objectbase)
    m.ev("call", "ObjectBase::ctor", m.norm(this))
    return this


@H("_ZN5cacao10ObjectBaseD2Ev")
def h_ob_dtor(m, name):
    (this,) = m.get_args("p")
    m.ev("call", "ObjectBase::dtor", m.norm(this))
    return this


@H("_ZN5cacao10ObjectBasenwEj", "_ZN5cacao10ObjectBasenwEm")
def h_ob_new(m, name):
    (n,) = m.get_args("p")
    m.weak.append(("ObjectBase::new", n))
    return m.malloc(n)


@H("_ZN5cacao10ObjectBasedlEPv")
def h_ob_del(m, name):
    (p,) = m.get_args("p")
    m.ev("free", m.norm(p))
    return 0


@H("_ZN5cacao10ObjectBase4dumpEj")
def h_ob_dump(m, name):
    this, f = m.get_args("pi")
    m.ev("call", "ObjectBase::dump", m.norm(this), f)
    return 0


@H("_ZN5cacao14ProcessFactory13createProcessEv")
def h_create_process(m, name):
    (this,) = m.get_args("p")
    ok = pol(m, "createProcess", [1, 0], [0.85, 0.15])
    m.ev("call", "createProcess", ok)
    if not ok:
        return 0
    p = m.fake_obj("Process", 0x100)
    m.process_obj = p
    return p


@H("_ZN5cacao14ProcessFactory17getJpegBufferSizeENS_9ImageSizeE")
def h_jpegsize(m, name):
    if m.is64:
        (sz,) = m.get_args("l")
        wd, ht = sz & 0xffffffff, sz >> 32
    else:
        wd, ht = m.get_args("ii")
    m.ev("call", "getJpegBufferSize", wd, ht)
    return pol(m, "jpegsize", [wd * ht, 0, 4096])


@H("_ZN5cacao22ProcessCtrlCapsFactory7getCapsERKNS_15ProcessCtrlCaps11CameraIndexEPNS_4CapsE")
def h_getcaps(m, name):
    idxp, caps = m.get_args("pp")
    idx = m.rd32(idxp) if idxp else None
    m.ev("call", "getCaps", idx)
    ok = pol(m, "getcaps", [0, 0, -1 & 0xffffffff], [0.8, 0.1, 0.1])
    if ok == 0 and caps:
        data = bytearray(0x262c)
        for i in range(0, 0x262c, 4):
            wi = i // 4
            v = ((wi * 2654435761 + m.seed * 97) >> 9) % 4      # 小整數(0..3)
            data[i:i + 4] = v.to_bytes(4, "little")

        def fill():
            # 以 Caps 自己的 deserialize (vtable) 填入，與 Caps 物件實際佈局無關
            vt0 = m.rdw(caps)
            cands = [(vt0, 0)]
            try:
                vt1 = m.rdw(caps + m.w)
                if BASE <= vt1 < BASE + m.lib.size:
                    cands.append((vt1, m.w))
            except UcError:
                pass
            for vt, adj in cands:
                for k in range(0, 14):
                    f = m.rdw(vt + k * m.w)
                    if not (BASE <= f < BASE + m.lib.size):
                        continue
                    fn = m.lib.func_at((f & ~1) - BASE)
                    if fn and "11deserializeEPN" in fn[0]:
                        sd = m.env_alloc(0x1a0, "sd")
                        buf = m.env_alloc(0x2700, "sdbuf")
                        m.wr(buf, bytes(data))
                        m.wr32(sd + 0x184, 0x262c)
                        m.wrw(sd + 0x188, buf)
                        m.wr32(sd + 0x18c, 0)
                        m.run_quiet(f, "pp", [caps + adj, sd])
                        return
            m.ev("status", "CAPS-NO-DESERIALIZE")
        m.service(fill, 0)
    return ok


@H("_ZN5cacao8ImageBufC1EPvNS_9ImageSizeENS_9DataSpaceENS_11ImageFormatE")
def h_imagebuf_ctor(m, name):
    if m.is64:
        this, data, sz, ds, fmt = m.get_args("pplii")
        wd, ht = sz & 0xffffffff, sz >> 32
    else:
        this, data, wd, ht, ds, fmt = m.get_args("ppiiii")
    m.wrw(this, m.vtables["ImageBuf"])
    m.wr(this + m.w, b"\0" * 0x30)
    m.imagebufs = getattr(m, "imagebufs", {})
    m.imagebufs[this] = (data, wd, ht, ds, fmt)
    m.ev("call", "ImageBuf::ctor", m.norm(this), m.norm(data), wd, ht, ds, fmt)
    return this


# ---- 虛擬函式 stub (Process / ImageBuf / ObjectBase / IBinder ...)
class Lazy:
    """延後解析的物件快照（需要在 guest 內呼叫 serialize）。"""
    __slots__ = ("ptr", "data", "val", "kind", "mask")

    def __init__(self, ptr, data, kind):
        self.ptr, self.data, self.kind, self.val = ptr, data, kind, None
        self.mask = None

    def __repr__(self):
        return "<%s %s>" % (self.kind, self.val)

    def __eq__(self, o):
        return isinstance(o, Lazy) and self.val == o.val

    def __hash__(self):
        return hash(self.val)


# Cacao(Process) vtable 各 slot 的參數型別: o=物件快照 p=指標 L=listener R=result V=Vector
PROC_ARGS = {2: "Lp", 3: "o", 4: "", 5: "o", 6: "o", 7: "oLR", 8: "oVLR", 9: "opLR", 10: "p"}


def snap(m, ptr, kind="obj", n=0x300):
    if not ptr or ptr <= 0xffff:
        return ptr
    try:
        data = m.rd(ptr, n)
    except UcError:
        try:
            data = m.rd(ptr, 0x40)
        except UcError:
            return m.norm(ptr)
    lz = Lazy(ptr, data, kind)
    m.lazies.append(lz)
    return lz


def h_vcall(m, name):
    cls, slot = name.split("::v")
    slot = int(slot)
    a = m.get_args("ppppppp")
    this = a[0]
    if cls == "Process":
        spec = PROC_ARGS.get(slot, "")
        args = []
        for ch, v in zip(spec, a[1:]):
            if ch == "o":
                args.append(snap(m, v, "obj"))
            elif ch == "V":
                args.append(snap(m, v, "vec", 0x20))
            elif ch == "L":
                args.append(("L", m.norm(v)))
            elif ch == "R":
                args.append(("R", m.norm(v), snap(m, v, "res", 0x80)))
            else:
                args.append(m.norm(v) if v > 0xffff else v)
        m.ev("vcall", cls, slot, m.norm(this), tuple(args))
        if not hasattr(m, "proc_args"):
            m.proc_args = []
        m.proc_args.append(a)
        r = pol(m, "P%d" % slot, [0, 0, 0, 1], [0.7, 0.1, 0.1, 0.1])
        return r
    if cls == "ImageBuf":
        m.ev("vcall", cls, slot, m.norm(this))
        if slot == 4:   # getNative
            return m.imagebuf_native(this)
        if slot in (5, 13):
            return 4096
        return 0
    m.ev("vcall", cls, slot, m.norm(this))
    if cls == "Obj":
        return pol(m, "O%d" % slot, [0, 1])
    return 0


def _class_of(self, p):
    """lib 內物件 -> 類別名 (由 vtable 內函式名推得)。"""
    if not p or p <= 0xffff:
        return None
    try:
        vt = self.rdw(p)
        if not (BASE <= vt < BASE + self.lib.size):
            return None
        for k in range(0, 8):
            f = self.rdw(vt + k * self.w)
            if BASE <= f < BASE + self.lib.size:
                fn = self.lib.func_at((f & ~1) - BASE)
                if fn:
                    mm = re.search(r"(?:_ZN|_ZNK|_ZThn\d+_NK?)(?:\d+imageprocessor)?(\d+)(\w+)", fn[0])
                    # 取類別名: 第一個 <len><name>
                    m2 = re.match(r"_Z(?:Thn\d+_)?N?K?(?:\d+imageprocessor)?(\d+)", fn[0])
                    t = fn[0]
                    t = re.sub(r"^_Z(?:Thn\d+_)?N?K?", "", t)
                    t = re.sub(r"^\d+imageprocessor", "", t)
                    mm = re.match(r"(\d+)", t)
                    if mm:
                        n = int(mm.group(1))
                        return t[len(mm.group(1)):len(mm.group(1)) + n]
    except UcError:
        return None
    return None


Machine.class_of = _class_of


def _imagebuf_native(self, this):
    if not hasattr(self, "_nat"):
        self._nat = {}
    if this not in self._nat:
        self._nat[this] = self.env_alloc(32, "nativebuf")
    return self._nat[this]


Machine.imagebuf_native = _imagebuf_native


# ---- JNI
def _new_handle(m, desc):
    h = m.next_handle
    m.next_handle += 8
    m.objects[h] = desc
    return h


def _jsig_spec(sig):
    args = sig[1:sig.index(")")]
    ret = sig[sig.index(")") + 1:]
    spec = ""
    i = 0
    while i < len(args):
        c = args[i]
        if c in "ZBCSI":
            spec += "i"
            i += 1
        elif c == "J":
            spec += "l"
            i += 1
        elif c in "FD":
            spec += "d"
            i += 1
        elif c == "L":
            spec += "p"
            i = args.index(";", i) + 1
        elif c == "[":
            while args[i] == "[":
                i += 1
            if args[i] == "L":
                i = args.index(";", i) + 1
            else:
                i += 1
            spec += "p"
        else:
            raise ValueError(sig)
    return spec, ret


def h_jni(m, name):
    jn = name[4:]
    lr = m.uc.reg_read(m.LR)
    # 約定: JNI_xxx(env, ...)
    if jn == "GetVersion":
        return 0x10006
    if jn == "FindClass":
        env, nm = m.get_args("pp")
        s = m.rdstr(nm)
        m.ev("jni", "FindClass", s)
        if pol(m, "FindClass:" + s, [1, 0], [0.93, 0.07]) == 0:
            return 0
        h = None
        for k, v in m.class_names.items():
            if v == s:
                h = k
        if h is None:
            h = m.next_handle
            m.next_handle += 8
            m.class_names[h] = s
        return h
    if jn in ("NewGlobalRef", "NewLocalRef", "NewWeakGlobalRef"):
        env, o = m.get_args("pp")
        m.ev("jni", jn, m.norm(o))
        return o
    if jn in ("DeleteGlobalRef", "DeleteLocalRef", "DeleteWeakGlobalRef"):
        env, o = m.get_args("pp")
        m.ev("jni", jn, m.norm(o))
        return 0
    if jn == "GetObjectClass":
        env, o = m.get_args("pp")
        m.ev("jni", jn, m.norm(o))
        k = "cls-of-" + str(m.norm(o))
        h = None
        for kk, v in m.class_names.items():
            if v == k:
                h = kk
        if h is None:
            h = m.next_handle
            m.next_handle += 8
            m.class_names[h] = k
        return h
    if jn in ("GetMethodID", "GetStaticMethodID", "GetFieldID", "GetStaticFieldID"):
        env, cls, nm, sg = m.get_args("pppp")
        n_, s_ = m.rdstr(nm), m.rdstr(sg)
        m.ev("jni", jn, m.norm(cls), n_, s_)
        key = "%s:%s:%s" % (jn, n_, s_)
        if pol(m, key, [1, 0], [0.93, 0.07]) == 0:
            return 0
        h = m.next_handle
        m.next_handle += 8
        if "Method" in jn:
            m.method_ids[h] = (cls, n_, s_, "Static" in jn)
        else:
            m.field_ids[h] = (cls, n_, s_)
        return h
    if jn in ("NewStringUTF",):
        env, s = m.get_args("pp")
        st = m.rdstr(s)
        m.ev("jni", jn, st)
        h = m.next_handle
        m.next_handle += 8
        m.strings[h] = st
        return h
    if jn == "GetStringUTFChars":
        env, js, iscopy = m.get_args("ppp")
        st = m.strings.get(js)
        if st is None:
            st = m.string_for(js)
        m.ev("jni", jn, m.norm(js))
        b = st.encode() + b"\0"
        p = m.malloc(len(b) + 1, "utf")
        m.wr(p, b)
        if iscopy:
            m.wr(iscopy, b"\x01")
        return p
    if jn == "ReleaseStringUTFChars":
        env, js, p = m.get_args("ppp")
        m.ev("jni", jn, m.norm(js))
        return 0
    if jn == "GetStringUTFLength":
        env, js = m.get_args("pp")
        return len((m.strings.get(js) or "").encode())
    if jn in ("ExceptionCheck",):
        m.ev("jni", jn)
        return pol(m, "ExcCheck", [0, 1], [0.95, 0.05])
    if jn in ("ExceptionOccurred",):
        m.ev("jni", jn)
        return 0
    if jn in ("ExceptionClear", "ExceptionDescribe"):
        m.ev("jni", jn)
        return 0
    if jn in ("IsSameObject",):
        env, a_, b_ = m.get_args("ppp")
        return int(a_ == b_)
    if jn == "GetJavaVM":
        env, vmpp = m.get_args("pp")
        m.wrw(vmpp, m.vm_obj)
        m.ev("jni", jn)
        return 0
    # GetXField / SetXField
    mm = re.match(r"(Get|Set)(Static)?(\w+?)Field$", jn)
    if mm:
        gs, st, ty = mm.groups()
        if gs == "Get":
            env, obj, fid = m.get_args("ppp")
            f = m.field_ids.get(fid)
            m.ev("jni", jn, m.norm(obj), f[1] if f else None)
            if f and f[1] == "mNativeObject":
                s = m.get_surface_obj(obj)
                return (s, ty == "Long")
            if ty == "Object":
                return _new_handle(m, "obj:%s" % (f[1] if f else "?"))
            if ty == "Long":
                return (0, True)
            return pol(m, "fld:%s" % (f[1] if f else "?"), [0, 1, 2], rand=True)
        else:
            tyspec = {"Boolean": "i", "Byte": "i", "Char": "i", "Short": "i", "Int": "i", "Long": "l",
                      "Float": "d", "Double": "d", "Object": "p"}[ty]
            r = m.get_args("ppp" + tyspec)
            env, obj, fid, val = r
            f = m.field_ids.get(fid)
            m.ev("jni", jn, m.norm(obj), f[1] if f else None, m.norm(val) if tyspec == "p" else val)
            return 0
    # Call*Method
    mm = re.match(r"Call(Static|Nonvirtual)?(\w+?)Method([VA]?)$", jn)
    if mm:
        kind, ty, form = mm.groups()
        rk = {"Void": "v", "Object": "p", "Boolean": "i", "Byte": "i", "Char": "i", "Short": "i", "Int": "i",
              "Long": "l", "Float": "d", "Double": "d"}[ty]
        if kind == "Nonvirtual":
            env, obj, cls, mid = m.get_args("pppp")
            pre = "pppp"
        else:
            env, obj, mid = m.get_args("ppp")
            pre = "ppp"
        meth = m.method_ids.get(mid)
        vals = []
        if meth is not None and form == "":
            spec, rsig = _jsig_spec(meth[2])
            r = m.get_args(pre + spec)
            vals = r[len(pre):]
        elif form == "V" and meth is not None:
            spec, rsig = _jsig_spec(meth[2])
            vl = m.get_args(pre + "p")[-1]
            vals = m.read_valist(vl, spec)
        elif form == "A" and meth is not None:
            spec, rsig = _jsig_spec(meth[2])
            ap = m.get_args(pre + "p")[-1]
            vals = []
            for k, c in enumerate(spec):
                vals.append(int.from_bytes(m.rd(ap + 8 * k, 8), "little"))
        m.ev("jni", jn, m.norm(obj), meth[1] if meth else None, meth[2] if meth else None,
             tuple(m.norm(x) if (c == "p" and isinstance(x, int)) else x for x, c in zip(vals, (_jsig_spec(meth[2])[0] if meth else ""))))
        if rk == "v":
            return 0
        if rk == "p":
            return _new_handle(m, "ret:%s" % (meth[1] if meth else "?"))
        if rk == "l":
            return (0, True)
        return pol(m, "call:%s" % (meth[1] if meth else "?"), [0, 1], rand=True)
    if jn in ("GetArrayLength",):
        env, arr = m.get_args("pp")
        m.ev("jni", jn, m.norm(arr))
        return 0
    if jn in ("PushLocalFrame", "EnsureLocalCapacity"):
        m.ev("jni", jn)
        return 0
    if jn == "PopLocalFrame":
        env, o = m.get_args("pp")
        m.ev("jni", jn, m.norm(o))
        return o
    m.ev("jni", jn, "(unmodeled)")
    m.unmodeled["JNI_" + jn] = m.unmodeled.get("JNI_" + jn, 0) + 1
    return 0


def _read_valist(self, vl, spec):
    out = []
    if self.is64:
        stack = self.rdw(vl)
        gr_top = self.rdw(vl + 8)
        vr_top = self.rdw(vl + 16)
        gr_offs = int.from_bytes(self.rd(vl + 24, 4), "little", signed=True)
        vr_offs = int.from_bytes(self.rd(vl + 28, 4), "little", signed=True)
        for c in spec:
            if c == "d":
                if vr_offs < 0:
                    v = int.from_bytes(self.rd(vr_top + vr_offs, 8), "little")
                    vr_offs += 16
                else:
                    v = int.from_bytes(self.rd(stack, 8), "little")
                    stack += 8
            else:
                if gr_offs < 0:
                    v = int.from_bytes(self.rd(gr_top + gr_offs, 8), "little")
                    gr_offs += 8
                else:
                    v = int.from_bytes(self.rd(stack, 8), "little")
                    stack += 8
                if c == "i":
                    v &= 0xffffffff
            out.append(v)
    else:
        ap = vl     # ARM32: va_list 以指標值直接傳入暫存器 (struct {void* __ap})
        for c in spec:
            if c in "ld":
                ap = (ap + 7) & ~7
                v = int.from_bytes(self.rd(ap, 8), "little")
                ap += 8
            else:
                v = int.from_bytes(self.rd(ap, 4), "little")
                ap += 4
            out.append(v)
    return out


Machine.read_valist = _read_valist


def _string_for(self, js):
    return pol(self, "jstr", ["on", "off", "auto", "zzz"], rand=True)


Machine.string_for = _string_for


def _get_surface_obj(self, obj):
    if not hasattr(self, "_surfobj"):
        self._surfobj = {}
    if obj not in self._surfobj:
        s = self.env_alloc(0x200, "Surface")
        self.surface_init(s)
        self._surfobj[obj] = s
    return self._surfobj[obj]


Machine.get_surface_obj = _get_surface_obj


def h_vm(m, name):
    vn = name[3:]
    if vn == "GetEnv":
        vm, pp, ver = m.get_args("ppi")
        m.ev("vm", "GetEnv", hex(ver))
        r = pol(m, "GetEnv", [0, 0, -2 & 0xffffffff], [0.9, 0.0, 0.1])
        if r == 0:
            m.wrw(pp, m.env_ptr)
        return r
    if vn in ("AttachCurrentThread", "AttachCurrentThreadAsDaemon"):
        vm, pp, args = m.get_args("ppp")
        m.ev("vm", vn)
        m.wrw(pp, m.env_ptr)
        return 0
    m.ev("vm", vn)
    return 0


# ---- 其他 import 預設 (含 Cacao/libgui)
@H("dummy")
def _d(m, name):
    return 0
