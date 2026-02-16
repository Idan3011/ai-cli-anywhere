"""Entry point — wires Config → TelegramClient → MessageRouter."""
import logging

from rich.logging import RichHandler

from src.config import Config
from src.constants import MSG_BOT_STARTING
from src.router import MessageRouter
from src.telegram.client import TelegramClient
from src.transcription.whisper import WhisperTranscriptionClient
from src.vision.claude import ClaudeVisionClient
from src.vision.openai import OpenAIVisionClient


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
    match (config.anthropic_api_key, config.openai_api_key):
        case (str() as k, _) if k:
            vision = ClaudeVisionClient(k)
        case (_, str() as k) if k:
            vision = OpenAIVisionClient(k)
        case _:
            vision = None
    client = TelegramClient(config, transcriber=transcriber, vision_client=vision)
    client.run(
        router.handle,
        on_model=router.handle_model_command,
        on_status=router.handle_status_command,
        on_new=router.handle_new_command,
        on_history=router.handle_history_command,
        stream_handle=router.stream_handle if config.stream_responses else None,
    )


if __name__ == "__main__":
    main()
