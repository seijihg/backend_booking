# Frontend API Documentation

Complete API reference for the Salon Booking System backend. Use this document when building frontend applications.

## Base Configuration

| Setting | Value |
|---------|-------|
| **Base URL** | `https://api.yourdomain.com` (production) or `http://localhost:8000` (dev) |
| **Content-Type** | `application/json` |
| **Authentication** | JWT tokens via HTTP-only cookies |

---

## Authentication

### How Authentication Works

1. **Login/Register** returns JWT tokens set as HTTP-only cookies
2. **Cookies**: `token` (access, 1hr) and `refresh_token` (refresh, 7 days)
3. **Cross-origin**: Cookies use `SameSite=None; Secure` for subdomain sharing
4. Include `credentials: 'include'` in fetch requests

### Login

```http
POST /users/login/
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response (200 OK):**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "phone_number": "+447123456789",
    "full_name": "John Doe",
    "is_owner": false,
    "is_staff": false,
    "is_active": true,
    "salons": [1, 2],
    "addresses": [],
    "first_name": "",
    "last_name": "",
    "date_joined": "2024-01-15T10:30:00Z",
    "last_login": "2024-01-20T14:00:00Z",
    "created": "2024-01-15T10:30:00Z",
    "modified": "2024-01-20T14:00:00Z"
  }
}
```

**Cookies Set:**
- `token` - Access token (httpOnly, secure, 1 hour)
- `refresh_token` - Refresh token (httpOnly, secure, 7 days)

**Errors:**
- `400` - Invalid credentials or validation error

---

### Register

```http
POST /users/register/
```

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "password1": "secure_password123",
  "password2": "secure_password123",
  "phone_number": "+447123456789",
  "salons": [1]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | User's email (must be unique) |
| `password1` | string | Yes | Password |
| `password2` | string | Yes | Password confirmation |
| `phone_number` | string | Yes | UK phone number (E.164 format) |
| `salons` | int[] | Yes | Array of salon IDs to associate with |

**Response (201 Created):**
```json
{
  "user": {
    "id": 2,
    "email": "newuser@example.com",
    "phone_number": "+447123456789",
    "full_name": "",
    "is_owner": false,
    "is_staff": false,
    "is_active": true,
    "salons": [1],
    "addresses": [],
    "first_name": "",
    "last_name": "",
    "date_joined": "2024-01-20T15:00:00Z",
    "last_login": null,
    "created": "2024-01-20T15:00:00Z",
    "modified": "2024-01-20T15:00:00Z"
  },
  "access_token": "eyJ0eXAiOiJKV1Q..."
}
```

