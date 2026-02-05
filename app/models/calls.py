"""Pydantic model for calls."""

from pydantic import Field

from app.models.base import MongoModel


class Call(MongoModel):
    """Call document: case_id, text (e.g. transcript), date."""

    conversation_id: str = Field(..., description="The ID of the conversation")
    conversation_init: bool = Field(..., description="Whether the conversation has started")
    conversation_end: bool = Field(..., description="Whether the conversation has ended")

    def save(self) -> "Call":
        """Persist to the calls collection."""
        return super().save("phone_call_transcriptions")
