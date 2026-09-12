"""
Clinical AI Decision Support — FastAPI Backend
Handles: auth, patient registration, disease analysis, dashboard
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Cookie, FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from src.config.diseases import DISEASES, list_diseases
from src.database.db import (
    get_analyses_for_patient,
    get_doctor_by_id,
    get_patient,
    get_patients_for_doctor,
    init_db,
    register_patient,
    save_analysis,
    verify_doctor,
)
from src.engine.disease_scorer import analyse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(title="Clinical AI Decision Support", version="2.0.0")

SECRET_KEY = "clinical-ai-secret-2026"
signer = URLSafeTimedSerializer(SECRET_KEY)

TEMPLATES_DIR = Path("src/templates")
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


@app.on_event("startup")
async def startup():
    init_db()
    logger.info("Database ready")


# ── Session helpers ───────────────────────────────────────────────────────────

def create_session(doctor_id: int) -> str:
    return signer.dumps({"doctor_id": doctor_id})


def get_session(session: str | None) -> dict | None:
    if not session:
        return None
    try:
        return signer.loads(session, max_age=86400)
    except (BadSignature, SignatureExpired):
        return None


def require_doctor(session: str | None) -> dict:
    data = get_session(session)
    if not data:
        raise HTTPException(status_code=401, detail="Not authenticated")
    doctor = get_doctor_by_id(data["doctor_id"])
    if not doctor:
        raise HTTPException(status_code=401, detail="Doctor not found")
    return doctor


# ── HTML helper ───────────────────────────────────────────────────────────────

def html(content: str) -> HTMLResponse:
    return HTMLResponse(content)


def _base(title: str, body: str, doctor_name: str = "") -> str:
    nav = f"<span class='doc-name'>👨‍⚕️ Dr. Clinical AI</span>" if doctor_name else ""
    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — ClinicalAI</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root[data-theme="dark"]{{
    --bg:#0f172a;--surface:#1e293b;--border:#334155;--text:#e2e8f0;
    --text-muted:#94a3b8;--teal:#6ee7b7;--teal-btn:#10b981;--teal-hover:#059669;
    --row-alt:#162032;--th-bg:#0f172a;--input-bg:#0a1120;
    --alert-ok-bg:#14532d;--alert-ok-text:#86efac;
    --alert-err-bg:#7f1d1d;--alert-err-text:#fca5a5;
  }}
  :root[data-theme="light"]{{
    --bg:#f1f5f9;--surface:#ffffff;--border:#cbd5e1;--text:#0f172a;
    --text-muted:#64748b;--teal:#0f766e;--teal-btn:#0f766e;--teal-hover:#0d9488;
    --row-alt:#f8fafc;--th-bg:#e2e8f0;--input-bg:#f8fafc;
    --alert-ok-bg:#dcfce7;--alert-ok-text:#166534;
    --alert-err-bg:#fee2e2;--alert-err-text:#991b1b;
  }}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;font-size:15px;line-height:1.6}}
  .navbar{{background:var(--surface);padding:1rem 2rem;display:flex;justify-content:space-between;
           align-items:center;border-bottom:2px solid var(--teal);position:sticky;top:0;z-index:100;box-shadow:0 2px 12px rgba(0,0,0,.3)}}
  .navbar h1{{color:var(--teal);font-size:1.25rem;font-weight:700;letter-spacing:-.3px}}
  .navbar a{{color:var(--text-muted);text-decoration:none;margin-left:1.5rem;font-size:.95rem;font-weight:500;transition:.15s}}
  .navbar a:hover{{color:var(--teal)}}
  .doc-name{{color:var(--teal);font-weight:600;font-size:.95rem}}
  .theme-btn{{background:var(--surface);border:1px solid var(--border);color:var(--text);
              padding:.35rem .8rem;border-radius:20px;cursor:pointer;font-size:.85rem;
              margin-left:1rem;font-family:'Inter',sans-serif;font-weight:500;transition:.15s}}
  .theme-btn:hover{{border-color:var(--teal);color:var(--teal)}}
  .container{{max-width:1150px;margin:2rem auto;padding:0 1.5rem}}
  .card{{background:var(--surface);border-radius:14px;padding:1.75rem;margin-bottom:1.5rem;
         border:1px solid var(--border);box-shadow:0 1px 4px rgba(0,0,0,.15)}}
  .card h2{{color:var(--teal);margin-bottom:1rem;font-size:1.15rem;font-weight:600}}
  input,select,textarea{{width:100%;padding:.65rem .9rem;background:var(--input-bg);border:1px solid var(--border);
    border-radius:8px;color:var(--text);font-size:.95rem;margin-top:.3rem;font-family:'Inter',sans-serif;transition:.15s}}
  input:focus,select:focus{{outline:none;border-color:var(--teal);box-shadow:0 0 0 3px rgba(110,231,183,.15)}}
  .btn{{padding:.65rem 1.5rem;border:none;border-radius:8px;cursor:pointer;
        font-size:.95rem;font-weight:600;transition:.2s;font-family:'Inter',sans-serif}}
  .btn-primary{{background:var(--teal-btn);color:#fff}}
  .btn-primary:hover{{background:var(--teal-hover);transform:translateY(-1px)}}
  .btn-secondary{{background:var(--border);color:var(--text)}}
  .btn-danger{{background:#ef4444;color:#fff}}
  .form-group{{margin-bottom:1.1rem}}
  .form-group label{{font-size:.9rem;color:var(--text-muted);display:block;margin-bottom:.25rem;font-weight:500}}
  .form-row{{display:grid;grid-template-columns:1fr 1fr;gap:1.1rem}}
  .badge{{display:inline-block;padding:.25rem .75rem;border-radius:20px;font-size:.8rem;font-weight:700;letter-spacing:.3px}}
  .badge-critical{{background:#7f1d1d;color:#fca5a5}}
  .badge-high{{background:#78350f;color:#fcd34d}}
  .badge-moderate{{background:#1e3a5f;color:#93c5fd}}
  .badge-low{{background:#14532d;color:#86efac}}
  table{{width:100%;border-collapse:collapse;font-size:.95rem}}
  th{{text-align:left;padding:.8rem 1rem;background:var(--th-bg);color:var(--text-muted);font-size:.8rem;text-transform:uppercase;letter-spacing:.5px;font-weight:600}}
  td{{padding:.8rem 1rem;border-bottom:1px solid var(--border);color:var(--text)}}
  tr:hover td{{background:var(--row-alt)}}
  .alert-success{{background:var(--alert-ok-bg);color:var(--alert-ok-text);padding:.9rem 1.1rem;border-radius:8px;margin-bottom:1rem;font-weight:500}}
  .alert-error{{background:var(--alert-err-bg);color:var(--alert-err-text);padding:.9rem 1.1rem;border-radius:8px;margin-bottom:1rem;font-weight:500}}
  .risk-bar{{height:10px;border-radius:5px;background:var(--border);margin-top:.5rem}}
  .risk-fill{{height:100%;border-radius:5px}}
  a{{color:var(--teal);text-decoration:none}}
  a:hover{{text-decoration:underline}}
  code{{background:var(--th-bg);padding:.15rem .4rem;border-radius:4px;font-size:.85rem}}
</style>
</head>
<body>
<nav class="navbar">
  <h1>🏥 ClinicalAI — Decision Support</h1>
  <div style="display:flex;align-items:center">
    {nav}
    {"<a href='/dashboard'>Dashboard</a><a href='/about'>About</a><a href='/register-patient'>Register Patient</a><a href='/logout'>Logout</a>" if doctor_name else ""}
    <button class="theme-btn" onclick="toggleTheme()" id="theme-toggle">☀ Light</button>
  </div>
</nav>
<div class="container">
{body}
</div>
<script>
  const html = document.documentElement;
  const btn = document.getElementById('theme-toggle');
  const saved = localStorage.getItem('theme') || 'dark';
  html.setAttribute('data-theme', saved);
  btn.textContent = saved === 'dark' ? '☀ Light' : '🌙 Dark';
  function toggleTheme(){{
    const cur = html.getAttribute('data-theme');
    const next = cur === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    btn.textContent = next === 'dark' ? '☀ Light' : '🌙 Dark';
  }}
</script>
</body>
</html>"""


