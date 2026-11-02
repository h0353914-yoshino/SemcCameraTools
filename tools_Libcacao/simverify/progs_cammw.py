"""libcammw_util 的差分測試程式（每個 mk_* 回傳 (world, prog)；prog(m) 對 Machine 連續呼叫匯出函數）。"""
import random
import struct

# cammw 的 pixel_format 碼表（alloc/attach 共用）
FORMATS = [0, 0x10000, 0x10001, 0x20000, 0x20001, 0x40000, 0x40001, 0x80000, 0x100000, 0x100001,
           0x100002, 0x100003, 0x800000, 0x1000000, 0x1000001, 0x1000002, 0x2000000, 0x4000000,
           0x4000001, 0x4000002, 0x4000003, 0x4000004, 0x30000, 0x200000, 0x3000000, 0x5, 0xffffffff]
HFORMATS = [0x11, 0x21, 0x23, 0x25, 0x10, 0x109, 0x10b, 0x102, 0x113, 0x7fa30c04, 0x32315659, 0x20,
            0x3, 0x1, 0x22, 0x24, 0x0, 0x112, 0x114]
USAGES = [0, 1, 2, 4, 8, 0x10, 0x20, 0x40, 0x1000, 0x1001, 0x1004, 0x1020, 0x21, 0x41, 0x6, 0x80000]


