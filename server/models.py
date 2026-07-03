from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, Date, CheckConstraint
from sqlalchemy.orm import relationship
import datetime
from database import Base

class Provider(Base):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # 'Provider' or 'Admin'
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint(role.in_(['Provider', 'Admin']), name='check_valid_role'),
    )

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    dob = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class Encounter(Base):
    __tablename__ = "encounters"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.id", ondelete="RESTRICT"), nullable=False)
    current_status = Column(String(50), default="Draft", nullable=False) # 'Draft' or 'Finalized'
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint(current_status.in_(['Draft', 'Finalized']), name='check_valid_status'),
    )

class EncounterVersion(Base):
    __tablename__ = "encounter_versions"

    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    transcript_snapshot = Column(Text, nullable=False)
    soap_note_json = Column(Text, nullable=False) # Stored stringified JSON structure
    saved_by_provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    system_prompt = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
