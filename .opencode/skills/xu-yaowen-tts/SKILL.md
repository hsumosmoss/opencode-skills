---
name: xu-yaowen-tts
description: 🔊 許耀文 TTS旁白 | 使用許耀文的聲音進行文字轉語音（TTS）。當使用者提及「用許耀文的聲音說…」、「許耀文說…」、「xu-yaowen voice」、「用許耀文的聲音做旁白」等時自動觸發。內含發音稿正規化、seed 重現、多候選挑選與已知錯音對策。
compatibility: opencode
---

# 許耀文語音克隆（VoxCPM2 TTS）

## When to use
- 使用者說「用許耀文的聲音說……」、「讓許耀文說……」
- 使用者提及「許耀文」並要求生成語音／旁白
- 使用者要做影片旁白並指定使用這個聲音

## Project path
```
<REPO>   預設：%USERPROFILE%\Documents\OpenCode\Voice\voxcpm2-voice-cloner
```

## Voice path
```
<REPO>\voices\許耀文\
```

## Python environment
```
<VENV>\python.exe   預設：<REPO>\.venv\Scripts\python.exe
```

---

## 生成指令

### 基本
```powershell
& "<VENV>\python.exe" "<REPO>\clone.py" "<要說的文字>" --voice 許耀文
```

### 加上發音稿轉換（建議預設使用）
```powershell
& "<VENV>\python.exe" "<REPO>\clone.py" "<文字>" --voice 許耀文 --speech
```

### 一句生多個版本讓你挑
```powershell
& "<VENV>\python.exe" "<REPO>\clone.py" "<文字>" --voice 許耀文 --speech --candidates 5
```
會輸出 `*_s<seed>.wav` 各版本、`*_montage.wav`（照順序拼接，方便試聽）、
`*_manifest.json`（記錄文字、參數、每個檔的長度）。

### 重現某一個聽過的好版本
```powershell
& "<VENV>\python.exe" "<REPO>\clone.py" "<文字>" --voice 許耀文 --seed 21
```

其他參數：`--cfg`（預設 2.0）、`--timesteps`（預設 10）、`--letters`、`--lexicon`。

---

## 發音正確性：先分三類，再對症下藥

VoxCPM2 的生成是**隨機抽樣**（每個 patch 抽一次噪聲），同一句話每次結果都不同。
因此「錯音」不是單一 bug，而是三種不同的病：

| 類型 | 判斷方式 | 對策 | 實例 |
|---|---|---|---|
| **文字層** | 稿子裡有阿拉伯數字、`……`、`——`、全形空白 | `--speech` 自動正規化 | `2026 年 10 月 15 日` → `二零二六年十月十五日` |
| **隨機型** | 同字不同 seed 時對時錯 | 同音字替換把機率歸零 | 倒掛：seed 7 對、seed 21 錯 → 改「到掛」 |
| **穩定型（詞/字）** | 所有 seed、所有 cfg 都錯 | 換詞或同音字；救不回就改寫句子 | 量角器→「亮角器」；噴→永遠四聲 |

### 標準流程
1. 用 `--speech` 生成（自動處理日期、數字、符號、lexicon）
2. 用 `--candidates 5` 生多版，聽 `*_montage.wav`
3. 若某個字**每次**都錯 → 查 `lexicon.txt`，加一條對照
4. 若某個字**時對時錯** → 同音字替換，或改用挑選到的 seed
5. 改任何字之前，**先 A/B 實測**（見下方鐵則）

### 影片專案請用 batch_tts.py
`explainer-videos/videos/<專案>/batch_tts.py` 已經接好本技能：

```powershell
python batch_tts.py --project . --dry-run      # 只看發音稿，不生成
python batch_tts.py --project .                # 正式生成 raw/NN.wav
python batch_tts.py --project . --candidates 5 # 每句 5 個候選（放 raw/cand/）
python batch_tts.py --project . --line 5 --seed 21   # 定稿某一句
```

