"""VisionClient — abstract base for image analysis backends."""
from abc import ABC, abstractmethod


class VisionClient(ABC):
    @abstractmethod
    async def analyze(self, image_bytes: bytes, caption: str | None = None) -> str:
        """Analyze image bytes and return a text description. Raises on failure."""
        ...
