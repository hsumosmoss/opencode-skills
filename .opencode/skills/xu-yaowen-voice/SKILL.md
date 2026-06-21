---
name: xu-yaowen-voice
description: 使用許耀文的聲音進行文字轉語音（TTS）。當使用者提及「用許耀文的聲音說…」、「許耀文說…」等時自動觸發。
compatibility: opencode
platform: windows, macos
---

# 許耀文語音克隆（VoxCPM2 TTS）

> 🪟 **Windows**：NVIDIA CUDA / Intel Arc XPU / CPU
> 🍎 **macOS**：Apple Silicon MPS / CPU

## When to use
- 使用者說「用許耀文的聲音說……」
- 使用者說「讓許耀文說……」
- 使用者提及「許耀文」並要求生成語音

## 前置安裝

請先安裝相依環境：

### 🪟 Windows
```powershell
git clone https://github.com/hsumosmoss/voxcpm2-voice-env.git
cd voxcpm2-voice-env
.\install.bat
```

### 🍎 macOS
```bash
git clone https://github.com/hsumosmoss/voxcpm2-voice-env.git
cd voxcpm2-voice-env
bash install.sh
```

錄製聲音：

### 🪟 Windows
```powershell
.\start.bat
```

### 🍎 macOS
```bash
bash start.sh
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

### 🪟 Windows
```powershell
& "<VOXCPM2_PATH>\.venv\Scripts\python.exe" "<VOXCPM2_PATH>\clone.py" "<要說的文字>" --voice 許耀文
```

### 🍎 macOS
```bash
"<VOXCPM2_PATH>/.venv/bin/python3" "<VOXCPM2_PATH>/clone.py" "<要說的文字>" --voice 許耀文
```

## Output
- 生成檔案：`<VOXCPM2_PATH>\output\cloned_voice.wav`
- 生成後回報給使用者檔案路徑

## Notes
- 🪟 **Windows**：支援 NVIDIA CUDA / Intel Arc XPU / CPU
- 🍎 **macOS**：支援 Apple Silicon MPS / CPU（Intel Mac 僅 CPU）
- 支援中文字詞
- 聲音需先透過 `record.py` 或 `app.py` 錄製
- 首次執行會自動下載 VoxCPM2 模型（約 4.7GB）
