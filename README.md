# OpenCode Skills

一套專為 [OpenCode](https://opencode.ai) 設計的 Skills 擴充套件包，提供文件處理、設計、簡報、影片製作、開發工具等多領域的 AI 輔助工作流程。

**跨平台支援**：🍎 macOS (Apple Silicon) 已驗證 ｜ 🪟 Windows 已驗證

---

## 快速開始

### 🍎 macOS（Apple Silicon）
```bash
# 1. 先裝必要工具
brew install ffmpeg uv node
uv python install 3.13

# 2. 複製 skills
cp -r .opencode/skills/ ~/.config/opencode/skills/

# 3. 安裝各 skill 依賴（依需求執行）
pip3 install edge-tts           # video-maker 旁白
npm install -g playwright       # video-maker 錄影
npx playwright install chromium
```

### 🪟 Windows
```powershell
# 1. 先裝必要工具
winget install "FFmpeg (Essentials Build)"
winget install Python.Python.3.13
winget install OpenJS.NodeJS.LTS

# 2. 複製 skills
cp -r .opencode/skills/ ~/.config/opencode/skills/

# 3. 安裝依賴
pip install edge-tts
npm install -g playwright
npx playwright install chromium
```

### 通用設定
在 `opencode.jsonc` 中設定權限：
```jsonc
{
  "permission": {
    "skill": { "*": "allow" }
  }
}
```

重啟 OpenCode 後用 `opencode debug skill` 確認所有 Skills 已載入。

---

## 包含 27 個 Skills

### 🎬 影片製作（本環境重點）
| Skill | 平台 | 用途 | 依賴 |
|-------|------|------|------|
| `video-maker` | 🍎🪟 | 活動紀錄 / 教學 / 社群科普影片 | edge-tts, ffmpeg, Playwright, Node.js |
| `video-podcast-maker` | 🍎🪟 | 自動化 4K 影片播客 | edge-tts, ffmpeg, Node.js, Remotion |

### 📄 文件處理
`docx` `pdf` `pptx` `xlsx`

### 🎨 設計與前端
`canvas-design` `algorithmic-art` `frontend-design` `web-design-engineer` `brand-guidelines` `theme-factory` `huashu-design` `web-artifacts-builder`

### 📊 簡報與教學
`presentation-architect` `soil-html-deck` `soil-image-deck` `soil-teaching-deck` `course-page-generator`

### 🔧 開發工具
`mcp-builder` `webapp-testing` `skill-creator` `github-setup`

### 💬 多媒體與溝通
`slack-gif-creator` `internal-comms`

### 📝 其他
`doc-coauthoring` `my-skill`

---

## 影片製作速查（video-maker）

```bash
# 1. 產生旁白
python3 scripts/generate_narration.py

# 2. 啟動本地伺服器（錄影用）
python3 -m http.server 8080

# 3. 錄影
node record.cjs

# 4. Mux 合成
ffmpeg -y -ss 3 -i renders/*.webm -i master_audio.mp3 \
  -map 0:v:0 -map 1:a:0 \
  -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest \
  -movflags +faststart final.mp4
```

> ⚠️ 踩坑紀錄見 [video-maker/GOTCHAS.md](.opencode/skills/video-maker/GOTCHAS.md)

---

## 建立自己的 Skill

```
my-skill/
├── SKILL.md
├── scripts/
├── references/
└── assets/
```

`SKILL.md` 格式：

```markdown
---
name: my-skill
description: 何時該用這個 Skill
compatibility: opencode
---

# Skill 名稱

給 AI 的指令...
```

詳見 [`SKILLS.md`](SKILLS.md) 完整說明。

---

## 環境紀錄

本 Repo 已在以下環境實測：

| 環境 | 晶片 | 測試日期 | 備註 |
|------|------|---------|------|
| macOS Sequoia | Apple Silicon (M4) | 2026-06-19 | video-maker 完整流程驗證 |
| Windows | x86_64 | 2025 (原始) | video-maker 原始開發環境 |

---

## 來源

這些 Skills 最初源自 Antigravity Editor，經改寫以相容 OpenCode 格式。
