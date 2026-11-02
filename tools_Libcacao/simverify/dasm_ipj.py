#!/usr/bin/env python3
"""反組譯 libimageprocessorjni 的某函式，並把 bl/b 目標（含 PLT -> GOT -> reloc 符號）標註名稱。
用法: dasm_ipj.py <orig|new> <lib|lib64> <函式名子字串> [最大位元組]"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu_ipj import Lib
import capstone
from capstone import arm_const as AC, arm64_const as A64C

w, arch, name = sys.argv[1:4]
nmax = int(sys.argv[4]) if len(sys.argv) > 4 else 0
lib = Lib(f'/home/h/tmp/SemcCameraUI/.tmp/simverify/{w}/{arch}/libimageprocessorjni.so')
if name not in lib.syms:
    c = [k for k in lib.syms if name in k]
    if len(c) != 1:
        print(c); sys.exit()
    name = c[0]
d = open(lib.path, 'rb').read()
is64 = arch == 'lib64'

def foff(v):
    for s in lib.img.elf.iter_segments():
        if s['p_type'] == 'PT_LOAD' and s['p_vaddr'] <= v < s['p_vaddr'] + s['p_filesz']:
            return v - s['p_vaddr'] + s['p_offset']

# GOT slot -> symbol
slot = {}
for off, t, sym, add in lib.img.relocs:
    if sym:
        slot[off] = sym
def mkmd(thumb):
    md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM) if is64 else capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB if thumb else capstone.CS_MODE_ARM)
    md.detail = True
    return md
plt_cache = {}
def plt_target(addr):
    if addr in plt_cache: return plt_cache[addr]
    r = None
    try:
        code = d[foff(addr):foff(addr) + 16]
        if is64:
            ins = list(mkmd(False).disasm(code, addr))
            if ins[0].mnemonic == 'adrp':
                page = ins[0].operands[1].imm
                off = ins[1].operands[1].mem.disp
                r = slot.get(page + off)
        else:
            ins = list(mkmd(False).disasm(code, addr))
            ip = ins[0].address + 8 + ins[0].operands[2].imm
            ip += ins[1].operands[2].imm
            sl = ip + ins[2].operands[1].mem.disp
            r = slot.get(sl)
    except Exception:
        r = None
    plt_cache[addr] = r
    return r
def veneer(t):
    # Thumb 'bx pc; nop' + ARM 'ldr ip,[pc]; add pc,ip,pc' 長跳 veneer
    try:
        b = d[foff(t):foff(t) + 16]
        if not is64 and b[:2] == b'\x78\x47':
            word = int.from_bytes(b[12:16], 'little')
            return (word + t + 16) & 0xffffffff
    except Exception:
        pass
    return None

def label(t):
    v = veneer(t & ~1)
    if v is not None:
        t = v
    f = lib.func_at(t)
    if f and f[1] == 0:
        return f[0]
    p = plt_target(t)
    if p: return 'PLT:' + p
    return None
a, sz = lib.syms[name]
start = a & ~1
thumb = bool(a & 1) and not is64
md = mkmd(thumb)
code = d[foff(start):foff(start) + (nmax or sz)]
print('#', name, hex(start), sz)
for i in md.disasm(code, start):
    extra = ''
    if i.mnemonic.startswith(('bl', 'b')) and i.operands and i.operands[-1].type == (capstone.CS_OP_IMM):
        l = label(i.operands[-1].imm)
        if l: extra = '   ; ' + l
    print('%x: %-8s %s%s' % (i.address, i.mnemonic, i.op_str, extra))
