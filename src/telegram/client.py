"""TelegramClient — event-driven transport via python-telegram-bot."""
import logging
import time
from typing import Awaitable, Callable, Optional

from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.ext import MessageHandler as TGMessageHandler
from telegram.ext import filters

from src.bot_client import BotClient, OnModel
from src.config import Config
from src.constants import (
    CMD_MODEL,
    CMD_NEW,
    CMD_STATUS,
    MSG_BLOCKED_CHAT,
    MSG_HELP,
    MSG_IMAGE_ANALYSIS_FAILED,
    MSG_IMAGE_NOT_CONFIGURED,
    MSG_MODEL_USAGE,
    MSG_NO_RESPONSE,
    MSG_SEND_FAIL,
    MSG_SEND_OK,
    MSG_VOICE_NOT_CONFIGURED,
    MSG_VOICE_TRANSCRIPTION_FAILED,
)
from src.message_handler import ChatMessage, normalize_phone
from src.telegram.typing import TelegramTypingIndicator
from src.transcription.client import TranscriptionClient
from src.vision.client import VisionClient

logger = logging.getLogger(__name__)


class TelegramClient(BotClient):

    def __init__(
        self,
        config: Config,
        transcriber: Optional[TranscriptionClient] = None,
        vision_client: Optional[VisionClient] = None,
    ) -> None:
        self._token = config.telegram_bot_token
        self._allowed_chat_id = config.allowed_chat_id
        self._app: Optional[Application] = None
        self._transcriber = transcriber
        self._vision_client = vision_client

    # ── BotClient interface ───────────────────────────────────────────────────

    def run(
        self,
        on_message: Callable[[ChatMessage], Awaitable[str]],
        on_model: OnModel | None = None,
        on_status: Callable[[], str] | None = None,
        on_new: Callable[[str], str] | None = None,
    ) -> None:
        self._app = Application.builder().token(self._token).build()
        self._app.add_handler(
            TGMessageHandler(filters.TEXT & ~filters.COMMAND, self._make_handler(on_message))
        )
        if on_model is not None:
            self._app.add_handler(
                CommandHandler(CMD_MODEL, self._make_model_handler(on_model))
            )
        if on_status is not None:
            self._app.add_handler(
                CommandHandler(CMD_STATUS, self._make_simple_handler(on_status))
            )
        if on_new is not None:
            self._app.add_handler(
                CommandHandler(CMD_NEW, self._make_sender_handler(on_new))
            )
        self._app.add_handler(CommandHandler("help", self._make_help_handler()))
        self._app.add_handler(
            TGMessageHandler(filters.VOICE, self._make_voice_handler(on_message))
        )
        self._app.add_handler(
            TGMessageHandler(filters.PHOTO, self._make_photo_handler(on_message))
        )
        self._app.run_polling()

    async def send_message(self, to: str, text: str) -> bool:
        match self._app:
            case None:
                logger.error("send_message called before run()")
                return False
            case app:
                try:
                    await app.bot.send_message(chat_id=int(to), text=text)
                    return True
                except Exception as exc:
                    logger.error("Telegram send_message failed: %s", exc)
                    return False

    # ── helpers (also used in tests) ─────────────────────────────────────────

    def _is_allowed(self, update: Update) -> bool:
        if update.effective_chat is None:
            return False
        incoming = normalize_phone(str(update.effective_chat.id))
        allowed = normalize_phone(self._allowed_chat_id)
        return incoming == allowed

    def _update_to_message(self, update: Update) -> Optional[ChatMessage]:
        if update.message is None or update.effective_chat is None:
            return None
        msg, chat = update.message, update.effective_chat
        text = (msg.text or "").strip()
        match text:
            case "":
                return None
            case content:
                return ChatMessage(
                    sender=str(chat.id),
                    content=content,
                    timestamp=int(msg.date.timestamp()),
                )

    @staticmethod
    def _parse_model_args(args: str) -> tuple[str, str] | None:
        """Parse '<provider> <model-args>' → (provider, model_args) or None."""
        parts = args.strip().split(None, 1)
        match parts:
            case [provider, model] if provider in ("claude", "cursor"):
                return (provider, model)
            case _:
                return None

    # ── internal handler factory ──────────────────────────────────────────────

    def _make_simple_handler(self, callback: Callable[[], str]) -> Callable:
        """Handler for commands that need no arguments — just call callback and reply."""
        async def _handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            match self._is_allowed(update):
                case False:
                    return
                case True:
                    pass
            sender = str(update.effective_chat.id) if update.effective_chat else ""
            await self.send_message(sender, callback())

        return _handler

    def _make_sender_handler(self, callback: Callable[[str], str]) -> Callable:
        """Handler for commands that pass the sender ID to the callback."""
        async def _handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            match self._is_allowed(update):
                case False:
                    return
                case True:
                    pass
            sender = str(update.effective_chat.id) if update.effective_chat else ""
            await self.send_message(sender, callback(sender))

        return _handler

    def _make_help_handler(self) -> Callable:
        async def _handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            match self._is_allowed(update):
                case False:
                    return
                case True:
                    pass
            sender = str(update.effective_chat.id) if update.effective_chat else ""
            await self.send_message(sender, MSG_HELP)

        return _handler

    def _make_voice_handler(
        self, on_message: Callable[[ChatMessage], Awaitable[str]]
    ) -> Callable:
        async def _handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            match self._is_allowed(update):
                case False:
                    chat_id = update.effective_chat.id if update.effective_chat else "?"
                    logger.warning(MSG_BLOCKED_CHAT, chat_id)
                    return
                case True:
                    pass

            sender = str(update.effective_chat.id) if update.effective_chat else ""
            match self._transcriber:
                case None:
                    await self.send_message(sender, MSG_VOICE_NOT_CONFIGURED)
                    return
                case _:
                    pass
            voice = update.message.voice if update.message else None
            match voice:
                case None:
                    return
                case v:
                    try:
                        tg_file = await v.get_file()
                        audio_bytes = bytes(await tg_file.download_as_bytearray())
                        text = await self._transcriber.transcribe(audio_bytes)
                    except Exception:
                        logger.exception("Voice transcription failed")
                        await self.send_message(sender, MSG_VOICE_TRANSCRIPTION_FAILED)
                        return
                    msg = ChatMessage(
                        sender=sender,
                        content=text,
                        timestamp=int(update.message.date.timestamp()),
                    )
                    await self._process(msg, context.bot, on_message)

        return _handler

    def _make_photo_handler(
        self, on_message: Callable[[ChatMessage], Awaitable[str]]
    ) -> Callable:
        async def _handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            match self._is_allowed(update):
                case False:
                    chat_id = update.effective_chat.id if update.effective_chat else "?"
                    logger.warning(MSG_BLOCKED_CHAT, chat_id)
                    return
                case True:
                    pass

            sender = str(update.effective_chat.id) if update.effective_chat else ""
            match self._vision_client:
                case None:
                    await self.send_message(sender, MSG_IMAGE_NOT_CONFIGURED)
                    return
                case _:
                    pass

            photos = update.message.photo if update.message else None
            match photos:
                case None | []:
                    return
                case _:
                    try:
                        tg_file = await photos[-1].get_file()
                        image_bytes = bytes(await tg_file.download_as_bytearray())
                        caption = update.message.caption if update.message else None
                        text = await self._vision_client.analyze(image_bytes, caption)
                    except Exception:
                        logger.exception("Image analysis failed")
                        await self.send_message(sender, MSG_IMAGE_ANALYSIS_FAILED)
                        return
                    msg = ChatMessage(
                        sender=sender,
                        content=text,
                        timestamp=int(update.message.date.timestamp()),
                    )
                    await self._process(msg, context.bot, on_message)

        return _handler

    def _make_model_handler(self, on_model: OnModel) -> Callable:
        async def _handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            match self._is_allowed(update):
                case False:
                    chat_id = update.effective_chat.id if update.effective_chat else "?"
                    logger.warning(MSG_BLOCKED_CHAT, chat_id)
                    return
                case True:
                    pass

            sender = str(update.effective_chat.id) if update.effective_chat else ""
            raw_args = " ".join(context.args or [])
            parsed = self._parse_model_args(raw_args)
            match parsed:
                case None:
                    await self.send_message(sender, MSG_MODEL_USAGE)
                case (provider, model_args):
                    reply = await on_model(sender, provider, model_args)
                    await self.send_message(sender, reply)

        return _handler

    def _make_handler(
        self, on_message: Callable[[ChatMessage], Awaitable[str]]
    ) -> Callable:
        async def _handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            match self._is_allowed(update):
                case False:
                    chat_id = update.effective_chat.id if update.effective_chat else "?"
                    logger.warning(MSG_BLOCKED_CHAT, chat_id)
                    return
                case True:
                    pass

            msg = self._update_to_message(update)
            match msg:
                case None:
                    return
                case message:
                    await self._process(message, context.bot, on_message)

        return _handler

    async def _process(
        self,
        message: ChatMessage,
        bot: Bot,
        on_message: Callable[[ChatMessage], Awaitable[str]],
    ) -> None:
        start = time.time()
        typing = TelegramTypingIndicator(bot, message.sender)
        await typing.start(message.sender)
        try:
            response = await on_message(message)
        finally:
            await typing.stop(message.sender)

        elapsed = time.time() - start
        match response.strip() if response else "":
            case "":
                logger.warning(MSG_NO_RESPONSE)
            case text:
                success = await self.send_message(message.sender, text)
                match success:
                    case True:
                        logger.info(MSG_SEND_OK, elapsed)
                    case False:
                        logger.error(MSG_SEND_FAIL, elapsed)
