#!/usr/bin/env python3
"""libimageprocessorjni 場景式差分：原版 vs 重建版，逐步比對「外部可觀察行為」軌跡。

用法: scen_ipj.py <lib|lib64> <seeds> [out.json]
"""
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu_ipj import *  # noqa

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OD = ROOT + "/.tmp/simverify"
JN = "Java_com_sonymobile_imageprocessor_bypasscamera2_BypassCamera_native"

# 名稱 -> (spec, 參數樣板)
# 參數樣板: env thiz ctx(=jlong 或指標) 以外為 ('i', choices) 等
API = {
    JN + "IsDebugable": ("pp", ["env", "thiz"]),
    JN + "Initialize": ("ppi", ["env", "thiz", ("i", [0, 1, 2])]),
    JN + "Finalize": ("ppl", ["env", "thiz", "ctx"]),
    JN + "ChangeToPhotoMode": ("ppliiiiii", ["env", "thiz", "ctx", ("i", [0, 0, 0, 1]), ("i", [640, 4000]), ("i", [480, 3000]), ("i", [640, 2000]), ("i", [480, 1500]), ("i", [1, 3, 10])]),
    JN + "ChangeToVideoMode": ("ppliiiiii", ["env", "thiz", "ctx", ("i", [0, 1, 2]), ("i", [1920, 1280]), ("i", [1080, 720]), ("i", [1920, 1280]), ("i", [1080, 720]), ("i", [30, 60])]),
    JN + "ChangeToSuperSlowMode": ("ppliiiiiiii", ["env", "thiz", "ctx", ("i", [0, 1, 2]), ("i", [1920, 1280]), ("i", [1080, 720]), ("i", [1920, 1280]), ("i", [1080, 720]), ("i", [30, 120]), ("i", [480, 960]), ("i", [4, 8])]),
    JN + "GetLatestRequestId": ("ppl", ["env", "thiz", "ctx"]),
    JN + "RequestPrepareSnapshot": ("pplpi", ["env", "thiz", "ctx", "surface", ("i", [0, 1, 4, 8])]),
    JN + "RequestSnapshotReady": ("ppl", ["env", "thiz", "ctx"]),
    JN + "RequestSnapshot": ("ppl" + "ii" + "ddd" + "i" + "p" + "i" * 11,
                             ["env", "thiz", "ctx", ("i", [0, 1]), ("i", [0, 1]), ("d", [0.0, 25.5]), ("d", [0.0, 121.25]), ("d", [0.0, 30.0]), ("i", [0, 1]), "jstr"] + [("i", [0, 1, 5, 90, 270])] * 11),
    JN + "RequestSnapshotFree": ("ppl", ["env", "thiz", "ctx"]),
    JN + "RequestPrepareVideoRecording": ("pplpiii", ["env", "thiz", "ctx", "surface", ("i", [0, 1, 2, 30]), ("i", [0, 1, 1920]), ("i", [0, 1, 1080])]),
    JN + "RequestPrepareSuperSlowRecording": ("pplpiii", ["env", "thiz", "ctx", "surface", ("i", [0, 1, 2, 30]), ("i", [0, 1, 1920]), ("i", [0, 1, 1080])]),
    JN + "RequestStartVideoRecording": ("ppl", ["env", "thiz", "ctx"]),
    JN + "RequestStartSuperSlowRecording": ("ppl", ["env", "thiz", "ctx"]),
    JN + "RequestStopVideoRecording": ("ppl", ["env", "thiz", "ctx"]),
    JN + "RequestPrepareBurstShot": ("ppl", ["env", "thiz", "ctx"]),
    JN + "RequestFinishBurstShot": ("ppl", ["env", "thiz", "ctx"]),
    JN + "GetCaps": ("ppip", ["env", "thiz", ("i", [0, 1, 2]), "capsobj"]),
    JN + "SetConfig": ("pplp", ["env", "thiz", "ctx", "cfgobj"]),
    # 內部匯出
    "BypassCameraPhoto_initialize": ("ppp", ["env", "thiz", "ctxp"]),
    "BypassCameraPhoto_finalize": ("ppp", ["env", "thiz", "ctxp"]),
    "BypassCameraPhoto_changeToPhotoMode": ("piiiii", ["ctxp", ("i", [640, 4000]), ("i", [480, 3000]), ("i", [640, 2000]), ("i", [480, 1500]), ("i", [1, 3, 10])]),
    "BypassCameraPhoto_requestSnapshotReady": ("p", ["ctxp"]),
    "BypassCameraPhoto_prepareSnapshot": ("pppi", ["env", "ctxp", "surface", ("i", [0, 1, 4, 8])]),
    "BypassCameraPhoto_requestSnapshotFree": ("p", ["ctxp"]),
    "BypassCameraPhoto_prepareBurstShot": ("p", ["ctxp"]),
    "BypassCameraPhoto_finishBurstShot": ("p", ["ctxp"]),
    "BypassCameraVideo_initialize": ("ppp", ["env", "thiz", "ctxp"]),
    "BypassCameraVideo_finalize": ("ppp", ["env", "thiz", "ctxp"]),
    "BypassCameraVideo_changeToVideoMode": ("piiiiii", ["ctxp", ("i", [0, 1, 2]), ("i", [1920, 1280]), ("i", [1080, 720]), ("i", [1920, 1280]), ("i", [1080, 720]), ("i", [30, 60])]),
    "BypassCameraVideo_changeToSuperSlowMode": ("piiiiiiii", ["ctxp", ("i", [0, 1, 2]), ("i", [1920, 1280]), ("i", [1080, 720]), ("i", [1920, 1280]), ("i", [1080, 720]), ("i", [30, 120]), ("i", [480, 960]), ("i", [4, 8])]),
    "BypassCameraVideo_prepareVideoRecording": ("pppiii", ["env", "ctxp", "surface", ("i", [0, 1, 2, 30]), ("i", [0, 1, 1920]), ("i", [0, 1, 1080])]),
    "BypassCameraVideo_prepareSuperSlowRecording": ("pppiii", ["env", "ctxp", "surface", ("i", [0, 1, 2, 30]), ("i", [0, 1, 1920]), ("i", [0, 1, 1080])]),
    "BypassCameraVideo_startVideoRecording": ("p", ["ctxp"]),
    "BypassCameraVideo_startSuperSlowRecording": ("p", ["ctxp"]),
    "BypassCameraVideo_stopVideoRecording": ("p", ["ctxp"]),
    "BypassCameraBurst_initialize": ("ppp", ["env", "thiz", "ctxp"]),
    "BypassCameraBurst_finalize": ("ppp", ["env", "thiz", "ctxp"]),
    "BypassCameraBurst_requestSnapshot": ("ppp" + "ii" + "ddd" + "i" + "p" + "i" * 11,
                                           ["env", "thiz", "ctxp", ("i", [0, 1]), ("i", [0, 1]), ("d", [0.0, 25.5]), ("d", [0.0, 121.25]), ("d", [0.0, 30.0]), ("i", [0, 1]), "jstr", ("i", [0]), ("i", [0]), ("i", [0]), ("i", [0]), ("i", [0]), ("i", [0]), ("i", [0]), ("i", [0]), ("i", [0]), ("i", [0, 1]), ("i", [1, 3])]),
    "BypassCameraBurstBufferManager_initializeSurface": ("pppi" if False else "ppip", ["env", "surface", ("i", [0, 1, 4, 8]), "ctxp"]),
    "BypassCameraBurstBufferManager_finalizeSurface": ("p", ["ctxp"]),
    "BypassCameraBurstBufferManager_createBuffers": ("p", ["ctxp"]),
    "BypassCameraBurstBufferManager_deleteBuffers": ("pp", ["ctxp", "nullp"]),
    "BypassCameraBurstBufferManager_dequeueBuffer": ("pp", ["ctxp", "outp"]),
    "BypassCameraBurstBufferManager_queueBuffer": ("pp", ["ctxp", "entry"]),
    "BypassCameraBurstBufferManager_cancelBuffer": ("pp", ["ctxp", "entry"]),
    "BypassCameraBurstBufferManager_cancelBuffers": ("pp", ["ctxp", "nullp"]),
    "BypassCameraBurstBufferManager_cancelAllBuffer": ("pp", ["ctxp", "nullp"]),
    "BypassCameraBurstBufferManager_createBufVector": ("ppi", ["ctxp", "outp", ("i", [0, 1, 2, 4])]),
    "BypassCameraBurstBufferManager_dump": ("p", ["ctxp"]),
    "getJNIEnv": ("", []),
    "getSurface": ("pp", ["env", "surfobj"]),
}
# 內部匯出若在 so 內有不同的符號名 (C++ mangled)，以此表對應
ALIAS = {
    "imageprocessor_BypassCameraPhoto_requestSnapshot": "_ZN14imageprocessor33BypassCameraPhoto_requestSnapshotEP7_JNIEnvP8_jobjectPNS_19BypassCameraContextEhhdddhP8_jstringhihihiiiih",
}
API["imageprocessor_BypassCameraPhoto_requestSnapshot"] = (
    "ppp" + "ii" + "ddd" + "i" + "p" + "i" * 10,
    ["env", "thiz", "ctxp", ("i", [0, 1]), ("i", [0, 1]), ("d", [0.0, 25.5]), ("d", [0.0, 121.25]), ("d", [0.0, 30.0]),
     ("i", [0, 1]), "jstr"] + [("i", [0, 1, 5, 90, 270])] * 10)

