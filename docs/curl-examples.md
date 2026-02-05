# cURL Examples

Base URL: `http://localhost:5000/api` (adjust host/port if your app runs elsewhere)

---

## Notes

**Required fields:** `case_id`, `text`, `date`  
**Optional:** `sender`

### GET notes by case_id

```bash
curl -X GET "http://localhost:5000/api/notes?case_id=CASE-001"
```

### POST notes (create)

**Example 1 – Minimal (no sender)**

```bash
curl -X POST "http://localhost:5000/api/notes" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "CASE-001",
    "text": "Initial assessment: client requested support with documentation.",
    "date": "2025-02-05"
  }'
```

**Example 2 – With sender**

```bash
curl -X POST "http://localhost:5000/api/notes" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "CASE-001",
    "text": "Follow-up call completed. Client confirmed next steps.",
    "date": "2025-02-05",
    "sender": "agent@support.com"
  }'
```

**Example 3 – Long note**

```bash
curl -X POST "http://localhost:5000/api/notes" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "CASE-002",
    "text": "Meeting notes: Discussed timeline, budget constraints, and risk mitigation. Action items: (1) Send proposal by Friday (2) Schedule technical review (3) Confirm stakeholder availability.",
    "date": "2025-02-04",
    "sender": "maria.garcia@company.com"
  }'
```

**Example 4 – Short reminder**

```bash
curl -X POST "http://localhost:5000/api/notes" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "CASE-003",
    "text": "Reminder: send contract before EOD.",
    "date": "2025-02-05"
  }'
```

**Example 5 – Escalation note**

```bash
curl -X POST "http://localhost:5000/api/notes" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "CASE-001",
    "text": "Escalated to L2. Ticket #TKT-789. Priority: high.",
    "date": "2025-02-05",
    "sender": "support-tier1"
  }'
```

---

## Calls

**Required fields:** `case_id`, `text`, `date`

### GET calls by case_id

```bash
curl -X GET "http://localhost:5000/api/calls?case_id=CASE-001"
```

### POST calls (create)

**Example 1 – Short transcript**

```bash
curl -X POST "http://localhost:5000/api/calls" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "CASE-001",
    "text": "Agent: Hello, how can I help? Client: I need help with my order. Agent: Can you provide the order ID?",
    "date": "2025-02-05"
  }'
```

**Example 2 – Full call transcript**

```bash
curl -X POST "http://localhost:5000/api/calls" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "CASE-002",
    "text": "[00:00] Agent: Good morning, support line. [00:05] Client: Hi, I have a billing question. [00:12] Agent: Sure, I can help. What is your account email? [00:20] Client: john.doe@example.com [00:25] Agent: I see the invoice from January. The charge is for the premium plan. [00:35] Client: I thought I had cancelled. [00:38] Agent: I can check the cancellation status and process a refund if applicable. [00:45] Client: Thank you.",
    "date": "2025-02-04"
  }'
```

**Example 3 – Voicemail summary**

```bash
curl -X POST "http://localhost:5000/api/calls" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "CASE-003",
    "text": "Voicemail left by +34 612 000 000. Message: Please call back regarding contract renewal. Urgent.",
    "date": "2025-02-05"
  }'
```

**Example 4 – Outbound call log**

```bash
curl -X POST "http://localhost:5000/api/calls" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "CASE-001",
    "text": "Outbound call to client. No answer. Will retry tomorrow.",
    "date": "2025-02-05"
  }'
```

**Example 5 – Technical support call**

```bash
curl -X POST "http://localhost:5000/api/calls" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "CASE-004",
    "text": "Tech support call. Issue: login failure. Steps: reset password, clear cache, verified 2FA. Resolved. Duration: 12 min.",
    "date": "2025-02-03"
  }'
```

---

## WhatsApp chats (messages)

**Required fields:** `case_id`, `text`, `date`, `sender`

### GET WhatsApp chats by case_id

```bash
curl -X GET "http://localhost:5000/api/whatsapp-chats?case_id=CASE-001"
```

### POST WhatsApp chats (create)

**Example 1 – Incoming message**

```bash
curl -X POST "http://localhost:5000/api/whatsapp-chats" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "CASE-001",
    "text": "Hi, I would like to know the status of my request.",
    "date": "2025-02-05",
    "sender": "+34612345678"
  }'
```

**Example 2 – Outgoing reply**

```bash
curl -X POST "http://localhost:5000/api/whatsapp-chats" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "CASE-001",
    "text": "Your request is being processed. We will update you within 24h.",
    "date": "2025-02-05",
    "sender": "support-bot"
  }'
```

**Example 3 – Customer complaint**

```bash
curl -X POST "http://localhost:5000/api/whatsapp-chats" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "CASE-002",
    "text": "I still have not received my refund. Order #ORD-456. This is unacceptable.",
    "date": "2025-02-04",
    "sender": "+34987654321"
  }'
```

**Example 4 – Confirmation message**

```bash
curl -X POST "http://localhost:5000/api/whatsapp-chats" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "CASE-003",
    "text": "Your appointment is confirmed for Feb 10 at 10:00. Reply YES to confirm or CANCEL to cancel.",
    "date": "2025-02-05",
    "sender": "appointments@company.com"
  }'
```

**Example 5 – Multi-line conversation**

```bash
curl -X POST "http://localhost:5000/api/whatsapp-chats" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "CASE-001",
    "text": "Client sent: Can I get a quote for 50 units? Agent replied: Sure, I will send it in 5 minutes.",
    "date": "2025-02-05",
    "sender": "agent-ana"
  }'
```

---

## Error examples

**GET without case_id (400)**

```bash
curl -X GET "http://localhost:5000/api/notes"
```

**POST note with missing required field (400)**

```bash
curl -X POST "http://localhost:5000/api/notes" \
  -H "Content-Type: application/json" \
  -d '{"case_id": "CASE-001", "text": "Missing date"}'
```

**Index (root)**

```bash
curl -X GET "http://localhost:5000/api/"
```
