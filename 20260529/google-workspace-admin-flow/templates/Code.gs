/**
 * 學校行政專案半自動工作流
 *
 * 功能：
 *   - 公文 / 行政任務送出 Google Form 後，自動建立專案資料夾、紀錄文件、
 *     待辦追蹤表、成果檢核表、Calendar 提醒、Gmail 通知
 *   - 後續可透過第二張表單追加階段日期 → 自動同步到待辦表 + Calendar
 *
 * 安裝順序：
 *   1. 將本程式碼貼到新的 Apps Script 專案
 *   2. 修改下方 SETTINGS（4 個值）
 *   3. 執行 installFlow()
 *   4. 從執行紀錄取得兩張表單網址
 *
 * 作者：曾慶良（阿亮老師）
 */

// ──────────────────────────────────────────────────────────────────────────
// 一、SETTINGS（請依學校環境修改）
// ──────────────────────────────────────────────────────────────────────────

const SETTINGS = {
  rootFolderId:    'PASTE_YOUR_DRIVE_FOLDER_ID_HERE',
  controlSheetId:  '',                       // 留空會自動建立
  calendarId:      'primary',                // 不確定就用 primary
  adminEmail:      'admin@example.com',      // 系統錯誤通知收件人
  timezone:        'Asia/Taipei',
};

// 子資料夾與 ScriptProperties 名稱集中管理
const NAMES = {
  intakeFolder:    '01_公文專案啟動表',
  controlFolder:   '02_專案總控表',
  projectsFolder:  '03_專案資料夾',
  milestoneFolder: '04_專案階段日期新增表',
  scriptFolder:    '06_Apps Script',
  controlSheet:    '行政專案總控表',
  ledgerSheet:     '專案階段日期紀錄',
  intakeForm:      '公文專案啟動表',
  intakeResp:      '公文專案啟動表_表單回應',
  milestoneForm:   '專案階段日期新增表',
  milestoneResp:   '專案階段日期新增表_表單回應',
};

const PROPS = PropertiesService.getScriptProperties();
const PROP_KEYS = {
  controlSheet:    'CONTROL_SHEET_ID',
  intakeForm:      'INTAKE_FORM_ID',
  intakeResp:      'INTAKE_RESPONSE_SHEET_ID',
  milestoneForm:   'MILESTONE_FORM_ID',
  milestoneResp:   'MILESTONE_RESPONSE_SHEET_ID',
};

// ──────────────────────────────────────────────────────────────────────────
// 二、安裝入口
// ──────────────────────────────────────────────────────────────────────────

/**
 * 主安裝函式。第一次跑會：
 *   1. 在總資料夾建立 5 個子資料夾
 *   2. 建立總控表（含兩個 sheet）
 *   3. 建立兩張 Form 與對應回應表
 *   4. 註冊兩個 onSubmit 觸發器
 */
function installFlow() {
  const root = DriveApp.getFolderById(SETTINGS.rootFolderId);

  const folders = setupRootFolders(root);
  const control = setupControlSpreadsheet(folders.control);

  const intake = setupIntakeForm(folders.intake);
  const milestone = setupMilestoneForm(folders.milestone);

  wireTrigger('onIntakeSubmit', intake.responseSheetId);
  wireTrigger('onMilestoneSubmit', milestone.responseSheetId);

  const summary = {
    intakeFormEdit:    FormApp.openById(intake.formId).getEditUrl(),
    intakeFormFill:    FormApp.openById(intake.formId).getPublishedUrl(),
    intakeResponses:   SpreadsheetApp.openById(intake.responseSheetId).getUrl(),
    milestoneFormEdit: FormApp.openById(milestone.formId).getEditUrl(),
    milestoneFormFill: FormApp.openById(milestone.formId).getPublishedUrl(),
    milestoneResp:     SpreadsheetApp.openById(milestone.responseSheetId).getUrl(),
    controlSheet:      control.getUrl(),
  };

  Logger.log('✅ 安裝完成');
  Object.entries(summary).forEach(([k, v]) => Logger.log(`${k}: ${v}`));
  return summary;
}

/** 卸載入口（清掉觸發器與 ScriptProperties，不刪檔案） */
function uninstallFlow() {
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));
  Object.values(PROP_KEYS).forEach(k => PROPS.deleteProperty(k));
  Logger.log('🧹 卸載完成（觸發器與 ScriptProperties 已清空，檔案保留）');
}

// ──────────────────────────────────────────────────────────────────────────
// 三、總資料夾與總控表
// ──────────────────────────────────────────────────────────────────────────

function setupRootFolders(root) {
  return {
    intake:    ensureSubFolder(root, NAMES.intakeFolder),
    control:   ensureSubFolder(root, NAMES.controlFolder),
    projects:  ensureSubFolder(root, NAMES.projectsFolder),
    milestone: ensureSubFolder(root, NAMES.milestoneFolder),
    script:    ensureSubFolder(root, NAMES.scriptFolder),
  };
}

function setupControlSpreadsheet(controlFolder) {
  let id = SETTINGS.controlSheetId || PROPS.getProperty(PROP_KEYS.controlSheet) || '';
  let ss;

  if (id) {
    ss = SpreadsheetApp.openById(id);
  } else {
    ss = SpreadsheetApp.create(NAMES.controlSheet);
    id = ss.getId();
    relocateFile(id, controlFolder);
    PROPS.setProperty(PROP_KEYS.controlSheet, id);
  }

  ensureControlSheet(ss);
  ensureLedgerSheet(ss);
  return ss;
}

function ensureControlSheet(ss) {
  return ensureSheetWithHeaders(ss, NAMES.controlSheet, CONTROL_HEADERS);
}

function ensureLedgerSheet(ss) {
  return ensureSheetWithHeaders(ss, NAMES.ledgerSheet, LEDGER_HEADERS);
}

const CONTROL_HEADERS = [
  '專案編號', '專案名稱', '年度', '承辦處室', '承辦人', '承辦人Email',
  'Drive資料夾連結', '專案紀錄Docs連結', '待辦追蹤表連結', '成果檢核表連結',
  'NotebookLM筆記本連結', '專案狀態', '備註',
  '來文單位', '公文文號', '建立日期',
  '活動日期', '成果期限', '經費期限', '是否有經費',
];

