---
name: soundtrack-mixer
description: 🔊 配樂搜尋與混音 | 從 Openverse（520萬+ 免費音檔）搜尋、試聽、下載配樂與音效，並用 ffmpeg 為影片或簡報做專業混音。適用於任何「找音檔」需求：找音樂、找配樂、找 BGM、背景音樂、找音效、sound effect、音效設計、音檔下載、音樂下載、Openverse、試聽換歌、授權授權條款查詢，以及混音處理：淡入淡出、音量調整、響度正規化 loudnorm、ducking 閃避、多段音效排時間軸、疊加到影片、格式轉換。也涵蓋生成式配樂/音效（Generative Music、程序生成 BGM、合成音效、自製音檔、配合畫面時點的音樂、cue 對齊、零授權音樂）：搜不到、要對齊畫面時點或要零授權風險時，用代碼生成音樂與音效。
---

# Audio Soundtrack

透過 Openverse API 搜尋免費音檔，走「候選 → 批次下載試聽 → 換到滿意為止 → 混音」的迴圈，直到選出合適的配樂或音效。

## 核心原則

1. **先問再抓**：需求不明時先確認用途（片頭/訪談/緊張/溫馨/轉場）、長度、是否可能商用、存放資料夾。
2. **全部列，清楚標**：不預設過濾授權，候選一律列出並標示授權代號，`nd`／`nc` 必須醒目警告。
3. **可一直換**：下載後不喜歡就換下一批、換關鍵字或加條件，循環到滿意。舊的採用檔直接覆蓋（若已嵌進影片先問）。
4. **只留採用的**：決定後保留正式檔，刪除 `_candidates/` 其餘候選。

## 工作流程

### 階段 1：釐清需求

確認四件事：**用途情境**（片頭/訪談/懸疑/溫馨/科技感/轉場音效）、**需要長度**、**是否可能商用**（有無廣告或業配）、**下載資料夾**（預設依專案，例如 `assets/audio/`）。

需求已明確就直接進階段 2，不必逐項追問。

### 階段 2：搜尋出候選表

**先讀 [references/api.md](references/api.md)**（端點用法、速率限制、來源分流、英文搜尋詞對照表）。

**再讀 [references/licenses.md](references/licenses.md)（若尚未熟悉授權規則）。**

要點：
- 端點 `https://api.openverse.org/v1/audio/?q=<英文關鍵字>&format=json`，**必須 `format=json`，不可加 `Accept: application/json`**
- 匿名限 `page_size≤20`、翻頁深度 240、約 20 次/分 → 少量精準查詢，不可暴力翻頁
- 來源分流：音效→`source=freesound`、配樂→`source=jamendo`、古典/公有領域→`source=wikimedia_audio`
- 搜尋詞用英文（中文庫極少），可搭配 `-排除`、`|`或、`"精確片語"`
- **候選整片都是 ⛔/⚠️ 時主動提示**可加 `license_type=commercial` 收斂（實測有效）；使用者說「可能商用」就直接套用過濾

回傳 **5–10 筆候選表**，欄位：`#`／標題／創作者／時長／來源／授權（含警告）／簡短適配說明／連結。附上可直接貼片尾的 `attribution` 出處文字。

**搜尋前先判斷是否走第三條路（生成式）**——符合任一條件就跳過搜尋、直接告知使用者並改走生成式：
- 需求是**配合畫面特定時點變化**（特定秒數安靜、劇情轉折處換情緒）→ 素材庫音樂做不到
- 使用者要求**零授權風險**（不願署名/查 nc/nd）
- 關鍵字搜兩輪仍無合適候選

生成式細節讀 [references/generative-music.md](references/generative-music.md)（術語、能力邊界、兩條路徑、選路決策）；生成式音效的可行範圍見 [references/generative-sfx.md](references/generative-sfx.md)（三層分類：可替代/湊合/別勉強）。依賴安裝見 [references/dependencies.md](references/dependencies.md)。

### 階段 3：批次下載試聽迴圈

1. 使用者挑 **2–3 首** → 下載到 `<指定資料夾>/_candidates/`
   - 下載 = 直接 GET 結果的 `url` 欄位（Freesound mp3 preview、Jamendo mp3、Wikimedia ogg 均免登入）
   - 檔名用 `序號_標題.副檔名`，並同時寫入 `.credits.json` 記錄標題/創作者/授權/連結/attribution
