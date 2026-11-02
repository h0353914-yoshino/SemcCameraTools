#!/usr/bin/env python3
"""gfuzz2.py — 半結構化差分：以真實建構的 ProcessCtrlGateway / Request / ResultItem / Param 為輸入，
隨機化旗標欄位與 stub 回傳，逐方法比對 事件/回傳值/log/配置/記憶體副作用。
用法: python gfuzz2.py [seeds=24] [name-substring]
輸出: .tmp/simverify/result/ctrl_gateway_fuzz2.json
"""
import json
import os
import random
import struct
import subprocess
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gdiff import D, MOD, ROOT, filt_events, ev_cmp, norm_logs
from gemu import M32, UVT, Lib, Run
from gobj import W
from grettype import is_void

MEMW = 0x700


def mkW(lib, seed, flavor):
    return W(lib, seed=seed, flavor=flavor)


class Ctx:
    """單次執行的物件世界。"""

    def __init__(self, lib, seed):
        self.w = w = W(lib, seed=seed, flavor=seed % 4)
        self.rr = random.Random(seed * 99991 + 5)
        rr = self.rr
        self.lib = lib
        self.gw = w.new(MEMW)
        w.call("_ZN5cacao18ProcessCtrlGatewayC2Ev", self.gw)
        w.r.events.clear(); w.r.logs.clear(); w.r.allocs.clear()
        g = self.gw
        # 隨機化 gateway 狀態欄位
        for off, vals in ((0x5dc, (0, 1, 2, 3, 4, 5)), (0x660, (0, 1)), (0x2f0, (0, 1, 2, 3)), (0x5bc, (0x78, 5)),
                          (0x5c0, (10, 3)), (0x5c4, (30, 2)), (0x65c, (0x49742400, 7)), (0x664, (0, 1, 2, 3, 100))):
            w.r.wr32(g + off, rr.choice(vals))
        w.r.wr32(g + 0x2f4, self.fake())
        if rr.random() < 0.6:
            w.r.wr32(g + 0x2f8, self.fake())
        if rr.random() < 0.5:
            w.r.wr32(g + 0x57c, self.fake())
        self.mode = None

    def fake(self):
        """具 UVT vtable 的假物件（虛擬呼叫 -> 具名 stub）。"""
        p = self.w.new(0x100)
        self.w.r.wr32(p, UVT + 0x100 * self.rr.randrange(8))
        # 內含若干指向其他假物件的欄位，增加解參考深度
        for off in (4, 8, 0xc):
            self.w.r.wr32(p + off, self.rr.choice([0, 1, 4, p, p + 0x20]))
        return p

    def sd(self, n=0x200):
        data = bytes(self.rr.getrandbits(8) if self.rr.random() < 0.4 else 0 for _ in range(n))
        return self.w.sd(data)[0]

    def param(self):
        return self.w.call("createParam(cacao::ISerialize::SerializedData*)", self.sd())

    def result(self):
        return self.w.call("ProcessCtrlGatewayFactory::createResult", self.sd())

    def config(self):
        return self.w.call("ProcessCtrlGatewayFactory::createConfig", 0x65, self.sd())

    def modeobj(self):
        return self.w.call("ProcessCtrlGatewayFactory::createMode", self.sd())

    def vecbufs(self):
        w = self.w
        n = self.rr.choice([0, 1, 2, 3])
        arr = w.new(16)
        for i in range(n):
            w.r.wr32(arr + 4 * i, self.fake())
        vec = w.new(0x20)
        w.r.wr32(vec + 4, arr)
        w.r.wr32(vec + 8, n)
        return vec

    def request(self):
        w = self.w
        req = w.new(0xb0)
        p = self.param()
        w.call("cacao::ProcessCtrlGatewayBase::Request::Request(cacao::ProcessParamBase const*, android::Vector<cacao::ImageBuf*>*, cacao::ICBProcessResultListener*, cacao::ProcessResultBase*, unsigned char, PAL_Msg_t const*)"
               if False else "_ZN5cacao22ProcessCtrlGatewayBase7RequestC2EPKNS_16ProcessParamBaseEPN7android6VectorIPNS_8ImageBufEEEPNS_24ICBProcessResultListenerEPNS_17ProcessResultBaseEhPK9PAL_Msg_t",
               req, p, self.vecbufs() if self.rr.random() < 0.7 else 0, self.fake(), self.result(),
               self.rr.choice([0, 1, 2, 3]), self.w.new(0x40))
        # state
        w.r.wr32(req + 0xa4, self.rr.choice([0, 1, 2, 3, 4]))
        return req

    def item(self):
        w = self.w
        it = w.new(0x130)
        ks = sorted(k for k in w.lib.find("cacao::ProcessCtrlGateway::ResultItem::ResultItem()") if "ResultItemC" in k)
        w.call(ks[-1] if "C1E" in ks[-1] and len(ks) == 1 else [k for k in ks if "C2E" in k][0] if any("C2E" in k for k in ks) else ks[0], it)
        w.r.uc.mem_write(it + 0xcc, b"\x01")      # 已知差異：原版 ctor 設 +0xcc=1（無讀取者），兩邊統一以免干擾
        w.r.wr32(it + 4, 0)
        w.r.wr32(it + 0xd0, self.result())
        w.r.wr32(it + 0x124, self.fake())
        for off in (0x8, 0xd8, 0xdc, 0xf0, 0xf4, 0xf8, 0xfc, 0x100, 0x104, 0x118, 0x120):
            w.r.wr32(it + off, self.rr.choice([0, 1, 2, 5, 9, 0xffffffff, 100]))
        return it

    def item_in_list(self, key):
        it = self.item()
        self.w.r.wr32(it + 0xd8, key)
        self.w.r.wr32(it + 0xdc, 0)
        ks = sorted(k for k in self.lib.demangled() if self.lib.demangled()[k].startswith("cacao_pal::PtrLockList<") and "::pushLast(" in self.lib.demangled()[k])
        self.w.call(ks[0], self.gw + 0x2fc, it)
        return it

    def resmsg(self, key):
        w = self.w
        m = w.new(0x80)
        w.r.wr32(m + 0x18, key)
        for off in (0x1c, 0x20, 0x24, 0x28, 0x2c, 0x30, 0x34, 0x38):
            w.r.wr32(m + off, self.rr.choice([0, 1, 2, 5, 0xffffffff, 100]))
        w.r.wr32(m + 0x24, self.rr.choice([0, 0, 0, 1, 5, 0xffffff99]))
        return m


