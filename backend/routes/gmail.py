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
    print(f"[OAuth] [{datetime.now().isoformat()}] ==== GMAIL OAUTH START ====")
    print(f"[OAuth] User ID: {current_user.id}, Email: {current_user.email}")
    
    oauth_config = _get_oauth_credentials()
    if not oauth_config:
        print(f"[OAuth] ERROR: OAuth credentials not configured in .env")
        raise HTTPException(status_code=400, detail="OAuth2 credentials not configured")
    
    print(f"[OAuth] Credentials loaded - client_id: {oauth_config.get('web', {}).get('client_id', 'N/A')[:30]}...")

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
        print(f"[OAuth] Redirect URI: {redirect_uri}")

        client_id = config.get("client_id")
        print(f"[OAuth] Client ID: {client_id[:30]}...")

        code_verifier, code_challenge = _build_pkce_pair()
        print(f"[OAuth] PKCE generated - verifier length: {len(code_verifier)}, challenge length: {len(code_challenge)}")
        
        state = secrets.token_urlsafe(32)
        print(f"[OAuth] State: {state[:20]}...")

        OAUTH_STATE_STORE[state] = (code_verifier, datetime.now().timestamp() + 600)
        print(f"[OAuth] State stored in memory, TTL: 600s")

        flow = Flow.from_client_config(
            oauth_config,
            scopes=GMAIL_SCOPES,
        )

        flow.redirect_uri = redirect_uri
        print(f"[OAuth] Flow configured with scopes: {GMAIL_SCOPES}")

        authorization_url, state_generated = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state,
            prompt='consent',
            code_challenge=code_challenge,
            code_challenge_method='S256'
        )
        
        print(f"[OAuth] Authorization URL generated (full URL printed below):")
        print(f"[OAuth] URL: {authorization_url}")
        print(f"[OAuth] ==== AUTHORIZATION URL READY ====")

        return {
            "authorization_url": authorization_url
        }

    except Exception as e:
        print(f"[OAuth] ERROR: {str(e)}")
        import traceback
        print(f"[OAuth] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to complete OAuth: {str(e)}")

