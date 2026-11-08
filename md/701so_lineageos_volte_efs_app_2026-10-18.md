# 701SO（LineageOS 15）用 CustomizationSelector 的 EFS 模式啟用中華電信 VoLTE（2026-10-18）

適用：701SO（BH904YZF9A），`lineage_poplar-userdebug 15`（test-keys），中華電信 SIM（46692），fsg 為原廠 `amss_fsg_poplar_701so_softbank_r21b_tar.mbn`。

## 1. 結論

- **VoLTE 可以起來**：用 app 的不相容（EFS）模式，選中華電信寫入 12 個 EFS 檔，**重開機到 modem 不再當機（通常第 2 次、有一輪第 3 次）**後 IMS 自己註冊（`isImsRegistered = true`、`show HD Icon: true`），狀態列出現 VoLTE 話筒圖示。
- 從乾淨原廠狀態也能重現（見第 5 節），不是殘留狀態造成。
- **每次改 fsg 或改 EFS「內容」之後，第一次開機 modem 會進入當機循環、不會註冊**；需要重開機才會恢復，**次數不固定**（實測 2 次居多，有一輪要 3 次）。判斷標準是 modem 重啟次數為 0，不是固定開兩次；細節見第 9 節。
- Android 端的 `ims` APN **不是必要條件**：刪掉後重開機，IMS 仍然註冊成功。IMS 承載是由 modem 端的 `Profile5`（APN `ims`）加 ANDSF 規則決定的。
- 還沒做：實際撥打/接聽電話。

## 2. 為什麼之前不能用（時間序）

1. 這台 LineageOS 701SO 原本 fsg 是國際版 `amss_fsg_poplar_tar.mbn`，EFS 的 policy 沒有 `operator_mcc_list`，app 的 policy 改寫步驟找不到東西而失敗（`policy 的 operator_mcc_list 出現 0 次`）。
2. 切到 `701so_softbank_r21b` 之後再寫 EFS，**檔案被洗掉**：切 fsg 時 `vendor.modem_switcher` 在開機重寫 fsg 並重設 modemst，EFS 會從 fsg 重建。順序必須是「先切 fsg、重開機直到 modem 穩定（重啟次數 0），再寫 EFS，再重開機直到穩定」。
3. EFS 還原成原廠 policy 時，附著請求的語音域偏好是 **CS only**（`5D 01 00`），NAS 回報 `voice_support_on_lte = 0`、IMS 應用回報 `lte_ims_voice_avail (VOPS) is NOT available`，所以 IMS 一直未註冊，從不要求 IMS 承載。
4. 寫入 12 檔後，modem 的狀態變化（用 diag 日誌與 NAS 封包確認）：
   - MPPM 認得 `ims` APN（ANDSF 規則生效，`create_active_tech_plist for apn: ims`）。
   - 語音域偏好設為 3（IMS 優先）成功（`result = 0`，之前是 `res 40`）；NV `voice_domain_pref` 也因此變成 `03`，不需要另外寫。
   - 附著請求：`5D 01 03`（IMS PS 優先）；附著接受：EPS 網路功能 `0x83`（IMS VoPS = 1）。
   - UE 對網路要求 `ims` 承載，網路回 `Activate default EPS bearer context request`（EBI 6）。
   - NAS 回報 `lte_ims_voice_avail(VOPS) is available : 1`，IMS 註冊成功。

## 3. 寫入的 12 個 EFS 檔

| EFS 路徑 | 來源 |
|---|---|
| `/policyman/carrier_policy.xml` | 日本型號的原廠預設 mbn（701SO 為 `701so_softbank_r12c`）的 policy，把 `operator_mcc_list` 換成 SIM 的 MCC（466），`svc_mode LIMITED` 改成 `FULL`，5172 bytes |
| `/data/andsf.xml`、`andsf.xml_Subscription01` | 選中的 mbn（cht）tar 內 |
| `/data/ds_andsf_config.txt`、`ds_andsf_config.txt_Subscription01` | 同上 |
| `/data/ds_dsd_attach_profile.txt_Subscription01` | 同上 |
| `/Data_Profiles/Profile5`、`Profile8` | 同上 |
| `/nv/item_files/modem/nas/nas_ims_setting_mode`、`nas_operator_plmn_list` | 同上 |
| `/nv/item_files/ims/qp_ims_reg_config_db`（1024 bytes）、`ims_operation_mode`（`03`） | 選中 mbn 的 LTE NV 預載 bin（`nvpreload/nv_L…bin.gz`，gzip）內的 CNV 記錄：表頭為「單元號 u16 小端 + 大小 u16 小端」，單元 5991（1024 bytes）、4703（1 byte），必須唯一匹配 |

