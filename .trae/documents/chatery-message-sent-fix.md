# Plan: Fix WhatsApp Webhook and Message Sending

## Summary
The goal is to fix two separate issues identified in the logs:
1. The Chatery API connection webhook event configuration must be changed to `["all"]` so that we receive the `message.sent` event to verify that the automated reply was sent.
2. The `send-text` request payload requires `chatId`, `message`, and `sessionId`. The logs indicate that the automated reply is being sent to `None`, which implies that `from_phone` is `None` or not being parsed correctly when passing to the `send-text` API.

## Current State Analysis
- **Webhook Events Registration:**
  - Currently set to `["message", "message_ack"]` in `connect_chatery()`.
- **Message Sending Payload Issue:**
  - In the `chatery_webhook` method:
    - The webhook payload structure for messages in Chatery places the sender phone under `data.senderPhone`.
    - However, looking at the Chatery payload from earlier explorations, the sender's phone might actually be `data.from` or `data.senderPhone` depending on the event format.
    - We need to ensure that `chatId` is correctly populated. If `from_phone` is `None` during sending, it's because `message_data.get("senderPhone")` failed. We should fall back to `message_data.get("from")` if `senderPhone` is not present.
    - The `send-text` request requires `sessionId`, `chatId`, and `message`.
- **Handling `message.sent` event:**
  - We need to handle `message.sent` events in the webhook to verify message sending.

## Proposed Changes

### 1. Update Webhook Event Registration
**File**: `backend/routes/chatery.py`
- In `connect_chatery()`, update the `events` payload parameter to `["all"]` so the backend receives `message.sent` events.

### 2. Fix Message Data Extraction & Handle `message.sent`
**File**: `backend/routes/chatery.py`
- In `chatery_webhook()`:
  - Add fallback logic for extracting the phone number: `from_phone = message_data.get("senderPhone") or message_data.get("from")`.
  - Add a block to handle `event == "message.sent"`. When received, log a success message: `logger.info(f"Message sent confirmation received for session {session_id} to {message_data.get('to')}")`.
  - Ensure the `chatId` passed to `send-text` strips any `@s.whatsapp.net` suffix if present, which is already handled by `replace('@s.whatsapp.net', '')`.

## Assumptions & Decisions
- Setting `events` to `["all"]` is safe and will just result in more unhandled events being logged as "Unhandled webhook event", which is fine for debugging.
- The `message.sent` event will contain data about the sent message. Based on standard Baileys/Chatery payloads, it usually contains a `to` field.
- The root cause of `from_phone` being `None` during sending is that `senderPhone` was not the correct key for this specific Chatery payload format. Adding `message_data.get("from")` as a fallback ensures we capture it regardless of the format variation.

## Verification Steps
- Trigger a reconnect to register the new `["all"]` webhook events.
- Send a message to the bot.
- Verify in the logs that `from_phone` is correctly parsed (not `None`).
- Verify in the logs that the `send-text` request succeeds and the reply is delivered.
- Verify in the logs that a `message.sent` event is received and handled correctly.