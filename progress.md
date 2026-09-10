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
- XGBoost + SHAP + Platt calibration, AUC ~0.97

## Phase 2B - scispaCy NLP Pipeline [COMPLETE]
- src/nlp/note_parser.py
- en_ner_bc5cdr_md, custom NegEx negation detection
- Extracts symptoms, diagnoses, medications

## Phase 3 - Multimodal Fusion Engine [COMPLETE]
- src/engine/clinical_engine.py
- XGBoost score + NLP findings -> final risk level

## Phase 4 - FastAPI REST Layer [COMPLETE]
- src/api/main.py
- /health, /analyse, /audit, /dashboard endpoints

## Phase 5 - LangGraph Agent Orchestration [COMPLETE]
- src/agent/graph.py, nodes.py, state.py
- 7-node pipeline: triage->vitals->nlp->fusion->treatment->summary->audit
- Reasoning trace returned in response

## Phase 6 - Treatment Engine + Frontend [COMPLETE]
- src/treatment/protocols.py, recommender.py
- Evidence-based protocols (Surviving Sepsis Campaign 2021)
- IMMEDIATE / URGENT / ROUTINE action tiers
- src/dashboard/index.html: full single-page frontend
  - Hero, stats, architecture, tech stack
  - Live demo: vitals form, 4 presets, 7-step pipeline visualization
  - Results: risk header, SHAP drivers, NLP tags, treatment plan
  - Federated Learning section, Live Audit Trail
- Verified: all 4 risk levels working correctly

## Phase 6B - Calibration + UI Polish [COMPLETE]
- qSOFA calibration layer in vitals_node
  - Score >= 0.85 + lactate >= 4 or BP < 90 -> CRITICAL
  - Score >= 0.85 + qSOFA >= 2 -> HIGH
  - Score 0.40-0.84 -> MEDIUM, Score < 0.40 -> LOW
- Treatment recommender priority gate (LOW=ROUTINE only)
- Theme toggle: Dark / Light / High Contrast
- DM Sans font
- Explainer tooltips: SHAP, FHIR, HITL, XGBoost, NLP, FL
- Medium Risk preset (4th scenario)
- Docker files removed - deploying to Render instead

## Phase 6C - Federated Learning Stub [COMPLETE]
- src/federated/fl_client.py: SepsisFlowerClient, non-IID data generator
- fl_server.py and run_simulation.py: stubs present

---

## NEXT STEPS
- [ ] Fix root URL redirect: / -> /dashboard
- [ ] Presentation/walkthrough mode for interviews
- [ ] fl_server.py + run_simulation.py (complete FL simulation)
- [ ] Ruff lint cleanup + final commit
- [ ] README.md update (project summary for GitHub)
- [ ] Deploy to Render (free tier) - live public URL for resume

---

## Skipped (by choice)
- MIMIC-IV real data integration (synthetic data sufficient for portfolio)
- Docker (removed - using Render native deployment)

---

## Key Gotchas (do not forget)
- numpy must be ==1.26.4 (scispaCy conflict with 2.x)
- shap must be ==0.47.0 (llvmlite fails on Python 3.12 with newer)
- scispaCy model: uv pip install <S3 URL> (not uv add)
- Module execution: uv run python -m src.module.file
- File writes: [System.IO.File]::WriteAllText() with UTF-8 no BOM
- Always cd C:\Projects\clinical-ai before any command
- Frontend served at /dashboard not /
- Theme toggle: cycleTheme() must be global scope (not inside async fn)