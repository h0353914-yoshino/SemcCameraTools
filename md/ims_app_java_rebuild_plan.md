# IMS App（org.codeaurora.ims）改為從 Java 原始碼重新編譯 — 交接計畫

> 給接手的 AI：本文件自成一體。先讀「0. 規則」與「1. 背景與目標」，再依「5. 工作步驟」逐步做。
> 標示「**未驗證**」的項目是推論，動手前請先自行確認。所有回覆、註解、文件使用繁體中文（台灣）。

---

## 0. 專案規則（來自 `AGENTS.md`，必須遵守）

- 所有暫存檔與 log 只能放 `SemcCameraUI/.tmp/`（即 `/home/h/tmp/SemcCameraUI/.tmp/`），**嚴禁用 `/tmp`**。
- adb 一律用 Windows 版：`/mnt/f/Android/platform-tools/adb.exe -s BH90018Q63 ...`。WSL 內的 `adb`（LineageOS 編出來的）看不到 USB 手機。
- **每次** AOSP/LineageOS 編譯前先 export，否則 Soong 判定環境變了、整個 `out/soong` 快取失效，觸發全樹重編：
  ```bash
  cd ~/lineageos
  export CCACHE_EXEC=/usr/bin/ccache USE_CCACHE=1
  source build/envsetup.sh && lunch lineage_poplar-bp1a-userdebug && mka <模組名>
  ```
  輸出若出現 `environment variables changed value`（舊 → 新 的箭頭格式）就停下來，代表環境錯了。只編單一模組，不要 `make bacon`。
- 同一個 `~/lineageos` 樹有另一個 AI 也在使用（測 701SO）。編譯前先 `ps -eo pid,etime,cmd | grep -E "soong_ui|ninja|kati"` 確認沒有編譯在跑，不要同時開兩個建置。**不要動**它尚未提交的改動（例如 `device/sony/yoshino-common/overlay/packages/apps/CarrierConfig/res/xml/vendor.xml`）。
- 除非使用者明說，**不要 commit / push**。若被要求提交：LineageOS 各 repo 用一行主旨、不寫多行內文、不加 Co-Authored-By。
- 改 `ims.apk` 之前先備份，且每次重開機後 `adb root` 會失效，要重下。
- 等待動作（重開機、編譯）啟動時先說預估時間；不要在單一前景指令裡串長時間 sleep 迴圈。

---

## 1. 背景與目標

**裝置**：Sony G8342（Xperia XZ1 台灣版，序號 `BH90018Q63`），跑 LineageOS 22.2（Android 15，`lineage_poplar-bp1a-userdebug`）。

**現況**：VoLTE 已在這台 A15 上走通（乾淨開機後 MmTel `Voice: true`、IMS 註冊成功、可通話不退回 3G）。狀態列的「VOLTE」圖示由 IMS App 自己以**通知**發出。

**IMS App 來源**：`system_ext/priv-app/ims/ims.apk` 是從 **Fairphone FP3 韌體 6.A.040.4** 抽出來的預編譯檔（`device/sony/yoshino-common/proprietary-files.txt` 第 910 行，段落標題 `# Radio (IMS) - from FP3 - 6.A.040.4`），樹裡以 `android_app_import` 掛載：

```
vendor/sony/yoshino-common/Android.bp 第 15719–15729 行
android_app_import {
    name: "ims",
    owner: "sony",
    apk: "proprietary/system_ext/priv-app/ims/ims.apk",
    certificate: "platform",
    dex_preopt: { enabled: false },
    privileged: true,
    system_ext_specific: true,
}
```

**目標（本任務）**：把 `ims.apk` 的 Java 原始碼（JADX 已反編譯好）整包重新編成可安裝的 App，行為與原 APK 一致，作為之後修改（例如改圖示顯示方式）的基礎。

**本任務不包含**：任何功能修改。第一階段只求「重編後的 APK 行為與原版一致」。圖示改法見「8. 後續（不在本任務範圍）」。

**為什麼要做**：整包 Java 只有約 2.7 萬行應用程式碼（其餘是自動生成的 HIDL 介面），比直接改 smali 容易維護；但只為了一個圖示就整包重編，投入比直接改 smali 單一方法大得多。因此本任務是「評估並嘗試」，**如果發現某處無法保證行為一致，請停下並回報，而不是硬做**。

