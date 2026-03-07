"""
Prompt templates for LLM-based content generation.
"""

def build_script_generation_prompt(
    article_title: str,
    article_summary: str,
    key_points: list,
    style: str = "engaging",
    target_duration: int = 90,
    scene_based: bool = True,
    article_content: str = "",
    category: str = "",
    genre_strategy: dict = None
) -> str:
    """
    Build prompt for script generation.
    
    Args:
        article_title: Title of the article
        article_summary: Summary of the article
        key_points: List of key points from analysis
        style: Script style (engaging, casual, formal)
        target_duration: Target duration in seconds
        scene_based: Whether to generate scene-based structure
        article_content: Original article content for factual accuracy
        category: Content category (e.g. "book_review") for specialized prompts
        genre_strategy: Optional genre persona dict from GenreStrategyRegistry
        
    Returns:
        Formatted prompt string
    """
    
    # Route to specialized prompt for book reviews
    if category == "book_review":
        return _build_book_review_script_prompt(
            article_title, article_summary, key_points, target_duration, article_content,
            genre_strategy=genre_strategy
        )

    # Route to specialized prompt for viral news
    if category == "viral_news":
        return _build_viral_news_script_prompt(
            article_title, article_summary, key_points, target_duration, article_content,
            news_strategy=genre_strategy  # reuse genre_strategy param for news strategy
        )

    # Route to specialized prompt for daily AI digest (multi-story roundup)
    if category == "daily_update":
        return _build_daily_digest_script_prompt(
            article_title, article_summary, key_points, target_duration, article_content
        )
    
    if scene_based:
        return _build_scene_based_prompt(
            article_title, article_summary, key_points, style, target_duration, article_content
        )
    else:
        return _build_simple_prompt(
            article_title, article_summary, key_points, style, target_duration
        )


def _build_scene_based_prompt(
    article_title: str,
    article_summary: str,
    key_points: list,
    style: str,
    target_duration: int,
    article_content: str = ""
) -> str:
    """Build scene-based script generation prompt with emphasis on factual accuracy."""
    
    key_points_text = "\n".join(f"- {point}" for point in key_points)
    
    # Include source content if available (truncate if too long)
    source_section = ""
    if article_content:
        content_preview = article_content[:3000] if len(article_content) > 3000 else article_content
        source_section = f"""
**SOURCE ARTICLE CONTENT** (Use this as your primary reference):
{content_preview}
"""
    
    return f"""You are a viral YouTube Shorts scriptwriter. Your scripts get millions of views.

**CRITICAL RULES**:
- ONLY use facts from the source content
- If source says "launched", it IS launched - DO NOT say "rumored"
- Every sentence MUST be under 8 words
- NO filler words, NO "um", NO "so basically"

Create a PUNCHY {target_duration}-second script about:
**Title**: {article_title}

**Summary**: {article_summary}

**Key Points**:
{key_points_text}
{source_section}
**VIRAL SHORTS FORMULA**:
1. **2 scenes ONLY** (8-12 seconds each):
   - Scene 1: The HOOK + main fact
   - Scene 2: The payoff + CTA
2. **Hook patterns that work**:
   - "This changes everything."
   - "You need to know this."
   - "No one is talking about this."
   - "[Company/Product] just dropped this."
3. **Short, punchy sentences**: 5-8 words max per sentence
4. **Create urgency**: Use present tense, active voice
5. **End with a cliffhanger or question**

**IMAGE KEYWORDS** (CRITICAL - Read Carefully):
Generate 3-4 CONTEXT-SPECIFIC keywords per scene that will find relevant images on Google.
Keywords should reflect the ACTUAL content topic, not generic tech visuals.

**How to create effective keywords**:
1. Extract key entities (companies, products, people, places) from the content
2. Identify the main theme (security threat, product launch, financial news, tutorial, review)
3. Combine entity + theme + visual descriptor

**Examples by content type**:

📰 **News Articles**:
- Security/Scam: "phishing email warning", "[Company] security breach", "cybersecurity alert red"
- Product launch: "[Product] official announcement", "[Company] new product", "tech product reveal"
- Business: "[Company] headquarters", "stock market graph up", "corporate merger deal"
- Science/Health: "[Topic] research study", "medical breakthrough", "laboratory research"

📺 **YouTube Videos**:
- Tech review: "[Product] hands-on review", "[Product] unboxing", "[Product] vs comparison"
- Tutorial: "[Software] interface screenshot", "step by step guide", "how to [topic]"
- Commentary: "[Topic] explained diagram", "analysis breakdown", "[Subject] controversy"

📚 **Book/Content Reviews**:
- Book review: "[Book title] cover", "author [name] photo", "[Genre] book aesthetic"
- Movie/Show: "[Title] movie poster", "[Title] scene still", "entertainment review"

📝 **General/Pasted Content**:
- Identify the core subject and use: "[Subject] visual", "[Topic] illustration", "[Concept] diagram"
- For abstract topics, use: metaphorical imagery that represents the concept

**NEVER use**:
- Generic filler: "data visualization", "futuristic interface", "circuit board", "abstract tech"
- Unspecific people: "team photo", "business people", "happy customer"
- Vague concepts that don't relate to the specific content topic

**Output Format** (JSON):
{{
  "hook": "8 words MAX. Punchy. Creates curiosity.",
  "scenes": [
    {{
      "scene_number": 1,
      "text": "Hook + main point. Short sentences. Max 35 words total.",
      "image_keywords": ["topic_keyword_1", "topic_keyword_2", "topic_keyword_3"],
      "visual_style": "tech_modern",
      "duration_estimate": 10
    }},
    {{
      "scene_number": 2,
      "text": "Impact + CTA. End with question or cliffhanger. Max 30 words.",
      "image_keywords": ["topic_keyword_1", "topic_keyword_2", "topic_keyword_3"],
      "visual_style": "engaging",
      "duration_estimate": 10
    }}
  ],
  "call_to_action": "Short CTA - question or follow prompt",
  "title_suggestion": "Clickbait but accurate. Under 50 chars. Emoji optional."
}}

**Word count**: 50-80 words total (for {target_duration}s at 2.5 words/second)

Generate viral script JSON:"""


