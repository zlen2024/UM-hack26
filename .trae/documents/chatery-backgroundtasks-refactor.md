## Summary

Refactor the Chatery WhatsApp webhook to (1) extract Chatery “send text message” logic into a reusable function in `chatery.py`, and (2) acknowledge inbound webhooks immediately while doing LLM processing + outbound replies in FastAPI `BackgroundTasks`. Apply the same “ack fast, respond async” best practice to Telegram and Meta WhatsApp webhooks for consistent behavior and better reliability under slow LLM calls.

## Current State Analysis

### Chatery

- Webhook endpoint: `POST /api/chatery/webhook` in [chatery.py](file:///workspace/backend/routes/chatery.py#L188-L313).
- Current behavior:
  - Parses webhook JSON.
  - For `event == "message"`, does DB lookup, calls `process_whatsapp_message()` (LLM call), then sends reply via `requests.post()` to Chatery `/chats/send-text` inline (blocking request lifecycle) at [chatery.py:L281-L303](file:///workspace/backend/routes/chatery.py#L281-L303).

### Telegram

- Webhook endpoint: `POST /api/telegram/webhook/{bot_token}` in [telegram.py](file:///workspace/backend/routes/telegram.py#L101-L164).
- Current behavior:
  - Parses inbound update, does DB lookups, calls `process_telegram_message()` (LLM call), then sends reply inline via Telegram `sendMessage` at [telegram.py:L148-L163](file:///workspace/backend/routes/telegram.py#L148-L163).

### Meta WhatsApp Cloud API

- Webhook endpoint: `POST /api/whatsapp/webhook` in [whatsapp.py](file:///workspace/backend/routes/whatsapp.py#L201-L318).
- Current behavior:
  - Validates signature (good), does DB lookups, calls `process_whatsapp_message()` (LLM call), then sends reply inline via Graph API at [whatsapp.py:L300-L316](file:///workspace/backend/routes/whatsapp.py#L300-L316).

### Existing BackgroundTasks Usage

- `BackgroundTasks` is already used in the Gmail webhook at [gmail.py:L366-L404](file:///workspace/backend/routes/gmail.py#L366-L404), which indicates the codebase is open to this pattern.

## Proposed Changes

### 1) Make Chatery send-text reusable

**File:** [chatery.py](file:///workspace/backend/routes/chatery.py)

- Add a module-level helper function (no new module required, per request):
  - `send_chatery_text_message(*, session_id: str, chat_id: str, message: str, typing_time: int = 1500) -> dict`
- Implementation details:
  - Build URL: `f"{CHATERY_API_URL}/chats/send-text"`.
  - Use `get_chatery_headers()` for auth headers.
  - Use `requests.post(..., timeout=<small>)` to avoid hanging threads.
  - Log success/failure via existing `logger`.
  - Return a structured dict like `{"success": bool, "status_code": int | None, "error": str | None, "response": dict | None}` (pure primitives).

### 2) Chatery webhook: acknowledge immediately + background processing

**File:** [chatery.py](file:///workspace/backend/routes/chatery.py)

- Change the webhook signature to accept `background_tasks: BackgroundTasks`:
  - `async def chatery_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db))`
- In the `event == "message"` branch:
  - Keep lightweight parsing + validation in the request thread (current parsing logic can remain).
  - Avoid doing the LLM call and outbound send inline.
  - Schedule a background function (defined in the same file) and return immediately:
    - Return body: `{"status": "accepted"}` (and optionally include `event`, `sessionId` for debugging).
- New background function:
  - `def process_chatery_message_and_reply(*, session_id: str, from_phone: str, contact_name: str, text: str) -> None`
  - Inside background function:
    - Create its own SQLAlchemy session (do not re-use the request-scoped `db`, because it will be closed after the response):
      - `from database import SessionLocal` (already present in `database.py`)
      - `db = SessionLocal()` with `try/finally: db.close()`
    - Load `ChateryWhatsAppSession` by `session_id`, then `User` by `session.user_id`.
    - Call `process_whatsapp_message()` with the same payload as today.
    - If response exists: call `send_chatery_text_message(...)`.
    - Log outcomes via `logger`.
- Keep existing “ignore fromMe” guard and “empty text” guard in the request handler so we don’t queue useless work.

### 3) Telegram webhook: acknowledge immediately + background processing

**File:** [telegram.py](file:///workspace/backend/routes/telegram.py)

- Add `BackgroundTasks` to the endpoint signature:
  - `async def receive_webhook(bot_token: str, request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db))`
- Change flow:
  - Parse payload and validate “has message + text” inline (fast).
  - Instead of calling the agent and sending inline, schedule a background function and return `{"status": "accepted"}`.
- Background function:
  - `def process_telegram_update_and_reply(*, bot_token: str, chat_id: str, contact_name: str, text: str) -> None`
  - Create its own DB session (`SessionLocal`) and fetch `TelegramBot` config + `User`.
  - Call `process_telegram_message()` then `send_telegram_message()`.
  - Prefer using structured logging (or at minimum replace `print` with the module’s logger if one exists; otherwise add a logger consistent with this file’s conventions).

### 4) Meta WhatsApp webhook: acknowledge immediately + background processing

**File:** [whatsapp.py](file:///workspace/backend/routes/whatsapp.py)

- Add `BackgroundTasks` to the endpoint signature:
  - `async def receive_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db))`
- Keep signature validation inline (must remain request-scoped, based on raw body).
- After extracting message data and confirming it’s a user message:
  - Schedule background function and return HTTP 200 with `{"status":"accepted"}`.
- Background function:
  - `def process_whatsapp_webhook_message_and_reply(*, display_phone: str, recipient: str, contact_name: str, text: str) -> None`
  - Create its own DB session (`SessionLocal`) and fetch `WhatsAppPhoneNumber` config + `User`.
  - Call `process_whatsapp_message()` then `send_whatsapp_message()`.

## Assumptions & Decisions

- Decision: Use FastAPI/Starlette `BackgroundTasks` (in-process) as the best-practice improvement requested, because it provides immediate webhook acknowledgements without introducing new infrastructure.
- Decision: Keep `requests` and the existing synchronous LLM client calls, but run them in background tasks (Starlette will execute sync background functions without blocking the response).
- Decision: Do not introduce external queues (Celery/RQ) in this change. If throughput grows, this is the next step.
- Decision: Background functions create their own DB sessions via `SessionLocal` to avoid using a request-scoped session that may be closed after returning the webhook response.

## Verification Steps

- Run a syntax/type sanity check:
  - `python -m compileall backend`
- Run a lightweight import check to ensure route modules still import:
  - `python -c "import backend.routes.chatery, backend.routes.telegram, backend.routes.whatsapp"`
- Manual smoke test (local/dev):
  - Send a sample webhook payload to each endpoint and verify:
    - HTTP response is immediate with `200 OK` and `status=accepted`.
    - Background logs show message processing and outbound send attempts.
