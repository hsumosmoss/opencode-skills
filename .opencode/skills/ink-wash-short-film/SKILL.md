---
name: ink-wash-short-film
description: 製作完整的水墨成語／歷史故事短片（1920×1080、24fps、VoxCPM2 旁白、字幕、音樂、ffmpeg 輸出）。含分鏡、逐句 TTS 與時間軸、紙墨渲染、still 審查、draft/final、片尾留白與實際踩過的坑。當使用者說「做一支水墨短片」「水墨成語動畫」「水墨說書影片」「把這個故事做成水墨動畫」「延續 ink-videos 專案」，或要把旁白、字幕、畫面整合成水墨 MP4 時使用。
---

# 水墨成語／故事短片

## 先判斷要做哪一種

| 情境 | 做法 |
|---|---|
| 全新短片 | 從 `assets/project-template` 複製專案，先做 3 幕 stills，不一次做 9 幕 |
| 已有 ink-videos 專案 | 先讀 `script.json`、`work/timeline.json`、`tts/_manifest.json`，只改被指出的那一幕 |
| 只有旁白／腳本 | 先做 TTS 與時間軸，再做 stills |
| 已有解說影片，只想加水墨風 | 不要用本技能重做；用 `ink-wash-explainer` |

**鐵則**
- 字幕稿與 TTS 發音稿分開。字幕不動，只改送進 TTS 的文字。
- 任何文字改動先 A/B 實測，不要憑猜測改發音。
- 先 stills 審查，構圖確認才跑 `draft`；不要用整片渲染來找構圖。
- 最後一幕不是 `s9` 時，片尾留白要自己補，不能只靠 `END_HOLD`。

## 交付規格

- 畫面：1920×1080、24 fps、H.264（`yuv420p`）
- 聲音：AAC、44.1 kHz、立體聲；旁白優先，音樂 duck
- 長度：依旁白與字幕，通常 45–60 秒；片尾留 2–3 秒
- 檔案：`renders/<片名>.mp4`
- 專案保留：`script.json`、`work/timeline.json`、`work/mix.wav`、`tts/_manifest.json`

## 專案結構

```text
my-film/
├─ scripts/
│  ├─ build.py          # 紙墨渲染、音訊、時間軸、stills、draft/final
│  ├─ script.json       # 標題、分鏡、字幕 lines、speech 對照
│  └─ tts_vox.py        # 逐句 VoxCPM2
├─ scripts/tts/         # <scene>_<index>.wav + _manifest.json
├─ scripts/work/        # timeline.json、mix.wav、stills、parts
└─ renders/             # 輸出 MP4
```

`build.py` 的 `HERE` 是 `scripts/`；TTS 一定要放 `scripts/tts/`，不是專案根的 `tts/`。

## 流程

### 0. 盤點環境

```powershell
$py = "$env:USERPROFILE\Documents\OpenCode\Voice\voxcpm2-voice-cloner\.venv\Scripts\python.exe"
ffmpeg -version
ffprobe -version
```

