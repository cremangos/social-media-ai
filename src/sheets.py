"""
Google Sheets client — reads the 'Article' trigger sheet and logs
generated posts back to the platform-specific sheets.
"""
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

SHEET_ID = os.getenv("GOOGLE_SHEETS_ID", "")

# Tab names matching the n8n workflow
TAB_ARTICLE    = "Article"
TAB_INSTAGRAM  = "Instagram posts"
TAB_FACEBOOK   = "Facebook posts"
TAB_LINKEDIN   = "Linkedin posts"
TAB_TWITTER    = "X/Twitter posts"


def get_service():
    creds = None
    token_file = "token.pickle"

    if os.path.exists(token_file):
        with open(token_file, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json"), SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(token_file, "wb") as f:
            pickle.dump(creds, f)

    return build("sheets", "v4", credentials=creds)


def get_pending_articles(service, since_row: int = 2):
    """Read all rows from Article tab. Returns list of dicts."""
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=SHEET_ID, range=f"{TAB_ARTICLE}!A:D")
        .execute()
    )
    rows = result.get("values", [])
    if len(rows) <= 1:
        return []

    headers = rows[0]
    articles = []
    for i, row in enumerate(rows[since_row - 1 :], start=since_row):
        # Pad short rows
        row += [""] * (len(headers) - len(row))
        articles.append({"row": i, **dict(zip(headers, row))})
    return articles


def log_posts(service, platform_posts: dict, image_url: str):
    """
    platform_posts: {'instagram': '...', 'facebook': '...', ...}
    """
    tabs = {
        "instagram": TAB_INSTAGRAM,
        "facebook":  TAB_FACEBOOK,
        "linkedin":  TAB_LINKEDIN,
        "twitter":   TAB_TWITTER,
    }
    for platform, tab in tabs.items():
        text = platform_posts.get(platform, "")
        if not text:
            continue
        service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range=f"{tab}!A:B",
            valueInputOption="RAW",
            body={"values": [[text, image_url]]},
        ).execute()
        print(f"  ✓ Logged {platform} post to Sheets")
