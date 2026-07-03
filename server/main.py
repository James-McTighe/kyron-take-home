from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

import models
from database import engine, get_db

# Initialize database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Clinical Scribe Platform Backend")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Automated Seeding function for Day 1 Demo verification
def seed_demo_accounts(db: Session):
    # Check if we already seeded accounts
    if db.query(models.Provider).count() == 0:
        print("🌱 Seeding hardcoded demo accounts...")
        demo_accounts = [
            {"email": "provider1@clinic.com", "role": "Provider"},
            {"email": "provider2@clinic.com", "role": "Provider"},
            {"email": "provider3@clinic.com", "role": "Provider"},
            {"email": "admin@clinic.com", "role": "Admin"},
        ]
        for acc in demo_accounts:
            # Simple uniform test password: 'password123'
            hashed_pw = pwd_context.hash("password123")
            db.add(models.Provider(
                email=acc["email"],
                password_hash=hashed_pw,
                role=acc["role"],
                is_active=True
            ))
        db.commit()
        print("Seeding complete. Use password 'password123' for all accounts.")

# Run seeding on application start
@app.on_event("startup")
def on_startup():
    db = next(get_db())
    seed_demo_accounts(db)

@app.get("/")
def health_check():
    return {"status": "healthy", "message": "Backend engine and connection pooling are live."}
