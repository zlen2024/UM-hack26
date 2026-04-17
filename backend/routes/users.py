from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import User
from schemas import UserResponse
from auth import get_current_user

router = APIRouter()


@router.get("", response_model=List[UserResponse])
def get_users(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return db.query(User).filter(User.id != current_user.id).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    return user
