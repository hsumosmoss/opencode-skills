"""Google API 授權（支援 OAuth + Service Account）"""

import json
import os
from pathlib import Path

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.send",
]

ROOT = Path(__file__).parent
TOKEN_FILE = ROOT / "token.json"
OAUTH_CLIENT_FILE = ROOT / "client_secret.json"
SERVICE_ACCOUNT_FILE = ROOT / "service-account.json"


def get_credentials():
    """依優先順序取得憑證：Service Account > OAuth > 互動式登入"""

    # 1. Service Account（推薦給自動化）
    if SERVICE_ACCOUNT_FILE.exists():
        return service_account.Credentials.from_service_account_file(
            str(SERVICE_ACCOUNT_FILE), scopes=SCOPES
        )

    # 2. OAuth Token（互動式）
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not OAUTH_CLIENT_FILE.exists():
                raise FileNotFoundError(
                    f"找不到 {OAUTH_CLIENT_FILE.name}。\n"
                    "請到 https://console.cloud.google.com 建立 OAuth 2.0 Client ID（type: Desktop App）\n"
                    f"下載 JSON 後改名為 {OAUTH_CLIENT_FILE.name} 放到 {ROOT}"
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(OAUTH_CLIENT_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    return creds


if __name__ == "__main__":
    creds = get_credentials()
    print(f"✅ 已取得憑證：{type(creds).__name__}")
