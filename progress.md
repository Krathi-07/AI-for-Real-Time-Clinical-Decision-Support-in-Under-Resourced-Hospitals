# PROGRESS.md

## Project: AI for Real-Time Clinical Decision Support in Under-Resourced Hospitals

---

## Phase 0 - Environment Setup [COMPLETE]
- uv + Python 3.12, repo created, folder structure, pyproject.toml

## Phase 1 - FHIR Data Layer [COMPLETE]
- src/fhir/client.py, parser.py, feature_builder.py
- LOINC-coded vitals, HAPI FHIR test server

## Phase 2A - XGBoost Sepsis Model [COMPLETE]
- src/models/early_warning.py
- XGBoost + SHAP + Platt calibration
- AUC ~0.97 on synthetic data

## Phase 2B - scispaCy NLP Pipeline [COMPLETE]
- src/nlp/note_parser.py
- en_ner_bc5cdr_md model, custom NegEx negation detection
- Extracts symptoms, diagnoses, medications from clinical notes

## Phase 3 - Multimodal Fusion Engine [COMPLETE]
- src/fusion/clinical_engine.py
- Combines XGBoost score + NLP findings -> final risk level
- Rules: sepsis NLP -> CRITICAL, antibiotics found -> note treatment

## Phase 4 - FastAPI REST Layer [COMPLETE]
- src/api/main.py
- /health, /analyse, /audit endpoints
- Pydantic request/response models

## Phase 5 - LangGraph Agent Orchestration [COMPLETE]
- src/agent/graph.py, nodes.py, state.py
- 7-node pipeline: triage -> vitals -> nlp -> fusion -> treatment -> summary -> audit
- /analyse uses clinical_agent.invoke()
- Reasoning trace returned in response

## Phase 6 - Treatment Engine + Frontend [COMPLETE]
- src/treatment/protocols.py, recommender.py
- Evidence-based protocols (Surviving Sepsis Campaign 2021 + WHO low-resource)
- IMMEDIATE / URGENT / ROUTINE action tiers
- Escalation triggers, reassess timers per risk level
- src/dashboard/index.html: full single-page frontend
  - Hero, stats, architecture, tech stack
  - Live demo: vitals form, 3 presets, 7-step pipeline visualization
  - Results: CRITICAL header, SHAP drivers, NLP tags, treatment plan
  - Federated Learning section, Live Audit Trail
- Verified: sepsis patient -> CRITICAL 98.8% -> 17 actions -> audit logged

## Phase 6B - Federated Learning Stub [COMPLETE]
- src/federated/fl_client.py: SepsisFlowerClient, non-IID data generator
- fl_server.py and run_simulation.py: TODO (next)

---

## NEXT STEPS
- [ ] Presentation mode: guided step-by-step walkthrough for interviews
- [ ] Test High Risk + Low Risk presets end-to-end
- [ ] fl_server.py + run_simulation.py (complete FL simulation)
- [ ] Real MIMIC-IV data loaders (swap synthetic stubs)
- [ ] Ruff lint cleanup (main.py, client.py, parser.py, note_parser.py)

---

## Key Gotchas (do not forget)
- numpy must be ==1.26.4 (scispaCy conflict with 2.x)
- shap must be ==0.47.0 (llvmlite fails on Python 3.12 with newer)
- scispaCy model: uv pip install <S3 URL> (not uv add)
- Module execution: uv run python -m src.module.file
- File writes: [System.IO.File]::WriteAllText() with UTF-8 no BOM
- Always cd C:\Projects\clinical-ai before any command
- ClinicalNoteParseResult is a dataclass -> use dot notation
