#!/usr/bin/env python3
import sys
sys.path.insert(0, '/app/backend')

from database import SessionLocal
from models import Activity

db = SessionLocal()
activities = db.query(Activity).filter(Activity.source == 'google_calendar').all()
print(f'Found {len(activities)} Google Calendar Activities:')
for act in activities:
    print(f'  - ID: {act.id}')
    print(f'    Title: {act.title}')
    print(f'    External ID: {act.external_id}')
    print(f'    Source: {act.source}')
    print()
