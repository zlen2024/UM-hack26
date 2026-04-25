# Plan: Fix Chatery Webhook Text Extraction

## Summary
The logs reveal that `from_phone` is now successfully extracted (`147527898800287`), but the AI processing was skipped because the text was considered empty. The webhook logged `Message text: None` right before it exited with `Message webhook: Empty text, skipping AI processing`.

We need to fix the message text extraction logic to properly grab the message content based on the actual JSON structure received from the Chatery API.

## Current State Analysis
- **Webhook Endpoint**: `backend/routes/chatery.py` -> `chatery_webhook`
- **Incoming Payload Structure**:
  ```json
  "data": {
    "type": "text",
    "content": "test"
  }
  ```
- **Current Code Logic**:
  ```python
  msg_type = message_data.get("type")
  if msg_type == "text":
      text = message_data.get("content")
  else:
      text = message_data.get("caption")
  ```
- **The Issue**: 
  If `message_data.get("content")` is actually working but somehow returning `None` or failing, we need to inspect why. However, looking at the logs provided by the user in a previous turn:
  ```json
  {"event": "message", "sessionId": "2", "metadata": {"userId": 2}, "data": {"id": "AC25DD961AB33EB125973B2096F83B08", "chatId": "147527898800287@lid", "fromMe": false, "sender": "147527898800287@lid", "senderPhone": "147527898800287", "senderName": "nel", "timestamp": 1776995360, "type": "text", "content": "test", "caption": null, "mimetype": null, "filename": null, "mediaUrl": null, "isGroup": false, "quotedMessage": null}, "timestamp": "2026-04-24T01:49:20.142Z"}
  ```
  The payload clearly has `"content": "test"`. If the text was parsed as empty in the latest log, it could be that the `text` variable isn't correctly assigned, or there is another format variation we aren't accounting for (like `message.text` or `text` being at the root of `data`). To be safe, we will add fallback logic to `text` extraction.

## Proposed Changes
1. **Modify `backend/routes/chatery.py`**:
   - Update the text extraction to aggressively look for text across all possible fields: `content`, `text`, `caption`, `message`.
   ```python
   text = message_data.get("content") or message_data.get("text") or message_data.get("message") or message_data.get("caption") or ""
   ```
   - This removes the rigid `if msg_type == "text"` check, which might be failing if the type is unexpected or missing, and ensures we grab whatever text is available in the payload.

## Assumptions & Decisions
- A robust fallback chain is safer than relying on `msg_type` alone, as Chatery payloads might vary slightly between text, media, and interactive messages.
- We will still ensure `text` defaults to an empty string `""` so `.strip()` doesn't throw an AttributeError.

## Verification Steps
- Wait for a new message webhook from Chatery.
- Verify in the logs that `Message text: test` is correctly printed.
- Verify that the `Empty text` early exit is bypassed and the CS agent is called.