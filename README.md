# OpenCode Skills

一套專為 [OpenCode](https://opencode.ai) 設計的 Skills 擴充套件包，提供文件處理、設計、簡報、開發工具等多領域的 AI 輔助工作流程。

## 快速開始

1. 將 `.opencode/skills/` 複製到 `~/.config/opencode/skills/`（或保留在專案中）
2. 在 `opencode.jsonc` 中設定權限：
   ```jsonc
   {
     "permission": {
       "skill": { "*": "allow" }
     }
   }
   ```
3. 重啟 OpenCode，Skills 會自動載入

使用 `opencode debug skill` 可確認所有 Skills 已載入。

## 包含 26 個 Skills

### 文件處理
`docx` `pdf` `pptx` `xlsx`

### 設計與前端
`canvas-design` `algorithmic-art` `frontend-design` `web-design-engineer` `brand-guidelines` `theme-factory` `huashu-design` `web-artifacts-builder`

### 簡報與教學
`presentation-architect` `soil-html-deck` `soil-image-deck` `soil-teaching-deck` `course-page-generator`

### 開發工具
`mcp-builder` `webapp-testing` `skill-creator` `github-setup`

### 多媒體與溝通
`video-podcast-maker` `slack-gif-creator` `internal-comms`

### 其他
`doc-coauthoring` `my-skill`

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

## 來源

這些 Skills 最初源自 Antigravity Editor，經改寫以相容 OpenCode 格式。
