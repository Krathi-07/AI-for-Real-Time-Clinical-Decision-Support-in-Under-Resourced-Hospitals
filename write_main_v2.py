from pathlib import Path

content = '''# src/api/main.py
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from itsdangerous import URLSafeTimedSerializer, BadSignature

from src.agent.graph import build_graph
from src.agent.state import AgentState
from src.alerts.alert_manager import AlertManager, FileAlertChannel
from src.api.schemas import AnalyseRequest, HealthResponse
from src.audit.audit_logger import AuditLogger

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# --- Auth config ---
SECRET_KEY = os.environ.get("SESSION_SECRET", "clinical-ai-secret-2026")
VALID_USER = os.environ.get("CLINICAL_USERNAME", "doctor")
VALID_PASS = os.environ.get("CLINICAL_PASSWORD", "clinical2026")
COOKIE_NAME = "clinical_session"
serializer = URLSafeTimedSerializer(SECRET_KEY)

def make_session_cookie(username: str) -> str:
    return serializer.dumps(username)

def verify_session_cookie(cookie: str) -> str | None:
    try:
        return serializer.loads(cookie, max_age=86400)  # 24 hours
    except BadSignature:
        return None

def get_current_user(request: Request) -> str | None:
    cookie = request.cookies.get(COOKIE_NAME)
    if not cookie:
        return None
    return verify_session_cookie(cookie)


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
    description="Real-time sepsis early warning for under-resourced hospitals.",
    version="0.3.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="src/dashboard"), name="static")


# --- Root redirect ---
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/login")


# --- Login page ---
@app.get("/login", include_in_schema=False)
def login_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard")
    html = Path("src/dashboard/login.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)


@app.post("/login", include_in_schema=False)
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if username == VALID_USER and password == VALID_PASS:
        token = make_session_cookie(username)
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            httponly=True,
            max_age=86400,
            samesite="lax",
        )
        return response
    html = Path("src/dashboard/login.html").read_text(encoding="utf-8")
    html = html.replace("<!-- ERROR -->", "<div class=\\"error-msg\\">Invalid username or password.</div>")
    return HTMLResponse(content=html, status_code=401)


@app.get("/logout", include_in_schema=False)
def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie(COOKIE_NAME)
    return response


# --- Protected pages ---
@app.get("/dashboard", include_in_schema=False)
def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return FileResponse("src/dashboard/index.html")


@app.get("/demo", include_in_schema=False)
def demo_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return FileResponse("src/dashboard/demo.html")


# --- Health ---
@app.get("/health", response_model=HealthResponse)
def health_check():
    ready = getattr(app.state, "agent_ready", False)
    return HealthResponse(
        status="ok" if ready else "degraded",
        models_loaded=ready,
    )


# --- Audit ---
@app.get("/audit")
def get_audit_log(request: Request, n: int = 20):
    records = request.app.state.audit_logger.tail(n)
    return {"count": len(records), "records": records}


# --- Analyse ---
@app.post("/analyse")
def analyse_patient(req: AnalyseRequest, request: Request):
    if not getattr(app.state, "agent_ready", False):
        raise HTTPException(status_code=503, detail="Agent not ready.")

    if not req.fhir_features and not req.note_text.strip():
        raise HTTPException(status_code=422, detail="Provide fhir_features or note_text.")

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
        logger.exception(f"Analysis failed for patient {req.patient_id}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {e!s}")


# --- PDF Report ---
@app.get("/report/{patient_id}")
def download_report(patient_id: str, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Login required.")

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    import tempfile

    records = request.app.state.audit_logger.tail(50)
    record = next((r for r in reversed(records) if r.get("patient_id") == patient_id), None)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        pdf_path = f.name

    doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    # Header
    title_style = ParagraphStyle("title", fontSize=18, fontName="Helvetica-Bold",
                                  textColor=colors.HexColor("#0891b2"), spaceAfter=6)
    story.append(Paragraph("AI Clinical Decision Support", title_style))
    story.append(Paragraph("Patient Risk Assessment Report", styles["Heading2"]))
    story.append(Spacer(1, 0.4*cm))

    # Meta
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    meta = [
        ["Patient ID", patient_id],
        ["Generated", now],
        ["Model Version", "0.6.0"],
        ["System", "AI for Real-Time Clinical Decision Support"],
    ]
    t = Table(meta, colWidths=[5*cm, 12*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#f0f9ff")),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ("PADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    if record:
        # Risk level
        risk = record.get("risk_level", "UNKNOWN")
        risk_color = {"CRITICAL": "#ef4444", "HIGH": "#f97316",
                      "MEDIUM": "#fbbf24", "LOW": "#22c55e"}.get(risk, "#64748b")
        risk_style = ParagraphStyle("risk", fontSize=24, fontName="Helvetica-Bold",
                                     textColor=colors.HexColor(risk_color), spaceAfter=4)
        story.append(Paragraph(f"Risk Level: {risk}", risk_style))
        score = record.get("risk_score", 0)
        story.append(Paragraph(f"Risk Score: {score*100:.1f}%", styles["Normal"]))
        story.append(Spacer(1, 0.4*cm))

        # Drivers
        drivers = record.get("top_drivers", [])
        if drivers:
            story.append(Paragraph("Top Risk Drivers (SHAP)", styles["Heading3"]))
            for d in drivers:
                story.append(Paragraph(f"• {d}", styles["Normal"]))
            story.append(Spacer(1, 0.3*cm))
    else:
        story.append(Paragraph("No recent record found for this patient ID.", styles["Normal"]))

    # Disclaimer
    story.append(Spacer(1, 1*cm))
    disc_style = ParagraphStyle("disc", fontSize=8, textColor=colors.HexColor("#94a3b8"),
                                 borderColor=colors.HexColor("#e2e8f0"), borderWidth=1,
                                 borderPadding=6)
    story.append(Paragraph(
        "DISCLAIMER: This report is AI-generated for decision support only. "
        "The attending clinician must review and approve all treatment decisions. "
        "This system complies with India DISHA guidelines.",
        disc_style
    ))

    doc.build(story)
    return FileResponse(pdf_path, media_type="application/pdf",
                        filename=f"clinical_report_{patient_id}.pdf")
'''

Path('src/api/main.py').write_text(content, encoding='utf-8')
print('main.py written OK')