def _build_simple_prompt(
    article_title: str,
    article_summary: str,
    key_points: list,
    style: str,
    target_duration: int
) -> str:
    """Build simple (legacy) script generation prompt."""
    
    key_points_text = "\n".join(f"- {point}" for point in key_points)
    
    return f"""You are a professional YouTube Shorts scriptwriter specializing in AI and technology content.

Create an engaging {target_duration}-second video script about:
**Title**: {article_title}

**Summary**: {article_summary}

**Key Points**:
{key_points_text}

**Requirements**:
1. Hook viewers in the first 3 seconds
2. Use a {style} tone
3. Target word count: 250-350 words (for {target_duration}s)
4. Write for spoken delivery
5. End with a call-to-action

Generate the script now:"""


def build_article_analysis_prompt(
    title: str,
    description: str,
    content_preview: str,
    published_at: str,
    source: str
) -> str:
    """
    Build prompt for article analysis and scoring.
    
    Args:
        title: Article title
        description: Article description
        content_preview: Preview of article content
        published_at: Publication date
        source: Source name
        
    Returns:
        Formatted prompt string
    """
    return f"""You are an AI content analyst specializing in technology and AI news.

Analyze this article and provide scores and insights:

**Article Details**:
- Title: {title}
- Source: {source}
- Published: {published_at}
- Description: {description}
- Content Preview: {content_preview}

**Task**: Score this article on the following dimensions (0-10 scale):

1. **Relevance Score**: How relevant is this to AI/tech audience?
2. **Engagement Score**: How likely to engage viewers (viral potential)?
3. **Recency Score**: How timely/newsworthy is this?
4. **Uniqueness Score**: How unique/novel is this content?

Also provide:
- **Category**: Main category (e.g., "AI Research", "Tech News", "Product Launch")
- **Key Topics**: List of 3-5 key topics/keywords (keep each keyword short, 1-3 words max)
- **Why Interesting**: Brief explanation of why this is interesting (1-2 sentences ONLY, max 50 words)

**IMPORTANT**: Keep the response compact. Do not write long explanations. Each field should be concise.

**Output Format** (JSON):
{{
  "relevance_score": 8.5,
  "engagement_score": 7.0,
  "recency_score": 9.0,
  "uniqueness_score": 6.5,
  "category": "AI Research",
  "key_topics": ["GPT-4", "language models", "AI safety"],
  "why_interesting": "Groundbreaking research that could change how we interact with AI."
}}

Provide your analysis in valid JSON format:"""


def build_book_analysis_prompt(book: dict) -> str:
    """
    Build prompt for book analysis to generate key takeaways and video angles.
    
    Args:
        book: Book data dict with title, author, description, subjects
        
    Returns:
        Formatted prompt string
    """
    subjects_text = ", ".join(book.get("subjects", [])[:10]) or "General"
    
    return f"""You are a professional book reviewer creating content for YouTube Shorts.

Analyze this book and extract key insights for a 60-second video summary.

**Book Information**:
- Title: {book.get('title', 'Unknown')}
- Author: {book.get('author', 'Unknown')}
- Published: {book.get('first_publish_year', 'Unknown')}
- Genres/Subjects: {subjects_text}
- Description: {book.get('description', 'No description available')}

**Task**: Generate engaging content for a book review Short:

1. **Key Takeaways**: Extract 5-7 actionable insights from this book that viewers can apply immediately. Each takeaway should have:
   - A clear point (1 sentence)
   - A hook phrase that would make viewers want to learn more
   - A viral score (1-10) indicating how shareable this insight is

2. **Suggested Video Angles**: Generate 3-4 video title options that would perform well on YouTube Shorts:
   - Make them clickable and curiosity-inducing
   - Use proven formats like "X Lessons from...", "Why You Should Read...", "The Book That Changed..."
   - Keep under 60 characters each

3. **Target Audience**: Who is this book for?

4. **Emotional Hook**: What emotional response should the video evoke?

**Output Format** (JSON):
{{
  "key_takeaways": [
    {{"point": "The 1% improvement rule compounds to massive results over time", "hook": "This simple math will blow your mind", "viral_score": 9}},
    {{"point": "Focus on systems, not goals", "hook": "Goals are actually killing your progress", "viral_score": 8}}
  ],
  "suggested_angles": [
    "5 Life-Changing Lessons from {book.get('title', 'This Book')}",
    "Why {book.get('title', 'This Book')} Changed My Life",
    "The 1 Habit That Will Transform Your 2026"
  ],
  "target_audience": "Professionals looking to build better habits and improve productivity",
  "emotional_hook": "Inspiration and actionable motivation"
}}

Generate the analysis in valid JSON format:"""


