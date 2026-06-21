# OpenCode Skills 使用說明

## 什麼是 Skills？

Skills 是 OpenCode 的擴充套件，提供 AI 助手專門的知識、工作流程和工具整合。
每個 Skill 是一個目錄，內含 `SKILL.md`（指令）+ 選配套件（腳本、範本、參考文件）。

## Skills 運作方式

1. OpenCode 啟動時會掃描多個目錄尋找 `SKILL.md`
2. **中繼資料**（name + description）常駐在 context 中，讓 AI 知道何時該用
3. AI 判斷使用者請求符合某個 Skill 後，才會載入完整的 `SKILL.md` 內容
4. 可再依需求讀取配套的 scripts / references / assets

## 已安裝的 Skills（26 個）

所有 Skills 存放於 `~/.config/opencode/skills/`

### 文件處理
| Skill | 說明 |
|-------|------|
| `docx` | Word 文件建立、編輯、紅線修訂、註解 |
| `pdf` | PDF 文字/表格提取、合併/分割、表單填寫 |
| `pptx` | PowerPoint 簡報建立（html2pptx）、編輯（OOXML）、範本套用 |
| `xlsx` | Excel 試算表操作與公式重算 |

### 設計與前端
| Skill | 說明 |
|-------|------|
| `canvas-design` | 設計哲學 → 輸出高品質 PDF/PNG 藝術品 |
| `algorithmic-art` | p5.js 生成式藝術（含互動參數控制） |
| `frontend-design` | 生產級前端介面（React/HTML/CSS） |
| `web-design-engineer` | 高品質 Web 成品（頁面、儀表板、互動原型） |
| `brand-guidelines` | Anthropic 品牌色與字型套用 |
| `theme-factory` | 主題工廠 |
| `huashu-design` | 華書設計 |
| `web-artifacts-builder` | Web 成品建置 |

### 簡報與教學
| Skill | 說明 |
|-------|------|
| `presentation-architect` | 簡報架構總監（圖文錨定 + 生成式企劃，中英雙語） |
| `soil-html-deck` | SOIL 互動 HTML 投影片 |
| `soil-image-deck` | SOIL 圖片式投影片 |
| `soil-teaching-deck` | SOIL 教學投影片 |
| `course-page-generator` | 課程頁面產生器 |

### 開發工具
| Skill | 說明 |
|-------|------|
| `mcp-builder` | MCP Server 開發指南（Python FastMCP / TS SDK） |
| `webapp-testing` | Playwright Web 應用測試 |
| `skill-creator` | 建立新 Skill 的完整指南與腳本 |

### 多媒體與溝通
| Skill | 說明 |
|-------|------|
| `video-podcast-maker` | 影片/Podcast 製作（含語音、腳本、素材） |
| `slack-gif-creator` | Slack GIF 動圖製作 |
| `internal-comms` | 內部溝通文件 |

### 語音
| Skill | 說明 |
|-------|------|
| `xu-yaowen-voice` | 🪟 許耀文語音克隆 TTS（VoxCPM2，僅 Windows）|

### 其他
| Skill | 說明 |
|-------|------|
| `doc-coauthoring` | 文件協作 |
| `my-skill` | 自訂 Skill 範本 |

## 設定檔

`~/.config/opencode/opencode.jsonc`：

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "permission": {
    "skill": {
      "*": "allow"           // 允許所有 Skills
    }
  }
}
```

### 權限控制

```jsonc
"permission": {
  "skill": {
    "*": "allow",            // 全部允許
    "internal-*": "deny",    // 隱藏 internal 系列的 Skill
    "experimental-*": "ask"  // 使用前先詢問
  }
}
```

### 自訂 Skills 路徑

```jsonc
{
  "skills": {
    "path": ["~/my-other-skills", "~/.config/agents/skills"],
    "urls": ["https://example.com/skills-registry/"]
  }
}
```

## 建立自己的 Skill

```
my-skill/
├── SKILL.md          # 必要：YAML frontmatter + Markdown 指令
├── scripts/          # 可執行腳本（Python/Bash/JS）
├── references/       # 參考文件（按需載入）
└── assets/           # 輸出用素材（範本、圖檔等）
```

### SKILL.md 格式

```markdown
---
name: my-skill
description: 這裡寫什麼時候該用這個 Skill
compatibility: opencode
---

# Skill 名稱

在這裡寫具體的指令給 AI 助手...
```

### 建立流程

1. `mkdir -p ~/.config/opencode/skills/my-skill`
2. 寫 `SKILL.md`（frontmatter 要有 `name` + `description`）
3. 加上 scripts / references / assets
4. 重啟 OpenCode，用 `opencode debug skill` 確認

## 驗證

```bash
opencode debug skill
```

會列出所有已發現的 Skills 及其狀態。

---

*最後更新：2026-05-18*
