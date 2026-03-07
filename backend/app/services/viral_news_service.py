"""
Viral news service for discovering and analyzing trending news.

Uses existing NewsAPIService for source discovery and LLM for virality analysis.
Follows the same pattern as BookService.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models import ViralNewsSource, Article
from app.services.news_api_service import NewsAPIService
from app.services.base_provider import BaseLLMProvider
from app.services.provider_factory import ProviderFactory, LLMProvider
from app.utils.llm_helpers import parse_llm_json
from app.prompts import build_viral_news_analysis_prompt
from app.config import settings

logger = logging.getLogger(__name__)


class ViralNewsService:
    """Service for discovering trending news and generating viral video content."""

    def __init__(self, db: Session, llm_provider: Optional[BaseLLMProvider] = None):
        """
        Initialize viral news service.

        Args:
            db: Database session
            llm_provider: Optional LLM provider (lazy-initialized when needed)
        """
        self.db = db
        self._llm = llm_provider

    @property
    def llm(self) -> BaseLLMProvider:
        """Lazy-initialize LLM provider only when analysis is needed."""
        if self._llm is None:
            self._llm = ProviderFactory.create_llm_provider(LLMProvider.GEMINI)
        return self._llm

    # ── Discovery ───────────────────────────────────────────────

    def discover_trending(
        self,
        category: Optional[str] = None,
        query: Optional[str] = None,
        page_size: int = 15,
    ) -> List[Dict[str, Any]]:
        """
        Discover trending news articles using NewsAPI.

        Args:
            category: Filter by category (technology, business, etc.)
                      Extended categories (politics, elon_musk, humanoid) are
                      converted to search queries since NewsAPI only supports
                      7 standard categories.
            query: Optional search query for targeted discovery
            page_size: Number of results

        Returns:
            List of article dicts with headline, source, URL, etc.
        """
        # NewsAPI only supports these 7 categories for top-headlines
        NEWSAPI_CATEGORIES = {
            "business", "entertainment", "general", "health",
            "science", "sports", "technology",
        }

        # Extended categories → treated as search queries
        EXTENDED_CATEGORY_QUERIES = {
            "politics": "politics government policy election",
            "elon_musk": "Elon Musk Tesla SpaceX xAI",
            "humanoid": "humanoid robot robotics bipedal autonomous",
            "world": (
                "international global breaking news crisis conflict diplomacy "
                "war protest economy summit UN NATO G7 election foreign"
            ),
        }

        # China uses targeted sub-queries (single long query exceeds NewsAPI limits)
        CHINA_SUB_QUERIES = [
            "China Xi Jinping Beijing CCP policy",
            "China economy military Taiwan South China Sea",
            "Huawei China technology trade sanctions",
        ]

        try:
            service = NewsAPIService()
            articles = []

            # Normalize category — strip non-ascii (emoji) so '🌍 world' → 'world'
            raw_cat = (category or "").lower().strip()
            cat_key = "".join(c for c in raw_cat if c.isascii()).strip().replace(" ", "_")

            if cat_key == "world":
                # World strategy: 3 focused keyword searches covering different aspects
                # of global news (country top-headlines fail on NewsAPI free plan)
                world_sub_queries = [
                    f"{query} world crisis war conflict diplomacy" if query else "world crisis war conflict diplomacy ceasefire",
                    f"{query} international news global summit UN NATO" if query else "international news global summit UN NATO sanctions",
                    f"{query} breaking news foreign protest election coup" if query else "breaking news foreign protest election coup revolution",
                ]
                per_query = max(10, page_size)
                for sub_q in world_sub_queries:
                    try:
                        search_results = service.search_articles(
                            query=sub_q,
                            sort_by="publishedAt",
                            page_size=per_query,
                        )
                        articles.extend(search_results.get("articles", []))
                    except Exception as sub_err:
                        logger.warning(f"World sub-query failed [{sub_q[:40]}]: {sub_err}")

                logger.info(f"World category → fetched {len(articles)} raw articles from {len(world_sub_queries)} targeted searches")

            elif cat_key == "china":
                # China strategy: 3 focused sub-queries (single long query fails on NewsAPI)
                china_queries = [
                    f"{query} China Xi Jinping Beijing CCP policy" if query else CHINA_SUB_QUERIES[0],
                    f"{query} China economy military Taiwan" if query else CHINA_SUB_QUERIES[1],
                    f"{query} Huawei China technology trade" if query else CHINA_SUB_QUERIES[2],
                ]
                per_query = max(10, page_size)
                for sub_q in china_queries:
                    try:
                        search_results = service.search_articles(
                            query=sub_q,
                            sort_by="publishedAt",
                            page_size=per_query,
                        )
                        articles.extend(search_results.get("articles", []))
                    except Exception as sub_err:
                        logger.warning(f"China sub-query failed [{sub_q[:40]}]: {sub_err}")

                logger.info(f"China category → fetched {len(articles)} raw articles from {len(china_queries)} targeted searches")

            elif cat_key in EXTENDED_CATEGORY_QUERIES:
                # Other extended categories → use search query instead of category param
                search_query = EXTENDED_CATEGORY_QUERIES[cat_key]
                # Combine with user query if provided
                if query:
                    search_query = f"{search_query} {query}"
                search_results = service.search_articles(
                    query=search_query,
                    sort_by="publishedAt",
                    page_size=page_size,
                )
                articles.extend(search_results.get("articles", []))
                logger.info(f"Extended category '{cat_key}' → search query: '{search_query}'")

            else:  # Standard categories or bare query
                # Standard category or no category → use top-headlines
                api_category = cat_key if cat_key in NEWSAPI_CATEGORIES else None
                if category or not query:
                    headlines = service.get_top_headlines(
                        category=api_category,
                        page_size=page_size,
                    )
                    articles.extend(headlines.get("articles", []))

                # If a query is provided, also search for it
                if query:
                    search_results = service.search_articles(
                        query=query,
                        sort_by="popularity",
                        page_size=page_size,
                    )
                    articles.extend(search_results.get("articles", []))

            # Deduplicate by URL
            seen_urls = set()
            unique = []
            for a in articles:
                url = a.get("url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique.append(a)

            # Normalize to a consistent shape
            results = []
            for a in unique[:page_size]:
                results.append({
                    "title": a.get("title", ""),
                    "description": a.get("description", ""),
                    "url": a.get("url", ""),
                    "source_name": (a.get("source") or {}).get("name", "Unknown"),
                    "published_at": a.get("publishedAt"),
                    "image_url": a.get("urlToImage"),
                    "content_preview": (a.get("content") or "")[:3000],
                    "category": category or "general",
                })

            logger.info(f"Discovered {len(results)} trending articles (category={category})")
            return results

        except Exception as e:
            logger.error(f"Error discovering trending news: {e}")
            raise

    # ── Source management ────────────────────────────────────────

    def get_or_create_source(self, article_data: Dict[str, Any]) -> ViralNewsSource:
        """
        Get existing viral news source or create a new one.

        Args:
            article_data: Article data from discovery results

        Returns:
            ViralNewsSource model instance
        """
        url = article_data.get("url", "")

        # Check if already exists
        existing = (
            self.db.query(ViralNewsSource)
            .filter(ViralNewsSource.original_url == url)
            .first()
        )
        if existing:
            return existing

        # Parse published_at
        published_at = None
        raw_date = article_data.get("published_at")
        if raw_date:
            try:
                published_at = datetime.fromisoformat(
                    raw_date.replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                published_at = datetime.now(timezone.utc)

        source = ViralNewsSource(
            original_url=url,
            title=article_data.get("title", "")[:500],
            source_name=article_data.get("source_name"),
            published_at=published_at,
            description=article_data.get("description", "")[:2000],
            content_preview=article_data.get("content_preview", "")[:3000],
            image_url=article_data.get("image_url"),
            news_category=article_data.get("category"),
            analysis_status="pending",
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        logger.info(f"Created ViralNewsSource id={source.id}: {source.title[:80]}")
        return source

    # ── Analysis ────────────────────────────────────────────────

    async def analyze_virality(self, source_id: int) -> ViralNewsSource:
        """
        Analyze a news source for virality using LLM.

        Args:
            source_id: ViralNewsSource ID

        Returns:
            Updated ViralNewsSource with analysis results
        """
        source = self.db.query(ViralNewsSource).get(source_id)
        if not source:
            raise ValueError(f"ViralNewsSource {source_id} not found")

        source.analysis_status = "analyzing"
        self.db.commit()

        try:
            prompt = build_viral_news_analysis_prompt({
                "title": source.title,
                "source_name": source.source_name,
                "description": source.description,
                "content_preview": source.content_preview,
                "category": source.news_category,
                "published_at": str(source.published_at) if source.published_at else "Unknown",
            })

            response = await self.llm.generate_text(prompt)
            analysis = parse_llm_json(response)

            source.virality_score = float(analysis.get("virality_score", 5.0))
            source.virality_reasons = analysis.get("virality_reasons", [])
            source.suggested_angles = analysis.get("suggested_angles", [])
            source.key_facts = analysis.get("key_facts", [])
            source.target_audience = analysis.get("target_audience", "")
            source.emotional_hook = analysis.get("emotional_hook", "")
            source.analysis_status = "completed"
            source.analyzed_at = datetime.now(timezone.utc)

            self.db.commit()
            self.db.refresh(source)

            logger.info(
                f"Analyzed ViralNewsSource id={source.id}: "
                f"virality={source.virality_score}"
            )
            return source

        except Exception as e:
            source.analysis_status = "failed"
            source.error_message = str(e)[:1000]
            self.db.commit()
            logger.error(f"Virality analysis failed for source {source_id}: {e}")
            raise

    # ── Article creation (bridge to video pipeline) ─────────────

    async def create_article_from_source(
        self,
        source_id: int,
        angle_index: int = 0,
        custom_angle: Optional[str] = None,
    ) -> Article:
        """
        Create an Article from a viral news source for the video pipeline.

        Args:
            source_id: ViralNewsSource ID
            angle_index: Index of suggested angle to use
            custom_angle: Optional custom angle override

        Returns:
            Created Article
        """
        source = self.db.query(ViralNewsSource).get(source_id)
        if not source:
            raise ValueError(f"ViralNewsSource {source_id} not found")

        if source.analysis_status != "completed":
            raise ValueError("Source must be analyzed before creating an article")

        # Determine the video angle
        if custom_angle:
            angle = custom_angle
        elif source.suggested_angles and angle_index < len(source.suggested_angles):
            angle = source.suggested_angles[angle_index]
        else:
            angle = f"Viral: {source.title}"

        # Build key points from analysis
        key_points = []
        if source.key_facts:
            key_points = source.key_facts[:7]
        if source.virality_reasons:
            key_points.append(f"Viral because: {', '.join(source.virality_reasons[:3])}")

        # Build rich content for the script generator
        content_parts = []
        content_parts.append(f"HEADLINE: {source.title}")
        content_parts.append(f"SOURCE: {source.source_name or 'Unknown'}")
        if source.description:
            content_parts.append(f"SUMMARY: {source.description}")
        if source.content_preview:
            content_parts.append(f"DETAILS: {source.content_preview}")
        if source.virality_reasons:
            content_parts.append(
                f"WHY IT'S VIRAL: {'; '.join(source.virality_reasons)}"
            )
        if source.emotional_hook:
            content_parts.append(f"EMOTIONAL HOOK: {source.emotional_hook}")

        content = "\n\n".join(content_parts)

        # Create a unique URL for deduplication
        article_url = f"{source.original_url}#viral-angle-{angle_index}"

        # Check for existing article with same URL
        existing = self.db.query(Article).filter(Article.url == article_url).first()
        if existing:
            return existing

        article = Article(
            viral_news_source_id=source.id,
            title=angle[:500],
            url=article_url,
            author=source.source_name,
            published_at=source.published_at,
            description=source.description,
            content=content,
            summary=source.description,
            key_points=key_points,
            category=source.news_category,
            suggested_content_type="viral_news",
            is_processed=True,
            is_selected=True,
            analyzed_at=datetime.now(timezone.utc),
        )
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)

        logger.info(
            f"Created Article id={article.id} from ViralNewsSource id={source.id}"
        )
        return article

    # ── Queries ──────────────────────────────────────────────────

    def get_source_by_id(self, source_id: int) -> Optional[ViralNewsSource]:
        """Get a viral news source by ID."""
        return self.db.query(ViralNewsSource).get(source_id)

    def get_all_sources(
        self,
        limit: int = 50,
        status: Optional[str] = None,
    ) -> List[ViralNewsSource]:
        """Get all viral news sources, optionally filtered by status."""
        query = self.db.query(ViralNewsSource)
        if status:
            query = query.filter(ViralNewsSource.analysis_status == status)
        return (
            query.order_by(ViralNewsSource.created_at.desc())
            .limit(limit)
            .all()
        )
