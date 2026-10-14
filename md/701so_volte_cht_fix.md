# 701SO 在中華電信（46692）啟用 VoLTE：做了什麼、缺什麼

結果：701SO（原廠 Android 9，Magisk root）插能通話的 CHT SIM，狀態列出現 VoLTE 圖示，SIP 註冊 200 OK，實測通話成功（2026-10-14）。

## 1. 問題

- 701SO 是日本 SoftBank 版 modem 設定（fsg 內是 SoftBank 的 EFS 金本），台灣版 G8342 的 fsg 內有中華電信（`cht_tw_ims`）整組設定。
- 改 policy、Profile、IM_CN 都沒用：IMS 承載（APN `ims`）網路接受後，立刻被 UE 以 ESM cause 31 拒絕。
- 另有獨立問題：原廠 RIL 的 `No MSISDN SIM` 規則在開機時把網路類型改成 0（無 LTE），造成開機後偶爾完全不搜網。與 VoLTE 本身無關。

## 2. 怎麼找到原因

1. G8342（原廠台灣版，已用 Fox + Magisk 取得 root）的 `CustomizationSelector` 會依 SIM 從 `/system/etc/customization/modem/` 挑一份營運商 mbn（本例 `amss_fsg_poplar_dsds_cht_tw_ims_tar.mbn`）整份寫進 fsg 分區。
2. 解開 mbn 的 tar，與 701SO 自己的出廠 fsg 比對**檔案清單與內容**。
3. G8342 的 diag 被鎖（所有指令回 BAD_CMD）、modemst 是加密的，所以無法直接讀它的即時 EFS，只能靠 mbn 內容。
4. 用同一張 SIM 在兩機串流完整 logcat：Android 側的 IMS 流程（`turnOnIms`、`enableIms`、`REQUEST_IMS_REG_STATE_CHANGE`）兩邊一致，差異在 modem 內部。
5. 用 diag 抓 modem F3 日誌（開機後第一次附著，IMS 承載請求只在這時出現；飛航模式重附著不會重發）。看到 `ds_mppm_cmd_hdlr: Invalid apn_string ims requesting pref_sys change`，之後 IMS 就停住。
6. mbn 裡有 `data/andsf.xml`，內含 `<APN>ims</APN>` 的路由規則；701SO 完全沒有 ANDSF/IWLAN 這組檔案。補上之後 MPPM 認得 `ims`，modem 要求 Android 建立 IMS 承載，IMS 註冊成功。

## 3. 寫入 701SO 的項目（全部用 diag EFS 寫入，可還原）

來源皆為 G8342 的 cht mbn（解開於 `.tmp/g8342/x_cht`）。

| 類別 | EFS 路徑 | 備註 |
|---|---|---|
| ANDSF/IWLAN（**關鍵**） | `/data/andsf.xml`、`/data/default_andsf.xml`、`/data/ds_andsf_config.txt`、`/data/iwlan_s2b_config.txt`，各自加 `_Subscription01` 版 | subs_id=1 用的是 Subscription01 版 |
| 附著 | `/data/ds_dsd_attach_profile.txt_Subscription01`（內容 `Attach_Profile_ID:1;` + `Attach_Profile_ID:8;`） | 主檔原本已有 |
| 資料 Profile | `/Data_Profiles/Profile1`（internet）、`Profile5`（ims，IPv4v6，IM_CN=0）、`Profile8`（空 APN 附著） | 刪除自製的 `Profile2`；`Profile3` 保留 |
| NAS/RRC | `/nv/item_files/modem/nas/nas_ims_setting_mode`（01）、`nas_operator_plmn_list`（466-92）、`/nv/item_files/modem/lte/rrc/cap/rrc_capability_capable_plmn_list`（原三筆日本 PLMN + 466-92） | |
| IMS 堆疊設定 | `/nv/item_files/ims/` 下 9 檔：`ims_operation_mode`(03)、`qp_ims_reg_config_db`、`qp_ims_common_config`、`qp_ims_ut_config_item`、`IMSEmerDynamicConfig`、`ims_user_agent`、`qp_ims_xcap_common_config`、`qp_ims_service_enablement_config`、`ims_sip_config` | CNV 預載 unit 編號對應：4703/5991/8299/8316/8308/4153/8315/8297/8298 |
| IMS 參數 | `/efsprofiles/overideconfig`、`/data/3gpp/throttling/srv_req_throt_config.txt`（`FAILURE_TIMER_5:20`） | |
| policy | `/policyman/carrier_policy.xml`：`svc_mode FULL`、`operator_mcc_list` 含 466、不含 B8+B3 組合 | 這是自己改的版本，非 cht 原檔 |

另外 Android 端：APN 表加入 CHT internet / ims / mms 三筆（ims 類型為 `ims`）、`persist.dbg.volte_avail_ovr=1`（讓設定出現「啟用 VoLTE」開關）、網路類型 4G only。

## 4. 還沒確認 / 限制

- 以上項目沒有逐一二分，**哪些是最小必要集合還不知道**；最可疑的是 ANDSF 組，其餘可能不必要。
- EFS 是 modem 裡的資料；重刷 fsg、清 modemst、或 CustomizationSelector 重新套用都可能讓它消失。
- 沒寫入的 NV 預載項：4779/4780/6831/7000/7017/7018/7020/8009/8181/4265（cht 有、701SO 出廠沒有，用途不明）。實測 VoLTE 已成功，暫不需要。
- G8342 的 mbn 不能整份刷進 701SO：日系機缺全球版需要的 RFFE 元件（見 `TA_解析筆記.md`）。

## 5. 備份與還原

- 補丁前的 701SO 即時 EFS：`.tmp/backup_701_before_mirror/`、`.tmp/ims_live701/`。
- 原廠 fsg/modemst：`.tmp/701so_modem_backup/`。
- 工具：`.tmp/diag_efs_batch.py`（寫入並讀回驗證、支援 mkdir/unlink）、`.tmp/diag_efs_read.py`、`.tmp/boot_cap_persist.sh`（開機第一次附著擷取）。
- **EFS 寫入後必須等 65 秒以上再重開機**，否則 modem 快取會丟掉。

## 6. 最小必要集合（二分法實測，2026-10-14）

方法：每輪只改一組項目 → 診斷寫入並讀回驗證 → 等 65 秒 → 重開機（確認運轉時間歸零）→ 開機完成後點「設定→行動網路→進階」觸發註冊 → 註冊後觀察 120 秒；以「Android 發出 IMS requestNetwork + `MmTelFeatureConnection: onRegistered` + IMS 承載 rmnet_data2」判定 VoLTE。

| 測試 | 狀態 | 結果 |
|---|---|---|
| A2 | 只留 ANDSF 組 | ✗ |
| B | ANDSF + Profile 組 | ✗ |
| C | ANDSF + Profile + IMS 9 檔 | ✓ |
| D | ANDSF + IMS 9 檔 | ✓（Profile 組、NAS/RRC 名單、overideconfig、throttling 都不必要） |
| E | ANDSF 只留 andsf.xml(+S) + IMS 9 | ✗ |
| F | + default_andsf.xml | ✗ |
| G | + ds_andsf_config.txt | ✓ |
| H | 只留 Subscription01 版 | ✗ |
| I | 主檔版 + Subscription01 版（不含 default） | ✓（default_andsf.xml、iwlan_s2b_config.txt、attach 副檔不必要） |
| J | IMS 只留 4 檔 | ✓ |
| K | IMS 只留 ims_operation_mode + qp_ims_reg_config_db | ✓ |
| L | ims_operation_mode 改回 02 | ✗（IMS 承載有、但註冊不成功） |
| M | qp_ims_reg_config_db 還原 | ✗（IMS 不再要承載） |
| N | ANDSF 只留主檔版 | ✗ |
| O | 只留 ds_andsf_config.txt | ✗ |
| FINAL | 下表 6 檔 | ✓ |

**最小集合（6 檔，檔案在 `md/701so_volte_min_files/`，套用腳本 `apply.sh`）**

| EFS 路徑 | 作用 |
|---|---|
| `/data/andsf.xml`、`/data/andsf.xml_Subscription01` | 內含 `<APN>ims</APN>` 規則，MPPM 才認得 `ims` 是合法 PDN（缺它 → `Invalid apn_string ims` → IMS 承載 cause 31） |
| `/data/ds_andsf_config.txt`、`/data/ds_andsf_config.txt_Subscription01` | `andsf_rule_mgr_active:1;`，啟用 ANDSF 規則管理器 |
| `/nv/item_files/ims/qp_ims_reg_config_db` | cht 版 IMS 註冊設定（APN `ims`），讓 IMS 堆疊去要承載 |
| `/nv/item_files/ims/ims_operation_mode`（內容 `03`） | 承載建立後 IMS 能註冊成功（02 會卡在註冊） |

必須「主檔版 + Subscription01 版」同時存在（只留任一種都失敗）。其餘已驗證不必要：Profile1/5/8、nas_ims_setting_mode、nas_operator_plmn_list、rrc plmn list、overideconfig、throttling、default_andsf.xml、iwlan_s2b_config.txt、attach 副檔、其他 7 個 IMS 檔。

注意：`apply.sh` 的各步驟（寫入、落盤、重開機）都已分開實測過，但整支腳本尚未一次跑完整流程。開機後偶爾不搜網是另一個問題（`No MSISDN SIM` 規則），點開「進階」即可觸發。

## 7. 附記：G8342（LineageOS A15）同樣驗證（2026-10-14）

- 把 cht mbn 寫進 fsg 後，必須用 newflasher 刷 `amss_fs_1/2`（1024 位元組零）重設 modemst，EFS 才會載入 cht 設定（`/data/andsf.xml` 變成與 cht mbn 相同、含 `<APN>ims`）。
- 之後 IMS 承載仍不出現，原因在 Android 端：使用者的「VoLTE」開關關閉（`ImsManager enabled=false`）。打開後 IMS 承載（rmnet_data2）建立、IMS 註冊成功（tech=LTE）。
- 這也提醒 701SO 這類機器：二分法判定前要先確認 VoLTE 開關是開的。
- 尚未實測通話；`ims_operation_mode` 02 與 03 在 G8342 上哪個必要未分辨。
