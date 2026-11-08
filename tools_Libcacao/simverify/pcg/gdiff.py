#!/usr/bin/env python3
"""diff2：對 libcacao_process_ctrl_gateway 做全函數差分（原版 vs 重建版）。
用法: python diff2.py [seeds=48] [only_substring]
輸出: .tmp/simverify/result/ctrl_gateway_fuzz.json
"""
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gemu import ARENA, BASE, Lib, Run
from grettype import is_void

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
D = ROOT + "/.tmp/simverify/"
MOD = "libcacao_process_ctrl_gateway"

# 相容性事件（重建版使用不同 libc++/HIDL 實作造成的外呼差異）：自軌跡濾除
COMPAT_RE = re.compile(
    r"^(_ZNSt3__1(12basic_string|21__basic_string_common)|"
    r"_ZNK?7android8hardware7details13return_status|_ZNK7android8hardware6Status11description|"
    r"_ZN7android8hardware7details13return_status|"
    r"_ZNSt3__1(19__libcpp_verbose|.*function)|"
    r"__aeabi_(i|l)div0|__aeabi_uidiv|__aeabi_idiv|__aeabi_uldiv|__aeabi_ldiv|PAL_TimeGetMonotonic|"
    r"_ZN5cacao10ObjectBaseC[12]Ev|_ZNK7android7RefBase9(inc|dec)Strong)")


def filt_events(ev):
    out = []
    for n, a in ev:
        if COMPAT_RE.match(n):
            continue
        out.append((n, a))
    return out


KNOWN_LOG_NORM = {
    "Convert error(or type Max):cacao to hidl": "convert-error",
    "Convert error:hidl to cacao": "convert-error",
    "invalid process type": "convert-error",
}


def norm_logs(lg):
    return [(m, l, KNOWN_LOG_NORM.get(f, f)) for (m, l, f) in lg]


def _hx(a):
    if isinstance(a, (list, tuple)):
        if len(a) == 3 and a[0] == "H":
            return ("H", "*", a[2])
        return tuple(_hx(x) for x in a)
    return a


def ev_cmp(ea, eb):
    """'SAME' / 'REORDER'（多重集合相同但順序不同）/ 'DIFF'"""
    if ea == eb:
        return "SAME"
    from collections import Counter as C
    ka = C((n, _hx(a)) for n, a in ea)
    kb = C((n, _hx(a)) for n, a in eb)
    if ka == kb:
        return "REORDER"
    # 虛擬 getter（uvt/匯入 vtable stub）呼叫次數不同但種類相同 → COUNT（純讀取的 CSE/重複呼叫差異）
    def strip(k):
        return C({x: (1 if "#" in x[0] else c) for x, c in k.items()})
    if strip(ka) == strip(kb):
        return "COUNT"
    return "DIFF"


def gen_args(seed, is_method):
    r = random.Random(seed * 1315423911 + 17)
    args = []
    for i in range(10):
        k = r.random()
        if i == 0 and is_method:
            args.append(ARENA + 0x40 * r.randrange(1, 600))
        elif k < 0.40:
            args.append(ARENA + 0x40 * r.randrange(1, 600))
        elif k < 0.75:
            args.append(r.randrange(0, 16))
        elif k < 0.85:
            args.append(0)
        elif k < 0.92:
            args.append(0xffffffff)
        else:
            args.append(0x80000000 | r.getrandbits(31))
    return args


def one(lib, ent, seed, is_method):
    r = Run(lib, seed)
    args = gen_args(seed, is_method)
    r0, r1 = r.call(ent, args)
    ev = filt_events(r.events)
    return {
        "ret": r.norm(r0), "fault": r.fault, "events": ev,
        "logs": r.logs, "allocs": r.allocs, "anom": r.anomalies,
        "mem": r.memdiff() if r.fault in (None,) else None,
        "insn_limit": r.fault == "insn_limit",
    }


