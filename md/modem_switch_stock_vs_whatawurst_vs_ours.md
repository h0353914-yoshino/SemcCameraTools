# modem 切換：原廠 vs whatawurst（OpenCS）vs 我們的 tree 比對

比對日期：2026-10-16。來源：
- 原廠：`G8342_Customized TW_47.2.A.11.228-R3C` 的 system / oem 映像（`debugfs rdump`），CustomizationSelector 以 jadx 反編譯（`.tmp/stock_cs/jadx_out`），oem 抽出在 `.tmp/stock_oem`。
- whatawurst：`.tmp/whatawurst_full/yoshino-common`（lineage-21）與三個裝置樹（`.tmp/whatawurst_clone`）。
- 我們：`~/lineageos/device/sony/yoshino-common` 與 G8342（BH90018Q63）上的實機。

## 結論（一句話）
**app 層與資料層，原廠與 OpenCS 對台灣電信是等價的；真正的差異在「檔案放哪裡」和「sepolicy」：我們的 tree 把 switcher 改寫到 `/vendor`，但沒有把 mbn、reset_modemst、modem.conf 放進對應位置，也沒有 `/cache/modem` 專用標籤，所以 switcher 在我們的 build 上根本跑不起來。**

## 1. app 層（原廠 CustomizationSelector vs OpenCS）— 切換行為相同
逐檔比對（`Configurator`、`ModemConfiguration`、`ModemSwitcher`、`CustomizationSelectorService/Activity`、`CommonUtil.getCarrierBundle`）：
- TA 單元與格式完全一樣：**2405 = `F0 7A 01` + mbn 檔名**；**2212 = config_id**。
- 流程一樣：Service 只評估（`isNewConfigurationNeeded`）→ 跳對話框 → 按重開機時 Activity 才呼叫 `Configurator.set()` 寫 TA → `PowerManager.reboot`。
- 目標與目前相同就不寫（`setModemConfiguration` 比對 `getCurrentModemConfig`）。
- 失敗保護一樣：狀態檔不成功且已嘗試過同一組態就不再試。

OpenCS 多出來的（原廠沒有）：
| 項目 | 說明 |
|---|---|
| `cs_ims` 開關 + `ImsSwitcher` | 關閉時把 modem 切回該機種預設 mbn（依 `ro.build.flavor`） |
| `reApplyModem` / `revertReApplyModem` | 重寫 2405，並把 2404 設成 `temporary_modem`（再還原） |
| `NetworkSwitcher`（`NS/*`） | SIM 載入後 LTE→3G→LTE 重新註冊 |
| 通知、`event_subID` 暫存 | 啟動時顯示狀態 |
| config key 多含 `ro.semc.version.opencs` | 升級 app 版本會觸發重新評估 |

原廠 `EventReceiver` 另外要求 `isMandatorySimParmsAvailable(subId)`；OpenCS 改成先存 subID 再判斷。

## 2. 資料層（SIM → config_id → modem）— 台灣相同
- `modem.conf`：`92 fareastone_tw_ims`、`93 cht_tw_ims`、`94 twm_tw_ims`、`426 tstar_tw_ims`、`567 asiapacific_tw_ims`，兩邊逐字相同。
- `configuration_selectors`：原廠 G8342 TW 只有 5 個 config（`S278.1→92`、`S277.1→93`、`S280.1→94`、`S283.1→426`、`S8779.1/.6→567`），**沒有 anysim 備援**。whatawurst `poplar_dsds` 這 5 條相同，另外多 33 個非台灣 config，同樣沒有 anysim。
- `service_providers`：台灣 466-92/01/97/89/05 相同；whatawurst 多 `S277.2`（466-11）、`S278.2`（466-02）兩條，沒有對應 config，不影響。
- 原廠資料放在 oem 的 RRO（`com.sonymobile.customizationselector-res-305.apk`）與 `/oem/modem-config/<id>/modem.conf`；app 本身內建的表是空的。

## 3. binary 層（sony-modem-switcher）— 路徑被改寫
| 用途 | 原廠 / whatawurst（未修改） | 我們 tree（`extract-files.py` 的 blob_fixup） |
|---|---|---|
| 安裝位置 | `/system/bin/sony-modem-switcher` | `/vendor/bin/sony-modem-switcher` |
| mbn 目錄 | `/system/etc/customization/modem/` | `/vendor/etc/customization/modem/` |
| reset_modemst1/2、default | `/system/etc/customization/modem/` | `/vendor/etc/customization/modem/` |
| modem.conf | `/oem/modem-config/…` | `/vendor/modemconf/…` |
| 狀態/報告/loglevel | `/cache/modem/…` | `/data/vendor/…` |

binary 其他部分逐位元組相同（96 個 byte 差異都在這些字串）。

**後果**：app（原廠或 OpenCS）寫死讀 `/system/etc/customization/modem/`、`/oem/modem-config`、`/cache/modem/modem_switcher_status`。tree 的 binary 改成 `/vendor`、`/data/vendor`。如果之後裝 OpenCS，app 與 binary 會看不到對方的檔案：app 讀不到狀態檔 → `getCurrentModemConfig` 丟 IOException → 評估回傳空字串 → 永遠不會切。必須連 app 的常數一起改，或不要改 binary 路徑。

