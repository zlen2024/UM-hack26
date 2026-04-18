import argparse
from datetime import datetime, timedelta, date, timezone
from decimal import Decimal
import random

from sqlalchemy.orm import Session

from database import SessionLocal, Base, engine
from models import User, Contact, Opportunity, Task, Activity
from auth import get_password_hash

STAGES = ["lead", "qualified", "proposal", "won", "lost"]
TASK_STATUSES = ["pending", "in_progress", "completed"]
TASK_PRIORITIES = ["low", "medium", "high"]
ACTIVITY_TYPES = ["call", "email", "meeting", "demo"]


def reset_user_data(db: Session, user: User, delete_user: bool = True) -> None:
    db.query(Activity).filter(Activity.user_id == user.id).delete(
        synchronize_session=False
    )
    db.query(Task).filter(Task.user_id == user.id).delete(
        synchronize_session=False
    )
    db.query(Opportunity).filter(Opportunity.user_id == user.id).delete(
        synchronize_session=False
    )
    db.query(Contact).filter(Contact.user_id == user.id).delete(
        synchronize_session=False
    )
    if delete_user:
        db.delete(user)
    db.commit()


def reset_all_data(db: Session) -> None:
    db.query(Activity).delete(synchronize_session=False)
    db.query(Task).delete(synchronize_session=False)
    db.query(Opportunity).delete(synchronize_session=False)
    db.query(Contact).delete(synchronize_session=False)
    db.query(User).delete(synchronize_session=False)
    db.commit()


def delete_users_by_email(db: Session, email: str) -> None:
    users = db.query(User).filter(User.email == email).all()
    for user in users:
        reset_user_data(db, user, delete_user=True)


def seed_demo_data(
    email: str,
    password: str,
    force: bool,
    contacts_count: int,
    opportunities_count: int,
    tasks_count: int,
    activities_count: int,
    reset_user: bool,
    drop_all: bool = False,
    reset_all: bool = False,
) -> None:
    if drop_all:
        Base.metadata.drop_all(bind=engine)
        print("Dropped all tables")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if reset_all:
            reset_all_data(db)
            print("Cleared all data")

        if reset_user or force:
            delete_users_by_email(db, email)

        user = db.query(User).filter(User.email == email).first()
        if user is None:
            user = User(
                email=email,
                password_hash=get_password_hash(password),
                full_name="Demo User",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user.password_hash = get_password_hash(password)
            if not user.full_name:
                user.full_name = "Demo User"
            db.commit()
            db.refresh(user)

        existing_contacts = db.query(Contact).filter(Contact.user_id == user.id).count()
        existing_opps = db.query(Opportunity).filter(Opportunity.user_id == user.id).count()
        existing_tasks = db.query(Task).filter(Task.user_id == user.id).count()
        existing_activities = (
            db.query(Activity).filter(Activity.user_id == user.id).count()
        )

        if not force and (existing_contacts + existing_opps + existing_tasks + existing_activities) > 0:
            print("Demo data already exists for this user. Use --force to overwrite.")
            return

        contacts = []
        for i in range(1, contacts_count + 1):
            contact = Contact(
                user_id=user.id,
                name=f"Contact {i}",
                email=f"contact{i}@example.com",
                phone=f"555-01{i:02d}",
                company=f"Company {i}",
                notes="Seeded demo contact",
            )
            db.add(contact)
            contacts.append(contact)
        db.commit()
        for contact in contacts:
            db.refresh(contact)

        opportunities = []
        for i in range(1, opportunities_count + 1):
            stage = random.choice(STAGES)
            value = Decimal(random.randint(5_000, 45_000))
            contact = random.choice(contacts)
            opportunity = Opportunity(
                user_id=user.id,
                title=f"Opportunity {i}",
                value=value,
                stage=stage,
                contact_id=contact.id,
                expected_close_date=date.today() + timedelta(days=random.randint(7, 120)),
            )
            db.add(opportunity)
            opportunities.append(opportunity)
        db.commit()
        for opportunity in opportunities:
            db.refresh(opportunity)

        tasks = []
        for i in range(1, tasks_count + 1):
            task = Task(
                user_id=user.id,
                title=f"Task {i}",
                description="Seeded demo task",
                status=random.choice(TASK_STATUSES),
                priority=random.choice(TASK_PRIORITIES),
                due_date=datetime.now(timezone.utc)
                + timedelta(days=random.randint(1, 21)),
                contact_id=random.choice(contacts).id,
                opportunity_id=random.choice(opportunities).id,
            )
            db.add(task)
            tasks.append(task)
        db.commit()
        for task in tasks:
            db.refresh(task)

        for i in range(1, activities_count + 1):
            activity = Activity(
                user_id=user.id,
                type=random.choice(ACTIVITY_TYPES),
                description="Seeded demo activity",
                contact_id=random.choice(contacts).id,
                opportunity_id=random.choice(opportunities).id,
                scheduled_at=datetime.now(timezone.utc)
                + timedelta(days=random.randint(-5, 10)),
            )
            db.add(activity)
        db.commit()

        print(
            f"Seeded demo data for {email}: "
            f"{len(contacts)} contacts, {len(opportunities)} opportunities, "
            f"{len(tasks)} tasks, {activities_count} activities."
        )
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed demo data for UM CRM")
    parser.add_argument("--email", default="demo@example.com", help="User email")
    parser.add_argument("--password", default="Passw0rd!", help="User password")
    parser.add_argument("--contacts", type=int, default=100, help="Number of contacts")
    parser.add_argument("--opportunities", type=int, default=140, help="Number of opportunities")
    parser.add_argument("--tasks", type=int, default=180, help="Number of tasks")
    parser.add_argument("--activities", type=int, default=200, help="Number of activities")
    parser.add_argument(
        "--reset-user",
        action="store_true",
        help="Delete all data for this email before seeding",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite data for this email and reseed",
    )
    parser.add_argument(
        "--drop-all",
        action="store_true",
        help="Drop all tables and recreate from scratch",
    )
    parser.add_argument(
        "--reset-all",
        action="store_true",
        help="Delete all data across all users before seeding",
    )
    args = parser.parse_args()
    seed_demo_data(
        args.email,
        args.password,
        args.force,
        args.contacts,
        args.opportunities,
        args.tasks,
        args.activities,
        args.reset_user,
        args.drop_all,
        args.reset_all,
    )
