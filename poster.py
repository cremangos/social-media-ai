"""
poster.py — Thin platform publisher. No AI. No external LLMs.

The AI agent (Antigravity) does all content generation.
This script only handles the mechanical API calls to post content.

Usage:
  python poster.py instagram --caption "text" --image path/to/image.png
  python poster.py twitter   --text "tweet text"
  python poster.py sheets    --platform instagram --caption "text" --image-url "url"
  python poster.py all       --data '{"instagram": "...", "twitter": "...", "image": "path"}'
"""
import os
import sys
import json
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------------------------------
# Instagram — Meta Graph API
# --------------------------------------------------------------------------
IG_TOKEN    = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
IG_BIZ_ID   = os.getenv("INSTAGRAM_BUSINESS_ID", "")

def upload_image_to_imgbb(image_path: str) -> str:
    """
    Upload a local image to imgbb (free, no account needed) to get a public URL.
    Instagram Graph API requires a publicly accessible image URL.
    """
    api_key = os.getenv("IMGBB_API_KEY", "")
    if not api_key:
        raise ValueError("IMGBB_API_KEY not set. Get a free key at imgbb.com/api")
    with open(image_path, "rb") as f:
        resp = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": api_key},
            files={"image": f},
            timeout=30,
        )
    resp.raise_for_status()
    return resp.json()["data"]["url"]


def post_instagram(caption: str, image_path: str) -> dict:
    if not IG_TOKEN or not IG_BIZ_ID:
        return {"error": "INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_BUSINESS_ID not set in .env"}

    # Upload image to get public URL (DALL-E URLs expire; local files need hosting)
    print("  📤 Uploading image to get public URL...")
    image_url = upload_image_to_imgbb(image_path)
    print(f"  ✓ Public URL: {image_url}")

    base = f"https://graph.facebook.com/v19.0/{IG_BIZ_ID}"

    # Step 1: Create media container
    r = requests.post(f"{base}/media", params={
        "image_url": image_url, "caption": caption, "access_token": IG_TOKEN
    }, timeout=30)
    r.raise_for_status()
    creation_id = r.json().get("id")

    # Step 2: Publish
    r2 = requests.post(f"{base}/media_publish", params={
        "creation_id": creation_id, "access_token": IG_TOKEN
    }, timeout=30)
    r2.raise_for_status()
    post_id = r2.json().get("id")
    print(f"  ✅ Instagram posted! ID: {post_id}")
    return {"platform": "instagram", "post_id": post_id, "image_url": image_url}


# --------------------------------------------------------------------------
# Twitter / X — Tweepy v2
# --------------------------------------------------------------------------
def post_twitter(text: str) -> dict:
    try:
        import tweepy
    except ImportError:
        return {"error": "tweepy not installed. Run: pip install tweepy"}

    keys = [
        os.getenv("TWITTER_API_KEY"),
        os.getenv("TWITTER_API_SECRET"),
        os.getenv("TWITTER_ACCESS_TOKEN"),
        os.getenv("TWITTER_ACCESS_SECRET"),
    ]
    if not all(keys):
        return {"error": "Twitter credentials not set in .env"}

    client = tweepy.Client(
        consumer_key=keys[0], consumer_secret=keys[1],
        access_token=keys[2], access_token_secret=keys[3],
    )
    resp = client.create_tweet(text=text[:280])
    tweet_id = resp.data["id"]
    print(f"  ✅ Tweet posted! ID: {tweet_id}")
    return {"platform": "twitter", "tweet_id": tweet_id}


# --------------------------------------------------------------------------
# Google Sheets — log posts
# --------------------------------------------------------------------------
def log_to_sheets(entries: list[dict]) -> dict:
    """
    entries: [{"platform": "instagram", "caption": "...", "image_url": "...", "post_id": "..."}, ...]
    """
    try:
        import pickle
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        SHEET_ID = os.getenv("GOOGLE_SHEETS_ID", "")

        creds = None
        if Path("token.pickle").exists():
            with open("token.pickle", "rb") as f:
                creds = pickle.load(f)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json"), SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open("token.pickle", "wb") as f:
                pickle.dump(creds, f)

        service = build("sheets", "v4", credentials=creds)
        tab_map = {
            "instagram": "Instagram posts",
            "facebook": "Facebook posts",
            "linkedin": "Linkedin posts",
            "twitter": "X/Twitter posts",
        }
        for entry in entries:
            tab = tab_map.get(entry.get("platform", ""), "Instagram posts")
            service.spreadsheets().values().append(
                spreadsheetId=SHEET_ID,
                range=f"{tab}!A:C",
                valueInputOption="RAW",
                body={"values": [[
                    entry.get("caption", entry.get("text", "")),
                    entry.get("image_url", ""),
                    entry.get("post_id", "pending"),
                ]]},
            ).execute()
            print(f"  ✓ Logged {entry.get('platform')} to Sheets")
        return {"logged": len(entries)}
    except Exception as e:
        return {"error": str(e)}


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Social media publisher — thin poster, no AI")
    sub = parser.add_subparsers(dest="platform")

    # instagram
    ig = sub.add_parser("instagram")
    ig.add_argument("--caption", required=True)
    ig.add_argument("--image", required=True, help="Local image path")

    # twitter
    tw = sub.add_parser("twitter")
    tw.add_argument("--text", required=True)

    # sheets log
    sh = sub.add_parser("sheets")
    sh.add_argument("--platform", required=True)
    sh.add_argument("--caption", default="")
    sh.add_argument("--text", default="")
    sh.add_argument("--image-url", default="")
    sh.add_argument("--post-id", default="")

    # post all from JSON
    al = sub.add_parser("all")
    al.add_argument("--data", required=True, help="JSON string with platform posts")

    args = parser.parse_args()

    if args.platform == "instagram":
        result = post_instagram(args.caption, args.image)
        print(json.dumps(result, indent=2))

    elif args.platform == "twitter":
        result = post_twitter(args.text)
        print(json.dumps(result, indent=2))

    elif args.platform == "sheets":
        result = log_to_sheets([{
            "platform": args.platform,
            "caption": args.caption or args.text,
            "image_url": args.image_url,
            "post_id": args.post_id,
        }])
        print(json.dumps(result, indent=2))

    elif args.platform == "all":
        data = json.loads(args.data)
        results = []
        if "instagram" in data:
            results.append(post_instagram(data["instagram"], data.get("image", "")))
        if "twitter" in data:
            results.append(post_twitter(data["twitter"]))
        if results:
            log_to_sheets(results)
        print(json.dumps(results, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
