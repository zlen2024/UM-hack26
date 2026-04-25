# Plan: Resolve WhatsApp LIDs to Phone Numbers

## Summary
When receiving incoming messages via the Chatery WhatsApp webhook, the `senderPhone` field occasionally contains an LID (Linked Identity) format (e.g., `147527898800287@lid`) instead of a standard JID (e.g., `60123456789@s.whatsapp.net`). This is a privacy feature by WhatsApp. To ensure proper contact matching and CRM integration, we need to resolve these LIDs to standard phone numbers using the Chatery `/contacts` API and cache the results to optimize performance.

## Current State Analysis
- The `chatery_webhook` handler in `backend/routes/chatery.py` extracts `from_phone` from `message_data.get("senderPhone")` or `message_data.get("from")`.
- Currently, `from_phone` is used as-is, meaning LIDs are passed directly to the AI agent (`cs_agent`) and potentially saved or logged without resolving to the actual phone number.
- When sending an automated reply, the code strips `@s.whatsapp.net` but doesn't handle `@lid`.

## Proposed Changes

### 1. Implement LID caching and resolution in `routes/chatery.py`
- **Global Cache**: Add an in-memory cache `LID_TO_PHONE_CACHE = {}` to map known LIDs to their respective phone numbers, minimizing redundant API calls.
- **Resolution Function**: Create a new async helper `resolve_lid_to_phone(session_id: str, lid: str) -> str`:
  - Check `LID_TO_PHONE_CACHE`. If the LID is cached, return the phone number immediately.
  - If not cached, make a POST request to the Chatery `/contacts` API endpoint (`f"{CHATERY_API_URL}/contacts"`).
  - Iterate through the returned contacts to find the matching LID.
  - Extract the real phone number (checking fields like `jid`, `number`, or `id` ending in `@s.whatsapp.net` if the mapping provides it) and update `LID_TO_PHONE_CACHE`.
  - If resolution fails, return the original LID as a fallback.

### 2. Update `chatery_webhook` logic in `routes/chatery.py`
- Modify the `from_phone` extraction logic when `event == "message"`:
  - If `from_phone.endswith('@s.whatsapp.net')`: Extract the base phone number by splitting at `@`.
  - If `from_phone.endswith('@lid')`: Await `resolve_lid_to_phone(session_id, from_phone)` to get the real phone number.
  - Check the webhook payload for any nested `vcard` or `profile` objects that might contain the phone number directly, as an additional fallback before calling the API.
- Ensure the resolved phone number is passed cleanly to the `process_whatsapp_message` agent payload and used for the `chatId` in the reply.

## Assumptions & Decisions
- **In-Memory Cache**: A simple Python dictionary (`LID_TO_PHONE_CACHE`) will be used for caching. This assumes a single-worker deployment or that cache misses resulting in an API call are acceptable across multiple workers.
- **Contact Object Structure**: We assume the Chatery `/contacts` API returns a list of contacts where the LID and actual phone number can be correlated. The exact key for the phone number might need to be inferred (e.g., `id`, `jid`, `phoneNumber`), so we will implement robust extraction logic.
- **Fallback**: If the LID cannot be resolved (e.g., WhatsApp strictly masks it because the user isn't in the contact list), the system will gracefully fall back to using the LID, as WhatsApp still allows replying to LIDs.

## Verification Steps
1. Simulate an incoming webhook payload with an `@lid` in the `senderPhone` field.
2. Verify that the system intercepts the LID, calls the `/contacts` API, and correctly caches and resolves it to the real phone number.
3. Confirm that the AI agent receives the correct standard phone number.
4. Verify that subsequent webhook payloads with the same LID retrieve the phone number directly from the cache without calling the API.