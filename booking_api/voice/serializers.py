from rest_framework import serializers

MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_AUDIO_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/wav",
    "audio/x-wav",
    "audio/webm",
    "audio/ogg",
    "audio/x-m4a",
    "audio/m4a",
}


class TranscribeRequestSerializer(serializers.Serializer):
    audio = serializers.FileField(required=True)
    language = serializers.CharField(default="en", required=False)

    def validate_audio(self, value):
        if value.size > MAX_AUDIO_SIZE:
            raise serializers.ValidationError(
                f"File too large. Max size is {MAX_AUDIO_SIZE // (1024 * 1024)} MB."
            )
        if value.content_type not in ALLOWED_AUDIO_TYPES:
            raise serializers.ValidationError(
                f"Unsupported audio format: {value.content_type}. "
                f"Allowed: mp3, mp4, wav, webm, ogg, m4a."
            )
        return value


class TranscribeResponseSerializer(serializers.Serializer):
    text = serializers.CharField()


VALID_ROLES = {"user", "assistant", "tool", "system"}


class MessageSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=list(VALID_ROLES))
    content = serializers.CharField(allow_blank=True, required=False, default="")
    tool_call_id = serializers.CharField(required=False)
    tool_calls = serializers.ListField(child=serializers.DictField(), required=False)


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(required=True)
    conversation_history = MessageSerializer(many=True, required=False, default=[])


class ChatResponseSerializer(serializers.Serializer):
    reply = serializers.CharField()
    conversation_history = serializers.ListField(child=serializers.DictField())
