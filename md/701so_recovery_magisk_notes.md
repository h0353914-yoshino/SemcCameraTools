# 701SO（XZ1 / poplar）recovery、Fox 與 Magisk 操作筆記

最後更新：2026-10-17。適用機型：701SO（BH904YZF9A，XZ1 poplar 系列，非 A/B 分區）。

## 1. Recovery 分區

- XZ1 有獨立的 recovery 分區。
- 分區名稱不一定會出現在 `/dev/block/by-name` 或 sysfs 的 PARTNAME 列表裡，但 `fastboot flash recovery` 指令可用。
- 裝置為非 A/B（`ro.boot.slot_suffix` 為空），所以不需要指定 slot。

**更正**：2026-10-17 我先前用 sysfs PARTNAME 列表判定「沒有獨立 recovery 分區」，並據此推論 Fox 放在 boot 分區，這個判斷是錯的。以使用者提供的資訊為準：recovery 分區存在，只是名稱沒有列出。

## 2. Fox 內安裝 Magisk

- 在 Fox 可以直接安裝 Magisk，不需要先另外刷入或修補原廠 boot.img。
- 操作（2026-10-17 實測成功）：
  1. `adb -s BH904YZF9A push Magisk-v30.7.zip /sdcard/Magisk-v30.7.zip`
  2. `adb -s BH904YZF9A shell 'twrp install /sdcard/Magisk-v30.7.zip'`
- 安裝器輸出 `Done`，中間會顯示 `Stock boot image detected`（代表 Magisk 判定目前 boot 未被修補）與 `Unable to find preinit dir`（提示，未影響結果）。
- 安裝後驗證：
  - 重開機後 `sys.boot_completed=1`，`ro.build.fingerprint` 為 `Sony/701SO/701SO:9/47.2.D.1.150/1632724448:user/release-keys`。
  - `adb shell su -c id` 回傳 `uid=0(root)`，context `u:r:magisk:s0`。
  - `su -v` 為 `30.7:MAGISKSU`，`magisk -V` 為 `30700`。

## 3. 本次操作的備份與讀取檔

| 檔案 | 內容 |
|---|---|
| `.tmp/701so_boot_now_read.img` | 安裝 Magisk 前讀取的 boot 分區（sda38，64MB，當時在 Fox 中讀取） |
| `.tmp/701so_boot_after_magisk.img` | Magisk 安裝後讀取的 boot 分區 |
| `.tmp/701so_boot_now2.img` | 重開機進系統後讀取的 boot 分區（仍含 magisk 與 init.recovery） |

- boot 分區大小 67108864 bytes（64MB），與分區大小相符。
- 在 `.tmp` 裡可以比對 `cmp` 還原前後差異。
- 還原 boot（若需要）需要使用者明確同意，寫入動作不可在未同意的情況下執行。

## 4. a15 分支

- a15 預設含 KSU Next（使用者提供的資訊，本次未在裝置上驗證）。
- 701SO 目前走的是 a9 的 Magisk 路線（見第 2 節），和 a15 的 KSU Next 無關。

## 5. 注意事項

- Fox 內 `/data` 本次可讀（`/data/media/0` 可列出，`/sdcard` 已掛載）。先前「`/sdcard` 讀不到、`twrp install` 會失敗」的記錄在本次不成立，需依實際情況判斷。
- 不要用 sideload 刷 701SO（使用者 2026-10-17 指示，見 memory）。
- 寫入 boot、recovery 或其他分區前需要使用者明確同意。