const LEDGER_HEADERS = [
  '紀錄編號', '新增時間', '建立者Email', '專案編號', '專案名稱',
  '日期類型', '日期', '提醒設定', '負責人', '負責人Email',
  '是否寫入待辦追蹤表', '是否建立Calendar提醒', '說明',
  'Calendar事件ID', '對應待辦追蹤表連結', '狀態', '備註',
];

// ──────────────────────────────────────────────────────────────────────────
// 四、兩張 Form 建立
// ──────────────────────────────────────────────────────────────────────────

function setupIntakeForm(folder) {
  let formId = PROPS.getProperty(PROP_KEYS.intakeForm) || '';
  let respId = PROPS.getProperty(PROP_KEYS.intakeResp) || '';

  if (!formId || !respId) {
    const respSs = SpreadsheetApp.create(NAMES.intakeResp);
    respId = respSs.getId();
    relocateFile(respId, folder);

    const form = buildIntakeForm();
    form.setDestination(FormApp.DestinationType.SPREADSHEET, respId);
    formId = form.getId();
    relocateFile(formId, folder);

    PROPS.setProperty(PROP_KEYS.intakeForm, formId);
    PROPS.setProperty(PROP_KEYS.intakeResp, respId);
  }

  return { formId, responseSheetId: respId };
}

function setupMilestoneForm(folder) {
  let formId = PROPS.getProperty(PROP_KEYS.milestoneForm) || '';
  let respId = PROPS.getProperty(PROP_KEYS.milestoneResp) || '';

  if (!formId || !respId) {
    const respSs = SpreadsheetApp.create(NAMES.milestoneResp);
    respId = respSs.getId();
    relocateFile(respId, folder);

    const form = buildMilestoneForm();
    form.setDestination(FormApp.DestinationType.SPREADSHEET, respId);
    formId = form.getId();
    relocateFile(formId, folder);

    PROPS.setProperty(PROP_KEYS.milestoneForm, formId);
    PROPS.setProperty(PROP_KEYS.milestoneResp, respId);
  }

  return { formId, responseSheetId: respId };
}

function buildIntakeForm() {
  const f = FormApp.create(NAMES.intakeForm);
  f.setDescription(
    '收到需追蹤的公文或行政任務時，請填寫本表。送出後系統會自動建立：\n' +
    '專案資料夾、專案紀錄、待辦追蹤表、成果檢核表、Calendar 提醒、Gmail 通知。\n\n' +
    '註：本表「不收附件」。公文與附件請在專案建立完成後，自行上傳到專案資料夾中的「00_原始公文與附件」。'
  );
  f.setCollectEmail(true);

  f.addSectionHeaderItem().setTitle('一、基本資料').setHelpText('建立專案資料夾與總控表會用到。');
  f.addTextItem().setTitle('專案年度').setRequired(true).setHelpText('例：115');
  f.addTextItem().setTitle('承辦處室').setRequired(true).setHelpText('例：教務處、學務處、總務處、資訊組');
  f.addTextItem().setTitle('專案名稱').setRequired(true).setHelpText('例：AI 融入教學研習');
  f.addTextItem().setTitle('承辦人').setRequired(true);
  f.addTextItem().setTitle('承辦人Email').setRequired(true);
  f.addParagraphTextItem().setTitle('協辦人員');

  f.addSectionHeaderItem().setTitle('二、公文資訊').setHelpText('若非正式公文，可填通知/任務來源。');
  f.addTextItem().setTitle('公文主旨');
  f.addTextItem().setTitle('來文單位');
  f.addDateItem().setTitle('公文日期');
  f.addTextItem().setTitle('公文文號');

  f.addSectionHeaderItem().setTitle('三、期限與成果要求');
  f.addDateItem().setTitle('活動日期');
  f.addDateItem().setTitle('成果繳交期限');
  f.addDateItem().setTitle('經費核銷期限');
  f.addMultipleChoiceItem().setTitle('是否有經費').setChoiceValues(['是', '否', '不確定']);
  f.addTextItem().setTitle('核定或預估金額');
  f.addMultipleChoiceItem().setTitle('是否需要收家長或教師回覆').setChoiceValues(['是', '否', '不確定']);
  f.addMultipleChoiceItem().setTitle('是否需要活動照片').setChoiceValues(['是', '否', '不確定']);
  f.addMultipleChoiceItem().setTitle('是否需要成果報告').setChoiceValues(['是', '否', '不確定']);
  f.addParagraphTextItem().setTitle('備註');

  return f;
}

function buildMilestoneForm() {
  const f = FormApp.create(NAMES.milestoneForm);
  f.setDescription('既有專案要追加重要日期、階段任務或 Calendar 提醒時填寫。請先從行政專案總控表查詢專案編號。');
  f.setCollectEmail(false);

  f.addTextItem().setTitle('專案編號').setRequired(true).setHelpText('請填行政專案總控表中的專案編號');
  f.addTextItem().setTitle('專案名稱').setRequired(true);
  f.addListItem().setTitle('日期類型').setRequired(true).setChoiceValues([
    '校內協調會', '第一次會議',
    '報名開始日', '報名截止日', '資料回收期限',
    '採購期限', '經費核銷期限',
    '活動前檢查日', '正式活動日期',
    '照片與成果資料回收日', '成果報告初稿期限', '成果送出期限',
    '結案檢討日', '其他',
  ]);
  f.addDateItem().setTitle('日期').setRequired(true);
  f.addCheckboxItem().setTitle('提醒設定').setChoiceValues([
    '當天提醒', '前1天提醒', '前3天提醒', '前7天提醒', '前14天提醒',
  ]);
  f.addTextItem().setTitle('負責人').setRequired(true);
  f.addTextItem().setTitle('負責人Email').setRequired(true);
  f.addMultipleChoiceItem().setTitle('是否寫入待辦追蹤表').setHelpText('沒特殊原因請選「是」').setRequired(true).setChoiceValues(['是', '否']);
  f.addMultipleChoiceItem().setTitle('是否建立Calendar提醒').setHelpText('沒特殊原因請選「是」').setRequired(true).setChoiceValues(['是', '否']);
  f.addParagraphTextItem().setTitle('說明');
  f.addParagraphTextItem().setTitle('備註');

  return f;
}

// ──────────────────────────────────────────────────────────────────────────
// 五、觸發器註冊
// ──────────────────────────────────────────────────────────────────────────

