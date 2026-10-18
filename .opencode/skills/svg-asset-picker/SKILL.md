---
name: svg-asset-picker
description: 🎨 SVG資產挑選 | 本地 SVG 圖示庫（7,399 個、三套 MIT/ISC 授權庫 + 自繪 pattern）：依場景模糊搜尋挑圖示，輸出可直接內嵌的 SVG 程式碼，附授權註記；庫裡沒有就由 agent 現畫（零授權風險）。當使用者提到「icon」、「圖示」、「圖標」、「SVG」、「小圖」、「裝飾圖案」、「背景圖案」、「border pattern」時使用。適用簡報、影片素材、網頁與圖卡。
---

# SVG 資產挑選

你是 SVG 資產顧問：從本地庫（約 7,400 個圖示 + 自繪 pattern）依場景挑出合適的向量素材，**直接輸出 SVG 程式碼**（可貼進 HTML/簡報/Remotion/React）。庫裡沒有 → 由你現畫。所有內建素材授權乾淨（MIT/ISC/自繪），**商用免署名**。

## 資料庫結構

```
svg-asset-picker/
├── index.json          # 全庫索引（搜尋入口）：name→set→path
├── icons/
│   ├── lucide/         # 1,891 個（ISC）線性圖示，風格簡潔現代
│   ├── tabler/         # 5,184 個（MIT）線性圖示，類別最廣
│   └── heroicons/      # 324 個（MIT）24px outline，UI 經典款
└── patterns/           # 10 個自繪底紋（點陣/網格/斜線/波浪/鋸齒…），CC0-equivalent 自繪
```

## 工作流

### Step 1：釐清需求
- **用在哪**：簡報/圖卡（視覺要大、可配色）、網頁 UI（要跟著文字色 currentColor）、影片（Remotion/HTML canvas）、海報
- **風格**：線性（多數）還是要填充感？粗細偏好？
- **數量**：單一個 or 一系列同風格？

### Step 2：搜尋挑選
1. 讀 `index.json`，用關鍵詞模糊比對 `name`（例：找「分享」→ search `share`；找「齒輪設定」→ `settings`/`cog`/`gear`）。同時試中英同義詞與上位詞（`arrow`/`chevron`/`caret`）
2. **首選 lucide**（最齊且風格一致）；tabler 補缺（類別最廣）；heroicons 當 UI 替補
3. 命中後 Read 該 .svg 檔確認形狀符合預期；不確定時給使用者 2-3 個候選名（可用 browser.preview 顯示）
4. 同系列圖示要**同一 set 取材**，避免粗細/風格混雜

### Step 3：輸出
- **直接貼出 SVG 程式碼**，並依用途調整：
  - 顏色：改為 `fill="currentColor"` 或 `stroke="currentColor"`（網頁/深色模式自動跟隨文字色），或指定色值
  - 尺寸：改 `width`/`height`（簡報用可放大到 128+，SVG 無糊的問題）或移除改由 CSS 控制
  - 線寬：lucide/tabler 為 24 viewBox、stroke-width 2；放大很多倍時可按比例加粗 stroke 才不顯細
  - 嵌入 HTML 時建議加 `aria-hidden="true"`（裝飾用）或 `role="img"`+`<title>`
- **附授權註記**：lucide=ISC、tabler/heroicons=MIT、patterns=自繪（三者皆可商用免署名；如對外發佈成品仍想註明，寫「Icons: Lucide/Tabler/Heroicons」即可）

### Step 4：庫裡沒有 → 現畫（零授權風險）
模糊搜尋都撈不到、或需求特殊（特定象徵、文字標誌、裝飾構圖）時，**直接手繪 SVG**：
- 慣例：`viewBox="0 0 24 24"`、`fill="none"` + `stroke="currentColor"`、`stroke-width="2"`、`stroke-linecap="round"`、`stroke-linejoin="round"`（與 lucide 風格一致，混排不突兀）
- 路徑力求簡潔對稱，優先直線+圓弧；複雜形狀拆多個 path
- 畫完檢查：形狀辨識度（縮到 16px 還看得出嗎）、重心居中、視覺大小與同系列一致
- 自繪素材屬使用者所有，**想入庫**就存到 `patterns/`（底紋）或另立 `icons/custom/`，執行 `python tools/build_index.py` 重建索引

### Pattern（背景/裝飾底紋）的用法
`patterns/` 為可無限平鋪的 tile SVG（24×24 或 20×20 viewBox，`currentColor`）：
- 網頁：用 CSS `background-image: url("data:image/svg+xml,…")` + `background-repeat: repeat`，或 inline SVG + `<pattern>`
- 簡報/海報：放一個大 SVG，內嵌 `<defs><pattern>`（patternUnits="userSpaceOnUse"）+ 矩形填充
- 影片：Remotion 內直接渲染，`color` 設定即可換色
- 需求超出既有 10 款（點/格/斜線/波浪/三角/十字/圓環/鋸齒/棋盤）→ Step 4 現畫

## 擴充機制

- **加單一圖示**：放入對應 set 目錄（檔名 kebab-case 英文，語意化命名）→ `python tools/build_index.py`
- **加整套圖示庫**：複製到 `icons/<新set名>/`（務必附其 LICENSE）→ 在 `tools/build_index.py` 的 `ICON_SETS` 登記授權 → 重建索引
- **入庫前檢查**：確認授權可再散布（MIT/ISC/CC0/Apache 優先；CC-BY 要署名的標註在 index 的 license 欄）；品牌 logo 不入庫（商標風險）

## 授權紅線（不可踩）

1. **品牌/商標 logo**（Simple Icons 之類即使 SVG 碼 CC0，logo 本體是別人的商標）——不得直接取用，需要時由使用者自負風險另行下載
2. **字型轉外框成 SVG**——字型授權會跟著走，不可把商用字型輪廓當圖形素材
3. **CC-BY-SA 素材**——衍生同授權，未搞懂前不要混入本庫
4. 本庫內建素材全部免責：lucide(ISC) / tabler(MIT) / heroicons(MIT) / patterns(自繪)

## 來源

三套圖示庫取自官方 GitHub 倉庫（lucide-icons/lucide、tabler/tabler-icons、tailwindlabs/heroicons），各 set 目錄內附 LICENSE.txt。patterns/ 為本庫自繪。