---

## 2. 現有資產（都已備妥，不需重做）

| 項目 | 路徑 |
|---|---|
| 原版 APK（從手機拉下來，已被建置重簽） | `/home/h/tmp/SemcCameraUI/.tmp/imsapk/ims.apk`（SHA-256 `565256bea422e27c7196696756a9463ab411c1245b8d192f8a7382dc03b95c18`） |
| 樹內預編譯檔（簽章前） | `~/lineageos/vendor/sony/yoshino-common/proprietary/system_ext/priv-app/ims/ims.apk`（SHA-1 `5340ba42c0108de7d7bad44f48492fd06bd1f91f`） |
| **JADX 反編譯 Java（本任務輸入）** | `/home/h/tmp/SemcCameraUI/.tmp/imsapk/ims_java/sources/`（273 個 `.java`，共 76,586 行） |
| JADX 解出的資源與 manifest（已解碼的 XML） | `/home/h/tmp/SemcCameraUI/.tmp/imsapk/ims_java/resources/`（`AndroidManifest.xml`、`res/`） |
| smali 反編譯（用 apktool `-r`，**manifest 與資源是二進位未解碼**） | `/home/h/tmp/SemcCameraUI/.tmp/imsapk/ims_smali/` |
| 整包反編譯驅動程式 | `/home/h/tmp/SemcCameraUI/.tmp/rea_tools/Dec.java`（4 秒跑完，見 §6） |
| 逆向工具 | REA 6.4.0 與 JADX JAR：`/home/h/tools/jadx-headless-mcp/jadx-headless-mcp-0.7.1-all.jar`（SHA-256 已核對 `6e5eacf5…ff75`） |

**Java 原始碼規模**（`ims_java/sources/`）：

| 套件 | 檔數 | 行數 | 說明 |
|---|---|---|---|
| `vendor/qti/hardware`（HIDL 介面 V1_0 到 V1_7 的 Java 代理） | 164 | 49,103 | 自動生成，不需手動維護 |
| `org/codeaurora/ims` | 92 | 23,091 | 主要應用程式碼 |
| `com/qualcomm/ims` | 15 | 3,867 | 視訊（VT）與相機 |
| `android/hidl/base` | 2 | 525 | HIDL 基礎介面 |

最大的類別：`ImsSenderRxr` 3,372 行、`ImsRadioUtils` 2,505 行、`ImsCallSessionImpl` 2,369 行、`ImsServiceSub` 1,929 行。類別名稱未混淆。

---

## 3. 原 APK 的關鍵屬性（重編後必須維持）

來自 `ims_java/resources/AndroidManifest.xml`：

- `package="org.codeaurora.ims"`、`versionCode=1`、`versionName=1.0`
- `coreApp="true"`、`android:persistent="true"`、`android:directBootAware="true"`、`android:usesNonSdkApi="true"`、`android:extractNativeLibs="true"`、`android:allowBackup="false"`
- `minSdkVersion=33`、`targetSdkVersion=31`（`compileSdkVersion=33`）
- 兩個服務：
  - `org.codeaurora.ims.ImsService`（權限 `android.permission.BIND_IMS_SERVICE`，meta-data `MMTEL_FEATURE`、`EMERGENCY_MMTEL_FEATURE`，intent-filter `android.telephony.ims.ImsService`，`singleUser`）
  - `org.codeaurora.ims.QtiImsExtService`（權限 `com.qti.permission.BIND_QTI_IMS_SERVICE`）
