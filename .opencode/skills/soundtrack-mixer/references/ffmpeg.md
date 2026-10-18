# ffmpeg 配樂混音指令

環境：ffmpeg 8.1.1（Windows / PowerShell）。含 libmp3lame、libopus、libvorbis，可讀寫 mp3/ogg/opus/wav。

## 目錄

1. [基本檢查](#1-基本檢查)
2. [淡入淡出](#2-淡入淡出)
3. [音量與平衡](#3-音量與平衡)
4. [響度正規化](#4-響度正規化loudnorm)
5. [Ducking 閃避](#5-ducking-閃避)
6. [多段音效排時間軸](#6-多段音效排時間軸)
7. [疊加到影片](#7-疊加到影片)
8. [裁剪與循環](#8-裁剪與循環)
9. [格式轉換](#9-格式轉換)
10. [場景配方](#10-場景配方)

---

## 1. 基本檢查

```powershell
# 資訊（時長、編碼、取樣率）
ffprobe -v error -show_entries format=duration,bit_rate -show_entries stream=codec_name,sample_rate,channels -of default=noprint_wrappers=1 input.mp3

# 音量量測（看 mean_volume / max_volume，用來判斷要壓低多少）
ffmpeg -i input.mp3 -af volumedetect -f null NUL 2>&1 | Select-String "mean_volume|max_volume"

# 波形/音量統計（loudnorm 前的偵測）
ffmpeg -i input.mp3 -af loudnorm=I=-14:print_format=summary -f null NUL
```

## 2. 淡入淡出

`afade=t=in` 淡入、`afade=t=out` 淡出。`st`=起始秒、`d`=持續秒。

```bash
# 淡入 2 秒、最後 3 秒淡出（需知道總長度）
ffmpeg -i bgm.mp3 -af "afade=t=in:st=0:d=2,afade=t=out:st=57:d=3" -c:a libmp3lame -q:a 2 out.mp3

# 只淡入
ffmpeg -i bgm.mp3 -af "afade=t=in:st=0:d=1.5" out.mp3
```

總長度未知時先用 `ffprobe` 取 `duration`，再以 `st = duration - 淡出長度` 計算。

## 3. 音量與平衡

```bash
# 降到 20%（背景音樂常見值 0.15–0.3）
ffmpeg -i bgm.mp3 -af "volume=0.2" out.mp3

# 降 12dB
ffmpeg -i bgm.mp3 -af "volume=-12dB" out.mp3

# 混合：人聲 1.0、BGM 0.5（weights 對應輸入順序）
ffmpeg -i voice.wav -i bgm.mp3 -filter_complex "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=0:weights=1 0.5[a]" -map "[a]" out.wav
```

先用第 1 節的 `volumedetect` 量原檔，再決定降幅，不要盲調。

## 4. 響度正規化（loudnorm）

YouTube / Podcast 標準約 **-14 LUFS**；純音檔歸檔可用 -16。

```bash
# 單次處理（快，略不精確）
ffmpeg -i in.mp3 -af "loudnorm=I=-14:TP=-1.5:LRA=11" -c:a libmp3lame -q:a 2 out.mp3

# 兩段式（精確，先偵測再套用）
ffmpeg -i in.mp3 -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null NUL
# 取回輸出的 input_i, input_tp, input_lra, input_thresh, target_offset
ffmpeg -i in.mp3 -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=<..>:measured_TP=<..>:measured_LRA=<..>:measured_thresh=<..>:offset=<..>:linear=true" -c:a libmp3lame -q:a 2 out.mp3
```

## 5. Ducking 閃避

人聲說話時 BGM 自動壓低。

```bash
ffmpeg -i voice.wav -i bgm.mp3 -filter_complex "
[1:a]volume=0.9[bg];
[bg][0:a]sidechaincompress=threshold=0.05:ratio=8:attack=250:release=400:makeup=1[duck];
[0:a][duck]amix=inputs=2:duration=first:weights=1 0.7[a]
" -map "[a]" out.wav
```

參數調校：
- `threshold` 越低越容易觸發（0.03–0.1）
- `ratio` 壓制強度（4–12，越大壓越深）
- `attack` 觸發速度（ms）、`release` 回復速度（ms，300–800 較自然）

## 6. 多段音效排時間軸

用 `adelay` 指定每段的插入時間（毫秒），`amix` 合併。適合一條時間軸上排多個音效 cue。

```bash
ffmpeg -i base.wav -i sfx_whoosh.mp3 -i sfx_click.mp3 -filter_complex "
[1:a]adelay=1500:all=1[v1];
[2:a]adelay=4200:all=1[v2];
[0:a][v1][v2]amix=inputs=3:duration=first:normalize=0[a]
" -map "[a]" out.wav
```

- `adelay=1500` = 第 1.5 秒處插入（毫秒），`all=1` 讓所有聲道都延遲
- `normalize=0` 避免因軌數增多而整體變小聲
- 需要淡出結尾時接 `afade=t=out:st=<總長-2>:d=2`

## 7. 疊加到影片

```bash
# BGM 疊進影片，以影片長度為準，輸出 mp4（音訊 aac）
ffmpeg -i video.mp4 -i bgm.mp3 -filter_complex "[1:a]volume=0.25,afade=t=in:st=0:d=2,afade=t=out:st=57:d=3[b]" -map 0:v -map "[b]" -c:v copy -c:a aac -b:a 192k -shortest out.mp4

# 同時保留影片原聲（例如口白）+ BGM
ffmpeg -i video.mp4 -i bgm.mp3 -filter_complex "[1:a]volume=0.25[b];[0:a][b]amix=inputs=2:duration=first:weights=1 0.5[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest out.mp4
```

- `-c:v copy` 不重編影片，快且無畫質損失
- `-shortest` 以較短者結束（避免 BGM 比影片長留下黑畫面）
- BGM 比影片短時：加 `-stream_loop -1` 無限循環輸入，再搭配 `-shortest`

```powershell
# BGM 循環填滿影片
ffmpeg -i video.mp4 -stream_loop -1 -i bgm.mp3 -filter_complex "[1:a]volume=0.25,afade=t=out:st=<影片長-3>:d=3[b]" -map 0:v -map "[b]" -c:v copy -c:a aac -shortest out.mp4
```

## 8. 裁剪與循環

```bash
# 從第 10 秒起取 30 秒（-ss 放輸入前較快）
ffmpeg -ss 10 -t 30 -i bgm.mp3 -c:a libmp3lame -q:a 2 seg.mp3

# 精確裁切（-ss 放 -i 之後，重編碼才精確）
ffmpeg -i bgm.mp3 -ss 10 -to 40 -c:a libmp3lame -q:a 2 seg.mp3

# 重複 3 次
ffmpeg -stream_loop 3 -i bgm.mp3 -c copy looped.mp3
```

**注意**：裁剪/淡入淡出屬「改作」，選 `*-nd` 授權的音檔時不可執行（見 licenses.md）。

## 9. 格式轉換

```bash
# mp3（128k VBR 較佳）
ffmpeg -i in.wav -c:a libmp3lame -q:a 2 out.mp3

# ogg / opus
ffmpeg -i in.wav -c:a libvorbis -q:a 5 out.ogg
ffmpeg -i in.wav -c:a libopus -b:a 128k out.opus

# 給 Remotion / 瀏覽器：mp3 或 aac
ffmpeg -i in.ogg -c:a aac -b:a 192k out.m4a
```

## 10. 場景配方

| 場景 | 處理組合 |
|---|---|
| 純 BGM 配音白 | `volume=0.2` + 淡入淡出 |
| 有人聲口白 + BGM | ducking（第 5 節）或 `volume=0.15` |
| 片頭/片尾 | 淡入 2s + 淡出 3s + `loudnorm I=-14` |
| 影片成品交付 | 疊加（第 7 節）+ `loudnorm I=-14:TP=-1.5` |
| 多個轉場音效 | `adelay` + `amix`（第 6 節） |
| BGM 太小聲/太大聲 | `volumedetect` 量測 → `volume` 補償 |
| 純音檔歸檔 | `loudnorm I=-16`（語音/播客較適合 -16） |

**執行規則**：
1. 每次實際執行前，把完整指令與輸出路徑回報給使用者
2. 處理後用 `ffprobe` 確認輸出檔存在、時長正確
3. 混音前先量測原檔音量，避免疊加後爆音
4. 勿覆蓋來源音檔，一律輸出到新檔名
