"""
Helper functions for Phase 1 publishing features.
Adds catchy title, hashtag, and description generation.
"""

import logging
from typing import List
from app.models import Script, Article

logger = logging.getLogger(__name__)


async def generate_catchy_title(
    llm,
    article_title: str,
    article_summary: str,
    content_type: str = "daily_update"
) -> str:
    """Generate YouTube-optimized catchy title."""
    style_prompts = {
        "daily_update": "Create a catchy, broad-appeal title with curiosity gap",
        "big_tech": "Create an analytical, detailed title for tech professionals",
        "leader_quote": "Create an inspirational title highlighting the leader's wisdom",
        "arxiv_paper": "Create a clear, educational title explaining the research"
    }
    
    prompt = f"""{style_prompts.get(content_type, style_prompts['daily_update'])}

Original: {article_title}
Summary: {article_summary}

Requirements:
- 100 characters max
- Include 1-2 relevant emoji
- Accurate (no clickbait)
- Engaging hook

Return ONLY the title."""
    
    try:
        title = await llm.generate_text(prompt, max_tokens=50)
        title = title.strip().replace('"', '').replace("'", "")
        return title[:100]
    except Exception as e:
        logger.error(f"Error generating catchy title: {e}")
        return article_title[:100]


async def generate_hashtags(
    llm,
    article_title: str,
    content_type: str = "daily_update",
    max_tags: int = 5
) -> List[str]:
    """Generate relevant hashtags."""
    prompt = f"""Generate {max_tags} relevant hashtags for this video:
Title: {article_title}
Category: {content_type}

Requirements:
- Mix of popular and niche tags
- Relevant to content
- No spaces (e.g., #AINews not #AI News)

Return as comma-separated list."""
    
    try:
        response = await llm.generate_text(prompt, max_tokens=100)
        tags = [tag.strip() for tag in response.replace('#', '').split(',')]
        return ['#' + tag for tag in tags[:max_tags]]
    except Exception as e:
        logger.error(f"Error generating hashtags: {e}")
        return ["#AI", "#ArtificialIntelligence", "#TechNews"]


def generate_video_description(
    script: Script,
    article: Article,
    catchy_title: str,
    hashtags: List[str]
) -> str:
    """Generate YouTube description."""
    description = f"{catchy_title}\n\n"
    description += f"{article.summary or article.description}\n\n"
    description += f"🔗 Read more: {article.url}\n\n"
    
    if script.scenes:
        description += "📌 Timestamps:\n"
        for i, scene in enumerate(script.scenes, 1):
            start_time = scene.get('start_time', (i-1) * 15)
            minutes = int(start_time // 60)
            seconds = int(start_time % 60)
            timestamp = f"{minutes}:{seconds:02d}"
            description += f"{timestamp} - Scene {i}\n"
        description += "\n"
    
    description += f"{' '.join(hashtags)}\n\n"
    description += """📺 Subscribe for daily AI news!
🔔 Turn on notifications!
💬 Comment your thoughts below!

#AI #ArtificialIntelligence #TechNews"""
    
    return description