- 與先前在 A9 驗證成功的 12 檔相比：11 檔逐位元相同（含 CNV 取出的兩檔）；policy 不同（見第 6 節）。
- cht 的 mbn 本身 policy 是 70308 bytes，不使用。

## 4. app 的改動（`device/sony/yoshino-common/apps/CustomizationSelector`，**尚未 commit**）

- `EfsSwitcher.java`：不相容模式只寫 12 檔（不再寫 mbn 全部約 80 個檔）；備份與寫入失敗還原保留；`mccList == null`（非日本型號）時不動 policy。
- 新增 `FsgEfsSource.java`（不依賴 Android，可在電腦獨立測試）：解 mbn 內嵌 tar、解 gzip NV 預載 bin 的 CNV 記錄、`withOperatorMcc`、`withFullServiceMode`、`normalizeMccList`、`policyOf`。缺任一檔就整個失敗，不部分寫入（嚴格模式）。
- 新增 `OperatorMcc.java`：`isJapanModel()`（`Build.MODEL` 符合 `SO-xx?`、`SOVxx`、`xxxSO`）、`simMcc()`、`defaultFor()`（偵錯欄位預設值，依選中 mbn 的 `modem.conf` → config id → `service_providers.xml` 查 MCC，查不到用 SIM 的 MCC）、`factoryModemFile()`。
- `ManualSwitchActivity.java`：選單最上方加「原廠預設」（701SO → `701so_softbank_r12c`、SO-01K → `so01k_docomo_r12c`、SOV36 → `sov36_kddi_r15c`；國際版不加）；偵測選項內加 `operator_mcc_list` 欄位（只在日本型號顯示，預設值隨選中 mbn 變動，格式為 3 位數 MCC、空白分隔）。
- `CustomizationSelectorActivity.java`：自動流程呼叫 `OperatorMcc.autoMcc()`（日本型號用 SIM 的 MCC，其他型號 `null`）。
- `res/layout/activity_manual_switch.xml`、`res/values/strings.xml`、`res/values-zh-rTW/strings.xml`：MCC 欄位與提示字串。
- 原廠預設 mbn 對照（原廠 ROM 的 `amss_fsg` 映像解開後與 mbn 逐位元相同）：701SO R12C → `701so_softbank_r12c`；SO-01K R12C → `so01k_docomo_r12c`；SOV36 R15C → `sov36_kddi_r15c`。國際版 ROM 有多個地區版本，沒有唯一預設。
- 編譯：`lunch lineage_poplar-bp1a-userdebug`（先 `export CCACHE_EXEC=/usr/bin/ccache USE_CCACHE=1`）→ `m CustomizationSelector`。安裝到 701SO：`adb root`、`adb remount`（會顯示 `Remount failed` 但推送成功）→ 推到 `/system/system_ext/priv-app/CustomizationSelector/CustomizationSelector.apk`、刪 `oat`、重開機。簽名與裝置上的相同（平台金鑰，SHA256 `C8:A2:E9:BC…`）。最後安裝的 APK md5 為 `d1253c986531dcf39a58c87bf0636a34`。舊 APK 備份在 `.tmp/cs_backup/`。

## 5. 驗證流程與結果

兩段式測試（2026-10-18 07:06 到 07:30）：

| 階段 | 做法 | 結果 |
|---|---|---|
| A. 切回原廠 | app 選 `701so_softbank_r21b`（相容模式，TA 2212/2405，開機由 switcher 重寫 fsg）；重開機直到穩定（兩輪測試都是第 2 次穩定） | 第一次開機 modem 重啟 2 次、未註冊；第二次開機 46692、LTE、modem 重啟 0 次、**IMS 未註冊（無 VoLTE）**。diag 讀回 EFS 為原廠：policy 5183 bytes（md5 `3eeb5be3ac31`）、無 ANDSF/Profile 檔、`ims_operation_mode` 02、`voice_domain_pref` 00 |
| B. EFS 模式 | app 選中華電信（不相容、`operator_mcc_list = 466`），套用；寫入 12 檔後 65 秒自動重開機 | 第一次開機：modem 重啟 2 次、未註冊、IMS 未註冊。第二次開機：46692、LTE、重啟 0 次、約 24 秒後 **IMS 註冊成功、HD 圖示出現** |
| C. 刪 `ims` APN | 刪除先前手動加的 `CHT IMS` APN（`_id=3631`）後重開機 | **IMS 仍註冊成功** |

