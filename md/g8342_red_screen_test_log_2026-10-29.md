# G8342（Xperia XZ1 Compact 類，msm8998 / poplar）4.19 紅屏測試總紀錄

- 整理日期：2026-10-29
- 來源：`.tmp/review/REVIEW.md`（第 1 至 28 節）、`.tmp/port/`（映像與 DTB）、`.tmp/cam/`（照片與 MISR 輸出）、先前對話摘要。
- 現象：4.19 基準系統的螢幕只剩紅色單通道。灰階條紋變紅，G、B 整條為黑。4.4 原廠核心正常。

## 1. 結論（目前為止）

- **紅屏根因仍未查出。**
- 已確認不是下列項目造成：
  - 我們的 Sony 修改（標準 4.19 + 我們的 DTB 同樣紅）。
  - IGC（關閉後仍紅，見 test84）。
  - DSPP 的 PCC、PA、PGC、dither、gamut（皆關閉，見第 15 節）。
  - fb 格式、fb pipe 的格式／unpack／stride／fetch 設定（4.4 與 4.19 相同）。
  - cache 一致性（清除 cache 後 CRC 不變）。
  - VBIF 設定（DT 覆寫後兩邊都是 `<0xd0 0x2020>`）。
  - 面板參數、DCS 序列、PCC 係數（逐位元組相同）。
  - PLL handoff、`iommu-earlymap`、`iommu-dma-addr-pool`。
- **已確認的差異**：同一張條紋圖，DSI0 輸出端（MISR block 1）的 CRC 在 4.4 與 4.19 不同（4.19 `0xebc45355`，4.4 `0x27209235`）。差異在 MDP 到 DSI0 之間，但目前的暫存器層級比對沒有找到來源。
- **未完成**：SMP 分配（0x180 區段）、VBIF 本體（0xc9b0000）、SMMU 映射到的實體頁、MDP 內部狀態。另外還有 4.4 的 IGC LUT 內容未讀取。

## 2. 基準與參考映像

| 名稱 | 內容 | 用途 |
|---|---|---|
| test67（flashed，核心 `#76`） | 4.19 我們的核心 + 我們的 DTB | 紅屏基準，已刷入分區 |
| test61 / test81 | 4.4 原廠核心（test81 為 trace 版，可開機） | 4.4 對照 |
| test63_clean | 4.19 乾淨建置 | 比對用 |
| test72 | 標準 4.19（ederevx `msm8998`，關閉 Sony 選項）+ 我們的 DTB | 證明紅屏不是 Sony 修改造成 |

## 3. 測試總表（依時間順序，含 REVIEW 章節）

| # | 章節 | 改動 | 結果 | 判定 | 證據 |
|---|---|---|---|---|---|
| 1 | §1 | 靜態程式碼審查（4.4 與 4.19 顯示路徑語意 diff） | 找到多處差異（PLL、SMMU、SKIP_CPU_SYNC、HS/LP 時脈、TE 中斷、EARLY_MAP 等） | 候選清單，需實機驗證 | `review/REVIEW.md` §1–§5 |
| 2 | §6 | 比對標準 4.19 與我們的樹 | 差異來自 Sony 修改；gamut 64 位元截斷為真實回歸（潛伏，未啟用），`enable_gate` 預設亦是 | 不是紅屏原因 | §6 |
| 3 | §7 | test72：標準 4.19 + 我們的 DTB | 紅色單通道鎖定畫面 | 紅屏不是 Sony 修改造成 | `port/test72_std419.img`、`cam/p_std419_boot_s.png` |
| 4 | §8, §10 | test73：標準 4.19 + 4.4 stock DTB | 卡在 SONY 開機畫面 | 4.4 DTB 無法在標準 4.19 開機 | `port/test73_std419_44dtb.img` |
| 5 | §8, §10 | test74：我們的 DTB，MDP `interrupts` 改為 `<0x0 0x53 0x0>` | 卡在 SONY 開機畫面（超過約 6 分鐘） | MDP 中斷需 level-high（0x4） | `port/test74_std419_irq0.img`、`cam/p_irq0_boot2_s.png` |
| 6 | §10 | test75：我們的 DTB，移除 `qcom,iommu-earlymap` | 紅色鎖定畫面 | 不是紅屏原因 | `port/test75_std419_noearly.img`、`cam/p_noearly_boot_s.png` |
| 7 | §10 | test76：我們的 DTB，移除 MDSS SMMU `qcom,iommu-dma-addr-pool` | 紅色鎖定畫面 | 不是紅屏原因 | `port/test76_std419_nopool.img`、`cam/p_nopool_boot_s.png` |
| 8 | §13 | test77：標準 4.19 不設定 `handoff_resources` | 紅色鎖定畫面 | PLL handoff 不是紅屏原因 | `port/test77_std419_nohandoff.img`、`cam/p_nohandoff_boot_s.png` |
| 9 | §12 | 4.4 與 4.19 PLL 初始化表逐行比對 | 只差 `PLL_INT_GAIN_IFILT_BAND_1`（0x82 vs 0xfa）；4.19 改 0x82 仍紅 | 增益不是主因 | §12 |
| 10 | §14 | test78：build-time 強制關閉 IGC（`opmode & ~BIT(0)`，在 `mdss_mdp_pp.c:2586`） | 兩次開機都卡在 SONY | 無法判斷，開機即卡住 | `port/test78_std419_noigc.img`、`cam/p_noigc_v2_s.png`、`cam/p_noigc_v3_s.png` |
| 11 | §9 | DSI PLL VCO 讀值 | `dsi0pll_vco_clk` = 1.798 GHz，理論約 1.794 GHz（差約 0.2%） | 數值合理，間接推算 | §9 |
| 12 | §15 | test67 即時 DSPP 暫存器 | DSPP0 OP_MODE = `0x1`（只有 IGC），DSPP1 = 0，`enable_gate` = 0 | 目前唯一生效的後處理是 IGC | §15 |
| 13 | §16 | 4.19 IGC LUT dump（zz_dumpigc，較早的建置） | R、G、B 三組 256 筆逐筆相同，為完整斜坡 | G、B 表不是全零 | `cam/igc_419.txt` |
| 14 | §17 | 4.4 與 4.19 的 `mdss_panel_fb0` 完整 dump | 逐位元組相同（PHY、lanecfg、strength、TE、porch、clock、on/off 指令） | 面板與 PHY 參數不是原因 | `review/panelinfo_k44.txt`、`review/panelinfo_k419.txt` |
| 15 | §18 | DSI 命令與 kickoff 追蹤（test79） | 開機只有 5 筆 DCS，之後純像素；PCC 係數相同但只計算、未寫入 | 命令序列與 PCC 不是原因 | §18 |
| 16 | §19 | 4.4（test81）與 4.19（test79）逐筆 DCS 比對 | DCS 序列完全相同 | 命令內容不是原因 | §19 |
| 17 | §20–§21 | 幀率量測（第 19 節的 58.9 Hz 與 51.2 Hz） | 相同負載下只差 1–2% | 幀率差異是量測條件造成，不成立 | §20、§21 |
| 18 | §22 | test82：標準 4.19 + 4.4 DTB，MDP 中斷 `<0x0 0x53 0x4>` | 卡在 SONY 開機畫面（兩次嘗試皆無 adb） | 無法判斷紅屏；4.4 DTB 無法在標準核心開機 | `port/test82_std419_d44irq4.img` |
| 19 | §23 | MISR 基準（test67，DSI0 block 1，BM 模式，條紋圖，開機後第一次呼叫） | CRC `0xebc45355`（多次重現） | MISR 可用的起點 | `cam/misr4.c`、`cam/misr5_b1` |
| 20 | §24 | 同一張圖在 4.4（test81）第一次呼叫 | CRC `0x27209235`（三次獨立開機重現） | 4.4 與 4.19 的 DSI0 輸出不同 | §24、§25 |
| 21 | §25 | 4.19 上清 DSPP OP_MODE（無效，驅動 commit 時寫回 0x1） | CRC 不變 | 無效測試，不能排除 IGC | §25 |
| 22 | §25 | 清除 4.4 殘留 LM0 blend stage | 4.4 CRC 仍為 `0x27209235` | 殘留圖層不是差異來源 | §25 |
| 23 | §26 | test83：IGC 關閉的第一版（只改 `if`，無效，OP_MODE 仍 0x1） | CRC `0xebc45355`（與基準相同） | 無效測試 | `port/test83_igcoff.img` |
| 24 | §26 | test84：IGC 真正關閉（DSPP0 OP_MODE 讀回 0x0） | CRC `0x5a3c8d72`；SO-01K 拍照：仍紅，藍綠為黑，灰階變紅 | IGC 會改變 DSI0 輸出，但不是紅屏原因 | `port/test84_igcclr.img`、`cam/so_screen.png` |
| 25 | §27 | 4.19 fb 第二頁做 DC CIVAC 後 pan | CRC 仍為 `0xebc45355` | MDP 讀到的就是 CPU 寫入的內容，cache 不是原因 | §27 |
| 26 | §27 | fb pipe（DMA0）、VBIF、DT vbif-settings 比對 | 兩邊 format/unpack/stride/fetch 相同；VBIF 經 DT 覆寫後相同 | 不是原因（VBIF 本體與 SMP 未讀） | §27、`cam/mdp_live419.txt`、`cam/mdp_live44.txt` |
| 27 | §28 | 開機後轉圈（非紅屏問題） | NFC 模組 `pn553.ko` 因 `module_layout` 不符無法載入，NFC HAL 不啟動 | 與紅屏無關，但會拖慢或卡住開機 | §28 |

## 4. 已排除項（彙整）

以下項目在先前紀錄（plan 檔與摘要）中已有驗證，REVIEW.md 未逐條重列：

- SurfaceFlinger、GPU、UBWC：直接寫 fb0（停 SF）仍紅；SF 截圖與 4.4 逐像素相同。
- 通道對應：R、G、B、灰階全範圍漸層測試。R 正常，G、B 整條黑，灰階變紅。
- MDP 暫存器範圍（TOP、CTL、SSPP、LM、DSPP、INTF、PP、DSC）與 DT 列出的範圍；fb pipe 設定；MDP 時脈與頻寬。
- DSI 控制器 0x000–0x1ff、PHY 與 PLL 0x000–0x7bf；clamp；色彩順序與 dst_format。
- 電源：LAB、IBB、ps-threshold（改回 70 仍紅）、各路 regulator、DCDC、reset、TE、觸控 GPIO、上下電時序。
- 面板：三個面板節點 DT 與原廠一致；DCS 0x00–0xFF 未解鎖讀取一致，含 0x05 錯誤計數 = 0；0x0F 診斷一致；0x3A COLMOD = 0x77（24 bpp）。
- 其他：強制關閉 splash（無效測試）、觸控 clearpad 解除綁定。
- DT：MDP 節點、DSI lane strength、lane-config、GPU bank bit。
- 我們的 commit 的其他回歸：`enable_gate` 預設（執行期切換無影響）、gamut 64 位元截斷（潛伏，未啟用）。

## 5. 未完成與未排除

