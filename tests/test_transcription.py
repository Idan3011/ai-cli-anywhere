"""TDD: TranscriptionClient tests written FIRST"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.transcription.client import TranscriptionClient
from src.transcription.whisper import WhisperTranscriptionClient


def test_whisper_client_implements_abc():
    assert issubclass(WhisperTranscriptionClient, TranscriptionClient)


@pytest.mark.asyncio
async def test_whisper_transcribe_calls_openai_with_audio():
    client = WhisperTranscriptionClient(api_key="test-key")
    audio_bytes = b"fake-audio-data"

    mock_response = MagicMock()
    mock_response.text = "hello from voice"

    mock_transcriptions = AsyncMock()
    mock_transcriptions.create = AsyncMock(return_value=mock_response)

    mock_audio = MagicMock()
    mock_audio.transcriptions = mock_transcriptions

    mock_openai = MagicMock()
    mock_openai.audio = mock_audio

    with patch("src.transcription.whisper.AsyncOpenAI", return_value=mock_openai):
        result = await client.transcribe(audio_bytes)

    assert result == "hello from voice"
    mock_transcriptions.create.assert_called_once()


@pytest.mark.asyncio
async def test_whisper_transcribe_returns_stripped_text():
    client = WhisperTranscriptionClient(api_key="test-key")

    mock_response = MagicMock()
    mock_response.text = "  hello  "

    mock_transcriptions = AsyncMock()
    mock_transcriptions.create = AsyncMock(return_value=mock_response)
    mock_openai = MagicMock()
    mock_openai.audio.transcriptions = mock_transcriptions

    with patch("src.transcription.whisper.AsyncOpenAI", return_value=mock_openai):
        result = await client.transcribe(b"audio")

    assert result == "hello"


@pytest.mark.asyncio
async def test_whisper_transcribe_raises_on_api_error():
    client = WhisperTranscriptionClient(api_key="test-key")

    mock_transcriptions = AsyncMock()
    mock_transcriptions.create = AsyncMock(side_effect=Exception("API error"))
    mock_openai = MagicMock()
    mock_openai.audio.transcriptions = mock_transcriptions

    with patch("src.transcription.whisper.AsyncOpenAI", return_value=mock_openai):
        with pytest.raises(Exception, match="API error"):
            await client.transcribe(b"audio")
