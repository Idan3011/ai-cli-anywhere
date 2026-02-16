"""TDD: TelegramClient tests written FIRST"""
import pytest
from unittest.mock import MagicMock

from src.config import Config
from src.telegram.client import TelegramClient


def make_config(*, token: str = "test-token", chat_id: str = "123456789") -> Config:
    return Config(
        telegram_bot_token=token,
        allowed_chat_id=chat_id,
        claude_cli_path="claude",
        log_level="INFO",
        cursor_cli_path=None,
        cursor_timeout=60,
        claude_timeout=45,
        claude_patterns=("@claude",),
        claude_model_aliases={},
        cursor_working_dir=None,
        openai_api_key=None,
        anthropic_api_key=None,
        stream_responses=False,
    )


def make_update(*, chat_id: int, text: str) -> MagicMock:
    """Build a minimal mock of a python-telegram-bot Update."""
    update = MagicMock()
    update.effective_chat.id = chat_id
    update.message.text = text
    update.message.date.timestamp.return_value = 1000.0
    return update


# ── allowed-chat filter ───────────────────────────────────────────────────────


def test_allowed_chat_id_passes_filter():
    client = TelegramClient(make_config(chat_id="123456789"))
    assert client._is_allowed(make_update(chat_id=123456789, text="hi"))


def test_blocked_chat_id_fails_filter():
    client = TelegramClient(make_config(chat_id="123456789"))
    assert not client._is_allowed(make_update(chat_id=999999999, text="hi"))


# ── Update → ChatMessage conversion ─────────────────────────────────────


def test_update_converts_to_chat_message():
    client = TelegramClient(make_config(chat_id="123456789"))
    update = make_update(chat_id=123456789, text="hello")

    msg = client._update_to_message(update)

    assert msg is not None
    assert msg.sender == "123456789"
    assert msg.content == "hello"
    assert msg.timestamp == 1000


def test_empty_message_text_returns_none():
    client = TelegramClient(make_config(chat_id="123456789"))
    update = make_update(chat_id=123456789, text="")

    msg = client._update_to_message(update)

    assert msg is None


def test_whitespace_only_message_returns_none():
    client = TelegramClient(make_config(chat_id="123456789"))
    update = make_update(chat_id=123456789, text="   ")

    msg = client._update_to_message(update)

    assert msg is None


def test_message_content_is_stripped():
    client = TelegramClient(make_config(chat_id="123456789"))
    update = make_update(chat_id=123456789, text="  hello  ")

    msg = client._update_to_message(update)

    assert msg is not None
    assert msg.content == "hello"


# ── /model command parsing ────────────────────────────────────────────────────


def test_parse_model_args_claude_provider():
    result = TelegramClient._parse_model_args("claude claude-opus-4-6")
    assert result == ("claude", "claude-opus-4-6")


def test_parse_model_args_cursor_provider_with_spaces():
    result = TelegramClient._parse_model_args("cursor sonnet 4.5")
    assert result == ("cursor", "sonnet 4.5")


def test_parse_model_args_unknown_provider_returns_none():
    result = TelegramClient._parse_model_args("gpt gpt-4o")
    assert result is None


def test_parse_model_args_empty_returns_none():
    result = TelegramClient._parse_model_args("")
    assert result is None


def test_parse_model_args_provider_only_returns_none():
    result = TelegramClient._parse_model_args("claude")
    assert result is None


# ── voice transcription ───────────────────────────────────────────────────────


def test_voice_transcriber_is_none_by_default():
    """Without a transcriber, _transcriber is None."""
    client = TelegramClient(make_config())
    assert client._transcriber is None


async def test_voice_replies_not_configured_when_no_transcriber():
    """Voice handler sends MSG_VOICE_NOT_CONFIGURED when transcriber is None."""
    from unittest.mock import AsyncMock, patch
    from src.constants import MSG_VOICE_NOT_CONFIGURED

    client = TelegramClient(make_config())
    on_message = AsyncMock()

    update = MagicMock()
    update.effective_chat.id = 123456789
    update.message.voice = MagicMock()
    update.message.date.timestamp.return_value = 1000.0
    context = MagicMock()

    with patch.object(client, "send_message", new_callable=AsyncMock) as mock_send:
        handler = client._make_voice_handler(on_message)
        await handler(update, context)
        mock_send.assert_called_once_with("123456789", MSG_VOICE_NOT_CONFIGURED)
    on_message.assert_not_called()


def test_voice_transcriber_stored_on_client():
    from src.transcription.client import TranscriptionClient
    from unittest.mock import MagicMock

    transcriber = MagicMock(spec=TranscriptionClient)
    client = TelegramClient(make_config(), transcriber=transcriber)
    assert client._transcriber is transcriber


# ── /help command ─────────────────────────────────────────────────────────────


def test_help_text_mentions_model_command():
    from src.constants import MSG_HELP
    assert "/model" in MSG_HELP


def test_help_text_mentions_routing():
    from src.constants import MSG_HELP
    assert "@claude" in MSG_HELP