def _build_book_review_script_prompt(
    article_title: str,
    article_summary: str,
    key_points: list,
    target_duration: int = 85,
    article_content: str = "",
    genre_strategy: dict = None
) -> str:
    """Build an 85-second story-driven book review script — Nano Banana retention format.

    Structure: Forbidden Hook → Paradox Amplifier → Relatable Story → Famous Example
               → Hidden Truth → Cheat Code → Identity Mirror → Loop CTA

    When genre_strategy is provided (from GenreStrategyRegistry), injects
    persona-specific hook style, tone, and visual mood.
    """

    key_points_text = "\n".join(f"- {point}" for point in key_points)

    # Include source content if available
    source_section = ""
    if article_content:
        content_preview = article_content[:5000] if len(article_content) > 5000 else article_content
        source_section = f"""
**SOURCE CONTENT** (Use this as your factual backbone — every claim must come from here):
{content_preview}
"""

    # ── Genre-Aware Persona Injection ──
    if genre_strategy and genre_strategy.get("name") != "The Storyteller":
        persona_line = genre_strategy["persona_instruction"]

        hook_examples = ""
        if genre_strategy.get("hook_patterns"):
            examples = "\n".join(f'   - "{h}"' for h in genre_strategy["hook_patterns"][:3])
            hook_examples = f"""\n**GENRE HOOK EXAMPLES** (adapt these — do NOT copy verbatim):
{examples}\n"""

        genre_tone = genre_strategy.get("tone_guidance", "")
        tone_section = f"""\n**NARRATIVE PERSONA: {genre_strategy['name']}**
{genre_tone}\n""" if genre_tone else ""

        visual_hint = genre_strategy.get("visual_emphasis", "")
        visual_section = f"""\n**VISUAL MOOD** (must influence every image_keywords and visual_cues):
{visual_hint}\n""" if visual_hint else ""
    else:
        persona_line = (
            "You are '60 Second Books' — the most addictive book review channel on YouTube Shorts. "
            "Your scripts feel like forbidden knowledge being whispered by a brilliant friend. "
            "Viewers finish every video thinking: 'I need to read that book right now.'"
        )
        hook_examples = ""
        tone_section = ""
        visual_section = ""

    return f"""{persona_line}

**BOOK**: {article_title}

**SUMMARY**: {article_summary}

**KEY INSIGHTS**:
{key_points_text}
{source_section}
{hook_examples}{tone_section}{visual_section}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STORY-DRIVEN SCRIPT FORMAT — "NANO BANANA" RETENTION ENGINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is NOT an informational book summary. This is a 60-second story that makes viewers
feel something and NEED to read the book. Follow the 8-beat story arc EXACTLY.

**REFERENCE EXAMPLE — Psychology of Money (target energy level):**
- Scene 1 Hook: "Most people don't want to be millionaires — they want to SPEND a million dollars."
- Scene 2: "That's the fastest way to stay broke. Morgan Housel's Psychology of Money changed how 4 million people think about wealth."
- Scene 3: "Think of your money like a seed. Every dollar you don't spend is a seed you're planting."
- Scene 4: "Warren Buffett didn't get rich because he was smart. He got rich because he was patient."
- Scene 5: "He started investing at 10. But 95% of his wealth came after age 65. That's compounding."
- Scene 6: "True wealth is invisible. It's the car you didn't buy. The vacation you didn't take."
- Scene 7: "Are you building wealth — or performing wealth for people who don't care about you?"
- Scene 8: "Follow 60 Second Books. We read the books so you don't have to."

NOW write the script for **{article_title}** at this same energy level. Make it better.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
8-SCENE STORY ARC (total ~{target_duration} seconds)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Scene 1 — FORBIDDEN HOOK** (~6s, 12-16 words):
Drop a counterintuitive bomb. Challenge what the viewer "knows" is true.
Rules: NO questions. Start with "Most people..." / "The [thing] that..." / "[Topic] doesn't work..."
This is a verbal slap that STOPS the scroll. Make them feel slightly uncomfortable.

**Scene 2 — PARADOX AMPLIFIER** (~8s, 20-24 words):
Twist the knife. Show WHY the conventional approach is broken. Name the book + author naturally.
Format: "[Consequence of wrong thinking]. [Book title] by [Full Author Name] reveals why."

**Scene 3 — THE RELATABLE STORY** (~12s, 28-34 words):
Anchor the big idea in a vivid metaphor or analogy. Use "Think of it like..."
Make it physical, sensory, and instantly recognizable. No jargon.
Example formula: "Think of [concept] like a [everyday object]. [Analogy]. That's [book's core idea]."

**Scene 4 — THE FAMOUS EXAMPLE** (~10s, 24-28 words):
Name a real person (billionaire, historical figure, athlete) who proves the principle.
Show the surprising REASON they succeeded — it's never what people assume.
Format: "[Famous person] didn't succeed because of [obvious reason]. They succeeded because of [real reason]."

**Scene 5 — THE HIDDEN TRUTH** (~10s, 24-28 words):
Reveal the counterintuitive implication most people MISS. The "wait, what?" moment.
Use: "But here's what nobody tells you..." / "The part everyone gets wrong..."
This is the insight that makes viewers SAVE the video.

**Scene 6 — THE CHEAT CODE** (~10s, 24-28 words):
Give the viewer the actionable secret. Frame it as forbidden knowledge.
Use: "True [wealth/success/happiness] is..." / "The real [metric/rule/trick] is..."
Vivid, concrete. No vague advice. This should feel like an unlocked achievement.

**Scene 7 — IDENTITY MIRROR** (~8s, 18-22 words):
Hold up a mirror. Make the viewer see themselves. Ask the question that haunts them.
Format: "Are you [doing the wrong thing] — or [doing the right thing]?"
This creates the itch that forces them to get the book.

**Scene 8 — LOOP CTA** (~6s, 12-16 words):
Close the loop opened in Scene 1. Deliver payoff, then brand drop.
MANDATORY: End with "Follow 60 Second Books."
Format: "[Payoff statement]. Follow 60 Second Books — we read the books so you don't have to."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCRIPT WRITING RULES (NON-NEGOTIABLE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Every sentence under 10 words (TTS rhythm)
- Present tense, active voice ONLY
- SPELL OUT all names fully — never "Housel", always "Morgan Housel"
- ZERO filler: no "basically", "kind of", "sort of", "um"
- Story > information: show don't tell, analogy over explanation
- The FEELING matters more than the facts — make viewers feel something
- Each scene must EARN its place — cut anything that doesn't advance the story

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NANO BANANA VISUAL FORMULA (for image_keywords and visual_cues)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DO NOT use generic stock photo keywords. Use the Nano Banana formula:
  [Specific Subject] + [Precise Action] + [Evocative Setting] + [Cinematic Lighting] + [Camera/Motion]

Style suffix to append to ALL image_keywords:
  "cinematic color grade, dramatic lighting, shallow depth of field, 4K film look"

**Scene-by-scene visual guide:**
- Scene 1 (Forbidden Hook): Dark, high-contrast visual of the book's CORE TENSION. Not the book cover.
  Example: "person staring at empty wallet in dim light, dramatic shadows, shallow depth of field, 4K film look"
- Scene 2 (Paradox Amplifier): {article_title} book cover with moody dramatic lighting — NOT a flat product shot.
  Example: "{article_title} book cover glowing on dark mahogany desk, rim lighting, cinematic color grade"
- Scene 3 (Relatable Story): The metaphor made visual. If seed → plant a seed image. If water → river/ocean.
  Example: "tiny seed cracking concrete sidewalk sprouting green, macro photography, cinematic color grade"
- Scene 4 (Famous Example): The famous person in their element OR a symbolic visual of their achievement.
  Example: "Warren Buffett style older investor sitting patiently in quiet library, warm amber light, 4K film look"
- Scene 5 (Hidden Truth): Reveal visual — moment of discovery, light breaking through, door opening.
  Example: "person having eureka moment at dawn window, golden light, shallow depth of field, cinematic"
- Scene 6 (Cheat Code): The SECRET made physical. Invisible becomes visible.
  Example: "person NOT buying luxury car choosing savings instead, dramatic irony shot, cinematic color grade"
- Scene 7 (Identity Mirror): Person looking at their own reflection or at a crossroads.
  Example: "person at mirror in moody blue light, introspective, film noir aesthetic, shallow depth of field"
- Scene 8 (Loop CTA): Book cover in hands — warm, inviting, aspirational.
  Example: "close-up hands holding {article_title} open, warm morning light, bokeh background, 4K film look"

**BANNED visual keywords** (instant fail — DO NOT USE):
"abstract", "illustration", "clipart", "futuristic interface", "circuit board",
"business people", "team photo", "stock photo", "generic background"

**BOOK GROUNDING RULE**: {article_title} book cover MUST appear in at least 2 scenes (Scenes 1-2 and Scene 8).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TRANSITION HINTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- `"cut"` — hard cut (0s). Use for Scenes 1, 4, 6 — punchy moments.
- `"fade"` — smooth crossfade (0.8s). Use for Scenes 2, 3, 5, 7 — emotional transitions.
- `"match_cut"` — quick dissolve (0.3s). Use Scene 8 — close the loop visually.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CALLOUT FIELD RULES (NEW — CRITICAL)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Every scene MUST include a `callout` field:
- 2-3 words MAX, ALL CAPS
- Extract the MOST IMPACTFUL phrase from that scene's text
- Must create INSTANT curiosity or punch hard emotionally
- Examples by beat:
  Scene 1 (Hook):        "STOP SCROLLING", "MOST PEOPLE WRONG", "FORBIDDEN TRUTH"
  Scene 2 (Paradox):     "HERE'S THE LIE", "WHAT THEY HIDE", "CONVENTIONAL WISDOM"
  Scene 3 (Story):       "THINK OF IT", "MONEY LIKE SEEDS", "THE REAL GAME"
  Scene 4 (Example):     "WARREN BUFFETT", "NOT BECAUSE SMART", "THE REAL SECRET"
  Scene 5 (Hidden Truth):"NOBODY TELLS YOU", "THE PART MISSED", "WAIT FOR IT"
  Scene 6 (Cheat Code):  "TRUE WEALTH IS", "INVISIBLE FORTUNE", "CHEAT CODE"
  Scene 7 (Mirror):      "ARE YOU?", "WHICH ONE ARE", "THE REAL QUESTION"
  Scene 8 (CTA):         "FOLLOW NOW", "60 SECOND BOOKS", "READ THE BOOK"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT (JSON — strict)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{{
  "hook": "The Forbidden Hook verbatim. 12-16 words. No question mark.",
  "scenes": [
    {{
      "scene_number": 1,
      "callout": "STOP SCROLLING",
      "text": "FORBIDDEN HOOK: Counterintuitive bomb. 12-16 words. No questions.",
      "visual_cues": "Dark, high-contrast visual of the book's core tension — NOT the book cover",
      "image_keywords": ["[specific concept] + [dramatic action] + [setting], cinematic color grade, dramatic lighting, 4K film look"],
      "transition_hint": "cut",
      "duration_estimate": 6
    }},
    {{
      "scene_number": 2,
      "callout": "HERE'S THE LIE",
      "text": "PARADOX AMPLIFIER: Why conventional wisdom is broken. Name book + author. 20-24 words.",
      "visual_cues": "{article_title} book cover with dramatic moody lighting, not a flat product shot",
      "image_keywords": ["{article_title} book cover dramatic dark lighting cinematic", "[Full Author Name] author speaking at event"],
      "transition_hint": "fade",
      "duration_estimate": 8
    }},
    {{
      "scene_number": 3,
      "callout": "THINK OF IT",
      "text": "RELATABLE STORY: Vivid analogy. Think of [concept] like [everyday object]. 28-34 words.",
      "visual_cues": "The metaphor made physical and cinematic — sensory, not abstract",
      "image_keywords": ["[metaphor object] + [dramatic state] + [evocative setting], cinematic color grade, shallow depth of field"],
      "transition_hint": "fade",
      "duration_estimate": 12
    }},
    {{
      "scene_number": 4,
      "callout": "THE REAL SECRET",
      "text": "FAMOUS EXAMPLE: [Name] succeeded not because of [obvious] but because of [real reason]. 24-28 words.",
      "visual_cues": "Famous person in their element — or symbolic achievement visual",
      "image_keywords": ["[famous person type] + [symbolic setting] + [mood], warm amber light, 4K film look"],
      "transition_hint": "cut",
      "duration_estimate": 10
    }},
    {{
      "scene_number": 5,
      "callout": "NOBODY TELLS YOU",
      "text": "HIDDEN TRUTH: The part everyone misses. 'But here's what nobody tells you...' 24-28 words.",
      "visual_cues": "Revelation moment — light breaking through, discovery, the veil lifting",
      "image_keywords": ["[reveal visual] + [person discovering] + [dramatic light], cinematic, shallow depth of field"],
      "transition_hint": "fade",
      "duration_estimate": 10
    }},
    {{
      "scene_number": 6,
      "callout": "TRUE WEALTH IS",
      "text": "CHEAT CODE: The actionable secret. 'True [X] is...' — vivid and concrete. 24-28 words.",
      "visual_cues": "The invisible made visible — the secret shown physically",
      "image_keywords": ["[secret concept] + [physical manifestation] + [setting], dramatic lighting, cinematic color grade, 4K"],
      "transition_hint": "cut",
      "duration_estimate": 10
    }},
    {{
      "scene_number": 7,
      "callout": "WHICH ARE YOU?",
      "text": "IDENTITY MIRROR: 'Are you [wrong thing] — or [right thing]?' Make viewer see themselves. 18-22 words.",
      "visual_cues": "Person at a mirror or crossroads — introspective, moody",
      "image_keywords": ["person at mirror introspective moody blue light, film noir aesthetic, shallow depth of field"],
      "transition_hint": "fade",
      "duration_estimate": 8
    }},
    {{
      "scene_number": 8,
      "callout": "60 SECOND BOOKS",
      "text": "LOOP CTA: Close the loop. [Payoff]. Follow 60 Second Books. 12-16 words.",
      "visual_cues": "Book in warm inviting hands — aspirational close",
      "image_keywords": ["hands holding {article_title} open warm morning light bokeh background 4K film look", "{article_title} book cover inviting"],
      "transition_hint": "match_cut",
      "duration_estimate": 6
    }}
  ],
  "call_to_action": "Are you [identity question from Scene 7]? Follow 60 Second Books — we read the books so you don't have to.",
  "title_suggestion": "Clickbait-but-accurate title. Under 60 chars. Emoji ok."
}}

**Word count**: 160-200 words total (for {target_duration}s at ~2.5 words/second)

Generate the story-driven book review script JSON now. Make it impossible NOT to read {article_title}:"""