def compare(a, b, skip_ret=False):
    tags = []
    # 事件共同前綴
    if a["fault"] == "insn_limit" or b["fault"] == "insn_limit":
        return ["UNSIM_LIMIT"], None
    ea, eb = a["events"], b["events"]
    ec = ev_cmp(ea, eb)
    if ec == "DIFF":
        tags.append("EVENTS")
    elif ec in ("REORDER", "COUNT"):
        tags.append(ec)
    if a["fault"] != b["fault"]:
        tags.append("FAULT")
    if norm_logs(a["logs"]) != norm_logs(b["logs"]):
        tags.append("LOGS")
    if a["allocs"] != b["allocs"]:
        # 只比較 new 的 size 序列與 del 次數
        sa = [x for x in a["allocs"] if x[0] == "new"]
        sb = [x for x in b["allocs"] if x[0] == "new"]
        if sa != sb:
            tags.append("ALLOC_SIZE")
        elif len([x for x in a["allocs"] if x[0] == "del"]) != len([x for x in b["allocs"] if x[0] == "del"]):
            tags.append("ALLOC_DEL")
    if a["anom"] != b["anom"]:
        tags.append("ANOM")
    if a["fault"] is None and b["fault"] is None:
        if a["ret"] != b["ret"] and not skip_ret:
            tags.append("RET")
        if a["mem"] != b["mem"]:
            tags.append("MEM")
    return tags, None


def pairs(la, lb):
    out = []
    for name in sorted(set(la.syms) & set(lb.syms)):
        ea = sorted(e for e in la.syms[name] if e[2] == "STT_FUNC")
        eb = sorted(e for e in lb.syms[name] if e[2] == "STT_FUNC")
        for i, (x, y) in enumerate(zip(ea, eb)):
            out.append((name, i, x, y))
    return out


def main():
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 48
    only = sys.argv[2] if len(sys.argv) > 2 else ""
    la = Lib(D + "orig/lib/%s.so" % MOD)
    lb = Lib(D + "new/lib/%s.so" % MOD)
    res = {"seeds": seeds, "funcs": {}}
    for name, i, x, y in pairs(la, lb):
        if only and only not in name:
            continue
        if name.startswith(("_Unwind", "unw_", "__aeabi_unwind", "decode_eht")):
            continue
        is_method = name.startswith(("_ZN", "_ZNK", "_ZThn", "_ZTv"))
        skip_ret = is_void(la.demangled().get(name, "").split("(")[0])
        agg = Counter()
        ex = {}
        for s in range(seeds):
            try:
                ra = one(la, x[0], s, is_method)
                rb = one(lb, y[0], s, is_method)
            except Exception as e:  # harness 自身錯誤
                agg["HARNESS_ERR"] += 1
                ex.setdefault("HARNESS_ERR", repr(e))
                continue
            tags, _ = compare(ra, rb, skip_ret)
            if not tags:
                agg["SAME"] += 1
                if ra["fault"]:
                    agg["SAME_FAULT"] += 1
                continue
            for t in tags:
                agg[t] += 1
            key = "+".join(tags)
            if key not in ex:
                ex[key] = {"seed": s, "orig": slim(ra), "new": slim(rb), "first_div": first_div(ra, rb)}
        res["funcs"]["%s#%d" % (name, i)] = {"size": [x[1], y[1]], "agg": dict(agg), "examples": ex}
    os.makedirs(D + "result", exist_ok=True)
    out = D + "result/ctrl_gateway_fuzz%s.json" % ("_" + only if only else "")
    json.dump(res, open(out, "w"), indent=1, default=str)
    cnt = Counter()
    for n, v in res["funcs"].items():
        a = v["agg"]
        real = [k for k in a if k not in ("SAME", "SAME_FAULT", "UNSIM_LIMIT")]
        cnt["DIFF" if real else ("UNSIM" if a.get("UNSIM_LIMIT", 0) and not a.get("SAME") else "OK")] += 1
    print("funcs", len(res["funcs"]), dict(cnt))


def first_div(ra, rb):
    ea, eb = ra["events"], rb["events"]
    i = 0
    while i < min(len(ea), len(eb)) and ea[i] == eb[i]:
        i += 1
    d = {"prefix": i, "n_orig": len(ea), "n_new": len(eb),
         "orig_next": ea[i:i + 3], "new_next": eb[i:i + 3]}
    return d


def slim(r):
    m = r["mem"]
    return {"ret": r["ret"], "fault": r["fault"], "events": r["events"][:25], "logs": r["logs"][:5],
            "allocs": r["allocs"][:8], "anom": r["anom"][:3],
            "mem": None if m is None else {str(k): v for k, v in list(m.items())[:30]}}


if __name__ == "__main__":
    main()
