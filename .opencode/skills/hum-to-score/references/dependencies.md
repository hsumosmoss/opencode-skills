# 依賴安裝與環境（hum-to-score）

## 0. 現場檢查（每次先做）

```powershell
python -c "import pretty_midi, librosa; print('ok')"   # 作曲層 + 音高追蹤
Test-Path "<資料夾>\FluidR3_GM.sf2"                    # 音色庫
Get-Command ffmpeg -ErrorAction SilentlyContinue        # 轉檔/量測
# FluidSynth（渲染用，見下）
```

全綠直接用；缺哪項照下面補。

## 1. Python 依賴（pip 直裝）

```bash
pip install pretty_midi librosa
```

| 套件 | 授權 | 用途 |
|---|---|---|
| pretty_midi | MIT | 簡譜⇄MIDI |
| librosa | ISC/MIT | pyin 音高追蹤（哼唱抽取） |

**裝不上的（實測踩坑，別再試）**：
- `basic-pitch`（Spotify，神經網路版）→ 需 TensorFlow，**Python 3.13 建置失敗**
- `tinysoundfont` → **cp313 無 wheel**，編譯失敗

若日後要 basic-pitch 的更準切分：另建 Python 3.11 環境裝它，是獨立選項。

## 2. FluidSynth 渲染引擎（Windows）

conda-forge **無 win-64 版本**（實測 API 確認），走官方 release 二進位：

```powershell
$tools = "<資料夾>\tools"
curl.exe -L --retry 3 -o "$tools\fs.zip" `
  "https://github.com/FluidSynth/fluidsynth/releases/download/v2.6.1/fluidsynth-v2.6.1-win10-x64-cpp11.zip"
Expand-Archive "$tools\fs.zip" "$tools\fluidsynth" -Force
# → $tools\fluidsynth\fluidsynth-v2.6.1-win10-x64-cpp11\bin\fluidsynth.exe（2.7MB，解壓即用）

& $fs -ni -F out.wav -r 44100 -g 0.7 FluidR3_GM.sf2 song.mid
```

授權：FluidSynth = LGPL-2.1（動態連結使用無 copyleft 義務）。

## 3. 音色庫 FluidR3_GM.sf2（148MB，不隨 skill 分發）

```powershell
curl.exe -L --retry 3 -o "<資料夾>\FluidR3_GM.sf2" `
  "https://github.com/urish/cinto/raw/master/media/FluidR3%20GM.sf2"
# 校驗: 148,358,590 bytes；來源實測 200/11 秒
# 小型替代: MuseScore_General.sf3 (39,900,972 bytes)
```

授權：LGPL-2.0，音訊輸出使用無義務；庫檔本身不可改名散發。
（與 `soundtrack-mixer` 共用同一套安裝，裝一次即可。）

## 4. 格式相容與量測（實測事實）

| 事實 | 對策 |
|---|---|
| **m4a/aac 不被 libsndfile/librosa 認**（`Format not recognised`） | `ffmpeg -i in.m4a -ar 22050 -ac 1 out.wav`；`hum2midi.py` 已內建自動轉檔 |
| ffmpeg 解不了 MIDI | 必經 FluidSynth 渲染 wav |
| 錄音音量太小 | 先 `volumedetect` 確認（實測良好錄音：mean -17.8 / peak -0.7 dB） |
| **ffmpeg 快速 seek 量測失準**（`-ss` 在 `-i` 前，短窗讀數不可信） | 先 `-i 檔 -ss T -t D seg.wav` 抽出，再對 seg.wav 量 |
| 含中文 .ps1 用 pwsh 執行（powershell 5.1 cp950 亂碼） | JSON 含中文字用 write 工具寫入 |
| PowerShell `$var:後續` 被當 scoped variable | 寫 `${var}` |
