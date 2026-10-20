---
name: ink-wash-explainer
description: 把現有解說影片、簡報或 HyperFrames 專案加上水墨視覺，不重寫內容與時間軸。三種力度：L1 紙墨覆蓋、L2 水墨插卡／轉場、L3 重點場景重繪。含透明覆蓋層、HyperFrames 與 ffmpeg 合成、alpha 格式、字幕對比、旁白同步與實測坑。當使用者說「把這支解說影片改成水墨風」「加水墨濾鏡」「水墨轉場」「水墨風簡報影片」「幫現有 explainer 套水墨」「不要重做內容只換視覺」時使用。
---

# 水墨風解說影片

## 先選力度

| 力度 | 改什麼 | 不改什麼 | 典型時間 |
|---|---|---|---|
| **L1 紙墨覆蓋** | 紙紋、墨邊、暗角、色調、印章 | 原始畫面、字幕、旁白、時間軸 | 10–30 分 |
| **L2 水墨插卡** | L1 ＋ 標題卡、章節卡、書法引號、筆刷轉場 | 主體內容與資料畫面 | 1–2 小時 |
| **L3 重點重繪** | 選 1–3 個關鍵場景／圖表，用紙墨渲染器重畫 | 旁白、字幕、總長度、其他場景 | 半天–1 天 |

**先問三件事**

1. 來源是 HyperFrames 專案、MP4，還是 PPT／Keynote 匯出的影片？
2. 字幕是燒在畫面裡，還是獨立圖層？這決定覆蓋層能不能壓在字上。
3. 畫面有沒有資料圖表、UI、品牌色？資料與 UI 不要整片水墨化，否則可讀性會崩。

## 不改什麼（硬規則）

- **旁白與時間軸不動**：水墨是視覺層，不是重剪。不要為了套濾鏡而重配旁白或改字幕時間。
- **字幕不動**：字幕稿與 TTS 發音稿分開；若重配旁白，字幕仍用原本用字。
- **資料不動**：圖表數字、座標、品牌色、產品 UI 保留；只加外框、紙底或一章的插卡。
- **不在文字上壓紙紋**：紙紋與墨邊要放在文字圖層下方；燒在畫面裡的字則要靠「中心透明＋底部安全區」。
- **不改 frame rate**：來源 30 fps 就輸出 30 fps；不要為了水墨感改成 24 fps。

## 0. 盤點來源

```powershell
ffprobe -v error -show_entries format=duration,size,bit_rate `
  -show_entries stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels `
  -of default=noprint_wrappers=1 <input>
```

記下：

- 解析度、fps、duration、audio codec／sample rate／channels
- 字幕是否燒進畫面；字幕安全區在哪（通常底部 10–15%）
- 主要構圖：人物、簡報、圖表、終端機、產品畫面
- 品牌色與不能覆蓋的區域（logo、價格、按鈕、QR code）
- 若來源是 HyperFrames：先跑 `npx hyperframes timeline` 與 `npx hyperframes check`

先備份原檔。所有輸出都用新檔名，例如 `renders/explainer_ink_v1.mp4`，不要覆蓋母帶。

## 1. 產生透明水墨覆蓋層

需要 `numpy`、`scipy`、`Pillow`：

```powershell
$py = "$env:USERPROFILE\Documents\OpenCode\Voice\voxcpm2-voice-cloner\.venv\Scripts\python.exe"
$skill = "$env:USERPROFILE\.config\opencode\skills\ink-wash-explainer"
& $py -m pip install -r "$skill\scripts\requirements.txt"
& $py "$skill\scripts\make_ink_overlay.py" `
  --width 1920 --height 1080 --seed 7 `
  --out-dir assets/ink-overlay
```

輸出：

| 檔案 | 用途 | 建議合成 |
|---|---|---|
| `ink_edge.png` | 深墨邊框＋角落墨漬；中心透明 | `multiply` 或 alpha overlay；opacity 0.35–0.6 |
| `paper_grain.png` | 暖紙色＋紙紋；中心很淡、邊緣較明顯 | `soft-light` 或 `screen`；opacity 0.3–0.5 |
| `overlay.json` | 尺寸、seed、用法 | 專案紀錄 |

