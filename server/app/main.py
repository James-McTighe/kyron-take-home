from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import database, models, schemas  # Ensure correct directory imports

from .api import auth, encounters  # <-- Import your new API modules
from .database import Base, engine, get_db
from .models import Provider, Template

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

@app.post("/api/encounters", status_code=status.HTTP_201_CREATED)
def create_initial_encounter(
    payload: schemas.EncounterCreate, 
    db: Session = Depends(database.get_db)  # Uses your active connection pool
):
    try:
        # 1. Check if patient already exists or create them dynamically
        patient = db.query(models.Patient).filter(
            models.Patient.first_name == payload.patient.first_name,
            models.Patient.last_name == payload.patient.last_name,
            models.Patient.dob == payload.patient.dob
        ).first()

        if not patient:
            patient = models.Patient(
                first_name=payload.patient.first_name,
                last_name=payload.patient.last_name,
                dob=payload.patient.dob
            )
            db.add(patient)
            db.flush()  # Generates patient.id without committing yet

        # 2. Hardcode a testing provider ID for Day 1 local verification
        # (Tomorrow we swap this out for your authenticated JWT get_current_user guard!)
        fallback_provider = db.query(models.Provider).first()
        if not fallback_provider:
            raise HTTPException(status_code=500, detail="No seeded providers found.")

        # 3. Initialize the core Encounter record shell
        encounter = models.Encounter(
            patient_id=patient.id,
            provider_id=fallback_provider.id,
            current_status="Draft"
        )
        db.add(encounter)
        db.flush()  # Generates encounter.id

        # 4. Insert the initial workspace state as Version 1 
        # Keeping to your mandatory append-only history audit tracking rule
        initial_version = models.EncounterVersion(
            encounter_id=encounter.id,
            version_number=1,
            transcript_snapshot=payload.transcript,
            soap_note_json={},  # Empty dict for Day 1 since AI hasn't run yet
            saved_by_provider_id=fallback_provider.id
        )
        db.add(initial_version)
        
        # Commit the atomic transaction cleanly
        db.commit()
        
        return {
            "status": "success",
            "message": "Initial encounter entry saved successfully",
            "encounter_id": encounter.id,
            "patient_id": patient.id,
            "version": 1
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database write failure: {str(e)}")
