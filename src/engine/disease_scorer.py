"""
Rule-based clinical scoring engine for all 11 supported diseases.
Each scorer takes a dict of parameter values and returns a ScoringResult.
These rules are based on published clinical guidelines (qSOFA, HEART, ADA, WHO, JNC-8).
"""

from dataclasses import dataclass


@dataclass
class ScoringResult:
    disease_id: str
    disease_name: str
    risk_level: str          # LOW / MODERATE / HIGH / CRITICAL
    risk_score: float        # 0.0 – 1.0
    findings: list[str]      # what the AI found abnormal
    recommendations: list[str]  # what the doctor should consider
    parameters_used: dict    # the raw values that were analysed


# ── Helpers ───────────────────────────────────────────────────────────────────

def _level(score: float) -> str:
    if score >= 0.75:  return "CRITICAL"
    if score >= 0.50:  return "HIGH"
    if score >= 0.25:  return "MODERATE"
    return "LOW"


def _abnormal(value, low, high, label, unit, findings):
    """Check one parameter and add a finding if abnormal."""
    if low is not None and value < low:
        findings.append(f"{label} LOW: {value} {unit} (normal ≥{low})")
        return True
    if high is not None and value > high:
        findings.append(f"{label} HIGH: {value} {unit} (normal ≤{high})")
        return True
    return False


# ── 11 Disease Scorers ────────────────────────────────────────────────────────

def score_sepsis(p: dict) -> ScoringResult:
    findings, flags = [], 0

    # qSOFA criteria
    if p.get("respiratory_rate", 0) >= 22:
        findings.append(f"Respiratory rate elevated: {p['respiratory_rate']}/min (qSOFA +1)")
        flags += 1
    if p.get("systolic_bp", 999) <= 100:
        findings.append(f"Systolic BP low: {p['systolic_bp']} mmHg (qSOFA +1)")
        flags += 1

    # Lab markers
    if p.get("lactate", 0) > 2.0:
        findings.append(f"Lactate elevated: {p['lactate']} mmol/L — strong sepsis marker")
        flags += 2
    if p.get("wbc", 0) > 12 or p.get("wbc", 999) < 4:
        findings.append(f"WBC abnormal: {p.get('wbc')} ×10³/µL")
        flags += 1
    if p.get("temperature", 37) > 38.3 or p.get("temperature", 37) < 36:
        findings.append(f"Temperature abnormal: {p.get('temperature')}°C")
        flags += 1
    if p.get("creatinine", 0) > 2.0:
        findings.append(f"Creatinine elevated: {p['creatinine']} mg/dL — possible organ dysfunction")
        flags += 1
    if p.get("spo2", 100) < 94:
        findings.append(f"SpO2 low: {p['spo2']}% — respiratory compromise")
        flags += 1

    score = min(flags / 6, 1.0)
    recs = []
    if score >= 0.5:
        recs = ["Initiate Sepsis-3 bundle immediately", "Blood cultures × 2 before antibiotics",
                "IV broad-spectrum antibiotics within 1 hour", "IV fluid resuscitation 30 mL/kg",
                "Lactate recheck in 2 hours", "ICU consultation"]
    elif score >= 0.25:
        recs = ["Monitor vitals every 30 minutes", "Blood cultures", "Consider IV antibiotics",
                "Fluid challenge 500 mL", "Reassess in 1 hour"]
    else:
        recs = ["Continue routine monitoring", "Reassess if condition changes"]

    return ScoringResult("sepsis", "Sepsis / Systemic Infection", _level(score), round(score, 2),
                         findings or ["All sepsis parameters within normal range"],
                         recs, p)


