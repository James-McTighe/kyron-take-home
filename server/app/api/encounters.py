import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Encounter, EncounterVersion, Patient, Template
from ..schemas import EncounterCreate, DraftSaveRequest, EncounterResponse
from .auth import get_current_provider, TokenData

router = APIRouter(prefix="/api/encounters", tags=["Encounters Workspace"])

@router.post("/start", response_model=EncounterResponse)
def start_encounter(payload: EncounterCreate, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_provider)):
    """Registers patient metrics and links an open encounter context to the provider."""
    # Check if patient exists to satisfy the historical recurrence matching rule [cite: 150, 222]
    patient = db.query(Patient).filter(
        Patient.first_name == payload.patient.first_name,
        Patient.last_name == payload.patient.last_name,
        Patient.dob == payload.patient.dob
    ).first()

    if not patient:
        patient = Patient(
            first_name=payload.patient.first_name,
            last_name=payload.patient.last_name,
            dob=payload.patient.dob
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)

    # Spawn fresh encounter baseline draft [cite: 209]
    encounter = Encounter(
        patient_id=patient.id,
        provider_id=current_user.user_id,
        current_status="Draft"
    )
    db.add(encounter)
    db.commit()
    db.refresh(encounter)
    return encounter

@router.put("/{id}/draft")
def save_debounced_draft(id: int, payload: DraftSaveRequest, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_provider)):
    """Receives quick debounced frontend auto-saves to prevent session loss[cite: 130]."""
    encounter = db.query(Encounter).filter(Encounter.id == id).first()
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter record context target not found.")
    
    # Enforce strict multi-tenant tenant constraints [cite: 59, 145]
    if encounter.provider_id != current_user.user_id and current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Unauthorized access to target patient record data.")

    # Fetch latest version number to handle incremental version updates [cite: 129]
    latest_version = db.query(EncounterVersion).filter(EncounterVersion.encounter_id == id)\
                       .order_by(EncounterVersion.version_number.desc()).first()
    next_ver = (latest_version.version_number + 1) if latest_version else 1

    # Write append-only version record rather than overwriting text [cite: 128, 129]
    new_version = EncounterVersion(
        encounter_id=id,
        version_number=next_ver,
        transcript_snapshot=payload.transcript_snapshot,
        soap_note_json=payload.soap_note_json,
        saved_by_provider_id=current_user.user_id
    )
    db.add(new_version)
    db.commit()
    return {"status": "Draft successfully saved", "version": next_ver}

@router.post("/{id}/generate")
async def generate_soap_note_stream(id: int, template_id: int, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_provider)):
    """Orchestrates historical injection and routes real-time tokens down an SSE channel[cite: 122, 125, 213]."""
    encounter = db.query(Encounter).filter(Encounter.id == id).first()
    if not encounter or encounter.provider_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Unauthorized execution context.")

    # Fetch latest draft content to extract transcript text
    latest_draft = db.query(EncounterVersion).filter(EncounterVersion.encounter_id == id)\
                     .order_by(EncounterVersion.version_number.desc()).first()
    transcript = latest_draft.transcript_snapshot if latest_draft else ""
    
    if not transcript or len(transcript.strip()) < 5:
        raise HTTPException(status_code=400, detail="Insufficient clinical data provided to process a note.")

    # 1. Grab Admin Template Live [cite: 138, 164, 220]
    template = db.query(Template).filter(Template.id == template_id, Template.is_active == True).first()
    system_instruction = template.system_prompt if template else "You are an expert clinical scribe. Generate a professional SOAP note."

    # 2. Historical Context Injection 
    prior_encounters = db.query(EncounterVersion).join(Encounter).filter(
        Encounter.patient_id == encounter.patient_id,
        Encounter.current_status == "Finalized"
    ).order_by(EncounterVersion.created_at.desc()).limit(3).all()

    historical_context = ""
    if prior_encounters:
        historical_context = "\n[CRITICAL RETROSPECTIVE CONTEXT - PRIOR CLINICAL ENCOUNTERS]:\n"
        for idx, past_note in enumerate(prior_encounters):
            historical_context += f"Past Visit {idx+1} Note JSON: {json.dumps(past_note.soap_note_json)}\n"

    final_system_prompt = f"{system_instruction}\n{historical_context}"

    # Asynchronous generator mock simulating an active LLM chunk streaming client connection (OpenAI stream=True) [cite: 123, 124, 216]
    async def fake_llm_stream_generator():
        # Simulated payload breakdown mapping expected structure
        response_segments = [
            "\n[SUBJECTIVE]\nPatient presents reporting localized discomfort.",
            "\n[OBJECTIVE]\nVital parameters present within expected baseline.",
            "\n[ASSESSMENT]\nPrimary observation tracks clinical indicators.",
            "\n[ICD-10 SUGGESTION]\nM54.5 - Low back pain",
            "\n[PLAN]\nSchedule follow-up evaluation in 14 days."
        ]
        for segment in response_segments:
            for word in segment.split(" "):
                # SSE formatting requires strict prefix structure: 'data: {content}\n\n' [cite: 124, 217]
                yield f"data: {json.dumps({'token': word + ' '})}\n\n"
                await asyncio.sleep(0.08)  # Matches progressive human typing speeds
        yield "data: [DONE]\n\n"

    return StreamingResponse(fake_llm_stream_generator(), media_type="text/event-stream")
