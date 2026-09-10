# src/treatment/recommender.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.treatment.protocols import (
    DRIVER_ACTIONS,
    NLP_ACTIONS,
    PROTOCOL_MAP,
    TreatmentAction,
)


@dataclass
class TreatmentPlan:
    risk_level: str
    estimated_severity: str
    immediate_actions: list[TreatmentAction] = field(default_factory=list)
    urgent_actions: list[TreatmentAction] = field(default_factory=list)
    routine_actions: list[TreatmentAction] = field(default_factory=list)
    escalation_triggers: list[str] = field(default_factory=list)
    reassess_in_minutes: int = 240

    def to_dict(self) -> dict:
        def action_dict(a: TreatmentAction) -> dict:
            return {
                "priority": a.priority,
                "category": a.category,
                "action": a.action,
                "rationale": a.rationale,
                "timeframe": a.timeframe,
            }
        return {
            "risk_level": self.risk_level,
            "estimated_severity": self.estimated_severity,
            "immediate_actions": [action_dict(a) for a in self.immediate_actions],
            "urgent_actions": [action_dict(a) for a in self.urgent_actions],
            "routine_actions": [action_dict(a) for a in self.routine_actions],
            "escalation_triggers": self.escalation_triggers,
            "reassess_in_minutes": self.reassess_in_minutes,
        }


SEVERITY_TEXT = {
    "CRITICAL": "Patient is in immediate danger. Septic shock likely. Act within minutes.",
    "HIGH":     "Patient at high risk of deterioration. Urgent assessment required within 2 hours.",
    "MEDIUM":   "Patient showing early warning signs. Close monitoring required. Can escalate.",
    "LOW":      "Patient currently stable. Routine monitoring. Re-analyse if vitals change.",
}

ESCALATION_TRIGGERS = {
    "CRITICAL": [
        "No improvement in BP after 2L fluids -> start vasopressors",
        "SpO2 drops below 90% -> prepare intubation",
        "Urine output <0.5 mL/kg/hr for 2 hours -> nephrology consult",
        "GCS drops -> CT head + neurology",
    ],
    "HIGH": [
        "Lactate rises or stays >4 -> escalate to CRITICAL protocol",
        "BP drops below 90 systolic -> start IV fluids immediately",
        "Temperature rises above 39.5C -> blood cultures immediately",
        "Confusion develops -> immediate reassessment",
    ],
    "MEDIUM": [
        "Any vital sign worsens -> re-run AI analysis immediately",
        "Patient reports new symptoms -> reassess",
        "Lactate comes back >2 -> escalate to HIGH protocol",
    ],
    "LOW": [
        "Any new symptom -> reassess immediately",
        "Vital signs change -> re-run AI analysis",
    ],
}

REASSESS_MINUTES = {
    "CRITICAL": 30,
    "HIGH": 60,
    "MEDIUM": 120,
    "LOW": 240,
}


class TreatmentRecommender:
    def recommend(
        self,
        risk_level: str,
        top_drivers: list[Any],
        nlp_symptoms: list[str],
        nlp_diagnoses: list[str],
    ) -> TreatmentPlan:

        level = risk_level.upper() if risk_level else "LOW"
        base_protocol = PROTOCOL_MAP.get(level, PROTOCOL_MAP["LOW"])

        immediate, urgent, routine = [], [], []

        for action in base_protocol:
            if action.priority == "IMMEDIATE":
                immediate.append(action)
            elif action.priority == "URGENT":
                urgent.append(action)
            else:
                routine.append(action)

        driver_names = []
        for d in top_drivers:
            if hasattr(d, "feature_name"):
                driver_names.append(d.feature_name)
            elif isinstance(d, dict):
                driver_names.append(d.get("feature_name", d.get("feature", "")))
            elif isinstance(d, str):
                driver_names.append(d)

        seen = set()
        for driver in driver_names:
            if driver in DRIVER_ACTIONS and driver not in seen:
                seen.add(driver)
                action = DRIVER_ACTIONS[driver]
                if action.priority == "IMMEDIATE":
                    immediate.append(action)
                elif action.priority == "URGENT":
                    urgent.append(action)
                else:
                    routine.append(action)

        all_nlp = [s.lower() for s in nlp_symptoms + nlp_diagnoses]
        for term in all_nlp:
            for key, action in NLP_ACTIONS.items():
                if key in term and key not in seen:
                    seen.add(key)
                    if action.priority == "IMMEDIATE":
                        immediate.append(action)
                    elif action.priority == "URGENT":
                        urgent.append(action)
                    else:
                        routine.append(action)

        return TreatmentPlan(
            risk_level=level,
            estimated_severity=SEVERITY_TEXT.get(level, ""),
            immediate_actions=immediate,
            urgent_actions=urgent,
            routine_actions=routine,
            escalation_triggers=ESCALATION_TRIGGERS.get(level, []),
            reassess_in_minutes=REASSESS_MINUTES.get(level, 240),
        )