1. **SMP 分配**：MDP 低段暫存器（0x180 區段）不在 debugfs 允許的範圍內（`mdss_debug_base_is_valid_range` 只接受 DT `regs-dump-mdp`，起點 0x1000）。要讀得改 DT 範圍後重編 dtb。
2. **VBIF 本體**（0xc9b0000）：不在 mdp debugfs 映射範圍內。
3. **SMMU 映射**：MDP 的 iova（4.19 為 `0xfc5f8000`，4.4 為 `0x03618000`）對應到的實體頁尚未驗證。
4. **4.4 的 IGC LUT**：未讀取。4.19 的 identity 已確認，但 IGC 關閉後 DSI0 CRC 改變，表示兩邊的 IGC 行為不同。
5. **DSI0 CRC 差異來源**：差異位於 MDP 到 DSI0 之間，但目前已比對的暫存器（fb pipe、LM、DSPP、CTL、INTF、DSI 控制器）都相同。
6. **面板未解鎖暫存器**（B0 04 解鎖後的 C1、C2、C6、D6 等）：尚未比對 4.4 與 4.19。這是 REVIEW 先前列為「方法 3」的項目。

## 6. 注意與陷阱（重要）

- **MISR 只有每次開機後的第一次呼叫可信**。同一開機內第二次以後的呼叫會回 0（4.4 與 4.19 都觀察到）。第 24 節的 `0xebc45355` 早期紀錄是第二次以後得到的，第 25 節起才改用第一次結果。
- **MISR enum**：`MISR_OP_NONE=0, SFM=1, MFM=2, BM=3`。早期 SFM/MFM 的 -110 與 -524 錯誤來自 op 值錯位，不是硬體問題。
- **`dmesg -c` 會清空 kernel log**：我在測試中多次使用，因此早期的 `init.nfc_insmod` 等訊息已無法回溯。
- **debugfs `reg` 讀取的偏移**：必須落在 DT `regs-dump-mdp` 範圍內，否則 `off` 寫入會被拒絕，讀到的是預設區段，標籤也會對不上。
- **IGC 關閉的正確做法**：在 `mdss_mdp_pp.c` 的 DSPP OP_MODE 寫入前清 `IGC_LUT_EN`（`pp_dspp_setup`，約 2592 行）。只改設定 IGC 的 `if`（約 2319 行）無效，因為位元會從硬體既有值保留。運行期寫 OP_MODE 會被驅動 commit 覆寫。
- **第 14 節的結論需修正**：第 14 節（test78）指出「IGC 強制關閉會讓標準 4.19 開機卡住」。但 test84 是用正確的清除方式、在我們的樹上做的，它能開機，仍紅。兩者的編輯不同，不應該直接推論到同一個結論。
- **4.4 DTB 在標準 4.19 上無法開機**（test73、test74、test78、test82）：原因之一是 MDP 中斷 flags，但其他 DT 差異尚未逐項替換，所以無法用「4.4 DTB 二分」來定位紅屏。
- 照片中，SO-01K 的即時取景可以直接看到 G8342 螢幕，比截圖更能反映面板實際輸出。

## 7. 與開機相關的新問題（不是紅屏）

- 現象：重開後開機動畫持續播放，約 5 分鐘後才到鎖定畫面。
- 原因：`init.nfc_insmod.sh` 判定 chip 為 NXP PN553，`modprobe pn553.ko` 失敗，錯誤為 `disagrees about version of symbol module_layout`（Exec format error）。因此 `vendor.nfc.nxp.ready` 未設定，NFC HAL 不啟動，`com.android.nfc` 每秒等待一次。
- 狀態：模組與目前 4.19 核心不相容，尚未修正。
- 選項：重編 `pn553.ko` 對應目前核心的 modversions，或暫時停用 NFC。

## 8. 證據檔位置

- 審查報告：`.tmp/review/REVIEW.md`（第 1–28 節）
- 基準與對照映像：`.tmp/port/test67_noigc3.img`（基準）、`.tmp/port/test61_k44z18.img`、`.tmp/port/test81_k44_trace.img`（4.4）、`.tmp/port/test72_std419.img` 至 `test84_igcclr.img`
- 照片：`.tmp/cam/p_std419_boot_s.png`、`p_irq0_boot2_s.png`、`p_noearly_boot_s.png`、`p_nopool_boot_s.png`、`p_nohandoff_boot_s.png`、`p_noigc_v2_s.png`、`p_noigc_v3_s.png`、`p_test67_now_s.png`、`so_screen.png`
- 暫存器 dump：`.tmp/cam/mdp_live419.txt`、`.tmp/cam/mdp_live44.txt`、`.tmp/cam/igc_419.txt`
- MISR 工具與輸出：`.tmp/cam/misr4.c`、`misr5_b1`、`misr6`、`misr7`（DC CIVAC 版）、`fbvar`、`dm_bm.txt`
- 核心原始碼：`~/lineageos/kernel/sony/msm8998`（4.19，含未提交的 PA dither 修改）

## 9. 建議的下一步（依優先順序）

1. 讀取 4.4 與 4.19 的面板未解鎖暫存器（B0 04 解鎖後的 C1、C2、C6、D6），比對色彩與伽瑪狀態。
2. 擴充 debugfs DT 範圍讀取 SMP（0x180 區段）與 VBIF 狀態，重編 dtb 後對兩邊做 MDP 第一次 MISR 比對。
3. 讀取 4.4 的 IGC LUT 內容，與 4.19 的硬體 LUT 逐筆比對。
4. 先處理 NFC 模組，讓開機不再卡住，再繼續上述測試。

## 10. 依排查規劃執行的結果（2026-10-29 第二輪）

依 `建議排查規劃` 的順序執行。每一步都以 4.4（`test81`/`test85`）與 4.19 成對比較，每次開機只取第一次 MISR。

### 步驟 1：固定基準
- 4.19 基準以還原後的原始碼重建（`test86_419_smp.img`），第一次 MISR 仍為 `0xebc45355`，與先前基準一致，基準可重現。
- 4.4 對照 `test85_k44_smp.img` 第一次 MISR 仍為 `0x27209235`。

### 步驟 2：IGC LUT（已完成，排除）
- 4.4 的 LUT 以 `zz_dumpigc` 讀出（`cam/igc_k44_zz.txt`），4.19 讀值來自先前建置（`cam/igc_419.txt`）。
- 結果：256 筆 R、G、B 全部相同，兩邊都是 0x000 到 0xfff 的 12 位元斜坡。
- 判定：LUT 內容不是差異來源。
- 限制：4.19 的讀值來自較早的除錯建置，尚未用同一個映像重讀。

### 步驟 3：SMP 與 VBIF（部分完成）
- SMP（`regs-dump-mdp` 新增 `0x100–0x240`）：兩邊讀值全為 0（`cam/smp_k44.txt`、`cam/smp_419_run.txt`）。兩邊相同，SMP 暫存器不是差異來源（0 也可能代表未使用，這一點未驗證）。
- VBIF（`vbif_off`/`vbif_reg`，`cam/vbif_419.txt`、`cam/vbif_k44.txt`），有以下差異：
  - RD/WR 限制（0xb0–0xcc）：4.4 全為 0x20；4.19 部分位元組為 0。
  - QoS remapper（0x100、0x104）：4.19 寫入 `76543210`/`00dcba98`，4.4 為 0。
  - 0x124、0x160、0x164、0x170、0x178、0x17c：4.19 有值，4.4 為 0。
  - 0xd0（DDR 最大突發）與 0xac：兩邊的 DT 設定相同，已在前面排除。
- 判定：這些差異來自 4.19 驅動的 QoS 與 outstanding-limit 設定（`mdss_mdp_pipe.c` 1004–1060、2386–2390；`mdss_mdp.c` 2207、2258）。它們影響優先權與頻寬，不會直接移除 G、B 通道，但是 MDP 讀取路徑上的實際差異，需要做 A/B 確認。
- 下一步：在 4.19 上關閉 QoS remapper（`MDSS_QOS_REMAPPER`）或 OT limit，比對 MISR 與照片。

### 步驟 4：SMMU IOVA 與實體頁（未完成）
- debugfs 沒有 SMMU 或 io-pgtable 映射資訊（只有 `dma_buf/bufinfo`，可看到 fb buffer 掛在 `smmu_mdp_unsec_cb`，沒有位址）。
- 需要在驅動中加入唯讀診斷（列出 fb 的 sg 表與 iova），兩邊各需要一次編譯。

### 步驟 5、6、7（未開始）
- 步驟 5（MDP 提交時的完整狀態比對）待步驟 3 的 A/B 結果決定。
- 步驟 6（面板未解鎖暫存器）與步驟 7（NFC 開機延遲）依規劃列為後續支線。

### 本輪結論
- 排除：IGC LUT 內容、SMP 暫存器（兩邊皆為 0）、VBIF 的 DT 設定（0xd0、0xac）。
- 新的候選：4.19 的 VBIF QoS remapper 與 outstanding-limit 設定與 4.4 不同。需要 A/B 驗證，尚未證明與紅屏相關。
- 紅屏根因仍未查出。

## 11. SMMU 診斷前的發現：4.19 fb mmap 會關閉再開啟面板（2026-10-29 第三輪）

### 發現
- 4.19（我們的樹與標準 ederevx 4.19 都有）：`mdss_fb_fbmem_ion_mmap`（`mdss_fb.c` 約 2610 行）每次 mmap fb0 都會呼叫 `mdss_fb_blank_blank(POWER_OFF)` 與 `mdss_fb_blank_unblank()`。
- 4.4：沒有這兩個呼叫（`k44src/.../mdss_fb.c` 中出現次數為 0）。
- 影響：本文件所有 MISR 量測都用 `mmap(fb0)` 寫入條紋圖。在 4.19 上，每次量測都會先把面板關閉再開啟，4.4 則不會。因此 4.19 與 4.4 的 DSI0 CRC 比較，可能混入「面板電源循環」這個變因。

### 排除 mmap 的嘗試
- 試用 `write(fb0)`（`misr8`）：回傳 `-ENODEV`，mdss fb 不支援 write，無法使用。

### 測試（進行中）
- 診斷映像 `test88_nofbcycle.img`：4.19 樹，僅將 mmap 中的 `blank/unblank` 包進 `if (0)`，其餘不變（暫時編輯，之後需還原）。
- 結果：`fastboot boot` 成功，但約 20 分鐘後 adb 與 fastboot 都看不到裝置，判定為開機卡住（尚未實機確認畫面）。
- 下一步：需要使用者長按電源鍵強制重開，回到已刷入的基準系統；然後確認原因（是否 `if (0)` 造成開機卡住）。

### 進度
- SMMU 診斷（規劃步驟 4）尚未開始；本輪先做 mmap 面板循環的 A/B，因為它直接影響前面所有 MISR 比較。

### 第三輪補充結果
- 4.4 ↔ 4.19 的 mmap 面板循環 A/B（`test88_nofbcycle.img`）：移除 mmap 時的 blank/unblank 後，第一次 MISR 仍為 `0xebc45355`，SO-01K 拍照仍為紅色單通道。判定：mmap 面板循環不是紅屏原因（已排除）。
- 注意：`test88` 開機後約 20 分鐘才出現在 adb。
- SMMU 診斷（規劃步驟 4）：
  - 4.19：`mdss_fb.c` 的 `mdss_fb_alloc_fb_ion_memory`，在 `fb_table` 映射完成後、vmap 前，加入 `smmudiag_fb()`（TEMP DIAG）。列印 page 1（偏移 `1920*4352`）所在的 sg 段、其 DMA 位址、sg 實體位址，以及 `iommu_iova_to_phys`。映像 `test89_419_smmu.img` 已打包。
  - 4.4：同樣的診斷，但編譯失敗（4.4 樹中 `mdss_mdp_trace.h` 的 tracepoint 重複定義，與診斷本身無關），尚未取得 4.4 的映射資料。
  - 目前狀態：`test89` 已 `fastboot boot`，約 20 分鐘後仍未出現在 adb 或 fastboot，尚未讀到 `SMMUDIAG` 行。
