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
    """Build an 85-second book review script prompt with 7-8 structured scenes.
    
    When genre_strategy is provided (from GenreStrategyRegistry), injects
    persona-specific instructions, hook patterns, and tone guidance.
    """
    
    key_points_text = "\n".join(f"- {point}" for point in key_points)
    
    # Include source content if available
    source_section = ""
    if article_content:
        content_preview = article_content[:5000] if len(article_content) > 5000 else article_content
        source_section = f"""
**SOURCE CONTENT** (Use this as your primary reference):
{content_preview}
"""
    
    # ── Genre-Aware Persona Injection ──
    # When a genre strategy is detected, override the default persona and tone.
    if genre_strategy and genre_strategy.get("name") != "The Storyteller":
        persona_line = genre_strategy["persona_instruction"]
        
        # Build hook examples from the strategy
        hook_examples = ""
        if genre_strategy.get("hook_patterns"):
            examples = "\n".join(f'   - "{h}"' for h in genre_strategy["hook_patterns"][:3])
            hook_examples = f"""\n**GENRE-SPECIFIC HOOK EXAMPLES** (adapt, don't copy verbatim):
{examples}\n"""
        
        # Genre-specific tone replaces the default VOICE & STYLE RULES
        genre_tone = genre_strategy.get("tone_guidance", "")
        tone_section = f"""\n**NARRATIVE PERSONA: {genre_strategy['name']}**
{genre_tone}\n""" if genre_tone else ""
        
        # Visual emphasis hint for image keywords
        visual_hint = genre_strategy.get("visual_emphasis", "")
        visual_section = f"""\n**VISUAL MOOD** (influence image_keywords and visual_cues):
{visual_hint}\n""" if visual_hint else ""
    else:
        persona_line = (
            "You are a professional book reviewer creating an engaging YouTube Shorts script.\n"
            "Your book review videos get thousands of views because they are well-structured, "
            "informative, and visually compelling."
        )
        hook_examples = ""
        tone_section = ""
        visual_section = ""
    
    return f"""{persona_line}

**BOOK**: {article_title}

**SUMMARY**: {article_summary}

**KEY POINTS**:
{key_points_text}
{source_section}
{hook_examples}{tone_section}{visual_section}**SCRIPT STRUCTURE** (7-8 scenes, ~200 words total, {target_duration} seconds):

1. **Scene 1 – Hook** (~5 seconds, 12-15 words):
   Open with a bold, curiosity-driven statement that makes viewers STOP scrolling.
   Patterns that work: "This book changed how [X million] people think about [topic]."
   Do NOT start with a question. Start with a bold claim.

2. **Scene 2 – Social Proof** (~8 seconds, 20-25 words):
   Establish WHY this book matters with hard numbers and credibility.
   Include: copies sold, awards, years on bestseller lists, notable endorsements.
   Example: "Over 40 million copies sold. Used by presidents, CEOs, and Olympic athletes. This isn't just a book — it's a movement."

3. **Scene 3 – Author & Context** (~8 seconds, 20-25 words):
   Introduce the author's credentials and what led them to write this book.
   Make the author relatable and credible.
   Example: "Stephen Covey spent 25 years studying what makes people truly effective. His framework changed modern leadership forever."

4. **Scene 4 – Key Takeaway 1** (~13 seconds, 30-35 words):
   The MOST impactful insight from the book. Make it actionable and specific.
   Structure: State the principle → Explain WHY it works → Give a concrete example.

5. **Scene 5 – Key Takeaway 2** (~13 seconds, 30-35 words):
   The second most powerful insight. Connect it to the viewer's daily life.
   Structure: Relatable problem → Book's solution → Transformation promised.

6. **Scene 6 – Key Takeaway 3** (~13 seconds, 30-35 words):
   A surprising or counterintuitive insight that makes viewers think differently.
   This should be the "I never thought of it that way" moment.

7. **Scene 7 – Who Should Read This** (~8 seconds, 20-25 words):
   Directly address the target audience. Make viewers feel personally called out.
   Example: "If you've ever felt stuck in a cycle of busyness without progress, this book will rewire how you think about productivity."

8. **Scene 8 – CTA** (~5 seconds, 12-15 words):
   Strong call to action. End with a question that invites comments.
   Example: "Which habit will you start with? Tell me in the comments. Follow for more book reviews."

**VOICE & STYLE RULES**:
- Speak like a knowledgeable friend recommending a life-changing book
- Clear, articulate sentences (8-12 words each)
- Use present tense and active voice throughout
- Be enthusiastic but authentic — NOT salesy or hype-driven
- Every single sentence MUST add value — zero filler
- SPELL OUT all author names fully and correctly (critical for TTS)
- Do NOT abbreviate names or use nicknames

**IMAGE KEYWORDS** (CRITICAL — Entity Grounding Required):
Every image keyword MUST include the EXACT book title or author's full name.
Generic keywords like "bestseller" or "author photo" will return WRONG images.

- Scene 1 (Hook): "{article_title} book cover front"
- Scene 2 (Social Proof): "{article_title} infographic" or "{article_title} sales accolades"
- Scene 3 (Author): "[Full Author Name] author portrait photo" (FULL NAME always required)
- Scenes 4-6 (Takeaways): "{article_title} [concept keyword]" (e.g., "Atomic Habits habit loop diagram")
  - Good: "Atomic Habits 1 percent improvement graph", "Atomic Habits cue craving response reward"
  - Bad: "self help book", "motivation", "success" (too generic — BANNED)
- Scene 7 (Audience): "person reading {article_title}" or "{article_title} target audience"
- Scene 8 (CTA): "{article_title} book recommendation" or "book review subscribe"

**BANNED keywords** (NEVER use alone without book title): "bestseller", "author photo", 
"book cover", "self help", "motivation", "success", "reading", "abstract", "illustration", "clipart"

**HUMAN PRESENCE WEIGHT** (IMPORTANT — High Engagement Rule):
Live-action book reviewers outperform abstract visuals. To match their engagement:
- If the scene text uses personal pronouns ("you", "I", "we", "your", "our"), 
  the image keywords MUST include at least ONE human-centric keyword.
- Human-centric keyword patterns:
  - "diverse person reading in library", "close-up hands holding {article_title}"
  - "person looking thoughtful with book", "student taking notes at desk"
  - "person looking at city skyline reflective", "woman reading in cozy setting"
- Scenes 4-6 (Takeaways) are ideal for human visuals — show people APPLYING the concept.
- At least 2 of scenes 4-7 MUST have a human-centric keyword in their image_keywords list.

**BOOK OBJECT GROUNDING** (30% Rule — Contextual Anchoring):
The physical book MUST appear in at least 3 of 8 scenes (~30%) to ground the review in reality.
- Scene 1 (Hook): ALWAYS includes the book cover (mandatory).
- Scene 7 (Audience): ALWAYS includes "person holding {article_title}" (mandatory).
- At least ONE of Scenes 4-6 MUST include a keyword like "{article_title} book on desk", 
  "hands holding open {article_title}", or "person with {article_title} in hand".
- This ensures viewers always remember WHICH book is being reviewed.

**TRANSITION HINTS** (Scene-to-Scene Pacing):
Each scene should include a `transition_hint` to control visual pacing:
- `"fade"` — smooth crossfade (default, 0.8s). Use for most scene transitions.
- `"cut"` — hard cut (0s). Use for dramatic reveals or punchlines.
- `"match_cut"` — quick dissolve (0.3s). Use when transitioning from an abstract metaphor 
  to a human reaction, or from a book cover to a person holding the book.

**Output Format** (JSON):
{{
  "hook": "Bold opening statement about the book. 12-15 words max.",
  "scenes": [
    {{
      "scene_number": 1,
      "text": "Hook: Bold claim that makes viewers stop scrolling.",
      "visual_cues": "Show book cover prominently with dark overlay",
      "image_keywords": ["{article_title} book cover front", "{article_title} bestselling book"],
      "transition_hint": "fade",
      "duration_estimate": 5
    }},
    {{
      "scene_number": 2,
      "text": "Social proof with hard numbers — copies sold, awards, notable readers.",
      "visual_cues": "Show bestseller stats, bookstore displays, or award badges",
      "image_keywords": ["{article_title} sales infographic", "{article_title} award accolades"],
      "transition_hint": "fade",
      "duration_estimate": 8
    }},
    {{
      "scene_number": 3,
      "text": "Author introduction — credentials and what inspired the book.",
      "visual_cues": "Show author photo or speaking at event",
      "image_keywords": ["[Full Author Name] author portrait photo", "[Full Author Name] speaking event"],
      "transition_hint": "cut",
      "duration_estimate": 8
    }},
    {{
      "scene_number": 4,
      "text": "Key takeaway 1 — most impactful. Principle + why it works + example.",
      "visual_cues": "Person applying the concept in real life",
      "image_keywords": ["{article_title} [concept keyword 1]", "person applying {article_title} concept", "{article_title} book on desk"],
      "transition_hint": "match_cut",
      "duration_estimate": 13
    }},
    {{
      "scene_number": 5,
      "text": "Key takeaway 2 — problem + solution + transformation.",
      "visual_cues": "Person experiencing the transformation described",
      "image_keywords": ["{article_title} [concept keyword 2]", "person thinking reflective", "{article_title} [concept visual 2]"],
      "transition_hint": "fade",
      "duration_estimate": 13
    }},
    {{
      "scene_number": 6,
      "text": "Key takeaway 3 — surprising, counterintuitive insight.",
      "visual_cues": "Thought-provoking visual — person with lightbulb moment",
      "image_keywords": ["{article_title} [concept keyword 3]", "close-up hands holding open {article_title}", "{article_title} [concept visual 3]"],
      "transition_hint": "match_cut",
      "duration_estimate": 13
    }},
    {{
      "scene_number": 7,
      "text": "Who should read this — directly address target audience.",
      "visual_cues": "Diverse person holding and reading the book",
      "image_keywords": ["diverse person reading {article_title}", "person holding {article_title} in hands"],
      "transition_hint": "fade",
      "duration_estimate": 8
    }},
    {{
      "scene_number": 8,
      "text": "CTA — question + follow prompt.",
      "visual_cues": "Motivational closing with subscribe prompt",
      "image_keywords": ["{article_title} book recommendation", "book review subscribe"],
      "transition_hint": "cut",
      "duration_estimate": 5
    }}
  ],
  "call_to_action": "Which insight resonated most? Comment below and follow for more book reviews!",
  "title_suggestion": "Compelling title under 60 chars with emoji"
}}

**Word count**: 190-225 words total (for {target_duration}s at ~2.5 words/second)

Generate the book review script JSON:"""


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

