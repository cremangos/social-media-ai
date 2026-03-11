---
name: social-post
description: >
  Generate and publish AI-powered social media posts for any niche site.
  Given an article URL and topic, uses Perplexity to summarize, DALL-E 3 to
  generate an image, and Claude 3.7 Sonnet to write platform-specific posts
  for Instagram, Facebook, LinkedIn, and Twitter/X. Logs everything to Google
  Sheets and optionally publishes live via Meta Graph API and Tweepy.
  
  Use when user says "post to Instagram", "create social posts", "social media
  post for this article", "promote this on Instagram", "schedule a post".
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
---

# Social Post — AI Social Media Generator

Generates platform-optimized social posts from any article URL using the
pipeline in `main.py`. Port of the n8n `Social_media_ai_system` workflow.

## Pipeline (what happens under the hood)

```
Article URL  →  Perplexity sonar-pro (summarize)
             →  GPT-4o-mini (DALL-E image prompt)
             →  DALL-E 3 1024×1024 (generate image)
             →  Claude 3.7 Sonnet × 4 (write posts)
             →  Gmail preview + CLI approval
             →  Google Sheets (log posts + image URL)
             →  Instagram Graph API + Tweepy (optional publish)
```

## Skill Directory

```
social-media-ai/
├── main.py              ← Entry point (run this)
├── src/
│   ├── pipeline.py      ← Perplexity → GPT-4o-mini → DALL-E → Claude
│   ├── sheets.py        ← Google Sheets read/write
│   ├── approval.py      ← Gmail preview + CLI approval
│   └── publisher.py     ← Instagram Graph API + Tweepy
├── .env                 ← API keys (copy from .env.example)
└── requirements.txt
```

## Workflow

### Step 1 — Collect inputs
Ask the user for:
- **Article URL** (required) — the published page to promote
- **Topic/headline** (optional) — brief hint, e.g. "Guitar Tone Guide"
- **Mode** — review (CLI approval) / auto-approve / publish live

### Step 2 — Check prerequisites
Verify the following before running:
```bash
# Check .env exists with required keys
ls /home/corsa/antigravity_projects/social-media-ai/.env

# Check required keys are set
grep -E "OPENAI_API_KEY|ANTHROPIC_API_KEY|PERPLEXITY_API_KEY" \
  /home/corsa/antigravity_projects/social-media-ai/.env | grep -v "^#"
```

If `.env` is missing or keys are blank, tell the user which keys are needed:
- `OPENAI_API_KEY` — DALL-E + GPT-4o-mini
- `ANTHROPIC_API_KEY` — Claude 3.7 Sonnet  
- `PERPLEXITY_API_KEY` — article summarization

Optional (for live publishing):
- `INSTAGRAM_ACCESS_TOKEN` + `INSTAGRAM_BUSINESS_ID` — Meta Graph API
- `TWITTER_API_KEY/SECRET` + `TWITTER_ACCESS_TOKEN/SECRET` — Tweepy
- `APPROVAL_EMAIL` + `GMAIL_APP_PASSWORD` — email previews
- `GOOGLE_SHEETS_ID` + `GOOGLE_CREDENTIALS_FILE` — Sheets logging

### Step 3 — Install dependencies (if needed)
```bash
cd /home/corsa/antigravity_projects/social-media-ai
pip install -r requirements.txt -q
```

### Step 4 — Run the pipeline

**Single article with CLI approval (default):**
```bash
cd /home/corsa/antigravity_projects/social-media-ai
python main.py --url "<ARTICLE_URL>" --topic "<TOPIC>"
```

**Auto-approve, log to Sheets only (no publishing):**
```bash
python main.py --url "<ARTICLE_URL>" --topic "<TOPIC>" --auto-approve
```

**Auto-approve + publish live to Instagram & Twitter:**
```bash
python main.py --url "<ARTICLE_URL>" --topic "<TOPIC>" --publish
```

**Process all pending rows from Google Sheets:**
```bash
python main.py --auto-approve
```

### Step 5 — Report results
After the run, tell the user:
- ✅ Which platforms had posts generated
- 🖼️ The DALL-E image URL
- 📊 Whether posts were logged to Sheets
- 📱 Whether posts were published live (and the post IDs)
- ❌ Any errors and how to fix them

## Common Issues

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `AuthenticationError` | Check API keys in `.env` |
| Instagram 400 error | Image URL must be publicly accessible (DALL-E URLs expire — host the image first) |
| Sheets auth popup | First run only — browser will open for OAuth consent |
| Twitter rate limit | Free tier allows ~17 posts/day |

## Instagram Publishing Notes

DALL-E URLs are temporary (expire in ~1 hour). For Instagram publishing:
1. Download the image from the DALL-E URL
2. Upload it to a public URL (Cloudflare R2, S3, or the site's `/public` folder)
3. Pass the permanent URL to the Instagram Graph API

The skill handles step 4's publish call — but the user must host the image first
or create a permanent URL. Add a note in the output if publishing to Instagram.

## Example Usage

```
User: "Can you create Instagram posts for my guitar tone guide article?"

→ You: "Sure! I'll run the social media AI pipeline on that article.
        Give me the URL and I'll generate an Instagram post, image, and
        log everything to Sheets."

→ Run: python main.py --url "https://musicgearspecialist.com/guides/guitar-tone-guide" \
                      --topic "Guitar Tone Guide"
```