另外在 B 之前的調查中，穩定之後的每次重開機、不做任何操作，IMS 都自己註冊。

## 6. 與 A9 驗證成功版本的差異（policy）

app 產生的 policy 是 701SO 原廠 policy 改兩處（`operator_mcc_list` 與 `svc_mode`）。先前 A9 驗證的 final701 是另外手改的版本，兩者還差：

- final701 保留 `operator_mcc_list = 440 441 001`，另加 `vo_mcc_list = 440 441 466 001`，並讓 RULE #2 用 `vo_mcc_list`；app 版直接把 `operator_mcc_list` 換成 `466`。
- final701 移除 B8+B3 載波聚合組合（3 處）；app 版保留原廠完整 CA 清單。
- 記憶中「保留 B8+B3 的 policy 會讓 modem 當機」這次**沒有重現**：穩定開機後 modem 重啟 0 次。

## 7. 診斷用的方法（可重複）

- 切 USB 為 diag：`adb root` 後 `setprop sys.usb.config diag,serial_cdev,rmnet,adb`（Windows 端出現 `Qualcomm HS-USB Diagnostics 9012`，701SO 是 COM10，G8342 是 COM22，要看 parent 的序號）。開機完成後系統會把組合重設，持久設 `persist.sys.usb.config` 也撐不過開機，所以要在開機後再設一次。結束務必還原：`setprop persist.sys.usb.config adb; setprop sys.usb.config adb`。
- 用 `diag_efs_read.py` / `diag_efs_batch.py` 讀寫 EFS（Windows Python，路徑用 `\\wsl.localhost\Ubuntu-24.04\…`）；用 `diag_combo.py` 擷取 F3 文字訊息與 LTE NAS/RRC 封包。
- **抓 NAS 空口封包要讓 UE 真的送出 Detach/Attach**：飛航模式只開約 16 秒時沒有 NAS 封包；開約 35 秒再關才會有。紀錄遮罩不會被清掉（用 `diag_logcfg.py` 的 op 4 讀回確認）。
- NAS 附著請求的 IE `5D 01 xx`：bit2 = UE 使用設定（0 語音中心）、bit1..0 = 語音域偏好（0 CS only、1 PS only、2 CS 優先、3 IMS PS 優先）；附著接受的 IE `64 01 xx`：bit0 = IMS VoPS、bit1 = 緊急承載。

## 8. 更正與沒有確認的事

- 更正：先前曾推論「modem 沒回報 `andsf.xml` 打不開，所以檔案還在」是錯的；diag 讀回才是準確的結果。
- 更正：曾推測「NV `voice_domain_pref` 是 00 所以 NAS 判斷 CS only」不成立；該 NV 在 policy 修正後會被 qcril 設成 `03`。
- 沒有確認：實際通話；`attach` 副檔與 `nas_*` 兩檔在 EFS 寫入後沒有再用 diag 讀回（app 寫入當下回報 OK）；「沒有 APN、從原廠基線完整重測一輪」沒有做（只在已穩定狀態下刪除 APN）。
- 限制：不相容模式在 191 個 mbn 中只有 cht 能取得全部 12 個項目（多數缺 `andsf.xml` 或 `nas_*`），缺檔時整個失敗；`operator_mcc_list` 的改寫只在日本型號啟用，國際版（G8341/2/3）不動 policy。

## 9. 重開機次數與 modem 當機循環調查（2026-10-18 07:06 到 08:55）

測試做法：每次改 fsg 或寫 EFS 之後，**不手動重開機**，用腳本每 20 秒記錄 modem 重啟次數（`dmesg` 的 `Restart sequence requested for modem`）、營運商、IMS 註冊狀態。

