# src/agent/nodes.py
from src.agent.state import AgentState
from src.models.early_warning import EarlyWarningSepsis
from src.nlp.note_parser import ClinicalNoteParser
from src.treatment.recommender import TreatmentRecommender

_recommender = TreatmentRecommender()

_warning_model = None
_note_parser = None

def _get_warning_model():
    global _warning_model
    if _warning_model is None:
        _warning_model = EarlyWarningSepsis()
        _warning_model.train_on_synthetic_data()
    return _warning_model

def _get_note_parser():
    global _note_parser
    if _note_parser is None:
        _note_parser = ClinicalNoteParser()
    return _note_parser


def triage_node(state):
    trace = list(state.get('reasoning_trace', []))
    features = state.get('fhir_features', {})
    critical = ['heart_rate', 'systolic_bp', 'respiratory_rate',
                'spo2', 'body_temperature', 'lactate', 'wbc']
    present = sum(1 for k in critical if features.get(k, -1.0) != -1.0)
    completeness = present / len(critical)
    sufficient = completeness >= 0.4
    msg = 'Proceeding.' if sufficient else 'Aborting.'
    trace.append(f'[Triage] {present}/{len(critical)} features ({completeness:.0%}). {msg}')
    return {'data_sufficient': sufficient, 'completeness_score': completeness, 'reasoning_trace': trace}


def _calibrate_risk(score: float, features: dict) -> str:
    """
    Post-model calibration layer using qSOFA + Sepsis-3 vital thresholds.
    Overrides bimodal XGBoost output with clinically grounded risk tiers.
    qSOFA: resp_rate >= 22 (+1), systolic_bp <= 100 (+1) = each 1 point.
    """
    lactate = features.get('lactate', 0.0)
    systolic_bp = features.get('systolic_bp', 120.0)
    resp_rate = features.get('respiratory_rate', 16.0)

    # qSOFA score from vitals only (confusion added later by fusion if NLP present)
    qsofa = 0
    if resp_rate >= 22:
        qsofa += 1
    if systolic_bp <= 100:
        qsofa += 1

    if score >= 0.85:
        # Septic shock criteria: high score + organ hypoperfusion markers
        if lactate >= 4.0 or systolic_bp < 90:
            return 'CRITICAL'
        # High risk: elevated score + 2 qSOFA points
        if qsofa >= 2:
            return 'HIGH'
        # Elevated score alone without shock markers
        return 'HIGH'
    elif score >= 0.40:
        return 'MEDIUM'
    else:
        return 'LOW'


def vitals_node(state):
    trace = list(state.get('reasoning_trace', []))
    features = state.get('fhir_features', {})
    model = _get_warning_model()
    prediction = model.predict(features)

    # Apply calibration layer to fix bimodal XGBoost distribution
    calibrated_level = _calibrate_risk(prediction.risk_score, features)

    drivers = [f"{d.feature_name} ({d.direction})" for d in prediction.top_drivers[:3]]
    trace.append(
        f'[Vitals] Risk: {calibrated_level} (score={prediction.risk_score:.3f}). '
        f'Drivers: {", ".join(drivers)}'
    )
    return {
        'model_risk_score': prediction.risk_score,
        'model_risk_level': calibrated_level,
        'model_drivers': prediction.top_drivers,
        'reasoning_trace': trace,
    }


def nlp_node(state):
    trace = list(state.get('reasoning_trace', []))
    note_text = state.get('note_text', '')
    if not note_text.strip():
        trace.append('[NLP] No note provided - skipping.')
        return {'nlp_symptoms': [], 'nlp_diagnoses': [], 'nlp_medications': [],
                'nlp_vitals_mentioned': {}, 'reasoning_trace': trace}
    parser = _get_note_parser()
    result = parser.parse(note_text)
    symptoms = list(result.symptoms)
    diagnoses = list(result.diagnoses)
    medications = list(result.medications)
    vitals = result.vitals_mentioned
    trace.append(f'[NLP] symptoms={symptoms}, diagnoses={diagnoses}, meds={medications}')
    return {'nlp_symptoms': symptoms, 'nlp_diagnoses': diagnoses,
            'nlp_medications': medications, 'nlp_vitals_mentioned': vitals,
            'reasoning_trace': trace}


