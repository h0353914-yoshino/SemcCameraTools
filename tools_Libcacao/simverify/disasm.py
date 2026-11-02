#!/usr/bin/env python3
"""反組譯：dis.py <orig|new> <lib> <匯出名|0xaddr> [長度|auto]  —— bl/blx 目標自動解析 PLT -> reloc 符號、內部 sub_XXXX。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capstone
from emu import SoImage
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class Dis:
    def __init__(self, path):
        self.img = SoImage(path)
        self.mem = bytearray(self.img.size + 0x1000)
        for v, m, d in self.img.segs:
            self.mem[v:v + len(d)] = d
        self.got = {off: sym for off, t, sym, add in self.img.relocs if sym}
        dyn = self.img.elf.get_section_by_name(".dynsym")
        self.exp = {}
        self.addr2name = {}
        for s in dyn.iter_symbols():
            if s["st_shndx"] != "SHN_UNDEF" and s.name and s["st_info"]["type"] == "STT_FUNC":
                self.exp[s.name] = s["st_value"] & ~1
                self.addr2name[s["st_value"] & ~1] = s.name
        self.cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
        self.cs.detail = False
        self.csa = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
        self.plt = {}

    def plt_target(self, a):
        """a 是 ARM PLT 條目位址 -> 符號名或 None"""
        if a in self.plt:
            return self.plt[a]
        r = None
        try:
            w = struct.unpack("<3I", bytes(self.mem[a:a + 12]))
            if w == (0x46c04778, 0xe59fc000, 0xe08cf00f):          # thumb->ARM long-branch veneer
                L = struct.unpack("<I", bytes(self.mem[a + 12:a + 16]))[0]
                t = (a + 16 + L) & 0xffffffff
                r = self.plt_target(t) or self.addr2name.get(t) or ("sub_%x" % t)
                self.plt[a] = r
                return r
            # add ip,pc,#imm8 ror ; add ip,ip,#.. ; ldr pc,[ip,#..]!
            def imm(x):
                v = x & 0xff; rot = ((x >> 8) & 0xf) * 2
                return ((v >> rot) | (v << (32 - rot))) & 0xffffffff if rot else v
            if (w[0] & 0xfff00000) == 0xe2800000 and (w[2] & 0xfff0f000) == 0xe5b0f000 and ((w[2] >> 16) & 0xf) == 12:
                ip = a + 8 + imm(w[0] & 0xfff)
                ip = ip + imm(w[1] & 0xfff)
                ip = ip + (w[2] & 0xfff)
                r = self.got.get(ip)
                if r is None:
                    # 自身符號
                    pass
        except Exception:
            pass
        self.plt[a] = r
        return r

    def name_of(self, t):
        if t in self.addr2name:
            return self.addr2name[t]
        p = self.plt_target(t)
        if p:
            return "PLT:" + p
        return "sub_%x" % t

    def dis(self, start, n=None, end=None):
        start &= ~1
        out = []
        pc = start
        limit = end or (start + (n or 0x600))
        while pc < limit:
            ins = None
            for i in self.cs.disasm(bytes(self.mem[pc:pc + 4]), pc, 1):
                ins = i
            if ins is None:
                out.append("%x: .word %08x" % (pc, struct.unpack("<I", self.mem[pc:pc + 4])[0]))
                pc += 2
                continue
            txt = "%x: %-8s %s" % (ins.address, ins.mnemonic, ins.op_str)
            if ins.mnemonic in ("bl", "blx", "b", "b.w") and ins.op_str.startswith("#"):
                t = int(ins.op_str[1:], 16)
                txt += "    ; " + self.name_of(t)
            elif ins.mnemonic.startswith("ldr") and "[pc" in ins.op_str:
                try:
                    off = int(ins.op_str.split("#")[-1].rstrip("]"), 16)
                    ea = ((ins.address + 4) & ~3) + off
                    txt += "    ; =0x%x" % struct.unpack("<I", self.mem[ea:ea + 4])[0]
                except Exception:
                    pass
            out.append(txt)
            pc += ins.size
            if ins.mnemonic in ("pop", "pop.w") and "pc" in ins.op_str and end is None and n is None:
                nxt = bytes(self.mem[pc:pc + 2])
                # 簡單啟發：遇到 pop {..pc} 且其後不是分支目標延伸就停；auto 模式交給呼叫端指定長度
        return out

if __name__ == "__main__":
    ver, lib, tgt = sys.argv[1:4]
    d = Dis("%s/.tmp/simverify/%s/lib/%s.so" % (ROOT, ver, lib))
    a = d.exp[tgt] if not tgt.startswith("0x") else int(tgt, 16)
    n = int(sys.argv[4], 0) if len(sys.argv) > 4 else 0x200
    print("\n".join(d.dis(a, n)))
