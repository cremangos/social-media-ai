"""
AI pipeline — mirrors the n8n flow:
  1. Perplexity sonar-pro  → summarize article
  2. GPT-4o-mini           → create DALL-E image prompt from summary
  3. DALL-E 3              → generate 1024x1024 image
  4. Claude 3.7 Sonnet     → write platform-specific posts
"""
import os
import requests
import openai
import anthropic

openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
PERPLEXITY_KEY = os.getenv("PERPLEXITY_API_KEY", "")


# ---------------------------------------------------------------------------
# STEP 1 — Perplexity: summarize the article URL
# ---------------------------------------------------------------------------
def summarize_article(article_url: str) -> str:
    """Calls Perplexity sonar-pro to summarize the article at the given URL."""
    print(f"  📰 Summarizing: {article_url}")
    resp = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers={
            "accept": "application/json",
            "Authorization": f"Bearer {PERPLEXITY_KEY}",
        },
        json={
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "user",
                    "content": f"Summarize this article in 3-4 sentences, focusing on the key points and takeaways: {article_url}",
                }
            ],
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# STEP 2 — GPT-4o-mini: create a DALL-E image prompt
# ---------------------------------------------------------------------------
def create_image_prompt(summary: str, topic: str = "") -> str:
    """Uses GPT-4o-mini to write a photorealistic DALL-E image prompt."""
    print("  🎨 Creating image prompt...")
    resp = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a creative director specializing in social media visuals. "
                    "Create vivid, photorealistic DALL-E image prompts that are eye-catching "
                    "for Instagram. Keep prompts under 200 words. No text overlays."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Create a DALL-E 3 image prompt for a social media post about this topic.\n"
                    f"Topic: {topic}\n"
                    f"Article summary: {summary}\n\n"
                    "The image should be visually striking, relevant to the content, "
                    "and optimized for a 1:1 Instagram format."
                ),
            },
        ],
    )
    return resp.choices[0].message.content


# ---------------------------------------------------------------------------
# STEP 3 — DALL-E 3: generate the image
# ---------------------------------------------------------------------------
def generate_image(image_prompt: str) -> str:
    """Generates an image with DALL-E 3. Returns the URL."""
    print("  🖼️  Generating image with DALL-E 3...")
    resp = openai_client.images.generate(
        model="dall-e-3",
        prompt=image_prompt,
        n=1,
        size="1024x1024",
        quality="standard",
        style="natural",
    )
    url = resp.data[0].url
    print(f"  ✓ Image URL: {url[:80]}...")
    return url


# ---------------------------------------------------------------------------
# STEP 4 — Claude 3.7 Sonnet: write platform-specific posts
# ---------------------------------------------------------------------------
PLATFORM_PROMPTS = {
    "instagram": (
        "You are a social media expert specializing in Instagram. "
        "Write an engaging Instagram caption (150-220 chars ideal body text) "
        "with relevant emojis, a strong hook, and 10-15 niche hashtags at the end. "
        "Format: caption text\\n\\n#hashtags"
    ),
    "facebook": (
        "You are a social media expert specializing in Facebook. "
        "Write a conversational Facebook post (2-3 short paragraphs). "
        "Include a question to drive comments. No hashtags needed."
    ),
    "linkedin": (
        "You are a LinkedIn content strategist. "
        "Write a professional LinkedIn post (3-5 short paragraphs). "
        "Use line breaks for readability. Start with a hook. End with 3-5 relevant hashtags."
    ),
    "twitter": (
        "You are a Twitter/X content expert. "
        "Write a punchy tweet under 280 characters. "
        "Include 1-2 relevant hashtags within the character limit."
    ),
}


def write_platform_posts(article_content: str, summary: str) -> dict:
    """
    Uses Claude 3.7 Sonnet to write posts for all 4 platforms.
    Returns dict: {'instagram': '...', 'facebook': '...', 'linkedin': '...', 'twitter': '...'}
    """
    posts = {}
    for platform, system_prompt in PLATFORM_PROMPTS.items():
        print(f"  ✍️  Writing {platform} post...")
        msg = anthropic_client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Article content:\n{article_content}\n\n"
                        f"Summary:\n{summary}\n\n"
                        f"Write the {platform} post now."
                    ),
                }
            ],
        )
        posts[platform] = msg.content[0].text
    return posts
