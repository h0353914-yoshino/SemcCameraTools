#!/usr/bin/env python3
"""用法: run_diff.py cammw|ckb [seeds] [--prog 名稱] [--nofault]
對每個測試程式、每個種子，原版/重建版各跑一次（含逐點失敗注入），比對整條觀察序列。"""
import json
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu2 import Machine  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SV = ROOT + "/.tmp/simverify"
LIBS = {"cammw": "libcammw_util.so", "ckb": "libsomc_chokoballpal.so"}

WARM = True
DROP_EV = {"pthread_once", "pthread_equal"}
INJECTABLE = {"mmap", "dup", "pipe", "ashmem_create_region", "ashmem_set_prot_region",
              "hw_get_module", "sendmsg", "recvmsg", "pthread_create", "socket_local_client",
              "android_get_control_socket", "listen", "open", "write", "munmap", "select", "pthread_cond_timedwait",
              "g.open", "g1.createDescriptor", "g1.setFormat", "g1.setDimensions", "g1.setConsumerUsage",
              "g1.setProducerUsage", "g1.allocate", "g1.retain", "g1.release", "g1.lock", "g1.lockFlex",
              "g1.unlock", "g1.destroyDescriptor", "g1.perform", "accept", "read"}


def keep(e):
    n = e[0]
    if n in DROP_EV:
        return False
    if n.startswith("pthread_mutex_") or n.startswith("pthread_cond_"):
        a = e[1] if len(e) > 1 else None
        # 全域 context 的鎖（原版為堆積上的 context 物件，重建版為 .bss）屬初始化機制差異
        if a == "C" or (isinstance(a, tuple) and a[0] == "H" and a[1] < 0):
            return False
    return True


VOIDS = {"set_thermal", "cli_close", "srv_close", "srv_delete_session", "cammw_util_thread_destroy", "cammw_util_init_diff_timespec", "cammw_util_get_thermal_camera_info",
         "cammw_util_set_thermal", "cammw_util_msg_cli_close", "cammw_util_msg_srv_close",
         "cammw_util_msg_srv_delete_session"}
SOFT = {"logs": {}, "allocsz": {}, "numplanes": {}}


def canon_ev(e):
    """相容性正規化：alloc 家族合併；log 另走 soft channel；lockFlex 的 num_planes 輸入值略過。"""
    n = e[0]
    if n in ("calloc", "malloc", "new"):
        return ("alloc", e[2])
    if n == "g1.lockFlex":
        return e[:5] + e[6:]
    return e


def flt(evs):
    out = []
    net = {}
    for e in evs:
        if not keep(e) or e[0] == "log":
            continue
        if e[0].startswith("_ZNK7android7RefBase9incStrong"):
            net[e[1]] = net.get(e[1], 0) + 1
            continue
        if e[0].startswith("_ZNK7android7RefBase9decStrong"):
            net[e[1]] = net.get(e[1], 0) - 1
            continue
        out.append(canon_ev(e))
    for k2 in sorted(net, key=repr):
        out.append(("refnet", k2, net[k2]))
    # 連續 free/delete 視為集合（釋放順序屬編譯器/容器實作差異）
    res, run = [], []
    for e in out + [("END",)]:
        if e[0] in ("free", "delete"):
            run.append(("free",) + tuple(e[1:]))
        else:
            res.extend(sorted(run, key=repr))
            run = []
            res.append(e)
    return res[:-1]


def logs(evs):
    return [(e[1], e[2], e[3]) for e in evs if e[0] == "log"]


def fault_cat(f):
    if f is None:
        return None
    return f.split("(")[0].split(":")[0] + (":" + f.split(":")[1].split(" ")[0] if f.startswith("uc:") else "")


def run_one(path, spec, fail, warm=True, extra_hook=None, hot=False):
    world, prog = spec
    m = Machine(path, fail=fail, world=world)
    if warm and WARM:
        m.warm(hot)
    try:
        prog(m)
    except Exception as e:  # harness / guest 例外
        m.obs.append({"call": "EXC", "ret": repr(e)[:200], "fault": "py", "events": [], "csr_ok": True})
    return m


def compare(oa, ob, multi=False):
    """回傳第一個差異 dict（multi=True 時回傳全部差異 list，每個呼叫點至多一筆）。"""
    diffs = []
    n = max(len(oa), len(ob))
    for i in range(n):
        d = _cmp_one(oa, ob, i)
        if d:
            diffs.append(d)
            if not multi:
                return d
            if d.get("kind") == "len":
                break
    return diffs if multi else None


