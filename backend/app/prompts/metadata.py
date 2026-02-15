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

2. **Description** (structured, max 500 chars):
   - Line 1: Hook sentence — expand on the title's curiosity gap
   - Line 2: (blank line)
   - Lines 3-5: "📌 Key Takeaways:" followed by 3 bullet points (use • character)
   - Line 6: (blank line)
   - Line 7: "👉 Follow @60SecondBooks for daily book reviews in 60 seconds!"
   - Lines 8+: Hashtags on a new line (most important first)

3. **Hashtags** (3-5 total):
   - MUST start with #Shorts
   - Include #BookReview
   - Include book-specific tag (e.g., #AtomicHabits)
   - Optionally include genre tag (e.g., #SelfHelp, #Psychology)

4. **Tags** (comma-separated long-tail keywords, 8-12):
   - MUST include: "{book_title} summary", "{book_author} books", "book review shorts"
   - Include genre-specific terms (e.g., "habit building tips", "self improvement books")
   - Include common misspellings and variations
   - Include: "60 second book review", "short book summary"

Return ONLY valid JSON in this format:
{{
  "title": "🧠 3 Tiny Habits That Will Change Your Life",
  "description": "What if getting 1% better every day could make you 37x better in a year?\\n\\n📌 Key Takeaways:\\n• Small habits compound into remarkable results\\n• Focus on systems, not goals\\n• The 4 laws of behavior change\\n\\n👉 Follow @60SecondBooks for daily book reviews in 60 seconds!\\n\\n#Shorts #BookReview #AtomicHabits #SelfHelp",
  "hashtags": ["#Shorts", "#BookReview", "#AtomicHabits", "#SelfHelp"],
  "tags": ["atomic habits summary", "james clear books", "book review shorts", "habit building tips", "self improvement books", "60 second book review", "short book summary", "atomic habits review"]
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
