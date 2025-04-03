# app/services/openai_service.py
import json
import logging
from enum import Enum
from typing import List, Generator, Dict, Any, Optional
from pydantic import BaseModel, Field
from instructor import from_openai, Mode
from openai import AzureOpenAI
from app.config import settings
import traceback


from app.schemas.scene_segment_ai import (GeneratedSceneSegment,
                                          ScriptRewriteResponse, 
                                          ScriptExpansion,
                                          ScriptExpansionResponse,
                                          ScriptContinuationResponse
                                          )


logger = logging.getLogger(__name__)


class ActEnum(str, Enum):
    act_1 = "act_1"
    act_2a = "act_2a"
    act_2b = "act_2b"
    act_3 = "act_3"


class Beat(BaseModel):
    beat_number: int
    beat_name: str
    beat_title: str
    description: str
    page_length: str
    timing: str
    act: ActEnum

class DialogueBlock(BaseModel):
    character_name: str
    dialogue: str
    parenthetical: str | None = None
    position: int

# class GeneratedScriptScene(BaseModel):
#     scene_heading: str
#     scene_description: str
#     dialogue_blocks: List[DialogueBlock] | None = None
#     estimated_duration: float

class GeneratedScene(BaseModel):
    scene_heading: str
    scene_description: str
    position: int

class ScriptRewrite(BaseModel):
    explanation: str = Field(..., description="How the script was refined for brevity and impact")
    shortened_text: str = Field(..., description="Concise version of the script segment")


class ScriptShortenerResponse(BaseModel):
    concise: ScriptRewrite = Field(..., description="A shorter, more to-the-point version of the script segment")
    dramatic: ScriptRewrite = Field(..., description="A shortened version with heightened drama and impact")
    minimal: ScriptRewrite = Field(..., description="A stripped-down version using the fewest words possible")
    poetic: ScriptRewrite = Field(..., description="A concise yet more lyrical and visually rich version")
    humorous: ScriptRewrite = Field(..., description="A shorter version with amusing or funny tone")

