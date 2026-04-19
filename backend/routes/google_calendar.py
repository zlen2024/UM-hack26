from datetime import datetime, timedelta
from base64 import urlsafe_b64encode
import hashlib
from pathlib import Path
import secrets
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode
from uuid import uuid4
import xml.etree.ElementTree as ET
import json

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Activity, User
from schemas import (
    GoogleCalendarCredentials,
    GoogleCalendarEventCreate,
    GoogleCalendarEventUpdate,
    GoogleCalendarEventResponse,
)

# Google Calendar API imports
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.auth.transport.requests import Request as GoogleAuthRequest
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    # Print diagnostic message
    import sys
    print("WARNING: google-api-python-client not installed", file=sys.stderr)
    print("To use real Google Calendar API, run:", file=sys.stderr)
    print("  pip install google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib", file=sys.stderr)

router = APIRouter()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
XML_PATH = DATA_DIR / "google_calendar.xml"
OAUTH_CREDENTIALS_PATH = DATA_DIR / "oauth_credentials.json"
TOKENS_DIR = DATA_DIR / "tokens"
DEFAULT_TEST_EMAIL = "fakhrulhakimy93@gmail.com"
SCOPES = ['https://www.googleapis.com/auth/calendar']
OAUTH_STATE_TTL_SECONDS = 600
OAUTH_STATE_STORE: Dict[str, Tuple[str, float]] = {}


def _prune_oauth_state_store() -> None:
    now = time.time()
    expired_states = [
        state for state, (_, expires_at) in OAUTH_STATE_STORE.items() if expires_at <= now
    ]
    for state in expired_states:
        del OAUTH_STATE_STORE[state]


def _build_pkce_pair() -> Tuple[str, str]:
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return code_verifier, code_challenge


import os
import json

def _get_oauth_credentials():
    """Load OAuth2 credentials from env variables or fallback to file"""
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

    if client_id and client_secret:
        return {
            "web": {
                "client_id": client_id,
                "project_id": os.environ.get("GOOGLE_PROJECT_ID", "umhack26"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": client_secret,
                "redirect_uris": [
                    "https://um-hack26-zf1hkq.fly.dev/api/auth/callback/google",
                    "http://localhost:3000/api/auth/callback/google",
                    "http://127.0.0.1:3000/api/auth/callback/google"
                ]
            }
        }

    if not OAUTH_CREDENTIALS_PATH.exists():
        return None
    try:
        with open(OAUTH_CREDENTIALS_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading OAuth credentials: {e}")
        return None


def _build_calendar_service_oauth(user_id: int):
    """Build Google Calendar service using OAuth2 credentials for a user"""
    if not GOOGLE_API_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="Google API client not installed. Run: pip install google-api-python-client google-auth-oauthlib"
        )
    
    # Ensure tokens directory exists
    TOKENS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get OAuth2 config
    oauth_config = _get_oauth_credentials()
    if not oauth_config:
        raise HTTPException(
            status_code=400,
            detail="OAuth2 credentials not configured. Please upload credentials JSON."
        )
    
    # Token file for this user
    token_file = TOKENS_DIR / f"user_{user_id}_token.json"
    creds = None
    
    # Load existing token if available
    if token_file.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
        except Exception as e:
            print(f"Error loading token: {e}")
            creds = None
    
    # If no valid credentials, need to authorize
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleAuthRequest())
        else:
            # This would normally require user to authenticate via browser
            # For now, we'll raise an error
            raise HTTPException(
                status_code=400,
                detail="OAuth2 authorization needed. Please authorize the application."
            )
        
        # Save the refreshed token
        with open(token_file, 'w') as f:
            f.write(creds.to_json())
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create Calendar service: {str(e)}"
        )


def _query_params(request: Request) -> dict:
    return {key: value for key, value in request.query_params.items()}


def _execute_google_request(callable_request, error_prefix: str):
    try:
        return callable_request.execute()
    except HttpError as e:
        error_message = str(e)
        try:
            error_details = json.loads(e.content.decode('utf-8'))
            error_message = error_details.get('error', {}).get('message', str(e))
        except Exception:
            pass
        raise HTTPException(status_code=400, detail=f"{error_prefix}: {error_message}")


def _normalize_attendees(emails: List[str]) -> List[str]:
    seen = set()
    cleaned = []
    for email in emails:
        if not email:
            continue
        key = email.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        cleaned.append(email.strip())
    return cleaned


def _create_google_calendar_event(
    service,
    title: str,
    description: str,
    start_time: datetime,
    end_time: datetime,
    attendee_emails: List[str],
    calendar_id: str,
) -> str:
    """Create a real event in Google Calendar and return event ID"""
    try:
        attendees = _normalize_attendees(attendee_emails)
        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC'
            },
        }

        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        
        result = service.events().insert(
            calendarId=calendar_id,
            body=event,
            sendUpdates='all'
        ).execute()
        return result['id']
    except HttpError as e:
        error_details = json.loads(e.content.decode('utf-8'))
        error_message = error_details.get('error', {}).get('message', str(e))
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create Google Calendar event: {error_message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error creating calendar event: {str(e)}"
        )


def _update_google_calendar_event(
    service,
    event_id: str,
    updates: dict,
    calendar_id: str,
) -> None:
    try:
        service.events().patch(
            calendarId=calendar_id,
            eventId=event_id,
            body=updates,
            sendUpdates='all',
        ).execute()
    except HttpError as e:
        error_details = json.loads(e.content.decode('utf-8'))
        error_message = error_details.get('error', {}).get('message', str(e))
        raise HTTPException(
            status_code=400,
            detail=f"Failed to update Google Calendar event: {error_message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error updating calendar event: {str(e)}"
        )