# 每個方法 -> 參數建構器 lambda c -> [args]（不含 this）
def argspec(shortname):
    P = {
        "passRequest": lambda c: [c.request()],
        "prepareVideoRec": lambda c: [c.request()],
        "startVideoRec": lambda c: [c.request()],
        "stopVideoRec": lambda c: [c.request()],
        "triggerSuperSlow": lambda c: [c.request()],
        "onProcess": lambda c: [c.request()],
        "processInternal": lambda c: [c.rr.randrange(0, 11)],
        "processAsyncInternal": lambda c: [c.rr.randrange(0, 11)],
        "convert": lambda c: [c.rr.randrange(0, 12)],
        "copyProcessCtrlParam": lambda c: [c.request(), c.w.new(0x100)],
        "copyResultItem": lambda c: [c.item(), c.item()],
        "handleVideoCapture": lambda c: [c.item()],
        "returnBufferToSurface": lambda c: [c.item(), c.rr.choice([0, 1])],
        "createNativeWindow": lambda c: [c.w.call("createParam(android::sp<android::IBinder> const&, cacao::ISerialize::SerializedData*)", c.w.new(0x10), c.sd())],
        "deleteNativeWindow": lambda c: [],
        "createFreeSwResultList": lambda c: [],
        "createResultItemFromBuffer": lambda c: [],
        "tryVideoCaptureRequest": lambda c: [],
        "onHandleSuperSlowDoneInternal": lambda c: [],
        "handleFinishCamera": lambda c: [],
        "onInit": lambda c: [],
        "onDeinit": lambda c: [],
        "onStop": lambda c: [c.rr.choice([0, 1])],
        "onStart": lambda c: [c.modeobj()],
        "onStopRequest": lambda c: [],
        "setConfig": lambda c: [c.config()],
        "getConfig": lambda c: [c.config()],
        "onHandleMsg": lambda c: [c.w.new(0x80)],
        "onCreateRequest": lambda c: [c.param(), c.vecbufs(), c.fake(), c.result(), c.rr.choice([0, 1]), c.w.new(0x40)],
        "onHandleResultInternal": None,   # 特殊處理
        "onHandleProgressInternal": None,
    }
    return P.get(shortname, "NA")


def snapshot(c, extra_ptrs):
    w = c.w
    out = {"gw": w.dump(c.gw, MEMW)}
    for i, (p, n) in enumerate(extra_ptrs):
        r = w.r
        k = max(0, min(len(r.alloc_starts) - 1, __import__("bisect").bisect_right(r.alloc_starts, p) - 1))
        lim = r.alloc_tab[k][1] if r.alloc_starts and r.alloc_starts[k] <= p else n
        out["x%d" % i] = w.dump(p, min(n, max(4, (lim + 3) & ~3)))
    return out


