# 客製化點清單

依學校情境調整以下項目。修改 `templates/Code.gs` 內對應段落即可。

## 一、處室列表

**位置**：`buildIntakeForm()` 函式中「承辦處室」欄位

預設值：說明文字「例：教務處、學務處、總務處、資訊組」

要改成下拉選單：

```javascript
// 把
f.addTextItem().setTitle('承辦處室').setRequired(true).setHelpText('例：教務處、學務處、總務處、資訊組');

// 改成
f.addListItem()
  .setTitle('承辦處室').setRequired(true)
  .setChoiceValues(['教務處', '學務處', '總務處', '輔導室', '資訊組', '人事室', '會計室']);
```

## 二、日期類型（階段日期表）

**位置**：`buildMilestoneForm()` 函式

預設 14 選項。要加學校特有日期：

```javascript
f.addListItem().setTitle('日期類型').setRequired(true).setChoiceValues([
  '校內協調會', '第一次會議',
  '報名開始日', '報名截止日', '資料回收期限',
  '採購期限', '經費核銷期限',
  '活動前檢查日', '正式活動日期',
  '照片與成果資料回收日', '成果報告初稿期限', '成果送出期限',
  '結案檢討日',
  '校外參訪日',     // ← 新增
  '家長日',         // ← 新增
  '評鑑訪視日',     // ← 新增
  '其他',
]);
```

加完日期類型後，記得到 `stageFromDateType()` 補對應的階段分類：

```javascript
function stageFromDateType(type) {
  // ... 原有
  if (['校外參訪日', '家長日'].includes(t)) return '執行';
  if (t === '評鑑訪視日') return '結案';
  // ...
}
```

## 三、預設任務模板（10 筆）

**位置**：`defaultTaskRows(data)` 函式

依專案類型可以分流：

```javascript
function defaultTaskRows(data) {
  const projectType = data['專案類型'] || '一般';

  if (projectType === '研習') return researchTasks(data);
  if (projectType === '採購') return procurementTasks(data);
  if (projectType === '評鑑') return evaluationTasks(data);
  return generalTasks(data);
}

function researchTasks(data) {
  const owner = data['承辦人'] || '';
  return [
    ['T001', '公文', '整理研習公文要求', '', owner, '', '', '', '未開始', '否', '', ''],
    ['T002', '籌備', '邀請講師', '', owner, '', '', '', '未開始', '否', '', ''],
    ['T003', '籌備', '場地與設備預約', '', owner, '總務處', '', '', '未開始', '否', '', ''],
    ['T004', '籌備', '研習報名表單', '', owner, '', '', '', '未開始', '否', '', ''],
    // ...
  ];
}
```

## 四、子資料夾結構

**位置**：`PROJECT_SUBFOLDERS` 常數

預設 11 個，要改順序或新增：

```javascript
const PROJECT_SUBFOLDERS = [
  '00_原始公文與附件',
  '01_計畫書與核定資料',
  '02_工作分工與會議紀錄',
  // ... 加你的
  '10_問卷與評量結果',  // ← 新增
  '99_系統產生文件',
];
```

加完後記得同步調整 `defaultChecklistRows()` 對應的「存放位置」欄位。

## 五、Calendar 提醒間隔

**位置**：`wireInitialReminders()` 函式

預設「前 7 天提醒」。要改成「前 14 天 + 前 7 天 + 前 3 天」：

```javascript
// 把單一行
tryCreateAllDay(cal, `【成果前7天提醒】${data['專案名稱']}`, shiftDate(data['成果繳交期限'], -7), desc);

// 改成多個
[14, 7, 3].forEach(days => {
  tryCreateAllDay(cal,
    `【成果前${days}天提醒】${data['專案名稱']}`,
    shiftDate(data['成果繳交期限'], -days),
    desc);
});
```

## 六、Gmail 通知信內容

**位置**：`notifyOwnerOfProject()` 與 `notifyOwnerOfMilestone()`

要加學校簽名檔：

```javascript
const lines = [
  // ... 原有內容
  '',
  '— 行政專案半自動工作流系統',
  '○○國中｜資訊組｜分機 5xx',
];
```

要客製稱謂（例如不叫「老師」叫「主任」）：

```javascript
const greeting = data['承辦人職稱'] || '老師';
lines.push(`${data['承辦人'] || ''} ${greeting}您好：`);
```

## 七、專案編號格式

**位置**：`buildProjectCode(data)` 函式

預設：`{年度}-{處室}-{MMddHHmmss}` → 範例 `115-教務處-0521143025`

要改成更短：

```javascript
function buildProjectCode(data) {
  const y = data['專案年度'] || '000';
  const o = (data['承辦處室'] || '未').substring(0, 2);  // 只取前 2 字
  const ts = Utilities.formatDate(new Date(), SETTINGS.timezone, 'yyMMddHHmm');
  return `${y}${o}${ts}`;  // 例：115教務2605211430
}
```

## 八、總控表額外欄位

要在總控表加學校特有欄位（例如「核定文號」、「校長批示」）：

1. 在 `CONTROL_HEADERS` 加上欄名
2. 在 `recordProjectToControl()` 補對應的值
3. 必要時也改 `lookupProject()` 的回傳結構

## 九、客製化檢查清單

部署到學校前，逐項確認：

- [ ] 處室列表是否符合貴校組織
- [ ] 日期類型是否含校內特有事件（家長日、評鑑、招生）
- [ ] 預設任務是否符合常見專案類型
- [ ] 子資料夾結構是否符合校內歸檔慣例
- [ ] 提醒間隔是否合理（太密會被忽略，太疏會遺漏）
- [ ] 通知信內容是否符合校內溝通語氣
- [ ] 是否要加學校 logo / 簽名檔
- [ ] 是否要對接學校現有的公文系統（API / 信件）