- 尚未完成：SMMU 診斷的讀值（需要實機確認開機狀態，並讀取 dmesg 中的 `SMMUDIAG` 與 MDP 的 `SRC0_ADDR`）。
- 暫時編輯尚未還原：4.19 `mdss_fb.c` 的 `smmudiag_fb`；4.4 worktree `mdss_fb.c` 的 `smmudiag_fb` 與 include。

### 第三輪後段：SMMU 診斷讀值與新發現
- 4.19 SMMU 診斷（`test89`，核心 `#85`），`dmesg` 的 `SMMUDIAG`（`cam/smmudiag_419.txt`）：
  - 第 0 頁（偏移 0）：sg DMA `0xfb600000` → 實體 `0x176c00000`；SMMU `iova_to_phys` 也是 `0x176c00000`，一致。
  - 第 1 頁（偏移 `0x7f8000`）：sg DMA `0xfbdf8000`（MDP 的 SRC0 讀值也是 `0xfbdf8000`，一致）→ sg 實體 `0x1773f8000`，但 SMMU `iova_to_phys` 為 `0x175bf8000`。兩者不一致，相差 `0x1800000`。
- 純綠測試（`fillg`，從 CPU 寫入第二頁後 pan；另有第一頁版本 `fillg0`）：SO-01K 拍到的螢幕仍是紅色單色，與寫入內容無關（`cam/so_green.png`、`cam/so_green0.png`）。
- MDP 計數器（`/sys/kernel/debug/mdp/stat`）：一次開機內，多次 pan 後 `intf2 play` 只從 0 變成 1 且之後不再增加；`vsync` 停在 992。
- `/proc/interrupts`：`VSYNC_GPIO`（msmgpio 10，面板 TE 線）計數為 0；`MDSS` 有計數。
- 這解釋了「同一開機內只有第一次 MISR 有效」：第一次 kickoff 之後，MDP 沒有再收到 TE 中斷，之後的 kickoff 不會完成。
- 待確認：4.4 在相同操作下 `VSYNC_GPIO` 是否計數、`play` 是否隨 pan 增加。
- 4.4 對照（`test85`，SurfaceFlinger 運行中）：vsync 與 play 計數器持續增加（約每秒 vsync +60，play 持續增加）。停止 SurfaceFlinger 後兩者都停住，所以 `VSYNC_GPIO` 為 0 與停住的計數器本身不能用來比較兩版。`VSYNC_GPIO` 在 4.4 上也是 0，因此 TE GPIO 不是差異來源。
- 待做：在 4.19 flashed 基準上，SurfaceFlinger 運行中取樣 vsync 與 play，與 4.4 比較。
- 4.19 flashed 基準：`adb reboot` 後約 15 分鐘仍不在 adb 或 fastboot，尚未完成 SurfaceFlinger 運行中的 vsync/play 取樣。
- 狀態小結（第三輪）：
  - SMMU 映射不一致（第一頁 sg 實體與 SMMU 翻譯不同）是目前最具體的新發現，但還需要確認 MDP 實際讀取的位址，以及此差異是否直接造成紅屏（純綠測試的畫面仍是紅色，與寫入內容無關）。
  - 4.4 與 4.19 在 SurfaceFlinger 運行中的 vsync/play 行為待比較；4.4 已確認正常更新。
- 4.19 基準（核心 `#76`，SurfaceFlinger 運行中，鎖定畫面）：vsync 會增加，但呈爆發式（連續兩次取樣 vsync 不變，之後一次增加約 40–57），10 秒平均約 14/s。play 也不是穩定增加。
- 4.4（SurfaceFlinger 運行中，取樣時的畫面狀態不同）：vsync 穩定約 60/s。
- 判定：兩邊的取樣時螢幕狀態不同（4.19 在鎖定畫面，4.4 取樣時是另一個狀態），目前不能直接比較速率。下一步要在相同畫面狀態（例如都在桌面或都在鎖定畫面）下重新取樣。
- 同畫面比對（兩版都在桌面，靜止）：
  - 4.19 flashed 基準：12 秒內 vsync 1908 → 1914（+6），play 0 → 1。
  - 4.4 對照：12 秒內 vsync 固定 1128（+0），play 固定 1。
  - 判定：靜止桌面時兩版的 vsync 都幾乎不動，行為一致。先前 4.4 的約 60/s 是在畫面變動時量到的，不能拿來和 4.19 靜止狀態比。
  - 原始資料：`cam/rate419_home.txt`、`cam/rate44_home.txt`；畫面：`cam/g_home419.png`、`cam/g_home44.png`。

## 12. 格式比對：HWC/SDM 送進核心的像素格式（2026-10-29 第四輪）

- 介面確認：HWC/SDM 與核心之間的 uapi（`include/uapi/linux/msm_mdp.h`）在 4.4 與 4.19 的結構、列舉值與 ioctl 編號完全相同，只有註解與一個新的硬體版本巨集不同。所以介面本身不是差異來源。
- 4.19 flashed 基準（核心 `#76`，SurfaceFlinger 運行中，開啟 `mdss_mdp_pipe.c +p`）：`mdss_mdp_format_setup` 印出 `pnum=8/12/13 format=45 opmode=0`。
- 解碼：`mdp_img_format` 列舉中 45 = `MDP_RGBA_8888_UBWC`（UBWC 壓縮的 RGBA），不是一般 RGBA8888（13）。
- 待做：4.4（`test85`）在相同操作下的 format 值，比較是否同樣使用 UBWC 格式。
- 原始輸出：`cam/fmt419.txt`。
- 4.4 對照（`test85`，同樣的畫面操作，`cam/fmt44.txt`）：`mdss_mdp_format_setup` 同樣是 `pnum=8/12/13 format=45 opmode=0`，即 `MDP_RGBA_8888_UBWC`。
- 判定：在 HWC/SDM 送進核心的像素格式上，4.4 與 4.19 完全相同（UBWC 壓縮 RGBA、同樣的管線與 opmode）。格式選擇不是差異來源。
- 仍待確認：UBWC 解碼器的設定（DT 的 UBWC 參數與 UBWC 暫存器寫入）是否兩版不同。注意 fb0 直寫路徑不使用 UBWC，所以它的紅屏不能用 UBWC 解釋。
- UBWC 設定檢查（第四輪後段）：
  - UBWC 格式對應表 `mdss_mdp_format_ubwc_map`，以及平面大小計算 `mdss_mdp_get_ubwc_plane_size`：兩版程式碼相同（僅空行差異）。UBWC metadata 巨集（`UBWC_META_MACRO_W_H=16`、`UBWC_META_BLOCK_SIZE=256`）也相同。
  - 裝置上實際載入的 DT 值（4.19 基準，`/proc/device-tree/soc/qcom,mdss_mdp@c900000/`）：`mdss-highest-bank-bit=2`、`default-ot-rd/wr-limit=0x20`、`dram-channels=2`，與 4.4 的 DTB 同名屬性相同。
  - 4.19 驅動的 buffer 匯入路徑有差異：`mdss_mdp_util.c` 改用 `dma_buf_get` 並在 SMMU 對應時加上 `DMA_ATTR_SKIP_CPU_SYNC`（4.4 走 ion client 路徑）。這會影響 SF/GPU 寫入的 UBWC buffer 的快取同步，是目前最具體的候選。
  - 驅動內沒有找到 UBWC 解碼器的靜態設定寫入（`ubwc static` 相關），所以 UBWC 解碼器設定很可能由閉源的 SDM 使用者層寫入，無法從核心程式碼直接確認。
- 尚未檢查：buffer 的實際像素內容（SF/HWC 寫入的 UBWC buffer 與 MDP 實際讀到的內容是否相同）。

## 13. 1：去除 SKIP_CPU_SYNC 的 A/B（第四輪後段）

- 修改：`mdss_mdp_util.c` 三處 `DMA_ATTR_SKIP_CPU_SYNC`（映射 1028 行、解除映射 945 與 1181 行）全部移除（TEMP DIAG）。
- 4.19 重編成功（`build_noskip419.log`，`BUILD_RC=0`），映像 `test90_noskip.img`。
- 狀態（已更正）：`fastboot boot test90` 成功；依時間戳，裝置約 02:19 即開機完成（uptime 約 87 秒），整段只有幾分鐘，先前寫的「約 25 分鐘」是錯誤的。
- 結果：核心 `#86`（test90），SO-01K 拍到的鎖定畫面仍為紅色單通道（`cam/so_noskip.png`）。結論：去除 `SKIP_CPU_SYNC` 不能修正紅屏，已排除。
- 已還原：`mdss_mdp_util.c` 與 `mdss_fb.c` 以 `git checkout` 還原到 HEAD（兩檔原本沒有使用者的未提交修改）。

### 13（更正後）與 2 的結果
- 1（去除 SKIP_CPU_SYNC）：核心 `#86`（test90），SO-01K 拍到的鎖定畫面仍為紅色單通道（`cam/so_noskip.png`）。結論：已排除。三處暫時編輯已以 `git checkout` 還原。
- 時間更正：依時間戳，test90 約 02:19 即開機完成（uptime 約 87 秒）；前面寫的「約 20–25 分鐘」是錯誤的，實際等待為數分鐘。已修正上文。
- 2（gralloc 圖層的 IOVA 與實體位址比對，`GRALDIAG`，核心 `#87`，`cam/grald419.txt`）：
  - 圖層 pnum=13、fmt=47（`MDP_RGBX_8888_UBWC`），每個採樣的 `iova` 經 `iommu_iova_to_phys` 得到的實體位址，與 buffer 的 sg 實體位址完全相同（例如 iova `0xff60f000` → `0x17540f000`）。
  - 結論：圖層 buffer 的 SMMU 映射一致，MDP 讀取的實體頁就是 gralloc buffer 的頁。
- 補充：先前 fb 第 1 頁的映射不一致（`0x1800000` 差距）仍未解釋。已確認 fb 與圖層都使用 `MDSS_IOMMU_DOMAIN_UNSECURE`（domain=0），所以不是 domain 選錯；但圖層路徑沒有出現同樣的不一致，可能與 fb ION buffer 的映射時機有關，尚待確認。
- 目前排除項目更新：IGC、SKIP_CPU_SYNC、UBWC 格式選擇、UBWC DT 參數、VBIF DT 設定、SMP 暫存器、mmap 面板循環、圖層 SMMU 映射。
- 仍未解釋的：紅屏本身。純綠填充的 fb 測試仍顯示紅色，表示 fb 直寫路徑與圖層路徑都有同樣的紅色輸出，問題可能在 MDP 之後（DSPP/DSI/面板）或 SDM 閉源層的設定。

## 14. 實際記憶體內容（ZZFB，核心 `#88`，4.19，`cam/zzfb419.txt`）

- 方法：`fillg` 從 CPU 把 fb 第 1 頁（偏移 `0x7f8000`）填成綠色（每像素 `00 ff 00 00`）並 pan；再用 `/sys/module/mdss_fb/parameters/zz_fbphys` 觸發診斷，以 `memremap` 讀取兩個實體位址的前 16 bytes：
  - sg 表（CPU 視角）算出的實體位址 `0x1773f8000`：內容全為 `00`。
  - SMMU 翻譯（MDP 視角）`iommu_iova_to_phys` 得到的實體位址 `0x1759f8000`：內容為 `00 ff 00 00 00 ff 00 00 ...`，即綠色。