def build_viral_news_analysis_prompt(article: dict) -> str:
    """
    Build prompt for viral news analysis to score virality and extract facts.

    Args:
        article: Article data dict with title, source_name, description, content_preview

    Returns:
        Formatted prompt string
    """
    return f"""You are a viral content strategist specializing in YouTube Shorts.

Analyze this news article for viral video potential on YouTube Shorts.

**Article Information**:
- Headline: {article.get('title', 'Unknown')}
- Source: {article.get('source_name', 'Unknown')}
- Published: {article.get('published_at', 'Unknown')}
- Category: {article.get('category', 'General')}
- Summary: {article.get('description', 'No description available')}
- Content: {(article.get('content_preview') or '')[:3000]}

**Task**: Evaluate this article's viral video potential:

1. **Virality Score** (1-10): How likely is this to go viral as a YouTube Short?
   - 9-10: Once-a-month stories (major breakthroughs, scandals, paradigm shifts)
   - 7-8: Strong weekly material (product launches, surprising studies, celebrity involvement)
   - 5-6: Decent content (interesting but not urgent)
   - 1-4: Low potential (routine news, niche audience)

2. **Virality Reasons**: Why would people share this? (3 bullet points max)

3. **Key Facts**: Extract 3-5 factual claims from the article that MUST be in the video.
   Every claim must be directly stated in the source — NO speculation.

4. **Suggested Video Angles**: Generate 3-4 clickbait-but-accurate titles for YouTube Shorts.
   Use proven formats: "This changes everything", "No one saw this coming", "Breaking: [X] just [Y]"

5. **Target Audience**: Who will care about this most?

6. **Emotional Hook**: What emotion should the video trigger? (shock, curiosity, fear, excitement, outrage)

**Output Format** (JSON):
{{
  "virality_score": 8.5,
  "virality_reasons": [
    "Affects millions of people directly",
    "Major company involved — brand recognition",
    "Timing is perfect — trending topic right now"
  ],
  "key_facts": [
    "Fact 1 from the article",
    "Fact 2 from the article",
    "Fact 3 from the article"
  ],
  "suggested_angles": [
    "🔥 Breaking: [Headline rewritten for clicks]",
    "This Changes Everything for [Audience]",
    "No One Is Talking About This [Topic] News"
  ],
  "target_audience": "Tech enthusiasts and early adopters aged 18-35",
  "emotional_hook": "Shock and curiosity"
}}

Generate the analysis in valid JSON format:"""


