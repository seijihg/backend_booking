# Voice Booking Feature - Full Specification

## Context

Salon staff need a faster way to book appointments while working with clients. Instead of manually navigating the UI, they'll speak into a microphone ("Book Ellie, 07xxx, tomorrow at 3pm for 30 minutes"), and the system will transcribe the audio, parse intent via GPT-4 function calling, look up/create customers, check availability, and book appointments -- all through a conversational interface displayed as text on screen.

## Requirements Summary

| Decision | Answer |
|----------|--------|
| **User** | Salon staff/owner (authenticated via JWT) |
| **Platform** | Web browser (existing frontend) |
| **STT** | OpenAI Whisper API |
| **AI Chat** | OpenAI GPT-4 with function calling |
| **Response** | Text on screen (no TTS) |
| **Conversation** | Single-turn AND multi-turn, ephemeral (no DB storage) |
| **Salon scope** | Logged-in user's single salon (one email = one salon) |
| **Customer ID** | Phone number is primary identifier (UK format) |
| **Columns** | Fixed 5 per salon (represents staff members) |
| **Availability** | Check existing appointments for column_id + time range overlap |
| **Duration** | User specifies in 15-min blocks (15, 30, 45, 60...), default 60 min |
| **Conflicts** | Report conflict + offer available column options |
| **Invalid phone** | AI re-prompts for correct number |
| **AI provider** | OpenAI only (GPT-4o + Whisper) |
| **New Django app** | No -- add as `booking_api/voice/` package |

---

## Architecture

```
Browser: [Mic Button] → MediaRecorder API → audio blob
                ↓
Django:  POST /voice/transcribe/  →  OpenAI Whisper  →  text
                ↓
Browser: displays transcript, sends text + history
                ↓
Django:  POST /voice/chat/  →  GPT-4 (function calling)
              ↓ tool calls loop (max 5 rounds)
              ├─ lookup_customer(phone)    → Customer.objects.filter()
              ├─ create_customer(name,ph)  → Customer.objects.create()
              ├─ check_availability(...)   → Appointment overlap query
              └─ create_appointment(...)   → Appointment.save() (triggers SMS)
              ↓
Browser: displays AI reply, stores updated conversation_history in state
```

Conversation is ephemeral -- frontend sends full message history each request, nothing stored in DB. API keys stay on the server.

---

## Files to Create

| File | Purpose |
|------|---------|
| `booking_api/voice/__init__.py` | Package init (empty) |
| `booking_api/voice/urls.py` | URL routing: `transcribe/` and `chat/` |
| `booking_api/voice/views.py` | `TranscribeView` and `ChatView` API views |
| `booking_api/voice/serializers.py` | Request/response validation for both endpoints |
| `booking_api/voice/openai_client.py` | Lazy singleton OpenAI client, `transcribe_audio()`, `chat_completion()` |
| `booking_api/voice/tools.py` | GPT-4 function calling tool definitions (4 tools) |
| `booking_api/voice/tool_executor.py` | Dispatches tool calls to Django ORM operations |
| `booking_api/voice/prompts.py` | System prompt constant |
| `.claude/docs/voice-booking-frontend-spec.md` | Frontend integration spec |

## Files to Modify

| File | Line | Change |
|------|------|--------|
| `requirements.in` | After line 30 | Add `openai>=1.40.0` |
| `requirements.txt` | All | Re-compile via `pip-compile requirements.in` |
| `booking_api/settings.py` | After line 235 | Add `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_WHISPER_MODEL` |
| `booking_api/urls.py` | Line 44 | Add `path("voice/", include("booking_api.voice.urls"))` |
| `.env.example` | After line 16 | Add `OPENAI_API_KEY=` |
| `docker-compose.yml` | After line 46 | Add `OPENAI_API_KEY` env var to web service |

---

## Progress Checklist

### Implementation Steps

- [x] **Step 1: Dependencies & Settings**
  - [x] Add `openai>=1.40.0` to `requirements.in`
  - [x] Add `openai>=1.40.0` to `requirements.txt` and install
  - [x] Add `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_WHISPER_MODEL` to `booking_api/settings.py`
  - [x] Add `OPENAI_API_KEY=` to `.env.example`
  - [x] Add `OPENAI_API_KEY` env var to `docker-compose.yml` (web service)

- [x] **Step 2: Package Structure & URL Routing**
  - [x] Create `booking_api/voice/__init__.py`
  - [x] Create `booking_api/voice/urls.py` with `transcribe/` and `chat/` routes
  - [x] Create `booking_api/voice/views.py` (stub views)
  - [x] Add `path("voice/", ...)` to `booking_api/urls.py`
  - [x] Verify URL routing resolves (`/voice/transcribe/`, `/voice/chat/`)

- [x] **Step 3: OpenAI Client Module**
  - [x] Create `booking_api/voice/openai_client.py` (singleton, `transcribe_audio()`, `chat_completion()`)
  - [x] Add dummy OpenAI settings to `booking_api/test_settings.py`
  - [x] Create `booking_api/voice/tests/test_openai_client.py` (7 tests, all passing)

- [x] **Step 4: Transcribe Endpoint** (serializers + view)
  - [x] Create `booking_api/voice/serializers.py` (`TranscribeRequestSerializer`, `TranscribeResponseSerializer`)
  - [x] Implement `TranscribeView` in `booking_api/voice/views.py`
  - [x] Create `booking_api/voice/tests/test_serializers.py` (12 tests, all passing)

- [x] **Step 5: Tool Definitions & System Prompt**
  - [x] Create `booking_api/voice/tools.py` (4 GPT-4 function calling tool definitions)
  - [x] Create `booking_api/voice/prompts.py` (system prompt constant)

