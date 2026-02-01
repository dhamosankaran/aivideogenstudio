"""
Article analysis prompt templates.
"""

ARTICLE_ANALYSIS_PROMPT = """You are an AI news curator for a YouTube Shorts channel focused on AI/tech news.

Your job is to analyze articles and score them on engagement potential for short-form video content.

Article to analyze:
---
Title: {title}
Description: {description}
Content Preview: {content_preview}
Published: {published_at}
Source: {source}
---

Extract the following scores and insights from the article.

Scoring Guidelines:

1. Relevance (0-10): Importance to AI/tech.
2. Engagement (0-10): Potential for YouTube Shorts.
3. Recency (0-10): Time sensitivity.
4. Uniqueness (0-10): Originality.

Categories: research, product, policy, industry, other.


**Key Topics**: 3-5 specific topics.

**Why Interesting**: One compelling sentence explanation.
"""


def build_article_analysis_prompt(
    title: str,
    description: str,
    content_preview: str,
    published_at: str,
    source: str
) -> str:
    """Build the complete article analysis prompt."""
    return ARTICLE_ANALYSIS_PROMPT.format(
        title=title,
        description=description or "N/A",
        content_preview=content_preview or "N/A",
        published_at=published_at or "Unknown",
        source=source or "Unknown"
    )
