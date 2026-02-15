"""TDD: MessageRouter tests written FIRST"""
import pytest
from unittest.mock import AsyncMock, patch

from src.message_handler import ChatMessage
from src.router import MessageRouter, _is_claude_tagged, _strip_claude_tag


def make_config(monkeypatch, *, cursor_cli: str = "agent"):
    from src.config import Config

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("ALLOWED_CHAT_ID", "123456789")
    monkeypatch.setenv("CURSOR_CLI_PATH", cursor_cli)
    return Config.from_env()


def make_message(content: str = "hello") -> ChatMessage:
    return ChatMessage(sender="123456789", content=content, timestamp=0)


# ── tag helpers ───────────────────────────────────────────────────────────────


def test_is_claude_tagged_matches_pattern():
    assert _is_claude_tagged("@claude help", ("@claude",))


def test_is_claude_tagged_is_case_insensitive():
    assert _is_claude_tagged("@Claude help", ("@claude",))


def test_is_claude_tagged_returns_false_when_no_pattern():
    assert not _is_claude_tagged("fix my code", ("@claude",))


def test_strip_claude_tag_removes_pattern():
    assert _strip_claude_tag("@claude help me", ("@claude",)) == "help me"


def test_strip_claude_tag_removes_multiple_patterns():
    result = _strip_claude_tag("claude: do stuff", ("claude:", "@claude"))
    assert result == "do stuff"


# ── routing decisions ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_handle_routes_to_claude_when_tagged(monkeypatch):
    config = make_config(monkeypatch)
    router = MessageRouter(config)
    msg = make_message("@claude what is 2+2?")

    with patch.object(router, "_call_claude_cli", new=AsyncMock(return_value="4")) as mock:
        result = await router.handle(msg)

    mock.assert_called_once()
    assert result == "4"


@pytest.mark.asyncio
async def test_handle_strips_tag_before_sending_to_claude(monkeypatch):
    config = make_config(monkeypatch)
    router = MessageRouter(config)
    msg = make_message("@claude what is 2+2?")

    with patch.object(router, "_call_claude_cli", new=AsyncMock(return_value="4")) as mock:
        await router.handle(msg)

    _sender, text = mock.call_args.args
    assert "@claude" not in text.lower()


@pytest.mark.asyncio
async def test_handle_routes_to_cursor_when_untagged(monkeypatch):
    config = make_config(monkeypatch, cursor_cli="agent")
    router = MessageRouter(config)
    msg = make_message("fix my code")

    with patch.object(router, "_call_cursor_cli", new=AsyncMock(return_value="done")) as mock:
        result = await router.handle(msg)

    mock.assert_called_once()
    assert result == "done"


@pytest.mark.asyncio
async def test_handle_routes_to_claude_when_no_cursor_configured(monkeypatch):
    config = make_config(monkeypatch, cursor_cli="")
    router = MessageRouter(config)
    msg = make_message("fix my code")

    with patch.object(router, "_call_claude_cli", new=AsyncMock(return_value="fixed")) as mock:
        result = await router.handle(msg)

    mock.assert_called_once()
    assert result == "fixed"


# ── model state ───────────────────────────────────────────────────────────────


def test_get_claude_model_default_is_none(monkeypatch):
    router = MessageRouter(make_config(monkeypatch))
    assert router.get_claude_model() is None


def test_set_claude_model_updates_state(monkeypatch):
    router = MessageRouter(make_config(monkeypatch))
    router.set_claude_model("claude-opus-4-6")
    assert router.get_claude_model() == "claude-opus-4-6"


def test_set_claude_model_can_be_overwritten(monkeypatch):
    router = MessageRouter(make_config(monkeypatch))
    router.set_claude_model("claude-opus-4-6")
    router.set_claude_model("claude-haiku-4-5-20251001")
    assert router.get_claude_model() == "claude-haiku-4-5-20251001"


# ── handle_model_command ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_handle_model_command_claude_sets_model(monkeypatch):
    router = MessageRouter(make_config(monkeypatch))
    result = await router.handle_model_command("123", "claude", "claude-opus-4-6")
    assert router.get_claude_model() == "claude-opus-4-6"
    assert "claude-opus-4-6" in result


@pytest.mark.asyncio
async def test_handle_model_command_claude_resolves_alias(monkeypatch):
    monkeypatch.setenv("CLAUDE_MODEL_ALIASES", "opus:claude-opus-4-6,sonnet:claude-sonnet-4-5-20250929")
    router = MessageRouter(make_config(monkeypatch))
    result = await router.handle_model_command("123", "claude", "opus")
    assert router.get_claude_model() == "claude-opus-4-6"
    assert "claude-opus-4-6" in result


@pytest.mark.asyncio
async def test_handle_model_command_claude_unknown_alias_passes_through(monkeypatch):
    monkeypatch.setenv("CLAUDE_MODEL_ALIASES", "opus:claude-opus-4-6")
    router = MessageRouter(make_config(monkeypatch))
    await router.handle_model_command("123", "claude", "claude-custom-model")
    assert router.get_claude_model() == "claude-custom-model"


