"""
Social Media AI — main runner
Port of the n8n 'Social media ai system' workflow

Usage:
  python main.py                    # Process pending rows, CLI approval
  python main.py --auto-approve     # Skip approval, log to Sheets only
  python main.py --publish          # Auto-approve + publish to platforms
  python main.py --url <url>        # Run on a single article URL
  python main.py --schedule         # Run on a schedule (every 5 minutes, like n8n poll)
"""
import os
import sys
import time
import argparse
from dotenv import load_dotenv

load_dotenv()

# Import after .env is loaded
from src.sheets import get_service, get_pending_articles, log_posts
from src.pipeline import summarize_article, create_image_prompt, generate_image, write_platform_posts
from src.approval import send_approval_email, cli_approval_prompt
from src.publisher import publish_approved_posts


def process_article(article: dict, auto_approve: bool = False, publish: bool = False) -> None:
    url = article.get("News link", article.get("URL", ""))
    topic = article.get("Topic", article.get("Title", ""))

    if not url:
        print(f"  ⚠️  No URL found in row {article.get('row')} — skipping.")
        return

    print(f"\n{'='*60}")
    print(f"🚀 Processing: {topic or url}")
    print(f"{'='*60}")

    # Step 1 — Summarize article
    summary = summarize_article(url)
    print(f"  📋 Summary: {summary[:120]}...")

    # Step 2 — Create image prompt
    image_prompt = create_image_prompt(summary, topic)

    # Step 3 — Generate image
    image_url = generate_image(image_prompt)

    # Step 4 — Write platform posts (Claude 3.7 Sonnet)
    posts = write_platform_posts(url, summary)

    # Step 5 — Approval
    if auto_approve or publish:
        approved_posts = posts
        print("  ✅ Auto-approved all posts")
    else:
        # Send email preview
        send_approval_email(posts, image_url, topic or url)
        # CLI approval
        approved_posts = cli_approval_prompt(posts)

    if not approved_posts:
        print("  ✗ No posts approved — skipping.")
        return

    # Step 6 — Log to Google Sheets
    try:
        service = get_service()
        log_posts(service, approved_posts, image_url)
    except Exception as e:
        print(f"  ⚠️  Sheets logging failed: {e}")

    # Step 7 — Publish to platforms
    if publish:
        results = publish_approved_posts(approved_posts, image_url)
        print(f"\n  📊 Publish results: {results}")
    else:
        print(f"\n  ℹ️  Posts logged to Sheets. Run with --publish to push live.")

    print(f"\n  ✅ Completed: {topic or url}")


def run_from_sheets(auto_approve: bool, publish: bool) -> None:
    """Poll Google Sheets for new rows (mirrors n8n GoogleSheetsTrigger)."""
    print("📊 Checking Google Sheets for pending articles...")
    try:
        service = get_service()
        articles = get_pending_articles(service)
    except Exception as e:
        print(f"❌ Failed to read Sheets: {e}")
        return

    if not articles:
        print("  No pending articles found.")
        return

    print(f"  Found {len(articles)} article(s) to process.")
    for article in articles:
        try:
            process_article(article, auto_approve=auto_approve, publish=publish)
        except Exception as e:
            print(f"  ✗ Error processing {article}: {e}")


def run_single_url(url: str, topic: str = "", auto_approve: bool = False, publish: bool = False) -> None:
    """Run the pipeline on a single article URL without needing Sheets."""
    article = {"News link": url, "Topic": topic, "row": 0}
    process_article(article, auto_approve=auto_approve, publish=publish)


def main():
    parser = argparse.ArgumentParser(description="Social Media AI — Python port of n8n workflow")
    parser.add_argument("--url", help="Process a single article URL")
    parser.add_argument("--topic", default="", help="Topic/title hint for the article")
    parser.add_argument("--auto-approve", action="store_true", help="Skip manual approval")
    parser.add_argument("--publish", action="store_true", help="Auto-approve + publish to platforms")
    parser.add_argument("--schedule", action="store_true", help="Poll Sheets every 5 minutes")
    args = parser.parse_args()

    if args.url:
        run_single_url(args.url, topic=args.topic, auto_approve=args.auto_approve, publish=args.publish)
    elif args.schedule:
        print("🕐 Scheduler started — polling Google Sheets every 5 minutes (Ctrl+C to stop)")
        while True:
            run_from_sheets(auto_approve=args.auto_approve, publish=args.publish)
            print("\n  💤 Sleeping 5 minutes...\n")
            time.sleep(300)
    else:
        run_from_sheets(auto_approve=args.auto_approve, publish=args.publish)


if __name__ == "__main__":
    main()