def _badge(level: str) -> str:
    cls = {"CRITICAL": "badge-critical", "HIGH": "badge-high",
           "MODERATE": "badge-moderate", "LOW": "badge-low"}.get(level, "badge-low")
    return f'<span class="badge {cls}">{level}</span>'


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse("/login")


@app.get("/login", response_class=HTMLResponse)
async def login_page(error: str = ""):
    err_html = f'<div class="alert-error">{error}</div>' if error else ""
    body = f"""
    <div style="max-width:420px;margin:4rem auto">
      <div class="card">
        <h2>🔐 Doctor Login</h2>
        <p style="color:#64748b;font-size:.85rem;margin-bottom:1.5rem">
          AI Clinical Decision Support System
        </p>
        {err_html}
        <form method="post" action="/login">
          <div class="form-group">
            <label>Username</label>
            <input name="username" placeholder="doctor" required>
          </div>
          <div class="form-group">
            <label>Password</label>
            <input type="password" name="password" placeholder="••••••••" required>
          </div>
          <button class="btn btn-primary" style="width:100%;margin-top:.5rem">Login</button>
        </form>
        <p style="color:#475569;font-size:.8rem;margin-top:1rem;text-align:center">
          Default: doctor / clinical2026
        </p>
      </div>
    </div>"""
    return html(_base("Login", body))


