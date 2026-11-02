import re, os
SRC = "/home/h/tmp/SemcCameraUI/camera/cacao/libcacao_process_ctrl_gateway/"
_rt = None

def load():
    global _rt
    if _rt is not None:
        return _rt
    _rt = {}
    pat = re.compile(r'^\s*(?:__attribute__\(\([^)]*\)\)\s*)?((?:const\s+)?[\w:<>\*&]+(?:\s*[\*&])?)\s+((?:\w+::)+)(~?\w+)\(')
    for f in ("src/ProcessCtrlGateway.cpp", "src/ProcessCtrlGatewayBase.cpp"):
        for line in open(SRC + f, encoding="utf-8", errors="ignore"):
            m = pat.match(line)
            if m and m.group(1) not in ("return", "else", "new", "delete"):
                key = (m.group(2) + m.group(3)).replace(" ", "")
                _rt[key] = m.group(1).strip()
    return _rt

def is_void(demangled_head):
    """demangled_head: e.g. 'cacao::ProcessCtrlGatewayBase::Request::cancel'"""
    rt = load()
    k = demangled_head.replace("cacao::", "", 1).replace(" ", "")
    t = rt.get(k)
    return t == "void"