- `uses-library`：`qti-telephony-hidl-wrapper`、`qti-telephony-utils`、`ims-ext-common`
- 多個 `protected-broadcast`（`org.codeaurora.VOIP_VOPS_SSAC_STATUS` 等）與自訂 `permission`（`com.qti.permission.*`），以及一長串 `uses-permission`（`MODIFY_PHONE_STATE`、`READ_PRECISE_PHONE_STATE`、`WRITE_SECURE_SETTINGS`、`CAMERA`、`SYSTEM_ALERT_WINDOW` 等）。**直接沿用 `ims_java/resources/AndroidManifest.xml` 的全部內容**，不要自己刪減。
- 簽章：以平台金鑰簽（`certificate: "platform"`），`privileged: true`，`system_ext_specific: true`。
- 特權權限白名單目前在 `vendor/sony/yoshino-common/proprietary/system_ext/etc/permissions/telephony_system-ext_privapp-permissions-qti.xml` 第 51–58 行（`org.codeaurora.ims`）：`MODIFY_PHONE_STATE`、`READ_PRECISE_PHONE_STATE`、`READ_PRIVILEGED_PHONE_STATE`、`INTERACT_ACROSS_USERS`、`SUBSTITUTE_NOTIFICATION_APP_NAME`、`WRITE_SECURE_SETTINGS`。
- JNI：APK 本身不含 `.so`。`libimscamera_jni.so`、`libimsmedia_jni.so` 由樹裡其他模組安裝在 `system_ext/lib64`，並以符號連結放到 `/system_ext/priv-app/ims/lib/arm64/`（`vendor/sony/yoshino-common/Android.bp` 第 17695、17702 行的 `installed_location`）。手機上實際可見 `/system_ext/priv-app/ims/lib/arm64/` 底下這兩個檔案。**新模組必須保留這個安裝佈局**（`/system_ext/priv-app/ims/ims.apk` 加上同目錄 `lib/arm64/` 兩個符號連結），否則視訊通話的 JNI 會載入失敗。

---

## 4. 編譯依賴（已查證位置）

| 依賴 | 位置 / 模組 |
|---|---|
| `qti-telephony-utils`（`org.codeaurora.telephony.utils.*`，被引用 38 次） | `~/lineageos/vendor/codeaurora/telephony/qti-utils/Android.bp`，`java_library` 名稱 `qti-telephony-utils` |
| `qti-telephony-hidl-wrapper` | `~/lineageos/vendor/codeaurora/telephony/qti-hidl-wrapper/Android.bp` |
| `ims-ext-common` | `~/lineageos/vendor/codeaurora/telephony/ims/ims-ext-common/Android.bp` |
| 隱藏 API（`android.os.HwBinder`、`HwBlob`、`HwParcel`、`HidlSupport`、`NativeHandle`、`IHwBinder`、`android.hidl.base`、`com.android.internal.*`、`android.telephony.ims.*`） | 需要 `platform_apis: true`（框架 jar 在 `out/soong/.intermediates/frameworks/base/framework-minus-apex/android_common/combined/framework.jar`） |
| `vendor.qti.telephony.vt`（被引用 1 次） | **未查到來源，需確認是否在 APK 內自帶或是缺依賴** |
| HIDL `.hal` 原始檔 | **樹裡找不到** `IImsRadio.hal`。因此不能用 `hidl-gen` 重新生成，**直接沿用 JADX 反編譯出的 `vendor/qti/hardware/radio/ims/V1_*` Java**（它們在原 APK 內就是已編譯好的類別） |

手機上這三個 uses-library 的實際檔案：`/system_ext/framework/qti-telephony-utils.jar`、`qti-telephony-hidl-wrapper.jar`（`ims-ext-common` 的 jar 名稱未在手機 `framework/` 找到，**未驗證**，請確認它是被打包成別的名字還是 static_libs）。

資源：`ims_java/resources/res/` 有 `drawable`、`drawable-xhdpi`（`ims_state.png`、`volte_icon` 實際是 PNG，90×28）、`values`（`bools.xml`、`drawables.xml`、`public.xml`、`strings.xml`）與數個語系 `values-*`。Java 內以 `org.codeaurora.ims.R` 引用（只有 3 個檔案 import）。

---

## 5. 工作步驟

### Phase 0：確認環境
1. 確認沒有其他編譯在跑（見 §0）。
2. 確認基準：用 `~/lineageos/out/target/product/poplar/` 目前的狀態不要動；所有新增物放在新目錄，不改現有檔案（除了最後把 `ims` 模組換掉，見 Phase 4）。
3. 備份手機上的 `ims.apk`：
   ```bash
   A="/mnt/f/Android/platform-tools/adb.exe -s BH90018Q63"
   $A root; $A pull /system_ext/priv-app/ims/ims.apk /home/h/tmp/SemcCameraUI/.tmp/imsapk/ims.apk.device_backup
   ```

