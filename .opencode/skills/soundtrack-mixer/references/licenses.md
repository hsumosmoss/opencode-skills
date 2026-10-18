# 授權速查與署名規則

## 目錄

1. [核心觀念](#1-核心觀念)
2. [六種授權速查表](#2-六種授權速查表)
3. [兩類警告規則](#3-兩類警告規則)
4. [署名四要素](#4-署名四要素)
5. [候選表呈現格式](#5-候選表呈現格式)
6. [credits.json 格式](#6-creditsjson-格式)

---

## 1. 核心觀念

- **Openverse 平台本身不要求任何出處**——它只是搜尋引擎。
- 要求來自**每筆音檔各自的 Creative Commons 授權**，逐筆不同。
- 策略：**不預設篩選，全部列出並標示**，但對會造成違規的授權給醒目警告，由使用者決定。

## 2. 六種授權速查表

| 代號 | 名稱 | 需署名 | 商用 | 可剪輯/改作 | 備註 |
|---|---|---|---|---|---|
| `cc0` | Creative Commons Zero | ❌ | ✅ | ✅ | **最安全**，等同放棄權利 |
| `pdm` | Public Domain Mark | ❌ | ✅ | ✅ | 公有領域標記 |
| `by` | 署名 | ✅ | ✅ | ✅ | 只要署名即可 |
| `by-sa` | 署名－相同方式分享 | ✅ | ✅ | ⚠️ | 改作須以同授權釋出 |
| `by-nc` | 署名－非商業 | ✅ | ❌ | ✅ | 有廣告/業配即算商業 |
| `by-nd` | 署名－禁止改作 | ✅ | ✅ | ❌ | **剪輯即違規** |
| `by-nc-sa` | 署名－非商業－相同方式分享 | ✅ | ❌ | ⚠️ | |
| `by-nc-nd` | 署名－非商業－禁止改作 | ✅ | ❌ | ❌ | **限制最多** |

## 3. 兩類警告規則

### ⛔ ND 警告（禁止改作）— 最高優先

命中 `by-nd` 或 `by-nc-nd` 時，候選表該列必須標示：

> ⛔ **禁止改作** — 淡入淡出、裁剪、混音、調速都可能構成改作，**不建議用於配樂剪輯**。若採用，只能整段原樣使用且不做任何處理。

### ⚠️ NC 警告（禁止商業）

命中 `by-nc` / `by-nc-sa` / `by-nc-nd` 時標示：

> ⚠️ **非商業限定** — 影片若有廣告收益、業配、會員付費或公司用途，不可使用。

### 判斷流程

```
授權代號含 "nd" → 標 ⛔ 禁止改作（並提醒本次要剪輯）
授權代號含 "nc" → 標 ⚠️ 非商業（若使用者說可能商用，加註不可用）
含 "sa"        → 標 ℹ️ 改作需同授權分享
cc0 / pdm      → 標 ✅ 完全自由
by / by-sa     → 標 ✅ 可商用可剪輯（只需署名）
```

**實際建議**：配樂幾乎都要剪輯，優先推薦 `cc0`、`pdm`、`by`；`nd` 類除非使用者明確要求整段使用，否則提醒避開。

## 4. 署名四要素

CC 官方要求的正確署名包含：

1. **作品標題**
2. **創作者姓名**（+ 創作者連結若有）
3. **授權名稱與連結**（如 `CC BY 4.0` → license_url）
4. **來源頁面連結**（`foreign_landing_url`）

好消息：Openverse 每筆結果的 `attribution` 欄位**已符合上述四要素**，可直接取用貼到片尾字幕、影片說明欄或簡報末頁。

範例：
```
"Deep Whoosh #1" by Kinoton is marked with CC0 1.0.
To view the terms, visit https://creativecommons.org/publicdomain/zero/1.0/.
```

中文影片可用的改寫格式（資訊不變，僅翻譯句式）：
```
〈作品標題〉作者：創作者／授權：CC BY 4.0／來源：https://...
```

## 5. 候選表呈現格式

```markdown
| # | 標題 | 創作者 | 時長 | 來源 | 授權 | 適配 | 
|---|------|--------|------|------|------|------|
| 1 | Deep Whoosh #1 | Kinoton | 3.2s | freesound | ✅ CC0 | 轉場音效，短促乾淨 |
| 2 | Cinematic Piano | XX | 1:36 | jamendo | ⚠️ **BY-NC** 非商業 | 溫馨片頭 |
| 3 | Orchestral Hit | YY | 1.1s | freesound | ⛔ **BY-ND** 禁改作 | 打擊強調（需剪輯→不建議） |
```

表後附可貼片尾的出處文字（僅列使用者挑中的候選即可，或全部附上）。

## 6. credits.json 格式

每次下載音檔時同步產生同名 `.credits.json`：

```json
{
  "title": "Deep Whoosh #1",
  "creator": "Kinoton",
  "creator_url": "https://freesound.org/people/Kinoton",
  "license": "cc0",
  "license_version": "1.0",
  "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
  "commercial_use": true,
  "derivatives_allowed": true,
  "attribution_required": false,
  "source": "freesound",
  "foreign_landing_url": "https://freesound.org/people/Kinoton/sounds/351256",
  "download_url": "https://cdn.freesound.org/previews/351/351256_2247456-hq.mp3",
  "attribution_text": "\"Deep Whoosh #1\" by Kinoton is marked with CC0 1.0. ...",
  "duration_ms": 3155,
  "downloaded_at": "2026-10-17T00:00:00Z",
  "used_in": "",
  "notes": ""
}
```

`commercial_use` 與 `derivatives_allowed` 依第 2 節表格換算填入，`used_in` 供日後填入實際用在哪个影片。