def _cmp_one(oa, ob, i):
    if i >= len(oa) or i >= len(ob):
        return {"idx": i, "kind": "len", "orig": len(oa), "new": len(ob)}
    a, b = oa[i], ob[i]
    for key in ("ret", "csr_ok"):
        if key == "ret" and a["call"].split(" ")[0] in VOIDS:
            continue
        if key == "ret" and a["fault"] == b["fault"] == "insn_limit":
            continue
        if a.get(key) != b.get(key):
            return {"idx": i, "call": a["call"], "kind": key, "orig": a.get(key), "new": b.get(key)}
    if fault_cat(a["fault"]) != fault_cat(b["fault"]):
        return {"idx": i, "call": a["call"], "kind": "fault", "orig": a["fault"], "new": b["fault"]}
    ea, eb = flt(a["events"]), flt(b["events"])
    if a["fault"] == b["fault"] == "insn_limit":
        ea, eb = ea[:30], eb[:30]
    if ea != eb:
        j = 0
        while j < min(len(ea), len(eb)) and ea[j] == eb[j]:
            j += 1
        return {"idx": i, "call": a["call"], "kind": "events", "at": j,
                "orig": ea[j:j + 3], "new": eb[j:j + 3], "n": [len(ea), len(eb)]}
    la, lb = logs(a["events"]), logs(b["events"])
    if [x[0] for x in la] != [x[0] for x in lb]:
        return {"idx": i, "call": a["call"], "kind": "log_count", "orig": la[:3], "new": lb[:3]}
    for x, y in zip(la, lb):
        SOFT["logs"].setdefault((x[1], x[2]), set()).add((y[1], y[2]))
    if a.get("dump") != b.get("dump"):
        da, db = a.get("dump") or [], b.get("dump") or []
        for k, (x, y) in enumerate(zip(da, db)):
            if x != y:
                w = [q for q in range(min(len(x), len(y))) if x[q] != y[q]] if isinstance(x, list) and isinstance(y, list) else None
                return {"idx": i, "call": a["call"], "kind": "dump", "region": k, "words": w[:8] if w else w,
                        "orig": [x[q] for q in w[:4]] if w else x, "new": [y[q] for q in w[:4]] if w else y}
    return None


def sigof(d):
    c = d.get("call", "?").split(" ")[0]
    k = d.get("kind")
    if k == "events":
        o = d["orig"][0][0] if d["orig"] else "-"
        n = d["new"][0][0] if d["new"] else "-"
        return "%s|events|%s->%s" % (c, o, n)
    if k == "dump":
        return "%s|dump|r%s w%s" % (c, d.get("region"), (d.get("words") or [])[:3])
    if k in ("ret", "fault"):
        return "%s|%s|%s->%s" % (c, k, str(d["orig"])[:30], str(d["new"])[:30])
    return "%s|%s" % (c, k)


def main():
    global WARM
    which = sys.argv[1]
    WARM = which == "cammw"
    seeds = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 20
    only = None
    if "--prog" in sys.argv:
        only = sys.argv[sys.argv.index("--prog") + 1]
    nofault = "--nofault" in sys.argv
    if which == "cammw":
        import progs_cammw as P
    else:
        import progs_ckb as P
    progs = [(n, f) for n, f in sorted(vars(P).items()) if n.startswith("mk_") and callable(f)]
    nseeds = getattr(P, "NSEEDS", {})
    po = SV + "/orig/lib/" + LIBS[which]
    pn = SV + "/new/lib/" + LIBS[which]
    res = {"lib": LIBS[which], "programs": {}}
    tot = same = diff = 0
    for pname, mk in progs:
        if only and only not in pname:
            continue
        for hot in ((False, True) if which == 'cammw' else (False,)):
            ns = nseeds.get(pname, seeds)
            pr = {"runs": 0, "diff_runs": 0, "diffs": []}
            for seed in range(ns):
                try:
                    spec_o, spec_n = mk(seed), mk(seed)
                    mo = run_one(po, spec_o, None, hot=hot)
                    mn = run_one(pn, spec_n, None, hot=hot)
                except Exception:
                    pr["diffs"].append({"seed": seed, "kind": "HARNESS", "tb": traceback.format_exc()[-600:]})
                    continue
                cands = []
                if not nofault:
                    seen = {}
                    for e in flt(sum([o["events"] for o in mo.obs], [])) + flt(sum([o["events"] for o in mn.obs], [])):
                        pass
                    names = set()
                    for mm in (mo, mn):
                        cnt = {}
                        for o in mm.obs:
                            for e in o["events"]:
                                if e[0] in INJECTABLE:
                                    cnt[e[0]] = cnt.get(e[0], 0) + 1
                        for k2, v in cnt.items():
                            names.add((k2, min(v, 3)))
                    for nm, c in sorted(names):
                        for k in range(c):
                            cands.append((nm, k))
                variants = [None] + cands
                for fv in variants:
                    fail = {fv: 1} if fv else None
                    try:
                        if fv:
                            ao = run_one(po, mk(seed), fail, hot=hot)
                            an = run_one(pn, mk(seed), fail, hot=hot)
                        else:
                            ao, an = mo, mn
                        dl = compare(ao.obs, an.obs, multi=True)
                        d = dl[0] if dl else None
                        if d:
                            d["more"] = dl[1:6]
                    except Exception:
                        d = {"kind": "HARNESS", "tb": traceback.format_exc()[-600:]}
                    pr["runs"] += 1
                    tot += 1
                    if d:
                        pr["diff_runs"] += 1
                        diff += 1
                        d["seed"] = seed
                        d["sig"] = sigof(d)
                        d["fail"] = list(fv) if fv else None
                        if len(pr["diffs"]) < 60:
                            pr["diffs"].append(d)
                    else:
                        same += 1
            res["programs"][pname + ("@hot" if hot else "@cold")] = pr
            print("%-34s runs=%5d diff=%5d" % (pname + ("@hot" if hot else "@cold"), pr["runs"], pr["diff_runs"]), flush=True)
    res["total"] = {"runs": tot, "same": same, "diff": diff}
    os.makedirs(SV + "/result", exist_ok=True)
    res["soft_logs"] = [[list(k), sorted(map(list, v))] for k, v in SOFT["logs"].items()]
    json.dump(res, open(SV + "/result/raw_%s%s.json" % (which, ("_" + only) if only else ""), "w"), indent=1, default=str)
    print(res["total"])


if __name__ == "__main__":
    main()
