#!/usr/bin/env python3
"""匯總第 1 層（正規化比對）與第 2 層（直譯器差分）結果為 Markdown。

用法：
  python3 report.py <layer1.json> <layer2.json> <out.md>
"""
import collections
import json
import sys

# 主 app 自有套件（其餘為第三方函式庫，單獨列出）
APP_PREFIXES = ("Lcom/sonyericsson/", "Lcom/sonymobile/")  # 含 L 前綴的類別名


def pkg_of(cls):
    parts = cls[1:].split("/")
    return "/".join(parts[:4]) if len(parts) > 4 else "/".join(parts[:-1])


def main(argv):
    l1 = json.load(open(argv[1], encoding="utf-8"))
    l2 = json.load(open(argv[2], encoding="utf-8"))
    res2 = l2["results"]
    rows = collections.defaultdict(collections.Counter)
    for cls, entry in l1["classes"].items():
        for sig, st in entry["methods"].items():
            key = "%s|%s" % (cls, sig)
            if st == "same":
                final = "L1 證明相同"
            elif st == "diff":
                final = {"dyn_same": "L2 動態相同（抽樣）", "diff": "真差異（待追查）",
                         "unsupported": "無法模擬", "no-code": "抽象/原生（無本體）"}.get(
                    res2.get(key, {}).get("status"), "未執行")
                if key in res2 and res2[key]["status"] == "diff" and res2[key].get("detail") \
                        and "orig_body" in res2[key]["detail"]:
                    final = "本體有無不一致"
            elif st == "only_orig":
                final = "僅原版（重建缺少）"
            elif st == "only_new":
                final = "僅重建（原版沒有）"
            else:
                final = st
            group = "app" if cls.startswith(APP_PREFIXES) else "third-party"
            rows[(group, pkg_of(cls))][final] += 1
    out = []
    out.append("# 主相機 app（SemcCameraUI-xxhdpi）差分驗證匯總\n")
    out.append("## 總覽（依方法數）\n")
    total = collections.Counter()
    for (g, p), c in rows.items():
        total.update({(g, k): v for k, v in c.items()})
    for g in ("app", "third-party"):
        out.append("### %s\n" % g)
        cnt = collections.Counter({k: v for (gg, k), v in total.items() if gg == g})
        for k, v in sorted(cnt.items(), key=lambda kv: -kv[1]):
            out.append("- %s：%d" % (k, v))
        out.append("")
    out.append("## 類別層級\n")
    out.append("- 僅原版類別：%d" % len(l1["classes_only_orig"]))
    out.append("- 僅重建類別：%d" % len(l1["classes_only_new"]))
    out.append("")
    out.append("## 依套件（app 自有套件列前）\n")
    out.append("| 群組 | 套件 | 結果 |")
    out.append("|---|---|---|")
    for (g, p), c in sorted(rows.items(), key=lambda kv: (kv[0][0] != "app", kv[0][1])):
        out.append("| %s | %s | %s |" % (g, p, "；".join("%s %d" % (k, v) for k, v in sorted(c.items()))))
    out.append("")
    out.append("## 真差異清單（L2 diff，app 自有）\n")
    diffs = [(k, v) for k, v in res2.items()
             if v["status"] == "diff" and k.startswith(APP_PREFIXES)]
    for k, v in sorted(diffs)[:500]:
        out.append("- `%s`（seed %s）" % (k, v["detail"].get("seed") if isinstance(v.get("detail"), dict) else "-"))
    out.append("")
    with open(argv[3], "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("wrote", argv[3], "diff items:", len(diffs))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    main(sys.argv)
