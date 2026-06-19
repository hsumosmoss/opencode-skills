# 模式 A：手動引導安裝（15 分鐘）

## 適用對象

- 第一次接觸 Apps Script 的老師
- 研習現場學員（不會 CLI）
- 只裝一次、不需重複部署

## 操作步驟

### 步驟 1：準備 Google Drive 總資料夾

1. 開啟 [Google Drive](https://drive.google.com)
2. 新建一個資料夾，命名「行政專案工作流」（或任何你喜歡的名字）
3. 進入該資料夾，看網址列：
   ```
   https://drive.google.com/drive/folders/1AbCdEfGhIjKlMnOpQrStUvWxYz
                                          └─────── 這串就是 Folder ID
   ```
4. 把 Folder ID 抄下來（待會要用）

### 步驟 2：取得 Calendar ID（可跳過）

如果你想用個人預設日曆，直接用 `primary` 就好。

要用學校共用日曆：
1. 開 [Google Calendar](https://calendar.google.com)
2. 左側日曆列表 → 滑鼠移到目標日曆 → ⋮ → 「設定和共用」
3. 拉到「整合日曆」→ 複製「日曆編號」（會是 Email 格式）

### 步驟 3：建立 Apps Script 專案

1. 開 [Apps Script](https://script.google.com)
2. 左上角「新增專案」
3. 把專案命名為「行政專案工作流」
4. 把 `templates/Code.gs` 的**全部內容**貼到編輯器

### 步驟 4：修改 SETTINGS

在程式碼最上方找到 `SETTINGS`，改成你的值：

```javascript
const SETTINGS = {
  rootFolderId:    '1AbCdEfGhIjKlMnOpQrStUvWxYz',      // ← 你的 Folder ID
  controlSheetId:  '',                                  // ← 留空
  calendarId:      'primary',                           // ← 個人帳號就用 primary
  adminEmail:      'your.email@school.edu.tw',          // ← 你的 Email
  timezone:        'Asia/Taipei',                       // ← 不用改
};
```

### 步驟 5：第一次執行（會要求授權）

1. 編輯器左上角下拉選單，選 `installFlow`
2. 點「執行」（▶）
3. 跳出授權視窗 → 「審查權限」→ 選你的 Google 帳號
4. 出現「Google 尚未驗證此應用程式」警告 → 「進階」→「前往 [專案名稱]（不安全）」
5. 列出權限清單 → 「允許」

### 步驟 6：確認安裝成功

執行紀錄（Logger）會印出 7 個連結：

```
✅ 安裝完成
intakeFormEdit:    https://docs.google.com/forms/d/.../edit
intakeFormFill:    https://docs.google.com/forms/d/e/.../viewform   ← 給承辦人填的網址
intakeResponses:   https://docs.google.com/spreadsheets/d/.../edit
milestoneFormEdit: ...
milestoneFormFill: ...                                              ← 給負責人填的網址
milestoneResp:     ...
controlSheet:      https://docs.google.com/spreadsheets/d/.../edit  ← 總控表
```

把 **intakeFormFill** 和 **milestoneFormFill** 兩個網址抄起來，這就是要給承辦人/負責人填的表單。

### 步驟 7：自我檢測

執行 `runSelfCheck`，確認三項都通過：

```
── 開始自我檢測 ──
✅ Drive：行政專案工作流
✅ 總控表：行政專案總控表
✅ 日曆：用戶名稱
── 自我檢測結束 ──
```

### 步驟 8：實測一筆假資料

1. 開啟 `intakeFormFill` 網址
2. 填一筆測試資料（年度 115、處室「測試」、名稱「測試案」、Email 填你自己的）
3. 送出
4. 確認：
   - Drive 總資料夾下「03_專案資料夾」出現新資料夾
   - 你的 Gmail 收到通知信
   - 「行政專案總控表」多一列

## 如果失敗了

依錯誤訊息查看 `troubleshooting.md`。

## 常見追問

**Q：可以重裝嗎？**
A：可以。執行 `uninstallFlow()` 清掉觸發器 + ScriptProperties，再執行 `installFlow()`。Form 與 Sheet 不會被刪。

**Q：可以裝在學校的 Workspace 帳號嗎？**
A：可以，但 Google Workspace 管理員可能限制 Apps Script 對外寄信。執行時若 Gmail 通知沒寄出，問問資訊組。

**Q：可以共用給其他承辦人嗎？**
A：把 Drive 總資料夾的權限設為「校內可編輯」即可。表單網址也分享給對應的人。