function wireTrigger(handlerName, responseSheetId) {
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === handlerName)
    .forEach(t => ScriptApp.deleteTrigger(t));

  ScriptApp.newTrigger(handlerName)
    .forSpreadsheet(SpreadsheetApp.openById(responseSheetId))
    .onFormSubmit()
    .create();
}

// ──────────────────────────────────────────────────────────────────────────
// 六、主流程：新建專案（onIntakeSubmit）
// ──────────────────────────────────────────────────────────────────────────

function onIntakeSubmit(e) {
  try {
    const data = extractFormData(e);
    requireFields(data, ['專案年度', '承辦處室', '專案名稱', '承辦人', '承辦人Email']);

    const projectCode = buildProjectCode(data);
    const folderName = toSafeFileName(`${data['專案年度']}_${data['承辦處室']}_${data['專案名稱']}`);

    const root = DriveApp.getFolderById(SETTINGS.rootFolderId);
    const projectsRoot = ensureSubFolder(root, NAMES.projectsFolder);
    const projectFolder = projectsRoot.createFolder(folderName);

    const subs = buildProjectFolders(projectFolder);
    const projectDoc = buildProjectRecordDoc(data, subs);
    const taskSheet = buildTaskSheet(data, projectFolder);
    const checklistSheet = buildChecklistSheet(data, projectFolder);

    wireInitialReminders(data, projectFolder, taskSheet, checklistSheet);

    recordProjectToControl({ projectCode, data, projectFolder, projectDoc, taskSheet, checklistSheet });
    notifyOwnerOfProject({ projectCode, data, projectFolder, projectDoc, taskSheet, checklistSheet });

  } catch (err) {
    console.error(err);
    notifyAdminOfError(err);
  }
}

// ──────────────────────────────────────────────────────────────────────────
// 七、專案子資料夾
// ──────────────────────────────────────────────────────────────────────────

const PROJECT_SUBFOLDERS = [
  '00_原始公文與附件',
  '01_計畫書與核定資料',
  '02_工作分工與會議紀錄',
  '03_表單與回覆資料',
  '04_經費與採購核銷',
  '05_活動照片與照片說明',
  '06_成果資料與成果報告',
  '07_公告通知與對外文字',
  '08_簡報與成果展示',
  '09_檢討與下次改進',
  '99_系統產生文件',
];

function buildProjectFolders(projectFolder) {
  const map = {};
  PROJECT_SUBFOLDERS.forEach(name => { map[name] = projectFolder.createFolder(name); });
  return map;
}

// ──────────────────────────────────────────────────────────────────────────
// 八、專案紀錄 Docs
// ──────────────────────────────────────────────────────────────────────────

function buildProjectRecordDoc(data, subs) {
  const name = toSafeFileName(`${data['專案年度']}_${data['承辦處室']}_${data['專案名稱']}_專案紀錄`);
  const doc = DocumentApp.create(name);
  const body = doc.getBody();

  body.appendParagraph('行政專案紀錄文件').setHeading(DocumentApp.ParagraphHeading.TITLE);

  appendSection(body, '一、基本資料', [
    ['公文主旨', data['公文主旨']],
    ['來文單位', data['來文單位']],
    ['公文日期', data['公文日期']],
    ['公文文號', data['公文文號']],
    ['專案名稱', data['專案名稱']],
    ['專案年度', data['專案年度']],
    ['承辦處室', data['承辦處室']],
    ['承辦人', data['承辦人']],
    ['承辦人Email', data['承辦人Email']],
    ['協辦人員', data['協辦人員']],
  ]);

  appendSection(body, '二、重要期限', [
    ['活動日期', data['活動日期']],
    ['成果繳交期限', data['成果繳交期限']],
    ['經費核銷期限', data['經費核銷期限']],
  ]);

  appendSection(body, '三、經費資訊', [
    ['是否有經費', data['是否有經費']],
    ['核定或預估金額', data['核定或預估金額']],
  ]);

  appendFreeSection(body, '四、公文要求摘要', '請後續用 NotebookLM 或 Gemini 整理後補入。');
  appendFreeSection(body, '五、執行紀錄', '日期｜事項｜處理情形｜負責人');
  appendListSection(body, '六、成果資料', ['照片：', '簽到表：', '回饋表：', '成果報告：', '經費附件：']);
  appendListSection(body, '七、缺漏檢查', ['尚缺資料：', '需要補件：', '需人工確認：']);
  appendListSection(body, '八、檢討與下次建議', ['本次問題：', '下次改善：', '可沿用資料：']);
  appendFreeSection(body, '九、NotebookLM 建議提問',
    '請根據本專案來源資料，整理公文要求、重要期限、成果報告要求、目前缺漏資料與需要人工確認的地方。');

  doc.saveAndClose();

  const file = DriveApp.getFileById(doc.getId());
  subs['99_系統產生文件'].addFile(file);
  DriveApp.getRootFolder().removeFile(file);
  return file;
}

function appendSection(body, title, pairs) {
  body.appendParagraph(title).setHeading(DocumentApp.ParagraphHeading.HEADING1);
  pairs.forEach(([k, v]) => body.appendParagraph(`${k}：${v || ''}`));
}

function appendFreeSection(body, title, text) {
  body.appendParagraph(title).setHeading(DocumentApp.ParagraphHeading.HEADING1);
  body.appendParagraph(text);
}

function appendListSection(body, title, lines) {
  body.appendParagraph(title).setHeading(DocumentApp.ParagraphHeading.HEADING1);
  lines.forEach(line => body.appendParagraph(line));
}

// ──────────────────────────────────────────────────────────────────────────
// 九、待辦追蹤表
// ──────────────────────────────────────────────────────────────────────────

const TASK_HEADERS = [
  '任務編號', '階段', '任務名稱', '任務說明',
  '負責人', '協助單位', '期限', '提醒日期',
  '狀態', '需要附件', '附件位置', '備註',
];

function buildTaskSheet(data, projectFolder) {
  const name = toSafeFileName(`${data['專案年度']}_${data['承辦處室']}_${data['專案名稱']}_待辦追蹤表`);
  const ss = SpreadsheetApp.create(name);
  const sh = ss.getActiveSheet();
  sh.setName('待辦追蹤');

  sh.appendRow(TASK_HEADERS);
  defaultTaskRows(data).forEach(r => sh.appendRow(r));

  applyDataValidation(sh.getRange('I2:I'), ['未開始', '進行中', '待確認', '完成']);
  styleHeaderRow(sh, TASK_HEADERS.length);

  const file = DriveApp.getFileById(ss.getId());
  ensureSubFolder(projectFolder, '99_系統產生文件').addFile(file);
  DriveApp.getRootFolder().removeFile(file);
  return file;
}

