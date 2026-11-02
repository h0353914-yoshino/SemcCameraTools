#!/usr/bin/env python3
"""gemu：libcacao_process_ctrl_gateway 專用的 ARM32 Unicorn 差分模擬器（獨立於 emu.py/emu2.py）。

改進重點：
  * ARM 模式啟動（正確執行 ARM PLT / veneer），以位址 bit0 切 Thumb；啟用 VFP/NEON
  * 完整重定位（R_ARM_ABS32 對區域/匯出符號、GLOB_DAT 資料符號、內部 PLT 自呼叫綁回自身）
  * 符號表取自 .dynsym + .gnu_debugdata（含 local 符號）
  * 假 vtable（UVT）：arena 內任何物件的 vtable 指標都指向 stub 表，虛擬呼叫可被記錄
  * 匯入資料符號（_ZTV*、__sF 等）配置假資料區；匯入 vtable 的每個槽位是具名 stub
  * 有狀態 stub：記憶體配置、memcpy/memset、PAL_*、Mutex 遞迴鎖偵測
  * 事件軌跡正規化：指標 -> (區域, 偏移 / 配置序號 / 符號名)，兩邊可直接比對
"""
import bisect
import hashlib
import io
import lzma
import os
import random
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from elftools.elf.elffile import ELFFile  # noqa: E402
from unicorn import (UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_ARM, UC_PROT_ALL, Uc, UcError)  # noqa: E402
from unicorn import arm_const as A  # noqa: E402

from emu import SoImage  # noqa: E402  (沿用 relocation/APS2 解析)

BASE = 0x10000000
ARENA = 0x20000000
ARENA_SZ = 0x40000
STACK = 0x30000000
STACK_SZ = 0x100000
HEAP = 0x40000000
HEAP_SZ = 0x800000
UVT = 0x50000000          # 通用 vtable 表（每張 0x100 bytes，64 槽）
UVT_N = 8
DATAIMP = 0x60000000      # 匯入資料符號區（每個 0x400）
STUB_BASE = 0x70000000
STUB_SZ = 0x20000
RET_MAGIC = 0x7f000000
MAX_INSNS = 60000
M32 = 0xffffffff

# 相容性噪音：不列入事件軌跡（重建版 libc/toolchain 差異）
IGNORE = {
    "__stack_chk_fail", "__cxa_atexit", "__cxa_finalize", "__android_log_print",
    "__register_atfork", "__aeabi_memcpy", "__aeabi_memcpy4", "__aeabi_memcpy8",
    "__aeabi_memclr", "__aeabi_memclr4", "__aeabi_memclr8", "__aeabi_memset", "__aeabi_memset4",
    "__aeabi_memset8", "memcpy", "memset", "memmove", "strlen", "clock_gettime",
    "__cxa_pure_virtual", "abort", "__vsnprintf_chk", "fprintf", "fflush", "raise", "dladdr",
    "dl_iterate_phdr", "_ZNSt3__122__libcpp_verbose_abortEPKcz",
}


