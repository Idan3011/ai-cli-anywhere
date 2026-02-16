"""TDD: VisionClient backend tests written FIRST"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


async def test_claude_vision_analyze_calls_api_with_image():
    from src.vision.claude import ClaudeVisionClient

    client = ClaudeVisionClient(api_key="test-key")
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="  a cat  ")]

    with patch("src.vision.claude.AsyncAnthropic") as mock_cls:
        mock_anthropic = AsyncMock()
        mock_anthropic.messages.create = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_anthropic

        result = await client.analyze(b"fake-image-bytes")

    mock_anthropic.messages.create.assert_called_once()
    call_kwargs = mock_anthropic.messages.create.call_args.kwargs
    content = call_kwargs["messages"][0]["content"]
    assert any(block["type"] == "image" for block in content)


async def test_claude_vision_analyze_returns_stripped_text():
    from src.vision.claude import ClaudeVisionClient

    client = ClaudeVisionClient(api_key="test-key")
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="  a dog \n")]

    with patch("src.vision.claude.AsyncAnthropic") as mock_cls:
        mock_anthropic = AsyncMock()
        mock_anthropic.messages.create = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_anthropic

        result = await client.analyze(b"bytes")

    assert result == "a dog"


async def test_claude_vision_analyze_uses_caption_when_provided():
    from src.vision.claude import ClaudeVisionClient

    client = ClaudeVisionClient(api_key="test-key")
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="answer")]

    with patch("src.vision.claude.AsyncAnthropic") as mock_cls:
        mock_anthropic = AsyncMock()
        mock_anthropic.messages.create = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_anthropic

        await client.analyze(b"bytes", caption="What is the error in this screenshot?")

    call_kwargs = mock_anthropic.messages.create.call_args.kwargs
    content = call_kwargs["messages"][0]["content"]
    text_blocks = [b for b in content if b["type"] == "text"]
    assert text_blocks[0]["text"] == "What is the error in this screenshot?"


async def test_claude_vision_analyze_raises_on_api_error():
    from src.vision.claude import ClaudeVisionClient

    client = ClaudeVisionClient(api_key="test-key")

    with patch("src.vision.claude.AsyncAnthropic") as mock_cls:
        mock_anthropic = AsyncMock()
        mock_anthropic.messages.create = AsyncMock(side_effect=RuntimeError("API down"))
        mock_cls.return_value = mock_anthropic

        with pytest.raises(RuntimeError):
            await client.analyze(b"bytes")


# ── OpenAIVisionClient ────────────────────────────────────────────────────────


async def test_openai_vision_analyze_calls_api_with_image():
    from src.vision.openai import OpenAIVisionClient

    client = OpenAIVisionClient(api_key="test-key")
    mock_choice = MagicMock()
    mock_choice.message.content = "  a cat  "
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("src.vision.openai.AsyncOpenAI") as mock_cls:
        mock_openai = AsyncMock()
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_openai

        result = await client.analyze(b"fake-image-bytes")

    mock_openai.chat.completions.create.assert_called_once()
    call_kwargs = mock_openai.chat.completions.create.call_args.kwargs
    content = call_kwargs["messages"][0]["content"]
    assert any(block["type"] == "image_url" for block in content)


async def test_openai_vision_analyze_returns_stripped_text():
    from src.vision.openai import OpenAIVisionClient

    client = OpenAIVisionClient(api_key="test-key")
    mock_choice = MagicMock()
    mock_choice.message.content = "  a dog \n"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("src.vision.openai.AsyncOpenAI") as mock_cls:
        mock_openai = AsyncMock()
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_openai

        result = await client.analyze(b"bytes")

    assert result == "a dog"


async def test_openai_vision_analyze_uses_caption_when_provided():
    from src.vision.openai import OpenAIVisionClient

    client = OpenAIVisionClient(api_key="test-key")
    mock_choice = MagicMock()
    mock_choice.message.content = "answer"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("src.vision.openai.AsyncOpenAI") as mock_cls:
        mock_openai = AsyncMock()
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_openai

        await client.analyze(b"bytes", caption="What is the error?")

    call_kwargs = mock_openai.chat.completions.create.call_args.kwargs
    content = call_kwargs["messages"][0]["content"]
    text_blocks = [b for b in content if b["type"] == "text"]
    assert text_blocks[0]["text"] == "What is the error?"


async def test_openai_vision_analyze_raises_on_api_error():
    from src.vision.openai import OpenAIVisionClient

    client = OpenAIVisionClient(api_key="test-key")

    with patch("src.vision.openai.AsyncOpenAI") as mock_cls:
        mock_openai = AsyncMock()
        mock_openai.chat.completions.create = AsyncMock(side_effect=RuntimeError("API down"))
        mock_cls.return_value = mock_openai

        with pytest.raises(RuntimeError):
            await client.analyze(b"bytes")
