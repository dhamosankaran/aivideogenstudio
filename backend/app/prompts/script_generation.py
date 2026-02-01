"""
Script generation prompt templates.

Contains prompts for converting articles into engaging 60-120 second
YouTube Shorts scripts.
"""

SCRIPT_GENERATION_PROMPT = """You are a professional YouTube Shorts scriptwriter specializing in AI and tech news.

Your goal: Convert this article into an engaging 60-120 second video script.

ARTICLE INFORMATION:
---
Title: {title}
Why Interesting: {why_interesting}
Key Points: {key_points}
Category: {category}
---

SCRIPT STRUCTURE:
Write a script following this exact 5-part structure with section markers:

[HOOK]
- Start with a shocking statement, question, or surprising fact
- Grab attention in the first 3 seconds
- Make viewers want to keep watching

[CONTEXT]
- Briefly explain what happened or what this is about
- Set the stage without boring details
- Keep it to 2-3 sentences max

[MAIN POINTS]
- Present 3-5 specific takeaways
- Use concrete examples, numbers, or comparisons
- Make each point visual (add [visual cue] in brackets)
- This is the meat of the video - be specific!

[WRAP-UP]
- Synthesize why this matters
- Connect to viewer's life or future implications
- Make it memorable

[CTA]
- Quick call-to-action
- Encourage engagement (comment, like, subscribe)
- Keep it natural, not pushy

STYLE REQUIREMENTS:
- Conversational tone (like talking to a friend over coffee)
- Short sentences (10-15 words max per sentence)
- No jargon without explanation
- TTS-friendly: no URLs, no special symbols, proper punctuation
- Active voice, present tense where possible
- Energetic and engaging throughout

LENGTH TARGET:
- 180-250 words total
- This equals 45-60 seconds when spoken
- Each section should be roughly:
  * HOOK: 15-20 words
  * CONTEXT: 30-40 words
  * MAIN POINTS: 90-120 words
  * WRAP-UP: 30-40 words
  * CTA: 10-15 words

VISUAL CUES:
Add helpful visual suggestions in [brackets] like:
- [Show GPT-4 logo]
- [Display graph of growth]
- [Cut to code example]
- [Show before/after comparison]

OUTPUT FORMAT:
Return ONLY the script with section markers. No meta-commentary, no explanations.
Just the script ready for voice-over.

Now write the script:
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
