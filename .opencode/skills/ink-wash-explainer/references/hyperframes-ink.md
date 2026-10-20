# HyperFrames：水墨圖層整合

## 圖層順序

```text
z-index 20  字幕、正文、標題（最上）
z-index 10  重點標註、箭頭、資料 callout
z-index 5   墨邊 ink_edge.png
z-index 4   紙紋 paper_grain.png
z-index 0   原始 video / 既有畫面
```

- 文字一定要在紙紋與墨邊 **之上**。若字幕是燒在 video 裡，就沒有「之上」；只能讓覆蓋層中心透明，並把底部 10–15% 淡出。
- `data-track-index` 只是 Studio 的顯示軌，**不控制前後**；用 CSS `z-index`。
- 在 root 上加 `isolation: isolate`，讓 `mix-blend-mode` 只在這個 composition 內混合，不要跟頁面背景或別的 composition 互相影響。

## 最小可用結構

```html
<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <style>
    html, body { margin: 0; background: #f5f2e9; }
    #root {
      position: relative;
      width: 1920px;
      height: 1080px;
      overflow: hidden;
      isolation: isolate;
      background: #f5f2e9;
    }
    .clip {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    #captions {
      position: absolute;
      inset: 0;
      z-index: 20;
      pointer-events: none;
    }
  </style>
</head>
<body>
  <div id="root" data-composition-id="main"
       data-width="1920" data-height="1080" data-duration="60">

    <video id="talk" src="assets/explainer.mp4"
           data-start="0" data-duration="60"
           data-has-audio="true" data-track-index="0"
           style="position:absolute; inset:0; width:100%; height:100%; object-fit:cover"></video>

    <img id="paper" class="clip" src="assets/ink-overlay/paper_grain.png"
         data-start="0" data-duration="60" data-track-index="1"
         style="z-index:4; mix-blend-mode:soft-light; opacity:.38; pointer-events:none">

    <img id="ink" class="clip" src="assets/ink-overlay/ink_edge.png"
         data-start="0" data-duration="60" data-track-index="2"
         style="z-index:5; mix-blend-mode:multiply; opacity:.45; pointer-events:none">

    <div id="captions" data-start="0" data-duration="60">
      <!-- 字幕／正文；由 captions build 產生，或手寫 -->
    </div>
  </div>

</body>
</html>
```

> 這個例子是靜態 clip：root 有 `data-duration`、每個 clip 有 `data-start`／`data-duration`，不需要另外註冊 timeline。若專案已有 `window.__timelines["main"]`，不要重複註冊；把覆蓋層加進現有 timeline 所在的檔案即可。HyperFrames 的 root duration 是 `data-duration`，不是 timeline 長度。

## 只覆蓋某幾章

把 overlay 放在 root 層，使用 **絕對秒數**：

```html
<img id="ink_ch1" class="clip" src="assets/ink-overlay/ink_edge.png"
     data-start="12.5" data-duration="8.0" data-track-index="2"
     style="z-index:5; mix-blend-mode:multiply; opacity:.42">

<img id="ink_ch2" class="clip" src="assets/ink-overlay/ink_edge.png"
     data-start="34.0" data-duration="6.5" data-track-index="2"
     style="z-index:5; mix-blend-mode:multiply; opacity:.42">
```

- `data-start` 是 composition 的絕對秒數，不是「上一個 clip 結束後」。
- 要相對時間可以用 `data-start="intro - 0.4"`，但 **運算子兩邊要有空格**；`intro-0.4` 會被當成不存在的 id，默默從 0 開始。
- 解析不到的 id 也會默默變 0；打完用 `npx hyperframes timeline` 檢查。

## 水墨插卡（L2）

### 做法 A：靜態標題卡

1. 用 `ink-wash-short-film` 的 `InkText` 產生 1920×1080 PNG（透明或紙色）。
2. 放到 `assets/ink-cards/`。
3. 在 root 層加：

```html
<img id="chapter_card" class="clip" src="assets/ink-cards/ch1.png"
     data-start="11.8" data-duration="2.4" data-track-index="3"
     style="z-index:15; pointer-events:none">
```

- 卡片前後各留 0.2 秒；不要蓋住旁白的第一個字。
- 若卡片是紙色底，確認紙色與原片一致；不一致會像貼紙。
- 卡片在 root 層，`data-duration` 一定要寫；`<img>` 不寫只會顯示 3 秒。

### 做法 B：預渲染筆刷轉場

- 用 PNG 序列或 ProRes 4444 渲染 0.5–0.8 秒的 alpha 轉場。
- 序列命名 `wipe/%06d.png`，放進 composition 的 `assets/`。
- 在 HyperFrames 裡用 `<img>` 序列較麻煩；建議直接把轉場 **烘進**一支帶 alpha 的影片，再用 `<video>` 疊。
- 不要用 runtime `Math.random()` 畫筆刷；seek 會不穩定，draft 與 final 也會不同。
- 轉場期間避免字幕；把字幕排在轉場後 0.15 秒。

## 聲音

- 原始 video 有聲音：`data-has-audio="true"`，不要再放同一份 `<audio>`。
- 原始 video 靜音：`muted`；旁白另放 `<audio data-start=...>`。
- 若用 detach／link 分軌：video 與 audio 的 `data-start`、`data-duration`、`data-media-start` 要一致；`data-track-index` 可以不同。
- 不要為了套 overlay 改 `data-start`；聲音會跟著 video 移。
- 輸出前確認 audio clip 沒有超出 root duration。

## 檢查指令

```powershell
npx hyperframes lint
npx hyperframes check
npx hyperframes timeline
npx hyperframes render --quality draft --output renders/ink_draft.mp4
```

- `lint` 會抓：clip 超過 root、image 缺 duration、video 嵌套 timed ancestor、audio 重軌。
- `check` 要看有 N samples（N>0），不要只看「沒有錯誤」。
- `timeline` 會列出每個 clip 的實際 start／end；用來確認 overlay 沒有默默跑到 0。
- draft 出來後抽 0、每個章節邊界、片尾，總共至少 8 幀。

## HyperFrames 常見坑

| 坑 | 症狀 | 修法 |
|---|---|---|
| `<img>` 沒寫 `data-duration` | 只出現 3 秒 | 補上與章節相同的 duration |
| root duration 太短 | overlay 最後被裁 | 把 root `data-duration` 設到最後 clip 結束 |
| 把 overlay 放在 timed wrapper 裡 | 開始時間變成相對或 0 | 放 root 層，用絕對秒數 |
| `data-start` 參考 id 打錯 | 默默從 0 開始 | 用 `hyperframes timeline` 驗；運算子留空格 |
| 用 track index 想控制層級 | overlay 在 video 下面 | 用 `z-index`；track 只是顯示軌 |
| video 與 wrapper 都 `data-start` | lint `video_nested_in_timed_element` | 時間只放 video 或 wrapper 其中一層 |
| `mix-blend-mode` 跟頁面背景混 | 顏色怪、紙色外溢 | root `isolation:isolate`；必要時用普通 alpha |
| 紙紋壓在字上 | 字幕變灰 | 文字 `z-index` 提高；燒進畫面的字靠中心透明 |
| 影片有聲又加 audio | 雙聲、回音 | 只留一個來源；`data-has-audio` 或 `<audio>` |
| 24/30 fps 混用 | 轉場抖、frame 重複 | overlay 與來源同 fps |
