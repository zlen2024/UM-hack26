from datetime import datetime, timedelta
import random
from decimal import Decimal

from database import SessionLocal, engine, Base
from models import User, Contact, Opportunity, Task, Activity
from auth import get_password_hash

Base.metadata.create_all(bind=engine)

db = SessionLocal()

email = "demo@example.com"
existing_user = db.query(User).filter(User.email == email).first()

if existing_user:
    print("Demo user already exists!")
    db.close()
    exit()

user = User(
    email=email,
    password_hash=get_password_hash("demo123"),
    full_name="Demo User",
    role="user"
)
db.add(user)
db.commit()
db.refresh(user)
print(f"Created user: {user.email}")

contacts_data = [
    {"name": "John Smith", "email": "john@acme.com", "phone": "555-0101", "company": "Acme Corp"},
    {"name": "Sarah Johnson", "email": "sarah@tech.co", "phone": "555-0102", "company": "Tech Inc"},
    {"name": "Michael Brown", "email": "michael@global.com", "phone": "555-0103", "company": "Global Ltd"},
    {"name": "Emily Davis", "email": "emily@startup.io", "phone": "555-0104", "company": "Startup Co"},
    {"name": "David Wilson", "email": "david@enterprise.com", "phone": "555-0105", "company": "Enterprise Inc"},
    {"name": "Lisa Anderson", "email": "lisa@solutions.com", "phone": "555-0106", "company": "Solutions LLC"},
    {"name": "James Taylor", "email": "james@digital.co", "phone": "555-0107", "company": "Digital Tech"},
    {"name": "Jennifer Martinez", "email": "jennifer@innovate.com", "phone": "555-0108", "company": "Innovate Inc"},
]

contacts = []
for c in contacts_data:
    contact = Contact(
        user_id=user.id,
        name=c["name"],
        email=c["email"],
        phone=c["phone"],
        company=c["company"],
        notes=f"VIP client from {c['company']}"
    )
    db.add(contact)
    contacts.append(contact)

db.commit()
for c in contacts:
    db.refresh(c)
print(f"Created {len(contacts)} contacts")

opportunities_data = [
    {"title": "Acme Enterprise License", "value": 50000, "stage": "won"},
    {"title": "Tech Platform Integration", "value": 35000, "stage": "proposal"},
    {"title": "Global Marketing Campaign", "value": 25000, "stage": "qualified"},
    {"title": "Startup MVP Development", "value": 15000, "stage": "lead"},
    {"title": "Enterprise Security Audit", "value": 45000, "stage": "proposal"},
    {"title": "Solutions Cloud Migration", "value": 60000, "stage": "qualified"},
    {"title": "Digital Transformation", "value": 80000, "stage": "lead"},
    {"title": "Innovation Workshop", "value": 12000, "stage": "won"},
]

for i, o in enumerate(opportunities_data):
    if i < len(contacts):
        contact_id = contacts[i].id
    else:
        contact_id = None
    
    opp = Opportunity(
        user_id=user.id,
        title=o["title"],
        value=Decimal(str(o["value"])),
        stage=o["stage"],
        contact_id=contact_id,
        expected_close_date=datetime.now().date() + timedelta(days=random.randint(30, 90))
    )
    db.add(opp)

db.commit()
print(f"Created {len(opportunities_data)} opportunities")

task_data = [
    {"title": "Follow up with John", "description": "Discuss contract details", "status": "completed", "priority": "high"},
    {"title": "Prepare proposal for Tech Inc", "description": "Include all features from discussion", "status": "in_progress", "priority": "high"},
    {"title": "Send pricing to Michael", "description": "Final quote for approval", "status": "pending", "priority": "medium"},
    {"title": "Schedule demo with Emily", "description": "Show platform features", "status": "pending", "priority": "medium"},
    {"title": "Review contract terms", "description": "Legal review needed", "status": "pending", "priority": "high"},
    {"title": "Update CRM documentation", "description": "Add new client workflows", "status": "completed", "priority": "low"},
    {"title": "Call with Jennifer", "description": "Weekly check-in call", "status": "in_progress", "priority": "medium"},
    {"title": "Prepare invoice", "description": "For completed project", "status": "pending", "priority": "high"},
]

for i, t in enumerate(task_data):
    if i < len(contacts):
        contact_id = contacts[i].id
    else:
        contact_id = None
    
    task = Task(
        user_id=user.id,
        title=t["title"],
        description=t["description"],
        status=t["status"],
        priority=t["priority"],
        due_date=datetime.now() + timedelta(days=random.randint(-5, 14)),
        contact_id=contact_id
    )
    db.add(task)

db.commit()
print(f"Created {len(task_data)} tasks")

activity_types = ["call", "email", "meeting", "note"]
for i, c in enumerate(contacts[:5]):
    activity = Activity(
        user_id=user.id,
        type=random.choice(activity_types),
        description=f"Discussed {c.company} partnership opportunities",
        contact_id=c.id,
        scheduled_at=datetime.now() - timedelta(days=random.randint(1, 7))
    )
    db.add(activity)

db.commit()
print("Created activities")

db.close()
print("\nDemo data injected successfully!")
print("Login with: demo@example.com / demo123")