import asyncio
import json
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.auth import get_current_provider
from app.database import get_db
from app.models import Encounter, EncounterVersion, Patient, Provider
from app.schemas import EncounterDraftPayload, EncounterGeneratePayload

router = APIRouter(prefix="/api/encounters", tags=["Encounters"])

@router.post("/{id}/generate")
async def generate_soap_stream(
    id: int, 
    payload: EncounterGeneratePayload, 
    db: Session = Depends(get_db),
    current_user: Provider = Depends(get_current_provider)
):
    # 1. Enforce multi-tenant authorization parameters
    encounter = db.query(Encounter).filter(Encounter.id == id).first()
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter record not found")
    if encounter.provider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to encounter record")

    # 2. Check if we should run in offline dummy mode
    api_key = os.getenv("OPENAI_API_KEY", "")
    is_dummy_mode = (api_key == "sk-test-dummy-key" or not api_key or "yourActualOpenAiSecretKeyHere" in api_key)

    async def sse_stream_generator():
        if is_dummy_mode:
            # Provide a realistic medical-grade structural text block for testing
            mock_note = (
                "### SUBJECTIVE:\n"
                "The patient presents today complaining of localized, dull, aching lower back pain "
                "that began approximately three weeks ago after lifting heavy boxes. Pain is rated a 4/10 "
                "and radiates occasionally into the left gluteal region.\n\n"
                "### OBJECTIVE:\n"
                "Vitals are stable. Lumbar spine range of motion is slightly restricted upon forward flexion. "
                "No focal neurological deficits noted in the lower extremities.\n\n"
                "### ASSESSMENT:\n"
                "1. Low back pain, acute (ICD-10: M54.50)\n"
                "2. Lumbar muscle strain\n\n"
                "### PLAN:\n"
                "Recommend physical therapy evaluation twice per week for 4 weeks. "
                "Instructed patient on proper lifting mechanics and ergonomic adjustments."
            )
            
            # Chop the text up into progressive micro-packets to mock streaming chunks
            for chunk in mock_note.split(" "):
                token = chunk + " "
                yield f"data: {json.dumps({'token': token})}\n\n"
                await asyncio.sleep(0.05)  # Mimics actual LLM processing latency!
            return

        # --- LIVE API EXECUTION (Runs if a real key is present) ---
        try:
            from openai import AsyncOpenAI
            aclient = AsyncOpenAI()
            
            # Historical Context Lookup Rule: Programmatically extract past medical timeline data
            patient = db.query(Patient).filter(Patient.id == encounter.patient_id).first()
            past_versions = (
                db.query(EncounterVersion)
                .join(Encounter)
                .filter(Encounter.patient_id == patient.id, Encounter.current_status == "Finalized")
                .order_by(EncounterVersion.created_at.desc())
                .limit(3)
                .all()
            )
            
            history_context = ""
            if past_versions:
                history_context = "\n\n[PAST PATIENT MEDICAL HISTORY ENCOUNTERS]:\n"
                for idx, ver in enumerate(past_versions):
                    history_context += f"Encounter History {idx+1}: {json.dumps(ver.soap_note_json)}\n"

            system_prompt = (
                "You are an elite, medical-grade AI Clinical Scribe. Transform the provided conversation transcript "
                "into a high-density, professional, clear SOAP note. You MUST include suggested semantic ICD-10 diagnosis "
                f"codes and plain descriptions matching the evaluation details.{history_context}"
            )

            response_stream = await aclient.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Active Transcript Observation Data:\n{payload.transcript}"}
                ],
                stream=True
            )
            
            async for chunk in response_stream:
                token = chunk.choices[0].delta.content
                if token:
                    yield f"data: {json.dumps({'token': token})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(sse_stream_generator(), media_type="text/event-stream")

@router.put("/{id}/draft", status_code=status.HTTP_200_OK)
def save_encounter_draft(
    id: int,
    payload: EncounterDraftPayload,
    db: Session = Depends(get_db),
    current_user: Provider = Depends(get_current_provider)
):
    # Locate the target encounter structure
    encounter = db.query(Encounter).filter(Encounter.id == id).first()
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter row not found")
        
    # Multi-tenant context block validation (Comment out if bypassing ID matches)
    if encounter.provider_id != current_user.id:
         raise HTTPException(status_code=403, detail="Unauthorized session context match")

    # Commit state variables directly to data storage
    encounter.soap_note_json = payload.soap_note_json
    encounter.updated_at = datetime.now()
    
    db.commit()
    return {"status": "success", "message": "Draft auto-saved successfully"}
