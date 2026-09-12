"""
Pydantic schemas for the Clinical Decision Support API.

Separation of concerns:
  - schemas.py  → what the API accepts and returns (HTTP contract)
  - clinical_engine.py → business logic (no HTTP knowledge)

This means the engine can be used by the API, a CLI, or a batch job
without any changes — only the schemas know about HTTP.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyseRequest(BaseModel):
    """
    Request body for POST /analyse.

    All vitals/labs are optional because rural hospitals may not have
    full data — the engine handles missing values with sentinel -1.0.
    At least one of fhir_features or note_text must be provided
    (validated in the route handler).
    """

    patient_id: str = Field(
        ...,
        description="Unique patient identifier",
        example="P001",
    )
    encounter_id: str = Field(
        default="",
        description="Hospital encounter/visit ID",
        example="ENC-2026-001",
    )

    # Structured vitals and labs — keys must match FEATURE_NAMES in early_warning.py
    fhir_features: dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Vital signs and lab values keyed by LOINC feature name. "
            "Missing values are handled automatically. "
            "Valid keys: systolic_bp, diastolic_bp, heart_rate, respiratory_rate, "
            "body_temperature, spo2, glucose, creatinine, wbc, lactate, hemoglobin, pulse_pressure"
        ),
        example={
            "systolic_bp": 88.0,
            "heart_rate": 118.0,
            "respiratory_rate": 26.0,
            "lactate": 4.2,
        },
    )

    # Free-text clinical note — optional
    note_text: str = Field(
        default="",
        description="Free-text clinical note or discharge summary for NLP analysis",
        example="65F presenting with fever and tachycardia. Suspect sepsis.",
    )


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    version: str = "0.1.0"
