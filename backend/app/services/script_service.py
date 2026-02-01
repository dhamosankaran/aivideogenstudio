"""
Script generation service with validation.

Converts analyzed articles into engaging 45-60 second YouTube Shorts scripts.
"""

import re
import logging
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import SessionLocal

from app.models import Article, Script
from app.services.base_provider import BaseLLMProvider
from app.services.provider_factory import ProviderFactory, LLMProvider
from app.prompts import build_script_generation_prompt

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of script validation."""
    def __init__(self, is_valid: bool, errors: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []


class ScriptService:
    """Service for generating and validating video scripts."""
    
    # Words per second for duration estimation (average speaking rate)
    WORDS_PER_SECOND = 2.5
    
    # Length targets (optimized for YouTube Shorts algorithm: 45-60s)
    MIN_WORDS = 180
    MAX_WORDS = 250
    MIN_DURATION = 45  # seconds
    MAX_DURATION = 60  # seconds
    
    def __init__(
        self,
        db: Session,
        llm_provider: Optional[BaseLLMProvider] = None
    ):
        """
        Initialize script service.
        
        Args:
            db: Database session
            llm_provider: Optional LLM provider (defaults to Gemini)
        """
        self.db = db
        self.llm = llm_provider or ProviderFactory.create_llm_provider(
            provider=LLMProvider.GEMINI
        )
    
    async def generate_script(
        self,
        article: Article,
        style: str = "engaging",
        target_duration: int = 50  # Optimized for Shorts (45-60s)
    ) -> Script:
        """
        Generate a video script from an article.
        
        Args:
            article: Article to generate script from
            style: Script style (engaging, casual, formal)
            target_duration: Target duration in seconds
            
        Returns:
            Created Script instance
        """
        from app.schemas.script_generation import ScriptOutput
        
        logger.info(f"Generating scene-based script for article {article.id} in {style} style")
        
        try:
            # Build scene-based prompt
            prompt = build_script_generation_prompt(
                article_title=article.title,
                article_summary=article.summary or article.description or "",
                key_points=article.key_points or [],
                style=style,
                target_duration=target_duration,
                scene_based=True
            )
            
            # Use Gemini's native JSON mode if available (provider check is implicit via kwargs support)
            # We pass the schema to the provider which supports 'response_schema' in generation_config
            response_text = await self.llm.generate_text(
                prompt=prompt,
                temperature=0.7,
                max_tokens=8000,
                # Gemini-specific: enforce JSON response matching the schema
                response_mime_type="application/json",
                response_schema=ScriptOutput
            )
            
            # Validate with Pydantic (robust parsing)
            try:
                script_data = ScriptOutput.model_validate_json(response_text)
            except Exception as e:
                logger.error(f"JSON Validation failed: {e}. Raw response: {response_text[:200]}...")
                # Fallback: Try regex if strict parsing failed (though unlikely with response_schema)
                import re
                import json
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    script_data = ScriptOutput.model_validate_json(json_match.group(0))
                else:
                    raise ValueError(f"Failed to parse script JSON: {e}")

            scenes_data = [
                {
                    "scene_number": s.scene_number,
                    "text": s.text,
                    "visual_cues": s.visual_cues,
                    "image_keywords": s.image_keywords
                } for s in script_data.scenes
            ]
            
            # Build raw script for display/review
            raw_script = f"[HOOK]\n{script_data.hook}\n\n"
            for scene in script_data.scenes:
                raw_script += f"[SCENE {scene.scene_number}]\n"
                raw_script += f"{scene.text}\n"
                if scene.visual_cues:
                    raw_script += f"[VISUAL: {scene.visual_cues}]\n"
                raw_script += "\n"
            raw_script += f"[CTA]\n{script_data.call_to_action}\n"
            
            # Format for TTS (just the narration text)
            formatted_parts = [script_data.hook]
            formatted_parts.extend([s.text for s in script_data.scenes])
            formatted_parts.append(script_data.call_to_action)
            formatted_script = " ".join(formatted_parts)
            
            # Calculate metadata
            word_count = self._count_words(formatted_script)
            estimated_duration = self.estimate_duration(formatted_script)
            
            # Validate
            validation = self.validate_script(formatted_script)
            
            # Calculate cost
            generation_cost = self.llm.estimate_cost(
                input_tokens=len(prompt.split()) * 1.3,
                output_tokens=len(response_text.split()) * 1.3
            )
            
            # Create script
            script = Script(
                article_id=article.id,
                raw_script=raw_script,
                formatted_script=formatted_script,
                scenes=scenes_data,
                word_count=word_count,
                estimated_duration=estimated_duration,
                llm_provider=self.llm.get_provider_name(),
                llm_model=self.llm.model,
                is_valid=validation.is_valid,
                validation_errors=validation.errors,
                style=style,
                has_hook=bool(script_data.hook),
                has_cta=bool(script_data.call_to_action),
                catchy_title=script_data.title_suggestion,
                status="generated",
                generation_cost=generation_cost
            )
            
            self.db.add(script)
            self.db.commit()
            self.db.refresh(script)
            
            logger.info(f"Generated structured script {script.id}: {len(scenes_data)} scenes, {word_count} words")
            return script
            
        except Exception as e:
            logger.error(f"Error generating script for article {article.id}: {str(e)}")
            raise
    
    async def generate_commentary_script(
        self,
        insight: dict,
        source_title: str,
        source_channel: str = "Unknown Channel",
        mode: str = "reaction",
        clip_duration: float = 30.0
    ) -> Dict:
        """
        Generate a commentary script for Mode A (Clip + Commentary) videos.
        
        The script is designed to be played AFTER showing the original clip,
        providing our unique perspective and added value.
        
        Args:
            insight: Insight dict from YouTubeSource.insights
            source_title: Title of the original YouTube video
            source_channel: Channel name of original video
            mode: Style of commentary (reaction, analysis, educational)
            clip_duration: Duration of the original clip in seconds
            
        Returns:
            Dict with script components for video generation
        """
        from app.schemas.script_generation import ScriptOutput
        
        logger.info(f"Generating commentary script for insight: {insight.get('summary', '')[:50]}...")
        
        # Calculate target commentary duration (30-45s to complement clip)
        target_commentary_duration = min(45, max(30, 90 - clip_duration))
        target_words = int(target_commentary_duration * self.WORDS_PER_SECOND)
        
        # Build prompt for commentary generation
        prompt = self._build_commentary_prompt(
            insight=insight,
            source_title=source_title,
            source_channel=source_channel,
            mode=mode,
            target_words=target_words,
            clip_duration=clip_duration
        )
        
        try:
            response_text = await self.llm.generate_text(
                prompt=prompt,
                temperature=0.8,
                max_tokens=2000,
                response_mime_type="application/json",
                response_schema=ScriptOutput
            )
            
            script_data = ScriptOutput.model_validate_json(response_text)
            
            # Build scenes for video rendering
            scenes_data = [
                {
                    "scene_number": s.scene_number,
                    "text": s.text,
                    "visual_cues": s.visual_cues or "Show engaging visuals",
                    "image_keywords": s.image_keywords or ["technology", "innovation"]
                } for s in script_data.scenes
            ]
            
            # Build formatted script for TTS
            formatted_parts = [script_data.hook]
            formatted_parts.extend([s.text for s in script_data.scenes])
            formatted_parts.append(script_data.call_to_action)
            formatted_script = " ".join(formatted_parts)
            
            word_count = self._count_words(formatted_script)
            estimated_duration = self.estimate_duration(formatted_script)
            
            logger.info(f"Generated commentary script: {len(scenes_data)} scenes, {word_count} words, ~{estimated_duration:.0f}s")
            
            return {
                "hook": script_data.hook,
                "scenes": scenes_data,
                "call_to_action": script_data.call_to_action,
                "title_suggestion": script_data.title_suggestion,
                "formatted_script": formatted_script,
                "word_count": word_count,
                "estimated_duration": estimated_duration,
                "source_attribution": f"Reacting to: {source_title} by {source_channel}"
            }
            
        except Exception as e:
            logger.error(f"Error generating commentary script: {str(e)}")
            raise
    
    def _build_commentary_prompt(
        self,
        insight: dict,
        source_title: str,
        source_channel: str,
        mode: str,
        target_words: int,
        clip_duration: float
    ) -> str:
        """Build the LLM prompt for commentary script generation."""
        mode_instructions = {
            "reaction": """
