# 水墨風解說：實際踩過的坑

這份清單是「把水墨加進現有解說影片」的專用版。從零做水墨短片請看 `ink-wash-short-film/references/pitfalls.md`。

## A. 策略

### A1. 把 L1 做成 L3

- 一開始就想整片重畫，結果內容、時間軸、字幕全部要重做。
- 先問：這支片的價值在內容還是視覺？若內容是資料／教學，通常 L1 或 L2 就夠。
- 只有「開場、概念比喻、結論」值得重畫；中間的圖表與操作畫面保留原樣。

### A2. 資料與 UI 也水墨化

- 圖表格線、數字、按鈕、QR code 被紙紋蓋住，可讀性直接崩。
- 資料區保留原色與原對比；只加外框、紙底或章節插卡。
- 品牌色不要整片 grade；先問品牌色能不能偏暖。

### A3. 風格不一致

- 原片是冷色科技感，硬套暖紙色會像兩種影片接在一起。
- L1 先做「低濃度」：墨邊 0.35、紙紋 0.25；讓它像濾鏡，不像換了一套美術。
- 插卡的紙色要跟原片一致；不一致會像貼紙。

## B. 來源與格式

### B1. H.264 沒有 alpha

- 把透明水墨層輸出成 `.mp4`，透明區會變黑。
- 有 alpha 的格式：PNG 序列、ProRes 4444（`yuva444p10le`）、WebM VP9（`yuva420p`）。
- 交付前用 `ffprobe` 看 `pix_fmt`；看到 `yuv420p` 就沒有 alpha。

### B2. 沒加 `-loop 1`

- 單張 PNG 當輸入只會有一幀，overlay 可能只出現瞬間或直接失敗。
- 加 `-loop 1`，並用 `-shortest` 或 `-t` 控制長度。

### B3. `-shortest` 切掉音訊

- 圖片是無限 loop；`-shortest` 會選最短的 stream。若音訊比畫面短，片尾會被切。
- 先 `ffprobe` 看 audio duration；用 `-t <video duration>` 或先補齊音訊。

### B4. VFR 來源

- 手機螢幕錄影常是 variable frame rate；overlay 會漂或抖。
- 先轉成固定 fps 的中間檔，再做 overlay；不要直接在 VFR 上疊。
- 轉檔時用來源主要 fps，不要自動猜成 24。

### B5. HDR／色彩空間

- HDR 來源直接套 sRGB 紙紋會過亮或偏色。
- 先確認 `color_transfer`／`color_primaries`；必要時先轉 SDR 工作檔，再套 overlay。
- 一般 sRGB 解說影片不用特別處理，但不要忽略 ffprobe 的 `color_space`。

## C. 合成

### C1. `blend=multiply` 不是 CSS

- CSS 的 `mix-blend-mode: multiply` 會處理 alpha；ffmpeg 的 `blend` 對透明區域不友善，透明的地方容易變黑。
- 優先用 `overlay` ＋ RGBA PNG；顏色與 alpha 已經烘在圖裡。
- 一定要用 `blend` 時，先把 overlay flatten 成 full-frame，再用 `all_opacity` 控制。

### C2. 圖層順序

- 正確：video → 紙紋 → 墨邊 → 文字。
- 若把紙紋放最上，字幕會變灰；若把墨邊放 video 下面，等於沒加。
- HyperFrames 用 `z-index`；ffmpeg 用 filter 順序。兩者都不要靠 track index。

### C3. 濃度過高

- 一次加到 0.8，畫面像蓋了一層髒玻璃。
- 先 0.35，再看 100% 裁切；每次只加 0.05–0.1。
- 紙紋比墨邊更容易過頭；它會提亮暗部、拉黃膚色。

### C4. 兩層都太強

- 墨邊＋紙紋＋grade 三個一起上，暗部會死。
- 若已經 grade，紙紋降到 0.25；若紙紋明顯，grade 的 contrast 回到 1.0。
- 一次只改一個變數。

### C5. Alpha 邊緣黑邊／白邊

- PNG 若是非預乘 alpha，合成邊緣會出現黑邊。
- 用 PIL 輸出 RGBA 時保持 straight alpha；ffmpeg `overlay` 會處理。
- 若看到白邊，檢查是不是把透明區填成白色再壓縮。

## D. HyperFrames

### D1. `<img>` 只出現 3 秒

- 有 `data-start` 的 `<img>` 預設 duration 是 3 秒。
- 一定要寫 `data-duration`，且與覆蓋的章節等長。

### D2. root duration 太短

- overlay 比 root 長，最後會被裁；lint 會警告 `clip_ends_past_root_duration`。
- 把 root `data-duration` 設到最後一個 clip 的結束，或縮短 overlay。

### D3. 把 overlay 放進 timed wrapper

- 巢狀 clip 的 `data-start` 可能從 composition 起算，也可能相對；容易默默跑掉。
- 放 root 層，用絕對秒數最穩。

### D4. `data-start` 參考 id 打錯

- 解析不到 id 會默默變 0；字幕／overlay 會在片頭就出現。
- 運算子兩邊要有空格：`intro - 0.4`，不是 `intro-0.4`。
- 用 `npx hyperframes timeline` 看實際 start。

### D5. track index 不是層級