- 判定：
  - MDP 讀取的記憶體內容是正確的綠色，與 CPU 寫入一致。也就是說 CPU 寫入與 MDP 讀取走的是同一組實體頁，先前的「映射不一致」是 sg 表的位址與實際映射對不上，不是 MDP 讀到錯誤的記憶體。
  - 但面板仍顯示紅色。記憶體內容正確、面板結果錯誤，所以問題發生在 MDP 讀取之後（像素格式解讀、DSPP、DSI、面板）。
- 下一步：在 4.4 上做同樣的 `fillg` 測試，看 4.4 的面板是否顯示綠色。
- 4.4 對照（`test85`，同樣的 `fillg` 綠色填充，SO-01K 拍照 `cam/so_fill44.png`）：面板正確顯示綠色。
- 結論（關鍵 A/B）：同樣的 fb 記憶體內容（綠色），4.4 顯示綠色、4.19 顯示紅色。差異發生在 MDP 讀取 buffer 之後（像素格式解讀、DSPP、DSI 或面板），不在記憶體內容或映射。
- 目前狀態：手機為 4.4 臨時映像（`test85`），尚未還原到已刷入的 4.19 基準。

## 15. 逐層複製 4.4 的暫存器值（綠色填充，第一輪）

- 基準：4.4 `test85`（核心 `#?`，SurfaceFlinger 停止、`fillg` 綠色），4.19 已刷入基準（核心 `#76`，同樣的 `fillg`）。
- 相機確認：4.4 綠色（`cam/so_base44_green.png` 等）；4.19 基準綠色填充仍為紅色（`cam/so_base419_green.png`）。
- 第一層（MDP 暫存器，`g44_mdp_green_v2.txt` vs `g419_mdp_green.txt`，排除 SRC 位址）：
  - fb 管線 DMA0（`0x25000`）：除 SRC 位址（`0x25014`、`0x250a4`）外完全相同。
  - DSPP0（`0x55000`）、INTF_2（`0x6b000`）、LM 階段暫存器的 fb 相關欄位：相同。
  - 其餘差異：VIG0（`0x5000`）、VIG3（`0xb000`）、DMA2（`0x29000`）、LM 的額外 blend 階段（`0x45020` 等）在 4.4 有殘留設定、4.19 為 0；這些管線不是 fb 管線，不影響綠色填充的 DMA0 輸出。
  - `0x2018` 是 CTL 的 FLUSH 暫存器（不是 layer 設定），差異為 flush 的時序，不是設定差異。
- 判定：MDP 暫存器層級在 fb 路徑上沒有可複製的差異，第一層複製不會改變顏色。
- 第二層（DSPP/INTF）：與第一層同一組比對，DSPP0 與 INTF_2 相同，判定同上。
- 第三層以後（DSI controller、DSI PHY、面板）：未完成。原因：DSI controller/PHY 的 debugfs 偏移只接受 DT 定義的有效範圍，超出範圍的寫入被拒絕、讀到舊值，導致先前擷取的 DSI 檔案標籤與內容不可靠（`g44_dsi_*_green.txt` 作廢，改用 `*_v2.txt` 也仍需確認有效範圍）。
- 下一步：從 DT（`qcom,regs-dump-dsi` 或等效屬性）確認 DSI 的有效範圍，重新擷取 4.4 與 4.19 的 DSI controller/PHY，再進行第三層與第四層的複製。
- 目前狀態：手機為 4.4 臨時映像（`test85`）。

## 16. 第三層測試一：面板直接 DCS 測試（4.19 基準，核心 `#76`）

- 寫入路徑：`/sys/kernel/debug/mdss_dsi_panel/write`，格式 `dcs <暫存器> [參數]`；讀取用 `read` + `result`。
- 基準讀值：`0x3A`=`0x77`，`0x0A`=`0x1C`。
- 測試 `dcs 23`（all pixels on）：拍照（`cam/so_dcs23.png`）顯示的是紅色桌面，沒有變成全白；`0x0A` 不變。
- 測試 `dcs 22`（all pixels off）：拍照（`cam/so_dcs22.png`）仍是紅色桌面；`0x0A` 不變（`0x1C`）。
- 正向對照 `dcs 28`（display off）：拍照（`cam/so_dcs28.png`）畫面全黑，`0x0A` 變為 `0x18`；之後 `dcs 29` 還原，`0x0A` 回到 `0x1C`。
- 判定：DCS 寫入路徑有效（`0x28` 可以關閉顯示）。`0x22`/`0x23` 沒有可見效果且 `0x0A` 沒有變化，表示這顆 DDIC 很可能不實作 all-pixel 模式，或被 MDP 的 frame 覆蓋。這個測試無法判斷 G/B 通道的驅動狀況，不能當作面板層的結論。
- 下一步候選：找 DDIC 型號與它支援的測試圖樣命令（需要該 DDIC 的命令表）。

## 17. 面板唯讀掃描（方法 2，4.19 基準，核心 `#76`）

- 面板型號：DT 與裝置 `dsi_on_cmd` 對應到 `somc,9_panel`（Sharp ID9）。原廠 4.4 DTB 的 ID9 節點同樣只有 `35 00`、`29` 兩條 on 命令，DDIC 初始化由 bootloader 留下。
- 作法：`dcs b0 04` 解鎖，`dcs 1 0xNN` 讀取 `0xB0`–`0xFF`，最後 `dcs b0 03` 鎖定（已確認回應 `0x03`）。
- 結果（`cam/ddic_419_unlock.txt`）：幾乎全部為 `0x00`；有值的只有 `0xDA`=`0x5E`、`0xDB`=`0xE0`。
- 判定：單位元組讀取下，這些廠商暫存器看起來都是 0，資訊不足。下一步要比對 4.4 的同一份結果，確認是否也全為 0；若兩邊一致，這個方法無法找出差異。

## 18. ZZDSI 診斷的崩潰原因（UART 證實）與 DDIC 4 位元組掃描

- 崩潰：`zz_dsi_dump` 觸發後，裝置在第一行 `ZZDSI` 輸出之前就重開（UART 記錄 `F:\PL\Android\uart_20261029_142343.txt`）。解鎖 `dcs b0 04` 正常回應，之後直接進入新的 PBL 開機，沒有任何 `ZZDSI` 行。
- 判定：第一次 `readl` DSI controller MMIO 時，DSI 時脈已被閘控，匯流排卡住後由 watchdog 重開。DSI 暫存器傾印必須先開啟 DSI 時脈。
- DDIC 掃描（不需重編）：`dcs b0 04` 解鎖後，用 `dcs 4 0xNN` 讀取 `0xB0`–`0xFF`（`cam/ddic_419_4byte.txt`）。結果與 1 位元組讀取相同：只有 `0xDA`=`0x5E`、`0xDB`=`0xE0` 有值，其餘為 0（4 個位元組全為 0）。
- 判定：這顆 DDIC 的 `0xB0`–`0xFF` 在解鎖後沒有可讀的設定資料，這個方法無法用來比對 4.4 與 4.19 的差異。
- 目前狀態：裝置為已刷入的 4.19 基準（`#76`）。UART 擷取程式（`UART.py`，COM6）仍在執行中。

## 19. 第三層以後：DSI 傾印（4.4 與 4.19）與 DDIC 掃描

- 先前 DSI debugfs 讀值不可靠（見第 17 節）。改用核心內的 `zz_dsi_dump`（`mdss_dsi.c`，`module_param_cb`）直接讀 `ctrl_io`/`phy_io` 並 `pr_err`。
- 崩潰修正：第一版在 DSI 時脈閘控時讀 MMIO，匯流排卡住後重開（UART 證實，第 18 節）。修正版在讀取前後以 `mdss_dsi_clk_ctrl(MDSS_DSI_CORE_CLK)` 開關時脈，4.19（`test94`，核心 `#90`）與 4.4（`test95`）都能完整輸出。
- 比對（`cam/dsi_ctrl_*.txt`、`cam/dsi_phy_*.txt`，每組 128 / 496 個 32 位元字）：
  - DSI controller 0x000–0x1FF：128 字中 2 字不同。`0x048` 4.4=`00827000` / 4.19=`febff000`（DMA 位址）；`0x04c` 4.4=`8` / 4.19=`4`（計數/旗標）。
  - DSI PHY 0x000–0x7BF：496 字中 1 字不同。`0x75c`（PLL 增益）4.4=`0x82` / 4.19=`0xfa`，此差異已在第 11、13 節驗證過不是紅屏原因。
- DDIC（`0xB0`–`0xFF` 4 位元組掃描）：4.4 與 4.19 完全相同（第 17 節與本節）。
- 判定：第三層（DSI controller）與第四層（PHY/PLL）的暫存器值在兩版之間幾乎相同。第五層（面板 DDIC 的可讀暫存器）也相同。複製這些暫存器不會改變顏色。
- 含意：紅屏不是 DSI 或面板的設定差異。剩下的可能是 (1) 像素資料本身的編碼或順序、(2) MDP→DSI 的 kickoff/時序（先前 play 計數器在 pan 後不增加）、(3) 閉源 SDM 層在執行期寫入、而 debugfs 讀不到的狀態。
- 注意：4.19 的 `ZZDSI`、`ZZFB` 等 TEMP DIAG 編輯仍在 `~/lineageos/kernel/sony/msm8998`，需要還原；4.4 worktree 的 `mdss_dsi.c` 目前也含 `ZZDSI` 補丁。

## 20. 最接近面板的測試：DSI 命令模式直接寫 GRAM（方法 2，4.19）

- 實作：`mdss_dsi.c` 的 `zz_gram` 觸發點（TEMP DIAG）。寫入 `1`（綠）時，先送 DCS `0x2A`（X 0..1079）與 `0x2B`（Y 0..1919），再以 `0x2C` + `0x3C` 分 6480 個封包（每封包 960 bytes 像素）送出 6.2MB，透過 `mdss_dsi_cmds_tx`。SurfaceFlinger 先停止。
- 結果：`test96`（核心 `#91`）觸發後裝置重開（回到 `#76` 基準），沒有任何 `ZZGRAM` 完成訊息（UART 與 dmesg 都沒有）。
- 判定：這條路徑目前不可用。與前面的 DSI 傾印相同，可能是在沒有開啟 DSI/MDP 時脈或沒有持有 `ctl->lock` 的情況下做 DSI 傳輸，造成匯流排或看門狗重開。尚未確認是哪一個步驟（0x2A/0x2B 或像素迴圈）造成。
- 下一步候選：(1) 先只送 `0x2A`/`0x2B` 確認位址命令不會重開；(2) 送像素前以 `mdss_dsi_clk_ctrl(MDSS_DSI_CORE_CLK, ON)` 包住，並比照面板 debugfs 的路徑持有 `ctl->lock`；(3) 若仍重開，改用 DSI 命令的 DMA 路徑（較大緩衝）。
- 目前狀態：裝置為已刷入的 4.19 基準（`#76`）。

## 21. zz_gram 步驟一／二（test97，核心 `#92`，log 以 adb dmesg 讀取）

