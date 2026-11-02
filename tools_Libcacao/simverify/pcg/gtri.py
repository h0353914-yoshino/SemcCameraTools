#!/usr/bin/env python3
"""gtri.py <mangled-name> [seeds=4] [idx=0] — 單函數逐 seed 差異：首個分歧事件、ret、mem、log。"""
import subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gemu import Lib
import gdiff
from gdiff import one, compare, D, MOD

def dm(s):
    return subprocess.run(["c++filt", "-n"], input=str(s), capture_output=True, text=True).stdout.strip()

def main():
    name = sys.argv[1]; seeds = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    idx = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    la = Lib(D + "orig/lib/%s.so" % MOD); lb = Lib(D + "new/lib/%s.so" % MOD)
    if name not in la.syms or name not in lb.syms:
        m = [k for k in la.find(name) if k in lb.syms]
        if len(m) != 1:
            print("candidates:"); [print("  ", k, la.demangled().get(k)) for k in m]; return
        name = m[0]
    xa = sorted(e for e in la.syms[name] if e[2] == "STT_FUNC")[idx]
    xb = sorted(e for e in lb.syms[name] if e[2] == "STT_FUNC")[idx]
    print(dm(name))
    for s in range(seeds):
        ra = one(la, xa[0], s, True); rb = one(lb, xb[0], s, True)
        tags, _ = compare(ra, rb)
        print("seed", s, tags, "ret", ra["ret"], rb["ret"], "fault", ra["fault"], rb["fault"])
        if not tags or tags == ["UNSIM_LIMIT"]:
            continue
        ea, eb = ra["events"], rb["events"]
        i = 0
        while i < min(len(ea), len(eb)) and ea[i] == eb[i]:
            i += 1
        print("  events common prefix", i, "of", len(ea), len(eb))
        for side, e in (("orig", ea), ("new ", eb)):
            for ev in e[max(0, i - 1): i + 4]:
                print("   ", side, dm(ev[0])[:100], ev[1])
        if ra["logs"] != rb["logs"]:
            print("  logs orig", ra["logs"][:6]); print("  logs new ", rb["logs"][:6])
        if ra["allocs"] != rb["allocs"]:
            print("  allocs orig", ra["allocs"][:6]); print("  allocs new ", rb["allocs"][:6])
        if ra["anom"] != rb["anom"]:
            print("  anom orig", ra["anom"][:3]); print("  anom new ", rb["anom"][:3])
        ma, mb = ra["mem"], rb["mem"]
        if ma is not None and mb is not None and ma != mb:
            ks = sorted(set(ma) | set(mb), key=str)
            n = 0
            for k in ks:
                if ma.get(k) != mb.get(k):
                    print("   mem", k, "orig", ma.get(k), "new", mb.get(k)); n += 1
                    if n > 8: break
main()