def score_diabetes(p: dict) -> ScoringResult:
    findings, flags = [], 0

    hba1c = p.get("hba1c", 0)
    glucose = p.get("fasting_glucose", 0)
    bmi = p.get("bmi", 0)

    if hba1c >= 6.5:
        findings.append(f"HbA1c: {hba1c}% — meets ADA diabetes diagnostic threshold (≥6.5%)")
        flags += 3
    elif hba1c >= 5.7:
        findings.append(f"HbA1c: {hba1c}% — prediabetes range (5.7–6.4%)")
        flags += 1

    if glucose >= 126:
        findings.append(f"Fasting glucose: {glucose} mg/dL — diabetic range (≥126)")
        flags += 3
    elif glucose >= 100:
        findings.append(f"Fasting glucose: {glucose} mg/dL — impaired fasting glucose (100–125)")
        flags += 1

    if bmi >= 30:
        findings.append(f"BMI: {bmi} — obese, significant diabetes risk factor")
        flags += 1
    elif bmi >= 25:
        findings.append(f"BMI: {bmi} — overweight")
        flags += 1

    if p.get("family_history") == "Yes":
        findings.append("Positive family history of diabetes")
        flags += 1

    if p.get("cholesterol", 0) > 200:
        findings.append(f"Total cholesterol: {p['cholesterol']} mg/dL — elevated")
        flags += 1

    score = min(flags / 7, 1.0)
    recs = []
    if score >= 0.5:
        recs = ["Confirm diagnosis with repeat fasting glucose or OGTT",
                "Refer to endocrinologist", "Start metformin if confirmed T2DM",
                "Diabetic diet counselling", "HbA1c recheck in 3 months",
                "Screen for nephropathy and retinopathy"]
    elif score >= 0.25:
        recs = ["Lifestyle modification — diet and exercise", "Repeat HbA1c in 3–6 months",
                "Monitor fasting glucose monthly", "Weight reduction target: 5–10% body weight"]
    else:
        recs = ["Annual diabetes screening recommended", "Maintain healthy BMI and diet"]

    return ScoringResult("diabetes", "Diabetes Mellitus", _level(score), round(score, 2),
                         findings or ["Diabetes parameters within normal range"], recs, p)


def score_heart_attack(p: dict) -> ScoringResult:
    """HEART score: History, ECG, Age, Risk factors, Troponin."""
    findings, heart_score = [], 0

    # Troponin
    troponin = p.get("troponin", 0)
    if troponin > 3 * 0.04:
        findings.append(f"Troponin I: {troponin} ng/mL — significantly elevated (>3× ULN)")
        heart_score += 2
    elif troponin > 0.04:
        findings.append(f"Troponin I: {troponin} ng/mL — elevated (above ULN)")
        heart_score += 1

    # ECG
    ecg = p.get("ecg_changes", "Normal")
    if ecg == "ST Elevation":
        findings.append("ECG: ST Elevation — STEMI pattern, emergency intervention required")
        heart_score += 2
    elif ecg == "ST Depression":
        findings.append("ECG: ST Depression — NSTEMI/unstable angina pattern")
        heart_score += 1

    # Chest pain
    pain = p.get("chest_pain", "None")
    if pain == "Typical Angina":
        findings.append("Chest pain: Typical angina pattern — high suspicion for ACS")
        heart_score += 2
    elif pain == "Atypical Angina":
        findings.append("Chest pain: Atypical angina — moderate suspicion")
        heart_score += 1

    # Age
    age = p.get("age", 0)
    if age >= 65:
        findings.append(f"Age {age} — high-risk group for MI")
        heart_score += 2
    elif age >= 45:
        findings.append(f"Age {age} — moderate-risk group")
        heart_score += 1

    # Smoking
    if p.get("smoking") == "Current":
        findings.append("Current smoker — major cardiovascular risk factor")
        heart_score += 1

    # BP
    if p.get("systolic_bp", 0) > 160:
        findings.append(f"Systolic BP: {p['systolic_bp']} mmHg — severely elevated")
        heart_score += 1

    score = min(heart_score / 8, 1.0)
    recs = []
    if score >= 0.5:
        recs = ["Activate cardiac catheterisation lab immediately (if STEMI)",
                "Aspirin 325 mg stat + P2Y12 inhibitor", "IV heparin anticoagulation",
                "Cardiology emergency consultation", "Serial troponin every 3 hours",
                "Continuous cardiac monitoring", "Oxygen if SpO2 <94%"]
    elif score >= 0.25:
        recs = ["Serial troponin at 0, 3, 6 hours", "Continuous ECG monitoring",
                "Cardiology consultation", "Aspirin 325 mg", "Rest and IV access"]
    else:
        recs = ["Routine cardiac review", "Lifestyle counselling", "Annual ECG if age >40"]

    return ScoringResult("heart_attack", "Acute Myocardial Infarction", _level(score), round(score, 2),
                         findings or ["Cardiac parameters within normal range"], recs, p)


