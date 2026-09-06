# src/api/schemas.py
"""
Pydantic schemas for the Clinical Decision Support API.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyseRequest(BaseModel):
    patient_id: str = Field(..., description="Unique patient identifier", example="P001")
    encounter_id: str = Field(default="", description="Hospital encounter/visit ID", example="ENC-2026-001")
    fhir_features: dict[str, float] = Field(
        default_factory=dict,
        description="Vital signs and lab values keyed by feature name.",
        example={"systolic_bp": 88.0, "heart_rate": 118.0, "lactate": 4.2},
    )
    note_text: str = Field(
        default="",
        description="Free-text clinical note for NLP analysis",
        example="65F presenting with fever and tachycardia. Suspect sepsis.",
    )


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    version: str = "0.1.0"
