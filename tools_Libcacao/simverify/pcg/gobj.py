#!/usr/bin/env python3
"""gobj.py — 結構化物件測試：建構子佈局 / 解構事件 / Factory create* / 序列化 wire layout。
輸出 .tmp/simverify/result/ctrl_gateway_obj.json
"""
import json
import os
import random
import re
import struct
import subprocess
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gdiff import D, MOD, ROOT, filt_events
from gemu import ARENA, ARENA_SZ, Lib, M32, Run

ZERO_ARENA = bytes(ARENA_SZ)


class W:
    """單一 lib 的結構化世界。"""

    def __init__(self, lib, seed=0, flavor=0, retfn=None):
        self.lib = lib
        self.r = Run(lib, seed, flavor=flavor, arena=ZERO_ARENA, retfn=retfn)
        self.vts = {}

    def new(self, size):
        p, _ = self.r.alloc(size)
        return p

    def fn(self, name):
        """name: mangled 或 demangled 子字串（需唯一）"""
        m = self.lib.find(name)
        m = [k for k in m if any(e[2] == "STT_FUNC" for e in self.lib.syms[k])]
        if len(m) > 1:
            m2 = [k for k in m if not k.startswith(("_ZThn", "_ZTv", "_ZTh"))]
            m = m2 or m
        if len(m) != 1:
            raise KeyError("%s -> %s" % (name, m))
        return sorted(e for e in self.lib.syms[m[0]] if e[2] == "STT_FUNC")[0][0]

    def call(self, name, *args):
        a = self.fn(name) if isinstance(name, str) else name
        return self.r.call(a, [x & M32 for x in args])[0]

    def dump(self, p, n):
        out = {}
        self.vts = {}
        b = bytes(self.r.uc.mem_read(p, n))
        for off in range(0, n, 4):
            v = struct.unpack_from("<I", b, off)[0]
            if v:
                out[off] = self.r.norm(v)
                if out[off] == "@vt":
                    self.vts[off] = self.lib.vt_slots(v - 0x10000000)
        return out

    def wbytes(self, p, data):
        self.r.uc.mem_write(p, data)

    def sd(self, data):
        buf = self.new(len(data) + 16)
        self.wbytes(buf, data)
        sd = self.new(0x194)
        self.r.wr32(sd + 0x184, len(data))
        self.r.wr32(sd + 0x188, buf)
        self.r.wr32(sd + 0x18c, 0)
        return sd, buf

    def sd_empty(self, size):
        buf = self.new(size + 16)
        sd = self.new(0x194)
        self.r.wr32(sd + 0x184, size)
        self.r.wr32(sd + 0x188, buf)
        self.r.wr32(sd + 0x18c, 0)
        return sd, buf


def snap(w):
    return {"events": filt_events(w.r.events), "logs": w.r.logs, "allocs": [a for a in w.r.allocs if a[0] == "new"],
            "fault": w.r.fault, "anom": w.r.anomalies}


def icf_ok(xa, xb):
    """兩邊槽位函式名稱無交集，但皆屬於 cacao_pal 樣板容器 / sp / std 的相同函式種類（ICF 別名差異）。"""
    from gemu import demangle
    def kind(names):
        ks = set()
        for n in names:
            d = demangle(n)
            if re.search(r"::~\w+\(\)$", d.split(" const")[0]):
                ks.add("~dtor")
                continue
            if not d.startswith(("cacao_pal::", "android::sp", "std::", "non-virtual thunk to cacao_pal")):
                return None
            # 取函式名（去掉樣板引數）：最後一個 :: 之後、括號之前
            head = re.sub(r"<[^<>]*>", "", d.split("(")[0]) if "<" in d else d.split("(")[0]
            head = re.sub(r"<[^<>]*>", "", head)
            ks.add(head.split("::")[-1])
        return ks
    ka, kb = kind(xa), kind(xb)
    return ka is not None and kb is not None and bool(ka & kb)


def vtdiff(va, vb):
    """比對兩邊物件內每個 vtable 指標所指 vtable 的槽位（別名集合需有交集）。"""
    out = []
    for off in sorted(set(va) | set(vb)):
        sa, sb = va.get(off), vb.get(off)
        if sa is None or sb is None:
            out.append((off, "vtable-ptr presence", sa is not None, sb is not None))
            continue
        n = min(len(sa), len(sb))
        for i in range(n):
            xa = sa[i] if i < len(sa) else None
            xb = sb[i] if i < len(sb) else None
            if xa is not None and xb is not None and not (xa & xb) and icf_ok(xa, xb):
                continue
            if xa is None or xb is None or not (xa & xb):
                out.append((off, i, sorted(xa) if xa else None, sorted(xb) if xb else None))
                break
    return out