Windows 請先設 UTF-8，否則中文與 emoji 會讓 Python 的 `print` 爆 `cp950`：

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING='utf-8'
```

### 1. 故事與分鏡

- 3–5 幕；每幕 2–4 句旁白。成語短片先用 3 幕：事件 → 關鍵動作 → 結果／點題。
- `script.json` 的 `lines` 是字幕；`speech` 只覆蓋 TTS 文字。
- 每幕一個 `tag`（右上角）與可選 `seal`（片尾紅印）。
- 先寫「觀眾要看到什麼動作」，再寫裝飾。不要用畫面去解釋旁白已經說的事。

`script.json` 最小結構：

```json
{
  "title": "刻舟求劍",
  "subtitle": "船走了，劍還在原地",
  "output_dir": "renders",
  "output_name": "刻舟求劍",
  "style": "沉穩的台灣男性說書人，語速中等偏慢",
  "speech": { "s2_0": "同船的人都替他招急，……" },
  "scenes": [
    { "id": "s1", "tag": "渡江", "seal": false, "lines": ["……", "……"] },
    { "id": "s2", "tag": "刻記", "seal": false, "lines": ["……"] },
    { "id": "s3", "tag": "尋劍", "seal": true,  "lines": ["……", "……"] }
  ]
}
```

### 2. 旁白（VoxCPM2）

完整語音規則見 `xu-yaowen-tts` 技能；這裡只記短片整合重點。

```powershell
cd <proj>\scripts
& $py tts_vox.py --dry-run
& $py tts_vox.py --only s2_0 --candidates 3 --seed 1
```

- 一句一檔：`tts/<scene>_<index>.wav`；多候選在 `tts/cand/`。
- 先聽候選，鎖定 seed；把選中的 `cand/<key>_s<seed>.wav` 覆蓋成 `tts/<key>.wav`，並在 `_manifest.json` 記 `selected`。
- VoxCPM2 輸出 **48 kHz**；`build.py` 會依檔頭換算到 44.1 kHz。不要手動先轉檔。
- **台灣讀音**：「著急」讀 ㄓㄠ ㄐㄧ；字幕保留「著急」，TTS 發音稿在 `speech` 寫「招急」。已 A/B 實測。
- **尾端截斷**：每次生成後聽最後 0.3 秒。尾端被吃掉就換候選／seed，不要直接混音。
- 只重做一句時用 `--only`，不要重跑全部，避免其他句的 seed 與長度變動。

### 3. 時間軸與片尾

```powershell
& $py build.py audio
& $py "$env:USERPROFILE\.config\opencode\skills\ink-wash-short-film\scripts\check_timeline.py" `
  --project <proj>
```

`build.py audio` 會重建 `work/timeline.json` 與 `work/mix.wav`。檢查：

- 段落總和 = `total`
- `mix.wav` 長度 = `total`（±0.05 s）
- 最後一句字幕在 `total - 2.0` 之前結束
- 最後一幕結尾至少有 **2 秒**留白

`END_HOLD` 可能只套用在 `s9`；本片最後是 `s3`，所以在 `build.py` 的時間軸組裝處加：

```python
elif sc["id"] == "s3":
    info["dur"] = end - start + 2.5
```

加完要重跑 `build.py audio`，總長會變；字幕不動，但音樂與淡出會跟著延長。

### 4. 畫面

`build.py` 是完整渲染器；模板已包含紙張、墨色、紅色印章、山、水、船、人物、文字、音訊與輸出。先讀這幾個地方：

| 位置 | 用途 |
|---|---|
| `paper()` / `INK` / `RED` | 紙、墨、紅三色 |
| `Scene` / `plane()` / `fx()` | 靜態層與動態繪製 |
| `InkText` | 標題、tag、印章的墨暈字 |
| `put_ink()` / `Pen` / `inkify()` | 把灰階圖層壓進 A/R |
| `KTitle` / `K1` / `K2` / `K3` | 本片四個場景 |
| `SCENES` | 場景 id → class；只映射實際使用的幕 |
| `do_stills()` | 每幕取樣 stills |
| `do_video()` | draft / final |

原則：

- 一個 scene 的 `build()` 只做不會動的圖；`draw(t, A, R)` 做船、人、劍、水花、字。
- 大面積用 `plane()`，小物件用 `put_ink()`；不要在每幀重畫山。
- 畫面先有「剪影可讀性」，再加墨紋。遠景人物不必畫臉。
- 字幕區（約 y=930–1040）保持乾淨；不要把岸、船、蘆葦壓在字上。
- 換幕用 **收墨到紙色**（`TR=0.9`）或乾淨 crossfade；不要用大面積 radial mask + edge glow，會變成巨大墨塊。

### 5. stills 審查（必要）

