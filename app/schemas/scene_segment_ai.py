# app/schemas/scene_segment_ai.py

from pydantic import BaseModel, UUID4, Field
from typing import List, Optional, Dict, Any
from enum import Enum

from app.schemas.scene_segment import ComponentType, Component  # Import existing enum

class ScriptSceneGenerationRequestUser(BaseModel):
    script_id: UUID4


class SceneSegmentGenerationRequest(BaseModel):
    script_id: UUID4
    scene_description_id: UUID4
    story_synopsis: str
    genre: str
    arc_structure: str
    beat_position: int
    template_beat_title: str
    template_beat_definition: str
    story_specific_beat_title: str
    story_specific_beat_description: str
    scene_title: str  # Scene heading
    scene_description: str
    min_word_count: Optional[int] = 200
    previous_scenes: Optional[List[str]] = None

class ComponentTypeAI(str, Enum):
    HEADING = "HEADING"
    ACTION = "ACTION"
    DIALOGUE = "DIALOGUE"
    CHARACTER = "CHARACTER"
    TRANSITION = "TRANSITION"

class AISceneComponent(BaseModel):
    component_type: ComponentTypeAI
    position: float
    content: str
    character_name: Optional[str] = None
    parenthetical: Optional[str] = None
    # component_id : UUID4

class GeneratedSceneSegment(BaseModel):
    components: List[AISceneComponent]


class AISceneComponentResponse(BaseModel):
    component_type: ComponentTypeAI
    position: float
    content: str
    character_name: Optional[str] = None
    parenthetical: Optional[str] = None
    component_id : UUID4

class GeneratedSceneSegmentResponseResponse(BaseModel):
    components: List[AISceneComponentResponse]

class AISceneSegmentGenerationResponse(BaseModel):
    success: bool
    input_context: Optional[Dict[str, Any]] = None
    generated_segment: Optional[GeneratedSceneSegmentResponseResponse] = None
    fountain_text: Optional[str] = None
    error: Optional[str] = None
    scene_segment_id: Optional[UUID4] = None
    creation_method: str
    message: str

class AISceneGenerationResponse(BaseModel):
    success: bool
    input_context: Optional[dict] = None
    generated_segment: Optional[GeneratedSceneSegment] = None
    fountain_text: Optional[str] = None
    error: Optional[str] = None

class SceneSegmentGenerationResponse(BaseModel):
    success: bool
    input_context: Optional[Dict[str, Any]] = None
    generated_segment: Optional[GeneratedSceneSegment] = None
    fountain_text: Optional[str] = None
    error: Optional[str] = None
    scene_segment_id: Optional[UUID4] = None
    creation_method: str
    message: str

class ComponentCreate(BaseModel):
    component_type: ComponentTypeAI
    position: float
    content: str
    character_name: Optional[str] = None
    parenthetical: Optional[str] = None
    # id : UUID4

######################################################################################################################################################
######################################################################################################################################################
##### For Shorten Service
class ScriptShorten(BaseModel):
    shortened_text: str
    explanation: str

class ShorteningAlternativeType(str, Enum):
    CONCISE = "concise"
    DRAMATIC = "dramatic"
    MINIMAL = "minimal"
    POETIC = "poetic"
    HUMOROUS = "humorous"

class ShortenComponentResponse(BaseModel):
    component_id: UUID4
    original_text: str
    concise: ScriptShorten
    dramatic: ScriptShorten
    minimal: ScriptShorten
    poetic: ScriptShorten
    humorous: ScriptShorten



class ShortenerAlternative(BaseModel):
    shortened_text: str = Field(..., description="The shortened version of the original text")
    explanation: str = Field(..., description="Brief explanation of what was changed")

# class ShortenComponentResponse(BaseModel):
#     component: Component
#     alternatives: List[ShortenerAlternative]
#     original_text: str

class ApplyShortenedTextRequest(BaseModel):
    shortened_text: str = Field(..., description="The selected shortened text to apply")

class ApplyShortenedTextResponse(BaseModel):
    component: Component
    was_updated: bool
    was_recorded: bool
    message: str

######################################################################################################################################################
######################################################################################################################################################


######################################################################################################################################################
######################################################################################################################################################
##### For Rewrite Service
class RewriteAlternativeType(str, Enum):
    CONCISE = "concise"
    DRAMATIC = "dramatic"
    MINIMAL = "minimal"
    POETIC = "poetic"
    HUMOROUS = "humorous"

class ScriptRewrite(BaseModel):
    explanation: str = Field(..., description="Brief explanation of the changes and approach")
    rewritten_text: str = Field(..., description="The rewritten version of the original text")
    

class RewriteComponentResponse(BaseModel):
    component_id: UUID4
    original_text: str
    concise: ScriptRewrite
    dramatic: ScriptRewrite
    minimal: ScriptRewrite
    poetic: ScriptRewrite
    humorous: ScriptRewrite

