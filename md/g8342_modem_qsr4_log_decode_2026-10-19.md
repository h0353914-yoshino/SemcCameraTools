# G8342：從 modem 取得 QSR4 內部日誌並解碼（2026-10-19）

目的：AP 端 logcat 看不到 modem 內部。本文記錄如何用 diag 通道取出 modem 的 QSR4（雜湊壓縮）訊息，並用裝置自帶的字典還原成可讀文字。
前置知識（USB 組合、HDLC、CRC）見 `md/poplardcm_modem_diag_log_capture.md`。

## 1. 結論：QSR4 可以解碼

- modem 韌體（`modem.b18`）內嵌字典路徑 `/readonly/firmware/image/qdsp6m.qdb`。
- 該檔就在裝置的 firmware 分區：`/vendor/firmware_mnt/image/qdsp6m.qdb`（5,170,427 B，僅 root/system 可讀）。
- 不需要 QXDM 或外部字典，但字典必須與 modem 同一版建置（GUID 要一致）。

## 2. 字典格式

```
offset 0x00  7f 51 44 42  ("\x7fQDB")
offset 0x04  16 bytes     建置 GUID（與 modem.b18 內嵌的 GUID 同；modem 內是位元組反序）
offset 0x40  zlib 資料（78 da 開頭）
```

解壓後約 23 MB 文字，標頭為 `Qshrink 4.0 Hash Database File`，內容行格式：

```
<hash>:<ss_mask>:<ssid>:<line>:<file>:<format string>
```

本機 GUID：`e89023ff-e27f-bbce-aba6-6335b7bd84dd`，約 278,955 筆。

```bash
adb -s BH90018Q63 exec-out 'cat /vendor/firmware_mnt/image/qdsp6m.qdb' > qdsp6m.qdb
python3 -c "
import zlib
d=open('qdsp6m.qdb','rb').read()
open('qdb.bin','wb').write(zlib.decompressobj().decompress(d[0x40:]))"
```

## 3. 取得原始封包

1. 切 USB 為 diag 組合（G8342 的 PID 為 0x9012，COM 號以裝置管理員為準，本次是 COM22）：
   ```bash
   adb shell 'nohup sh -c "sleep 300; setprop sys.usb.config adb" >/dev/null 2>&1 &'   # 保險還原
   adb shell setprop sys.usb.config diag,serial_cdev,rmnet,adb
   ```
2. 用 Windows Python（pyserial）執行 `.tmp/diag_raw.py COM22 輸出檔 秒數`。它做兩件事：
   - 送 `7D 05 00 00 FF FF FF FF`（MSG_CONFIG 全開），每 4 秒重送（modem 重啟會清掉設定）。
   - 把收到的每個 HDLC 封包去跳脫、去 CRC 後，以「時間 hex」一行存檔。
3. 在擷取期間觸發要觀察的動作（例如 `cmd connectivity airplane-mode enable/disable`）。
4. 用完切回 adb：`adb shell setprop sys.usb.config adb`。

注意：
- 腳本與輸出放在 `C:\Users\h035\`（WSL 看不到 COM），再 `cp` 回 `.tmp/`。
- 90 秒約產生 120 萬行、數百 MB 以內；QSR4 封包佔七成以上。
- 擷取前先把 logd 緩衝調大，避免 radio 緩衝被大量 RIL 訊息沖掉：`adb shell logcat -b all -G 64M`（開機後設定；重開機即失效）。
- 同時另開 `adb logcat -b all -v threadtime,year` 存檔，用來對時。

## 4. 封包類型

| 第一個位元組 | 內容 |
|---|---|
| `0x99` | QSR4 訊息（本文主角） |
| `0x98` | QSR4 的另一種格式（帶 payload，尚未解析） |
| `0x92` | QSR（v1）訊息 |
| `0x79` | 內含字串的傳統 F3 訊息（`.tmp/diag_combo2.py` 可直接解） |
| `0x10` | 一般 log 封包（LTE NAS/RRC OTA 等，見舊文件） |

## 5. 解碼 0x99

封包結構（已用 3001 筆驗證，全部命中字典）：

```
bytes 0..3    99 02 <len16>
bytes 4..11   時間戳（8 bytes）
bytes 12..15  hash（uint32 小端）  ← 以此查字典
bytes 16..17  dd 84（GUID 尾碼）
bytes 18..    引數（壓縮打包，尚未完整解析）
```

目前只還原「檔名:行號 + 格式字串」，引數未解開，但已足夠看出狀態機流程。腳本 `.tmp/lte_boot/dec.py`：

```bash
python3 -I dec.py raw3.txt '正則表達式'      # 輸出：時間 檔名:行號 格式字串 引數hex
```

整檔解碼並依檔名統計：見 `.tmp/lte_boot/qsr4_dec.txt` 的產生方式（對每個 0x99 封包用 `hash` 查字典、寫成一行）。

## 6. 常用過濾（NAS / DS）

| 要看什麼 | 檔名關鍵字 |
|---|---|
| EMM 狀態機（附著、去註冊） | `emm_*.c`、`reg_*.c`、`mm_*.c` |
| ESM / PDN | `esm_*.c` |
| 資料服務 attach 流程 | `ds_eps_pdn_context.c`、`ds_dsd_apm.c`、`ds_mppm*.c` |
| profile 寫入 | `ds_qmi_wds_profile.c`、`ds_Profile_*.cpp` |
| 運作模式切換 | `cmph.c`、`cm.c`（`oprt_mode`） |
| SIM | `mmgsdi*.c` |

另有 diag log 封包可用 `.tmp/diag_lteall.py` 開啟 LTE（equip 0xB）全部 log code，其中 `0xB0EE` 是 EMM 狀態（state/substate），可直接看到「去註冊」停留多久。

## 7. 本次用這套方法查到的結果（摘要）

- 重開射頻後 modem 0.5 秒就駐上 CHT，但 Attach Request 要等約 26 秒。
- 原因：`ds_eps_pdn_context.c:6957` 迴圈 `profile1_change_came doesn't come yet, wait 1sec`，約 19 次後 `6964 did not come after all, continue LTE attach`。
- 此旗標由 Sony 客製的 `ds_qmi_wds_profile.c` 在「profile 1 內容被 AP 改寫並寫入 miscTA」時設為 TRUE。目前 qcrild 對 profile 1 只送「APN 類型」欄位（TLV 0xB1），舊 modem 不認得，整筆被拒（`result=1` → `Profile Change skip`）。
- 即使把該欄位拿掉（`libril-qc-hal-qmi.so` 的 `setProfileSupportedAPNTypes` 內 `strb w8,[sp,#0xd1c]` → `strb wzr,[sp,#0xd1c]`），modem 回 `result=0` 但旗標仍不設，需要「帶實際內容」的 profile 1 改寫。實驗已還原（SHA1 `cc70a2e8e2435dee4cb396dadbcd7c4c244287bd`）。
- 過去 22 份 logcat 的 radio on → `AttachPdnMgr_ActionRule` 都是 24～27 秒，與 EFS/fsg 設定無關。

