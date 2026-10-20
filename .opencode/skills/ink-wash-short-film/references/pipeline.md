# 水墨短片完整流程

## 1. 建立專案

```powershell
$skill = "$env:USERPROFILE\.config\opencode\skills\ink-wash-short-film"
$dst = "$env:USERPROFILE\Documents\OpenCode\ink-videos\my-film"
Copy-Item -Recurse "$skill\assets\project-template" $dst
```

複製後先改 `scripts/script.json` 的 `title`、`subtitle`、`output_name`、`scenes`。`build.py` 的 `HERE` 是 `scripts/`，所有相對路徑都以那裡為準。

```text
scripts/
├─ build.py
├─ script.json
├─ tts_vox.py
├─ tts/                 # TTS 輸出；build.py 讀這裡
└─ work/                # 自動產生
```

`work/` 與 `renders/` 可以刪掉重建；`script.json`、`tts/`、`tts/_manifest.json` 是資產，不要亂刪。

## 2. 寫 script.json

- `lines`：字幕用，保留「著急」等正確用字與引號。
- `speech`：只覆蓋 TTS 文字，key 是 `<scene>_<index>`，例如 `s2_0`。
- `scenes`：只放實際會出現的幕；`title` 是特別場景，不列在 `scenes` 也可以。
- `seal`：片尾紅印；只有最後一幕開。
- `tag`：右上角兩字；不要和字幕或紅印重疊。

新增場景時同步改：

1. `script.json` 的 `scenes`
2. `build.py` 的 `SCENES` 映射
3. `build.py` 的 `do_stills()` 取樣時間
4. `Overlay` 的 tag／seal（若 tag 不是兩字，`text_v` 會變）
5. 音樂段落（`make_music` 若用 scene id 判斷）

## 3. TTS 與發音稿

```powershell
cd <proj>\scripts
& $py tts_vox.py --dry-run
& $py tts_vox.py --candidates 3 --seed 1
& $py tts_vox.py --only s2_0 --candidates 3 --seed 1
```

- 第一次可以全部生成 2–3 個候選；之後只重做有問題的那一句。
- `tts/_manifest.json` 會記錄每句的 `text`、`speech_text`、長度、候選 seed、`selected`。
- 選定後把 `tts/cand/<key>_s<seed>.wav` 複製成 `tts/<key>.wav`；不要讓 `build.py` 直接讀 cand。
- 生成後**聽最後 0.3 秒**；尾端被截斷就換 seed，不要用淡出掩蓋。
- 48 kHz 是正常的；`build.py` 會用 `resample_poly` 轉 44.1 kHz。

### 台灣讀音

| 字幕 | TTS 發音稿 | 備註 |
|---|---|---|
| 著急 | 招急 | 台灣讀 ㄓㄠ ㄐㄧ；已 A/B 實測 |
| 角色 | 腳色 | 若遇到再 A/B，不要直接改 |

字幕與發音稿分離是硬規則：`build.py` 用 `lines` 上字幕，`tts_vox.py` 只用 `speech` 生成。

## 4. 時間軸與混音

```powershell
& $py build.py audio
```

輸出：

- `work/timeline.json`：segments、lines、subs、total
- `work/mix.wav`：旁白＋音樂，44.1 kHz 立體聲

`build.py audio` 的關鍵常數：

| 常數 | 用途 |
|---|---|
| `GAP` | 句與句之間 |
| `TAIL` | 最後一句之後的基礎留白 |
| `END_HOLD` | 舊片尾 s9 的長留白；不是每片都適用 |

最後一幕不是 s9 時，在 segment 組裝處補：

```python
elif sc["id"] == "s3":
    info["dur"] = end - start + 2.5
```

補完重跑 `audio`，再用 `check_timeline.py` 驗證。**不要**只改 `timeline.json` 而不重跑，`mix.wav` 會對不上。

### 字幕

- `split_sub()` 會依停頓切句；引號與全形空格由 `disp()` 處理。
- 修改字幕後要重跑 `audio`，`timeline.json` 的 `subs` 才會更新。
- 不要把字幕改短來「讓 TTS 好念」；改 `speech`。

## 5. 紙墨渲染器

`build.py` 的圖層是 `A`（墨）與 `R`（紅）：

```python
img = paper * (1 - A) + INK * A
img = img * (1 - R) + RED * R
```

