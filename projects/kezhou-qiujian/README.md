# 刻舟求劍（52 秒水墨成語短片）

《刻舟求劍》是 `ink-wash-short-film` 技能的實戰案例：1920×1080、24 fps、52 秒，VoxCPM2（許耀文聲音）旁白，紙墨渲染管線直接輸出 MP4。

- 成片： [`renders/刻舟求劍.mp4`](renders/刻舟求劍.mp4)
- 技能： [`ink-wash-short-film`](../../.opencode/skills/ink-wash-short-film/)
- 依賴： Python 3.10+、numpy、scipy、Pillow、ffmpeg、標楷體；旁白用 VoxCPM2

> 目前 `renders/刻舟求劍.mp4` 是 S2 與轉場最後修正前的 draft。程式碼已包含後續修正；要更新成片請重跑 `build.py final`。

## 專案結構

```text
kezhou-qiujian/
├─ scripts/
│  ├─ build.py          # 紙墨渲染、時間軸、混音、stills、draft/final
│  ├─ script.json       # 標題、分鏡、字幕、speech 發音對照
│  ├─ tts_vox.py        # 逐句 VoxCPM2
│  ├─ tts/              # 8 句定稿旁白 + _manifest.json
│  └─ work/
│     ├─ timeline.json  # 段落、字幕、總長
│     └─ stills/contact.jpg
├─ renders/
│  └─ 刻舟求劍.mp4
└─ references/
   └─ lessons.md        # 渲染器與審查的實戰筆記
```

## 重現

```powershell
cd projects/kezhou-qiujian/scripts
python -m pip install -r ../../../.opencode/skills/ink-wash-short-film/assets/project-template/requirements.txt

# 重算時間軸與混音（需要 tts/*.wav）
python build.py audio

# 出 stills
python build.py stills s1 s2 s3

# 出 draft / final
python build.py draft
python build.py final
```

`build.py` 的 `HERE` 是 `scripts/`；TTS 必須放在 `scripts/tts/`，不是專案根的 `tts/`。輸出檔名由 `script.json` 的 `output_name` 決定。

## 這次定下的關鍵值

| 項目 | 值 |
|---|---|
| 總長 | 52.0 秒（原 49.5，片尾 +2.5） |
| 畫面 | 1920×1080、24 fps、H.264 |
| 聲音 | AAC 44.1 kHz 立體聲 |
| 轉場 | `TR = 0.9`，收墨到紙色再落下一幕 |
| 片尾 | s3 額外留 2.5 秒 |
| 台灣讀音 | 字幕「著急」；TTS 發音稿「招急」；s2_0 seed 2 |
| 場景 | Title 6.00 / S1 11.67 / S2 13.34 / S3 21.02 |

## 旁白與發音

`script.json` 的 `lines` 是字幕；`speech` 只覆蓋送進 TTS 的文字：

```json
"speech": {
  "s2_0": "同船的人都替他招急，他卻不慌不忙，拿出小刀，在船舷上刻了一道記號。"
}
```

- 字幕仍保留「著急」。
- 定稿 `s2_0` 使用 `cand/` 的 seed 2，7.68 秒，結尾乾淨。
- VoxCPM2 輸出 48 kHz；`build.py` 依檔頭換算到 44.1 kHz。
- 只重做一句用 `tts_vox.py --only s2_0`，不要整批重跑。

## 已知狀況

- 這支片是 3 幕版本，不是最初規劃的 9 幕；3 幕先出 stills 再渲染，速度較快。
- S2 的手部特寫是最難的一段：手掌連續兩版都像黑團，最後改成「袖口藏手、只露刀身」的方向。
- 成片仍是舊 draft；最新 S2／轉場修正尚未重新輸出 final。

## 授權與素材

- 程式碼與專案文件可作為 `ink-wash-short-film` 的教學案例使用。
- 字型、VoxCPM2 模型、聲音與其他第三方素材依各自原授權；若要對外散布，請先確認聲音與字型的再散布條件。
