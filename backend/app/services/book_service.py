"""
Book service for searching and analyzing books.

Uses Open Library API (primary) and Google Books API (fallback) to fetch book data,
then uses LLM to generate key takeaways and suggested video angles.
"""

import logging
import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models import BookSource, Article
from app.services.provider_factory import ProviderFactory, LLMProvider
from app.prompts import build_book_analysis_prompt
from app.utils.llm_helpers import parse_llm_json

logger = logging.getLogger(__name__)

# API endpoints
OPEN_LIBRARY_SEARCH = "https://openlibrary.org/search.json"
OPEN_LIBRARY_WORKS = "https://openlibrary.org"
GOOGLE_BOOKS_SEARCH = "https://www.googleapis.com/books/v1/volumes"


class BookService:
    """Service for searching books and generating review content."""
    
    def __init__(self, db: Session, google_books_api_key: Optional[str] = None):
        """
        Initialize book service.
        
        Args:
            db: Database session
            google_books_api_key: Optional Google Books API key for fallback
        """
        self.db = db
        self.google_books_api_key = google_books_api_key
        self.llm_provider = ProviderFactory.create_llm_provider(LLMProvider.GEMINI)
    
    async def search_books(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for books using Open Library API.
        
        Args:
            query: Search query (title, author, or both)
            limit: Maximum number of results
            
        Returns:
            List of book search results
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Search Open Library first
                response = await client.get(
                    OPEN_LIBRARY_SEARCH,
                    params={
                        "q": query,
                        "limit": limit,
                        "fields": "key,title,author_name,first_publish_year,subject,cover_i,number_of_pages_median"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                results = []
                for doc in data.get("docs", [])[:limit]:
                    # Build cover URL if available
                    cover_url = None
                    if doc.get("cover_i"):
                        cover_url = f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-M.jpg"
                    
                    results.append({
                        "open_library_key": doc.get("key", ""),
                        "title": doc.get("title", "Unknown"),
                        "author": ", ".join(doc.get("author_name", ["Unknown"])),
                        "first_publish_year": doc.get("first_publish_year"),
                        "subjects": doc.get("subject", [])[:10],  # Limit subjects
                        "cover_url": cover_url,
                        "page_count": doc.get("number_of_pages_median")
                    })
                
                logger.info(f"Found {len(results)} books for query: {query}")
                return results
                
        except Exception as e:
            logger.error(f"Error searching Open Library: {e}")
            # Try Google Books fallback if we have API key
            if self.google_books_api_key:
                return await self._search_google_books(query, limit)
            raise
    
    async def _search_google_books(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fallback search using Google Books API."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    GOOGLE_BOOKS_SEARCH,
                    params={
                        "q": query,
                        "maxResults": limit,
                        "key": self.google_books_api_key
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("items", []):
                    info = item.get("volumeInfo", {})
                    results.append({
                        "open_library_key": f"google:{item.get('id', '')}",
                        "google_books_id": item.get("id"),
                        "title": info.get("title", "Unknown"),
                        "author": ", ".join(info.get("authors", ["Unknown"])),
                        "first_publish_year": int(info.get("publishedDate", "0")[:4]) if info.get("publishedDate") else None,
                        "subjects": info.get("categories", []),
                        "cover_url": info.get("imageLinks", {}).get("thumbnail"),
                        "page_count": info.get("pageCount"),
                        "description": info.get("description")
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Error searching Google Books: {e}")
            return []
    
    async def get_book_details(self, open_library_key: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed book information from Open Library.
        
        Args:
            open_library_key: Open Library work key (e.g., "/works/OL123W")
            
        Returns:
            Book details dict or None
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Fetch work details
                response = await client.get(f"{OPEN_LIBRARY_WORKS}{open_library_key}.json")
                response.raise_for_status()
                work = response.json()
                
                # Extract description
                description = work.get("description")
                if isinstance(description, dict):
                    description = description.get("value", "")
                
                return {
                    "open_library_key": open_library_key,
                    "title": work.get("title", "Unknown"),
                    "description": description,
                    "subjects": [s.get("name") if isinstance(s, dict) else s for s in work.get("subjects", [])][:15],
                    "first_publish_date": work.get("first_publish_date")
                }
                
        except Exception as e:
            logger.error(f"Error fetching book details: {e}")
            return None
    
    async def get_or_create_book(self, book_data: Dict[str, Any]) -> BookSource:
        """
        Get existing book source or create new one.
        
        Args:
            book_data: Book data from search results
            
        Returns:
            BookSource model instance
        """
        # Check if book already exists
        existing = self.db.query(BookSource).filter(
            BookSource.open_library_key == book_data["open_library_key"]
        ).first()
        
        if existing:
            return existing
        
        # Fetch additional details if we have a valid Open Library key
        if not book_data["open_library_key"].startswith("google:"):
            details = await self.get_book_details(book_data["open_library_key"])
            if details:
                book_data["description"] = details.get("description") or book_data.get("description")
                book_data["subjects"] = details.get("subjects") or book_data.get("subjects")
        
        # Create new book source
        book = BookSource(
            open_library_key=book_data["open_library_key"],
            google_books_id=book_data.get("google_books_id"),
            title=book_data["title"],
            author=book_data.get("author"),
            first_publish_year=book_data.get("first_publish_year"),
            description=book_data.get("description"),
            subjects=book_data.get("subjects"),
            cover_url=book_data.get("cover_url"),
            page_count=book_data.get("page_count")
        )
        
        self.db.add(book)
        self.db.commit()
        self.db.refresh(book)
        
        logger.info(f"Created book source: {book.title}")
        return book
    
    async def analyze_book(self, book_id: int) -> BookSource:
        """
        Analyze a book using LLM to generate key takeaways and video angles.
        
        Args:
            book_id: BookSource ID
            
        Returns:
            Updated BookSource with analysis
        """
        book = self.db.query(BookSource).filter(BookSource.id == book_id).first()
        if not book:
            raise ValueError(f"Book not found: {book_id}")
        
        # Update status
        book.analysis_status = "analyzing"
        self.db.commit()
        
        try:
            # Build analysis prompt
            prompt = build_book_analysis_prompt({
                "title": book.title,
                "author": book.author or "Unknown",
                "description": book.description or "No description available",
                "subjects": book.subjects or [],
                "first_publish_year": book.first_publish_year
            })
            
            # Get LLM analysis
            response = await self.llm_provider.generate_text(prompt)
            
            # Parse the JSON response
            try:
                analysis = parse_llm_json(response, strict=True)
                
                book.key_takeaways = analysis.get("key_takeaways", [])
                book.suggested_angles = analysis.get("suggested_angles", [])
                book.analysis_status = "completed"
                book.analyzed_at = datetime.now(timezone.utc)
                
            except (ValueError, Exception) as e:
                logger.error(f"Failed to parse LLM response: {e}")
                book.error_message = f"Failed to parse analysis: {e}"
                book.analysis_status = "failed"
            
            self.db.commit()
            self.db.refresh(book)
            
            logger.info(f"Analyzed book: {book.title} - {len(book.key_takeaways or [])} takeaways")
            return book
            
        except Exception as e:
            logger.error(f"Error analyzing book: {e}")
            book.analysis_status = "failed"
            book.error_message = str(e)
            self.db.commit()
            raise
    
    async def create_article_from_book(
        self,
        book_id: int,
        angle_index: int = 0,
        custom_angle: Optional[str] = None
    ) -> Article:
        """
        Create an Article from a book for the video pipeline.
        
        Args:
            book_id: BookSource ID
            angle_index: Index of suggested angle to use
            custom_angle: Optional custom angle override
            
        Returns:
            Created Article
        """
        book = self.db.query(BookSource).filter(BookSource.id == book_id).first()
        if not book:
            raise ValueError(f"Book not found: {book_id}")
        
        if book.analysis_status != "completed":
            raise ValueError("Book has not been analyzed yet")
        
        # Determine video angle/title
        if custom_angle:
            video_title = custom_angle
        elif book.suggested_angles and angle_index < len(book.suggested_angles):
            video_title = book.suggested_angles[angle_index]
        else:
            video_title = f"Book Review: {book.title}"
        
        # Generate unique URL for the article
        import hashlib
        unique_hash = hashlib.md5(f"{book.id}:{video_title}:{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:8]
        article_url = f"book://{book.open_library_key}/{unique_hash}"
        
        # Build rich content from book data for script generation
        content_parts = [
            f"# {book.title}",
            f"**Author**: {book.author or 'Unknown'}",
            f"**Published**: {book.first_publish_year or 'Unknown'}",
            "",
            "## Description",
            book.description or "No description available.",
            "",
        ]
        
        if book.subjects:
            content_parts.append(f"**Subjects**: {', '.join(book.subjects[:10])}")
            content_parts.append("")
        
        content_parts.append("## Key Takeaways")
        for i, takeaway in enumerate(book.key_takeaways or [], 1):
            if isinstance(takeaway, dict):
                point = takeaway.get("point", str(takeaway))
                hook = takeaway.get("hook", "")
                score = takeaway.get("viral_score", 0)
                content_parts.append(f"{i}. **{point}**")
                if hook:
                    content_parts.append(f"   Hook: \"{hook}\" (Viral Score: {score}/10)")
            else:
                content_parts.append(f"{i}. {str(takeaway)}")
        
        content = "\n".join(content_parts)
        
        # Create article
        article = Article(
            book_source_id=book.id,
            title=video_title,
            url=article_url,
            author=book.author,
            description=f"Book review video for: {book.title}",
            content=content,
            suggested_content_type="book_review",
            key_topics=book.subjects[:5] if book.subjects else [],
            why_interesting=f"Engaging book summary of {book.title} with actionable insights",
            is_selected=True,
            selected_at=datetime.now(timezone.utc)
        )
        
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)
        
        logger.info(f"Created article from book: {article.title}")
        return article
    
    def get_book_by_id(self, book_id: int) -> Optional[BookSource]:
        """Get a book by ID."""
        return self.db.query(BookSource).filter(BookSource.id == book_id).first()
    
    def get_all_books(self, limit: int = 50) -> List[BookSource]:
        """Get all analyzed books."""
        return self.db.query(BookSource).order_by(
            BookSource.created_at.desc()
        ).limit(limit).all()

    async def prepare_book_assets(self, book_id: int) -> Dict[str, str]:
        """
        Prepare assets for a book video.
        
        Creates a dedicated project folder: data/projects/{book_id}_{sanitized_title}/images/
        Downloads the high-res cover to this folder.
        
        Returns:
            Dict containing 'project_folder' and 'assets'
        """
        import re
        from pathlib import Path
        import shutil
        
        book = self.get_book_by_id(book_id)
        if not book:
            raise ValueError(f"Book {book_id} not found")
        
        # 1. Sanitize title for folder name
        # Remove special chars, spaces to underscores, lowercase
        sanitized_title = re.sub(r'[^\w\s-]', '', book.title).strip().lower()
        sanitized_title = re.sub(r'[-\s]+', '_', sanitized_title)
        
        # 2. Create project structure
        # backend/data/projects/{id}_{title}/images
        base_dir = Path("data/projects")
        project_dir = base_dir / f"{book.id}_{sanitized_title}"
        images_dir = project_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        assets = []
        cover_path = images_dir / "cover.jpg"
        
        # 3. Download Cover (if not exists or empty)
        if not cover_path.exists() or cover_path.stat().st_size < 1000:
            if book.cover_url:
                try:
                    async with httpx.AsyncClient() as client:
                        # Try Large size first
                        # OpenLibrary format: ...-M.jpg -> ...-L.jpg
                        large_url = book.cover_url.replace("-M.jpg", "-L.jpg").replace("-S.jpg", "-L.jpg")
                        logger.info(f"Downloading cover from: {large_url}")
                        
                        resp = await client.get(large_url, follow_redirects=True, timeout=10.0)
                        if resp.status_code == 200 and len(resp.content) > 1000:
                            cover_path.write_bytes(resp.content)
                            logger.info(f"Downloaded Large cover to {cover_path}")
                        else:
                            # Fallback to original URL
                            logger.info(f"Large cover failed, trying original: {book.cover_url}")
                            resp = await client.get(book.cover_url, follow_redirects=True, timeout=10.0)
                            if resp.status_code == 200:
                                cover_path.write_bytes(resp.content)
                                logger.info(f"Downloaded original cover to {cover_path}")
                except Exception as e:
                    logger.error(f"Failed to download cover: {e}")
        
        if cover_path.exists():
            # Return relative path for frontend serving if we had static mount (but we use backend API usually)
            # For now return absolute path string for backend services
            assets.append(str(cover_path.absolute()))
            
        return {
            "project_folder": str(project_dir.absolute()),
            "cover_image": str(cover_path.absolute()) if cover_path.exists() else None,
            "assets": assets
        }
