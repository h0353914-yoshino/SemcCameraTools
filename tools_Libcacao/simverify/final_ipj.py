#!/usr/bin/env python3
"""彙整 libimageprocessorjni 差分結果 -> .tmp/simverify/result/ipj_<arch>.json"""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scen_ipj import *
from dumpflows_ipj import align
from cmp_ipj import *
import difflib

TOOLCHAIN = re.compile(r"^(_Unwind|_ZN9libunwind|_ZL13unwind|__ThumbV7PI|__aeabi|__emutls|__on_dlclose|pthread_atfork|atexit|__atexit|_ZSt28__throw|_ZNSt3__1|_ZL8snprintf|_ZN7android2sp|_ZNK?7android(12SortedVector|6Vector)|_ZN7android12SortedVector)")

def func_stats(arch):
    o = Lib(f"{OD}/orig/{arch}/libimageprocessorjni.so")
    n = Lib(f"{OD}/new/{arch}/libimageprocessorjni.so")
    canon = lambda x: Machine._canon(x)
    on = {canon(k): k for k in o.syms}
    nn = {canon(k): k for k in n.syms}
    common = sorted(set(on) & set(nn))
    only_o = sorted(set(on) - set(nn))
    only_n = sorted(set(nn) - set(on))
    return o, n, {
        "orig_total": len(o.syms), "new_total": len(n.syms), "paired": len(common),
        "only_orig": only_o, "only_new": only_n,
        "orig_toolchain": sum(1 for k in o.syms if TOOLCHAIN.match(k)),
        "new_toolchain": sum(1 for k in n.syms if TOOLCHAIN.match(k)),
        "exports_orig": len(o.exports), "exports_new": len(n.exports),
    }

def run_flows(arch, policy, seeds):
    agg = collections.OrderedDict()
    cov = {"orig": set(), "new": set()}
    for fl, steps in flows().items():
        for seed in seeds:
            a, b = run_masked(arch, seed, policy, steps)
            for w, sc in (("orig", a), ("new", b)):
                for addr in sc.m.cov:
                    cov[w].add(addr - BASE)
            for l, ea, eb in align(a.seg, b.seg):
                fa = [e for e in ea if e[0] not in ("sync", "free", "log")]
                fb = [e for e in eb if e[0] not in ("sync", "free", "log")]
                la = [e[1:] for e in ea if e[0] == "log"]
                lb = [e[1:] for e in eb if e[0] == "log"]
                key = l.replace(JN, "n:")
                d = agg.setdefault(key, {"n": 0, "equal": 0, "log_equal": 0, "flows": {}, "sigs": {}})
                d["n"] += 1
                hunks = diff_events(fa, fb)
                ok = all(h[0] == "equal" for h in hunks)
                d["equal"] += ok
                d["log_equal"] += (la == lb)
                f = d["flows"].setdefault(fl, [0, 0])
                f[0] += 1
                f[1] += ok
                if not ok:
                    sg = json.dumps([[[key_(x) for x in h[1]], [key_(x) for x in h[2]]] for h in hunks if h[0] != "equal"], ensure_ascii=False)
                    dd = d["sigs"].setdefault(sg, 0)
                    d["sigs"][sg] = dd + 1
    return agg, cov

def key_(e):
    return key(e)[:200]

def coverage(lib, covset):
    seen = set()
    for off in covset:
        f = lib.func_at(off)
        if f:
            seen.add(f[0])
    return seen

if __name__ == "__main__":
    arch = sys.argv[1]
    o, n, fs = func_stats(arch)
    happy, cov1 = run_flows(arch, {"happy": True}, [0, 1, 2])
    fail, cov2 = run_flows(arch, {}, list(range(10, 22)))
    covo = coverage(o, cov1["orig"] | cov2["orig"])
    covn = coverage(n, cov1["new"] | cov2["new"])
    fs["orig_covered"] = len(covo)
    fs["new_covered"] = len(covn)
    fs["orig_uncovered_project"] = sorted(k for k in o.syms if k not in covo and not TOOLCHAIN.match(k))
    fs["new_uncovered_project"] = sorted(k for k in n.syms if k not in covn and not TOOLCHAIN.match(k))
    out = {"arch": arch, "funcs": fs, "happy": happy, "fail_injection": fail}
    json.dump(out, open(f"{ROOT}/.tmp/simverify/result/ipj_{arch}.json", "w"), indent=1, default=str)
    print(arch, {k: v for k, v in fs.items() if not isinstance(v, list)})
    for k, v in happy.items():
        print("%-60s n=%d equal=%d log_equal=%d" % (k[:60], v["n"], v["equal"], v["log_equal"]))
