#!/usr/bin/env python3
"""gscen.py — Gateway 生命週期情境差分：ctor -> init -> start -> stop -> deinit -> dtor（含 worker thread 訊息投遞）。
PAL 以假物件模擬：thread 表、queue、訊息投遞；偵測 PAL_Delete 時仍有存活 thread、重複 ThreadClose、
Mutex 遞迴鎖。輸出 .tmp/simverify/result/ctrl_gateway_scen.json
"""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gdiff import D, MOD, ROOT, filt_events
from gemu import M32, Lib, Run, UVT
from gobj import W, ZERO_ARENA

MSG_NAMES = {0x01000000: "INIT", 0x01000001: "DEINIT", 0x01000002: "START", 0x01000003: "STOP_REQ",
             0x01000004: "STOP", 0x01000005: "PROCESS", 0x01000006: "CLEANUP"}


class Pal:
    """PAL 假實作（以 hooks 掛到 Run）。"""

    def __init__(self, init_ret=0, reply_err=0, send_err=0):
        self.threads = {}        # handle -> alive
        self.n = 0
        self.pending = []        # 待投遞訊息 (bytes)
        self.msglog = []         # 供比對的訊息序列
        self.anoms = []
        self.deleted = False
        self.send_err = send_err
        self.reply_err = reply_err

    def hooks(self):
        P = self

        def create(run, a):
            P.msglog.append("PAL_Create")
            return 0

        def delete(run, a):
            P.msglog.append("PAL_Delete")
            live = [h for h, al in P.threads.items() if al]
            if live:
                P.anoms.append(("PAL_Delete_with_live_thread", len(live)))
            P.deleted = True
            return 0

        def thr_create(run, a):
            P.n += 1
            h = 0xAA00 + P.n
            P.threads[h] = True
            run.wr32(a[4] if False else run.arg(4), h)
            P.msglog.append("ThreadCreate")
            return 0

        def thr_close(run, a):
            h = a[0]
            if h not in P.threads:
                P.anoms.append(("ThreadClose_unknown_handle", run.norm(h)))
            elif not P.threads[h]:
                P.anoms.append(("ThreadClose_twice", hex(h)))
            P.threads[h] = False
            P.msglog.append("ThreadClose")
            return 0

        def qid(run, a):
            return 0x77

        def msg_cap(run, a):
            m = a[0]
            try:
                size = run.rd32(m + 0x14)
                size = min(max(size, 0x18), 0x40)
                raw = bytes(run.uc.mem_read(m, size))
            except Exception:
                raw = b""
            P.pending.append(raw)
            mid = struct.unpack_from("<I", raw, 0)[0] if len(raw) >= 4 else 0
            P.msglog.append("Send:%s:size=%d%s" % (MSG_NAMES.get(mid, hex(mid)), len(raw),
                                                 ":p=%s" % raw[0x18:].hex() if len(raw) > 0x18 else ""))
            return P.send_err

        def reply(run, a):
            P.msglog.append("Reply:err=%d" % (a[1] if a[1] < 0x80000000 else a[1] - (1 << 32)))
            return 0

        def provider(run, a):
            p, _ = run.alloc(0x40)
            run.wr32(p, UVT)
            run.wr32(a[0], p)
            return a[0]

        return {
            "PAL_Create": create, "PAL_Delete": delete, "PAL_ThreadCreateWithMsgQue": thr_create,
            "PAL_ThreadClose": thr_close, "PAL_ThreadGetQueId": qid, "PAL_MsgSend": msg_cap,
            "PAL_MsgSendRecv": msg_cap, "PAL_MsgReply": reply,
            "_ZN6vendor4somc8hardware6camera8provider4V1_025IVendorSomcCameraProvider10getServiceERKNSt3__112basic_stringIcNS6_11char_traitsIcEENS6_9allocatorIcEEEEb": provider,
        }


KNOWN_LOCK_FN = ("_ZN9cacao_pal5Mutex4lockEv", "_ZN9cacao_pal5Mutex7tryLockEv", "_ZN9cacao_pal5Mutex6unlockEv",
                 "_ZN9cacao_pal9Condition6signalEv", "_ZN9cacao_pal9Condition9timedWaitEjj")


def knorm(events):
    """已知差異（stop() 的全域 vs 成員鎖；init 的 thread 名稱格式）正規化後再比對，凸顯其他差異。"""
    out = []
    for n, a in events:
        if n in KNOWN_LOCK_FN and a and (a[0] == "@lib_data" or (isinstance(a[0], list) and a[0][0] == "H") or
                                         (isinstance(a[0], tuple) and a[0][0] == "H")) and \
                (a[0] == "@lib_data" or tuple(a[0])[2] in (168, 20, 320)):
            out.append((n, ("STOPLOCK",) + tuple(a[1:])))
        elif n == "PAL_StrNPrintf":
            out.append((n, (a[0], a[1], "FMT") + tuple(a[3:])))
        else:
            out.append((n, tuple(a)))
    return out


def deliver(w, gw, pal, rounds=8):
    while pal.pending and rounds:
        rounds -= 1
        batch, pal.pending = pal.pending, []
        for raw in batch:
            m = w.new(0x80)
            w.wbytes(m, raw)
            w.call("ProcessCtrlGatewayBase::threadDispatchMsg", m, gw)