def _build_viral_news_script_prompt(
    article_title: str,
    article_summary: str,
    key_points: list,
    target_duration: int = 60,
    article_content: str = "",
    news_strategy: dict = None
) -> str:
    """Build a 60-second viral news script prompt with 4 urgency-driven scenes.
    
    When news_strategy is provided (from NewsStrategyRegistry), injects
    category-specific persona, hook patterns, visual formula, and tone.
    """

    key_points_text = "\n".join(f"- {point}" for point in key_points)

    # Include source content if available
    source_section = ""
    if article_content:
        content_preview = article_content[:5000] if len(article_content) > 5000 else article_content
        source_section = f"""
**SOURCE CONTENT** (Use this as your primary reference — every claim MUST come from here):
{content_preview}
"""

    # ── News Strategy Injection ──
    if news_strategy and news_strategy.get("name") != "The Breaking News Anchor":
        persona_line = news_strategy["persona_instruction"]

        # Hook examples from strategy
        hook_examples = ""
        if news_strategy.get("hook_patterns"):
            examples = "\n".join(f'   - "{h}"' for h in news_strategy["hook_patterns"][:3])
            hook_examples = f"""\n**CATEGORY-SPECIFIC HOOK EXAMPLES** (adapt, don't copy verbatim):
{examples}\n"""

        # Tone guidance
        tone = news_strategy.get("tone_guidance", "")
        tone_section = f"""\n**NARRATIVE PERSONA: {news_strategy['name']}**
{tone}\n""" if tone else ""

        # Visual emphasis for image keywords
        visual_hint = news_strategy.get("visual_emphasis", "")
        visual_section = f"""\n**VISUAL MOOD** (influence image_keywords and visual_cues):
{visual_hint}\n""" if visual_hint else ""

        # Nano Banana style suffix
        style_suffix = news_strategy.get("style_suffix", "Photojournalistic, raw lighting, motion blur, 8k, sharp news aesthetic")
        visual_formula = news_strategy.get("visual_formula", "[Subject] + [Action] + [Setting] + [Lighting] + [Motion]")
    else:
        persona_line = (
            "You are a viral news anchor for YouTube Shorts. Your videos break trending stories "
            "and consistently get millions of views because of their urgency, accuracy, and punchy delivery."
        )
        hook_examples = ""
        tone_section = ""
        visual_section = ""
        style_suffix = "Photojournalistic, raw lighting, motion blur, 8k, sharp news aesthetic"
        visual_formula = "[Subject] + [Action] + [Setting] + [Lighting] + [Motion]"

    # ── Duration-aware scene structure ──
    if target_duration <= 60:
        scene_count = 4
        word_count_range = "130-160 words"
        scene_structure_block = (
            "1. **Scene 1 — The Urgent Hook** (~8s, 12-15 words):\n"
            "   PATTERN INTERRUPT. Drop the single biggest fact like a bomb.\n"
            "   Use words like URGENT, JUST IN, BREAKING, STOP SCROLLING.\n\n"
            "2. **Scene 2 — The Impact** (~18s, 40-50 words):\n"
            "   Rapid-fire facts. Connect directly to viewer's life.\n"
            "   Name specific companies, people, numbers.\n\n"
            "3. **Scene 3 — The Cheat Code** (~18s, 40-50 words):\n"
            "   The actionable hack nobody else is sharing.\n"
            "   Phrases: 'But here's the hack:', 'Here's what smart people do:'\n\n"
            "4. **Scene 4 — The Retention CTA** (~16s, 28-35 words):\n"
            "   Provocative question that DEMANDS comments. Clear follow CTA."
        )
    elif target_duration <= 120:
        scene_count = 6
        word_count_range = "280-320 words"
        scene_structure_block = (
            "1. **Scene 1 — The Urgent Hook** (~8s, 12-15 words):\n"
            "   PATTERN INTERRUPT. Drop the single biggest fact immediately.\n\n"
            "2. **Scene 2 — Context & Why Now** (~18s, 40-50 words):\n"
            "   What led to this moment. Why it matters right now.\n\n"
            "3. **Scene 3 — The Impact** (~22s, 50-60 words):\n"
            "   Full story with rapid-fire facts. Viewer life connection.\n"
            "   Specific companies, numbers, people.\n\n"
            "4. **Scene 4 — The Cheat Code** (~22s, 50-60 words):\n"
            "   The actionable insight. What smart people are doing with this.\n\n"
            "5. **Scene 5 — Counter-Narrative** (~18s, 40-45 words):\n"
            "   What critics or skeptics say, then your sharp rebuttal.\n\n"
            "6. **Scene 6 — Retention CTA** (~12s, 25-30 words):\n"
            "   Provocative question + follow CTA."
        )
    else:  # 300s — full regular video
        scene_count = 10
        word_count_range = "700-800 words"
        scene_structure_block = (
            "1. **Scene 1 — Hook** (~8s, 12-15 words): Pattern interrupt. Biggest fact.\n\n"
            "2. **Scene 2 — Background & Context** (~28s, 65-75 words):\n"
            "   Full context. History of this story. Why this moment is pivotal.\n\n"
            "3. **Scene 3 — The Main Event** (~30s, 70-80 words):\n"
            "   What exactly happened, with all specifics.\n\n"
            "4. **Scene 4 — Key Players** (~28s, 65-75 words):\n"
            "   Companies, people, locations, specific numbers.\n\n"
            "5. **Scene 5 — Industry Impact** (~30s, 70-80 words):\n"
            "   How this reshapes the competitive landscape.\n\n"
            "6. **Scene 6 — Viewer Impact** (~28s, 65-75 words):\n"
            "   Direct relevance to viewer's job, finances, daily life.\n\n"
            "7. **Scene 7 — Expert Perspectives** (~28s, 65-75 words):\n"
            "   What analysts, insiders, and credible voices say.\n\n"
            "8. **Scene 8 — Counter-Narrative** (~28s, 65-75 words):\n"
            "   The other side. Skeptics' view. Your sharp rebuttal.\n\n"
            "9. **Scene 9 — Cheat Code** (~28s, 65-75 words):\n"
            "   The actionable insight. What to DO with this information.\n\n"
            "10. **Scene 10 — Big Picture CTA** (~14s, 30-35 words):\n"
            "    Zoom out. 5-year implications. Provocative question + follow CTA."
        )

    return f"""{persona_line}

**BREAKING STORY**: {article_title}

**SUMMARY**: {article_summary}

**KEY FACTS**:
{key_points_text}
{source_section}
{hook_examples}{tone_section}{visual_section}**CRITICAL RULES**:
- ONLY use facts from the source content — NO speculation, NO "reportedly"
- Every sentence MUST be under 12 words
- Create URGENCY — this is breaking news, not a lecture
- Present tense, active voice ONLY
- End with a question that drives comments

**SCRIPT STRUCTURE** ({scene_count} scenes, ~{target_duration} seconds):

{scene_structure_block}

**IMAGE KEYWORDS — NANO BANANA FORMULA** (CRITICAL):
Every image prompt MUST follow this formula:
  {visual_formula}

Append this style to ALL image keywords:
  "{style_suffix}"

- Must reference the ACTUAL news subject (company names, people, products)
- Use photojournalistic, real-world visuals — NOT generic stock
- NEVER use generic: "breaking news graphic", "newspaper", "abstract tech"

**Output Format** (JSON):
{{
  "hook": "Pattern interrupt hook. 8-12 words. URGENT energy.",
  "scenes": [
    {{
      "scene_number": 1,
      "text": "The Urgent Hook. Pattern interrupt + biggest fact. 12-15 words.",
      "visual_cues": "Dramatic visual description for this scene",
      "image_keywords": ["[subject] + [action] + [setting], {style_suffix}"],
      "transition_hint": "cut",
      "duration_estimate": 5
    }},
    {{
      "scene_number": 2,
      "text": "The Impact. Full story with rapid-fire facts. Personal connection. 45-55 words.",
      "visual_cues": "Cinematic wide establishing shot of the news scene",
      "image_keywords": ["[company/person] + [event] + [setting], {style_suffix}"],
      "transition_hint": "fade",
      "duration_estimate": 20
    }},
    {{
      "scene_number": 3,
      "text": "The Cheat Code. Actionable insight. What to DO with this info. 45-55 words.",
      "visual_cues": "Close-up of person taking action or solution visual",
      "image_keywords": ["[action/solution] + [person] + [setting], {style_suffix}"],
      "transition_hint": "cut",
      "duration_estimate": 20
    }},
    {{
      "scene_number": 4,
      "text": "The Retention CTA. Provocative question + follow CTA. 30-35 words.",
      "visual_cues": "Engaging close-up with call to action energy",
      "image_keywords": ["[subject symbol] + [person engaging] + [city/crowd], {style_suffix}"],
      "transition_hint": "fade",
      "duration_estimate": 15
    }}
  ],
  "call_to_action": "Provocative question that DEMANDS comments + follow CTA",
  "title_suggestion": "🔥 Clickbait but accurate. Under 60 chars."
}}

**Word count**: {word_count_range} (for {target_duration}s at ~2.5 words/second)

Generate the viral news script JSON:"""


