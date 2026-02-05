"""Single service for notes, calls, and WhatsApp messages (get by case_id and save)."""

from bson import ObjectId

from app.db_connection import db
from app.models.calls import Call
from app.models.message import Message
from app.models.notes import Note


def _to_json_safe(doc):
    """Convert a MongoDB doc to a JSON-serializable dict (ObjectId -> str)."""
    if doc is None:
        return None
    out = dict(doc)
    if "_id" in out and isinstance(out["_id"], ObjectId):
        out["_id"] = str(out["_id"])
    return out


def save_note(data: dict):
    """Create and save a note; returns JSON-safe dict. Expects data with case_id, text, date; optional sender."""
    note = Note(**data)
    note.save()
    return note.model_dump(by_alias=False)


def get_notes_by_case_id(case_id: str):
    """Return list of notes for the given case_id (JSON-safe dicts), newest first."""
    cursor = db["notes"].find({"case_id": case_id}).sort("date", -1)
    return [_to_json_safe(doc) for doc in cursor]


def save_call(data: dict):
    """Create and save a call; returns JSON-safe dict. Expects data with case_id, text, date."""
    call = Call(**data)
    call.save()
    return call.model_dump(by_alias=False)


def get_calls_by_case_id(case_id: str):
    """Return list of calls for the given case_id (JSON-safe dicts), newest first."""
    cursor = db["calls"].find({"case_id": case_id}).sort("date", -1)
    return [_to_json_safe(doc) for doc in cursor]


def save_message(data: dict):
    """Create and save a WhatsApp message; returns JSON-safe dict. Expects data with case_id, text, date, sender."""
    message = Message(**data)
    message.save()
    return message.model_dump(by_alias=False)


def get_messages_by_case_id(case_id: str):
    """Return list of WhatsApp messages for the given case_id (JSON-safe dicts), newest first."""
    cursor = db["whatsapp_chats"].find({"case_id": case_id}).sort("date", -1)
    return [_to_json_safe(doc) for doc in cursor]
