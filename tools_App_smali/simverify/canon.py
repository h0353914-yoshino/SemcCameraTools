#!/usr/bin/env python3
"""第 1 層：正規化 smali 比對（主相機 app 差分驗證）。

對原版與重建版的每個類別、每個方法做正規化後比較：
- 去除 .line / .local / .param / .prologue / .source 等純除錯資訊
- 去除 nop、整行註解
- 暫存器（v/p）依首次出現順序改名
- 標籤依首次出現順序改名
- const/move/invoke 的寬窄變體視為同一指令
相同者可證明等價（僅呼叫點順序與常數不變）；不同者進第 2 層。

用法：
  python3 canon.py <orig_dir> <new_dir> <out_json>
  （目錄內為 smali 根，檔案樹即 apktool 輸出的 smali/ smali_classes2/）
"""
import json
import os
import re
import sys
from collections import defaultdict

DEBUG_PREFIXES = (
    ".line", ".local", ".end local", ".restart local", ".param", ".end param",
    ".prologue", ".source", ".registers",
)
REG_RE = re.compile(r"(?<![\w/])([vp]\d+)(?![\w])")
# d8 與 dx 的合成存取子名稱不同：access$NNN 與 -$$Nest$f... 視為同一類
ACCESSOR_RE = re.compile(r"->(?:access\$\d+|-\$\$Nest\$[a-z]\w*)\(")
NORMALIZE_OPS = [
    (re.compile(r"^const(-wide)?/(4|16|32|high16)\b"), r"const\1"),
    (re.compile(r"^const-wide/(16|32|high16)\b"), r"const-wide"),
    (re.compile(r"^move(-object|-wide)?/(from16|16)\b"), r"move\1"),
    (re.compile(r"^(invoke-[a-z]+)/range\b"), r"\1"),
    (re.compile(r"^(if-[a-z]+)z\b"), r"\1z"),
]


def collect_classes(root):
    """回傳 {類別名: (檔案路徑, 原始文字)}，類別名取自 .class 行。"""
    out = {}
    for dp, _, fns in os.walk(root):
        for fn in fns:
            if not fn.endswith(".smali"):
                continue
            path = os.path.join(dp, fn)
            with open(path, encoding="utf-8", errors="replace") as f:
                text = f.read()
            m = re.search(r"^\.class .*?(L[^;\s]+;)\s*$", text, re.M)
            if not m:
                continue
            out[m.group(1)] = (path, text)
    return out


def split_methods(text):
    """回傳 (類別表頭列表, {方法簽章: [方法行]})。"""
    header, methods, cur, sig = [], {}, None, None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(".method "):
            sig = s
            cur = [s]
            continue
        if cur is not None:
            cur.append(line)
            if s == ".end method":
                methods.setdefault(sig, []).append(cur)
                cur, sig = None, None
            continue
        header.append(s)
    return header, methods


def strip_annotations(lines):
    """去除 d8 不保留的建置期/參數名註解（build、system MethodParameters）。"""
    out, skip = [], False
    for s in lines:
        t = s.strip()
        if not skip and (t.startswith(".annotation build ")
                         or t.startswith(".annotation system Ldalvik/annotation/MethodParameters;")):
            skip = True
            continue
        if skip:
            if t == ".end annotation":
                skip = False
            continue
        out.append(s)
    return out


def canon_method(lines):
    """正規化一個方法，回傳 canonical 字串列表。"""
    body = []
    for raw in strip_annotations(lines[1:-1]):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith(DEBUG_PREFIXES):
            continue
        if s == "nop":
            continue
        s = re.sub(r"\s+#.*$", "", s)
        s = ACCESSOR_RE.sub("->ACCESSOR(", s)
        for pat, rep in NORMALIZE_OPS:
            s = pat.sub(rep, s, count=1)
        body.append(s)
    # 暫存器與標籤依首次出現順序改名
    reg_map, lab_map = {}, {}

    def reg_sub(m):
        name = m.group(1)
        if name not in reg_map:
            reg_map[name] = "R%d" % len(reg_map)
        return reg_map[name]

    def label_token(tok):
        # 標籤僅出現在 token 開頭的 ":name"，且不含 / 或 ;（排除型別描述子）
        if tok.startswith(":") and "/" not in tok and ";" not in tok and len(tok) > 1:
            if tok not in lab_map:
                lab_map[tok] = ":L%d" % len(lab_map)
            return lab_map[tok]
        return tok

    out = []
    for s in body:
        parts = re.split(r"([\s,{}]+)", s)
        s = "".join(label_token(p) for p in parts)
        s = REG_RE.sub(reg_sub, s)
        out.append(s)
    return out


def compare(orig_root, new_root):
    orig = collect_classes(orig_root)
    new = collect_classes(new_root)
    res = {
        "classes_only_orig": sorted(set(orig) - set(new)),
        "classes_only_new": sorted(set(new) - set(orig)),
        "classes": {},
        "totals": defaultdict(int),
    }
    for cls in sorted(set(orig) & set(new)):
        oh, om = split_methods(orig[cls][1])
        nh, nm = split_methods(new[cls][1])
        entry = {"methods": {}, "field_diff": False}
        ofields = sorted(l for l in oh if l.startswith(".field "))
        nfields = sorted(l for l in nh if l.startswith(".field "))
        entry["field_diff"] = ofields != nfields
        for sig in sorted(set(om) | set(nm)):
            if sig not in om:
                st, detail = "only_new", None
            elif sig not in nm:
                st, detail = "only_orig", None
            else:
                ocs = [canon_method(x) for x in om[sig]]
                ncs = [canon_method(x) for x in nm[sig]]
                if ocs == ncs:
                    st, detail = "same", None
                else:
                    st, detail = "diff", None
            entry["methods"][sig] = st
            res["totals"][st] += 1
        res["classes"][cls] = entry
    res["totals"] = dict(res["totals"])
    return res


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    r = compare(sys.argv[1], sys.argv[2])
    with open(sys.argv[3], "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=1)
    print("classes only orig:", len(r["classes_only_orig"]))
    print("classes only new :", len(r["classes_only_new"]))
    print("classes compared :", len(r["classes"]))
    print("methods:", r["totals"])