- 步驟一（pattern 4，只送 0x2A/0x2B，DSI 核心時脈開啟）：成功（`61.77`–`62.17` 秒，`rc=0`，無 DSI 錯誤）。
- 步驟二（pattern 1，綠色像素）：`89.86` 秒開始，0x2A、0x2B 就失敗（`cmd_dma_tx` 失敗），同一次寫入中 0x2C、0x3C 全部失敗，約每 200 毫秒一次，共 2652 次。
- 判定：同一個開機內，第一次位址命令成功，第二次（相隔約 30 秒）起 DSI command DMA 就失敗。
- 程式問題：`mdss_dsi_cmds_tx` 失敗時回傳 0（不是錯誤碼），所以 `rc` 沒有被設為非零，迴圈沒有中止，6480 個封包都在逐一逾時。這是寫入卡住的直接原因，需要修正為檢查真正的錯誤。
- 處理：以 `adb reboot` 結束卡住的寫入（`15:25:12`）。dmesg 已存為 `cam/dmesg_gram_test97.txt`。
- 下一步：(1) 修正 `zz_gram_send` 的錯誤判斷（回傳值非正即失敗，並中止迴圈）；(2) 確認 DSI DMA 失敗的原因（DSI 狀態或 `ctl->lock`），再重新測試。

## 22. 4.4 對照：DSI 命令 DMA 像素寫入（test100 與 4.19 test99 重跑）

- 作法：`fastboot boot` 暫開映像（不寫入分區），開機後 `adb root`、執行 `misr5_b1` 完成 fb0 mmap，再依序寫入 `zz_gram` pattern 4 與 pattern 1。
- 4.4 第一次（test100，核心 `#15`）：pattern 4 `rc=0`；pattern 1 位址 `rc=0`，6480 個像素封包全部 `rc=0`（dmesg 時間 73.24 s 位址完成、83.11 s 像素完成）。dmesg 當時未存檔（之後裝置重開），僅由 adb 讀到上述 ZZGRAM 行。
- 4.4 第一次之後的相機截圖（`cam/so_k44_pattern1_cam.png`）：畫面為下拉通知列加藍色桌布，不是綠色。判斷是 SurfaceFlinger 在寫入後重繪，覆蓋了 GRAM 內容，因此這張照片不能證明面板顯示綠色。
- 4.4 第二次（新開機，dmesg 存為 `cam/dmesg_k44_run2.txt`）：pattern 4 `rc=0`；pattern 1 位址 `rc=0`，但像素在第 35 個封包失敗：`mdss_dsi_cmds2buf_tx: failed to call cmd_dma_tx for cmd = 0x3c`，`ZZGRAM pixels done n=35 rc=-5`。
- 4.4 第三次：先 `cmd statusbar collapse` 再寫 pattern 1，裝置重置（adb `closed`）。pstore 為空，崩潰紀錄沒有留下。
- 4.19 test99（核心 `#94`，前次）：0x2a 即失敗，`wait4pingpong timed out ctl=0 ... koff_cnt=1`，重置。UART 紀錄 `uart_20261029_142343.txt` 的 `83.2 s` 起段落為此次。
- 判定：DSI command DMA 的像素寫入在 4.4 也會失敗（同一個 `cmd_dma_tx` 錯誤，並可能重置），因此這個測試不是區分 4.19 紅屏的有效方法。第 21 節以「4.4 的 pattern 1 未確定」為前提的推論需要改寫：4.4 上此路徑一次完整成功、一次中途失敗，屬於不穩定。
- UART 限制：4.4 核心的 printk 不會出現在 UART（UART 檔中 `4.4.302` 出現 0 次），4.4 的紀錄只能用 adb dmesg 讀取。
- 測試映像注意：4.4 dmesg 中大量 `pp_pgc_set_config: ZZDBG6`、`pp_igc_set_config: ZZDBG2`、`pp_pcc_set_config: ZZDBG12` 來自 test100 映像的 pp 層臨時除錯。它們不是原版輸出，正式提交前必須清除。
- 讀取方法更正：toybox 的 grep 不支援 `\|`，會靜默回傳空輸出。本節前期「4.4 沒有 DMA 失敗」的判斷因此無效；之後改用 `grep -e A -e B`。
- 裝置狀態：已 `adb reboot`，回到已刷入的 4.19 基準（`#76`）。UART 擷取程式仍在寫入同一個檔。
- 下一步：不再以整屏 GRAM 像素寫入作為 4.4／4.19 的區分依據。需要另找不依賴 DSI 命令 DMA 的面板觀測方式，或比對 TE/pingpong 的時序（4.4 需先確認 VSYNC_GPIO 計數）。

## 23. MISR 基準重現與單色圖樣（2026-10-29 第五輪）

- 重要前提：MISR 量到的是 DSI0 輸出的合成結果，SurfaceFlinger 的其他圖層也會影響 CRC。
  - 4.19 flashed 基準、SF 運行中、開機後第一次呼叫 `misr5_b1`：CRC `0xe87ed21f`（與先前不同）。
  - 同一基準、`stop surfaceflinger` 後、開機後第一次呼叫：`0xebc45355`（三個讀值一致）。重開後再測一次，結果相同。
  - 4.4 control（`test85`，fastboot 暫開）、SF 停止、第一次呼叫：`0x27209235`，與先前相同。
- 結論：條紋圖樣的 MISR 比較必須在 SF 停止下進行。先前 SF 運行中的 CRC 不能拿來比較。
- 下一步：以 `misr_pat.c`（由 `misr4.c` 改寫，`-DPAT=n`）做單色圖樣：1 紅、2 綠、6 灰階漸層，4.4 與 4.19 各一次，腳本 `.tmp/cam/run_pat.sh`，紀錄 `.tmp/cam/misr_pat_run.log`。
- 單色結果（每次開機第一次 MISR，SF 停止，`run_pat.sh` 與 `.tmp/cam/misr_pat_run.log`）：

| 圖樣 | 4.4（test85） | 4.19 flashed #76 |
|---|---|---|
| 條紋（pat 0） | `0x27209235` | `0xebc45355` |
| 紅色（pat 1） | `0xf41f9b0c` | 全 0（開機後 7 秒與 122 秒各測一次，兩次皆全 0） |
| 綠色（pat 2） | `0xc3ba1a2f` | `0x8a27711a` |
| 灰階漸層（pat 6） | `0xfa686c92` | `0xbd9b84e5` |

- 判定：綠色與灰階在兩個核心的 MISR 不同，所以 MDP 到 DSI0 的輸出在單色內容上就已不同，不只是條紋的位置或 stride 問題。
- 未解釋：4.19 紅色圖樣的 MISR 回傳全 0。CRC 為 0 通常表示 DSI0 沒有輸出任何像素，或 MISR 沒有收到完成的畫面，但這點還沒有驗證。
- 尚未做：同一開機內重複讀取綠色（4.19 第二次綠色，確認 `0x8a27711a` 可重現）；把 4.19 紅色換成 R 值不是 255 的變化量，看是否仍為 0。
- 裝置狀態：4.19 flashed 基準，SF 已停止（需 `adb reboot` 或 `start surfaceflinger` 還原）。

### 23 後續（run2，`.tmp/cam/misr_pat_run2.log`，SF 停止，每次開機第一次 MISR）

| 圖樣 | 4.4（test85） | 4.19 flashed #76 |
|---|---|---|
| 綠色（pat 2）重測 | — | `0x8a27711a`（與前次相同，可重現） |
| 半強度紅 R=128（pat 7） | `0x2c98f751` | `0x150cfb93` |

- 4.19 的 R=128 不是全 0，所以「4.19 紅色全 0」不是紅色通道本身的問題，但 R=255 與 R=128 的行為不同，原因未查明。
- 目前 4 組單色（紅 128、綠 255、灰階漸層，以及條紋）在兩個核心都不同。差異不限於某一個通道，像是整體的像素編碼或輸出轉換。
- 尚未驗證：全紅 R=255 在 4.19 得 0 是 MISR 的特殊情況，還是 DSI0 真的沒有輸出該值。
- 下一步候選：以 4.4 為參考，逐步改變 R 值（例如 0、64、192、255）在 4.19 量測，找出 4.19 有效輸出值的對應關係；每個值需要一次開機。
- 裝置狀態：目前為 4.4 test85（fastboot 暫開），需 `adb reboot` 回到 4.19 flashed 基準。
- 更正：已於 16:20 還原為 4.19 flashed 基準（核心 #76，已確認 uname）。
- 無效紀錄：`misr_rv_run.log`（16:30–16:37）的 R=0/64/192 全部無效。腳本的 `wait_adb` 會覆寫迴圈變數 `v`，導致推送的檔名為不存在的 `misr_rv1`，裝置實際執行的是上一輪殘留的 `/data/local/tmp/misrp`（R=128）。已修正為 `rv` 變數，重新執行，結果寫入 `.tmp/cam/misr_rv_run2.log`。

### 23 續：R 值掃描（修正後，`.tmp/cam/misr_rv_run2.log`，SF 停止，每次開機第一次 MISR）

| R（紅色通道） | 4.4 test85 | 4.19 flashed #76 |
|---|---|---|
| 0 | `0x00000000` | `0x00000000` |
| 64 | `0xbefa9637` | `0x05fcab96` |
| 128 | `0x2c98f751` | `0x150cfb93` |
| 192 | `0x77f7624d` | `0x05fcab96` |
| 255 | `0xf41f9b0c` | `0x00000000` |

- 4.4 的 R 值掃描結果單調、各不相同，R=0 為 0。
- 4.19 的 R=64 與 R=192 CRC 相同，R=0 與 R=255 都是 0。也就是說，4.19 的 MISR 輸出不是 R 的單調函數。
- 4.19 的 R=64 CRC 與 4.4 任何 R 值都不相同，因此無法用 4.4 的表找出 4.19 有效輸出值的對應。
- 未解釋：4.19 在 R=0 與 R=255 得到 0。若 0 代表 DSI0 沒有輸出，R=255 就表示輸出與黑色相同，但面板實際顯示紅色。這需要驗證，不能直接解讀。
- 可能的方向：4.19 的紅色通道輸出經過某種非線性或位元遮罩，但目前沒有證據指向特定元件。

### 23 程式碼審讀：BM 模式 MISR 的讀值機制（4.19 與 4.4 相同機制）

- `mdss_misr_crc_collect()`（`mdss_debug.c`）在 MDP 中斷中、每次 `PING_PONG_0_DONE`（命令模式）收集一筆 CRC，存入 ping/pong 批次（`MISR_CRC_BATCH_SIZE` 筆）。批次滿了才設 `is_ping_full`/`is_pong_full`。
- `mdss_misr_get()` 的 BM 分支只在批次已滿時回傳資料；否則回傳 `ret=-1` 且 `crc_value` 保持 0。
- 因此：
  - 「第一次呼叫有效、之後為 0」與「全 0」都可能只是批次尚未填滿（沒有足夠的 kickoff 中斷），不一定是像素輸出為 0。
  - 4.19 的 R=255 全 0 不能解讀為像素輸出，需要先確認有足夠的 PING_PONG_DONE 中斷。
  - 4.4 的同一段程式碼也是批次 BM，兩邊的讀值機制相同，但 4.19 的 R=64 與 R=192 CRC 相同仍未解釋。
- 下一步：每次量測前後讀 `/proc/interrupts` 的 MDSS 計數，確認有實際中斷；並讀完 32 筆批次的每一筆，看是否都相同。

### 23 續二：完整批次讀值（32 筆）與 MDSS 中斷計數（`.tmp/cam/misr_all_run.log`、`misr_all_k44_run.log`，SF 停止）

