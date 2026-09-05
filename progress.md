# AI Clinical Decision Support — Project Progress

**Project:** Virtual Junior Doctor for Under-Resourced Hospitals
**Goal:** Real-time AI that catches worsening patient conditions and suggests diagnoses
**Target:** Tier-2/Tier-3 community and rural hospitals in India
**Started:** September 2026

---

## My Background (what I already know)

| Skill | Relevance to This Project |
|---|---|
| Python | Glue for everything — pipelines, APIs, parsers, training scripts |
| Machine Learning | Early warning engine (XGBoost on vitals + lab data) |
| Deep Learning | Time-series vitals (LSTMs), medical image analysis (CNNs) |
| Generative AI | Diagnosis suggestion engine — fine-tune medical LLMs |
| Agentic AI | The "virtual junior doctor" orchestration brain |
| NLP | Extract symptoms/meds from clinical notes via NER |

---

## System Architecture (3 Layers)

```
LAYER 1 — Data Ingestion
  EHR Records (FHIR R4) → Live Vitals (ECG, SpO2, BP) → Lab + Imaging (DICOM) → Clinical Notes (NLP)

LAYER 2 — AI Core
  Multimodal Fusion → Early Warning Engine → Diagnosis Engine → XAI Layer
  ↕
  Federated Learning Coordinator (weights only, never patient data)

LAYER 3 — Clinical Output
  Alert Dashboard → Diagnosis Suggestions → Reasoning Trace → Doctor Feedback (HITL)

COMPLIANCE WRAPPER
  HIPAA / DISHA · Audit Trails · Model Versioning · Doctor Override Always Available
```

---

## Tech Stack

| Technology | Purpose | Library/Tool |
|---|---|---|
| HL7 / FHIR R4 | Universal hospital data standard | `fhir.resources` (Python) |
| Multimodal AI | Text + image + time-series fusion | PyTorch, HuggingFace |
| Federated Learning | Train across hospitals without sharing patient data | `flwr` (Flower) |
| Explainable AI (XAI) | Show doctors WHY the AI flagged something | SHAP, LIME |
| NLP / NER | Extract clinical entities from doctor notes | ClinicalBERT, BioBERT |
| Early Warning | Detect deterioration from structured vitals | XGBoost, LightGBM |
| Orchestration | Agentic routing between analysers | LangGraph / AutoGen |
| API | Backend for hospital integration | FastAPI |

---

## Key Concepts Learned

### HL7 / FHIR

- **FHIR** = Fast Healthcare Interoperability Resources — the universal JSON format for health data
- **HL7** = the standards body that created FHIR (like ISO for healthcare)
- **Resource** = a standard JSON object representing one piece of health data
- **Bundle** = a container holding many Resources together — this is what hospitals send you

**Critical FHIR Resources for this project:**

| Resource | What It Holds |
|---|---|
| `Patient` | Name, DOB, ID, gender |
| `Observation` | Any measurement — vitals, labs (uses LOINC codes) |
| `DiagnosticReport` | CBC, X-ray, ECG reports |
| `Condition` | ICD-10 diagnoses |
| `MedicationRequest` | Prescriptions |
| `Encounter` | A hospital visit — ties everything together |
| `AllergyIntolerance` | Drug/food allergies |

**LOINC Codes** — the universal language for lab/vital names (same code in every hospital worldwide):

```python
CLINICAL_LOINC_MAP = {
    "8480-6":  "systolic_bp",
    "8462-4":  "diastolic_bp",
    "8867-4":  "heart_rate",
    "9279-1":  "respiratory_rate",
    "8310-5":  "body_temperature",
    "59408-5": "spo2",
    "2339-0":  "glucose",
    "2160-0":  "creatinine",      # kidney function
    "6690-2":  "wbc",             # white blood cells — infection marker
    "32693-4": "lactate",         # CRITICAL sepsis marker
    "718-7":   "hemoglobin",
    "4548-4":  "hba1c",
}
```

**Key FHIR API Endpoint:**
```
GET /Patient/{id}/$everything   →  returns ALL patient data in one Bundle
```

**Free test server for development:**
```
https://hapi.fhir.org/baseR4
```

**Core FHIR Python code pattern:**
```python
from fhir.resources.bundle import Bundle
from fhir.resources.observation import Observation

bundle = Bundle.parse_raw(response.text)

for entry in bundle.entry:
    if entry.resource.resource_type == "Observation":
        loinc  = entry.resource.code.coding[0].code
        value  = entry.resource.valueQuantity.value
        unit   = entry.resource.valueQuantity.unit
```