function defaultTaskRows(data) {
  const owner = data['承辦人'] || '';
  const dResult = data['成果繳交期限'] || '';
  const dBudget = data['經費核銷期限'] || '';
  const dEvent = data['活動日期'] || '';

  // 預設 10 筆任務（依專案生命週期）
  const tasks = [
    ['T001', '公文', '整理公文要求',        '確認辦理依據、期限、成果要求與附件',         owner, '',     '',       '',       '未開始', '否', '', ''],
    ['T002', '公文', '建立 NotebookLM 筆記本', '把公文與附件加入專案 Notebook，連結貼回總控表', owner, '',     '',       '',       '未開始', '否', '', ''],
    ['T003', '籌備', '撰寫或修正計畫書',      '依公文要求完成校內計畫草案',                    owner, '',     '',       '',       '未開始', '是', '', ''],
    ['T004', '籌備', '建立報名或回覆表單',    '確認是否需收教師、家長或學生回覆',              owner, '',     '',       '',       '未開始', '否', '', ''],
    ['T005', '執行', '收集活動照片',          '活動期間收集照片並補上照片說明',                owner, '',     dEvent,   dEvent,   '未開始', '是', '', ''],
    ['T006', '執行', '整理簽到表或參與名冊',  '建立人數與參與對象統計',                        owner, '',     dEvent,   dEvent,   '未開始', '是', '', ''],
    ['T007', '經費', '整理經費明細與憑證',    '確認支出項目、憑證與核銷資料',                  owner, '會計', dBudget,  dBudget,  '未開始', '是', '', ''],
    ['T008', '成果', '撰寫成果報告草稿',      '用 NotebookLM 與 Gemini 協助整理',              owner, '',     dResult,  dResult,  '未開始', '是', '', ''],
    ['T009', '成果', '檢查成果附件是否齊全',  '確認照片、簽到、回饋、經費與公文附件',          owner, '',     dResult,  dResult,  '未開始', '是', '', ''],
    ['T010', '結案', '建立下次改進建議',      '整理檢討與交接注意事項',                        owner, '',     '',       '',       '未開始', '否', '', ''],
  ];
  return tasks;
}

// ──────────────────────────────────────────────────────────────────────────
// 十、成果檢核表
// ──────────────────────────────────────────────────────────────────────────

const CHECKLIST_HEADERS = ['項目', '是否需要', '目前狀態', '存放位置', '負責人', '備註'];

function buildChecklistSheet(data, projectFolder) {
  const name = toSafeFileName(`${data['專案年度']}_${data['承辦處室']}_${data['專案名稱']}_成果檢核表`);
  const ss = SpreadsheetApp.create(name);
  const sh = ss.getActiveSheet();
  sh.setName('成果檢核');

  sh.appendRow(CHECKLIST_HEADERS);
  defaultChecklistRows(data).forEach(r => sh.appendRow(r));

  applyDataValidation(sh.getRange('C2:C'), ['待整理', '進行中', '已完成', '不需要', '需人工確認']);
  styleHeaderRow(sh, CHECKLIST_HEADERS.length);

  const file = DriveApp.getFileById(ss.getId());
  ensureSubFolder(projectFolder, '99_系統產生文件').addFile(file);
  DriveApp.getRootFolder().removeFile(file);
  return file;
}

function defaultChecklistRows(data) {
  const owner = data['承辦人'] || '';
  return [
    ['原始公文',           '是',                                       '待整理', '00_原始公文與附件',         owner, ''],
    ['計畫書或核定資料',   '建議',                                     '待整理', '01_計畫書與核定資料',       owner, ''],
    ['會議紀錄或工作分工', '建議',                                     '待整理', '02_工作分工與會議紀錄',     owner, ''],
    ['表單回覆或名冊',     data['是否需要收家長或教師回覆'] || '不確定', '待整理', '03_表單與回覆資料',         owner, ''],
    ['經費明細與憑證',     data['是否有經費'] || '不確定',              '待整理', '04_經費與採購核銷',         owner, '需會計或主任人工確認'],
    ['活動照片與照片說明', data['是否需要活動照片'] || '不確定',        '待整理', '05_活動照片與照片說明',     owner, ''],
    ['成果報告',           data['是否需要成果報告'] || '不確定',        '待整理', '06_成果資料與成果報告',     owner, ''],
    ['公告通知與對外文字', '建議',                                     '待整理', '07_公告通知與對外文字',     owner, '正式公告需人工確認'],
    ['成果簡報或展示資料', '視需要',                                   '待整理', '08_簡報與成果展示',         owner, ''],
    ['檢討與下次改進',     '建議',                                     '待整理', '09_檢討與下次改進',         owner, ''],
  ];
}

// ──────────────────────────────────────────────────────────────────────────
// 十一、Calendar 初始提醒（活動日 / 成果期限 / 經費期限）
// ──────────────────────────────────────────────────────────────────────────

function wireInitialReminders(data, projectFolder, taskSheet, checklistSheet) {
  const cal = CalendarApp.getCalendarById(SETTINGS.calendarId);
  if (!cal) throw new Error('找不到指定 Calendar，請確認 calendarId 設定。');

  const ctx = {
    folderUrl: projectFolder.getUrl(),
    taskUrl: taskSheet.getUrl(),
    checklistUrl: checklistSheet.getUrl(),
  };

  const prefix = `${data['專案年度']}_${data['承辦處室']}_${data['專案名稱']}`;
  const desc = buildInitialEventDescription(data, ctx);

  // 活動日
  tryCreateAllDay(cal, `【活動日】${prefix}`, data['活動日期'], desc);

  // 成果期限 + 前 7 天提醒
  if (data['成果繳交期限']) {
    tryCreateAllDay(cal, `【成果期限】${prefix}`, data['成果繳交期限'], desc);
    tryCreateAllDay(cal, `【成果前7天提醒】${data['專案名稱']}`, shiftDate(data['成果繳交期限'], -7), desc);
  }

  // 經費期限 + 前 7 天提醒
  if (data['經費核銷期限']) {
    tryCreateAllDay(cal, `【經費核銷期限】${prefix}`, data['經費核銷期限'], desc);
    tryCreateAllDay(cal, `【經費前7天提醒】${data['專案名稱']}`, shiftDate(data['經費核銷期限'], -7), desc);
  }
}

