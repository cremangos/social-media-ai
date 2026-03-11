"""
Platform publisher — posts approved content to Instagram and Twitter.

Instagram: Meta Graph API (requires Business account linked to Facebook Page)
Twitter:   Tweepy v2

Facebook and LinkedIn posting omitted from auto-publish (use the Sheets output
to schedule via Buffer/Hootsuite, or add your own API credentials).
"""
import os
import requests
import tweepy


# ---------------------------------------------------------------------------
# Instagram (Meta Graph API)
# ---------------------------------------------------------------------------
IG_ACCESS_TOKEN  = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
IG_BUSINESS_ID   = os.getenv("INSTAGRAM_BUSINESS_ID", "")


def post_to_instagram(caption: str, image_url: str) -> bool:
    """
    Posts a photo to Instagram Business via Meta Graph API.
    image_url must be a publicly accessible URL (not a DALL-E temporary URL).
    """
    if not IG_ACCESS_TOKEN or not IG_BUSINESS_ID:
        print("  ⚠️  Instagram credentials not set — skipping publish.")
        return False

    base = f"https://graph.facebook.com/v19.0/{IG_BUSINESS_ID}"

    # Step 1: Create media container
    create_resp = requests.post(
        f"{base}/media",
        params={
            "image_url": image_url,
            "caption": caption,
            "access_token": IG_ACCESS_TOKEN,
        },
        timeout=30,
    )
    create_resp.raise_for_status()
    creation_id = create_resp.json().get("id")
    if not creation_id:
        print(f"  ✗ Instagram container creation failed: {create_resp.text}")
        return False

    # Step 2: Publish the container
    publish_resp = requests.post(
        f"{base}/media_publish",
        params={
            "creation_id": creation_id,
            "access_token": IG_ACCESS_TOKEN,
        },
        timeout=30,
    )
    publish_resp.raise_for_status()
    print(f"  ✓ Instagram post published! ID: {publish_resp.json().get('id')}")
    return True


# ---------------------------------------------------------------------------
# Twitter / X (Tweepy)
# ---------------------------------------------------------------------------
def get_twitter_client():
    return tweepy.Client(
        consumer_key=os.getenv("TWITTER_API_KEY"),
        consumer_secret=os.getenv("TWITTER_API_SECRET"),
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.getenv("TWITTER_ACCESS_SECRET"),
    )


def post_to_twitter(text: str) -> bool:
    if not os.getenv("TWITTER_API_KEY"):
        print("  ⚠️  Twitter credentials not set — skipping publish.")
        return False
    try:
        client = get_twitter_client()
        resp = client.create_tweet(text=text[:280])
        print(f"  ✓ Tweet posted! ID: {resp.data['id']}")
        return True
    except Exception as e:
        print(f"  ✗ Twitter post failed: {e}")
        return False


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------
def publish_approved_posts(approved_posts: dict, image_url: str) -> dict:
    """
    Publishes all approved posts to their platforms.
    Returns dict of results per platform.
    """
    results = {}

    if "instagram" in approved_posts:
        results["instagram"] = post_to_instagram(
            approved_posts["instagram"], image_url
        )

    if "twitter" in approved_posts:
        results["twitter"] = post_to_twitter(approved_posts["twitter"])

    # Facebook and LinkedIn returned as text only (log to Sheets for manual posting)
    for platform in ("facebook", "linkedin"):
        if platform in approved_posts:
            print(f"  ℹ️  {platform.capitalize()} post logged to Sheets (manual post recommended)")
            results[platform] = "logged"

    return results