- 預設 `--safe-bottom 0.10` 會把畫面底部 10% 的覆蓋層淡出，避免壓到字幕。
- 想要更乾淨：`--no-paper` 只留墨邊。
- 想要不同墨跡：換 `--seed`；不要每次渲染都隨機，seed 要寫進交付紀錄。
- `assets/ink-overlay-sample/` 已有一組 1920×1080 範例，可直接試合成；正式專案仍建議用自己的 seed 產生。

**預設不要太重**。先從 `ink_edge` opacity 0.35、`paper_grain` opacity 0.35 開始；不夠再加。解說影片的目標是「有紙墨感」，不是「把畫面蓋掉」。

## 2. 合成：HyperFrames 專案

把覆蓋層放在 **video 之上、字幕與文字之下**。`z-index` 控制前後；`data-track-index` 只是 Studio 的顯示軌，不是層級。

```html
<div id="root" data-composition-id="main"
     data-width="1920" data-height="1080" data-duration="60">

  <!-- 原始解說畫面；有聲音才加 data-has-audio -->
  <video id="talk" src="assets/explainer.mp4"
         data-start="0" data-duration="60"
         data-has-audio="true" data-track-index="0"
         style="position:absolute; inset:0; width:100%; height:100%; object-fit:cover"></video>

  <!-- 紙紋：在 video 上、文字下 -->
  <img id="paper" class="clip" src="assets/ink-overlay/paper_grain.png"
       data-start="0" data-duration="60" data-track-index="1"
       style="z-index:4; mix-blend-mode:soft-light; opacity:.38; pointer-events:none">

  <!-- 墨邊：中心透明，不會蓋住字幕 -->
  <img id="ink" class="clip" src="assets/ink-overlay/ink_edge.png"
       data-start="0" data-duration="60" data-track-index="2"
       style="z-index:5; mix-blend-mode:multiply; opacity:.45; pointer-events:none">

  <!-- 字幕／文字必須在最上層 -->
  <div id="captions" data-start="0" data-duration="60"
       style="position:absolute; inset:0; z-index:20; pointer-events:none">
    ...
  </div>
</div>
```

規則：

- `class="clip"` 給視覺 clip；`<img>` 有 `data-start` 時預設 3 秒，**一定要寫 `data-duration`**。
- 只覆蓋某幾章時，把 `data-start`／`data-duration` 設成絕對秒數；不要放進另一個有 `data-start` 的 wrapper，除非你確定相對時間。
- `<video data-start>` 不要放在也有 `data-start` 的祖先裡；HyperFrames lint 會報 `video_nested_in_timed_element`。
- 根層 `data-duration` 要覆蓋最後一個 clip；覆蓋層比 root 長會被裁掉，lint 也會警告。
- 文字圖層 `z-index` 要高於紙紋與墨邊；`pointer-events:none` 避免擋互動。
- 若原始 video 已含聲音，不要再放同一份 `<audio>`；要分軌才用 detach／link，且 `data-start`、`data-duration`、`data-media-start` 必須同步。
- 覆蓋層是靜態圖也可以；不要用 runtime `Math.random` 做紙紋，否則每次 render 不同、seek 也不穩定。

```powershell
npx hyperframes lint
npx hyperframes check
npx hyperframes render --quality draft --output renders/ink_draft.mp4
```

## 3. 合成：一般 MP4（ffmpeg）

### 3.1 靜態 PNG 覆蓋