- `data-track-index` 只是 Studio 的顯示軌；render 不看。
- 前後由 CSS `z-index` 決定。兩 clip 同 track 重疊是合法的。

### D6. video 與 wrapper 都 `data-start`

- lint 會報 `video_nested_in_timed_element`；render 可能拿到錯的 source frame，clip 中途消失。
- 時間只放 video 或 wrapper 其中一層。

### D7. 雙聲

- video 已經有聲音，又放同一份 `<audio>`，會回音／雙聲。
- 用 `data-has-audio="true"`，或把 video 靜音後只放 `<audio>`；不要兩者都來。

### D8. `mix-blend-mode` 外溢

- 沒有 `isolation:isolate` 時，混合可能跟頁面背景或其他 composition 互相影響。
- root 加 `isolation:isolate`；必要時改用普通 alpha overlay。

### D9. runtime 隨機

- 用 `Math.random()` 畫紙紋／墨點，seek 不穩定，draft 與 final 不同。
- 紙紋預先渲染成 PNG；真要動態，用 seeded noise 或固定序列。

### D10. 只看 lint 不看 check

- `hyperframes check` 要看到 N samples（N>0）；「沒有錯誤」不代表 browser session 跑過。
- draft 一定要抽邊界幀。

## E. 文字與可讀性

### E1. 紙紋壓在字上

- 燒進畫面的字幕無法用 z-index 救；只能讓覆蓋層中心透明、底部淡出。
- 獨立字幕圖層：文字 z-index 高於紙紋與墨邊。
- 若字在畫面中央，墨邊不要延伸到中央；用 `--safe-bottom` 只能救底部。

### E2. 對比不足

- 紙紋會提亮暗部，白字可能變灰；墨邊會壓暗，黑字可能糊。
- 目標：正文 ≥ 4.5:1、標題 ≥ 3:1；沒把握就抽 100% 裁切量。
- 必要時給文字加一層很淡的紙色底（不是黑色描邊），或把 overlay 從文字區挖掉。

### E3. 字體

- 水墨插卡用繁體中文字體（標楷體、楷書、宋體）；不要用簡體預設字。
- 字體要嵌入或轉曲線；不要依賴觀眾系統字。
- 插卡字數不要多；水墨標題適合 4–8 字。

### E4. 印章與 logo

- 紅印不要蓋在字幕、價格、按鈕、QR code 上。
- 印章是點綴，不是每幕都蓋；片頭、章節、片尾各一次就夠。
- 品牌 logo 若必須保留原色，不要讓紙紋壓上去。

## F. 旁白、字幕與時間軸

### F1. 為了視覺重配旁白

- 原本的旁白已經跟剪輯綁好；重配會連帶改字幕、音樂、停頓。
- 能不重配就不重配；先做 L1，真的需要再 L2。

### F2. 重配後字幕漂移

- 新 TTS 長度不同，字幕時間會對不上。
- 先鎖旁白，再重建字幕時間，最後才套視覺；不要用 overlay 掩蓋。

### F3. 台灣讀音

- 「著急」讀 ㄓㄠ ㄐㄧ；字幕保留「著急」，TTS 發音稿用「招急」。
- 先 A/B 實測，不要憑猜測改全部。
- 其他可能地雷：角色（腳色）、重複（蟲複）；遇到再測。

### F4. 尾端截斷

- VoxCPM2 偶爾吃掉句尾；每句聽最後 0.3 秒。
- 截斷就換 seed，不要用淡出遮。
- 最後一句與片尾至少留 2 秒。

### F5. 48 kHz

- VoxCPM2 輸出 48 kHz；混音前轉 44.1 kHz。
- 不要手動先轉再讓 build 二次重取樣。

### F6. 雙聲／重軌

- 同一份旁白放兩個 `<audio>`，或 video 帶聲又加 audio，會雙聲。
- HyperFrames 用 `data-has-audio` 或獨立 audio，二選一。
- ffmpeg 用 `-map 0:a?` 只保留原音，不要另外混同一份。

### F7. 音量

- 套水墨不影響音量，但重壓音訊會。
- 盡量 `-c:a copy`；要重混才重壓。
- 目標約 −14 LUFS、true peak ≤ −1 dBFS。

## G. 審查與交付

### G1. 只看 still

- 紙紋在靜態看起來剛好，動起來會閃；墨邊在暗景會消失。
- 至少抽 8 幀：開場、每個章節邊界、片尾。
- 每個邊界看前後 0.4 秒。

### G2. 只看小圖

- 100% 裁切看字邊、臉、圖表、alpha 邊緣。
- contact sheet 只看整體節奏，不能取代 1:1。

### G3. 多次重壓

- 先壓一版 overlay，再壓一版字幕，再壓一版上傳，紙紋會糊。
- 一次完成；中間檔用高品質，最終只壓一次。

### G4. 檔案規格

- 交付前 `ffprobe`：codec、解析度、fps、audio、duration。
- 平台需要 `faststart`；網路播放先出畫面。
- 有 alpha 的素材不要用 H.264 交付。

### G5. 保留原檔

- 不要覆蓋母帶；輸出 `_ink_v1`、`_ink_v2`。
- 保留 overlay 的 seed 與 PNG，之後要微調才重現得出來。
