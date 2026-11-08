#!/usr/bin/env python3
"""用法: diff.py <lib|lib64> <模組名> [seeds=20]  → .tmp/simverify/result/<arch>_<模組>.json
同名函數以相同種子輸入跑原版/重建版，比對 ret / fault / 外呼序列 / arena hash。"""
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from emu import SoImage, run_function

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
arch, mod = sys.argv[1], sys.argv[2]
seeds = int(sys.argv[3]) if len(sys.argv) > 3 else 20
od = f"{ROOT}/.tmp/simverify"
a = SoImage(f"{od}/orig/{arch}/{mod}.so")
b = SoImage(f"{od}/new/{arch}/{mod}.so")
res = {"only_orig": sorted(set(a.funcs) - set(b.funcs)), "only_new": sorted(set(b.funcs) - set(a.funcs)), "funcs": {}}
for n in sorted(set(a.funcs) & set(b.funcs)):
    diffs = []
    for s in range(seeds):
        try:
            ra, rb = run_function(a, n, s), run_function(b, n, s)
        except Exception as e:  # harness 自身錯誤
            diffs.append({"seed": s, "harness_error": repr(e)}); continue
        d = {k: [ra[k], rb[k]] for k in ("ret", "fault", "calls", "mem") if ra[k] != rb[k]}
        if d:
            diffs.append({"seed": s, **d})
    res["funcs"][n] = {"size": [a.funcs[n][1], b.funcs[n][1]], "ndiff": len(diffs), "diffs": diffs[:3]}
os.makedirs(f"{od}/result", exist_ok=True)
json.dump(res, open(f"{od}/result/{arch}_{mod}.json", "w"), indent=1, default=str)
bad = [n for n, v in res["funcs"].items() if v["ndiff"]]
print(f"{arch} {mod}: paired={len(res['funcs'])} differing={len(bad)} only_orig={len(res['only_orig'])} only_new={len(res['only_new'])}")
