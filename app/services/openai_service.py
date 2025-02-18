# app/services/openai_service.py
import json
import logging
from typing import List
from pydantic import BaseModel
from instructor import from_openai, Mode
from openai import AzureOpenAI
from config import settings

logger = logging.getLogger(__name__)


class Beat(BaseModel):
    beat_number: int
    beat_name: str
    beat_title: str
    description: str
    page_length: str
    timing: str


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

# class AzureOpenAIService:
#     def __init__(self):
#         self.endpoint = settings.AZURE_OPENAI_ENDPOINT
#         self.api_key = settings.AZURE_OPENAI_API_KEY
#         self.api_version = settings.AZURE_OPENAI_API_VERSION
#         self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME
        
#     async def _make_request(self, messages: List[Dict]) -> Dict:
#         headers = {
#             "Content-Type": "application/json",
#             "api-key": self.api_key
#         }
        
#         payload = {
#             "messages": messages,
#             "max_completion_tokens": settings.AZURE_OPENAI_MAX_TOKENS,
#             "temperature": settings.AZURE_OPENAI_TEMPERATURE
#             # "response_format": { "type": "json_object" }
#         }
        
#         url = f"{self.endpoint}/openai/deployments/{self.deployment_name}/chat/completions?api-version={self.api_version}"
#         url = "https://openai-test-azure.openai.azure.com/openai/deployments/o1-mini/chat/completions?api-version=2024-08-01-preview"
        
#         async with aiohttp.ClientSession() as session:
#             async with session.post(url, headers=headers, json=payload) as response:
#                 if response.status != 200:
#                     error_text = await response.text()
#                     logger.error(f"Azure OpenAI API error: {error_text}")
#                     raise Exception(f"Azure OpenAI API error: {response.status}")
                
#                 return await response.json()

#     async def generate_beat_sheet(self, title: str, subtitle: str, genre: str, story: str) -> List[Dict]:
#         system_prompt = """You are an expert screenplay writer specializing in Blake Snyder's Save the Cat! beat sheet structure. 
#         Generate a detailed beat sheet with exactly 15 beats. For each beat, provide:
#         1. Beat number (1-15)
#         2. Beat name
#         3. Description tailored to the given story
#         4. Suggested page length
#         5. Timing (in terms of script percentage)
#         Format the response as a JSON object with an array of beats."""

#         user_prompt = f"""Create a Save the Cat! beat sheet for a screenplay with the following details:
#         Title: {title}
#         Subtitle: {subtitle}
#         Genre: {genre}
#         Story: {story}"""

#         messages = [
#             {"role": "user", "content": system_prompt},
#             {"role": "user", "content": user_prompt}
#         ]

#         try:
#             response = await self._make_request(messages)
#             logger.info(response['choices'][0]['message']['content'])
#             content = json.loads(response['choices'][0]['message']['content'])
#             return content['beats']
#         except Exception as e:
#             logger.error(f"Error generating beat sheet: {str(e)}")
#             raise