| 情境 | 第一次開機 | 之後 |
|---|---|---|
| 相容模式切 r21b（07:06） | 2 分鐘內重啟 2 次，未註冊 | 手動重開機一次 → 穩定（0 次） |
| EFS 寫入 cht（07:13） | 2 分鐘內重啟 2 次，未註冊 | 手動重開機一次 → 穩定、VoLTE |
| 相容模式切 r21b（08:13） | 觀察 17 分鐘，**重啟 22 次**，沒有停 | 重開機一次 → 穩定（0 次） |
| EFS 寫入 cht（08:34） | 觀察 5 分鐘，重啟 7 次 | 重開機後**仍循環**（重啟 6 次以上）；第 3 次開機才穩定、VoLTE |
| EFS 寫入**相同內容**（08:50） | **沒有循環**（0 次），開機後 21 秒 IMS 註冊 | — |

結論：
- 當機循環是 modem 的看門狗：`modem subsystem failure reason: dog_hb.c:266:DOG_HB detects starvation of task 0x…`，每次是**不同的任務位址**（整體卡住，不是某個特定任務），每輪相隔約 46 秒。
- 循環**不會自己停**：單純等待、`sync`、重啟 `vendor.rmt_storage` 與 `vendor.tftp_server` 都沒有用；只有重開機才會恢復，而且需要的次數不固定（2 到 3 次）。
- **觸發的是內容改變，不是寫入動作**：重新套用逐位元相同的 12 檔，第一次開機就不會循環。
- 每一輪 modem 的 rcinit 初始化約 0.5 秒就完成（不是初始化變慢），之後約 40 秒的穩態只有 `a2_power`、`lte_rrc_stm`、`pdsch_emem_mgr` 等例行訊息，然後才被殺。擷取結尾那批 `ims_rtp_daemon` 訊息是 Android 端在 modem 當機後的反應，不是原因。
- 沒有發現 `rmt_storage`、UFS 的錯誤；`keyprov_daemon` 每次開機（含穩定那幾次）都會印 `Suntory is not ready`，不是區別。
- **根因沒有查出來**。

工具與日誌（`.tmp/`）：`poll_boot.sh`、`watch_boot.sh`、`poll_now.sh`、`loop_exp.sh`（循環中的對照實驗）、`cap_loop_701so.sh`（循環中擷取 F3）；`poll_*.log`、`poll_*_ssr_*.txt`（每次重啟的 kernel 記錄）、`modem_loop_701so.txt`。

### 9.1 在循環中的深入調查（09:31 到 10:15）

- **modem 記憶體傾印拿不到內容**：把 `/sys/module/subsystem_restart/parameters/enable_ramdumps` 設為 1，並在當機前常駐讀取 `/dev/ramdump_modem`，每次當機都得到 116,435,317 bytes 的 ELF（28 個區段），但**內容全是 0**（整份只有標頭 423 個非零位元組）。modem 記憶體區域對 Android 端是受保護的，這條路走不通。
- **當機和無線電運作有關**：循環中把飛航模式打開（無線電關閉），modem 重啟完全停止（135 秒內重啟次數不變，原本約每 46 秒一次）。
- **結束循環的關鍵是飛航模式「開得夠久」**：
  - 開約 135 秒再關：再重啟 1 次後註冊、穩定（先前的觀察）。
  - 開約 168 秒再關：再重啟 1 次後註冊，IMS 約 67 秒後註冊成功，**不需要重開機**；之後用 diag 讀回，12 個 EFS 檔內容都保留。
  - 只開 30 秒再關：**循環沒有停止**（重啟仍在增加）。