- [x] **Step 6: Tool Executor**
  - [x] Create `booking_api/voice/tool_executor.py` (dispatcher + 4 handlers)
  - [x] Create `booking_api/voice/tests/test_tool_executor.py` (29 tests)

- [x] **Step 7: Chat Endpoint** (serializers + view)
  - [x] Add `MessageSerializer`, `ChatRequestSerializer`, `ChatResponseSerializer` to serializers
  - [x] Implement `ChatView` in `booking_api/voice/views.py` (tool-call loop)
  - [x] Add chat serializer tests to `test_serializers.py`
  - [x] Create `booking_api/voice/tests/test_views.py` (16 tests)
  - [x] Manual end-to-end testing (full booking flow verified)

- [ ] **Step 8: Frontend Spec Document**
  - [ ] Create `.claude/docs/voice-booking-frontend-spec.md`

- [ ] **Step 9: Update CLAUDE.md**
  - [ ] Add voice booking section to project documentation

### Test Infrastructure (pre-existing)

- [x] `conftest.py` (project root) -- SMS mocking
- [x] `booking_api/voice/tests/__init__.py` -- test package
- [x] `booking_api/voice/tests/conftest.py` -- shared fixtures (salon, user, customer, auth_client)
- [x] `booking_api/test_settings.py` -- SQLite, stub broker, dummy credentials
- [x] `pyproject.toml` -- pytest config with `DJANGO_SETTINGS_MODULE`

---

## Implementation Details

### Step 1: Dependencies & Settings

**`requirements.in`** -- add after twilio line:
```
openai>=1.40.0
```

Then run: `pip-compile requirements.in && pip install -r requirements.txt`

**`booking_api/settings.py`** -- add after `TWILIO_PHONE_NUMBER` (line 235):
```python
# OpenAI (Voice Booking)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
OPENAI_WHISPER_MODEL = os.environ.get("OPENAI_WHISPER_MODEL", "whisper-1")
```

**`.env.example`** -- add after Twilio section:
```
# OpenAI (Voice Booking)
OPENAI_API_KEY=
```

**`docker-compose.yml`** -- add to web service environment after TWILIO vars:
```yaml
- OPENAI_API_KEY=${OPENAI_API_KEY:-}
```

---

### Step 2: Package Structure & URL Routing

**`booking_api/voice/__init__.py`** -- empty file

**`booking_api/voice/urls.py`**:
```python
from django.urls import path
from .views import TranscribeView, ChatView

app_name = "voice"
urlpatterns = [
    path("transcribe/", TranscribeView.as_view(), name="transcribe"),
    path("chat/", ChatView.as_view(), name="chat"),
]
```

**`booking_api/urls.py`** -- add before closing bracket:
```python
path("voice/", include("booking_api.voice.urls")),
```

---

### Step 3: OpenAI Client (`booking_api/voice/openai_client.py`)

```python
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
        file=audio_file,
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
```

---

### Step 4: GPT-4 Tool Definitions (`booking_api/voice/tools.py`)

Four function calling tools:

#### 1. `lookup_customer`
```json
{
  "type": "function",
  "function": {
    "name": "lookup_customer",
    "description": "Look up an existing customer by phone number in the salon's customer list.",
    "parameters": {
      "type": "object",
      "properties": {
        "phone_number": {
          "type": "string",
          "description": "Customer phone number in E.164 format (e.g. '+447700900123')."
        }
      },
      "required": ["phone_number"],
      "additionalProperties": false
    }
  }
}
```

#### 2. `create_customer`
```json
{
  "type": "function",
  "function": {
    "name": "create_customer",
    "description": "Create a new customer record in the salon. Only call after lookup_customer returns not found.",
    "parameters": {
      "type": "object",
      "properties": {
        "full_name": { "type": "string", "description": "Customer's full name." },
        "phone_number": { "type": "string", "description": "Phone in E.164 format." }
      },
      "required": ["full_name", "phone_number"],
      "additionalProperties": false
    }
  }
}
```

#### 3. `check_availability`
```json
{
  "type": "function",
  "function": {
    "name": "check_availability",
    "description": "Check if a time slot is available. Returns which columns (1-5) are free.",
    "parameters": {
      "type": "object",
      "properties": {
        "date": { "type": "string", "description": "Date in YYYY-MM-DD format." },
        "time": { "type": "string", "description": "Start time in HH:MM (24-hour) format." },
        "duration_minutes": { "type": "integer", "description": "Duration in minutes, multiple of 15. Default 60.", "default": 60 },
        "column_id": { "type": "integer", "description": "Optional specific column (1-5) to check.", "minimum": 1, "maximum": 5 }
      },
      "required": ["date", "time"],
      "additionalProperties": false
    }
  }
}
```

#### 4. `create_appointment`
```json
{
  "type": "function",
  "function": {
    "name": "create_appointment",
    "description": "Book an appointment. Always check_availability first.",
    "parameters": {
      "type": "object",
      "properties": {
        "customer_id": { "type": "integer", "description": "Customer's database ID." },
        "appointment_time": { "type": "string", "description": "ISO 8601 format (e.g. '2024-03-15T14:30:00Z')." },
        "duration_minutes": { "type": "integer", "description": "Duration in minutes, multiple of 15. Default 60.", "default": 60 },
        "column_id": { "type": "integer", "description": "Column/staff member (1-5).", "minimum": 1, "maximum": 5 },
        "comment": { "type": "string", "description": "Optional booking notes.", "default": "" }
      },
      "required": ["customer_id", "appointment_time", "column_id"],
      "additionalProperties": false
    }
  }
}
```