- 4.19 R=64：32 筆全部 `0x05fcab96`，MDSS 中斷計數 +51（1188 → 1239）。批次有效。
- 4.19 R=255：32 筆全部 0，MDSS 中斷計數 +51（150 → 201）。批次已填滿，0 是實際讀值，不是空批次。
- 4.4 R=64：32 筆全部 `0xbefa9637`，MDSS +38。
- 4.4 R=255：32 筆全部 `0xf41f9b0c`，MDSS +34。
- 結論：4.19 的全紅 CRC 為 0 是真實讀值，不是批次未填滿造成的假 0。R=64 與 R=192 相同 CRC 仍未解釋。

### 相機確認（SO-01K，（`shoot.sh` 回報 no new photo，改用 screencap 檢查檔）；`so_419_R255_check.png`、`so_check.png`）

- 4.19 R=255 單獨顯示後，G8342 面板的相機畫面接近全黑，帶一點暗紅褐色，沒有亮紅色。與 MISR 全 0 一致。
- 4.4 R=255 後的相機畫面是明亮的藍色，不是紅色。這張照片無法確定是否顯示了我們的圖樣，可能是 SF 桌布停留在 page 0，尚未確認。
- 注意：`shoot.sh` 的 `input tap` 第一次拍照常回報 `no new photo`，所以相機照片需要用 `screencap` 的檢查檔確認。
- 裝置狀態：4.19 flashed 基準，SF 已停止（需 `adb reboot` 還原）。

### 23 續三：通道對應的相機確認（4.4 與 4.19 同一組純色填充，SF 停止，SO-01K 取景截圖）

- 重要更正：本節之前用的 `R=255` 標籤指的是 byte2（`px[2]`）。在這個 fb 的位元組順序下，byte0 才是面板的紅色，byte2 是藍色。之前所有「R」「G」「B」的標記需以此為準，表格如下。
- 圖樣：`misr_pat_p3`（byte0=255）、`misr_pat_p2`（byte1=255）、`misr_pat_p1`（byte2=255）。

| 填充（位元組） | 4.4 面板 | 4.19 面板 |
|---|---|---|
| byte0=255 | 紅（`k44_vf_p3.png`） | 紅（`k419_vf_p3.png`） |
| byte1=255 | 綠（`k44_vf_p2.png`） | 暗紅（`k419_vf_p2.png`） |
| byte2=255 | 藍（`k44_vf_R255.png`、`k44_vf_p1` 同組） | 黑（`k419_vf_p1.png`） |

- 4.4 的 R0（全 0）為深紫黑，對照正常。
- 判定：4.4 的通道對應正確（byte0→R、byte1→G、byte2→B）。4.19 的面板上，綠色輸入顯示為紅色，藍色輸入顯示為黑色，紅色輸入顯示為紅色。這與「只剩紅色」的現象一致。
- 這同時解釋了先前 MISR 的全 0：4.19 的 byte2 輸出為黑，所以 DSI0 整幀為 0。
- 下一步：比對 4.4 與 4.19 的 fb pipe 位元組解包（unpack pattern、元素位置、alpha 與 swap 欄位）。先前「fb 格式相同」的結論是比對 SF 圖層 pipe 得出的，還沒驗證 fb0 直寫路徑。
- 裝置狀態：4.19 flashed 基準，SF 已停止（需 `adb reboot` 還原）。

### 24 通道路徑：MDP 暫存器差異（4.4 與 4.19 同為 byte2=255，`mdp44_blue.txt`、`mdp419_blue.txt`）

- 差異：
  - DMA0（0x25000）：除 SRC 位址（`0x03618000` vs `0xfbff8000`）外相同；DSPP（0x55000）與 INTF_2（0x6b000）相同（0x6b990 為 MISR 暫存器本身，4.4 為 `0xf41f9b0c`）。
  - LM 殘留 blend 階段（0x45020、0x45050、0x45080、0x450b0、0x45230、0x45260）：4.4 為 `0x600`/`0xff`（或 `0x400`/`0xff`），4.19 為 0。
  - 未使用的 pipe（VIG0 0x5000、VIG3 0xb000、DMA2 0x29000、DMA3 0x2b000）：4.4 有殘留設定，4.19 為 0。
- 判定：DMA0 與 DSPP 相同，但仍找不到會改變通道順序的暫存器。
- E1（`e1_lm_copy.sh`）：4.19 上寫入 4.4 的 LM blend 值後，藍色填充仍為黑（`e1_after.png`），即 LM 殘留 blend 值不是原因。寫入是否被 commit 覆寫未驗證。
- 裝置狀態：4.19 flashed 基準，SF 已停止。

### 25 最接近面板：DSI 命令模式直接寫 GRAM（4.19 test99，`gram_check.sh`，`k419_gram2.png`）

- 作法：`fastboot boot test99_gram_lock.img`（4.19 #94，不寫入分區），SF 停止，先以 `misr_pat_p0` 完成 fb0 mmap，再 `echo 1 > zz_gram`（pattern 1，綠）。
- 結果：`ZZGRAM addr done rc=-5`，`pixels done n=0 rc=-5`。位址命令 `0x2A` 即失敗，沒有送出任何像素，DSI command DMA 在這次開機中就已失敗。
- 第一次嘗試（未先 mmap）：`ZZGRAM no fb0 ctl (mmap fb0 first)`，未送出任何命令。
- 面板照片（`k419_gram2.png`）：紅色，沒有綠色。這反映的是 mmap 後 fb 的內容（stripe 圖樣的紅色段），不是 GRAM 寫入的結果，因為寫入從未成功。
- 判定：這條路徑在 4.19 目前無法使用，無法用來區分 MDP 與面板。4.4 的同一路徑先前也曾在第 35 個封包失敗（第 22 節），所以即使修好 4.19 的位址命令，兩邊的可比性也還需要再驗證。
- 尚未做：找出 `0x2A` 在 4.19 失敗的原因（DSI 時脈、ctl lock、或 wait4pingpong），以及重複 4.4 的同一測試。
- 裝置狀態：test99 fastboot 暫開，需 `adb reboot` 還原。

### 26 DSI 位址命令失敗的原因追查（4.19 flashed #76，SF 停止）

- 程式碼：`zz_gram_send` 經 `mdss_dsi_cmds_tx` 送出；`mdss_mdp_display_wait4pingpong`（`mdss_mdp_ctl.c` 5743）在超時時回傳錯誤並重置 ctl。`koff_cnt=1` 表示有一次 kickoff 未完成。
- 實測：`/proc/interrupts` 的 `VSYNC_GPIO`（msmgpio 10）計數為 0，SF 停止期間 MDSS 計數不變（884 / 4395）。
- 透過 panel debugfs 送 `dcs 35 00`（TE on）後，VSYNC_GPIO 仍為 0。
- 判定：DDIC 的 TE 腳位在這台裝置上沒有脈衝。但 4.4 的 VSYNC_GPIO 也是 0，而 4.4 的 kickoff 能完成，所以 GPIO 計數本身不能當成失敗原因。若 tear-check 由 MDP 內部產生，GPIO 為 0 是正常的。
- 尚未驗證：DT 的 `qcom,platform-te-gpio` 數值、tear-check 暫存器（INTF_2 的 TEAR 區段在先前的 MDP 暫存器比對中相同），以及 4.4 與 4.19 的 `mdss_dsi.c` TE IRQ 啟用時機（1710、3707–3731 行）。
- 裝置狀態：4.19 flashed 基準，SF 已停止（需 `adb reboot` 還原）。

### 27 TE 設定比對（DT 與驅動，4.19 live FDT `.tmp/cam/fdt419.dts` 與 4.4 `d44_a.dtb`）

- DT：`qcom,platform-te-gpio` = msmgpio 10（4.19 實測）。作用中的面板節點 `qcom,mdss_dual_sharp_1080p_120hz_cmd`：`te-check-enable`、`te-using-te-pin`、`te-pin-select=1`、`te-dcs-command=1`、`tear-check-frame-rate=0x2ee0`。4.4 DTB 的同一節點完全相同。
- 驅動：`mdss_dsi_unblank` 中，命令模式且 `vsync_enable && hw_vsync_mode` 時呼叫 `mdss_dsi_set_tear_on` 並啟用 TE IRQ（4.19 `mdss_dsi.c` 1708–1712；4.4 為 1740–1744，其中 TE IRQ 經 `panel_update_te_irq`）。兩邊邏輯相同。
- 實測：4.19 的 VSYNC_GPIO 計數為 0（SF 停止與運行中皆然，`dcs 35 00` 後仍為 0）；4.4 同樣為 0。
- 判定：TE 的 DT 與啟用條件相同，TE 腳位在兩邊都沒有邊緣。TE 不是 4.19 kickoff 停滯的已知差異。
- 尚未解決：4.19 在第一次 kickoff 後 `intf2 play` 不再增加（第 11 節），4.4 則持續增加。這個差異仍然未知，需要從 `mdss_mdp_ctl` 的 kickoff 與 pingpong 完成路徑追查。
- 裝置狀態：4.19 flashed 基準，SF 運行中。

### 28 kickoff 完成路徑（4.19，`mdss_mdp_intf_cmd.c`）與 TE 腳位實測

- TLMM：`gpio10` 為 `func1`（經 `/sys/kernel/debug/gpio`），TE 腳位被路由到 MDP，因此 Linux 的 GPIO 中斷計數不會增加。這解釋了 VSYNC_GPIO 為 0 的原因，兩邊都是這樣。
- TE 實測：400 次取樣中有 15 次為 high（其餘 low），TE 脈衝存在，不是固定低電位。
- DSI_TRIG_CTRL（0x084）：兩邊相同（先前 DSI 比對）。
- 命令模式 kickoff 完成：`koff_cnt` 由 PING_PONG_COMP 回呼遞減（`mdss_mdp_intf_cmd.c` 1416、2104）。`__mdss_mdp_wait4pingpong` 等待 `koff_cnt==0`，超時後 `mdss_mdp_ctl_reset`。
- MISR 實測：4.19 在 40 次 pan 的期間 MDSS 中斷增加 51 次，且 BM 批次（PING_PONG_0_DONE 收集）全部填滿。也就是 MDP 的 pingpong 完成中斷確實會在 4.19 觸發。
- 判定：4.19 的 MDP 硬體完成了 kickoff，但 `koff_cnt` 沒有歸零（位址命令看到 `koff_cnt=1`）。這表示問題在驅動的計數或回呼（PING_PONG_COMP callback 是否被清除、或 koff 與 MISR 收集的競爭），而不是 TE 或硬體。
- 尚未驗證：4.4 的 `koff_cnt` 行為（同一開機中 pan 後的計數），以及 4.19 PING_PONG_COMP callback 是否在某些路徑被 `__clear_ping_pong_callback` 清除。
- 裝置狀態：4.19 flashed 基準，SF 運行中。

### 29 ZZKOFF 實測（4.19，test101 = 4.19 + `mdss_mdp_intf_cmd.c` 臨時 pr_err，`.tmp/cam/koff_pan_dmesg.txt`）