# 這幾個在狀態機中最常被呼叫，抽樣權重較高
WEIGHT_FIRST = [JN + "Initialize"]


class Scenario:
    def __init__(self, lib_path, seed, steps, policy=None):
        self.lib = Lib(lib_path)
        self.seed = seed
        self.policy = policy or {}
        self.m = Machine(self.lib, seed, self.policy)
        self.steps = steps
        self.seg = []            # [(step_desc, events_slice, weak_slice)]
        self.ctx = None
        self.captured = []       # (listener, result)
        self.cb_done = 0
        self.cap_origin = []
        self.cb_done_map = {}
        self.cur_label = ''
        self._scanned = 0
        m = self.m
        self.h_thiz = self._obj("thiz")
        self.h_surfaces = [self._obj("surface%d" % i) for i in range(2)]
        self.h_caps = self._obj("capsobj")
        self.h_cfg = self._obj("cfgobj")
        self.h_str = None
        self.surfobj = self._obj("surfobj")

    def _obj(self, name):
        h = self.m.next_handle
        self.m.next_handle += 8
        self.m.objects[h] = name
        return h

    def resolve(self, tok, spec_char, rng):
        m = self.m
        if tok == "env":
            return m.env_ptr
        if tok == "thiz":
            return self.h_thiz
        if tok == "ctx":
            return self.ctx_or_bad(rng)
        if tok == "ctxp":
            return self.ctx_or_bad(rng)
        if tok == "surface":
            return rng.choice(self.h_surfaces + [0]) if rng.random() < 0.15 else self.h_surfaces[0]
        if tok == "capsobj":
            return self.h_caps
        if tok == "cfgobj":
            return self.h_cfg
        if tok == "jstr":
            h = m.next_handle
            m.next_handle += 8
            m.strings[h] = rng.choice(["", "ABC", "gps"])
            return h
        if tok == "nullp":
            return 0
        if tok == "outp":
            return m.env_alloc(64, "outp")
        if tok == "entry":
            return self.pick_entry(rng)
        if tok == "surfobj":
            return self.surfobj
        if isinstance(tok, tuple):
            kind, ch = tok
            return rng.choice(ch)
        raise ValueError(tok)

    def ctx_or_bad(self, rng):
        if self.ctx is None:
            return 0
        if self.policy.get("nullctx") and rng.random() < 0.2:
            return 0
        return self.ctx

    def pick_entry(self, rng):
        # BufEntry*：從 ctx 取不到結構，改在 env 配一塊全零的假 entry
        p = self.m.env_alloc(0x40, "entry")
        return p

    # ---- 掃描 Process 呼叫的參數，找 listener/result
    def scan_captures(self):
        m = self.m
        args = getattr(m, "proc_args", [])
        while self._scanned < len(args):
            raw = args[self._scanned]
            self._scanned += 1
            lis = res = None
            for k, a in enumerate(raw):
                if a <= 0xffff:
                    continue
                kk = self.classify(a)
                if kk and kk.startswith("L:") and lis is None:
                    lis = (a, kk)
                    if k + 1 < len(raw) and raw[k + 1] > 0xffff:
                        res = raw[k + 1]
            if lis:
                self.captured.append((lis, res))
                self.cap_origin.append(self.cur_label.replace(JN, ''))

    def classify(self, p):
        m = self.m
        if not (HEAP_BASE <= p < HEAP_BASE + HEAP_SZ):
            return None
        try:
            vt = m.rdw(p)
            if not (BASE <= vt < BASE + m.lib.size):
                return None
            names = []
            for k in range(0, 9):
                f = m.rdw(vt + k * m.w)
                if BASE <= f < BASE + m.lib.size:
                    fn = m.lib.func_at((f & ~1) - BASE)
                    names.append(fn[0] if fn else "")
                else:
                    names.append("")
        except UcError:
            return None
        for n in names:
            mm = re.search(r"imageprocessor(\d+)(\w+?Callback)", n)
            if mm and "onHandle" in "".join(names[2:4]):
                return "L:cb"
        if any("ProcessCtrlResult" in n for n in names[:4]):
            return "R"
        return None

    def run(self):
        m = self.m
        rng = random.Random(self.seed * 7919 + 13)
        # 啟動步驟
        prelude = [("JNI_OnLoad", "pp", [m.vm_obj, 0])]
        for fn, spec, vals in prelude:
            self.do(fn, spec, vals, "pre")
        for st in self.steps:
            kind = st[0]
            if kind == "api":
                name = st[1]
                spec, tmpl = API[name]
                ov = st[2] if len(st) > 2 else {}
                vals = []
                for k, (t, c) in enumerate(zip(tmpl, spec)):
                    if k in ov:
                        v = ov[k]
                        if isinstance(v, str):
                            v = self.resolve(v, c, rng)
                        vals.append(v)
                    else:
                        vals.append(self.resolve(t, c, rng))
                self.do(name, spec, vals, name)
                if name.endswith("Initialize") and name.startswith("Java_"):
                    ret = m.threads[0].retval
                    if ret and ret != 0xffffffff and ret != (1 << 64) - 1:
                        self.ctx = ret & ((1 << (8 * m.w)) - 1)
                        m.ctx_ptr = self.ctx
                    # 假如傳回 -1 則 ctx 維持
            elif kind == "cb":
                ne, nw = len(m.events), len(m.weak)
                self.do_cb(st[1], st[2], st[3], rng)
                self.seg.append(("cb:%s" % st[1], m.events[ne:], m.weak[nw:]))
            elif kind == "cball":
                # 依捕捉順序觸發所有尚未觸發的 listener，每個 listener 獨立成段 (以其來源步驟標記)
                n0 = self.cb_done_map.get(st[1], 0)
                for idx in range(n0, len(self.captured)):
                    ne, nw = len(m.events), len(m.weak)
                    self.do_cb(st[1], idx, st[2], rng)
                    self.seg.append(("cb[%s]:%s" % (self.cap_origin[idx], st[1]), m.events[ne:], m.weak[nw:]))
                self.cb_done_map[st[1]] = len(self.captured)
        return self

    def do(self, fn, spec, vals, label):
        m = self.m
        ne, nw = len(m.events), len(m.weak)
        fname = ALIAS.get(fn, fn)
        if fname not in self.lib.syms:
            m.ev("call", fn)
            m.ev("status", "NOSYM")
            self.seg.append((label, m.events[ne:], m.weak[nw:]))
            return
        m.fault = None
        self.cur_label = label
        m.call(fname, spec, vals, label)
        self.scan_captures()
        m.resolve_lazies()
        self.seg.append((label, m.events[ne:], m.weak[nw:]))

    def do_cb(self, which, idx, err, rng):
        m = self.m
        if not self.captured:
            return
        (lis, kind), res = self.captured[idx % len(self.captured)]
        label = "cb:%s" % which
        if res:
            # setResult / setProgress 透過物件自己的 vtable
            try:
                vt = m.rdw(res)
                f5 = m.rdw(vt + 5 * m.w)
                f7 = m.rdw(vt + 7 * m.w)
                m.run_quiet(f5, "pi", [res, err[0]])
                m.run_quiet(f7, "pi", [res, err[1]])
            except UcError:
                pass
        vt = m.rdw(lis)
        slot = 3 if which == "result" else 2
        f = m.rdw(vt + slot * m.w)
        m.fault = None
        m.call(f - BASE, "pp", [lis, res or 0], label, record_ret=False)
        self.scan_captures()
        m.resolve_lazies()