---

### Step 5: System Prompt (`booking_api/voice/prompts.py`)

```python
SYSTEM_PROMPT = """You are a booking assistant for salon staff. You help them book appointments by voice.

## Your Role
- You assist salon STAFF (not end customers) in creating appointments.
- Be concise and professional. Staff are busy - keep responses short.

## Booking Workflow
1. **Identify the customer** by phone number (ALWAYS ask for phone number first)
2. **Look up the customer** using lookup_customer. If not found, ask for name and use create_customer.
3. **Get appointment details**: date, time, duration (default 60 min), and column/staff preference.
4. **Check availability** using check_availability before booking.
5. **Book the appointment** using create_appointment.

## Rules
- Phone numbers must be UK format with country code (e.g., +447700900123). If user says "07700900123", convert to "+447700900123".
- Duration must be in 15-minute blocks: 15, 30, 45, 60, 75, 90, etc. Default is 60 minutes.
- There are 5 columns (staff positions numbered 1-5). If not specified, check all columns.
- If a time slot is busy, report the conflict and suggest available columns.
- If ALL columns are busy, suggest trying a different time.
- Never fabricate appointment data. Only confirm after create_appointment succeeds.
- If phone number is invalid, ask the user to repeat it.
- Ask ONE question at a time for missing info.

## Context
Current date/time: {current_datetime}
Salon: {salon_name} (ID: {salon_id})
Staff user: {user_name}
"""
```

---

### Step 6: Tool Executor (`booking_api/voice/tool_executor.py`)

Dispatcher function `execute_tool_call(tool_name, arguments, salon, user)` routes to four handlers:

#### `_handle_lookup_customer(args, salon, user)`
```python
Customer.objects.filter(salons=salon, phone_number=phone_number).first()
# Returns: {"found": true, "customer_id": 42, "full_name": "Ellie", "phone_number": "+447..."}
# Or:      {"found": false, "message": "No customer found with phone number..."}
```

#### `_handle_create_customer(args, salon, user)`
```
# Check existing first to avoid duplicates
existing = Customer.objects.filter(salons=salon, phone_number=phone_number).first()
if existing: return {"created": false, "customer_id": existing.id, ...}

customer = Customer.objects.create(full_name=full_name, phone_number=phone_number)
customer.salons.add(salon)
# Returns: {"created": true, "customer_id": ..., "full_name": ..., "phone_number": ...}
```

#### `_handle_check_availability(args, salon, user)`
```python
# For each column in [1,2,3,4,5] (or specific column_id):
# Find overlapping: existing.start < requested.end AND existing.end > requested.start
Appointment.objects.filter(
    salon=salon,
    column_id=col,
    appointment_time__lt=end_dt,
    appointment_time__date=start_dt.date(),
).exclude(end_time__lte=start_dt)

# Handle null end_time by assuming 60-min default
# Returns: {"available_columns": [1, 3, 5], "busy_columns": {2: ["14:00-15:00"], 4: ["13:30-14:30"]}}
```

#### `_handle_create_appointment(args, salon, user)`
```python
# Validate customer belongs to salon, column 1-5, duration multiple of 15, not in past
appointment = Appointment(
    salon=salon,
    user=user,
    customer=customer,
    appointment_time=start_dt,
    end_time=start_dt + timedelta(minutes=duration),
    column_id=column_id,
    comment=comment,
)
appointment.save()  # Existing save() auto-triggers SMS confirmation + reminder
# Returns: {"created": true, "appointment_id": ..., "message": "Appointment booked for..."}
```

All handlers return JSON strings. Errors return `{"error": "..."}` so GPT-4 handles them conversationally.

---

### Step 7: Serializers (`booking_api/voice/serializers.py`)

**TranscribeRequestSerializer**: Validates `audio` file (max 10MB, allowed audio MIME types: mp3, mp4, wav, webm, ogg, m4a) + optional `language` (default "en").

**TranscribeResponseSerializer**: `{"text": "..."}`

**MessageSerializer**: Validates conversation history messages with `role` (user/assistant/tool), `content`, optional `tool_call_id`, optional `tool_calls` list.

**ChatRequestSerializer**: `message` (string, required) + `conversation_history` (list of MessageSerializer, optional, default []).

**ChatResponseSerializer**: `reply` (string) + `conversation_history` (list of dicts - updated history for frontend to store).

---

### Step 8: Views (`booking_api/voice/views.py`)

#### `TranscribeView` (POST /voice/transcribe/)
- `parser_classes = [MultiPartParser]`
- Validates request via `TranscribeRequestSerializer`
- Calls `transcribe_audio(audio_file, language)`
- Returns `{"text": "transcribed text"}` (200)
- Returns `{"error": "Transcription failed: ..."}` (502) on OpenAI errors

#### `ChatView` (POST /voice/chat/)
1. Validate request via `ChatRequestSerializer`
2. Get salon: `request.user.salons.first()` -- returns 400 if no salon
3. Build system prompt with `arrow.now()`, salon name/id, user name
4. Assemble: `[system_prompt] + conversation_history + [new user message]`
5. **Tool-call loop** (max 5 rounds):
   - Call `chat_completion(messages, TOOL_DEFINITIONS)`
   - If `tool_calls` in response: execute each via `execute_tool_call()`, append results, continue
   - If text response (no tool calls): break with final reply
6. Return `{"reply": "...", "conversation_history": [updated history without system prompt]}`

---

## API Contracts

### POST /voice/transcribe/