function tryCreateAllDay(cal, title, dateValue, description) {
  const d = toDate(dateValue);
  if (!d) return null;
  return cal.createAllDayEvent(title, d, { description });
}

function buildInitialEventDescription(data, ctx) {
  return [
    `專案名稱：${data['專案名稱'] || ''}`,
    `承辦處室：${data['承辦處室'] || ''}`,
    `承辦人：${data['承辦人'] || ''}`,
    '',
    '請確認以下資料：',
    '1. 公文與附件',
    '2. 待辦追蹤表',
    '3. 成果檢核表',
    '4. 經費與憑證',
    '5. 活動照片與照片說明',
    '',
    `Drive 專案資料夾：${ctx.folderUrl}`,
    `待辦追蹤表：${ctx.taskUrl}`,
    `成果檢核表：${ctx.checklistUrl}`,
    '',
    '⚠ 正式公告、經費核銷、成果送出仍需人工確認。',
  ].join('\n');
}

// ──────────────────────────────────────────────────────────────────────────
// 十二、寫入總控表 & 寄通知信
// ──────────────────────────────────────────────────────────────────────────

function recordProjectToControl(p) {
  const ss = SpreadsheetApp.openById(resolveControlSheetId());
  const sh = ensureControlSheet(ss);
  const headers = readHeaderRow(sh);
  const row = {
    '專案編號':           p.projectCode,
    '專案名稱':           p.data['專案名稱'] || '',
    '年度':               p.data['專案年度'] || '',
    '承辦處室':           p.data['承辦處室'] || '',
    '承辦人':             p.data['承辦人'] || '',
    '承辦人Email':        p.data['承辦人Email'] || '',
    'Drive資料夾連結':    p.projectFolder.getUrl(),
    '專案紀錄Docs連結':   p.projectDoc.getUrl(),
    '待辦追蹤表連結':     p.taskSheet.getUrl(),
    '成果檢核表連結':     p.checklistSheet.getUrl(),
    'NotebookLM筆記本連結': '',
    '專案狀態':           '籌備中',
    '備註':               p.data['備註'] || '',
    '來文單位':           p.data['來文單位'] || '',
    '公文文號':           p.data['公文文號'] || '',
    '建立日期':           formatNow(),
    '活動日期':           p.data['活動日期'] || '',
    '成果期限':           p.data['成果繳交期限'] || '',
    '經費期限':           p.data['經費核銷期限'] || '',
    '是否有經費':         p.data['是否有經費'] || '',
  };
  appendRowByHeader(sh, headers, row);
  styleHeaderRow(sh, headers.length);
}

function notifyOwnerOfProject(p) {
  const to = p.data['承辦人Email'];
  if (!to) return;

  const subject = `【行政專案已建立】${p.data['專案名稱']}`;
  const lines = [
    `${p.data['承辦人'] || ''} 老師您好：`,
    '',
    '系統已建立行政專案工作資料夾。',
    '',
    `專案編號：${p.projectCode}`,
    `專案名稱：${p.data['專案名稱'] || ''}`,
    `承辦處室：${p.data['承辦處室'] || ''}`,
    `成果繳交期限：${p.data['成果繳交期限'] || '未填'}`,
    `經費核銷期限：${p.data['經費核銷期限'] || '未填'}`,
    '',
    'Drive 專案資料夾：',
    p.projectFolder.getUrl(),
    '',
    '專案紀錄 Docs：',
    p.projectDoc.getUrl(),
    '',
    '待辦追蹤表：',
    p.taskSheet.getUrl(),
    '',
    '成果檢核表：',
    p.checklistSheet.getUrl(),
    '',
    '建議下一步：',
    '1. 把公文與附件上傳到「00_原始公文與附件」資料夾。',
    '2. 若案件重要，建立 NotebookLM 筆記本並把連結貼回總控表。',
    '3. 用 Gemini 協助整理公文要求、待辦與成果草稿。',
    '4. 正式公告、經費核銷、成果送出前仍需人工確認。',
    '',
    '— 行政專案半自動工作流系統',
  ];
  GmailApp.sendEmail(to, subject, lines.join('\n'));
}

// ──────────────────────────────────────────────────────────────────────────
// 十三、階段日期主流程（onMilestoneSubmit）
// ──────────────────────────────────────────────────────────────────────────

function onMilestoneSubmit(e) {
  const data = extractFormData(e);
  data._notes = [];
  data['新增時間'] = formatNow();
  data['建立者Email'] = resolveSubmitterEmail(data);

  let ledgerRow = null;

  try {
    requireFields(data, ['專案編號', '專案名稱', '日期類型', '日期', '負責人', '負責人Email']);
    ledgerRow = appendLedger(data, [], '', '處理中', '');

    const project = lookupProject(data['專案編號']);
    if (!project) return handleMilestoneError(ledgerRow, data, `找不到專案編號：${data['專案編號']}`);

    data['專案名稱'] = project.projectName || data['專案名稱'];
    const milestoneDate = toDate(data['日期']);
    if (!milestoneDate) return handleMilestoneError(ledgerRow, data, `日期無法解析：${data['日期']}`);
    data._milestoneDate = milestoneDate;

    let taskSheetUrl = '';
    if (isYes(data['是否寫入待辦追蹤表'])) {
      try {
        taskSheetUrl = appendMilestoneToTaskSheet(project, data);
        if (!taskSheetUrl) data._notes.push('未寫入待辦追蹤表：找不到待辦追蹤表連結');
      } catch (err) {
        data._notes.push(`寫入待辦追蹤表失敗：${err.message}`);
      }
    } else {
      data._notes.push('表單選擇不寫入待辦追蹤表');
    }

    let eventIds = [];
    if (isYes(data['是否建立Calendar提醒'])) {
      try {
        eventIds = wireMilestoneReminders(project, data);
      } catch (err) {
        data._notes.push(`Calendar 建立失敗：${err.message}`);
      }
    } else {
      data._notes.push('表單選擇不建立 Calendar 提醒');
    }

    const note = [data['備註'] || '', data._notes.join('；')].filter(Boolean).join('；');
    updateLedger(ledgerRow, eventIds, taskSheetUrl, '有效', note);

    notifyOwnerOfMilestone(project, data, eventIds);

  } catch (err) {
    if (ledgerRow) updateLedger(ledgerRow, [], '', '錯誤', [data['備註'] || '', err.message].filter(Boolean).join('；'));
    notifyAdminOfMilestoneError(data, err.message);
  }
}