def I(n):
    return JN + n


def flows():
    F = {}
    snap_args = {3: 0, 4: 0}
    F["photo"] = [
        ("api", I("Initialize"), {2: 0}),
        ("api", I("ChangeToPhotoMode"), {3: 0, 4: 4000, 5: 3000, 6: 4000, 7: 3000, 8: 1}),
        ("api", I("RequestPrepareSnapshot"), {3: "surface", 4: 4}),
        ("api", I("RequestSnapshotReady")),
        ("cball", "result", (0, 100)),
        ("api", I("GetLatestRequestId")),
        ("api", I("RequestSnapshot"), {3: 1, 4: 1, 5: 25.5, 6: 121.25, 7: 30.0, 8: 1, 9: "jstr", 10: 1, 11: 90, 12: 1, 13: 5, 14: 1, 15: 5, 16: 2, 17: 3, 18: 1, 19: 5, 20: 7}),
        ("cball", "progress", (0, 50)),
        ("cball", "result", (0, 100)),
        ("api", I("GetLatestRequestId")),
        ("api", I("RequestSnapshotFree")),
        ("cball", "result", (0, 100)),
        ("api", I("Finalize")),
    ]
    F["photo0"] = [
        ("api", I("Initialize"), {2: 1}),
        ("api", I("ChangeToPhotoMode"), {3: 0, 4: 640, 5: 480, 6: 640, 7: 480, 8: 3}),
        ("api", I("RequestPrepareSnapshot"), {3: "surface", 4: 1}),
        ("api", I("RequestSnapshotReady")),
        ("cball", "result", (0, 100)),
        ("api", I("RequestSnapshot"), {3: 0, 4: 0, 5: 0.0, 6: 0.0, 7: 0.0, 8: 0, 9: "jstr", 10: 0, 11: 0, 12: 0, 13: 0, 14: 0, 15: 0, 16: 0, 17: 0, 18: 0, 19: 0, 20: 0}),
        ("cball", "result", (0, 100)),
        ("api", I("RequestSnapshotFree")),
        ("cball", "result", (5, 100)),
        ("api", I("Finalize")),
    ]
    F["video"] = [
        ("api", I("Initialize"), {2: 0}),
        ("api", I("ChangeToVideoMode"), {3: 0, 4: 1920, 5: 1080, 6: 1920, 7: 1080, 8: 30}),
        ("api", I("RequestPrepareVideoRecording"), {3: "surface", 4: 0, 5: 1920, 6: 1080}),
        ("cball", "result", (0, 100)),
        ("api", I("RequestStartVideoRecording")),
        ("cball", "result", (0, 100)),
        ("api", I("RequestStopVideoRecording")),
        ("cball", "result", (0, 100)),
        ("api", I("Finalize")),
    ]
    F["video1"] = [
        ("api", I("Initialize"), {2: 0}),
        ("api", I("ChangeToVideoMode"), {3: 1, 4: 1280, 5: 720, 6: 1280, 7: 720, 8: 60}),
        ("api", I("RequestPrepareVideoRecording"), {3: "surface", 4: 1, 5: 1280, 6: 720}),
        ("cball", "result", (5, 100)),
        ("api", I("RequestStartVideoRecording")),
        ("cball", "result", (5, 100)),
        ("api", I("RequestStopVideoRecording")),
        ("cball", "result", (5, 100)),
        ("api", I("Finalize")),
    ]
    F["slow"] = [
        ("api", I("Initialize"), {2: 0}),
        ("api", I("ChangeToSuperSlowMode"), {3: 0, 4: 1920, 5: 1080, 6: 1920, 7: 1080, 8: 30, 9: 960, 10: 8}),
        ("api", I("RequestPrepareSuperSlowRecording"), {3: "surface", 4: 0, 5: 1920, 6: 1080}),
        ("cball", "result", (0, 100)),
        ("api", I("RequestStartSuperSlowRecording")),
        ("cball", "result", (0, 100)),
        ("api", I("RequestStopVideoRecording")),
        ("cball", "result", (0, 100)),
        ("api", I("Finalize")),
    ]
    F["slow1"] = [
        ("api", I("Initialize"), {2: 0}),
        ("api", I("ChangeToSuperSlowMode"), {3: 1, 4: 1280, 5: 720, 6: 1280, 7: 720, 8: 120, 9: 480, 10: 4}),
        ("api", I("RequestPrepareSuperSlowRecording"), {3: "surface", 4: 1, 5: 1280, 6: 720}),
        ("cball", "result", (0, 100)),
        ("api", I("RequestStartSuperSlowRecording")),
        ("cball", "progress", (0, 50)),
        ("cball", "result", (0, 100)),
        ("api", I("RequestStopVideoRecording")),
        ("cball", "result", (0, 100)),
        ("api", I("Finalize")),
    ]
    F["burst"] = [
        ("api", I("Initialize"), {2: 0}),
        ("api", I("ChangeToPhotoMode"), {3: 0, 4: 4000, 5: 3000, 6: 4000, 7: 3000, 8: 5}),
        ("api", I("RequestPrepareSnapshot"), {3: "surface", 4: 6}),
        ("api", I("RequestPrepareBurstShot")),
        ("cball", "result", (0, 100)),
        ("api", I("RequestSnapshot"), {3: 1, 4: 1, 5: 25.5, 6: 121.25, 7: 30.0, 8: 1, 9: "jstr", 10: 1, 11: 90, 12: 1, 13: 5, 14: 1, 15: 5, 16: 2, 17: 3, 18: 1, 19: 5, 20: 7}),
        ("cball", "progress", (0, 50)),
        ("cball", "result", (0, 100)),
        ("api", I("RequestFinishBurstShot")),
        ("cball", "result", (0, 100)),
        ("api", I("RequestSnapshotFree")),
        ("cball", "result", (0, 100)),
        ("api", I("Finalize")),
    ]
    F["caps"] = [
        ("api", I("GetCaps"), {2: 0}),
        ("api", I("GetCaps"), {2: 1}),
        ("api", I("GetCaps"), {2: 2}),
        ("api", I("Initialize"), {2: 0}),
        ("api", I("SetConfig")),
        ("api", I("SetConfig")),
        ("api", I("SetConfig")),
        ("api", I("SetConfig")),
        ("api", I("IsDebugable")),
        ("api", I("GetLatestRequestId")),
        ("api", I("Finalize")),
    ]
    F["badhandle"] = [
        ("api", I("GetLatestRequestId"), {2: 0}),
        ("api", I("Finalize"), {2: 0}),
        ("api", I("ChangeToPhotoMode"), {2: 0, 3: 0, 4: 640, 5: 480, 6: 640, 7: 480, 8: 1}),
        ("api", I("RequestSnapshotReady"), {2: 0}),
        ("api", I("RequestStartVideoRecording"), {2: 0}),
        ("api", I("SetConfig"), {2: 0}),
        ("api", I("GetLatestRequestId"), {2: 0xffffffffffffffff}),
        ("api", I("Finalize"), {2: 0xffffffffffffffff}),
        ("api", I("RequestStartVideoRecording"), {2: 0xffffffffffffffff}),
        ("api", I("Initialize"), {2: 0}),
        ("api", I("Initialize"), {2: 1}),
        ("api", I("Finalize")),
        ("api", I("Finalize")),
        ("api", I("GetLatestRequestId")),
    ]
    F["badmode"] = [
        ("api", I("Initialize"), {2: 0}),
        ("api", I("ChangeToPhotoMode"), {3: 1, 4: 640, 5: 480, 6: 640, 7: 480, 8: 1}),
        ("api", I("ChangeToPhotoMode"), {3: 2, 4: 640, 5: 480, 6: 640, 7: 480, 8: 1}),
        ("api", I("ChangeToVideoMode"), {3: 2, 4: 1280, 5: 720, 6: 1280, 7: 720, 8: 60}),
        ("api", I("ChangeToVideoMode"), {3: 7, 4: 1280, 5: 720, 6: 1280, 7: 720, 8: 60}),
        ("api", I("ChangeToSuperSlowMode"), {3: 2, 4: 1280, 5: 720, 6: 1280, 7: 720, 8: 60, 9: 480, 10: 4}),
        ("api", I("RequestPrepareSnapshot"), {3: "surface", 4: 0}),
        ("api", I("RequestPrepareSnapshot"), {3: 0, 4: 4}),
        ("api", I("RequestPrepareVideoRecording"), {3: 0, 4: 0, 5: 1920, 6: 1080}),
        ("api", I("RequestPrepareSuperSlowRecording"), {3: 0, 4: 0, 5: 1920, 6: 1080}),
        ("api", I("Finalize")),
    ]
    return F