class ApplyRewriteTextRequest(BaseModel):
    rewritten_text: str = Field(..., description="The selected rewritten text to apply")

class ApplyRewriteTextResponse(BaseModel):
    component: Component
    was_updated: bool
    was_recorded: bool
    message: str

class ScriptRewriteResponse(BaseModel):
    concise: ScriptRewrite = Field(..., description="A focused, efficient version that cuts unnecessary description")
    dramatic: ScriptRewrite = Field(..., description="A version with heightened tension and dramatic flair")
    minimal: ScriptRewrite = Field(..., description="A version using sparse prose focused only on essentials")
    poetic: ScriptRewrite = Field(..., description="A lyrical version with elegant language and vivid imagery")
    humorous: ScriptRewrite = Field(..., description="A version with subtle wit or comedic undertones")


######################################################################################################################################################
######################################################################################################################################################
##### For Expand Service
class ExpansionAlternativeType(str, Enum):
    CONCISE = "concise"
    DRAMATIC = "dramatic"
    MINIMAL = "minimal"
    POETIC = "poetic"
    HUMOROUS = "humorous"

class ScriptExpansion(BaseModel):
    explanation: str = Field(..., description="Brief explanation of what was expanded and how")
    expanded_text: str = Field(..., description="The expanded version of the original text")
    

class ScriptExpansionResponse(BaseModel):
    """
    Contains multiple themed expansion alternatives for a script component.
    """
    concise: ScriptExpansion = Field(..., description="A moderately expanded version that adds crucial details while remaining economical")
    dramatic: ScriptExpansion = Field(..., description="An expansion that heightens tension and emotional impact")
    minimal: ScriptExpansion = Field(..., description="A carefully expanded version that adds only the most essential elements")
    poetic: ScriptExpansion = Field(..., description="An expansion with rich imagery and sensory details")
    humorous: ScriptExpansion = Field(..., description="An expansion that introduces subtle humor while maintaining the scene's purpose")


class ExpandComponentResponse(BaseModel):
    component_id: UUID4
    original_text: str
    concise: ScriptExpansion
    dramatic: ScriptExpansion
    minimal: ScriptExpansion
    poetic: ScriptExpansion
    humorous: ScriptExpansion


class ApplyExpandedTextRequest(BaseModel):
    expanded_text: str = Field(..., description="The selected expanded text to apply")


class ApplyExpandedTextResponse(BaseModel):
    component: Component  # This will contain the updated component data
    was_updated: bool
    was_recorded: bool
    message: str



######################################################################################################################################################
######################################################################################################################################################
##### For Continue Service
class ContinuationAlternativeType(str, Enum):
    CONCISE = "concise"
    DRAMATIC = "dramatic"
    MINIMAL = "minimal"
    POETIC = "poetic" 
    HUMOROUS = "humorous"

class ScriptContinuation(BaseModel):
    """
    Represents a single continuation alternative with the continuation text and explanation.
    """
    explanation: str = Field(..., description="Brief explanation of the approach used for this continuation")
    continuation_text: str = Field(..., description="The text that continues the original content")
    

class ScriptContinuationResponse(BaseModel):
    """
    Contains multiple themed continuation alternatives for a script component.
    """
    concise: ScriptContinuation = Field(..., description="A brief, focused continuation that gets to the point")
    dramatic: ScriptContinuation = Field(..., description="A continuation with heightened tension or emotional impact")
    minimal: ScriptContinuation = Field(..., description="A sparse continuation with only essential elements")
    poetic: ScriptContinuation = Field(..., description="A lyrical continuation with rich imagery or metaphor")
    humorous: ScriptContinuation = Field(..., description="A continuation with wit, irony, or comedic elements")

class ContinueComponentResponse(BaseModel):
    """
    Response model for the continue component endpoint.
    """
    component_id: UUID4
    original_text: str
    concise: ScriptContinuation
    dramatic: ScriptContinuation
    minimal: ScriptContinuation
    poetic: ScriptContinuation
    humorous: ScriptContinuation

class ApplyContinuationRequest(BaseModel):
    """
    Request model for applying a selected continuation.
    """
    continuation_text: str = Field(..., description="The selected continuation text to apply")

class ApplyContinuationResponse(BaseModel):
    """
    Response model for the apply continuation endpoint.
    """
    component: Component  # This will contain the updated component data
    was_updated: bool
    was_recorded: bool
    message: str




class TransformationType(str, Enum):
    SHORTEN = "shorten"
    REWRITE = "rewrite"
    EXPAND = "expand"
    CONTINUE = "continue"

class TransformRequest(BaseModel):
    transform_type: TransformationType = Field(..., description="Type of transformation to apply")
    
class ApplyTransformRequest(BaseModel):
    transform_type: TransformationType = Field(..., description="Type of transformation that was applied")
    alternative_text: str = Field(..., description="The selected alternative text to apply")
