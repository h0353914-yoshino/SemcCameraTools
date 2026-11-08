#!/usr/bin/env python3
"""dis.py <orig|new> <mangled-name | 0xaddr> [idx]  — 帶註解的 ARM/Thumb 反組譯。
  * bl/blx/b 目標：符號 → PLT(GOT reloc 符號) → veneer 追蹤
  * ldr rX,[pc,#n] + add rX,pc 的字串/符號常值解析
"""
import os
import struct
import subprocess
import sys

import capstone as cs

sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gemu import Lib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
D = ROOT + "/.tmp/simverify/"
MOD = "libcacao_process_ctrl_gateway"


def demangle(s):
    return subprocess.run(["c++filt", "-n"], input=s, capture_output=True, text=True).stdout.strip()


class Dis:
    def __init__(self, ver, mod=MOD):
        self.lib = Lib(D + "%s/lib/%s.so" % (ver, mod))
        self.img = bytes(self.lib.image)
        self.t = cs.Cs(cs.CS_ARCH_ARM, cs.CS_MODE_THUMB)
        self.a = cs.Cs(cs.CS_ARCH_ARM, cs.CS_MODE_ARM)
        self.t.detail = self.a.detail = True
        self.got = {}
        for off, t, sym, add in self.lib.img.relocs:
            if t in (21, 22) and sym:
                self.got[off] = sym
        self.plt_cache = {}

    def sym(self, a):
        # a = lib offset (去 thumb bit)
        n = self.lib.addr_name(a)
        return n

    def u32(self, off):
        return struct.unpack_from("<I", self.img, off)[0]

    def plt_target(self, a):
        """a 為 ARM PLT 入口 (add ip,pc,#; add ip,ip,#; ldr pc,[ip,#]!) → GOT reloc 符號。"""
        if a in self.plt_cache:
            return self.plt_cache[a]
        r = None
        if a + 12 <= len(self.img):
            w0, w1, w2 = struct.unpack_from("<III", self.img, a)
            if (w0 >> 20) == 0xe28 and (w1 >> 20) == 0xe28 and (w2 & 0xfffff000) == 0xe5bcf000:
                def imm(w):
                    v, rot = w & 0xff, ((w >> 8) & 0xf) * 2
                    return ((v >> rot) | (v << (32 - rot))) & 0xffffffff if rot else v
                got = a + 8 + imm(w0) + imm(w1) + (w2 & 0xfff)
                r = self.got.get(got)
        self.plt_cache[a] = r
        return r

    def resolve(self, a, depth=0):
        """bl/b 目標 → 名稱字串。"""
        n = self.sym(a)
        if n:
            return n
        r = self.plt_target(a)
        if r:
            return "PLT:" + r
        # Thumb->ARM veneer: bx pc; nop; ldr ip,[pc]; add pc,ip,pc ; .word off
        if self.img[a:a + 2] == b"\x78\x47" and self.img[a + 4:a + 8] == bytes.fromhex("00c09fe5") and depth < 3:
            w = self.u32(a + 12)
            return "veneer->" + self.resolve((w + a + 16) & 0xffffffff, depth + 1)
        # veneer / 內部 stub：看前幾條指令
        if depth < 3:
            try:
                for md in (self.t, self.a):
                    ins = list(md.disasm(self.img[a:a + 12], a))
                    if ins and ins[0].mnemonic in ("b", "b.w", "bx", "ldr") and depth < 2 and ins[0].mnemonic in ("b", "b.w"):
                        import re
                        m = re.search(r"#(0x[0-9a-f]+)", ins[0].op_str)
                        if m:
                            return "veneer->" + self.resolve(int(m.group(1), 16), depth + 1)
            except Exception:
                pass
        return "sub_%x" % a

    def lines(self, name_or_addr, idx=0):
        if name_or_addr.startswith("0x"):
            addr, size = int(name_or_addr, 16), 0x100
            ents = [(addr, size)]
        else:
            m = self.lib.find(name_or_addr)
            if len(m) > 1:
                m = [k for k in m if not k.startswith(("_ZThn", "_ZTv", "_ZTh"))] or m
            if len(m) != 1:
                raise SystemExit("candidates:\n" + "\n".join("  %s %s" % (k, self.lib.demangled().get(k)) for k in m))
            ents = [(e[0], e[1]) for e in sorted(self.lib.syms[m[0]]) if e[2] == "STT_FUNC"]
        addr, size = ents[idx]
        thumb = addr & 1
        a0 = addr & ~1
        md = self.t if thumb else self.a
        out = []
        regs = {}
        for i in md.disasm(self.img[a0:a0 + size], a0):
            note = ""
            m = i.mnemonic
            ops = i.op_str
            if m in ("bl", "blx", "b", "b.w", "bne", "beq") or m.startswith("b") and i.group(cs.CS_GRP_JUMP) or m == "bl":
                import re
                mm = re.search(r"#(0x[0-9a-f]+)", ops)
                if mm and m.startswith(("bl", "b")) and m not in ("bic", "bics", "bfi", "bfc"):
                    t = int(mm.group(1), 16)
                    note = "  ; -> " + demangle(self.resolve(t))
            if m.startswith("ldr") and "[pc" in ops:
                import re
                mm = re.search(r"(\w+), \[pc, #(-?0x[0-9a-f]+|-?\d+)\]", ops)
                if mm:
                    base = (i.address + (4 if thumb else 8)) & ~3
                    v = self.u32(base + int(mm.group(2), 0))
                    regs[mm.group(1)] = v
                    note = "  ; lit=0x%x" % v
            if m == "add" and ops.endswith(", pc"):
                r = ops.split(",")[0]
                if r in regs:
                    t = (regs[r] + i.address + (4 if thumb else 8)) & 0xffffffff
                    regs[r] = t
                    s = self.lib.cstr(t, 64) if t < len(self.img) else ""
                    nm = self.sym(t)
                    note = "  ; => 0x%x %s" % (t, nm or (repr(s) if s and s.isprintable() and len(s) > 2 else ""))
            out.append("%x: %-8s %s%s" % (i.address, m, ops, note))
        return out