- 推測（尚未驗證）：循環不會停，是因為 modem 每約 46 秒就當機一次，EFS/NV 的改動還來不及被提交（寫回）；無線電關閉後 modem 不再當機，可以活得夠久完成提交；整機重開機則在關機流程中提交。這和「寫入相同內容不會循環」「重開機後恢復」「飛航模式要夠久」三個現象一致，但沒有直接證據（未確認提交間隔，也沒有試 60 或 90 秒的飛航模式）。
- **寫入被洗掉的情形**：app 回報寫入 OK，但開機後讀回是原廠內容。共 3 次：05:12（剛切換 fsg 之後）、09:43 與 09:51（切換 fsg 後的循環，用 30 秒以外的飛航模式結束，沒有重開機）。而 07:13、08:34、10:01 的寫入有保留（切換後以重開機穩定下來，或是穩定一段時間之後）。使用者推測與「剛切換過預設再切回來」有關；資料與這個說法部分吻合，但沒有證實，也沒有找到 modem 端的還原訊息。
- 在循環中比較 F3 日誌：開機最初 8 秒的訊息量與組成與穩定開機相近（WLAN 校正訊息兩邊都有）；modem 的 rcinit 初始化約 0.5 秒完成，沒有明顯卡在某個步驟。
- 沒有發現 AP 端 `rmt_storage`/`tftp_server` 或 UFS 的錯誤；`sync`、重啟這兩個服務對循環沒有影響。

### 9.2 取得 modem 當機現場的其他途徑（16:30 到 16:45）

- **minidump 沒有資料**：設 `enable_mini_ramdumps=1`（同時 `enable_ramdumps=1`），在當機前常駐讀取 `/dev/ramdump_md_modem` 與 `/dev/ramdump_modem`。用診斷指令強制當機後（見下），kernel 確認走了 SSR 流程，但 `ramdump_md_modem` 讀到 **0 位元組**（完全沒產生資料）；`ramdump_modem` 仍是 116,435,317 bytes、只有標頭 423 個非零位元組。這是一般的 ERR_FATAL，不是看門狗，所以不是看門狗情境才全 0。
- **強制 modem 當機的方法**：用診斷口送 `4B 25 03 00`（QXDM 的 `send_data 75 37 3 0`），modem 會立刻 ERR_FATAL，kernel 記錄為 `modem subsystem failure reason: err_inject_crash.c:347:Crash injected via Diag.`。不必再等當機循環就能測傾印；腳本是 `.tmp/diag_crash.py`。強制當機後 IMS 不會自己重新註冊，需要重開機（modem 重啟次數維持不變，重開機後 27 秒內 IMS 註冊）。
- **modem 在 EFS 留下的記錄**：用診斷口列 EFS 目錄（`.tmp/diag_efs_ls.py`）。根目錄沒有 `err`、`crash`、`dump` 資料夾；有 `mcfg`（空）、`nvta_log`、`safe`、`nvm`、`.efs_private`（後三個列目錄逾時）。`/nvta_log/log.txt`（26,757 bytes）是每次 modem 開機的 NV/TA 載入記錄：修剪區載入 855 項只花 600 ms、CNV 匯入正常、EFS 剩餘空間約 1.27 MB；**沒有當機資訊**。
- **尚未嘗試的路**：核心的 `msm_poweroff/download_mode` 是 1，可以把 modem 重啟層級設成 `SYSTEM` 讓 modem 當機觸發核心 panic，進 Qualcomm 下載模式後用 PC 端 Sahara memory debug 讀整份 DDR（modem 區段從 `0x8cc00000` 起）。這會刻意讓核心 panic，需要先確認。

建議的操作流程（目前最穩的做法）：切換 fsg 後先**重開機直到 modem 重啟次數為 0**，再寫 EFS；寫入後若進入當機循環，把飛航模式**開 150 秒以上**再關，或重開機到穩定；最後用 diag 讀回確認 12 檔是否保留。

還沒做、可以接著試的：飛航模式 60、90、120 秒各自能否結束循環（找出門檻）；逐檔二分是哪一個 EFS 檔案的內容改變觸發循環。

### 9.3 直接比較 EFS：穩定態 vs 寫入內容改變後（2026-10-18 17:52 到 18:47）

工具：`.tmp/efs_snap2.sh 標籤`（暫切 USB 到 diag，唯讀列出 `/policyman`、`/data`、`/Data_Profiles`、`/nv/item_files/ims`、`/nv/item_files/modem/{nas,mmode}`，再逐檔讀回；`carrier_policy.xml_Subscription01` 為省時間略過）。結果在 `.tmp/efs_cmp/<標籤>/`（`files/`、`tree.txt`、`sha.txt`）。