### Phase 1：建立原始碼專案（新目錄）
建議位置（可調整，但請不要放進 `proprietary/`）：`~/lineageos/vendor/sony/yoshino-common/ims-src/`
```
ims-src/
  Android.bp
  AndroidManifest.xml          ← 複製 ims_java/resources/AndroidManifest.xml
  res/                         ← 複製 ims_java/resources/res/
  src/                         ← 複製 ims_java/sources/ 的內容（org/、com/、vendor/、android/）
```
- 若 `src/android/hidl/base/` 這 2 個檔案與框架內的 `android.hidl.base` 衝突，改成從 `srcs` 排除，改用框架提供的版本（**未驗證**，先試編譯看錯誤）。
- 資源注意：JADX 解出的 `res/` 可能與原資源 ID 不同，這是正常的（Soong 會重新指派），只要 Java 內以名稱引用即可。

### Phase 2：寫 `Android.bp`
參考專案裡已有的類似做法：app-scan3d 的 Soong 移植（見記憶 `project_app_scan3d_soong_port.md`，需把遞移依賴攤平、`assets`/`asset_dirs` 等）。起點：

```
android_app {
    name: "ImsFromSource",          // 不要叫 "ims"，避免與 android_app_import 同名衝突
    stem: "ims",                    // 安裝成 ims.apk
    owner: "sony",
    srcs: ["src/**/*.java"],
    manifest: "AndroidManifest.xml",
    resource_dirs: ["res"],
    platform_apis: true,
    certificate: "platform",
    privileged: true,
    system_ext_specific: true,
    dex_preopt: { enabled: false },
    optimize: { enabled: false },   // 原 APK 未經 R8/ProGuard，保持一致
    libs: ["qti-telephony-utils", "qti-telephony-hidl-wrapper", "ims-ext-common"],
    required: ["qti_telephony_utils.xml", "qti_telephony_hidl_wrapper.xml", "ims_ext_common.xml"],
}
```
- `uses-library` 在 manifest 內已宣告；Soong 可能要求以 `uses_libs` 對應，視錯誤調整。
- 保留 `/system_ext/priv-app/ims/lib/arm64/` 的 JNI 符號連結規則（見 §3），確認它們不依賴舊的 `android_app_import` 模組名稱。

### Phase 3：修編譯錯誤（預期工作量最大的一步）
1. 先單獨 `mka ImsFromSource`，依錯誤逐一處理：缺依賴、隱藏 API、JADX 產生的不合法 Java（常見：變數名稱衝突、泛型推論、`switch` 還原錯誤、巢狀類別存取）。
2. **必須手動處理的已知問題**：
   - `org/codeaurora/ims/ImsServiceClassTracker.java` 的 `handleCalls(ArrayList)`：JADX 完全沒反編譯出來，原始碼是
     `throw new UnsupportedOperationException("Method not decompiled: org.codeaurora.ims.ImsServiceClassTracker.handleCalls(...)")`（第 233 行附近，另有警告在第 214–220 行）。**依 smali 手寫還原**：
     `/home/h/tmp/SemcCameraUI/.tmp/imsapk/ims_smali/smali/org/codeaurora/ims/ImsServiceClassTracker.smali` 第 2053 行 `.method public handleCalls(Ljava/util/ArrayList;)V`。這是通話狀態處理的核心，**務必逐段比對 smali，不要靠猜**。
   - 其他 JADX 警告（逐一確認行為沒變）：
     - `ImsServiceSub.java:1292`（Code duplicated）
     - `ImsService.java:30`（Multi-variable type inference failed）
     - `ImsCallSessionImpl.java:2190`（Type inference failed，匿名類別 `ImsCallSessionImpl$2`）
     - `com/qualcomm/ims/vt/CameraController.java:223`、`CameraManager.java:22`
3. 每修一處，註解標明「由 JADX 反編譯修正」與原因；完成後清掉除錯用的註解與 log（見 `feedback_clean_debug_instrumentation.md`：最終只保留原本就有的 log 輸出）。

