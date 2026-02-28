TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_customer",
            "description": (
                "Look up an existing customer by phone number "
                "in the salon's customer list."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": (
                            "Customer phone number in E.164 format "
                            "(e.g. '+447700900123')."
                        ),
                    },
                },
                "required": ["phone_number"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_customer",
            "description": (
                "Create a new customer record in the salon. "
                "Only call after lookup_customer returns not found."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "full_name": {
                        "type": "string",
                        "description": "Customer's full name.",
                    },
                    "phone_number": {
                        "type": "string",
                        "description": "Phone in E.164 format.",
                    },
                },
                "required": ["full_name", "phone_number"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": (
                "Check if a time slot is available. "
                "Returns which columns (1-5) are free."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format.",
                    },
                    "time": {
                        "type": "string",
                        "description": "Start time in HH:MM (24-hour) format.",
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": (
                            "Duration in minutes, multiple of 15. Default 60."
                        ),
                        "default": 60,
                    },
                    "column_id": {
                        "type": "integer",
                        "description": ("Optional specific column (1-5) to check."),
                        "minimum": 1,
                        "maximum": 5,
                    },
                },
                "required": ["date", "time"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_appointment",
            "description": "Book an appointment. Always check_availability first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "integer",
                        "description": "Customer's database ID.",
                    },
                    "appointment_time": {
                        "type": "string",
                        "description": (
                            "ISO 8601 format " "(e.g. '2024-03-15T14:30:00Z')."
                        ),
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": (
                            "Duration in minutes, multiple of 15. Default 60."
                        ),
                        "default": 60,
                    },
                    "column_id": {
                        "type": "integer",
                        "description": "Column/staff member (1-5).",
                        "minimum": 1,
                        "maximum": 5,
                    },
                    "comment": {
                        "type": "string",
                        "description": "Optional booking notes.",
                        "default": "",
                    },
                },
                "required": ["customer_id", "appointment_time", "column_id"],
                "additionalProperties": False,
            },
        },
    },
]
