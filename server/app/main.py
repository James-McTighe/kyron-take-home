from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from .database import engine, Base, get_db
from .models import Provider, Template
from .api import auth, encounters  # <-- Import your new API modules

app = FastAPI(
    title="AI Clinical Scribe Platform API",
    version="1.0.0",
    description="Production-ready backbone for clinical transcript processing."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

@app.on_event("startup")
def seed_demo_accounts_and_templates():
    """Seeds required authentication users and base clinical prompt guidelines[cite: 12, 137]."""
    db = SessionLocal() if 'SessionLocal' in globals() else None
    if not db:
        from .database import SessionLocal
        db = SessionLocal()
        
    try:
        # User account seeding [cite: 12]
        demo_accounts = [
            {"email": "dr.smith@scribe.com", "password_hash": "securepass123", "role": "Provider"},
            {"email": "dr.jones@scribe.com", "password_hash": "securepass123", "role": "Provider"},
            {"email": "dr.lee@scribe.com", "password_hash": "securepass123", "role": "Provider"},
            {"email": "admin.root@scribe.com", "password_hash": "adminmaster99", "role": "Admin"},
        ]
        for account in demo_accounts:
            exists = db.query(Provider).filter(Provider.email == account["email"]).first()
            if not exists:
                db.add(Provider(email=account["email"], password_hash=account["password_hash"], role=account["role"]))
        
        # Base clinical template seeding 
        default_template = db.query(Template).filter(Template.name == "Standard SOAP Note Evaluation").first()
        if not default_template:
            db.add(Template(
                name="Standard SOAP Note Evaluation",
                system_prompt="Extract and transform clinical observations into high-density Subjective, Objective, Assessment, and Plan structures.",
                is_active=True
            ))
            
        db.commit()
    except Exception as e:
        print(f"Error executing database auto-seeding: {e}")
        db.rollback()
    finally:
        db.close()

# Mount your route groups [cite: 59]
app.include_router(auth.router)
app.include_router(encounters.router)

@app.get("/healthz", tags=["Infrastructure"])
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected and pooled"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
