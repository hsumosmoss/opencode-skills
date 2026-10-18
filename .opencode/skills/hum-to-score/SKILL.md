---
name: hum-to-score
description: 把人哼的旋律或腦中的曲子變成可用的音樂檔與簡譜，雙向往返修改。適用：哼唱轉譜、哼歌轉 MIDI、把旋律記下來、hum to MIDI、旋律抽取、人聲轉簡譜、簡譜轉音樂、簡譜生成音檔、jianpu 記譜、首調簡譜、以簡譜修改旋律、MIDI 轉簡譜、音檔轉譜、旋律聽寫、記譜工具、瀏覽器簡譜編輯器、鋼琴捲簾編輯器、在瀏覽器編輯/調整旋律再重新生曲、哼唱編輯器。
---

# Hum to Score（哼唱⇄簡譜⇄音檔）

把「人哼的旋律」轉成**音樂檔＋簡譜文字檔**，使用者改簡譜數字後傳回，重新生成音樂——雙向往返的旋律記譜工具。

```
哼唱錄音 ─hum2midi.py→ .mid ─mid2jianpu.py→ 簡譜.txt ─┐
   ↑                                                    │ 使用者改數字
   └── jianpu2midi.py ← 簡譜.txt ←─────────────────────┘
            ↓ fluidsynth + 音色庫
         鋼琴音檔 mp3
```

## 核心原則

1. **先確認輸入是什麼**：哼唱錄音（給路徑）／口述旋律（給簡譜或唱名）／已有 .mid——三種起點不同。
2. **同時交付兩個檔**：音樂檔（mp3，可聽）＋簡譜檔（txt，可編輯）。這是本 skill 的價值核心——**可編輯性**。
3. **如實報告準確度**：哼唱抽取約 8–9 成，必須主動給「驗證基準對比」並請使用者聽後回報修正，不可宣稱完美還原。
4. **簡譜是首調記法**：`1=C` 即 C 調；轉調只改 `--key`，數字不動。

## 工作流程

### 階段 1：判斷輸入類型

| 使用者給的是 | 起點 | 跳到 |
|---|---|---|
| 錄音檔（wav/mp3/m4a…） | 哼唱抽取 | 階段 2 |
| 簡譜文字（`1 1 5 5 …`） | 直接轉 | 階段 3 |
| 哼不出來、只會描述（「do re mi 上去再下來」） | 先幫他寫成簡譜初稿確認 | 階段 3 |
| .mid/.midi 檔 | 直接轉簡譜 | 階段 3 |

### 階段 2：哼唱 → MIDI（讀 [references/notation.md](references/notation.md)）

```bash
python scripts/hum2midi.py --in 錄音.m4a --out out.mid --snap chromatic
```
- `librosa.pyin` 統計式音高追蹤（非神經網路，CPU 即可）；內建中值濾波壓顫音、碎片合併、非 wav 自動 ffmpeg 轉檔
- `--snap chromatic`（預設）保留原調半音取整；`--snap scale --key N` 吸附大調音階修跑音
- `--bpm 80` 把節奏量化到拍格（原速彈性會消失，先問使用者要不要）
- `--min-dur 0.12` 預設；旋律連段成碎片 → 調升到 0.2

**輸出後必做驗證並回報**：音符數、音域（MIDI 範圍）、與使用者確認「聽起來是否同一首」。音高錯 → 調 snap；節奏碎 → 調 min-dur 重抽；整段漏 → 檢查換氣處音量。

### 階段 3：→ 簡譜 / 簡譜 → 音樂（讀 [references/notation.md](references/notation.md)）

```bash
# MIDI → 簡譜（自動偵測調性、時值量化、非調內音吸附並列報告）
python scripts/mid2jianpu.py --in out.mid --out out.jianpu.txt

# 簡譜 → MIDI（`'` `,` 八度、`_` 減半、`-` 加一拍、`.` 附點、`0` 休止、`|` 小節線）
python scripts/jianpu2midi.py --file out.jianpu.txt --bpm 66 --key C --out back.mid
```

- 簡譜檔開頭 `#` 行是自動報告（調性/BPM/吸附清單），**跳過不解析**，使用者也不用改
- 使用者改完 txt 傳回 → 重跑 `jianpu2midi.py` → 進階段 4

### 階段 3.5：（可選）瀏覽器編輯器——給「要自己動手改」的使用者

使用者想**自己編輯調整、改完直接再生曲**時，生成單檔 HTML 編輯器：

