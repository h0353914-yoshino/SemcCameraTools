#!/usr/bin/env python3
"""cemu：libcacao_client/service 專用降噪版 Unicorn 差分模擬（私有副本）。
 1. 符號 = dynsym + .gnu_debugdata，依位址去重（ICF 別名）。
 2. arena 以指標為主；未映射存取按需補零頁；執行 arena 位址 = 虛擬呼叫（記錄後返回）。
 3. 外呼記錄：名稱正規化、依 demangle 推算參數個數、字串內容/heap 序號/arena 偏移正規化。
 4. 外呼回傳模式 3 種（0 / 假物件指標 / -1）。
 5. 記憶體寫入以最終位元組字典比較（排除 stack）。
 6. 庫內自定義符號（函數/資料）的 GOT/PLT 導向庫內真實位址；外部資料符號給假資料區。
"""
import os, random, re, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from base import SoImage as _Base, regs
from dbgsyms import debug_syms
from unicorn import *
from unicorn import arm_const as A
from unicorn import arm64_const as A64

BASE = 0x10000000
STUB_BASE = 0x70000000
RET_MAGIC = 0x7f000000
ARENA = 0x20000000
ARENA_SZ = 0x40000
STACK = 0x30000000
STACK_SZ = 0x100000
DATA = 0x78000000
HEAP = 0x40000000
HSTRIDE = 0x4000
HEAP_SZ = 0x1000000
MAX_INSNS = 60000

DROP = {"__cxa_atexit", "__cxa_finalize", "__stack_chk_fail", "atexit", "pthread_atfork", "__register_atfork",
        "__on_dlclose_late", "__emutls_get_address", "__emutls_unregister_key", "__aeabi_unwind_cpp_pr0",
        "__aeabi_unwind_cpp_pr1", "__aeabi_unwind_cpp_pr2", "__cxa_begin_cleanup", "__gnu_Unwind_Resume",
        "_Unwind_Resume", "__gxx_personality_v0", "__cxa_end_cleanup"}
ALIAS = {"__aeabi_memcpy": "memcpy", "__aeabi_memcpy4": "memcpy", "__aeabi_memcpy8": "memcpy",
         "__aeabi_memmove": "memmove", "__aeabi_memmove4": "memmove", "__aeabi_memmove8": "memmove",
         "_Znwj": "new", "_Znwm": "new", "_Znaj": "new", "_Znam": "new",
         "_ZdlPv": "delete", "_ZdaPv": "delete", "_ZdlPvj": "delete", "_ZdlPvm": "delete"}
CANON = {"_ZNK7android7IMemory7pointerEv": "IMemory::ptr", "_ZNK7android7IMemory15unsecurePointerEv": "IMemory::ptr",
         "_ZNK7android6Parcel10readIntPtrEv": "Parcel::readIntPtr64", "_ZNK7android6Parcel9readInt64Ev": "Parcel::readIntPtr64",
         "_ZNK7android6Parcel10readUint32Ev": "_ZNK7android6Parcel9readInt32Ev"}
IGNORE_ARGS = {"PAL_MemAllocEx": (2,)}   # __FILE__ 字串

_AR = {}
_ISD = {}
LIBC_AR = {"pthread_mutex_init": 2, "pthread_mutex_destroy": 1, "pthread_mutex_lock": 1, "pthread_mutex_unlock": 1,
           "memcpy": 3, "memmove": 3, "memset": 3, "strlen": 1, "getpid": 0, "usleep": 1, "close": 1, "dup": 1,
           "abort": 0, "PAL_MemAllocEx": 5, "PAL_MemFreeEx": 2, "__android_log_print": 3, "free": 1, "malloc": 1,
           "new": 1, "delete": 1, "__aeabi_memclr": 2, "__aeabi_memclr4": 2, "__aeabi_memclr8": 2,
           "native_handle_close": 1, "native_handle_delete": 1, "strzcmp16": 4, "fflush": 1, "fprintf": 3,
           "__vsnprintf_chk": 5, "dladdr": 2, "__cxa_pure_virtual": 0}
STATIC_PAT = re.compile(r"(ProcessState::self|IPCThreadState::self|defaultServiceManager|IInterface::asBinder|"
                        r"IMemory::asInterface|ProcessCtrlGatewayFactory::create|::getService|checkCallingPermission|"
                        r"castFrom|operator (new|delete)|^android::Cacao::create|getCaps|getJpegBufferSize|"
                        r"android::Cacao::\w+$|sp_report_race|__libcpp_verbose_abort)")


def demangle(n):
    return subprocess.run(["c++filt", n], capture_output=True, text=True).stdout.strip()