### Federated Learning

- Hospitals won't share patient data due to regulations (India's DISHA, HIPAA)
- Each hospital trains a LOCAL model on its own data
- Only model **weights** are sent to a central server — NEVER patient records
- Central server aggregates weights using **FedAvg** algorithm
- Updated global model is sent back to all hospitals
- Library: **Flower (flwr)** — Python-native, purpose-built

### Explainable AI (XAI)

Why doctors won't trust black-box AI:
- "Sepsis risk: HIGH" alone is useless
- Doctors need: *"Sepsis risk HIGH — because lactate 4.2 mmol/L (↑3×), HR 118 bpm for 6h, Temp 39.4°C"*

Tools:
- **SHAP** — for structured ML models (XGBoost, Random Forest)
- **LIME** — local explanations for any model
- **Attention visualization** — for transformer/LLM-based components

### Multimodal AI

Three data types to fuse:
1. **Structured** — vitals numbers, lab values → tabular ML (XGBoost)
2. **Text** — clinical notes → NLP (ClinicalBERT / BioBERT)
3. **Image** — chest X-rays (DICOM), ECG traces → CNN (CheXNet / DenseNet)

Architecture approach: **Late fusion** — separate encoders per modality, concatenate embeddings, joint classifier.
Start with structured + text. Add images in Phase 3.

---

## Feature Engineering Pattern (FHIR → ML)

```python
def fhir_bundle_to_feature_vector(bundle):
    features = {v: -1.0 for v in CLINICAL_LOINC_MAP.values()}  # -1 = not measured

    for entry in bundle.entry:
        if entry.resource.resource_type != "Observation":
            continue
        obs   = entry.resource
        loinc = obs.code.coding[0].code
        if loinc in CLINICAL_LOINC_MAP and obs.valueQuantity:
            features[CLINICAL_LOINC_MAP[loinc]] = float(obs.valueQuantity.value)

    # Derived feature — pulse pressure (narrow = sepsis warning)
    if features["systolic_bp"] > 0 and features["diastolic_bp"] > 0:
        features["pulse_pressure"] = features["systolic_bp"] - features["diastolic_bp"]

    return features
```

**Handling missing data** — rural hospitals often have incomplete records:
```python
completeness = available_critical_features / total_critical_features
if completeness < 0.4:
    return {"confidence": "insufficient_data", "message": "Recommend manual assessment"}
```

---

## Datasets

| Dataset | Contents | Access |
|---|---|---|
| **MIMIC-IV** | Real ICU vitals, labs, notes, prescriptions | physionet.org — free with training course |
| **CheXpert** | 224,000 chest X-rays with labels | Stanford — free for research |
| **n2c2 NLP** | De-identified clinical notes for NLP tasks | n2c2.dbmi.pitt.edu |
| **PhysioNet ECG** | ECG time-series data | physionet.org |

**Start with MIMIC-IV.** It is the gold standard dataset for clinical AI research.

---

## 6-Phase Build Roadmap

### Phase 0 — Environment & Repository Setup (Week 1)

#### GitHub Repository Structure
```
clinical-ai-decision-support/
│
├── README.md                        # Project overview, setup instructions
├── progress.md                      # This file — learning journal
├── requirements.txt                 # All pip dependencies
├── .env.example                     # Template for API keys (never commit .env)
├── .gitignore                       # Exclude .env, data/, __pycache__, models/
│
├── data/
│   ├── raw/                         # Raw downloaded datasets — never commit
│   ├── processed/                   # Cleaned, feature-engineered data
│   └── samples/                     # Small safe samples for testing (no PHI)
│
├── notebooks/
│   ├── 01_fhir_exploration.ipynb    # Phase 1 — HAPI FHIR connection & parsing
│   ├── 02_mimic_eda.ipynb           # Phase 1 — MIMIC-IV exploratory analysis
│   ├── 03_sepsis_model.ipynb        # Phase 1 — XGBoost training + SHAP
│   ├── 04_nlp_pipeline.ipynb        # Phase 2 — ClinicalBERT NER
│   └── 05_multimodal_fusion.ipynb   # Phase 3 — Fusing modalities
│
├── src/
│   ├── __init__.py
│   ├── fhir/
│   │   ├── __init__.py
│   │   ├── parser.py                # Bundle → resource extraction
│   │   ├── feature_builder.py       # LOINC → feature vector
│   │   └── client.py                # FHIR server REST client
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── early_warning.py         # XGBoost sepsis/deterioration model
│   │   ├── nlp_pipeline.py          # ClinicalBERT NER
│   │   ├── image_analyser.py        # CheXNet chest X-ray model
│   │   └── multimodal_fusion.py     # Late fusion combiner
│   │
│   ├── explainability/
│   │   ├── __init__.py
│   │   └── shap_explainer.py        # SHAP explanations + natural language summary
│   │
│   ├── federated/
│   │   ├── __init__.py
│   │   ├── client_node.py           # Hospital-side Flower client
│   │   └── server.py                # Central aggregation server (FedAvg)
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   └── virtual_doctor.py        # LangGraph orchestration agent
│   │
│   └── api/
│       ├── __init__.py
│       ├── main.py                  # FastAPI app entry point
│       ├── routes.py                # Endpoints — /analyse, /alert, /feedback
│       └── schemas.py               # Pydantic request/response models
│
├── tests/
│   ├── test_fhir_parser.py
│   ├── test_feature_builder.py
│   └── test_early_warning.py
│
└── docs/
    ├── architecture.md              # System design decisions
    ├── fhir_guide.md                # FHIR concepts reference
    └── compliance_notes.md          # DISHA / HIPAA notes
```