**Auth**: JWT required
**Content-Type**: multipart/form-data

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `audio` | File | Yes | Audio file (MP3, WAV, WEBM, OGG, M4A). Max 10 MB |
| `language` | String | No | ISO-639-1 code. Default: "en" |

**Response 200:**
```json
{ "text": "Book an appointment for John at 2pm tomorrow" }
```

**Response 502:**
```json
{ "error": "Transcription failed: <detail>" }
```

---

### POST /voice/chat/

**Auth**: JWT required
**Content-Type**: application/json

**First request:**
```json
{
  "message": "Book appointment for 07700900123 tomorrow at 2pm",
  "conversation_history": []
}
```

**Follow-up request** (multi-turn):
```json
{
  "message": "Yes, column 3 please",
  "conversation_history": [
    {"role": "user", "content": "Book appointment for 07700900123 tomorrow at 2pm"},
    {"role": "assistant", "content": "", "tool_calls": [{"id": "call_abc", "type": "function", "function": {"name": "lookup_customer", "arguments": "{\"phone_number\": \"+447700900123\"}"}}]},
    {"role": "tool", "tool_call_id": "call_abc", "content": "{\"found\": true, \"customer_id\": 42, \"full_name\": \"Jane Smith\"}"},
    {"role": "assistant", "content": "Found Jane Smith. Columns 1, 3, 5 are available at 2pm tomorrow. Which column?"}
  ]
}
```

**Response 200:**
```json
{
  "reply": "Appointment booked for Jane Smith on 2024-03-15 at 14:00 (column 3, 60 minutes).",
  "conversation_history": [
    "... all previous messages ...",
    {"role": "user", "content": "Yes, column 3 please"},
    {"role": "assistant", "content": "", "tool_calls": [...]},
    {"role": "tool", "tool_call_id": "...", "content": "{...}"},
    {"role": "assistant", "content": "Appointment booked for Jane Smith..."}
  ]
}
```

**Response 400:**
```json
{ "error": "No salon associated with your account." }
```

**Response 502:**
```json
{ "error": "Chat failed: <detail>" }
```

---

## Error Handling Strategy

| Layer | Behavior |
|-------|----------|
| **Serializer validation** (400) | Malformed requests -- DRF handles automatically |
| **Tool execution errors** | Returned as `{"error": "..."}` in tool response -- GPT-4 reads it and responds conversationally (e.g., "That phone number doesn't look right") |
| **OpenAI API errors** (502) | Caught in view, returned as `{"error": "..."}` -- frontend shows "Service unavailable" |
| **Safety limit** | Max 5 tool-call rounds. If exceeded, returns fallback "please try again" message |
| **Race condition** | Availability check is advisory. Two simultaneous bookings for same slot will both succeed (matches current behavior -- no DB unique constraint on column+time) |

---

## Frontend Specification

### UI Components
- **Mic button**: Uses browser `MediaRecorder` API to record audio (`audio/webm` format)
- **Chat panel**: Displays conversation messages (user transcripts + AI replies)
- **Text input fallback**: Optional typing instead of speaking
- **Loading indicator**: Show during transcription (1-2s) and chat processing (2-5s)
- **"New Conversation" button**: Resets `conversationHistory` state

### State Management (React)
```typescript
interface VoiceBookingState {
  conversationHistory: Message[];  // From API response, stored in component state
  isRecording: boolean;
  isProcessing: boolean;
  currentTranscript: string;
}
```

### Flow
1. User clicks mic -> browser records audio -> stops recording
2. Frontend sends audio blob to `POST /voice/transcribe/` as `multipart/form-data`
3. Transcribed text displayed in chat panel
4. Frontend sends text + `conversationHistory` to `POST /voice/chat/`
5. AI reply displayed; `conversation_history` from response stored in state
6. For follow-ups: repeat from step 1, passing stored history

### Audio Recording (MediaRecorder API)
```javascript
const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
const chunks = [];
mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
mediaRecorder.onstop = () => {
  const blob = new Blob(chunks, { type: 'audio/webm' });
  // Send blob as FormData to /voice/transcribe/
};
```

### Error Handling
- **400**: Display validation error message
- **502**: Display "Voice service temporarily unavailable"
- **Network error**: Display "Connection error, please try again"

### Auth
All requests include JWT token via cookie (existing auth mechanism). No additional auth needed.

---

## Verification Plan

1. **Transcribe endpoint**: Upload audio file via curl, verify text returned
2. **Chat single-turn**: Send "Book customer 07700900123 tomorrow at 2pm" -- verify tool calls execute
3. **Chat multi-turn**: Send follow-up with conversation_history -- verify context maintained
4. **End-to-end**: Audio -> transcribe -> chat -> verify customer + appointment in DB
5. **Edge cases**: Invalid phone, past time, all columns busy, null end_time appointments
6. **Regression**: Run `pytest` to ensure nothing breaks
7. **Lint**: `black . && ruff check . --fix`

---

## Implementation Order

1. Dependencies & settings
2. Package structure & URL routing
3. OpenAI client module
4. Transcribe endpoint (serializers + view) -- test independently
5. Tool definitions & system prompt
6. Tool executor -- test each handler via Django shell
7. Chat endpoint (serializers + view) -- test full loop
8. Frontend spec document
9. Update CLAUDE.md

---

## Unit Test Plan

### Test Infrastructure Setup

No tests currently exist in the project. We need to create:

