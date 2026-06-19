---
name: google-workspace-admin-flow
description: 學校行政專案半自動工作流 SKILL — 用 Google Workspace（Form/Sheet/Drive/Docs/Calendar/Gmail）+ Apps Script 建立「公文進來 → 自動建專案資料夾 + 待辦表 + 成果檢核表 + Calendar 提醒 + Gmail 通知」的減量工作流。三種部署模式：A 手動引導（最低門檻、給研習學員）、B clasp 一鍵自動部署（給承辦人快速建置）、C 純 API 旁路（給開發者串接其他 SKILL）。觸發：「行政自動化」「行政減量」「公文工作流」「Google Workspace 自動化」「Apps Script 自動部署」「clasp 部署」「自動建專案資料夾」「自動排提醒」「自動寄通知」「公文自動建檔」「學校行政流程」「workflow admin」「admin automation」「workspace 工作流」。
metadata:
  author: 曾慶良（阿亮老師）
  version: 1.0.0
---

# 學校行政專案半自動工作流

## 一、SKILL 用途

協助學校承辦人把「公文進來 → 散落在信件/雲端/桌面 → 結案前手忙腳亂」這個痛點，轉成「填一張表 → 系統自動建檔 → 自動排提醒」的固定流程。

## 二、三種部署模式

| 模式 | 對象 | 操作流程 | 時間 |
|------|------|---------|------|
| **A 手動引導** | 第一次接觸的老師、研習學員 | 開 Apps Script 編輯器 → 貼程式碼 → 改 4 個參數 → 執行 | 15 分鐘 |
| **B clasp 自動部署** | 主任、組長、有 CLI 經驗者 | 跑一個指令 → 自動推程式 → 自動執行 | 3 分鐘 |
| **C 純 API 旁路** | 開發者、要串接其他 SKILL 的人 | 跑 Python 腳本，不走 Apps Script，直接建立專案 | 即時 |

三種模式**功能完全等價**，差別只在「使用者要付出多少操作成本」。

## 三、何時啟用此 SKILL

### 觸發情境
- 使用者說：「我想自動化行政流程」「公文進來就自動建資料夾」「Google Workspace 工作流」「Apps Script 怎麼部署」「clasp」「行政減量」
- 使用者拿著一張 Google Form 問「能不能送出後自動建專案」
- 使用者問如何「不要再手動建資料夾、寄信、排日曆」

### 不適用情境
- 使用者要的是純 Google Drive 操作 → 用 `google-drive` SKILL
- 使用者要的是寄信而已 → 用 `email-reply-helper` 或 `imap-smtp-email`
- 使用者要的是 NotebookLM 整理 → 用 `notebooklm` SKILL（兩者可以搭配，本 SKILL 是「建檔」，NotebookLM 是「理解」）

## 四、執行流程

### 第一步：確認使用者要哪一個模式

向使用者提問（必要時用 AskUserQuestion）：

1. **你想自己貼程式碼進 Apps Script，還是讓系統自動推上去？**
   - 自己貼 → 模式 A
   - 自動推 → 模式 B
   - 完全跳過 Apps Script → 模式 C

2. **你有 Google Drive 總資料夾的 folder ID 了嗎？**
   - 有 → 直接進行
   - 沒有 → 引導建立總資料夾

3. **你的 Calendar ID 是？**
   - 預設用 `primary`（個人帳號的主日曆）
   - 學校共用日曆 → 引導取得 ID

### 第二步：依模式查閱對應指南

- 模式 A → 讀 `references/mode-a-manual-install.md`
- 模式 B → 讀 `references/mode-b-clasp-deploy.md`
- 模式 C → 讀 `references/mode-c-api-bypass.md`

### 第三步：產出客製化程式碼或執行部署

依模式呼叫對應 `scripts/`：
- 模式 A/B → 跑 `scripts/generate-code.mjs` 產生 `Code.gs`
- 模式 B → 跑 `scripts/deploy-via-clasp.ps1` 一鍵推上去
- 模式 C → 跑 `scripts/api-bypass/create_project.py` 直接建立

### 第四步：測試與驗收