def run_one(lib, name_mangled, shortname, seed, is_vcall=False):
    c = Ctx(lib, seed)
    w = c.w
    spec = argspec(shortname)
    extra = []
    if shortname in ("onHandleResultInternal", "onHandleProgressInternal"):
        key = 7
        it = c.item_in_list(key) if seed % 3 else None
        m = c.resmsg(key)
        args = [m]
        extra = [(m, 0x80)] + ([(it, 0x130)] if it else [])
    else:
        args = spec(c)
        extra = [(a, 0x130) for a in args if isinstance(a, int) and 0x40000000 <= a < 0x40800000][:4]
    w.r.events.clear(); w.r.logs.clear(); w.r.allocs.clear()
    addr = sorted(e for e in lib.syms[name_mangled] if e[2] == "STT_FUNC")[0][0]
    ret = w.r.call(addr, [c.gw] + [a & M32 for a in args])[0]
    snap = snapshot(c, extra)
    return {"ret": w.r.norm(ret), "fault": w.r.fault, "events": filt_events(w.r.events), "logs": w.r.logs,
            "allocs": [a for a in w.r.allocs if a[0] == "new"], "anom": w.r.anomalies, "mem": snap}


def cmp(a, b, skip_ret):
    tags = []
    if a["fault"] == "insn_limit" or b["fault"] == "insn_limit":
        return ["UNSIM_LIMIT"]
    ec = ev_cmp(a["events"], b["events"])
    if ec == "DIFF":
        tags.append("EVENTS")
    elif ec in ("REORDER", "COUNT"):
        tags.append(ec)
    if a["fault"] != b["fault"]:
        tags.append("FAULT")
    if norm_logs(a["logs"]) != norm_logs(b["logs"]):
        tags.append("LOGS")
    if Counter(map(tuple, a["allocs"])) != Counter(map(tuple, b["allocs"])):
        tags.append("ALLOC")
    if [x[0] for x in a["anom"]] != [x[0] for x in b["anom"]]:
        tags.append("ANOM")
    if a["fault"] is None and b["fault"] is None:
        if a["ret"] != b["ret"] and not skip_ret:
            tags.append("RET")
        if a["mem"] != b["mem"]:
            tags.append("MEM")
    return tags


def memdiff(a, b, limit=10):
    out = []
    for k in sorted(set(a) | set(b)):
        da, db = a.get(k, {}), b.get(k, {})
        for off in sorted(set(da) | set(db)):
            if da.get(off) != db.get(off):
                out.append((k, off, da.get(off), db.get(off)))
                if len(out) >= limit:
                    return out
    return out


def main():
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    only = sys.argv[2] if len(sys.argv) > 2 else ""
    la, lb = Lib(D + "orig/lib/%s.so" % MOD), Lib(D + "new/lib/%s.so" % MOD)
    dem = la.demangled()
    res = {}
    for name in sorted(set(la.syms) & set(lb.syms)):
        d = dem.get(name, "")
        if not d.startswith("cacao::ProcessCtrlGateway::") or "(" not in d:
            continue
        head = d.split("(")[0]
        short = head.split("::")[-1]
        cls = head.split("::")[-2]
        if cls != "ProcessCtrlGateway" or short in ("ProcessCtrlGateway", "~ProcessCtrlGateway", "printStackTrace", "matchResult", "matchOldFrameId"):
            continue
        if argspec(short) == "NA":
            continue
        if only and only not in d:
            continue
        agg = Counter()
        ex = {}
        skip_ret = is_void(head)
        for s in range(seeds):
            try:
                ra = run_one(la, name, short, s)
                rb = run_one(lb, name, short, s)
            except Exception as e:
                import traceback
                agg["HARNESS_ERR"] += 1
                ex.setdefault("HARNESS_ERR", traceback.format_exc()[-400:])
                continue
            tags = cmp(ra, rb, skip_ret)
            if not tags:
                agg["SAME"] += 1
                if ra["fault"]:
                    agg["SAME_FAULT"] += 1
                continue
            for t in tags:
                agg[t] += 1
            key = "+".join(tags)
            if key not in ex:
                ex[key] = {"seed": s,
                           "orig": {k: ra[k] for k in ("ret", "fault", "logs", "allocs", "anom")},
                           "new": {k: rb[k] for k in ("ret", "fault", "logs", "allocs", "anom")},
                           "events_orig": ra["events"][:30], "events_new": rb["events"][:30],
                           "memdiff": memdiff(ra["mem"], rb["mem"]) if ra["fault"] is None and rb["fault"] is None else None}
        res[d] = {"agg": dict(agg), "ex": ex}
    out = ROOT + "/.tmp/simverify/result/ctrl_gateway_fuzz2%s.json" % ("_" + only.replace(":", "").replace(" ", "_")[:30] if only else "")
    json.dump(res, open(out, "w"), indent=1, default=str)
    for k, v in res.items():
        a = v["agg"]
        bad = {x: n for x, n in a.items() if x not in ("SAME", "SAME_FAULT")}
        print(("DIFF " if bad else "ok   ") + k[:100], dict(a))


if __name__ == "__main__":
    main()
