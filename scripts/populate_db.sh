#!/usr/bin/env bash
# Populate the database via API (notes, calls, whatsapp-chats).
# Usage: ./scripts/populate_db.sh [BASE_URL]
# Example: ./scripts/populate_db.sh http://localhost:5000/api
# Requires: Flask app running and MongoDB available.

set -e
BASE_URL="${1:-http://localhost:5000/api}"

echo "Using API base: $BASE_URL"
echo ""

# Helper: POST and show status
post() {
  local label="$1"
  local path="$2"
  local body="$3"
  local code
  code=$(curl -s -o /tmp/curl_out -w "%{http_code}" -X POST "$BASE_URL$path" \
    -H "Content-Type: application/json" \
    -d "$body")
  if [[ "$code" == "201" ]]; then
    echo "  OK $code  $label"
  else
    echo "  FAIL $code  $label"
    cat /tmp/curl_out 2>/dev/null && echo ""
  fi
}

echo "--- Notes ---"
post "Note 1 (minimal)" "/notes" '{
  "case_id": "CASE-001",
  "text": "Initial assessment: client requested support with documentation.",
  "date": "2025-02-05",
  "note_id": "n1"
}'
post "Note 2 (with sender)" "/notes" '{
  "case_id": "CASE-001",
  "text": "Follow-up call completed. Client confirmed next steps.",
  "date": "2025-02-05",
  "sender": "agent@support.com",
  "note_id": "n2"
}'
post "Note 3 (long)" "/notes" '{
  "case_id": "CASE-002",
  "text": "Meeting notes: Discussed timeline, budget constraints, and risk mitigation. Action items: (1) Send proposal by Friday (2) Schedule technical review (3) Confirm stakeholder availability.",
  "date": "2025-02-04",
  "sender": "maria.garcia@company.com",
  "note_id": "n3"
}'
post "Note 4 (reminder)" "/notes" '{
  "case_id": "CASE-003",
  "text": "Reminder: send contract before EOD.",
  "date": "2025-02-05",
  "note_id": "n4"
}'
post "Note 5 (escalation)" "/notes" '{
  "case_id": "CASE-001",
  "text": "Escalated to L2. Ticket #TKT-789. Priority: high.",
  "date": "2025-02-05",
  "sender": "support-tier1",
  "note_id": "n5"
}'

echo ""
echo "--- Calls ---"
post "Call 1 (short transcript)" "/calls" '{
  "case_id": "CASE-001",
  "text": "Agent: Hello, how can I help? Client: I need help with my order. Agent: Can you provide the order ID?",
  "date": "2025-02-05",
  "conversation_id": "conv1",
  "conversation_init": true,
  "conversation_end": true
}'
post "Call 2 (full transcript)" "/calls" '{
  "case_id": "CASE-002",
  "text": "[00:00] Agent: Good morning, support line. [00:05] Client: Hi, I have a billing question. [00:12] Agent: Sure, I can help. What is your account email? [00:20] Client: john.doe@example.com [00:25] Agent: I see the invoice from January. The charge is for the premium plan. [00:35] Client: I thought I had cancelled. [00:38] Agent: I can check the cancellation status and process a refund if applicable. [00:45] Client: Thank you.",
  "date": "2025-02-04",
  "conversation_id": "conv2",
  "conversation_init": true,
  "conversation_end": true
}'
post "Call 3 (voicemail)" "/calls" '{
  "case_id": "CASE-003",
  "text": "Voicemail left by +34 612 000 000. Message: Please call back regarding contract renewal. Urgent.",
  "date": "2025-02-05",
  "conversation_id": "conv3",
  "conversation_init": true,
  "conversation_end": true
}'
post "Call 4 (outbound)" "/calls" '{
  "case_id": "CASE-001",
  "text": "Outbound call to client. No answer. Will retry tomorrow.",
  "date": "2025-02-05",
  "conversation_id": "conv4",
  "conversation_init": true,
  "conversation_end": true
}'
post "Call 5 (tech support)" "/calls" '{
  "case_id": "CASE-004",
  "text": "Tech support call. Issue: login failure. Steps: reset password, clear cache, verified 2FA. Resolved. Duration: 12 min.",
  "date": "2025-02-03",
  "conversation_id": "conv5",
  "conversation_init": true,
  "conversation_end": true
}'

echo ""
echo "--- WhatsApp chats ---"
post "WhatsApp 1 (incoming)" "/whatsapp-chats" '{
  "case_id": "CASE-001",
  "text": "Hi, I would like to know the status of my request.",
  "date": "2025-02-05",
  "sender": "+34612345678",
  "message_id": "wa1"
}'
post "WhatsApp 2 (outgoing)" "/whatsapp-chats" '{
  "case_id": "CASE-001",
  "text": "Your request is being processed. We will update you within 24h.",
  "date": "2025-02-05",
  "sender": "support-bot",
  "message_id": "wa2"
}'
post "WhatsApp 3 (complaint)" "/whatsapp-chats" '{
  "case_id": "CASE-002",
  "text": "I still have not received my refund. Order #ORD-456. This is unacceptable.",
  "date": "2025-02-04",
  "sender": "+34987654321",
  "message_id": "wa3"
}'
post "WhatsApp 4 (confirmation)" "/whatsapp-chats" '{
  "case_id": "CASE-003",
  "text": "Your appointment is confirmed for Feb 10 at 10:00. Reply YES to confirm or CANCEL to cancel.",
  "date": "2025-02-05",
  "sender": "appointments@company.com",
  "message_id": "wa4"
}'
post "WhatsApp 5 (multi-line)" "/whatsapp-chats" '{
  "case_id": "CASE-001",
  "text": "Client sent: Can I get a quote for 50 units? Agent replied: Sure, I will send it in 5 minutes.",
  "date": "2025-02-05",
  "sender": "agent-ana",
  "message_id": "wa5"
}'

echo ""
echo "--- GET (verify) ---"
for c in CASE-001 CASE-002 CASE-003 CASE-004; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/notes?case_id=$c")
  echo "  GET /notes?case_id=$c  -> $code"
done

echo ""
echo "Done. DB populated with notes, calls, and whatsapp-chats."