```powershell
ffmpeg -y -i input.mp4 `
  -loop 1 -i ink_edge.png `
  -loop 1 -i paper_grain.png `
  -filter_complex "[0:v]eq=contrast=0.97:saturation=0.90:brightness=0.01[base];`
    `[1:v]format=rgba,colorchannelmixer=aa=0.45[ink];`
    `[2:v]format=rgba,colorchannelmixer=aa=0.38[paper];`
    `[base][ink]overlay=0:0:format=auto:shortest=1[v1];`
    `[v1][paper]overlay=0:0:format=auto:shortest=1,format=yuv420p[v]" `
  -map "[v]" -map 0:a? `
  -c:v libx264 -crf 18 -preset slow `
  -c:a copy -movflags +faststart output_ink.mp4
```

- `colorchannelmixer=aa=...` 是整體 alpha；先從 0.35–0.5 試。
- `overlay` 會尊重 PNG 的 alpha；**不要**期待 `blend=multiply` 跟 CSS 的 mix-blend-mode 一模一樣。ffmpeg 的 `blend` 不處理透明區域，容易把透明的地方變黑。
- `-map 0:a?` 保留原音；`-c:a copy` 不重壓。
- `-shortest` 可以避免圖片無限 loop；但如果原檔音訊比畫面短，優先用 `-t <duration>`，不要讓音訊被切。
- 一次完成，不要先壓一版再壓一版；每次重壓都會掉畫質。

### 3.2 動態水墨 overlay（alpha 影片）

若用 PNG 序列或 ProRes 4444：

```powershell
ffmpeg -y -framerate 24 -i overlay/%06d.png `
  -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le overlay.mov

ffmpeg -y -i input.mp4 -i overlay.mov `
  -filter_complex "[0:v][1:v]overlay=0:0:format=auto:shortest=1,format=yuv420p[v]" `
  -map "[v]" -map 0:a? -c:v libx264 -crf 18 -preset slow `
  -c:a copy -movflags +faststart output_ink.mp4
