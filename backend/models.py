from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Numeric,
    ForeignKey,
    Date,
    Boolean,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    full_name = Column(String)
    role = Column(String, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Google API fields
    google_email = Column(String, nullable=True)
    google_access_token = Column(String, nullable=True)
    google_refresh_token = Column(String, nullable=True)

    # Google API fields
    google_email = Column(String, nullable=True)
    google_access_token = Column(String, nullable=True)
    google_refresh_token = Column(String, nullable=True)

    # Google API fields
    google_email = Column(String, nullable=True)
    google_access_token = Column(String, nullable=True)
    google_refresh_token = Column(String, nullable=True)

    # Google API fields
    google_email = Column(String, nullable=True)
    google_access_token = Column(String, nullable=True)
    google_refresh_token = Column(String, nullable=True)

    # Google API fields
    google_email = Column(String, nullable=True)
    google_access_token = Column(String, nullable=True)
    google_refresh_token = Column(String, nullable=True)

    contacts = relationship(
        "Contact", back_populates="owner", foreign_keys="Contact.user_id"
    )
    opportunities = relationship(
        "Opportunity", back_populates="owner", foreign_keys="Opportunity.user_id"
    )
    tasks = relationship("Task", back_populates="owner", foreign_keys="Task.user_id")
    activities = relationship(
        "Activity", back_populates="owner", foreign_keys="Activity.user_id"
    )
    emails = relationship("Email", back_populates="owner")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    company = Column(String)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Google API fields
    google_email = Column(String, nullable=True)
    google_access_token = Column(String, nullable=True)
    google_refresh_token = Column(String, nullable=True)

    owner = relationship("User", back_populates="contacts")
    opportunities = relationship("Opportunity", back_populates="contact")
    tasks = relationship("Task", back_populates="contact")
    activities = relationship("Activity", back_populates="contact")


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    value = Column(Numeric(10, 2))
    stage = Column(String, default="lead")
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    expected_close_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Google API fields
    google_email = Column(String, nullable=True)
    google_access_token = Column(String, nullable=True)
    google_refresh_token = Column(String, nullable=True)

    owner = relationship("User", back_populates="opportunities", foreign_keys=[user_id])
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    contact = relationship("Contact", back_populates="opportunities")
    tasks = relationship("Task", back_populates="opportunity")
    activities = relationship("Activity", back_populates="opportunity")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    description = Column(Text, nullable=True)
    status = Column(String, default="pending")
    priority = Column(String, default="medium")
    due_date = Column(DateTime, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Google API fields
    google_email = Column(String, nullable=True)
    google_access_token = Column(String, nullable=True)
    google_refresh_token = Column(String, nullable=True)

    owner = relationship("User", back_populates="tasks", foreign_keys=[user_id])
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    contact = relationship("Contact", back_populates="tasks")
    opportunity = relationship("Opportunity", back_populates="tasks")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String)
    description = Column(Text, nullable=True)
    source = Column(String, nullable=True)
    external_id = Column(String, nullable=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="activities", foreign_keys=[user_id])
    contact = relationship("Contact", back_populates="activities")
    opportunity = relationship("Opportunity", back_populates="activities")


class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    gmail_id = Column(String, unique=True, index=True)
    thread_id = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    from_email = Column(String)
    to_email = Column(String)
    snippet = Column(Text, nullable=True)
    body = Column(Text, nullable=True)
    html_body = Column(Text, nullable=True)
    label_ids = Column(String, nullable=True)
    history_id = Column(String)
    is_read = Column(Boolean, default=False)
    received_at = Column(DateTime, nullable=True)
    stored_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="emails")
