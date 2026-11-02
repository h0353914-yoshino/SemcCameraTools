import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_diff as R
which, prog, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
fail = None
R.WARM = which == "cammw"
if len(sys.argv) > 4:
    fail = {(sys.argv[4], int(sys.argv[5])): 1}
import importlib
P = importlib.import_module("progs_cammw" if which == "cammw" else "progs_ckb")
mk = getattr(P, prog)
ms = []
for v in ("orig", "new"):
    ms.append(R.run_one(R.SV + "/%s/lib/%s" % (v, R.LIBS[which]), mk(seed), fail, hot=os.environ.get("HOT")=="1"))
d = R.compare(ms[0].obs, ms[1].obs)
print("DIFF:", d)
idx = d["idx"] if d and "idx" in d else 0
for v, m in zip(("orig", "new"), ms):
    print("=====", v)
    for i, o in enumerate(m.obs):
        if os.environ.get("ALL") != "1" and (i < idx or i > idx):
            continue
        print(i, o["call"], "ret", o["ret"], "fault", o["fault"])
        for e in o["events"]:
            print("    ", e)
