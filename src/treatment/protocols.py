# src/treatment/protocols.py
"""
Evidence-based clinical protocols for sepsis management.
Based on Surviving Sepsis Campaign guidelines (2021)
and WHO Emergency Care guidelines for low-resource settings.

IMPORTANT: These are decision-support suggestions only.
           The attending doctor always makes the final call.
"""

from dataclasses import dataclass


@dataclass
class TreatmentAction:
    priority: str        # IMMEDIATE / URGENT / ROUTINE
    category: str        # FLUID / ANTIBIOTIC / TEST / MONITOR / TRANSFER
    action: str          # What to do
    rationale: str       # Why (shown to doctor)
    timeframe: str       # When to do it


# ── SEPSIS PROTOCOLS ──────────────────────────────────────────────────────────

CRITICAL_SEPSIS_PROTOCOL = [
    TreatmentAction(
        priority="IMMEDIATE",
        category="FLUID",
        action="Start IV crystalloid fluid bolus 30 mL/kg",
        rationale="Septic shock resuscitation — restore perfusion pressure",
        timeframe="Within 1 hour"
    ),
    TreatmentAction(
        priority="IMMEDIATE",
        category="ANTIBIOTIC",
        action="Administer broad-spectrum IV antibiotics",
        rationale="Every hour delay increases mortality by 7%",
        timeframe="Within 1 hour — before culture results"
    ),
    TreatmentAction(
        priority="IMMEDIATE",
        category="TEST",
        action="Draw blood cultures x2 (before antibiotics if possible)",
        rationale="Identify causative organism for targeted therapy",
        timeframe="Immediately"
    ),
    TreatmentAction(
        priority="IMMEDIATE",
        category="TEST",
        action="Measure serum lactate",
        rationale="Lactate >4 mmol/L indicates tissue hypoperfusion",
        timeframe="Immediately"
    ),
    TreatmentAction(
        priority="IMMEDIATE",
        category="MONITOR",
        action="Insert urinary catheter — monitor urine output hourly",
        rationale="Target urine output >0.5 mL/kg/hr as perfusion marker",
        timeframe="Immediately"
    ),
    TreatmentAction(
        priority="IMMEDIATE",
        category="TRANSFER",
        action="Transfer to ICU or highest available care level",
        rationale="CRITICAL patients require continuous monitoring",
        timeframe="Within 1 hour"
    ),
    TreatmentAction(
        priority="URGENT",
        category="TEST",
        action="Order CBC, CMP, coagulation panel, procalcitonin",
        rationale="Assess organ function and infection severity",
        timeframe="Within 2 hours"
    ),
    TreatmentAction(
        priority="URGENT",
        category="MONITOR",
        action="Continuous ECG + SpO2 monitoring",
        rationale="Detect arrhythmia and respiratory failure early",
        timeframe="Immediately"
    ),
]

HIGH_RISK_PROTOCOL = [
    TreatmentAction(
        priority="URGENT",
        category="TEST",
        action="Order serum lactate, blood cultures, CBC",
        rationale="Confirm sepsis diagnosis and baseline organ function",
        timeframe="Within 2 hours"
    ),
    TreatmentAction(
        priority="URGENT",
        category="FLUID",
        action="Start IV access — administer 500 mL crystalloid bolus",
        rationale="Early fluid resuscitation before deterioration",
        timeframe="Within 2 hours"
    ),
    TreatmentAction(
        priority="URGENT",
        category="ANTIBIOTIC",
        action="Prepare empiric antibiotics — await culture if stable",
        rationale="HIGH risk may progress to CRITICAL within hours",
        timeframe="Within 2 hours"
    ),
    TreatmentAction(
        priority="URGENT",
        category="MONITOR",
        action="Vital signs every 30 minutes",
        rationale="Early detection of deterioration to CRITICAL",
        timeframe="Start immediately"
    ),
    TreatmentAction(
        priority="ROUTINE",
        category="TEST",
        action="Chest X-ray to rule out pneumonia source",
        rationale="Identify infection source for targeted treatment",
        timeframe="Within 4 hours"
    ),
]

MEDIUM_RISK_PROTOCOL = [
    TreatmentAction(
        priority="URGENT",
        category="MONITOR",
        action="Vital signs every 1 hour for next 4 hours",
        rationale="Catch early deterioration — medium risk can escalate",
        timeframe="Start immediately"
    ),
    TreatmentAction(
        priority="URGENT",
        category="TEST",
        action="Check lactate level and urine output",
        rationale="Lactate trend predicts trajectory",
        timeframe="Within 2 hours"
    ),
    TreatmentAction(
        priority="ROUTINE",
        category="FLUID",
        action="Ensure adequate oral or IV hydration",
        rationale="Prevent dehydration-driven deterioration",
        timeframe="Within 4 hours"
    ),
    TreatmentAction(
        priority="ROUTINE",
        category="TEST",
        action="Reassess full vitals panel in 2 hours",
        rationale="Re-run AI analysis with updated values",
        timeframe="In 2 hours"
    ),
]