class AzureOpenAIService:
    def __init__(self):
        self.azure_client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        )
        self.client = from_openai(self.azure_client, mode=Mode.TOOLS_STRICT)
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME

    def _make_request(self, messages: List[dict]) -> List[Beat]:
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                response_model=List[Beat],
                max_tokens=settings.AZURE_OPENAI_MAX_TOKENS,
                temperature=settings.AZURE_OPENAI_TEMPERATURE,
            )
            return response
        except Exception as e:
            logger.error(f"Azure OpenAI API error: {str(e)}")
            raise

    def generate_beat_sheet(self, title: str, subtitle: str, genre: str, story: str) -> List[Beat]:
        system_prompt = (
            "You are an expert screenplay writer specializing in Blake Snyder's 'Save the Cat!' beat sheet structure. "
            "Generate a detailed beat sheet with exactly 15 beats. For each beat, provide:\n"
            "1. Beat number (1-15)\n"
            "2. Beat name\n"
            "3. Description tailored to the given story\n"
            "4. Suggested page length\n"
            "5. Timing (in terms of script percentage)\n"
            "Format the response as a JSON object with an array of beats."
        )

        user_prompt = (
            f"Create a 'Save the Cat!' beat sheet for a screenplay with the following details:\n"
            f"Title: {title}\n"
            f"Subtitle: {subtitle}\n"
            f"Genre: {genre}\n"
            f"Story: {story}"
        )

        messages = [
            {"role": "user", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        return self._make_request(messages)
    def generate_beat_sheet_stream(
        self, title: str, subtitle: str, genre: str, story: str
    ) -> Generator[List[Beat], None, None]:
        system_prompt = (
            "You are an expert screenplay writer specializing in Blake Snyder's 'Save the Cat!' beat sheet structure. "
            "Generate a detailed beat sheet with exactly 15 beats. For each beat, provide:\n"
            "1. Beat number (1-15)\n"
            "2. Beat name\n"
            "3. Description tailored to the given story\n"
            "4. Suggested page length\n"
            "5. Timing (in terms of script percentage)\n"
            "Format the response as a JSON object with an array of beats."
        )

        user_prompt = (
            f"Create a 'Save the Cat!' beat sheet for a screenplay with the following details:\n"
            f"Title: {title}\n"
            f"Subtitle: {subtitle}\n"
            f"Genre: {genre}\n"
            f"Story: {story}"
        )

        messages = [
            {"role": "user", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Use create_partial to stream progress; each yield is a partial List[Beat]
        return self.client.chat.completions.create_partial(
            model=self.deployment_name,
            messages=messages,
            response_model=List[Beat],
            max_tokens=settings.AZURE_OPENAI_MAX_TOKENS,
            temperature=settings.AZURE_OPENAI_TEMPERATURE,
        )

    def generate_scenes_for_beat(
        self,
        beat_title: str,
        beat_description: str,
        script_genre: str,
        tone: str | None = None,
    ) -> List[GeneratedScene]:
        """
        Generate scenes for a specific beat using Azure OpenAI.
        Returns a list of scenes with their dialogue and descriptions.
        """
        system_prompt = """You are an expert screenplay writer with deep knowledge of screenplay formatting and scene structure. 
        You will generate detailed scenes based on the given beat description. Each scene should include:
        1. Scene Heading (INT/EXT. LOCATION - TIME)
        2. Scene Description (action/description)
        3. Dialogue (if applicable)
        4. Estimated duration in minutes

        Follow these rules:
        - Scene headings must be clear and follow standard format
        - Scene descriptions should be vivid but concise
        - Dialogue should feel natural and reveal character
        - Consider tone and genre in your writing
        - Focus on visual storytelling
        - Create proper dramatic build-up
        - Each scene should serve the beat's purpose

        Format each scene according to the provided scene structure.
        """

        user_prompt = f"""Create scenes for the following beat:
        Title: {beat_title}
        Description: {beat_description}
        Genre: {script_genre}
        Tone: {tone if tone else 'Match genre conventions'}

        Break this beat into logical scenes that build toward the beat's goal.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_model=List[GeneratedScene],
                max_tokens=settings.AZURE_OPENAI_MAX_TOKENS,
                temperature=settings.AZURE_OPENAI_TEMPERATURE,
            )
            
            return response

        except Exception as e:
            logger.error(f"Scene generation failed: {str(e)}")
            raise

    def generate_scenes_for_act(
        self,
        act_beats: List[Dict[str, Any]],
        script_genre: str,
        tone: str | None = None
    ) -> Dict[str, List[GeneratedScene]]:
        """Generate scenes for an entire act maintaining narrative flow."""

        try:
            counter= 1
            scenes_by_beat = {}
            for beat in act_beats:
                scenes = self.generate_scenes_for_beat(
                    beat_title=beat.title,
                    beat_description=beat.description,
                    script_genre=script_genre,
                    tone=tone
                )
                scenes_by_beat[counter] = scenes
                counter+=1
            return scenes_by_beat

        except Exception as e:
            logger.error(f"Act-level scene generation failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def regenerate_scene(
        self,
        scene_id: str,
        beat_context: Dict[str, Any],
        previous_scene: Dict[str, Any] | None,
        next_scene: Dict[str, Any] | None,
        feedback: str | None = None
    ) -> GeneratedScene:
        """
        Regenerate a specific scene with context and optional feedback.
        """
        system_prompt = """You are an expert screenplay writer tasked with regenerating a scene.
        Consider the surrounding context and any feedback provided to improve the scene.
        Maintain consistency with surrounding scenes while addressing the specified issues.
        """

        context = {
            "beat": beat_context,
            "previous_scene": previous_scene,
            "next_scene": next_scene,
            "feedback": feedback
        }

        user_prompt = f"""Regenerate the scene with the following context:
        Beat: {beat_context['title']}
        Beat Description: {beat_context['description']}

        Contex: {context}

        Previous Scene: {previous_scene['scene_heading'] if previous_scene else 'None'}
        Next Scene: {next_scene['scene_heading'] if next_scene else 'None'}

        Feedback: {feedback if feedback else 'Improve the scene while maintaining story consistency'}

        Create a new version of the scene that better serves the story.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_model=GeneratedScene,
                max_tokens=settings.AZURE_OPENAI_MAX_TOKENS,
                temperature=settings.AZURE_OPENAI_TEMPERATURE,
            )
            
            return response

        except Exception as e:
            logger.error(f"Scene regeneration failed: {str(e)}")
            raise


    def generate_scene_description_for_beat(
        self,
        story_synopsis: str,
        genre: str,
        beat_position: int,
        template_beat_title: str,
        template_beat_definition: str,
        story_specific_beat_title: str,
        story_specific_beat_description: str,
        previous_scenes: Optional[List[str]] = None,
        num_scenes: int = 5
    ) -> List[GeneratedScene]:
        """
        Generate scenes for a specific beat using Azure OpenAI.
        
        Args:
            story_synopsis: Overall story summary
            genre: Script genre
            beat_position: Position of beat in story
            template_beat_title: Original beat title from template
            template_beat_definition: Original beat definition from template
            story_specific_beat_title: Customized beat title
            story_specific_beat_description: Customized beat description
            previous_scenes: List of previous scene titles for continuity
            num_scenes: Number of scenes to generate
        """
        self.openai_service = AzureOpenAIService()
        system_prompt = f"""You are an expert screenplay writer specialized in {genre} films.
        Your task is to generate {num_scenes} unique and compelling scenes that fulfill the requirements of a specific beat in the screenplay.
        
        For each scene, provide:
        1. A scene heading is a short version of whats happening in the script flow within four or five words.
        2. A scene description is a very short one line on what's going to unfold in that scene, No need to descriptive, only outline is needed.
        
        Consider:
        - Genre conventions and audience expectations
        - The beat's purpose in the story structure
        - Visual storytelling elements
        - Character development opportunities
        - Proper dramatic pacing
        - Natural story progression
        """

        user_prompt = f"""Create {num_scenes} scenes for this beat in the screenplay:

        Story Context:
        - Synopsis: {story_synopsis}
        - Genre: {genre}
        - Beat Position: {beat_position}

        Beat Information:
        - Template Title: {template_beat_title}
        - Template Definition: {template_beat_definition}
        - Story-Specific Title: {story_specific_beat_title}
        - Story-Specific Description: {story_specific_beat_description}

        {f'Previous Scenes for Context: {", ".join(previous_scenes)}' if previous_scenes else ''}

        Generate {num_scenes} distinct scenes that:
        1. Fulfill this beat's purpose in the story
        2. Maintain consistent tone and pacing
        3. Follow proper screenplay formatting
        4. Advance the plot while developing characters
        5. Consider the story's genre conventions
        """

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_model=List[GeneratedScene],
                max_tokens=settings.AZURE_OPENAI_MAX_TOKENS,
                temperature=settings.AZURE_OPENAI_TEMPERATURE,
            )
            
            return response

        except Exception as e:
            logger.error(f"Scene generation failed: {str(e)}")
            raise

    # @staticmethod
    def generate_scene_segment(
        self,
        story_synopsis: str,
        genre: str,
        arc_structure: str,
        beat_position: int,
        scene_position: int,
        template_beat_title: str,
        template_beat_definition: str,
        story_specific_beat_title: str,
        story_specific_beat_description: str,
        scene_title: str,
        scene_description: str,
        min_word_count: int = 200,
        previous_scenes: Optional[List[str]] = None
    ) -> GeneratedSceneSegment:
        """
        Generate a screenplay scene with structured components using instructor.
        
        Returns a GeneratedSceneSegment object with components that can be directly
        added to the database.
        """
        system_prompt = f"""You are an expert screenplay writer specialized in {genre} films.
        Your task is to write a compelling, detailed scene based on the provided scene description.
        
        Follow these rules for screenplay formatting:
        1. Scene headings must be in uppercase (e.g., "INT. LIVING ROOM - DAY")
        2. Action/description paragraphs should be concise but vivid
        3. Character names should be in uppercase when preceding dialogue
        4. Parentheticals for character directions should be in (parentheses)
        5. Dialogue should feel natural and match the character's voice
        6. Use transitions (e.g., CUT TO:, DISSOLVE TO:) sparingly and only when necessary
        
        The scene should have these components in this order:
        1. A scene heading (HEADING type)
        2. Action descriptions (ACTION type)
        3. Character dialogue (CHARACTER type) with optional parentheticals
        4. Additional action and dialogue as needed
        5. Optional transition (TRANSITION type)
        
        Ensure your scene:
        - Maintains the tone and style appropriate for {genre}
        - Contains at least {min_word_count} words total
        - Advances the story while developing characters
        - Is consistent with the beat's purpose in the overall story arc
        - Is consistent with the scene's title and description

        STRICTLY PROHIBITED CONTENT:
        1. Technical/markdown formatting like ```, **bold**, or ANY code blocks
        2. Placeholder text (e.g., END, COMPLETION, FINAL, TEMPLATE_PLACEHOLDER)
        3. Underscore_phrases or hyphenated-special-terms
        4. Run-on CAPITALIZED words (e.g., FINALENDSCENE)
        5. Non-screenplay vocabulary (e.g., "Completion", "Pipeline", "Module")

        EXAMPLES OF BAD OUTPUT:
        - ENDENDEND DINING ROOM - NIGHT
        - (completion_state = "finished")
        - CHARACTER_NAME_WITH_UNDERSCORE
        - "We need to FINALIZE_IMPLEMENTATION!"

        ALWAYS USE:
        - Standard screenplay formatting
        - Proper punctuation
        - Natural dialogue
        - Scene-appropriate vocabulary
        """

        user_prompt = f"""Write a screenplay scene based on the following context:

        Story Synopsis: {story_synopsis}
        Genre: {genre}
        Story Arc: {arc_structure}
        
        Beat Information:
        - Beat Position: {beat_position}
        - Template Beat: {template_beat_title}
        - Template Definition: {template_beat_definition}
        - Story-Specific Beat Title: {story_specific_beat_title}
        - Story-Specific Description: {story_specific_beat_description}
        
        Scene Information:
        - Scene Position: {scene_position}
        - Scene Heading: {scene_title}
        - Scene Description: {scene_description}
        
        {f'Previous Scenes: {", ".join(previous_scenes)}' if previous_scenes else ''}
        
        Return a structured scene with multiple components (heading, action, character, dialogue etc.)
        Each component should have a position value starting at 1000.0 and incrementing by 1000.0.
        Make the scene engaging, visual, and at least {min_word_count} words in total.
        """

        try:
            # Use instructor's from_openai wrapper to get structured output
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_model=GeneratedSceneSegment,
                max_tokens=settings.AZURE_OPENAI_MAX_TOKENS,
                temperature=settings.AZURE_OPENAI_TEMPERATURE,
                top_p=settings.AZURE_TOP_P,        # Focus on high-probability words
                presence_penalty=settings.AZURE_PRESENCE_PENALTY,  # Discourage repetitive phrases
                frequency_penalty=settings.AZURE_FREQUENCY_PENALTY,  # Discourage word repetition
                seed=settings.AZURE_SEED
            )
            return response

        except Exception as e:
            logger.error(f"Scene segment generation failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise


    def shorten_action_component(self, text: str, context: dict) -> ScriptShortenerResponse:
        """
        Shorten an action component with themed alternatives.
        """
        genre = context.get("genre", "")
        script_title = context.get("script_title", "")
        
        system_prompt = """
        You are a professional script editor with expertise in action line optimization for screenplays. Your task is to condense and refine action blocks while preserving essential narrative elements.

        Task: Create FIVE distinct themed versions of the provided action text, each with a different style but all maintaining the essential visual elements and narrative purpose.

        Create these specific themed versions:
        1. CONCISE: A shorter, more to-the-point version focusing on clarity
        2. DRAMATIC: A shortened version with heightened tension and impact
        3. MINIMAL: A stripped-down version using the fewest words possible
        4. POETIC: A concise yet more lyrical and visually rich version
        5. HUMOROUS: A shorter version with amusing or funny tone
        """
        
        user_prompt = f"""
        Script: {script_title}
        Genre: {genre}
        
        Original action description:
        "{text}"
        
        Create five distinct themed shortened alternatives as specified, each with a brief explanation of your approach.
        Each version should be shorter than the original while preserving the essential narrative elements.
        """
        
        try:
            # Use instructor with your schema
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_model=ScriptShortenerResponse,
                temperature=settings.AZURE_OPENAI_TEMPERATURE
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error shortening action component: {str(e)}")
            raise

    def shorten_dialogue_component(self, text: str, character_name: str, context: dict) -> ScriptShortenerResponse:
        """
        Shorten a dialogue component with themed alternatives.
        """
        genre = context.get("genre", "")
        script_title = context.get("script_title", "")
        parenthetical = context.get("parenthetical", "")
        
        system_prompt = """
        You are a dialogue specialist with expertise in script editing and emotional storytelling. Your task is to distill dialogue to its essential emotional core while preserving the character's unique voice, motivations, and any crucial revelations.

        Situation: You are working with a script excerpt that needs to be condensed while maintaining its dramatic impact and character integrity.

        Task: Analyze and shorten the provided dialogue from a the given genre script for the character, removing unnecessary elements while preserving the emotional essence and narrative purpose of the lines.

        Objective: Create more impactful, concise dialogue that maintains the character's voice and the scene's emotional weight, making the script tighter and more effective without losing important character moments or plot points.

        When editing dialogue:
        - Eliminate all stammering, hesitations, and filler words (such as "um," "uh," "you know," "like," etc.)
        - Remove redundant phrases and repetitive statements
        - Merge overlapping or connected thoughts into single, powerful lines
        - Consider the adjacent action/parenthetical context to ensure your edits align with the character's emotional state
        - Preserve distinctive speech patterns that define the character's voice
        - Retain all plot-critical information and emotional revelations
        - Maintain the character's specific motivations and intentions
        - Ensure the shortened dialogue flows naturally with what comes before and after


        Create these specific themed versions:
        1. CONCISE: A shorter, more to-the-point version focusing on clarity
        2. DRAMATIC: A shortened version with heightened emotional impact
        3. MINIMAL: A stripped-down version using the fewest words possible
        4. POETIC: A concise yet more lyrical and elevated version
        5. HUMOROUS: A shorter version with amusing or funny tone
        """
        
        user_prompt = f"""
        Script: {script_title}
        Genre: {genre}
        Character: {character_name}
        Parenthetical mood: {parenthetical if parenthetical else "None provided"}
        
        Original dialogue:
        "{text}"
        
        Create five distinct themed shortened alternatives as specified, each with a brief explanation of your approach.
        Each version should be shorter than the original while preserving the character's voice and essential information.
        """
        
        try:
            # Use instructor with your schema
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_model=ScriptShortenerResponse,
                temperature=settings.AZURE_OPENAI_TEMPERATURE
            )
            logger.info(response)
            return response
        
        except Exception as e:
            logger.error(f"Error shortening dialogue component: {str(e)}")
            raise


    def rewrite_action_component(self, text: str, context: dict) -> ScriptRewriteResponse:
        """
        Rewrite an action component with themed alternatives.
        
        Args:
            text: The original action text to rewrite
            context: Contextual information about the script
        
        Returns:
            A ScriptRewriteResponse with multiple themed alternatives
        """
        genre = context.get("genre", "")
        script_title = context.get("script_title", "")
        
        system_prompt = """
        You are a professional screenplay consultant specializing in action descriptions. Your expertise lies in rewriting action blocks to fit different tones and styles while maintaining the essential narrative elements.

        Task: Create FIVE distinct themed versions of the provided action text, each with a different style but all conveying the same essential visual information and narrative purpose.

        Create these specific themed versions:
        1. CONCISE: A focused, efficient version that cuts unnecessary description while maintaining clarity
        2. DRAMATIC: A version with heightened tension, evocative language, and dramatic flair
        3. MINIMAL: A version using sparse, hemingway-esque prose focused only on essential movements
        4. POETIC: A lyrical, visually-rich version with elegant language and vivid imagery
        5. HUMOROUS: A version with subtle wit, irony, or comedic undertones that add levity
        
        For each rewrite:
        - Maintain the same essential story beats and visual information
        - Keep the same character actions and motivations
        - Focus on style transformation, not content change
        - Include a brief explanation of your approach and specific techniques used
        
        Constraints:
        - No clichés
        - No excessive description
        - No melodrama unless specifically in the "dramatic" version
        - Keep the cinematographic qualities intact
        """
        
        user_prompt = f"""
        Script: {script_title}
        Genre: {genre}
        
        Original action description:
        "{text}"
        
        Create five distinct themed rewrites as specified, each with a brief explanation of your approach.
        Each version should match its theme while preserving the essential narrative and visual elements.
        """
        
        try:
            # Use instructor with your schema
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_model=ScriptRewriteResponse,
                temperature=settings.AZURE_OPENAI_TEMPERATURE
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error rewriting action component: {str(e)}")
            raise

    def rewrite_dialogue_component(self, text: str, character_name: str, context: dict) -> ScriptRewriteResponse:
        """
        Rewrite a dialogue component with themed alternatives.
        
        Args:
            text: The original dialogue text to rewrite
            character_name: The name of the character speaking
            context: Contextual information about the script and character
        
        Returns:
            A ScriptRewriteResponse with multiple themed alternatives
        """
        genre = context.get("genre", "")
        script_title = context.get("script_title", "")
        parenthetical = context.get("parenthetical", "")
        
        system_prompt = f"""
        You are a dialogue consultant for screenplays, specializing in authentic character voice and diverse writing styles. Your task is to rewrite dialogue for {character_name} with five different stylistic approaches.

        Task: Create FIVE distinct themed versions of {character_name}'s dialogue, each with a different style but all conveying the same essential information and character intention.

        Create these specific themed versions:
        1. CONCISE: Stripped-down, essential dialogue where each word counts
        2. DRAMATIC: Emotionally heightened dialogue with strong subtext and psychological depth
        3. MINIMAL: Sparse, understated dialogue using as few words as possible
        4. POETIC: Dialogue with literary quality, rhythm, metaphor, and rich language
        5. HUMOROUS: Dialogue with wit, comedic timing, or subtle humor that fits the character
        
        Character context:
        - Character: {character_name}
        - Emotional state: {parenthetical if parenthetical else "Not specified"}
        
        For each rewrite:
        - Maintain character consistency (voice, vocabulary, speech patterns)
        - Preserve the core meaning and intention of the line
        - Adjust only the stylistic approach, not the fundamental content
        - Include a brief explanation of your approach and techniques used
        
        Constraints:
        - No unnecessary exposition
        - Avoid clichés and stock phrases
        - Maintain subtext and character psychology
        - Ensure dialogue feels natural to speak aloud
        """
        
        user_prompt = f"""
        Script: {script_title}
        Genre: {genre}
        Character: {character_name}
        
        Original dialogue:
        "{text}"
        
        Create five distinct themed rewrites as specified, each with a brief explanation of your approach.
        Each version should match its theme while preserving the essential meaning and character voice.
        """
        
        try:
            # Use instructor with your schema
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_model=ScriptRewriteResponse,
                temperature=settings.AZURE_OPENAI_TEMPERATURE
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error rewriting dialogue component: {str(e)}")
            raise


    def expand_action_component(self, text: str, context: dict) -> ScriptExpansion:
        """
        Expand an action component with themed alternatives.
        """
        genre = context.get("genre", "")
        script_title = context.get("script_title", "")
        
        system_prompt = """
        You are a professional screenplay editor with expertise in action description enhancement. 
        Your task is to expand and enrich action blocks while maintaining the screenplay's tone and pacing.

        Task: Create FIVE distinct themed expansions of the provided action text, each with a different style but all
        enhancing the visual storytelling without becoming verbose.

        Create these specific themed versions:
        1. CONCISE: A moderately expanded version that adds crucial visual details while remaining economical with words
        2. DRAMATIC: An expansion that heightens tension and emotional impact with atmospheric details
        3. MINIMAL: A carefully expanded version that adds only the most essential visual elements
        4. POETIC: An expansion with rich imagery and sensory details that create a distinctive visual style
        5. HUMOROUS: An expansion that introduces subtle humor or irony while maintaining the scene's purpose

        Each expansion should:
        - Enhance visual storytelling without becoming verbose
        - Maintain the original action's core purpose
        - Be tailored to the genre of the screenplay
        - Avoid dialogue or character thoughts unless they're in the original
        - Preserve the flow and pacing of the scene
        """
        
        user_prompt = f"""
        Script: {script_title}
        Genre: {genre}
        
        Original action description:
        "{text}"
        
        Create five distinct themed expansions as specified, each with a brief explanation of your approach.
        Each expansion should enhance the visual storytelling while respecting the screenplay format.
        """
        
        try:
            # Use instructor with your schema
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_model=ScriptExpansionResponse,
                temperature=settings.AZURE_OPENAI_TEMPERATURE
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error expanding action component: {str(e)}")
            raise

    def expand_dialogue_component(self, text: str, character_name: str, context: dict) -> ScriptExpansionResponse:
        """
        Expand a dialogue component with themed alternatives.
        """
        genre = context.get("genre", "")
        script_title = context.get("script_title", "")
        parenthetical = context.get("parenthetical", "")
        
        system_prompt = """
        You are a dialogue specialist with expertise in screenplay writing and character voice development. 
        Your task is to expand dialogue to enhance character development and dramatic impact while maintaining 
        the character's unique voice and the scene's purpose.

        Situation: You are working with a script excerpt that needs dialogue expansion to more fully reveal character,
        advance the plot, or heighten emotional impact.

        Task: Analyze and expand the provided dialogue from the given genre script for the character, adding depth
        and nuance while preserving the character's voice and the scene's dramatic intent.

        Objective: Create more impactful, developed dialogue that enhances the character's personality, advances story
        elements, or increases emotional resonance without becoming unnecessarily verbose.

        When expanding dialogue:
        - Maintain the character's established voice, speech patterns, and vocabulary
        - Consider the genre and appropriate dialogue style
        - Keep additions natural to the flow of conversation
        - Avoid exposition that would be unnatural in speech
        - Consider the parenthetical mood information if provided
        - Ensure expansion serves character development, plot advancement, or emotional impact

        Create these specific themed versions:
        1. CONCISE: A moderately expanded version that adds character depth while remaining relatively economical
        2. DRAMATIC: An expansion that heightens emotional impact and tension
        3. MINIMAL: A carefully expanded version that adds just enough to deepen characterization
        4. POETIC: An expansion with more lyrical or metaphorical language appropriate to the character
        5. HUMOROUS: An expansion that introduces subtle humor or wit while maintaining the character's voice
        """
        
        user_prompt = f"""
        Script: {script_title}
        Genre: {genre}
        Character: {character_name}
        Parenthetical mood: {parenthetical if parenthetical else "None provided"}
        
        Original dialogue:
        "{text}"
        
        Create five distinct themed dialogue expansions as specified, each with a brief explanation of your approach.
        Each expansion should enhance the character while maintaining their voice and the scene's purpose.
        """
        
        try:
            # Use instructor with your schema
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_model=ScriptExpansionResponse,
                temperature=settings.AZURE_OPENAI_TEMPERATURE
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error expanding dialogue component: {str(e)}")
            raise


    def continue_action_component(self, text: str, context: dict) -> ScriptContinuationResponse:
        """
        Generate continuations for an action component with multiple themed alternatives.
        
        Args:
            text: The original action text to continue
            context: Contextual information about the script
        
        Returns:
            ScriptContinuationResponse with multiple themed continuation alternatives
        """
        genre = context.get("genre", "")
        script_title = context.get("script_title", "")
        
        system_prompt = """
        You are a professional screenplay writer with expertise in action description continuation. Your task is to continue the given action block in a screenplay with multiple themed variations.

        Task: Create FIVE distinct themed continuations of the provided action text, each with a different style but all maintaining narrative coherence and visual storytelling principles.

        Create these specific themed continuations:
        1. CONCISE: A brief, focused continuation that gets straight to the point without unnecessary description
        2. DRAMATIC: A continuation with heightened tension, evocative language, and dramatic impact
        3. MINIMAL: A sparse, hemingway-esque continuation using only essential words and visual elements
        4. POETIC: A lyrical continuation with rich imagery, metaphor, and sensory details
        5. HUMOROUS: A continuation that introduces subtle wit, irony, or comedic elements while maintaining scene integrity
        
        For each continuation:
        - Ensure it flows naturally from the original text
        - Maintain the established tone and visual style
        - Respect screenplay format conventions
        - Keep the continuation focused on action (not dialogue)
        - Include a brief explanation of your approach and specific techniques used
        
        Constraints:
        - No introducing new main characters
        - No drastic scene changes
        - No dialogue lines
        - No "CONTINUED FROM" or "TO BE CONTINUED" meta-references
        - Keep within screenplay formatting conventions
        """
        
        user_prompt = f"""
        Script: {script_title}
        Genre: {genre}
        
        Original action description:
        "{text}"
        
        Please continue this action description with five distinct themed variations as specified.
        Each continuation should flow naturally from the original text and maintain the established visual style.
        """
        
        try:
            # Use instructor with the ScriptContinuationResponse schema
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_model=ScriptContinuationResponse,
                temperature=settings.AZURE_OPENAI_TEMPERATURE
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error continuing action component: {str(e)}")
            raise

    def continue_dialogue_component(self, text: str, character_name: str, context: dict) -> ScriptContinuationResponse:
        """
        Generate continuations for a dialogue component with multiple themed alternatives.
        
        Args:
            text: The original dialogue text to continue
            character_name: The name of the character speaking
            context: Contextual information about the script and character
        
        Returns:
            ScriptContinuationResponse with multiple themed continuation alternatives
        """
        genre = context.get("genre", "")
        script_title = context.get("script_title", "")
        parenthetical = context.get("parenthetical", "")
        
        system_prompt = f"""
        You are a dialogue specialist for screenplays, with expertise in character voice and authentic speech patterns. Your task is to continue the dialogue for {character_name} with multiple themed variations.

        Task: Create FIVE distinct themed continuations of {character_name}'s dialogue, each with a different style but all maintaining the character's established voice and the scene's dramatic purpose.

        Create these specific themed continuations:
        1. CONCISE: A brief, direct continuation focusing on the character's immediate goal or reaction
        2. DRAMATIC: A continuation with heightened emotional intensity, revealing deeper feelings or stakes
        3. MINIMAL: A sparse, understated continuation using as few words as possible while preserving meaning
        4. POETIC: A continuation with literary quality, metaphorical language, or philosophical depth
        5. HUMOROUS: A continuation that introduces wit, irony, or comedic elements appropriate to the character
        
        Character context:
        - Name: {character_name}
        - Emotional state: {parenthetical if parenthetical else "Not specified"}
        
        For each continuation:
        - Ensure it flows naturally from the original dialogue
        - Maintain the character's established voice, vocabulary, and speech patterns
        - Respect the emotional state indicated by any parenthetical direction
        - Keep the continuation in character and consistent with the scene's purpose
        - Include a brief explanation of your approach and how it serves the character
        
        Constraints:
        - No introducing new plot elements that would dramatically change the scene
        - No switching to another character's dialogue
        - No stage directions or action descriptions
        - No "trailing off" endings that don't actually continue the thought
        - Ensure the dialogue sounds natural when spoken aloud
        """
        
        user_prompt = f"""
        Script: {script_title}
        Genre: {genre}
        Character: {character_name}
        
        Original dialogue:
        "{text}"
        
        Please continue this dialogue with five distinct themed variations as specified.
        Each continuation should sound natural for {character_name} and flow seamlessly from the original line.
        """
        
        try:
            # Use instructor with the ScriptContinuationResponse schema
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_model=ScriptContinuationResponse,
                temperature=settings.AZURE_OPENAI_TEMPERATURE
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error continuing dialogue component: {str(e)}")
            raise