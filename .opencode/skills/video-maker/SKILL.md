---
name: video-maker
description: 'claude-video-specs 三類影片產生器。活動紀錄 / 教學 / 社群科普，可選男/女聲、背景音樂。'
---

# video-maker — 三類影片產生技能

## 安裝（新電腦）

```powershell
# 1. 複製此 skills 目錄到新電腦
cp -r ~/.config/opencode/skills/video-maker <新電腦>/.config/opencode/skills/

# 2. 一鍵安裝所有依賴
powershell -ExecutionPolicy Bypass -File ~/.config/opencode/skills/video-maker/setup.ps1
```

**手動需要裝的**（如 setup.ps1 已自動裝好則可跳過）：
| 元件 | 檢查 | 安裝 |
|------|------|------|
| Python 3.8+ | `python --version` | [python.org](https://python.org) |
| edge-tts | `pip show edge-tts` | `pip install edge-tts` |
| Node.js 18+ | `node --version` | [nodejs.org](https://nodejs.org) |
| ffmpeg | `ffmpeg -version` | `winget install "FFmpeg (Essentials Build)"` |
| Playwright | `dir "$env:TEMP\cvs-render\node_modules\playwright"` | `npm install playwright` + `npx playwright install chromium`（在 `%TEMP%/cvs-render` 內執行）|
| 源石黑體 | `dir "$env:LOCALAPPDATA\Microsoft\Windows\Fonts\GenSekiGothic2TW-H.otf"` | `Invoke-WebRequest https://github.com/ButTaiwan/genseki-font/raw/master/TW/GenSekiGothic2TW-H.otf` |

## 觸發詞
- 「做一支影片」
- 「啟動 video-maker」
- 「做一支活動紀錄／教學／科普影片」

## 支援三類影片

| 類型 | 片長 | 適合場景 | 版面 |
|------|------|---------|------|
| **01 活動紀錄** | 60–180s | 婚禮、研習、運動會、紀念短片 | 口白 + 大字卡 + BGM 過場 |
| **02 教學影片** | 4–8 min | 學科概念解釋、知識教學 | SOIL 脈絡 + 動畫 + TTS |
| **03 社群科普** | 2–3 min | FB/IG/YT Shorts 知識短片 | 強 Hook + 多版面 + 照片 |

## 工作流程

### 階段 0：前置檢查
1. `python --version` / `node --version` / `ffmpeg -version`
2. `pip show edge-tts`
3. 確認 `%TEMP%/cvs-render/node_modules/playwright` 存在
4. 確認字體已安裝

### 階段 1：腳本與設計（先寫先確認，不可跳過）
1. 產出 **SCRIPT.md**（旁白 + 字卡 + 分鏡）→ 給使用者確認
2. 產出 **DESIGN.md**（字體 / 配色 / 字級 / 版面 / 節奏）→ 給使用者確認
3. 使用者說 **go** 才動工

### 階段 2：旁白生成
1. 複製 `scripts/generate_narration.py` 到專案目錄
2. 修改內文的 `SCRIPT` 陣列（頁碼 + 旁白文字）
3. 執行：`python generate_narration.py`
4. `ffprobe` 取得每頁旁白秒數 → 設 page_dur = ceil(narration_dur) + 1s

### 階段 3：動畫 HTML
1. 寫 `index.html`（依 `specs/` 對應類型的規範）
2. 動畫用純 CSS/JS，不要 requestAnimationFrame 驅動時間軸
3. **每頁 audio 用 `audio.currentTime` 判斷是否換頁**
4. 測試：`npx serve .` 開本地伺服器預覽

### 階段 4：錄製與合成
1. 複製 `scripts/record.cjs` 到專案目錄
2. 修改 `waitForTimeout` 為總片長 + 5s 緩衝
3. **清除舊檔**：`Remove-Item renders/*.webm`
4. 設定環境變數：`$env:NODE_PATH = "$env:TEMP\cvs-render\node_modules"`
5. 執行：`node record.cjs`
6. 看哪個 webm 是新的（或時間最接近的）

### 階段 5：音畫合成
1. pad 各頁旁白到 page_dur：`ffmpeg -i page-NN.mp3 -af apad -t <dur> pNN.mp3`
2. concat 成 master_audio.mp3（在純英文路徑執行）
3. mux：
   ```bash
   ffmpeg -y -ss 0.8 -i <最新.webm> -i master_audio.mp3 `
     -map 0:v:0 -map 1:a:0 `
     -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest final.mp4
   ```
   **要點**：`-ss 0.8` **只加在 video input**，audio 不裁

## 核心原則（踩坑血淚）
| 原則 | 說明 |
|------|------|
| **先腳本、再設計、最後寫 code** | 跳過一定重做（見 GOTCHAS.md A-1~3）|
| **字幕單行 ≤ 25 字** | 太長就拆兩頁，永不換行 |
| **段落間距 1–2s** | page_dur = ceil(narration_dur) + 1s |
| **mux 只裁 video 不裁 audio** | `-ss` 只加在 `-i video.webm` |
| **錄影前清舊 webm** | 防錯拿舊檔 |
| **用 `audio.currentTime` 驅動換頁** | 不用 performance.now() |
| **`-map 0:v:0 -map 1:a:0` 不可漏** | 否則 webm 空白音軌覆蓋旁白 |

## 踩坑紀錄
| 問題 | 解法 |
|------|------|
| 字體未載入就錄影 | `waitForTimeout(3000)` 等字型載入完成才點開始 |
| 音畫不同步 | 用 `audio.currentTime` 驅動換頁，不用 requestAnimationFrame |
| 聲音比畫面快 | CSS transition 縮到 0.15s，audio 延遲 150ms 播放 |
| 開頭空白畫面 | ffmpeg `-ss 0.8~3.2` 裁掉字體載入時間 |
| Playwright 無聲時 currentTime 不推進 | 移除 `--mute-audio` |
| BGM 太小聲 | BGM volume 調至 0.3，使用 `amix weights=1 0.5` |
| Python 中文路徑崩潰 | 設 `$env:PYTHONUTF8=1` |
| ffmpeg concat 中文路徑 | 在純英文路徑（如 `%TEMP%`）產生 list.txt |
| 照片張數 vs BGM 長度失衡 | 每張圖最多 5 秒。若 BGM 過長而照片不足，**實作前先問使用者**：裁 BGM 或接受較長停留 |
| 段落間距過長（3-4s 死寂） | page_dur = ceil(narration_dur) + 1s，間距 1-2s |
| ffmpeg 裁錯音訊導致錯位 | 只對 video input 用 `-ss`，audio 不裁 |
| 多個 webm 殘留導致用錯舊檔 | 錄製前先清 renders/*.webm |

## 參考（已內建於 skills 目錄）
- `specs/01-活動紀錄影片.md` / `02-教學影片.md` / `03-社群科普影片.md`
- `GOTCHAS.md` — 完整踩坑大全
- `scripts/generate_narration.py` — TTS 產生腳本（範本）
- `scripts/record.cjs` — Playwright 錄製腳本（範本）
- `setup.ps1` — 新電腦一鍵安裝