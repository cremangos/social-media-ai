"""
Gmail approval module — sends platform posts for human review before publishing.
Mirrors the n8n 'Check post' gmail nodes.

Flow: send email with post content → wait for user to reply "approve" or "decline"
Since Python can't block waiting for Gmail replies, we use a simpler approach:
  - Send a preview email with all 4 posts
  - Wait for approval file OR use --auto-approve flag for CI/headless use
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


APPROVAL_EMAIL = os.getenv("APPROVAL_EMAIL", "")


def send_approval_email(posts: dict, image_url: str, article_title: str) -> bool:
    """
    Sends an HTML email preview of all generated posts.
    Returns True (always sends — actual approval logic via CLI prompt or flag).
    """
    if not APPROVAL_EMAIL:
        print("  ⚠️  No APPROVAL_EMAIL set — skipping email, auto-approving.")
        return True

    # Build HTML email body
    html = f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto;">
    <h2>📱 New Social Media Posts Ready for Approval</h2>
    <p><b>Article:</b> {article_title}</p>
    <img src="{image_url}" style="max-width: 300px; border-radius: 8px;" />

    <hr/>
    <h3>📸 Instagram</h3>
    <pre style="background:#f5f5f5;padding:12px;border-radius:6px;">{posts.get('instagram','')}</pre>

    <h3>👥 Facebook</h3>
    <pre style="background:#f5f5f5;padding:12px;border-radius:6px;">{posts.get('facebook','')}</pre>

    <h3>💼 LinkedIn</h3>
    <pre style="background:#f5f5f5;padding:12px;border-radius:6px;">{posts.get('linkedin','')}</pre>

    <h3>🐦 X / Twitter</h3>
    <pre style="background:#f5f5f5;padding:12px;border-radius:6px;">{posts.get('twitter','')}</pre>

    <hr/>
    <p><i>Posts logged to Google Sheets. Run with --publish to push live.</i></p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Social Media] New posts ready — {article_title}"
    msg["From"] = APPROVAL_EMAIL
    msg["To"] = APPROVAL_EMAIL
    msg.attach(MIMEText(html, "html"))

    # Use Gmail SMTP (requires App Password if 2FA enabled)
    smtp_password = os.getenv("GMAIL_APP_PASSWORD", "")
    if not smtp_password:
        print("  ⚠️  No GMAIL_APP_PASSWORD set — printing posts to console instead.")
        _print_posts_to_console(posts, image_url)
        return True

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(APPROVAL_EMAIL, smtp_password)
            server.send_message(msg)
        print(f"  ✓ Approval email sent to {APPROVAL_EMAIL}")
    except Exception as e:
        print(f"  ⚠️  Email failed ({e}) — printing to console.")
        _print_posts_to_console(posts, image_url)

    return True


def cli_approval_prompt(posts: dict) -> dict:
    """
    Interactive CLI approval for each platform post.
    Returns dict of approved posts only.
    """
    approved = {}
    for platform, text in posts.items():
        print(f"\n{'='*60}")
        print(f"📱 {platform.upper()} POST:")
        print(f"{'='*60}")
        print(text)
        print(f"{'='*60}")
        answer = input(f"Approve {platform} post? [y/n/e(dit)]: ").strip().lower()
        if answer == "y":
            approved[platform] = text
        elif answer == "e":
            print("Paste your edited version (press Enter twice when done):")
            lines = []
            while True:
                line = input()
                if line == "" and lines and lines[-1] == "":
                    break
                lines.append(line)
            approved[platform] = "\n".join(lines[:-1])
        else:
            print(f"  ✗ Skipping {platform}")
    return approved


def _print_posts_to_console(posts: dict, image_url: str):
    print(f"\n  🖼️  Image: {image_url}")
    for platform, text in posts.items():
        print(f"\n  [{platform.upper()}]\n{text}\n")
