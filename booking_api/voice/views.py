import logging
from typing import ClassVar

from openai import OpenAIError
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .openai_client import transcribe_audio
from .serializers import TranscribeRequestSerializer

logger = logging.getLogger(__name__)


class TranscribeView(APIView):
    parser_classes: ClassVar[list] = [MultiPartParser]

    def post(self, request):
        serializer = TranscribeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        audio_file = serializer.validated_data["audio"]
        language = serializer.validated_data["language"]

        try:
            text = transcribe_audio(audio_file, language=language)
        except OpenAIError as exc:
            logger.exception("Transcription failed")
            return Response(
                {"error": f"Transcription failed: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"text": text}, status=status.HTTP_200_OK)


class ChatView(APIView):
    pass
