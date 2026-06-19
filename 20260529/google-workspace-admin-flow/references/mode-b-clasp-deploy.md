# 模式 B：clasp 自動部署（3 分鐘）

## 適用對象

- 主任、組長要重複部署到多個學校 / 多個帳號
- 有 Node.js / CLI 基礎
- 想用 git 管理 Apps Script 程式碼

## 前置需求

```powershell
# 安裝 clasp（Google 官方 Apps Script CLI）
npm install -g @google/clasp

# 開啟 Apps Script API
# 開瀏覽器到 https://script.google.com/home/usersettings
# 把「Google Apps Script API」打開

# 登入
clasp login
```

## 部署流程

### 步驟 1：準備 SETTINGS 參數

填寫部署參數檔（建議用 .env 或直接放 JSON）：

```json
{
  "rootFolderId": "1AbCdEfGhIjKlMnOpQrStUvWxYz",
  "controlSheetId": "",
  "calendarId": "primary",
  "adminEmail": "admin@school.edu.tw"
}
```

### 步驟 2：跑生成器產出客製化 Code.gs

```powershell
# 從本 SKILL 目錄執行
node scripts/generate-code.mjs `
  --root "1AbCdEfGhIjKlMnOpQrStUvWxYz" `
  --calendar primary `
  --admin "admin@school.edu.tw" `
  --out ./build/Code.gs
```

### 步驟 3：建立 Apps Script 專案並推上去

```powershell
# 從本 SKILL 目錄執行
.\scripts\deploy-via-clasp.ps1 -Title "行政專案工作流" -SourceDir .\build
```

腳本會：
1. 在你的 Google 帳號建立新 Apps Script 專案
2. 把 `build/Code.gs` 與 `appsscript.json` 推上去
3. 自動執行 `installFlow()`（透過 clasp run）
4. 印出兩張 Form 與總控表的 URL

### 步驟 4：驗收

腳本結束後會印出：

```
✅ Apps Script 專案已建立：https://script.google.com/d/.../edit
✅ Drive 總資料夾結構已建立
✅ 兩張表單與總控表已建立

公文表單：https://docs.google.com/forms/.../viewform
階段日期表單：https://docs.google.com/forms/.../viewform
行政專案總控表：https://docs.google.com/spreadsheets/.../edit
```

## 多學校批次部署

```powershell
# 假設你有多個學校設定檔
foreach ($cfg in (ls schools\*.json)) {
  $school = (Get-Content $cfg | ConvertFrom-Json)
  node scripts/generate-code.mjs `
    --root $school.rootFolderId `
    --calendar $school.calendarId `
    --admin $school.adminEmail `
    --out "build\$($school.name)\Code.gs"

  .\scripts\deploy-via-clasp.ps1 `
    -Title "行政工作流-$($school.name)" `
    -SourceDir "build\$($school.name)"
}
```

## clasp 常用指令備查

```powershell
# 查看現有專案
clasp list

# 把雲端的 Apps Script 拉下來（搶救已存在的專案）
clasp clone <scriptId>

# 改完程式後推上去
clasp push

# 從本機執行雲端的 Apps Script 函式
clasp run installFlow

# 開啟編輯器
clasp open
```

## 常見問題

**Q：「User has not enabled the Apps Script API」**
A：開 https://script.google.com/home/usersettings 把 API 打開。

**Q：clasp login 一直失敗**
A：可能是 Google Workspace 管理員限制了第三方應用程式。換個人 Google 帳號試試。

**Q：clasp run 出現 timeout**
A：`installFlow()` 第一次跑會建很多檔案，可能超過 6 分鐘上限。改用 `clasp open` 進編輯器手動執行。

**Q：能不能不用 clasp，純 HTTP API 部署？**
A：可以，用 Google Apps Script API 直接 POST。但 OAuth scope 更複雜，clasp 已經封裝好了。
