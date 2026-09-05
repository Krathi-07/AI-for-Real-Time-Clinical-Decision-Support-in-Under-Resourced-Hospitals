# AI for Real-Time Clinical Decision Support in Under-Resourced Hospitals

A virtual junior doctor AI system for tier-2/tier-3 community and rural hospitals in India.
Analyses live patient vitals, lab reports, and clinical notes to detect worsening conditions
early and suggest diagnoses — with full explainability for doctor trust.

## Core Technologies
- **HL7/FHIR R4** — universal hospital data standard
- **Multimodal AI** — fuses vitals, clinical notes, and medical images
- **Federated Learning** — trains across hospitals without sharing patient data
- **Explainable AI (XAI)** — every suggestion shows exactly why

## Stack
- Python 3.14 · uv · FastAPI · uvicorn
- XGBoost · PyTorch · HuggingFace Transformers
- Flower (federated learning) · SHAP · LangGraph

## Setup
```bash
uv venv
.venv\Scripts\activate
uv pip install -r requirements.txt
```

## Project Structure
src/fhir/ → FHIR parser, LOINC feature builder, REST client
src/models/ → Early warning, NLP pipeline, image analyser, fusion
src/explainability/ → SHAP explainer, natural language summaries
src/federated/ → Flower client nodes and aggregation server
src/agent/ → LangGraph virtual doctor orchestration
src/api/ → FastAPI backend, routes, schemas
notebooks/ → Numbered exploration and training notebooks

## Compliance
DISHA (India) · HIPAA · Full audit trail · Doctor override always available