#!/usr/bin/env python3
"""事件比較：以兩種 stack/heap 填充 (0x00 / 0xA5) 的執行找出「未初始化垃圾」位元組並遮罩，再做萬用字元比對。"""
import difflib, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scen_ipj import *

def walk(x, out):
    if isinstance(x, Lazy):
        out.append(x)
    elif isinstance(x, (tuple, list)):
        for y in x:
            walk(y, out)

def lazies_of(sc):
    out = []
    for l, ev, w in sc.seg:
        for e in ev:
            walk(e, out)
    return out

def mask_lazies(sc0, sc1):
    """sc0 = fill 0x00 run, sc1 = fill 0xA5 run。逐 Lazy 比對，把差異處標成萬用字元 (None)。"""
    l0, l1 = lazies_of(sc0), lazies_of(sc1)
    if len(l0) != len(l1):
        return False
    for a, b in zip(l0, l1):
        va, vb = a.val, b.val
        if va == vb or not isinstance(va, tuple) or va[0] != vb[0]:
            a.mask = None
            continue
        if va[0] == "SER" and len(va[2]) == len(vb[2]):
            a.mask = {i for i in range(0, len(va[2]), 2) if va[2][i:i + 2] != vb[2][i:i + 2]}
        elif va[0] == "RAW" and len(va[2]) == len(vb[2]):
            a.mask = {i for i in range(len(va[2])) if va[2][i] != vb[2][i]}
        else:
            a.mask = None
    return True

def lz_eq(a, b):
    va, vb = a.val, b.val
    if va == vb:
        return True
    if not (isinstance(va, tuple) and isinstance(vb, tuple)) or va[0] != vb[0]:
        return False
    ma = getattr(a, "mask", None) or set()
    mb = getattr(b, "mask", None) or set()
    m = ma | mb
    if va[0] == "SER":
        if len(va[2]) != len(vb[2]):
            return False
        return all(i in m for i in range(0, len(va[2]), 2) if va[2][i:i + 2] != vb[2][i:i + 2])
    if va[0] == "RAW":
        if len(va[2]) != len(vb[2]):
            return False
        return all(i in m for i in range(len(va[2])) if va[2][i] != vb[2][i])
    return False

import re
LABEL = re.compile(r"^([A-Za-z]+)(\d+)(\+\d+)?$")

def eq(x, y, mp=None):
    """mp = (正向對照, 反向對照)：物件標籤須一致地一對一對應。"""
    if isinstance(x, Lazy) and isinstance(y, Lazy):
        return lz_eq(x, y)
    if isinstance(x, (tuple, list)) and isinstance(y, (tuple, list)):
        return len(x) == len(y) and all(eq(p, q, mp) for p, q in zip(x, y))
    if isinstance(x, str) and isinstance(y, str) and mp is not None:
        mx, my = LABEL.match(x), LABEL.match(y)
        if mx and my and mx.group(1) == my.group(1) and mx.group(3) == my.group(3):
            f, r = mp
            a, b = mx.group(1) + mx.group(2), my.group(1) + my.group(2)
            if f.setdefault(a, b) != b or r.setdefault(b, a) != a:
                return False
            return True
    return x == y

def key(e):
    def k(x):
        if isinstance(x, Lazy):
            return "<%s>" % x.kind
        if isinstance(x, (tuple, list)):
            return "(" + ",".join(k(y) for y in x) + ")"
        if isinstance(x, str):
            m = LABEL.match(x)
            if m:
                return repr(m.group(1) + "#" + (m.group(3) or ""))
        return repr(x)
    return k(e)

def diff_events(ea, eb):
    """回傳 hunks: [(tag, [orig events], [new events])]，equal 區塊也做萬用字元驗證。"""
    A = [key(e) for e in ea]
    B = [key(e) for e in eb]
    sm = difflib.SequenceMatcher(None, A, B, autojunk=False)
    out = []
    mp = ({}, {})
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            ok = all(eq(ea[i1 + t], eb[j1 + t], mp) for t in range(i2 - i1))
            if ok:
                out.append(("equal", ea[i1:i2], eb[j1:j2]))
            else:
                out.append(("replace", ea[i1:i2], eb[j1:j2]))
        else:
            out.append((tag, ea[i1:i2], eb[j1:j2]))
    return out

def run_masked(arch, seed, policy, steps):
    """回傳 (scenario_orig, scenario_new) — 已遮罩未初始化垃圾。"""
    res = {}
    for w in ("orig", "new"):
        p0 = dict(policy or {}); p0["fill"] = 0x00
        p1 = dict(policy or {}); p1["fill"] = 0xA5
        s0 = Scenario(f"{OD}/{w}/{arch}/libimageprocessorjni.so", seed, steps, p0).run()
        s1 = Scenario(f"{OD}/{w}/{arch}/libimageprocessorjni.so", seed, steps, p1).run()
        mask_lazies(s0, s1)
        res[w] = s0
    return res["orig"], res["new"]
