# Openverse Audio API 參考

## 目錄

1. [端點與呼叫方式](#1-端點與呼叫方式)
2. [必須知道的坑](#2-必須知道的坑)
3. [搜尋參數](#3-搜尋參數)
4. [搜尋語法](#4-搜尋語法)
5. [三個來源分流](#5-三個來源分流)
6. [回應欄位](#6-回應欄位)
7. [下載方式](#7-下載方式)
8. [英文搜尋詞對照表](#8-英文搜尋詞對照表)

---

## 1. 端點與呼叫方式

```bash
# 搜尋
curl "https://api.openverse.org/v1/audio/?q=cinematic+whoosh&page_size=5&format=json"

# 來源統計
curl "https://api.openverse.org/v1/audio/stats/?format=json"

# 單筆詳情（含 waveform、related）
curl "https://api.openverse.org/v1/audio/<id>/?format=json"
```

免註冊、免 API key 即可搜尋與下載。

## 2. 必須知道的坑

| 坑 | 實測結果 | 對策 |
|---|---|---|
| `Accept: application/json` | 回傳 Django REST framework 的 **HTML** 頁面 | 改用 **`?format=json`** |
| `category=sound_effect` | **永遠回 0 筆**（Freesound 的 category 欄位是 null） | 用 `source=freesound` 分流 |
| `page_size` > 20 | `page_size may not exceed 20 for anonymous requests` | 上限 20 |
| `page` 翻太深 | `pagination depth may not exceed 240 for anonymous requests` | 只能翻到前 240 筆 |
| 連續快打 | 約 20 次/分、200 次/天，超過回 429 | 少量精準查詢，別暴力翻頁 |
| `category=music` | **只對 Jamendo 有效**，Freesound/Wikimedia 為 null | 配樂用 `source=jamendo` |

## 3. 搜尋參數

| 參數 | 值 | 用途 |
|---|---|---|
| `q` | 字串 | 主查詢（與 `tags`/`title` 互斥） |
| `source` | `freesound` / `jamendo` / `wikimedia_audio` | 來源分流，逗號分隔 |
| `excluded_source` | 同上 | 排除來源 |
| `page_size` | 1–20 | 每頁筆數 |
| `page` | 1–12（受 240 深度限制） | 分頁 |
| `license` | `cc0,by,by-sa,by-nc,by-nd,by-nc-sa,by-nc-nd,pdm` | 指定授權 |
| `license_type` | `commercial` / `modification` / `all-cc` / `all` | 依用途粗篩（**預設不篩**） |
| `length` | `shortest` / `short` / `medium` / `long` | 時長分級（音效找 shortest/short） |
| `extension` | `mp3,wav,ogg,flac` | 檔案格式 |
| `tags` | 字串 | 只搜標籤 |
| `title` | 字串 | 只搜標題 |
| `creator` | 字串 | 只搜創作者 |
| `filter_dead` | true（預設） | 過濾失效連結 |
| `mature` | false（預設） | 是否含敏感內容 |

## 4. 搜尋語法

```
q=dog -pug              排除 pug
q=cat|dog               或
q=cat + dog             且
q="exact phrase"        精確片語
q=net*                  前綴萬用
q=theatre~1             模糊拼寫（差 1 字元）
q=ambient (piano|strings)  分組
```

## 5. 三個來源分流

| source | 顯示名 | 數量 | 強項 | 建議情境 |
|---|---|---|---|---|
| `freesound` | Freesound 59 萬 | 音效為主 | whoosh、click、thunder、ambience、UI 音效 | 轉場、UI、環境音、特效 |
| `jamendo` | Jamendo 64 萬 | 現代配樂 | `category=music` 在此有效 | BGM、情緒配樂 |
| `wikimedia_audio` | Wikimedia Commons 398 萬 | 古典/公有領域 | 古典樂、歷史錄音、發音、語音 | 古典、紀錄片、公有領域 |

**分流決策**：
- 要**音效** → `source=freesound`
- 要**現代 BGM** → `source=jamendo`（可加 `category=music`）
- 要**古典或完全公有領域** → `source=wikimedia_audio`
- 找不到時 → 移除 `source` 改全域搜尋

### ⚠️ Jamendo 配樂大量是 by-nc-nd（實測）

預設（不加授權過濾）搜 `q=cinematic intro&source=jamendo`，前 4 筆**全是 `by-nc-nd`**（限制最多，不可商用也不可剪輯）。

過濾**確定有效**（實測）：

```bash
# 只要可商用（實測回 6 筆，授權為 by / by-sa）
q=cinematic+intro&source=jamendo&license_type=commercial

# 只要可剪輯的寬鬆授權（實測回 5 筆）
q=cinematic+intro&source=jamendo&license=cc0,by,by-sa,pdm

# 全域搜尋可商用（實測回 182 筆，含 cc0）
q=inspiring+background&license_type=commercial
```

**實務策略**：維持「不預設篩選、全部標示」，但當候選表整片都是 ⛔/⚠️ 時，**主動提示**使用者可加 `license_type=commercial` 或 `license=cc0,by,by-sa,pdm` 收斂（候選量會明顯變少，但都安全）。使用者說「可能商用」時則直接套用過濾。

Freesound 的音效相對多 `cc0`/`by`，音效搜尋通常不必擔心。

## 6. 回應欄位

```jsonc
{
  "result_count": 240, "page_count": 12, "page_size": 20, "page": 1,
  "results": [{
    "id": "uuid",
    "title": "Deep Whoosh #1",
    "creator": "Kinoton",
    "creator_url": "https://freesound.org/people/Kinoton",
    "url": "https://cdn.freesound.org/previews/.../xxx-hq.mp3",  // 下載用
    "foreign_landing_url": "https://freesound.org/people/.../sounds/351256",  // 出處連結
    "license": "cc0", "license_version": "1.0",
    "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
    "attribution": "\"Deep Whoosh #1\" by Kinoton is marked with CC0 1.0...",  // 可直接貼片尾
    "source": "freesound", "provider": "freesound",
    "category": null,             // Freesound 常為 null
    "duration": 3155,             // 毫秒
    "filetype": "mp3", "filesize": 69196,
    "bit_rate": 128000, "sample_rate": null,
    "genres": null,
    "tags": [{ "name": "whoosh" }, { "name": "sfx" }],
    "alt_files": [{ "url": "https://freesound.org/apiv2/sounds/351256/download/",
                    "filetype": "wav", "filesize": 841236 }],  // ⚠️ 需 Freesound API key
    "detail_url": "https://api.openverse.org/v1/audio/<id>/",
    "waveform": "https://api.openverse.org/v1/audio/<id>/waveform/",
    "audio_set": { "title": "Transitions" }   // 音效包，常有同系列
  }]
}
```

`duration` 是**毫秒**。`alt_files` 的 wav 原檔需要 Freesound API key，匿名只能拿 `url` 的 mp3 preview（對影片配樂已足夠）。

## 7. 下載方式

直接 GET `url` 欄位，免登入：

| 來源 | URL 形式 | 實測 |
|---|---|---|
| Freesound | `cdn.freesound.org/previews/.../xxx-hq.mp3` | ✅ 200, 58KB |
| Jamendo | `prod-1.storage.jamendo.com/?trackid=...&format=mp32` | ✅ 200, 6.5MB |
| Wikimedia | `upload.wikimedia.org/wikipedia/commons/...ogg` | ✅ |

```bash
curl -L -o "_candidates/01_whoosh.mp3" "<url>"
```

失敗時（403/404）換下一筆，或用 `filter_dead=true` 重搜。下載後用 `ffprobe` 驗證可讀、確認實際長度。

## 8. 英文搜尋詞對照表

**配樂（優先 `source=jamendo`）**

| 中文情境 | 建議搜尋詞 |
|---|---|
| 片頭/激勵 | `inspiring` `uplifting` `epic intro` |
| 科技/產品 | `tech` `corporate` `electronic` |
| 溫馨/感動 | `emotional piano` `heartwarming` `acoustic` |
| 懸疑/緊張 | `tense` `suspense` `dark ambient` |
| 輕快/日常 | `upbeat` `happy` `ukulele` `cheerful` |
| 放鬆/冥想 | `calm` `ambient` `relaxing` |
| 古典/紀錄片 | `orchestra` `strings` `classical`（配 `source=wikimedia_audio`） |

**音效（優先 `source=freesound`）**

| 中文需求 | 建議搜尋詞 |
|---|---|
| 轉場 | `whoosh` `swoosh` `transition` `swipe` |
| 打擊/強調 | `impact` `hit` `boom` `bass drop` |
| 點擊/UI | `mouse click` `button` `ui sound` `notification` |
| 提示/成功 | `chime` `ding` `success` `sparkle` |
| 環境 | `rain` `wind` `birds` `forest ambience` `thunder` |
| 打字/機械 | `keyboard typing` `typing` `switch` |
| 倒帶/科技 | `glitch` `sci-fi` `laser` `power up` |

搜尋無結果時的排錯順序：① 換更通用的英文詞 → ② 移除 `source` → ③ 移除其他過濾參數 → ④ 改用 `tags=` 搜尋。
