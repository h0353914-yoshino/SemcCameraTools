# whatawurst OpenCustomizationSelector（OpenCS）分析

來源：`github.com/whatawurst/android_device_sony_yoshino-common`（已完整 clone 到 `.tmp/whatawurst_full/yoshino-common`，lineage-21，5426 筆提交，另有 lineage-17.1～21、android-9.0/12.1、twrp 分支）。同時 clone 了 `poplar`、`poplar_dsds`、`poplar_kddi` 三個裝置樹到 `.tmp/whatawurst_clone/`。
原廠二進位 `sony-modem-switcher` 取自 G8342 原廠 system 映像（`.tmp/sms/`）。

## 1. 一句話
OpenCS 是 Sony 原廠 CustomizationSelector 的開源重寫（約 3000 行 Java，system_ext 特權 APP，platform 簽章，`sharedUserId=android.uid.phone`）。它**只負責「判斷該切哪個 modem 設定並寫 TA 指令、請使用者重開機」**；真正把 mbn 寫進 fsg 並重設 modemst 的是原廠二進位 `/system/bin/sony-modem-switcher`。

## 2. 資料流（SIM → fsg）
1. **觸發**：`EventReceiver` 收到 `CARRIER_CONFIG_CHANGED`（且是預設數據卡）或 `BOOT_COMPLETED` → 啟動 `CustomizationSelectorService("evaluate_action")`。使用者未解鎖（非 DirectBoot）時直接略過。
2. **SIM → sim_config_id**：`SimConfigId` 取 MCC/MNC、營運商名稱、IMSI、GID1、ICCID，與 `res/xml/service_providers.xml` 逐條比對並計分（MCC+MNC 相符 +1；有 sp/imsi/gid1 條件則相符 +1、不符 −1，取最高分）。例：466-92 → `S277.1`、466-01 → `S278.1`、466-97 → `S280.1`、466-89 → `S283.1`。
3. **sim_config_id → config_id**：`DynamicConfigParser` 讀 `res/xml/configuration_selectors.xml`（`<configuration config_id="93"><sim_config_id>S277.1</sim_config_id>`；`ANY_SIM` 為備援）。
4. **config_id → modem 變體名**：`ModemConfParser` 讀 `/oem/modem-config/<id>/modem.conf`（沒有 `/oem` 才讀 `/system/etc/customization/modem/<id>/modem.conf`），內容是一個字串，如 93 → `cht_tw_ims`、92 → `fareastone_tw_ims`、94 → `twm_tw_ims`、426 → `tstar_tw_ims`、567 → `asiapacific_tw_ims`。
5. **變體 → mbn**：`ModemConfiguration` 在 `/system/etc/customization/modem/` 找結尾為 `<變體>_tar.mbn` 的檔（找不到用排序後第一個，也就是最短檔名＝預設）。目前 modem 與目標相同就不切。
6. **寫指令**：`ModemSwitcher.writeModemToMiscTA` 把 TA 單元 **2405** 寫成 `F0 7A 01` + mbn 檔名；`Configurator.set` 另把 config_id 寫進 TA 單元 **2212**（`ro.semc.version.cust.active`），並把 sim id 設進 `persist.sys.sim_config_ids`。
7. **跳重開機對話框**（`CustomizationSelectorActivity`，`UserPresentReceiver` 在螢幕亮起時叫出 HOME）；使用者重開機。
8. **實際切換**：init 在 `on boot` 的 `start modem_switcher`（`class main`、`user root`、`oneshot`）啟動 `sony-modem-switcher`。依 binary 字串：讀 TA（modem 指令單元／active customization 單元）→ 把 `/system/etc/customization/modem/<檔>` 整份寫進 `/dev/block/bootdevice/by-name/fsg`（先取分區大小、讀檔、寫、`sync`）→ 把 `reset_modemst1/2`（連到 1 KB 全零的 `amss_fs_empty.mbn`）寫進 `modemst1`、`modemst2` → 寫 `/cache/modem/modem_switcher_status`（格式 `<狀態碼>,<modem 名>`）與 TA 單元 2404（TA_FOTA_INTERNAL）。字串中有三種分支：「active customization 未啟用→用 default modem」、「MiscTA 說要用最新版本」、「MiscTA 指定 %s」。錯誤碼：`MODEM_ERR_CONFIG_WRITE`、`MODEM_ERR_PART_WRITE`。
9. modem 以空的 modemst 啟動後，會把 fsg 這份 tar 的檔案灌進 EFS（G8342 實測 `andsf.xml` 與 mbn 內的逐位元組相同）；頻段預載資料則由 TA 的組態名（`0x09FB`）從 fsg 內多組 `nvpreload` 中挑一組。