**Errors:**
- `400` - Validation error (email exists, passwords don't match, invalid salon IDs)

---

### Refresh Token

```http
POST /token/refresh/
```

**Request:** Send with cookies (no body required if using cookie-based refresh)

**Response (200 OK):** New access token set in cookie

---

## Users

### List Users (by Salon)

```http
GET /users/?salon={salon_id}
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `salon` | int | Yes | Filter users by salon ID |

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "email": "user@example.com",
    "phone_number": "+447123456789",
    "full_name": "John Doe",
    "is_owner": false,
    "is_staff": false,
    "is_active": true,
    "salons": [1],
    "addresses": [],
    "first_name": "",
    "last_name": "",
    "date_joined": "2024-01-15T10:30:00Z",
    "last_login": "2024-01-20T14:00:00Z",
    "created": "2024-01-15T10:30:00Z",
    "modified": "2024-01-20T14:00:00Z"
  }
]
```

---

### Get User Details

```http
GET /users/{id}/
```

**Response (200 OK):**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "phone_number": "+447123456789",
    "full_name": "John Doe",
    "is_owner": false,
    "is_staff": false,
    "is_active": true,
    "salons": [1],
    "addresses": [],
    "first_name": "",
    "last_name": "",
    "date_joined": "2024-01-15T10:30:00Z",
    "last_login": "2024-01-20T14:00:00Z",
    "created": "2024-01-15T10:30:00Z",
    "modified": "2024-01-20T14:00:00Z"
  }
}
```

**Errors:**
- `404` - User not found

---

### Update User

```http
PATCH /users/{id}/
```

**Request Body (partial update):**
```json
{
  "full_name": "John Smith",
  "phone_number": "+447987654321"
}
```

**Response (200 OK):** Updated user object

---

## Salons

### List Salons

```http
GET /salons/
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Main Street Salon",
    "phone_number": "+447123456789",
    "reminder_time_minutes": 60,
    "addresses": [
      {
        "id": 1,
        "street": "123 Main Street",
        "city": "London",
        "postal_code": "SW1A 1AA",
        "created": "2024-01-10T09:00:00Z",
        "modified": "2024-01-10T09:00:00Z"
      }
    ],
    "created": "2024-01-10T09:00:00Z",
    "modified": "2024-01-15T12:00:00Z"
  }
]
```

---

### Create Salon

```http
POST /salons/
```

**Request Body:**
```json
{
  "name": "New Salon",
  "phone_number": "+447123456789",
  "reminder_time_minutes": 60,
  "addresses": [
    {
      "street": "456 High Street",
      "city": "Manchester",
      "postal_code": "M1 1AA"
    }
  ]
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Salon name |
| `phone_number` | string | Yes | - | UK phone number (E.164) |
| `reminder_time_minutes` | int | No | 60 | Minutes before appointment to send SMS reminder |
| `addresses` | object[] | Yes | - | At least one address required |

**Address Object:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `street` | string | No | Street address |
| `city` | string | No | City |
| `postal_code` | string | No | UK postcode (validated) |

**Response (201 Created):** Created salon object

**Errors:**
- `400` - Validation error (empty addresses, invalid postcode)

---

### Get Salon Details

```http
GET /salons/{id}/
```

**Response (200 OK):** Salon object

---

### Update Salon

```http
PATCH /salons/{id}/
```

**Request Body (partial update):**
```json
{
  "reminder_time_minutes": 120
}
```

**Response (200 OK):** Updated salon object

---

### Delete Salon

```http
DELETE /salons/{id}/
```

**Response:** `204 No Content`

---

## Customers

### List Customers

```http
GET /customers/
GET /customers/?salon={salon_id}
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `salon` | int | No | Filter customers by salon ID |

**Examples:**
```bash
# Get all customers
GET /customers/

# Get customers for salon ID 1
GET /customers/?salon=1
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "full_name": "Jane Customer",
    "phone_number": "+447111222333",
    "salons": [
      {
        "id": 1,
        "name": "Main Street Salon",
        "phone_number": "+447123456789",
        "reminder_time_minutes": 60,
        "addresses": [...],
        "created": "2024-01-10T09:00:00Z",
        "modified": "2024-01-15T12:00:00Z"
      }
    ],
    "created": "2024-01-12T11:00:00Z",
    "modified": "2024-01-12T11:00:00Z"
  }
]
```

---

### Create Customer

```http
POST /customers/
```

**Request Body:**
```json
{
  "full_name": "Jane Customer",
  "phone_number": "+447111222333",
  "salon_ids": [1]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `full_name` | string | No | Customer's full name |
| `phone_number` | string | Yes | UK phone number (E.164) |
| `salon_ids` | int[] | Yes | At least one salon ID required |

**Response (201 Created):** Created customer object

**Errors:**
- `400` - Validation error (no salons, invalid phone)

---

### Get Customer Details

```http
GET /customers/{id}/
```

**Response (200 OK):** Customer object

---

### Update Customer

```http
PATCH /customers/{id}/
```

**Request Body:**
```json
{
  "full_name": "Jane Smith",
  "salon_ids": [1, 2]
}
```

**Response (200 OK):** Updated customer object

---

### Delete Customer

```http
DELETE /customers/{id}/
```

**Response:** `204 No Content`

---

## Appointments

### List Appointments

```http
GET /appointments/
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "salon": 1,
    "user": 1,
    "customer": 1,
    "appointment_time": "2024-01-25T14:00:00Z",
    "end_time": "2024-01-25T15:00:00Z",
    "column_id": 1,
    "comment": "Regular trim",
    "created": "2024-01-20T10:00:00Z",
    "modified": "2024-01-20T10:00:00Z"
  }
]
```

---

### Create Appointment

```http
POST /appointments/
```

**Request Body:**
```json
{
  "salon": 1,
  "user": 1,
  "customer": 1,
  "appointment_time": "2024-01-25T14:00:00Z",
  "end_time": "2024-01-25T15:00:00Z",
  "column_id": 1,
  "comment": "Regular trim"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `salon` | int | Yes | - | Salon ID |
| `user` | int | Yes | - | Staff user ID performing service |
| `customer` | int | Yes | - | Customer ID |
| `appointment_time` | datetime | Yes | - | ISO 8601 format (must be in future) |
| `end_time` | datetime | No | null | ISO 8601 format |
| `column_id` | int | No | 1 | Column for calendar display |
| `comment` | string | No | "" | Notes about the appointment |

**Response (201 Created):** Created appointment object

**SMS Behavior on Create:**
1. **Confirmation SMS** sent immediately to customer
2. **Reminder SMS** scheduled for X minutes before (based on `salon.reminder_time_minutes`)

**Errors:**
- `400` - Validation error (appointment time in past, invalid IDs)

---

### Get Appointment Details

```http
GET /appointments/{id}/
```

**Response (200 OK):** Appointment object

---

### Update Appointment

```http
PATCH /appointments/{id}/
```

**Request Body:**
```json
{
  "appointment_time": "2024-01-25T15:00:00Z",
  "comment": "Updated: Color treatment"
}
```

**Response (200 OK):** Updated appointment object

**SMS Behavior on Update:**
- If `appointment_time` changed: **New confirmation SMS** sent
- **Reminder SMS** rescheduled automatically

---

### Delete Appointment

```http
DELETE /appointments/{id}/
```

**Response:** `204 No Content`

**SMS Behavior on Delete:**
- **Cancellation SMS** sent to customer
- Scheduled reminder cancelled

---

## SMS Notification System

The backend automatically handles SMS notifications via Twilio.

### SMS Types

| Type | When Sent | Message |
|------|-----------|---------|
| **Confirmation** | On create OR time change | "Your appointment at {salon} has been confirmed for {date} at {time}. See you soon!" |
| **Reminder** | X minutes before (configurable) | "You have an appointment coming up at {time}. Regards {salon}." |
| **Cancellation** | On appointment deletion | "Your scheduled appointment for {date/time} has been cancelled." |

### Configuring Reminder Time

Update salon's `reminder_time_minutes`:

```http
PATCH /salons/{id}/
```

```json
{
  "reminder_time_minutes": 120
}
```

Common values:
- `30` - 30 minutes before
- `60` - 1 hour before (default)
- `120` - 2 hours before
- `1440` - 24 hours before (1 day)

---

## Data Models Reference

### User (ExtendedUser)

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Primary key |
| `email` | string | Unique, used for login |
| `phone_number` | string | E.164 format |
| `full_name` | string | Display name |
| `first_name` | string | First name |
| `last_name` | string | Last name |
| `is_owner` | bool | Can manage salons |
| `is_staff` | bool | Can access admin |
| `is_active` | bool | Account active |
| `salons` | int[] | Associated salon IDs |
| `addresses` | int[] | Associated address IDs |
| `date_joined` | datetime | Registration date |
| `last_login` | datetime | Last login timestamp |
| `created` | datetime | Record created |
| `modified` | datetime | Record updated |

### Salon

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Primary key |
| `name` | string | Salon name |
| `phone_number` | string | E.164 format |
| `reminder_time_minutes` | int | SMS reminder timing (default: 60) |
| `addresses` | Address[] | Nested address objects |
| `created` | datetime | Record created |
| `modified` | datetime | Record updated |

### Customer

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Primary key |
| `full_name` | string | Customer name |
| `phone_number` | string | E.164 format (receives SMS) |
| `salons` | Salon[] | Nested salon objects (read) |
| `salon_ids` | int[] | Salon IDs (write) |
| `created` | datetime | Record created |
| `modified` | datetime | Record updated |

### Appointment

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Primary key |
| `salon` | int | Salon ID |
| `user` | int | Staff user ID |
| `customer` | int | Customer ID |
| `appointment_time` | datetime | Appointment start (ISO 8601) |
| `end_time` | datetime | Appointment end (optional) |
| `column_id` | int | Calendar column (default: 1) |
| `comment` | string | Notes |
| `created` | datetime | Record created |
| `modified` | datetime | Record updated |

### Address

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Primary key |
| `street` | string | Street address |
| `city` | string | City |
| `postal_code` | string | UK postcode (validated) |
| `created` | datetime | Record created |
| `modified` | datetime | Record updated |

---

## Error Responses

All errors follow this format:

```json
{
  "field_name": ["Error message 1", "Error message 2"],
  "non_field_errors": ["General error message"]
}
```

### Common Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `201` | Created |
| `204` | No Content (successful delete) |
| `400` | Bad Request (validation error) |
| `401` | Unauthorized (missing/invalid token) |
| `403` | Forbidden (insufficient permissions) |
| `404` | Not Found |
| `500` | Server Error |

---

## Frontend Implementation Notes

### Fetch Configuration

```javascript
const API_BASE = 'http://localhost:8000';

async function apiRequest(endpoint, options = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    credentials: 'include', // Required for cookies
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(JSON.stringify(error));
  }

  if (response.status === 204) return null;
  return response.json();
}
```

### Phone Number Format

All phone numbers must be in E.164 format:
- UK: `+447123456789`
- Include country code with `+` prefix

### DateTime Format

All datetime fields use ISO 8601 format:
- Example: `2024-01-25T14:00:00Z`
- Always in UTC

### Pagination

Pagination is **disabled** - all endpoints return complete lists. Implement client-side filtering/pagination as needed.

---

## Health Check

```http
GET /health/
```

**Response (200 OK):**
```json
{
  "status": "healthy"
}
```

Use for load balancer health checks and monitoring.
