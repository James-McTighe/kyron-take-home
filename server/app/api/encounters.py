import asyncio
import json
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

    async def sse_stream_generator():
        # Deterministic dummy SOAP content for local/demo use.
        mock_segments = [
            {"section": "### SUBJECTIVE:\n"},
            {"token": "The patient presents today complaining of localized, dull, aching lower back pain "},
            {"token": "that began approximately three weeks ago after lifting heavy boxes. Pain is rated a 4/10 "},
            {"token": "and radiates occasionally into the left gluteal region.\n\n"},

            {"section": "### OBJECTIVE:\n"},
            {"token": "Vitals are stable. Lumbar spine range of motion is slightly restricted upon forward flexion. "},
            {"token": "No focal neurological deficits noted in the lower extremities.\n\n"},

            {"section": "### ASSESSMENT:\n"},
            {"token": "1. Low back pain, acute (ICD-10: M54.50)\n"},
            {"token": "2. Lumbar muscle strain\n\n"},

            {"section": "### PLAN:\n"},
            {"token": "Recommend physical therapy evaluation twice per week for 4 weeks. "},
            {"token": "Instructed patient on proper lifting mechanics and ergonomic adjustments."}
        ]

        for packet in mock_segments:
            if "section" in packet:
                yield f"data: {json.dumps({'token': packet['section']})}\n\n"
            else:
                yield f"data: {json.dumps({'token': packet['token']})}\n\n"
            await asyncio.sleep(0.3)

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

# High-frequency billing codes dictionary for immediate clinical lookup matching
ICD10_DATABASE = [
    {"code": "M54.50", "description": "Low back pain, unspecified"},
    {"code": "J06.9", "description": "Acute upper respiratory infection, unspecified (Cold)"},
    {"code": "J02.9", "description": "Acute pharyngitis, unspecified (Sore Throat)"},
    {"code": "I10", "description": "Essential (primary) hypertension (High Blood Pressure)"},
    {"code": "E11.9", "description": "Type 2 diabetes mellitus without complications"},
    {"code": "F41.1", "description": "Generalized anxiety disorder"},
    {"code": "F32.9", "description": "Major depressive disorder, single episode, unspecified"},
    {"code": "K21.9", "description": "Gastro-esophageal reflux disease without esophagitis (GERD)"},
    {"code": "M19.90", "description": "Osteoarthritis, unspecified site"},
    {"code": "B34.9", "description": "Viral infection, unspecified"},
]

@router.get("/icd10/search")
def search_icd10_codes(
    q: str = "", 
    current_user=Depends(get_current_provider)
):
    if not q or len(q.strip()) < 2:
        return []
        
    search_query = q.lower().strip()
    results = []
    
    for item in ICD10_DATABASE:
        if search_query in item["code"].lower() or search_query in item["description"].lower():
            results.append(item)
            
    # Limit results to top 5 matches for high-density UI rendering
    return results[:5]