- 40 次 pan：`ZZKOFF inc` 與 `ZZKOFF ppcomp` 各 40 筆，`koff` 在每次 inc 後為 1，ppcomp 後歸 0；kickoff 每次約 33 ms 完成。pan 路徑的計數是平衡的。
- 開機後 SF 停止期間的一次 kickoff（約 36 s）：`wait4pingpong timed out ctl=0 ... koff_cnt=1`，之後 SF 重新提交的 kickoff 也都平衡（inc/ppcomp 各 676 筆）。
- zz_gram 位址命令（77.69 s）：`mdss_dsi_cmds2buf_tx: failed to call cmd_dma_tx for cmd = 0x2a`，約 200 ms 後失敗（`DMA_TX_TIMEOUT`）。沒有 `dma tx done but irq not triggered`，表示 DSI_INTR_CTRL 的 CMD_DMA_DONE 位元在超時時為 0：DSI 主機沒有執行這個命令。
- 判定：位址命令的失敗不是 koff 計數造成（與先前「koff_cnt=1」的推論不同）。它是 DSI 命令 DMA 的完成中斷沒有觸發。
- 還原：`mdss_mdp_intf_cmd.c` 已以 `.tmp/port/mdss_mdp_intf_cmd.c.orig` 還原（4.19 源碼樹該檔無 diff）。
- 尚未查：DSI 主機為何不執行命令 DMA（DSI_STATUS 0x0c0、DSI_INTR_CTRL 0x110 在 zz_gram 寫入時的值，以及 4.4 同一時點的值）。
- 裝置狀態：test101 fastboot 暫開，需 `adb reboot` 還原 4.19 基準。

### 30 DSI 命令 DMA 失敗的對照（4.19 與 4.4 相同路徑）

- 4.19（test101，`.tmp/cam/dsi_fail_dump.txt`）：SF 停止、pan 後寫 zz_gram，位址命令 `0x2a` 失敗（約 200 ms，`DMA_TX_TIMEOUT`，無 `irq not triggered` 警告）。失敗後 DSI 控制器暫存器傾印：`0x080=001c1a02/80000004`、`0x090=1`、`0x0c0=0/729/010f0f08/1`、`0x110=02200202`、`0x100=…03f03bc0`。
- 4.4（test100，`.tmp/cam/k44_fail_dump.txt` 與本節後段）：pan（`misr_pat_p0`，`0x27209235`）後寫 zz_gram，位址命令 `0x2a` 與 `0x2b` 同樣失敗（`failed to call cmd_dma_tx`，`rc=-5`）。
- 對照：兩邊 DSI 控制器的 `0x080`、`0x090`、`0x0c0`、`0x100`、`0x110` 相同。
- 先前 4.4 第一次寫入成功（第 22 節）是在沒有 pan 的情況下。此次 4.4 在 pan 後失敗，所以 zz_gram 的 DMA 路徑在兩個核心上都不穩定，是否能成功取決於開機後的狀態。
- 判定：直接 GRAM 寫入無法用來區分 4.4 與 4.19。這條路徑的失敗與 4.19 特有的 kickoff 問題無關。
- 裝置狀態：4.4 test100 fastboot 暫開，需 `adb reboot` 還原 4.19 基準。

### 31 LM 混色階段：E1 無效的更正與新線索（4.19 與 4.4 的 `mdp44_blue.txt`、`mdp419_blue.txt`）

- 更正：第 24 節的 E1 無效。以 debugfs 寫入 LM 暫存器後，下一次 pan 的 commit 會把值覆寫回去（實測：寫入 `0x45020=0x600` 後讀到 `0x600`，再 pan 一次後為 `0`）。所以 E1 的黑色結果不能用來排除 LM 殘留值。
- 新線索（4.4 的 LM 混色）：
  - `0x45020`（stage 0）= `0x600`，`0x45024` = `0xff`；stage 1、2、3（`0x45050`、`0x45080`、`0x450b0`）相同；另有 `0x45230`、`0x45260` = `0x400`。
  - 解碼（`mdss_mdp_hwio.h`）：`0x600` = BG_ALPHA_FG_PIXEL（`2<<8`）加 BG_INV_ALPHA（`1<<10`），即 premultiplied 混色：輸出 = fg + bg·(1 − fg 像素 alpha)。
  - 4.19 上 stage 0–3 全部為 0，且 CTL_LAYER2（0x2018）為 0（4.4 為 `0x60000000`）。
- 判定：4.4 把 DMA0 的 fb 像素經 premultiplied 混色階段送出；4.19 的混色階段與 CTL 圖層設定與之不同。這兩者都由驅動在每次 commit 時寫入，不能用 debugfs 驗證，需要在 4.19 驅動的 `mdss_mdp_ctl.c`（5120–5214 行，blend op 的選擇）與 CTL 圖層寫入處修改並重新編譯，才能判定這是不是通道錯誤的來源。
- 尚未驗證：4.19 的 fb pipe 實際落在哪個 LM 階段（stage 0–3 全為 0，表示 fb pipe 可能不經過任何混色階段，或走 CTL 的其他路徑）。
- 裝置狀態：4.19 flashed 基準，SF 已停止。

### 32 混色階段實測（4.19，test102 = 4.19 + `mdss_mdp_ctl.c` 臨時 pr_err，`.tmp/cam/blend_dmesg.txt`）

- 4.19 實際記錄（藍色填充、SF 停止，40 次 pan）：`pnum=13 stage=2 blend_op=0x100 fg_alpha=0xff bg_alpha=0x0 pipe_alpha_en=0`。
- 解碼：`0x100` = BG_ALPHA_BG_CONST（`1<<8`），FG 為常數 alpha 0xff，所以輸出 = fg（直通）。
- 4.4 的 `0x600`（BG_ALPHA_FG_PIXEL 加 BG_INV_ALPHA）在像素 alpha 為 0 時同樣是 fg 直通。
- 判定：兩邊的混色結果都是直通，混色模式不是通道錯誤的原因。這也解釋了第 31 節的 LM 階段 0 為 0：4.19 的 fb 管線使用的是 stage 2（pnum 13），dump 讀取時的狀態與 commit 時不同。
- 注意：pnum=13 是 4.19 實際用來顯示的管線，而先前比對的 DMA0（0x25000）不是它。需要確認 pnum 13 的暫存器（0x2xxxx 區段中對應的 SSPP）在兩個核心上是否相同。
- 還原：`mdss_mdp_ctl.c` 已還原（4.19 源碼樹該檔無 diff）。
- 裝置狀態：test102 fastboot 暫開，需 `adb reboot` 還原 4.19 基準。
- 補充（LM 暫存器的讀值時機）：ZZBLEND 記錄的 stage 2 寫入（`0x80` 偏移，LM0 基底 0x45000 → `0x45080`）在 dump（`mdp419_blue.txt`，SF 停止後讀取）中為 0；4.4 的 dump 中同一位置為 `0x600`。LM 階段暫存器在 frame 結束後可能被清除，因此 dump 反映的是「讀取當時」而不是 commit 當時的狀態。第 24、31 節的 LM 比較因此不能直接作為通道錯誤的證據。
- 另確認：fb 的 DMA0（0x25000）確實是 fb 管線（4.19 `0x25010 = fbff8000`、4.4 `0x25010 = 03618000`）。DMA0 與 DSPP、INTF_2 的暫存器相同，不影響上述結論。

### 33 能否直接讀 DMA0 輸出像素（LM 區塊 MISR 與寫回管線）

- 直接記錄 DMA0 的輸出像素：MDP 硬體沒有 pipe 輸出的讀回介面。DMA0 送出的是經 fetch 後的串流，不會寫到記憶體。
- LM 輸出 MISR（區塊 5，`DISPLAY_MISR_MDP`，`misr_blk5_p1`、`misr_blk5_p2`，`blk_run.log`）：藍與綠兩組、4.4 與 4.19 皆為 0。此區塊在兩個核心都沒有收集到資料，不能使用。
- 寫回管線：`fb2`（`mdssfb_a0000`，DT 為 `qcom,mdss_wb_panel`，類型 `writeback panel`）是 concurrent writeback（mdp5 CWB）裝置。它可以把 LM 混色後的輸出寫入記憶體，正是 DMA0 之後、DSPP 之前的像素，因此能讀回實際的像素值。
- 寫回的呼叫方式：4.19 的 CWB 透過 `mdp_layer_commit` 原子提交，輸出緩衝區需要由使用者以 ION fd 提供（`mdss_mdp.c`、`mdss_fb.c` 的 WRITEBACK 分支）。需要先確認 `/dev/ion` 或 dma-heap 的可用性，以及目前源碼樹中使用者未提交的 ion 改動是否影響此路徑。
- 尚未實作。下一步：用 CWB 讀回 4.19 與 4.4 對同一藍色填充的 LM 輸出像素，找出第一個與 4.4 不同的位置。
- 裝置狀態：4.4 test100 fastboot 暫開，需 `adb reboot` 還原 4.19 基準。

### 34 寫回（CWB / WFD）讀回 LM 輸出像素的嘗試（4.19 flashed #76，`.tmp/cam/wb.c`、`mkelf2.py`）

- 工具：freestanding aarch64 程式（`wbtest`），以 `/dev/ion` 的 `ION_IOC_ALLOC`（heap 25，`fd` 直接回傳）配置輸入（純藍，byte2=255，alpha=255）與輸出緩衝區（輸出填 0xAA），送 `MSMFB_ATOMIC_COMMIT`（`_IOWR('S',128,8)`），讀回輸出統計。
- ION 分配與 mmap 正常。輸入層需要有效的 pipe：`pipe_ndx = BIT(pnum)`，DMA3（pnum 13）可通過 `mdss_mdp_layer` 的檢查，DMA0（pnum 6）未試。
- 輸出 stride 單位是「像素」（`mdss_mdp_intf_writeback.c` 的 `img_width = planes[0].stride`），用位元組會得到 `Buffer size=8294400, expected size=33177600` 的錯誤。
- CWB 路徑（`MDP_COMMIT_CWB_EN=0x800`，在 fb0 上 commit）：
  - 送出後核心在 CWB 中斷中 oops：`Unable to handle kernel read from unreadable memory at 0x102`，位置 `mdss_mdp_writeback_cwb_intr_done`（`mdss_mdp_intf_writeback.c` 313 行），`mdp5_data->cwb.priv_data` 為 NULL，隨後 `Kernel panic - not syncing`，裝置重開。UART 紀錄 `uart_20261029_142343.txt` 的 `[60.105774]` 起。
  - 這表示 CWB 路徑在這個組合下會崩潰，不能直接用。
- WFD 路徑（fb0 commit，不設 CWB 旗標，`writeback_ndx=0`）：commit 回傳 0，但輸出緩衝區內容仍是 0xAA（未被寫入）。已嘗試 sleep 1 s、3 s，以及 `MDP_COMMIT_WAIT_FOR_FINISH`，皆無效。核心日誌沒有 WFD 相關訊息。
- 尚未解決：WFD 為什麼沒有寫入輸出緩衝區。可能的原因是 SF 停止後 fb0 沒有觸發實際的 frame，或 WFD 需要額外的設定。
- 裝置狀態：CWB 崩潰後重開；之後的 WFD 測試為 4.19 flashed 基準，SF 已停止。

### 35 WFD 提交是否觸發 frame（4.19 flashed #76，SF 停止，`/sys/kernel/debug/mdp/stat`）