def gen_steps(seed, apis):
    rng = random.Random(seed)
    steps = [("api", JN + "Initialize")]
    n = rng.randrange(7, 16)
    weights = []
    for a in apis:
        w = 1
        if "Initialize" in a or "Finalize" in a:
            w = 1
        weights.append(w)
    for _ in range(n):
        if rng.random() < 0.25:
            steps.append(("cb", rng.choice(["result", "progress"]), rng.randrange(0, 8),
                          (rng.choice([0, 0, -1 & 0xffffffff, 5]), rng.choice([0, 50, 100, 0xffffffff]))))
        else:
            steps.append(("api", rng.choices(apis, weights)[0]))
    return steps


def run_pair(arch, seed, apis, policy=None, steps=None):
    steps = steps or gen_steps(seed, apis)
    out = {}
    for w in ("orig", "new"):
        sc = Scenario(f"{OD}/{w}/{arch}/libimageprocessorjni.so", seed, steps, policy)
        sc.run()
        out[w] = sc
    return steps, out["orig"], out["new"]


STRICT = {"call", "jni", "vm", "vcall", "anw", "anwb", "thread", "ret", "status", "vec", "guard"}
SOFT = {"sync", "free", "log"}


def split_chan(events):
    s = [e for e in events if e[0] in STRICT]
    y = [e for e in events if e[0] in SOFT]
    return s, y


