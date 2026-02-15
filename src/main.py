"""Entry point — wires Config → TelegramClient → MessageRouter."""
import logging

from rich.logging import RichHandler

from src.config import Config
from src.constants import MSG_BOT_STARTING
from src.router import MessageRouter
from src.telegram.client import TelegramClient
from src.transcription.whisper import WhisperTranscriptionClient


def _setup_logging(level: str) -> None:
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    list(map(root.removeHandler, root.handlers[:]))
    root.addHandler(RichHandler(rich_tracebacks=True))


def main() -> None:
    config = Config.from_env()
    _setup_logging(config.log_level)

    logger = logging.getLogger(__name__)
    logger.info(MSG_BOT_STARTING)

    router = MessageRouter(config)
    transcriber = (
        WhisperTranscriptionClient(config.openai_api_key)
        if config.openai_api_key
        else None
    )
    client = TelegramClient(config, transcriber=transcriber)
    client.run(router.handle, on_model=router.handle_model_command)


if __name__ == "__main__":
    main()
