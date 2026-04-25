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

# Realistic CRM Data
FIRST_NAMES = ["John", "Sarah", "Michael", "Emily", "David", "Jennifer", "Robert", "Lisa", "James", "Amanda",
               "William", "Maria", "Richard", "Jessica", "Joseph", "Karen", "Thomas", "Nancy", "Charles", "Angela",
               "Daniel", "Melissa", "Matthew", "Donna", "Mark", "Carol", "Donald", "Margaret", "Steven", "Ashley"]

LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
              "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"]

COMPANY_NAMES = ["TechCorp Solutions", "Digital Innovations Inc.", "CloudBase Systems", "DataFlow Analytics",
                 "NetSecure Technologies", "GreenEnergy Systems", "FinTech Ventures", "MediCare Solutions",
                 "LogiShip Logistics", "ConsultPro Services", "RetailHub Global", "ManufactureTech Industries",
                 "EduTech Platforms", "RealEstate Direct", "HealthPlus Clinic", "AutoDrive Motors",
                 "FoodChain Distributors", "AirTravel Services", "ConstructBuild Corp", "DesignStudio Creative"]

JOB_TITLES = ["CEO", "CTO", "VP Sales", "VP Marketing", "Sales Manager", "Operations Manager", "Project Manager",
              "Business Development Manager", "Account Executive", "Solutions Architect", "Business Analyst",
              "Product Manager", "Procurement Manager", "IT Director", "CFO"]

ACTIVITY_DESCRIPTIONS = [
    "Discussed pricing and contract terms",
    "Presented product demo and ROI analysis",
    "Reviewed technical requirements and architecture",
    "Negotiated SLA terms and support packages",
    "Introduced to procurement team for budget approval",
    "Addressed concerns about integration with existing systems",
    "Scheduled follow-up meeting for stakeholder alignment",
    "Reviewed competitor analysis and competitive advantages",
    "Discussed implementation timeline and resource allocation",
    "Provided case studies from similar industry implementations",
    "Clarified licensing and renewal options",
    "Introduced to legal team for contract review",
    "Conducted needs assessment workshop",
    "Provided training overview for their team",
    "Finalized pricing proposal and quote"
]

TASK_DESCRIPTIONS = [
    "Follow up on proposal from last meeting",
    "Prepare technical documentation",
    "Schedule demo with key stakeholders",
    "Send contract for review",
    "Get CFO approval on budget",
    "Coordinate with implementation team",
    "Prepare ROI analysis and business case",
    "Update stakeholder on project status",
    "Prepare final presentation for executive approval",
    "Arrange training session for users"
]

OPPORTUNITY_TITLES = [
    "Cloud Migration Project",
    "Digital Transformation Initiative",
    "ERP System Implementation",
    "CRM Software License",
    "Data Analytics Platform",
    "Cybersecurity Solutions",
    "Marketing Automation Platform",
    "Business Intelligence Suite",
    "Supply Chain Optimization",
    "Customer Portal Development",
    "Mobile App Development",
    "IT Infrastructure Upgrade",
    "Managed IT Services Contract",
    "SaaS Subscription Bundle",
    "Process Automation Initiative"
]



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
        for i in range(contacts_count):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            company = random.choice(COMPANY_NAMES)
            # Clean company name for email: remove spaces and periods
            company_email = company.lower().replace(' ', '').replace('.', '')
            contact = Contact(
                user_id=user.id,
                name=f"{first_name} {last_name}",
                email=f"{first_name.lower()}.{last_name.lower()}@{company_email}.com",
                phone=f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
                company=company,
                notes=f"{random.choice(JOB_TITLES)} at {company}. Interested in optimizing operations.",
            )
            db.add(contact)
            contacts.append(contact)
        db.commit()
        for contact in contacts:
            db.refresh(contact)

        opportunities = []
        for i in range(opportunities_count):
            stage = random.choice(STAGES)
            # More realistic deal values: $10k-$500k
            value = Decimal(random.randint(10, 500) * 1000)
            contact = random.choice(contacts)
            opportunity = Opportunity(
                user_id=user.id,
                title=random.choice(OPPORTUNITY_TITLES),
                value=value,
                stage=stage,
                contact_id=contact.id,
                expected_close_date=date.today() + timedelta(days=random.randint(7, 180)),
            )
            db.add(opportunity)
            opportunities.append(opportunity)
        db.commit()
        for opportunity in opportunities:
            db.refresh(opportunity)

        tasks = []
        for i in range(tasks_count):
            task = Task(
                user_id=user.id,
                title=random.choice(TASK_DESCRIPTIONS),
                description=random.choice(TASK_DESCRIPTIONS) + " - " + ("High urgency" if random.random() > 0.7 else "Standard"),
                status=random.choice(TASK_STATUSES),
                priority=random.choice(TASK_PRIORITIES),
                due_date=datetime.now(timezone.utc) + timedelta(days=random.randint(1, 30)),
                contact_id=random.choice(contacts).id if contacts else None,
                opportunity_id=random.choice(opportunities).id if opportunities else None,
            )
            db.add(task)
            tasks.append(task)
        db.commit()
        for task in tasks:
            db.refresh(task)

        for i in range(activities_count):
            activity = Activity(
                user_id=user.id,
                type=random.choice(ACTIVITY_TYPES),
                description=random.choice(ACTIVITY_DESCRIPTIONS),
                contact_id=random.choice(contacts).id if contacts else None,
                opportunity_id=random.choice(opportunities).id if opportunities else None,
                scheduled_at=datetime.now(timezone.utc) + timedelta(days=random.randint(-10, 15)),
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