```

- **H.264 沒有 alpha**；把透明層輸出成 `.mp4` 會變黑底。
- 有 alpha 的格式：PNG 序列、ProRes 4444（`yuva444p10le`）、WebM VP9（`yuva420p`，瀏覽器支援較好）。
- overlay 的 fps 要跟來源一致；24 對 30 會抖。
- 若用 WebM alpha：`-c:v libvpx-vp9 -pix_fmt yuva420p -auto-alt-ref 0`，並在瀏覽器測試。

## 4. L2／L3：水墨插卡與重點重繪

### L2：只換章節節奏

- 用 `ink-wash-short-film` 的 `build.py` 或 `InkText` 產生 **透明標題卡**：片名、章節名、一句話引文。
- 輸出 PNG 序列／ProRes 4444，疊在原始影片上；長度 1.5–3 秒。
- 轉場用「收墨到紙色」0.4–0.8 秒，或一筆刷過；不要用大面積 radial mask，會變巨大墨塊。
- 插卡前後留 0.2 秒讓觀眾呼吸；不要把旁白切斷。

### L3：重畫關鍵場景

- 只選 1–3 個「最值得水墨化」的場景：開場、概念比喻、結論。
- 其餘場景保留原畫面，只加 L1 覆蓋；整片重畫通常不划算，也容易風格不一致。
- 用 `ink-wash-short-film` 的 `KTitle`／`K1` 等場景骨架，渲染 **透明背景** 或 **紙色背景** 的片段。
- 若用紙色背景，先確認它跟原片的紙色一致；不一致會像貼上去的。
- 重畫場景的旁白與字幕時間不變；用原音軌對齊，不要重新計時。

## 5. 旁白與時間軸（若需要重配）

**能不重配就不重配。** 原有旁白通常已經跟畫面剪好；重配會連帶改字幕、音樂、停頓。

若一定要重配：

1. 先鎖定旁白與時間軸，再做視覺。不要一邊配音一邊改畫面。
2. 用 `xu-yaowen-tts`；一句一檔，先聽候選，鎖 seed。
3. VoxCPM2 輸出 48 kHz；混音前轉 44.1 kHz。
4. 每句聽最後 0.3 秒；尾端截斷就換 seed，不要用淡出遮。
5. 台灣讀音先 A/B：「著急」讀 ㄓㄠ ㄐㄧ，字幕保留「著急」，TTS 發音稿用「招急」。
6. 字幕與發音稿分開；不要為了好念改字幕。
7. 混音後量測：整合響度約 −14 LUFS、true peak ≤ −1 dBFS；旁白優先，音樂 duck。
8. **不要用視覺 overlay 掩蓋對嘴／對時錯誤**；先修音訊，再套水墨。

HyperFrames 的音訊：一個 video 帶聲音，或一條獨立的 `<audio>`，不要同一份聲音放兩次。剪 video 時聲音會跟著 clip 走；要 J/L cut 才分軌。

## 6. 審查

先做 5 秒測試，不要直接全片：

- 開場 0–5 秒（第一印象）
- 每個章節轉場前後 0.4 秒
- 有字幕／圖表的段落
- 片尾 3 秒

每段抽 3 幀，1:1 看：

1. 文字邊緣是否被紙紋吃掉；深色字在墨邊上是否還清楚。
2. 人物膚色是否被暖紙色拉黃；品牌色是否偏移。
3. 圖表數字是否仍可讀；格線是否被紙紋蓋住。
4. 墨邊是否擋住重要 UI／logo／QR code。
5. alpha 邊緣有沒有黑框或白邊。
6. 聲音是否同步；轉場是否吃掉字。

**驗收門檻**

- 字幕與正文對比盡量 ≥ 4.5:1；標題 ≥ 3:1。
- 墨邊與紙紋的 opacity 以「拿掉後會覺得少一點，但不會覺得畫面被蓋住」為準。
- 全片至少看一次 draft；不要只看 still。
- `ffprobe` 確認 fps、duration、audio 與原片一致。

## 7. 最常踩的坑（摘要）

完整清單見 `references/pitfalls.md`。

- **H.264 沒有 alpha**：透明層輸出 MP4 會變黑底；用 PNG／ProRes 4444／WebM VP9。
- **覆蓋層壓在字上**：紙紋會讓字幕變灰；順序是 video → 紙紋 → 墨邊 → 文字。燒進畫面的字只能靠中心透明＋底部安全區。
- **`blend=multiply` 不是 CSS**：ffmpeg 的 blend 對透明區域不友善；優先用 `overlay` ＋ RGBA，或先把圖層 flatten。
- **`-shortest` 切掉音訊**：圖片 loop 是無限的；若音訊較短，改用 `-t`。
- **HyperFrames 圖層用 z-index，不是 track**：`data-track-index` 只是顯示軌；前後由 CSS 決定。
- **`<img>` 的 `data-duration` 會預設 3 秒**：不寫就只出現 3 秒。
- **video 與 wrapper 都寫 `data-start`**：lint 會報 `video_nested_in_timed_element`；時間只放在其中一層。
- **root duration 沒包住 overlay**：最後一段會被裁掉；先算好總長度。
- **紙紋太重**：整片變灰、膚色變黃；先 0.3，再看 100% 裁切。
- **資料畫面也水墨化**：圖表與 UI 可讀性會崩；資料區保留原色，只加外框。
- **重配旁白卻沒重對字幕**：字幕會漂；先鎖旁白，再鎖字幕，最後才套視覺。
- **多次重壓**：先出高品質 intermediate，再一次最終編碼；不要疊三次 CRF 18。

## 資源

- `scripts/make_ink_overlay.py`：產生透明墨邊與紙紋；支援尺寸、seed、底部字幕安全區。
- `assets/ink-overlay-sample/`：1920×1080 範例（`ink_edge.png`、`paper_grain.png`）。
- `references/hyperframes-ink.md`：HyperFrames 圖層、clip 時間、文字安全區與實際 snippet。
- `references/ffmpeg-ink.md`：靜態／動態 overlay、alpha 格式、色彩與音訊指令。
- `references/pitfalls.md`：合成、格式、HyperFrames、字幕、旁白與效能的完整坑。
- 需要從零做一支水墨短片：用 `ink-wash-short-film`。
- 需要重配旁白：用 `xu-yaowen-tts`。
