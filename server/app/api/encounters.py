# backend/app/api/encounters.py
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from openai import AsyncOpenAI
from app.database import get_db
from app.models import Encounter, EncounterVersion, Patient
from app.api.auth import get_current_provider
from app.schemas import EncounterGeneratePayload

router = APIRouter(prefix="/api/encounters", tags=["Encounters"])

# Ensure your local environment mounts OPENAI_API_KEY into the container environment variables
aclient = AsyncOpenAI()

@router.post("/{id}/generate")
async def generate_soap_stream(
    id: int, 
    payload: EncounterGeneratePayload, 
    db: Session = Depends(get_db),
    current_user: Provider = Depends(get_current_provider)
):
    # Enforce multi-tenant authorization parameters
    encounter = db.query(Encounter).filter(Encounter.id == id).first()
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter record not found")
    if encounter.provider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to encounter record")

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
    
    # Structure background context hidden entirely from client payloads
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

    # Asynchronous Generator function to stream tokens safely through Server-Sent Events (SSE)
    async def sse_stream_generator():
        try:
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
                    # Format as standard Server-Sent Event data packets
                    yield f"data: {json.dumps({'token': token})}\n\n"
                    await asyncio.sleep(0.01)  # Micro-cooldown to allow pipeline flushing
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(sse_stream_generator(), media_type="text/event-stream")
