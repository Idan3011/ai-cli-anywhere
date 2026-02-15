from dataclasses import dataclass
from typing import Optional
import os
from dotenv import load_dotenv

from src.constants import DEFAULT_CLAUDE_MODEL_ALIASES


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    allowed_chat_id: str
    claude_cli_path: str
    log_level: str
    cursor_cli_path: Optional[str]
    cursor_timeout: int
    claude_timeout: int
    claude_patterns: tuple[str, ...]
    claude_model_aliases: dict[str, str]
    cursor_working_dir: Optional[str]
    openai_api_key: Optional[str]
    anthropic_api_key: Optional[str]

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()

        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("ALLOWED_CHAT_ID")
        claude_cli = os.getenv("CLAUDE_CLI_PATH", "claude")
        log_level = os.getenv("LOG_LEVEL", "INFO")
        cursor_cli = os.getenv("CURSOR_CLI_PATH", "agent") or None
        cursor_timeout = os.getenv("CURSOR_TIMEOUT", "60")
        claude_timeout = os.getenv("CLAUDE_TIMEOUT", "45")
        raw_patterns = os.getenv("CLAUDE_PATTERNS", "@claude,claude:,hey claude,claude,")
        raw_aliases = os.getenv("CLAUDE_MODEL_ALIASES", DEFAULT_CLAUDE_MODEL_ALIASES)
        cursor_working_dir = os.getenv("CURSOR_WORKING_DIR") or None
        openai_api_key = os.getenv("OPENAI_API_KEY") or None
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY") or None

        patterns = tuple(p.strip() for p in raw_patterns.split(",") if p.strip())
        aliases = dict(
            pair.split(":", 1)
            for pair in raw_aliases.split(",")
            if ":" in pair
        )

        return cls._validate(
            telegram_bot_token=token,
            allowed_chat_id=chat_id,
            claude_cli_path=claude_cli,
            log_level=log_level,
            cursor_cli_path=cursor_cli,
            cursor_timeout=int(cursor_timeout),
            claude_timeout=int(claude_timeout),
            claude_patterns=patterns,
            claude_model_aliases=aliases,
            cursor_working_dir=cursor_working_dir,
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
        )

    @staticmethod
    def _validate(
        telegram_bot_token: Optional[str],
        allowed_chat_id: Optional[str],
        claude_cli_path: str,
        log_level: str,
        cursor_cli_path: Optional[str],
        cursor_timeout: int,
        claude_timeout: int,
        claude_patterns: tuple[str, ...],
        claude_model_aliases: dict[str, str],
        cursor_working_dir: Optional[str],
        openai_api_key: Optional[str],
        anthropic_api_key: Optional[str],
    ) -> "Config":
        match telegram_bot_token:
            case None | "":
                raise ValueError("TELEGRAM_BOT_TOKEN must be set in .env")
            case _:
                pass

        match allowed_chat_id:
            case None | "":
                raise ValueError("ALLOWED_CHAT_ID must be set in .env")
            case _:
                pass

        return Config(
            telegram_bot_token=telegram_bot_token,
            allowed_chat_id=allowed_chat_id,
            claude_cli_path=claude_cli_path,
            log_level=log_level,
            cursor_cli_path=cursor_cli_path,
            cursor_timeout=cursor_timeout,
            claude_timeout=claude_timeout,
            claude_patterns=claude_patterns,
            claude_model_aliases=claude_model_aliases,
            cursor_working_dir=cursor_working_dir,
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
        )