def scenario(lib, name, flavor=0, **palkw):
    pal = Pal(**palkw)
    w = W(lib, seed=1, flavor=flavor)
    w.r.hooks = pal.hooks()
    w.r.retfn = None
    gw = w.new(0x700)
    w.call("_ZN5cacao18ProcessCtrlGatewayC2Ev", gw)
    steps = []
    base = lambda n: "cacao::ProcessCtrlGatewayBase::" + n

    def step(label, fn):
        e0, l0 = len(w.r.events), len(w.r.logs)
        try:
            r = fn()
        except KeyError as e:
            r = "KeyError:%s" % e
        deliver(w, gw, pal)
        steps.append({"step": label, "ret": r if isinstance(r, str) else (r - (1 << 32) if r >= 0x80000000 else r),
                      "fault": w.r.fault, "events": [e for e in filt_events(w.r.events[e0:])],
                      "logs": w.r.logs[l0:]})
        w.r.fault = None

    mode = None
    if name in ("start_stop",):
        sd0, _ = w.sd(bytes(0x200))
        mode = w.call("ProcessCtrlGatewayFactory::createMode", sd0)

    if name == "no_init_dtor":
        step("dtor", lambda: w.call("_ZN5cacao18ProcessCtrlGatewayD2Ev", gw))
    elif name == "init_dtor":
        step("init", lambda: w.call(base("init(short)"), gw, 0x78))
        step("dtor", lambda: w.call("_ZN5cacao18ProcessCtrlGatewayD2Ev", gw))
    elif name == "init_deinit_dtor":
        step("init", lambda: w.call(base("init(short)"), gw, 0x78))
        step("deinit", lambda: w.call(base("deinit()"), gw))
        step("dtor", lambda: w.call("_ZN5cacao18ProcessCtrlGatewayD2Ev", gw))
    elif name == "start_stop":
        step("init", lambda: w.call(base("init(short)"), gw, 0x78))
        step("start", lambda: w.call(base("start(cacao::ProcessModeBase const*)"), gw, mode))
        step("stop", lambda: w.call(base("stop()"), gw))
        step("stop2", lambda: w.call(base("stop()"), gw))
        step("deinit", lambda: w.call(base("deinit()"), gw))
        step("dtor", lambda: w.call("_ZN5cacao18ProcessCtrlGatewayD2Ev", gw))
    elif name == "dtor_via_vtable_D0":
        step("init", lambda: w.call(base("init(short)"), gw, 0x78))
        vt = w.r.rd32(gw)
        d0 = w.r.rd32(vt + 4)
        step("D0(vtable[1])", lambda: w.r.call(d0 - 0x10000000, [gw])[0])
    return {"steps": steps, "pal": pal.msglog, "pal_anoms": pal.anoms, "mutex_anoms": w.r.anomalies,
            "alive_threads": sum(1 for v in pal.threads.values() if v), "deleted": pal.deleted}


SCEN = ["no_init_dtor", "init_dtor", "init_deinit_dtor", "start_stop", "dtor_via_vtable_D0"]


def main():
    la, lb = Lib(D + "orig/lib/%s.so" % MOD), Lib(D + "new/lib/%s.so" % MOD)
    res = {}
    for name in SCEN:
        for flavor, kw in ((0, {}), (1, {}), (0, {"reply_err": -1}), (0, {"send_err": 0xffffff91})):
            tag = "%s|flavor%d|%s" % (name, flavor, ",".join("%s=%s" % kv for kv in kw.items()) or "ok")
            ra = scenario(la, name, flavor, **kw)
            rb = scenario(lb, name, flavor, **kw)
            diffs = []
            if ra["pal"] != rb["pal"]:
                diffs.append("PAL_SEQ")
            if ra["pal_anoms"] != rb["pal_anoms"]:
                diffs.append("PAL_ANOM")
            if [a[0] for a in ra["mutex_anoms"]] != [a[0] for a in rb["mutex_anoms"]]:
                diffs.append("MUTEX_ANOM")
            if ra["alive_threads"] != rb["alive_threads"]:
                diffs.append("ALIVE_THREADS")
            for sa, sb in zip(ra["steps"], rb["steps"]):
                if sa["ret"] != sb["ret"]:
                    diffs.append("RET@" + sa["step"])
                if sa["fault"] != sb["fault"]:
                    diffs.append("FAULT@" + sa["step"])
                if knorm(sa["events"]) != knorm(sb["events"]):
                    diffs.append("EVENTS@" + sa["step"])
                if sa["logs"] != sb["logs"]:
                    diffs.append("LOGS@" + sa["step"])
            res[tag] = {"diffs": diffs, "orig": ra, "new": rb}
    out = ROOT + "/.tmp/simverify/result/ctrl_gateway_scen.json"
    json.dump(res, open(out, "w"), indent=1, default=str)
    for k, v in res.items():
        print(k, v["diffs"], "origAnom", v["orig"]["pal_anoms"], v["orig"]["mutex_anoms"][:1], "newAnom", v["new"]["pal_anoms"], v["new"]["mutex_anoms"][:1])


if __name__ == "__main__":
    main()
