from typing import List, Optional
from pydantic import BaseModel, Field

class Scene(BaseModel):
    scene_number: int = Field(..., description="The sequential number of the scene")
    text: str = Field(..., description="The spoken narration for this scene")
    visual_cues: Optional[str] = Field(default=None, description="Description of visuals to show during this scene")
    image_keywords: List[str] = Field(default_factory=list, description="List of specific keywords for image search (e.g., 'Google HQ', 'Sundar Pichai', 'coding')")
    duration_estimate: Optional[int] = Field(default=None, description="Estimated duration for this scene in seconds")
    visual_style: Optional[str] = Field(default=None, description="Visual style hint (tech_modern, corporate, etc.)")

class ScriptOutput(BaseModel):
    hook: str = Field(..., description="An attention-grabbing opening sentence (0-5 seconds)")
    scenes: List[Scene] = Field(..., description="List of script scenes")
    call_to_action: str = Field(..., description="Closing call to action (last 5-10 seconds)")
    title_suggestion: Optional[str] = Field(default=None, description="A catchy title for the video")
    estimated_duration_seconds: Optional[int] = Field(default=None, description="Estimated duration based on word count")

