"""ClaudeVisionClient — Anthropic Claude vision backend."""
import base64

from anthropic import AsyncAnthropic

from src.constants import CLAUDE_VISION_MODEL, MSG_IMAGE_DEFAULT_PROMPT
from src.vision.client import VisionClient


class ClaudeVisionClient(VisionClient):

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def analyze(self, image_bytes: bytes, caption: str | None = None) -> str:
        client = AsyncAnthropic(api_key=self._api_key)
        prompt = caption or MSG_IMAGE_DEFAULT_PROMPT
        image_data = base64.standard_b64encode(image_bytes).decode()
        message = await client.messages.create(
            model=CLAUDE_VISION_MODEL,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
        return message.content[0].text.strip()