整個流程**沒有任何部分複製**：app 只寫 TA，binary 只寫整份分區。

## 3. 其他元件
- **ImsSwitcher**：設定開關 `cs_ims`（Settings.System）。開＝重新評估並切到該電信的 IMS 版 mbn；關＝切回預設（依 `ro.build.flavor`：lilac / poplar / poplar_dsds / maple / maple_dsds 各有預設檔）。
- **reApplyModem**（`cs_re_apply_modem`，預設關）：每次評估後重寫 TA 2405 並把 2404 設成 `temporary_modem`，避免 modem 被原廠機制沖掉；`revertReApplyModem` 把 2404 寫回目前 modem 名。對應我們在 701SO 看過「EFS 被沖掉」的現象。
- **NetworkSwitcher**（`NS/*`，預設關）：SIM 載入後，把偏好網路從 LTE 切到 3G 再切回，用來讓「SIM 一直沒服務」的機器重新註冊（提交說明：「Some users were found who required to switch to 3G to get their SIM in service」）。等於程式化版本的「點開進階觸發註冊」，與我們 701SO 開機偶爾不搜網的狀況相近。雙卡用 `ns_slot` 選卡，也會等 `ACTION_USER_UNLOCKED`。
- **MasterClearReceiver**：收到 `MASTER_CLEAR_NOTIFICATION` 時清 TA 2212。
- 設定開關都是 `Settings.System`：`cs_ims`、`cs_notification`、`cs_re_apply_modem`、`ns_slot`；由 XperiaParts 透過 `PreferenceReceiver` 操作。

## 4. 裝置樹如何接上（重點：資料都在裝置樹，不在 app）
- app 內 `res/xml/configuration_selectors.xml` 是空的（提交 `04f5ca66`：「These are to be filled by devices via overlays」）；`service_providers.xml` 只有 yoshino-common 的 overlay 填入（2653 行）。
- 各裝置樹提供 `overlay/device/sony/yoshino-common/hardware/OpenCustomizationSelector/res/xml/configuration_selectors.xml`：
  - `poplar_dsds`（G8342）：196 行、38 個 config（含台灣 92/93/94/426/567），`config/modem/<id>/modem.conf` 只有 5 個台灣條目＋預設。
  - `poplar` / `poplar_kddi`：327 行、95 個 config（歐洲／拉丁美洲為主），**沒有任何台灣 sim_config_id**，`config/modem/` 有 96 份（多為歐美），`92/93/94/426/567` 不存在。
- `hardware/modem/Android.mk` 建立 `reset_modemst1/2 → amss_fs_empty.mbn` 與 `default →` 該機種預設 mbn（`poplar_kddi` 的預設是 `amss_fsg_poplar_tar.mbn`，單卡全球版）。
- `poplar_kddi` 的 mbn 全是單卡全球版（來自 G8341），其預設檔內含 5 組頻段預載資料（含 SOV36 自己的 `L13457_11…`），所以 SOV36 靠 TA 組態名仍選到自己那組。`system.prop` 把 SOV36 偽裝成 G8341（`ro.semc.product.model=G8341`、`sw_variant=GLOBAL-LTE4A`）。

## 5. 對我們（poplardcm）的意義
1. 想在 LineageOS 上依 SIM 自動切 fsg：`CustomizationSelector` APK ＋ `sony-modem-switcher` ＋ init 服務 ＋ TA 權限（`com.sonymobile.permission.TRIMAREA`、oem_2993 群組）＋ `/system/etc/customization/modem/` 的 mbn 與 modem.conf ＋ 兩份 overlay XML，缺一不可。
2. 切換本身對 modem 是整份 fsg ＋ 清空 modemst，不會只換部分電信檔案。
3. 701SO（日系）能不能切，取決於 fsg 裡有沒有它 TA 組態名對應的預載資料：G8341 單卡 fsg 有（含 `L12348_11`），G8342 雙卡 fsg 沒有（實測 modem 當機）。
4. 即使 fsg 換成中華電信，也不保證能 VoLTE 的 Android 端條件仍要另外滿足（`persist.dbg.volte_avail_ovr`、CarrierConfig 圖示 key）。
5. NetworkSwitcher 可作為「開機不搜網」的參考做法（切 3G 再切回），但它預設關閉，且依賴 `setAllowedNetworkTypesForReason`。

## 6. 尚未驗證／限制
- `sony-modem-switcher` 只看了字串，沒有反組譯，不知道它如何決定「寫檔長度」與「active customization」分支的細節。
- 我沒有在裝置上跑過 OpenCS；本文是原始碼與檔案內容的靜態分析。
