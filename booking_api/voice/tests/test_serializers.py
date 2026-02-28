from django.core.files.uploadedfile import SimpleUploadedFile

from booking_api.voice.serializers import TranscribeRequestSerializer

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