- 提交前：`intf2 play=0x28`、`DMA3.0=0x84`、`vsync=0x998`。
- 提交後（`wbtest`，WFD 路徑）：`intf2 play=0x1`、`DMA3.0=0x1`、`vsync=0x999`。
- 判定：提交確實觸發了一次顯示 frame（DMA3 與 intf2 計數都有變化），所以 commit 有進入硬體。`stat` 沒有寫回（wb）的計數，無法直接確認寫回是否完成。
- 因此輸出緩衝區沒有被寫入，原因不在「沒有 frame」。下一步候選：(1) 寫回輸出格式改為 XRGB/RGB888 並比對 `mdss_mdp_wfd_validate` 的格式限制；(2) 輸出緩衝區改用快取屬性（`ION_FLAG_CACHED`）並在讀取前做 cache invalidate；(3) 確認 WFD 是否需要 `MDP_COMMIT_*` 其他旗標才會觸發 wb done。
- 裝置狀態：4.19 flashed 基準，SF 已停止（需 `adb reboot` 還原）。

### 36 寫回路徑的最後嘗試（4.19 flashed #76）

- 輸出格式改為 XRGB8888（`MDP_XRGB_8888` = 1）：fb0 WFD 提交仍回傳 0，輸出緩衝區仍為 0xAA。
- ION 配置改為快取（`ION_FLAG_CACHED`）：仍為 0xAA，排除快取過時的可能。
- 在 fb1（writeback panel）上提交：`wfd not setup`（`mdss_mdp_wfd_add_data`），提交回傳 -22。`fbioblank(0)` 回傳 -14。核心日誌先前出現 `mdss_mdp_ctl_setup: writeback panel, ignore`，表示 writeback panel 的 ctl 沒有被建立，所以 WFD 的 `ctl->wb` 為 NULL。
- 判定：在這個核心組態下，writeback panel 的 ctl 被忽略（`mdss_mdp_ctl_setup`），因此 fb1 上的 WFD 無法設定；fb0 上的 WFD 提交會觸發 frame 但不寫入輸出；fb0 上的 CWB 路徑會在中斷中崩潰（第 34 節）。寫回讀取路徑在此核心上不可用，除非另外修正驅動。
- 裝置狀態：4.19 flashed 基準（已重開），SF 運行中。

### 37 查：WFD 無法建立的原因，以及寫回讀取到的 LM 與 DSPP 輸出（2026-10-30）

- 原因：`mdss_mdp_ctl_setup` 對 writeback panel 的 "ignore" 分支只是直接 `return 0`，不是失敗點。真正的原因是 WFD 的 `ctl->wb` 由 validate 步驟的 `mdss_mdp_wfd_setup` 設定，而我們之前只做 commit，沒有先送 `MDP_VALIDATE_LAYER`（0x01）。加入 validate 後，fb1（4.19）與 fb2（4.4，wb panel）的寫回都能成功提交。
- ION：4.19 為新 ABI（`ion_allocation_data.fd`），4.4 為舊 ABI（`handle` + `ION_IOC_SHARE`）；兩者的 `msm_mdp_ext.h` 提交結構相同。
- LM 輸出（WFD，不設 CWB 旗標，輸入為純 R/G/B，單一 boot 各跑三次）：
  - 4.19 與 4.4 的讀回結果完全相同：R 輸入→(255,255,0,0)、G 輸入→(255,0,255,0)、B 輸入→(255,0,0,255)（依 XRGB 解讀的位元組排列）。
  - 判定：在 LM 輸出（DSPP 之前）兩個核心一致，差異不在 DMA、混色或 LM。
- DSPP 之後（CWB + `MDP_COMMIT_CWB_DSPP`，fb0）：
  - 4.4：輸出是非二元值，例如 R 輸入→(255,244,29,0)、G→(255,92,251,0)、B→(255,0,49,255)。判定：4.4 的 DSPP 階段有非恆等的色彩轉換（PCC 或 PA）。
  - 4.19：第一次 CWB 提交即在 `mdss_mdp_writeback_cwb_intr_done` 的 NULL 解參考中崩潰（`0x102`）。加上 `ctx` NULL 保護後，崩潰移到同一函式 +0xa8 的另一個解參考，仍無法完成。
- 尚未確認：4.19 的 DSPP 輸出與 4.4 是否相同。這需要先修正 CWB 中斷處理，或改用其他方法讀取 DSPP 輸出。
- 還原：`mdss_mdp_intf_writeback.c` 已還原為原始版本（4.19 源碼樹無 diff）。
- 裝置狀態：崩潰後仍在 test103（含 CWB 保護的測試映像），需 `adb reboot` 回到 4.19 flashed 基準。

### 38 Gamut LUT 64 位元寫入造成 DSPP 色彩錯誤（2026-10-30，test117–120）

- 更正 §37：當時 4.19 CWB 中斷路徑已修到可讀取 DSPP 輸出；本輪已確認兩個核心的 DSPP 輸出差異。
- test117：PA opmode 啟用時為 `0x1e100000`，PA 的 hue/sat/val/contrast 參數皆為 0；PGC LUT（0、32、64、128、512、992、1023）與 4.4 的 `ZZDBG6` 樣本相同。純綠 CWB 輸出為 `(255,92,0,0)`。
- test118：僅清除 DSPP PA opmode（`0x1e100000 → 0`），輸出仍為 `(255,92,0,0)`；PA 排除。
- test119：Gamut opmode 原值為 `0x3`；只將 Gamut opmode 清為 0，輸出變為正確的純綠 `(255,0,255,0)`。證明異常由啟用中的 DSPP Gamut 路徑造成。
- 根因：Sony hook commit `33f784d41068` 把 `pp_gamut_set_config()` 的 64 位元 LUT 寫入由 `writeq_relaxed()` 改成 `writeq_relaxed_no_log()`。本樹 `arch/arm64/include/asm/io.h` 的 `writeq_relaxed_no_log` 將參數先轉成 `cpu_to_le32(v)`，因此丟掉高 32 位；Gamut 每筆 `{c1_c2,c0}` LUT 資料遭截斷。
- test120：暫時把該呼叫改回 `writeq_relaxed()`，Gamut 保持啟用；同一純綠 CWB 輸出恢復為 `(255,92,251,0)`，與 4.4 §37 基準一致。這確認 64 位元截斷是紅屏色偏的直接原因。
- 4.4 對照：原始 Gamut 程式碼使用 `writeq_relaxed()`；本地 ARM64 no-log macro 的錯誤轉型使 Sony hook 的替換不等價。
- 本輪沒有保留正式核心修正；test117–120 都是 `fastboot boot` 暫開，核心來源在建置結束時已還原。test120 後已重開回原本安裝的 4.19 核心；runner log 確認核心版本為 `4.19.325-cip135-st19-perf-gae19392bf8c8-dirty`，`sys.boot_completed=1`，SurfaceFlinger 正常執行。核心來源檔均與 test120 前備份相同。
- 測試紀錄：`.tmp/port/cwbd_419_test117_papgc_20261030.log`、`.tmp/port/cwbd_419_test118_paoff_20261030.log`、`.tmp/port/cwbd_419_test119_gamutoff_20261030.log`、`.tmp/port/cwbd_419_test120_gamut64fix_20261030.log`。


### 39 外部相機確認修正後的實際面板顏色（2026-10-30）

- G8342 暫開 test120（Gamut 啟用、完整 64 位元 LUT 寫入），停 SurfaceFlinger 後以 fb0 顯示純綠圖樣；SO-01K 相機取景即時畫面拍到面板為綠色，未見紅色偏移。取景截圖：`.tmp/cam/g8342_gamutfix_camera_preview.png`。
- 相機快門未產生新 JPEG，因此採用相機即時取景截圖作為外部確認，不把舊照片當成此次拍攝結果。
- 清理後 G8342 已重開回原安裝的 `4.19.325-cip135-st19-perf-gae19392bf8c8-dirty`，`sys.boot_completed=1`，SurfaceFlinger 已執行；SO-01K 相機 app 已關閉。

### 40 外部相機確認純藍通道（2026-10-30）

- 使用 test120 修正版（Gamut 啟用、完整 64 位元 LUT 寫入），G8342 fb0 顯示純藍單通道圖樣；SO-01K 相機即時取景拍到整片藍色，未變黑、未轉紅。取景截圖：`.tmp/cam/g8342_gamutfix_blue_camera_preview.png`。
- 測試後 G8342 已重開回原安裝的 4.19 核心，`sys.boot_completed=1`，SurfaceFlinger 正常執行；SO-01K 相機 app 已關閉。

### 38 驗證 f120f557faffa6544d9aa0a62be608a66feb17f3（修正 Gamut LUT 64 位元寫入截斷）

- 提交內容：`mdss_mdp_pp_v1_7.c` 的 `pp_gamut_set_config` 把 `writeq_relaxed_no_log(gamut_val, ...)` 改為 `writeq_relaxed(...)`。`writeq_relaxed_no_log` 內部先做 `cpu_to_le32(v)`，會把 64 位元的 LUT 值截成 32 位元，高 32 位元（c1_c2）遺失。
- 建置：以 `git worktree`（`.tmp/k_f120`，detached 於 f120f557）乾淨建置，未包含使用者未提交的改動。`.config` 取自 `out_main419`，`_dcm` DTB 取自 `out_main419`（worktree 建置未產生該 DTB）。核心版本 `4.19.325-...-gf120f557faff`。映像 `test104_f120.img`（fastboot 暫開，未寫入分區）。
- 結果（SF 停止，第一次 MISR）：
  - 條紋 MISR：`0x27209235`（4.4 的值）。4.19 flashed 基準為 `0xebc45355`。
  - 面板照片（SO-01K）：藍色填充顯示為藍色（基準為黑）；綠色填充顯示為綠色（基準為紅）。
- 判定：這個提交能解決 4.19 上「G 變紅、B 消失」的通道錯誤，條紋 CRC 也與 4.4 一致。
- 注意：
  1. 只在 fastboot 暫開的映像上驗證，尚未刷入分區。
  2. 紅色（byte0）的照片未另外拍攝，此結論以藍、綠兩色為準。
  3. `git worktree` 的 metadata 留在 kernel repo（`~/lineageos/kernel/sony/msm8998`），需要時以 `git worktree remove .tmp/k_f120` 清除。
- 裝置狀態：已重開回到 4.19 flashed 基準。

### 39 刷入 boot 分區（f120f557 核心）

- 備份：刷入前以 `dd` 讀取 `/dev/block/sda38`（boot，64 MB）存為 `.tmp/port/boot_backup_4.19_76.img`（sha256 前 16 碼 `e939571b5354e018`），即刷入前的 4.19 flashed #76 基準。
- 刷入：`fastboot flash boot test104_f120.img`（OKAY），之後 `fastboot reboot`。
- 結果：開機後 `uname -r` 為 `4.19.325-cip135-st19-perf-gf120f557faff`，`sys.boot_completed=1`。
- 還原方法（如需）：`fastboot flash boot` 指定 `boot_backup_4.19_76.img`。
- 尚未做：刷入後的面板照片與 MISR 複核（先前的驗證在 fastboot 暫開映像上完成）。

## 40. 提交改寫後的 hash 對照（2026-10-30）

- 修補併入原提交（e8d242f→2f0d393、cf6da79→29bda09、690f83b→b568a20）後，`f120f557` 改為 `273ef4756aa0`，之後又因 pstore 提交併入改寫為 `5229e2e135ad`，內容（tree）皆不變。
- 之後的開機慢修正（關 UART console、ramoops DT）已併入 `4be0da3ecbf9`，開機慢的細節見 `md/msm8998_4.19_slow_boot_2026-10-30.md`。
- 刷入 boot 的映像已換成 `.tmp/port/test106_quiet_pstore.img`；舊的 f120 映像為 `.tmp/port/test104_f120.img`（回滾用）。