function handleMilestoneError(rowIndex, data, message) {
  Logger.log(message);
  if (rowIndex) updateLedger(rowIndex, [], '', '錯誤', [data['備註'] || '', message].filter(Boolean).join('；'));
  notifyAdminOfMilestoneError(data, message);
}

function appendLedger(data, eventIds, taskSheetUrl, status, note) {
  const ss = SpreadsheetApp.openById(resolveControlSheetId());
  const sh = ensureLedgerSheet(ss);
  const recordId = `M-${Utilities.formatDate(new Date(), SETTINGS.timezone, 'yyyyMMdd-HHmmss')}`;
  sh.appendRow([
    recordId,
    data['新增時間'] || formatNow(),
    data['建立者Email'] || '',
    data['專案編號'] || '',
    data['專案名稱'] || '',
    data['日期類型'] || '',
    data['日期'] || '',
    data['提醒設定'] || '',
    data['負責人'] || '',
    data['負責人Email'] || '',
    data['是否寫入待辦追蹤表'] || '是',
    data['是否建立Calendar提醒'] || '是',
    data['說明'] || '',
    (eventIds || []).join(', '),
    taskSheetUrl || '',
    status || '有效',
    note || data['備註'] || '',
  ]);
  styleHeaderRow(sh, LEDGER_HEADERS.length);
  return sh.getLastRow();
}

function updateLedger(rowIndex, eventIds, taskSheetUrl, status, note) {
  if (!rowIndex) return;
  const ss = SpreadsheetApp.openById(resolveControlSheetId());
  const sh = ensureLedgerSheet(ss);
  sh.getRange(rowIndex, 14).setValue((eventIds || []).join(', '));
  sh.getRange(rowIndex, 15).setValue(taskSheetUrl || '');
  sh.getRange(rowIndex, 16).setValue(status || '有效');
  sh.getRange(rowIndex, 17).setValue(note || '');
}

function lookupProject(projectCode) {
  const ss = SpreadsheetApp.openById(resolveControlSheetId());
  const sh = ss.getSheetByName(NAMES.controlSheet);
  if (!sh || sh.getLastRow() < 2) return null;

  const values = sh.getDataRange().getValues();
  const headers = values[0];
  const map = headerIndex(headers);
  if (map['專案編號'] === undefined) throw new Error('總控表缺少欄位：專案編號');

  const target = String(projectCode || '').trim();
  for (let i = 1; i < values.length; i++) {
    if (String(values[i][map['專案編號']] || '').trim() !== target) continue;
    return {
      rowIndex: i + 1,
      projectCode: target,
      projectName: pick(values[i], map, '專案名稱'),
      folderUrl: pick(values[i], map, 'Drive資料夾連結'),
      projectDocUrl: pick(values[i], map, '專案紀錄Docs連結'),
      taskSheetUrl: pick(values[i], map, '待辦追蹤表連結'),
      checklistSheetUrl: pick(values[i], map, '成果檢核表連結'),
      owner: pick(values[i], map, '承辦人'),
      ownerEmail: pick(values[i], map, '承辦人Email'),
      status: pick(values[i], map, '專案狀態'),
    };
  }
  return null;
}

function appendMilestoneToTaskSheet(project, data) {
  if (!project.taskSheetUrl) return '';
  const id = parseSpreadsheetId(project.taskSheetUrl);
  if (!id) {
    data._notes.push('未寫入待辦追蹤表：無法解析試算表 ID');
    return '';
  }

  const ss = SpreadsheetApp.openById(id);
  const sh = ss.getSheetByName('待辦追蹤') || ss.getSheets()[0];
  const reminders = parseReminders(data['提醒設定']);
  const remindDate = earliestReminderDate(data._milestoneDate, reminders);
  const taskId = `M${Utilities.formatDate(new Date(), SETTINGS.timezone, 'MMddHHmmss')}`;
  const dateText = formatDate(data._milestoneDate);
  const remindText = remindDate ? formatDate(remindDate) : dateText;
  const dateType = data['日期類型'] || '其他';
  const taskName = `【${dateType}】${project.projectName || data['專案名稱'] || ''}`;
  const description = [
    `階段日期：${dateText}`,
    `提醒設定：${data['提醒設定'] || '當天提醒'}`,
    `說明：${data['說明'] || ''}`,
  ].join('\n');

  sh.appendRow([
    taskId, stageFromDateType(dateType), taskName, description,
    data['負責人'] || '', '', dateText, remindText,
    '未開始', '否', '', data['備註'] || '',
  ]);
  styleHeaderRow(sh, TASK_HEADERS.length);
  return ss.getUrl();
}

function wireMilestoneReminders(project, data) {
  const eventIds = [];
  const cal = CalendarApp.getCalendarById(SETTINGS.calendarId);
  if (!cal) { data._notes.push('Calendar 建立失敗：找不到指定日曆'); return eventIds; }

  const reminders = parseReminders(data['提醒設定']);
  const options = reminders.length ? reminders : [{ label: '當天提醒', days: 0 }];
  const desc = buildMilestoneEventDescription(project, data);

  options.forEach(opt => {
    try {
      const d = shiftDate(data._milestoneDate, opt.days);
      if (!d) { data._notes.push(`Calendar 建立失敗：${opt.label} 日期無法解析`); return; }
      const title = `【${opt.label}｜${data['日期類型'] || '階段日期'}】${project.projectName || data['專案名稱'] || ''}`;
      const ev = cal.createAllDayEvent(title, d, { description: desc });
      eventIds.push(ev.getId());
    } catch (err) {
      data._notes.push(`Calendar 建立失敗：${opt.label}：${err.message}`);
    }
  });
  return eventIds;
}

