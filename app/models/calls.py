"""Pydantic model for calls."""

from pydantic import Field

from app.models.base import MongoModel


class Call(MongoModel):
    """Call document: case_id, text (e.g. transcript), date."""

    case_id: str = Field(..., description="The ID of the case")
    text: str = Field(..., description="Call transcript or text")
    date: str = Field(..., description="The date")

    def save(self) -> "Call":
        """Persist to the calls collection."""
        return super().save("calls")
