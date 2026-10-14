# poplardcm：從 modem 取得內部日誌與讀寫 EFS（diag 方式）

2026-10-13 在 701SO（poplardcm，LineageOS 22.2，MPSS.AT.2.0.c4.3-00278）上實作並驗證。
目的：AP 端的 logcat/dmesg 看不到 modem 內部（`dog_hb` 當機、attach 失敗、IMS 承載被拒），改用 Qualcomm diag 通道從 PC 直接取得。

## 1. 為什麼走 diag，而不是別的

| 方式 | 結果 |
|---|---|
| logcat / dmesg | 只看得到 AP 側與 `SSLM` 轉出的少量 modem 訊息；modem 當機前後什麼都沒有 |
| modem F3 訊息（QXDM） | 訊息是 QSR4 雜湊壓縮，需要對應版本的字典（`.qsr4` / qdb），手上沒有，無法解碼 |
| **diag log 封包（本文方法）** | **LTE NAS/RRC 空口封包的格式是公開的，不需字典，可以直接解碼** |
| diag EFS2 命令 | 可讀寫 modem EFS 檔案（policyman、Data_Profiles…），不需要 QPST |

## 2. 前置：讓 USB 帶出 diag 且 adb 不消失

這支手機預設只有 adb。要有 diag 口，執行時期切 USB 組合：

```bash
adb root
adb shell setprop sys.usb.config diag,serial_cdev,rmnet,adb
```

- 此組合使用 PID `0x9012`（見 `yoshino-common` 提交 `d6dd2c23`）。舊的 PID `0x9091` 會讓 ADB 介面落在 MI_02 被 Windows 的 Qualcomm WWAN 驅動搶走，adb 會消失。
- Windows 端會出現 `Qualcomm HS-USB Diagnostics 9012 (COM10)`。COM 號碼以裝置管理員為準。
- 用完一定要切回：`adb shell setprop sys.usb.config adb`。
- **保險機制**：切 diag 前先在裝置背景排一個自動還原，避免 adb 回不來：
  ```bash
  adb shell 'nohup sh -c "sleep 150; setprop sys.usb.config adb" >/dev/null 2>&1 &'
  ```
  注意：這種背景任務會累積，舊的會在之後誤把 diag 切回 adb。開新一輪前先
  `adb shell 'pkill -f "setprop sys.usb.config adb"'`。
- 切換組合時 USB 會重新列舉，adb 與 COM 埠都會暫時消失 5～10 秒，要等。

### COM 口被占用
QPST 的 `QPSTServer`／`EFSExplorer` 會獨占 COM 埠，Python 會報 `could not open port`（Windows error 170/22）。**必須先請使用者關閉 QPST**，不要自行結束它的程序。

## 3. Diag 協定最小知識

### 3.1 封裝（HDLC-like）
- 一個封包 = `payload + CRC16`，再逐 byte 跳脫，最後接 `0x7E`。
- CRC16：CRC-CCITT 反射型，初值 `0xFFFF`，多項式 `0x8408`，最後取反，小端附在 payload 後面。
- 跳脫：`0x7E`、`0x7D` 變成 `0x7D, byte ^ 0x20`。

### 3.2 Windows 端 Python
用 Windows 的 Python + pyserial（WSL 看不到 COM 口）：

```bash
PY=/mnt/c/Users/h035/AppData/Local/Python/pythoncore-3.14-64/python.exe
```

腳本要複製到 Windows 使用者目錄再執行（`cp x.py /mnt/c/Users/h035/`），輸出檔也寫在那裡，再 `cp` 回專案 `.tmp/`。

## 4. 取得 LTE NAS/RRC 空口封包

### 4.1 設定 log mask
命令 `0x73`（LOG_CONFIG），子命令 3（SET_MASK）：

```
73 00 00 00 | 03 00 00 00 | equip_id(4) | last_item(4) | mask bytes
```

