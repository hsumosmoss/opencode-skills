---
name: xu-yaowen-voice
description: 使用許耀文的聲音進行文字轉語音（TTS）。當使用者提及「用許耀文的聲音說…」、「許耀文說…」等時自動觸發。
compatibility: opencode
platform: windows
---

# 許耀文語音克隆（VoxCPM2 TTS）

> ⚠️ **僅支援 Windows** — 依賴 NVIDIA CUDA + VoxCPM2，macOS / Linux 無法使用。

## When to use
- 使用者說「用許耀文的聲音說……」
- 使用者說「讓許耀文說……」
- 使用者提及「許耀文」並要求生成語音

## 前置安裝

請先安裝 [VoxCPM2 Voice Cloner](https://github.com/mathruffian-dot/voxcpm2-voice-cloner)：

```powershell
git clone https://github.com/mathruffian-dot/voxcpm2-voice-cloner.git
cd voxcpm2-voice-cloner
.\install.bat
```

錄製聲音：

```powershell
.\start.bat
# 或
.\.venv\Scripts\python.exe record.py --voice 許耀文
```

## 設定專案路徑

請將下方 `<VOXCPM2_PATH>` 取代為你本機的 `voxcpm2-voice-cloner` 路徑。

## TTS generation command

```powershell
& "<VOXCPM2_PATH>\.venv\Scripts\python.exe" "<VOXCPM2_PATH>\clone.py" "<要說的文字>" --voice 許耀文
```

## Output
- 生成檔案：`<VOXCPM2_PATH>\output\cloned_voice.wav`
- 生成後回報給使用者檔案路徑

## Notes
- 僅支援 Windows（需 NVIDIA CUDA GPU 或 CPU 模式）
- 支援中文字詞
- 聲音需先透過 `record.py` 或 `app.py` 錄製
- 首次執行會自動下載 VoxCPM2 模型（約 4.7GB）