@pytest.mark.asyncio
async def test_handle_model_command_cursor_forwards_to_cursor(monkeypatch):
    router = MessageRouter(make_config(monkeypatch))
    with patch.object(router, "_call_cursor_cli", new=AsyncMock(return_value="ok")) as mock:
        result = await router.handle_model_command("123", "cursor", "sonnet 4.5")
    mock.assert_called_once_with("123", "/model sonnet 4.5")
    assert result == "ok"


@pytest.mark.asyncio
async def test_handle_model_command_unknown_provider_returns_usage(monkeypatch):
    router = MessageRouter(make_config(monkeypatch))
    result = await router.handle_model_command("123", "gpt", "gpt-4")
    assert "Usage" in result or "usage" in result.lower()


# ── Claude CLI --model flag passthrough ───────────────────────────────────────


@pytest.mark.asyncio
async def test_call_cursor_cli_passes_working_dir_as_cwd(monkeypatch):
    monkeypatch.setenv("CURSOR_WORKING_DIR", "/home/user/myproject")
    config = make_config(monkeypatch)
    router = MessageRouter(config)

    captured_kwargs = {}

    async def fake_exec(*args, **kwargs):
        captured_kwargs.update(kwargs)
        proc = AsyncMock()
        proc.returncode = 0
        proc.communicate = AsyncMock(return_value=(b"done", b""))
        return proc

    with patch("asyncio.create_subprocess_exec", side_effect=fake_exec):
        with patch("asyncio.wait_for", new=AsyncMock(side_effect=lambda coro, **_: coro)):
            await router._call_cursor_cli("123", "hello")

    assert captured_kwargs.get("cwd") == "/home/user/myproject"


@pytest.mark.asyncio
async def test_call_cursor_cli_cwd_is_none_when_not_configured(monkeypatch):
    monkeypatch.delenv("CURSOR_WORKING_DIR", raising=False)
    config = make_config(monkeypatch)
    router = MessageRouter(config)

    captured_kwargs = {}

    async def fake_exec(*args, **kwargs):
        captured_kwargs.update(kwargs)
        proc = AsyncMock()
        proc.returncode = 0
        proc.communicate = AsyncMock(return_value=(b"done", b""))
        return proc

    with patch("asyncio.create_subprocess_exec", side_effect=fake_exec):
        with patch("asyncio.wait_for", new=AsyncMock(side_effect=lambda coro, **_: coro)):
            await router._call_cursor_cli("123", "hello")

    assert captured_kwargs.get("cwd") is None


@pytest.mark.asyncio
async def test_call_claude_cli_passes_model_flag_when_set(monkeypatch):
    config = make_config(monkeypatch)
    router = MessageRouter(config)
    router.set_claude_model("claude-opus-4-6")

    captured_args = []

    async def fake_exec(*args, **kwargs):
        captured_args.extend(args)
        proc = AsyncMock()
        proc.returncode = 0
        proc.communicate = AsyncMock(return_value=(b'{"result":"hi","session_id":"s1"}', b""))
        return proc

    with patch("asyncio.create_subprocess_exec", side_effect=fake_exec):
        with patch("asyncio.wait_for", new=AsyncMock(side_effect=lambda coro, **_: coro)):
            await router._call_claude_cli("123", "hello")

    assert "--model" in captured_args
    idx = captured_args.index("--model")
    assert captured_args[idx + 1] == "claude-opus-4-6"


# ── /status command ───────────────────────────────────────────────────────────


def test_status_shows_default_model(monkeypatch):
    router = MessageRouter(make_config(monkeypatch))
    assert "default" in router.handle_status_command()


def test_status_shows_set_model(monkeypatch):
    router = MessageRouter(make_config(monkeypatch))
    router.set_claude_model("claude-opus-4-6")
    assert "claude-opus-4-6" in router.handle_status_command()


def test_status_shows_voice_disabled_when_no_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("src.config.load_dotenv", lambda **_: None)
    router = MessageRouter(make_config(monkeypatch))
    assert "disabled" in router.handle_status_command()


def test_status_shows_cursor_not_configured(monkeypatch):
    router = MessageRouter(make_config(monkeypatch, cursor_cli=""))
    assert "not configured" in router.handle_status_command()


# ── /new command ──────────────────────────────────────────────────────────────


def test_new_clears_session_and_returns_confirmation(monkeypatch):
    from src.constants import MSG_NEW_SESSION
    router = MessageRouter(make_config(monkeypatch))
    router._claude_store.set("123456789", "session-abc")
    router._chat_store.set("123456789", "chat-xyz")
    result = router.handle_new_command("123456789")
    assert result == MSG_NEW_SESSION
    assert router._claude_store.get("123456789") is None
    assert router._chat_store.get("123456789") is None


def test_new_on_empty_session_still_returns_confirmation(monkeypatch):
    from src.constants import MSG_NEW_SESSION
    router = MessageRouter(make_config(monkeypatch))
    result = router.handle_new_command("123456789")
    assert result == MSG_NEW_SESSION
