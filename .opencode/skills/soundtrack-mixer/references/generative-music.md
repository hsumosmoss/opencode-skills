# 生成式配樂（Generative Music）

## 術語（對外描述用）

| 正確名稱 | 英文 | 說明 |
|---|---|---|
| **生成式配樂** | Generative Music / Procedural Music | 規則系統產生的音樂，首選說法 |
| 程序生成音樂 | Procedural Music | 遊戲圈常用，強調依規則即時產生 |
| 演算法音樂 | Algorithmic Music | 學術味，強調作曲邏輯是算出來的 |

**❌ 禁止稱「AI 音樂」**——本路線無任何神經網路/模型。稱 AI 會讓使用者期待 Suno 式人聲歌，聽到正弦波或鋼琴採樣時產生落差，且無法誠實解釋音色來源。

**❌ 避免稱「我寫的曲」**——規則與種子是人定的，但作曲家級的聲明會抬高期待。標準說法：

> 「不是 AI、不是素材庫，是程式算出來的生成配樂（Generative Music）。」

**署名寫法**（生成式 BGM 無第三方授權，比素材庫乾淨）：
```
配樂：程序生成式音樂（Generative Music），本片自製，無第三方素材授權
```

## 能力邊界（誠實版）

**能做到：**
- 氛圍型 BGM（治癒/懸疑/冥想背景樂）
- 長度精準等於影片長度；淡入淡出程式化
- **cue 對齊**：指定時點靜音/轉折（例：00:26 燈管熄滅 → 音樂同步死寂 1.5 秒）。素材庫音樂永遠做不到這點
- **零授權風險**：自己生成=自己擁有，不需署名、無 nc/nd
- 零成本可重跑：改 seed/style/BPM 即是另一首

**做不到（不要過度承諾）：**
- 曲式（主歌副歌）、情感弧線
- 真實樂器質感（正弦波合成明顯；MIDI+採樣路線較佳但仍非錄音）
- 鼓組、貝斯線、抓耳的片頭曲
- 複雜和聲進行、對位

## 兩條生成路徑

### 路徑 1：MIDI 作曲層 + FluidSynth 樣本渲染（預設，音色跳級）

```
compose_film.py（改常數=改音樂，不碰聲音代碼）
   ↓ pretty_midi
.mid（作曲描述檔，幾百位元組）
   ↓ fluidsynth.exe + FluidR3_GM.sf2（真鋼琴採樣）
wav → ffmpeg（loudnorm/淡入淡出）→ mp3
```

**走向/節奏的控制面板**（`compose_film.py` 開頭常數）：

| 想改什麼 | 改哪個常數 |
|---|---|
| 速度 | `BPM` |
| 曲式轉折點 | `SWITCH_AT`（例 27.5 秒 calm→tense） |
| 和弦進行 | `PROGRESSION_CALM` / `PROGRESSION_TENSE` |
| 空曠感 | `MOOD["rest"]` 休止率 |
| 音區高低 | `MOOD["lo"]/["hi"]` |
| 配合畫面的死寂 | `MUTE = (起, 迄)`（該區間不寫任何音符） |
| 防難聽保險 | `SCALE` 五聲音階（旋律候選音限制） |

依賴安裝見 [dependencies.md](dependencies.md)（FluidSynth Windows 二進位 + 148MB 音色庫，**不隨 skill 分發**）。

**已知坑**：
- FluidSynth 自帶混響的**殘響尾巴會漏進靜音區**（實測 -14dB 而非全靜音）→ 必須 ffmpeg 閘道硬切：
  `volume=enable='between(t,起,迄)':volume=0`
- 小節對齊的墊底和聲在靜音區截斷後，下一個和弦要到下個小節才開始，會留空洞 → 轉折點強制補一個和弦

### 路徑 2：純代碼正弦波合成（備胎，零依賴）

`generate_bgm.py` + `generate_sfx.py`，**只用 Python 標準庫**，無需 pip 裝任何東西、無需音色庫。

- **使用場景**：乾淨機器無法下載 148MB 音色庫時；或需要**秒級精準時點靜音**（`--mute 26:1.5` 內建，不依賴 ffmpeg 閘道）
- **音色明顯輸給路徑 1**（正弦波 vs 真鋼琴採樣），非首選

```bash
# 治癒風 30 秒
python generate_bgm.py --seconds 30 --seed 42 --style calm --out bgm.wav
# 對齊影片 cue：26–27.5 靜音、27.5 後轉懸疑
python generate_bgm.py --seconds 50 --style calm --style-b tense \
  --switch-at 27.5 --mute 26:1.5 --out film.wav
```

## 選路決策

```
需要背景音樂/音效
├─ 需要配合畫面特定時點變化（靜音、轉折）？ → 生成式
├─ 零授權風險優先（不願署名/查授權）？      → 生成式
├─ Openverse 搜不到合適的？                → 生成式
└─ 其他（音質優先）                        → 走 Openverse 搜尋（階段 1–3）
```

**素材庫優先**：真樂器錄音音質永遠贏過生成式，生成式是補充不是替代。

## 驗證基準（重跑時的通過標準）

| 項目 | 通過標準 |
|---|---|
| 指定時點靜音區 | **-91 dB**（數位全靜音；~-60 以下不合格=殘響漏出） |
| 靜音後轉折段 | 音樂有回來（實測 -5.6 dB，~-35 以下=留了空洞） |
| 音效/BGM 分離 | 音效峰值領先 BGM ≥ 11 dB |
| 節拍/時長 | MIDI 總長 = 影片長度（±0.1 秒） |

## 依賴授權（一覽）

| 依賴 | 授權 | 用途 |
|---|---|---|
| pretty_midi | MIT | MIDI 生成 |
| FluidSynth | LGPL-2.1 | MIDI 渲染引擎（動態連結使用） |
| FluidR3_GM.sf2 | LGPL-2.0 | GM 音色採樣庫 |
| librosa | ISC/MIT | （hum-to-score 用）音高追蹤 |
