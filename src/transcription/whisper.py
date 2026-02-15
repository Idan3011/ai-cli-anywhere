"""WhisperTranscriptionClient — OpenAI Whisper speech-to-text backend."""
import io

from openai import AsyncOpenAI

from src.constants import VOICE_FILENAME, WHISPER_MODEL
from src.transcription.client import TranscriptionClient


class WhisperTranscriptionClient(TranscriptionClient):

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def transcribe(self, audio: bytes) -> str:
        client = AsyncOpenAI(api_key=self._api_key)
        audio_file = io.BytesIO(audio)
        audio_file.name = VOICE_FILENAME
        response = await client.audio.transcriptions.create(
            model=WHISPER_MODEL,
            file=audio_file,
        )
        return response.text.strip()