def diffdict(a, b, limit=12):
    out = []
    for k in sorted(set(a) | set(b), key=str):
        if a.get(k) != b.get(k):
            out.append((k, a.get(k), b.get(k)))
            if len(out) >= limit:
                break
    return out


CTORS = [  # (demangled 子字串, 物件大小)
    ("cacao::ProcessCtrlGatewayBase::ProcessCtrlGatewayBase()", 0x300),
    ("cacao::ProcessCtrlGateway::ProcessCtrlGateway()", 0x680),
    ("cacao::ProcessCtrlGatewayBase::RequestList::RequestList()", 0x130),
    ("cacao::ProcessCtrlGatewayBase::ConfigList::ConfigList()", 0xa0),
    ("cacao::ProcessCtrlGateway::ResultItem::ResultItem()", 0x130),
    ("cacao::ProcessCtrlMode::ProcessCtrlMode()", 0x2c),
    ("cacao::ProcessCtrlParam::ProcessCtrlParam()", 0x160),
    ("cacao::ProcessCtrlVideoRecParam::ProcessCtrlVideoRecParam()", 0x170),
    ("cacao::ProcessCtrlResult::ProcessCtrlResult()", 0x34),
    ("cacao::ProcessCtrlDynamicParameterConfig::ProcessCtrlDynamicParameterConfig()", 0xc),
    ("cacao::ProcessCtrlGateway::Callback::Callback(cacao::ProcessCtrlGateway*)", 0x30),
]


def find_ctor(lib, sub):
    ks = [k for k in lib.find(sub) if any(e[2] == "STT_FUNC" for e in lib.syms[k])]
    return sorted(ks)


def test_ctors(res):
    la, lb = Lib(D + "orig/lib/%s.so" % MOD), Lib(D + "new/lib/%s.so" % MOD)
    for sub, size in CTORS:
        ca, cb = find_ctor(la, sub), find_ctor(lb, sub)
        key = "ctor:" + sub
        if not ca or not cb:
            res[key] = {"verdict": "NA", "note": "orig=%s new=%s" % (ca, cb)}
            continue
        # 使用 C2 (base object ctor) 優先，否則第一個
        pick = lambda ks: [k for k in ks if k.endswith("C2Ev") or "C2E" in k][0] if any("C2E" in k for k in ks) else ks[0]
        na, nb = pick(ca), pick(cb)
        out = {}
        for tag, lib, nm in (("orig", la, na), ("new", lb, nb)):
            w = W(lib)
            p = w.new(size + 0x40)
            # 參數：此處 this, 其餘用結構化假指標
            extra = [w.new(0x40) for _ in range(3)]
            args = [p] + extra
            if "Callback" in sub:
                args = [p, w.new(0x680)]
            w.call(nm, *args)
            out[tag] = {"mem": w.dump(p, size + 0x40), "vts": w.vts, **snap(w)}
        d = diffdict(out["orig"]["mem"], out["new"]["mem"])
        vd = vtdiff(out["orig"]["vts"], out["new"]["vts"])
        ev_same = out["orig"]["events"] == out["new"]["events"]
        res[key] = {"verdict": "SAME" if not d and not vd and ev_same and out["orig"]["logs"] == out["new"]["logs"] else "DIFF",
                    "memdiff": d, "vtdiff": vd, "events_same": ev_same,
                    "events_orig": out["orig"]["events"][:10], "events_new": out["new"]["events"][:10]}