`put_ink(A, R, image, x, y, alpha)` 會把灰階圖層壓進 A/R。`Pen` 是灰階畫布，`inkify()` 加墨紋與暈邊。

### 場景骨架

```python
class K2(Scene):
    fog = ((360, 80, 0.25),)

    def build(self):
        self.plane(mountain(...), 3)
        self.fogpass()
        self.plane(waves(...), 9)
        self.hull = hull_closeup(2000, 430, 61)
        self.fx(self.draw)

    def draw(self, t, A, R):
        ...
```

- `plane()` 放不會動的大圖；`Slice` 會依 `speed` 做視差。
- `fogpass()` 只做一次；`fog` tuple 是 `(x, y, alpha)`。
- `draw()` 每幀重畫小物件；保持 deterministic，不要用 `random` 沒 seed。
- `bob = sin()` 讓船與水面同步呼吸；不要每層不同相位。

### 換幕

`frame(T)` 在邊界 `TR/2` 內做轉場。**建議**：

```python
TR = 0.9
if p < 0.5:
    k = 1 - smooth(p, 0.0, 0.5)
    A, R = A0 * k, R0 * k
else:
    k = smooth(p, 0.5, 1.0)
    A, R = A1 * k, R1 * k
```

這是「收墨到紙色，再落下一幕」。乾淨、不會雙重曝光。

**不要**用大面積 radial mask 加 edge glow：

```python
# 會產生巨大墨塊，已否決
m = clip((p * 1.3 - F) / 0.15)
e = exp(...) * 0.4 * sin(pi * p)
A = 1 - (1 - A) * (1 - e)
```

## 6. 文字與印章

- `InkText` 的 `alpha(p)` 控制墨暈；`p` 太快會爆，太慢會像污漬。
- 標題在 1.5 秒內要可讀；tag 在 1 秒內要可讀。
- 標題 `p=(t-0.4)/1.2`、tag `p=(local-0.35)/0.9` 是實測可用的速度。
- `make_seal()` 回傳紅色印章；`put(R, seal, ...)` 不要放進 A。
- 印章不要壓在字幕或 tag 上；片尾才出現。

## 7. stills

`build.py stills s1 s2 s3` 會依 `do_stills()` 的取樣輸出 `work/stills/`。

每個 scene 至少取：

- 進場（0.2–0.3）
- 動作中（0.5–0.6）
- 結束（0.8）

S1 這種有落劍的場景再加 0.52／0.58。輸出後：

1. 看 contact sheet 的整體節奏。
2. 以 1:1 裁切看手、劍、刀尖、岸邊、字。
3. 只修有問題的那一幕，不要三幕一起重畫。

## 8. draft 與 final

```powershell
& $py build.py draft
& $py build.py final
```

- draft：8 段 multiprocessing → `work/video_hq.mp4` → 單次壓縮。
- final：同一份 HQ → 兩階段位元率控制，目標約 19.2 MB。
- 渲染中不要改 `build.py`；子程序可能已載入舊碼，結果會混亂。
- 每次改圖後至少重跑 stills；改動跨幕才重跑 draft。

### 邊界檢查

用 `review_draft.py` 抽：

- 所有 scene 邊界 ±0.4 秒
- 標題出現 1.0／5.5 秒
- 落劍、刻痕、跳船、片尾

檢查：

- 是否有一幀全紙色（dip 正常，但不要超過 0.8 秒）
- 是否雙重曝光
- 是否有大墨塊
- 字幕是否在轉場時被吃掉
- 聲音是否還在

## 9. 輸出驗收

```powershell
ffprobe -v error -show_entries format=duration,size,bit_rate `
  -show_entries stream=codec_name,width,height,r_frame_rate,sample_rate,channels `
  -of default=noprint_wrappers=1 <proj>\renders\<片名>.mp4
```

- 1920×1080、24/1、h264、aac、44100、2 channels
- duration 與 `timeline.json` 的 `total` 一致
- 最後 2–3 秒是留白，不是黑屏或突然斷音
- 檔案大小符合平台

## 10. 交付清單

- `renders/<片名>.mp4`
- `scripts/script.json`
- `scripts/tts/_manifest.json`
- `scripts/work/timeline.json`
- `scripts/work/mix.wav`
- 一組 stills／contact sheet（供回顧）
- 若做過 A/B，記下哪個 seed、哪個發音稿被採用
