#!/usr/bin/env python3
"""把每個 flow 的原版/重建版軌跡差異輸出成文字檔 (.tmp/simverify/result/flows_<arch>.txt)。"""
import difflib, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scen_ipj import *
from cmp_ipj import *

def align(sa, sb):
    """依 label 對齊（同 label 的多段串接），順序以原版為準。"""
    def group(seg):
        d, order = {}, []
        for l, e, w in seg:
            if l not in d:
                d[l] = []
                order.append(l)
            d[l] += e
        return d, order
    da, oa = group(sa)
    db, ob = group(sb)
    labs = oa + [l for l in ob if l not in da]
    return [(l, da.get(l, []), db.get(l, [])) for l in labs]


def dump(arch, seed=0, policy=None, flows_sel=None, out=sys.stdout, with_log=False):
    policy = policy or {"happy": True}
    F = flows()
    for fl, steps in F.items():
        if flows_sel and fl not in flows_sel:
            continue
        a, b = run_masked(arch, seed, policy, steps)
        print("######## flow=%s arch=%s seed=%d faults=%s | %s" % (fl, arch, seed, a.m.fault, b.m.fault), file=out)
        for la, ea, eb in align(a.seg, b.seg):
            fa = [e for e in ea if e[0] not in ("sync", "free") and (with_log or e[0] != "log")]
            fb = [e for e in eb if e[0] not in ("sync", "free") and (with_log or e[0] != "log")]
            print("===== %s" % la.replace(JN, "n:"), file=out)
            for tag, ha, hb in diff_events(fa, fb):
                if tag == "equal":
                    print("   = (%d events)" % len(ha), file=out)
                    continue
                for x in ha:
                    print("  O- %s" % str(x)[:300], file=out)
                for x in hb:
                    print("  N+ %s" % str(x)[:300], file=out)

if __name__ == "__main__":
    arch = sys.argv[1]
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    sel = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    dump(arch, seed, flows_sel=sel)
