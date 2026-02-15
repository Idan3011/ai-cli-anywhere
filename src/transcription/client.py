"""TranscriptionClient — abstract base for speech-to-text backends."""
from abc import ABC, abstractmethod


class TranscriptionClient(ABC):
    @abstractmethod
    async def transcribe(self, audio: bytes) -> str:
        """Convert raw audio bytes to text. Raises on failure."""
        ...