| File | Purpose |
|------|---------|
| `booking_api/voice/tests/__init__.py` | Test package |
| `booking_api/voice/tests/conftest.py` | Shared fixtures (salon, user, customer, appointments) |
| `booking_api/voice/tests/test_serializers.py` | Serializer validation tests |
| `booking_api/voice/tests/test_tool_executor.py` | Tool execution logic tests (heaviest test file) |
| `booking_api/voice/tests/test_views.py` | API endpoint tests with mocked OpenAI |
| `booking_api/voice/tests/test_openai_client.py` | OpenAI client wrapper tests |
| `conftest.py` (project root) | Global pytest-django config |

**Root `conftest.py`** (needed since project has no pytest config):
```python
import django
from django.conf import settings

# pytest-django requires this
django_settings_module = "booking_api.settings"
```

Add to `pyproject.toml`:
```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "booking_api.settings"
pythonpath = ["."]
```

---

### Shared Fixtures (`conftest.py`)

```python
import pytest
from django.utils import timezone
from datetime import timedelta


@pytest.fixture
def salon(db):
    """Create a test salon."""
    from salon.models import Salon

    return Salon.objects.create(
        name="Test Salon",
        phone_number="+447700900000",
        reminder_time_minutes=60,
    )


@pytest.fixture
def user(db, salon):
    """Create an authenticated staff user linked to the salon."""
    from user.models import ExtendedUser

    u = ExtendedUser.objects.create_user(
        email="staff@test.com",
        password="testpass123",
        full_name="Test Staff",
    )
    u.salons.add(salon)
    return u


@pytest.fixture
def customer(db, salon):
    """Create a test customer linked to the salon."""
    from customer.models import Customer

    c = Customer.objects.create(
        full_name="Ellie Smith",
        phone_number="+447700900123",
    )
    c.salons.add(salon)
    return c


@pytest.fixture
def existing_appointment(db, salon, user, customer):
    """Create an existing appointment for conflict testing."""
    from appointment.models import Appointment

    start = timezone.now() + timedelta(days=1, hours=2)
    return Appointment.objects.create(
        salon=salon,
        user=user,
        customer=customer,
        appointment_time=start,
        end_time=start + timedelta(minutes=60),
        column_id=2,
    )


@pytest.fixture
def auth_client(client, user):
    """DRF API client with JWT authentication."""
    from rest_framework.test import APIClient
    from rest_framework_simplejwt.tokens import RefreshToken

    api_client = APIClient()
    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client
```

---

### Step 3 Tests: OpenAI Client (`test_openai_client.py`)

Tests the lazy singleton and wrapper functions. All OpenAI calls are mocked.

| # | Test | What it verifies |
|---|------|-----------------|
| 1 | `test_get_client_raises_without_api_key` | `ValueError` raised when `OPENAI_API_KEY` is empty |
| 2 | `test_get_client_creates_singleton` | Same client instance returned on repeated calls |
| 3 | `test_transcribe_audio_calls_whisper` | `client.audio.transcriptions.create()` called with correct model and file |
| 4 | `test_transcribe_audio_returns_text` | Returns `.text` from Whisper response |
| 5 | `test_chat_completion_calls_gpt4` | `client.chat.completions.create()` called with messages, tools, `tool_choice="auto"` |
| 6 | `test_chat_completion_passes_model_from_settings` | Uses `settings.OPENAI_MODEL` value |

```python
# Example test pattern
from unittest.mock import patch, MagicMock


@pytest.mark.django_db
@patch("booking_api.voice.openai_client._client", None)  # Reset singleton
def test_get_client_raises_without_api_key(settings):
    settings.OPENAI_API_KEY = ""
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        get_openai_client()


@patch("booking_api.voice.openai_client.get_openai_client")
def test_transcribe_audio_calls_whisper(mock_get_client, settings):
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value.text = "Hello"
    mock_get_client.return_value = mock_client

    result = transcribe_audio(MagicMock(), language="en")

    assert result == "Hello"
    mock_client.audio.transcriptions.create.assert_called_once()
```

---

### Step 4 Tests: Serializers (`test_serializers.py`)

#### TranscribeRequestSerializer

| # | Test | Input | Expected |
|---|------|-------|----------|
| 1 | `test_valid_audio_file` | 1MB webm file | Valid |
| 2 | `test_rejects_missing_audio` | No file | ValidationError on `audio` |
| 3 | `test_rejects_oversized_file` | 11MB file | ValidationError "too large" |
| 4 | `test_rejects_invalid_mime_type` | `text/plain` file | ValidationError "Unsupported" |
| 5 | `test_accepts_all_valid_mime_types` | mp3, wav, webm, ogg, m4a | All valid |
| 6 | `test_default_language_is_en` | No language field | `language == "en"` |
| 7 | `test_custom_language` | `language="fr"` | `language == "fr"` |

```python
# Example
from django.core.files.uploadedfile import SimpleUploadedFile


def test_rejects_oversized_file():
    big_file = SimpleUploadedFile(
        "big.webm", b"x" * (11 * 1024 * 1024), content_type="audio/webm"
    )
    serializer = TranscribeRequestSerializer(data={"audio": big_file})
    assert not serializer.is_valid()
    assert "too large" in str(serializer.errors["audio"])
```

#### ChatRequestSerializer

| # | Test | Input | Expected |
|---|------|-------|----------|
| 8 | `test_valid_first_message` | `{"message": "hi", "conversation_history": []}` | Valid |
| 9 | `test_valid_with_history` | Message + history with user/assistant/tool roles | Valid |
| 10 | `test_rejects_missing_message` | No `message` field | ValidationError |
| 11 | `test_defaults_empty_history` | Only `message`, no `conversation_history` | History defaults to `[]` |
| 12 | `test_rejects_invalid_role` | History message with `role="admin"` | ValidationError |

#### MessageSerializer

