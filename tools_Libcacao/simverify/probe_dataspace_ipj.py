#!/usr/bin/env python3
"""探測 prepareVideoRecording / prepareSuperSlowRecording 送出的 dataspace(_extra[2]) 與 frameNum(_extra[3])：原版 vs 重建版。"""
import itertools, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cmp_ipj import *

def run1(arch, w, kind, p, mode, out, fps, ss):
    steps = [("api", I("Initialize"), {2: 0})]
    if kind == "video":
        steps += [("api", I("ChangeToVideoMode"), {3: mode, 4: out[0], 5: out[1], 6: out[0], 7: out[1], 8: fps}),
                  ("api", I("RequestPrepareVideoRecording"), {3: "surface", 4: p[0], 5: p[1], 6: p[2]})]
    else:
        steps += [("api", I("ChangeToSuperSlowMode"), {3: mode, 4: out[0], 5: out[1], 6: out[0], 7: out[1], 8: fps, 9: ss[0], 10: ss[1]}),
                  ("api", I("RequestPrepareSuperSlowRecording"), {3: "surface", 4: p[0], 5: p[1], 6: p[2]})]
    sc = Scenario(f"{OD}/{w}/{arch}/libimageprocessorjni.so", 0, steps, {"happy": True, "fill": 0}).run()
    last = sc.seg[-1][1]
    for e in last:
        if e[0] == "vcall" and e[1] == "Process" and e[2] == 9:
            lz = []
            walk(e, lz)
            for z in lz:
                if z.kind == "obj" and z.val[0] == "SER":
                    h = z.val[2]
                    b = bytes.fromhex(h)
                    return int.from_bytes(b[344:348], "little"), int.from_bytes(b[348:352], "little") if len(b) >= 352 else None
    return None

if __name__ == "__main__":
    arch = sys.argv[1]
    rows = []
    for kind in ("video", "slow"):
        for p in itertools.product((0, 1), repeat=3):
            for out in ((1920, 1080), (1280, 720), (3840, 2160), (640, 480)):
                for mode in (0, 1):
                    for fps, ss in ((30, (960, 8)), (120, (480, 4))):
                        o = run1(arch, "orig", kind, p, mode, out, fps, ss)
                        n = run1(arch, "new", kind, p, mode, out, fps, ss)
                        rows.append({"kind": kind, "p": p, "out": out, "mode": mode, "fps": fps, "ss": ss, "orig": o, "new": n})
    json.dump(rows, open(f"{ROOT}/.tmp/simverify/result/probe_dataspace_{arch}.json", "w"), indent=1)
    bad = [r for r in rows if r["orig"] != r["new"]]
    print(arch, len(rows), "differ", len(bad))
    for r in bad[:40]:
        print(r)
