"""
模式 C：純 API 旁路 — 建立新行政專案

用法：
    python create_project.py \\
        --year 115 \\
        --office 教務處 \\
        --name "AI 融入教學研習" \\
        --owner "王老師" \\
        --owner-email "wang@school.edu.tw" \\
        --root-folder-id "1AbCd..."

可選參數：
    --event-date 2026-07-01
    --result-deadline 2026-08-15
    --budget-deadline 2026-09-30
    --calendar-id primary
    --admin-email admin@school.edu.tw
    --control-sheet-id <existing-id>
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from auth import get_credentials

TZ = timezone(timedelta(hours=8))  # Asia/Taipei

PROJECT_SUBFOLDERS = [
    "00_原始公文與附件",
    "01_計畫書與核定資料",
    "02_工作分工與會議紀錄",
    "03_表單與回覆資料",
    "04_經費與採購核銷",
    "05_活動照片與照片說明",
    "06_成果資料與成果報告",
    "07_公告通知與對外文字",
    "08_簡報與成果展示",
    "09_檢討與下次改進",
    "99_系統產生文件",
]


def safe_name(name: str) -> str:
    bad = '\\/:*?"<>|#%{}~&'
    for c in bad:
        name = name.replace(c, "_")
    return "_".join(name.split())[:180]


def now_str() -> str:
    return datetime.now(TZ).strftime("%Y/%m/%d %H:%M")


def project_code(year: str, office: str) -> str:
    ts = datetime.now(TZ).strftime("%m%d%H%M%S")
    return f"{year}-{office}-{ts}"


def ensure_folder(drive, parent_id: str, name: str) -> str:
    """資料夾不存在就建，回傳 ID"""
    q = f"'{parent_id}' in parents and name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    result = drive.files().list(q=q, fields="files(id)").execute()
    if result.get("files"):
        return result["files"][0]["id"]
    folder = drive.files().create(
        body={"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]},
        fields="id",
    ).execute()
    return folder["id"]


def create_project_folders(drive, projects_root_id: str, folder_name: str) -> dict:
    """建專案資料夾 + 11 子資料夾"""
    project_id = drive.files().create(
        body={"name": folder_name, "mimeType": "application/vnd.google-apps.folder", "parents": [projects_root_id]},
        fields="id, webViewLink",
    ).execute()

    subs = {}
    for sub_name in PROJECT_SUBFOLDERS:
        sub = drive.files().create(
            body={"name": sub_name, "mimeType": "application/vnd.google-apps.folder", "parents": [project_id["id"]]},
            fields="id",
        ).execute()
        subs[sub_name] = sub["id"]

    return {"id": project_id["id"], "url": project_id["webViewLink"], "subs": subs}


def create_project_doc(docs, drive, data: dict, system_folder_id: str) -> dict:
    """建專案紀錄 Docs（9 段結構）"""
    name = safe_name(f"{data['year']}_{data['office']}_{data['name']}_專案紀錄")
    doc = docs.documents().create(body={"title": name}).execute()
    doc_id = doc["documentId"]

    # 寫內容
    requests = []
    insert_at = 1

    def add_heading(text, level=1):
        nonlocal insert_at
        requests.append({"insertText": {"location": {"index": insert_at}, "text": text + "\n"}})
        requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": insert_at, "endIndex": insert_at + len(text)},
                "paragraphStyle": {"namedStyleType": f"HEADING_{level}"},
                "fields": "namedStyleType",
            }
        })
        insert_at += len(text) + 1

    def add_para(text):
        nonlocal insert_at
        requests.append({"insertText": {"location": {"index": insert_at}, "text": text + "\n"}})
        insert_at += len(text) + 1

    add_heading("行政專案紀錄文件", 1)

    add_heading("一、基本資料", 2)
    for k, v in [
        ("公文主旨", data.get("subject", "")),
        ("來文單位", data.get("source", "")),
        ("公文文號", data.get("doc_no", "")),
        ("專案名稱", data["name"]),
        ("專案年度", data["year"]),
        ("承辦處室", data["office"]),
        ("承辦人", data["owner"]),
        ("承辦人Email", data["owner_email"]),
    ]:
        add_para(f"{k}：{v}")

    add_heading("二、重要期限", 2)
    for k, v in [
        ("活動日期", data.get("event_date", "")),
        ("成果繳交期限", data.get("result_deadline", "")),
        ("經費核銷期限", data.get("budget_deadline", "")),
    ]:
        add_para(f"{k}：{v}")

    for title in ["三、經費資訊", "四、公文要求摘要", "五、執行紀錄", "六、成果資料", "七、缺漏檢查", "八、檢討與下次建議", "九、NotebookLM 建議提問"]:
        add_heading(title, 2)
        add_para("")

    docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

    # 搬到 99_系統產生文件
    drive.files().update(fileId=doc_id, addParents=system_folder_id, removeParents="root", fields="id, webViewLink").execute()
    meta = drive.files().get(fileId=doc_id, fields="webViewLink").execute()

    return {"id": doc_id, "url": meta["webViewLink"], "name": name}


def create_sheet_in_folder(sheets, drive, name: str, folder_id: str, headers: list, rows: list) -> dict:
    """建 Sheet → 寫表頭與資料 → 搬到目標資料夾"""
    ss = sheets.spreadsheets().create(body={"properties": {"title": name}}).execute()
    ss_id = ss["spreadsheetId"]

    sheets.spreadsheets().values().update(
        spreadsheetId=ss_id,
        range="A1",
        valueInputOption="RAW",
        body={"values": [headers] + rows},
    ).execute()

    # 加粗表頭
    sheets.spreadsheets().batchUpdate(
        spreadsheetId=ss_id,
        body={
            "requests": [
                {
                    "repeatCell": {
                        "range": {"startRowIndex": 0, "endRowIndex": 1},
                        "cell": {"userEnteredFormat": {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.92, "green": 0.95, "blue": 1.0}}},
                        "fields": "userEnteredFormat(textFormat,backgroundColor)",
                    }
                },
                {"updateSheetProperties": {"properties": {"gridProperties": {"frozenRowCount": 1}}, "fields": "gridProperties.frozenRowCount"}},
            ]
        },
    ).execute()

    drive.files().update(fileId=ss_id, addParents=folder_id, removeParents="root").execute()
    meta = drive.files().get(fileId=ss_id, fields="webViewLink").execute()
    return {"id": ss_id, "url": meta["webViewLink"]}


def build_default_tasks(data):
    owner = data["owner"]
    d_event = data.get("event_date", "")
    d_result = data.get("result_deadline", "")
    d_budget = data.get("budget_deadline", "")
    return [
        ["T001", "公文", "整理公文要求", "確認辦理依據、期限、成果要求與附件", owner, "", "", "", "未開始", "否", "", ""],
        ["T002", "公文", "建立 NotebookLM 筆記本", "把公文與附件加入專案 Notebook", owner, "", "", "", "未開始", "否", "", ""],
        ["T003", "籌備", "撰寫或修正計畫書", "依公文要求完成校內計畫草案", owner, "", "", "", "未開始", "是", "", ""],
        ["T004", "籌備", "建立報名或回覆表單", "確認是否需收回覆", owner, "", "", "", "未開始", "否", "", ""],
        ["T005", "執行", "收集活動照片", "活動期間收集照片", owner, "", d_event, d_event, "未開始", "是", "", ""],
        ["T006", "執行", "整理簽到表或參與名冊", "建立人數統計", owner, "", d_event, d_event, "未開始", "是", "", ""],
        ["T007", "經費", "整理經費明細與憑證", "確認支出項目", owner, "會計", d_budget, d_budget, "未開始", "是", "", ""],
        ["T008", "成果", "撰寫成果報告草稿", "用 NotebookLM 與 Gemini 協助", owner, "", d_result, d_result, "未開始", "是", "", ""],
        ["T009", "成果", "檢查成果附件是否齊全", "確認照片、簽到、回饋", owner, "", d_result, d_result, "未開始", "是", "", ""],
        ["T010", "結案", "建立下次改進建議", "整理檢討與交接", owner, "", "", "", "未開始", "否", "", ""],
    ]


def build_default_checklist(data):
    owner = data["owner"]
    return [
        ["原始公文", "是", "待整理", "00_原始公文與附件", owner, ""],
        ["計畫書或核定資料", "建議", "待整理", "01_計畫書與核定資料", owner, ""],
        ["會議紀錄或工作分工", "建議", "待整理", "02_工作分工與會議紀錄", owner, ""],
        ["表單回覆或名冊", "不確定", "待整理", "03_表單與回覆資料", owner, ""],
        ["經費明細與憑證", "不確定", "待整理", "04_經費與採購核銷", owner, "需會計或主任人工確認"],
        ["活動照片與照片說明", "不確定", "待整理", "05_活動照片與照片說明", owner, ""],
        ["成果報告", "不確定", "待整理", "06_成果資料與成果報告", owner, ""],
        ["公告通知與對外文字", "建議", "待整理", "07_公告通知與對外文字", owner, "正式公告需人工確認"],
        ["成果簡報或展示資料", "視需要", "待整理", "08_簡報與成果展示", owner, ""],
        ["檢討與下次改進", "建議", "待整理", "09_檢討與下次改進", owner, ""],
    ]


def create_calendar_event(cal_svc, calendar_id, title, date_str, description):
    if not date_str:
        return None
    try:
        d = datetime.strptime(date_str.replace("-", "/"), "%Y/%m/%d")
    except ValueError:
        return None
    end = d + timedelta(days=1)
    body = {
        "summary": title,
        "description": description,
        "start": {"date": d.strftime("%Y-%m-%d")},
        "end": {"date": end.strftime("%Y-%m-%d")},
    }
    ev = cal_svc.events().insert(calendarId=calendar_id, body=body).execute()
    return ev.get("id")


def create(year, office, name, owner, owner_email, root_folder_id, event_date=None, result_deadline=None, budget_deadline=None, calendar_id="primary", subject=None, source=None, doc_no=None):
    """主入口：建立完整行政專案"""

    creds = get_credentials()
    drive = build("drive", "v3", credentials=creds)
    docs = build("docs", "v1", credentials=creds)
    sheets = build("sheets", "v4", credentials=creds)
    cal_svc = build("calendar", "v3", credentials=creds)

    data = {
        "year": year, "office": office, "name": name,
        "owner": owner, "owner_email": owner_email,
        "subject": subject or "", "source": source or "", "doc_no": doc_no or "",
        "event_date": event_date or "", "result_deadline": result_deadline or "", "budget_deadline": budget_deadline or "",
    }

    code = project_code(year, office)
    folder_name = safe_name(f"{year}_{office}_{name}")

    print(f"📁 建立專案資料夾：{folder_name}")
    projects_root_id = ensure_folder(drive, root_folder_id, "03_專案資料夾")
    project = create_project_folders(drive, projects_root_id, folder_name)
    system_folder = project["subs"]["99_系統產生文件"]

    print("📄 建立專案紀錄 Docs...")
    doc = create_project_doc(docs, drive, data, system_folder)

    print("📊 建立待辦追蹤表...")
    task_headers = ["任務編號", "階段", "任務名稱", "任務說明", "負責人", "協助單位", "期限", "提醒日期", "狀態", "需要附件", "附件位置", "備註"]
    task_sheet = create_sheet_in_folder(sheets, drive, safe_name(f"{year}_{office}_{name}_待辦追蹤表"), system_folder, task_headers, build_default_tasks(data))

    print("📋 建立成果檢核表...")
    checklist_headers = ["項目", "是否需要", "目前狀態", "存放位置", "負責人", "備註"]
    checklist_sheet = create_sheet_in_folder(sheets, drive, safe_name(f"{year}_{office}_{name}_成果檢核表"), system_folder, checklist_headers, build_default_checklist(data))

    print("📅 建立 Calendar 提醒...")
    desc = f"專案名稱：{name}\n承辦處室：{office}\n承辦人：{owner}\n\nDrive：{project['url']}\n待辦表：{task_sheet['url']}\n成果檢核：{checklist_sheet['url']}"
    event_ids = []
    if event_date:
        event_ids.append(create_calendar_event(cal_svc, calendar_id, f"【活動日】{year}_{office}_{name}", event_date, desc))
    if result_deadline:
        event_ids.append(create_calendar_event(cal_svc, calendar_id, f"【成果期限】{year}_{office}_{name}", result_deadline, desc))
    if budget_deadline:
        event_ids.append(create_calendar_event(cal_svc, calendar_id, f"【經費核銷期限】{year}_{office}_{name}", budget_deadline, desc))

    return {
        "projectCode": code,
        "projectFolderUrl": project["url"],
        "projectDocUrl": doc["url"],
        "taskSheetUrl": task_sheet["url"],
        "checklistSheetUrl": checklist_sheet["url"],
        "calendarEventIds": [eid for eid in event_ids if eid],
    }


def main():
    p = argparse.ArgumentParser(description="建立行政專案（純 API 模式）")
    p.add_argument("--year", required=True)
    p.add_argument("--office", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--owner", required=True)
    p.add_argument("--owner-email", required=True)
    p.add_argument("--root-folder-id", required=True)
    p.add_argument("--event-date")
    p.add_argument("--result-deadline")
    p.add_argument("--budget-deadline")
    p.add_argument("--calendar-id", default="primary")
    p.add_argument("--subject")
    p.add_argument("--source")
    p.add_argument("--doc-no")
    args = p.parse_args()

    result = create(
        year=args.year, office=args.office, name=args.name,
        owner=args.owner, owner_email=args.owner_email,
        root_folder_id=args.root_folder_id,
        event_date=args.event_date, result_deadline=args.result_deadline, budget_deadline=args.budget_deadline,
        calendar_id=args.calendar_id, subject=args.subject, source=args.source, doc_no=args.doc_no,
    )
    print("")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
