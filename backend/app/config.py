"""
Configuration management using Pydantic Settings.
All settings loaded from environment variables (.env file).
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # === API Keys ===
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    google_cloud_project_id: str = Field(default="", alias="GOOGLE_CLOUD_PROJECT_ID")
    elevenlabs_api_key: str = Field(default="", alias="ELEVENLABS_API_KEY")
    pexels_api_key: str = Field(default="", alias="PEXELS_API_KEY")
    newsapi_key: str = Field(default="", alias="NEWSAPI_KEY")
    
    # === Database ===
    database_url: str = Field(default="sqlite:///./data/app.db", alias="DATABASE_URL")
    
    # === Defaults ===
    default_llm_provider: Literal["gemini", "openai", "claude"] = Field(
        default="gemini", 
        alias="DEFAULT_LLM_PROVIDER"
    )
    default_tts_provider: Literal["google", "openai", "elevenlabs"] = Field(
        default="openai",
        alias="DEFAULT_TTS_PROVIDER"
    )
    
    # === Application ===
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # === Video Settings ===
    video_format: Literal["vertical", "horizontal"] = Field(
        default="vertical",
        alias="VIDEO_FORMAT"
    )
    video_resolution: str = Field(default="1080x1920", alias="VIDEO_RESOLUTION")
    video_fps: int = Field(default=30, alias="VIDEO_FPS")
    
    # === Cost Limits ===
    monthly_budget_limit: float = Field(default=10.0, alias="MONTHLY_BUDGET_LIMIT")
    daily_video_limit: int = Field(default=5, alias="DAILY_VIDEO_LIMIT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"  # Allow extra fields in .env


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings (for dependency injection)."""
    return settings