| # | Test | Input | Expected |
|---|------|-------|----------|
| 13 | `test_valid_user_message` | `{"role": "user", "content": "hello"}` | Valid |
| 14 | `test_valid_tool_message` | `{"role": "tool", "content": "...", "tool_call_id": "call_x"}` | Valid |
| 15 | `test_valid_assistant_with_tool_calls` | `{"role": "assistant", "tool_calls": [...]}` | Valid |

---

### Step 6 Tests: Tool Executor (`test_tool_executor.py`)

This is the most critical test file -- these are pure Django ORM operations, no OpenAI mocking needed.

#### `lookup_customer` tests

| # | Test | Setup | Expected |
|---|------|-------|----------|
| 1 | `test_lookup_finds_existing_customer` | Customer with +447700900123 in salon | `{"found": true, "customer_id": ..., "full_name": "Ellie"}` |
| 2 | `test_lookup_not_found` | No matching customer | `{"found": false, "message": "No customer found..."}` |
| 3 | `test_lookup_scoped_to_salon` | Customer exists but in different salon | `{"found": false}` |
| 4 | `test_lookup_invalid_phone_format` | `"not-a-phone"` | `{"found": false, "message": "Invalid phone..."}` |

```python
@pytest.mark.django_db
def test_lookup_finds_existing_customer(salon, user, customer):
    result = json.loads(
        execute_tool_call(
            "lookup_customer",
            {"phone_number": "+447700900123"},
            salon,
            user,
        )
    )
    assert result["found"] is True
    assert result["customer_id"] == customer.id
    assert result["full_name"] == "Ellie Smith"


@pytest.mark.django_db
def test_lookup_scoped_to_salon(user, customer):
    """Customer in salon A should NOT be found when searching in salon B."""
    from salon.models import Salon

    other_salon = Salon.objects.create(name="Other", phone_number="+447700900999")
    result = json.loads(
        execute_tool_call(
            "lookup_customer",
            {"phone_number": "+447700900123"},
            other_salon,
            user,
        )
    )
    assert result["found"] is False
```

#### `create_customer` tests

| # | Test | Setup | Expected |
|---|------|-------|----------|
| 5 | `test_create_new_customer` | No existing customer | `{"created": true}`, customer in DB with salon |
| 6 | `test_create_returns_existing_if_duplicate` | Customer already exists | `{"created": false, "customer_id": existing.id}` |
| 7 | `test_create_adds_salon_association` | New customer | `customer.salons.filter(id=salon.id).exists()` is True |

```python
@pytest.mark.django_db
def test_create_new_customer(salon, user):
    result = json.loads(
        execute_tool_call(
            "create_customer",
            {"full_name": "New Person", "phone_number": "+447700900456"},
            salon,
            user,
        )
    )
    assert result["created"] is True
    assert Customer.objects.filter(phone_number="+447700900456").exists()
    customer = Customer.objects.get(id=result["customer_id"])
    assert customer.salons.filter(id=salon.id).exists()
```

#### `check_availability` tests

| # | Test | Setup | Expected |
|---|------|-------|----------|
| 8 | `test_all_columns_free` | No appointments on date | `available_columns: [1,2,3,4,5]` |
| 9 | `test_one_column_busy` | Appointment on column 2 at 14:00-15:00, query 14:00 | `available: [1,3,4,5]`, `busy: {2: [...]}` |
| 10 | `test_specific_column_free` | Query column 3, no conflicts | `available: [3]` |
| 11 | `test_specific_column_busy` | Appointment on column 1, query column 1 same time | `available: []`, `busy: {1: [...]}` |
| 12 | `test_overlap_start_inside_existing` | Existing 14:00-15:00, query 14:30 | Column is busy |
| 13 | `test_overlap_end_inside_existing` | Existing 14:00-15:00, query 13:30 for 60min | Column is busy |
| 14 | `test_adjacent_not_overlapping` | Existing 14:00-15:00, query 15:00 | Column is free |
| 15 | `test_null_end_time_assumes_60min` | Appointment at 14:00 with `end_time=None`, query 14:30 | Column is busy |
| 16 | `test_invalid_duration_not_multiple_of_15` | `duration_minutes: 25` | `{"error": "Duration must be..."}` |
| 17 | `test_invalid_date_format` | `date: "tomorrow"` | `{"error": "Invalid date/time..."}` |
| 18 | `test_default_duration_60` | No `duration_minutes` provided | Uses 60 minutes |

```python
@pytest.mark.django_db
def test_one_column_busy(salon, user, existing_appointment):
    """existing_appointment is on column 2. Other columns should be free."""
    appt_date = existing_appointment.appointment_time.strftime("%Y-%m-%d")
    appt_time = existing_appointment.appointment_time.strftime("%H:%M")

    result = json.loads(
        execute_tool_call(
            "check_availability",
            {"date": appt_date, "time": appt_time, "duration_minutes": 60},
            salon,
            user,
        )
    )
    assert 2 not in result["available_columns"]
    assert 2 in result["busy_columns"] or str(2) in result["busy_columns"]
    assert 1 in result["available_columns"]


@pytest.mark.django_db
def test_adjacent_not_overlapping(salon, user, existing_appointment):
    """Appointment ending at 15:00, query starting at 15:00 should be free."""
    end_time = existing_appointment.end_time
    result = json.loads(
        execute_tool_call(
            "check_availability",
            {
                "date": end_time.strftime("%Y-%m-%d"),
                "time": end_time.strftime("%H:%M"),
                "duration_minutes": 60,
                "column_id": existing_appointment.column_id,
            },
            salon,
            user,
        )
    )
    assert existing_appointment.column_id in result["available_columns"]
```

