from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import IntegrationCredential, User


router = APIRouter()


class IntegrationKeyPayload(BaseModel):
    api_key: str


def _get_credential(db: Session, user_id: int, provider: str) -> Optional[IntegrationCredential]:
    return db.query(IntegrationCredential).filter(
        IntegrationCredential.user_id == user_id,
        IntegrationCredential.provider == provider,
    ).first()


def _credential_response(provider: str, credential: Optional[IntegrationCredential]) -> dict:
    if not credential:
        return {
            "provider": provider,
            "connected": False,
            "has_key": False,
            "updated_at": None,
        }

    return {
        "provider": provider,
        "connected": True,
        "has_key": True,
        "updated_at": credential.updated_at.isoformat() if credential.updated_at else None,
        "last4": credential.secret_value[-4:] if credential.secret_value else None,
    }


@router.get("/{provider}")
def get_integration_status(
    provider: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    credential = _get_credential(db, current_user.id, provider.lower())
    return _credential_response(provider.lower(), credential)


@router.put("/{provider}")
def save_integration_key(
    provider: str,
    payload: IntegrationKeyPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    provider_name = provider.lower()
    secret_value = payload.api_key.strip()

    if not secret_value:
        raise HTTPException(status_code=400, detail="API key is required")

    credential = _get_credential(db, current_user.id, provider_name)
    if credential:
        credential.secret_value = secret_value
        credential.updated_at = datetime.utcnow()
    else:
        credential = IntegrationCredential(
            user_id=current_user.id,
            provider=provider_name,
            secret_value=secret_value,
        )
        db.add(credential)

    db.commit()
    db.refresh(credential)
    return _credential_response(provider_name, credential)


@router.delete("/{provider}")
def clear_integration_key(
    provider: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    provider_name = provider.lower()
    credential = _get_credential(db, current_user.id, provider_name)

    if credential:
        db.delete(credential)
        db.commit()

    return _credential_response(provider_name, None)