def arity(mangled):
    if mangled in LIBC_AR:
        return LIBC_AR[mangled]
    if mangled in _AR:
        return _AR[mangled]
    dm = demangle(mangled)
    if dm == mangled:
        n = 4
    else:
        m = re.match(r"^(.*?)\((.*)\)( const)?$", dm)
        if not m:
            n = 2
        else:
            head, params, c = m.group(1), m.group(2), m.group(3)
            depth = 0
            cnt = 0 if not params.strip() or params.strip() == "void" else 1
            for ch in params:
                if ch in "<(":
                    depth += 1
                elif ch in ">)":
                    depth -= 1
                elif ch == "," and depth == 0:
                    cnt += 1
            ismethod = bool(c) or ("::" in head and not STATIC_PAT.search(head))
            n = cnt + (1 if ismethod else 0)
    _AR[mangled] = n
    return n


class Img(_Base):
    def __init__(self, path):
        super().__init__(path)
        self.dynfuncs = dict(self.funcs)
        for k, v in debug_syms(path).items():
            self.funcs.setdefault(k, v)
        self.byaddr = {}
        for k, (a, s) in self.funcs.items():
            self.byaddr.setdefault(a & ~1, []).append(k)
        self.objs = {}
        for sec in self.elf.iter_sections():
            if sec.name == ".dynsym":
                for sy in sec.iter_symbols():
                    if sy["st_shndx"] != "SHN_UNDEF" and sy["st_info"]["type"] in ("STT_OBJECT", "STT_NOTYPE", "STT_TLS") and sy.name:
                        self.objs[sy.name] = (sy["st_value"], sy["st_size"])
        for k, v in debug_syms(path, 'STT_OBJECT').items():
            self.objs.setdefault(k, v)
        self.objs_sorted = sorted((a, s, n) for n, (a, s) in self.objs.items() if s)
        self.imgbuf = bytearray(((self.size + 0xfff) & ~0xfff) + 0x1000)
        for v, m, d in self.segs:
            self.imgbuf[v:v + len(d)] = d

    def cstr(self, off):
        if not (0 <= off < len(self.imgbuf)):
            return None
        e = self.imgbuf.find(b"\0", off, off + 160)
        if e < 0 or e - off < 2:
            return None
        s = bytes(self.imgbuf[off:e])
        if all(32 <= c < 127 or c in (9, 10) for c in s):
            return s.decode()
        return None