def _build_daily_digest_script_prompt(
    digest_title: str,
    digest_summary: str,
    stories: list,
    target_duration: int = 60,
    raw_content: str = "",
) -> str:
    """
    Build a multi-story roundup script prompt for the Daily AI Digest format.

    AI Insider persona: investigative tech journalist, "Urgent Insider" tone.
    Every story beat explains WHY IT MATTERS to the viewer.

    Durations:
      60s  → 7 scenes: Hook + 3 story beats + Thread + Impact + CTA
      90s  → 9 scenes: Hook + 5 story beats + Thread + Impact + CTA

    Each story beat covers one article in ~10-15s.
    """
    import json

    if target_duration <= 65:
        num_stories = 3
        story_duration = 12
        total_scenes = 7
        word_count_range = "135-165"
        structure_label = "60-second (3-story)"
    else:
        num_stories = 5
        story_duration = 10
        total_scenes = 9
        word_count_range = "220-260"
        structure_label = "90-second (5-story)"

    # Format stories for the prompt
    stories_to_use = stories[:num_stories]
    stories_text = ""
    for i, story in enumerate(stories_to_use, 1):
        title = story.get("title", "")
        source = story.get("source", "")
        key_fact = story.get("key_fact", story.get("description", ""))
        company = story.get("company", "")
        impact = story.get("impact", "")
        stories_text += f"""
STORY {i}: {title}
  Source: {source}
  Company/Topic: {company}
  Key fact: {key_fact}
  Why it matters: {impact}
"""

    story_beats_schema = ""
    for i in range(1, num_stories + 1):
        story_beats_schema += f"""  {{
      "scene_number": {i + 1},
      "story_index": {i},
      "company": "Company or topic name from story {i}",
      "text": "Story {i}: [COMPANY] just [WHAT happened — 1 bold fact]. Why you need to care: [DIRECT impact on viewer career/money/future — 1-2 sharp sentences]. ~{int(story_duration * 2.5)} words.",
      "visual_cues": "Dark cinematic close-up of [company product/logo/HQ] on obsidian surface, dramatic rim lighting, midnight blue gradient",
      "image_keywords": ["[company name] dark cinematic midnight blue 8k", "[company] technology high-tech bokeh obsidian", "[story subject] investigative journalism dramatic lighting"],
      "transition_hint": "cut",
      "duration_estimate": {story_duration}
    }},
"""

    return f"""You are a lead investigative tech journalist for AI Insider — the most credible AI news channel on YouTube Shorts.

Your mission: Write a {structure_label} DAILY AI DIGEST that feels like EXCLUSIVE INSIDER INTELLIGENCE — not news. INTELLIGENCE.

## TODAY'S AI INSIDER BRIEFING — {num_stories} STORIES
{stories_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THE AI INSIDER FORMULA (NON-NEGOTIABLE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Opening Hook** — High-stakes pattern interrupt that creates IMMEDIATE tension. Energy examples:
  - "The AI world just shifted. Here's what they don't want you to know."
  - "Three AI moves happened today. Most people missed all of them."
  - "The AI race just changed direction. Here's the insider view."
  - "While you were sleeping, the AI landscape just flipped."

**Story Beat Formula** (APPLY TO EVERY STORY — no exceptions):
  Line 1: [COMPANY] just [WHAT happened — bold, one sentence, active voice].
  Line 2: WHY IT MATTERS: [Direct impact on viewer's career/tools/future — specific, not generic].
  NEVER say "this is significant" or "this is noteworthy" — SHOW why it matters.
  If it's an AI model: "Your [workflow/job/code] just changed because..."
  If it's funding: "This money signals [company] is betting on [specific outcome] — which means..."
  If it's policy: "If you work in [field], this law now affects you by..."

**Connecting Thread** — One sentence naming the MACRO TREND:
  "The pattern? Every major lab doubled down on [X] this week."
  "What ties all three? The race for [capability] just went vertical."

**Closing Question** — MUST be provocative enough to force a comment:
  "Which story changes YOUR strategy this week? Drop it below."
  "Are we watching the foundation of AGI being laid right now? Tell me."
  "Is this the week AI crossed a line you didn't see coming?"

**CTA** — Close with: "Subscribe to AI Insider. We brief you daily before the mainstream catches up."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCENE STRUCTURE ({total_scenes} scenes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Scene 1:           URGENCY HOOK (5s) — Creates immediate tension. Insider tone.
Scenes 2-{num_stories + 1}:    STORY BEATS ({story_duration}s each) — Company + What + WHY IT MATTERS
Scene {num_stories + 2}:        CONNECTING THREAD (8s) — The macro pattern, the insider read
Scene {num_stories + 3}:        IMPACT (6s) — Direct viewer impact right now
Scene {total_scenes}:           PROVOCATIVE CLOSE + CTA (4s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMAGE KEYWORDS — DARK CINEMATIC "AI INSIDER" AESTHETIC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MANDATORY style prefix for ALL image_keywords:
  "Dark cinematic lighting, shallow depth of field, high-tech bokeh, midnight blue and obsidian
   color palette, hyper-realistic textures, 8k, professional tech journalism style"

Topic-specific visual direction:
  - OpenAI:      "glowing minimalist OpenAI logo brushed titanium, dimly lit research lab, midnight blue"
  - Google/Gemini: "Google DeepMind dark server room, blue holographic glow, obsidian surface, 8k"
  - Robotics:    "robotic hand holding silicon chip, intricate wiring, laboratory, midnight blue bokeh"
  - Funding:     "venture capital dark boardroom, holographic AI projection, obsidian table, 8k"
  - Policy:      "capitol building AI regulation dramatic storm sky, dark cinematic, 8k"
  - Default:     "[company] [product] dark cinematic obsidian surface, high-tech bokeh midnight blue"

NEVER USE: "breaking news graphic", "newspaper", "abstract tech", "business people smiling", "bright office"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT (strict JSON)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{{
  "hook": "High-stakes insider opener. Under 12 words. Creates immediate tension.",
  "scenes": [
    {{
      "scene_number": 1,
      "story_index": 0,
      "company": "",
      "text": "URGENCY HOOK. Insider briefing energy. Make them feel this is exclusive intel. ~12 words.",
      "visual_cues": "Dark split of today's AI logos, midnight blue, dramatic rim lighting, investigative aesthetic",
      "image_keywords": ["AI insider briefing dark cinematic midnight blue 8k", "artificial intelligence headlines obsidian dramatic", "tech news investigation hyper-realistic 8k"],
      "transition_hint": "cut",
      "duration_estimate": 5
    }},
{story_beats_schema}    {{
      "scene_number": {num_stories + 2},
      "story_index": 0,
      "company": "",
      "text": "CONNECTING THREAD. 'The pattern here?' Name the macro AI trend tying all stories. Sharp insight. ~20 words.",
      "visual_cues": "AI neural network nodes connecting, dark midnight blue gradient, cinematic depth of field",
      "image_keywords": ["AI convergence network dark cinematic 8k", "artificial intelligence strategy obsidian surface", "tech industry macro trend investigative 8k"],
      "transition_hint": "fade",
      "duration_estimate": 8
    }},
    {{
      "scene_number": {num_stories + 3},
      "story_index": 0,
      "company": "",
      "text": "VIEWER IMPACT. 'What this means for you right now:' — concrete career or business implication. ~15 words.",
      "visual_cues": "Person at dark workstation, holographic AI display, midnight blue ambiance, introspective glow",
      "image_keywords": ["professional AI career impact dark cinematic 8k", "tech builder opportunity 2025 dramatic lighting", "future work midnight blue obsidian holographic"],
      "transition_hint": "cut",
      "duration_estimate": 6
    }},
    {{
      "scene_number": {total_scenes},
      "story_index": 0,
      "company": "",
      "text": "[PROVOCATIVE QUESTION that demands a comment]. Subscribe to AI Insider. We brief you daily before the mainstream catches up.",
      "visual_cues": "AI Insider brand mark, dark obsidian aesthetic, single cyan accent glow, clean and bold",
      "image_keywords": ["AI insider news intelligence dark studio", "tech journalist investigative dramatic 8k", "subscribe news daily midnight blue obsidian"],
      "transition_hint": "fade",
      "duration_estimate": 4
    }}
  ],
  "call_to_action": "Subscribe to AI Insider — we brief you daily before the mainstream catches up. Which of these stories changes your strategy this week?",
  "title_suggestion": "Today's {num_stories} AI Insider Briefings (You Need to Know)"
}}

**Word count target**: {word_count_range} words total across all scenes
**Tone**: Authoritative investigative journalist. NOT hype. NOT a listicle. INTELLIGENCE BRIEFING.

Generate the AI Insider daily digest script JSON now:"""
