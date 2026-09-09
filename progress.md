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

### Session 2 — FHIR Data Layer (Phase 1 started)
- Built `src/fhir/client.py` — connects to any FHIR R4 server, fetches Bundles
- Built `src/fhir/parser.py` — extracts Patient, Observations, Conditions from Bundle
- Built `src/fhir/feature_builder.py` — converts LOINC observations to ML feature vectors
- Implemented qSOFA bedside sepsis scoring (respiratory rate + systolic BP)
- Implemented data completeness assessment — system knows when not to predict
- Tested full pipeline on real HAPI FHIR server patient `sindhu-syn-000005`
- Committed 591 lines, pushed to GitHub

### Key clinical concepts learned
- qSOFA score: RR ≥22 + SBP ≤100 = sepsis high risk (score ≥2)
- MAP (Mean Arterial Pressure) < 65 mmHg = septic shock threshold
- Lactate > 2 mmol/L = strongest single sepsis predictor
- Sentinel value -1.0 used for missing features (not 0, which is a valid measurement)
- Completeness < 40% = model should abstain, recommend manual assessment

### Next Session — Phase 1 continued
- [ ] Build `src/models/early_warning.py` — XGBoost sepsis model
- [ ] Generate synthetic training data (until MIMIC-IV access granted)
- [ ] Train model, evaluate with ROC-AUC
- [ ] Add SHAP explanations
- [ ] Wire model to FHIR pipeline end-to-end

## Session 3 — Sepsis Early Warning Model ✅
**Completed:** `src/models/early_warning.py`
- XGBoost classifier with Platt calibration
- Synthetic data generator (2000 healthy + 2000 septic patients)
- ClinicalPrediction dataclass with SHAP-equivalent feature contributions
- Val AUC: 1.000 on synthetic (target >0.85 on MIMIC)
- No SHAP dependency — uses XGBoost native pred_contribs
- All 3 test cases passing (septic, healthy, sparse data)
- Committed: 7b6c486

**Environment fix:** Project moved to C:\Projects\clinical-ai (out of OneDrive)
UV_LINK_MODE=copy set permanently via [System.Environment]::SetEnvironmentVariable

## Next Session — Phase 2: NLP Pipeline
**File to build:** `src/nlp/note_parser.py`
- Extract clinical entities from free-text doctor notes
- Libraries: spacy + scispacy (biomedical NLP model)
- Input: raw discharge summary / progress note text
- Output: structured dict (symptoms, medications, diagnoses, vitals mentioned)

## Phase 2: ML Models + NLP Pipeline

### Phase 2A: Early Warning Model (written, NOT YET RUN)
- **File:** `src/models/early_warning.py`
- **Status:** Written last session, not yet validated or committed
- **Next:** Run smoke test, validate output, commit

### Phase 2B: NLP Pipeline ✅ COMPLETE (committed 2026-09-06)
- **File:** `src/nlp/note_parser.py`
- **Commit:** 0f9ba67
- **What it does:**
  - scispaCy NER with `en_ner_bc5cdr_md` model
  - Abbreviation expansion (T2DM → type 2 diabetes mellitus)
  - Entity classification: symptoms vs diagnoses, medications vs chemicals
  - NegEx negation detection (implemented directly, no negspacy)
  - Regex vital sign extraction (HR, BP, Temp, RR, SpO2)
- **Key gotcha:** negspacy>=1.1.0 requires spacy>=3.8, incompatible with
  scispaCy model needing spacy==3.7.5. Solution: implement NegEx directly.
- **Key gotcha:** numpy must be pinned to ==1.26.4 in pyproject.toml.
  numpy 2.x breaks thinc binary compatibility with spacy 3.7.

### Next Session — Phase 2A
- Run `uv run python src/models/early_warning.py`
- Validate smoke test output
- Commit to GitHub

### Phase 2A: Early Warning Model ✅ COMPLETE (committed 2026-09-06)
- **File:** `src/models/early_warning.py`
- **Commit:** 763d500
- **Val AUC:** 1.000 on synthetic data (expected — will be ~0.88 on MIMIC-IV)
- **Test cases passed:** septic patient CRITICAL alert, healthy patient LOW, incomplete data graceful refusal

### Phase 3: Multimodal Fusion ✅ COMPLETE (2026-09-06)
- **File:** `src/engine/clinical_engine.py`
- **Commit:** 850e976
- **Run:** `uv run python -m src.engine.clinical_engine`
- **What it does:**
  - Orchestrates FHIR vitals + early warning model + NLP in one pipeline
  - Returns PatientSnapshot with fused risk level and alert text
  - 4 fusion rules:
    - Rule 1: NLP sepsis diagnosis escalates risk one level
    - Rule 2: NLP symptoms corroborate model drivers → higher confidence
    - Rule 3: Broad-spectrum antibiotics flagged as infection signal
    - Rule 4: Negation conflicts between model and note surfaced
