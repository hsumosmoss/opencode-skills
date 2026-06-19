"""
模式 C：純 API 旁路 — 替既有專案新增階段日期

用法：
    python add_milestone.py \\
        --project-folder-url "<已知專案資料夾連結>" \\
        --date-type "報名截止日" \\
        --date "2026-06-15" \\
        --reminders "前7天提醒,前3天提醒,當天提醒" \\
        --owner "王老師" \\
        --owner-email "wang@school.edu.tw" \\
        --calendar-id primary
"""

import argparse
import json
import re
from datetime import datetime, timedelta, timezone

from googleapiclient.discovery import build

from auth import get_credentials

TZ = timezone(timedelta(hours=8))

REMINDER_MAP = {
    "當天提醒": 0,
    "前1天提醒": -1,
    "前3天提醒": -3,
    "前7天提醒": -7,
    "前14天提醒": -14,
}

STAGE_MAP = {
    "報名開始日": "表單收件", "報名截止日": "表單收件", "資料回收期限": "表單收件",
    "採購期限": "經費", "經費核銷期限": "經費",
    "校內協調會": "執行", "第一次會議": "執行", "活動前檢查日": "執行", "正式活動日期": "執行",
    "照片與成果資料回收日": "成果", "成果報告初稿期限": "成果", "成果送出期限": "成果",
    "結案檢討日": "結案",
}


def parse_date(s: str) -> datetime:
    return datetime.strptime(s.replace("-", "/"), "%Y/%m/%d")


def extract_sheet_id(url: str) -> str:
    m = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    return m.group(1) if m else ""


def add_milestone(project_folder_url, date_type, date_str, reminders, owner, owner_email, calendar_id="primary", project_name=None, description=""):
    creds = get_credentials()
    sheets = build("sheets", "v4", credentials=creds)
    cal_svc = build("calendar", "v3", credentials=creds)
    drive = build("drive", "v3", credentials=creds)

    folder_id = extract_sheet_id(project_folder_url) or project_folder_url

    # 找該專案的「99_系統產生文件/_待辦追蹤表」
    sys_folder = drive.files().list(
        q=f"'{folder_id}' in parents and name='99_系統產生文件' and trashed=false",
        fields="files(id)",
    ).execute().get("files", [])

    if not sys_folder:
        raise FileNotFoundError("找不到 99_系統產生文件 資料夾")

    task_files = drive.files().list(
        q=f"'{sys_folder[0]['id']}' in parents and name contains '_待辦追蹤表' and trashed=false",
        fields="files(id,name,webViewLink)",
    ).execute().get("files", [])

    if not task_files:
        raise FileNotFoundError("找不到待辦追蹤表")

    task_sheet_id = task_files[0]["id"]
    task_sheet_url = task_files[0]["webViewLink"]

    milestone_date = parse_date(date_str)
    reminder_list = [r.strip() for r in (reminders or "").split(",") if r.strip() in REMINDER_MAP]
    if not reminder_list:
        reminder_list = ["當天提醒"]

    earliest_days = min(REMINDER_MAP[r] for r in reminder_list)
    remind_date = milestone_date + timedelta(days=earliest_days)

    # 寫入待辦表
    task_id = "M" + datetime.now(TZ).strftime("%m%d%H%M%S")
    stage = STAGE_MAP.get(date_type, "其他")
    task_name = f"【{date_type}】{project_name or ''}"
    desc_lines = [
        f"階段日期：{milestone_date.strftime('%Y/%m/%d')}",
        f"提醒設定：{','.join(reminder_list)}",
        f"說明：{description}",
    ]
    row = [
        task_id, stage, task_name, "\n".join(desc_lines),
        owner, "",
        milestone_date.strftime("%Y/%m/%d"),
        remind_date.strftime("%Y/%m/%d"),
        "未開始", "否", "", "",
    ]
    sheets.spreadsheets().values().append(
        spreadsheetId=task_sheet_id,
        range="待辦追蹤!A:L",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [row]},
    ).execute()

    # 建多個 Calendar 事件
    event_ids = []
    for label in reminder_list:
        days = REMINDER_MAP[label]
        ev_date = milestone_date + timedelta(days=days)
        title = f"【{label}｜{date_type}】{project_name or ''}"
        ev = cal_svc.events().insert(
            calendarId=calendar_id,
            body={
                "summary": title,
                "description": f"{description}\n\n專案：{project_name or ''}\n負責人：{owner}\n負責人 Email：{owner_email}",
                "start": {"date": ev_date.strftime("%Y-%m-%d")},
                "end": {"date": (ev_date + timedelta(days=1)).strftime("%Y-%m-%d")},
            },
        ).execute()
        event_ids.append(ev.get("id"))

    return {
        "taskId": task_id,
        "taskSheetUrl": task_sheet_url,
        "calendarEventIds": event_ids,
        "milestoneDate": milestone_date.strftime("%Y/%m/%d"),
        "stage": stage,
    }


def main():
    p = argparse.ArgumentParser(description="新增階段日期到既有專案（純 API 模式）")
    p.add_argument("--project-folder-url", required=True, help="專案資料夾連結或 ID")
    p.add_argument("--date-type", required=True)
    p.add_argument("--date", required=True, help="格式 YYYY-MM-DD")
    p.add_argument("--reminders", help="逗號分隔，例：前7天提醒,前3天提醒,當天提醒")
    p.add_argument("--owner", required=True)
    p.add_argument("--owner-email", required=True)
    p.add_argument("--project-name")
    p.add_argument("--description", default="")
    p.add_argument("--calendar-id", default="primary")
    args = p.parse_args()

    result = add_milestone(
        project_folder_url=args.project_folder_url,
        date_type=args.date_type,
        date_str=args.date,
        reminders=args.reminders,
        owner=args.owner,
        owner_email=args.owner_email,
        calendar_id=args.calendar_id,
        project_name=args.project_name,
        description=args.description,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