def test_factory(res, nseeds=24):
    la, lb = Lib(D + "orig/lib/%s.so" % MOD), Lib(D + "new/lib/%s.so" % MOD)
    cases = [
        ("createMode", lambda w, sd: w.call("ProcessCtrlGatewayFactory::createMode", sd), 0x2c),
        ("createParam", lambda w, sd: w.call("createParam(cacao::ISerialize::SerializedData*)", sd), 0x160),
        ("createResult", lambda w, sd: w.call("ProcessCtrlGatewayFactory::createResult", sd), 0x34),
        ("createConfig", lambda w, sd: w.call("ProcessCtrlGatewayFactory::createConfig", 0x65, sd), 0xc),
    ]
    for name, fnc, size in cases:
        agg = defaultdict(int)
        ex = None
        for s in range(nseeds):
            rr = random.Random(1000 + s)
            L = rr.choice([0, 4, 8, 0x10, 0x20, 0x28, 0x30, 0x40, 0x80, 0x100])
            data = bytes(rr.getrandbits(8) if rr.random() < 0.5 else 0 for _ in range(L))
            outs = {}
            for tag, lib in (("orig", la), ("new", lb)):
                w = W(lib, seed=s, flavor=0)
                sd, buf = w.sd(data)
                ret = fnc(w, sd)
                o = {"ret": w.r.norm(ret) if ret else 0, "sdoff": w.r.rd32(sd + 0x18c),
                     "obj": w.dump(ret, size) if ret and ret != 0 else {}}
                o["vts"] = w.vts
                o["sdmem"] = w.dump(sd, 0x194)
                o.update(snap(w))
                outs[tag] = o
            a, b = outs["orig"], outs["new"]
            tags = []
            if bool(a["ret"]) != bool(b["ret"]):
                tags.append("RET_NULLNESS")
            if a["sdoff"] != b["sdoff"]:
                tags.append("SD_OFFSET")
            if a["obj"] != b["obj"]:
                tags.append("OBJ")
            if a["sdmem"] != b["sdmem"]:
                tags.append("SDMEM")
            if vtdiff(a["vts"], b["vts"]):
                tags.append("VTABLE")
            if a["events"] != b["events"]:
                tags.append("EVENTS")
            if a["logs"] != b["logs"]:
                tags.append("LOGS")
            if a["allocs"] != b["allocs"]:
                tags.append("ALLOC")
            if a["fault"] != b["fault"]:
                tags.append("FAULT")
            key = "+".join(tags) or "SAME"
            agg[key] += 1
            if tags and ex is None:
                ex = {"seed": s, "L": L, "a": {k: a[k] for k in ("ret", "sdoff", "events", "logs", "allocs", "fault")},
                      "b": {k: b[k] for k in ("ret", "sdoff", "events", "logs", "allocs", "fault")},
                      "objdiff": diffdict(a["obj"], b["obj"]), "vtdiff": vtdiff(a["vts"], b["vts"])}
        res["factory:" + name] = {"agg": dict(agg), "example": ex}


SER = [
    ("ProcessCtrlMode", 0x2c, ("ProcessCtrlGatewayFactory::createMode", ())),
    ("ProcessCtrlParam", 0x160, ("createParam(cacao::ISerialize::SerializedData*)", ())),
    ("ProcessCtrlResult", 0x34, ("ProcessCtrlGatewayFactory::createResult", ())),
    ("ProcessCtrlDynamicParameterConfig", 0xc, ("ProcessCtrlGatewayFactory::createConfig", (0x65,))),
    ("ProcessCtrlVideoRecParam", 0x170, ("VIDEO", ())),
]


def make_obj(w, cls, size, spec):
    if spec is not None and spec[0] == "VIDEO":
        sd0, _ = w.sd(bytes(0x200))
        binder = w.new(0x10)
        return w.call("createParam(android::sp<android::IBinder> const&, cacao::ISerialize::SerializedData*)", binder, sd0)
    if spec is not None:
        sd0, _ = w.sd(bytes(0x200))
        nm, pre = spec
        return w.call(nm, *pre, sd0)
    ks = find_ctor(w.lib, "cacao::%s::%s()" % (cls, cls))
    p = w.new(size + 0x40)
    pick = [k for k in ks if "C2E" in k] or ks
    w.call(pick[0], p)
    return p