class Emu:
    def __init__(self, img, mode, seed, akind='rand'):
        self.akind = akind
        self.img = img
        self.mode = mode
        self.seed = seed
        self.is64 = img.is64
        self.w = img.ptr
        self.uc = Uc(UC_ARCH_ARM64, UC_MODE_ARM) if self.is64 else Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.rregs, self.sp, self.pc = regs(self.is64)
        self.calls = []
        self.writes = set()
        self.nalloc = 0
        self.stubs = {}
        self.stub_names = {}
        self.fault = None
        self.autopages = 0
        self.data_names = {}
        self.data_idx = {}
        if not self.is64:
            v = self.uc.reg_read(A.UC_ARM_REG_C1_C0_2)
            self.uc.reg_write(A.UC_ARM_REG_C1_C0_2, v | (0xf << 20))
            self.uc.reg_write(A.UC_ARM_REG_FPEXC, 0x40000000)
        self._map()
        self._reloc()
        self._seed_arena()

    def _map(self):
        uc = self.uc
        sz = (self.img.size + 0xfff) & ~0xfff
        uc.mem_map(BASE, sz + 0x1000)
        for v, m, data in self.img.segs:
            uc.mem_write(BASE + v, data)
        uc.mem_map(ARENA, ARENA_SZ)
        uc.mem_map(STACK, STACK_SZ)
        uc.mem_map(HEAP, HEAP_SZ)
        uc.mem_map(STUB_BASE, 0x20000)
        uc.mem_map(RET_MAGIC, 0x1000)
        uc.mem_map(DATA, 0x10000)
        nop = b"\x1f\x20\x03\xd5" if self.is64 else b"\x00\xbf\x00\xbf"
        uc.mem_write(STUB_BASE, nop * (0x20000 // 4))
        uc.mem_write(RET_MAGIC, nop * 8)
        uc.hook_add(UC_HOOK_CODE, self._stub_hook, begin=STUB_BASE, end=STUB_BASE + 0x20000)
        uc.hook_add(UC_HOOK_CODE, lambda u, a, s, d: u.emu_stop(), begin=RET_MAGIC, end=RET_MAGIC + 0x1000)
        uc.hook_add(UC_HOOK_CODE, self._icall_hook, begin=ARENA, end=ARENA + ARENA_SZ)
        uc.hook_add(UC_HOOK_MEM_WRITE, self._wr_hook, begin=ARENA, end=ARENA + ARENA_SZ)
        uc.hook_add(UC_HOOK_MEM_WRITE, self._wr_hook, begin=HEAP, end=HEAP + HEAP_SZ)
        uc.hook_add(UC_HOOK_MEM_READ_UNMAPPED | UC_HOOK_MEM_WRITE_UNMAPPED, self._unmapped)

    def _unmapped(self, uc, access, addr, size, value, ud):
        if self.autopages > 64 or addr < 0x1000:
            return False
        try:
            uc.mem_map(addr & ~0xfff, 0x2000)
        except UcError:
            return False
        self.autopages += 1
        return True

    def _wr_hook(self, uc, access, addr, size, value, ud):
        self.writes.add((addr, size))

    def _seed_arena(self):
        r = random.Random(0xC0FFEE)
        w = self.w
        if self.akind != 'rand':
            V = self.akind
            if V == 'ptr':
                V = ARENA + 0x20000
            buf = (V & ((1 << (8 * w)) - 1)).to_bytes(w, 'little') * (ARENA_SZ // w)
            self.uc.mem_write(ARENA, buf)
            self.arena0 = buf
            return
        buf = bytearray()
        for i in range(ARENA_SZ // w):
            k = r.random()
            if k < 0.65:
                v = ARENA + (r.randrange(0, ARENA_SZ - 0x1000) & ~(w - 1))
            elif k < 0.8:
                v = r.randrange(1, 40)
            elif k < 0.88:
                v = 0
            else:
                v = r.getrandbits(w * 8) if r.random() < 0.5 else r.getrandbits(16)
            buf += v.to_bytes(w, "little")
        self.uc.mem_write(ARENA, bytes(buf))
        self.arena0 = bytes(buf)

    def _stub_for(self, name):
        name = name.split("@")[0]
        if name not in self.stubs:
            a = STUB_BASE + 16 * (len(self.stubs) + 1)
            self.stubs[name] = a
            self.stub_names[a] = name
        return self.stubs[name]

    def _is_data(self, name):
        if name in ("__sF", "__stack_chk_guard"):
            return True
        if not name.startswith("_Z"):
            return False
        if name.startswith(("_ZTV", "_ZTT", "_ZTI", "_ZTS")):
            return True
        if name not in _ISD:
            dm = demangle(name)
            _ISD[name] = ("(" not in dm) and ("::" in dm)
        return _ISD[name]

    def _data_for(self, name):
        if name not in self.data_idx:
            i = len(self.data_idx) + 1
            self.data_idx[name] = i
            self.data_names[i] = name
            m = (1 << (8 * self.w)) - 1
            self.uc.mem_write(DATA + i * 0x100, b"".join(((ARENA + 0x100 * (j + 1)) & m).to_bytes(self.w, "little") for j in range(0x100 // self.w)))
        return DATA + self.data_idx[name] * 0x100

    def _reloc(self):
        uc, w, img = self.uc, self.w, self.img
        mask = (1 << (8 * w)) - 1
        for off, t, sym, add in img.relocs:
            where = BASE + off
            rd = lambda: int.from_bytes(bytes(uc.mem_read(where, w)), "little")
            wr = lambda v: uc.mem_write(where, (v & mask).to_bytes(w, "little"))
            if t == "RELR":
                wr(rd() + BASE)
            elif t in (23, 1027):
                wr(BASE + (add if add is not None else rd()))
            elif t in (21, 22, 1025, 1026):
                if not sym:
                    continue
                if sym in img.dynfuncs:
                    wr(BASE + img.dynfuncs[sym][0])
                elif sym in img.objs:
                    wr(BASE + img.objs[sym][0])
                elif self._is_data(sym):
                    wr(self._data_for(sym))
                else:
                    wr(self._stub_for(sym) | (0 if self.is64 else 1))
            elif t in (2, 257):
                ad = add if add is not None else (rd() if not self.is64 else 0)
                if sym in img.dynfuncs:
                    wr(BASE + img.dynfuncs[sym][0] + ad)
                elif sym in img.objs:
                    wr(BASE + img.objs[sym][0] + ad)
                elif self._is_data(sym):
                    wr(self._data_for(sym) + ad)
                else:
                    wr((self._stub_for(sym) | (0 if self.is64 else 1)) + ad)

    def norm(self, v):
        img = self.img
        if BASE <= v < BASE + img.size:
            off = v - BASE
            s = img.cstr(off)
            return ("s", s) if s else "IMG"
        if DATA <= v < DATA + 0x10000:
            return ("D", self.data_names.get((v - DATA) // 0x100, "?"), (v - DATA) % 0x100)
        if STUB_BASE <= v < STUB_BASE + 0x20000:
            return "STUB"
        if ARENA <= v < ARENA + ARENA_SZ:
            return ("A", v - ARENA) if self.akind == 'rand' else "A"
        if HEAP <= v < HEAP + HEAP_SZ:
            return ("H", (v - HEAP) // HSTRIDE, (v - HEAP) % HSTRIDE)
        if STACK <= v < STACK + STACK_SZ:
            return "STK"
        return v

    def _arg(self, i):
        uc = self.uc
        if self.is64 or i < 4:
            return uc.reg_read(self.rregs[i])
        sp = uc.reg_read(self.sp)
        return int.from_bytes(bytes(uc.mem_read(sp + 4 * (i - 4), 4)), "little")

    def _ret_to_lr(self, ret):
        uc = self.uc
        lr = uc.reg_read(A64.UC_ARM64_REG_X30 if self.is64 else A.UC_ARM_REG_LR)
        uc.reg_write(self.rregs[0], ret & ((1 << (8 * self.w)) - 1))
        if self.is64:
            uc.reg_write(self.pc, lr)
        else:
            uc.reg_write(self.pc, lr & ~1)
            cpsr = uc.reg_read(A.UC_ARM_REG_CPSR)
            uc.reg_write(A.UC_ARM_REG_CPSR, (cpsr | 0x20) if lr & 1 else (cpsr & ~0x20))

    def _stub_hook(self, uc, addr, size, ud):
        name = self.stub_names.get(addr & ~1)
        if name is None:
            return
        name = ALIAS.get(name, name)
        if name.startswith("__ThumbV7PILongThunk_"):
            name = name[len("__ThumbV7PILongThunk_"):]
        args = [self._arg(i) for i in range(8 if self.is64 else 6)]
        ret = self._model(name, args)
        name2 = CANON.get(name, name)
        if name2 != name:
            name = name2
        if name in ('_ZN7android6Parcel5writeEPKvj', '_ZN7android6Parcel5writeEPKvm') and args[2] in (4, 8):
            try:
                val = int.from_bytes(bytes(uc.mem_read(args[1], args[2])), 'little')
            except UcError:
                val = None
            self.calls.append(('Parcel::writeInt%d' % (args[2] * 8), (val,)))
            self._ret_to_lr(ret)
            return
        if name in ('_ZN7android6Parcel10writeInt32Ei', '_ZN7android6Parcel11writeUint32Ej'):
            self.calls.append(('Parcel::writeInt32', (args[1] & 0xffffffff,)))
            self._ret_to_lr(ret)
            return
        if name in ('_ZN7android6Parcel10writeInt64El', '_ZN7android6Parcel11writeUint64Ey'):
            self.calls.append(('Parcel::writeInt64', (args[1] | (args[2] << 32) if not self.is64 else args[1],)))
            self._ret_to_lr(ret)
            return
        if name not in DROP and not (os.environ.get('MASKLOG') and name == '__android_log_print'):
            ign = IGNORE_ARGS.get(name, ())
            ar = arity(name)
            self.calls.append((name, tuple(self.norm(a) for i, a in enumerate(args[:ar]) if i not in ign)))
        self._ret_to_lr(ret)

    def _icall_hook(self, uc, addr, size, ud):
        self.calls.append((("ICALL", addr - ARENA), (self.norm(self._arg(0)),)))
        self._ret_to_lr(self._extret(("ICALL", addr)))

    def _extret(self, key):
        if self.mode == 0:
            return 0
        if self.mode == 2:
            return -1
        h = (sum(str(key[0]).encode()) * 131) & 0xff
        return ARENA + 0x30000 + h * 0x80

    def _alloc(self, n):
        i = self.nalloc
        self.nalloc += 1
        p = HEAP + (i % (HEAP_SZ // HSTRIDE)) * HSTRIDE
        self.uc.mem_write(p, b"\0" * min(max(n, 1), HSTRIDE))
        return p

    def _model(self, name, a):
        uc = self.uc
        if not self.is64 and re.search(r'^_ZN.*(C[12]|D[012])E', name) and name not in ALIAS:
            return a[0]
        m = (1 << (8 * self.w)) - 1

        def rdmem(p, n):
            try:
                return bytes(uc.mem_read(p, n))
            except UcError:
                return b"\0" * n
        if name in ("malloc", "new", "calloc", "PAL_MemAllocEx", "realloc"):
            n = {"malloc": a[0], "new": a[0], "calloc": a[0] * a[1], "PAL_MemAllocEx": a[1], "realloc": a[1]}[name]
            return self._alloc(min(n, HSTRIDE))
        if name in ("free", "delete", "PAL_MemFreeEx"):
            return 0
        if name in ("memcpy", "memmove"):
            if a[2] <= 0x4000:
                uc.mem_write(a[0], rdmem(a[1], a[2]))
            return a[0]
        if name == "memset":
            if a[2] <= 0x4000:
                uc.mem_write(a[0], bytes([a[1] & 0xff]) * a[2])
            return a[0]
        if name in ("__aeabi_memclr", "__aeabi_memclr4", "__aeabi_memclr8"):
            if a[1] <= 0x4000:
                uc.mem_write(a[0], b"\0" * a[1])
            return a[0]
        if name == "__aeabi_memset":
            if a[1] <= 0x4000:
                uc.mem_write(a[0], bytes([a[2] & 0xff]) * a[1])
            return a[0]
        if name == "strlen":
            return len(rdmem(a[0], 256).split(b"\0")[0])
        if name.startswith("pthread_"):
            return 0
        if name in DROP:
            return 0
        if name == "__android_log_print":
            return 1
        return self._extret((name,)) & m

    def run(self, name, args):
        img = self.img
        addr, _ = img.funcs[name]
        uc = self.uc
        uc.reg_write(self.sp, STACK + STACK_SZ - 0x1000)
        for i, v in enumerate(args[: (8 if self.is64 else 4)]):
            uc.reg_write(self.rregs[i], v)
        if self.is64:
            uc.reg_write(A64.UC_ARM64_REG_X30, RET_MAGIC)
            start = BASE + addr
        else:
            uc.reg_write(A.UC_ARM_REG_LR, RET_MAGIC | 1)
            start = (BASE + (addr & ~1)) | (addr & 1)
        try:
            uc.emu_start(start, RET_MAGIC, count=MAX_INSNS)
        except UcError as e:
            self.fault = str(e).split("(")[-1].rstrip(")")
        r0 = uc.reg_read(self.rregs[0])
        mem = {}
        for (a, s) in sorted(self.writes):
            b = bytes(uc.mem_read(a, s))
            if s == self.w:
                n = self.norm(int.from_bytes(b, "little"))
                key = None
                if isinstance(n, str) and n in ("IMG", "STUB", "STK"):
                    key = n
                elif isinstance(n, tuple) and n[0] in ("s", "V", "D", "H"):
                    key = n if n[0] != "s" else "IMG"
                if key is not None:
                    for i in range(s):
                        mem[a + i] = (key, i)
                    continue
            for i in range(s):
                mem[a + i] = b[i]
        if self.akind != 'rand':
            # 均勻 arena：位址與 layout 無關，改以寫入值的多重集合比較
            vals = sorted(repr(v) for k, v in mem.items() if not (ARENA <= k < ARENA + ARENA_SZ and not isinstance(v, tuple) and self.arena0[(k - ARENA) % self.w] == v))
            return {"ret": self.norm(r0), "fault": self.fault, "calls": self.calls, "mem": {"vals": vals}}
        out = {}
        for k, v in mem.items():
            if ARENA <= k < ARENA + ARENA_SZ and not isinstance(v, tuple) and self.arena0[k - ARENA] == v:
                continue
            out[("A", k - ARENA) if k < HEAP else ("H", (k - HEAP) // HSTRIDE, (k - HEAP) % HSTRIDE)] = v
        return {"ret": self.norm(r0), "fault": self.fault, "calls": self.calls, "mem": out}


def make_args(is64, seed):
    r = random.Random(seed * 7919 + 1)
    n = 8 if is64 else 4
    w = 8 if is64 else 4
    out = []
    for i in range(n):
        k = r.random()
        if i == 0 or k < 0.5:
            out.append(ARENA + (r.randrange(0x100, ARENA_SZ // 2) & ~(w - 1)))
        elif k < 0.85:
            out.append(r.choice([0, 1, 2, 3, 4, 5, 7, 8, 16, 32, 100, 255, 0x100, 0x1000]))
        else:
            out.append(r.getrandbits(32))
    return out


def run_one(img, name, seed, mode=None, akind='rand'):
    e = Emu(img, seed % 3 if mode is None else mode, seed, akind)
    return e.run(name, make_args(img.is64, seed))
