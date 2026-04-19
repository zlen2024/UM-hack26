import base64
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Email, User

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from routes.google_calendar import _get_oauth_credentials

router = APIRouter()


def _build_gmail_service(user: User):
    """Build Gmail service for a user using their stored tokens"""
    if not user.google_refresh_token:
        raise HTTPException(status_code=400, detail="Gmail not connected")
    
    oauth_config = _get_oauth_credentials()
    if not oauth_config:
        raise HTTPException(status_code=400, detail="OAuth not configured")
    
    config = oauth_config.get("web") or oauth_config.get("installed")
    creds = Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri=config.get("token_uri"),
        client_id=config.get("client_id"),
        client_secret=config.get("client_secret")
    )
    
    service = build('gmail', 'v1', credentials=creds)
    return service


@router.get("")
def list_emails(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
):
    """List user's stored emails"""
    if not current_user.google_refresh_token:
        raise HTTPException(status_code=400, detail="Gmail not connected. Please connect Gmail in Settings.")
    
    query = db.query(Email).filter(Email.user_id == current_user.id)
    
    if unread_only:
        query = query.filter(Email.is_read == False)
    
    emails = query.order_by(Email.received_at.desc()).limit(limit).all()
    
    return [
        {
            "id": e.id,
            "gmail_id": e.gmail_id,
            "subject": e.subject,
            "from": e.from_email,
            "snippet": e.snippet,
            "is_read": e.is_read,
            "received_at": e.received_at.isoformat() if e.received_at else None,
        }
        for e in emails
    ]


@router.get("/{email_id}")
def get_email(
    email_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get single email detail"""
    email = db.query(Email).filter(
        Email.id == email_id,
        Email.user_id == current_user.id
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    return {
        "id": email.id,
        "gmail_id": email.gmail_id,
        "thread_id": email.thread_id,
        "subject": email.subject,
        "from": email.from_email,
        "to": email.to_email,
        "snippet": email.snippet,
        "body": email.body,
        "html_body": email.html_body,
        "label_ids": email.label_ids,
        "is_read": email.is_read,
        "received_at": email.received_at.isoformat() if email.received_at else None,
    }


@router.post("/{email_id}/read")
def mark_as_read(
    email_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark email as read"""
    email = db.query(Email).filter(
        Email.id == email_id,
        Email.user_id == current_user.id
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    email.is_read = True
    db.commit()
    
    return {"status": "updated", "id": email_id}


@router.post("/sync")
def sync_emails(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sync emails from Gmail API"""
    if not current_user.google_refresh_token:
        raise HTTPException(status_code=400, detail="Gmail not connected")
    
    try:
        service = _build_gmail_service(current_user)
        
        results = service.users().messages().list(
            userId='me',
            maxResults=50,
            labelIds=['INBOX'],
        ).execute()
        
        messages = results.get('messages', [])
        new_emails = 0
        
        for msg_meta in messages:
            msg_id = msg_meta['id']
            
            existing = db.query(Email).filter(
                Email.gmail_id == msg_id,
                Email.user_id == current_user.id
            ).first()
            
            if existing:
                continue
            
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
            history_id = msg.get('historyId', '')
            
            body = ''
            html_body = ''
            
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain' and 'data' in part.get('body', {}):
                        body = base64.b64decode(part['body']['data']).decode('utf-8', errors='replace')
                    elif part.get('mimeType') == 'text/html' and 'data' in part.get('body', {}):
                        html_body = base64.b64decode(part['body']['data']).decode('utf-8', errors='replace')
            
            if not body and 'body' in payload and 'data' in payload['body']:
                body = base64.b64decode(payload['body']['data']).decode('utf-8', errors='replace')
            
            try:
                internal_date = int(msg.get('internalDate', 0)) / 1000
                received_at = datetime.fromtimestamp(internal_date)
            except:
                received_at = datetime.utcnow()
            
            email_record = Email(
                user_id=current_user.id,
                gmail_id=msg_id,
                thread_id=thread_id,
                subject=subject,
                from_email=from_email,
                to_email=to_email,
                snippet=snippet[:500] if snippet else '',
                body=body[:50000] if body else '',
                html_body=html_body[:50000] if html_body else '',
                label_ids=label_ids,
                history_id=history_id,
                is_read='UNREAD' not in label_ids,
                received_at=received_at,
            )
            db.add(email_record)
            new_emails += 1
        
        db.commit()
        
        return {
            "status": "synced",
            "new_emails": new_emails,
            "total": len(messages)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")