def rflex(rng):
    base = 0x50900000
    st = rng.choice([320, 640, 1280, 704])
    h = rng.choice([240, 480, 720])
    ysz = st * h
    layouts = [
        (7, [(base, 1, 8, 8, 1, st, 1, 1), (base + ysz, 2, 8, 8, 2, st, 2, 2), (base + ysz + 1, 4, 8, 8, 2, st, 2, 2)]),
        (7, [(base, 1, 8, 8, 1, st, 1, 1), (base + ysz + 1, 2, 8, 8, 2, st, 2, 2), (base + ysz, 4, 8, 8, 2, st, 2, 2)]),
        (7, [(base, 1, 8, 8, 1, st, 1, 1), (base + ysz, 2, 8, 8, 1, st // 2, 2, 2), (base + ysz + ysz // 4, 4, 8, 8, 1, st // 2, 2, 2)]),
        (7, [(base, 1, 8, 8, 1, st, 1, 1), (base + ysz, 4, 8, 8, 2, st, 2, 2), (base + ysz + 1, 2, 8, 8, 2, st, 2, 2)]),
        (1, [(base, 1, 8, 8, 1, st, 1, 1)]),
    ]
    return rng.choice(layouts)


def fill_random(m, p, n, rng):
    m.wr(p, bytes(rng.getrandbits(8) for _ in range(n)))


def new_img_out(m):
    p = m.alloc(0x68 + 16)
    m.wr(p, b"\xa5" * (0x68 + 16))
    return p


# ---------------------------------------------------------------- bufmgr
def mk_bufmgr(seed):
    rng = random.Random(seed)

    def prog(m):
        mg = m.alloc(0x120)
        if rng.random() < 0.5:
            fill_random(m, mg, 0x120, rng)
        m.call("cammw_util_bufmgr_init", mg, dump=[(mg, 0x120)])
        for _ in range(rng.randint(3, 9)):
            op = rng.choice(["open", "lock", "lockidx", "unlock", "deinit", "open", "lock", "init0"])
            if op == "open":
                cnt = rng.choice([0, 1, 2, 3, 5, 10, 11])
                fds = m.alloc(4 * 12)
                for i in range(12):
                    m.w32(fds + 4 * i, rng.choice([3, 4, 5, 0xffffffff, 7]))
                m.call("cammw_util_bufmgr_open", mg, cnt, rng.choice([0, 0x1000, 5000]),
                       rng.choice([0, 1, 2, 3]), fds, dump=[(mg, 0x120)])
            elif op == "lock":
                oi = m.alloc(8)
                ob = m.alloc(32)
                m.call("cammw_util_bufmgr_lock_buf", mg, rng.choice([0, 1, 5]), oi, ob, dump=[(mg, 0x120), (oi, 4), (ob, 24)])
            elif op == "lockidx":
                ob = m.alloc(32)
                m.call("cammw_util_bufmgr_lock_buf", mg, rng.choice([0, 1, 2, 3, 9, 10, 99]), 0,
                       rng.choice([ob, 0]), dump=[(mg, 0x120), (ob, 24)])
            elif op == "unlock":
                m.call("cammw_util_bufmgr_unlock_buf", mg, rng.choice([0, 1, 2, 3, 9, 10, 99]), dump=[(mg, 0x120)])
            elif op == "deinit":
                m.call("cammw_util_bufmgr_deinit", mg, dump=[(mg, 0x120)])
            else:
                m.call("cammw_util_bufmgr_init", 0)
                m.call("cammw_util_bufmgr_lock_buf", 0, 0, 0, 0)
                m.call("cammw_util_bufmgr_unlock_buf", 0, 0)
                m.call("cammw_util_bufmgr_deinit", 0)
                m.call("cammw_util_bufmgr_open", 0, 1, 1, 1, 0)
    return {}, prog


# ---------------------------------------------------------------- event / time / misc
def mk_event(seed):
    rng = random.Random(seed)

    def prog(m):
        ev = m.alloc(0x80)
        fill_random(m, ev, 0x80, rng)
        m.call("cammw_util_event_init", ev, dump=[(ev, 0x80)])
        m.call("cammw_util_event_init", 0)
        m.call("cammw_util_event_notify", ev, rng.choice([0, 5, 0xffffffff]), dump=[(ev, 0x80)])
        m.call("cammw_util_event_notify", 0, 1)
        m.call("cammw_util_event_wait", ev, rng.choice([0, 1, 500, 1500, 70000]), dump=[(ev, 0x80)])
        m.call("cammw_util_event_wait", 0, 1)
        m.call("cammw_util_event_wait", ev, rng.choice([1, 2500]), dump=[(ev, 0x80)])
        m.call("cammw_util_event_deinit", ev)
        m.call("cammw_util_event_deinit", 0)
    return {"timedwait": rng.choice([0, 110])}, prog


def mk_time(seed):
    rng = random.Random(seed)

    def prog(m):
        for c in range(0, 5):
            m.call("cammw_util_get_timestamp", c, ret64=True)
        m.call("cammw_util_get_timestamp", rng.choice([-1, 7]), ret64=True)
        m.call("cammw_util_init_diff_timespec")
        m.call("cammw_util_init_diff_timespec")
        for fn in ("cammw_util_convert_boottime_to_monotonic", "cammw_util_convert_realtime_to_monotonic"):
            out = m.alloc(16)
            m.call(fn, rng.getrandbits(32), rng.randint(0, 100000), out, dump=[(out, 8)])
            m.call(fn, 5, 6, 0)
        m.call("cammw_util_get_thermal_camera_info")
        for z in (0, 1, 12):
            m.call("cammw_util_set_thermal", z, rng.getrandbits(32))
    return {"props": {}}, prog


def mk_thermal_prop(seed):
    rng = random.Random(seed)

    def prog(m):
        m.call("cammw_util_get_thermal_camera_info")
        m.call("cammw_util_set_thermal", 3, 77)
    return {"props": {"persist.camera.thermal": rng.choice(["1", "0", "5"]), "camera.thermal": "2"}}, prog


# ---------------------------------------------------------------- descriptor list
def mk_desclist(seed):
    rng = random.Random(seed)

    def prog(m):
        out = m.alloc(16)
        for _ in range(rng.randint(4, 12)):
            op = rng.choice(["add", "add", "del", "del"])
            fd = rng.choice([3, 4, 5, 6, 0xffffffff, 0])
            if op == "add":
                d = rng.getrandbits(40)
                m.call("_Z39cammw_util_gralloc1_add_descriptor_listiy", fd, d & 0xffffffff, d >> 32,
                       label="add")
            else:
                m.wr(out, b"\x77" * 8)
                m.call("_Z39cammw_util_gralloc1_del_descriptor_listiPy", fd, rng.choice([out, 0]),
                       dump=[(out, 8)], label="del")
    return {}, prog


# ---------------------------------------------------------------- shmem
def _gworld(rng, **kw):
    w = {"alloc_fmt": rng.choice(HFORMATS), "flex": rflex(rng)}
    w.update(kw)
    return w


def mk_alloc_buf(seed):
    rng = random.Random(seed)

    def prog(m):
        for _ in range(rng.randint(2, 6)):
            out = new_img_out(m)
            t = rng.choice([0, 1, 1, 1, 2, 3, 4, 0xffffffff])
            sz = rng.choice([0, 0x1000, 0x1234, 0x40000, 1 << 20])
            m.call("cammw_util_shmem_alloc_buf", t, rng.choice(USAGES), sz, rng.choice([out, out, 0]),
                   dump=[(out, 0x68)])
            if rng.random() < 0.7:
                m.call("cammw_util_shmem_free_buf", out, dump=[(out, 0x68)])
    return _gworld(rng), prog


def mk_alloc_image(seed):
    rng = random.Random(seed)

    def prog(m):
        for _ in range(rng.randint(2, 5)):
            out = new_img_out(m)
            t = rng.choice([0, 1, 1, 1, 1, 2, 3, 3, 4])
            fmt = rng.choice(FORMATS)
            w = rng.choice([0, 1, 33, 640, 1920, 4000])
            h = rng.choice([0, 1, 31, 480, 1080, 3000])
            m.w["alloc_fmt"] = rng.choice(HFORMATS)
            m.w["flex"] = rflex(rng)
            m.call("cammw_util_shmem_alloc_image_buf", t, rng.choice(USAGES), w, h, fmt,
                   rng.choice([0, 1, 2, 3, 4]), rng.choice([out, out, out, 0]), dump=[(out, 0x68)],
                   label="alloc_image t%d fmt%x" % (t, fmt))
            if rng.random() < 0.6:
                m.call("cammw_util_shmem_free_buf", out, dump=[(out, 0x68)])
    return _gworld(rng), prog


def mk_alloc_image_systematic(seed):
    """seed 編號 = 格式索引 × usage 索引：保證每個格式碼×每個 usage 組合都被跑到。"""
    fi = seed % len(FORMATS)
    ui = (seed // len(FORMATS)) % len(USAGES)
    rng = random.Random(seed)

    def prog(m):
        for t in (0, 1, 3):
            out = new_img_out(m)
            for hf in (0x11, 0x21, 0x109, 0x32315659):
                m.w["alloc_fmt"] = hf
                m.w["flex"] = rflex(rng)
                out = new_img_out(m)
                m.call("cammw_util_shmem_alloc_image_buf", t, USAGES[ui], 641, 479, FORMATS[fi], 1, out,
                       dump=[(out, 0x68)], label="t%d fmt%x usage%x hf%x" % (t, FORMATS[fi], USAGES[ui], hf))
                if t != 1:
                    break
    return _gworld(rng), prog


def mk_import(seed):
    rng = random.Random(seed)

    def prog(m):
        for _ in range(rng.randint(2, 5)):
            out = new_img_out(m)
            m.call("cammw_util_shmem_import_buf", rng.choice([0, 1, 2, 3, 4]), rng.choice([0, 0x1000, 5000, 1 << 20]),
                   rng.choice([0xffffffff, 0, 5, 9]), rng.choice([out, out, 0]), dump=[(out, 0x68)])
            if rng.random() < 0.5:
                m.call("cammw_util_shmem_free_buf", out, dump=[(out, 0x68)])
    return _gworld(rng), prog


def mk_free_raw(seed):
    """直接構造各型態的 buffer 描述子餵 free_buf / clean_buf。"""
    rng = random.Random(seed)

    def prog(m):
        for _ in range(rng.randint(3, 7)):
            b = m.alloc(0x68)
            t = rng.choice([0, 1, 1, 2, 3, 4, 5, 0xffffffff])
            hp = m.mk_handle(rng.choice(HFORMATS)) if rng.random() < 0.6 else 0
            vals = [rng.choice([0, 0x50000000, 0x20000800]), rng.choice([0, 0x1000]), rng.choice([3, 0xffffffff, 7]),
                    hp, t, rng.choice([0, 1, 0x101])]
            m.wr(b, struct.pack("<6I", *vals))
            if rng.random() < 0.5:
                m.call("cammw_util_shmem_free_buf", b, dump=[(b, 0x68)])
            else:
                m.call("cammw_util_shmem_clean_buf", b, rng.choice([0, 1, 2, 3, 99]), dump=[(b, 0x68)])
            if rng.random() < 0.2:
                m.call("cammw_util_shmem_free_buf", 0)
                m.call("cammw_util_shmem_clean_buf", 0, 1)
    return _gworld(rng), prog


def mk_attach(seed):
    rng = random.Random(seed)

    def prog(m):
        for _ in range(rng.randint(2, 5)):
            src = m.alloc(0x68)
            hp = m.mk_handle(rng.choice(HFORMATS), offset=rng.choice([0, 0x6000]))
            stype = rng.choice([1, 1, 1, 0, 2, 3, 4])
            m.wr(src, struct.pack("<6I", 0x50000000, rng.choice([0x1000, 0xa000]), 11, hp, stype, 0))
            src5 = m.alloc(16)
            m.wr(src5, struct.pack("<3I", rng.choice([0, 0x6000, 0x1000]), 5, 6))
            out = new_img_out(m)
            fmt = rng.choice(FORMATS)
            w = rng.choice([0, 640, 1000])
            h = rng.choice([0, 480, 360])
            m.call("cammw_util_shmem_attach_image_buf", src, rng.choice([100, 640]), rng.choice([50, 480]), fmt,
                   rng.choice([src5, src5, 0]), w, h, rng.choice([out, out, out, 0]), dump=[(out, 0x68), (src, 0x68)],
                   label="attach fmt%x type%d" % (fmt, stype))
            if rng.random() < 0.7:
                m.call("cammw_util_shmem_detach_image_buf", out, dump=[(out, 0x68)])
    return _gworld(rng, g1_failrc=rng.choice([1, 2, 0xffffffff])), prog


def mk_attach_systematic(seed):
    fi = seed % len(FORMATS)
    rng = random.Random(seed)

    def prog(m):
        for hf in (0x11, 0x109):
            src = m.alloc(0x68)
            hp = m.mk_handle(hf, offset=0x6000)
            m.wr(src, struct.pack("<6I", 0x50000000, 0xa000, 11, hp, 1, 0))
            src5 = m.alloc(16)
            m.wr(src5, struct.pack("<3I", 0x6000, 5, 6))
            out = new_img_out(m)
            m.call("cammw_util_shmem_attach_image_buf", src, 100, 50, FORMATS[fi], src5, 640, 480, out,
                   dump=[(out, 0x68)], label="attach_sys fmt%x" % FORMATS[fi])
            m.call("cammw_util_shmem_detach_image_buf", out, dump=[(out, 0x68)])
    return _gworld(rng), prog


def mk_make_from_handle(seed):
    rng = random.Random(seed)

    def prog(m):
        for _ in range(rng.randint(2, 5)):
            hf = rng.choice(HFORMATS + [rng.getrandbits(32)])
            hp = m.mk_handle(hf, w=rng.choice([640, 1280]), h=rng.choice([480, 720]), size=rng.choice([0x70800, 0x100000]),
                             offset=rng.choice([0, 0x6000]))
            out = new_img_out(m)
            m.w["flex"] = rflex(rng)
            m.call("cammw_util_shmem_make_image_buf_from_handle", rng.choice([hp, hp, hp, 0]),
                   rng.choice([0, 640, 321]), rng.choice([0, 480, 241]), rng.choice([0, 1, 3, 4]),
                   rng.choice([out, out, out, 0]), dump=[(out, 0x68)], label="mk_from_handle fmt%x" % hf)
    return _gworld(rng), prog


def mk_make_systematic(seed):
    hf = (HFORMATS + [0x7fa30c04 + 1, 0x101, 0x103, 0x112, 0x114])[seed % (len(HFORMATS) + 5)]
    fl = seed // (len(HFORMATS) + 5)
    rng = random.Random(seed)

    def prog(m):
        hp = m.mk_handle(hf, w=704, h=480, size=0x100000, offset=0x6000)
        out = new_img_out(m)
        m.call("cammw_util_shmem_make_image_buf_from_handle", hp, 641, 479, 1, out, dump=[(out, 0x68)],
               label="mk_from_handle fmt%x flex%d" % (hf, fl))
    return {"flex": [rflex(random.Random(100 + fl)) for _ in range(1)][0], "alloc_fmt": hf}, prog


def mk_reg(seed):
    def prog(m):
        m.call("cammw_util_shmem_register_buf", 1, 1, 0x1000)
        m.call("cammw_util_shmem_unregister_buf", 1, 1, 0x1000)
        m.call("cammw_util_shmem_register_buf", 0, 0, 0)
    return {}, prog


# ---------------------------------------------------------------- thread
def mk_thread(seed):
    rng = random.Random(seed)

    def prog(m):
        ctx = m.alloc(0x70)
        fill_random(m, ctx, 0x70, rng) if rng.random() < 0.3 else None
        m.wr(ctx, b"\0" * 0x70) if rng.random() < 0.7 else None
        nm = m.alloc_str(rng.choice(["abc", "", "x" * 70, "cam"]))
        routine = m.cb_stub("routine", 7)
        for _ in range(rng.randint(1, 4)):
            op = rng.choice(["create", "create", "destroy", "run"])
            if op == "create":
                m.call("cammw_util_thread_create", rng.choice([0, 1]), rng.choice([nm, 0]), rng.choice([0, 100, 120, 139, 140, 500, 0xffffff00]),
                       rng.choice([routine, routine, 0]), 0x1234, rng.choice([ctx, ctx, 0]), dump=[(ctx, 0x70)])
            elif op == "destroy":
                m.call("cammw_util_thread_destroy", rng.choice([ctx, 0]), dump=[(ctx, 0x70)])
            else:
                m.run_threads()
    return {}, prog


# ---------------------------------------------------------------- msg
def _msg(m, rng, payload=b"hello"):
    msg = m.alloc(0x34)
    pl = m.alloc(0x100)
    m.wr(pl, payload.ljust(0x100, b"\0"))
    nfd = rng.choice([0, 0, 1, 3, 10, 11])
    m.wr(msg, struct.pack("<3I", len(payload), pl, nfd) + b"".join(struct.pack("<I", 20 + i) for i in range(10)))
    return msg


def mk_msg_client(seed):
    rng = random.Random(seed)
    w = {"session_signal": rng.choice([True, True, False]), "wait_effect": rng.choice([True, False])}

    def prog(m):
        name = m.alloc_str(rng.choice(["svc", "abc_def", "", "x" * 120]))
        cb = m.cb_stub("msgcb", 5)
        dcb = m.cb_stub("disccb", 0)
        pd = m.alloc(64)
        m.wr(pd, bytes(range(64)))
        s = m.call("cammw_util_msg_cli_open", rng.choice([name, name, 0]), rng.choice([100, 120, 150]),
                   rng.choice([0x1234, 0x1234, 0]), cb, dcb, rng.choice([0, 16, 64]), rng.choice([pd, 0]),
                   7, 8, label="cli_open")
        if s:
            msg = _msg(m, rng)
            m.call("cammw_util_msg_send", s, msg, dump=[(msg, 0x34), (s, 0x120)], label="msg_send")
            msg = _msg(m, rng)
            m.call("cammw_util_msg_sendrecv", s, msg, dump=[(msg, 0x34), (s, 0x120)], label="msg_sendrecv")
            m.call("cammw_util_msg_send", 0, msg)
            m.call("cammw_util_msg_sendrecv", 0, msg)
            m.run_threads()
            m.call("cammw_util_msg_cli_close", s, label="cli_close")
        m.call("cammw_util_msg_cli_close", 0)
    return w, prog


def mk_msg_server(seed):
    rng = random.Random(seed)
    w = {"session_signal": True}

    def prog(m):
        name = m.alloc_str(rng.choice(["svc", "abc", ""]))
        cb = m.cb_stub("conncb", 0)
        mcb = m.cb_stub("msgcb", 5)
        dcb = m.cb_stub("disccb", 0)
        srv = m.call("cammw_util_msg_srv_open", rng.choice([name, name, 0]), rng.choice([100, 130]),
                     0x4321, rng.choice([cb, cb, 0]), label="srv_open")
        if srv:
            nm = m.alloc_str("sess")
            for i in range(rng.randint(1, 6)):
                sess = m.call("cammw_util_msg_srv_create_session", srv, rng.choice([30, 31, 0xffffffff]), nm, 120,
                              0x77, mcb, dcb, rng.choice([0, 8]), rng.choice([nm, 0]), 1, 2, dump=[(srv, 0xf4)],
                              label="srv_create_session")
                if sess and rng.random() < 0.5:
                    m.call("cammw_util_msg_srv_delete_session", srv, sess, dump=[(srv, 0xf4)], label="srv_delete_session")
            m.call("cammw_util_msg_srv_delete_session", srv, 0)
            m.call("cammw_util_msg_srv_close", srv, label="srv_close")
        m.call("cammw_util_msg_srv_close", 0)
        m.call("cammw_util_msg_srv_create_session", 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    return w, prog


def mk_msg_threads(seed):
    """執行 session thread / server thread 本體（腳本化 select/recvmsg/read）。"""
    rng = random.Random(seed)
    hdr = lambda fl, nfd, psz, res: struct.pack("<4I", fl, nfd, psz, res)
    script = []
    for _ in range(rng.randint(1, 4)):
        fl = rng.choice([0, 1, 2, 3, 9])
        psz = rng.choice([0, 4, 20])
        nfd = rng.choice([0, 0, 1, 11])
        script.append(([30], 1))
        script.append((hdr(fl, nfd, psz, rng.choice([0, 5])), [40] if nfd else None))
        if psz:
            script.append((b"PAYLOAD-" * 3, None))
    end = rng.choice(["shutdown", "eof", "err"])
    sel, rcv, rd = [], [], []
    for it in script:
        if isinstance(it[0], list):
            sel.append(it)
        else:
            rcv.append(it)
    if end == "shutdown":
        sel.append(([20], 1))
        rd.append(b"y")
    elif end == "eof":
        sel.append(([30], 1))
        rcv.append(0)
    else:
        sel.append(([30], 1))
        rcv.append(0xffffffff)
    w = {"select": sel, "recv": rcv, "read": rd, "session_signal": True}

    def prog(m):
        name = m.alloc_str("cli")
        cb = m.cb_stub("msgcb", 5)
        dcb = m.cb_stub("disccb", 0)
        s = m.call("cammw_util_msg_cli_open", name, 120, 0x99, cb, dcb, 8, name, 1, 2, label="cli_open")
        m.run_threads()
        m.obs.append({"call": "state", "ret": 0, "fault": None, "events": [], "csr_ok": True,
                      "dump": [m.snap_words(s, 0x1c0) if s else None]})
    return w, prog


def mk_time2(seed):
    rng = random.Random(seed)

    def prog(m):
        for c in (-1, 0, 1, 2, 3, 4, 5, 100):
            m.call("cammw_util_get_timestamp", c, ret64=True, label="get_timestamp(%d)" % c)
        for fn in ("cammw_util_convert_boottime_to_monotonic", "cammw_util_convert_realtime_to_monotonic"):
            for _ in range(3):
                out = m.alloc(16)
                m.wr(out, b"\xee" * 16)
                m.call(fn, rng.getrandbits(32), rng.choice([0, 1, 5, 100000, 0xffffffff]), out, dump=[(out, 16)], label=fn)
            m.call(fn, 5, 6, 0, label=fn + "_null")
        for z in (0, 1, 12, 0xffffffff, 1000):
            m.call("cammw_util_set_thermal", z, rng.getrandbits(32), label="set_thermal")
    return {}, prog
