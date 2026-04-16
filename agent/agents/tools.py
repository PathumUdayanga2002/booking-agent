"""Tool definitions for booking agent with Groq function calling."""
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field
from utils.logger import get_logger

logger = get_logger(__name__)


# ==================== Input Models ====================
class SearchRoomsInput(BaseModel):
    """Input for searching hotels rooms."""
    check_in: str = Field(..., description="Check-in date in YYYY-MM-DD format")
    check_out: str = Field(..., description="Check-out date in YYYY-MM-DD format")
    guests: int = Field(..., description="Number of guests", ge=1, le=10)
    room_type: Optional[str] = Field(None, description="Type of room (e.g., 'single', 'double', 'suite')")


class CreateBookingInput(BaseModel):
    """Input for creating a booking."""
    room_id: str = Field(..., description="Room ID to book")
    check_in: str = Field(..., description="Check-in date in YYYY-MM-DD format")
    check_out: str = Field(..., description="Check-out date in YYYY-MM-DD format")
    guests: int = Field(..., description="Number of guests", ge=1, le=10)
    total_price: float = Field(..., description="Total booking price")
    guest_name: Optional[str] = Field(None, description="Guest full name")
    guest_email: Optional[str] = Field(None, description="Guest email address")
    guest_phone: Optional[str] = Field(None, description="Guest phone number")


class CancelBookingInput(BaseModel):
    """Input for cancelling a booking."""
    booking_id: str = Field(..., description="Booking ID to cancel")
    reason: Optional[str] = Field(None, description="Reason for cancellation")


class RescheduleBookingInput(BaseModel):
    """Input for rescheduling a booking."""
    booking_id: str = Field(..., description="Booking ID to reschedule")
    new_check_in: str = Field(..., description="New check-in date in YYYY-MM-DD format")
    new_check_out: str = Field(..., description="New check-out date in YYYY-MM-DD format")


class GetBookingStatusInput(BaseModel):
    """Input for checking booking status."""
    booking_id: str = Field(..., description="Booking ID to check")


class SearchKnowledgeBaseInput(BaseModel):
    """Input for searching knowledge base."""
    query: str = Field(..., description="Search query about hotel or bookings")


# ==================== Tool Definitions ====================
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_rooms",
            "description": "Search for available hotel rooms based on check-in/out dates and number of guests.",
            "parameters": {
                "type": "object",
                "properties": {
                    "check_in": {
                        "type": "string",
                        "description": "Check-in date in YYYY-MM-DD format"
                    },
                    "check_out": {
                        "type": "string",
                        "description": "Check-out date in YYYY-MM-DD format"
                    },
                    "guests": {
                        "type": "integer",
                        "description": "Number of guests (1-10)"
                    },
                    "room_type": {
                        "type": ["string", "null"],
                        "description": "Optional room type (single, double, suite, etc.)"
                    }
                },
                "required": ["check_in", "check_out", "guests"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_booking",
            "description": "Create a new hotel booking for the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "room_id": {
                        "type": "string",
                        "description": "The room ID to book"
                    },
                    "check_in": {
                        "type": "string",
                        "description": "Check-in date in YYYY-MM-DD format"
                    },
                    "check_out": {
                        "type": "string",
                        "description": "Check-out date in YYYY-MM-DD format"
                    },
                    "guests": {
                        "type": "integer",
                        "description": "Number of guests"
                    },
                    "total_price": {
                        "type": "number",
                        "description": "Total booking price"
                    },
                    "guest_name": {
                        "type": "string",
                        "description": "Guest full name"
                    },
                    "guest_email": {
                        "type": "string",
                        "description": "Guest email address"
                    },
                    "guest_phone": {
                        "type": "string",
                        "description": "Guest phone number (e.g., +1234567890 or 123-456-7890)"
                    }
                },
                "required": ["room_id", "check_in", "check_out", "guests", "total_price", "guest_name", "guest_email", "guest_phone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_bookings",
            "description": "Retrieve all bookings for the current user.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_booking",
            "description": "Cancel an existing booking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": "The booking ID to cancel"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Optional reason for cancellation"
                    }
                },
                "required": ["booking_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reschedule_booking",
            "description": "Reschedule an existing booking to new dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": "The booking ID to reschedule"
                    },
                    "new_check_in": {
                        "type": "string",
                        "description": "New check-in date in YYYY-MM-DD format"
                    },
                    "new_check_out": {
                        "type": "string",
                        "description": "New check-out date in YYYY-MM-DD format"
                    }
                },
                "required": ["booking_id", "new_check_in", "new_check_out"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_booking_status",
            "description": "Check the status of a specific booking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": "The booking ID to check"
                    }
                },
                "required": ["booking_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search the hotel knowledge base for information about amenities, policies, or common questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What you want to know about the hotel"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_available_dates",
            "description": "Get available dates for a specific room in a given month.",
            "parameters": {
                "type": "object",
                "properties": {
                    "room_id": {
                        "type": "string",
                        "description": "The room ID"
                    },
                    "month": {
                        "type": "integer",
                        "description": "Month (1-12)"
                    },
                    "year": {
                        "type": "integer",
                        "description": "Year (e.g., 2024)"
                    }
                },
                "required": ["room_id", "month", "year"]
            }
        }
    }
]


# ==================== Groq Function Calling Tool Defs ====================
GROQ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_rooms",
            "description": "Search for available hotel rooms based on check-in/out dates and guests",
            "parameters": {
                "type": "object",
                "properties": {
                    "check_in": {"type": "string", "description": "Check-in date (YYYY-MM-DD)"},
                    "check_out": {"type": "string", "description": "Check-out date (YYYY-MM-DD)"},
                    "guests": {"type": "integer", "description": "Number of guests"},
                    "room_type": {"type": "string", "description": "Room type (optional)"}
                },
                "required": ["check_in", "check_out", "guests"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_booking",
            "description": "Create a new hotel booking",
            "parameters": {
                "type": "object",
                "properties": {
                    "room_id": {"type": "string", "description": "Room ID"},
                    "check_in": {"type": "string", "description": "Check-in date (YYYY-MM-DD)"},
                    "check_out": {"type": "string", "description": "Check-out date (YYYY-MM-DD)"},
                    "guests": {"type": "integer", "description": "Number of guests"},
                    "total_price": {"type": "number", "description": "Total price"}
                },
                "required": ["room_id", "check_in", "check_out", "guests", "total_price"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_bookings",
            "description": "Get all bookings for the current user",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_booking",
            "description": "Cancel an existing booking",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {"type": "string", "description": "Booking ID"},
                    "reason": {"type": "string", "description": "Cancellation reason (optional)"}
                },
                "required": ["booking_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reschedule_booking",
            "description": "Reschedule a booking to new dates",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {"type": "string", "description": "Booking ID"},
                    "new_check_in": {"type": "string", "description": "New check-in (YYYY-MM-DD)"},
                    "new_check_out": {"type": "string", "description": "New check-out (YYYY-MM-DD)"}
                },
                "required": ["booking_id", "new_check_in", "new_check_out"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_booking_status",
            "description": "Check booking status",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {"type": "string", "description": "Booking ID"}
                },
                "required": ["booking_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search hotel knowledge base",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_available_dates",
            "description": "Get available dates for a room",
            "parameters": {
                "type": "object",
                "properties": {
                    "room_id": {"type": "string", "description": "Room ID"},
                    "month": {"type": "integer", "description": "Month (1-12)"},
                    "year": {"type": "integer", "description": "Year"}
                },
                "required": ["room_id", "month", "year"]
            }
        }
    }
]