import difflib


def sig_of(sa, sb):
    """差異簽名：只保留差異區塊（去掉堆積標號）。"""
    def clean(e):
        t = re.sub(r"\bH\d+(\+\d+)?\b", "H", str(e))
        t = re.sub(r"\bProcess\d+\b", "Process", t)
        return t
    A = [clean(x) for x in sa]
    B = [clean(x) for x in sb]
    sm = difflib.SequenceMatcher(None, A, B, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            out.append((tuple(A[i1:i2]), tuple(B[j1:j2])))
    return out


def compare(arch, seeds, apis, policy=None):
    res = {"seeds": {}, "funcs": {}}
    for seed in range(seeds):
        steps, a, b = run_pair(arch, seed, apis, policy)
        info = {"steps": [], "faults": [a.m.fault, b.m.fault]}
        first = True
        for (la, ea, wa), (lb, eb, wb) in zip(a.seg, b.seg):
            sa, ya = split_chan(ea)
            sb, yb = split_chan(eb)
            ok = sa == sb
            fn = res["funcs"].setdefault(la, {"n": 0, "equal": 0, "diff": 0, "first_diff": 0, "sigs": {}, "examples": []})
            fn["n"] += 1
            if ok:
                fn["equal"] += 1
            else:
                fn["diff"] += 1
                if first:
                    fn["first_diff"] += 1
                    first = False
                sg = sig_of(sa, sb)
                k = json.dumps(sg, ensure_ascii=False)
                d = fn["sigs"].setdefault(k, {"count": 0, "seeds": []})
                d["count"] += 1
                if len(d["seeds"]) < 5:
                    d["seeds"].append(seed)
            info["steps"].append((la, ok))
        res["seeds"][seed] = info
    return res


if __name__ == "__main__":
    arch = sys.argv[1]
    seeds = int(sys.argv[2])
    out = sys.argv[3] if len(sys.argv) > 3 else None
    apis = [k for k in API if k.startswith(JN)]
    r = compare(arch, seeds, apis, {'happy': True})
    for k, v in sorted(r["funcs"].items()):
        print("%-60s n=%d eq=%d diff=%d (first=%d) nsig=%d" % (k.replace(JN, "n:"), v["n"], v["equal"], v["diff"], v["first_diff"], len(v["sigs"])))
    if out:
        json.dump(r, open(out, "w"), indent=1, default=str)
