---
name: presentation-architect
description: "A unified AI workflow for generating presentations. Supports two modes: (1) Anchored Mode (圖文錨定模式) for parsing DOCX/text into YAML and 1:1 mapped PPTX, and (2) Generative Design Mode (生成式企劃模式) for 5-step brainstorming, ASCII layout design, and AI image generation. (簡報架構總監)"
compatibility: opencode
---

# 簡報架構總監 (Presentation Architect)

這是一個強大且統一的簡報生成技能，整合了「圖文錨定」與「生成式企劃」兩大工作流。身為架構總監，您需要根據使用者提供的素材多寡，自動判斷並選擇最適合的模式來執行任務。

## 🚦 模式選擇邏輯
*   **Mode 1：圖文錨定模式 (Anchored Mode)**
    *   **觸發條件**：使用者提供了結構完整的長文、DOCX 或 Markdown 筆記，要求依據原文製作簡報。
    *   **核心精神**：1:1 鎖定文案，精準分頁。
*   **Mode 2：生成式企劃模式 (Generative Design Mode)**
    *   **觸發條件**：使用者只有一個主題、初步構想，或是要求從零開始企劃一份「圖片式簡報」。
    *   **核心精神**：5 步引導企劃，產出 ASCII 排版，最後生成精美圖片。

---

## 【Mode 1】圖文錨定模式工作流

如果您判斷應進入 Mode 1，請嚴格遵守以下步驟：

### 必讀參考文件 (Mode 1)
- `references/Soul_Logic.md`: 定義了章節分頁邏輯、圖片調用優先級。
- `references/Body_YAML_Template.md`: 定義了最終輸出的 YAML 資料結構。
- `references/IP_Asset_Catalog.md`: 個人 IP 圖庫。

### Step 1：環境設定與 IP 詢問
1. 確認已讀取來源文件。
2. 主動詢問：「本次簡報是否需要開啟『個人 IP』圖庫配圖功能？」 (等待回覆)

### Step 2：產出章節對應清單 (Slide Mapping)
- 根據來源文件與 IP 選擇，產出章節對應清單。
- 每偵測到一個獨立大項（如：一、二...）必須強制開啟新頁。
- (等待使用者同意)

### Step 3：輸出完整 YAML 架構
- 套用 `Body_YAML_Template.md`，輸出完整的 YAML 至 `presentation_body.yaml`。

### Step 4：IP 圖像生成 (選用)
- 若開啟 IP，調用 `generate_image` 工具，並將 `resources/個人IP.png` 作為墊圖，生成各頁插圖。

### Step 5：自動組裝簡報
- 執行腳本將 YAML、DOCX 與圖片合成實體 `.pptx`：
  ```bash
  python3 ~/.gemini/antigravity/skills/presentation-architect/scripts/build_pptx.py <YAML路徑> <圖片目錄> <DOCX路徑>
  ```
- **中文字體**：預設使用 `Microsoft JhengHei`；macOS 環境 fallback 至 `PingFang TC` 或 `Noto Sans TC`。
- 建議在文字層疊加半透明深色底框，避免白色文字被明亮背景吃掉。

---

## 【Mode 2】生成式企劃模式工作流

如果您判斷應進入 Mode 2，請嚴格遵守以下 5 步引導：

> **[!] 重要原則**：在引導使用者時，必須一步一步來。每完成一個步驟後，必須**暫停並等待確認**。

### 必讀參考文件 (Mode 2)
- `references/prompts.md`: 5 步引導的提示詞模板。
- `references/methodology.md`: ASCII PPT 排版方法論。

### Step 1：先定義簡報任務
- 詢問構想（主題、對象、目的）。
- 套用 `prompts.md` 的 Step 1 模板進行分析並輸出核心主張。
- (等待確認)

### Step 2：產生完整頁面架構與 ASCII 排版
- 套用 Step 2 模板，設計大綱（12-15頁）。
- 結合 `methodology.md` 的邏輯，為每一頁繪製 ASCII 框架排版。
- (等待確認)

### Step 3：建立統一視覺風格
- 套用 Step 3 模板，定義視覺風格規範（色彩、字體等），並與使用者確認比例（如 16:9）。
- (等待確認)

### Step 4：直接產生「圖片式簡報頁面」
- 套用 Step 4 模板，根據風格與 ASCII 框架，調用 `generate_image` 工具逐頁生成圖片。
- **排版解決方案**：若產出 1:1 圖片，請勿直接拉伸。執行 `scripts/generate_presentation.py` 透過「左圖右文」交錯版型契合 16:9：
  ```bash
  python3 ~/.gemini/antigravity/skills/presentation-architect/scripts/generate_presentation.py
  ```
- (交由使用者檢視)

### Step 5：產生講稿
- 套用 Step 5 模板，為每一頁產出 120~200 字口語化講稿與轉場句。

---

## 輸出路由表（版型廠串接）

企劃完成後（無論 Mode 1 或 Mode 2），根據使用者需求選擇最適合的輸出載體：

| 使用者說... | 推薦 Skill + 模式 | 輸出 | 說明 |
|------------|------------------|------|------|
| 「全圖版」「文字燒入圖片」「baked」 | → `soil-image-deck` **baked** | `.pptx`（每頁一圖，不可編輯） | 社群分享、直播、海報感 |
| 「全圖＋可編輯文字」「plate」「之後要改」 | → `soil-image-deck` **plate** | `.pptx`（底圖+文字框） | 需要事後修改文字 |
| 「互動式」「網頁」「Chart.js」「HTML」 | → `soil-html-deck` | 單一 `.html` | 線上分享、直播、互動表格 |
| 「教學簡報」「課堂」「可編輯」 | → `soil-teaching-deck` | `.pptx`（純文字物件） | 課堂教學、認知最佳化 |
| 「套用模板」「編輯現有簡報」 | → `pptx` | `.pptx` | 底層工具 |
| 未指定格式（Mode 1/2 預設） | → 本 Skill 內建腳本 | `.pptx` | 無需額外 Skill |

> **主動詢問原則**：
> - 企劃完成後，若使用者未指定輸出格式，主動詢問：「您希望以哪種格式輸出？（全圖式 baked / 全圖式 plate 可編輯 / 互動網頁 / 教學簡報）」
> - 若使用者選了 `soil-image-deck` 但未指定 baked/plate，詢問：「請問要文字燒入圖片（baked），還是底圖+可編輯文字（plate）？」

---

## 品質驗證

簡報產出後，執行以下驗證步驟：
1. **文字可見性**：確認所有文字在背景圖上清晰可讀（尤其是 baked 圖片中的中文字）。
2. **頁面完整性**：確認每一頁都包含核心訊息與對應配圖。
3. **中文字體渲染**：確認繁體中文正確顯示，無亂碼或缺字。
4. **風格一致性**：確認全簡報的色彩、字型、排版風格統一。

> 若環境支援，可使用 `pptx` skill 的 `scripts/thumbnail.py` 生成縮圖檢查。

---

## 中文簡報設計守則

- **字體 fallback**：`"Microsoft JhengHei"` → `"Noto Sans TC"` → `"PingFang TC"` → `sans-serif`
- **標題字數**：每頁大標題建議 ≤ 10 個中文字
- **baked 圖片文字**：AI 圖片中的燒入文字建議 ≤ 20 個中文字，並加入半透明底框確保可讀性
- **用詞規範**：使用繁體中文（台灣用語），避免簡體字或大陸用語