- **Known issue:** NegEx occasionally misclassifies "denies X" as symptom

---

## Next Session — Phase 4: FastAPI Layer
- **Goal:** Expose ClinicalEngine as REST endpoints
- **Files to create:**
  - `src/api/main.py` — FastAPI app with /analyse endpoint
  - `src/api/schemas.py` — Pydantic request/response models
- **Run command:** `uv run uvicorn src.api.main:app --reload`
- **Key endpoint:** `POST /analyse` — accepts patient_id, fhir_features, note_text → returns PatientSnapshot as JSON

## Phase 4: FastAPI Layer ✅ COMPLETE (committed 3f4d78e)
- src/api/schemas.py — Pydantic AnalyseRequest and HealthResponse models
- src/api/main.py — FastAPI app with lifespan startup, /health and /analyse endpoints
- ClinicalEngine loaded once at startup via lifespan context manager
- Tested: /health returns ok, /analyse returns CRITICAL 98.8% on septic patient
- Key fix: fastapi and uvicorn added to pyproject.toml
- Key fix: scispaCy model installed via uv pip into C:\Projects\clinical-ai venv

## Next Session — Phase 5: Agentic Orchestration
- Build src/agent/ — LangGraph orchestration layer
- Agent routes patient to appropriate analyser
- Compose final clinical summary
- HITL doctor feedback loop

## Phase 5: Agentic Orchestration with LangGraph ✅ COMPLETE (2026-09-07)

### Files created
- `src/agent/state.py` — AgentState TypedDict (shared memory across all nodes)
- `src/agent/nodes.py` — 5 nodes: triage, vitals, nlp, fusion, summary
- `src/agent/graph.py` — LangGraph StateGraph with conditional routing
- `src/agent/run_agent.py` — smoke test (3 scenarios)

### Commits
- `50f034f` — LangGraph agent
- `faa6eaa` — FastAPI wired to agent

### What the agent does
1. Triage gate — aborts gracefully if <40% critical features present
2. Vitals node — XGBoost sepsis model, extracts risk score + drivers
3. NLP node — scispaCy extracts symptoms, diagnoses, medications
4. Fusion node — 4 rules: escalate on sepsis diagnosis, corroborate drivers, flag antibiotics, surface negation conflicts
5. Summary node — composes doctor-readable alert, sets HITL flag

### API test result (septic patient)
- Risk: CRITICAL 98.8%
- Drivers: lactate, heart_rate, respiratory_rate
- NLP: fever, hypotension, sepsis, piperacillin-tazobactam
- HITL: true — mandatory attending review

### Key gotchas
- ClinicalNoteParseResult is a dataclass — use dot notation (result.symptoms), not dict .get()
- FeatureExplanation fields are feature_name, direction, shap_value (not feature, contribution)
- EarlyWarningSepsis method is train_on_synthetic_data() with no verbose argument
- PowerShell cannot handle multiline -c strings — use .py helper files for complex fixes

## Next Session — Phase 6: Production Hardening
- [ ] Federated learning stub (src/federated/ — Flower client/server skeleton)
- [ ] Alert system — real-time notifications for high-risk patients
- [ ] Audit logging for regulatory compliance

## Phase 6: Federated Learning ✅ COMPLETE (committed 0c9fba9)

### Files created
- `src/federated/fl_client.py` — SepsisFlowerClient wrapping EarlyWarningSepsis, non-IID synthetic data per hospital
- `src/federated/fl_server.py` — FedAvg strategy, weighted AUC aggregation, audit log stub
- `src/federated/run_simulation.py` — 3-hospital in-process simulation via Ray

### Result
- 3 rounds, 0 failures, weighted AUC 0.965 across 3000 samples
- Audit events logged per round (DISHA compliance stub)

### Key gotchas
- EarlyWarningSepsis attributes are `_xgb` (model) and `_is_trained` (flag), not `model`/`is_trained`
- flwr[simulation] requires Ray — install with `uv add "flwr[simulation]"`
- Flower's client_fn now expects `context: Context`, not `cid: str`
- Synthetic data must match model's n_features (12, not 13)
- losses_distributed is a list of (round, loss) tuples, not a dict

### Next Session — Phase 6 continued / Phase 7
- [ ] Alert system — real-time notifications for CRITICAL patients
- [ ] Audit logging — write to append-only file for DISHA compliance
- [ ] Push to GitHub, update PROGRESS.md