- LTE 的 equip id 是 `0xB`。`last_item` 設 `0x100`，mask 長度 32 bytes。
- 要開的 log code，在 mask 的位元位置是 `code & 0xFFF`：

| log code | 內容 |
|---|---|
| `0xB0EC` / `0xB0ED` | LTE NAS EMM OTA（下行/上行）：Attach、TAU、Service、Detach… |
| `0xB0E2` / `0xB0E3` | LTE NAS ESM OTA（下行/上行）：PDN 連線、承載啟用… |
| `0xB0C0` | LTE RRC OTA（ASN.1 UPER，本次未解碼，只留原始資料） |

- 回應 `73 00 00 00 03 00 00 00 00 00 00 00 0b 00 00 00` 代表設定成功。
- **modem 重啟（SSR）後 mask 會被清掉**，必須重送。

### 4.2 讀取封包
Log 封包格式：

```
10 | more(1) | len(2) | len(2) | log_code(2) | timestamp(8) | payload...
```

- log_code 在 `r[6:8]`，payload 從 `r[16:]` 開始。
- NAS OTA 的 payload 前 4 bytes 是版本等標頭，之後才是 NAS 訊息（`07 xx`＝EMM，`02 xx`＝ESM；若有 security header 要再跳過 6 bytes）。

### 4.3 斷線重連
USB 在開機早期、modem 重啟、組合切換時都會重新列舉，串口會丟 `GetOverlappedResult failed` 或 `PermissionError`。腳本必須：
1. 讀寫例外時重開串口；
2. 重開後重送 mask；
3. 每輪寫檔後 flush，這樣中途斷掉資料也還在。

### 4.4 抓「開機當下」的 attach
attach 約發生在開機後 10～40 秒，所以流程是：
`adb reboot` → 等 `sys.boot_completed=1` → `adb root` → 切 diag 組合 → 立即開始抓（`cap_boot.sh` 已包好）。
抓取時間 110 秒就足以涵蓋 attach、IMS PDN 請求與第一次 `dog_hb` 當機。

## 5. 解讀 NAS 訊息（3GPP TS 24.301）

`nas_decode.py` 會輸出類似：

```
15.29 EMM_OTA_OUT  EMM ATTACH_REQ attach_type=2 ... VoiceDomainPref/UEusage=03 ...
16.52 EMM_OTA_IN   EMM ATTACH_ACCEPT eps_result=2 | ESM ACT_DEF_BEARER_REQ APN=internet.mnc092.mcc466.gprs
18.78 ESM_OTA_OUT  ESM PDN_CONN_REQ req_type=1 pdn_type=2 APN=IMS
18.78 ESM_OTA_IN   ESM PDN_CONN_REJ ESMcause=50
```

重點欄位：
- **Attach Request 的 IE `0x5D`（Voice domain preference and UE's usage setting）**：
  `0x00`＝語音中心、只用 CS；`0x03`＝IMS PS 語音優先、CS 次要。這是 policyman `voice_domain_pref` 的直接結果。
- **ESM `pdn_type`**：1＝IPv4、2＝IPv6、3＝IPv4v6。
- **ESM cause 常見值**：#27 APN 未知、#31 未指定原因拒絕、#33 未訂閱、#50 只允許 IPv4、#51 只允許 IPv6。
- **Attach Accept 的 IE `0x64`（EPS network feature support）bit0**＝網路支援 IMS VoPS。

## 6. 讀寫 modem EFS（EFS2 診斷命令）

命令前綴 `4B 13 <cmd:2>`（subsys 0x13＝EFS2）。**命令碼容易記錯**：

| cmd | 動作 | 請求內容 |
|---|---|---|
| 2 | open | `oflag(4) mode(4) path\0` → 回 `fd(4) errno(4)` |
| 3 | close | `fd(4)` |
| 4 | read | `fd(4) nbytes(4) offset(4)` → 回 `fd offset n errno data` |
| 5 | write | `fd(4) offset(4) data` → 回 `fd offset n errno` |

