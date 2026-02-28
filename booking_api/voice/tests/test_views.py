from unittest.mock import MagicMock, patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from openai import OpenAIError

# ---------------------------------------------------------------------------
# TranscribeView
# ---------------------------------------------------------------------------


class TestTranscribeView:
    @pytest.mark.django_db
    @patch("booking_api.voice.views.transcribe_audio")
    def test_transcribe_success(self, mock_transcribe, auth_client):
        mock_transcribe.return_value = "Book Ellie at 3pm"
        audio = SimpleUploadedFile(
            "test.webm", b"fake-audio-data", content_type="audio/webm"
        )

        response = auth_client.post(
            "/voice/transcribe/", {"audio": audio}, format="multipart"
        )

        assert response.status_code == 200
        assert response.data["text"] == "Book Ellie at 3pm"
        mock_transcribe.assert_called_once()

    @pytest.mark.django_db
    def test_transcribe_requires_auth(self, client):
        audio = SimpleUploadedFile("test.webm", b"data", content_type="audio/webm")
        response = client.post("/voice/transcribe/", {"audio": audio})
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_transcribe_requires_audio_file(self, auth_client):
        response = auth_client.post("/voice/transcribe/", {}, format="multipart")
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_transcribe_rejects_large_file(self, auth_client):
        big = SimpleUploadedFile(
            "big.webm",
            b"x" * (10 * 1024 * 1024 + 1),
            content_type="audio/webm",
        )
        response = auth_client.post(
            "/voice/transcribe/", {"audio": big}, format="multipart"
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    @patch("booking_api.voice.views.transcribe_audio")
    def test_transcribe_handles_openai_error(self, mock_transcribe, auth_client):
        mock_transcribe.side_effect = OpenAIError("Service down")
        audio = SimpleUploadedFile("test.webm", b"data", content_type="audio/webm")

        response = auth_client.post(
            "/voice/transcribe/", {"audio": audio}, format="multipart"
        )

        assert response.status_code == 502
        assert "error" in response.data


# ---------------------------------------------------------------------------
# ChatView
# ---------------------------------------------------------------------------


class TestChatView:
    @pytest.mark.django_db
    @patch("booking_api.voice.views.chat_completion")
    def test_chat_simple_text_response(self, mock_chat, auth_client, salon):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "How can I help?"
        mock_response.choices[0].message.tool_calls = None
        mock_chat.return_value = mock_response

        response = auth_client.post(
            "/voice/chat/",
            {"message": "Hello", "conversation_history": []},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["reply"] == "How can I help?"
        assert len(response.data["conversation_history"]) == 2

    @pytest.mark.django_db
    @patch("booking_api.voice.views.chat_completion")
    @patch("booking_api.voice.views.execute_tool_call")
    def test_chat_with_tool_call(self, mock_execute, mock_chat, auth_client, salon):
        # First call: GPT-4 wants to call lookup_customer
        tool_call_response = MagicMock()
        tool_call = MagicMock()
        tool_call.id = "call_123"
        tool_call.type = "function"
        tool_call.function.name = "lookup_customer"
        tool_call.function.arguments = '{"phone_number": "+447700900123"}'
        tool_call_response.choices[0].message.content = ""
        tool_call_response.choices[0].message.tool_calls = [tool_call]

        # Second call: GPT-4 returns final text
        text_response = MagicMock()
        text_response.choices[0].message.content = "Found Ellie Smith."
        text_response.choices[0].message.tool_calls = None

        mock_chat.side_effect = [tool_call_response, text_response]
        mock_execute.return_value = (
            '{"found": true, "customer_id": 1, "full_name": "Ellie Smith"}'
        )

        response = auth_client.post(
            "/voice/chat/",
            {
                "message": "Look up 07700900123",
                "conversation_history": [],
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.data["reply"] == "Found Ellie Smith."
        mock_execute.assert_called_once()

    @pytest.mark.django_db
    @patch("booking_api.voice.views.chat_completion")
    @patch("booking_api.voice.views.execute_tool_call")
    def test_chat_multi_tool_calls(self, mock_execute, mock_chat, auth_client, salon):
        """GPT-4 calls lookup, then check_availability, then replies."""
        # Round 1: lookup_customer
        r1 = MagicMock()
        tc1 = MagicMock()
        tc1.id = "call_1"
        tc1.type = "function"
        tc1.function.name = "lookup_customer"
        tc1.function.arguments = '{"phone_number": "+447700900123"}'
        r1.choices[0].message.content = ""
        r1.choices[0].message.tool_calls = [tc1]

        # Round 2: check_availability
        r2 = MagicMock()
        tc2 = MagicMock()
        tc2.id = "call_2"
        tc2.type = "function"
        tc2.function.name = "check_availability"
        tc2.function.arguments = '{"date": "2026-03-01", "time": "14:00"}'
        r2.choices[0].message.content = ""
        r2.choices[0].message.tool_calls = [tc2]

        # Round 3: final text
        r3 = MagicMock()
        r3.choices[0].message.content = "Columns 1, 3, 5 are available."
        r3.choices[0].message.tool_calls = None

        mock_chat.side_effect = [r1, r2, r3]
        mock_execute.side_effect = [
            '{"found": true, "customer_id": 1, "full_name": "Ellie"}',
            '{"available_columns": [1, 3, 5], "busy_columns": {}}',
        ]

        response = auth_client.post(
            "/voice/chat/",
            {"message": "Book Ellie at 2pm", "conversation_history": []},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["reply"] == "Columns 1, 3, 5 are available."
        assert mock_execute.call_count == 2

    @pytest.mark.django_db
    def test_chat_requires_auth(self, client):
        response = client.post(
            "/voice/chat/",
            {"message": "hello", "conversation_history": []},
            format="json",
        )
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_chat_requires_salon(self, db):
        """User with no salon gets 400."""
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken

        from user.models import ExtendedUser

        no_salon_user = ExtendedUser.objects.create_user(
            email="nosalonuser@test.com",
            password="testpass123",
            full_name="No Salon",
        )
        api_client = APIClient()
        token = RefreshToken.for_user(no_salon_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

        response = api_client.post(
            "/voice/chat/",
            {"message": "hello", "conversation_history": []},
            format="json",
        )
        assert response.status_code == 400
        assert "salon" in response.data["error"].lower()

    @pytest.mark.django_db
    @patch("booking_api.voice.views.chat_completion")
    def test_chat_includes_system_prompt(self, mock_chat, auth_client, salon):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Hi"
        mock_response.choices[0].message.tool_calls = None
        mock_chat.return_value = mock_response

        auth_client.post(
            "/voice/chat/",
            {"message": "hello", "conversation_history": []},
            format="json",
        )

        messages = mock_chat.call_args[0][0]
        assert messages[0]["role"] == "system"
        assert salon.name in messages[0]["content"]

    @pytest.mark.django_db
    @patch("booking_api.voice.views.chat_completion")
    def test_chat_appends_user_message(self, mock_chat, auth_client, salon):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Ok"
        mock_response.choices[0].message.tool_calls = None
        mock_chat.return_value = mock_response

        auth_client.post(
            "/voice/chat/",
            {"message": "Book at 3pm", "conversation_history": []},
            format="json",
        )

        messages = mock_chat.call_args[0][0]
        assert messages[-1] == {"role": "user", "content": "Book at 3pm"}

    @pytest.mark.django_db
    @patch("booking_api.voice.views.chat_completion")
    def test_chat_preserves_conversation_history(self, mock_chat, auth_client, salon):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Column 3 it is."
        mock_response.choices[0].message.tool_calls = None
        mock_chat.return_value = mock_response

        history = [
            {"role": "user", "content": "Book at 2pm"},
            {"role": "assistant", "content": "Which column?"},
        ]

        auth_client.post(
            "/voice/chat/",
            {
                "message": "Column 3 please",
                "conversation_history": history,
            },
            format="json",
        )

        messages = mock_chat.call_args[0][0]
        # system + 2 history + 1 new user message = 4
        assert len(messages) == 4
        assert messages[1]["content"] == "Book at 2pm"
        assert messages[2]["content"] == "Which column?"

    @pytest.mark.django_db
    @patch("booking_api.voice.views.chat_completion")
    def test_chat_max_rounds_safety(self, mock_chat, auth_client, salon):
        infinite_response = MagicMock()
        tc = MagicMock()
        tc.id = "call_loop"
        tc.type = "function"
        tc.function.name = "lookup_customer"
        tc.function.arguments = '{"phone_number": "+447700900123"}'
        infinite_response.choices[0].message.content = ""
        infinite_response.choices[0].message.tool_calls = [tc]
        mock_chat.return_value = infinite_response

        with patch(
            "booking_api.voice.views.execute_tool_call",
            return_value='{"found": false}',
        ):
            response = auth_client.post(
                "/voice/chat/",
                {"message": "test", "conversation_history": []},
                format="json",
            )

        assert response.status_code == 200
        assert "try again" in response.data["reply"].lower()
        assert mock_chat.call_count == 5

    @pytest.mark.django_db
    @patch("booking_api.voice.views.chat_completion")
    def test_chat_handles_openai_error(self, mock_chat, auth_client, salon):
        mock_chat.side_effect = OpenAIError("API error")

        response = auth_client.post(
            "/voice/chat/",
            {"message": "hello", "conversation_history": []},
            format="json",
        )

        assert response.status_code == 502
        assert "error" in response.data

    @pytest.mark.django_db
    @patch("booking_api.voice.views.chat_completion")
    def test_chat_response_excludes_system_prompt(self, mock_chat, auth_client, salon):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Hi there"
        mock_response.choices[0].message.tool_calls = None
        mock_chat.return_value = mock_response

        response = auth_client.post(
            "/voice/chat/",
            {"message": "hello", "conversation_history": []},
            format="json",
        )

        history = response.data["conversation_history"]
        for msg in history:
            assert msg.get("role") != "system"
