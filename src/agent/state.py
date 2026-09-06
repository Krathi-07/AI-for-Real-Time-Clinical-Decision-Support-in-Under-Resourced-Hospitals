# src/agent/state.py
from typing import TypedDict


class AgentState(TypedDict):
    # Inputs
    patient_id: str
    fhir_features: dict
    note_text: str

    # Triage gate
    data_sufficient: bool
    completeness_score: float

    # Vitals analyser output
    model_risk_score: float
    model_risk_level: str
    model_drivers: list

    # NLP analyser output
    nlp_symptoms: list
    nlp_diagnoses: list
    nlp_medications: list
    nlp_vitals_mentioned: dict

    # Fusion output
    fused_risk_level: str
    conflicts: list
    alert_text: str

    # Reasoning trace
    reasoning_trace: list

    # HITL flag
    requires_human_review: bool
    review_reason: str