You're creating a REACTION video where you add your perspective after showing a clip.
- React genuinely to what was said
- Add your own insights and opinions  
- Create a conversation with the viewer about this topic
- Be engaging and personality-driven""",
            "analysis": """
You're creating an ANALYSIS video where you break down the content after showing a clip.
- Provide deeper context and background
- Explain implications and consequences
- Connect to broader trends
- Be informative and educational""",
            "educational": """
You're creating an EDUCATIONAL video where you expand on the topic after showing a clip.
- Explain any technical concepts simply
- Add examples and analogies
- Share additional facts and research
- Make it accessible to all viewers"""
        }
        
        return f'''Generate a commentary script for a YouTube Shorts "react" video.

VIDEO STRUCTURE:
1. Brief intro (3 seconds) - hook the viewer
2. [ORIGINAL CLIP PLAYS HERE - {clip_duration:.0f} seconds]
3. Your commentary (this is what you're writing - ~{target_words} words)
4. Call to action (3 seconds)

ORIGINAL VIDEO CONTEXT:
- Title: "{source_title}"
- Channel: {source_channel}
- Clip Summary: {insight.get('summary', 'Key insight from video')}
- Key Points from clip:
{chr(10).join(f"  • {p}" for p in insight.get('key_points', ['Interesting point']))}

COMMENTARY STYLE: {mode.upper()}
{mode_instructions.get(mode, mode_instructions['reaction'])}

YOUR TASK:
Write ONLY the commentary that plays AFTER the clip. Structure it as:
1. **Hook** (played BEFORE clip): 5-7 words to grab attention. Something like "Wait until you hear this..." or "This changes everything..."
2. **Scene 1**: Your initial reaction/take (2-3 sentences)
3. **Scene 2**: Your deeper insight or added value (2-3 sentences)  
4. **Scene 3**: What this means for viewers (1-2 sentences)
5. **CTA**: Engaging call to action

REQUIREMENTS:
- First person perspective (I, we, you)
- Conversational and authentic tone
- Total commentary: ~{target_words} words
- Don't repeat what the clip already says
- Add VALUE - give viewers a reason to follow you

Return JSON with this structure:
{{
  "hook": "<5-7 word attention-grabber played before clip>",
  "scenes": [
    {{"scene_number": 1, "text": "<your reaction>", "visual_cues": "<what to show>", "image_keywords": ["keyword1", "keyword2"]}},
    {{"scene_number": 2, "text": "<your insight>", "visual_cues": "<what to show>", "image_keywords": ["keyword1", "keyword2"]}},
    {{"scene_number": 3, "text": "<takeaway>", "visual_cues": "<what to show>", "image_keywords": ["keyword1", "keyword2"]}}
  ],
  "call_to_action": "<engaging CTA>",
  "title_suggestion": "<catchy title for the video>"
}}'''


    
    def validate_script(self, script: str) -> ValidationResult:
        """
        Validate a script against quality criteria.
        
        Args:
            script: Script text to validate
            
        Returns:
            ValidationResult with errors if invalid
        """
        errors = []
        
        # Check word count
        word_count = self._count_words(script)
        if word_count < self.MIN_WORDS:
            errors.append(f"Script too short: {word_count} words (min {self.MIN_WORDS})")
        elif word_count > self.MAX_WORDS:
            errors.append(f"Script too long: {word_count} words (max {self.MAX_WORDS})")
        
        # Check duration
        duration = self.estimate_duration(script)
        if duration < self.MIN_DURATION:
            errors.append(f"Duration too short: {duration:.1f}s (min {self.MIN_DURATION}s)")
        elif duration > self.MAX_DURATION:
            errors.append(f"Duration too long: {duration:.1f}s (max {self.MAX_DURATION}s)")
        
        # Check structure
        required_sections = ["[HOOK]", "[CONTEXT]", "[MAIN POINTS]", "[WRAP-UP]", "[CTA]"]
        missing_sections = [s for s in required_sections if s not in script]
        if missing_sections:
            errors.append(f"Missing sections: {', '.join(missing_sections)}")
        
        # Check for TTS issues
        if "http://" in script or "https://" in script:
            errors.append("Contains URLs (not TTS-friendly)")
        
        # Check sentence length (rough)
        sentences = re.split(r'[.!?]', script)
        long_sentences = [s for s in sentences if len(s.split()) > 25]
        if len(long_sentences) > 3:
            errors.append(f"Contains {len(long_sentences)} very long sentences (may be hard to follow)")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    def estimate_duration(self, script: str) -> float:
        """
        Estimate duration in seconds based on word count.
        
        Args:
            script: Script text
            
        Returns:
            Estimated duration in seconds
        """
        # Remove section markers for accurate word count
        clean_script = re.sub(r'\[.*?\]', '', script)
        word_count = self._count_words(clean_script)
        return word_count / self.WORDS_PER_SECOND
    
    def format_for_tts(self, script: str) -> str:
        """
        Format script for TTS by removing visual cues and section markers.
        
        Args:
            script: Raw script with markers
            
        Returns:
            Cleaned script ready for TTS
        """
        # Remove section markers
        formatted = re.sub(r'\[HOOK\]\s*', '', script)
        formatted = re.sub(r'\[CONTEXT\]\s*', '', formatted)
        formatted = re.sub(r'\[MAIN POINTS\]\s*', '', formatted)
        formatted = re.sub(r'\[WRAP-UP\]\s*', '', formatted)
        formatted = re.sub(r'\[CTA\]\s*', '', formatted)
        
        # Remove visual cues but keep the text flow
        formatted = re.sub(r'\[Show .*?\]', '', formatted)
        formatted = re.sub(r'\[Display .*?\]', '', formatted)
        formatted = re.sub(r'\[Cut to .*?\]', '', formatted)
        
        # Clean up extra whitespace
        formatted = re.sub(r'\n{3,}', '\n\n', formatted)
        formatted = formatted.strip()
        
        return formatted
    
    def _count_words(self, text: str) -> int:
        """Count words in text."""
        # Remove section markers and visual cues for accurate count
        clean_text = re.sub(r'\[.*?\]', '', text)
        return len(clean_text.split())
    
    def get_script(self, script_id: int) -> Optional[Script]:
        """Get script by ID."""
        return self.db.query(Script).filter(Script.id == script_id).first()
    
    def update_script(self, script_id: int, **kwargs) -> Optional[Script]:
        """Update script properties."""
        script = self.get_script(script_id)
        if not script:
            return None
        
        for key, value in kwargs.items():
            if hasattr(script, key):
                setattr(script, key, value)
        
        script.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(script)
        
        return script
    
    def approve_script(self, script_id: int) -> Optional[Script]:
        """Approve a script for video generation."""
        return self.update_script(script_id, status="approved")
    
    def reject_script(self, script_id: int, reason: str = None) -> Optional[Script]:
        """Reject a script."""
        updates = {"status": "rejected"}
        if reason:
            updates["validation_errors"] = [reason]
        return self.update_script(script_id, **updates)
    
    # Script Review Methods (Issue #016)
    
    def get_pending_scripts(self) -> List[Script]:
        """Get all scripts ready for review or video generation (pending or approved)."""
        from sqlalchemy.orm import joinedload
        from sqlalchemy import or_
        return self.db.query(Script).options(
            joinedload(Script.article)
        ).filter(
            or_(
                Script.script_status == "pending",
                Script.script_status == "approved"
            )
        ).order_by(Script.created_at.desc()).all()
    
    async def get_script_with_article(self, script_id: int) -> Optional[Dict]:
        """
        Get script with its source article for review.
        
        Returns:
            Dict with 'script', 'article', 'article_url', 'catchy_title', and 'scene_count' keys
        """
        script = self.get_script(script_id)
        if not script:
            return None
        
        article = self.db.query(Article).filter(Article.id == script.article_id).first()
        
        # Generate catchy title if not already present
        catchy_title = None
        if article:
            try:
                # Use LLM to generate catchy YouTube title
                prompt = f"""Generate a catchy, click-worthy YouTube title for this article.
                
