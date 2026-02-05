"""Pydantic model for notes."""

from token import OP
from typing import Optional

from pydantic import Field

from app.models.base import MongoModel


class Note(MongoModel):
    """Note document: case_id, text, date; optional sender."""

    note_id: Optional[str] = Field(None, description="The ID of the note")
    sender: Optional[str] = Field(None, description="The sender of the note")

    def save(self) -> "Note":
        """Persist to the notes collection."""
        self.note_id = str(uuid.uuid4())
        return super().save("notes")
