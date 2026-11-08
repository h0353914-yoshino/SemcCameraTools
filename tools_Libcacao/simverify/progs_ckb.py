"""libsomc_chokoballpal 的差分測試程式。"""
import random
import struct

NSEEDS = {"mk_create_buf_sys": 90, "mk_instance_sys": 80}
CI = "_ZN3ckb9CkbPalBuf14createInstanceEjjjjP9ckb_buf_tjNS0_6FormatEb"
CB = "_ZN3ckb9CkbPalBuf9createBufEjj18ckb_image_format_tbP9ckb_buf_t"
DB = "_ZN3ckb9CkbPalBuf9deleteBufEP9ckb_buf_t"
CC = "_ZN3ckb9CkbPalBuf10cleanCacheEP15ckb_image_buf_t"
IC = "_ZN3ckb9CkbPalBuf15invalidateCacheEP15ckb_image_buf_t"
INC = "_ZN3ckb9CkbPalBuf18increaseMemorySizeEj"
DEC = "_ZN3ckb9CkbPalBuf18decreaseMemorySizeEj"
GNB = "_ZN3ckb9CkbPalBuf15getNativeBufferEv"
C1 = "_ZN3ckb9CkbPalBufC1Ev"
D1 = "_ZN3ckb9CkbPalBufD1Ev"
D0 = "_ZN3ckb9CkbPalBufD0Ev"

DIMS = [0, 1, 16, 31, 32, 33, 640, 1000, 1920, 4000, 4096]
FMTS = [2, 0x10, 0x20, 0x40000000, 0, 1, 3, 0x11, 0xffffffff]


def mk_create_buf(seed):
    rng = random.Random(seed)
    w = {"alloc_rc": rng.choice([0, 0, 0, 5])}

    def prog(m):
        for _ in range(rng.randint(2, 6)):
            pb = m.alloc(32)
            m.wr(pb, b"\xcc" * 32)
            m.call(CB, rng.choice(DIMS), rng.choice(DIMS), rng.choice(FMTS), rng.choice([0, 1, 2]),
                   rng.choice([pb, pb, pb, 0]), dump=[(pb, 24)], label="createBuf")
            if rng.random() < 0.6:
                m.call(DB, rng.choice([pb, 0]), dump=[(pb, 24)], label="deleteBuf")
    return w, prog


def mk_create_buf_sys(seed):
    fi = seed % len(FMTS)
    di = (seed // len(FMTS)) % len(DIMS)

    def prog(m):
        pb = m.alloc(32)
        for h in (0, 1, 33, 480, 1081):
            for un in (0, 1):
                m.call(CB, DIMS[di], h, FMTS[fi], un, pb, dump=[(pb, 24)], label="createBuf")
    return {}, prog


def mk_instance(seed):
    rng = random.Random(seed)
    w = {"attach_rc": rng.choice([0, 0, 0, 7]), "initcheck": rng.choice([0, 0, 0, 1])}

    def prog(m):
        for _ in range(rng.randint(2, 6)):
            pb = m.alloc(32)
            m.wr(pb, struct.pack("<6I", rng.choice([0, 0x1111]), 0x2222, rng.choice([0, 5]), 0x4444, 0x5555, 0))
            wd, ht = rng.choice(DIMS), rng.choice(DIMS)
            stride = rng.choice([wd, (wd + 31) & ~31, (wd + 31) & ~31, wd + 1, 0, 64])
            scan = rng.choice([ht, ht + 8, 0, 64, ht - 1 if ht else 0])
            obj = m.call(CI, stride, scan, wd, ht, rng.choice([pb, pb, pb, 0]), rng.choice([0, 0x6000, 0x1000]),
                         rng.choice([0, 1, 2, 3, 0xffffffff]), rng.choice([0, 1]), dump=[(pb, 24)],
                         label="createInstance")
            if obj:
                m.call(GNB, obj, label="getNativeBuffer")
                if rng.random() < 0.5:
                    m.call(D1, obj, label="dtor1")
                else:
                    m.call(D0, obj, label="dtor0")
        m.call(GNB, 0)
    return w, prog


def mk_instance_sys(seed):
    rng = random.Random(seed)
    fmts = [0, 1, 2, 3, 7]
    renders = [0, 1]
    sizes = [(640, 480, 640, 480), (640, 480, 704, 480), (641, 480, 640, 480), (640, 481, 640, 480),
             (640, 480, 640, 500), (100, 100, 96, 100), (0, 0, 0, 0), (1920, 1080, 1920, 1088)]
    f = fmts[seed % 5]
    r = renders[(seed // 5) % 2]
    sz = sizes[(seed // 10) % len(sizes)]

    def prog(m):
        pb = m.alloc(32)
        m.wr(pb, struct.pack("<6I", 0x1111, 0x2222, 5, 0x4444, 0x5555, 0))
        obj = m.call(CI, sz[2], sz[3], sz[0], sz[1], pb, 0x6000, f, r, label="createInstance")
        if obj:
            m.call(D0, obj, label="dtor0")
    return {}, prog


def mk_cache_misc(seed):
    rng = random.Random(seed)
    w = {"clean_rc": rng.choice([0, 5])}

    def prog(m):
        for _ in range(rng.randint(2, 5)):
            inner = m.alloc(0x68)
            m.wr(inner, b"\x00" * 0x68)
            ib = m.alloc(32)
            m.wr(ib, struct.pack("<5I", 0, 0, 0, 0, rng.choice([inner, inner, 0])))
            m.call(CC, rng.choice([ib, ib, 0]), dump=[(inner, 0x68)], label="cleanCache")
            m.call(IC, rng.choice([ib, ib, 0]), dump=[(inner, 0x68)], label="invalidateCache")
            m.call(INC, rng.choice([0, 0x1000, 0x7fffffff]), label="increaseMemorySize")
            m.call(DEC, rng.choice([0, 0x1000, 0xffffffff]), label="decreaseMemorySize")
        o = m.alloc(16)
        m.call(C1, o, dump=[(o, 8)], label="ctor")
        m.call(D1, o, label="dtor1_empty")
    return w, prog
