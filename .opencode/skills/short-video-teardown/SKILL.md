---
name: short-video-teardown
description: 🎬 短影音爆款拆解 | 從競品短影音拆解到腳本生成的完整工作流：下載競品影片 → 影片分析（Gemini API 或本地抽幀雙路徑）→ 爆款公式提煉 → 腳本+分鏡生成 → 審校。當使用者提到「拆解影片」、「爆款拆解」、「競品分析」、「帶貨腳本」、「千川素材」、「種草腳本」、「短影音腳本」、「抖音/TikTok/Reels 拆解」時使用。生成的腳本交由 video-script-maker 審校、short-video-maker 製片。
---

# 短影音爆款拆解

從競品短影音拆解到腳本生成的完整工作流。將「憑感覺模仿爆款」變成「AI 系統拆解＋結構化複製」。原版以抖音為主，本版泛化支援抖音 / TikTok / Instagram Reels 等 yt-dlp 支援的平台（分析與公式以抖音電商場景最完備）。

## 環境要求

- `uv`（Python 包管理器）
- `yt-dlp`（影片下載：`pip install yt-dlp`）
- **影片分析二選一**：
  - **路徑 A（Gemini）**：`GEMINI_API_KEY` 環境變數（從 https://aistudio.google/apikey 获取，有免費額度）；可選 `GEMINI_BASE_URL` 自定義端點
  - **路徑 B（本地抽幀）**：`ffmpeg`（抽幀）+ 本 agent 的視覺分析能力，零 API 成本
- **選配**：`faster-whisper`（`pip install faster-whisper`）— 對白逐字稿。沒有它則「文案鉤子/話術」分析欄位標註「未取得逐字稿」，其餘維度照常
- 路徑 A 需要 Chrome 已登入對應平台（提取下載 Cookie）；路徑 B 若平台下載也需要 Cookie，同樣要 Chrome 登入

**路徑選擇**：Step 3 開頭先檢查 `GEMINI_API_KEY`——有則走路徑 A，沒有則走路徑 B，**不因缺 Key 中斷流程**。

**路徑約定**：下文 `SKILL_DIR` 指本 SKILL.md 所在目錄的絕對路徑。運行腳本前先確定實際位置並替換。

## 5 步工作流

### Step 1：收集輸入

**必填**：
- 競品影片連結（1-5 支）
- 產品/主題資訊（名稱、核心賣點、目標人群、價格或訴求）
- 腳本類型：種草 / 投放素材 / 知識科普（依平台調整）

**選填**：產品圖片（視覺參考）、目標時長（種草預設 30 秒）、品牌調性、投放目標

資訊不全時主動詢問缺失項。

### Step 2：下載影片

```bash
uv run SKILL_DIR/scripts/download_short_video.py \
  --urls "URL1" "URL2" \
  --output-dir _temp/short-video-downloads
```

- 支援短鏈、頁面連結、分享文本（自動提取 URL）
- `--cookies-browser` 預設 chrome，可選 edge/firefox
- 失敗時：① 確認瀏覽器已登入該平台 ② 提示手動下載放入 `_temp/short-video-downloads/`

### Step 3：影片分析（雙路徑）

對每支下載成功的影片做 **7 維度深度拆解**（前 3 秒逐幀級分析最關鍵）：

1. **鉤子分析（前 3 秒）⭐**：文案鉤子（類型/轉錄/關聯度）＋視覺鉤子（逐幀構圖/色調/運鏡/信息密度）＋文案×視覺配合＋強度評分
2. **分鏡結構**：`| 時間 | 景別 | 畫面內容 | 旁白/字幕 | 轉場 |` 表格
3. **節奏設計**：快切點、節奏模式、BGM 配合
4. **視覺元素**：色調濾鏡、字幕樣式、產品展示、構圖
5. **轉化設計**：CTA 類型與時機、價格錨定、緊迫感、轉化路徑
6. **合規檢查**：絕對化用語、功效表述、審核風險
7. **可複製要素**：可直接複製 vs 不可複製（獨特場景/達人/品牌勢能）