- 穩定態（開機 1 小時以上、modem 重啟 0 次、46692 LTE）共讀回 132 檔（`stable2`）。這個穩定態不是我們的 12 檔：`carrier_policy.xml` 是 70308 bytes（cht 原檔）、`andsf.xml` 1355 bytes、`ims_operation_mode`=02；`ds_andsf_config`、`Profile5/8`、`attach`、`nas_ims_setting_mode`、`nas_operator_plmn_list` 與暫存的 12 檔相同。
- 把暫存的 12 檔經 diag 寫入（內容與穩定態不同）→ 等 65 秒 → 重開機：**第一次開機沒有進入崩潰循環**（4 分鐘內 modem 重啟 0 次，46692 LTE 註冊）。與 §9 的「內容一改就循環」不一致，表示**單純 EFS 內容改變不足以觸發**，先前的循環應與 fsg 切換有關（尚未驗證）。
- 寫入後再讀 132 檔（`after_write`）與穩定態比對：檔案集合相同，**只有我們改的 5 個檔不同**（`carrier_policy.xml`、`andsf.xml`、`andsf.xml_Subscription01`、`ims_operation_mode`、`qp_ims_reg_config_db`），內容與寫入的逐位元一致；其餘 127 個檔（含 modem 自己產生的 `policyman/svc_mode`、`current_mcc`、`rat_mask`、`nas/rplmn`、`mm_backoff_remaining_info` 等）完全相同。
- **還沒有「崩潰態」的快照**：要造出崩潰循環得切換 fsg（寫 sda34 與重設 modemst），需使用者同意。

### 9.4 切 fsg 造崩潰態，三段 EFS 比對（2026-10-18 18:48 到 19:17）

做法：app「原廠預設」（`r12c`，相容模式）把 sda34 由 `r21b` 切成 `r12c`（開機後用 `dd` 與 mbn 逐位元比對確認），重開機後立刻進入崩潰循環（64 秒、112 秒各一次 `DOG_HB starvation`，task 位址每次不同）。三段各用 diag 唯讀讀回，工具 `.tmp/efs_snap3.sh`，結果在 `.tmp/efs_cmp/{after_write,loop,after_loop}/`、彙總在 `.tmp/cmp_out/`。

| 階段 | 時間 | 狀態 |
|---|---|---|
| A 切換前穩定 | 18:40 | 寫入 12 檔後的穩定態，重啟 0 次（132 檔） |
| B 崩潰循環中 | 18:51 到 18:56，另 18:58 讀 10 檔 | 讀取期間 modem 重啟 2→9 次，讀取沒被打斷（132 檔 + `/nvpreload`、`/ims`、`/nvta_log` 共 10 檔） |
| C 循環結束後穩定 | 19:11 到 19:17 | 重啟 0 次、46692（142 檔） |

結果：
- **A、B、C 的所有共同檔案逐位元相同，一個都沒有差**；B 額外讀的 10 檔（`/nvpreload/completed*`、`band_mapping_override*`、`/ims/imshandoverconfig`、`/nvta_log/log.txt`）與 C 也完全相同。
- **切 fsg 沒有改動任何可讀到的 EFS 檔**：循環中的 `carrier_policy.xml` 仍是切換前寫入的 4725 bytes。與先前「切 fsg 會重設 modemst、EFS 被洗掉」的描述不符，至少這一次沒有。
- `/nvta_log/log.txt`（21198 bytes）在循環中與循環後完全相同，也就是 modem 重啟十幾次、又重開機兩次，這份日誌都沒有新增區塊。內容的最後三個區塊記的變體是 `poplar_dsds_fareastone_tw_ims_glteca_…`，不是 `softbank`，與 16:22 保存的舊檔（全是 `softbank`）不同。這份日誌的寫入時間無法判斷，區塊順序也不是時間序，所以不能當成時間線用。
- `/nvpreload/completed*` 內容是固定字串 `EFS Completed`，沒有版本資訊，無法用來判斷預載是否套用完成。
- **飛航模式開 150 秒這次沒有結束循環**（關閉後重啟 14→17 次），與 §9.1 的「≥135 秒會結束」不一致，門檻不可靠。改用重開機：第 1 次開機仍循環，第 2 次開機穩定。
- 沒覆蓋到的範圍：`/nvm`（開啟逾時）、`/mcfg`（讀到是空的）、`/rf*`、`/sfs`、`/sd`、`/safe`、`/nv/item_files` 下 `ims`、`modem/nas`、`modem/mmode` 以外的子目錄、`carrier_policy.xml_Subscription01`。