注意事項：
- **不要送 hello（cmd 0）**，這顆 modem 會回 bad-param。
- 腳本一開始先 `close` fd 0～2，避免前一次異常結束洩漏 fd（第二次 open 會拿到 fd=1，與預期不符）。
- 覆寫整個檔案用 `oflag=0o1101`（`O_WRONLY|O_CREAT|O_TRUNC`），新舊檔案長度不同時才不會殘留尾巴。
- 寫完一定要讀回比對 md5。
- modem 正在 SSR 中途時 diag 會逾時，重試即可；崩潰迴圈中要在 modem 剛起來的空檔寫。
- 讀取分段 1024 bytes。

### 本次讀寫過的檔案
| EFS 路徑 | 說明 |
|---|---|
| `/policyman/carrier_policy.xml` | policyman 運營商策略；即時版在 modemst，出廠金本在 fsg（`/dev/block/sda34`，tar 格式） |
| `/policyman/device_config.xml` | 裝置組態（單 SIM、G W L） |
| `/Data_Profiles/Profile2` | **IMS 的 PDN profile**（APN=`IMS`，屬性 `11 00 01 00 02` 是 PDP type） |
| `/Data_Profiles/Profile3` | 另一個 profile |
| `/data/ds_dsd_attach_profile.txt` | attach 用的 profile id（`Attach_Profile_ID:1;`） |

### 讀 fsg 金本（不需要 diag）
fsg（`/dev/block/sda34`，約 1.5 MB）是 tar 格式，裡面就是出廠 EFS。`adb shell dd` 取出後，找 `ustar` 字樣，往前 257 bytes 是檔頭，檔案內容在檔頭後 512 bytes。
**tar 的 size 欄位是八進位**（例如 `00000012077` 是 5183 bytes），不是十進位。內容以 CRLF 換行。

## 7. 本次用到的腳本（都在 `SemcCameraUI/.tmp/`）

| 腳本 | 用途 |
|---|---|
| `diag_efs_read.py COM10 <path>...` | 讀 EFS 檔案，存成 `<路徑底線>.live` |
| `diag_efs_write.py COM10 <efs路徑> <本機檔>` | 覆寫 EFS 檔案（截斷） |
| `diag_logcap.py COM10 <輸出> <秒數>` | 設 mask 並抓 NAS/RRC 封包（含斷線重連） |
| `nas_decode.py <cap檔>` | 解 NAS 訊息 |
| `cap_boot.sh <標籤> [秒數]` | 重開機後立刻切 diag 並抓封包，存 `cap_<標籤>.txt` |
| `apply_policy.sh <xml>` | 切 diag、寫 `carrier_policy.xml`、讀回驗證、切回 adb |
| `boot_probe.sh <標籤>` | 重開機，記錄「進服務秒數」與 modem 當機次數 |
| `make_variants.py` | 以出廠 policy 為底，產生二分測試變體 |

## 8. 用這個方法查到的結論（摘要）

1. policyman 的 `operator_mcc_list` 加入台灣 MCC `466` 會讓 modem 不穩，**但 CA 組合與 `rf_bands_all` 分支沒有問題**（變體 C、E 皆 3/3 正常）；問題只來自「語音域不再被強制 `CS_ONLY`」（變體 D，4 次中 3 次異常）。
2. NAS 封包顯示：進入 IMS 模式後，modem 以 `Profile2` 發出 **IPv6-only 的 IMS PDN 請求**，網路回 ESM cause 50（只允許 IPv4），modem 不改用 IPv4 重試，之後卡住或 `dog_hb` 當機。
3. 把 `Profile2` 的 PDP type 由 2（IPv6）改成 3（IPv4v6）後，網路接受 IMS 承載（`APN=ims.mnc092.mcc466.gprs`），D 變體 4/4 開機穩定。
4. 尚未解決：手機端隨後以 ESM cause 31 拒絕這個 IMS 承載，IMS 仍未註冊。

