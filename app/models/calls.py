"""Pydantic model for calls."""

from pydantic import Field

from app.models.base import MongoModel


class Call(MongoModel):
    """Call document: case_id, text (e.g. transcript), date; conversation timestamps."""

    conversation_id: str = Field(..., description="The ID of the conversation")
    conversation_init: str = Field(..., description="Conversation start timestamp")
    conversation_end: str = Field(..., description="Conversation end timestamp")

    def save(self) -> "Call":
        """Persist to the calls collection."""
        return super().save("phone_call_transcriptions")
