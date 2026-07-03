import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from .database import Base

class Provider(Base):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)  # Stored securely via bcrypt/argon2
    role = Column(String, nullable=False, default="Provider")  # "Provider" or "Admin"
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    encounters = relationship("Encounter", back_populates="provider")

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False, index=True)
    last_name = Column(String, nullable=False, index=True)
    dob = Column(String, nullable=False, index=True)  # Format: YYYY-MM-DD
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    encounters = relationship("Encounter", back_populates="patient")

class Encounter(Base):
    __tablename__ = "encounters"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    current_status = Column(String, default="Draft", nullable=False)  # "Draft" or "Finalized"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    provider = relationship("Provider", back_populates="encounters")
    patient = relationship("Patient", back_populates="encounters")
    versions = relationship("EncounterVersion", back_populates="encounter", cascade="all, delete-orphan")

class EncounterVersion(Base):
    __tablename__ = "encounter_versions"

    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=False)
    version_number = Column(Integer, nullable=False)  # Explicit incrementing sequence
    transcript_snapshot = Column(Text, nullable=True)
    soap_note_json = Column(JSON, nullable=True)  # Strictly structures keys for S, O, A, P
    saved_by_provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    encounter = relationship("Encounter", back_populates="versions")

class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    system_prompt = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
