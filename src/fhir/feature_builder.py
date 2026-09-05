"""
Feature builder — converts FHIR Observations into ML-ready feature vectors.

Why this exists:
  ML models need fixed-size numeric input. FHIR gives us variable-length
  lists of observations with different LOINC codes each time.
  This module bridges that gap using LOINC codes as column names.

Learning note:
  Think of this like a spreadsheet. Each row is a patient.
  Each column is one clinical measurement (systolic BP, heart rate, etc).
  If a patient doesn't have a measurement, that cell is -1.0 (not 0 —
  because 0 is a valid value for some measurements like pain score).

Sepsis early warning — the critical features:
  Sepsis is a life-threatening response to infection. The clinical criteria
  (SOFA score) use these measurements:
    - Respiratory rate > 22 breaths/min
    - Systolic BP < 100 mmHg
    - GCS (consciousness) altered
    - Lactate > 2 mmol/L  ← single strongest predictor
    - WBC abnormal (too high OR too low)
    - Creatinine elevated (kidney failing)
    - Bilirubin elevated (liver failing)
"""


# LOINC code → feature name mapping
# These are the measurements our sepsis model will use
# Source: SOFA score + qSOFA + Sepsis-3 criteria
LOINC_FEATURE_MAP = {
    # --- Vital signs ---
    "8480-6":  "systolic_bp",        # mmHg — qSOFA criterion: <100 = 1 point
    "8462-4":  "diastolic_bp",       # mmHg
    "8867-4":  "heart_rate",         # bpm — tachycardia = infection response
    "9279-1":  "respiratory_rate",   # breaths/min — qSOFA criterion: >22 = 1 point
    "8310-5":  "body_temperature",   # Celsius — fever OR hypothermia = sepsis sign
    "59408-5": "spo2",               # % oxygen saturation — <94% = concerning

    # --- Critical lab markers ---
    "32693-4": "lactate",            # mmol/L — THE key sepsis marker. >2 = sepsis, >4 = septic shock
    "6690-2":  "wbc",                # 10^3/uL — infection marker (high OR low is bad)
    "2160-0":  "creatinine",         # mg/dL — kidney function. Rising = organ failure
    "1742-6":  "alt",                # U/L — liver function
    "1920-8":  "ast",                # U/L — liver function (also cardiac marker)
    "718-7":   "hemoglobin",         # g/dL — anaemia weakens immune response
    "777-3":   "platelet_count",     # 10^3/uL — low platelets = DIC (dangerous clotting)
    "2324-2":  "ggt",                # U/L — liver/bile duct marker
    "2339-0":  "glucose",            # mg/dL — stress hyperglycaemia common in sepsis
    "2823-3":  "potassium",          # mEq/L — electrolyte. Abnormal = kidney/heart risk
    "2951-2":  "sodium",             # mEq/L — electrolyte balance
    "4548-4":  "hba1c",              # % — diabetes marker (background condition)
    "1975-2":  "bilirubin_total",    # mg/dL — SOFA criterion: liver dysfunction
    "2028-9":  "co2",                # mEq/L — acid-base balance. Low = metabolic acidosis
}

# Features used by the qSOFA bedside score
# qSOFA = quick SOFA — can be calculated without lab tests
# Score 2+ = high risk of sepsis
QSOFA_FEATURES = ["respiratory_rate", "systolic_bp"]

# Features that require lab tests (SOFA score)
SOFA_LAB_FEATURES = ["lactate", "creatinine", "bilirubin_total", "platelet_count"]

# All critical features — if <40% present, model should abstain
CRITICAL_FEATURES = QSOFA_FEATURES + SOFA_LAB_FEATURES + ["heart_rate", "wbc"]


