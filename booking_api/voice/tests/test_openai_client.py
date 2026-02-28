from unittest.mock import MagicMock, patch

import pytest

from booking_api.voice.openai_client import (
    chat_completion,
    get_openai_client,
    transcribe_audio,
)


@patch("booking_api.voice.openai_client._client", None)
def test_get_client_raises_without_api_key(settings):
    settings.OPENAI_API_KEY = ""
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        get_openai_client()


@patch("booking_api.voice.openai_client._client", None)
def test_get_client_raises_when_key_is_none(settings):
    settings.OPENAI_API_KEY = None
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        get_openai_client()


@patch("booking_api.voice.openai_client._client", None)
@patch("booking_api.voice.openai_client.OpenAI")
def test_get_client_creates_singleton(mock_openai_cls, settings):
    settings.OPENAI_API_KEY = "sk-test-key"
    client1 = get_openai_client()
    client2 = get_openai_client()
    assert client1 is client2
    mock_openai_cls.assert_called_once_with(api_key="sk-test-key")


@patch("booking_api.voice.openai_client.get_openai_client")
def test_transcribe_audio_calls_whisper(mock_get_client, settings):
    settings.OPENAI_WHISPER_MODEL = "whisper-1"
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value.text = "Book Ellie at 3pm"
    mock_get_client.return_value = mock_client

    fake_file = MagicMock()
    result = transcribe_audio(fake_file, language="en")

    assert result == "Book Ellie at 3pm"
    mock_client.audio.transcriptions.create.assert_called_once_with(
        model="whisper-1",
        file=fake_file,
        language="en",
    )


@patch("booking_api.voice.openai_client.get_openai_client")
def test_transcribe_audio_returns_text(mock_get_client, settings):
    settings.OPENAI_WHISPER_MODEL = "whisper-1"
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value.text = "Hello world"
    mock_get_client.return_value = mock_client

    result = transcribe_audio(MagicMock())
    assert result == "Hello world"


@patch("booking_api.voice.openai_client.get_openai_client")
def test_chat_completion_calls_gpt4(mock_get_client, settings):
    settings.OPENAI_MODEL = "gpt-4o"
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    messages = [{"role": "user", "content": "hi"}]
    tools = [{"type": "function", "function": {"name": "test"}}]

    chat_completion(messages, tools)

    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )


@patch("booking_api.voice.openai_client.get_openai_client")
def test_chat_completion_passes_model_from_settings(mock_get_client, settings):
    settings.OPENAI_MODEL = "gpt-4o-mini"
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    chat_completion([{"role": "user", "content": "test"}], [])

    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs["model"] == "gpt-4o-mini"
