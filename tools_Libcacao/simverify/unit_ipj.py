#!/usr/bin/env python3
"""單元差分：callback 類別的 C1/C2/D0/D1/D2、getJNIEnv、getSurface、JNI_OnLoad。"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scen_ipj import *

CLASSES = ["BurstCallback", "SnapshotCallback", "VideoFinishCallback", "SnapshotFreeCallback", "VideoPrepareCallback",
           "SnapshotReadyCallback", "VideoStartRecCallback", "BurstShotFinishCallback", "BurstShotPrepareCallback",
           "VideoPrepareSuperSlowCallback", "VideoStartSuperSlowRecCallback"]

def mangle(c, k):
    return "_ZN14imageprocessor%d%s%sEv" % (len(c), c, k)

def vt_names(m, vt, n):
    out = []
    for k in range(n):
        f = m.rdw(vt + k * m.w)
        if BASE <= f < BASE + m.lib.size:
            out.append("CODE")
        elif STUB_BASE <= f < STUB_BASE + STUB_SZ:
            out.append("S:" + m.stub_by_addr.get(f & ~1, "?"))
        else:
            out.append(f)
    return out

def run(arch):
    res = {}
    for c in CLASSES:
        row = {}
        for w in ("orig", "new"):
            lib = Lib(f"{OD}/{w}/{arch}/libimageprocessorjni.so")
            m = Machine(lib, 0, {"happy": True})
            obj = m.malloc(0x80, "obj")
            m.call(mangle(c, "C2"), "p", [obj], "C2")
            vt = m.rdw(obj)
            first = m.rd(obj + m.w, 0x20)
            ev1 = [e for e in m.events]
            sz = lib.syms.get(mangle(c, "C2"), (0, 0))[1]
            # 每個 slot 行為: 以 slot 函式名稱判斷是否為 class 專屬、是否空函式
            slots = []
            for k in range(0, 8):
                f = m.rdw(vt + k * m.w)
                fn = lib.func_at((f & ~1) - BASE) if BASE <= f < BASE + lib.size else None
                slots.append(re.sub(r"^_ZN?K?(?:Thn\d+_)?", "", fn[0])[:60] if fn else str(m.norm(f)))
            # D2 / D1 / D0
            outs = {}
            for k in ("D2", "D1", "D0"):
                m2 = Machine(lib, 0, {"happy": True})
                o2 = m2.malloc(0x80, "obj")
                m2.call(mangle(c, "C2"), "p", [o2], "C2")
                m2.events.clear()
                s = mangle(c, k)
                if s in lib.syms:
                    m2.call(s, "p", [o2], k, record_ret=False)
                    outs[k] = [str(e) for e in m2.events]
                else:
                    outs[k] = "NOSYM"
            row[w] = {"events_C2": [str(e) for e in ev1], "tail_zero": first == b"\0" * 0x20, "dtor": outs, "slots": slots}
        res[c] = row
    return res

if __name__ == "__main__":
    arch = sys.argv[1]
    r = run(arch)
    json.dump(r, open(f"{ROOT}/.tmp/simverify/result/unit_ctor_{arch}.json", "w"), indent=1)
    for c, row in r.items():
        o, n = row["orig"], row["new"]
        same = (o["events_C2"] == n["events_C2"] and o["tail_zero"] == n["tail_zero"])
        dsame = all(o["dtor"][k] == n["dtor"][k] for k in o["dtor"])
        print("%-34s C2 same=%s dtor same=%s" % (c, same, dsame))
        if not dsame:
            for k in o["dtor"]:
                if o["dtor"][k] != n["dtor"][k]:
                    print("   ", k, "O:", o["dtor"][k], "N:", n["dtor"][k])
