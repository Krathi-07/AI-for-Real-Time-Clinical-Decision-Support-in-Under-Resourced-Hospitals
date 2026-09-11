# src/api/main.py
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.agent.graph import build_graph
from src.agent.state import AgentState
from src.alerts.alert_manager import AlertManager, FileAlertChannel
from src.api.schemas import AnalyseRequest, HealthResponse
from src.audit.audit_logger import AuditLogger

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up - compiling LangGraph clinical agent...")
    app.state.agent = build_graph()
    alert_manager = AlertManager()
    alert_manager.add_channel(FileAlertChannel("logs/clinical_alerts.jsonl"))
    app.state.alert_manager = alert_manager
    app.state.audit_logger = AuditLogger("logs/audit_trail.jsonl")
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


app.mount("/static", StaticFiles(directory="src/dashboard"), name="static")

@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse("src/dashboard/index.html")


@app.get("/health", response_model=HealthResponse)
def health_check():
    ready = getattr(app.state, "agent_ready", False)
    return HealthResponse(
        status="ok" if ready else "degraded",
        models_loaded=ready,
    )


@app.get("/audit")
def get_audit_log(request: Request, n: int = 20):
    """Return last N audit records for compliance review."""
    records = request.app.state.audit_logger.tail(n)
    return {"count": len(records), "records": records}


@app.post("/analyse")
def analyse_patient(req: AnalyseRequest, request: Request):
    if not getattr(app.state, "agent_ready", False):
        raise HTTPException(status_code=503, detail="Agent not ready. Try again in a few seconds.")

    if not req.fhir_features and not req.note_text.strip():
        raise HTTPException(
            status_code=422,
            detail="At least one of fhir_features or note_text must be provided.",
        )

    initial_state: AgentState = {
        "patient_id": req.patient_id,
        "fhir_features": req.fhir_features or {},
        "note_text": req.note_text or "",
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
        "treatment_plan": {},
    }

    try:
        result = app.state.agent.invoke(initial_state)

        # --- Audit log (every prediction, not just alerts) ---
        from types import SimpleNamespace
        _nlp = SimpleNamespace(
            symptoms=result["nlp_symptoms"],
            diagnoses=result["nlp_diagnoses"],
            negated_findings=[],
        )
        _snap = SimpleNamespace(
            patient_id=result["patient_id"],
            risk_level=result["fused_risk_level"],
            risk_score=result["model_risk_score"],
            model_version="0.6.0",
            top_drivers=result["model_drivers"],
            data_completeness=result["completeness_score"],
            hitl_required=result["requires_human_review"],
            fusion_rules_fired=[],
            nlp_findings=_nlp,
        )
        request.app.state.audit_logger.log(_snap, source="api:/analyse")

        # --- Alert manager (HIGH / CRITICAL only) ---
        if result["fused_risk_level"] in ("HIGH", "CRITICAL"):
            request.app.state.alert_manager.process(_snap)

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
            "treatment_plan": result.get("treatment_plan", {}),
        })

    except Exception as e:
        logger.exception(f"Analysis failed for patient {request.patient_id}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {e!s}")
    