@app.post("/login")
async def login(response: Response, username: str = Form(...), password: str = Form(...)):
    doctor = verify_doctor(username, password)
    if not doctor:
        return RedirectResponse("/login?error=Invalid+credentials", status_code=303)
    session_token = create_session(doctor["id"])
    resp = RedirectResponse("/dashboard", status_code=303)
    resp.set_cookie("session", session_token, httponly=True, max_age=86400)
    return resp


@app.get("/logout")
async def logout():
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie("session")
    return resp

@app.get("/about", response_class=HTMLResponse)
async def about_page(session: str | None = Cookie(default=None)):
    doctor = require_doctor(session)
    body = """
    <div class="card">
      <h2>🏥 About ClinicalAI</h2>
      <p style="font-size:1.05rem;line-height:1.8;margin-bottom:1rem">
        <strong>AI for Real-Time Clinical Decision Support in Under-Resourced Hospitals</strong><br>
        A production-grade clinical AI system designed for tier-2 and tier-3 rural hospitals in India,
        where specialist doctors are scarce and early disease detection saves lives.
      </p>
      <p style="color:var(--text-muted);line-height:1.8">
        The system analyses patient vitals, lab reports, and clinical parameters across
        <strong>11 disease categories</strong> using rule-based clinical scoring engines
        grounded in published guidelines (qSOFA, HEART Score, ADA Criteria, JNC-8, WHO thresholds).
        Every finding is explained in plain language so doctors can act immediately.
      </p>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:1.5rem">
      <div class="card" style="text-align:center">
        <div style="font-size:2.5rem;margin-bottom:.5rem">11</div>
        <div style="color:var(--teal);font-weight:600">Diseases Supported</div>
        <div style="color:var(--text-muted);font-size:.9rem;margin-top:.5rem">
          Sepsis · Diabetes · Heart Attack · Hypertension · Cancer · Respiratory ·
          Cold & Flu · Anaemia · GI · Musculoskeletal · Skin
        </div>
      </div>
      <div class="card" style="text-align:center">
        <div style="font-size:2.5rem;margin-bottom:.5rem">🔬</div>
        <div style="color:var(--teal);font-weight:600">AI-Powered Analysis</div>
        <div style="color:var(--text-muted);font-size:.9rem;margin-top:.5rem">
          XGBoost · scispaCy NLP · SHAP Explainability · LangGraph Orchestration · FHIR R4
        </div>
      </div>
      <div class="card" style="text-align:center">
        <div style="font-size:2.5rem;margin-bottom:.5rem">📋</div>
        <div style="color:var(--teal);font-weight:600">DISHA Compliant</div>
        <div style="color:var(--text-muted);font-size:.9rem;margin-top:.5rem">
          Audit logs · Patient consent · Data stays local · Doctor override always available
        </div>
      </div>
    </div>
    <div class="card">
      <h2>👥 Project Team</h2>
      <table>
        <thead><tr><th>Name</th><th>Role</th><th>Institution</th></tr></thead>
        <tbody>
          <tr><td>Krathika</td><td>Lead Developer — AI & Backend</td><td>M.H. Saboo Siddik College of Engineering</td></tr>
          <tr><td>Divya</td><td>Developer — NLP & Data Pipeline</td><td>M.H. Saboo Siddik College of Engineering</td></tr>
          <tr><td>Grishma</td><td>Developer — Frontend & Integration</td><td>M.H. Saboo Siddik College of Engineering</td></tr>
          <tr><td>Mr. Suraj Hindurao Chopade</td><td>Project Guide</td><td>M.H. Saboo Siddik College of Engineering</td></tr>
        </tbody>
      </table>
    </div>
    <div class="card">
      <h2>🏗 System Architecture</h2>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:1rem">
        <div style="background:var(--bg);padding:1rem;border-radius:8px;border:1px solid var(--border)">
          <div style="color:var(--teal);font-weight:600;margin-bottom:.5rem">Layer 1 — Ingestion</div>
          <div style="color:var(--text-muted);font-size:.9rem">FHIR R4 patient bundles · LOINC-coded vitals · Clinical notes · Completeness validation</div>
        </div>
        <div style="background:var(--bg);padding:1rem;border-radius:8px;border:1px solid var(--border)">
          <div style="color:var(--teal);font-weight:600;margin-bottom:.5rem">Layer 2 — AI Core</div>
          <div style="color:var(--text-muted);font-size:.9rem">Disease-specific scoring · XGBoost models · scispaCy NLP · SHAP explainability · LangGraph agent</div>
        </div>
        <div style="background:var(--bg);padding:1rem;border-radius:8px;border:1px solid var(--border)">
          <div style="color:var(--teal);font-weight:600;margin-bottom:.5rem">Layer 3 — Output</div>
          <div style="color:var(--text-muted);font-size:.9rem">Risk level + score · Clinical findings · Treatment recommendations · PDF report · Audit trail</div>
        </div>
      </div>
    </div>"""
    return html(_base("About", body, doctor["full_name"]))

# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(session: str | None = Cookie(default=None)):
    doctor = require_doctor(session)
    patients = get_patients_for_doctor(doctor["id"])

    rows = ""
    for p in patients:
        analyses = get_analyses_for_patient(p["patient_id"])
        last = analyses[0] if analyses else None
        risk_badge = _badge(last["risk_level"]) if last else "<span style='color:#475569'>—</span>"
        disease_name = DISEASES.get(p["disease_id"], type("x", (), {"name": p["disease_id"]})()).name
        rows += f"""<tr>
          <td><a href="/patient/{p['patient_id']}">{p['patient_id']}</a></td>
          <td>{p['full_name']}</td>
          <td>{p['age']} yrs / {p['gender']}</td>
          <td>{disease_name}</td>
          <td>{risk_badge}</td>
          <td style="color:#64748b;font-size:.8rem">{p['registered_at'][:16]}</td>
          <td>
            <a href="/analyse/{p['patient_id']}">
              <button class="btn btn-primary" style="padding:.3rem .8rem;font-size:.8rem">Analyse</button>
            </a>
          </td>
        </tr>"""

    empty = "<tr><td colspan='7' style='text-align:center;color:#475569;padding:2rem'>No patients registered yet</td></tr>" if not patients else ""

    body = f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.5rem">
      <div>
        <h2 style="color:#e2e8f0;font-size:1.4rem">Welcome, {doctor['full_name']}</h2>
        <p style="color:#64748b">{doctor['hospital']} · {len(patients)} patient(s) registered</p>
      </div>
      <a href="/register-patient">
        <button class="btn btn-primary">+ Register Patient</button>
      </a>
    </div>
    <div class="card">
      <h2>Your Patients</h2>
      <table>
        <thead><tr>
          <th>Patient ID</th><th>Name</th><th>Age / Gender</th>
          <th>Condition</th><th>Last Risk</th><th>Registered</th><th>Action</th>
        </tr></thead>
        <tbody>{rows}{empty}</tbody>
      </table>
    </div>"""
    return html(_base("Dashboard", body, doctor["full_name"]))


# ── Patient registration ──────────────────────────────────────────────────────

@app.get("/register-patient", response_class=HTMLResponse)
async def register_page(session: str | None = Cookie(default=None), msg: str = ""):
    doctor = require_doctor(session)
    disease_options = "".join(
        f'<option value="{d["id"]}">{d["name"]}</option>'
        for d in list_diseases()
    )
    msg_html = f'<div class="alert-success">✅ {msg}</div>' if msg else ""
    body = f"""
    {msg_html}
    <div class="card">
      <h2>📋 Register New Patient</h2>
      <form method="post" action="/register-patient">
        <div class="form-row">
          <div class="form-group">
            <label>Full Name *</label>
            <input name="full_name" placeholder="Patient full name" required>
          </div>
          <div class="form-group">
            <label>Age *</label>
            <input name="age" type="number" min="0" max="120" required>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Gender *</label>
            <select name="gender">
              <option>Male</option><option>Female</option><option>Other</option>
            </select>
          </div>
          <div class="form-group">
            <label>Phone</label>
            <input name="phone" placeholder="+91 98765 43210">
          </div>
        </div>
        <div class="form-group">
          <label>Address</label>
          <input name="address" placeholder="Village / City, District, State">
        </div>
        <div class="form-group">
          <label>Condition / Disease to Assess *</label>
          <select name="disease_id">{disease_options}</select>
        </div>
        <div style="margin-top:1rem;display:flex;gap:1rem">
          <button class="btn btn-primary" type="submit">Register Patient</button>
          <a href="/dashboard"><button class="btn btn-secondary" type="button">Cancel</button></a>
        </div>
      </form>
    </div>"""
    return html(_base("Register Patient", body, doctor["full_name"]))


@app.post("/register-patient")
async def register_patient_post(
    session: str | None = Cookie(default=None),
    full_name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    phone: str = Form(""),
    address: str = Form(""),
    disease_id: str = Form(...),
):
    doctor = require_doctor(session)
    patient_id = register_patient(full_name, age, gender, phone, address, disease_id, doctor["id"])
    return RedirectResponse(f"/analyse/{patient_id}?msg=Patient+registered", status_code=303)


# ── Analysis ──────────────────────────────────────────────────────────────────

@app.get("/analyse/{patient_id}", response_class=HTMLResponse)
async def analyse_page(patient_id: str, session: str | None = Cookie(default=None), msg: str = ""):
    doctor = require_doctor(session)
    patient = get_patient(patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")

    disease = DISEASES.get(patient["disease_id"])
    if not disease:
        raise HTTPException(400, "Unknown disease")

    # Build parameter input fields
    param_fields = ""
    for param in disease.parameters:
        if param.input_type == "select":
            opts = "".join(f'<option value="{o}">{o}</option>' for o in param.options)
            field = f'<select name="{param.key}">{opts}</select>'
        else:
            placeholder = f"{param.normal_min}–{param.normal_max}" if param.normal_min is not None else ""
            req = "required" if param.required else ""
            field = f'<input type="number" step="0.01" name="{param.key}" placeholder="Normal: {placeholder} {param.unit}" {req}>'

        param_fields += f"""
        <div class="form-group">
          <label>{param.label}
            <span style="color:#475569;font-size:.75rem"> ({param.unit})</span>
            {"<span style='color:#ef4444'> *</span>" if param.required else " <span style='color:#475569;font-size:.75rem'>(optional)</span>"}
          </label>
          {field}
        </div>"""

    msg_html = f'<div class="alert-success">✅ {msg}</div>' if msg else ""
    body = f"""
    {msg_html}
    <div style="display:flex;gap:.5rem;align-items:center;margin-bottom:1rem">
      <a href="/dashboard">← Dashboard</a>
      <span style="color:#475569"> / </span>
      <span style="color:#e2e8f0">{patient['full_name']}</span>
    </div>
    <div class="card">
      <h2>🔬 Clinical Analysis — {disease.name}</h2>
      <div style="color:#64748b;font-size:.85rem;margin-bottom:1.2rem">
        Patient: <strong style="color:#e2e8f0">{patient['full_name']}</strong> ·
        Age: <strong style="color:#e2e8f0">{patient['age']}</strong> ·
        ID: <code style="color:#6ee7b7">{patient_id}</code>
      </div>
      <form method="post" action="/analyse/{patient_id}">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0 1.5rem">
          {param_fields}
        </div>
        <div style="margin-top:1.5rem;display:flex;gap:1rem">
          <button class="btn btn-primary" type="submit">▶ Run Analysis</button>
          <a href="/patient/{patient_id}">
            <button class="btn btn-secondary" type="button">View History</button>
          </a>
        </div>
      </form>
    </div>"""
    return html(_base(f"Analyse — {patient['full_name']}", body, doctor["full_name"]))


@app.post("/analyse/{patient_id}")
async def run_analysis(request: Request, patient_id: str, session: str | None = Cookie(default=None)):
    doctor = require_doctor(session)
    patient = get_patient(patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")

    disease = DISEASES.get(patient["disease_id"])
    form_data = await request.form()

    # Parse parameters — convert numeric strings, keep select values as-is
    parameters = {}
    for param in disease.parameters:
        val = form_data.get(param.key, "")
        if param.input_type in ("select", "boolean"):
            parameters[param.key] = val
        else:
            try:
                parameters[param.key] = float(val) if val else None
            except ValueError:
                parameters[param.key] = None

    # Remove None values
    parameters = {k: v for k, v in parameters.items() if v is not None}

    # Run scoring
    result = analyse(patient["disease_id"], parameters)

    # Save to DB
    analysis_id = save_analysis(
        patient_id=patient_id,
        disease_id=patient["disease_id"],
        risk_level=result.risk_level,
        risk_score=result.risk_score,
        parameters=json.dumps(parameters),
        findings=json.dumps(result.findings),
        recommendations=json.dumps(result.recommendations),
        doctor_id=doctor["id"],
    )

    return RedirectResponse(f"/result/{analysis_id}", status_code=303)


# ── Result page ───────────────────────────────────────────────────────────────

@app.get("/result/{analysis_id}", response_class=HTMLResponse)
async def result_page(analysis_id: int, session: str | None = Cookie(default=None)):
    from src.database.db import get_connection
    doctor = require_doctor(session)
    conn = get_connection()
    row = conn.execute("SELECT * FROM analyses WHERE id=?", (analysis_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Analysis not found")

    row = dict(row)
    patient = get_patient(row["patient_id"])
    findings = json.loads(row["findings"])
    recs = json.loads(row["recommendations"])
    params = json.loads(row["parameters"])

    findings_html = "".join(f"<li style='margin:.4rem 0;color:#fcd34d'>⚠ {f}</li>" for f in findings)
    recs_html = "".join(f"<li style='margin:.4rem 0;color:#86efac'>→ {r}</li>" for r in recs)
    params_html = "".join(
        f"<tr><td style='color:#94a3b8'>{k.replace('_',' ').title()}</td><td style='color:#e2e8f0'>{v}</td></tr>"
        for k, v in params.items()
    )

    pct = int(row["risk_score"] * 100)
    fill_color = {"CRITICAL": "#ef4444", "HIGH": "#f97316", "MODERATE": "#3b82f6", "LOW": "#10b981"}.get(row["risk_level"], "#10b981")

    body = f"""
    <div style="display:flex;gap:.5rem;align-items:center;margin-bottom:1rem">
      <a href="/dashboard">← Dashboard</a>
      <span style="color:#475569"> / </span>
      <a href="/patient/{row['patient_id']}">{patient['full_name']}</a>
    </div>
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div>
          <h2>{DISEASES[row['disease_id']].name} — Analysis Result</h2>
          <p style="color:#64748b;font-size:.85rem;margin-top:.3rem">
            {patient['full_name']} · Age {patient['age']} · {patient['gender']} ·
            <code style="color:#6ee7b7">{row['patient_id']}</code>
          </p>
        </div>
        {_badge(row['risk_level'])}
      </div>
      <div style="margin:1.2rem 0">
        <div style="display:flex;justify-content:space-between;font-size:.85rem;color:#94a3b8;margin-bottom:.3rem">
          <span>Risk Score</span><span style="color:{fill_color};font-weight:700">{pct}%</span>
        </div>
        <div class="risk-bar">
          <div class="risk-fill" style="width:{pct}%;background:{fill_color}"></div>
        </div>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem">
      <div class="card">
        <h2>🔍 Clinical Findings</h2>
        <ul style="list-style:none;padding:0">{findings_html}</ul>
      </div>
      <div class="card">
        <h2>💊 Recommendations</h2>
        <ul style="list-style:none;padding:0">{recs_html}</ul>
      </div>
    </div>
    <div class="card">
      <h2>📊 Parameters Entered</h2>
      <table><tbody>{params_html}</tbody></table>
    </div>
    <div style="display:flex;gap:1rem;margin-top:1rem">
      <a href="/report/{analysis_id}">
        <button class="btn btn-primary">📄 Download PDF Report</button>
      </a>
      <a href="/analyse/{row['patient_id']}">
        <button class="btn btn-secondary">🔄 Re-analyse</button>
      </a>
      <a href="/patient/{row['patient_id']}">
        <button class="btn btn-secondary">📁 Patient History</button>
      </a>
    </div>"""
    return html(_base(f"Result — {patient['full_name']}", body, doctor["full_name"]))


# ── Patient history ───────────────────────────────────────────────────────────

@app.get("/patient/{patient_id}", response_class=HTMLResponse)
async def patient_history(patient_id: str, session: str | None = Cookie(default=None)):
    doctor = require_doctor(session)
    patient = get_patient(patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")

    analyses = get_analyses_for_patient(patient_id)
    rows = ""
    for a in analyses:
        pct = int(a["risk_score"] * 100)
        rows += f"""<tr>
          <td style="color:#64748b;font-size:.8rem">{a['created_at'][:16]}</td>
          <td>{DISEASES.get(a['disease_id'], type('x',(),{'name':a['disease_id']})()).name}</td>
          <td>{_badge(a['risk_level'])} {pct}%</td>
          <td><a href="/result/{a['id']}">View</a> &nbsp;
              <a href="/report/{a['id']}">PDF</a></td>
        </tr>"""

    disease_name = DISEASES.get(patient["disease_id"], type("x", (), {"name": patient["disease_id"]})()).name
    body = f"""
    <div style="margin-bottom:1rem"><a href="/dashboard">← Dashboard</a></div>
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div>
          <h2>{patient['full_name']}</h2>
          <p style="color:#64748b;font-size:.85rem;margin-top:.3rem">
            ID: <code style="color:#6ee7b7">{patient_id}</code> ·
            Age: {patient['age']} · {patient['gender']} ·
            Condition: {disease_name}
          </p>
          <p style="color:#64748b;font-size:.85rem">
            📞 {patient.get('phone') or '—'} &nbsp;|&nbsp;
            📍 {patient.get('address') or '—'}
          </p>
        </div>
        <a href="/analyse/{patient_id}">
          <button class="btn btn-primary">▶ New Analysis</button>
        </a>
      </div>
    </div>
    <div class="card">
      <h2>Analysis History ({len(analyses)} records)</h2>
      <table>
        <thead><tr><th>Date</th><th>Condition</th><th>Risk</th><th>Actions</th></tr></thead>
        <tbody>
          {rows if rows else "<tr><td colspan='4' style='text-align:center;color:#475569;padding:2rem'>No analyses yet</td></tr>"}
        </tbody>
      </table>
    </div>"""
    return html(_base(patient["full_name"], body, doctor["full_name"]))


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0", "diseases": len(DISEASES)}

# ── PDF Report ────────────────────────────────────────────────────────────────

@app.get("/report/{analysis_id}")
async def download_report(analysis_id: int, session: str | None = Cookie(default=None)):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    import io, json
    from src.database.db import get_connection

    doctor = require_doctor(session)
    conn = get_connection()
    row = conn.execute("SELECT * FROM analyses WHERE id=?", (analysis_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Analysis not found")

    row = dict(row)
    patient = get_patient(row["patient_id"])
    findings = json.loads(row["findings"])
    recs = json.loads(row["recommendations"])
    params = json.loads(row["parameters"])
    disease = DISEASES.get(row["disease_id"])
    now = datetime.now(tz=timezone.utc).strftime("%d %B %Y, %H:%M UTC")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            topMargin=1.5*cm, bottomMargin=1.5*cm,
                            leftMargin=2*cm, rightMargin=2*cm)

    styles = getSampleStyleSheet()
    teal   = colors.HexColor("#0f766e")
    dark   = colors.HexColor("#0f172a")
    gray   = colors.HexColor("#64748b")
    red    = colors.HexColor("#dc2626")
    orange = colors.HexColor("#ea580c")
    blue   = colors.HexColor("#2563eb")
    green  = colors.HexColor("#16a34a")

    risk_color = {"CRITICAL": red, "HIGH": orange, "MODERATE": blue, "LOW": green}.get(row["risk_level"], green)

    H1 = ParagraphStyle("H1", fontSize=18, textColor=teal, spaceAfter=4, fontName="Helvetica-Bold")
    H2 = ParagraphStyle("H2", fontSize=11, textColor=teal, spaceAfter=4, fontName="Helvetica-Bold", spaceBefore=10)
    BODY = ParagraphStyle("BODY", fontSize=9, textColor=dark, spaceAfter=3, leading=14)
    SMALL = ParagraphStyle("SMALL", fontSize=8, textColor=gray, spaceAfter=2)
    CENTER = ParagraphStyle("CENTER", fontSize=9, alignment=TA_CENTER, textColor=gray)

    story = []

    # ── Header ──
    story.append(Paragraph("ClinicalAI — Decision Support System", H1))
    story.append(Paragraph("AI-Assisted Medical Report &nbsp;|&nbsp; Confidential", SMALL))
    story.append(Paragraph(f"Generated: {now} &nbsp;|&nbsp; Report ID: {analysis_id}", SMALL))
    story.append(HRFlowable(width="100%", thickness=2, color=teal, spaceAfter=10))

    # ── Patient info table ──
    story.append(Paragraph("Patient Information", H2))
    info_data = [
        ["Patient ID", row["patient_id"], "Full Name", patient["full_name"]],
        ["Age", f"{patient['age']} years", "Gender", patient["gender"]],
        ["Phone", patient.get("phone") or "—", "Address", patient.get("address") or "—"],
        ["Condition", disease.name if disease else row["disease_id"], "ICD-10", disease.icd10_code if disease else "—"],
        ["Attending Doctor", doctor["full_name"], "Hospital", doctor["hospital"]],
        ["Analysis Date", row["created_at"][:16], "Report Generated", now],
    ]
    info_table = Table(info_data, colWidths=[3.5*cm, 6*cm, 3.5*cm, 6*cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",  (0,0), (-1,-1), 8.5),
        ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",  (2,0), (2,-1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0,0), (0,-1), gray),
        ("TEXTCOLOR", (2,0), (2,-1), gray),
        ("BACKGROUND",(0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, colors.HexColor("#f1f5f9")]),
        ("GRID",      (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING",   (0,0), (-1,-1), 6),
        ("VALIGN",    (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(info_table)

    # ── Risk summary ──
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Risk Assessment Summary", H2))
    pct = int(row["risk_score"] * 100)
    risk_data = [["Risk Level", "Risk Score", "Disease", "ICD-10 Code"],
                 [row["risk_level"], f"{pct}%", disease.name if disease else "—", disease.icd10_code if disease else "—"]]
    risk_table = Table(risk_data, colWidths=[4*cm, 3*cm, 8*cm, 4*cm])
    risk_table.setStyle(TableStyle([
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("BACKGROUND",  (0,0), (-1,0), dark),
        ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
        ("BACKGROUND",  (0,1), (0,1), risk_color),
        ("TEXTCOLOR",   (0,1), (0,1), colors.white),
        ("FONTNAME",    (0,1), (0,1), "Helvetica-Bold"),
        ("FONTSIZE",    (0,1), (0,1), 13),
        ("ALIGN",       (0,0), (-1,-1), "CENTER"),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING",     (0,0), (-1,-1), 8),
        ("ROWHEIGHT",   (0,1), (-1,1), 30),
    ]))
    story.append(risk_table)

    # ── Parameters ──
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Clinical Parameters Recorded", H2))
    param_rows = [["Parameter", "Value Recorded", "Normal Range", "Status"]]
    disease_params = {p.key: p for p in disease.parameters} if disease else {}
    for k, v in params.items():
        param_cfg = disease_params.get(k)
        if param_cfg:
            label = param_cfg.label
            unit = param_cfg.unit
            lo, hi = param_cfg.normal_min, param_cfg.normal_max
            normal_str = f"{lo}–{hi} {unit}" if lo is not None else "—"
            try:
                fv = float(v)
                if lo is not None and fv < lo:
                    status = "LOW ↓"
                elif hi is not None and fv > hi:
                    status = "HIGH ↑"
                else:
                    status = "Normal ✓"
            except (ValueError, TypeError):
                status = "—"
            param_rows.append([label, f"{v} {unit}".strip(), normal_str, status])
        else:
            param_rows.append([k.replace("_", " ").title(), str(v), "—", "—"])

    param_table = Table(param_rows, colWidths=[6*cm, 4*cm, 4.5*cm, 4.5*cm])
    param_table.setStyle(TableStyle([
        ("FONTNAME",       (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",       (0,0), (-1,-1), 8.5),
        ("BACKGROUND",     (0,0), (-1,0), dark),
        ("TEXTCOLOR",      (0,0), (-1,0), colors.white),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ("GRID",           (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING",        (0,0), (-1,-1), 6),
        ("ALIGN",          (1,0), (-1,-1), "CENTER"),
    ]))
    story.append(param_table)

    # ── Findings ──
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Clinical Findings", H2))
    for f in findings:
        story.append(Paragraph(f"⚠ {f}", BODY))

    # ── Recommendations ──
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Medical Recommendations", H2))
    for r in recs:
        story.append(Paragraph(f"→ {r}", BODY))

    # ── Disclaimer ──
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=gray, spaceAfter=6))
    story.append(Paragraph(
        "DISCLAIMER: This report is AI-generated and intended to assist clinical decision-making only. "
        "It does not replace professional medical judgement. The attending doctor must review and validate "
        "all findings before any clinical action is taken. ClinicalAI — DISHA Compliant.",
        SMALL))
    story.append(Paragraph(f"Doctor Signature: __________________ &nbsp;&nbsp; Date: __________________", SMALL))

    doc.build(story)
    buffer.seek(0)

    filename = f"ClinicalReport_{row['patient_id']}_{row['disease_id']}_{analysis_id}.pdf"
    from fastapi.responses import StreamingResponse
    return StreamingResponse(buffer, media_type="application/pdf",
                             headers={"Content-Disposition": f"attachment; filename={filename}"})