## 4. init（啟動時機）— 相同
兩邊都是 `on post-fs` 裡 `start modem_switcher`（`class main`、`user root`、`group root system oem_2993 cache`、`disabled`、`oneshot`），開機時序一樣。whatawurst 另外 `restorecon` fsc/fsg/modemst1/2/TA（我們也有）。

## 5. sepolicy — 我們缺 `/cache/modem` 專用標籤
whatawurst：
- 新增 `type modemsw_cache_file, file_type;`，`file_contexts` 把 `/cache/modem(/.*)?` 標成它。
- `type_transition modem_switcher cache_file:dir modemsw_cache_file "modem"`，以及 `modem_switcher_report`、`modem_switcher_status` 檔案的 type_transition。
- `modem_switcher` 對 `modemsw_cache_file` 完整讀寫；`radio`（android.phone，CustomizationSelector 跑在這個 domain）也可讀寫它，所以 app 讀得到狀態檔。
- `r_dir_file(modem_switcher, system_file)` 讀 `/system/etc/customization`；`oemfs` 讀 `modem.conf`。
- `block_device:dir r_dir_perms`、`modem_efs_partition_device:blk_file rw_file_perms`、`capability chown`。

我們：`modem-switcher.te` 只有 `block_device:dir search` 與 `modem_efs_partition_device:blk_file {open read write getattr ioctl}`。原本想加的 `cache_file` 規則違反 AOSP neverallow（編譯失敗，已移除）。因為 binary 的狀態檔路徑改到 `/data/vendor/`，目前也沒有 `vendor_data_file` 之外的規則寫狀態檔（`allow modem-switcher vendor_data_file:file create_file_perms` 已存在，所以狀態檔能寫）。若要保持原廠路徑，必須採用 whatawurst 的 `modemsw_cache_file` + type_transition 做法。

## 6. 我們實機的現況
- `/vendor/etc/customization`、`/vendor/modemconf`、`/system/etc/customization` **全部不存在**。switcher 跑出：`Could not find modem filesystem: /vendor/etc/customization/modem/`（00:02、00:05 實測；2405=cht 與 2405=00 都一樣）。
- 20:39 那次 switcher 能成功，是因為當時 vendor 分區裡有 `/vendor/etc/customization/modem`。tree 與 git 歷史都沒有這些檔案（`vendor/sony/yoshino-common` 沒有追蹤任何 customization），裝置上 `/data/local/tmp/cust/`（2026-10-15 05:08，內含 `amss_fs_empty.mbn`、`..._cht_tw_ims_tar.mbn`、`..._tar.mbn`）是手動放過去的備份 → 推論：那些檔案是之前手動放進 vendor，之後刷 Oct 15 的 build 就整個被取代掉了。
- 其他 mbn（39 組）只存在 `.tmp/g8342/orig_mbn`、`.tmp/g8342/mbn_all`。

## 7. 要在 tree 內讓原廠切換方式可用，需要補的東西
1. 決定路徑方案（二選一）：
   - **A. 還原成原廠路徑**：不要改 binary 的 `/system`、`/oem`、`/cache` 字串（或只改安裝位置），把 mbn、`reset_modemst1/2`、`default`、`modem.conf` 放到 `/system/etc/customization/modem` 與 `/oem/modem-config`，補 `modemsw_cache_file` 的 sepolicy。這與 whatawurst 一致，OpenCS 可以直接用。
   - **B. 維持 `/vendor` 路徑**：把檔案放到 `/vendor/etc/customization/modem`、`/vendor/modemconf`，狀態檔在 `/data/vendor/`，並且**同步改 OpenCS 的常數**（`MODEM_FS_PATH`、`MODEM_STATUS_FILE`、`ModemConfParser` 路徑），並給 `radio` domain 讀 `/data/vendor/modem_switcher_status` 的權限。
2. mbn 來源：從原廠 system 映像的 `/etc/customization/modem/` 抽出（`proprietary-files.txt` 目前沒有列），台灣只需要 `amss_fs_empty.mbn`、`amss_fsg_poplar_dsds_tar.mbn` 與 cht/fareastone/twm/tstar/asiapacific 的 `_ims_tar.mbn`，加上 `reset_modemst1/2`、`default` 符號連結（whatawurst 的 `hardware/modem/Android.mk` 做法）。
3. modem.conf：`92/93/94/426/567` 五個目錄（內容見上）。
4. 設定資料：`configuration_selectors`（5 條台灣）與 `service_providers`（台灣 5 條）。
5. 修改 sepolicy 後務必先 `m precompiled_sepolicy` 驗證 neverallow（我們之前的 `cache_file` 規則就是在這步被擋）。

## 8. 與「斷網」事件的關係
這份比對的差異（路徑、缺檔、sepolicy）**不能解釋 20:43→21:58 的斷網**：斷網期間 switcher 都沒有動作（2405=00 或找不到目錄），斷網是 modemst 內容的問題（見記憶 `project_g8342_modem_mcfg_missing_no_service`）。但這解釋了為什麼之後手動跑 switcher 一直是「Could not find modem filesystem」。

## 9. 尚未驗證
- 沒有在實機上跑過 OpenCS / 原廠 CustomizationSelector。
- 原廠 `sony-modem-switcher` 的寫檔長度與 active customization 分支只看了字串，沒有反組譯。
- 「那些 mbn 是手動放進 vendor」是推論，沒有當時的指令紀錄可證。
