# src/agent/state.py
"""
AgentState — the shared memory object passed between every LangGraph node.

Think of this as the agent's notepad. Each node reads what it needs,
adds its findings, and passes the updated state to the next node.
"""

from typing import TypedDict


class AgentState(TypedDict):
    # ── Inputs ──────────────────────────────────────────────────────────────
    patient_id: str
    fhir_features: dict          # raw vitals/labs from FHIR pipeline
    note_text: str               # free-text clinical note

    # ── Triage gate ─────────────────────────────────────────────────────────
    data_sufficient: bool        # False → agent exits early with abstention
    completeness_score: float    # 0.0–1.0, fraction of critical features present

    # ── Vitals analyser output ───────────────────────────────────────────────
    model_risk_score: float      # 0.0–1.0 probability from XGBoost
    model_risk_level: str        # LOW / MODERATE / HIGH / CRITICAL
    model_drivers: list          # top SHAP-style feature contributions

    # ── NLP analyser output ──────────────────────────────────────────────────
    nlp_symptoms: list           # e.g. ["fever", "rigors"]
    nlp_diagnoses: list          # e.g. ["sepsis", "pneumonia"]
    nlp_medications: list        # e.g. ["piperacillin-tazobactam"]
    nlp_vitals_mentioned: dict   # vitals extracted from note text

    # ── Fusion output ────────────────────────────────────────────────────────
    fused_risk_level: str        # final risk after NLP corroboration
    conflicts: list              # model vs note disagreements
    alert_text: str              # human-readable alert for the doctor

    # ── Reasoning trace ──────────────────────────────────────────────────────
    reasoning_trace: list        # ordered list of strings — what the agent did

    # ── HITL flag ────────────────────────────────────────────────────────────
    requires_human_review: bool  # True if CRITICAL or low data confidence
    review_reason: str           # why human review was triggered
    