def score_hypertension(p: dict) -> ScoringResult:
    findings, flags = [], 0
    sbp = p.get("systolic_bp", 0)
    dbp = p.get("diastolic_bp", 0)

    # JNC-8 staging
    if sbp >= 180 or dbp >= 120:
        findings.append(f"BP: {sbp}/{dbp} mmHg — Hypertensive Crisis (Stage 3)")
        flags += 4
    elif sbp >= 160 or dbp >= 100:
        findings.append(f"BP: {sbp}/{dbp} mmHg — Stage 2 Hypertension")
        flags += 3
    elif sbp >= 140 or dbp >= 90:
        findings.append(f"BP: {sbp}/{dbp} mmHg — Stage 1 Hypertension")
        flags += 2
    elif sbp >= 130 or dbp >= 80:
        findings.append(f"BP: {sbp}/{dbp} mmHg — Elevated (Prehypertension)")
        flags += 1

    if p.get("creatinine", 0) > 1.5:
        findings.append(f"Creatinine: {p['creatinine']} mg/dL — possible hypertensive nephropathy")
        flags += 1
    if p.get("bmi", 0) >= 30:
        findings.append(f"BMI: {p['bmi']} — obesity is a major hypertension driver")
        flags += 1

    score = min(flags / 5, 1.0)
    recs = []
    if score >= 0.75:
        recs = ["Emergency antihypertensive therapy IV", "Rule out hypertensive emergency (end-organ damage)",
                "Immediate cardiology/nephrology consult", "Continuous BP monitoring"]
    elif score >= 0.5:
        recs = ["Initiate antihypertensive medication (ACE inhibitor or ARB)",
                "Low-sodium DASH diet", "Home BP monitoring twice daily", "Follow-up in 1 week"]
    elif score >= 0.25:
        recs = ["Lifestyle changes: reduce salt, exercise 30 min/day, weight loss",
                "BP recheck in 1 month", "Consider medication if persistent"]
    else:
        recs = ["Annual BP monitoring", "Maintain healthy lifestyle"]

    return ScoringResult("hypertension", "Hypertension", _level(score), round(score, 2),
                         findings or ["Blood pressure within normal range"], recs, p)


def score_cancer_screening(p: dict) -> ScoringResult:
    findings, flags = [], 0

    if p.get("psa", 0) > 10:
        findings.append(f"PSA: {p['psa']} ng/mL — significantly elevated, prostate cancer workup needed")
        flags += 3
    elif p.get("psa", 0) > 4:
        findings.append(f"PSA: {p['psa']} ng/mL — elevated, further evaluation recommended")
        flags += 1

    if p.get("cea", 0) > 5:
        findings.append(f"CEA: {p['cea']} ng/mL — elevated, colorectal/lung cancer marker")
        flags += 2
    if p.get("ca125", 0) > 35:
        findings.append(f"CA-125: {p['ca125']} U/mL — elevated, ovarian cancer marker")
        flags += 2
    if p.get("ca199", 0) > 37:
        findings.append(f"CA 19-9: {p['ca199']} U/mL — elevated, pancreatic cancer marker")
        flags += 2

    if p.get("smoking") == "Current":
        findings.append("Current smoker — elevated risk for lung, oral, bladder cancers")
        flags += 1
    if p.get("family_history") == "Yes":
        findings.append("Positive family history — hereditary cancer risk")
        flags += 1

    score = min(flags / 6, 1.0)
    recs = []
    if score >= 0.5:
        recs = ["Urgent oncology referral", "CT scan / MRI of suspicious region",
                "Tissue biopsy as indicated", "Full cancer staging workup",
                "Genetic counselling if family history positive"]
    elif score >= 0.25:
        recs = ["Repeat tumour markers in 4–6 weeks", "Ultrasound of relevant organ",
                "Oncology consultation", "Smoking cessation programme"]
    else:
        recs = ["Routine age-appropriate cancer screening", "Annual physical examination",
                "Healthy lifestyle — no smoking, balanced diet"]

    return ScoringResult("cancer_screening", "Cancer Risk Screening", _level(score), round(score, 2),
                         findings or ["Cancer screening markers within normal range"], recs, p)


