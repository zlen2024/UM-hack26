from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class ContactBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None


class ContactResponse(ContactBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OpportunityBase(BaseModel):
    title: str
    value: Decimal
    stage: str = "lead"
    contact_id: Optional[int] = None
    assigned_to: Optional[int] = None
    expected_close_date: Optional[date] = None


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(BaseModel):
    title: Optional[str] = None
    value: Optional[Decimal] = None
    stage: Optional[str] = None
    contact_id: Optional[int] = None
    assigned_to: Optional[int] = None
    expected_close_date: Optional[date] = None


class OpportunityResponse(OpportunityBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "pending"
    priority: str = "medium"
    due_date: Optional[datetime] = None
    assigned_to: Optional[int] = None
    contact_id: Optional[int] = None
    opportunity_id: Optional[int] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    assigned_to: Optional[int] = None
    contact_id: Optional[int] = None
    opportunity_id: Optional[int] = None


class TaskResponse(TaskBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ActivityBase(BaseModel):
    type: str
    description: Optional[str] = None
    contact_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    type: Optional[str] = None
    description: Optional[str] = None
    contact_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None


class ActivityResponse(ActivityBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PipelineReport(BaseModel):
    stage: str
    count: int
    total_value: Decimal


class ContactActivityReport(BaseModel):
    contact_id: int
    contact_name: str
    activity_count: int
    last_activity: Optional[datetime]


class DashboardMetrics(BaseModel):
    total_contacts: int
    total_opportunities: int
    total_tasks: int
    open_tasks: int
    pipeline_value: Decimal
    won_value: Decimal
    leads_count: int
    qualified_count: int
    proposal_count: int


class GoogleCalendarCredentials(BaseModel):
    oauth_credentials: Optional[dict] = None
    test_email: Optional[EmailStr] = None
    api_key: Optional[str] = None


class GoogleCalendarEventBase(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    attendees: Optional[List[EmailStr]] = None
    contact_id: Optional[int] = None
    opportunity_id: Optional[int] = None


class GoogleCalendarEventCreate(GoogleCalendarEventBase):
    pass


class GoogleCalendarEventUpdate(BaseModel):
    title: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    description: Optional[str] = None
    attendees: Optional[List[EmailStr]] = None
    contact_id: Optional[int] = None
    opportunity_id: Optional[int] = None


class GoogleCalendarEventResponse(GoogleCalendarEventBase):
    id: str
