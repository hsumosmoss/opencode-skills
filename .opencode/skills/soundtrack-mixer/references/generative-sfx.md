# 生成式音效（Generative SFX）— 能力邊界

與 [generative-music.md](generative-music.md) 同為生成式路線，但音效的可行性**差異極大**，必須按三層判斷。

## 三層分類（依實測）

### ✅ 可替代（規則振動/電子音，代碼模型清楚）

| 音效 | 合成原理 | 腳本 |
|---|---|---|
| 燈管嗡聲 | 100Hz 基音+諧波+50Hz 拍頻+微噪 | `generate_sfx.py --kind hum` |
| 掃描嗶嗶 | 純音+快起快收包絡（本來就是電子音） | `--kind beep` |
| 門鈴叮咚 | 雙音+非諧波鐘體泛音+指數衰減 | `--kind chime` |

### ⚠️ 湊合能用（背景墊音、被 BGM 混著聽難辨真假）

| 音效 | 說明 |
|---|---|
| 打火機喀噠 | 短脈衝+金屬共振，衝擊類可程式化 | `--kind click` |
| 雨聲 | 濾波噪聲+水滴點綴，「像雨」但細節偏假 | `--kind rain` |
| 燈管熄滅爆點 | 「啪+悶響」可近似，缺真實瞬態 |

### ❌ 不要勉強（有機混沌聲，代碼出來必塑膠感）

| 音效 | 為什麼難 |
|---|---|
| **倒水進杯** | 水柱+氣泡+容器共振+音高隨水位上升，複雜度最高（`--kind water` 是誠實示範，聽得出假） |
| 腳步/濕腳步 | 鞋底、地面、步態的隨機組合，像打點機 |
| 塑膠袋 | 薄膜褶皺的混沌噪音 |

**規律**：電子音/規則振動 → 代碼強項；有機混沌聲 → Openverse 素材庫強項。

## 定位

- **不替代素材庫**：主角級 cue（觀眾會專注聽的倒水、腳步）一律用真錄音
- **生成式的價值**：
  1. **補洞**——搜不到的冷門 cue（如特定頻率的螢光燈爆點），自製永遠比沒有好
  2. **零授權**——CC0 之外多一條完全自由的路
  3. **精準時值**——要 0.12 秒的嗶聲就是 0.12 秒，不用剪

## 用法

```bash
python generate_sfx.py --kind hum    --out hum.wav     # 6 秒
python generate_sfx.py --kind beep   --out beep.wav    # 1 秒
python generate_sfx.py --kind chime  --out chime.wav   # 2 秒
python generate_sfx.py --kind click  --out click.wav   # 0.4 秒
python generate_sfx.py --kind rain   --out rain.wav    # 4 秒
python generate_sfx.py --kind water  --out water.wav   # 3 秒（困難組示範）
# 轉 mp3：ffmpeg -y -i X.wav -af loudnorm=I=-14:TP=-1.5 -c:a libmp3lame -q:a 2 X.mp3
```

僅需 Python 標準庫，無外部依賴。

## 驗證基準

| 項目 | 通過標準 |
|---|---|
| 生成音效可讀性 | ffprobe 可解、volumedetect peak 約 -1～-4 dB（正規化前 0.8 峰值） |
| 排入混音後 | 峰值領先 BGM ≥ 11 dB（同 generative-music 驗證表） |