**SCRIPT STRUCTURE** (4 scenes, ~{target_duration} seconds):

1. **Scene 1 — The Urgent Hook** (~5 seconds, 12-15 words):
   Open with a PATTERN INTERRUPT. Drop the single biggest fact like a bomb.
   Use words like URGENT, JUST IN, BREAKING, STOP SCROLLING.
   This is NOT a gentle opener — it's a verbal slap.

2. **Scene 2 — The Impact (The Story)** (~20 seconds, 45-55 words):
   Deliver the full story with rapid-fire facts.
   Immediately connect it to the viewer's personal life:
   "This is going to change your [bank account / privacy / job / health] by tomorrow."
   Name specific companies, people, locations, and numbers.
   Every sentence must push urgency forward.

3. **Scene 3 — The Cheat Code (Actionable News)** (~20 seconds, 45-55 words):
   Give the viewer the HACK — the actionable insight nobody else is sharing.
   What should they DO with this information? What's the opportunity?
   Use phrases like "But here's the hack:", "Here's what smart people are doing:",
   "The one thing you need to know:"
   This is the value-add that makes viewers SAVE the video.

4. **Scene 4 — The Retention CTA** (~15 seconds, 30-35 words):
   End with a provocative question that DEMANDS comments.
   Ask viewers to share their experience or pick a side.
   Include a clear follow CTA.
   Example: "Is your job safe, or are you leveling up? Drop your industry below."

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

**Word count**: 130-160 words total (for {target_duration}s at ~2.5 words/second)

Generate the 60-second viral news script JSON:"""
