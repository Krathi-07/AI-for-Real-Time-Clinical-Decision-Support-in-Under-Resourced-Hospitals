# src/api/main.py
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from src.agent.graph import build_graph
from src.agent.state import AgentState
from src.api.schemas import AnalyseRequest, HealthResponse

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up - compiling LangGraph clinical agent...")
    app.state.agent = build_graph()
    app.state.agent_ready = True
    logger.info("Clinical agent ready. Server accepting requests.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="AI Clinical Decision Support API",
    description="Real-time sepsis early warning for under-resourced hospitals. AI suggests - doctor decides.",
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
def health_check():
    ready = getattr(app.state, "agent_ready", False)
    return HealthResponse(
        status="ok" if ready else "degraded",
        models_loaded=ready,
    )


@app.post("/analyse")
def analyse_patient(request: AnalyseRequest):
    if not getattr(app.state, "agent_ready", False):
        raise HTTPException(status_code=503, detail="Agent not ready. Try again in a few seconds.")

    if not request.fhir_features and not request.note_text.strip():
        raise HTTPException(
            status_code=422,
            detail="At least one of fhir_features or note_text must be provided.",
        )

    initial_state: AgentState = {
        "patient_id": request.patient_id,
        "fhir_features": request.fhir_features or {},
        "note_text": request.note_text or "",
        "reasoning_trace": [],
        "data_sufficient": False,
        "completeness_score": 0.0,
        "model_risk_score": 0.0,
        "model_risk_level": "LOW",
        "model_drivers": [],
        "nlp_symptoms": [],
        "nlp_diagnoses": [],
        "nlp_medications": [],
        "nlp_vitals_mentioned": {},
        "fused_risk_level": "LOW",
        "conflicts": [],
        "alert_text": "",
        "requires_human_review": False,
        "review_reason": "",
    }

    try:
        result = app.state.agent.invoke(initial_state)

        return JSONResponse(content={
            "patient_id": result["patient_id"],
            "risk_level": result["fused_risk_level"],
            "risk_score": round(result["model_risk_score"], 4),
            "alert_text": result["alert_text"],
            "requires_human_review": result["requires_human_review"],
            "review_reason": result["review_reason"],
            "data_sufficient": result["data_sufficient"],
            "completeness_score": round(result["completeness_score"], 3),
            "nlp_findings": {
                "symptoms": result["nlp_symptoms"],
                "diagnoses": result["nlp_diagnoses"],
                "medications": result["nlp_medications"],
            },
            "conflicts": result["conflicts"],
            "reasoning_trace": result["reasoning_trace"],
        })

    except Exception as e:
        logger.exception(f"Analysis failed for patient {request.patient_id}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {e!s}")
    