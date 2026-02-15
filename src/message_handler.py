from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ChatMessage:
    sender: str
    content: str
    timestamp: int


@dataclass(frozen=True)
class MessageAction:
    should_respond: bool
    reason: Optional[str] = None


def normalize_phone(s: str) -> str:
    return "".join(c for c in s if c.isdigit())


class MessageHandler:
    
    def __init__(self, allowed_phone: str):
        self.allowed_phone = allowed_phone
        self.allowed_digits = normalize_phone(allowed_phone)

    def should_process(self, message: ChatMessage) -> MessageAction:
        sender_digits = normalize_phone(message.sender)
        match (sender_digits == self.allowed_digits, self.allowed_digits in sender_digits):
            case (True, _) | (_, True):
                return MessageAction(should_respond=True)
            case _:
                logger.debug(f"Blocked: {message.sender}")
                return MessageAction(
                    should_respond=False,
                    reason=f"Unauthorized sender: {message.sender}"
                )

    def filter_messages(self, messages: list[ChatMessage]) -> list[ChatMessage]:
        return list(filter(
            lambda msg: self.should_process(msg).should_respond,
            messages
        ))
