"""
Disease Registry — single source of truth for all supported conditions.
Each disease defines:
  - parameters: what to collect from the patient
  - thresholds: normal ranges for each parameter
  - scoring: clinical rule-based risk scoring function
"""

from dataclasses import dataclass, field

# ── Parameter descriptor ─────────────────────────────────────────────────────

@dataclass
class Parameter:
    key: str          # internal name used in code
    label: str        # human-readable label shown in UI / report
    unit: str         # e.g. "mmHg", "mg/dL", "%"
    normal_min: float | None
    normal_max: float | None
    required: bool = True
    input_type: str = "number"   # "number" | "select" | "boolean"
    options: list[str] = field(default_factory=list)  # for select inputs


# ── Disease definition ────────────────────────────────────────────────────────

@dataclass
class DiseaseConfig:
    id: str
    name: str
    description: str
    parameters: list[Parameter]
    icd10_code: str   # for the PDF report


# ── 9 Disease Configs ─────────────────────────────────────────────────────────

DISEASES: dict[str, DiseaseConfig] = {

    "sepsis": DiseaseConfig(
        id="sepsis",
        name="Sepsis / Systemic Infection",
        description="Life-threatening organ dysfunction caused by infection",
        icd10_code="A41.9",
        parameters=[
            Parameter("heart_rate",       "Heart Rate",          "bpm",   60,   100),
            Parameter("respiratory_rate", "Respiratory Rate",    "/min",  12,   20),
            Parameter("systolic_bp",      "Systolic BP",         "mmHg",  90,   140),
            Parameter("temperature",      "Body Temperature",    "°C",    36.1, 37.2),
            Parameter("spo2",             "SpO2",                "%",     95,   100),
            Parameter("wbc",              "WBC Count",           "×10³/µL", 4.0, 11.0),
            Parameter("lactate",          "Serum Lactate",       "mmol/L", 0.5, 1.9),
            Parameter("creatinine",       "Creatinine",          "mg/dL",  0.6, 1.2),
        ],
    ),

    "diabetes": DiseaseConfig(
        id="diabetes",
        name="Diabetes Mellitus",
        description="Chronic metabolic disorder affecting blood glucose regulation",
        icd10_code="E11.9",
        parameters=[
            Parameter("fasting_glucose",  "Fasting Blood Glucose", "mg/dL", 70,  99),
            Parameter("hba1c",            "HbA1c",                 "%",     4.0, 5.6),
            Parameter("bmi",              "BMI",                   "kg/m²", 18.5, 24.9),
            Parameter("age",              "Age",                   "years", None, None),
            Parameter("systolic_bp",      "Systolic BP",           "mmHg",  90,  120),
            Parameter("cholesterol",      "Total Cholesterol",     "mg/dL", 0,   200),
            Parameter("family_history",   "Family History of Diabetes", "",  None, None,
                      input_type="select", options=["Yes", "No"]),
        ],
    ),

    "heart_attack": DiseaseConfig(
        id="heart_attack",
        name="Acute Myocardial Infarction (Heart Attack)",
        description="Blockage of blood supply to the heart muscle",
        icd10_code="I21.9",
        parameters=[
            Parameter("troponin",         "Troponin I",           "ng/mL",  0,    0.04),
            Parameter("heart_rate",       "Heart Rate",           "bpm",    60,   100),
            Parameter("systolic_bp",      "Systolic BP",          "mmHg",   90,   140),
            Parameter("chest_pain",       "Chest Pain Type",      "",       None, None,
                      input_type="select",
                      options=["None", "Typical Angina", "Atypical Angina", "Non-Anginal"]),
            Parameter("age",              "Age",                  "years",  None, None),
            Parameter("ecg_changes",      "ECG ST Changes",       "",       None, None,
                      input_type="select", options=["Normal", "ST Elevation", "ST Depression"]),
            Parameter("smoking",          "Smoking Status",       "",       None, None,
                      input_type="select", options=["Never", "Former", "Current"]),
        ],
    ),

    "hypertension": DiseaseConfig(
        id="hypertension",
        name="Hypertension (High Blood Pressure)",
        description="Persistently elevated arterial blood pressure",
        icd10_code="I10",
        parameters=[
            Parameter("systolic_bp",      "Systolic BP",          "mmHg",  90,   120),
            Parameter("diastolic_bp",     "Diastolic BP",         "mmHg",  60,   80),
            Parameter("heart_rate",       "Heart Rate",           "bpm",   60,   100),
            Parameter("age",              "Age",                  "years", None, None),
            Parameter("bmi",              "BMI",                  "kg/m²", 18.5, 24.9),
            Parameter("sodium",           "Serum Sodium",         "mEq/L", 136,  145),
            Parameter("creatinine",       "Creatinine (Kidney)",  "mg/dL", 0.6,  1.2),
        ],
    ),

    "cancer_screening": DiseaseConfig(
        id="cancer_screening",
        name="Cancer Risk Screening",
        description="Multi-marker early cancer risk assessment",
        icd10_code="Z12.9",
        parameters=[
            Parameter("age",              "Age",                  "years", None, None),
            Parameter("psa",              "PSA (Prostate)",       "ng/mL", 0,    4.0,  required=False),
            Parameter("cea",              "CEA (Colon/Lung)",     "ng/mL", 0,    2.5,  required=False),
            Parameter("ca125",            "CA-125 (Ovarian)",     "U/mL",  0,    35,   required=False),
            Parameter("ca199",            "CA 19-9 (Pancreatic)", "U/mL",  0,    37,   required=False),
            Parameter("smoking",          "Smoking Status",       "",      None, None,
                      input_type="select", options=["Never", "Former", "Current"]),
            Parameter("family_history",   "Family History of Cancer", "", None, None,
                      input_type="select", options=["Yes", "No"]),
        ],
    ),

    "respiratory": DiseaseConfig(
        id="respiratory",
        name="Respiratory Infection",
        description="Lower respiratory tract infections including pneumonia, bronchitis",
        icd10_code="J22",
        parameters=[
            Parameter("respiratory_rate", "Respiratory Rate",     "/min",  12,   20),
            Parameter("spo2",             "SpO2",                 "%",     95,   100),
            Parameter("temperature",      "Body Temperature",     "°C",    36.1, 37.2),
            Parameter("heart_rate",       "Heart Rate",           "bpm",   60,   100),
            Parameter("wbc",              "WBC Count",            "×10³/µL", 4.0, 11.0),
            Parameter("cough_days",       "Cough Duration",       "days",  0,    7),
            Parameter("crp",              "CRP (Inflammation)",   "mg/L",  0,    5.0),
        ],
    ),

    "cold_flu": DiseaseConfig(
        id="cold_flu",
        name="Common Cold & Influenza",
        description="Upper respiratory viral infections",
        icd10_code="J11.1",
        parameters=[
            Parameter("temperature",      "Body Temperature",     "°C",    36.1, 37.2),
            Parameter("heart_rate",       "Heart Rate",           "bpm",   60,   100),
            Parameter("symptom_days",     "Symptom Duration",     "days",  0,    3),
            Parameter("sore_throat",      "Sore Throat",          "",      None, None,
                      input_type="select", options=["None", "Mild", "Severe"]),
            Parameter("body_aches",       "Body Aches",           "",      None, None,
                      input_type="select", options=["None", "Mild", "Severe"]),
            Parameter("runny_nose",       "Nasal Congestion",     "",      None, None,
                      input_type="select", options=["None", "Mild", "Severe"]),
        ],
    ),

    "anaemia": DiseaseConfig(
        id="anaemia",
        name="Anaemia & Nutritional Deficiency",
        description="Low haemoglobin or nutritional deficiencies",
        icd10_code="D64.9",
        parameters=[
            Parameter("hemoglobin",       "Haemoglobin",          "g/dL",  12.0, 17.5),
            Parameter("hematocrit",       "Haematocrit",          "%",     36,   52),
            Parameter("mcv",              "MCV (Cell Volume)",    "fL",    80,   100),
            Parameter("iron",             "Serum Iron",           "µg/dL", 60,   170),
            Parameter("ferritin",         "Ferritin",             "ng/mL", 12,   300),
            Parameter("vitamin_b12",      "Vitamin B12",          "pg/mL", 200,  900,  required=False),
            Parameter("age",              "Age",                  "years", None, None),
        ],
    ),

    "gastrointestinal": DiseaseConfig(
        id="gastrointestinal",
        name="Gastrointestinal Disorders",
        description="GI infections, IBS, gastritis, and related conditions",
        icd10_code="K59.9",
        parameters=[
            Parameter("temperature",      "Body Temperature",     "°C",    36.1, 37.2),
            Parameter("heart_rate",       "Heart Rate",           "bpm",   60,   100),
            Parameter("wbc",              "WBC Count",            "×10³/µL", 4.0, 11.0),
            Parameter("symptom_days",     "Symptom Duration",     "days",  0,    2),
            Parameter("pain_severity",    "Abdominal Pain (0–10)","score", 0,    3,
                      input_type="number"),
            Parameter("vomiting",         "Vomiting Episodes/Day","count", 0,    1),
            Parameter("stool_frequency",  "Stool Frequency/Day",  "count", 1,    3),
        ],
    ),

    "musculoskeletal": DiseaseConfig(
        id="musculoskeletal",
        name="Musculoskeletal Disorders",
        description="Joint pain, arthritis, muscle and bone conditions",
        icd10_code="M79.3",
        parameters=[
            Parameter("pain_severity",    "Pain Severity (0–10)", "score", 0,    3),
            Parameter("joint_swelling",   "Joint Swelling",       "",      None, None,
                      input_type="select", options=["None", "Mild", "Moderate", "Severe"]),
            Parameter("esr",              "ESR (Inflammation)",   "mm/hr", 0,    20),
            Parameter("crp",              "CRP",                  "mg/L",  0,    5.0),
            Parameter("uric_acid",        "Uric Acid",            "mg/dL", 2.4,  6.0),
            Parameter("age",              "Age",                  "years", None, None),
        ],
    ),

    "skin_infection": DiseaseConfig(
        id="skin_infection",
        name="Skin Infections & Dermatitis",
        description="Bacterial, fungal, and inflammatory skin conditions",
        icd10_code="L08.9",
        parameters=[
            Parameter("temperature",      "Body Temperature",     "°C",    36.1, 37.2),
            Parameter("wbc",              "WBC Count",            "×10³/µL", 4.0, 11.0),
            Parameter("infection_area",   "Affected Area",        "",      None, None,
                      input_type="select",
                      options=["Face", "Scalp", "Trunk", "Arms", "Legs", "Feet"]),
            Parameter("severity",         "Infection Severity",   "",      None, None,
                      input_type="select", options=["Mild", "Moderate", "Severe"]),
            Parameter("duration_days",    "Duration",             "days",  0,    3),
            Parameter("spreading",        "Is it Spreading?",     "",      None, None,
                      input_type="select", options=["No", "Yes – slowly", "Yes – rapidly"]),
        ],
    ),
}


def get_disease(disease_id: str) -> DiseaseConfig | None:
    return DISEASES.get(disease_id)


def list_diseases() -> list[dict]:
    """Return summary list for dropdowns / UI."""
    return [
        {"id": d.id, "name": d.name, "description": d.description}
        for d in DISEASES.values()
    ]