function buildMilestoneEventDescription(project, data) {
  return [
    `專案編號：${project.projectCode || data['專案編號'] || ''}`,
    `專案名稱：${project.projectName || data['專案名稱'] || ''}`,
    `日期類型：${data['日期類型'] || ''}`,
    `日期：${formatDate(data._milestoneDate || data['日期'])}`,
    `負責人：${data['負責人'] || ''}`,
    `負責人Email：${data['負責人Email'] || ''}`,
    `說明：${data['說明'] || ''}`,
    '',
    `Drive 專案資料夾：${project.folderUrl || ''}`,
    `待辦追蹤表：${project.taskSheetUrl || ''}`,
    '',
    '⚠ 正式公告、經費核銷、成果送出仍需人工確認。',
  ].join('\n');
}

function stageFromDateType(type) {
  const t = String(type || '').trim();
  if (['報名開始日', '報名截止日', '資料回收期限'].includes(t)) return '表單收件';
  if (['採購期限', '經費核銷期限'].includes(t)) return '經費';
  if (['正式活動日期', '活動前檢查日', '校內協調會', '第一次會議'].includes(t)) return '執行';
  if (['照片與成果資料回收日', '成果報告初稿期限', '成果送出期限'].includes(t)) return '成果';
  if (t === '結案檢討日') return '結案';
  return '其他';
}

function parseReminders(value) {
  const text = String(value || '').trim();
  if (!text) return [];
  const map = { '當天提醒': 0, '前1天提醒': -1, '前3天提醒': -3, '前7天提醒': -7, '前14天提醒': -14 };
  return text.split(/[,，\n]/).map(s => s.trim()).filter(s => s && map[s] !== undefined)
    .map(s => ({ label: s, days: map[s] }));
}

function earliestReminderDate(dateValue, reminders) {
  if (!reminders || !reminders.length) return toDate(dateValue);
  let best = null;
  reminders.forEach(opt => {
    const d = shiftDate(dateValue, opt.days);
    if (d && (!best || d.getTime() < best.getTime())) best = d;
  });
  return best || toDate(dateValue);
}

function notifyOwnerOfMilestone(project, data, eventIds) {
  const to = data['負責人Email'];
  if (!to) return;
  const subject = `【專案階段日期已新增】${project.projectName || data['專案名稱'] || ''}`;
  const lines = [
    `${data['負責人'] || ''} 老師您好：`,
    '',
    '已新增專案階段日期。',
    '',
    `專案編號：${project.projectCode || data['專案編號'] || ''}`,
    `專案名稱：${project.projectName || data['專案名稱'] || ''}`,
    `日期類型：${data['日期類型'] || ''}`,
    `日期：${formatDate(data._milestoneDate || data['日期'])}`,
    `提醒設定：${data['提醒設定'] || '未設定'}`,
    `Calendar Event ID：${(eventIds || []).join(', ') || '未建立'}`,
    '',
    'Drive 專案資料夾：',
    project.folderUrl || '',
    '',
    '待辦追蹤表：',
    project.taskSheetUrl || '',
    '',
    '說明：',
    data['說明'] || '',
    '',
    '⚠ 正式公告、經費核銷、成果送出仍需人工確認。',
  ];
  GmailApp.sendEmail(to, subject, lines.join('\n'));
}

function notifyAdminOfMilestoneError(data, message) {
  const to = data['負責人Email'] || data['建立者Email'] || SETTINGS.adminEmail;
  if (!to) return;
  GmailApp.sendEmail(to,
    `【專案階段日期新增失敗】${data['專案名稱'] || ''}`,
    [
      '專案階段日期新增失敗。',
      '',
      `專案編號：${data['專案編號'] || ''}`,
      `專案名稱：${data['專案名稱'] || ''}`,
      `日期類型：${data['日期類型'] || ''}`,
      `錯誤訊息：${message}`,
      '',
      '請確認專案編號、日期與總控表資料。',
    ].join('\n'));
}

function notifyAdminOfError(err) {
  console.error(`行政專案啟動器錯誤：${err.message}`);
  if (SETTINGS.adminEmail) {
    GmailApp.sendEmail(SETTINGS.adminEmail, '【行政專案啟動器錯誤】',
      `錯誤訊息：\n${err.message}\n\n請檢查 Apps Script 執行紀錄。`);
  }
}

// ──────────────────────────────────────────────────────────────────────────
// 十四、輔助函式（資料夾 / 試算表 / 日期 / 字串）
// ──────────────────────────────────────────────────────────────────────────

function ensureSubFolder(parent, name) {
  const it = parent.getFoldersByName(name);
  return it.hasNext() ? it.next() : parent.createFolder(name);
}

function relocateFile(fileId, targetFolder) {
  const file = DriveApp.getFileById(fileId);
  targetFolder.addFile(file);
  DriveApp.getRootFolder().removeFile(file);
}

function resolveControlSheetId() {
  const id = SETTINGS.controlSheetId || PROPS.getProperty(PROP_KEYS.controlSheet);
  if (!id) throw new Error('尚未建立行政專案總控表。請先執行 installFlow()。');
  return id;
}

function ensureSheetWithHeaders(ss, name, headers) {
  let sh = ss.getSheetByName(name) || ss.insertSheet(name);
  if (sh.getLastRow() === 0) {
    sh.appendRow(headers);
  } else {
    const current = readHeaderRow(sh);
    const missing = headers.filter(h => !current.includes(h));
    if (missing.length) sh.getRange(1, current.length + 1, 1, missing.length).setValues([missing]);
  }
  styleHeaderRow(sh, sh.getLastColumn());
  return sh;
}

function readHeaderRow(sh) {
  if (sh.getLastColumn() === 0) return [];
  return sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0].map(h => String(h || '').trim());
}

function headerIndex(headers) {
  const m = {};
  headers.forEach((h, i) => { const k = String(h || '').trim(); if (k) m[k] = i; });
  return m;
}

function pick(row, map, header) {
  return map[header] === undefined ? '' : row[map[header]];
}

function appendRowByHeader(sh, headers, rowMap) {
  sh.appendRow(headers.map(h => rowMap[h] !== undefined ? rowMap[h] : ''));
}

function styleHeaderRow(sh, columnCount) {
  const r = sh.getRange(1, 1, 1, columnCount);
  r.setFontWeight('bold').setBackground('#eaf2ff');
  sh.setFrozenRows(1);
  sh.autoResizeColumns(1, columnCount);
}

