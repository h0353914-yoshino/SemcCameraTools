# G8342 LTE 開機慢 24 秒的真因：libqdp 的 APN type mask（TLV 0xDD）

日期：2026-10-20　裝置：G8342（BH90018Q63，LineageOS 22.2）

## 結論
- LOS 的 `vendor/lib64/libqdp.so`（sha1 f83527aa…）比 A9 原廠 `libqdp` 新：多了 APN type mask 機制
  （字串 `ApnType match found…`、`Udpate needed mismatch in apntype mask`、`qdp_profiles_for_apntype`、
  `createEmergencyProfile` 等，A9 版本完全沒有）。
- qcrild 以 `qdp_init3(?, isAPAssistMode=1, allow_update=1)` 初始化。`isAPAssistMode` 為 1 時，
  `qdp_3gpp_profile_create`（case 8）與 `qdp_3gpp_profile_update_params_v2` 會把 RIL 第 8 個參數（mask 字串，
  例：`49`＝0x31）轉成數字並把「valid」旗標設 1，編成 WDS TLV 0xDD（8 位元組）。
- A9 時代的 modem 不認得 TLV 0xDD，CREATE 回 result 1 / err 1；profile 1 沒被更新，modem DS 在
  `ds_eps_pdn_context.c:6957/6964` 閘門等約 24 秒才逾時。

## 證據
1. QMI 傳輸層替身（LD_PRELOAD `qmi_client_send_msg_sync`）接住 CREATE（msg 0x27，3120 位元組）：
   `isAPAssistMode=1` 時 `valid@+0xc18=1, mask@+0xc20=49`；修補後 `valid=0`。
2. 原本 qcrild strace：CREATE 帶 `dd 08 00 31…` 被拒；MODIFY（只帶 pdp_type）成功。
3. `qdp_3gpp_profile_create` A9 1728 B、LOS 3200 B；`fill_common_params` A9 2804 B、LOS 5436 B。

## 修補（兩個指令，改存 wzr）
| 位置 | 原指令 | 新指令 |
|---|---|---|
| 0x17fd4 `qdp_3gpp_profile_create` case 8 | `strb w28,[sp,#0xe50]` (393943fc) | `strb wzr,[sp,#0xe50]` (393943ff) |
| 0xe094 `qdp_3gpp_profile_update_params_v2` | `strb w23,[x21,#0xc1c]` (393072b7) | `strb wzr,[x21,#0xc1c]` (393072bf) |

`device/sony/yoshino-common/extract-files.py` 已加 `vendor/lib64/libqdp.so` 的 blob_fixup（來源 sha1 f83527aa… 不變）。
修補後 sha1：664fa915678a7cb826408f78825795ec39c2117e。與先前 libril-qc-hal-qmi.so 的 MODIFY 修補互補。

## 方法與工具（.tmp/ghidra_qdp/）
- Ghidra headless 反編譯（相對路徑／無點號符號連結）、重建 C `recon/libqdp_recon.c`（`build_all.sh` 可重現）。
- 裝置端差分：`/vendor/bin/sh` + LD_PRELOAD 注入 `libqmistub.so`（QMI 替身）與差分器；原版 vs 重建版 53 個匯出函式
  2120 案例 0 不一致（7 個函式需手工結構輸入，零輸入一致）。
- 栈帧模型：Ghidra `local_XXX` ＝ 進入時 sp − XXX（位址越大偏移越低），重建時必須用 `frame_top - XXX`。
