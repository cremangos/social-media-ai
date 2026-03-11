# Social Media AI

Python port of the `Social_media_ai_system` n8n workflow.

## Pipeline (mirrors n8n exactly)

```
Article URL (Google Sheets or --url)
   ↓
Perplexity sonar-pro        → summarize article
   ↓
GPT-4o-mini                 → write DALL-E image prompt
   ↓
DALL-E 3 (1024×1024)        → generate image
   ↓
Claude 3.7 Sonnet ×4        → write Instagram / Facebook / LinkedIn / Twitter posts
   ↓
Gmail preview email + CLI   → human approval
   ↓
Google Sheets               → log posts + image URL
   ↓ (optional --publish)
Meta Graph API              → post to Instagram
Tweepy                      → post to Twitter/X
```

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure credentials
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Google OAuth (Sheets access)
- Go to [Google Cloud Console](https://console.cloud.google.com)
- Create a project → Enable **Google Sheets API**
- Create OAuth 2.0 credentials → Download as `credentials.json`
- Place `credentials.json` in this folder
- First run will open browser for auth

### 4. Instagram (optional)
- Convert `@musicgearspecialist` to a **Business/Creator** account
- Link to a Facebook Page
- Create a Meta Developer app
- Get a **Page Access Token** with `instagram_basic` + `instagram_content_publish` permissions
- Set `INSTAGRAM_ACCESS_TOKEN` and `INSTAGRAM_BUSINESS_ID` in `.env`

### 5. Gmail App Password (optional)
- Enable 2FA on your Google account
- Go to [App Passwords](https://myaccount.google.com/apppasswords)
- Create a password → set `GMAIL_APP_PASSWORD` in `.env`

## Usage

### Process a single article URL
```bash
python main.py --url "https://www.musicgearspecialist.com/blog/fender-vs-gibson" \
               --topic "Fender vs Gibson"
```

### Process all pending rows from Google Sheets
```bash
python main.py
```

### Auto-approve + log to Sheets (no manual review)
```bash
python main.py --auto-approve
```

### Auto-approve + publish live to Instagram & Twitter
```bash
python main.py --publish
```

### Run as a scheduler (polls Sheets every 5 minutes, like n8n)
```bash
python main.py --schedule
```

## Google Sheets Format

Your **Article** tab needs these columns:
| Column | Example |
|--------|---------|
| `News link` | `https://musicgearspecialist.com/guides/guitar-tone-guide` |
| `Topic` | `Guitar Tone Guide` |

Generated posts are saved to:
- `Instagram posts` tab
- `Facebook posts` tab  
- `Linkedin posts` tab
- `X/Twitter posts` tab