if __name__ == "__main__":
    d = Dis(sys.argv[1])
    print("\n".join(d.lines(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 0)))


# ------------------------------------------------------------------
# 靜態指紋：呼叫序列 / 字串常值 / 結構偏移 / 立即值
# ------------------------------------------------------------------
import re as _re


def _fp_sym(d, t):
    n = d.resolve(t)
    while n.startswith("veneer->"):
        n = n[8:]
    if n.startswith("PLT:"):
        n = n[4:]
    return n


def fingerprint(d, name, idx=0, inline_depth=0, _seen=None):
    """回傳 dict(calls=[...], strs=[...], offs=set, imms=set)；calls 為已解 veneer/PLT 的符號名。"""
    ents = [e for e in sorted(d.lib.syms[name]) if e[2] == "STT_FUNC"]
    addr, size = ents[idx][0], ents[idx][1]
    return fingerprint_addr(d, addr, size)


def fingerprint_addr(d, addr, size):
    thumb = addr & 1
    a0 = addr & ~1
    md = d.t if thumb else d.a
    calls, strs, offs, imms = [], [], set(), set()
    regs = {}
    for i in md.disasm(d.img[a0:a0 + size], a0):
        m, ops = i.mnemonic, i.op_str
        mm = _re.search(r"#(0x[0-9a-f]+)$", ops)
        if (m in ("bl", "blx", "b", "b.w") or (m.startswith("b") and m not in ("bic", "bics", "bfi", "bfc", "bkpt", "bx", "blx"))) and mm:
            t = int(mm.group(1), 16)
            if not (a0 <= t < a0 + size):                    # 函式內部跳轉不算呼叫
                calls.append(_fp_sym(d, t))
        if m.startswith("ldr") and "[pc" in ops:
            q = _re.search(r"(\w+), \[pc, #(-?0x[0-9a-f]+|-?\d+)\]", ops)
            if q:
                base = (i.address + (4 if thumb else 8)) & ~3
                regs[q.group(1)] = d.u32(base + int(q.group(2), 0))
        if m == "add" and ops.endswith(", pc"):
            r = ops.split(",")[0]
            if r in regs:
                t = (regs[r] + i.address + (4 if thumb else 8)) & 0xffffffff
                if t < len(d.img):
                    s = d.lib.cstr(t, 120)
                    if len(s) > 2 and all(32 <= ord(c) < 127 or c in "\n\t" for c in s):
                        strs.append(s)
        q = _re.match(r"(?:ldr|str)[a-z]*(?:\.w)? \w+, \[(\w+), #(-?0x[0-9a-f]+|-?\d+)\]", "%s %s" % (m, ops))
        if q and q.group(1) not in ("sp", "pc"):
            offs.add(int(q.group(2), 0))
        for q in _re.finditer(r"#(0x[0-9a-f]+|\d+)", ops):
            v = int(q.group(1), 0)
            if m.startswith(("mov", "cmp", "cmn")) and v > 0xff:
                imms.add(v)
    return {"calls": calls, "strs": strs, "offs": offs, "imms": imms}