#### 路徑 A：Gemini 視頻分析

```bash
uv run SKILL_DIR/scripts/analyze_video.py \
  --video "_temp/short-video-downloads/xxx.mp4" \
  --prompt "（下方分析 Prompt）" \
  --model flash --resolution medium \
  --output "_temp/short-video-downloads/analysis-1.md"
```

用 flash + medium 省成本；多支可並行（`run_in_background=true`）。分析 Prompt：

```
作為資深短影音電商分析師，請對這個影片進行 7 維度深度拆解。
特別注意：前 3 秒是最關鍵的部分，需要逐幀級別的詳細拆解。

## 1� 鉤子分析（前 3 秒）⭐ 最關鍵
前 3 秒 = 文案鉤子 + 視覺鉤子，兩條線都要詳細分析。
### 1a. 文案鉤子
- 鉤子類型（反常識/痛點/數據/場景/懸念/利益）
- 鉤子文案完整轉錄
- 文案與產品的關聯度（強/弱）
### 1b. 視覺鉤子（逐幀描述）
- 第 0 秒畫面：構圖、色調、主體
- 視覺鉤子類型（視覺奇觀/產品堆疊/畫面突變/動作衝擊/文字彈出/第一人稱 POV）
- 具體畫面：景別、色調、運鏡、特效、表情動作
- 視覺信息密度
### 1c. 文案×視覺配合
- 是否同步強化同一信息；聲音設計（音效/BGM/語氣變化）
- 綜合鉤子強度評分（1-10）及理由

## 2. 分鏡結構（表格）
| 時間 | 景別 | 畫面內容 | 旁白/字幕 | 轉場方式 |

## 3. 節奏設計：快切點、模式（快-慢-快/漸進/脈沖）、BGM 配合
## 4. 視覺元素：色調濾鏡、字幕樣式與時機、產品展示方式、構圖
## 5. 轉化設計：CTA 類型與時機、價格錨定、緊迫感、轉化路徑
## 6. 合規檢查：絕對化用語、功效表述、審核風險
## 7. 可複製要素：可直接複製的（鉤子句式/分鏡/視覺風格/CTA 話術）vs 不可複製的

請用繁體中文輸出，盡量詳細。
```

#### 路徑 B：本地抽幀分析（無 API Key）

1. **前 3 秒密集抽幀**（逐幀或 6-8fps）：
   ```bash
   ffmpeg -i 影片.mp4 -t 3 -vf fps=8 "_temp/short-video-downloads/hook-%03d.png"
   ```
2. **全片場景偵測關鍵幀**：
   ```bash
   ffmpeg -i 影片.mp4 -vf "select='gt(scene,0.3)',showinfo" -vsync vfr "_temp/short-video-downloads/scene-%03d.png"
   ```
3. **（選配）對白逐字稿**——已安裝 faster-whisper 時：
   ```bash
   ffmpeg -i 影片.mp4 -vn -ac 1 -ar 16000 "_temp/short-video-downloads/audio.wav"
   # 然後用 faster-whisper 轉錄（medium 模型即可），輸出含時間碼的逐字稿
   ```
   未安裝時：文案鉤子/旁白/CTA 話術欄位改由字幕截圖推斷或標註「未取得逐字稿」。
4. **由 agent 看圖分析**：讀取 hook-*.png 與 scene-*.png，按上方同一份 7 維度 Prompt 產出 analysis-1.md（逐幀部分依抽幀密度分析；聲音設計與 BGM 欄位標註「本地路徑未分析音軌」）。

### Step 4：爆款公式提煉 ← 使用者確認點

- **有競品影片**：讀所有 `analysis-*.md`，對照 `references/proven-formulas.md` 的已驗證公式，匯總提煉：品類共性、鉤子公式、最佳分鏡結構、節奏模板、轉化路徑、風險提示。存為 `_temp/short-video-downloads/[產品名]-爆款分析匯總.md`
- **無競品影片**：直接用 `references/proven-formulas.md` 選最接近品類的公式當基線，並提醒「缺品類針對性，建議補拆解」

