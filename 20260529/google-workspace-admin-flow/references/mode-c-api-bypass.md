# 模式 C：純 API 旁路（即時，不走 Apps Script）

## 適用對象

- 開發者要把「建立行政專案」這個動作接到其他 SKILL / 工具
- 想用一句話對 Claude/Codex 說「幫我建立資訊月活動專案」直接執行
- 不想處理 Apps Script 觸發器與 Form 介面

## 與模式 A/B 的關鍵差異

| 項目 | 模式 A/B | 模式 C |
|------|---------|--------|
| 入口 | Google Form | Python CLI |
| 執行環境 | Google 伺服器（Apps Script） | 本機（Python） |
| 觸發延遲 | 表單送出後幾秒 | 即時 |
| 是否要 OAuth 同意一次 | 是 | 是（Service Account 更省事） |
| 適合場景 | 學校承辦人填表 | 主任批次建立、其他工具串接 |

## 認證方式（選一）

### 選項 1：OAuth Client（個人帳號）
- 適合：個人使用、互動式
- 設定：到 [Google Cloud Console](https://console.cloud.google.com) 建立 OAuth 2.0 Client ID

### 選項 2：Service Account（伺服器帳號）
- 適合：自動化、伺服器執行
- 設定：建立 Service Account → 下載 JSON Key → 把 Service Account 加入 Drive 資料夾協作者

## 安裝 Python 依賴

```powershell
# 從本 SKILL 目錄
cd scripts/api-bypass
pip install -r requirements.txt
```

## 建立新行政專案

```powershell
python scripts/api-bypass/create_project.py `
  --year 115 `
  --office 教務處 `
  --name "AI 融入教學研習" `
  --owner "王老師" `
  --owner-email "wang@school.edu.tw" `
  --root-folder-id "1AbCdEf..." `
  --calendar-id "primary"
```

輸出：

```json
{
  "projectCode": "115-教務處-0521143025",
  "projectFolderUrl": "https://drive.google.com/...",
  "projectDocUrl": "https://docs.google.com/document/d/...",
  "taskSheetUrl": "https://docs.google.com/spreadsheets/d/...",
  "checklistSheetUrl": "https://docs.google.com/spreadsheets/d/..."
}
```

## 新增階段日期

```powershell
python scripts/api-bypass/add_milestone.py `
  --project-code "115-教務處-0521143025" `
  --date-type "報名截止日" `
  --date "2026-06-15" `
  --reminders "前7天提醒,前3天提醒,當天提醒" `
  --owner "王老師" `
  --owner-email "wang@school.edu.tw"
```

## 整合到 Claude / Codex

當使用者說「幫我建立『資訊月活動』專案，承辦人是李老師」，Claude 可以直接呼叫：

```python
# 在 SKILL 內部使用
from create_project import create

result = create(
    year='115',
    office='資訊組',
    name='資訊月活動',
    owner='李老師',
    owner_email='lee@school.edu.tw',
    root_folder_id=os.getenv('ROOT_FOLDER_ID'),
)
print(f"專案已建立：{result['projectFolderUrl']}")
```

## 安全注意

- **不要把 Service Account JSON 提交到 Git**：加入 `.gitignore`
- **環境變數而非硬寫**：用 `os.getenv('ROOT_FOLDER_ID')`
- **最小權限原則**：Service Account 只給「特定資料夾的編輯權」，不要給全 Drive

## 與模式 A/B 並存

模式 C **不取代** 模式 A/B，三者可以同時運作：
- 老師用 Form 填（A/B 建立的 Form）
- 主任用 Python 一鍵建立（C）
- 兩條路都會寫入同一張總控表

關鍵：`SETTINGS.rootFolderId` 與 `SETTINGS.controlSheetId` 在三模式必須一致。
