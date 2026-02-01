from typing import List, Optional
from pydantic import BaseModel, Field

class Scene(BaseModel):
    scene_number: int = Field(..., description="The sequential number of the scene")
    text: str = Field(..., description="The spoken narration for this scene")
    visual_cues: str = Field(..., description="Description of visuals to show during this scene")
    image_keywords: List[str] = Field(..., description="List of specific keywords for image search (e.g., 'Google HQ', 'Sundar Pichai', 'coding')")

class ScriptOutput(BaseModel):
    hook: str = Field(..., description="An attention-grabbing opening sentence (0-5 seconds)")
    scenes: List[Scene] = Field(..., description="List of script scenes")
    call_to_action: str = Field(..., description="Closing call to action (last 5-10 seconds)")
    title_suggestion: str = Field(..., description="A catchy title for the video")
    estimated_duration_seconds: int = Field(..., description="Estimated duration based on word count")
