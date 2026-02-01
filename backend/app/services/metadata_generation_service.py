"""
YouTube Metadata Generation Service.

Uses LLM to generate SEO-optimized metadata for YouTube Shorts:
- Catchy titles with hook words
- SEO descriptions with hashtags
- Searchable tags for discoverability
"""

import logging
from typing import Dict, Optional, List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class YouTubeMetadata(BaseModel):
    """Generated YouTube metadata."""
    title: str = Field(..., description="Catchy YouTube title (max 100 chars)")
    description: str = Field(..., description="SEO-optimized description with hashtags")
    hashtags: List[str] = Field(..., description="Relevant hashtags (5-10)")
    tags: List[str] = Field(..., description="Search tags for discoverability")


class MetadataGenerationService:
    """Service for generating YouTube-optimized metadata using LLM."""
    
    def __init__(self):
        """Initialize with LLM provider."""
        from app.services.provider_factory import ProviderFactory, LLMProvider
        self.llm = ProviderFactory.create_llm_provider(provider=LLMProvider.GEMINI)
    
    async def generate_metadata(
        self,
        article_title: str,
        article_description: str,
        script_content: Optional[str] = None,
        content_type: str = "daily_update"
    ) -> YouTubeMetadata:
        """
        Generate SEO-optimized YouTube metadata.
        
        Args:
            article_title: Original article title
            article_description: Article summary/description
            script_content: Optional script text for better context
            content_type: Type of content (daily_update, big_tech, leader_wisdom, etc)
            
        Returns:
            YouTubeMetadata with title, description, hashtags, and tags
        """
        
        prompt = f"""You are a YouTube SEO expert specializing in AI/Tech content for YouTube Shorts.

Generate optimized metadata for this video:

**Article Title**: {article_title}
**Description**: {article_description}
**Content Type**: {content_type}
{f"**Script Preview**: {script_content[:500]}..." if script_content else ""}

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

        try:
            response = await self.llm.generate_text(
                prompt=prompt,
                temperature=0.8,
                max_tokens=1000
            )
            
            # Parse JSON from response
            import json
            import re
            
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                metadata = YouTubeMetadata(**data)
            else:
                raise ValueError("No JSON found in response")
            
            # Ensure title length
            if len(metadata.title) > 100:
                metadata.title = metadata.title[:97] + "..."
            
            logger.info(f"Generated metadata: {metadata.title[:50]}...")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to generate metadata: {e}")
            # Return fallback metadata
            return YouTubeMetadata(
                title=article_title[:100],
                description=f"{article_description}\n\n#AI #Tech #News",
                hashtags=["#AI", "#Tech", "#News", "#Trending"],
                tags=[article_title.split()[0] if article_title else "AI"]
            )


# Convenience function for testing
async def test_metadata_generation():
    """Test metadata generation."""
    service = MetadataGenerationService()
    
    result = await service.generate_metadata(
        article_title="Why Elon Musk wants to put AI data centres in space",
        article_description="Elon Musk believes space-based AI data centres can slash power and cooling costs by using solar-powered satellites.",
        content_type="big_tech"
    )
    
    print(f"Title: {result.title}")
    print(f"Description: {result.description}")
    print(f"Hashtags: {result.hashtags}")
    print(f"Tags: {result.tags}")
    
    return result


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_metadata_generation())