結論：在已讀的 EFS 範圍內，崩潰循環和穩定態沒有檔案層面的差異，**原因不在這些 EFS 檔案的內容**。比較可能的方向是 fsg 切換本身（modem 在開機時載入新 fsg）、`/nvm`、`/mcfg` 這類讀不到的區域，或 modem 內部狀態。

### 9.5 fsg 版本、modem 韌體版本與 r12c / r21b 的差異（2026-10-19）

- 701SO 原廠 ROM 與 fsg：`47.2.D.1.150-R12C` 的 `amss_fsg` 映像 = `amss_fsg_poplar_701so_softbank_r12c_tar.mbn`（140072 bytes）；`47.1.D.11.32-R21B`（`amss_fsg.sin`，檔名不同）= `amss_fsg_poplar_701so_softbank_r21b_tar.mbn`（129832 bytes）。兩者都是 701SO 自己的原廠 fsg，r12c 較新。
- 這台 LineageOS 701SO 的 modem 韌體是 `MPSS.AT.2.0.c4.3-00278-8998_GEN_PACK-1`（`/vendor/firmware_mnt/verinfo/ver_info.txt`；`ro.vendor.build.fingerprint` 為 G8342 `47.2.A.11.228`）。三個 ROM 的 `modem.sin` 內的 MPSS 版本：701SO R12C 為 `00278`、G8342 台灣版為 `00278`、701SO R21B 為 `00197`。**韌體版本與 r12c 相同，而不是 r21b**，所以「fsg 必須和 modem 韌體同版」解釋不了 r12c 的問題。
- r12c 與 r21b 的 fsg 差異（其餘全部相同，policy 的 md5 都是 `3eeb5be3ac31`）：r12c 多 `/SUPL/Equifax.crt`、`/SUPL/GlobalSignR2.crt`；`srv_req_throt_config.txt` 的 `FAILURE_TIMER_5` 在 r12c 是 `0`、r21b 是 `20`；NV 預載 bin `nv_L12348_11_12_17_28_38_39_40_41_42LCA138_11_28_41_42W1248.bin.gz` 解壓後 r12c 86434 bytes、r21b 86410 bytes（r12c 多 3 筆各 8 bytes 的記錄與結尾 2 bytes 不同）。這些差異是否造成 r12c 的當機循環，**沒有驗證**。
- r12c 與 r21b 在這台上的已知現象（見 §9、§9.4）：切到 r12c 後第一次開機立刻進入 `DOG_HB` 循環、第 2 次開機穩定並註冊 46692 LTE（當時沒有檢查 IMS）；r21b 也出現過循環（08:13 重啟 22 次、08:34 重啟 7 次）。也就是當機循環不是 r12c 獨有，但「r12c 沒有 LTE」若發生在循環期間是成立的。r12c 上 VoLTE 是否能起來**沒有測過**。

### 9.6 r12c 基底的完整測試：切 r21b → 切回 r12c → 寫 cht EFS（2026-10-19 00:30 到 01:06）

每次改 fsg 或寫 EFS 後不手動操作，只用 `watch_boot.sh` 記錄開機後的 modem 重啟次數、營運商與 IMS 狀態（`.tmp/boot_*.log`）；fsg 以 `dd` 與 mbn 逐位元比對確認。

| 階段 | 開機次數與結果 |
|---|---|
| 起始：r12c | 開機 30 分鐘、modem 重啟 39 次、營運商空白（循環中）。重開機 1 次 → 46692、LTE、重啟 0 次；資料可用（Wi-Fi 關閉下連線檢查回 204、ping 168.95.1.1 通）；再重開機仍穩定。IMS 未註冊（EFS 為原廠內容） |
| 用 app 相容模式切 r21b | 第 1 次重啟 3 次未註冊；第 2 次重啟 3 次未註冊；**第 3 次** 46692、LTE、重啟 0 次 |
| 用 app「原廠預設」切回 r12c | 第 1 次重啟 3 次未註冊；**第 2 次**重啟 1 次後 46692、LTE，一分鐘後仍是 1 次，資料可用 |
| 用 app EFS 模式寫中華電信 12 檔（r12c 基底，`operator_mcc_list=466`） | 第 1 次重啟 3 次、未註冊；**第 2 次** 46692、LTE、重啟 0 次，約 30 秒後 **IMS 註冊成功、HD 圖示出現** |