#### Phase 0 Checklist
- [ ] Create GitHub repo — name: `clinical-ai-decision-support`
- [ ] Set repo to **Private** (patient data concepts, not for public yet)
- [ ] Create folder structure above using `mkdir -p` commands
- [ ] Write `.gitignore` — exclude `data/raw/`, `.env`, `*.pkl`, `models/`
- [ ] Write `requirements.txt` with all libraries (see Quick Reference below)
- [ ] Set up Python virtual environment: `python -m venv venv`
- [ ] Activate and install: `pip install -r requirements.txt`
- [ ] Create `.env.example` with placeholders for FHIR server URL, API keys
- [ ] Write initial `README.md` with project description and setup steps
- [ ] Make first commit: `git commit -m "feat: initial project scaffold"`
- [ ] Test HAPI FHIR connection — fetch one patient Bundle successfully
- **Deliverable:** Clean repo, working environment, first FHIR query running

#### Phase 0 Setup Commands
```bash
# 1. Create and enter project folder
mkdir clinical-ai-decision-support && cd clinical-ai-decision-support
git init

# 2. Create full folder structure
mkdir -p data/{raw,processed,samples}
mkdir -p notebooks
mkdir -p src/{fhir,models,explainability,federated,agent,api}
mkdir -p tests docs

# 3. Create __init__.py files
touch src/__init__.py src/fhir/__init__.py src/models/__init__.py
touch src/explainability/__init__.py src/federated/__init__.py
touch src/agent/__init__.py src/api/__init__.py

# 4. Python virtual environment
python -m venv venv
source venv/bin/activate          # Mac/Linux
# venv\Scripts\activate           # Windows

# 5. Install all dependencies
pip install -r requirements.txt

# 6. Verify FHIR connection
python -c "import requests; r = requests.get('https://hapi.fhir.org/baseR4/Patient?_count=1'); print(r.status_code)"
# Should print: 200
```

#### .gitignore (copy this exactly)
```
# Environment
.env
venv/
__pycache__/
*.pyc
*.pyo

# Data — never commit patient data
data/raw/
data/processed/
*.csv
*.parquet

# Models — too large for git
models/
*.pkl
*.pt
*.h5

# Notebooks checkpoints
.ipynb_checkpoints/

# IDE
.vscode/
.idea/
```

---

### Phase 1 — Sepsis Early Warning Model (Month 1–2)
- [ ] Get MIMIC-IV access (complete PhysioNet training)
- [ ] Build FHIR parser and LOINC feature extractor
- [ ] Train XGBoost sepsis model on vitals + labs
- [ ] Add SHAP explanations
- [ ] Connect to HAPI FHIR test server
- **Deliverable:** Working sepsis risk score with explanations

### Phase 2 — NLP Pipeline (Month 3)
- [ ] Set up ClinicalBERT / BioBERT
- [ ] NER on clinical notes — extract symptoms, meds, diagnoses
- [ ] Map extracted entities to SNOMED-CT / ICD-10 codes
- [ ] Train on n2c2 shared task datasets
- **Deliverable:** Structured data extracted from free-text notes

### Phase 3 — Multimodal Fusion (Month 4–5)
- [ ] Add CheXNet (DenseNet) for chest X-ray analysis
- [ ] Late fusion — combine structured + NLP + image encoders
- [ ] Joint risk classifier
- **Deliverable:** Multimodal patient risk score