## 9. 注意事項

- 台灣已無 3G，語音通話需要 VoLTE，所以「永遠 `CS_ONLY`」不是長久解法。
- EFS 寫入是持久的。實驗前先備份（`.tmp/` 內已有 `carrier_policy_fsg_orig.xml`、`live_Data_Profiles_Profile2.bin`）。
- policyman 的變更要重開機才生效。
- 每個變體至少測 3 次開機：問題是機率性的，單次正常不代表沒事（原版 466 五次中 4 次異常，其中一次正常）。

## 10. 補充：F3 明文訊息、合併時間軸、EFS 目錄列舉

### 10.1 這顆 modem 的 F3 有大量「明文」可讀
原本以為 F3 全是 QSR4 雜湊壓縮、沒字典讀不了。實測 MPSS.AT.2.0.c4.3-00278 開啟全部 F3 mask 後，20 秒就有約 8 萬筆，其中封包類型：

| 封包首位元組 | 內容 | 能否讀 |
|---|---|---|
| `0x79` | Extended message：含**格式字串、檔名、行號、參數** | **可讀** |
| `0x98` / `0x99` | QSR / QSR4 雜湊壓縮 | 需字典，不讀 |

明文訊息的來源包括 `ds_*.c`（資料服務）、`lte_rrc_*`（RRC 狀態機，會顯示 `LTE_RLCUL_MAX_RETX_IND`、`CRE_STARTED_INDI` 等）、`policyman_uim.c`、`sdss.c`、`mc_msgr.c`（RF 頻段/頻道）、`netmgr_*`、`qdp.c`、`qcril_data_netctrl.c`，甚至 **AP 端的 IMS 堆疊**（`[IMS_AP]`、`[IMS_QMID]`、`PDPHandler`、`RegisterManager`）與 qcril（SSID 63，`DiagLogger.cpp`）都會經 diag 送出。

設定方式：命令 `7D 05 00 00 FF FF FF FF`（SET_ALL_MASKS，rt mask 全開）。

`0x79` 封包格式：
```
79 | ts_type(1) | num_args(1) | drop_cnt(1) | ts(8) | line(2) | ssid(2) | mask(4) | args(4*n) | fmt\0 | file\0
```
- 行號在 `r[12:14]`、ssid 在 `r[14:16]`、參數從 `r[20:]` 起；`fmt % args` 即可還原文字（`%d` 要做有號轉換）。
- 速率很高（約 4000 筆/秒含雜湊封包），只存 `0x79` 解碼文字，100 秒約 11～19 萬行。
- 寫檔務必 `encoding='utf-8', errors='replace'`，Windows 預設 cp950 遇到 `\xff` 會丟 `UnicodeEncodeError` 中斷整個抓取（第一次就因此只抓到 11 秒）。

### 10.2 NAS 空口封包 + F3 文字放在同一條時間軸
`diag_combo.py`（`cap_boot_combo.sh <標籤> [秒]`）同時開 log mask 與 F3 mask，輸出每行以抓取時間起算：
- `<秒> LOG <名稱> <hex>`：NAS 封包（再用 `nas_decode.py` 解）；
- `<秒> [ssid] 檔:行 | 文字`：F3 明文。

這樣才能把「NAS 看到的現象」對到「modem 內部當時在做什麼」。例如：IMS 的 `PDN_CONN_REQ` 在 21.03 秒發出，F3 顯示 21.83 秒 `LTE_RLCUL_MAX_RETX_IND`（上行 RLC 重傳達上限 → 無線鏈路失敗）。

### 10.3 列舉 EFS 目錄（EFS2 opendir/readdir）
| cmd | 動作 | 請求 → 回應 |
|---|---|---|
| 11 | opendir | `path\0` → `dirp(4) errno(4)` |
| 12 | readdir | `dirp(4) seqno(4)`，seqno 從 1 起 → `dirp seq errno type(1=dir) mode size atime mtime ctime name\0`（名稱從 `r[40:]`） |
| 13 | closedir | `dirp(4)` |