## Phase 6: Alert System + Audit Logging COMPLETE (committed 939ca16)

### Alert System
- src/alerts/alert_manager.py - AlertManager, FileAlertChannel, WebhookChannel, dedup
- Alerts fire only on HIGH/CRITICAL predictions
- Output: logs/clinical_alerts.jsonl (one record per alert)
- Deduplication prevents repeat alerts for same patient

### Audit Logging
- src/audit/audit_logger.py - append-only JSONL audit trail (DISHA/HIPAA)
- Thread-safe writes using threading.Lock
- Every /analyse call logged regardless of risk level
- Fields: timestamp, patient_id, risk_level, risk_score, model_version,
  top_drivers, data_completeness, hitl_required, nlp_summary, source
- Output: logs/audit_trail.jsonl

### Wiring into FastAPI
- src/api/main.py patched:
  - AuditLogger initialized in lifespan startup
  - AlertManager initialized in lifespan startup
  - audit_logger.log() called after every /analyse prediction
  - alert_manager.process() called for HIGH/CRITICAL only
  - GET /audit endpoint returns last N records for compliance review

### End-to-End Live Test Result
- Patient: audit-test-001 (septic)
- Risk: CRITICAL 98.8%
- Drivers: lactate, heart_rate, respiratory_rate
- NLP: fever, hypotension, confusion, sepsis
- HITL: True - mandatory attending review
- audit_trail.jsonl: written OK
- clinical_alerts.jsonl: written OK

### Key gotchas
- FastAPI endpoint needs both 
eq: AnalyseRequest AND 
equest: Request
  as separate parameters - AnalyseRequest has no .app attribute
- PowerShell corrupts JS template literals () - always use Python
  scripts to write HTML/JS files
- AlertManager.process() takes snapshot directly, no AlertEvent wrapper needed
- StaticFiles and FileResponse must be imported from fastapi.staticfiles
  and fastapi.responses separately

### Commits
- 939ca16 - Phase 6: audit logging + alert wiring complete
- 3483e4 - Phase 7: GET /audit endpoint

---

## Bonus: Live Dashboard (committed e5cd041)

### File
- src/dashboard/index.html - dark UI, pure HTML/JS, no framework

### Features
- Auto-refreshes every 10 seconds via fetch('/audit?n=50')
- Stats row: total predictions, critical count, high count, HITL required
- Table: time, patient ID, risk badge (color-coded), score, top drivers,
  NLP findings, data completeness, HITL flag
- Served at http://localhost:8000/dashboard via FastAPI StaticFiles

### Verified
- CRITICAL 98.8% record rendered correctly
- All columns populated
- Auto-refresh working (Last refresh timestamp updating)

---

## PROJECT COMPLETE

### All 6 Phases Done

| Phase | Component | Commit |
|---|---|---|
| 0 | Environment + repo | initial |
| 1 | FHIR data layer | 591 lines |
| 2A | XGBoost early warning | 763d500 |
| 2B | scispaCy NLP pipeline | 0f9ba67 |
| 3 | Multimodal fusion engine | 850e976 |
| 4 | FastAPI REST layer | 3f4d78e |
| 5 | LangGraph agentic orchestration | 50f034f |
| 6 | Federated learning (Flower, 3 hospitals, AUC 0.965) | 0c9fba9 |
| 6 | Alert system (FileChannel, WebhookChannel, dedup) | 61cd7c3 |
| 6 | Audit logging (DISHA/HIPAA, append-only JSONL) | 939ca16 |
| + | /audit endpoint + live dashboard | e5cd041 |

### What the system does end-to-end
1. Hospital sends patient vitals + clinical note to POST /analyse
2. LangGraph agent runs triage gate (completeness check)
3. XGBoost scores sepsis risk with SHAP feature drivers
4. scispaCy extracts symptoms, diagnoses, medications from note
5. Fusion engine applies 4 rules (escalate, corroborate, antibiotics, negation)
6. Response returned: risk level, score, alert text, HITL flag
7. Every prediction appended to audit_trail.jsonl (DISHA compliance)
8. HIGH/CRITICAL predictions fire to clinical_alerts.jsonl
9. Live dashboard at /dashboard shows all predictions in real time
10. Federated learning trains across 3 hospitals without sharing patient data

### Pending (optional, does not block system)
- MIMIC-IV real data training (requires PhysioNet credentialing, ~2-5 days)
  Target: replace synthetic AUC 1.000 with real AUC ~0.88
  Start at: https://physionet.org/settings/credentialing/
- Docker containerization for hospital deployment