@router.post("/oauth/callback")
async def gmail_oauth_callback(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    print(f"[OAuth Callback] [{datetime.now().isoformat()}] ==== GMAIL OAUTH CALLBACK START ====")
    print(f"[OAuth Callback] User ID: {current_user.id}, Email: {current_user.email}")
    
    try:
        data = await request.json()
        code = data.get('code')
        state = data.get('state')

        print(f"[OAuth Callback] Received - code: {code[:30] if code else 'None'}..., state: {state[:20] if state else 'None'}...")
        
        if not code or not state:
            print(f"[OAuth Callback] ERROR: Missing code or state")
            raise HTTPException(status_code=400, detail="Missing code or state")

        if state not in OAUTH_STATE_STORE:
            print(f"[OAuth Callback] ERROR: State not in store - {state}")
            raise HTTPException(status_code=400, detail="Invalid state")

        code_verifier, expires_at = OAUTH_STATE_STORE[state]
        print(f"[OAuth Callback] State found - expires at: {expires_at}, remaining: {expires_at - datetime.now().timestamp()}s")

        if datetime.now().timestamp() > expires_at:
            del OAUTH_STATE_STORE[state]
            print(f"[OAuth Callback] ERROR: State expired")
            raise HTTPException(status_code=400, detail="OAuth state expired")

        oauth_config = _get_oauth_credentials()
        if not oauth_config:
            print(f"[OAuth Callback] ERROR: OAuth config not found")
            raise HTTPException(status_code=400, detail="OAuth2 credentials not configured")
        
        print(f"[OAuth Callback] OAuth config loaded")

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
        print(f"[OAuth Callback] Flow configured with redirect_uri: {redirect_uri}")

        print(f"[OAuth Callback] Fetching token with code_verifier...")
        flow.fetch_token(code=code, code_verifier=code_verifier)
        print(f"[OAuth Callback] Token fetched successfully")

        credentials = flow.credentials
        print(f"[OAuth Callback] Access token: {credentials.token[:30] if credentials.token else 'None'}...")
        print(f"[OAuth Callback] Refresh token: {'Yes, length: ' + str(len(credentials.refresh_token)) if credentials.refresh_token else 'None'}")

        print(f"[OAuth Callback] Building Gmail service...")
        service = build('gmail', 'v1', credentials=credentials)
        
        print(f"[OAuth Callback] Getting user profile...")
        profile = service.users().getProfile(userId='me').execute()
        user_email = profile.get('emailAddress')
        print(f"[OAuth Callback] Gmail user email: {user_email}")

        print(f"[OAuth Callback] Saving tokens to database for user_id: {current_user.id}")
        current_user.google_email = user_email
        current_user.google_access_token = credentials.token
        current_user.google_refresh_token = credentials.refresh_token
        db.commit()
        print(f"[OAuth Callback] Tokens saved successfully")

        print(f"[OAuth Callback] Setting up Gmail watch for topic: {TOPIC_NAME}")
        request_body = {
            'labelIds': ['INBOX'],
            'topicName': TOPIC_NAME,
            'labelFilterBehavior': 'INCLUDE'
        }
        watch_response = service.users().watch(userId='me', body=request_body).execute()
        print(f"[OAuth Callback] Watch response: {watch_response}")

        # Cleanup state
        del OAUTH_STATE_STORE[state]
        print(f"[OAuth Callback] State cleaned up")

        print(f"[OAuth Callback] ==== GMAIL CONNECTED SUCCESSFULLY ====")
        
        return {
            "message": "Gmail connected successfully",
            "email": user_email
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete OAuth callback: {str(e)}")

def process_gmail_update(user_email: str, history_id: str, db: Session):
    from models import Email
    from datetime import datetime
    
    print(f"[Process] [{datetime.now().isoformat()}] ==== PROCESS GMAIL UPDATE START ====")
    print(f"[Process] User email: {user_email}, History ID: {history_id}")
    
    user = db.query(User).filter(User.google_email == user_email).first()
    if not user or not user.google_refresh_token:
        print(f"[Process] ERROR: User {user_email} not found or no refresh token")
        return
    
    print(f"[Process] User found - id: {user.id}, has refresh_token: {bool(user.google_refresh_token)}")

    oauth_config = _get_oauth_credentials()
    if not oauth_config:
        print(f"[Process] ERROR: OAuth config not found")
        return
    
    print(f"[Process] OAuth config loaded")

    config = oauth_config.get("web") or oauth_config.get("installed")
    print(f"[Process] Building credentials for user...")
    creds = Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri=config.get("token_uri"),
        client_id=config.get("client_id"),
        client_secret=config.get("client_secret")
    )

    try:
        print(f"[Process] Building Gmail service...")
        service = build('gmail', 'v1', credentials=creds)
        print(f"[Process] Fetching messages.list() for user: {user_email}")
        
        results = service.users().messages().list(
            userId='me',
            maxResults=10,
            labelIds=['INBOX'],
        ).execute()
        
        messages = results.get('messages', [])
        print(f"[Process] Found {len(messages)} messages in inbox")
        
        stored_count = 0
        for i, msg_meta in enumerate(messages):
            msg_id = msg_meta['id']
            print(f"[Process] [{i+1}/{len(messages)}] Checking message: {msg_id}")
            
            existing = db.query(Email).filter(
                Email.gmail_id == msg_id,
                Email.user_id == user.id
            ).first()
            
            if existing:
                print(f"[Process] [{i+1}/{len(messages)}] Already exists, skipping")
                continue
            
            print(f"[Process] [{i+1}/{len(messages)}] Fetching full message: {msg_id}")
            msg = service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
            
            payload = msg.get('payload', {})
            headers = payload.get('headers', {})
            
            subject = headers.get('Subject', '')
            from_email = headers.get('From', '')
            to_email = headers.get('To', '')
            snippet = msg.get('snippet', '')
            thread_id = msg.get('threadId')
            label_ids = ','.join(msg.get('labelIds', []))
            msg_history_id = msg.get('historyId', '')
            
            print(f"[Process] [{i+1}/{len(messages)}] Parsed - subject: {subject[:50]}...")
            print(f"[Process] [{i+1}/{len(messages)}] From: {from_email}")
            print(f"[Process] [{i+1}/{len(messages)}] To: {to_email}")
            print(f"[Process] [{i+1}/{len(messages)}] Labels: {label_ids}")
            print(f"[Process] [{i+1}/{len(messages)}] Thread ID: {thread_id}")
            
            body = ''
            html_body = ''
            
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain' and 'body' in part and 'data' in part.get('body', {}):
                        body = base64.b64decode(part['body']['data']).decode('utf-8', errors='replace')
                        print(f"[Process] [{i+1}/{len(messages)}] Found text/plain body, length: {len(body)}")
                    elif part.get('mimeType') == 'text/html' and 'body' in part and 'data' in part.get('body', {}):
                        html_body = base64.b64decode(part['body']['data']).decode('utf-8', errors='replace')
                        print(f"[Process] [{i+1}/{len(messages)}] Found text/html body, length: {len(html_body)}")
            
            if not body and 'body' in payload and 'data' in payload.get('body', {}):
                body = base64.b64decode(payload['body']['data']).decode('utf-8', errors='replace')
                print(f"[Process] [{i+1}/{len(messages)}] Found body in payload, length: {len(body)}")
            
            try:
                internal_date = int(msg.get('internalDate', 0)) / 1000
                received_at = datetime.fromtimestamp(internal_date)
            except:
                received_at = datetime.utcnow()
            
            print(f"[Process] [{i+1}/{len(messages)}] Received at: {received_at.isoformat()}")
            
            email_record = Email(
                user_id=user.id,
                gmail_id=msg_id,
                thread_id=thread_id,
                subject=subject,
                from_email=from_email,
                to_email=to_email,
                snippet=snippet[:500] if snippet else '',
                body=body[:50000] if body else '',
                html_body=html_body[:50000] if html_body else '',
                label_ids=label_ids,
                history_id=msg_history_id,
                is_read='UNREAD' not in label_ids,
                received_at=received_at,
            )
            db.add(email_record)
            print(f"[Process] [{i+1}/{len(messages)}] Stored email: {subject[:50]}...")
            stored_count += 1
        
        print(f"[Process] Committing {stored_count} new emails to database...")
        db.commit()
        print(f"[Process] SUCCESS - {stored_count} new emails stored for {user_email}")
        print(f"[Process] ==== PROCESS COMPLETE ====")

    except Exception as e:
        print(f"[Process] ERROR: {str(e)}")
        import traceback
        print(f"[Process] Traceback: {traceback.format_exc()}")

@router.post("/webhooks/gmail")
async def gmail_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    print(f"[Webhook] [{datetime.now().isoformat()}] ==== GMAIL WEBHOOK RECEIVED ====")
    
    envelope = await request.json()
    print(f"[Webhook] Full envelope: {json.dumps(envelope)[:500]}...")

    pubsub_message = envelope.get("message", {})
    if not pubsub_message:
        print(f"[Webhook] ERROR: No message in envelope")
        return Response(status_code=400)

    try:
        data_str = base64.b64decode(pubsub_message["data"]).decode("utf-8")
        data = json.loads(data_str)
        
        print(f"[Webhook] Decoded data (first 500 chars): {data_str[:500]}...")
        print(f"[Webhook] Parsed JSON keys: {list(data.keys())}")

        user_email = data.get("emailAddress")
        history_id = data.get("historyId")
        
        print(f"[Webhook] Email address: {user_email}")
        print(f"[Webhook] History ID: {history_id}")

        if user_email and history_id:
            print(f"[Webhook] Scheduling background task: process_gmail_update({user_email}, {history_id})")
            background_tasks.add_task(process_gmail_update, user_email, history_id, db)
            print(f"[Webhook] Background task scheduled")
        else:
            print(f"[Webhook] WARNING: Missing user_email or history_id - not scheduling task")

    except Exception as e:
        print(f"[Webhook] ERROR: {str(e)}")
        import traceback
        print(f"[Webhook] Traceback: {traceback.format_exc()}")

    print(f"[Webhook] ==== WEBHOOK HANDLED - RETURNING 200 ====")
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