Article Title: {article.title}
Article Summary: {article.description or article.summary or ''}

Requirements:
- Maximum 60 characters
- Engaging and attention-grabbing
- Include numbers or power words if relevant
- Optimized for YouTube algorithm

Return ONLY the title, nothing else."""

                catchy_title = await self.llm.generate_text(
                    prompt=prompt,
                    temperature=0.8,
                    max_tokens=50
                )
                catchy_title = catchy_title.strip().strip('"').strip("'")
            except Exception as e:
                logger.warning(f"Failed to generate catchy title: {str(e)}")
                catchy_title = article.title[:60]  # Fallback to truncated original title
        
        # Parse scenes from raw_script if scenes field is null
        scene_count = 0
        if script.scenes:
            scene_count = len(script.scenes)
        elif script.raw_script:
            # Count [SCENE X] markers in raw script
            import re
            scene_markers = re.findall(r'\[SCENE \d+\]', script.raw_script)
            scene_count = len(scene_markers)
        
        return {
            "script": script,
            "article": article,
            "article_url": article.url if article else None,
            "catchy_title": catchy_title,
            "scene_count": scene_count
        }
    
    def update_script_content(
        self,
        script_id: int,
        catchy_title: Optional[str] = None,
        scenes: Optional[List[Dict]] = None,
        content_type: Optional[str] = None,
        video_description: Optional[str] = None,
        hashtags: Optional[List[str]] = None
    ) -> Optional[Script]:
        """
        Update script content during review.
        
        Args:
            script_id: Script ID to update
            catchy_title: Updated title
            scenes: Updated scenes list
            content_type: Updated content type
            video_description: Updated description
            hashtags: Updated hashtags
            
        Returns:
            Updated Script or None if not found
        """
        script = self.get_script(script_id)
        if not script:
            return None
        
        if catchy_title is not None:
            script.catchy_title = catchy_title
        if scenes is not None:
            script.scenes = scenes
            # Rebuild formatted_script from scenes
            formatted_parts = [scene.get('text', '') for scene in scenes]
            script.formatted_script = " ".join(formatted_parts)
            script.word_count = self._count_words(script.formatted_script)
            script.estimated_duration = self.estimate_duration(script.formatted_script)
        if content_type is not None:
            script.content_type = content_type
        if video_description is not None:
            script.video_description = video_description
        if hashtags is not None:
            script.hashtags = hashtags
        
        script.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(script)
        
        return script
    
    def approve_script(self, script_id: int) -> Optional[Script]:
        """
        Approve script (does NOT generate video).
        
        Use generate_video_from_script() to create the video.
        
        Returns:
            Updated Script or None/error
        """
        script = self.get_script(script_id)
        if not script:
            return None
        
        # Update script status
        script.script_status = "approved"
        script.reviewed_at = datetime.utcnow()
        script.status = "approved"
        
        self.db.commit()
        self.db.refresh(script)
        
        return script
    
    async def initialize_video_generation(self, script_id: int) -> Dict:
        """
        Stage 1: Generate Audio and Create Video Record.
        Returns the created video object immediately.
        """
        from app.services.audio_service import AudioService
        from app.services.enhanced_video_service import EnhancedVideoCompositionService

        script = self.get_script(script_id)
        if not script:
            raise ValueError("Script not found")
        if script.status != "approved":
            raise ValueError(f"Script must be approved first. Current status: {script.status}")

        try:
            logger.info(f"Initializing video generation for script {script_id}")

            # 1. Generate Audio (Avg 2-5s)
            logger.info("Generating audio...")
            audio_service = AudioService(self.db)
            audio = await audio_service.generate_audio_from_script(
                script_id=script_id,
                tts_provider="google"
            )

            # 2. Create Video Task
            logger.info("Creating video record...")
            video_service = EnhancedVideoCompositionService(self.db)
            video = video_service.create_video_task(
                script_id=script_id,
                audio_id=audio.id,
                background_style="scenes"
            )
            
            # Commit to ensure it's visible to background task
            self.db.commit()
            self.db.refresh(video)
            
            return video
            
        except Exception as e:
            logger.error(f"Video initialization failed: {e}")
            raise

    def finalize_video_generation(self, video_id: int):
        """
        Stage 2: Render Video (Long Running Background Task).
        """
        # Create NEW session for background execution
        db = SessionLocal()
        try:
            from app.services.enhanced_video_service import EnhancedVideoCompositionService
            video_service = EnhancedVideoCompositionService(db)
            
            logger.info(f"Background: Starting render for video {video_id}")
            video_service.process_video(video_id)
            
        except Exception as e:
            logger.error(f"Background render failed for video {video_id}: {e}")
        finally:
            db.close()

# Removed standalone function as logic is now in class methods