def _delete_google_calendar_event(service, event_id: str, calendar_id: str) -> None:
    try:
        service.events().delete(
            calendarId=calendar_id,
            eventId=event_id,
            sendUpdates='all',
        ).execute()
    except HttpError as e:
        error_details = json.loads(e.content.decode('utf-8'))
        error_message = error_details.get('error', {}).get('message', str(e))
        raise HTTPException(
            status_code=400,
            detail=f"Failed to delete Google Calendar event: {error_message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error deleting calendar event: {str(e)}"
        )


def _get_google_calendar_events(
    service,
    calendar_id: str,
    limit: int = 250,
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
) -> List[dict]:
    """Get all events from Google Calendar with pagination"""
    try:
        if time_min is None:
            time_min = (datetime.utcnow() - timedelta(days=365)).replace(microsecond=0).isoformat() + "Z"
        if time_max is None:
            time_max = (datetime.utcnow() + timedelta(days=365)).replace(microsecond=0).isoformat() + "Z"
        
        all_events = []
        page_token = None
        
        # Fetch all pages
        while True:
            results = service.events().list(
                calendarId=calendar_id,
                maxResults=min(limit, 250),  # Google's max is 250
                orderBy='startTime',
                singleEvents=True,
                timeMin=time_min,
                timeMax=time_max,
                pageToken=page_token,
            ).execute()
            
            items = results.get('items', [])
            all_events.extend(items)
            
            # Check for next page
            page_token = results.get('nextPageToken')
            if not page_token:
                break
        
        return all_events
    except HttpError as e:
        error_details = json.loads(e.content.decode('utf-8'))
        error_message = error_details.get('error', {}).get('message', str(e))
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch Google Calendar events: {error_message}"
        )


def _ensure_tree() -> ET.ElementTree:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not XML_PATH.exists():
        root = ET.Element("google_calendar")
        tree = ET.ElementTree(root)
        tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
    return ET.parse(XML_PATH)


def _get_user_node(
    root: ET.Element, user_id: int, create: bool = False
) -> Optional[ET.Element]:
    node = root.find(f"./user[@id='{user_id}']")
    if node is None and create:
        node = ET.SubElement(root, "user", {"id": str(user_id)})
    return node


def _get_credentials_node(user_node: ET.Element) -> ET.Element:
    node = user_node.find("credentials")
    if node is None:
        node = ET.SubElement(user_node, "credentials")
    return node


def _get_events_node(user_node: ET.Element) -> ET.Element:
    node = user_node.find("events")
    if node is None:
        node = ET.SubElement(user_node, "events")
    return node


def _write_tree(tree: ET.ElementTree) -> None:
    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)


def _ensure_activity_columns(db: Session) -> None:
    result = db.execute(text("PRAGMA table_info(activities)")).fetchall()
    columns = {row[1] for row in result}
    if "source" not in columns:
        db.execute(text("ALTER TABLE activities ADD COLUMN source TEXT"))
    if "external_id" not in columns:
        db.execute(text("ALTER TABLE activities ADD COLUMN external_id TEXT"))
    db.commit()


@router.get("/credentials")
def get_credentials(current_user: User = Depends(get_current_user)):
    tree = _ensure_tree()
    root = tree.getroot()
    user_node = _get_user_node(root, current_user.id)
    if user_node is None:
        return {"connected": False, "test_email": None}

    cred = user_node.find("credentials")
    test_email = cred.get("test_email") if cred is not None else None
    oauth_configured = OAUTH_CREDENTIALS_PATH.exists()
    token_file = TOKENS_DIR / f"user_{current_user.id}_token.json"
    authorized = False
    if token_file.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
            authorized = bool(creds.valid or (creds.expired and creds.refresh_token))
        except Exception:
            authorized = False
    connected = oauth_configured and authorized
    return {
        "connected": connected,
        "test_email": test_email,
        "oauth_configured": oauth_configured,
        "authorized": authorized,
    }