`diag_efs_ls.py COM10 <目錄>...` 可列出。用過的結果：
- 根目錄共 33 項；`/nv/item_files/rfnv` 有 305 項（RF 校準資料在，非校準缺失）；
- `/nv/item_files/ims` 有 27 項 `qp_ims_*`、`IMS*DynamicConfig`（modem 端 IMS 設定存在）；
- `/nv/item_files/mcfg` 只有 digest 版本檔（載入的是通用 MBN，不是中華電信專用）。

### 10.4 與原廠對照機（SOV36，KDDI，A9）
fsg 取法：`adb -s <序號> exec-out su -c "dd if=/dev/block/sda34 bs=1048576"`，再用第 6 節的 tar 解析。

| 項目 | 701SO（我們） | SOV36 原廠 KDDI |
|---|---|---|
| `/Data_Profiles` | Profile2（IMS，**IPv6**）、Profile3 兩個 | Profile1～8，`Profile5` APN=`IMS` PDP type=**3（IPv4v6）**，另有 `xcap`、internet 等 |
| `carrier_policy.xml` | 通用「Enterprise Users」版 | KDDI 專用，註明「VoLTE is always assumed ON」 |

結論：我們機器的 EFS 是通用版，缺少運營商專用的 profile 與 policy，這就是 IMS profile 變成 IPv6 的由來。

## 11. 後續發現（2026-10-13 晚）

1. **D 變體 + `Profile2` 改 IPv4v6**：累計 10 次開機中 9 次正常（D 單獨 4 次中 1 次正常）。仍有約 10% 異常，所以不是完整修法。
2. 網路接受 IMS 承載（`APN=ims.mnc092.mcc466.gprs`，P-CSCF 位址齊全，附 ESM cause 50 表示只配 IPv4，屬規範內行為），但手機端以 ESM cause 31 拒絕。原因是：
   - IMS 的 `PDN_CONN_REQ` 在 21.03、22.71、25.31、27.36、29.50 連發五次，網路 29.85 才回；
   - F3 顯示每次請求後約 0.8 秒 `LTE_RLCUL_MAX_RETX_IND` → RLF → 連線重建（`CRE_STARTED_INDI`），手機已放棄該次程序，遲到的回覆被當成不認得而回 cause 31。
3. 基線（446、CS_ONLY）100 秒內也有 1 次 RLF（attach 完成後第一筆上行資料），之後恢復，所以網際網路連線正常；**IMS 模式下上行 RLF 反覆發生（100 秒內 5 次，共 25 次連線重建）**。尚不確定是這個站台的上行品質、這台機器的上行發射，還是 IMS 模式下網路端配置（如 UE 能力導致的排程設定）造成。
4. 台灣已無 3G，沒有 CS fallback 可用；`CS_ONLY` 的基線實際上無法撥打語音，所以 VoLTE 是必要條件。

## 12. 解碼 RRC 空口（找到真正原因）

### 12.1 工具
- `pycrate`（有完整 LTE RRC ASN.1）：裝在 scratchpad venv（`python3 -m venv venv_rrc; venv_rrc/bin/pip install pycrate`）。
- `diag_combo.py` 已改成同時記錄 `0xB0C0` RRC OTA；`rrc_decode.py <combo檔> [--full 起 迄]` 解碼。
- **0xB0C0 log 版本 15（rrc_rel 13）的標頭**：`ver(1) rrc_rel(1) rrc_ver(1) rb_id(1) pci(2) earfcn(4) sfn(2) pdu(1) sib_mask(4) len(2) msg`。
  **pdu 編號與一般文件不同**：1=BCCH_BCH、2=BCCH_DL_SCH、4=MCCH、5=PCCH、6=DL_CCCH、7=DL_DCCH、8=UL_CCCH、9=UL_DCCH（用暴力法逐一試解、以重編碼長度一致判定）。
