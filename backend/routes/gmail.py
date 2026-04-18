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
def authorize_gmail(payload: Optional[dict] = None, current_user: User = Depends(get_current_user)):
    oauth_config = _get_oauth_credentials()
    if not oauth_config:
        raise HTTPException(status_code=400, detail="OAuth2 credentials not configured")

    try:
        config = oauth_config.get("web") or oauth_config.get("installed")
        # We assume the frontend callback URL for Gmail is http://localhost:3000/api/auth/callback/google
        redirect_uri = "http://localhost:3000/api/auth/callback/google"

        client_id = config.get("client_id")

        code_verifier, code_challenge = _build_pkce_pair()
        state = secrets.token_urlsafe(32)

        OAUTH_STATE_STORE[state] = (code_verifier, datetime.now().timestamp() + 600)

        flow = Flow.from_client_config(
            oauth_config,
            scopes=GMAIL_SCOPES,
        )
        flow.redirect_uri = redirect_uri

        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=state,
            code_challenge=code_challenge,
            code_challenge_method='S256'
        )
        return {"authorization_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate auth url: {str(e)}")

@router.post("/oauth/callback")
def complete_gmail_oauth(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    code = payload.get("code")
    state = payload.get("state")

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    oauth_config = _get_oauth_credentials()
    if not oauth_config:
        raise HTTPException(status_code=400, detail="OAuth2 credentials not configured")

    state_data = OAUTH_STATE_STORE.pop(state, None) if state else None
    code_verifier = state_data[0] if state_data else None

    try:
        flow = Flow.from_client_config(
            oauth_config,
            scopes=GMAIL_SCOPES,
        )
        flow.redirect_uri = "http://localhost:3000/api/auth/callback/google"
        flow.fetch_token(code=code, code_verifier=code_verifier)
        credentials = flow.credentials

        # Get user's email address
        service = build('gmail', 'v1', credentials=credentials)
        profile = service.users().getProfile(userId='me').execute()
        user_email = profile.get('emailAddress')

        # Update user in database
        current_user.google_email = user_email
        current_user.google_access_token = credentials.token
        current_user.google_refresh_token = credentials.refresh_token
        db.commit()

        # Start watch
        request_body = {
            'labelIds': ['INBOX'],
            'topicName': TOPIC_NAME,
            'labelFilterBehavior': 'INCLUDE'
        }
        watch_response = service.users().watch(userId='me', body=request_body).execute()

        return {
            "message": "Gmail OAuth complete and watch started",
            "email": user_email,
            "watch_response": watch_response
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete OAuth: {str(e)}")

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
        # Fetch actual changes
        # For a full implementation, you need a startHistoryId, but we'll print the push received
        print(f"Processing push update for {user_email}, new historyId: {history_id}")

        # Since we're keeping it simple and haven't stored startHistoryId,
        # we could just list the most recent messages:
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
