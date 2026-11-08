#!/usr/bin/env python3
"""gstat.py — 全函數靜態指紋差分（呼叫序列/字串/偏移/立即值）。輸出 .tmp/simverify/result/ctrl_gateway_static.json"""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gdis import Dis, fingerprint, ROOT

COMPAT = re.compile(r"^(_ZNSt3__1|_ZNK?7android8hardware7details13return_status|_ZNK7android8hardware6Status|__aeabi_mem|memcpy|memset|__aeabi_(i|l|u)?div|"
                    r"__stack_chk|__cxa|_ZN7android2spI|_ZN7android7RefBase(I|D)nc|_ZN7android7RefBase(inc|dec)Strong|sub_|__android_log|_ZNSt3__122__libcpp|_ZN7android12ANativeObject)")

def dem(names):
    return dict(zip(names, subprocess.run(["c++filt", "-n"], input="\n".join(names), capture_output=True, text=True).stdout.split("\n")))

def main():
    a, b = Dis("orig"), Dis("new")
    res = {}
    names = sorted(set(a.lib.syms) & set(b.lib.syms))
    for n in names:
        ea = [e for e in sorted(a.lib.syms[n]) if e[2] == "STT_FUNC"]
        eb = [e for e in sorted(b.lib.syms[n]) if e[2] == "STT_FUNC"]
        for i in range(min(len(ea), len(eb))):
            try:
                fa, fb = fingerprint(a, n, i), fingerprint(b, n, i)
            except Exception as e:
                res["%s#%d" % (n, i)] = {"err": repr(e)}; continue
            def fc(l): return [c for c in l if not COMPAT.match(c)]
            r = {"size": [ea[i][1], eb[i][1]],
                 "calls_same": fc(fa["calls"]) == fc(fb["calls"]),
                 "calls_orig": fc(fa["calls"]), "calls_new": fc(fb["calls"]),
                 "strs_orig": fa["strs"], "strs_new": fb["strs"],
                 "offs_only_orig": sorted(fa["offs"] - fb["offs"]), "offs_only_new": sorted(fb["offs"] - fa["offs"]),
                 "imms_only_orig": sorted(fa["imms"] - fb["imms"]), "imms_only_new": sorted(fb["imms"] - fa["imms"])}
            res["%s#%d" % (n, i)] = r
    out = ROOT + "/.tmp/simverify/result/ctrl_gateway_static.json"
    json.dump(res, open(out, "w"), indent=1)
    print(len(res), "pairs")
if __name__ == "__main__":
    main()
