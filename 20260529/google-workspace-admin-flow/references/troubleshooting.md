# 疑難排解

## 一、安裝階段

### `Exception: Cannot find file with id`
**症狀**：執行 `installFlow()` 時報錯
**原因**：`SETTINGS.rootFolderId` 不存在、貼錯、或你沒有該資料夾的權限
**處理**：
1. 執行 `checkDriveAccess()` 確認
2. 重新從 Drive 網址抄 ID（網址中 `/folders/` 後面那串）
3. 確認該帳號對該資料夾有「編輯者」權限

### `You do not have permission to call FormApp.create`
**症狀**：第一次安裝就跳這個
**原因**：Apps Script 還沒授權
**處理**：
1. 編輯器中執行 `installFlow()`
2. 跳出授權視窗 → 「審查權限」→「進階」→「前往 [專案名稱]」→「允許」
3. 重新執行

### `Exception: Service invoked too many times`
**症狀**：執行中途報錯
**原因**：Google 對 Apps Script 有每日呼叫上限（Form 建立 ~ 100 次/天）
**處理**：
1. 確認你不是在迴圈中重複建表單
2. 等 24 小時配額重置
3. 改用模式 C（純 API）

### Apps Script 編輯器看不到「新增專案」按鈕
**症狀**：開 https://script.google.com 但沒有按鈕
**原因**：Google Workspace 管理員停用了 Apps Script
**處理**：請資訊組到 Admin Console 開啟「Google Apps Script for users」

## 二、表單送出後沒反應

### Form 填了但沒有建專案
**檢查順序**：
1. 開「公文專案啟動表_表單回應」Sheet → 看資料是否真的進來
2. 開 Apps Script → 「執行作業」→ 看 `onIntakeSubmit` 是否被觸發
3. 若沒被觸發 → 觸發器設定問題

**修法**：
```javascript
// 在 Apps Script 編輯器執行
wireTrigger('onIntakeSubmit', PROPS.getProperty('INTAKE_RESPONSE_SHEET_ID'));
```

### 觸發器跑了但沒建檔
**檢查**：Apps Script → 「執行作業」→ 找剛剛那次 `onIntakeSubmit` 的紀錄 → 看錯誤訊息

**常見錯誤**：
- `缺少必填欄位：xxx` → Form 欄位名稱被改過，跟程式碼對不上
- `找不到指定 Calendar` → `SETTINGS.calendarId` 錯誤
- `沒有取得表單回應資料` → 觸發器類型錯誤，應為「試算表：提交表單時」

## 三、Calendar 提醒問題

### 沒有出現提醒
**檢查順序**：
1. 執行 `checkCalendar()` 確認日曆 ID 對
2. 確認執行 Apps Script 的帳號有該日曆的「建立事件」權限
3. 確認 Form 「是否建立 Calendar 提醒」選了「是」
4. 開「專案階段日期紀錄」看備註欄是否有錯誤訊息

### Calendar 出現了，但時間錯了
**原因**：時區設定錯誤
**處理**：確認 `SETTINGS.timezone` 是 `Asia/Taipei`

### 一次跑出太多重複事件
**原因**：可能裝了兩次 / 觸發器設了兩個
**處理**：
1. 執行 `uninstallFlow()`
2. 手動清掉重複的 Calendar 事件
3. 重新執行 `installFlow()`

## 四、Gmail 通知問題

### 通知信沒寄出
**檢查**：
1. 確認 Form 的「承辦人 Email」欄位有填
2. Apps Script「執行作業」看有沒有 Gmail 相關錯誤
3. 確認該帳號 Gmail 配額沒爆（每日 100-1500 封依帳號類型）

### 通知信被當垃圾信
**處理**：
- 在 Apps Script 編輯器執行一封自己寄給自己 → 加白名單
- 若是 Workspace 帳號 → 請資訊組調整 SMTP / DKIM 設定
- 信件內容避免太多連結（Gmail 會視為廣告信）

### 信件主旨亂碼
**原因**：通常是 Form 欄位內含特殊字元
**處理**：用 `toSafeFileName()` 函式清理過後才放入 subject

## 五、表單欄位不對

### Form 欄位想改但 setupAdminWorkflow 沒重建表單
**原因**：`setupAdminWorkflow` 用 ScriptProperties 保存 Form ID，不會重建
**處理**：
1. Apps Script 「專案設定」→「指令碼屬性」
2. 刪掉 `INTAKE_FORM_ID`、`INTAKE_RESPONSE_SHEET_ID`（或執行 `uninstallFlow()`）
3. 重新執行 `installFlow()`

### 改了 Form 欄位後總控表沒對應
**原因**：欄位名稱不一致，`onIntakeSubmit` 抓不到資料
**處理**：
1. 改 Form 欄位 → 同步改 `requireFields()` 與 `data[...]` 的所有引用
2. 改 `CONTROL_HEADERS` 加新欄
3. 改 `recordProjectToControl()` 寫入邏輯

## 六、找不到專案編號

### 階段日期表填了不存在的專案編號
**症狀**：階段日期紀錄狀態「錯誤」，備註「找不到專案編號」
**處理**：
1. 從總控表複製專案編號（不要手打）
2. 確認總控表第一欄是「專案編號」
3. 確認編號格式：`{年度}-{處室}-{時間戳}`

## 七、清掉重來

最簡單的「壞了就重來」方式：

```javascript
// 1. 清掉觸發器與 ScriptProperties
uninstallFlow();

// 2. 手動刪掉舊的 Form 與回應 Sheet（在 Drive）
//    或直接保留，重裝會用新的

// 3. 重新跑安裝
installFlow();
```

## 八、Debug 技巧

### 在程式中加 Logger
```javascript
function onIntakeSubmit(e) {
  Logger.log(`收到表單：${JSON.stringify(e.namedValues)}`);
  // ... 原有邏輯
}
```

### 用 console.log 看 Cloud Logging
```javascript
function onIntakeSubmit(e) {
  console.log('Submit received', e);
}
```
然後到 Apps Script「執行作業」→「Cloud Logging」看。

### 模擬表單送出（不用真的填表）
```javascript
function testIntakeSubmit() {
  const fakeEvent = {
    namedValues: {
      '專案年度': ['115'],
      '承辦處室': ['測試'],
      '專案名稱': ['測試專案'],
      '承辦人': ['測試人'],
      '承辦人Email': ['test@example.com'],
      '活動日期': ['2026-07-01'],
      '成果繳交期限': ['2026-08-01'],
    }
  };
  onIntakeSubmit(fakeEvent);
}
```

## 九、求助管道

- Apps Script 官方文件：https://developers.google.com/apps-script
- clasp GitHub：https://github.com/google/clasp
- Google Apps Script Stack Overflow：https://stackoverflow.com/questions/tagged/google-apps-script