**展示給使用者確認**：分析是否準確、腳本類型、補充產品資訊。

**公式沉澱**：新品類公式追加到 `references/proven-formulas.md`，持續積累。

### Step 5：腳本＋分鏡生成

**生成前**：讀 `references/script-style-samples.md`（口語風格範例）、`references/analysis-dimensions.md`（類型區別表）、Step 4 匯總。

**腳本要求**：
- 開頭 3 秒強鉤子（用分析中最有效的鉤子類型）
- 中段核心賣點最多 3 個
- 結尾明確 CTA
- 全文口語化（短句 ≤15 字）、具體數字錨點、感官描述、情感觸發
- 不用絕對化用語，符合平台審核規範
- 標注每段預估時長

**分鏡表**（前 3 秒必須詳細描述視覺鉤子）：

| 鏡號 | 時長 | 景別 | 畫面內容 | 旁白/字幕 | 拍攝建議 |
|------|------|------|---------|----------|---------|

前 3 秒分鏡必含：視覺鉤子類型、具體畫面（構圖/色調/運鏡/特效）、第一幀設計、文案×畫面配合。

**投放素材差異**：前 3 秒用數據型或痛點型鉤子（不用問句開頭）、信息密集賣點直給、CTA 明確引導點擊/下單。

**保存**到 `_temp/short-video-downloads/[產品名]-腳本.md`

### Step 6：審校 ← 使用者確認點

初稿完成後**交給 `video-script-maker`**（本機技能）做完整三遍審校（內容 → 口語化 → 演示標注）。其中投放類腳本額外檢查：

**廣審合規（最易被拒）**：
- ❌ 絕對化用語：最好/第一/100%/唯一/全網最低
- ❌ 時間+功效承諾（高危）：「60天淡斑83%」→「堅持用，斑真的有變淡」——**具體時間+具體功效=必須改寫**，即使數據來自官方臨床報告
- ❌ 功效措辭：治好/根治 → 緩解/幫助改善；美白/抗衰 → 提亮/讓皮膚狀態更好
- ❌ 對比貶損、虛假緊迫感、未標注的扮演使用者

**改寫原則**：第一人稱體感代替第三人稱數據——「我用了之後感覺...」比「經臨床驗證...」安全。

審校後展示修改清單，確認後應用。

## 文件保存規則

```
_temp/short-video-downloads/
├── xxx.mp4                    # 下載的影片
├── hook-*.png / scene-*.png   # 路徑 B 抽幀
├── audio.wav                  # 路徑 B 音軌（選配逐字稿用）
├── analysis-N.md              # 各支分析結果
├── [產品名]-爆款分析匯總.md
└── [產品名]-腳本.md           # 最終腳本
```

## 參考資源

| 資源 | 路徑 | 用途 |
|------|------|------|
| 分析維度框架 | `references/analysis-dimensions.md` | 7 維度＋類型區別 |
| 已驗證爆款公式 | `references/proven-formulas.md` | 品類公式庫，無競品時的基線，持續沉澱 |
| 口語風格樣本 | `references/script-style-samples.md` | 腳本生成的 few-shot 範例 |
| 影片下載 | `scripts/download_short_video.py` | yt-dlp 多平台下載 |
| Gemini 影片分析 | `scripts/analyze_video.py` | 路徑 A：視頻理解 |

## 完成後的管線

```
short-video-teardown（本技能：拆解+腳本初稿）
  → video-script-maker（審校 + 封標/承接檢查）
  → short-video-maker / knowledge-video-factory（製片出片）
```

## 來源

改編自花叔（Huashu-Design）開源 skill `huashu-douyin-script`（MIT License）。本版改動：抖音泛化為多平台短影音、新增本地抽幀雙路徑（無 Gemini Key 可用）、faster-whisper 列選配逐字稿、審校環節改接本機 `video-script-maker`、移除對作者自有技能的外部引用。
