"""Abstract interfaces for transport-agnostic bot clients."""
from abc import ABC, abstractmethod
from typing import Awaitable, Callable

from src.message_handler import ChatMessage

# on_model signature: (sender, provider, args) -> reply
OnModel = Callable[[str, str, str], Awaitable[str]]


class TypingIndicator(ABC):
    @abstractmethod
    async def start(self, to: str) -> None: ...

    @abstractmethod
    async def stop(self, to: str) -> None: ...


class BotClient(ABC):
    @abstractmethod
    def run(
        self,
        on_message: Callable[[ChatMessage], Awaitable[str]],
        on_model: OnModel | None = None,
    ) -> None: ...

    @abstractmethod
    async def send_message(self, to: str, text: str) -> bool: ...