2. 使用者試聽後回報：
   - **不喜歡** → 詢問「換一批同關鍵字 / 換關鍵字 / 加條件」→ 回階段 2 重新搜尋
   - **喜歡** → 複製成正式檔名（覆蓋舊檔），刪除 `_candidates/` 內其餘候選
3. 迴圈可重複任意次，直到使用者明確採用。

### 階段 4：ffmpeg 混音

**讀 [references/ffmpeg.md](references/ffmpeg.md)** 取得完整指令範例。

依需求套用，常見組合：
- **背景音樂**：`afade` 淡入淡出 + `volume` 壓低（約 0.15–0.3）
- **有人聲**：`sidechaincompress` 讓 BGM 被說話聲自動壓低
- **影片成品**：`-shortest` 疊進影片軌 + `loudnorm` 響度正規化到 -14 LUFS
- **多段音效**：`adelay` + `amix` 依時間軸排入

每種處理都要回報實際執行的指令與輸出路徑。

## 誠信條款（禁止事項）

1. **不虛構 API 呼叫、不假裝下載成功**——HTTP 200 ≠ 檔案可用；每次下載後必須 `ffprobe`/`volumedetect` 驗證可解碼，失敗就如實回報並重試或換來源。
2. **不偽稱聽過**——本技能無法發聲播放。音檔品質只能透過量測（ffprobe 時長/聲道、volumedetect 峰值、loudnorm 前後 LUFS）判斷。**交付時如實聲明「已完成量測驗證，未親耳試聽」**，並請使用者自行試聽回報。
3. **量測數據不得捏造**——所有 dB/時長數字必須來自實際執行的輸出；引用驗證基準表時說明其為基準非本次結果。
4. **密鑰/憑證永不讀取、打印或提交**（如日後擴充 API 付費源）。

## 檔案結構

```
<指定資料夾>/
├── <正式檔名>.mp3        ← 最終採用
├── <正式檔名>.credits.json ← 出處紀錄
└── _candidates/          ← 試聽用，決定後刪除
```

## 參考檔案

| 檔案 | 內容 | 何時讀 |
|---|---|---|
| [references/api.md](references/api.md) | 端點、參數、搜尋語法、來源分流、英文搜尋詞對照 | 階段 2 搜尋前 |
| [references/licenses.md](references/licenses.md) | CC 授權速查、nd/nc 警告規則、署名四要素 | 出候選表前 |
| [references/ffmpeg.md](references/ffmpeg.md) | 淡入淡出、音量、loudnorm、ducking、時間軸、疊影片 | 階段 4 混音時 |
| [references/generative-music.md](references/generative-music.md) | 生成式配樂：術語、能力邊界、MIDI/正弦波兩路徑、cue 對齊、驗證基準 | 走第三條路前 |
| [references/generative-sfx.md](references/generative-sfx.md) | 生成式音效三層分類（可替代/湊合/別勉強）與用法 | 使用者要生成音效時 |
| [references/dependencies.md](references/dependencies.md) | pretty_midi/FluidSynth/音色庫安裝、格式相容、ffmpeg 量測陷阱 | 路徑 1 缺依賴時 |

## 生成式腳本

| 腳本 | 用途 |
|---|---|
| [scripts/compose_film.py](scripts/compose_film.py) | **首選**：MIDI 作曲層——改常數（BPM/曲式/和弦/靜音區）即改音樂，配 FluidSynth 渲染真鋼琴音色 |
| [scripts/generate_bgm.py](scripts/generate_bgm.py) | 備胎：純標準庫正弦波 BGM，含 `--mute` 秒級時點靜音、calm/tense 轉折 |
| [scripts/generate_sfx.py](scripts/generate_sfx.py) | 6 種音效合成（hum/beep/chime/click/rain/water），零依賴 |

（記譜與哼唱抽取工具另見獨立 skill：`hum-to-score`）

## 擴充預留

**AI 生成音樂**（Suno 式神經網路，需 API key）仍不做——注意與本 skill 的生成式（Generative Music，純規則/代碼，無模型）是不同東西，對外描述勿混用術語，詳見 generative-music.md 術語節。
