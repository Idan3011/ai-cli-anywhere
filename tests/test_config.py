"""TDD: Config tests written FIRST"""
import pytest
from src.config import Config


def test_config_from_env_success(monkeypatch):
    """Happy-path: all required env vars present."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot123:ABC")
    monkeypatch.setenv("ALLOWED_CHAT_ID", "987654321")
    monkeypatch.setenv("CLAUDE_CLI_PATH", "/usr/bin/claude")

    config = Config.from_env()

    assert config.telegram_bot_token == "bot123:ABC"
    assert config.allowed_chat_id == "987654321"
    assert config.claude_cli_path == "/usr/bin/claude"


def test_config_missing_token_fails(monkeypatch):
    """Missing TELEGRAM_BOT_TOKEN must raise."""
    monkeypatch.setattr("src.config.load_dotenv", lambda **_: None)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("ALLOWED_CHAT_ID", "123456789")

    with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
        Config.from_env()


def test_config_missing_chat_id_fails(monkeypatch):
    """Missing ALLOWED_CHAT_ID must raise."""
    monkeypatch.setattr("src.config.load_dotenv", lambda **_: None)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot123:ABC")
    monkeypatch.delenv("ALLOWED_CHAT_ID", raising=False)

    with pytest.raises(ValueError, match="ALLOWED_CHAT_ID"):
        Config.from_env()


def test_config_immutable():
    """Frozen dataclass: attribute assignment must fail."""
    config = Config(
        telegram_bot_token="token",
        allowed_chat_id="123456789",
        claude_cli_path="claude",
        log_level="INFO",
        cursor_cli_path=None,
        cursor_timeout=60,
        claude_timeout=45,
        claude_patterns=("@claude",),
        claude_model_aliases={},
        cursor_working_dir=None,
        openai_api_key=None,
    )

    with pytest.raises(Exception):
        config.telegram_bot_token = "other"


def test_config_telegram_fields_from_env(monkeypatch):
    """Telegram-specific fields load from env."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mytoken:XYZ")
    monkeypatch.setenv("ALLOWED_CHAT_ID", "111222333")
    monkeypatch.setenv("CURSOR_CLI_PATH", "myagent")
    monkeypatch.setenv("CURSOR_TIMEOUT", "90")
    monkeypatch.setenv("CLAUDE_TIMEOUT", "30")
    monkeypatch.setenv("CLAUDE_PATTERNS", "@claude,claude:")

    config = Config.from_env()

    assert config.telegram_bot_token == "mytoken:XYZ"
    assert config.allowed_chat_id == "111222333"
    assert config.cursor_cli_path == "myagent"
    assert config.cursor_timeout == 90
    assert config.claude_timeout == 30
    assert config.claude_patterns == ("@claude", "claude:")


def test_config_defaults(monkeypatch):
    """Optional fields have sensible defaults."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot:tok")
    monkeypatch.setenv("ALLOWED_CHAT_ID", "123456789")
    monkeypatch.delenv("CURSOR_CLI_PATH", raising=False)
    monkeypatch.delenv("CURSOR_TIMEOUT", raising=False)
    monkeypatch.delenv("CLAUDE_TIMEOUT", raising=False)
    monkeypatch.delenv("CLAUDE_PATTERNS", raising=False)

    config = Config.from_env()

    assert config.cursor_cli_path == "agent"
    assert config.cursor_timeout == 60
    assert config.claude_timeout == 45
    assert len(config.claude_patterns) > 0


def test_config_cursor_cli_blank_becomes_none(monkeypatch):
    """Blank CURSOR_CLI_PATH → None (Claude-only mode)."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot:tok")
    monkeypatch.setenv("ALLOWED_CHAT_ID", "123456789")
    monkeypatch.setenv("CURSOR_CLI_PATH", "")

    config = Config.from_env()

    assert config.cursor_cli_path is None


def test_config_parses_claude_model_aliases(monkeypatch):
    """CLAUDE_MODEL_ALIASES parses into a dict."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot:tok")
    monkeypatch.setenv("ALLOWED_CHAT_ID", "123456789")
    monkeypatch.setenv("CLAUDE_MODEL_ALIASES", "opus:claude-opus-4-6,haiku:claude-haiku-4-5-20251001")

    config = Config.from_env()

    assert config.claude_model_aliases["opus"] == "claude-opus-4-6"
    assert config.claude_model_aliases["haiku"] == "claude-haiku-4-5-20251001"


def test_config_model_aliases_have_defaults(monkeypatch):
    """Default aliases are loaded when CLAUDE_MODEL_ALIASES is not set."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot:tok")
    monkeypatch.setenv("ALLOWED_CHAT_ID", "123456789")
    monkeypatch.delenv("CLAUDE_MODEL_ALIASES", raising=False)

    config = Config.from_env()

    assert "opus" in config.claude_model_aliases
    assert "sonnet" in config.claude_model_aliases
    assert "haiku" in config.claude_model_aliases


def test_config_cursor_working_dir_from_env(monkeypatch):
    """CURSOR_WORKING_DIR is read from env."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot:tok")
    monkeypatch.setenv("ALLOWED_CHAT_ID", "123456789")
    monkeypatch.setenv("CURSOR_WORKING_DIR", "/home/user/myproject")

    config = Config.from_env()

    assert config.cursor_working_dir == "/home/user/myproject"


def test_config_cursor_working_dir_default_is_none(monkeypatch):
    """CURSOR_WORKING_DIR defaults to None (inherits cwd)."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot:tok")
    monkeypatch.setenv("ALLOWED_CHAT_ID", "123456789")
    monkeypatch.delenv("CURSOR_WORKING_DIR", raising=False)

    config = Config.from_env()

    assert config.cursor_working_dir is None


def test_config_openai_api_key_from_env(monkeypatch):
    """OPENAI_API_KEY is read from env."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot:tok")
    monkeypatch.setenv("ALLOWED_CHAT_ID", "123456789")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test123")

    config = Config.from_env()

    assert config.openai_api_key == "sk-test123"


def test_config_openai_api_key_default_is_none(monkeypatch):
    """OPENAI_API_KEY defaults to None (voice transcription disabled)."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot:tok")
    monkeypatch.setenv("ALLOWED_CHAT_ID", "123456789")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    config = Config.from_env()

    assert config.openai_api_key is None