#### `create_appointment` tests

| # | Test | Setup | Expected |
|---|------|-------|----------|
| 19 | `test_create_appointment_success` | Valid customer, future time, free column | `{"created": true}`, appointment in DB |
| 20 | `test_creates_with_correct_end_time` | 30 min duration | `end_time == start + 30min` |
| 21 | `test_default_duration_60` | No `duration_minutes` | `end_time == start + 60min` |
| 22 | `test_rejects_past_time` | Appointment time in the past | `{"error": "Cannot book...past"}` |
| 23 | `test_rejects_invalid_column` | `column_id: 6` | `{"error": "column_id must be..."}` |
| 24 | `test_rejects_customer_not_in_salon` | Customer from different salon | `{"error": "Customer...not found"}` |
| 25 | `test_rejects_invalid_duration` | `duration_minutes: 25` | `{"error": "Duration must be..."}` |
| 26 | `test_saves_comment` | `comment: "Haircut"` | `appointment.comment == "Haircut"` |
| 27 | `test_appointment_triggers_sms` | Valid booking | `Appointment.save()` called (SMS handled by model) |

```python
@pytest.mark.django_db
def test_create_appointment_success(salon, user, customer):
    future_time = (timezone.now() + timedelta(days=1)).isoformat()
    result = json.loads(
        execute_tool_call(
            "create_appointment",
            {
                "customer_id": customer.id,
                "appointment_time": future_time,
                "duration_minutes": 30,
                "column_id": 3,
                "comment": "Haircut",
            },
            salon,
            user,
        )
    )
    assert result["created"] is True
    appt = Appointment.objects.get(id=result["appointment_id"])
    assert appt.column_id == 3
    assert appt.customer == customer
    assert appt.comment == "Haircut"
    assert appt.end_time == appt.appointment_time + timedelta(minutes=30)
```

#### `execute_tool_call` dispatcher tests

| # | Test | Input | Expected |
|---|------|-------|----------|
| 28 | `test_unknown_tool_returns_error` | `tool_name="delete_everything"` | `{"error": "Unknown tool..."}` |
| 29 | `test_exception_in_handler_returns_error` | Handler raises exception | `{"error": "..."}`, not a 500 |

---

### Step 7 & 8 Tests: Views (`test_views.py`)

All OpenAI calls are mocked. These test HTTP request/response handling.

#### TranscribeView tests

| # | Test | Setup | Expected |
|---|------|-------|----------|
| 1 | `test_transcribe_success` | Mock Whisper returns "hello" | 200, `{"text": "hello"}` |
| 2 | `test_transcribe_requires_auth` | No JWT token | 401 |
| 3 | `test_transcribe_requires_audio_file` | POST with no file | 400 |
| 4 | `test_transcribe_rejects_large_file` | 11MB file | 400 |
| 5 | `test_transcribe_handles_openai_error` | Mock raises OpenAI exception | 502, `{"error": "Transcription failed..."}` |

```python
@pytest.mark.django_db
@patch("booking_api.voice.views.transcribe_audio")
def test_transcribe_success(mock_transcribe, auth_client):
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
def test_transcribe_requires_auth(client):
    """Unauthenticated request should be rejected."""
    audio = SimpleUploadedFile("test.webm", b"data", content_type="audio/webm")
    response = client.post("/voice/transcribe/", {"audio": audio})
    assert response.status_code == 401
```

#### ChatView tests

| # | Test | Setup | Expected |
|---|------|-------|----------|
| 6 | `test_chat_simple_text_response` | Mock GPT-4 returns text (no tool calls) | 200, `reply` + `conversation_history` |
| 7 | `test_chat_with_tool_call` | Mock GPT-4 calls `lookup_customer` then replies | 200, tool was executed, history includes tool messages |
| 8 | `test_chat_multi_tool_calls` | Mock GPT-4 calls `lookup_customer` then `check_availability` then replies | 200, both tools executed |
| 9 | `test_chat_requires_auth` | No JWT | 401 |
| 10 | `test_chat_requires_salon` | User has no salon | 400, "No salon associated" |
| 11 | `test_chat_includes_system_prompt` | Mock GPT-4, inspect messages arg | System prompt is first message with salon name/datetime |
| 12 | `test_chat_appends_user_message` | Send "hello" | Messages passed to GPT-4 end with `{"role": "user", "content": "hello"}` |
| 13 | `test_chat_preserves_conversation_history` | Send history from previous turn | Messages include prior history |
| 14 | `test_chat_max_rounds_safety` | Mock GPT-4 always returns tool calls | Returns fallback message after 5 rounds |
| 15 | `test_chat_handles_openai_error` | Mock raises exception | 502 |
| 16 | `test_chat_response_excludes_system_prompt` | Any request | `conversation_history` in response has no system message |

