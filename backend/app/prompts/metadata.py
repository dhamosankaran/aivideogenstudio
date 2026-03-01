"""
YouTube metadata and publishing prompt templates.

Contains prompts for:
- SEO-optimized metadata (title, description, hashtags, tags)
- Book review–specific metadata with @60SecondBooks branding
- Catchy title generation
- Hashtag generation
"""


METADATA_GENERATION_PROMPT = """You are a YouTube SEO expert specializing in AI/Tech content for YouTube Shorts.

Generate optimized metadata for this video:

**Article Title**: {article_title}
**Description**: {article_description}
**Content Type**: {content_type}
{script_section}

**Requirements**:

1. **Title** (max 60 chars for mobile display):
   - Start with a hook word (BREAKING, INSANE, SHOCKING, Here's Why, etc.)
   - Include numbers if relevant
   - Create curiosity gap
   - Avoid clickbait that doesn't deliver

2. **Description** (max 500 chars):
   - First line: Hook that expands on title
   - Briefly explain what viewers will learn
   - Include call-to-action
   - End with 5-8 relevant hashtags (most important first)
   - Format: #AINews #TechUpdate etc.

3. **Hashtags** (5-10 total):
   - Mix of broad (#AI #Tech) and specific (#ElonMusk #SpaceX)
   - Include trending relevant tags
   - No spaces in hashtags

4. **Tags** (for YouTube search, 5-15):
   - Include common misspellings of key terms
   - Include related search terms
   - Include the main topic as first tag

Return ONLY valid JSON in this format:
{{
  "title": "Your catchy title here",
  "description": "Your SEO description here with hashtags at the end",
  "hashtags": ["#AI", "#Tech", "#Trending"],
  "tags": ["main topic", "related term", "common search"]
}}"""


BOOK_REVIEW_METADATA_PROMPT = """You are a YouTube SEO expert for the channel @60SecondBooks, specializing in book review Shorts.

Generate metadata for this book review video:

**Book Title**: {book_title}
**Author**: {book_author}
**Key Takeaways**: {takeaways}
{script_section}

**Requirements**:

1. **Title** (max 60 chars, CRITICAL):
   - Lead with a curiosity-gap number from the book's content (e.g., "37x", "1%", "3 Rules", "5 Habits")
   - Include the book title OR author name (not both — pick whichever is more recognizable)
   - Include ONE relevant emoji at the start or end
   - Use hook patterns: "X Lessons from…", "The 1% Rule from…", "Why [Book] Changed…"
   - Examples:
     - "🧠 3 Tiny Habits That Will Change Your Life"
     - "📖 The 1% Rule from Atomic Habits"
     - "🔥 Why 37x Better Isn't About Willpower"

2. **Description** (structured, 500-1500 chars — FILL IT OUT):
   - Line 1: Hook sentence — expand on the title's curiosity gap (1-2 sentences)
   - Line 2: (blank line)
   - Lines 3-7: "📌 Key Takeaways:" followed by 3-5 bullet points (use • character)
   - Line 8: (blank line)
   - Lines 9-10: "📚 About the Book:" — 1-2 sentences about the book and author's credibility
   - Line 11: (blank line)
   - Line 12: "🎯 Who Should Read This:" — 1 sentence describing the target audience
   - Line 13: (blank line)
   - Line 14: "👉 Follow @60SecondBooks for daily book reviews in 60 seconds!"
   - Lines 15+: Hashtags on a new line (most important first)
   
   IMPORTANT: Aim for 500-1500 characters. Shorter descriptions hurt SEO. Include real value so viewers engage.

3. **Hashtags** (5-8 total for maximum reach):
   - MUST start with #Shorts
   - Include #BookReview
   - Include book-specific tag (e.g., #AtomicHabits — no spaces)
   - Include genre tags (e.g., #SelfHelp, #Psychology, #BusinessBooks, #Leadership)
   - Include trending book tags: #BookTok, #MustRead, #BookRecommendation
   - Include at least ONE niche tag relevant to the book's topic

4. **Tags** (comma-separated long-tail keywords, 15-20 to FILL toward 500 chars):
   - MUST include: "{book_title} summary", "{book_author} books", "book review shorts", "60 second book review", "short book summary"
   - Include genre-specific terms (e.g., "habit building tips", "self improvement books 2026")
   - Include comparison/discovery tags: "books like {book_title}", "best [genre] books", "top [genre] books 2026"
   - Include audience-intent tags: "what to read next", "book recommendations [genre]", "[topic] tips from books"
   - Include channel tags: "60secondbooks", "60 second books review", "quick book summary"
   - Include common misspellings and search variations of the book title
   - IMPORTANT: Generate enough tags to use 400-500 of the 500 character limit

Return ONLY valid JSON in this format:
{{
  "title": "🧠 3 Tiny Habits That Will Change Your Life",
  "description": "What if getting 1% better every day could make you 37x better in a year? James Clear's Atomic Habits reveals the science behind small changes.\\n\\n📌 Key Takeaways:\\n• Small habits compound into remarkable results — 1% daily = 37x in a year\\n• Focus on systems, not goals — systems drive lasting change\\n• The 4 laws of behavior change: Cue, Craving, Response, Reward\\n• Identity-based habits outperform outcome-based goals\\n• Environment design matters more than motivation\\n\\n📚 About the Book: Atomic Habits by James Clear has sold over 15 million copies and been translated into 50+ languages. It's the definitive guide to habit formation backed by behavioral science.\\n\\n🎯 Who Should Read This: Anyone who wants to break bad habits, build good ones, and master the tiny behaviors that lead to remarkable results.\\n\\n👉 Follow @60SecondBooks for daily book reviews in 60 seconds!\\n\\n#Shorts #BookReview #AtomicHabits #SelfHelp #BookTok #MustRead #ProductivityBooks #HabitBuilding",
  "hashtags": ["#Shorts", "#BookReview", "#AtomicHabits", "#SelfHelp", "#BookTok", "#MustRead", "#ProductivityBooks", "#HabitBuilding"],
  "tags": ["atomic habits summary", "james clear books", "book review shorts", "60 second book review", "short book summary", "atomic habits review", "habit building tips", "self improvement books 2026", "books like atomic habits", "best self help books", "productivity books", "atomic habits key takeaways", "james clear atomic habits", "what to read next self help", "book recommendations self improvement", "60secondbooks", "quick book summary", "top habit books 2026", "behavior change books", "atomic habbits summary"]
}}"""


def build_metadata_prompt(
    article_title: str,
    article_description: str,
    content_type: str = "daily_update",
    script_content: str | None = None,
    book_author: str | None = None,
    takeaways: list | None = None,
) -> str:
    """Build prompt for YouTube metadata generation.
    
    Routes to book review–specific prompt when content_type is 'book_review'.
    """
    script_section = ""
    if script_content:
        script_section = f"**Script Preview**: {script_content[:500]}..."

    if content_type == "book_review":
        takeaway_text = ""
        if takeaways:
            if isinstance(takeaways, list):
                takeaway_text = "\n".join(f"- {t}" for t in takeaways[:5])
            else:
                takeaway_text = str(takeaways)
        
        return BOOK_REVIEW_METADATA_PROMPT.format(
            book_title=article_title,
            book_author=book_author or "Unknown Author",
            takeaways=takeaway_text or "See script for details",
            script_section=script_section,
        )

    return METADATA_GENERATION_PROMPT.format(
        article_title=article_title,
        article_description=article_description,
        content_type=content_type,
        script_section=script_section,
    )
