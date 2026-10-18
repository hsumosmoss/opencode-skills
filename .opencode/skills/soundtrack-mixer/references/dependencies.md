# 依賴安裝與環境（生成式音樂路線）

路徑 2（正弦波）無任何依賴。**路徑 1（MIDI+FluidSynth）依賴以下三項**，skill 本身不附帶 148MB 音色庫與二進位。

## 0. 現場檢查（每次先做，避免重複下載）

```powershell
# 音色庫是否已在本機
Test-Path "<資料夾>\FluidR3_GM.sf2"          # 專案慣例放 assets/audio/
# FluidSynth 是否已解壓
Get-Command fluidsynth -ErrorAction SilentlyContinue
# Python 依賴
python -c "import pretty_midi; print(pretty_midi.__version__)"
```

**全綠 → 直接用；缺哪項 → 依下面補。**

## 1. Python 依賴（小，直接 pip）

```bash
pip install pretty_midi          # MIDI 生成（MIT）
```

生成式音效/正弦波 BGM 不需安裝任何東西。

## 2. FluidSynth 渲染引擎（Windows 踩坑記錄）

| 路徑 | 結果 |
|---|---|
| `conda install fluidsynth` | ❌ **conda-forge 無 win-64 版本**（182 個檔全非 Windows，實測 API 確認） |
| `pip install tinysoundfont` | ❌ Python 3.13 無對應 wheel，編譯失敗 |
| **官方 release 二進位** | ✅ **正解**，2.7MB 解壓即用 |

```powershell
$tools = "<資料夾>\tools"        # 專案慣例 assets/audio/tools/
curl.exe -L --retry 3 -o "$tools\fs.zip" `
  "https://github.com/FluidSynth/fluidsynth/releases/download/v2.6.1/fluidsynth-v2.6.1-win10-x64-cpp11.zip"
Expand-Archive "$tools\fs.zip" "$tools\fluidsynth" -Force
# → fluidsynth.exe 位置:
#   $tools\fluidsynth\fluidsynth-v2.6.1-win10-x64-cpp11\bin\fluidsynth.exe
```

驗證：`& $fs --version` → `FluidSynth runtime version 2.6.1`

**渲染指令**：
```powershell
& $fs -ni -F out.wav -r 44100 -g 0.7 FluidR3_GM.sf2 song.mid
```
（`-ni` 不用 MIDI 鍵盤介面、`-g 0.7` 主音量防爆）

## 3. 音色庫 FluidR3_GM.sf2（148MB，不隨 skill 分發）

實測可用來源（HTTP 200，148,358,590 bytes，11 秒下完）：

```powershell
curl.exe -L --retry 3 -o "<資料夾>\FluidR3_GM.sf2" `
  "https://github.com/urish/cinto/raw/master/media/FluidR3%20GM.sf2"
# 校驗: Length 應 = 148,358,590
```

- 小型替代：MuseScore General.sf3（39,900,972 bytes，sf3 壓縮格式，fluidsynth 2.6 支援）
  `https://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/MuseScore_General.sf3`
- 依 LGPL-2.0，商用影片使用 GM 樣本無虞（音訊輸出無 copyleft 義務），但庫檔本身不可改名散發

## 4. 格式與量測的環境事實（實測踩過）

| 事實 | 對策 |
|---|---|
| **m4a/aac 不被 libsndfile/librosa 認** | 先 `ffmpeg -i in.m4a -ar 22050 -ac 1 out.wav`（`hum2midi.py` 已內建自動轉檔） |
| ffmpeg 解不了 MIDI | 必須經 FluidSynth 渲染成 wav |
| 中文字型 drawtext 用 `C\:/Windows/Fonts/msjh.ttc` | （影片製作相關，見原 ffmpeg.md） |
| 含中文字的 .ps1 需 pwsh（非 powershell 5.1） | cp950 編碼問題；JSON 含中文用 write 工具寫入 |
| PowerShell 字串 `$var:後續` 被解析成 scoped variable | 寫 `${var}` |

### ⚠️ ffmpeg 音量量測陷阱（重要）

**快速 seek（`-ss` 在 `-i` 之前）對 0.1 秒級短窗量測會失準**——曾量出「音效峰值 = 純 BGM 峰值」的假象，誤判音效消失。

**可靠方法：先抽出成 wav，再量該 wav**：
```powershell
ffmpeg -y -i in.mp3 -ss 31.0 -t 0.6 seg.wav
ffmpeg -i seg.wav -af volumedetect -f null NUL   # 取 mean_volume / max_volume
```
（`-ss` 在 `-i` 後 = 解碼式精確 seek；再對短窗量測仍建議抽檔）