```bash
python scripts/make_editor.py --mid out.mid --audio 哼唱.m4a --name 曲名 --out editor.html
```

- **單檔自足**（旋律資料＋原哼唱 base64 內嵌），雙擊瀏覽器開啟即可，無需伺服器
- 內容：鋼琴捲簾（Shift+點加音、拖曳移動、右緣改時值、右鍵刪）、Web Audio 即時試聽、
  原哼唱對照播放、BPM/調/拍號/吸附格線調整、Ctrl+Z 復原
- **三種存檔**：`.jianpu.txt`（回流程重新生曲用）、`.wav`（離線渲染試聽版）、`.score.json`（續編狀態）
- **回程生曲**：`python scripts/jianpu2midi.py --file 使用者存的.jianpu.txt --out x.mid`
  → 階段 4 渲染真鋼琴成品。`jianpu2midi.py` **自動解析 header** 的 `# 1=X` 與 `bpm=NN`
  （檔案無 header 才退回預設 66/1=C）；`--key/--bpm` 明確指定時覆蓋 header
- **取回使用者存的檔**：若編輯器開在 OpenCode 瀏覽器工具分頁，「存檔」落在**瀏覽器下載空間**
  （非檔案系統）——用 `browser.files.list({tabID})` 找檔名 → `browser.files.get({tabID, fileID})`
  取回本機路徑；使用者用自己瀏覽器「另存」時，直接跟使用者要檔案路徑或檔名
- 誠實界線：編輯器內試聽與 `.wav` 都是 **Web Audio 合成音**（確認音高節奏用），成品音色仍以 FluidSynth 為準

驗收：開啟後音符全數繪出、console 零錯誤、三種存檔可下載、復原可用；
回程以無參數 `jianpu2midi.py --file 編輯器輸出.txt` 生曲，輸出須標示「（header）」且音符數一致。

實戰記錄（2026-10）：哼唱 51 音 → 編輯器刪除 3 音存 `record test001.jianpu.txt` →
自動讀 header（1=D, bpm=170）生曲 48 音 mp3，與手動傳參數版 MIDI 逐音一致。

### 階段 4：渲染音檔

```powershell
& "<tools>\fluidsynth.exe" -ni -F out.wav -r 44100 -g 0.7 FluidR3_GM.sf2 back.mid
ffmpeg -y -i out.wav -af "loudnorm=I=-14:TP=-1.5" -c:a libmp3lame -q:a 2 out.mp3
```

依裝（FluidSynth 二進位、148MB 音色庫）見 soundtrack-mixer 的 `references/dependencies.md`（共用），或首次使用時照該文件安裝。

## 驗證基準（重跑通過標準）

| 項目 | 通過標準 |
|---|---|
| 簡譜往返（MIDI→簡譜→MIDI） | **音符數 100% 一致**；音高除「已報告的調內吸附處」外逐音相同 |
| 往返起點 | 量化到半拍格線（±0.3s 內屬預期，非 bug） |
| 哼唱盲測（模擬顫音+呼吸破綻） | 音高全對、音符數 ≥ 85%（12/14 為實測基準） |
| 真實哼唱 | 交由使用者聽後回報；抽完必附「音符數/音域/吸附處數」三個數字 |

## 誠信條款

1. **不虛構抽取/渲染結果**——音符數、dB、時長必須來自實際執行輸出。
2. **不偽稱聽過**——交付時聲明「已完成結構驗證（音符數/音高比對），未親耳試聽」，請使用者試聽比對原哼唱。
3. **不誇稱還原度**——哼唱抽取必然有誤差（切分、節奏、換氣處），主動列出已知差異（如吸附清單），不宣稱「完全一樣」。

## 檔案結構

```
<資料夾>/
├── 哼唱原檔.m4a            ← 使用者輸入
├── <名字>.mid              ← 抽取結果
├── <名字>.jianpu.txt       ← 簡譜（可編輯，傳回用）
└── <名字>_extracted.mp3    ← 可聽成品
```

## 參考檔案

| 檔案 | 內容 | 何時讀 |
|---|---|---|
| [references/notation.md](references/notation.md) | 簡譜記法規格、往返工作流、抽音參數調校、踩坑記錄 | 階段 2/3 前 |
| [references/dependencies.md](references/dependencies.md) | librosa/pretty_midi/FluidSynth 安裝、格式相容、量測陷阱 | 缺依賴時 |