def score_respiratory(p: dict) -> ScoringResult:
    findings, flags = [], 0

    if p.get("spo2", 100) < 90:
        findings.append(f"SpO2: {p['spo2']}% — severe hypoxia, immediate oxygen required")
        flags += 3
    elif p.get("spo2", 100) < 94:
        findings.append(f"SpO2: {p['spo2']}% — low oxygen saturation")
        flags += 1

    if p.get("respiratory_rate", 0) >= 25:
        findings.append(f"Respiratory rate: {p['respiratory_rate']}/min — tachypnoea")
        flags += 2
    if p.get("temperature", 37) > 38.5:
        findings.append(f"Temperature: {p['temperature']}°C — high fever suggesting infection")
        flags += 1
    if p.get("wbc", 0) > 12:
        findings.append(f"WBC: {p['wbc']} ×10³/µL — leukocytosis, bacterial infection likely")
        flags += 1
    if p.get("crp", 0) > 50:
        findings.append(f"CRP: {p['crp']} mg/L — significant inflammation")
        flags += 1
    if p.get("cough_days", 0) > 14:
        findings.append(f"Cough duration: {p['cough_days']} days — consider atypical/TB")
        flags += 1

    score = min(flags / 6, 1.0)
    recs = []
    if score >= 0.5:
        recs = ["Chest X-ray immediately", "Sputum culture and sensitivity",
                "IV antibiotics (cover atypicals)", "Oxygen therapy to maintain SpO2 >94%",
                "Consider hospitalisation", "Blood cultures if febrile"]
    elif score >= 0.25:
        recs = ["Oral antibiotics (amoxicillin-clavulanate)", "Chest X-ray",
                "Rest, hydration, antipyretics", "Follow-up in 3 days"]
    else:
        recs = ["Symptomatic treatment", "Adequate rest and hydration", "Return if worsening"]

    return ScoringResult("respiratory", "Respiratory Infection", _level(score), round(score, 2),
                         findings or ["Respiratory parameters within acceptable range"], recs, p)


def score_cold_flu(p: dict) -> ScoringResult:
    findings, flags = [], 0

    if p.get("temperature", 37) > 39:
        findings.append(f"Temperature: {p['temperature']}°C — high fever, influenza likely")
        flags += 2
    elif p.get("temperature", 37) > 37.5:
        findings.append(f"Temperature: {p['temperature']}°C — low-grade fever")
        flags += 1

    severity_map = {"Severe": 2, "Mild": 1, "None": 0}
    for key, label in [("sore_throat", "Sore throat"), ("body_aches", "Body aches"),
                       ("runny_nose", "Nasal congestion")]:
        val = p.get(key, "None")
        if val != "None":
            findings.append(f"{label}: {val}")
            flags += severity_map.get(val, 0)

    if p.get("symptom_days", 0) > 7:
        findings.append(f"Symptoms lasting {p['symptom_days']} days — consider secondary infection")
        flags += 2

    score = min(flags / 7, 1.0)
    recs = []
    if score >= 0.5:
        recs = ["Influenza rapid antigen test", "Oseltamivir (Tamiflu) if influenza confirmed within 48h",
                "Paracetamol for fever and pain", "Isolate to prevent spread",
                "Rule out bacterial superinfection"]
    elif score >= 0.25:
        recs = ["Rest and adequate hydration", "Paracetamol / ibuprofen for symptomatic relief",
                "Honey + lemon for sore throat", "Return if fever >39°C or symptoms worsen"]
    else:
        recs = ["Symptomatic relief", "Rest and hydration", "Usually resolves in 5–7 days"]

    return ScoringResult("cold_flu", "Common Cold & Influenza", _level(score), round(score, 2),
                         findings or ["Mild viral symptoms"], recs, p)