function applyDataValidation(range, list) {
  range.setDataValidation(SpreadsheetApp.newDataValidation().requireValueInList(list, true).build());
}

function extractFormData(e) {
  if (!e || !e.namedValues) throw new Error('沒有取得表單回應資料，請確認觸發器設定。');
  const out = {};
  Object.keys(e.namedValues).forEach(k => {
    const v = e.namedValues[k];
    out[k] = Array.isArray(v) ? v.join(', ').trim() : String(v || '').trim();
  });
  return out;
}

function requireFields(data, fields) {
  fields.forEach(f => { if (!data[f]) throw new Error(`缺少必填欄位：${f}`); });
}

function buildProjectCode(data) {
  const y = data['專案年度'] || '000';
  const o = data['承辦處室'] || '未分類';
  const ts = Utilities.formatDate(new Date(), SETTINGS.timezone, 'MMddHHmmss');
  return `${y}-${o}-${ts}`;
}

function resolveSubmitterEmail(data) {
  if (data['電子郵件地址'] || data['Email Address'] || data['建立者Email']) {
    return data['電子郵件地址'] || data['Email Address'] || data['建立者Email'];
  }
  try {
    const e = Session.getActiveUser().getEmail();
    if (e) return e;
  } catch (_) {}
  return data['負責人Email'] || '';
}

function isYes(value) {
  const t = String(value || '').trim();
  return t === '' || t === '是' || t.toLowerCase() === 'yes' || t.toLowerCase() === 'true';
}

function toDate(value) {
  if (!value) return null;
  if (Object.prototype.toString.call(value) === '[object Date]') return new Date(value.getTime());
  const d = new Date(String(value).trim().replace(/-/g, '/'));
  return isNaN(d.getTime()) ? null : d;
}

function shiftDate(value, days) {
  const d = toDate(value);
  if (!d) return null;
  d.setDate(d.getDate() + Number(days || 0));
  return d;
}

function formatDate(value) {
  const d = toDate(value);
  return d ? Utilities.formatDate(d, SETTINGS.timezone, 'yyyy/MM/dd') : String(value || '');
}

function formatNow() {
  return Utilities.formatDate(new Date(), SETTINGS.timezone, 'yyyy/MM/dd HH:mm');
}

function parseSpreadsheetId(url) {
  const t = String(url || '').trim();
  if (!t) return '';
  const patterns = [/\/d\/([a-zA-Z0-9_-]+)/, /[?&]id=([a-zA-Z0-9_-]+)/, /^([a-zA-Z0-9_-]{20,})$/];
  for (const p of patterns) {
    const m = t.match(p);
    if (m && m[1]) return m[1];
  }
  return '';
}

function toSafeFileName(name) {
  return String(name || '').replace(/[\\/:*?"<>|#%{}~&]/g, '_').replace(/\s+/g, '_').substring(0, 180);
}

// ──────────────────────────────────────────────────────────────────────────
// 十五、自我檢測函式（在 Apps Script 編輯器手動執行）
// ──────────────────────────────────────────────────────────────────────────

function checkDriveAccess() {
  const f = DriveApp.getFolderById(SETTINGS.rootFolderId);
  Logger.log(`✅ Drive：${f.getName()}`);
}

function checkControlSheet() {
  const ss = SpreadsheetApp.openById(resolveControlSheetId());
  Logger.log(`✅ 總控表：${ss.getName()}`);
}

function checkCalendar() {
  const cal = CalendarApp.getCalendarById(SETTINGS.calendarId);
  Logger.log(cal ? `✅ 日曆：${cal.getName()}` : '❌ 找不到日曆');
}

/** 一次跑完三項自我檢測 */
function runSelfCheck() {
  Logger.log('── 開始自我檢測 ──');
  try { checkDriveAccess(); } catch (e) { Logger.log(`❌ Drive 檢測失敗：${e.message}`); }
  try { checkControlSheet(); } catch (e) { Logger.log(`❌ 總控表檢測失敗：${e.message}`); }
  try { checkCalendar(); } catch (e) { Logger.log(`❌ 日曆檢測失敗：${e.message}`); }
  Logger.log('── 自我檢測結束 ──');
}

// ──────────────────────────────────────────────────────────────────────────
// 十六、便利查詢函式（在 Apps Script 編輯器手動執行）
// ──────────────────────────────────────────────────────────────────────────

/** 列出總控表中所有專案的簡要資訊 */
function listAllProjects() {
  const ss = SpreadsheetApp.openById(resolveControlSheetId());
  const sh = ss.getSheetByName(NAMES.controlSheet);
  if (!sh || sh.getLastRow() < 2) { Logger.log('（尚無專案）'); return; }
  const values = sh.getDataRange().getValues();
  const map = headerIndex(values[0]);
  for (let i = 1; i < values.length; i++) {
    Logger.log(`${pick(values[i], map, '專案編號')} | ${pick(values[i], map, '專案名稱')} | 狀態：${pick(values[i], map, '專案狀態')}`);
  }
}

/** 查詢單一專案狀態 */
function getProjectStatus(projectCode) {
  const p = lookupProject(projectCode);
  if (!p) { Logger.log(`❌ 找不到專案：${projectCode}`); return null; }
  Logger.log(`✅ ${p.projectCode} | ${p.projectName} | 狀態：${p.status}`);
  Logger.log(`資料夾：${p.folderUrl}`);
  Logger.log(`待辦表：${p.taskSheetUrl}`);
  return p;
}

/** 標記專案為結案（修改總控表的狀態欄位） */
function archiveProject(projectCode) {
  const ss = SpreadsheetApp.openById(resolveControlSheetId());
  const sh = ss.getSheetByName(NAMES.controlSheet);
  const values = sh.getDataRange().getValues();
  const map = headerIndex(values[0]);
  const codeCol = map['專案編號'];
  const statusCol = map['專案狀態'];
  if (codeCol === undefined || statusCol === undefined) throw new Error('總控表缺少必要欄位');
  for (let i = 1; i < values.length; i++) {
    if (String(values[i][codeCol] || '').trim() === String(projectCode || '').trim()) {
      sh.getRange(i + 1, statusCol + 1).setValue('已結案');
      Logger.log(`✅ ${projectCode} 已標記為結案`);
      return;
    }
  }
  Logger.log(`❌ 找不到專案：${projectCode}`);
}
