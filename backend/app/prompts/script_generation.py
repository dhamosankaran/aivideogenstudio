"""
Script generation prompt templates.

Contains prompts for converting articles into viral 20-30 second
YouTube Shorts scripts.
"""

SCRIPT_GENERATION_PROMPT = """You are a viral YouTube Shorts scriptwriter. Your videos get millions of views.

ARTICLE:
---
Title: {title}
Why Interesting: {why_interesting}
Key Points: {key_points}
Category: {category}
---

VIRAL SHORTS FORMAT (20-30 seconds):

[HOOK]
- Shocking statement or surprising fact
- MAX 10 words. Punchy.
- Make them STOP scrolling

[CONTENT]  
- 2-3 rapid-fire points
- Each point = 1 short sentence (5-8 words)
- Use numbers, stats, or bold claims
- No filler, no "basically", no "um"

[CTA]
- End with question or cliffhanger
- "What do you think?"
- "Follow for more"
- MAX 10 words

STYLE:
- Every sentence under 8 words
- Active voice only
- Present tense
- TTS-friendly (no URLs, symbols)
- Energy level: HIGH

LENGTH: 50-80 words total = 20-30 seconds spoken

OUTPUT: Script only. No explanations. Ready for TTS.

Write it:
"""


SCRIPT_GENERATION_CASUAL = """You are writing a conversational YouTube Shorts script about AI news.

Imagine you're texting a friend about this cool thing you just learned.

ARTICLE:
{title}
{why_interesting}

Write a 45-60 second script that feels like you're chatting:
- Start with "So you know how..." or "Okay so..."
- Use "literally", "basically", "honestly" naturally
- Ask rhetorical questions
- Be excited but not fake

Follow the [HOOK], [CONTEXT], [MAIN POINTS], [WRAP-UP], [CTA] structure.

Keep it real. 180-250 words.
"""


SCRIPT_GENERATION_FORMAL = """You are a news anchor presenting breaking AI news for YouTube Shorts.

ARTICLE:
Title: {title}
Summary: {why_interesting}
Key Facts: {key_points}

Write a professional 60-120 second news-style script:
- Start with "Breaking news in artificial intelligence..."
- Use data and specific examples
- Quote sources when relevant
- Maintain journalistic tone

Follow the [HOOK], [CONTEXT], [MAIN POINTS], [WRAP-UP], [CTA] structure.

Professional but accessible. 250-350 words.
"""


def build_script_generation_prompt(
    title: str,
    why_interesting: str,
    key_points: list,
    category: str,
    style: str = "engaging"
) -> str:
    """
    Build script generation prompt based on article and style.
    
    Args:
        title: Article title
        why_interesting: One-sentence pitch
        key_points: List of key points
        category: Article category
        style: Script style (engaging, casual, formal)
        
    Returns:
        Complete prompt for LLM
    """
    # Format key points
    if isinstance(key_points, list):
        points_str = "\n".join(f"- {point}" for point in key_points)
    else:
        points_str = str(key_points)
    
    # Select template based on style
    if style == "casual":
        template = SCRIPT_GENERATION_CASUAL
    elif style == "formal":
        template = SCRIPT_GENERATION_FORMAL
    else:
        template = SCRIPT_GENERATION_PROMPT
    
    return template.format(
        title=title,
        why_interesting=why_interesting or "Interesting AI development",
        key_points=points_str,
        category=category or "technology"
    )
