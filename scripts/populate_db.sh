#!/usr/bin/env bash
# Populate the database via API using JSON data from scripts/data/.
# Usage: ./scripts/populate_db.sh [BASE_URL]
# Example: ./scripts/populate_db.sh http://localhost:5000/api
# Requires: jq, curl. Flask app running and MongoDB available.

set -e
BASE_URL="${1:-http://localhost:5000/api}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${SCRIPT_DIR}/data"

if ! command -v jq &>/dev/null; then
  echo "Error: jq is required. Install with: brew install jq (macOS) or apt install jq (Linux)"
  exit 1
fi

echo "Using API base: $BASE_URL"
echo "Data dir: $DATA_DIR"
echo ""

# POST one JSON document and print status
post_one() {
  local path="$1"
  local body="$2"
  local code
  code=$(curl -s -o /tmp/curl_out -w "%{http_code}" -X POST "$BASE_URL$path" \
    -H "Content-Type: application/json" \
    -d "$body")
  if [[ "$code" == "201" ]]; then
    echo "  OK $code"
  else
    echo "  FAIL $code"
    cat /tmp/curl_out 2>/dev/null && echo ""
  fi
}

# --- Notes ---
NOTES_FILE="${DATA_DIR}/ainara-db.notes.json"
if [[ ! -f "$NOTES_FILE" ]]; then
  echo "Error: $NOTES_FILE not found"
  exit 1
fi
echo "--- Notes ($NOTES_FILE) ---"
count=0
while IFS= read -r line; do
  post_one "/notes" "$line"
  ((count++)) || true
done < <(jq -c '.[] | del(._id)' "$NOTES_FILE")
echo "  Posted $count notes"

# --- Calls (add date from conversation_init first 10 chars for API) ---
CALLS_FILE="${DATA_DIR}/ainara-db.phone_call_transcriptions.json"
if [[ ! -f "$CALLS_FILE" ]]; then
  echo "Error: $CALLS_FILE not found"
  exit 1
fi
echo ""
echo "--- Calls ($CALLS_FILE) ---"
count=0
while IFS= read -r line; do
  post_one "/calls" "$line"
  ((count++)) || true
done < <(jq -c '.[] | del(._id) | . + {date: (.conversation_init | .[0:10])}' "$CALLS_FILE")
echo "  Posted $count calls"

# --- WhatsApp messages ---
WA_FILE="${DATA_DIR}/ainara-db.whatsapp_messages.json"
if [[ ! -f "$WA_FILE" ]]; then
  echo "Error: $WA_FILE not found"
  exit 1
fi
echo ""
echo "--- WhatsApp chats ($WA_FILE) ---"
count=0
while IFS= read -r line; do
  post_one "/whatsapp-chats" "$line"
  ((count++)) || true
done < <(jq -c '.[] | del(._id)' "$WA_FILE")
echo "  Posted $count whatsapp messages"

echo ""
echo "--- GET (verify) ---"
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/notes?case_id=ABC-123")
echo "  GET /notes?case_id=ABC-123  -> $code"
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/calls?case_id=ABC-123")
echo "  GET /calls?case_id=ABC-123  -> $code"
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/whatsapp-chats?case_id=ABC-123")
echo "  GET /whatsapp-chats?case_id=ABC-123  -> $code"

echo ""
echo "Done. DB populated from scripts/data/ (notes, calls, whatsapp_messages)."
