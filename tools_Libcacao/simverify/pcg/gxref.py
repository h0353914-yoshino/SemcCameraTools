#!/usr/bin/env python3
"""gxref.py <orig|new> <demangled-substr>  列出呼叫者（bl/blx/b 目標、含 veneer/PLT 解析）與 vtable/資料指標引用。"""
import sys, os, re, struct, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gdis import Dis, _fp_sym
import capstone as cs

def build(d):
    refs = {}
    for (a, sz, n) in d.lib.code:
        if sz < 2: continue
        md = d.t
        for i in md.disasm(d.img[a:a + sz], a):
            m, ops = i.mnemonic, i.op_str
            if m.startswith("b") and m not in ("bic", "bics", "bfi", "bfc", "bkpt", "bx"):
                mm = re.search(r"#(0x[0-9a-f]+)$", ops)
                if mm:
                    t = int(mm.group(1), 16)
                    if not (a <= t < a + sz):
                        refs.setdefault(_fp_sym(d, t), set()).add(n)
    # 資料指標（vtable 等）
    for off in range(0, len(d.img) - 4, 4):
        w = struct.unpack_from("<I", d.img, off)[0]
        if 0x10000000 <= w < 0x10000000 + len(d.img):
            nm = d.lib.addr_name(w - 0x10000000)
            if nm and "+" not in nm:
                holder = d.lib.addr_name(off) or ("data@%x" % off)
                refs.setdefault(nm, set()).add("[data]" + holder)
    return refs

if __name__ == "__main__":
    d = Dis(sys.argv[1])
    refs = build(d)
    dem = d.lib.demangled()
    for k, cl in refs.items():
        if sys.argv[2] in dem.get(k, k) or sys.argv[2] in k:
            print(dem.get(k, k)[:120])
            for c in sorted(cl):
                print("    <-", subprocess.run(["c++filt", "-n", c.replace("[data]", "")], capture_output=True, text=True).stdout.strip()[:110], "(data)" if c.startswith("[data]") else "")
