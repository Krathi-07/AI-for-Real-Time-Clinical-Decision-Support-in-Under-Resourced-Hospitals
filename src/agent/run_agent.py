# src/agent/run_agent.py
"""
Smoke test for the LangGraph clinical agent.
Runs three scenarios: septic patient, healthy patient, insufficient data.
"""

from src.agent.graph import clinical_agent


def run(label: str, fhir_features: dict, note_text: str) -> None:
    print(f"\n{'='*60}")
    print(f"SCENARIO: {label}")
    print('='*60)

    initial_state = {
        "patient_id": "test-001",
        "fhir_features": fhir_features,
        "note_text": note_text,
        "reasoning_trace": [],
        # Defaults for all other fields
        "data_sufficient": False,
        "completeness_score": 0.0,
        "model_risk_score": 0.0,
        "model_risk_level": "LOW",
        "model_drivers": [],
        "nlp_symptoms": [],
        "nlp_diagnoses": [],
        "nlp_medications": [],
        "nlp_vitals_mentioned": {},
        "fused_risk_level": "LOW",
        "conflicts": [],
        "alert_text": "",
        "requires_human_review": False,
        "review_reason": "",
    }

    result = clinical_agent.invoke(initial_state)

    print("\n--- REASONING TRACE ---")
    for step in result["reasoning_trace"]:
        print(f"  {step}")

    print("\n--- FINAL ALERT ---")
    print(result["alert_text"])

    print("\n--- HITL FLAG ---")
    print(f"  Requires human review: {result['requires_human_review']}")
    if result["review_reason"]:
        print(f"  Reason: {result['review_reason']}")


if __name__ == "__main__":

    # Scenario 1 — Septic patient with corroborating note
    run(
        label="Septic Patient (HIGH RISK)",
        fhir_features={
            "heart_rate": 118.0,
            "systolic_bp": 88.0,
            "diastolic_bp": 58.0,
            "respiratory_rate": 24.0,
            "body_temperature": 39.4,
            "spo2": 93.0,
            "lactate": 4.2,
            "wbc": 18.5,
            "creatinine": 2.1,
        },
        note_text=(
            "Patient presents with fever, rigors, and hypotension. "
            "Suspected sepsis. Started on piperacillin-tazobactam. "
            "HR 118, BP 88/58, Temp 39.4C, RR 24. "
            "Blood cultures sent. ICU consult requested."
        ),
    )

    # Scenario 2 — Healthy patient
    run(
        label="Healthy Patient (LOW RISK)",
        fhir_features={
            "heart_rate": 72.0,
            "systolic_bp": 118.0,
            "diastolic_bp": 76.0,
            "respiratory_rate": 14.0,
            "body_temperature": 37.0,
            "spo2": 99.0,
            "lactate": 0.9,
            "wbc": 7.2,
        },
        note_text=(
            "Routine follow-up. Patient feels well. "
            "No fever, no shortness of breath. Vitals stable."
        ),
    )

    # Scenario 3 — Insufficient data
    run(
        label="Sparse Data (ABSTENTION)",
        fhir_features={
            "heart_rate": 101.0,
        },
        note_text="",
    )