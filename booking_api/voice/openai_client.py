import logging

from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)
_client = None


def get_openai_client():
    """Lazy singleton for the OpenAI client."""
    global _client
    if _client is None:
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")
        _client = OpenAI(api_key=api_key)
    return _client


def transcribe_audio(audio_file, language="en"):
    """Transcribe audio using OpenAI Whisper."""
    client = get_openai_client()
    transcription = client.audio.transcriptions.create(
        model=settings.OPENAI_WHISPER_MODEL,
        file=(audio_file.name, audio_file.read(), audio_file.content_type),
        language=language,
    )
    return transcription.text


def chat_completion(messages, tools):
    """Send a chat completion request with function calling tools."""
    client = get_openai_client()
    return client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