結論：
- r12c 這個 fsg 在這台上不是「沒有 LTE」：切換後第一次開機會進入 modem 當機循環，**多開機一到兩次**就會註冊並有資料。使用者觀察到的「r12c 沒有 LTE」對應的是循環期間。
- r12c 基底上的 VoLTE 與 r21b 一樣成立（寫 EFS 後開兩次機）。
- 各階段穩定所需的開機次數不固定：r21b 3 次、r12c 2 次、EFS 寫入後 2 次；循環中的重啟次數 1 到 3 次不等。判斷時看「重啟次數是否為 0 或維持不變」並多開機，不要只看第一次開機。

### 9.7 「SIM 自動」選項與「目前 modem：?」的修復（2026-10-19）

- **「SIM 自動」**：`ManualSwitchActivity.simAutoCarrier()` 用自動流程同一套邏輯（預設資料卡 → `sim_config_id` → config id → `modem.conf` → mbn）解出目前 SIM 對應的設定，放在選單最上面，標示「SIM 自動」，套用時一併寫該 config id 到 TA 2212。沒有 SIM、找不到對應設定、或對應的 mbn 不存在時不顯示。驗證：遠傳 SIM（46601，`S278.1`）顯示 `poplar_dsds_fareastone_tw_ims (SIM 自動)`。下拉選單會為了顯示目前選取的項目而往下捲一格，「SIM 自動」在最上面，需要往上捲才看得到。
- **「目前 modem：?」的原因**：app 讀 `/cache/modem/modem_switcher_status`，檔案存在、內容正確（`0,amss_fsg_poplar_701so_softbank_r12c_tar.mbn`），但目錄 `/cache/modem` 是 `root:root` `0770`（由 root 身分的 `vendor.modem_switcher` 建立），app 是 `radio` 使用者，沒有一般檔案權限進入，所以 `isFile()` 回傳 false（日誌 `Status file does not exists or is not a file`）。SELinux 規則（`allow radio modemsw_cache_file:dir rw_dir_perms`）本來就有，問題只在檔案權限。
- **修法**：`device/sony/yoshino-common/init/init.qcom.rc` 的 `service vendor.modem_switcher` 把 `group` 的第一個（主要）群組由 `root` 改成 `radio`（`group radio system oem_2993 cache`，`user root` 不變），這樣 switcher 建立的 `/cache/modem` 群組直接是 `radio`（尚未 commit，要等下次 ROM 建置才生效）。**已在 701SO 實測**：把改過的 rc 推到 `/vendor/etc/init/hw/init.qcom.rc`（原檔備份在 `.tmp/rc_backup/init.qcom.rc.device_orig`）並重開機（LTE、modem 重啟 0 次、IMS 註冊）；刪除 `/cache/modem` 後手動啟動服務，switcher 行程為 `Uid 0`、`Gid 1001`（radio）、補充群組 `1000 2001 2993`，並自行重建目錄為 `0:1001`、`0770`、標籤 `modemsw_cache_file`。switcher 在「目前 modem 與 TA 要求相同」時只比對、不寫狀態檔，所以那次重建的目錄是空的，我把備份的兩個狀態檔放回去（`root:cache` `0644`）後，app 顯示正確的 `amss_fsg_poplar_701so_softbank_r12c_tar.mbn`，下拉選單也預選對應項目。
- 較早用過的做法（switcher 結束後 `chown root radio /cache/modem`）已撤掉，不需要兩個並存。
- 「設定 ID：」空白是正常的（原廠預設與相容模式切換會把 TA 2212 清空）。

## 10. 相關

- 前一份狀態文件（A9 原廠系統上的成功狀態）：[701so_volte_working_state_2026-10-17.md](701so_volte_working_state_2026-10-17.md)
- 最小集與二分：[701so_volte_cht_fix.md](701so_volte_cht_fix.md)
- 暫存與日誌（`.tmp/`）：`modem_live4_701so.txt`（含 NAS 封包的擷取）、`modem_cap_701so_boot.txt`、`cap_live4_701so.sh`、`diag_combo2.py`、`diag_logcfg.py`、`diag_maskwatch.py`、`watch_boot.sh`、`boot_*.log`、`efs_read_*`。
