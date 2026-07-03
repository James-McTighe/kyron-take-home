from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from .database import engine, Base, get_db
from .models import Provider

app = FastAPI(
    title="AI Clinical Scribe Platform API",
    version="1.0.0",
    description="Production-ready backbone for clinical transcript processing."
)

# Enable CORS for local cross-port interaction before moving behind Nginx
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Automatically bind metadata to establish structural tables on application startup
Base.metadata.create_all(bind=engine)

@app.on_event("startup")
def seed_demo_accounts():
    """Ensures at least 3 distinct Providers and 1 Admin account exist immediately."""
    db = SessionLocal() if 'SessionLocal' in globals() else None
    if not db:
        from .database import SessionLocal
        db = SessionLocal()
        
    try:
        # Simple plain-text demonstration checks (switch to passlib/bcrypt for production auth)
        demo_accounts = [
            {"email": "dr.smith@scribe.com", "password_hash": "securepass123", "role": "Provider"},
            {"email": "dr.jones@scribe.com", "password_hash": "securepass123", "role": "Provider"},
            {"email": "dr.lee@scribe.com", "password_hash": "securepass123", "role": "Provider"},
            {"email": "admin.root@scribe.com", "password_hash": "adminmaster99", "role": "Admin"},
        ]
        
        for account in demo_accounts:
            exists = db.query(Provider).filter(Provider.email == account["email"]).first()
            if not exists:
                new_user = Provider(
                    email=account["email"],
                    password_hash=account["password_hash"],
                    role=account["role"],
                    is_active=True
                )
                db.add(new_user)
        db.commit()
    except Exception as e:
        print(f"Error executing database auto-seeding: {e}")
        db.rollback()
    finally:
        db.close()

@app.get("/healthz", tags=["Infrastructure"])
def health_check(db: Session = Depends(get_db)):
    """Verifies backend operational status and active connection pooling health."""
    try:
        # Simple evaluation query to confirm active DB socket connection
        db.execute(text( "SELECT 1" ))
        return {"status": "healthy", "database": "connected and pooled"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