def test_serialize(res, nseeds=16):
    """以各 lib 自己的建構路徑建物件，覆寫為相同隨機欄位（保留 +0/+4 vtable）後，比對
    getSerializedSize / serialize 輸出位元組 / deserialize 結果欄位 / clone / copy。"""
    la, lb = Lib(D + "orig/lib/%s.so" % MOD), Lib(D + "new/lib/%s.so" % MOD)
    for cls, size, spec in SER:
        for what in ("getSerializedSize", "serialize", "deserialize", "clone", "copy"):
            if what in ("clone", "copy") and cls in ("ProcessCtrlMode", "ProcessCtrlResult"):
                continue
            key = "ser:%s::%s" % (cls, what)
            agg = defaultdict(int)
            ex = None
            for s in range(nseeds):
                rr = random.Random(7000 + s)
                pat = [rr.choice([0, 1, 2, 0xffffffff, rr.getrandbits(32), rr.randrange(0, 100)]) for _ in range(size // 4)]
                pat2 = [rr.choice([0, 1, 2, 0xffffffff, rr.getrandbits(32), rr.randrange(0, 100)]) for _ in range(size // 4)]
                data = bytes(rr.getrandbits(8) for _ in range(0x200))
                outs = {}
                for tag, lib in (("orig", la), ("new", lb)):
                    w = W(lib, seed=s)
                    p = make_obj(w, cls, size, spec)
                    if not p:
                        outs[tag] = {"err": "make_obj null"}
                        continue
                    for i, v in enumerate(pat):
                        if i in (0, 1):
                            continue
                        if cls == "ProcessCtrlVideoRecParam" and i == 0x160 // 4:
                            continue
                        w.r.wr32(p + 4 * i, v)
                    w.r.events.clear(); w.r.logs.clear(); w.r.allocs.clear()
                    base = "cacao::%s::" % cls
                    if what == "getSerializedSize":
                        r0 = w.call(base + "getSerializedSize() const", p)
                        outs[tag] = {"ret": r0, **snap(w)}
                    elif what == "serialize":
                        sd, buf = w.sd_empty(0x300)
                        r0 = w.call(base + "serialize(cacao::ISerialize::SerializedData*) const", p, sd)
                        outs[tag] = {"ret": r0, "off": w.r.rd32(sd + 0x18c),
                                     "bytes": bytes(w.r.uc.mem_read(buf, 0x300)).rstrip(b"\0").hex(), **snap(w)}
                    elif what == "deserialize":
                        sd, buf = w.sd(data)
                        r0 = w.call(base + "deserialize(cacao::ISerialize::SerializedData*)", p, sd)
                        outs[tag] = {"ret": r0, "off": w.r.rd32(sd + 0x18c), "obj": w.dump(p, size), **snap(w)}
                    elif what == "clone":
                        r0 = w.call(base + "clone() const", p)
                        outs[tag] = {"ret": 1 if r0 else 0, "obj": w.dump(r0, size) if r0 else {}, **snap(w)}
                    else:   # copy(src)：src 由同一建構路徑建立並填 pat2
                        q = make_obj(w, cls, size, spec)
                        for i, v in enumerate(pat2):
                            if i in (0, 1):
                                continue
                            if cls == "ProcessCtrlVideoRecParam" and i == 0x160 // 4:
                                continue
                            w.r.wr32(q + 4 * i, v)
                        w.r.events.clear(); w.r.logs.clear(); w.r.allocs.clear()
                        sig = "copy(cacao::ProcessConfigBase const*)" if "Config" in cls else "copy(cacao::ProcessParamBase const*)"
                        r0 = w.call(base + sig, p, q)
                        outs[tag] = {"ret": 0, "obj": w.dump(p, size), **snap(w)}
                a, b = outs["orig"], outs["new"]
                if "err" in a or "err" in b:
                    agg["ERR"] += 1
                    continue
                tags = [k for k in ("ret", "off", "bytes", "obj", "events", "logs", "fault") if k in a and a[k] != b[k]]
                if what in ("clone", "copy") and "ret" in tags and a["ret"] == 0 and b["ret"] == 0:
                    tags.remove("ret")
                agg["+".join(tags) or "SAME"] += 1
                if tags and ex is None:
                    ex = {"seed": s, "a": {k: a[k] for k in a if k != "obj"}, "b": {k: b[k] for k in b if k != "obj"}}
                    if "obj" in a:
                        ex["objdiff"] = diffdict(a["obj"], b["obj"])
            res[key] = {"agg": dict(agg), "example": ex}


def main():
    res = {}
    for f in (test_ctors, test_factory, test_serialize):
        try:
            f(res)
        except Exception as e:
            import traceback
            res["ERR:" + f.__name__] = traceback.format_exc()
    out = ROOT + "/.tmp/simverify/result/ctrl_gateway_obj.json"
    json.dump(res, open(out, "w"), indent=1, default=str)
    for k, v in res.items():
        if k.startswith("ERR"):
            print(k, v)
        elif "verdict" in v:
            print(k, v["verdict"], v.get("memdiff", "")[:3] if v.get("memdiff") else "", v.get("vtdiff", "")[:2] if v.get("vtdiff") else "")
        else:
            print(k, v["agg"])


if __name__ == "__main__":
    main()
