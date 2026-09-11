import pathlib

extra = """

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


def vitals_node(state):
    trace = list(state.get('reasoning_trace', []))
    model = _get_warning_model()
    prediction = model.predict(state.get('fhir_features', {}))
    drivers = [f"{d['feature']} ({d['direction']})" for d in prediction.top_drivers[:3]]
    trace.append(f'[Vitals] Risk: {prediction.risk_level} (score={prediction.risk_score:.3f}). Drivers: {", ".join(drivers)}')
    return {'model_risk_score': prediction.risk_score, 'model_risk_level': prediction.risk_level,
            'model_drivers': prediction.top_drivers, 'reasoning_trace': trace}


def nlp_node(state):
    trace = list(state.get('reasoning_trace', []))
    note_text = state.get('note_text', '')
    if not note_text.strip():
        trace.append('[NLP] No note provided - skipping.')
        return {'nlp_symptoms': [], 'nlp_diagnoses': [], 'nlp_medications': [],
                'nlp_vitals_mentioned': {}, 'reasoning_trace': trace}
    parser = _get_note_parser()
    result = parser.parse(note_text)
    symptoms = [e['text'] for e in result.get('symptoms', [])]
    diagnoses = [e['text'] for e in result.get('diagnoses', [])]
    medications = [e['text'] for e in result.get('medications', [])]
    vitals = result.get('vitals', {})
    trace.append(f'[NLP] symptoms={symptoms}, diagnoses={diagnoses}, meds={medications}')
    return {'nlp_symptoms': symptoms, 'nlp_diagnoses': diagnoses,
            'nlp_medications': medications, 'nlp_vitals_mentioned': vitals, 'reasoning_trace': trace}


def fusion_node(state):
    trace = list(state.get('reasoning_trace', []))
    risk_level = state.get('model_risk_level', 'LOW')
    diagnoses = [d.lower() for d in state.get('nlp_diagnoses', [])]
    symptoms = [s.lower() for s in state.get('nlp_symptoms', [])]
    medications = [m.lower() for m in state.get('nlp_medications', [])]
    drivers = state.get('model_drivers', [])
    conflicts = []
    RISK_ORDER = ['LOW', 'MODERATE', 'HIGH', 'CRITICAL']

    def escalate(level):
        idx = RISK_ORDER.index(level)
        return RISK_ORDER[min(idx + 1, len(RISK_ORDER) - 1)]

    sepsis_terms = {'sepsis', 'septicaemia', 'septicemia', 'bacteraemia', 'bacteremia'}
    if any(term in d for d in diagnoses for term in sepsis_terms):
        old = risk_level
        risk_level = escalate(risk_level)
        trace.append(f'[Fusion] Rule 1 - Sepsis in NLP. Risk {old} -> {risk_level}.')

    driver_features = {d['feature'].lower().replace('_', ' ') for d in drivers}
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
    drivers = state.get('model_drivers', [])[:3]
    symptoms = state.get('nlp_symptoms', [])
    diagnoses = state.get('nlp_diagnoses', [])
    conflicts = state.get('conflicts', [])
    completeness = state.get('completeness_score', 1.0)
    driver_text = '; '.join(f"{d['feature']} ({d['direction']})" for d in drivers) or 'insufficient data'
    alert = (f'CLINICAL ALERT - Risk Level: {risk} ({score:.1%})\\n'
             f'Model drivers: {driver_text}\\n'
             f'NLP symptoms: {", ".join(symptoms) or "none"}\\n'
             f'NLP diagnoses: {", ".join(diagnoses) or "none"}\\n'
             f'Data completeness: {completeness:.0%}')
    if conflicts:
        alert += '\\nCONFLICTS: ' + '; '.join(conflicts)
    requires_review = risk in ('HIGH', 'CRITICAL') or completeness < 0.5
    review_reason = ''
    if risk in ('HIGH', 'CRITICAL'):
        review_reason = f'Risk level is {risk} - mandatory attending review required.'
    elif completeness < 0.5:
        review_reason = f'Data completeness only {completeness:.0%} - AI confidence limited.'
    trace.append(f'[Summary] HITL={"YES" if requires_review else "NO"}. Reason: {review_reason or "Not required."}')
    return {'alert_text': alert, 'requires_human_review': requires_review,
            'review_reason': review_reason, 'reasoning_trace': trace}
"""

existing = pathlib.Path('src/agent/nodes.py').read_text(encoding='utf-8')
pathlib.Path('src/agent/nodes.py').write_text(existing + extra, encoding='utf-8')
print('nodes.py updated OK')