對應 `references/testing-checklist.md` 跑驗證流程：
- 測試新建專案（送一筆假表單）
- 測試新增階段日期
- 測試 Calendar 提醒
- 測試 Gmail 通知

## 五、檔案地圖

```
google-workspace-admin-flow/
├── SKILL.md                              ← 本檔（主入口）
├── references/
│   ├── architecture.md                   ← 系統架構與資料流
│   ├── form-fields.md                    ← 兩張 Form 與 Sheet 的欄位定義
│   ├── mode-a-manual-install.md          ← 模式 A 手動引導步驟
│   ├── mode-b-clasp-deploy.md            ← 模式 B clasp 自動部署
│   ├── mode-c-api-bypass.md              ← 模式 C 純 API 旁路
│   ├── customization-points.md           ← 學校客製化欄位/處室/任務模板
│   ├── testing-checklist.md              ← 驗收清單
│   └── troubleshooting.md                ← 常見問題排解
├── templates/
│   ├── Code.gs                           ← Apps Script 完整程式碼（含參數佔位）
│   ├── appsscript.json                   ← Apps Script manifest
│   └── clasp.json.template               ← clasp 設定範本
└── scripts/
    ├── generate-code.mjs                 ← 從參數產生 Code.gs（Node.js）
    ├── deploy-via-clasp.ps1              ← Windows 一鍵部署
    └── api-bypass/
        ├── create_project.py             ← 模式 C: 直接建立專案
        ├── add_milestone.py              ← 模式 C: 新增階段日期
        ├── auth.py                       ← Google API 授權
        └── requirements.txt              ← Python 依賴
```

### 公文格式範本（templates/公文範本/）

`templates/公文範本/` 內附學校常用公文 Word 範本，供草擬公文初稿時參照格式：

- `簽.doc`（簽呈）、`函.doc`（公函）、`開會通知單.doc`（開會通知單）
- 來源：臺北市立大學總務處文書組公開的「常用公文格式」；實際使用請依貴校規定調整。
- 用法：用工作流建好專案資料夾後，依範本格式請 AI 草擬內容（如「依『簽』格式擬一份○○研習簽呈初稿」），**正式公文仍須承辦人與主管核校後再簽核發文**。詳見該資料夾 `README.md`。

## 六、客製化點（給進階使用者）

`references/customization-points.md` 列出所有可調整的地方：

- **處室列表**：教務處 / 學務處 / 總務處 / 輔導室 / 資訊組 / ...（依學校）
- **日期類型**：可以新增「校外參訪日」「家長日」等學校特有日期
- **任務模板**：每個專案自動產生的 10 筆預設任務可調整
- **資料夾結構**：00~09 子資料夾命名可調整
- **通知格式**：Gmail 通知信的開頭稱謂、簽名檔
- **提醒間隔**：預設「前 7 天提醒」可改為「前 14 天 / 30 天」

## 七、與其他 SKILL 的搭配

| 上游 SKILL | 用途 |
|-----------|------|
| `notebooklm` | 把建好的專案資料夾餵給 NotebookLM 做語意搜尋 |
| `google-drive` | 進一步操作建好的資料夾（搬檔、改權限） |
| `imap-smtp-email` | 若不想用 Gmail，改走自架 SMTP |

| 下游 SKILL | 用途 |
|-----------|------|
| `pdf` | 把成果檢核表匯出成 PDF 結案文件 |
| `xlsx` | 把總控表匯出做進階分析 |
| `email-reply-helper` | 自動回信給來文單位 |

## 八、安全與資料保護

⚠️ **本 SKILL 不要在以下情境直接執行：**
- 程式碼中含真實 Drive Folder ID、Calendar ID、真實 Email → 必須改用範本參數
- 公開 GitHub 上 → 必須先檢查 CONFIG 是否留下真實值
- 涉及學生/家長/教師個資的表單 → 必須先評估 GDPR / 個資法

⚠️ **本 SKILL 不會自動執行以下行為**（仍由人工把關）：
- 正式公告
- 經費核銷
- 成果送出
- 對外通知
- 校內簽核
