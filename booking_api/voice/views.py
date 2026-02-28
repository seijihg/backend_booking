import json
import logging
from typing import ClassVar

import arrow
from openai import OpenAIError
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .openai_client import chat_completion, transcribe_audio
from .prompts import SYSTEM_PROMPT
from .serializers import ChatRequestSerializer, TranscribeRequestSerializer
from .tool_executor import execute_tool_call
from .tools import TOOL_DEFINITIONS

logger = logging.getLogger(__name__)

MAX_TOOL_CALL_ROUNDS = 5


class TranscribeView(APIView):
    parser_classes: ClassVar[list] = [MultiPartParser]
    permission_classes: ClassVar[list] = [IsAuthenticated]

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
    permission_classes: ClassVar[list] = [IsAuthenticated]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data["message"]
        conversation_history = serializer.validated_data["conversation_history"]

        # Get salon
        salon = request.user.salons.first()
        if not salon:
            return Response(
                {"error": "No salon associated with your account."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Build system prompt
        system_message = {
            "role": "system",
            "content": SYSTEM_PROMPT.format(
                current_datetime=arrow.now().format("YYYY-MM-DD HH:mm"),
                salon_name=salon.name,
                salon_id=salon.id,
                user_name=request.user.full_name or request.user.email,
            ),
        }

        # Assemble messages: system + history + new user message
        messages = [system_message]
        for msg in conversation_history:
            messages.append(msg)
        messages.append({"role": "user", "content": message})

        # Track history without system prompt for response
        history = list(messages[1:])

        try:
            reply_text = self._tool_call_loop(messages, salon, request.user)
        except OpenAIError as exc:
            logger.exception("Chat failed")
            return Response(
                {"error": f"Chat failed: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Add final assistant reply to history
        history.append({"role": "assistant", "content": reply_text})

        return Response(
            {"reply": reply_text, "conversation_history": history},
            status=status.HTTP_200_OK,
        )

    def _tool_call_loop(self, messages, salon, user):
        for _round in range(MAX_TOOL_CALL_ROUNDS):
            response = chat_completion(messages, TOOL_DEFINITIONS)
            choice = response.choices[0].message

            if not choice.tool_calls:
                return choice.content or ""

            # Append assistant message with tool calls
            assistant_msg = {
                "role": "assistant",
                "content": choice.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in choice.tool_calls
                ],
            }
            messages.append(assistant_msg)

            # Execute each tool call and append results
            for tc in choice.tool_calls:
                args = json.loads(tc.function.arguments)
                result = execute_tool_call(tc.function.name, args, salon, user)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    }
                )

        return (
            "I'm having trouble processing your request. "
            "Please try again with a simpler instruction."
        )
