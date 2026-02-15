"""Telegram typing indicator — sends chat action every N seconds until stopped."""
import asyncio
import logging

from telegram import Bot
from telegram.constants import ChatAction

from src.bot_client import TypingIndicator
from src.constants import TELEGRAM_TYPING_INTERVAL

logger = logging.getLogger(__name__)


async def _keep_typing(bot: Bot, chat_id: str, stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            await bot.send_chat_action(chat_id=int(chat_id), action=ChatAction.TYPING)
        except Exception as exc:
            logger.debug("Typing action failed: %s", exc)
        await asyncio.sleep(TELEGRAM_TYPING_INTERVAL)


class TelegramTypingIndicator(TypingIndicator):

    def __init__(self, bot: Bot, chat_id: str) -> None:
        self._bot = bot
        self._chat_id = chat_id
        self._stop_event: asyncio.Event | None = None
        self._task: asyncio.Task | None = None

    async def start(self, to: str) -> None:
        await self.stop(to)
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(
            _keep_typing(self._bot, self._chat_id, self._stop_event)
        )

    async def stop(self, to: str) -> None:
        match self._stop_event:
            case None:
                pass
            case event:
                event.set()

        match self._task:
            case None:
                pass
            case task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                self._task = None

        self._stop_event = None
