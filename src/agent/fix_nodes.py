import pathlib

p = pathlib.Path('src/agent/nodes.py')
t = p.read_text(encoding='utf-8')

old = t[t.find('def summary_node'):]

new = """def summary_node(state):
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
        f"CLINICAL ALERT - Risk Level: {risk} ({score:.1%})\\n"
        f"Model drivers: {driver_text}\\n"
        f"NLP symptoms: {symptom_text}\\n"
        f"NLP diagnoses: {diagnosis_text}\\n"
        f"Data completeness: {completeness:.0%}"
    )
    if conflicts:
        alert += '\\nCONFLICTS: ' + '; '.join(conflicts)

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
"""

t = t[:t.find('def summary_node')] + new
p.write_text(t, encoding='utf-8')
print('fixed')