```powershell
& $py build.py stills s1 s2 s3
```

每幕至少看 3 個點：進場、動作中、結束。把 stills 拼成 contact sheet，先看整體，再放大有疑問的區域（手、劍、岸、字）。

審查順序：

1. 剪影是否讀得出「人是人、船是船、劍是劍」。
2. 動作方向是否與旁白一致（劍往船外落、刀尖對刻痕、船往岸邊）。
3. 字幕是否被畫面吃掉。
4. 墨色是否過黑／過灰；紙色是否一致。
5. 換幕邊界是否會出現雙重曝光或大墨塊。

**不要**在 stills 未確認前跑整片。

### 6. draft

```powershell
& $py build.py draft
& $py "$env:USERPROFILE\.config\opencode\skills\ink-wash-short-film\scripts\review_draft.py" `
  --video <proj>\renders\<片名>.mp4 --timeline <proj>\scripts\work\timeline.json --out <proj>\scripts\work\review
```

- draft 是 1080p 單次壓縮，只用來看動態與轉場。
- 一定要看 **每個換幕邊界** 的前後 0.4 秒，不只看 scene 中段。
- `ffprobe` 確認 duration、fps、audio。
- 有問題先改 stills／build.py，再重跑 draft；不要直接 final。

### 7. final

```powershell
& $py build.py final
ffprobe -v error -show_entries format=duration,size,bit_rate `
  -show_entries stream=codec_name,width,height,r_frame_rate,sample_rate,channels `
  -of default=noprint_wrappers=1 <proj>\renders\<片名>.mp4
```

final 前再確認：

- 片尾有 2–3 秒留白，不是字幕一完就斷。
- 最後 0.3 秒沒有 TTS 截斷。
- 換幕沒有黑屏過久或紙色閃爍。
- 檔案大小與平台限制相符（模板 final 目標約 19.2 MB）。

## 最常踩的坑（摘要）

完整清單見 `references/pitfalls.md`。

- **TTS**：台灣讀音、尾端截斷、48k、seed 不可重現、只改一句卻重跑全部。
- **時間軸**：`END_HOLD` 只套 s9、最後字幕與 total 太近、加長後沒重跑 audio。
- **轉場**：radial mask + edge glow 會產生巨大墨塊；標題／tag 墨暈太久會像污漬。
- **劍**：靜止時不要讓劍浮在船外；要斜靠在船內舷邊。落下要有旋轉與加速度，不要垂直插水。
- **水花**：一整排垂直線會像蘆葦；用低矮扇形＋少量水滴，漣漪 3 圈即可。
- **手**：手掌最難畫。連續兩版仍像黑團時，改用「袖口藏手、只露刀身」會比硬畫拳頭乾淨。
- **岸**：硬邊多邊形會像木棧／水泥平台；要淺沙色、斷續濕邊、兩層高低蘆葦。
- **審查**：只看 stills 不看邊界，或只看小圖不看 1:1 裁切，都會漏掉最明顯的錯。

## 資源

- `assets/project-template/`：可複製的 `build.py`、`script.json`、`tts_vox.py`。先複製再改，不要從零重寫渲染器。
- `scripts/check_timeline.py`：檢查 timeline 與 mix.wav 的長度、片尾、字幕尾端。
- `scripts/contact_sheet.py`：把 `work/stills/` 拼成 contact sheet。
- `scripts/review_draft.py`：抽換幕邊界與指定時間的 frames，產生 contact sheet；需要 `ffmpeg` 與 Pillow。
- `references/pipeline.md`：完整流程、指令、檔案與驗收。
- `references/pitfalls.md`：TTS、時間軸、轉場、繪畫、輸出、效能的所有坑。
- `references/case-kezhou.md`：《刻舟求劍》實例與實際數值。
- 語音：`xu-yaowen-tts` 技能（許耀文 VoxCPM2、發音稿、seed、尾端檢查）。
