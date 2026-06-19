# google-workspace-admin-flow

學校行政專案半自動工作流 SKILL — 把「公文 → 散落各地」轉成「填表 → 自動建檔 + 排提醒 + 寄通知」的固定流程。

## 🎯 一句話定位

收公文 → 填一張 Google Form → 系統自動完成下列事：

- 在 Drive 建專案資料夾（11 子資料夾，標準歸檔結構）
- 建專案紀錄 Docs（9 段結構模板）
- 建待辦追蹤表（12 欄 + 10 筆預設任務）
- 建成果檢核表（6 欄 + 10 項預設）
- 排 Calendar 提醒（活動日、成果期限、經費核銷）
- 寄 Gmail 通知承辦人
- 寫入行政專案總控表（集中管理）

後續任何階段日期（報名截止、採購、核銷、結案……）填第二張表即追加。

## 🚀 三種部署模式

| 模式 | 對象 | 操作 | 時間 |
|------|------|------|------|
| **A 手動引導** | 第一次接觸 Apps Script 的老師 | 開編輯器 → 貼程式 → 改 4 參數 → 執行 | 15 分鐘 |
| **B clasp 自動部署** | 主任、組長、批次部署 | 跑一個指令 | 3 分鐘 |
| **C 純 API 旁路** | 開發者、串接其他 SKILL | 跑 Python 直接建立專案 | 即時 |

## 📁 SKILL 內容

```
google-workspace-admin-flow/
├── SKILL.md                              ← 主入口
├── references/
│   ├── architecture.md                   ← 系統架構
│   ├── form-fields.md                    ← 表單與 Sheet 欄位定義
│   ├── mode-a-manual-install.md          ← 模式 A 詳細步驟
│   ├── mode-b-clasp-deploy.md            ← 模式 B 自動部署
│   ├── mode-c-api-bypass.md              ← 模式 C API 旁路
│   ├── customization-points.md           ← 學校客製化點
│   ├── testing-checklist.md              ← 驗收清單
│   └── troubleshooting.md                ← 疑難排解
├── templates/
│   ├── Code.gs                           ← Apps Script 完整程式碼
│   ├── appsscript.json                   ← manifest
│   └── clasp.json.template
└── scripts/
    ├── generate-code.mjs                 ← 從參數產生客製化 Code.gs
    ├── deploy-via-clasp.ps1              ← Windows 一鍵部署
    └── api-bypass/
        ├── auth.py                       ← Google API 授權
        ├── create_project.py             ← 模式 C：建立專案
        ├── add_milestone.py              ← 模式 C：新增階段日期
        └── requirements.txt
```

## 💡 快速開始

```powershell
# 模式 A：手動
# → 開 https://script.google.com，貼 templates/Code.gs，改 SETTINGS，執行 installFlow()

# 模式 B：自動部署
node scripts/generate-code.mjs --root <FolderID> --admin <Email>
.\scripts\deploy-via-clasp.ps1 -Title "行政工作流"

# 模式 C：純 API（無 Apps Script）
python scripts/api-bypass/create_project.py `
  --year 115 --office 教務處 --name "AI 研習" `
  --owner 王老師 --owner-email wang@school.edu.tw `
  --root-folder-id <FolderID>
```

詳細步驟見對應的 `references/mode-*.md`。

## 🤝 與其他 SKILL 搭配

| SKILL | 角色 |
|-------|------|
| `google-workspace-classroom-flow` | 姊妹 SKILL，班級經營+正向管教軸 |
| `notebooklm` | 把專案資料夾餵 NotebookLM 做語意搜尋 |
| `google-drive` | 額外操作建好的資料夾 |
| `pdf` / `xlsx` | 匯出結案文件 / 進階統計 |

## 👨‍🏫 關於作者

<div align="center">

### 曾慶良 主任（阿亮老師）

<img src="作者資訊.png" width="600" alt="作者資訊">

<br>

<table>
<tr>
<td width="50%">

**📌 現任職務**

🎓 新興科技推廣中心主任<br>
🎓 教育部學科中心研究教師<br>
🎓 臺北市資訊教育輔導員

</td>
<td width="50%">

**🏆 獲獎紀錄**

🥇 2025 年 SETEAM 教學專業講師認證<br>
🥇 2024 年 教育部人工智慧講師認證<br>
🥇 2022、2023 年 指導學生 XR 專題競賽特優<br>
🥇 2022 年 VR 教材開發教師組特優<br>
🥇 2019 年 百大資訊人才獎<br>
🥇 2018、2019 年 親子天下創新 100 教師<br>
🥇 2018 年 臺北市特殊優良教師<br>
🥇 2017 年 教育部行動學習優等

</td>
</tr>
</table>

<br>

### 📞 聯絡方式

[![YouTube](https://img.shields.io/badge/YouTube-@Liang--yt02-red?style=for-the-badge&logo=youtube)](https://www.youtube.com/@Liang-yt02)
[![Facebook](https://img.shields.io/badge/Facebook-3A科技研究社-blue?style=for-the-badge&logo=facebook)](https://www.facebook.com/groups/2754139931432955)
[![Email](https://img.shields.io/badge/Email-3a01chatgpt@gmail.com-green?style=for-the-badge&logo=gmail)](mailto:3a01chatgpt@gmail.com)

</div>

## 📜 授權聲明

**© 2026 阿亮老師 版權所有**

本 SKILL 僅供「阿亮老師課程學員」學習使用。

### ⚠️ 禁止事項

- ❌ 禁止修改本 SKILL 內容
- ❌ 禁止轉傳或散布
- ❌ 禁止商業使用
- ❌ 禁止未經授權之任何形式使用

如有任何授權需求，請聯繫作者。

---

<div align="center">

## 🌟 喜歡這個 SKILL 嗎？

如果這個工具對您的學校行政工作有幫助，請給我們一個 ⭐ Star！

<br>

**Made with ❤️ by 阿亮老師**

<br>

[⬆️ 回到頂部](#google-workspace-admin-flow)

---

© 2026 阿亮老師 版權所有

</div>
