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
    category: str = ""
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
        
    Returns:
        Formatted prompt string
    """
    
    # Route to specialized prompt for book reviews
    if category == "book_review":
        return _build_book_review_script_prompt(
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
    article_content: str = ""
) -> str:
    """Build an 85-second book review script prompt with 7-8 structured scenes."""
    
    key_points_text = "\n".join(f"- {point}" for point in key_points)
    
    # Include source content if available
    source_section = ""
    if article_content:
        content_preview = article_content[:5000] if len(article_content) > 5000 else article_content
        source_section = f"""
**SOURCE CONTENT** (Use this as your primary reference):
{content_preview}
"""
    
    return f"""You are a professional book reviewer creating an engaging YouTube Shorts script.
Your book review videos get thousands of views because they are well-structured, informative, and visually compelling.

**BOOK**: {article_title}

**SUMMARY**: {article_summary}

**KEY POINTS**:
{key_points_text}
{source_section}
**SCRIPT STRUCTURE** (7-8 scenes, ~200 words total, {target_duration} seconds):

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

**Output Format** (JSON):
{{
  "hook": "Bold opening statement about the book. 12-15 words max.",
  "scenes": [
    {{
      "scene_number": 1,
      "text": "Hook: Bold claim that makes viewers stop scrolling.",
      "visual_cues": "Show book cover prominently with dark overlay",
      "image_keywords": ["{article_title} book cover front", "{article_title} bestselling book"],
      "duration_estimate": 5
    }},
    {{
      "scene_number": 2,
      "text": "Social proof with hard numbers — copies sold, awards, notable readers.",
      "visual_cues": "Show bestseller stats, bookstore displays, or award badges",
      "image_keywords": ["{article_title} sales infographic", "{article_title} award accolades"],
      "duration_estimate": 8
    }},
    {{
      "scene_number": 3,
      "text": "Author introduction — credentials and what inspired the book.",
      "visual_cues": "Show author photo or speaking at event",
      "image_keywords": ["[Full Author Name] author portrait photo", "[Full Author Name] speaking event"],
      "duration_estimate": 8
    }},
    {{
      "scene_number": 4,
      "text": "Key takeaway 1 — most impactful. Principle + why it works + example.",
      "visual_cues": "Visual metaphor for the concept",
      "image_keywords": ["{article_title} [concept keyword 1]", "{article_title} [concept visual 1]"],
      "duration_estimate": 13
    }},
    {{
      "scene_number": 5,
      "text": "Key takeaway 2 — problem + solution + transformation.",
      "visual_cues": "Visual example of the takeaway in practice",
      "image_keywords": ["{article_title} [concept keyword 2]", "{article_title} [concept visual 2]"],
      "duration_estimate": 13
    }},
    {{
      "scene_number": 6,
      "text": "Key takeaway 3 — surprising, counterintuitive insight.",
      "visual_cues": "Thought-provoking visual for the concept",
      "image_keywords": ["{article_title} [concept keyword 3]", "{article_title} [concept visual 3]"],
      "duration_estimate": 13
    }},
    {{
      "scene_number": 7,
      "text": "Who should read this — directly address target audience.",
      "visual_cues": "Show relatable audience imagery",
      "image_keywords": ["person reading {article_title}", "{article_title} target audience"],
      "duration_estimate": 8
    }},
    {{
      "scene_number": 8,
      "text": "CTA — question + follow prompt.",
      "visual_cues": "Motivational closing with subscribe prompt",
      "image_keywords": ["{article_title} book recommendation", "book review subscribe"],
      "duration_estimate": 5
    }}
  ],
  "call_to_action": "Which insight resonated most? Comment below and follow for more book reviews!",
  "title_suggestion": "Compelling title under 60 chars with emoji"
}}

**Word count**: 190-225 words total (for {target_duration}s at ~2.5 words/second)

Generate the book review script JSON:"""


