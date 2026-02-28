from django.core.files.uploadedfile import SimpleUploadedFile

from booking_api.voice.serializers import (
    ChatRequestSerializer,
    MessageSerializer,
    TranscribeRequestSerializer,
)

# ---------------------------------------------------------------------------
# TranscribeRequestSerializer
# ---------------------------------------------------------------------------


class TestTranscribeRequestValidAudio:
    def test_valid_audio_file(self):
        audio = SimpleUploadedFile("test.webm", b"x" * 1024, content_type="audio/webm")
        serializer = TranscribeRequestSerializer(data={"audio": audio})
        assert serializer.is_valid(), serializer.errors

    def test_accepts_mp3(self):
        audio = SimpleUploadedFile("t.mp3", b"x" * 100, content_type="audio/mpeg")
        serializer = TranscribeRequestSerializer(data={"audio": audio})
        assert serializer.is_valid(), serializer.errors

    def test_accepts_mp4(self):
        audio = SimpleUploadedFile("t.mp4", b"x" * 100, content_type="audio/mp4")
        serializer = TranscribeRequestSerializer(data={"audio": audio})
        assert serializer.is_valid(), serializer.errors

    def test_accepts_wav(self):
        audio = SimpleUploadedFile("t.wav", b"x" * 100, content_type="audio/wav")
        serializer = TranscribeRequestSerializer(data={"audio": audio})
        assert serializer.is_valid(), serializer.errors

    def test_accepts_webm(self):
        audio = SimpleUploadedFile("t.webm", b"x" * 100, content_type="audio/webm")
        serializer = TranscribeRequestSerializer(data={"audio": audio})
        assert serializer.is_valid(), serializer.errors

    def test_accepts_ogg(self):
        audio = SimpleUploadedFile("t.ogg", b"x" * 100, content_type="audio/ogg")
        serializer = TranscribeRequestSerializer(data={"audio": audio})
        assert serializer.is_valid(), serializer.errors

    def test_accepts_m4a(self):
        audio = SimpleUploadedFile("t.m4a", b"x" * 100, content_type="audio/x-m4a")
        serializer = TranscribeRequestSerializer(data={"audio": audio})
        assert serializer.is_valid(), serializer.errors


class TestTranscribeRequestRejectsInvalid:
    def test_rejects_missing_audio(self):
        serializer = TranscribeRequestSerializer(data={})
        assert not serializer.is_valid()
        assert "audio" in serializer.errors

    def test_rejects_oversized_file(self):
        big = SimpleUploadedFile(
            "big.webm", b"x" * (10 * 1024 * 1024 + 1), content_type="audio/webm"
        )
        serializer = TranscribeRequestSerializer(data={"audio": big})
        assert not serializer.is_valid()
        assert "audio" in serializer.errors

    def test_rejects_invalid_mime_type(self):
        txt = SimpleUploadedFile("f.txt", b"hello", content_type="text/plain")
        serializer = TranscribeRequestSerializer(data={"audio": txt})
        assert not serializer.is_valid()
        assert "audio" in serializer.errors


class TestTranscribeRequestLanguage:
    def test_default_language_is_en(self):
        audio = SimpleUploadedFile("t.webm", b"x" * 100, content_type="audio/webm")
        serializer = TranscribeRequestSerializer(data={"audio": audio})
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["language"] == "en"

    def test_custom_language(self):
        audio = SimpleUploadedFile("t.webm", b"x" * 100, content_type="audio/webm")
        serializer = TranscribeRequestSerializer(
            data={"audio": audio, "language": "vi"}
        )
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["language"] == "vi"


# ---------------------------------------------------------------------------
# MessageSerializer
# ---------------------------------------------------------------------------


class TestMessageSerializer:
    def test_valid_user_message(self):
        serializer = MessageSerializer(data={"role": "user", "content": "hello"})
        assert serializer.is_valid(), serializer.errors

    def test_valid_assistant_message(self):
        serializer = MessageSerializer(
            data={"role": "assistant", "content": "How can I help?"}
        )
        assert serializer.is_valid(), serializer.errors

    def test_valid_tool_message(self):
        serializer = MessageSerializer(
            data={
                "role": "tool",
                "content": '{"found": true}',
                "tool_call_id": "call_abc123",
            }
        )
        assert serializer.is_valid(), serializer.errors

    def test_valid_assistant_with_tool_calls(self):
        serializer = MessageSerializer(
            data={
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "lookup_customer",
                            "arguments": '{"phone_number": "+447700900123"}',
                        },
                    }
                ],
            }
        )
        assert serializer.is_valid(), serializer.errors

    def test_rejects_invalid_role(self):
        serializer = MessageSerializer(data={"role": "admin", "content": "hello"})
        assert not serializer.is_valid()
        assert "role" in serializer.errors


# ---------------------------------------------------------------------------
# ChatRequestSerializer
# ---------------------------------------------------------------------------


class TestChatRequestSerializer:
    def test_valid_first_message(self):
        serializer = ChatRequestSerializer(
            data={"message": "Book appointment", "conversation_history": []}
        )
        assert serializer.is_valid(), serializer.errors

    def test_valid_with_history(self):
        serializer = ChatRequestSerializer(
            data={
                "message": "Yes, column 3",
                "conversation_history": [
                    {"role": "user", "content": "Book at 2pm"},
                    {"role": "assistant", "content": "Which column?"},
                ],
            }
        )
        assert serializer.is_valid(), serializer.errors

    def test_rejects_missing_message(self):
        serializer = ChatRequestSerializer(data={"conversation_history": []})
        assert not serializer.is_valid()
        assert "message" in serializer.errors

    def test_defaults_empty_history(self):
        serializer = ChatRequestSerializer(data={"message": "hello"})
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["conversation_history"] == []

    def test_rejects_invalid_role_in_history(self):
        serializer = ChatRequestSerializer(
            data={
                "message": "hello",
                "conversation_history": [
                    {"role": "admin", "content": "bad role"},
                ],
            }
        )
        assert not serializer.is_valid()
