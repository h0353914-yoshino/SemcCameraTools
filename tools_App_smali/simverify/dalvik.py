#!/usr/bin/env python3
"""第 2 層：Dalvik 直譯器差分（主相機 app）。

對第 1 層未能證明相同的方法，原版與重建版各以相同種子化輸入執行，比對：
- 回傳值 / 未捕捉例外類別
- 外呼序列（invoke 的目標簽章與參數）
- 欄位寫入序列（iput / sput）

設計：
- 暫存器存放 Dalvik 原始位元（int/float/long/double 皆以位元表示），物件為 Python 物件
- Android framework / 其他 invoke 一律不展開，回傳由簽章決定的確定性值（兩邊相同）
- Build.VERSION.SDK_INT 固定為 35（執行於 Android 15 裝置的實際值）
- 無法模擬的指令（invoke-polymorphic / invoke-custom / method handle）→ unsupported

用法：
  python3 dalvik.py <orig_root> <new_root> <layer1.json> <out.json> [seeds=8]
"""
import json
import math
import random
import re
import struct
import sys
import zlib

import canon

MASK32 = 0xFFFFFFFF
MASK64 = 0xFFFFFFFFFFFFFFFF
MAX_STEPS = 20000
SDK_INT = 35
INPUT_OID_BASE = 10 ** 6


class Unsupported(Exception):
    pass


class JavaThrow(Exception):
    def __init__(self, cls):
        super().__init__(cls)
        self.cls = cls


# ---------- 數值工具 ----------

def s32(v):
    v &= MASK32
    return v - (1 << 32) if v & 0x80000000 else v


def s64(v):
    v &= MASK64
    return v - (1 << 64) if v & 0x8000000000000000 else v


def f_of(bits):
    return struct.unpack("<f", struct.pack("<I", bits & MASK32))[0]


def f_bits(x):
    try:
        return struct.unpack("<I", struct.pack("<f", x))[0]
    except OverflowError:
        return struct.unpack("<I", struct.pack("<f", math.copysign(math.inf, x)))[0]


def d_of(bits):
    return struct.unpack("<d", struct.pack("<Q", bits & MASK64))[0]


def d_bits(x):
    return struct.unpack("<Q", struct.pack("<d", x))[0]


def java_f2i(x, bits):
    if math.isnan(x):
        return 0
    lo, hi = (-(1 << 31), (1 << 31) - 1) if bits == 32 else (-(1 << 63), (1 << 63) - 1)
    if math.isinf(x) or x >= hi:
        return hi if x > 0 else lo
    if x <= lo:
        return lo
    return int(x)


