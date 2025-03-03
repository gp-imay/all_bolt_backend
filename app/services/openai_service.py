# app/services/openai_service.py
import json
import logging
from enum import Enum
from typing import List, Generator, Dict, Any, Optional
from pydantic import BaseModel
from instructor import from_openai, Mode
from openai import AzureOpenAI
from config import settings
import traceback


from schemas.scene_segment_ai import GeneratedSceneSegment, AISceneComponent


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
        - Is consistent with the scene's title and descriiption
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
            )
            
            return response

        except Exception as e:
            logger.error(f"Scene segment generation failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise