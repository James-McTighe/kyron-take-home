from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Encounter, EncounterVersion
from pydantic import BaseModel
import re

router = APIRouter(prefix="/api/encounters", tags=["encounters"])

# Schema to validate the incoming finalized note payload
class FinalizeNotePayload(BaseModel):
    subjective: str
    objective: str
    assessment: str
    plan: str


class GenerateSOAPPayload(BaseModel):
    transcript: str
    template_id: int | None = None


def _normalize_transcript(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _infer_icd10(transcript: str) -> list[dict[str, str]]:
    lowered = transcript.lower()
    suggestions: list[dict[str, str]] = []

    keyword_map = [
        (("cough", "uri", "cold", "congestion", "sore throat"), ("J06.9", "Acute upper respiratory infection, unspecified")),
        (("fever", "chills", "febrile"), ("R50.9", "Fever, unspecified")),
        (("headache", "migraine"), ("R51.9", "Headache, unspecified")),
        (("pain", "ache", "sprain"), ("R52", "Pain, unspecified")),
        (("hypertension", "high blood pressure"), ("I10", "Essential (primary) hypertension")),
        (("diabetes", "dm2", "hyperglycemia"), ("E11.9", "Type 2 diabetes mellitus without complications")),
        (("anxiety", "panic"), ("F41.9", "Anxiety disorder, unspecified")),
    ]

    for keywords, (code, description) in keyword_map:
        if any(keyword in lowered for keyword in keywords):
            suggestions.append({"code": code, "description": description})

    if not suggestions:
        suggestions.append({"code": "R69", "description": "Illness, unspecified"})

    return suggestions[:3]


def _generate_soap(transcript: str) -> dict[str, object]:
    normalized = _normalize_transcript(transcript)
    lower = normalized.lower()
    icd10_suggestions = _infer_icd10(normalized)

    subjective_parts = []
    objective_parts = []
    assessment_parts = []
    plan_parts = []

    if normalized:
        subjective_parts.append(f"Patient report reviewed from transcript: {normalized}")

    if any(term in lower for term in ["cough", "throat", "congestion", "uri", "cold"]):
        subjective_parts.append("Reports upper respiratory symptoms including cough and/or throat irritation.")
        objective_parts.append("Appears consistent with a mild respiratory illness based on encounter description.")
        assessment_parts.append("Presentation is most consistent with an uncomplicated upper respiratory process.")
        plan_parts.append("Recommend supportive care, hydration, rest, and symptom monitoring.")

    if any(term in lower for term in ["fever", "chills"]):
        subjective_parts.append("Fever or systemic symptoms were mentioned in the encounter history.")
        objective_parts.append("Monitor temperature trend and clinical status if symptoms persist or worsen.")

    if any(term in lower for term in ["pain", "ache", "sprain", "injury"]):
        subjective_parts.append("Pain or injury-related symptoms are present in the transcript.")
        objective_parts.append("Documented pain pattern and functional impact should be clarified on exam.")
        assessment_parts.append("Pain syndrome or localized injury remains part of the working differential.")
        plan_parts.append("Consider conservative measures, reassessment, and escalation if symptoms worsen.")

    if any(term in lower for term in ["hypertension", "blood pressure"]):
        assessment_parts.append("Blood pressure-related follow-up may be warranted depending on observed readings.")
        plan_parts.append("Encourage home monitoring and follow-up for elevated blood pressure if applicable.")

    if not objective_parts:
        objective_parts.append("Objective data were limited in the transcript and should be completed from exam/vitals.")
    if not assessment_parts:
        assessment_parts.append("Clinical impression remains limited by the source transcript and should be refined after review.")
    if not plan_parts:
        plan_parts.append("Finalize treatment plan after clinician review and confirmatory exam details.")

    return {
        "subjective": " ".join(subjective_parts).strip(),
        "objective": " ".join(objective_parts).strip(),
        "assessment": f"{' '.join(assessment_parts).strip()} Suggested ICD-10: {icd10_suggestions[0]['code']} - {icd10_suggestions[0]['description']}.",
        "plan": " ".join(plan_parts).strip(),
        "icd10_suggestions": icd10_suggestions,
    }

@router.post("/{encounter_id}/finalize", status_code=status.HTTP_201_CREATED)
def finalize_encounter_version(
    encounter_id: int, 
    payload: FinalizeNotePayload, 
    db: Session = Depends(get_db)
):
    # 1. Look up the parent encounter
    encounter = db.query(Encounter).filter(Encounter.id == encounter_id).first()
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter record not found.")

    # 2. Query the database to find the current max version number for this encounter
    highest_version = db.query(EncounterVersion)\
        .filter(EncounterVersion.encounter_id == encounter_id)\
        .order_by(EncounterVersion.version_number.desc())\
        .first()
    
    next_version_number = (highest_version.version_number + 1) if highest_version else 1

    # 3. Pack the fields back into structured JSON for storage
    soap_json = {
        "subjective": payload.subjective,
        "objective": payload.objective,
        "assessment": payload.assessment,
        "plan": payload.plan
    }

    # 4. Perform an append-only write (Never overwrite historical records)
    new_version = EncounterVersion(
        encounter_id=encounter_id,
        version_number=next_version_number,
        soap_note_json=soap_json,
        saved_by_provider_id=encounter.provider_id  # Multi-tenant context binding
    )
    
    # 5. Flip encounter status flag to Finalized
    encounter.current_status = "Finalized"
    
    db.add(new_version)
    db.commit()
    db.refresh(new_version)

    return {
        "message": "Clinical record locked successfully.",
        "encounter_id": encounter_id,
        "committed_version": new_version.version_number
    }


@router.post("/generate-soap")
def generate_soap_note(payload: GenerateSOAPPayload):
    if not payload.transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript is required to generate a SOAP note.")

    return _generate_soap(payload.transcript)
