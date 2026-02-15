"""
YouTube Metadata Generation Service.

Uses LLM to generate SEO-optimized metadata for YouTube Shorts:
- Catchy titles with hook words
- SEO descriptions with hashtags
- Searchable tags for discoverability
- Book review–specific metadata with @60SecondBooks branding
"""

import logging
from typing import Dict, Optional, List
from pydantic import BaseModel, Field
from app.utils.llm_helpers import parse_llm_json
from app.prompts.metadata import build_metadata_prompt

logger = logging.getLogger(__name__)

# Hard-coded brand CTA — never omitted from book reviews
BOOK_REVIEW_CTA = "👉 Follow @60SecondBooks for daily book reviews in 60 seconds!"


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
        content_type: str = "daily_update",
        book_author: Optional[str] = None,
        takeaways: Optional[List[str]] = None,
    ) -> YouTubeMetadata:
        """
        Generate SEO-optimized YouTube metadata.
        
        Args:
            article_title: Original article title
            article_description: Article summary/description
            script_content: Optional script text for better context
            content_type: Type of content (daily_update, big_tech, book_review, etc)
            book_author: Author name (for book reviews)
            takeaways: Key takeaways list (for book reviews)
            
        Returns:
            YouTubeMetadata with title, description, hashtags, and tags
        """
        
        prompt = build_metadata_prompt(
            article_title=article_title,
            article_description=article_description,
            content_type=content_type,
            script_content=script_content,
            book_author=book_author,
            takeaways=takeaways,
        )

        try:
            response = await self.llm.generate_text(
                prompt=prompt,
                temperature=0.8,
                max_tokens=1000
            )
            
            # Parse JSON from response
            data = parse_llm_json(response, strict=True)
            
            # === Resilient parsing: coerce string fields to arrays ===
            data = self._normalize_list_fields(data)
            
            metadata = YouTubeMetadata(**data)
            
            # Ensure title length
            if len(metadata.title) > 100:
                metadata.title = metadata.title[:97] + "..."
            
            # === Hard-coded brand CTA for book reviews ===
            if content_type == "book_review":
                self._enforce_book_review_branding(metadata)
            
            logger.info(f"Generated metadata: {metadata.title[:50]}...")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to generate metadata: {e}")
            # Return content-type–aware fallback metadata
            fallback = self._build_fallback_metadata(
                article_title, article_description,
                content_type, book_author
            )
            return fallback
    
    def _build_fallback_metadata(
        self,
        article_title: str,
        article_description: str,
        content_type: str,
        book_author: Optional[str] = None,
    ) -> YouTubeMetadata:
        """Build niche-aware fallback when LLM times out or fails."""
        if content_type == "book_review":
            desc = (
                f"Book review and summary for {article_title}."
                f"\n\n{BOOK_REVIEW_CTA}"
                f"\n\n#Shorts #BookReview #Reading #BookSummary"
            )
            metadata = YouTubeMetadata(
                title=article_title[:100],
                description=desc,
                hashtags=["#Shorts", "#BookReview", "#Reading", "#BookSummary"],
                tags=self._build_fallback_tags(article_title, content_type, book_author),
            )
        else:
            metadata = YouTubeMetadata(
                title=article_title[:100],
                description=f"{article_description}\n\n#AI #Tech #News",
                hashtags=["#AI", "#Tech", "#News", "#Trending"],
                tags=self._build_fallback_tags(article_title, content_type, book_author),
            )
        return metadata
    
    def _normalize_list_fields(self, data: dict) -> dict:
        """Coerce tags/hashtags from comma-separated strings to proper arrays.
        
        LLMs sometimes return: "tags": "tag1, tag2, tag3" instead of ["tag1", "tag2", "tag3"]
        This normalizes both formats to a list.
        """
        for field in ("tags", "hashtags"):
            val = data.get(field)
            if isinstance(val, str):
                # Split by comma, strip whitespace, filter empties
                data[field] = [t.strip() for t in val.split(",") if t.strip()]
                logger.info(f"[SEO] Coerced '{field}' from string to list ({len(data[field])} items)")
        return data
    
    def _build_fallback_tags(
        self,
        article_title: str,
        content_type: str,
        book_author: Optional[str] = None,
    ) -> List[str]:
        """Build meaningful fallback tags from title + context (not just the first word)."""
        tags = []
        
        if content_type == "book_review":
            # Book-specific fallback
            tags.append(f"{article_title} summary")
            if book_author:
                tags.append(f"{book_author} books")
            tags.extend([
                "book review shorts",
                "60 second book review",
                "short book summary",
                article_title.lower(),
            ])
        else:
            # Generic fallback — use full title as first tag + common terms
            tags.append(article_title)
            tags.extend(["AI news", "tech news", "trending"])
        
        # Deduplicate while preserving order
        seen = set()
        unique_tags = []
        for t in tags:
            key = t.lower().strip()
            if key and key not in seen:
                seen.add(key)
                unique_tags.append(t.strip())
        
        return unique_tags

    def _enforce_book_review_branding(self, metadata: YouTubeMetadata):
        """Ensure @60SecondBooks CTA and #Shorts are always present."""
        # Guarantee CTA in description
        if BOOK_REVIEW_CTA not in metadata.description:
            metadata.description = metadata.description.rstrip() + f"\n\n{BOOK_REVIEW_CTA}"
        
        # Guarantee #Shorts is the first hashtag
        if "#Shorts" not in metadata.hashtags:
            metadata.hashtags.insert(0, "#Shorts")
        elif metadata.hashtags[0] != "#Shorts":
            metadata.hashtags.remove("#Shorts")
            metadata.hashtags.insert(0, "#Shorts")
        
        # Guarantee #BookReview is present
        if "#BookReview" not in metadata.hashtags:
            metadata.hashtags.insert(1, "#BookReview")


# Convenience function for testing
async def test_metadata_generation():
    """Test metadata generation."""
    service = MetadataGenerationService()
    
    # Test generic metadata
    result = await service.generate_metadata(
        article_title="Why Elon Musk wants to put AI data centres in space",
        article_description="Elon Musk believes space-based AI data centres can slash power and cooling costs.",
        content_type="big_tech"
    )
    
    print(f"=== Generic ===")
    print(f"Title: {result.title}")
    print(f"Description: {result.description}")
    print(f"Hashtags: {result.hashtags}")
    print(f"Tags: {result.tags}")
    
    # Test book review metadata
    result2 = await service.generate_metadata(
        article_title="Atomic Habits",
        article_description="A guide to building good habits and breaking bad ones.",
        content_type="book_review",
        book_author="James Clear",
        takeaways=["1% improvement compounds to 37x", "Focus on systems not goals", "4 laws of behavior change"],
    )
    
    print(f"\n=== Book Review ===")
    print(f"Title: {result2.title}")
    print(f"Description: {result2.description}")
    print(f"Hashtags: {result2.hashtags}")
    print(f"Tags: {result2.tags}")
    
    return result2


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_metadata_generation())