- 解 UE 能力：`ueCapabilityInformation` 內 `ueCapabilityRAT-Container` 再用 `UE_EUTRA_Capability` 解。

### 12.2 結論一：B8+B3 載波聚合下上行失敗（701SO）
- 網路在 B8 主載波（3750）上加了 B3 輔載波（1400），PUCCH 用 format 3，並開測量間隙（gp0）量 B3/B8 鄰區。
- 這段期間手機的上行（IMS 的 PDN 請求、測量報告）一直送不出去，約每 8 秒 `LTE_RLCUL_MAX_RETX_IND` → RLF → 連線重建；所有 RLF 都落在 CA 期間。
- 驗證：policy 的 `ca_band_combos` 拿掉所有同時含 B8 與 B3 的組合後，MAX_RETX **歸零**，網路 70ms 內回覆 IMS 承載。
- 國際版配置對中華電信是允許 B8+B3 的，所以這很可能是 701SO（日版硬體/RF NV）特有的問題。

### 12.3 （已修正，見 13 節）原先推測：modem 跑的是 SoftBank 的 IMS 設定
- `/nv/item_files/ims/qp_ims_common_config`：`ims.mnc020.mcc440.3gppnetwork.org`；`IMSVoiceDynamicConfig`：`sip:mmtel@conf-factory.ims.mnc020.mcc440...`（mnc020/mcc440 = SoftBank）。
- IMS 堆疊照 SoftBank 走 IPv6，中華電信的 IMS APN 只給 IPv4（ESM cause 50）→ 手機以 cause 31 拒絕承載。把 Profile2 改成 IPv4 也一樣（IMS 仍要求 IPv4v6、仍拒絕），證明主導的是 IMS 設定本身。
- 由來：Sony 用 `sony-modem-switcher`（`vendor/bin`，原廠預編譯）依 MiscTA 的 active customization，把 `/vendor/etc/customization/modem/<名稱>_tar.mbn` 寫進 fsg 並用 `reset_modemst1/2` 重置 EFS。**LineageOS 有帶切換程式，卻沒帶任何 modem 配置檔**（`/vendor/etc/customization/modem/`、`/vendor/modemconf/` 都不存在），所以 modem 一直沿用原廠 SoftBank 留下的 EFS。
- 本機已有國際版配置 `~/FSG/AndroidTool/fsg/amss_fsg_poplar_ir51_ir92_ims_tar.mbn`（格式與 fsg 分區相同：`IMGEFS-SIGNED_IMAGE` MBN）：policy 有中華電信（466-92）專屬規則、不鎖 CS_ONLY；IMS profile 為 `Profile5 APN=ims、IPv4v6`；不含 SoftBank IMS NV。
- 701SO 的 fsg、modemst1、modemst2、fsc 已完整備份在 `.tmp/701so_modem_backup/`（md5 記錄於該目錄）。

## 13. 原廠做法查證與修正（2026-10-13 深夜）

### 13.1 對 12.3 的修正
- 12.3 說「LineageOS 沒帶 modem 配置檔，所以沿用 SoftBank 設定」**不成立**：701SO 現在的 fsg 分區 md5 與 `701SO_SoftBank JP_47.2.D.1.150-R12C` 原廠 `amss_fsg` 的 `fsg.000`（md5 `7dfa29f8…`）**完全相同**。5183 位元組的通用 policy 與 IPv6 的 `Profile2` 本來就是 701SO 原廠內容。
- EFS 裡 `ims.mnc020.mcc440` 的 IMS NV：modem 映像與所有原廠 fsg 都**不含** `3gppnetwork` 的 SoftBank 字串（只有 SOV36 的 fsg 有 1 處），SOV36 與 701SO 的檔案系統上也**沒有任何 `.mbn` 檔**。這些值應是 IMS 堆疊依 SIM 在當時寫入的殘留，**不一定是現在生效的設定**。所以「SoftBank IMS 設定是根因」這個說法**沒有證據**。
- `sony-modem-switcher` 只在多國版機型使用（`/vendor/etc/customization/modem/<名>_tar.mbn`）；KDDI（SOV36）與 701SO 這類單一運營商機型沒有該目錄，fsg 出廠即固定。

