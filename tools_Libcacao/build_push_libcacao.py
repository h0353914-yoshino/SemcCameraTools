#!/usr/bin/env python3
import shutil
import subprocess
import sys
from pathlib import Path

SEMCCAMERA_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SEMCCAMERA_ROOT))


from tools_Common.parse_args import parse_args  # noqa: E402
from tools_Common.push_common import copy_compiled_file, push, push_lib_list  # noqa: E402
from tools_Common.adb import Adb  # noqa: E402

LINEAGE_ROOT = Path.home() / "lineageos"
LUNCH_TARGET = "lineage_poplar-bp1a-userdebug"
PRODUCT_NAME = "poplar"

# ── 分割區配置（cacao 已全面移到 vendor，傳輸為 stable AIDL）──
# system：app 端（libimageprocessorjni 與 libcacao_client 的 core 變體），32/64 位元
SYSTEM_LIBS = [
    "libcacao_client",
    "libimageprocessorjni",
]
# vendor：server 端（cacaoserver 鏈，32 位元；libcacao_client/libcacao_pal 的 vendor 變體）
VENDOR_LIBS = [
    "libcacao_client",
    "libcacao_pal",
    "libcacao_process_ctrl_gateway",
    "libcacao_service",
]
# vendor 的非函式庫檔案：（product out 內相對路徑，裝置路徑，是否為可執行檔）
VENDOR_FILES = [
    ("vendor/bin/cacaoserver", "/vendor/bin/cacaoserver", True),
    ("vendor/etc/init/cacaoserver.rc", "/vendor/etc/init/cacaoserver.rc", False),
    (
        "vendor/etc/vintf/manifest/vendor.somc.cacao.xml",
        "/vendor/etc/vintf/manifest/vendor.somc.cacao.xml",
        False,
    ),
]

# ── Soong 模組名稱（不含 .so） ──
SOONG_MODULES = [
    "libcacao_client",
    "libcacao_pal",
    "libcacao_service",
    "libimageprocessorjni",
    "libcacao_process_ctrl_gateway",
    "cacaoserver",
    "vendor.somc.cacao.xml",
]


def push_staged_libs(adb: Adb, out_root: Path) -> None:
    """依 staged 目錄推送：system 函式庫 → /system/lib{,64}，vendor 檔案 → /vendor/..."""
    for arch in ("lib64", "lib"):
        arch_dir = out_root / "system" / arch
        libs = sorted(p for p in arch_dir.glob("*.so") if p.is_file()) if arch_dir.exists() else []
        if not libs:
            print(f"[WARN] staged system/{arch} 沒有檔案: {arch_dir}")
            continue
        print(f"[PUSH] system/{arch}: {len(libs)} 個檔案")
        try:
            push_lib_list(
                [p.name for p in libs],
                arch=arch,
                local_paths=libs,
                remote_dir=f"/system/{arch}",
                adb=adb,
            )
        except Exception as exc:
            print(f"[WARN] system/{arch} 推送失敗: {exc}")

    vendor_lib_dir = out_root / "vendor" / "lib"
    vlibs = sorted(p for p in vendor_lib_dir.glob("*.so") if p.is_file()) if vendor_lib_dir.exists() else []
    if vlibs:
        print(f"[PUSH] vendor/lib: {len(vlibs)} 個檔案")
        try:
            push_lib_list(
                [p.name for p in vlibs],
                arch="lib",
                local_paths=vlibs,
                remote_dir="/vendor/lib",
                adb=adb,
            )
        except Exception as exc:
            print(f"[WARN] vendor/lib 推送失敗: {exc}")
    else:
        print(f"[WARN] staged vendor/lib 沒有檔案: {vendor_lib_dir}")

    for rel, remote, is_exec in VENDOR_FILES:
        local = out_root / rel
        if not local.exists():
            print(f"[WARN] staged 檔案不存在: {local}")
            continue
        print(f"[PUSH] {rel} → {remote}")
        try:
            push([local], [remote], adb=adb)
            adb.shell(f"chmod {'755' if is_exec else '644'} {remote}", check=False)
        except Exception as exc:
            print(f"[WARN] {remote} 推送失敗: {exc}")

    # 重新標記 SELinux 標籤（cacaoserver 需標成 cacaoserver_exec 才會轉入 cacaoserver 網域）
    adb.shell(
        "restorecon -R /vendor/bin/cacaoserver /vendor/lib /vendor/etc/init "
        "/vendor/etc/vintf /system/lib /system/lib64",
        check=False,
    )
    print(
        "[INFO] 服務啟動順序：VINTF 片段與 cacaoserver.rc 變更需重開機才生效；"
        "sepolicy 變更請另外 m selinux_policy，並推送 /vendor/etc/selinux/{precompiled_sepolicy,"
        "vendor_sepolicy.cil,vendor_file_contexts,vendor_service_contexts} 後重開機。"
    )


def build(paths):
    modules = " ".join(SOONG_MODULES).strip()
    cmd = f"""
        set -e
        export CCACHE_EXEC=/usr/bin/ccache
        export USE_CCACHE=1
        source build/envsetup.sh
        lunch {LUNCH_TARGET}
        m {modules}
        """
    print(f"\n[RUN] cwd={LINEAGE_ROOT}\n{cmd}\n")
    subprocess.run(["bash", "-lc", cmd], cwd=str(LINEAGE_ROOT), check=True)


def copy(paths, out_root):
    """把 Soong 編譯產出複製到本地 staged 目錄（out/system/、out/vendor/）。"""
    product_out = paths["product_out"]

    if out_root.exists():
        print(f"[INFO] 清除 out 目錄：{out_root}")
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    for module in SYSTEM_LIBS:
        so = module + ".so"
        for arch in ("lib64", "lib"):
            src = product_out / "system" / arch / so
            if src.exists():
                copy_compiled_file(src, out_root / "system" / arch / so)

    for module in VENDOR_LIBS:
        so = module + ".so"
        src = product_out / "vendor" / "lib" / so
        if src.exists():
            copy_compiled_file(src, out_root / "vendor" / "lib" / so)

    for rel, _remote, _is_exec in VENDOR_FILES:
        src = product_out / rel
        if src.exists():
            copy_compiled_file(src, out_root / rel)

    print(f"\n[DONE] staged 至 {out_root}")


def main() -> int:
    args = parse_args("編譯並推送 libcacao 相關的 .so 到設備。", enable_sign=False)
    adb = Adb(serial=args.device)

    print("編譯" if args.build else "", end="")
    print("推送" if args.push else "", end="")

    repo_root = Path(__file__).resolve().parents[1]
    out_root = repo_root / "out"

    product_out = LINEAGE_ROOT / "out" / "target" / "product" / PRODUCT_NAME
    paths = {"product_out": product_out}

    if not product_out.exists():
        raise SystemExit(f"[ERR] 找不到 product out：{product_out}")

    if args.build:
        build(paths)
    if args.copy:
        copy(paths, out_root)
    if args.push:
        push_staged_libs(adb, out_root)
        if not args.reboot:
            return 0
        print("\n[INFO] 正在重啟設備...")
        try:
            adb.reboot(check=False)
        except Exception as exc:
            print(f"[WARN] 重啟失敗: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