@router.post("/credentials")
def save_credentials(
    payload: GoogleCalendarCredentials,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.api_key:
        raise HTTPException(
            status_code=400,
            detail="API keys are not supported. Upload OAuth2 credentials JSON."
        )

    if payload.oauth_credentials:
        creds = payload.oauth_credentials
        if "web" not in creds and "installed" not in creds:
            raise HTTPException(
                status_code=400,
                detail="Invalid credentials format. Expected 'web' or 'installed' key"
            )
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(OAUTH_CREDENTIALS_PATH, 'w') as f:
            json.dump(creds, f, indent=2)

    if not _get_oauth_credentials():
        raise HTTPException(
            status_code=400,
            detail="OAuth2 credentials not configured. Upload credentials JSON."
        )

    tree = _ensure_tree()
    root = tree.getroot()
    user_node = _get_user_node(root, current_user.id, create=True)
    if user_node is None:
        raise HTTPException(status_code=500, detail="Failed to initialize storage")

    cred = _get_credentials_node(user_node)
    if "api_key" in cred.attrib:
        del cred.attrib["api_key"]
    test_email = payload.test_email or cred.get("test_email") or DEFAULT_TEST_EMAIL
    cred.set("test_email", test_email)
    cred.set("auth_type", "oauth")
    cred.set("updated_at", datetime.utcnow().isoformat())

    # Create test event in REAL Google Calendar (OAuth)
    start_time = datetime.utcnow() + timedelta(minutes=10)
    end_time = start_time + timedelta(minutes=30)
    
    title = "Integration Test"
    description = f"Test event created after saving OAuth credentials. Attendee: {test_email}"

    success = False
    google_event_id = str(uuid4())
    oauth_error = None
    try:
        service = _build_calendar_service_oauth(current_user.id)
        attendee_emails = _normalize_attendees(
            [test_email, current_user.email]
        )
        google_event_id = _create_google_calendar_event(
            service,
            title,
            description,
            start_time,
            end_time,
            attendee_emails,
            "primary",
        )
        print(f"✅ Created REAL Google Calendar event: {google_event_id}")
        success = True
    except HTTPException as e:
        oauth_error = e.detail
        print("⚠️ Warning: Could not create Google Calendar event")
        print(f"   Error: {e.detail}")
        print("   Using local storage as fallback")

    # Also store in local XML for backup
    events_node = _get_events_node(user_node)
    event_node = ET.SubElement(events_node, "event", {"id": google_event_id, "type": "test", "source": "google_calendar"})
    ET.SubElement(event_node, "title").text = title
    ET.SubElement(event_node, "description").text = description
    ET.SubElement(event_node, "start_time").text = start_time.isoformat()
    ET.SubElement(event_node, "end_time").text = end_time.isoformat()
    attendees_node = ET.SubElement(event_node, "attendees")
    for email in _normalize_attendees([test_email, current_user.email]):
        ET.SubElement(attendees_node, "attendee").text = email

    _write_tree(tree)

    # Create Activity record
    _ensure_activity_columns(db)
    db_activity = Activity(
        user_id=current_user.id,
        type="meeting",
        description="\n".join(
            [
                f"Title: {title}",
                f"Attendee: {test_email}",
                f"End: {end_time.isoformat()}",
                f"Google Calendar ID: {google_event_id}",
            ]
        ),
        scheduled_at=start_time,
        source="google_calendar",
        external_id=google_event_id,
    )
    db.add(db_activity)
    db.commit()

    return {
        "status": "saved",
        "test_event_id": google_event_id,
        "test_email": test_email,
        "message": "Test event created in Google Calendar!" if success else "Test event created in CRM (OAuth authorization pending)",
        "google_calendar_created": success,
        "oauth_error": oauth_error,
    }


@router.delete("/credentials")
def clear_credentials(current_user: User = Depends(get_current_user)):
    tree = _ensure_tree()
    root = tree.getroot()
    user_node = _get_user_node(root, current_user.id)
    if user_node is None:
        return {"status": "cleared"}

    cred = user_node.find("credentials")
    if cred is not None:
        user_node.remove(cred)
        _write_tree(tree)
    return {"status": "cleared"}


@router.get("/events", response_model=List[GoogleCalendarEventResponse])
def list_events(
    current_user: User = Depends(get_current_user),
    calendar_id: Optional[str] = Query(None),
    limit: int = Query(250, ge=1, le=500),
    time_min: Optional[str] = Query(None),
    time_max: Optional[str] = Query(None),
):
    """Fetch events from real Google Calendar API"""
    tree = _ensure_tree()
    root = tree.getroot()
    user_node = _get_user_node(root, current_user.id)
    if user_node is None:
        return []

    try:
        service = _build_calendar_service_oauth(current_user.id)
        resolved_calendar_id = calendar_id or "primary"
        google_events = _get_google_calendar_events(
            service,
            calendar_id=resolved_calendar_id,
            limit=limit,
            time_min=time_min,
            time_max=time_max,
        )

        events: List[GoogleCalendarEventResponse] = []
        for google_event in google_events:
            start = google_event.get('start', {})
            end = google_event.get('end', {})

            start_time = start.get('dateTime') or start.get('date')
            end_time = end.get('dateTime') or end.get('date')

            if not start_time or not end_time:
                continue

            events.append(
                GoogleCalendarEventResponse(
                    id=google_event.get('id', ''),
                    title=google_event.get('summary', ''),
                    description=google_event.get('description') or None,
                    start_time=start_time,
                    end_time=end_time,
                )
            )
        return events
    except Exception as e:
        print(f"Warning: Could not fetch from Google Calendar: {str(e)}")

    # Fallback to local XML storage
    events_node = user_node.find("events")
    if events_node is None:
        return []

    events: List[GoogleCalendarEventResponse] = []
    for event in events_node.findall("event"):
        start_text = event.findtext("start_time")
        end_text = event.findtext("end_time")
        if not start_text or not end_text:
            continue
        events.append(
            GoogleCalendarEventResponse(
                id=event.get("id", ""),
                title=event.findtext("title", default=""),
                description=event.findtext("description") or None,
                start_time=start_text,
                end_time=end_text,
            )
        )
    return events


@router.post("/events", response_model=GoogleCalendarEventResponse)
def create_event(
    payload: GoogleCalendarEventCreate,
    calendar_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tree = _ensure_tree()
    root = tree.getroot()
    user_node = _get_user_node(root, current_user.id, create=True)
    if user_node is None:
        raise HTTPException(status_code=500, detail="Failed to initialize storage")

    cred = user_node.find("credentials")
    test_email = DEFAULT_TEST_EMAIL
    if cred is not None and cred.get("test_email"):
        test_email = cred.get("test_email")

    service = _build_calendar_service_oauth(current_user.id)
    resolved_calendar_id = calendar_id or "primary"

    attendee_emails = _normalize_attendees(
        (payload.attendees or []) + [test_email, current_user.email]
    )

    # Create in real Google Calendar
    try:
        google_event_id = _create_google_calendar_event(
            service,
            payload.title,
            payload.description or "",
            payload.start_time,
            payload.end_time,
            attendee_emails,
            resolved_calendar_id,
        )
        event_id = google_event_id
        print(f"✅ Created Google Calendar event: {event_id}")
    except HTTPException as e:
        raise HTTPException(status_code=400, detail=e.detail)

    # Also store in local XML
    events_node = _get_events_node(user_node)
    event_node = ET.SubElement(
        events_node,
        "event",
        {
            "id": event_id,
            "source": "google_calendar",
            "calendar_id": resolved_calendar_id,
        },
    )
    ET.SubElement(event_node, "title").text = payload.title
    ET.SubElement(event_node, "description").text = payload.description or ""
    ET.SubElement(event_node, "start_time").text = payload.start_time.isoformat()
    ET.SubElement(event_node, "end_time").text = payload.end_time.isoformat()
    if attendee_emails:
        attendees_node = ET.SubElement(event_node, "attendees")
        for email in attendee_emails:
            ET.SubElement(attendees_node, "attendee").text = email
    if payload.contact_id is not None:
        ET.SubElement(event_node, "contact_id").text = str(payload.contact_id)
    if payload.opportunity_id is not None:
        ET.SubElement(event_node, "opportunity_id").text = str(payload.opportunity_id)

    _write_tree(tree)

    _ensure_activity_columns(db)
    description_lines = [payload.title]
    if payload.description:
        description_lines.append(payload.description)
    if attendee_emails:
        description_lines.append(f"Attendees: {', '.join(attendee_emails)}")
    description_lines.append(f"End: {payload.end_time.isoformat()}")

    db_activity = Activity(
        user_id=current_user.id,
        type="meeting",
        description="\n".join(description_lines),
        scheduled_at=payload.start_time,
        source="google_calendar",
        external_id=event_id,
        contact_id=payload.contact_id,
        opportunity_id=payload.opportunity_id,
    )
    db.add(db_activity)
    db.commit()

    return GoogleCalendarEventResponse(
        id=event_id,
        title=payload.title,
        description=payload.description,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )


@router.put("/events/{event_id}", response_model=GoogleCalendarEventResponse)
def update_event(
    event_id: str,
    payload: GoogleCalendarEventUpdate,
    calendar_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tree = _ensure_tree()
    root = tree.getroot()
    user_node = _get_user_node(root, current_user.id, create=True)
    if user_node is None:
        raise HTTPException(status_code=500, detail="Failed to initialize storage")

    events_node = _get_events_node(user_node)
    event_node = events_node.find(f"./event[@id='{event_id}']")
    resolved_calendar_id = (
        calendar_id
        or (event_node.get("calendar_id") if event_node is not None else None)
        or "primary"
    )

    def _set_text(tag: str, value: str) -> None:
        if event_node is None:
            return
        node = event_node.find(tag)
        if node is None:
            node = ET.SubElement(event_node, tag)
        node.text = value

    if event_node is not None:
        if payload.title is not None:
            _set_text("title", payload.title)
        if payload.description is not None:
            _set_text("description", payload.description)
        if payload.start_time is not None:
            _set_text("start_time", payload.start_time.isoformat())
        if payload.end_time is not None:
            _set_text("end_time", payload.end_time.isoformat())
        if payload.attendees is not None:
            attendees_node = event_node.find("attendees")
            if attendees_node is not None:
                event_node.remove(attendees_node)
            attendees_node = ET.SubElement(event_node, "attendees")
            for email in _normalize_attendees(payload.attendees):
                ET.SubElement(attendees_node, "attendee").text = email
        if payload.contact_id is not None:
            _set_text("contact_id", str(payload.contact_id))
        if payload.opportunity_id is not None:
            _set_text("opportunity_id", str(payload.opportunity_id))

    if event_node is not None and resolved_calendar_id:
        event_node.set("calendar_id", resolved_calendar_id)

    source = event_node.get("source") if event_node is not None else "google_calendar"
    google_event = None
    if source == "google_calendar":
        updates = {}
        if payload.title is not None:
            updates["summary"] = payload.title
        if payload.description is not None:
            updates["description"] = payload.description
        if payload.start_time is not None:
            updates["start"] = {
                "dateTime": payload.start_time.isoformat(),
                "timeZone": "UTC",
            }
        if payload.end_time is not None:
            updates["end"] = {
                "dateTime": payload.end_time.isoformat(),
                "timeZone": "UTC",
            }
        if payload.attendees is not None:
            attendees = _normalize_attendees(payload.attendees)
            updates["attendees"] = [{"email": email} for email in attendees]
        service = _build_calendar_service_oauth(current_user.id)
        if updates:
            _update_google_calendar_event(service, event_id, updates, resolved_calendar_id)
        google_event = _execute_google_request(
            service.events().get(calendarId=resolved_calendar_id, eventId=event_id),
            "Failed to fetch event",
        )

    if google_event and event_node is not None:
        start_payload = google_event.get("start", {})
        end_payload = google_event.get("end", {})
        start_text = start_payload.get("dateTime") or start_payload.get("date")
        end_text = end_payload.get("dateTime") or end_payload.get("date")
        if start_text:
            _set_text("start_time", start_text)
        if end_text:
            _set_text("end_time", end_text)
        _set_text("title", google_event.get("summary", ""))
        _set_text("description", google_event.get("description") or "")
        attendees_node = event_node.find("attendees")
        if attendees_node is not None:
            event_node.remove(attendees_node)
        attendees = [
            attendee.get("email")
            for attendee in google_event.get("attendees", [])
            if attendee.get("email")
        ]
        if attendees:
            attendees_node = ET.SubElement(event_node, "attendees")
            for email in attendees:
                ET.SubElement(attendees_node, "attendee").text = email

    if event_node is not None:
        _write_tree(tree)

    _ensure_activity_columns(db)
    activity = (
        db.query(Activity)
        .filter(Activity.user_id == current_user.id)
        .filter(Activity.source == "google_calendar")
        .filter(Activity.external_id == event_id)
        .first()
    )
    if activity is None:
        legacy_tag = f"[calendar:{event_id}]"
        activity = (
            db.query(Activity)
            .filter(Activity.user_id == current_user.id)
            .filter(Activity.description.contains(legacy_tag))
            .first()
        )
        if activity is not None:
            activity.source = "google_calendar"
            activity.external_id = event_id

    if google_event:
        start_payload = google_event.get("start", {})
        end_payload = google_event.get("end", {})
        start_text = start_payload.get("dateTime") or start_payload.get("date")
        end_text = end_payload.get("dateTime") or end_payload.get("date")
        title_text = google_event.get("summary", "")
        desc_text = google_event.get("description") or ""
    else:
        start_text = event_node.findtext("start_time")
        end_text = event_node.findtext("end_time")
        title_text = event_node.findtext("title", default="")
        desc_text = event_node.findtext("description") or ""
    if not start_text or not end_text:
        raise HTTPException(status_code=500, detail="Event time data missing")
    description_lines = [title_text.strip()]
    if desc_text:
        description_lines.append(desc_text)
    description_lines.append(f"End: {end_text}")

    scheduled_at = None
    try:
        scheduled_at = datetime.fromisoformat(start_text)
    except ValueError:
        scheduled_at = None

    if activity is None:
        activity = Activity(
            user_id=current_user.id,
            type="meeting",
            description="\n".join(description_lines),
            scheduled_at=scheduled_at,
            source="google_calendar",
            external_id=event_id,
            contact_id=payload.contact_id,
            opportunity_id=payload.opportunity_id,
        )
        db.add(activity)
    else:
        activity.description = "\n".join(description_lines)
        if payload.start_time is not None:
            activity.scheduled_at = payload.start_time
        elif scheduled_at is not None:
            activity.scheduled_at = scheduled_at
        if payload.contact_id is not None:
            activity.contact_id = payload.contact_id
        if payload.opportunity_id is not None:
            activity.opportunity_id = payload.opportunity_id
    db.commit()

    return GoogleCalendarEventResponse(
        id=event_id,
        title=title_text,
        description=desc_text or None,
        start_time=start_text,
        end_time=end_text,
    )


@router.delete("/events/{event_id}")
def delete_event(
    event_id: str,
    calendar_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tree = _ensure_tree()
    root = tree.getroot()
    user_node = _get_user_node(root, current_user.id)
    events_node = None
    event_node = None
    if user_node is not None:
        events_node = user_node.find("events")
        if events_node is not None:
            event_node = events_node.find(f"./event[@id='{event_id}']")

    resolved_calendar_id = (
        calendar_id
        or (event_node.get("calendar_id") if event_node is not None else None)
        or "primary"
    )

    source = event_node.get("source") if event_node is not None else "google_calendar"
    if source == "google_calendar":
        service = _build_calendar_service_oauth(current_user.id)
        _delete_google_calendar_event(service, event_id, resolved_calendar_id)

    if event_node is not None and events_node is not None:
        events_node.remove(event_node)
        _write_tree(tree)

    _ensure_activity_columns(db)
    activity = (
        db.query(Activity)
        .filter(Activity.user_id == current_user.id)
        .filter(Activity.source == "google_calendar")
        .filter(Activity.external_id == event_id)
        .first()
    )
    if activity is None:
        legacy_tag = f"[calendar:{event_id}]"
        activity = (
            db.query(Activity)
            .filter(Activity.user_id == current_user.id)
            .filter(Activity.description.contains(legacy_tag))
            .first()
        )
    if activity is not None:
        db.delete(activity)
        db.commit()

    return {"status": "deleted"}


@router.post("/oauth/upload-credentials")
def upload_oauth_credentials(payload: dict, current_user: User = Depends(get_current_user)):
    """
    Upload OAuth2 credentials JSON from Google Cloud Console
    Expected payload: {"credentials": {...oauth2 credentials...}} or raw JSON
    """
    try:
        creds = payload.get("credentials") or payload
        if not isinstance(creds, dict):
            raise ValueError("Credentials payload must be a JSON object")
        
        # Validate it's the correct format (should have 'web' or 'installed' key)
        if "web" not in creds and "installed" not in creds:
            raise ValueError("Invalid credentials format. Expected 'web' or 'installed' key")
        
        # Save to file
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(OAUTH_CREDENTIALS_PATH, 'w') as f:
            json.dump(creds, f, indent=2)
        
        return {
            "status": "uploaded",
            "message": "OAuth2 credentials saved successfully",
            "path": str(OAUTH_CREDENTIALS_PATH)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error saving credentials: {str(e)}")


@router.post("/oauth/authorize")
def authorize_oauth(payload: Optional[dict] = None, current_user: User = Depends(get_current_user)):
    """
    Start OAuth2 authorization flow (returns authorization URL)
    """
    oauth_config = _get_oauth_credentials()
    if not oauth_config:
        raise HTTPException(status_code=400, detail="OAuth2 credentials not configured")
    
    try:
        config = oauth_config.get("web") or oauth_config.get("installed")
        if not isinstance(config, dict):
            raise ValueError("Invalid OAuth configuration format")

        requested_redirect = payload.get("redirect_uri") if isinstance(payload, dict) else None
        redirect_uris = config.get("redirect_uris")
        redirect_uri = requested_redirect or (redirect_uris[0] if redirect_uris else None)
        if not redirect_uri:
            raise ValueError("redirect_uri is required in OAuth client configuration")

        auth_uri = config.get("auth_uri")
        client_id = config.get("client_id")
        if not auth_uri or not client_id:
            raise ValueError("OAuth client_id or auth_uri missing")

        code_verifier, code_challenge = _build_pkce_pair()
        state = secrets.token_urlsafe(32)
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        auth_uri = f"{auth_uri}?{urlencode(params)}"

        _prune_oauth_state_store()
        OAUTH_STATE_STORE[state] = (
            code_verifier,
            time.time() + OAUTH_STATE_TTL_SECONDS,
        )

        return {
            "status": "authorization_required",
            "authorization_url": auth_uri,
            "state": state,
            "redirect_uri": redirect_uri,
            "message": "Visit the URL above to authorize the application"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error starting OAuth flow: {str(e)}")


@router.post("/oauth/complete")
def complete_oauth(payload: dict, current_user: User = Depends(get_current_user)):
    """
    Exchange authorization code for tokens and persist them
    Expected payload: {"code": "...", "redirect_uri": "..."}
    """
    code = payload.get("code") if isinstance(payload, dict) else None
    redirect_uri = payload.get("redirect_uri") if isinstance(payload, dict) else None
    state = payload.get("state") if isinstance(payload, dict) else None
    code_verifier = payload.get("code_verifier") if isinstance(payload, dict) else None
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is required")

    oauth_config = _get_oauth_credentials()
    if not oauth_config:
        raise HTTPException(status_code=400, detail="OAuth2 credentials not configured")

    config = oauth_config.get("web") or oauth_config.get("installed")
    if not config:
        raise HTTPException(status_code=400, detail="OAuth2 credentials are invalid")

    flow = Flow.from_client_config(
        {"web": config} if "web" in oauth_config else oauth_config,
        SCOPES,
    )

    if redirect_uri:
        flow.redirect_uri = redirect_uri
    elif isinstance(config, dict) and config.get("redirect_uris"):
        flow.redirect_uri = config.get("redirect_uris")[0]

    if not code_verifier and state:
        _prune_oauth_state_store()
        stored = OAUTH_STATE_STORE.pop(state, None)
        if stored:
            code_verifier = stored[0]

    if not code_verifier:
        raise HTTPException(status_code=400, detail="Missing code verifier. Please re-authorize.")

    try:
        flow.fetch_token(code=code, code_verifier=code_verifier)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to exchange code: {str(e)}")

    TOKENS_DIR.mkdir(parents=True, exist_ok=True)
    token_file = TOKENS_DIR / f"user_{current_user.id}_token.json"
    with open(token_file, 'w') as f:
        f.write(flow.credentials.to_json())

    return {"status": "authorized"}


@router.post("/calendar", response_model=GoogleCalendarEventResponse)
def create_calendar(
    payload: GoogleCalendarEventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_event(payload, current_user, db)


@router.put("/calendar/{event_id}", response_model=GoogleCalendarEventResponse)
def update_calendar(
    event_id: str,
    payload: GoogleCalendarEventUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_event(event_id, payload, current_user, db)


@router.delete("/calendar/{event_id}")
def delete_calendar(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return delete_event(event_id, current_user, db)


# --- Google Calendar API passthrough (OAuth required) ---

@router.get("/gcal/colors")
def gcal_colors(current_user: User = Depends(get_current_user)):
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(service.colors().get(), "Failed to fetch colors")


@router.post("/gcal/channels/stop")
def gcal_channels_stop(payload: dict, current_user: User = Depends(get_current_user)):
    if not payload:
        raise HTTPException(status_code=400, detail="Channel body is required")
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(service.channels().stop(body=payload), "Failed to stop channel")


# Calendars
@router.get("/gcal/calendars/{calendar_id}")
def gcal_calendars_get(calendar_id: str, current_user: User = Depends(get_current_user)):
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(service.calendars().get(calendarId=calendar_id), "Failed to fetch calendar")


@router.post("/gcal/calendars")
def gcal_calendars_insert(payload: dict, current_user: User = Depends(get_current_user)):
    if not payload:
        raise HTTPException(status_code=400, detail="Calendar body is required")
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(service.calendars().insert(body=payload), "Failed to create calendar")


@router.delete("/gcal/calendars/{calendar_id}")
def gcal_calendars_delete(calendar_id: str, current_user: User = Depends(get_current_user)):
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(service.calendars().delete(calendarId=calendar_id), "Failed to delete calendar")


@router.post("/gcal/calendars/{calendar_id}/clear")
def gcal_calendars_clear(calendar_id: str, current_user: User = Depends(get_current_user)):
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(service.calendars().clear(calendarId=calendar_id), "Failed to clear calendar")


@router.patch("/gcal/calendars/{calendar_id}")
def gcal_calendars_patch(calendar_id: str, payload: dict, current_user: User = Depends(get_current_user)):
    if not payload:
        raise HTTPException(status_code=400, detail="Calendar patch body is required")
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(
        service.calendars().patch(calendarId=calendar_id, body=payload),
        "Failed to patch calendar",
    )


@router.put("/gcal/calendars/{calendar_id}")
def gcal_calendars_update(calendar_id: str, payload: dict, current_user: User = Depends(get_current_user)):
    if not payload:
        raise HTTPException(status_code=400, detail="Calendar update body is required")
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(
        service.calendars().update(calendarId=calendar_id, body=payload),
        "Failed to update calendar",
    )


# CalendarList
@router.get("/gcal/users/me/calendarList")
def gcal_calendar_list(request: Request, current_user: User = Depends(get_current_user)):
    service = _build_calendar_service_oauth(current_user.id)
    params = _query_params(request)
    return _execute_google_request(
        service.calendarList().list(**params),
        "Failed to list calendarList",
    )


@router.get("/gcal/users/me/calendarList/{calendar_id}")
def gcal_calendar_list_get(calendar_id: str, current_user: User = Depends(get_current_user)):
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(
        service.calendarList().get(calendarId=calendar_id),
        "Failed to fetch calendarList entry",
    )


@router.post("/gcal/users/me/calendarList")
def gcal_calendar_list_insert(payload: dict, current_user: User = Depends(get_current_user)):
    if not payload:
        raise HTTPException(status_code=400, detail="CalendarList body is required")
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(
        service.calendarList().insert(body=payload),
        "Failed to insert calendarList entry",
    )


@router.delete("/gcal/users/me/calendarList/{calendar_id}")
def gcal_calendar_list_delete(calendar_id: str, current_user: User = Depends(get_current_user)):
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(
        service.calendarList().delete(calendarId=calendar_id),
        "Failed to delete calendarList entry",
    )


@router.patch("/gcal/users/me/calendarList/{calendar_id}")
def gcal_calendar_list_patch(calendar_id: str, payload: dict, current_user: User = Depends(get_current_user)):
    if not payload:
        raise HTTPException(status_code=400, detail="CalendarList patch body is required")
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(
        service.calendarList().patch(calendarId=calendar_id, body=payload),
        "Failed to patch calendarList entry",
    )


@router.put("/gcal/users/me/calendarList/{calendar_id}")
def gcal_calendar_list_update(calendar_id: str, payload: dict, current_user: User = Depends(get_current_user)):
    if not payload:
        raise HTTPException(status_code=400, detail="CalendarList update body is required")
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(
        service.calendarList().update(calendarId=calendar_id, body=payload),
        "Failed to update calendarList entry",
    )


@router.post("/gcal/users/me/calendarList/watch")
def gcal_calendar_list_watch(payload: dict, current_user: User = Depends(get_current_user)):
    if not payload:
        raise HTTPException(status_code=400, detail="Watch body is required")
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(
        service.calendarList().watch(body=payload),
        "Failed to watch calendarList",
    )


# ACL
@router.get("/gcal/calendars/{calendar_id}/acl")
def gcal_acl_list(calendar_id: str, request: Request, current_user: User = Depends(get_current_user)):
    service = _build_calendar_service_oauth(current_user.id)
    params = _query_params(request)
    return _execute_google_request(
        service.acl().list(calendarId=calendar_id, **params),
        "Failed to list ACL",
    )


@router.post("/gcal/calendars/{calendar_id}/acl")
def gcal_acl_insert(calendar_id: str, payload: dict, current_user: User = Depends(get_current_user)):
    if not payload:
        raise HTTPException(status_code=400, detail="ACL body is required")
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(
        service.acl().insert(calendarId=calendar_id, body=payload),
        "Failed to insert ACL rule",
    )


@router.get("/gcal/calendars/{calendar_id}/acl/{rule_id}")
def gcal_acl_get(calendar_id: str, rule_id: str, current_user: User = Depends(get_current_user)):
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(
        service.acl().get(calendarId=calendar_id, ruleId=rule_id),
        "Failed to fetch ACL rule",
    )


@router.delete("/gcal/calendars/{calendar_id}/acl/{rule_id}")
def gcal_acl_delete(calendar_id: str, rule_id: str, current_user: User = Depends(get_current_user)):
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(
        service.acl().delete(calendarId=calendar_id, ruleId=rule_id),
        "Failed to delete ACL rule",
    )


@router.patch("/gcal/calendars/{calendar_id}/acl/{rule_id}")
def gcal_acl_patch(calendar_id: str, rule_id: str, payload: dict, current_user: User = Depends(get_current_user)):
    if not payload:
        raise HTTPException(status_code=400, detail="ACL patch body is required")
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(
        service.acl().patch(calendarId=calendar_id, ruleId=rule_id, body=payload),
        "Failed to patch ACL rule",
    )


@router.put("/gcal/calendars/{calendar_id}/acl/{rule_id}")
def gcal_acl_update(calendar_id: str, rule_id: str, payload: dict, current_user: User = Depends(get_current_user)):
    if not payload:
        raise HTTPException(status_code=400, detail="ACL update body is required")
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(
        service.acl().update(calendarId=calendar_id, ruleId=rule_id, body=payload),
        "Failed to update ACL rule",
    )


@router.post("/gcal/calendars/{calendar_id}/acl/watch")
def gcal_acl_watch(calendar_id: str, payload: dict, current_user: User = Depends(get_current_user)):
    if not payload:
        raise HTTPException(status_code=400, detail="Watch body is required")
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(
        service.acl().watch(calendarId=calendar_id, body=payload),
        "Failed to watch ACL",
    )


# Events
@router.get("/gcal/calendars/{calendar_id}/events")
def gcal_events_list(calendar_id: str, request: Request, current_user: User = Depends(get_current_user)):
    service = _build_calendar_service_oauth(current_user.id)
    params = _query_params(request)
    return _execute_google_request(
        service.events().list(calendarId=calendar_id, **params),
        "Failed to list events",
    )


@router.post("/gcal/calendars/{calendar_id}/events")
def gcal_events_insert(calendar_id: str, payload: dict, request: Request, current_user: User = Depends(get_current_user)):
    if not payload:
        raise HTTPException(status_code=400, detail="Event body is required")
    service = _build_calendar_service_oauth(current_user.id)
    params = _query_params(request)
    return _execute_google_request(
        service.events().insert(calendarId=calendar_id, body=payload, **params),
        "Failed to create event",
    )


@router.get("/gcal/calendars/{calendar_id}/events/{event_id}")
def gcal_events_get(calendar_id: str, event_id: str, current_user: User = Depends(get_current_user)):
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(
        service.events().get(calendarId=calendar_id, eventId=event_id),
        "Failed to fetch event",
    )


@router.delete("/gcal/calendars/{calendar_id}/events/{event_id}")
def gcal_events_delete(calendar_id: str, event_id: str, current_user: User = Depends(get_current_user)):
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(
        service.events().delete(calendarId=calendar_id, eventId=event_id),
        "Failed to delete event",
    )


@router.patch("/gcal/calendars/{calendar_id}/events/{event_id}")
def gcal_events_patch(calendar_id: str, event_id: str, payload: dict, request: Request, current_user: User = Depends(get_current_user)):
    if not payload:
        raise HTTPException(status_code=400, detail="Event patch body is required")
    service = _build_calendar_service_oauth(current_user.id)
    params = _query_params(request)
    return _execute_google_request(
        service.events().patch(calendarId=calendar_id, eventId=event_id, body=payload, **params),
        "Failed to patch event",
    )


@router.put("/gcal/calendars/{calendar_id}/events/{event_id}")
def gcal_events_update(calendar_id: str, event_id: str, payload: dict, request: Request, current_user: User = Depends(get_current_user)):
    if not payload:
        raise HTTPException(status_code=400, detail="Event update body is required")
    service = _build_calendar_service_oauth(current_user.id)
    params = _query_params(request)
    return _execute_google_request(
        service.events().update(calendarId=calendar_id, eventId=event_id, body=payload, **params),
        "Failed to update event",
    )


@router.get("/gcal/calendars/{calendar_id}/events/{event_id}/instances")
def gcal_events_instances(calendar_id: str, event_id: str, request: Request, current_user: User = Depends(get_current_user)):
    service = _build_calendar_service_oauth(current_user.id)
    params = _query_params(request)
    return _execute_google_request(
        service.events().instances(calendarId=calendar_id, eventId=event_id, **params),
        "Failed to list event instances",
    )


@router.post("/gcal/calendars/{calendar_id}/events/{event_id}/move")
def gcal_events_move(calendar_id: str, event_id: str, request: Request, current_user: User = Depends(get_current_user)):
    service = _build_calendar_service_oauth(current_user.id)
    params = _query_params(request)
    if "destination" not in params:
        raise HTTPException(status_code=400, detail="destination query param is required")
    return _execute_google_request(
        service.events().move(calendarId=calendar_id, eventId=event_id, **params),
        "Failed to move event",
    )


@router.post("/gcal/calendars/{calendar_id}/events/import")
def gcal_events_import(calendar_id: str, payload: dict, request: Request, current_user: User = Depends(get_current_user)):
    if not payload:
        raise HTTPException(status_code=400, detail="Event import body is required")
    service = _build_calendar_service_oauth(current_user.id)
    params = _query_params(request)
    return _execute_google_request(
        service.events().import_(calendarId=calendar_id, body=payload, **params),
        "Failed to import event",
    )


@router.post("/gcal/calendars/{calendar_id}/events/quickAdd")
def gcal_events_quick_add(calendar_id: str, request: Request, current_user: User = Depends(get_current_user)):
    service = _build_calendar_service_oauth(current_user.id)
    params = _query_params(request)
    if "text" not in params:
        raise HTTPException(status_code=400, detail="text query param is required")
    return _execute_google_request(
        service.events().quickAdd(calendarId=calendar_id, **params),
        "Failed to quick add event",
    )


@router.post("/gcal/calendars/{calendar_id}/events/watch")
def gcal_events_watch(calendar_id: str, payload: dict, current_user: User = Depends(get_current_user)):
    if not payload:
        raise HTTPException(status_code=400, detail="Watch body is required")
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(
        service.events().watch(calendarId=calendar_id, body=payload),
        "Failed to watch events",
    )


# Freebusy
@router.post("/gcal/freeBusy")
def gcal_freebusy(payload: dict, current_user: User = Depends(get_current_user)):
    if not payload:
        raise HTTPException(status_code=400, detail="Freebusy body is required")
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(service.freebusy().query(body=payload), "Failed to query freebusy")


# Settings
@router.get("/gcal/users/me/settings")
def gcal_settings_list(request: Request, current_user: User = Depends(get_current_user)):
    service = _build_calendar_service_oauth(current_user.id)
    params = _query_params(request)
    return _execute_google_request(
        service.settings().list(**params),
        "Failed to list settings",
    )


@router.get("/gcal/users/me/settings/{setting_id}")
def gcal_settings_get(setting_id: str, current_user: User = Depends(get_current_user)):
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(
        service.settings().get(setting=setting_id),
        "Failed to fetch setting",
    )


@router.post("/gcal/users/me/settings/watch")
def gcal_settings_watch(payload: dict, current_user: User = Depends(get_current_user)):
    if not payload:
        raise HTTPException(status_code=400, detail="Watch body is required")
    service = _build_calendar_service_oauth(current_user.id)
    return _execute_google_request(
        service.settings().watch(body=payload),
        "Failed to watch settings",
    )