LOW_RISK_PROTOCOL = [
    TreatmentAction(
        priority="ROUTINE",
        category="MONITOR",
        action="Routine vital signs every 4 hours",
        rationale="Low risk — standard monitoring sufficient",
        timeframe="Routine schedule"
    ),
    TreatmentAction(
        priority="ROUTINE",
        category="TEST",
        action="Reassess if any vital sign changes",
        rationale="AI will re-flag if condition deteriorates",
        timeframe="PRN (as needed)"
    ),
]

# ── DRIVER-SPECIFIC ADDITIONS ─────────────────────────────────────────────────

DRIVER_ACTIONS = {
    "lactate": TreatmentAction(
        priority="IMMEDIATE",
        category="TEST",
        action="Repeat lactate in 2 hours after resuscitation",
        rationale="Lactate clearance >10% confirms adequate resuscitation",
        timeframe="2 hours post-fluid"
    ),
    "heart_rate": TreatmentAction(
        priority="URGENT",
        category="MONITOR",
        action="Continuous cardiac monitoring — rule out arrhythmia",
        rationale="Tachycardia may indicate cardiac compromise or fever",
        timeframe="Immediately"
    ),
    "systolic_bp": TreatmentAction(
        priority="IMMEDIATE",
        category="FLUID",
        action="Vasopressors if MAP <65 despite adequate fluids (norepinephrine first-line)",
        rationale="Septic shock requires vasopressor support",
        timeframe="If no response to fluids within 1 hour"
    ),
    "respiratory_rate": TreatmentAction(
        priority="URGENT",
        category="MONITOR",
        action="Supplemental oxygen — target SpO2 >94%",
        rationale="Tachypnea indicates respiratory compensation or failure",
        timeframe="Immediately"
    ),
    "creatinine": TreatmentAction(
        priority="URGENT",
        category="TEST",
        action="Monitor urine output hourly — check for AKI",
        rationale="Rising creatinine = acute kidney injury from sepsis",
        timeframe="Immediately"
    ),
    "wbc": TreatmentAction(
        priority="URGENT",
        category="TEST",
        action="Blood cultures x2 + urine culture + consider LP if indicated",
        rationale="Elevated WBC confirms infection — identify source",
        timeframe="Within 1 hour"
    ),
    "spo2": TreatmentAction(
        priority="IMMEDIATE",
        category="MONITOR",
        action="Apply supplemental O2 immediately — prepare for intubation if SpO2 <90%",
        rationale="Hypoxia requires immediate intervention",
        timeframe="Immediately"
    ),
}

# ── NLP-SPECIFIC ADDITIONS ────────────────────────────────────────────────────

NLP_ACTIONS = {
    "sepsis": TreatmentAction(
        priority="IMMEDIATE",
        category="ANTIBIOTIC",
        action="Follow Surviving Sepsis Bundle — Hour-1 bundle mandatory",
        rationale="Clinical sepsis diagnosis confirmed by NLP + model",
        timeframe="Within 1 hour"
    ),
    "pneumonia": TreatmentAction(
        priority="URGENT",
        category="ANTIBIOTIC",
        action="Add respiratory fluoroquinolone or beta-lactam for CAP coverage",
        rationale="Pneumonia as sepsis source requires targeted coverage",
        timeframe="Within 2 hours"
    ),
    "fever": TreatmentAction(
        priority="ROUTINE",
        category="MONITOR",
        action="Antipyretic if temp >38.5C — paracetamol 1g IV/oral",
        rationale="Reduce metabolic demand — monitor temperature trend",
        timeframe="As needed"
    ),
    "hypotension": TreatmentAction(
        priority="IMMEDIATE",
        category="FLUID",
        action="Aggressive fluid resuscitation — 30 mL/kg bolus",
        rationale="Hypotension = septic shock until proven otherwise",
        timeframe="Immediately"
    ),
    "confusion": TreatmentAction(
        priority="URGENT",
        category="TEST",
        action="Rule out meningitis — consider LP. Check blood glucose.",
        rationale="Altered mental status in sepsis = severe organ dysfunction",
        timeframe="Within 1 hour"
    ),
}

PROTOCOL_MAP = {
    "CRITICAL": CRITICAL_SEPSIS_PROTOCOL,
    "HIGH": HIGH_RISK_PROTOCOL,
    "MEDIUM": MEDIUM_RISK_PROTOCOL,
    "LOW": LOW_RISK_PROTOCOL,
}
