import base64
import json
from fastapi import APIRouter, Depends, HTTPException, Request, Response, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
import secrets
from typing import Optional

from auth import get_current_user
from database import get_db
from models import User

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

router = APIRouter()

GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TOPIC_NAME = 'projects/umhack26/topics/UMHackCRM'

# We reuse the calendar OAuth credentials structure
from routes.google_calendar import _get_oauth_credentials, _build_pkce_pair, OAUTH_STATE_STORE

@router.get("/oauth/authorize")
def authorize_gmail(request: Request, payload: Optional[dict] = None, current_user: User = Depends(get_current_user)):
    oauth_config = _get_oauth_credentials()
    if not oauth_config:
        raise HTTPException(status_code=400, detail="OAuth2 credentials not configured")

    try:
        config = oauth_config.get("web") or oauth_config.get("installed")

        origin = request.headers.get("origin")
        referer = request.headers.get("referer")

        if origin:
            base_url = origin
        elif referer:
            parts = referer.split("/")
            base_url = f"{parts[0]}//{parts[2]}"
        else:
            scheme = request.headers.get("x-forwarded-proto", "http" if "localhost" in request.url.netloc else "https")
            host = request.headers.get("x-forwarded-host", request.url.netloc)
            base_url = f"{scheme}://{host}"

        if "um-hack26" in base_url or "fly.dev" in base_url or ("localhost" not in base_url and "127.0.0.1" not in base_url):
            base_url = "https://um-hack26-zf1hkq.fly.dev"

        redirect_uri = f"{base_url}/api/auth/callback/google"

        client_id = config.get("client_id")

        code_verifier, code_challenge = _build_pkce_pair()
        state = secrets.token_urlsafe(32)

        OAUTH_STATE_STORE[state] = (code_verifier, datetime.now().timestamp() + 600)

        flow = Flow.from_client_config(
            oauth_config,
            scopes=GMAIL_SCOPES,
        )

        flow.redirect_uri = redirect_uri

        authorization_url, state_generated = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state,
            prompt='consent'
        )

        return {
            "authorization_url": authorization_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete OAuth: {str(e)}")

@router.post("/oauth/callback")
async def gmail_oauth_callback(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        data = await request.json()
        code = data.get('code')
        state = data.get('state')

        if not code or not state:
            raise HTTPException(status_code=400, detail="Missing code or state")

        if state not in OAUTH_STATE_STORE:
            raise HTTPException(status_code=400, detail="Invalid state")

        code_verifier, expires_at = OAUTH_STATE_STORE[state]

        if datetime.now().timestamp() > expires_at:
            del OAUTH_STATE_STORE[state]
            raise HTTPException(status_code=400, detail="OAuth state expired")

        oauth_config = _get_oauth_credentials()
        if not oauth_config:
            raise HTTPException(status_code=400, detail="OAuth2 credentials not configured")

        flow = Flow.from_client_config(
            oauth_config,
            scopes=GMAIL_SCOPES,
        )

        origin = request.headers.get("origin")
        referer = request.headers.get("referer")

        if origin:
            base_url = origin
        elif referer:
            parts = referer.split("/")
            base_url = f"{parts[0]}//{parts[2]}"
        else:
            scheme = request.headers.get("x-forwarded-proto", "http" if "localhost" in request.url.netloc else "https")
            host = request.headers.get("x-forwarded-host", request.url.netloc)
            base_url = f"{scheme}://{host}"

        if "um-hack26" in base_url or "fly.dev" in base_url or ("localhost" not in base_url and "127.0.0.1" not in base_url):
            base_url = "https://um-hack26-zf1hkq.fly.dev"

        redirect_uri = f"{base_url}/api/auth/callback/google"
        flow.redirect_uri = redirect_uri

        flow.fetch_token(code=code) # Not using PKCE verifier here since standard flow doesn't always need it or we didn't send challenge
        # Let's handle it with PKCE since we generated verifier
        # Actually Google Python client flow.fetch_token doesn't take code_verifier in kwargs sometimes depending on the version.
        # But we can try passing it if we built the challenge. However, in our flow.authorization_url we didn't pass code_challenge.
        # So we should just fetch_token(code=code)

        credentials = flow.credentials

        service = build('gmail', 'v1', credentials=credentials)
        profile = service.users().getProfile(userId='me').execute()
        user_email = profile.get('emailAddress')

        current_user.google_email = user_email
        current_user.google_access_token = credentials.token
        current_user.google_refresh_token = credentials.refresh_token
        db.commit()

        request_body = {
            'labelIds': ['INBOX'],
            'topicName': TOPIC_NAME,
            'labelFilterBehavior': 'INCLUDE'
        }
        watch_response = service.users().watch(userId='me', body=request_body).execute()

        # Cleanup state
        del OAUTH_STATE_STORE[state]

        return {
            "message": "Gmail connected successfully",
            "email": user_email
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete OAuth callback: {str(e)}")

def process_gmail_update(user_email: str, history_id: str, db: Session):
    user = db.query(User).filter(User.google_email == user_email).first()
    if not user or not user.google_refresh_token:
        print(f"User {user_email} not found or no refresh token")
        return

    oauth_config = _get_oauth_credentials()
    if not oauth_config:
        return

    config = oauth_config.get("web") or oauth_config.get("installed")
    creds = Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri=config.get("token_uri"),
        client_id=config.get("client_id"),
        client_secret=config.get("client_secret")
    )

    try:
        service = build('gmail', 'v1', credentials=creds)
        print(f"Processing push update for {user_email}, new historyId: {history_id}")

        messages = service.users().messages().list(userId='me', maxResults=5).execute()
        print("Recent messages:", [m['id'] for m in messages.get('messages', [])])

    except Exception as e:
        print(f"Error processing gmail update: {str(e)}")

@router.post("/webhooks/gmail")
async def gmail_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    envelope = await request.json()

    pubsub_message = envelope.get("message", {})
    if not pubsub_message:
        return Response(status_code=400)

    try:
        data_str = base64.b64decode(pubsub_message["data"]).decode("utf-8")
        data = json.loads(data_str)

        user_email = data.get("emailAddress")
        history_id = data.get("historyId")

        if user_email and history_id:
            background_tasks.add_task(process_gmail_update, user_email, history_id, db)

    except Exception as e:
        print(f"Webhook decode error: {str(e)}")

    return Response(status_code=200)

@router.post("/renew-watch")
def renew_watch(db: Session = Depends(get_db)):
    users = db.query(User).filter(User.google_refresh_token.isnot(None)).all()
    oauth_config = _get_oauth_credentials()

    if not oauth_config:
        raise HTTPException(status_code=400, detail="OAuth config not found")

    config = oauth_config.get("web") or oauth_config.get("installed")
    successes = []
    errors = []

    for user in users:
        try:
            creds = Credentials(
                token=user.google_access_token,
                refresh_token=user.google_refresh_token,
                token_uri=config.get("token_uri"),
                client_id=config.get("client_id"),
                client_secret=config.get("client_secret")
            )
            service = build('gmail', 'v1', credentials=creds)
            request_body = {
                'labelIds': ['INBOX'],
                'topicName': TOPIC_NAME,
                'labelFilterBehavior': 'INCLUDE'
            }
            service.users().watch(userId='me', body=request_body).execute()
            successes.append(user.google_email)
        except Exception as e:
            errors.append(f"{user.google_email}: {str(e)}")

    return {"renewed": successes, "errors": errors}