def fdiv(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        if a == 0 or math.isnan(a):
            return math.nan
        return math.copysign(math.inf, a) * math.copysign(1.0, b)


def frem(a, b):
    if b == 0 or math.isinf(a) or math.isnan(a) or math.isnan(b):
        return math.nan
    if math.isinf(b):
        return a
    return math.fmod(a, b)


def cmp_fp(a, b, nan_result):
    if math.isnan(a) or math.isnan(b):
        return nan_result
    return (a > b) - (a < b)


def default_of(desc):
    return 0 if desc in ("Z", "B", "S", "C", "I", "J", "F", "D") else None


# ---------- 物件模型 ----------

class Obj:
    __slots__ = ("cls", "fields", "oid")

    def __init__(self, cls, oid, fields=None):
        self.cls = cls
        self.oid = oid
        self.fields = fields if fields is not None else {}

    def key(self):
        return ("o", self.cls, self.oid)


class Arr:
    __slots__ = ("elem", "items", "oid")

    def __init__(self, elem, items, oid):
        self.elem = elem
        self.items = items
        self.oid = oid

    def key(self):
        return ("a", self.elem, self.oid, tuple(norm(x) for x in self.items))


def norm(v):
    """正規化為可比較的值。負 id 為外部（stub）物件：只比類別，不比 id。"""
    if v is None or isinstance(v, (int, float, str)):
        return v
    if isinstance(v, Obj):
        return ("x", v.cls) if v.oid < 0 else v.key()
    if isinstance(v, Arr):
        return ("xa", v.elem) if v.oid < 0 else v.key()
    return repr(v)


# 已知的依賴遷移：重建版以 AndroidX 取代 android.arch（同一函式庫的改名，屬相容性差異）
COMPAT_RENAMES = (
    ("Landroid/arch/", "Landroidx/"),
    ("android$arch$", "androidx$"),
)


def compat(name):
    for a, b in COMPAT_RENAMES:
        name = name.replace(a, b)
    return name


# ---------- smali 方法解析 ----------

SIG_RE = re.compile(r"^\.method\s+(.*?)(\w+|<init>|<clinit>)\((.*)\)(.+)$")
DESC_RE = re.compile(r"\[*(?:[ZBSCIJFD]|L[^;]+;)")


class Method:
    def __init__(self):
        self.regcount = 0
        self.code = []        # [(op, arg)]
        self.labels = {}      # 標籤 -> 指令索引
        self.tries = []       # [(start, end, 例外型別或 None, handler 索引)]
        self.payloads = {}    # 標籤 -> ("packed", first, [標籤]) / ("sparse", {key: 標籤}) / ("array", [值])
        self.is_static = False
        self.params = []
        self.ret = "V"


def parse_method(lines):
    head = lines[0].strip()
    m = SIG_RE.match(head)
    if not m:
        raise Unsupported("sig")
    flags, name, params_s, ret = m.group(1), m.group(2), m.group(3), m.group(4)
    meth = Method()
    meth.is_static = "static" in flags.split()
    meth.params = DESC_RE.findall(params_s)
    meth.ret = ret
    pending_try = []
    raw_payloads = []
    pending_label = None
    payload = None
    skip_annot = False
    for raw in lines[1:-1]:
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        if skip_annot:
            if s == ".end annotation":
                skip_annot = False
            continue
        if s.startswith(".annotation"):
            skip_annot = True
            continue
        if payload is not None:
            if s.startswith(".end "):
                raw_payloads.append((payload["label"], payload["kind"], payload["head"], payload["lines"]))
                payload = None
            else:
                payload["lines"].append(s)
            continue
        if s.startswith(".registers"):
            meth.regcount = int(s.split()[1], 0)
            continue
        if s.startswith(".locals"):
            # 僅宣告區域暫存器數；總數 = 區域 + 參數槽（含 this）
            slots = (0 if meth.is_static else 1) + sum(2 if p in ("J", "D") else 1 for p in meth.params)
            meth.regcount = int(s.split()[1], 0) + slots
            continue
        if s.startswith((".line", ".local", ".end local", ".restart local", ".param", ".end param",
                         ".prologue", ".source")):
            continue
        if s.startswith(".catchall"):
            mm = re.match(r"\.catchall\s+\{(:\S+)\s+\.\.\s+(:\S+)\}\s+(:\S+)", s)
            pending_try.append((mm.group(1), mm.group(2), None, mm.group(3)))
            continue
        if s.startswith(".catch "):
            mm = re.match(r"\.catch\s+(L[^;]+;)\s+\{(:\S+)\s+\.\.\s+(:\S+)\}\s+(:\S+)", s)
            pending_try.append((mm.group(2), mm.group(3), mm.group(1), mm.group(4)))
            continue
        if s.startswith((".packed-switch", ".sparse-switch", ".array-data")):
            kind = s.split()[0][1:]
            payload = {"label": pending_label, "kind": kind, "head": s.split()[1:], "lines": [], "data": None}
            continue
        if s.startswith(":"):
            if s in meth.labels:
                raise Unsupported("dup-label")
            meth.labels[s] = len(meth.code)
            pending_label = s
            continue
        pending_label = None
        if s == "nop":
            meth.code.append(("nop", ""))
            continue
        parts = s.split(None, 1)
        meth.code.append((parts[0], parts[1] if len(parts) > 1 else ""))
    for start, end, typ, handler in pending_try:
        meth.tries.append((meth.labels[start], meth.labels[end], typ, meth.labels[handler]))
    finish_payloads(meth, raw_payloads)
    return meth


def finish_payloads(meth, raw):
    """raw: [(label, kind, head, lines)] → 解析為索引表。"""
    for label, kind, head, lines in raw:
        if kind == "packed-switch":
            first = int(head[0], 0)
            targets = [x for x in lines if x.startswith(":")]
            meth.payloads[label] = ("packed", first, [meth.labels[t] for t in targets])
        elif kind == "sparse-switch":
            table = {}
            for x in lines:
                k, t = [y.strip() for y in x.split("->")]
                table[int(k, 0)] = meth.labels[t]
            meth.payloads[label] = ("sparse", table)
        elif kind == "array-data":
            width = int(head[0], 0) if head else 4
            vals = []
            for x in lines:
                x = x.split("#", 1)[0].strip()
                if not x:
                    continue
                if x.endswith("f") and not x.lower().startswith("0x"):
                    vals.append(f_bits(float(x[:-1])) if width == 4 else d_bits(float(x[:-1])))
                else:
                    vals.append(int(x.rstrip("L"), 0))
            meth.payloads[label] = ("array", vals)


# ---------- 直譯器 ----------

ANDROID_STATIC = {
    ("Landroid/os/Build$VERSION;", "SDK_INT", "I"): SDK_INT,
}

BUILTIN_SUPER = {
    "Ljava/lang/Object;": None,
    "Ljava/lang/Throwable;": "Ljava/lang/Object;",
    "Ljava/lang/Exception;": "Ljava/lang/Throwable;",
    "Ljava/lang/Error;": "Ljava/lang/Throwable;",
    "Ljava/lang/RuntimeException;": "Ljava/lang/Exception;",
    "Ljava/lang/NullPointerException;": "Ljava/lang/RuntimeException;",
    "Ljava/lang/ArithmeticException;": "Ljava/lang/RuntimeException;",
    "Ljava/lang/IndexOutOfBoundsException;": "Ljava/lang/RuntimeException;",
    "Ljava/lang/ArrayIndexOutOfBoundsException;": "Ljava/lang/IndexOutOfBoundsException;",
    "Ljava/lang/NegativeArraySizeException;": "Ljava/lang/RuntimeException;",
    "Ljava/lang/ClassCastException;": "Ljava/lang/RuntimeException;",
    "Ljava/lang/IllegalArgumentException;": "Ljava/lang/RuntimeException;",
    "Ljava/lang/IllegalStateException;": "Ljava/lang/RuntimeException;",
}


class Interp:
    """單次執行。classes: 類別名 -> 父類名（由 smali .super 取得）。"""

    def __init__(self, supers):
        self.supers = supers
        self.oid = 0
        self.trace = []
        self.steps = 0
        self.last_result = None
        self.last_exc = None
        self.statics = {}
        self.base = 0
        self.last_pc = None

    def new_oid(self):
        self.oid += 1
        return self.oid

    def stub(self, sig, args, desc):
        """Android / 外部呼叫的確定性回傳值（兩邊相同）。"""
        h = zlib.crc32(("%s|%r" % (sig, [norm(a) for a in args])).encode())
        if desc == "V":
            return None
        if desc == "Z":
            return h & 1
        if desc in ("B", "S", "C", "I"):
            return s32(h)
        if desc == "J":
            return s64((h << 17) ^ 0x5A5A5A5A5A5A5A5A)
        if desc == "F":
            return f_bits(float(h % 1000) / 8.0)
        if desc == "D":
            return d_bits(float(h % 1000) / 8.0)
        if desc.startswith("["):
            return Arr(desc[1:], [], -h - 1)
        if desc == "Ljava/lang/String;":
            return "s%08x" % (h & MASK32)
        return Obj(desc, -h - 1)

    def is_subclass(self, sub, sup):
        cur, n = sub, 0
        while cur is not None and n < 64:
            if cur == sup:
                return True
            n += 1
            if cur in self.supers:
                cur = self.supers[cur]
            elif cur in BUILTIN_SUPER:
                cur = BUILTIN_SUPER[cur]
            else:
                raise Unsupported("hierarchy:" + cur)
        return False

    def run(self, meth, args):
        """args：依序的參數值（instance 方法 args[0] 為 this）。回傳 (ret, exc, trace)。"""
        self.regs = [None] * max(meth.regcount, 1)
        self.meth = meth
        slot_count = (0 if meth.is_static else 1) + sum(2 if p in ("J", "D") else 1 for p in meth.params)
        self.base = meth.regcount - slot_count
        if self.base < 0:
            raise Unsupported("regcount")
        idx, k = self.base, 0
        if not meth.is_static:
            self.regs[idx] = args[0]
            idx += 1
            k = 1
        for p in meth.params:
            self.regs[idx] = args[k]
            idx += 2 if p in ("J", "D") else 1
            k += 1
        return self.exec()

    def regnum(self, tok):
        tok = tok.strip()
        if tok.startswith("v"):
            return int(tok[1:])
        if tok.startswith("p"):
            return self.base + int(tok[1:])
        raise Unsupported("reg:" + tok)

    def regs_of(self, arg):
        """解析 {vX, vY} 或 {vX .. vY} 為暫存器索引列表。"""
        body = arg.split("}", 1)[0].lstrip("{")
        if ".." in body:
            a, b = [x.strip() for x in body.split("..")]
            return [self.regnum(a) + j for j in range(self.regnum(b) - self.regnum(a) + 1)]
        return [self.regnum(x) for x in body.split(",") if x.strip()]

    @staticmethod
    def lit(tok):
        tok = tok.strip().rstrip("L")
        neg = tok.startswith("-")
        t = tok[1:] if neg else tok
        v = int(t, 16) if t.lower().startswith("0x") else int(t)
        return -v if neg else v

    def exec(self):
        m = self.meth
        pc = 0
        while True:
            self.last_pc = pc
            self.steps += 1
            if self.steps > MAX_STEPS:
                return ("timeout",), None, self.trace
            if pc >= len(m.code):
                raise Unsupported("fall-off")
            op, arg = m.code[pc]
            try:
                res = self.step(op, arg, pc)
            except JavaThrow as e:
                handler = self.find_handler(pc, e.cls)
                if handler is None:
                    return None, e.cls, self.trace
                self.last_exc = Obj(e.cls, self.new_oid())
                pc = handler
                continue
            if res is None:
                pc += 1
            elif res[0] == "jump":
                pc = res[1]
            elif res[0] == "ret":
                return res[1], None, self.trace

    def find_handler(self, pc, exc_cls):
        for start, end, typ, handler in self.meth.tries:
            if start <= pc < end and (typ is None or self.is_subclass(exc_cls, typ)):
                return handler
        return None

    def step(self, op, arg, pc):
        R = self.regnum
        regs = self.regs
        if op == "nop":
            return None
        if op in ("move", "move/from16", "move/16", "move-wide", "move-wide/from16", "move-wide/16",
                  "move-object", "move-object/from16", "move-object/16"):
            a, b = [x.strip() for x in arg.split(",")]
            regs[R(a)] = regs[R(b)]
            return None
        if op in ("move-result", "move-result-wide", "move-result-object"):
            regs[R(arg)] = self.last_result
            return None
        if op == "move-exception":
            regs[R(arg)] = self.last_exc
            return None
        if op.startswith("const") and not op.startswith("const-string") and op not in (
                "const-class", "const-method-handle", "const-method-type"):
            a, b = [x.strip() for x in arg.split(",", 1)]
            v = self.lit(b)
            regs[R(a)] = s64(v) if op.startswith("const-wide") else s32(v)
            return None
        if op in ("const-string", "const-string/jumbo"):
            a, b = [x.strip() for x in arg.split(",", 1)]
            regs[R(a)] = b[1:-1]
            return None
        if op == "const-class":
            a, b = [x.strip() for x in arg.split(",", 1)]
            regs[R(a)] = ("class", b)
            return None
        if op in ("const-method-handle", "const-method-type", "invoke-polymorphic",
                  "invoke-polymorphic/range", "invoke-custom", "invoke-custom/range"):
            raise Unsupported(op)
        if op in ("monitor-enter", "monitor-exit"):
            if regs[R(arg)] is None:
                raise JavaThrow("Ljava/lang/NullPointerException;")
            return None
        if op == "check-cast":
            return None
        if op == "instance-of":
            a, b, typ = [x.strip() for x in arg.split(",")]
            obj = regs[R(b)]
            regs[R(a)] = 0 if not isinstance(obj, Obj) else int(self.is_subclass(obj.cls, typ))
            return None
        if op == "array-length":
            a, b = [x.strip() for x in arg.split(",")]
            arr = regs[R(b)]
            if arr is None:
                raise JavaThrow("Ljava/lang/NullPointerException;")
            regs[R(a)] = len(arr.items)
            return None
        if op == "new-instance":
            a, b = [x.strip() for x in arg.split(",", 1)]
            regs[R(a)] = Obj(b, self.new_oid())
            return None
        if op == "new-array":
            a, b, c = [x.strip() for x in arg.split(",")]
            n = regs[R(b)]
            if n < 0:
                raise JavaThrow("Ljava/lang/NegativeArraySizeException;")
            elem = c[1:]
            d = default_of(elem)
            regs[R(a)] = Arr(elem, [d] * n, self.new_oid())
            return None
        if op in ("filled-new-array", "filled-new-array/range"):
            elem = arg.split("}", 1)[1].split(",")[-1].strip()[1:]
            self.last_result = Arr(elem, [regs[i] for i in self.regs_of(arg)], self.new_oid())
            return None
        if op == "fill-array-data":
            a, b = [x.strip() for x in arg.split(",")]
            arr = regs[R(a)]
            if arr is None:
                raise JavaThrow("Ljava/lang/NullPointerException;")
            data = self.meth.payloads[b][1]
            if len(data) > len(arr.items):
                raise JavaThrow("Ljava/lang/ArrayIndexOutOfBoundsException;")
            arr.items[:len(data)] = data
            return None
        if op == "throw":
            obj = regs[R(arg)]
            if obj is None:
                raise JavaThrow("Ljava/lang/NullPointerException;")
            raise JavaThrow(obj.cls)
        if op in ("goto", "goto/16", "goto/32"):
            return ("jump", self.meth.labels[arg.strip()])
        if op.startswith("if-"):
            return self.do_if(op, arg)
        if op.startswith("return"):
            if op == "return-void":
                return ("ret", None)
            return ("ret", regs[R(arg)])
        if op in ("packed-switch", "sparse-switch"):
            a, label = [x.strip() for x in arg.split(",")]
            val = regs[R(a)]
            pl = self.meth.payloads[label]
            if pl[0] == "packed":
                i = val - pl[1]
                if 0 <= i < len(pl[2]):
                    return ("jump", pl[2][i])
            else:
                if val in pl[1]:
                    return ("jump", pl[1][val])
            return None
        if self.arith(op, arg):
            return None
        if op.startswith("aget"):
            a, b, c = [x.strip() for x in arg.split(",")]
            arr, i = regs[R(b)], regs[R(c)]
            if arr is None:
                raise JavaThrow("Ljava/lang/NullPointerException;")
            if not 0 <= i < len(arr.items):
                raise JavaThrow("Ljava/lang/ArrayIndexOutOfBoundsException;")
            regs[R(a)] = arr.items[i]
            return None
        if op.startswith("aput"):
            a, b, c = [x.strip() for x in arg.split(",")]
            arr, i = regs[R(b)], regs[R(c)]
            if arr is None:
                raise JavaThrow("Ljava/lang/NullPointerException;")
            if not 0 <= i < len(arr.items):
                raise JavaThrow("Ljava/lang/ArrayIndexOutOfBoundsException;")
            arr.items[i] = regs[R(a)]
            return None
        if op.startswith("iget"):
            dst, objr, fld = [x.strip() for x in arg.split(",")]
            o = regs[R(objr)]
            if o is None:
                raise JavaThrow("Ljava/lang/NullPointerException;")
            fname = fld.split("->", 1)[1].split(":")[0]
            fdesc = fld.rsplit(":", 1)[1]
            regs[R(dst)] = o.fields.get(fname, default_of(fdesc))
            return None
        if op.startswith("iput"):
            src, objr, fld = [x.strip() for x in arg.split(",")]
            o = regs[R(objr)]
            if o is None:
                raise JavaThrow("Ljava/lang/NullPointerException;")
            fname = fld.split("->", 1)[1].split(":")[0]
            v = regs[R(src)]
            o.fields[fname] = v
            self.trace.append(("iput", o.key(), fname, norm(v)))
            return None
        if op.startswith("sget"):
            dst, fld = [x.strip() for x in arg.split(",")]
            cls, rest = fld.split("->", 1)
            fname, fdesc = rest.split(":", 1)
            if (cls, fname, fdesc) in ANDROID_STATIC:
                regs[R(dst)] = ANDROID_STATIC[(cls, fname, fdesc)]
            elif (cls, fname) in self.statics:
                regs[R(dst)] = self.statics[(cls, fname)]
            else:
                regs[R(dst)] = self.stub("static:" + compat(fld), [], compat(fdesc))
            return None
        if op.startswith("sput"):
            src, fld = [x.strip() for x in arg.split(",")]
            cls, rest = fld.split("->", 1)
            fname, _ = rest.split(":", 1)
            v = regs[R(src)]
            self.statics[(cls, fname)] = v
            self.trace.append(("sput", compat(cls), compat(fname), norm(v)))
            return None
        if op.startswith("invoke-"):
            return self.do_invoke(op, arg)
        raise Unsupported("op:" + op)

    def do_if(self, op, arg):
        zero = op.endswith("z")
        kind = op[3:-1] if zero else op[3:]
        if zero:
            a, label = [x.strip() for x in arg.split(",")]
            va, vb = self.regs[self.regnum(a)], 0
        else:
            a, b, label = [x.strip() for x in arg.split(",")]
            va, vb = self.regs[self.regnum(a)], self.regs[self.regnum(b)]
        if kind in ("eq", "ne"):
            same = (va is vb) if (isinstance(va, (Obj, Arr)) or va is None or isinstance(va, tuple)) \
                else (va == vb)
            ok = same if kind == "eq" else not same
        else:
            if va is None or vb is None:
                raise JavaThrow("Ljava/lang/NullPointerException;")
            ok = {"lt": va < vb, "ge": va >= vb, "gt": va > vb, "le": va <= vb}[kind]
        return ("jump", self.meth.labels[label]) if ok else None

    def arith(self, op, arg):
        R = self.regnum
        regs = self.regs
        unary = {
            "neg-int": lambda x: s32(-x), "not-int": lambda x: s32(~x),
            "neg-long": lambda x: s64(-x), "not-long": lambda x: s64(~x),
            "neg-float": lambda x: f_bits(-f_of(x)), "neg-double": lambda x: d_bits(-d_of(x)),
            "int-to-long": lambda x: s64(x), "int-to-float": lambda x: f_bits(float(x)),
            "int-to-double": lambda x: d_bits(float(x)), "long-to-int": lambda x: s32(x),
            "long-to-float": lambda x: f_bits(float(x)), "long-to-double": lambda x: d_bits(float(x)),
            "float-to-int": lambda x: java_f2i(f_of(x), 32), "float-to-long": lambda x: java_f2i(f_of(x), 64),
            "float-to-double": lambda x: d_bits(f_of(x)), "double-to-int": lambda x: java_f2i(d_of(x), 32),
            "double-to-long": lambda x: java_f2i(d_of(x), 64), "double-to-float": lambda x: f_bits(d_of(x)),
            "int-to-byte": lambda x: ((x & 0xFF) ^ 0x80) - 0x80, "int-to-char": lambda x: x & 0xFFFF,
            "int-to-short": lambda x: ((x & 0xFFFF) ^ 0x8000) - 0x8000,
        }
        if op in unary:
            a, b = [x.strip() for x in arg.split(",")]
            regs[R(a)] = unary[op](regs[R(b)])
            return True
        if op == "cmp-long":
            a, b, c = [x.strip() for x in arg.split(",")]
            x, y = regs[R(b)], regs[R(c)]
            regs[R(a)] = (x > y) - (x < y)
            return True
        if op in ("cmpl-float", "cmpg-float", "cmpl-double", "cmpg-double"):
            a, b, c = [x.strip() for x in arg.split(",")]
            conv = f_of if "float" in op else d_of
            nr = -1 if op.startswith("cmpl") else 1
            regs[R(a)] = cmp_fp(conv(regs[R(b)]), conv(regs[R(c)]), nr)
            return True
        m2 = re.match(r"^(add|sub|mul|div|rem|and|or|xor|shl|shr|ushr|rsub)-(int|long|float|double)"
                      r"(/2addr|/lit16|/lit8)?$", op)
        if m2:
            name, typ, form = m2.group(1), m2.group(2), m2.group(3)
            parts = [x.strip() for x in arg.split(",")]
            if form is None:
                dst, x, y = parts
                xv, yv = regs[R(x)], regs[R(y)]
            elif form == "/2addr":
                dst, y = parts
                xv, yv = regs[R(dst)], regs[R(y)]
            else:
                dst, x, lit = parts
                xv, yv, typ = regs[R(x)], self.lit(lit), "int"
            regs[R(dst)] = self.binop(name, typ, xv, yv)
            return True
        return False

    @staticmethod
    def binop(name, typ, x, y):
        if name == "rsub":
            x, y, name = y, x, "sub"
        if typ in ("int", "long"):
            bits = 32 if typ == "int" else 64
            wrap = s32 if bits == 32 else s64
            mask = MASK32 if bits == 32 else MASK64
            if name in ("div", "rem"):
                if y == 0:
                    raise JavaThrow("Ljava/lang/ArithmeticException;")
                q = abs(x) // abs(y)
                q = q if (x >= 0) == (y >= 0) else -q
                return wrap(q if name == "div" else x - q * y)
            if name == "add":
                return wrap(x + y)
            if name == "sub":
                return wrap(x - y)
            if name == "mul":
                return wrap(x * y)
            if name == "and":
                return wrap(x & y)
            if name == "or":
                return wrap(x | y)
            if name == "xor":
                return wrap(x ^ y)
            sh = y & (bits - 1)
            if name == "shl":
                return wrap(x << sh)
            if name == "shr":
                return wrap(x >> sh)
            if name == "ushr":
                return wrap((x & mask) >> sh)
            raise Unsupported("op:" + name)
        conv, enc = (f_of, f_bits) if typ == "float" else (d_of, d_bits)
        a, b = conv(x), conv(y)
        if name == "add":
            r = a + b
        elif name == "sub":
            r = a - b
        elif name == "mul":
            r = a * b
        elif name == "div":
            r = fdiv(a, b)
        elif name == "rem":
            r = frem(a, b)
        else:
            raise Unsupported("fop:" + name)
        return enc(r)

    def do_invoke(self, op, arg):
        idx = self.regs_of(arg)
        sig = arg.split("}", 1)[1].strip().lstrip(",").strip()
        ccls, rest = sig.split("->", 1)
        mname, pr = rest.split("(", 1)
        params_s, ret = pr.split(")", 1)
        params = DESC_RE.findall(params_s)
        is_static = op.startswith("invoke-static")
        j, recv = 0, None
        if not is_static:
            recv = self.regs[idx[0]]
            j = 1
            if recv is None:
                raise JavaThrow("Ljava/lang/NullPointerException;")
        vals = []
        for p in params:
            vals.append(self.regs[idx[j]])
            j += 2 if p in ("J", "D") else 1
        full = compat("%s->%s(%s)%s" % (ccls, mname, params_s, ret))
        self.trace.append(("call", canon.ACCESSOR_RE.sub("->ACCESSOR(", full),
                           tuple(norm(v) for v in vals), None if recv is None else norm(recv)))
        if not is_static and isinstance(recv, Obj) and compat(ret) == recv.cls:
            # 流暢介面（如 StringBuilder.append）回傳接收者本身
            self.last_result = recv
        else:
            self.last_result = self.stub(full, vals if is_static else [recv] + vals, compat(ret))
        return None


# ---------- 輸入產生（兩邊共用同一份規格） ----------

INTS = [0, 1, -1, 2, 3, 7, 16, 255, -128, 65535, 0x7FFFFFFF, -0x80000000]
LONGS = [0, 1, -1, 1000, 0x7FFFFFFFFFFFFFFF, -0x8000000000000000]
FLOATS = [0.0, -0.0, 1.0, -1.5, 0.1, 1e30, math.nan, math.inf]


def gen_value(rng, desc, depth, classes):
    if desc in ("Z",):
        return rng.choice([0, 1])
    if desc in ("B", "S", "C", "I"):
        return rng.choice(INTS) if rng.random() < 0.7 else s32(rng.getrandbits(32))
    if desc == "J":
        return rng.choice(LONGS) if rng.random() < 0.7 else s64(rng.getrandbits(64))
    if desc == "F":
        return f_bits(rng.choice(FLOATS))
    if desc == "D":
        return d_bits(rng.choice(FLOATS))
    if desc.startswith("["):
        elem = desc[1:]
        n = rng.randint(0, 3)
        return ("arr", elem, [gen_value(rng, elem, depth, classes) for _ in range(n)]) \
            if elem in ("I", "J", "Z", "B", "S", "C", "F", "D") else ("arr", elem, [None] * n)
    if desc == "Ljava/lang/String;":
        return ("str", rng.choice(["", "a", "abc", "0", "com.sonyericsson"]))
    if rng.random() < 0.25 or depth > 1:
        return None
    return ("obj", desc, gen_fields(rng, desc, depth + 1, classes))


def gen_fields(rng, cls, depth, classes):
    out = {}
    for name, fdesc in classes.get(cls, {}).get("ifields", []):
        out[name] = gen_value(rng, fdesc, depth, classes)
    return out


def build(spec):
    """規格 → 執行期值。oid 依序分配（兩邊相同）。"""
    counter = [INPUT_OID_BASE]

    def mk(s):
        if s is None:
            return None
        kind = s[0]
        if kind == "arr":
            counter[0] += 1
            return Arr(s[1], [mk(x) if isinstance(x, tuple) else x for x in s[2]], counter[0])
        if kind == "str":
            return s[1]
        counter[0] += 1
        o = Obj(s[1], counter[0])
        for name, v in s[2].items():
            o.fields[name] = mk(v) if isinstance(v, tuple) else v
        return o
    return [mk(x) if isinstance(x, tuple) else x for x in spec]


def make_spec(sig_key, seed, method_is_static, params, classes, owner):
    rng = random.Random(zlib.crc32(("%s#%d" % (sig_key, seed)).encode()))
    spec = []
    if not method_is_static:
        spec.append(("obj", owner, gen_fields(rng, owner, 0, classes)))
    for p in params:
        spec.append(gen_value(rng, p, 0, classes))
    return spec


# ---------- 比對 ----------

def run_one(meth, spec, supers):
    interp = Interp(supers)
    args = build(spec)
    try:
        ret, exc, trace = interp.run(meth, args)
    except Unsupported as e:
        return ("unsupported", str(e))
    except (ValueError, IndexError, KeyError, TypeError, AttributeError, struct.error) as e:
        # 解析或模擬缺口：歸為 unsupported，附指令以供檢查
        op, arg = meth.code[interp.last_pc] if interp.last_pc is not None else ("?", "")
        return ("unsupported", "%s:%s @%s %s" % (type(e).__name__, e, op, arg))
    return ("ok", (norm(ret), exc, tuple(trace)))


def load_side(root):
    classes = {}
    supers = {}
    for dp, _, fns in __import__("os").walk(root):
        for fn in fns:
            if not fn.endswith(".smali"):
                continue
            path = __import__("os").path.join(dp, fn)
            text = open(path, encoding="utf-8", errors="replace").read()
            m = re.search(r"^\.class .*?(L[^;\s]+;)\s*$", text, re.M)
            if not m:
                continue
            cls = m.group(1)
            sup = re.search(r"^\.super (L[^;\s]+;)", text, re.M)
            supers[cls] = sup.group(1) if sup else None
            ifields = []
            for fm in re.finditer(r"^\.field (?!.*\bstatic\b)[^\n]*?(\w+):([^\s=]+)", text, re.M):
                ifields.append((fm.group(1), fm.group(2)))
            classes[cls] = {"ifields": ifields}
    return classes, supers


def main(argv):
    if len(argv) < 5:
        print(__doc__)
        return 1
    orig_root, new_root, l1_path, out_path = argv[1:5]
    seeds = int(argv[5]) if len(argv) > 5 else 8
    # 分片：argv[6] 形如 "i/n"，只處理 hash(key) % n == i 的方法（可平行執行）
    shard_i, shard_n = (0, 1)
    out_base = out_path
    if len(argv) > 6:
        shard_i, shard_n = [int(x) for x in argv[6].split("/")]
        out_path = "%s.shard%d" % (out_path, shard_i)
    l1 = json.load(open(l1_path, encoding="utf-8"))
    orig_classes, orig_supers = load_side(orig_root)
    _, new_supers = load_side(new_root)
    supers = dict(orig_supers)
    supers.update(new_supers)
    # 輸入欄位以原版為準（兩邊共用同一份規格）
    gen_classes = orig_classes
    orig_text = canon.collect_classes(orig_root)
    new_text = canon.collect_classes(new_root)
    # 續跑：載入所有分片既有檢查點，跳過已完成的方法（分片數可調整）
    import glob
    results = {}
    for ck in glob.glob(out_base + ".shard*.ckpt") + glob.glob(out_base + ".ckpt"):
        results.update(json.load(open(ck, encoding="utf-8"))["results"])
    counts = {}
    for v in results.values():
        counts[v["status"]] = counts.get(v["status"], 0) + 1
    done_since_ckpt = 0
    for cls, entry in l1["classes"].items():
        todo = [s for s, st in entry["methods"].items()
                if st == "diff" and "%s|%s" % (cls, s) not in results
                and zlib.crc32(("%s|%s" % (cls, s)).encode()) % shard_n == shard_i]
        if not todo:
            continue
        o_path, o_src = orig_text[cls]
        n_path, n_src = new_text[cls]
        _, o_methods = canon.split_methods(o_src)
        _, n_methods = canon.split_methods(n_src)
        for sig in todo:
            key = "%s|%s" % (cls, sig)
            try:
                om = parse_method(o_methods[sig][0])
                nm = parse_method(n_methods[sig][0])
            except (Unsupported, ValueError, IndexError, KeyError, AttributeError) as e:
                results[key] = {"status": "unsupported", "why": "parse:%s:%s" % (type(e).__name__, e)}
                counts["unsupported"] = counts.get("unsupported", 0) + 1
                continue
            if not om.code or not nm.code:
                # 抽象／原生方法沒有本體，只比對簽章與是否有本體
                st = "no-code" if (not om.code and not nm.code) else "diff"
                results[key] = {"status": st, "detail": {"orig_body": bool(om.code), "new_body": bool(nm.code)}}
                counts[st] = counts.get(st, 0) + 1
                continue
            static = om.is_static
            status, detail = "dyn_same", None
            for seed in range(seeds):
                spec = make_spec(key, seed, static, om.params, gen_classes, cls)
                ro = run_one(om, spec, supers)
                rn = run_one(nm, spec, supers)
                if ro[0] == "unsupported" or rn[0] == "unsupported":
                    status = "unsupported"
                    detail = {"orig": ro[1] if ro[0] == "unsupported" else None,
                              "new": rn[1] if rn[0] == "unsupported" else None}
                    break
                if ro[1] != rn[1]:
                    status = "diff"
                    detail = {"seed": seed, "orig": repr(ro[1])[:600], "new": repr(rn[1])[:600]}
                    break
            results[key] = {"status": status, "detail": detail}
            counts[status] = counts.get(status, 0) + 1
            done_since_ckpt += 1
            if done_since_ckpt >= 200:
                with open(out_path + ".ckpt", "w", encoding="utf-8") as f:
                    json.dump({"results": results}, f, ensure_ascii=False)
                done_since_ckpt = 0
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"counts": counts, "results": results}, f, ensure_ascii=False, indent=1)
    print("layer2 counts:", counts)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