### Phase 4：驗證編譯結果與原版一致（不上手機）
依記憶 `feedback_jadx_decompile_verify_methodology.md` 的方法論（jadx 反編譯 → 修編譯 → dex/smali 比對）：
1. 把新編出的 APK 的 `classes.dex` 用 baksmali 反組譯，與原 APK 的 smali（`ims_smali/`）逐類別比對：**類別清單、方法清單、欄位清單必須一致**；方法本體差異要逐一解釋（編譯器產生的合成方法可忽略）。
2. 重點比對：`ImsServiceStateReceiver`（圖示邏輯）、`ImsServiceClassTracker`、`ImsSenderRxr`（HIDL 收發）、`ImsServiceSub`、`ImsCallSessionImpl`。
3. 比對 manifest：用 `aapt2 dump xmltree` 或 `aapt2 dump badging`，與原 APK 逐項核對（§3 的所有屬性、服務、權限、`uses-library`）。
   `aapt2` 路徑：`~/lineageos/out/host/linux-x86/bin/aapt2`。

### Phase 5：換掉原模組並上機驗證
1. 讓產品改安裝新模組：先用 `grep -n "ims" ~/lineageos/vendor/sony/yoshino-common/yoshino-common-vendor.mk` 找出目前 `ims` 這個 `android_app_import` 是在哪裡被列入 `PRODUCT_PACKAGES`（該檔由 `setup-makefiles.py` 自動生成，我沒有確認列在哪一行）。改成安裝 `ImsFromSource`，並確保**不會同時安裝兩份**。**不要手動改被 `setup-makefiles.py` 自動生成的檔案而不留說明**；若要改，請在文件末尾記錄改了什麼。
2. 先做單機驗證（不經完整映像）：
   ```bash
   A="/mnt/f/Android/platform-tools/adb.exe -s BH90018Q63"
   $A root && $A remount          # /vendor 與 /system_ext 需可寫；若失敗，先確認是否要 disable-verity
   $A push <新 ims.apk> /system_ext/priv-app/ims/ims.apk
   $A shell 'chmod 644 /system_ext/priv-app/ims/ims.apk; restorecon /system_ext/priv-app/ims/ims.apk; sync'
   $A reboot
   ```
   - 推之前確認目前 `ls -lZ` 的所有者、SELinux 標籤，推完要一致。
   - 若出現安裝/簽章問題，優先看 `logcat | grep -E "PackageManager|ims"`。
3. **VoLTE 驗證流程（很重要，順序不能亂）**：
   - 必須是「**乾淨重開機後讓第一次附著自然發生**」。**不要**在開機後才切 VoLTE 開關，也不要中途重啟 phone 程序，否則會落入「中途重新註冊」的已知狀況（MmTel `Voice: false`、`imsrcsd` 當機），那不是新 APK 的問題。
   - 重開機後等 1–2 分鐘，確認：
     ```bash
     $A shell 'getprop gsm.operator.numeric'                                   # 46692
     $A shell 'logcat -d -b all | grep "MmTel Capabilities" | tail -1'          # 要有 Voice: true
     $A shell 'ip -o link | grep "rmnet_data[0-9]:" | grep -c "UP,LOWER_UP"'    # 3（含 IMS 承載 rmnet_data2）
     $A shell 'logcat -d -b all | grep "ImsRegCallbackHelper: updateRegistrationState" | tail -2'  # REGISTERED
     $A shell 'logcat -d -b all | grep -E "shallShowHDIcon config|updateHDIcon" | tail -3'        # showHDIcon: true、show HD Icon: true
     ```
   - 狀態列左側要出現「VOLTE」徽章（桌面看得到，鎖定畫面不顯示）。
   - **請使用者實際撥一通電話**確認 VoLTE 通話可通、不退回 3G（你不能代替使用者驗證通話）。
4. 若失敗：先還原備份（`ims.apk.device_backup`）並重開機，恢復到可用狀態，再回頭查。

---

## 6. 重新產生反編譯輸出的方法（若需要重做）

REA 沒有「整包輸出」指令，改直接呼叫它所用的 JADX 核心：