```python
@pytest.mark.django_db
@patch("booking_api.voice.views.chat_completion")
def test_chat_simple_text_response(mock_chat, auth_client, salon, user):
    """GPT-4 returns a plain text reply with no tool calls."""
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
    assert len(response.data["conversation_history"]) == 2  # user msg + assistant reply


@pytest.mark.django_db
@patch("booking_api.voice.views.chat_completion")
@patch("booking_api.voice.views.execute_tool_call")
def test_chat_with_tool_call(mock_execute, mock_chat, auth_client, salon, user):
    """GPT-4 calls a tool, then returns a text reply."""
    # First call: GPT-4 wants to call lookup_customer
    tool_call_response = MagicMock()
    tool_call = MagicMock()
    tool_call.id = "call_123"
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
        {"message": "Look up 07700900123", "conversation_history": []},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["reply"] == "Found Ellie Smith."
    mock_execute.assert_called_once_with(
        "lookup_customer", {"phone_number": "+447700900123"}, salon, user
    )


@pytest.mark.django_db
@patch("booking_api.voice.views.chat_completion")
def test_chat_max_rounds_safety(mock_chat, auth_client, salon, user):
    """If GPT-4 keeps calling tools forever, we break after MAX_TOOL_CALL_ROUNDS."""
    # Every response has tool_calls (infinite loop)
    infinite_response = MagicMock()
    tc = MagicMock()
    tc.id = "call_loop"
    tc.function.name = "lookup_customer"
    tc.function.arguments = '{"phone_number": "+447700900123"}'
    infinite_response.choices[0].message.content = ""
    infinite_response.choices[0].message.tool_calls = [tc]
    mock_chat.return_value = infinite_response

    with patch(
        "booking_api.voice.views.execute_tool_call", return_value='{"found": false}'
    ):
        response = auth_client.post(
            "/voice/chat/",
            {"message": "test", "conversation_history": []},
            format="json",
        )

    assert response.status_code == 200
    assert "try again" in response.data["reply"].lower()
    assert mock_chat.call_count == 5  # MAX_TOOL_CALL_ROUNDS
```

---

### Test Summary by File

| Test File | # Tests | What's Covered |
|-----------|---------|----------------|
| `test_openai_client.py` | 6 | Singleton, Whisper call, GPT-4 call, missing key error |
| `test_serializers.py` | 15 | Audio validation, message format, chat request/response shape |
| `test_tool_executor.py` | 29 | All 4 tools: lookup, create, availability, appointment + edge cases |
| `test_views.py` | 16 | HTTP layer: auth, transcribe, chat, tool loop, error responses |
| **Total** | **66** | |

### Running Tests

```bash
# All voice tests
pytest booking_api/voice/tests/ -v

# Specific test file
pytest booking_api/voice/tests/test_tool_executor.py -v

# With coverage
pytest booking_api/voice/tests/ --cov=booking_api.voice --cov-report=term-missing

# Only a specific test
pytest booking_api/voice/tests/test_tool_executor.py::test_one_column_busy -v
```

### Mocking Strategy

| Component | Mock? | Why |
|-----------|-------|-----|
| **OpenAI Whisper** | Yes, always | Costs money, external dependency, non-deterministic |
| **OpenAI GPT-4** | Yes, always | Costs money, non-deterministic responses |
| **Django ORM** | No, use real DB | Tool executor tests need real queries to validate overlap logic |
| **Appointment.save() SMS** | Patch Twilio client | Avoid real SMS sends in tests |
| **JWT Auth** | Use `RefreshToken.for_user()` | Generate real tokens for test user |

Mock target paths:
```
# In test_views.py
@patch("booking_api.voice.views.transcribe_audio")      # Mock Whisper
@patch("booking_api.voice.views.chat_completion")        # Mock GPT-4
@patch("booking_api.voice.views.execute_tool_call")      # Mock tool execution (for view-level tests)

# In test_openai_client.py
@patch("booking_api.voice.openai_client.get_openai_client")  # Mock client singleton

# In test_tool_executor.py -- use real DB, but mock SMS
@patch("appointment.tasks.send_sms_confirmation.send")   # Prevent real SMS
@patch("appointment.tasks.send_sms_reminder.send_with_options")  # Prevent real SMS
```

---

## Manual Testing Guide

### Prerequisites

1. Start services: `docker compose up -d db redis && python manage.py runserver`
2. Set `OPENAI_API_KEY` in `.env`
3. Seed data: `python manage.py seed_data`

### Authentication

The project uses `JWTCookieAuthentication` (via `dj-rest-auth`). To authenticate:

1. **Login** to get JWT cookie:
   ```bash
   curl -s -c /tmp/cookies.txt -X POST http://localhost:8000/users/login/ \
     -H "Content-Type: application/json" \
     -d '{"email": "<email>", "password": "<password>"}'
   ```

2. **Extract the JWT** from the `token` cookie:
   ```bash
   TOKEN=$(awk '/\ttoken\t/{print $NF}' /tmp/cookies.txt)
   ```

3. **Use Bearer auth** on all subsequent requests:
   ```bash
   curl -H "Authorization: Bearer $TOKEN" ...
   ```

> **Note**: The login response returns a `key` field (session token) — this is NOT for the voice API. Use the `token` cookie value as a Bearer token instead.

> **Postman**: After login, go to the Cookies tab, copy the `token` cookie value, then set Authorization → Bearer Token.

### Full Booking Flow (verified 2026-02-28)

```
Turn 1: "Hi, I need to book an appointment"
  → AI asks for customer phone number

Turn 2: "The phone number is 07999987828"
  → lookup_customer tool called → found customer "Le"
  → AI asks for date, time, and duration

Turn 3: "Tomorrow at 2pm for 30 minutes"
  → AI asks for column/staff preference

Turn 4: "Column 1 please"
  → check_availability tool called
  → create_appointment tool called (or date error if invalid)
  → AI confirms booking

Note: Each turn must include conversation_history from the previous response.
```

### Known Quirks

- **Leap year edge case**: GPT-4 may miscalculate "tomorrow" near month boundaries (e.g., Feb 28 → Feb 29 in non-leap years). Use explicit dates like "March 1st" to avoid this.
- **Auth**: Only `JWTCookieAuthentication` is configured — `TokenAuthentication` is NOT enabled, so `Authorization: Token <key>` will return 401.
