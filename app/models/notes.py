"""Pydantic model for notes."""

from typing import Optional

from pydantic import Field

from app.models.base import MongoModel


class Note(MongoModel):
    """Note document: case_id, text, date; optional sender."""

    note_id: str = Field(..., description="The ID of the note")
    sender: Optional[str] = Field(None, description="The sender of the note")

    def save(self) -> "Note":
        """Persist to the notes collection."""
        return super().save("notes")