```bash
cd /home/h/tmp/SemcCameraUI/.tmp
java -Xmx6g -cp /home/h/tools/jadx-headless-mcp/jadx-headless-mcp-0.7.1-all.jar \
     rea_tools/Dec.java imsapk/ims.apk imsapk/ims_java
# 結果：classes=273 errors=0 warnings=4（約 4 秒）
```
`Dec.java` 只是呼叫 `JadxArgs` / `JadxDecompiler` 並 `save()`。

REA 逐方法反編譯（MCP 工具 `mcp__rea__inspect_android_method`、`inspect_android_class`、`search_android_classes`）可用來核對單一方法。使用前請先重啟 Claude Code，讓 MCP 載入；REA 的設定已完成（`~/.claude.json` 的 `mcpServers.rea`，含 `REA_JADX_MCP_JAR`、`PATH`、`TMPDIR` 環境變數）。

---

## 7. 驗收標準

1. `mka ImsFromSource`（或你取的名稱）編譯成功，沒有出現 `environment variables changed value`。
2. 新 APK 與原版的 **類別、方法、欄位清單一致**；manifest 全項核對一致；`handleCalls` 已依 smali 手寫還原且經逐段比對。
3. 安裝到 G8342 後，**乾淨重開機**：SIM 載入、LTE 註冊、`MmTel Voice: true`、IMS REGISTERED、`rmnet_data2` UP、狀態列出現 VOLTE 徽章，`imsrcsd` 無新的當機（`logcat -b all | grep -c "Fatal signal.*imsrcsd"` 為 0）。
4. 使用者實測 VoLTE 通話可通、不退回 3G。
5. 備份可還原；`.tmp/` 以外沒有留下暫存檔；未擅自 commit。
6. 在本文件末尾追加「執行紀錄」：做了什麼、遇到什麼問題、哪些項目仍是推論。

---

## 8. 後續（不在本任務範圍，僅供參考）

重編成功後，才進行功能修改。目標是把 `ImsServiceStateReceiver.showHDIcon(boolean)`（約 30 行有效程式，負責建立通知頻道 `ims_services_channel_<phoneId>` 並發出通知）改成呼叫隱藏 API `StatusBarManager.setIcon(slot, iconId, level, desc)` / `removeIcon(slot)`，讓圖示成為狀態列槽位圖示（而不是通知）。需要：
- 在 `telephony_system-ext_privapp-permissions-qti.xml` 為 `org.codeaurora.ims` 加入 `android.permission.STATUS_BAR`，並在 manifest 宣告；
- 以覆蓋 `config_statusBarIcons` 在 `mobile` 旁插入新槽位（例如 `volte`）；
- 圖示開關仍由 carrier config 的 `config_update_service_status`、`config_update_volte_icon` 控制（中華電信區塊已有，位於 `device/sony/yoshino-common/overlay/packages/apps/CarrierConfig/res/xml/vendor.xml` 第 12453–12454 行，工作目錄未提交）。
- 注意：圖示若落在槽位清單最末端，位置不一定靠近訊號圖示，需實測。

---

## 9. 已知事實與限制（避免重複踩坑）

- **FP3 的 IMS 堆疊與 Sony modem 的搭配**：乾淨開機流程可通；中途重新註冊會失敗（`Voice: false`），這是既有行為，不是本任務要修的。
- `imsrcsd` 會讀 `persist.rcs.supported`；設成 0 會讓整個 `imsrcsd` 自己結束（連 VoLTE 用到的部分一起沒了），**不要用這個方式關 RCS**。
- carrier config 有「每張 SIM 的快取」：`/data/user_de/0/com.android.phone/files/carrierconfig-com.android.carrierconfig-<iccid>-<id>.xml`。換了 CarrierConfig 的覆蓋包後，需刪掉快取檔再重啟（或重開機）才會載入新值。
- 不要用 `pkill -f <字串>` 殺程序，若字串出現在自己的指令列會把自己的 shell 也殺掉。
- 相關記憶檔（在 `/home/h/.claude/projects/-home-h-tmp-SemcCameraUI/memory/`）：`project_g8342_a15_volte_fsg_modemst.md`（完整調查紀錄）、`reference_rea_reverse_engineering_tool.md`、`feedback_jadx_decompile_verify_methodology.md`、`project_app_scan3d_soong_port.md`、`feedback_always_export_ccache_before_aosp_build.md`、`feedback_state_expected_duration.md`。

