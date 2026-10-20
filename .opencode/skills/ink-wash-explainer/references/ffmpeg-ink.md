# ffmpeg：水墨 overlay 合成

## 先確認來源

```powershell
ffprobe -v error -show_entries format=duration,size `
  -show_entries stream=index,codec_type,codec_name,width,height,r_frame_rate,pix_fmt,sample_rate,channels `
  -of default=noprint_wrappers=1 input.mp4
```

- 有無音訊？`codec_type=audio`
- fps 是多少？overlay 要跟它一致。
- 字幕是否燒進畫面？燒進去的話，覆蓋層只能靠中心透明＋底部安全區。

## 1. 靜態 PNG：墨邊＋紙紋

這是最常用的 L1。**先從 opacity 0.35–0.45 開始**。

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

重點：

- `colorchannelmixer=aa=` 是整體 alpha；不是 CSS 的 opacity，但效果接近。
- `overlay` 會尊重 PNG 的 alpha；中心透明處不會蓋住畫面。
- `-map 0:a?` 的 `?` 表示「有音訊就保留，沒有也不報錯」。
- `-c:a copy` 不重壓音訊；避免世代損失。
- `-shortest` 讓無限 loop 的圖片在影片結束時停。**若原音比畫面短，不要用 `-shortest`**，改用 `-t <duration>`，否則片尾音訊會被切。
- `format=yuv420p` 是最後才轉；overlay 在中間用 RGBA。

### 只加墨邊

```powershell
ffmpeg -y -i input.mp4 -loop 1 -i ink_edge.png `
  -filter_complex "[0:v][1:v]overlay=0:0:format=auto:shortest=1,format=yuv420p[v]" `
  -map "[v]" -map 0:a? -c:v libx264 -crf 18 -preset slow `
  -c:a copy -movflags +faststart output_ink.mp4
```

### 只加紙紋

```powershell
ffmpeg -y -i input.mp4 -loop 1 -i paper_grain.png `
  -filter_complex "[1:v]format=rgba,colorchannelmixer=aa=0.35[paper];`
    `[0:v][paper]overlay=0:0:format=auto:shortest=1,format=yuv420p[v]" `
  -map "[v]" -map 0:a? -c:v libx264 -crf 18 -preset slow `
  -c:a copy -movflags +faststart output_paper.mp4
```

## 2. 動態 alpha overlay

### 2.1 PNG 序列 → ProRes 4444

```powershell
ffmpeg -y -framerate 24 -i overlay/%06d.png `
  -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le overlay.mov
```

確認 alpha：

```powershell
ffprobe -v error -select_streams v:0 `
  -show_entries stream=codec_name,pix_fmt,width,height,r_frame_rate `
  -of default=noprint_wrappers=1 overlay.mov
```

應該看到 `prores`、`yuva444p10le`。

合成：

```powershell
ffmpeg -y -i input.mp4 -i overlay.mov `
  -filter_complex "[0:v][1:v]overlay=0:0:format=auto:shortest=1,format=yuv420p[v]" `
  -map "[v]" -map 0:a? -c:v libx264 -crf 18 -preset slow `
  -c:a copy -movflags +faststart output_ink.mp4
```

### 2.2 WebM VP9 alpha

```powershell
ffmpeg -y -framerate 24 -i overlay/%06d.png `
  -c:v libvpx-vp9 -pix_fmt yuva420p -auto-alt-ref 0 `
  -b:v 0 -crf 24 overlay.webm
```

- 瀏覽器支援較好，但編碼慢。
- 不是所有播放器都吃 alpha WebM；交付前用目標播放器測。
- H.264／MP4 **沒有 alpha**；透明層輸出 `.mp4` 會變黑底。

## 3. 色彩與質感

先做輕微 grade，再上紙紋：

```text
eq=contrast=0.97:saturation=0.90:brightness=0.01
```

- 紙紋本身會提亮暗部；不要再把 contrast 拉高，否則黑會死。
- 人物膚色變黃時，把 `paper_grain` 的 opacity 降到 0.25，或改用 `--no-paper` 只留墨邊。
- 品牌色偏移時，不要整片 grade；只加外框，資料區保留原色。
- 需要紙色底（不是 overlay）時，才用 `colorchannelmixer` 或 `curves` 整體調；那會改變所有顏色，要另外檢查。

## 4. 音訊與長度

- 保留原音：`-map 0:a? -c:a copy`。
- 若原音是 48 kHz，不要為了影片改成 44.1；播放器會處理。要重混才轉。
- 片尾不要用 `-shortest` 硬切；先確認 `ffprobe` 的 audio duration。
- 需要標準化時，單獨做：

```powershell
ffmpeg -i input.mp4 -af "loudnorm=I=-14:TP=-1.0:LRA=11" `
  -c:v copy -c:a aac -b:a 192k output_norm.mp4
```

- 旁白優先：音樂 duck 到 −18～−22 dB；不要讓紙墨感犧牲語音清晰度。
- 若重配旁白，先鎖旁白與字幕，再做視覺；不要用 overlay 掩蓋對時錯誤。

## 5. 品質與檔案大小

- 中間檔用 `-crf 18 -preset slow`；最終依平台調整。
- 不要重壓三次；每次重壓都會掉細節，紙紋最容易先糊。
- `-movflags +faststart` 讓網路播放先出畫面。
- 1080p24、60 秒、CRF 18 的檔案通常 10–30 MB；若平台上限較低，先降 CRF 或解析度，不要降 fps。
- 上傳前用 `ffprobe` 確認：`h264`、`1920x1080`、`24/1`、`aac`、`2 channels`。

## 6. 常見錯誤

| 錯誤 | 原因 | 修法 |
|---|---|---|
| 透明區變黑 | 把 alpha 輸出成 H.264 | 用 PNG／ProRes 4444／WebM VP9 |
| overlay 跑到 0 秒 | 圖片沒 `-loop 1`，只出現一幀 | 加 `-loop 1`，並用 `-shortest` 或 `-t` |
| 片尾音訊被切 | `-shortest` 取了較短的音訊 | 改用 `-t <video duration>` |
| 整片灰掉 | 紙紋 opacity 太高 | 降到 0.25–0.35；或只留墨邊 |
| 字幕變灰 | 紙紋壓在燒進畫面的字上 | 用 `--safe-bottom`；或把紙紋換成 edge-only |
| 顏色變黃 | 暖紙色＋高 opacity | 降 paper；或把紙色調中性 |
| 畫面抖 | overlay fps 與來源不同 | 用來源 fps 重跑序列 |
| `blend=multiply` 變黑 | ffmpeg blend 不處理透明 | 用 `overlay` ＋ RGBA；或先把圖層 flatten |
| 兩層 overlay 順序錯 | 先紙後墨 | 先墨（深）再紙（淺），或依測試結果調整 |
| 檔案太大 | CRF 太低／preset 太慢 | 提高 CRF 或降解析度；不要降 fps |
