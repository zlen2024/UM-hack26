from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import User
from schemas import ContactCreate, ContactUpdate, ContactResponse
from auth import get_current_user
from services import contacts as contacts_service

router = APIRouter()


@router.get("", response_model=List[ContactResponse])
def get_contacts(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return contacts_service.list_contacts(db, current_user.id, search=search)


@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = contacts_service.get_contact(db, current_user.id, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.post("", response_model=ContactResponse)
def create_contact(
    contact: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return contacts_service.create_contact(db, current_user.id, **contact.model_dump())


@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: int,
    contact: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = contacts_service.update_contact(
        db, current_user.id, contact_id, **contact.model_dump(exclude_unset=True)
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Contact not found")
    return updated


@router.delete("/{contact_id}")
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not contacts_service.delete_contact(db, current_user.id, contact_id):
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact deleted successfully"}