## 8. 檔案位置

| 檔案 | 說明 |
|---|---|
| `.tmp/diag_raw.py` | 原始封包擷取（Windows Python） |
| `.tmp/diag_lteall.py` | LTE 全部 log code 擷取 |
| `.tmp/lte_boot/dec.py` | 0x99 解碼與過濾 |
| `.tmp/modem_g8342/qdsp6m.qdb`、`qdb.bin` | 字典（原檔與解壓後） |
| `.tmp/lte_boot/raw1.txt`、`raw2.txt`、`raw3.txt` | 擷取的原始封包 |
| `.tmp/lte_boot/qsr4_dec.txt` | raw1 的完整解碼結果 |
| `.tmp/qcrild_chk/libril-qc-hal-qmi.so`、`.patched.so` | qcrild 原檔與實驗修補檔 |

## 9. 尚未完成

- 0x99 的引數欄位未解（可再用 `%d` 個數與位元組長度推出打包方式）。
- 0x98 封包格式未解析。
- NAS 的 EMM 內部決策（例如為何停在 DEREGISTERED substate 7）只能由 `0xB0EE` 與文字訊息推論。
- modem 端旗標被設的確切條件，需要反組譯 Hexagon 韌體（雜湊值在指令中被拆成 immext + 低位，不能直接用位元組搜尋）。

## 10. 修正（2026-10-19 晚）：blob 修補已驗證

- 旗標條件確認：對 WDS profile 1 送「標準欄位」的 `MODIFY_PROFILE_SETTINGS`（0x28）成功時，modem 印 `Profile Change come, profile1_change_came set to TRUE`；旗標在 SIM 訂閱就緒時重置，設定後保持。
- 驗證工具：`.tmp/qmitool/qmiwds.c`（dlopen `libqmi_cci`/`libqmiservices`，`wds_get_service_object_internal_v01(1,0xc0,6)`，instance 0）。
- 修補：`libril-qc-hal-qmi.so`（來源 FP3 6.A.040.4）`setProfileSupportedAPNTypes`（0x14b3c7c）內三條指令：
  `0x14b3ec4 mov w8,#1 → cmp w20,#1`、`0x14b3ef0 strb w8,[sp,#0xd1c] → cset w8,eq`、`0x14b3ef4 str x19,[sp,#0xd20] → strb w8,[sp,#0x13c]`
  （不再送 APN 類型 TLV 0xDD，改為只對 profile 1 送 pdp_type TLV，值 0＝原值）。
- 結果：射頻開啟 → 註冊由約 26 秒降為 5.6 秒。
- 落實：`device/sony/yoshino-common/extract-files.py` 的 `blob_fixup`（52 位元組定長取代，已模擬驗證輸出與測試檔一致），`vendor/sony/yoshino-common/proprietary/vendor/lib64/libril-qc-hal-qmi.so` 已改為修補後版本（SHA1 `1a473f38…`）；`proprietary-files.txt` 的 SHA1 仍是來源檔 `cc70a2e8…`。
