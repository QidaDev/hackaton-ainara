"""Pydantic model for WhatsApp messages."""

from pydantic import Field

from app.models.base import MongoModel


class Message(MongoModel):
    """WhatsApp message document: case_id, text, date, sender."""

    message_id: str = Field(..., description="The ID of the message")
    sender: str = Field(..., description="The sender of the message")

    def save(self) -> "Message":
        """Persist to the whatsapp_chats collection."""
        return super().save("whatsapp_messages")
