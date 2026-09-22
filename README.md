# 🏥 AI for Real-Time Clinical Decision Support in Under-Resourced Hospitals

> A **Virtual Junior AI Doctor** that assists rural and Tier-2/3 hospital doctors in diagnosing multiple diseases, detecting sepsis in real time, and delivering instant treatment recommendations — built for hospitals where specialist doctors are scarce.

<br>

## 🩺 What It Does

Rural hospitals in India face a severe shortage of specialist doctors. This system acts as a **Virtual Junior Doctor** — it analyses patient vitals, runs AI models, extracts meaning from clinical notes, and tells the attending doctor exactly what to do next.

- 🔬 Detects **sepsis and multiple diseases** from patient vitals in real time
- 🧠 Extracts symptoms and entities from **free-text clinical notes** using NLP
- 💊 Delivers **instant treatment recommendations** following clinical guidelines
- 📄 Generates a **downloadable PDF report** per patient visit
- 💬 Enables **one-click WhatsApp sharing** of patient reports to registered phone numbers
- 📁 Maintains **full patient history** across multiple visits
- 🌸 Uses **federated learning** so patient data never leaves the hospital
- 🔒 **DISHA & HIPAA compliant** — privacy-first design

<br>

## 🚀 How to Run Locally

**Requirements:** Python 3.12+, `uv` package manager

```bash
# 1. Clone the repository
git clone https://github.com/Krathi-07/AI-for-Real-Time-Clinical-Decision-Support-in-Under-Resourced-Hospitals.git
cd AI-for-Real-Time-Clinical-Decision-Support-in-Under-Resourced-Hospitals

# 2. Install dependencies
uv sync

# 3. Start the server
uv run uvicorn src.api.main:app --reload

# 4. Open in browser
# http://localhost:8000
```

**Login credentials:**
| Field | Value |
|-------|-------|
| Username | `doctor` |
| Password | `clinical2026` |

<br>

## 🛠 Tech Stack

| Category | Technology |
|----------|-----------|
| **Backend** | FastAPI, Python 3.12 |
| **AI / ML** | XGBoost (sepsis model), SHAP (explainability) |
| **Clinical NLP** | scispaCy `en_ner_bc5cdr_md` |
| **Agent Orchestration** | LangGraph |
| **Federated Learning** | Flower (Flwr) |
| **Database** | SQLite (zero-dependency, runs anywhere) |
| **Healthcare Standard** | FHIR R4, LOINC-coded vitals |
| **PDF Reports** | ReportLab |
| **Auth** | itsdangerous (signed sessions) |
| **Guidelines** | Surviving Sepsis Campaign 2021 |

<br>

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    LAYER 1 — Data Ingestion          │
│  FHIR R4 bundles · LOINC vitals · Free-text notes   │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│                    LAYER 2 — AI Core                 │
│  XGBoost Model · scispaCy NLP · LangGraph Agent     │
│  Multimodal Fusion · SHAP Explainability             │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│                 LAYER 3 — Clinical Output            │
│  Risk Level · Treatment Plan · PDF Report            │
│  WhatsApp Share · Escalation Alerts · Audit Log      │
└─────────────────────────────────────────────────────┘
```

<br>

## ✅ Project Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | FHIR R4 Patient Data Ingestion | ✅ Complete |
| 2 | XGBoost Sepsis Detection Model + SHAP | ✅ Complete |
| 3 | scispaCy Clinical NLP (NER + Negation) | ✅ Complete |
| 4 | Multimodal Fusion Engine | ✅ Complete |
| 5 | FastAPI + LangGraph Agent + Treatment Engine | ✅ Complete |
| 6 | Federated Learning (Flower) + Alert System | ✅ Complete |

<br>

## 📊 Key Results

| Metric | Value |
|--------|-------|
| Federated AUC | **0.965** |
| Hospitals Simulated | **3** |
| Diseases Supported | **Multiple** (Sepsis, Diabetes, Hypertension, Anaemia, and more) |
| Compliance | **DISHA + HIPAA Ready** |

<br>

## 👥 Team

| Name | Role |
|------|------|
| **Krathika Mendon** | AI & Backend |
| **Divya** | NLP & Data Pipeline |
| **Grishma** | Frontend & Integration |

**Project Guide:** Mr. Suraj Chopade
**Institution:** M.H. Saboo Siddik College of Engineering (MHSSCE), Mumbai
**Year:** 2026

*Associated with Microsoft · LinkedIn · MoSDE · Edunet · SAP*

<br>

## 🔒 Privacy & Compliance

- Patient data **never leaves the hospital** — only model gradient weights are shared during federated learning
- Sessions are signed and expire after 24 hours
- All reports are generated locally and delivered via secure download or WhatsApp
- Compliant with **India's DISHA Act** and **HIPAA** standards

<br>

---

*Built with ❤️ for rural India — where every early diagnosis saves a life.*
