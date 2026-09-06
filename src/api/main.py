# src/api/main.py
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from src.api.schemas import AnalyseRequest, HealthResponse
from src.engine.clinical_engine import ClinicalEngine

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up - loading Clinical Engine...")
    engine = ClinicalEngine()
    engine.load_models()
    app.state.engine = engine
    logger.info("Clinical Engine ready. Server accepting requests.")
    yield
    logger.info("Shutting down.")

app = FastAPI(
    title="AI Clinical Decision Support API",
    description="Real-time sepsis early warning for under-resourced hospitals. AI suggests - doctor decides.",
    version="0.1.0",
    lifespan=lifespan,
)

@app.get("/health", response_model=HealthResponse)
def health_check():
    models_loaded = hasattr(app.state, "engine") and app.state.engine._models_loaded
    return HealthResponse(
        status="ok" if models_loaded else "degraded",
        models_loaded=models_loaded,
    )

@app.post("/analyse")
def analyse_patient(request: AnalyseRequest):
    if not hasattr(app.state, "engine") or not app.state.engine._models_loaded:
        raise HTTPException(status_code=503, detail="Models not loaded. Try again in a few seconds.")
    if not request.fhir_features and not request.note_text.strip():
        raise HTTPException(status_code=422, detail="At least one of fhir_features or note_text must be provided.")
    try:
        snapshot = app.state.engine.analyse(
            patient_id=request.patient_id,
            fhir_features=request.fhir_features,
            note_text=request.note_text,
            encounter_id=request.encounter_id,
        )
        return JSONResponse(content=snapshot.to_dict())
    except Exception as e:
        logger.exception(f"Analysis failed for patient {request.patient_id}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {e!s}")