def build_feature_vector(observations: list[dict]) -> dict:
    """
    Convert a list of parsed Observations into a flat feature dict.

    This is the core function — called every time a patient is analysed.

    Args:
        observations: List of observation dicts from parser.parse_observations()

    Returns:
        Dict mapping feature names to numeric values.
        Missing features = -1.0 (sentinel value, not zero)
    """
    # Start with all features set to -1.0 (= not measured)
    features = {name: -1.0 for name in LOINC_FEATURE_MAP.values()}

    for obs in observations:
        loinc = obs.get("loinc_code", "")

        if loinc not in LOINC_FEATURE_MAP:
            continue  # measurement we don't use — skip it

        value = obs.get("value")
        if value is None or not isinstance(value, (int, float)):
            continue  # non-numeric value — skip it

        feature_name = LOINC_FEATURE_MAP[loinc]
        features[feature_name] = float(value)

    # --- Derived features ---
    # These are calculated from raw values and add clinical signal

    # Pulse pressure = systolic - diastolic
    # Narrow pulse pressure (<25 mmHg) is a sepsis warning sign
    if features["systolic_bp"] > 0 and features["diastolic_bp"] > 0:
        features["pulse_pressure"] = (
            features["systolic_bp"] - features["diastolic_bp"]
        )
    else:
        features["pulse_pressure"] = -1.0

    # Mean Arterial Pressure (MAP) = diastolic + (pulse_pressure / 3)
    # MAP < 65 mmHg = septic shock threshold (critical!)
    if features["pulse_pressure"] > 0:
        features["map"] = (
            features["diastolic_bp"] + (features["pulse_pressure"] / 3)
        )
    else:
        features["map"] = -1.0

    # AST/ALT ratio — >2 suggests alcoholic liver disease or severe hepatitis
    if features["alt"] > 0 and features["ast"] > 0:
        features["ast_alt_ratio"] = features["ast"] / features["alt"]
    else:
        features["ast_alt_ratio"] = -1.0

    return features


def assess_data_completeness(features: dict) -> dict:
    """
    Check how complete the feature vector is.

    This is how your AI knows when to be humble.
    A model trained on 20 features shouldn't make predictions
    when only 2 features are available.

    Args:
        features: Feature dict from build_feature_vector()

    Returns:
        Dict with completeness score and confidence level
    """
    available = sum(
        1 for f in CRITICAL_FEATURES if features.get(f, -1.0) != -1.0
    )
    completeness = available / len(CRITICAL_FEATURES)

    # Determine confidence tier
    if completeness >= 0.8:
        confidence = "high"
        message = "Sufficient data for reliable risk assessment"
    elif completeness >= 0.4:
        confidence = "moderate"
        message = "Partial data — interpret risk score with caution"
    else:
        confidence = "insufficient"
        message = "Too few measurements — recommend manual clinical assessment"

    # Check if qSOFA can be calculated (needs only bedside vitals)
    qsofa_available = all(
        features.get(f, -1.0) != -1.0 for f in QSOFA_FEATURES
    )

    return {
        "completeness_score": round(completeness, 2),
        "available_critical": available,
        "total_critical": len(CRITICAL_FEATURES),
        "confidence": confidence,
        "message": message,
        "qsofa_calculable": qsofa_available,
    }


def calculate_qsofa(features: dict) -> dict:
    """
    Calculate the qSOFA bedside sepsis screening score.

    qSOFA (quick Sequential Organ Failure Assessment) is a clinical
    scoring tool that needs only 3 bedside measurements — no lab tests.
    Score of 2+ identifies patients at high risk of sepsis.

    Criteria:
      +1 if respiratory rate >= 22 breaths/min
      +1 if systolic BP <= 100 mmHg
      (third criterion is altered mentation — needs clinical observation)

    Args:
        features: Feature dict from build_feature_vector()

    Returns:
        Dict with qSOFA score and component breakdown
    """
    score = 0
    components = {}

    rr = features.get("respiratory_rate", -1.0)
    if rr != -1.0:
        rr_positive = rr >= 22
        components["respiratory_rate"] = {
            "value": rr,
            "threshold": ">=22",
            "positive": rr_positive,
            "points": 1 if rr_positive else 0,
        }
        score += 1 if rr_positive else 0

    sbp = features.get("systolic_bp", -1.0)
    if sbp != -1.0:
        sbp_positive = sbp <= 100
        components["systolic_bp"] = {
            "value": sbp,
            "threshold": "<=100",
            "positive": sbp_positive,
            "points": 1 if sbp_positive else 0,
        }
        score += 1 if sbp_positive else 0

    return {
        "qsofa_score": score,
        "max_calculable": len(components),
        "high_risk": score >= 2,
        "components": components,
        "interpretation": (
            "HIGH RISK — initiate sepsis protocol" if score >= 2
            else "Lower risk — continue monitoring"
        ),
    }


def build_full_assessment(observations: list[dict]) -> dict:
    """
    Run the complete feature pipeline on a list of observations.

    This is the single function your AI agent will call.
    It returns everything needed to make a risk prediction.

    Args:
        observations: From parser.parse_observations()

    Returns:
        Complete assessment dict ready for the ML model
    """
    features = build_feature_vector(observations)
    completeness = assess_data_completeness(features)
    qsofa = calculate_qsofa(features)

    return {
        "features": features,
        "completeness": completeness,
        "qsofa": qsofa,
    }
