---
name: social-post
description: >
  Create and publish AI-powered social media posts for any article or topic.
  The AI agent reads the article, writes platform-specific posts (Instagram,
  Facebook, LinkedIn, Twitter/X), generates a matching image, shows a preview
  for approval, then uses a thin Python poster to publish via platform APIs.
  No external AI APIs needed — the agent does all content generation natively.

  Use when user says "post to Instagram", "create social posts", "social post
  for this article", "promote this on social media", "schedule a post".
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - WebFetch
  - WebSearch
  - Task
---

# Social Post Skill

You (the AI agent) do ALL the content creation. The Python scripts only handle
the mechanical platform API calls to actually publish.

## Architecture

```
YOU (agent)
  1. Read article via read_url_content / browser
  2. Write 4 platform posts (Instagram, FB, LinkedIn, Twitter)
  3. Generate image via generate_image tool
  4. Show preview → user approves
  5. Run: python poster.py --platform instagram --caption "..." --image path/to/img.png
```

## Workflow

### Step 1 — Gather inputs
Ask the user for:
- **Article URL** or **topic** to post about
- **Which platforms** (default: all — Instagram, Facebook, LinkedIn, Twitter)
- **Tone** — educational, promotional, conversational (default: conversational)
- **Niche/brand** — infer from context if working in a project (e.g. musicgearspecialist)

### Step 2 — Read and understand the article
Use `read_url_content` to fetch the article. If behind a login or JS-heavy,
use `browser_subagent`.

Extract:
- Core topic and main takeaway
- 2-3 key facts or statistics to anchor the posts
- Any product names, prices, or recommendations to highlight

### Step 3 — Generate the image
Use the `generate_image` tool. Prompt should be:
- Photorealistic, vibrant, relevant to the topic
- Square format (1:1) — optimized for Instagram
- NO text overlays, NO logos
- Style: natural, lifestyle photography feel

Example prompt for a guitar article:
> "Close-up lifestyle photo of a vintage electric guitar in warm golden studio 
> lighting, rich amber tones, bokeh background with guitar pedals. Square format,
> professional product photography feel, no text."

Save the image path for use in Step 5.

### Step 4 — Write platform posts

Write all 4 posts in one pass. Use the article facts from Step 2.

#### Instagram (≤2,200 chars, ideal 150-220 word body)
- Hook line (first 125 chars visible before "more" — make it count)
- Body: 3-5 short punchy paragraphs, emojis used naturally (not excessively)
- Call to action: "Link in bio 🔗" or "Save this for later 📌"
- Hashtags: 10-15 niche hashtags on a new line at the end
- Format: `[hook]\n\n[body]\n\n[CTA]\n\n[hashtags]`

#### Facebook (≤500 words)
- Conversational, no formal tone
- 2-3 short paragraphs
- End with a question to drive comments
- 0-3 hashtags only (FB penalizes hashtag spam)

#### LinkedIn (≤1,300 chars ideal)
- Professional but not stiff
- Hook line → 3-4 short paragraphs with line breaks
- Insight or lesson the reader can take away
- End with 3-5 relevant hashtags

#### Twitter/X (≤280 chars)
- One punchy sentence or "take"
- 1-2 hashtags max embedded in text
- If a thread is better, write Tweet 1 + "Thread 🧵" then 3-4 follow-up tweets

### Step 5 — Show preview and get approval

Present all 4 posts + image in a clear preview:
```
🖼️ IMAGE: [embedded or path]

📸 INSTAGRAM:
[post text]

👥 FACEBOOK:
[post text]

💼 LINKEDIN:
[post text]

🐦 TWITTER/X:
[post text]
```

Ask: "Which platforms should I publish to? (or say 'edit [platform]' to revise)"

### Step 6 — Publish via Python poster

For each approved platform, run the appropriate command from the
`social-media-ai` project directory:

```bash
cd /home/corsa/antigravity_projects/social-media-ai

# Instagram
python poster.py instagram --caption "<caption>" --image "<image_path>"

# Twitter/X
python poster.py twitter --text "<tweet_text>"

# Log all to Google Sheets
python poster.py sheets --data "<json>"
```

If credentials aren't set in `.env`, tell the user which ones are needed:
- Instagram: `INSTAGRAM_ACCESS_TOKEN` + `INSTAGRAM_BUSINESS_ID`
- Twitter: `TWITTER_API_KEY/SECRET` + `TWITTER_ACCESS_TOKEN/SECRET`

### Step 7 — Confirm and report
Tell the user:
- ✅ Which platforms were published + post IDs/URLs
- 📊 Whether posts were logged to Sheets
- 💾 Image path saved locally in `social-media-ai/output/`
- 🔁 Any edits needed or errors to fix

## Tips
- For musicgearspecialist.com posts: use guitar/musician imagery, amber/warm tones
- Instagram performs best with gear close-ups, not people
- LinkedIn posts about "lessons from X gear" outperform pure promotional posts
- Twitter: hot take or contrarian opinion performs better than informational