### Phase 4 — Federated Learning (Month 6)
- [ ] Install Flower (`pip install flwr`)
- [ ] Simulate 3–5 hospital nodes using partitioned MIMIC-IV
- [ ] Implement FedAvg aggregation
- [ ] Test privacy — confirm no patient data leaves nodes
- **Deliverable:** Model that trains across hospitals without sharing data

### Phase 5 — Agentic System (Month 7–8)
- [ ] Build orchestration layer with LangGraph or AutoGen
- [ ] Agent routes each patient to appropriate analyser
- [ ] Compose final clinical summary (LLM-generated, grounded in data)
- [ ] Implement HITL — doctor feedback loop
- **Deliverable:** Full virtual junior doctor agent

### Phase 6 — API + Dashboard (Month 9)
- [ ] FastAPI backend with FHIR-compliant ingestion endpoint
- [ ] Streamlit or React doctor dashboard
- [ ] Alert system — real-time notifications for high-risk patients
- [ ] Audit logging for regulatory compliance
- **Deliverable:** Industry-ready deployable system

---

## Building Doctor Trust — Critical Design Rules

1. **Never autonomous** — AI suggests, doctor decides. Always.
2. **Show your work** — every suggestion references actual patient values with exact numbers.
3. **Calibrated confidence** — if model says 80% risk, be right 80% of the time. Use Platt scaling.
4. **Graceful uncertainty** — "Insufficient data — recommend specialist review" is more trustworthy than a wrong confident answer.
5. **Doctor override always available** — one click to dismiss any suggestion.
6. **Audit trail** — every AI suggestion, doctor response, and patient outcome is logged.

---

## Medical Ontologies to Know

| Ontology | What It Is | Used For |
|---|---|---|
| **LOINC** | Universal codes for lab tests and vitals | Inside FHIR Observation resources |
| **SNOMED-CT** | Clinical terminology (symptoms, findings) | NLP entity linking |
| **ICD-10** | Disease classification codes | Condition resources, billing |
| **RxNorm** | Drug terminology | MedicationRequest resources |

---

## Regulatory Compliance (India + International)

| Regulation | Scope | Key Requirement |
|---|---|---|
| **DISHA** (Digital Information Security in Healthcare Act) | India | Patient data stays in India; consent required |
| **HIPAA** | USA (if internationalising) | Data encryption, access logs |
| **MDR** (Medical Device Regulation) | EU | AI-as-medical-device approval |

For this project: implement audit logs, encryption at rest and in transit, and patient consent tracking from Day 1. Retrofitting compliance is extremely hard.

---

## Session Notes

### Session 1 — Project Foundation
- Mapped existing Python/ML/DL/GenAI/AgenticAI/NLP skills to project components
- Understood the 3-layer architecture (ingestion → AI core → clinical output)
- Learned HL7/FHIR R4 — Resources, Bundles, LOINC codes
- Understood the `$everything` API endpoint pattern
- Wrote FHIR parser and feature engineering code
- Understood why federated learning is non-negotiable for hospital data
- Understood XAI as the trust mechanism with doctors

### Next Session Goals
- [ ] Set up HAPI FHIR test server connection in Python
- [ ] Write and test `fhir_bundle_to_feature_vector()` on real HAPI data
- [ ] Begin MIMIC-IV credentialing process
- [ ] Understand how XGBoost training works on clinical tabular data

---

## Quick Reference — Key Libraries

```bash
pip install fhir.resources      # FHIR resource parsing
pip install flwr                # Federated learning (Flower)
pip install shap                # Explainable AI
pip install xgboost             # Early warning ML model
pip install transformers        # ClinicalBERT, BioBERT
pip install langchain langgraph # Agentic orchestration
pip install fastapi uvicorn     # API backend
```

---

## Resources & Links

- HAPI FHIR Test Server: https://hapi.fhir.org/baseR4
- MIMIC-IV Dataset: https://physionet.org/content/mimiciv/
- FHIR R4 Spec: https://hl7.org/fhir/R4/
- LOINC Code Search: https://loinc.org/search/
- Flower Federated Learning Docs: https://flower.dev/docs/
- ClinicalBERT on HuggingFace: https://huggingface.co/emilyalsentzer/Bio_ClinicalBERT
- n2c2 NLP Challenges: https://n2c2.dbmi.pitt.edu/
- CheXNet Paper (Stanford): https://arxiv.org/abs/1711.05225

---

*Update this file after every learning session. Track what you've built, what you've understood, and what questions remain.*
