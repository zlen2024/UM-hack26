# Plan: Fix Chatery Webhook Message Parsing

## Summary
The current `chatery.py` webhook handler assumes the incoming message data uses `from` and `text` fields. However, the Chatery WhatsApp API uses `senderPhone` for the phone number, `senderName` for the contact's name, and `content` (for text messages) or `caption` (for media messages) for the message body. Because of this mismatch, `None` is being passed to the `cs_agent`, resulting in a `400 Invalid JSON data` error from the Ilmu AI API.

This plan updates the webhook handler to correctly extract these fields from the Chatery payload, ensuring the AI agent receives the correct data and can successfully generate and send an automated reply.

## Current State Analysis
- **Webhook Endpoint**: `backend/routes/chatery.py` -> `chatery_webhook`
- **Current Extraction Logic**: 
  ```python
  from_phone = message_data.get("from")
  text = message_data.get("text")
  ```
- **Actual Chatery Payload**:
  ```json
  "data": {
    "senderPhone": "628123456789",
    "senderName": "John Doe",
    "type": "text",
    "content": "Hello",
    "caption": null
  }
  ```
- **Error Triggered**: `cs_agent` passes `None` for the message content to Ilmu AI, which rejects it with a `400` validation error.

## Proposed Changes
1. **Modify `backend/routes/chatery.py`**:
   - Update the extraction logic in the `if event == "message":` block.
   - Extract `from_phone` using `message_data.get("senderPhone")`.
   - Extract `contact_name` using `message_data.get("senderName")`.
   - Extract the message text based on the message type: if `type == "text"`, use `content`; otherwise, fallback to `caption`. Ensure the final `text` is always a string.
   - Add a check to skip processing and return `{"status": "ok", "message": "Empty text"}` if the extracted text is empty, preventing unnecessary calls to the AI model.
   - Update `agent_payload` to use the dynamically extracted `contact_name` instead of hardcoding `"Chatery Contact"`.

## Assumptions & Decisions
- We only want the AI to reply if there is actual text to respond to (either a direct text message or a media caption). Empty messages (like a sticker or a photo without a caption) will be gracefully skipped.
- The `senderPhone` field in the Chatery payload is already stripped of the `@s.whatsapp.net` suffix, which makes it perfectly formatted for the `send-text` API endpoint.

## Verification Steps
- Wait for a new message webhook from Chatery.
- Verify in the backend logs that the `senderPhone` and `text` are correctly extracted.
- Verify that `cs_agent` successfully calls Ilmu AI without throwing a `400` error.
- Verify that the automated reply is sent back to the correct `from_phone`.