def score_anaemia(p: dict) -> ScoringResult:
    findings, flags = [], 0
    hb = p.get("hemoglobin", 14)
    age = p.get("age", 30)

    # WHO thresholds
    hb_threshold = 12.0 if age < 15 else 13.0
    if hb < 8:
        findings.append(f"Haemoglobin: {hb} g/dL — severe anaemia")
        flags += 3
    elif hb < 10:
        findings.append(f"Haemoglobin: {hb} g/dL — moderate anaemia")
        flags += 2
    elif hb < hb_threshold:
        findings.append(f"Haemoglobin: {hb} g/dL — mild anaemia")
        flags += 1

    mcv = p.get("mcv", 90)
    if mcv < 80:
        findings.append(f"MCV: {mcv} fL — microcytic anaemia (iron deficiency or thalassaemia)")
        flags += 1
    elif mcv > 100:
        findings.append(f"MCV: {mcv} fL — macrocytic anaemia (B12/folate deficiency)")
        flags += 1

    if p.get("ferritin", 100) < 12:
        findings.append(f"Ferritin: {p['ferritin']} ng/mL — iron stores depleted")
        flags += 1
    if p.get("vitamin_b12", 500) < 200:
        findings.append(f"Vitamin B12: {p['vitamin_b12']} pg/mL — deficient")
        flags += 1

    score = min(flags / 5, 1.0)
    recs = []
    if score >= 0.5:
        recs = ["IV iron infusion or blood transfusion if Hb <7",
                "Identify and treat underlying cause (GI bleed, malabsorption)",
                "Haematology referral", "Dietary iron + B12 supplementation"]
    elif score >= 0.25:
        recs = ["Oral iron supplementation (ferrous sulphate 200 mg TDS)",
                "Vitamin B12 injections if deficient", "Iron-rich diet counselling",
                "Recheck CBC in 4 weeks"]
    else:
        recs = ["Balanced diet with iron-rich foods", "Annual CBC monitoring"]

    return ScoringResult("anaemia", "Anaemia & Nutritional Deficiency", _level(score), round(score, 2),
                         findings or ["Haematological parameters within normal range"], recs, p)


def score_gastrointestinal(p: dict) -> ScoringResult:
    findings, flags = [], 0

    if p.get("pain_severity", 0) >= 7:
        findings.append(f"Abdominal pain severity: {p['pain_severity']}/10 — severe, rule out surgical cause")
        flags += 3
    elif p.get("pain_severity", 0) >= 4:
        findings.append(f"Abdominal pain: {p['pain_severity']}/10 — moderate")
        flags += 1

    if p.get("vomiting", 0) > 5:
        findings.append(f"Vomiting: {p['vomiting']} episodes/day — risk of dehydration")
        flags += 2
    if p.get("stool_frequency", 1) > 6:
        findings.append(f"Stool frequency: {p['stool_frequency']}/day — severe diarrhoea")
        flags += 2

    if p.get("temperature", 37) > 38:
        findings.append(f"Temperature: {p['temperature']}°C — fever suggests infectious cause")
        flags += 1
    if p.get("wbc", 0) > 12:
        findings.append(f"WBC: {p['wbc']} ×10³/µL — leukocytosis")
        flags += 1
    if p.get("symptom_days", 0) > 7:
        findings.append(f"Symptoms for {p['symptom_days']} days — not self-limiting, investigate")
        flags += 1

    score = min(flags / 7, 1.0)
    recs = []
    if score >= 0.5:
        recs = ["Surgical consultation to rule out appendicitis/obstruction",
                "IV fluids for rehydration", "Stool culture and sensitivity",
                "Abdominal ultrasound / CT", "NBM (nil by mouth) until surgical cause excluded"]
    elif score >= 0.25:
        recs = ["ORS (oral rehydration salts)", "Stool culture", "Bland diet — BRAT (banana, rice, applesauce, toast)",
                "Antiemetics if needed", "Return if blood in stool or pain worsens"]
    else:
        recs = ["ORS and hydration", "Dietary rest", "Probiotics", "Usually self-limiting in 48–72 hours"]

    return ScoringResult("gastrointestinal", "Gastrointestinal Disorder", _level(score), round(score, 2),
                         findings or ["GI parameters within acceptable range"], recs, p)


def score_musculoskeletal(p: dict) -> ScoringResult:
    findings, flags = [], 0

    severity_map = {"Severe": 3, "Moderate": 2, "Mild": 1, "None": 0}
    swelling = p.get("joint_swelling", "None")
    if swelling != "None":
        findings.append(f"Joint swelling: {swelling}")
        flags += severity_map.get(swelling, 0)

    if p.get("pain_severity", 0) >= 7:
        findings.append(f"Pain severity: {p['pain_severity']}/10 — severe, limiting function")
        flags += 2
    elif p.get("pain_severity", 0) >= 4:
        findings.append(f"Pain severity: {p['pain_severity']}/10 — moderate")
        flags += 1

    if p.get("uric_acid", 0) > 7:
        findings.append(f"Uric acid: {p['uric_acid']} mg/dL — elevated, consider gout")
        flags += 2
    if p.get("crp", 0) > 10:
        findings.append(f"CRP: {p['crp']} mg/L — elevated, inflammatory arthritis possible")
        flags += 1
    if p.get("esr", 0) > 40:
        findings.append(f"ESR: {p['esr']} mm/hr — elevated sedimentation rate")
        flags += 1

    score = min(flags / 7, 1.0)
    recs = []
    if score >= 0.5:
        recs = ["Rheumatology referral", "X-ray of affected joint", "Anti-inflammatory therapy (NSAIDs)",
                "Joint aspiration if effusion present", "Uric acid lowering therapy if gout confirmed"]
    elif score >= 0.25:
        recs = ["NSAIDs (ibuprofen 400mg TDS with food)", "Rest and ice/heat application",
                "Physiotherapy referral", "Repeat inflammatory markers in 4 weeks"]
    else:
        recs = ["Paracetamol for mild pain", "Gentle exercise and physiotherapy",
                "Maintain healthy weight to reduce joint load"]

    return ScoringResult("musculoskeletal", "Musculoskeletal Disorder", _level(score), round(score, 2),
                         findings or ["Musculoskeletal parameters within normal range"], recs, p)


