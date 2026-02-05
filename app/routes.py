from flask import Blueprint, jsonify, request

from app.services.case_service import (
    get_calls_by_case_id,
    get_messages_by_case_id,
    get_notes_by_case_id,
    save_call,
    save_message,
    save_note,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/")
def index():
    return "Hello, World!"


@api_bp.route("/notes", methods=["POST"])
def create_note():
    data = request.get_json(silent=True) or {}
    if not data.get("case_id") or data.get("text") is None or data.get("date") is None:
        return jsonify({"error": "case_id, text and date are required"}), 400
    saved = save_note(data)
    return jsonify(saved), 201


@api_bp.route("/notes", methods=["GET"])
def get_notes():
    case_id = request.args.get("case_id")
    if not case_id:
        return jsonify({"error": "case_id is required"}), 400
    notes = get_notes_by_case_id(case_id)
    return jsonify(notes), 200


@api_bp.route("/calls", methods=["POST"])
def create_call():
    data = request.get_json(silent=True) or {}
    if not data.get("case_id") or data.get("text") is None or data.get("date") is None:
        return jsonify({"error": "case_id, text and date are required"}), 400
    saved = save_call(data)
    return jsonify(saved), 201

@api_bp.route("/calls", methods=["GET"])
def get_calls():
    case_id = request.args.get("case_id")
    if not case_id:
        return jsonify({"error": "case_id is required"}), 400
    calls = get_calls_by_case_id(case_id)
    return jsonify(calls), 200

@api_bp.route("/whatsapp-chats", methods=["POST"])
def create_whatsapp_chat():
    data = request.get_json(silent=True) or {}
    if not data.get("case_id") or data.get("text") is None or data.get("date") is None or not data.get("sender"):
        return jsonify({"error": "case_id, text, date and sender are required"}), 400
    saved = save_message(data)
    return jsonify(saved), 201


@api_bp.route("/whatsapp-chats", methods=["GET"])
def get_whatsapp_chats():
    case_id = request.args.get("case_id")
    if not case_id:
        return jsonify({"error": "case_id is required"}), 400
    whatsapp_chats = get_messages_by_case_id(case_id)
    return jsonify(whatsapp_chats), 200