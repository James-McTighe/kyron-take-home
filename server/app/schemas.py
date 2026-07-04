from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict
from datetime import datetime

# --- Authentication Schemas ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None

# --- Patient Schemas ---
class PatientCreate(BaseModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    dob: str = Field(..., description="YYYY-MM-DD format")

class PatientResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    dob: str

    class Config:
        from_attributes = True

# --- Encounter Schemas ---
class EncounterCreate(BaseModel):
    patient: PatientCreate
    transcript: str = Field(..., example="Patient presents with mild cough and fatigue...")
    template_id: Optional[int] = Field(None, example=1)

class DraftSaveRequest(BaseModel):
    transcript_snapshot: str
    soap_note_json: Optional[Dict] = None

class SOAPNoteSection(BaseModel):
    subjective: str
    objective: str
    assessment: str
    plan: str
    icd10_suggestions: List[Dict[str, str]] = []

class EncounterResponse(BaseModel):
    id: int
    patient_id: int
    provider_id: int
    current_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Template Schemas ---
class TemplateCreate(BaseModel):
    name: str
    system_prompt: str

class TemplateResponse(BaseModel):
    id: int
    name: str
    system_prompt: str
    is_active: bool

    class Config:
        from_attributes = True
