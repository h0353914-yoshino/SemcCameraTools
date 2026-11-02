#!/usr/bin/env python3
"""用法: cdiff.py <lib|lib64> <模組> [seeds=18]  → .tmp/simverify/cs/result/c_<arch>_<模組>.json"""
import json, os, sys
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(__file__))
from cemu import Img, run_one, demangle

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OD = f"{ROOT}/.tmp/simverify"
arch, mod = sys.argv[1], sys.argv[2]
SEEDS = int(sys.argv[3]) if len(sys.argv) > 3 else 18
A = Img(f"{OD}/orig/{arch}/{mod}.so")
B = Img(f"{OD}/new/{arch}/{mod}.so")


UNI = ['ptr', 0, 1, 0xffffffff]


def classify(ra, rb):
    d = []
    if ra["fault"] != rb["fault"]:
        d.append("fault")
    if ra["fault"] is None and rb["fault"] is None and ra["ret"] != rb["ret"]:
        d.append("ret")
    ca, cb = [repr(c) for c in ra["calls"]], [repr(c) for c in rb["calls"]]
    if ca != cb:
        d.append("reorder" if sorted(ca) == sorted(cb) else "calls")
    if ra["mem"] != rb["mem"] and ra["fault"] is None and rb["fault"] is None:
        d.append("mem")
    return d


def work(item):
    name = item
    out = {"name": name, "seeds": []}
    for s in range(SEEDS):
        akind = 'rand' if s < SEEDS // 2 else UNI[(s - SEEDS // 2) % len(UNI)]
        try:
            ra = run_one(A, name, s, akind=akind)
            rb = run_one(B, name, s, akind=akind)
        except Exception as e:
            out["seeds"].append({"seed": s, "cls": ["err"], "err": repr(e)})
            continue
        cls = classify(ra, rb)
        rec = {"seed": s, "akind": str(akind), "cls": cls, "faultA": ra["fault"], "faultB": rb["fault"]}
        if cls:
            ca, cb = ra["calls"], rb["calls"]
            k = 0
            while k < min(len(ca), len(cb)) and repr(ca[k]) == repr(cb[k]):
                k += 1
            rec["div"] = {"idx": k, "lenA": len(ca), "lenB": len(cb), "A": ca[max(0, k - 2):k + 3], "B": cb[max(0, k - 2):k + 3]}
            rec["A"] = {"ret": ra["ret"], "calls": ra["calls"][:14], "mem": sorted(ra["mem"].items(), key=str)[:8]}
            rec["B"] = {"ret": rb["ret"], "calls": rb["calls"][:14], "mem": sorted(rb["mem"].items(), key=str)[:8]}
        out["seeds"].append(rec)
    return out


def uniq(img, other):
    res = {}
    for n in sorted(set(img.funcs) - set(other.funcs)):
        res.setdefault(img.funcs[n][0], []).append(n)
    return [{"addr": hex(a), "size": img.funcs[ns[0]][1], "names": [demangle(x) for x in ns][:4], "mangled": ns[0]}
            for a, ns in sorted(res.items())]


if __name__ == "__main__":
    common = sorted(set(A.funcs) & set(B.funcs))
    groups = {}
    for n in common:
        groups.setdefault((A.funcs[n][0], B.funcs[n][0]), []).append(n)
    reps = [v[0] for v in groups.values()]
    with Pool(8) as p:
        res = p.map(work, reps, chunksize=2)
    funcs = {}
    for r, v in zip(res, groups.values()):
        clss = {}
        for s in r["seeds"]:
            for c in s["cls"]:
                k = c + ("@rand" if s.get("akind") == "rand" else "@uni")
                clss[k] = clss.get(k, 0) + 1
        r["aliases"] = v
        r["classes"] = clss
        r["nfault_seeds"] = sum(1 for s in r["seeds"] if s.get("faultA") or s.get("faultB"))
        r["demangled"] = demangle(v[0])
        r["size"] = [A.funcs[v[0]][1], B.funcs[v[0]][1]]
        funcs[r["name"]] = r
    out = {"arch": arch, "mod": mod, "seeds": SEEDS, "funcs": funcs,
           "only_orig": uniq(A, B), "only_new": uniq(B, A)}
    os.makedirs(f"{OD}/cs/result", exist_ok=True)
    json.dump(out, open(f"{OD}/cs/result/c{os.environ.get("MASKLOG","")}_{arch}_{mod}.json", "w"), indent=1, default=str)
    nd = [n for n, v in funcs.items() if v["classes"]]
    print(arch, mod, "groups", len(funcs), "differing", len(nd), "only_orig", len(out["only_orig"]), "only_new", len(out["only_new"]))
