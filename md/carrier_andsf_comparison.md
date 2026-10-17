# 各電信 mbn 的 ANDSF 組與 701SO 最小組合（cht）比對

來源：G8342 原廠 system 映像 `/etc/customization/modem/` 內 39 組 `amss_fsg_poplar_dsds_*_tar.mbn`（`default` 即 `..._tar.mbn`，歸為 `tar`），解包工具 `.tmp/mbn_extract.py`，解包結果在 `.tmp/g8342/mbn_all/`。

我們的最小組合（701SO 驗證過）的 andsf 部分**就是 cht 的 andsf**（逐位元組相同，`data/andsf.xml` 與 `_Subscription01` 都一樣）。所以下表以 cht 為基準。

## 比對欄位

- **andsf**：mbn 內有沒有 `data/andsf.xml`。
- **APN=ims**：andsf 裡有沒有完全相同的 `<APN>ims</APN>`。這是 MPPM 認得 IMS PDN 的條件（701SO 上缺它會出現 `Invalid apn_string ims` 與 cause 31）。
- **ims 順序**：ims 規則裡 LTE（AccessTechnology 1）與 WLAN（3）的 AccessNetworkPriority。數字越小越優先。
- **行差異**：andsf.xml 與 cht 版相比，不同的行數（`diff` 的變更行）。
- **ds_andsf**：`ds_andsf_config.txt` 是否與 cht 相同。

## 結果

| 電信（mbn） | andsf | APN=ims | ims 順序 | 行差異 | ds_andsf |
|---|---|---|---|---|---|
| **cht_tw（我們用的）** | 有 | Y | **LTE 優先** | 0 | 同 |
| fareastone_tw（遠傳） | 有 | Y | WLAN 優先 | 22 | 同 |
| asiapacific_tw（亞太） | 有 | Y | WLAN 優先 | 24 | 不同 |
| tstar_tw（台灣之星） | 無 | | | | |
| twm_tw（台灣大） | 無 | | | | |
| airtel_in | 有 | Y | WLAN 優先 | 24 | 同 |
| ais_th | 有 | Y | WLAN 優先 | 36 | 同 |
| china_mobile_hk | 有 | Y | WLAN 優先 | 38 | 同 |
| china_mobile_cn | 無 | | | | |
| csl_hk | 有 | Y | WLAN 優先 | 24 | 同 |
| ctm_mo | 無 | | | | |
| dtac_th | 有 | Y | WLAN 優先 | 24 | 同 |
| du | 有 | Y | WLAN 優先 | 30 | 不同 |
| etisalat_ae | 有 | Y | LTE 優先 | 10 | 不同 |
| gteb | 有 | Y | WLAN 優先 | 27 | 同 |
| hutch_hk | 有 | **N** | — | 26 | 同 |
| ir51_ir92_gte | 有 | Y | LTE 優先 | 19 | 不同 |
| ir51_ir92 | 有 | Y | LTE 優先 | 8 | 不同 |
| m1_sg | 有 | Y | WLAN 優先 | 38 | 同 |
| megafon_ru | 有 | Y | LTE 優先 | 18 | 同 |
| mts_ru | 有 | Y | WLAN 優先 | 24 | 同 |
| orange_poland | 無 | | | | |
| pccw_hk | 有 | Y | WLAN 優先 | 24 | 同 |
| reliance_com_in | 無 | | | | |
| reliance_jio_in | 有 | Y | WLAN 優先 | 24 | 同 |
| singtel_sg | 有 | Y | WLAN 優先 | 38 | 同 |
| smartone_hk | 有 | Y | WLAN 優先 | 34 | 同 |
| starhub_sg | 有 | Y | WLAN 優先 | 38 | 同 |
| stc_sa | 有 | Y | LTE 優先 | 26 | 不同 |
| telkom_za | 有 | **N**（大寫 `IMS`，另有 `Ut`） | — | 50 | 不同 |
| tmobile_us（ims 版） | 有 | Y | WLAN 優先 | 32 | 不同 |
| tmobile_us（一般版） | 無 | | | | |
| truemove_th | 有 | Y | WLAN 優先 | 22 | 同 |
| tele2_ru | 無 | | | | |
| verizon_us | 無 | | | | |
| vodafone_in | 無 | | | | |
| att_us | 無 | | | | |
| beeline | 無 | | | | |
| tar（default） | 無 | | | | |

## 摘要

- **39 組中 24 組有 ims 規則且 APN 為小寫 `ims`**，其中只有 **6 組（含 cht）是 LTE 優先**，其餘 **18 組是 WLAN 優先**。
- **13 組完全沒有 andsf 檔**，其中包括台灣的台灣之星（tstar）與台灣大（twm）。這些電信的 VoLTE 不是靠這組檔案，我們的做法不能直接套用。
- **hutch_hk、telkom_za 沒有小寫 `ims` APN**。若把我們的組合用在這兩家，預期會遇到同樣的 `Invalid apn_string` 問題，但這是推論，沒有實測。
- **andsf 內容差異大**：APN 清單不同，ims 規則的優先順序也不同。行差異從 8 到 50 行，最小的是 ir51_ir92（8 行），最大的是 telkom_za（50 行）。
- 台灣相關：遠傳（fareastone）與亞太（asiapacific）的 ims 都是 WLAN 優先，只有中華（cht）是 LTE 優先。

## 限制

- 只比對了 andsf 與 ds_andsf。`qp_ims_reg_config_db` 與 `ims_operation_mode` 在 mbn 裡是 CNV 預載格式，不是明文，也不是 1024 bytes 的連續區塊，所以**無法逐電信比對**。各電信的 `ims_operation_mode` 值也不知道。
- mbn 還包含其他 NV 與 EFS 檔案（56–80 個），這次沒有全部比對。
- 最小組合是用 cht 二分測出來的。套用到其他電信的 andsf 沒有實測過。
- 遠傳的 ims 是 WLAN 優先，這跟 `G8342` 上「連 Wi-Fi 時 VoLTE 走 VoWiFi」的既有記錄一致（見 `project_g8342_a15_volte_fsg_modemst`）。