def score_skin_infection(p: dict) -> ScoringResult:
    findings, flags = [], 0

    severity_map = {"Severe": 3, "Moderate": 2, "Mild": 1}
    sev = p.get("severity", "Mild")
    findings.append(f"Infection severity: {sev} — area: {p.get('infection_area', 'unspecified')}")
    flags += severity_map.get(sev, 1)

    if p.get("spreading") == "Yes – rapidly":
        findings.append("Infection spreading rapidly — cellulitis or necrotising fasciitis risk")
        flags += 3
    elif p.get("spreading") == "Yes – slowly":
        findings.append("Infection spreading slowly — antibiotic treatment recommended")
        flags += 1

    if p.get("temperature", 37) > 38:
        findings.append(f"Temperature: {p['temperature']}°C — systemic infection involvement")
        flags += 2
    if p.get("wbc", 0) > 12:
        findings.append(f"WBC: {p['wbc']} ×10³/µL — systemic inflammatory response")
        flags += 1
    if p.get("duration_days", 0) > 7:
        findings.append(f"Duration: {p['duration_days']} days — not resolving, may need culture")
        flags += 1

    score = min(flags / 7, 1.0)
    recs = []
    if score >= 0.5:
        recs = ["IV antibiotics (flucloxacillin or vancomycin)", "Surgical debridement if necrotic",
                "Wound swab for culture", "Hospitalisation for IV therapy",
                "Rule out necrotising fasciitis with imaging"]
    elif score >= 0.25:
        recs = ["Oral antibiotics (flucloxacillin or co-amoxiclav)", "Wound dressing daily",
                "Keep area clean and dry", "Return immediately if spreading or fever develops"]
    else:
        recs = ["Topical antiseptic (povidone-iodine)", "Keep area clean",
                "Monitor for spreading or fever", "Review in 3 days"]

    return ScoringResult("skin_infection", "Skin Infection", _level(score), round(score, 2),
                         findings, recs, p)


# ── Main dispatcher ───────────────────────────────────────────────────────────

SCORERS = {
    "sepsis":           score_sepsis,
    "diabetes":         score_diabetes,
    "heart_attack":     score_heart_attack,
    "hypertension":     score_hypertension,
    "cancer_screening": score_cancer_screening,
    "respiratory":      score_respiratory,
    "cold_flu":         score_cold_flu,
    "anaemia":          score_anaemia,
    "gastrointestinal": score_gastrointestinal,
    "musculoskeletal":  score_musculoskeletal,
    "skin_infection":   score_skin_infection,
}


def analyse(disease_id: str, parameters: dict) -> ScoringResult:
    scorer = SCORERS.get(disease_id)
    if not scorer:
        raise ValueError(f"Unknown disease: {disease_id}")
    return scorer(parameters)


if __name__ == "__main__":
    # Quick smoke test
    result = analyse("diabetes", {
        "fasting_glucose": 140,
        "hba1c": 7.2,
        "bmi": 31,
        "age": 52,
        "family_history": "Yes",
        "cholesterol": 220,
        "systolic_bp": 135,
    })
    print(f"Disease: {result.disease_name}")
    print(f"Risk: {result.risk_level} ({result.risk_score * 100:.0f}%)")
    print("Findings:")
    for f in result.findings:
        print(f"  • {f}")
    print("Recommendations:")
    for r in result.recommendations:
        print(f"  → {r}")
        