import lzma, io, sys
from elftools.elf.elffile import ELFFile
def debug_syms(path, kind='STT_FUNC'):
    f = ELFFile(open(path,'rb'))
    s = f.get_section_by_name('.gnu_debugdata')
    if not s: return {}
    e = ELFFile(io.BytesIO(lzma.decompress(s.data())))
    out = {}
    st = e.get_section_by_name('.symtab')
    if st is None: return {}
    for sym in st.iter_symbols():
        if sym['st_info']['type']==kind and sym['st_value']:
            out[sym.name] = (sym['st_value'], sym['st_size'])
    return out
if __name__=='__main__':
    for p in sys.argv[1:]:
        d = debug_syms(p); print(p, len(d))