### 13.2 為什麼不能直接換國際版 `.mbn`（與你先前實測一致）
1. **簽章**：fsg 為 Sony 雙層簽章，改過內容必定無法使用（`NV_解析筆記.md` 實機：清 modemst 後 modem 完全起不來）。只能整份換**原廠已簽好的**映像。
2. **射頻 NV 不符**：`amss_fsg_poplar_ir51_ir92_ims_tar.mbn` 只含全球版 `L1234578…` 的 `nvpreload`、`default_band` 也是全球版；701SO 需要 `L12348_11…`（RF card 192）。modem 以 TA 的 `0x09FB` 組態名找同名 nvpreload，找不到才用 `default_band`，會落到全球版射頻 NV。
3. **TA 元件缺少**：`TA_解析筆記.md`：日系機缺少全球版設定需要的 TA 元件。
- 唯一帶有 701SO 所需 `L12348_11` NV 且含中華電信（`cht_plmns`）規則的原廠簽章映像是 **G8341 Vodafone UK（`fsg.000` md5 `72dc9124…`，5 份 nvpreload、policy 69216 B）**；但它沒有 IMS 的 Data profile，且仍受 1、3 的限制，風險高，未嘗試。

### 13.3 各機型原廠 fsg 比較（`.tmp/stock_fsg/`）
| 機型 | default_band | nv 變體 | policy | IMS profile |
|---|---|---|---|---|
| 701SO SoftBank | `L12348_11…` | 1 | 5183 B 通用 | Profile2 `IMS` IPv6（精簡） |
| SO-01K docomo | `L13457_12…` | 1 | 8174 B | Profile3 `ims` IPv4v6 class3 |
| SOV36 KDDI | `L13457_11…` | 1 | 6826 B KDDI | Profile5 `IMS` IPv4v6 class5 |
| G8342/G8441 TW | `L1234578…` | 2 | 約 64–69 KB，含 CHT | 無 profile |
| G8341 UK | `L13457_12…` | 5（含 701SO 與 SoftBank 的） | 69216 B，含 CHT | 無 profile |

### 13.4 試驗：把 Profile2 換成完整的原廠 IMS profile
- 701SO 的 `Profile2` 缺少 `0x25`（APN class）、`0x12/0x13/0x1e/0x20/0x26–0x28/0x2d/0x36` 等屬性，其他原廠 IMS profile 都有。
- 以國際版 `Profile5`（`ims`、IPv4v6、class 5）為模板、改 id 為 2 寫入後：IMS 承載**仍被手機端以 cause 31 當場拒絕**（網路 240 ms 後回覆，手機 1 ms 內拒絕）。→ **不是 profile 屬性造成**。
- 此時 RLF 已不再發生（policy 已移除 B8+B3 組合），所以 cause 31 與上行失敗是**兩個獨立問題**。
- F3 可見：`qcril_qmi_nas_handle_ims_pdp_status_change: isPdpConnected = false`；DS 判定拒絕的條件在雜湊壓縮訊息裡，明文看不到。

### 13.5 下一步（需要對照基準）
要知道「手機端為何拒絕」，需要一台**VoLTE 正常運作**的原廠機，用同一套工具抓同樣的時間軸做差異比對：
- 原廠 SOV36 + 可 VoLTE 的 KDDI/au SIM，或原廠 701SO + SoftBank SIM；
- 或取得 QSR4 字典以讀雜湊訊息。