class Lib:
    """載入並重定位一個 .so（只做一次），Run 時複製影像。"""

    def __init__(self, path):
        self.img = SoImage(path)
        self.path = path
        self.size = self.img.size
        f = self.img.elf
        self.syms = {}      # name -> [(addr, size, type)]
        self.code = []      # (addr_nothumb, size, name)
        self.objs = []      # (addr, size, name)
        dyn = f.get_section_by_name(".dynsym")
        self.dynsyms = {s.name: s for s in dyn.iter_symbols()}
        for s in dyn.iter_symbols():
            self._addsym(s)
        try:
            e = ELFFile(io.BytesIO(lzma.decompress(f.get_section_by_name(".gnu_debugdata").data())))
            for s in e.get_section_by_name(".symtab").iter_symbols():
                self._addsym(s)
        except Exception:
            pass
        self.code.sort()
        self.objs.sort()
        self.code_keys = [c[0] for c in self.code]
        self.obj_keys = [o[0] for o in self.objs]
        self.stub_names = {}      # addr -> name
        self.stub_addr = {}       # name -> addr
        self.dataimp = {}         # name -> addr (資料匯入)
        self._build_image()
        for t in range(UVT_N):
            for i in range(64):
                self.stub("uvt%d#%d" % (t, i))

    def demangled(self):
        if not hasattr(self, "_dem"):
            import subprocess
            ks = sorted(self.syms)
            dd = subprocess.run(["c++filt", "-n"], input="\n".join(ks), capture_output=True, text=True).stdout.split("\n")
            self._dem = dict(zip(ks, dd))
        return self._dem

    def find(self, sub):
        """mangled 名稱直接命中，否則以 demangled 子字串搜尋；回傳 mangled 名稱 list。"""
        if sub in self.syms:
            return [sub]
        return [k for k, d in self.demangled().items() if sub in d]

    def _addsym(self, s):
        t = s["st_info"]["type"]
        if s["st_shndx"] == "SHN_UNDEF" or not s.name:
            return
        if t in ("STT_FUNC", "STT_OBJECT"):
            ent = (s["st_value"], s["st_size"], t)
            lst = self.syms.setdefault(s.name, [])
            if ent not in lst:
                lst.append(ent)
                if t == "STT_FUNC":
                    self.code.append((s["st_value"] & ~1, s["st_size"], s.name))
                else:
                    self.objs.append((s["st_value"], s["st_size"], s.name))

    def stub(self, name):
        if name not in self.stub_addr:
            a = STUB_BASE + 16 * (len(self.stub_addr) + 1)
            self.stub_addr[name] = a
            self.stub_names[a] = name
        return self.stub_addr[name]

    @staticmethod
    def is_data_name(name):
        return (name.startswith(("_ZTV", "_ZTT", "_ZTI", "_ZTS")) or name in ("__sF", "__stack_chk_guard")
                or (name.startswith("_ZN") and name.endswith("descriptorE")))

    def data_import(self, name):
        if name not in self.dataimp:
            self.dataimp[name] = DATAIMP + 0x400 * len(self.dataimp)
        return self.dataimp[name]

    def _build_image(self):
        sz = (self.size + 0xfff) & ~0xfff
        buf = bytearray(sz + 0x1000)
        for v, m, data in self.img.segs:
            buf[v:v + len(data)] = data
        self.image = buf

        def rd(off):
            return struct.unpack_from("<I", buf, off)[0]

        def wr(off, v):
            struct.pack_into("<I", buf, off, v & M32)

        for off, t, sym, add in self.img.relocs:
            if t in ("RELR", 23):
                wr(off, rd(off) + BASE)
            elif t in (2, 21, 22):
                if not sym:
                    continue
                s = self.dynsyms.get(sym)
                if s is not None and s["st_shndx"] != "SHN_UNDEF":
                    val = BASE + s["st_value"]       # 保留 thumb bit
                    if t == 2:
                        val += rd(off)
                    wr(off, val)
                elif self.is_data_name(sym):
                    wr(off, self.data_import(sym) + (rd(off) if t == 2 else 0))
                else:
                    wr(off, (self.stub(sym) | 1) + (rd(off) if t == 2 else 0))
        self.dataimp_bytes = {}
        for name, a in self.dataimp.items():
            b = bytearray(0x400)
            if name.startswith("_ZTV"):
                for i in range(2, 0x400 // 4):
                    struct.pack_into("<I", b, i * 4, self.stub("%s#%d" % (name, i - 2)) | 1)
            elif name == "__stack_chk_guard":
                struct.pack_into("<I", b, 0, 0xA5C3E1F7)
            self.dataimp_bytes[a] = bytes(b)

    def addr_name(self, addr):
        """lib 內偏移 -> 'sym+off'"""
        a = addr & ~1
        i = bisect.bisect_right(self.code_keys, a) - 1
        if i >= 0:
            c = self.code[i]
            if a < c[0] + max(c[1], 1):
                return "%s+%d" % (c[2], a - c[0]) if a != c[0] else c[2]
        j = bisect.bisect_right(self.obj_keys, addr) - 1
        if j >= 0:
            o = self.objs[j]
            if addr < o[0] + max(o[1], 1):
                return "%s+%d" % (o[2], addr - o[0])
        return None

    def aliases(self, addr):
        """函式位址（含 thumb bit 或不含）→ 該位址上所有符號名 frozenset。"""
        if not hasattr(self, "_alias"):
            self._alias = {}
            for a, sz, n in self.code:
                self._alias.setdefault(a, set()).add(n)
        return frozenset(self._alias.get(addr & ~1, {"?%x" % (addr & ~1)}))

    def vt_slots(self, vt_addr, maxn=40):
        """vt_addr: lib 內偏移（vtable 指標指向處）；回傳每槽的別名集合 list。"""
        out = []
        for i in range(maxn):
            off = vt_addr + 4 * i
            if off + 4 > len(self.image):
                break
            w = struct.unpack_from("<I", self.image, off)[0]
            if BASE <= w < BASE + self.size and self.addr_name(w - BASE) and (w - BASE) < len(self.image):
                if self.aliases(w - BASE) and not any(x.startswith("?") for x in self.aliases(w - BASE)):
                    out.append(self.aliases(w - BASE))
                    continue
            elif STUB_BASE <= w < STUB_BASE + STUB_SZ:
                out.append(frozenset([self.stub_names.get(w & ~1)]))
                continue
            break
        return out

    def cstr(self, off, n=96):
        b = bytes(self.image[off:off + n])
        i = b.find(b"\0")
        return b[: i if i >= 0 else n].decode("latin1")


def build_arena(seed):
    """通用物件池：混合 vtable 指標 / arena 指標 / 小整數 / 0 / 隨機高位值。"""
    r = random.Random(0xC0FFEE ^ (seed * 7919))
    out = bytearray()
    for i in range(ARENA_SZ // 4):
        k = r.random()
        if k < 0.12:
            v = UVT + 0x100 * r.randrange(UVT_N)
        elif k < 0.40:
            v = ARENA + (r.randrange(0, ARENA_SZ // 2) & ~3)
        elif k < 0.62:
            v = r.randrange(0, 40)
        elif k < 0.75:
            v = 0
        elif k < 0.80:
            v = 0xffffffff
        else:
            v = 0x80000000 | r.getrandbits(31)
        out += struct.pack("<I", v)
    return bytes(out)


C_NARGS = {
    "PAL_Create": 0, "PAL_Delete": 0, "PAL_ErrToString": 1, "PAL_MsgReply": 1, "PAL_MsgSend": 1,
    "PAL_MsgSendRecv": 1, "PAL_ThreadClose": 1, "PAL_ThreadCreateWithMsgQue": 5,
    "PAL_ThreadGetQueId": 1, "PAL_TimeGetMonotonic": 0, "usleep": 1, "close": 1,
    "native_handle_close": 1, "native_handle_delete": 1, "strlen": 1,
}
_NARGS = {}
_DEM = {}


def demangle(name):
    if name not in _DEM:
        import subprocess
        _DEM[name] = subprocess.run(["c++filt", "-n", name], capture_output=True, text=True).stdout.strip() if name.startswith("_Z") else name
    return _DEM[name]


def returns_this(name):
    """ARM EABI：ctor/dtor 與 operator= 類回傳 this。"""
    if not name.startswith("_Z"):
        return False
    d = demangle(name)
    head = d.split("(")[0]
    parts = head.replace(" ", "").split("::")
    if len(parts) >= 2:
        last, cls = parts[-1], parts[-2].split("<")[0]
        if last == cls or last == "~" + cls or last == "operator=" or last.startswith("operator="):
            return True
    return False


def _split_params(s):
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch in "<(":
            depth += 1
        elif ch in ">)":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def nargs(name):
    """由 demangle 簽名推估暫存器參數數（含 this）。"""
    if name in _NARGS:
        return _NARGS[name]
    n = 4
    if name in C_NARGS:
        n = C_NARGS[name]
    elif name.startswith("_Z"):
        import subprocess
        d = subprocess.run(["c++filt", "-n", name], capture_output=True, text=True).stdout.strip()
        if d.endswith(" const"):
            d = d[:-6]
        if d.endswith(")"):
            depth, i = 0, len(d) - 1
            while i >= 0:
                if d[i] == ")":
                    depth += 1
                elif d[i] == "(":
                    depth -= 1
                    if depth == 0:
                        break
                i -= 1
            params = d[i + 1:-1]
            head = d[:i]
            ps = _split_params(params)
            if ps == ["void"]:
                ps = []
            n = len(ps)
            for p in ps:
                if p.startswith(("long long", "unsigned long long", "double")) or p in ("long long", "unsigned long long"):
                    n += 1           # 64-bit 佔兩個暫存器（近似）
            parts = head.replace(" ", "").split("::")
            if len(parts) >= 2:
                cls, last = parts[-2], parts[-1].split("[")[0]
                if (cls[:1].isupper() or cls.startswith("hidl_") or cls in ("return_status", "sp", "function")
                        or last == cls.split("<")[0] or last.startswith("~")):
                    n += 1               # this
    _NARGS[name] = min(n, 6)
    return _NARGS[name]


class Fault(Exception):
    pass


class Run:
    def __init__(self, lib: Lib, seed: int, flavor=None, arena=None, retfn=None, hooks=None):
        self.lib = lib
        self.seed = seed
        self.flavor = seed % 4 if flavor is None else flavor
        self.retfn = retfn           # 可覆寫 stub 回傳值 retfn(run, name, k) -> int|None
        self.hooks = hooks or {}     # name -> fn(run, args) -> ret（優先於內建模型）
        self.events = []
        self.logs = []
        self.allocs = []
        self.heap_ptr = HEAP
        self.alloc_tab = []
        self.alloc_starts = []
        self.counters = {}
        self.fault = None
        self.mutex_depth = {}
        self.anomalies = []
        self.dead = set()            # 已 PAL_ThreadClose / 已刪除的 handle（供情境模擬）
        uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        self.uc = uc
        sz = (lib.size + 0xfff) & ~0xfff
        uc.mem_map(BASE, sz + 0x1000, UC_PROT_ALL)
        uc.mem_write(BASE, bytes(lib.image))
        uc.mem_map(ARENA, ARENA_SZ, UC_PROT_ALL)
        uc.mem_map(STACK, STACK_SZ, UC_PROT_ALL)
        uc.mem_map(HEAP, HEAP_SZ, UC_PROT_ALL)
        uc.mem_map(UVT, 0x10000, UC_PROT_ALL)
        uc.mem_map(DATAIMP, 0x10000, UC_PROT_ALL)
        uc.mem_map(STUB_BASE, STUB_SZ, UC_PROT_ALL)
        uc.mem_map(RET_MAGIC, 0x1000, UC_PROT_ALL)
        nop = b"\x00\xbf" * 8
        uc.mem_write(STUB_BASE, nop * (STUB_SZ // 16))
        uc.mem_write(RET_MAGIC, nop * 8)
        for a, b in lib.dataimp_bytes.items():
            uc.mem_write(a, b)
        uvt = bytearray()
        for t in range(UVT_N):
            for i in range(64):
                uvt += struct.pack("<I", lib.stub_addr["uvt%d#%d" % (t, i)] | 1)
        uc.mem_write(UVT, bytes(uvt))
        self.arena0 = arena if arena is not None else build_arena(seed)
        uc.mem_write(ARENA, self.arena0)
        uc.reg_write(A.UC_ARM_REG_C1_C0_2, uc.reg_read(A.UC_ARM_REG_C1_C0_2) | (0xf << 20))
        uc.reg_write(A.UC_ARM_REG_FPEXC, 0x40000000)
        uc.hook_add(UC_HOOK_CODE, self._stub_hook, begin=STUB_BASE, end=STUB_BASE + STUB_SZ)
        uc.hook_add(UC_HOOK_CODE, lambda u, a, s, d: u.emu_stop(), begin=RET_MAGIC, end=RET_MAGIC + 0x1000)

    # ---- 輔助 ----
    def rd32(self, a):
        return struct.unpack("<I", bytes(self.uc.mem_read(a, 4)))[0]

    def wr32(self, a, v):
        self.uc.mem_write(a, struct.pack("<I", v & M32))

    def arg(self, i):
        if i < 4:
            return self.uc.reg_read(A.UC_ARM_REG_R0 + i)
        sp = self.uc.reg_read(A.UC_ARM_REG_SP)
        try:
            return self.rd32(sp + 4 * (i - 4))
        except UcError:
            return 0

    def cstr(self, a, n=120):
        try:
            b = bytes(self.uc.mem_read(a, n))
        except UcError:
            try:
                b = bytes(self.uc.mem_read(a, 16))
            except UcError:
                return None
        i = b.find(b"\0")
        return b[: i if i >= 0 else len(b)].decode("latin1")

    def norm(self, v):
        v &= M32
        lib = self.lib
        if BASE <= v < BASE + lib.size:
            off = v - BASE
            n = lib.addr_name(off)
            if n and "_ZTV" not in n:
                return "@" + n
            s = lib.cstr(off, 64) if not n else ""
            if s and all(32 <= ord(c) < 127 or c in "\n\t" for c in s) and len(s) >= 2:
                return 'str"%s"' % s
            # vtable 類資料：以首個虛擬函式（relocated 後的函式位址）命名
            try:
                w0 = struct.unpack_from("<I", lib.image, off & ~3)[0]
                if BASE <= w0 < BASE + lib.size and lib.addr_name(w0 - BASE):
                    return "@vt"
                elif STUB_BASE <= w0 < STUB_BASE + STUB_SZ:
                    return "@vt"
            except Exception:
                pass
            return "@lib_data"
        if ARENA <= v < ARENA + ARENA_SZ:
            return ("A", v - ARENA)
        if STACK <= v < STACK + STACK_SZ:
            return "STK"
        if HEAP <= v < HEAP + HEAP_SZ:
            i = bisect.bisect_right(self.alloc_starts, v) - 1
            if i >= 0 and v < self.alloc_tab[i][0] + max(self.alloc_tab[i][1], 1):
                return ("H", i, v - self.alloc_tab[i][0])
            return ("H?", v - HEAP)
        if UVT <= v < UVT + 0x10000:
            return ("uvt", (v - UVT) // 0x100, (v - UVT) % 0x100)
        if DATAIMP <= v < DATAIMP + 0x10000:
            for n, a in self.lib.dataimp.items():
                if a <= v < a + 0x400:
                    return "D:%s+%d" % (n, v - a)
        if STUB_BASE <= v < STUB_BASE + STUB_SZ:
            return "@stub:" + str(self.lib.stub_names.get(v & ~1))
        return v

    def alloc(self, n):
        n0 = n
        n = max((n + 15) & ~15, 16)
        p = self.heap_ptr
        if p + n > HEAP + HEAP_SZ:
            raise Fault("heap exhausted")
        self.heap_ptr += n
        self.alloc_tab.append((p, n0))
        self.alloc_starts.append(p)
        return p, len(self.alloc_tab) - 1

    # ---- stub ----
    def _ret_val(self, name):
        k = self.counters.get(name, 0)
        self.counters[name] = k + 1
        if self.retfn is not None:
            v = self.retfn(self, name, k)
            if v is not None:
                return v
        if self.flavor == 0:
            return 0
        h = hashlib.md5(("%d|%s|%d" % (self.seed, name, k)).encode()).digest()
        x = h[0]
        if self.flavor == 1:
            return 0 if x < 200 else 1
        if x < 100:
            return 0
        if x < 140:
            return 1
        if x < 170:
            return 0xffffffff
        if x < 190:
            return 0xffffff91
        if x < 225:
            return ARENA + 0x40 * (h[1] % 200)
        return h[2]

    def _stub_hook(self, uc, addr, size, ud):
        name = self.lib.stub_names.get(addr & ~1)
        if name is None:
            return
        a = [self.arg(i) for i in range(6)]
        ret = self.model(name, a)
        lr = uc.reg_read(A.UC_ARM_REG_LR)
        if isinstance(ret, tuple):
            uc.reg_write(A.UC_ARM_REG_R1, ret[1] & M32)
            ret = ret[0]
        uc.reg_write(A.UC_ARM_REG_R0, ret & M32)
        uc.reg_write(A.UC_ARM_REG_PC, lr)

    def ev(self, name, a, n=None):
        if n is None:
            n = 2 if "#" in name else nargs(name)
        self.events.append((name, tuple(self.norm(x) for x in a[:n])))

    def _lock(self, m):
        k = m & M32
        d = self.mutex_depth.get(k, 0)
        if d > 0:
            self.anomalies.append(("RECURSIVE_LOCK", k, [e[0] for e in self.events[-3:]]))
        self.mutex_depth[k] = d + 1

    def _unlock(self, m):
        k = m & M32
        self.mutex_depth[k] = self.mutex_depth.get(k, 0) - 1

    def model(self, name, a):
        uc = self.uc
        if name in self.hooks:
            return self.hooks[name](self, a) & M32
        if name == "PAL_TimeGetMonotonic":
            self.ev(name, a, 0)
            ns = 123456789012 + 1000 * self.counters.setdefault("_t", 0)
            self.counters["_t"] += 1
            return (ns & M32, ns >> 32)
        if name == "clock_gettime":
            ns = 123456789012 + 1000 * self.counters.setdefault("_t", 0)
            self.counters["_t"] += 1
            self.wr32(a[1], ns // 1000000000)
            self.wr32(a[1] + 4, ns % 1000000000)
            return 0
        if name in IGNORE:
            if name in ("memcpy", "memmove", "__aeabi_memcpy", "__aeabi_memcpy4", "__aeabi_memcpy8"):
                if a[2] <= 0x40000:
                    uc.mem_write(a[0], bytes(uc.mem_read(a[1], a[2])))
                return a[0]
            if name == "memset":
                if a[2] <= 0x40000:
                    uc.mem_write(a[0], bytes([a[1] & 0xff]) * a[2])
                return a[0]
            if name in ("__aeabi_memclr", "__aeabi_memclr4", "__aeabi_memclr8"):
                if a[1] <= 0x40000:
                    uc.mem_write(a[0], b"\0" * a[1])
                return 0
            if name in ("__aeabi_memset", "__aeabi_memset4", "__aeabi_memset8"):
                if a[1] <= 0x40000:
                    uc.mem_write(a[0], bytes([a[2] & 0xff]) * a[1])
                return 0
            if name == "strlen":
                s = self.cstr(a[0], 4096)
                return len(s) if s is not None else 0
            return 0
        if name in ("_Znwj", "_Znaj", "_ZN5cacao10ObjectBasenwEj", "_ZnwjSt11align_val_t", "_ZnajSt11align_val_t"):
            n = min(a[0], 0x100000)
            p, i = self.alloc(n)
            self.allocs.append(("new", n))
            return p
        if name == "PAL_MemAllocEx":
            n = min(a[0], 0x100000)
            p, i = self.alloc(n)
            self.allocs.append(("new", n))
            return p
        if name in ("_ZdlPv", "_ZdaPv", "_ZN5cacao10ObjectBasedlEPv", "_ZdlPvSt11align_val_t", "_ZdaPvSt11align_val_t",
                    "PAL_MemFreeEx"):
            self.allocs.append(("del", self.norm(a[0])))
            return 0
        if name == "PAL_MemSet":
            if a[2] <= 0x40000:
                uc.mem_write(a[0], bytes([a[1] & 0xff]) * a[2])
            return 0
        if name == "PAL_StrLen":
            s = self.cstr(a[0], 4096)
            return len(s) if s is not None else 0
        if name == "PAL_LogPrint":
            self.logs.append((a[2] & M32, a[3] & M32, self.cstr(a[4])))
            return 0
        if name == "PAL_StrNPrintf":
            self.ev(name, a)
            return 1
        if name == "_ZN9cacao_pal5Mutex4lockEv":
            self._lock(a[0])
            self.ev(name, a, 1)
            return 0
        if name == "_ZN9cacao_pal5Mutex7tryLockEv":
            k = a[0] & M32
            self.ev(name, a, 1)
            if self.mutex_depth.get(k, 0) > 0:
                return 0
            self.mutex_depth[k] = 1
            return 1
        if name == "_ZN9cacao_pal5Mutex6unlockEv":
            self._unlock(a[0])
            self.ev(name, a, 1)
            return 0
        if name in ("_ZN9cacao_pal8AutoLockC1ERNS_5MutexE", "_ZN9cacao_pal8AutoLockC2ERNS_5MutexE"):
            self._lock(a[1])
            self.wr32(a[0], a[1])
            self.ev(name, a, 2)
            return a[0]
        if name in ("_ZN9cacao_pal8AutoLockD1Ev", "_ZN9cacao_pal8AutoLockD2Ev"):
            try:
                m = self.rd32(a[0])
            except UcError:
                m = 0
            self._unlock(m)
            self.ev(name, a, 1)
            return a[0]
        if name == "_ZN7android21IGraphicBufferProducer11asInterfaceERKNS_2spINS_7IBinderEEE":
            # sret sp<IGraphicBufferProducer>：寫入假物件指標（有 UVT vtable 的堆積物件）
            p, _ = self.alloc(0x40)
            self.wr32(p, UVT)
            self.wr32(a[0], p)
            self.ev(name, a, 2)
            return a[0]
        if name == "_ZN6vendor4somc8hardware6camera5cacao4V3_16ICacao8castFromERKN7android2spINS3_4V3_06ICacaoEEEb":
            uc.mem_write(a[0], b"\0" * 0x20)
            self.ev(name, a, 3)
            return a[0]
        if name == "PAL_Delete":
            held = [k for k, d in self.mutex_depth.items() if d > 0]
            if held:
                self.anomalies.append(("PAL_Delete_while_locked", held))
        self.ev(name, a)
        if returns_this(name):
            self._ret_val(name)
            return a[0]
        return self._ret_val(name)

    def call(self, addr, args):
        uc = self.uc
        sp = STACK + STACK_SZ - 0x1000
        uc.mem_write(sp - 0x4000, bytes(0x5000))      # 清除前次呼叫殘留的堆疊，避免讀未初始化堆疊的雜訊
        uc.reg_write(A.UC_ARM_REG_SP, sp)
        for i, v in enumerate(args[:4]):
            uc.reg_write(A.UC_ARM_REG_R0 + i, v & M32)
        for i, v in enumerate(args[4:10]):
            self.wr32(sp + 4 * i, v)
        uc.reg_write(A.UC_ARM_REG_LR, RET_MAGIC | 1)
        for i in range(4, 12):
            uc.reg_write(A.UC_ARM_REG_R0 + i, 0)
        start = BASE + addr          # addr 含 thumb bit
        try:
            uc.emu_start(start, RET_MAGIC, count=MAX_INSNS)
            pc = uc.reg_read(A.UC_ARM_REG_PC)
            if not (RET_MAGIC <= pc < RET_MAGIC + 0x1000):
                self.fault = "insn_limit"
        except UcError as e:
            self.fault = {6: "read_unmapped", 7: "write_unmapped", 8: "fetch_unmapped",
                          10: "read_unmapped", 11: "write_unmapped", 12: "fetch_unmapped",
                          21: "invalid_insn"}.get(e.errno, "uc%d" % e.errno)
        except Fault as e:
            self.fault = "fault:" + str(e)
        return uc.reg_read(A.UC_ARM_REG_R0), uc.reg_read(A.UC_ARM_REG_R1)

    def memdiff(self, extra=()):
        """arena 與配置區變更字（正規化）。"""
        cur = bytes(self.uc.mem_read(ARENA, ARENA_SZ))
        out = {}
        a0 = self.arena0
        for off in range(0, ARENA_SZ, 4):
            if cur[off:off + 4] != a0[off:off + 4]:
                v = struct.unpack_from("<I", cur, off)[0]
                out[("A", off)] = self.norm(v)
        for i, (p, n) in enumerate(self.alloc_tab):
            n = min(max(n, 0), 0x600)
            b = bytes(self.uc.mem_read(p, (n + 3) & ~3))
            for off in range(0, len(b), 4):
                v = struct.unpack_from("<I", b, off)[0]
                if v:
                    out[("H", i, off)] = self.norm(v)
        return out
