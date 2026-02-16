"""OpenAIVisionClient — OpenAI GPT-4o vision backend."""
import base64

from openai import AsyncOpenAI

from src.constants import MSG_IMAGE_DEFAULT_PROMPT, OPENAI_VISION_MODEL
from src.vision.client import VisionClient


class OpenAIVisionClient(VisionClient):

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def analyze(self, image_bytes: bytes, caption: str | None = None) -> str:
        client = AsyncOpenAI(api_key=self._api_key)
        prompt = caption or MSG_IMAGE_DEFAULT_PROMPT
        image_data = base64.standard_b64encode(image_bytes).decode()
        response = await client.chat.completions.create(
            model=OPENAI_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""
