from database import SessionLocal
from models import BusinessRule
db = SessionLocal()
print("DB connection OK")
db.close()