---

## 10. 尚未驗證的項目（接手前請先確認）

1. JADX 輸出能否通過編譯：預期會有若干處需要修（除了 `handleCalls`）。
2. `vendor.qti.telephony.vt` 的來源。
3. `ims-ext-common` 在手機上的實際 jar 名稱與 `uses-library` 對應。
4. `android/hidl/base` 兩個檔案是否與框架衝突。
5. `platform_apis: true` 下，`android:usesNonSdkApi`、`protected-broadcast` 等 manifest 項目能否原樣通過。
6. 重編後的 APK 在簽章後，與樹內 `android_app_import` 的行為是否在 `dexpreopt`/`extractNativeLibs` 上有差異。
7. 圖示的最終位置（§8）。

---

## 執行紀錄（2026-10-14，由本次 session 的 Claude 直接執行）

### 已完成
- 新增 `~/lineageos/vendor/sony/yoshino-common/ims-src/`（未提交）：`Android.bp`、`AndroidManifest.xml`、`res/`、`src/`（JADX 輸出，已移除 `android/hidl/base`，因 `qti-telephony-hidl-wrapper` 已靜態包含）。
- `Android.bp`：`ImsFromSource`（`android_app`）＋ 編譯期專用的 `ims-ext-common-fp3-compat`；`mka ImsFromSource` 約 30 秒～數分鐘。
- **重要發現（ext-common 版本不符）**：原 APK 是對 FP3 版 `ims-ext-common` 編的（`*Base.<init>()V` 無參數建構子、`QtiCallConstants.EXTRA_CALL_COMPOSER_TOKEN` / `_CALL_ENDED` 欄位、`ImsMultiIdentityControllerBase.queryVirtualLineInfo` 為 `public ... throws RemoteException`），樹內是新版 CAF 15.0。用 `compat/` 內 5 個覆蓋類別補齊，只在編譯期使用（`installable: false`），執行期仍是樹內的 ext-common。這也代表**原版 FP3 APK 在樹內 ext-common 上本來就有潛在的 NoSuchMethod/NoSuchField 風險**（目前未被觸發）。
- `uses_libs` 必須明確列出順序 `qti-telephony-hidl-wrapper, qti-telephony-utils, ims-ext-common`，否則 manifest_check 因順序不符失敗。
- `stem: "ims"` 會與 `android_app_import` 的 `ims` 在 Make 層名稱衝突（`MODULE.TARGET.APPS.ims already defined`），目前未使用 stem，輸出為 `ImsFromSource.apk`；最終要取代原模組時需先移除/改名 `android_app_import`。

### JADX 還原錯誤（javac 編得過、但行為錯，必須手修；依 smali 修正，原始碼內有「由 JADX 反編譯修正」註解）
1. `ImsServiceClassTracker.handleCalls`：JADX 完全未還原，依 smali 手寫。
2. `ImsVideoGlobals.init`：缺 `return`，**一律丟 `Default subscription is null`**（上機實測造成 ImsService 當機 → RescueParty 自動重開）。
3. `ImsSubController.updateActiveImsStackForPhoneId`：被還原成**無窮迴圈**。
4. `ImsUtImpl$ImsUtImplHandler`（CF 查詢）：`while` 內無條件 `break`，只處理第一筆。
5. `ImsSenderRxr.dial` / `sendGeolocationInfo` / `suppSvcStatusInternal`：JADX 漏掉共用的 `catch(Exception) { removeFromQueueAndSendResponse; Log.e }`。
6. `ImsConfigImpl.sendRequest`（`try/catch/finally { return }`）、`ImsSenderRxr$ImsRadioHandler.handleMessage`（補回 `check-cast`）、`CallDetails.addExtra`、`Log.secureHash`（try 範圍）。
7. 其餘：`Camera2` 的 `throws`、`CameraController.setPreviewSurface` 的 try 範圍、合成 lambda（`this.f$0` → `Outer.this`）、`CallComposerInfo` 型別歧義（`org.codeaurora.ims` vs `V1_6`）、`WakeLockRegistrant` 的 `super()` 順序、不可達的 `return`。