def fusion_node(state):
    trace = list(state.get('reasoning_trace', []))
    risk_level = state.get('model_risk_level', 'LOW')
    diagnoses = [d.lower() for d in state.get('nlp_diagnoses', [])]
    symptoms = [s.lower() for s in state.get('nlp_symptoms', [])]
    medications = [m.lower() for m in state.get('nlp_medications', [])]
    model_drivers = state.get('model_drivers', [])
    conflicts = []
    RISK_ORDER = ['LOW', 'MODERATE', 'HIGH', 'CRITICAL']

    def escalate(level):
        idx = RISK_ORDER.index(level)
        return RISK_ORDER[min(idx + 1, len(RISK_ORDER) - 1)]

    sepsis_terms = {'sepsis', 'septicaemia', 'septicemia', 'bacteraemia', 'bacteremia'}
    if any(term in d for d in diagnoses for term in sepsis_terms):
        old_level = risk_level
        risk_level = escalate(risk_level)
        trace.append(f'[Fusion] Rule 1 - Sepsis in NLP. Risk {old_level} -> {risk_level}.')

    driver_features = {d.feature_name.lower().replace('_', ' ') for d in model_drivers}
    overlap = [s for s in symptoms if any(f in s or s in f for f in driver_features)]
    if overlap:
        trace.append(f'[Fusion] Rule 2 - Symptoms corroborate drivers: {overlap}.')

    abx_terms = {'piperacillin', 'tazobactam', 'meropenem', 'vancomycin',
                 'ceftriaxone', 'metronidazole', 'imipenem'}
    abx_found = [m for m in medications if any(a in m for a in abx_terms)]
    if abx_found:
        trace.append(f'[Fusion] Rule 3 - Antibiotics found: {abx_found}.')

    negated = any('sepsis' in s and 'no ' in s
                  for s in state.get('note_text', '').lower().split('.'))
    if negated and risk_level in ('HIGH', 'CRITICAL'):
        conflicts.append('Model HIGH/CRITICAL but note negates sepsis - re-evaluate.')
        trace.append(f'[Fusion] Rule 4 - Conflict: {conflicts[-1]}')

    return {'fused_risk_level': risk_level, 'conflicts': conflicts, 'reasoning_trace': trace}


def summary_node(state):
    trace = list(state.get('reasoning_trace', []))
    risk = state.get('fused_risk_level', 'LOW')
    score = state.get('model_risk_score', 0.0)
    model_drivers = state.get('model_drivers', [])[:3]
    symptoms = state.get('nlp_symptoms', [])
    diagnoses = state.get('nlp_diagnoses', [])
    conflicts = state.get('conflicts', [])
    completeness = state.get('completeness_score', 1.0)

    driver_text = '; '.join(
        f"{d.feature_name} ({d.direction})" for d in model_drivers
    ) or 'insufficient data'
    symptom_text = ', '.join(symptoms) if symptoms else 'none documented'
    diagnosis_text = ', '.join(diagnoses) if diagnoses else 'none in note'

    alert = (
        f"CLINICAL ALERT - Risk Level: {risk} ({score:.1%})\n"
        f"Model drivers: {driver_text}\n"
        f"NLP symptoms: {symptom_text}\n"
        f"NLP diagnoses: {diagnosis_text}\n"
        f"Data completeness: {completeness:.0%}"
    )
    if conflicts:
        alert += '\nCONFLICTS: ' + '; '.join(conflicts)

    requires_review = risk in ('HIGH', 'CRITICAL') or completeness < 0.5
    review_reason = ''
    if risk in ('HIGH', 'CRITICAL'):
        review_reason = f'Risk level is {risk} - mandatory attending review required.'
    elif completeness < 0.5:
        review_reason = f'Data completeness only {completeness:.0%} - AI confidence limited.'

    trace.append(
        f'[Summary] HITL={"YES" if requires_review else "NO"}. '
        f'Reason: {review_reason or "Not required."}'
    )
    return {
        'alert_text': alert,
        'requires_human_review': requires_review,
        'review_reason': review_reason,
        'reasoning_trace': trace,
    }


def treatment_node(state: AgentState) -> AgentState:
    """Generate evidence-based treatment recommendations."""
    plan = _recommender.recommend(
        risk_level=state["fused_risk_level"],
        top_drivers=state["model_drivers"],
        nlp_symptoms=state["nlp_symptoms"],
        nlp_diagnoses=state["nlp_diagnoses"],
    )
    state["treatment_plan"] = plan.to_dict()
    state["reasoning_trace"].append(
        f"[Treatment] {len(plan.immediate_actions)} immediate, "
        f"{len(plan.urgent_actions)} urgent, "
        f"{len(plan.routine_actions)} routine actions. "
        f"Reassess in {plan.reassess_in_minutes} min."
    )
    return state
