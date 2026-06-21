from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from models import Contact


def create_contact(
    db: Session,
    user_id: int,
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    company: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    db_contact = Contact(
        user_id=user_id,
        name=name,
        email=email,
        phone=phone,
        company=company,
        notes=notes,
    )
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return {
        "id": db_contact.id,
        "user_id": db_contact.user_id,
        "name": db_contact.name,
        "email": db_contact.email,
        "phone": db_contact.phone,
        "company": db_contact.company,
        "notes": db_contact.notes,
        "created_at": db_contact.created_at.isoformat(),
        "updated_at": db_contact.updated_at.isoformat(),
    }


def get_contact(db: Session, user_id: int, contact_id: int) -> Optional[Dict[str, Any]]:
    contact = (
        db.query(Contact)
        .filter(Contact.id == contact_id, Contact.user_id == user_id)
        .first()
    )
    if not contact:
        return None
    return {
        "id": contact.id,
        "user_id": contact.user_id,
        "name": contact.name,
        "email": contact.email,
        "phone": contact.phone,
        "company": contact.company,
        "notes": contact.notes,
        "created_at": contact.created_at.isoformat(),
        "updated_at": contact.updated_at.isoformat(),
    }


def list_contacts(
    db: Session, user_id: int, search: Optional[str] = None
) -> List[Dict[str, Any]]:
    query = db.query(Contact).filter(Contact.user_id == user_id)
    if search:
        query = query.filter(
            (Contact.name.contains(search))
            | (Contact.email.contains(search))
            | (Contact.company.contains(search))
        )
    contacts = query.order_by(Contact.created_at.desc()).all()
    return [
        {
            "id": c.id,
            "user_id": c.user_id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "company": c.company,
            "notes": c.notes,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
        }
        for c in contacts
    ]


def update_contact(
    db: Session,
    user_id: int,
    contact_id: int,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    company: Optional[str] = None,
    notes: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    contact = (
        db.query(Contact)
        .filter(Contact.id == contact_id, Contact.user_id == user_id)
        .first()
    )
    if not contact:
        return None

    if name is not None:
        contact.name = name
    if email is not None:
        contact.email = email
    if phone is not None:
        contact.phone = phone
    if company is not None:
        contact.company = company
    if notes is not None:
        contact.notes = notes

    db.commit()
    db.refresh(contact)
    return {
        "id": contact.id,
        "user_id": contact.user_id,
        "name": contact.name,
        "email": contact.email,
        "phone": contact.phone,
        "company": contact.company,
        "notes": contact.notes,
        "created_at": contact.created_at.isoformat(),
        "updated_at": contact.updated_at.isoformat(),
    }


def delete_contact(db: Session, user_id: int, contact_id: int) -> bool:
    contact = (
        db.query(Contact)
        .filter(Contact.id == contact_id, Contact.user_id == user_id)
        .first()
    )
    if not contact:
        return False
    db.delete(contact)
    db.commit()
    return True