# app/services/openai_service.py
import json
import logging
from enum import Enum
from typing import List, Generator, Dict, Any
from pydantic import BaseModel
from instructor import from_openai, Mode
from openai import AzureOpenAI
from config import settings
import traceback

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

class GeneratedScene(BaseModel):
    scene_heading: str
    scene_description: str
    dialogue_blocks: List[DialogueBlock] | None = None
    estimated_duration: float


class AzureOpenAIService:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        )
        self.client = from_openai(self.client, mode=Mode.TOOLS_STRICT)
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
