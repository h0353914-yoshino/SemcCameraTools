# 701SO 中華電信 VoLTE 成功時的確定狀態（2026-10-17）

適用：701SO（BH904YZF9A），原廠 Sony Android 9（`47.2.D.1.150`，`user/release-keys`），中華電信 SIM（46692）。

## 1. 結果（已確認）

- 使用者確認 VoLTE 可用。
- `dumpsys telephony.registry`：`APN type: ims, APN: ims`，`Data Connection state: 2`（已連線），`Network type: 13`（LTE），介面 `rmnet_data2`，位址 `19.74.225.188/29`。這是 IMS 專用承載建立成功的證據。
- 網路：`gsm.operator.numeric=46692`、`gsm.network.type=LTE`，`mServiceState` 為 HOME。

## 2. 目前的 EFS（modem 端）

以 diag 讀回驗證。寫入與讀回通過，**重開機後只重讀了 policy 以外的部分**，下表標註來源。

| EFS 路徑 | 內容 / 來源 | 狀態 |
|---|---|---|
| `/policyman/carrier_policy.xml` | `.tmp/carrier_policy_final701.xml`（svc_mode FULL、`operator_mcc_list` 含 466、無 B8+B3 CA） | 寫入後讀回一致（4725 bytes） |
| `/data/andsf.xml`、`/data/andsf.xml_Subscription01` | `md/701so_volte_min_files/` | 讀回一致（2019 bytes） |
| `/data/ds_andsf_config.txt`、`…_Subscription01` | `md/701so_volte_min_files/` | 主檔讀回一致（`andsf_rule_mgr_active:1;`） |
| `/nv/item_files/ims/ims_operation_mode` | `03` | 讀回一致 |
| `/nv/item_files/ims/qp_ims_reg_config_db` | 最小集版（cht 版，1024 bytes） | 讀回一致 |
| `/Data_Profiles/Profile5` | G8342 cht（`g8342/x_cht/Data_Profiles/`），APN `ims`，IPv4v6 | 寫入讀回通過 |
| `/Data_Profiles/Profile8` | 同上，空 APN 附著 | 寫入讀回通過 |
| `/data/ds_dsd_attach_profile.txt_Subscription01` | `Attach_Profile_ID:1;` + `Attach_Profile_ID:8;` | 寫入讀回通過 |
| `/nv/item_files/modem/nas/nas_ims_setting_mode` | `01` | 寫入讀回通過 |
| `/nv/item_files/modem/nas/nas_operator_plmn_list` | 466-92 | 寫入讀回通過 |

寫入前的備份：`.tmp/backup_before_466_min/`（7 個檔，寫入前的狀態）。寫入前唯讀讀到的其他值：`/nv/item_files/modem/mmode/ue_usage_setting`=`00`、`voice_domain_pref`=`03`。

## 3. Android 端

- APN 表（`content://telephony/carriers`）：
  - CHT Internet（`_id=29`，apn `internet`，default,supl，IPV4V6，**偏好 APN**）
  - CHT MMS（`_id=30`，apn `emome`，mms，IPV4V6）
  - CHT IMS（`_id=31`，apn `ims`，ims，IPV4V6）
  - 之前加的 FET Internet（27）、FET IMS（28）仍在，對 46692 沒有影響。
- `persist.dbg.volte_avail_ovr`=`1`。**這個屬性在一次重開機後變成空值**，我用 root 設回 1。原因未查明。

## 4. fsg（sda34）

- 前 1 MB 與 2026-10-13 的 `.tmp/701so_modem_backup/fsg.img` sha256 一致（`f5ef4636…`）。
- 所以 modem 底座是原廠 r12c 基線，沒有換成 G8342 的 fsg。

## 5. 還沒確認的事

- **五個新加的 EFS 檔（Profile5/8、attach 副檔、nas_ims_setting_mode、nas_operator_plmn_list）是否必要，沒有做二分。** 它們是在 IMS 承載不通時加回去的，這次跟最小集一起存在時 VoLTE 起來了，但單獨加入的效果沒有比對。
- **policy final701 在遠傳 SIM 上是否穩定，沒有實測**（這次實測的 SIM 是中華電信）。
- 擷取時 diag 的 NAS/ESM 訊息沒有出現在輸出裡（只有 F3/L1 訊息），無法從 modem 日誌解出 IMS PDN 請求與 ESM cause。
- modem restart 次數：開機後為 0，但沒有跨多次開機的長期觀察。

## 6. 操作注意

- 最小集文件是 6 檔，不是 4 檔。這次寫入的是 6 檔加 policy。
- 開機後要點一次「設定 → 行動網路 → 進階」，才會觸發 IMS 註冊與承載建立。

## 7. 相關

- 成功配方與二分表：[701so_volte_cht_fix.md](701so_volte_cht_fix.md)
- 最小集檔案與套用腳本：[701so_volte_min_files/](701so_volte_min_files/)
- 中華電信 APN 腳本：`.tmp/add_apn.sh`