### 事後修補：接 explainer-video-maker 的 fix_voice.py
影片做完才發現某句唸錯時，**不要整句重錄**（會打亂那一格的動畫時間）。
改用 `explainer-video-maker/scripts/fix_voice.py`：

```powershell
python fix_voice.py --project . audition --line 5 --clauses <詞所在的子句>
python fix_voice.py --project . apply --line 5 --take 05_B
```

它會把新句子**整句等時伸縮回原長度**、對齊音量、重算字幕時間，每一格長度不變。
候選可以用本技能的 `--candidates` 產生。

### 鐵則：任何文字改動都要先 A/B
2026-10 的實測中，「a 的平方 → 欸的平方」這個看似合理的修正，
實際上比原稿更不自然，已被否決。**不要憑猜測改稿。**

### 台灣讀音與尾端檢查
- **「著急」在台灣讀 ㄓㄠ ㄐㄧ**，不是ㄓㄨㄛˊ ㄐㄧˊ。字幕保留「著急」，
  TTS 發音稿改成「招急」；此替換已 A/B 實測，`招急` 的種子 2 結尾乾淨。
  這類替換放在專案的 `script.json` → `speech` 對照表，不要改字幕。
- **每次生成後聽最後 0.3 秒**。VoxCPM2 偶爾會把句尾截掉或吃掉最後一個字；
  先換候選／種子，不要直接進混音。若已定稿，最後一幕的 timeline 要留
  **2–3 秒**尾端（不是只留 0.5–1 秒），避免字幕一結束就斷片。
- **48 kHz 是正常輸出**。短片混音若用 44.1 kHz，讓 build／ffmpeg 在混音時
  一次轉換；不要手動先轉檔再送進去，否則可能二次重取樣。
- **只重做有問題的那一句**。改一句發音稿就重生那一句、更新 `_manifest.json`
  的 `selected`，不要整批重跑；否則其他句的長度、快取與時間軸都會跟著變。
- **字幕稿與發音稿分開**。字幕用原用字；`script.json` 的 `speech` 只覆蓋
  送進 TTS 的文字。任何發音修改先 A/B，不要憑猜測改全部。

---

## lexicon.txt（頑固字對照表）

位置：`<REPO>\lexicon.txt`

格式：`原詞<TAB>替換`、`原詞 → 替換`、`原詞 => 替換`，`#` 開頭為註解。
只影響送給 TTS 的文字，**字幕與畫面不受影響**。

目前已驗證啟用：
```
倒掛	到掛        # 原版部分 seed 會唸 dǎo
量角器	良角器      # 「量」在「量角器」會唸成「亮」；但「量一量」正確，勿一起改
```

實測**正確、不需要改**的字：率(lǜ)、數(shù)、滯空、微調(tiáo)、塞進(sāi)、藏著。

---

## 已知限制

- **`噴` 一律唸成四聲（pèn）**：換 seed、cfg 2.0→3.0、timesteps 10→20 全部無效。
  同音字「歕」「喯」與注音／拼音寫法亦已測試。建議**寫稿時主動避開這個字**。
- **聲調錯誤無法用 ASR 驗證**：轉成文字一模一樣，只能靠人耳。
  產出時應附「高風險字 + 時間點」清單，讓人只聽那幾個點。
- 套件本身沒有 seed 介面，`clone.py` 是在外層用 `torch.manual_seed()` 固定，
  實測可達位元級重現。

---

## Output
- 單次生成：`output/cloned_voice.wav`
- 多候選：`output/<name>_s<seed>.wav`、`_montage.wav`、`_manifest.json`
- 生成後**回報實際檔案路徑**給使用者
- 首次執行會自動下載 VoxCPM2 模型（約 4.7GB，僅一次）

## Notes
- 使用 NVIDIA CUDA (RTX 3060 Ti) 加速，RTF ≈ 1.6（12 秒語音約 20 秒生成）
- 模型載入約 25~35 秒；多候選請在同一次執行中跑完，不要重複載入
- 聲音已錄製完畢，可直接使用