### 驗證方法（建議沿用）
- `dexdump -d` 後用 `.tmp/rea_tools/cmp_cfg.py orig.dump orig.dex new.dump new.dex [筆數] [過濾]` 比對每個方法的「事件先後邊集合」（呼叫/寫欄位/new/return/throw/monitor），能抓到缺 `return`、迴圈、`break`、try 範圍錯誤；附 `... anon` 模式比對匿名類別。`cmp_methods.py`/`cmp2.py`（呼叫計數）**抓不到**流程錯誤，不可單獨依賴。
- 剩餘已知良性差異：enum `$values()`、建構子欄位賦值順序、synchronized/finally 的 monitor 展開、`$$Nest$` 存取器、lambda 類別改為匿名類別、常數折疊、HIDL `hashCode` 宿主類別。
- manifest（`aapt2 dump xmltree`）全項一致，僅 `minSdkVersion` 33→35、compileSdk 33→35（平台建置改寫）；資源 ID 與原版相同。

### 上機驗證（G8342）
- 第一次推送（含 `init` 錯誤）→ 開機後 ImsService 當機迴圈 → RescueParty 重開；已還原原版 APK（備份：`.tmp/imsapk/ims.apk.device_backup`，SHA-256 `565256be…`），VoLTE 恢復。
- 修正後第二次推送：先設定 `persist.sys.disable_rescue true` 再推送。結果見下方「重開機穩定性」。

### 重開機穩定性（重編版 APK，SHA-256 `63482126…`，G8342，VoLTE 開關開著）
- 推送後第一次開機：**未註冊**（`Status 1`、`Voice: false`、`rmnet_data` 只有 2 條，0 FATAL、imsrcsd 無當機），原因未查明（懷疑是首次附著競態或「APK 剛更換後的第一次開機」，未做對照）。
- 之後連續 4 次開機（含 3 次自動循環 `.tmp/reboot_cycles.sh`，結果 `.tmp/reboot_cycles.log`）：全部 `REGISTRATION_STATE_REGISTERED`、`MmTel Voice: true`、`rmnet_data` 3 條 UP、`updateHDIcon … show HD Icon: true`、0 FATAL、`imsrcsd` 0 次當機；IMS App 通知（`ims_services_channel_0`、`volte_icon`）有發出。
- IMS App 啟動日誌訊息集合與原版成功開機（`boot_logcat4`）一致，僅有事件相關差異（地理位置請求、WFC 狀態行，原版各次開機也不固定出現）。
- **尚未驗證**：實際撥打 VoLTE 通話（需使用者）；解鎖後桌面狀態列的 VOLTE 徽章（鎖定畫面不顯示）；視訊通話（JNI）路徑。
- 目前裝置上安裝的是重編版；還原方式：`adb root; adb remount; adb push .tmp/imsapk/ims.apk.device_backup /system_ext/priv-app/ims/ims.apk; adb shell restorecon /system_ext/priv-app/ims/ims.apk; adb reboot`。
- `persist.sys.disable_rescue` 已改回 false。

### 尚未做（Phase 5 其餘）
- 沒有把 `ImsFromSource` 正式接進產品（`yoshino-common-vendor.mk` 第 829 行的 `ims \` 仍指向 `android_app_import`），也沒有 commit；`ims-src/` 目前是未追蹤的新目錄。接進產品前要先處理 `stem`/模組名稱衝突，且需確認 `android_app_import ims` 與新模組不會同時安裝。

### 注意事項
- 推送 `/system_ext/priv-app/ims/ims.apk` 前必須先備份；`adb root` 在每次重開機後失效；`/system_ext` 在可寫的根目錄上（`adb remount` 的 overlayfs 訊息可忽略）。
- 試驗新 APK 時先 `setprop persist.sys.disable_rescue true`，避免當機迴圈升級（測完請改回 false）。
- 日誌環形緩衝只有 256 KiB，早期啟動日誌會被蓋掉；需要對照時用 `.tmp/boot_logcat_g8342.sh` 串流（開機前啟動）。
