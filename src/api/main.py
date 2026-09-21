# PASTE THE ENTIRE NEW main.py CONTENT HERE
"""
Clinical AI Decision Support — FastAPI Backend
Handles: auth, patient registration, disease analysis, dashboard
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from fastapi import Cookie, FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
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
    nav = f"<span style='color:#6ee7b7'>👨‍⚕️ {doctor_name}</span>" if doctor_name else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — ClinicalAI</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  :root{{
    --bg:#0c0e1a;--surface:#111322;--surface2:#1a1d30;--surface3:#252840;
    --violet:#7c3aed;--violet-dim:#6d28d9;--violet-lit:#a78bfa;--violet-glow:rgba(124,58,237,.15);
    --text:#e2e4f0;--text-muted:#8b90b0;--text-dark:#0f1035;--border:#2a2d45;
    --success:#10b981;--warning:#f59e0b;--danger:#ef4444;
  }}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh}}
  .navbar{{background:var(--surface);padding:1rem 2rem;display:flex;justify-content:space-between;
           align-items:center;border-bottom:1px solid var(--border);
           box-shadow:0 1px 20px rgba(124,58,237,.1)}}
  .navbar h1{{color:var(--violet-lit);font-size:1.2rem;font-weight:800;letter-spacing:-.01em}}
  .navbar a{{color:var(--text-muted);text-decoration:none;margin-left:1.5rem;font-size:.9rem;
             font-weight:500;transition:color .15s}}
  .navbar a:hover{{color:var(--violet-lit)}}
  .container{{max-width:1100px;margin:2rem auto;padding:0 1.5rem}}
  .card{{background:var(--surface);border-radius:14px;padding:1.5rem;margin-bottom:1.5rem;
         border:1px solid var(--border);box-shadow:0 4px 24px rgba(0,0,0,.3)}}
  .card h2{{color:var(--violet-lit);margin-bottom:1rem;font-size:1.1rem;font-weight:700}}
  input,select,textarea{{width:100%;padding:.6rem .8rem;background:var(--surface2);
    border:1px solid var(--border);border-radius:8px;color:var(--text);
    font-size:.9rem;margin-top:.3rem;font-family:'Inter',sans-serif}}
  input:focus,select:focus{{outline:none;border-color:var(--violet);
    box-shadow:0 0 0 3px var(--violet-glow)}}
  .btn{{padding:.6rem 1.4rem;border:none;border-radius:8px;cursor:pointer;
        font-size:.9rem;font-weight:600;transition:.2s;font-family:'Inter',sans-serif}}
  .btn-primary{{background:linear-gradient(135deg,var(--violet),var(--violet-dim));color:#fff}}
  .btn-primary:hover{{opacity:.9;transform:translateY(-1px)}}
  .btn-secondary{{background:var(--surface3);color:var(--text)}}
  .btn-secondary:hover{{background:var(--surface2)}}
  .btn-danger{{background:var(--danger);color:#fff}}
  .form-group{{margin-bottom:1rem}}
  .form-group label{{font-size:.85rem;color:var(--text-muted);display:block;
    margin-bottom:.2rem;font-weight:500}}
  .form-row{{display:grid;grid-template-columns:1fr 1fr;gap:1rem}}
  .badge{{display:inline-block;padding:.25rem .7rem;border-radius:20px;
    font-size:.75rem;font-weight:700;letter-spacing:.02em}}
  .badge-critical{{background:rgba(239,68,68,.2);color:#fca5a5;border:1px solid rgba(239,68,68,.4)}}
  .badge-high{{background:rgba(245,158,11,.2);color:#fcd34d;border:1px solid rgba(245,158,11,.4)}}
  .badge-moderate{{background:rgba(124,58,237,.2);color:#a78bfa;border:1px solid rgba(124,58,237,.4)}}
  .badge-low{{background:rgba(16,185,129,.2);color:#6ee7b7;border:1px solid rgba(16,185,129,.4)}}
  table{{width:100%;border-collapse:collapse;font-size:.9rem}}
  th{{text-align:left;padding:.8rem 1rem;background:var(--bg);color:var(--text-muted);
     font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;font-weight:600}}
  td{{padding:.8rem 1rem;border-bottom:1px solid var(--border);color:var(--text)}}
  tr:hover td{{background:var(--surface2)}}
  .alert-success{{background:rgba(16,185,129,.15);color:#6ee7b7;padding:.8rem 1rem;
    border-radius:8px;margin-bottom:1rem;border:1px solid rgba(16,185,129,.3)}}
  .alert-error{{background:rgba(239,68,68,.15);color:#fca5a5;padding:.8rem 1rem;
    border-radius:8px;margin-bottom:1rem;border:1px solid rgba(239,68,68,.3)}}
  .risk-bar{{height:10px;border-radius:5px;background:var(--surface2);margin-top:.4rem}}
  .risk-fill{{height:100%;border-radius:5px}}
  a{{color:var(--violet-lit);text-decoration:none}}
  a:hover{{color:#c4b5fd;text-decoration:underline}}
  h1,h2,h3{{font-weight:700}}
  @media(prefers-color-scheme:light){{
    :root{{--bg:#f5f3ff;--surface:#ffffff;--surface2:#ede9fe;--surface3:#ddd6fe;
      --text:#1e1b4b;--text-muted:#4c1d95;--border:#c4b5fd}}
    tr:hover td{{background:#ede9fe}}
  }}
  [data-theme="dark"]{{
    --bg:#0c0e1a!important;--surface:#111322!important;--surface2:#1a1d30!important;
    --surface3:#252840!important;--text:#e2e4f0!important;--text-muted:#8b90b0!important;
    --border:#2a2d45!important;
  }}
  [data-theme="dark"] td{{color:#e2e4f0!important}}
  [data-theme="dark"] tr:hover td{{background:#1a1d30!important}}
  [data-theme="light"]{{
    --bg:#f5f3ff!important;--surface:#ffffff!important;--surface2:#ede9fe!important;
    --surface3:#ddd6fe!important;--text:#1e1b4b!important;--text-muted:#5b21b6!important;
    --border:#c4b5fd!important;
  }}
  [data-theme="light"] body{{background:#f5f3ff!important}}
  [data-theme="light"] .navbar{{background:#ffffff!important;border-bottom:1px solid #c4b5fd!important}}
  [data-theme="light"] .navbar h1{{color:#6d28d9!important}}
  [data-theme="light"] .navbar a{{color:#5b21b6!important}}
  [data-theme="light"] .navbar a:hover{{color:#7c3aed!important}}
  [data-theme="light"] h1,[data-theme="light"] h2,[data-theme="light"] h3{{color:#1e1b4b!important}}
  [data-theme="light"] td{{color:#1e1b4b!important}}
  [data-theme="light"] th{{color:#4c1d95!important}}
  [data-theme="light"] p{{color:#1e1b4b!important}}
  [data-theme="light"] .card{{background:#ffffff!important;border-color:#c4b5fd!important}}
  [data-theme="light"] tr:hover td{{background:#ede9fe!important}}
  [data-theme="light"] #themeBtn{{background:#ede9fe!important;color:#4c1d95!important;border-color:#c4b5fd!important}}
  [data-theme="light"] input,[data-theme="light"] select,[data-theme="light"] textarea{{background:#ffffff!important;color:#1e1b4b!important;border-color:#c4b5fd!important}}
  [data-theme="light"] input::placeholder,[data-theme="light"] textarea::placeholder{{color:#6b7280!important}}
  [data-theme="light"] .form-group label{{color:#4c1d95!important}}
  [data-theme="light"] .card{{box-shadow:0 4px 24px rgba(124,58,237,.08)!important}}
  [data-theme="light"] span{{color:#1e1b4b!important}}
  [data-theme="light"] small{{color:#4c1d95!important}}
  [data-theme="light"] *{{color:#1e1b4b}}
  [data-theme="light"] .badge-critical{{color:#dc2626!important}}
  [data-theme="light"] .badge-high{{color:#d97706!important}}
  [data-theme="light"] .badge-moderate{{color:#7c3aed!important}}
  [data-theme="light"] .badge-low{{color:#059669!important}}
  [data-theme="light"] .btn-primary{{color:#fff!important}}
  [data-theme="light"] .btn-danger{{color:#fff!important}}
  [data-theme="light"] a{{color:#6d28d9!important}}
  [data-theme="light"] a:hover{{color:#7c3aed!important}}
  [data-theme="light"] .navbar a{{color:#5b21b6!important}}
  [data-theme="light"] #themeBtn{{color:#4c1d95!important}}

        /* ── Dark mode ── */
        body.dark {{ background: #0f0f1a; color: #e2e8f0; }}
        body.dark .card, body.dark .stat-card {{ background: #1a1a2e; border-color: #2d2d4e; }}
        body.dark table thead {{ background: #1a1a2e; }}
        body.dark table tbody tr:hover {{ background: #1f1f35; }}
        body.dark .navbar {{ background: #0f0f1a; border-color: #2d2d4e; }}
        body.dark input, body.dark select {{ background: #1a1a2e; color: #e2e8f0; border-color: #3d3d6e; }}

        /* ── Stat cards ── */
        .stats-row {{ display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }}
        .stat-card {{
            flex: 1; min-width: 140px; background: #fff;
            border: 1px solid #e2e8f0; border-radius: 12px;
            padding: 1rem 1.25rem; text-align: center;
            box-shadow: 0 1px 4px rgba(0,0,0,.06);
        }}
        .stat-card .stat-value {{ font-size: 2rem; font-weight: 700; color: #6c3fcf; }}
        .stat-card .stat-label {{ font-size: .78rem; color: #64748b; margin-top: .2rem; }}
        .stat-card.critical .stat-value {{ color: #ef4444; }}
        .stat-card.high .stat-value    {{ color: #f97316; }}
        .stat-card.avg .stat-value     {{ color: #0ea5e9; }}

        /* ── Search box ── */
        .search-wrap {{ margin-bottom: 1rem; }}
        .search-wrap input {{
            width: 100%; padding: .55rem 1rem; border-radius: 8px;
            border: 1px solid #d1d5db; font-size: .95rem; outline: none;
        }}
        .search-wrap input:focus {{ border-color: #6c3fcf; box-shadow: 0 0 0 3px rgba(108,63,207,.15); }}
</style>
</head>
<body>
<nav class="navbar">
  <h1>ClinicalAI — Decision Support</h1>
  <div style="display:flex;align-items:center;gap:1rem"><button id='themeBtn' onclick='toggleTheme()' style='background:var(--navy-800,#ede9fe);border:1px solid #c4b5fd;color:#6c3fcf;padding:.25rem .8rem;border-radius:20px;cursor:pointer;font-size:.82rem;font-weight:600;font-family:Inter,sans-serif'>&#9790; Dark</button> 
    
    {nav}
    {"<a href='/dashboard'>Dashboard</a><a href='/register-patient'>Register Patient</a><a href='/logout'>Logout</a>" if doctor_name else ""}
  </div>
</nav>
<div class="container">
{body}
</div>
<script>
(function(){{
  var t=localStorage.getItem('theme')||(window.matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');
  document.documentElement.setAttribute('data-theme',t);
  document.addEventListener('DOMContentLoaded',function(){{
    var btn=document.getElementById('themeBtn');
    if(btn)btn.textContent=t==='dark'?'☀ Light':'☾ Dark';
  }});
}})();
function toggleTheme(){{
  var t=document.documentElement.getAttribute('data-theme')==='dark'?'light':'dark';
  document.documentElement.setAttribute('data-theme',t);
  localStorage.setItem('theme',t);
  var btn=document.getElementById('themeBtn');
  if(btn)btn.textContent=t==='dark'?'☀ Light':'☾ Dark';
}}
</script>

        <script>
        function filterPatients() {{
            var inp = document.getElementById('searchInput');
            if (!inp) return;
            var q = inp.value.toLowerCase().trim();
            document.querySelectorAll('#patient-table tr').forEach(function(row) {{
                if (!q) {{ row.style.display = ''; return; }}
                var cells = row.querySelectorAll('td');
                var matched = false;
                cells.forEach(function(td) {{
                    if (td.textContent.toLowerCase().indexOf(q) >= 0) matched = true;
                }});
                row.style.display = matched ? '' : 'none';
            }});
        }}
        async function refreshStats() {{
            try {{
                var r = await fetch('/stats');
                if (!r.ok) return;
                var d = await r.json();
                ['total_analysed','critical_count','high_count','avg_risk_score'].forEach(function(k,i) {{
                    var ids = ['sc-total-val','sc-crit-val','sc-high-val','sc-avg-val'];
                    var el = document.getElementById(ids[i]);
                    if (el) el.textContent = d[k];
                }});
            }} catch(e) {{ console.log('stats err',e); }}
        }}
        refreshStats();
        setInterval(refreshStats, 30000);
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
    from fastapi.responses import FileResponse
    return FileResponse("src/dashboard/login.html")

@app.get("/login-OLD", response_class=HTMLResponse)
async def login_page_old(error: str = ""):
    err_html = f'<div class="alert-error">{error}</div>' if error else ""
    body = f"""
    <div style="max-width:420px;margin:4rem auto">
      <div class="card">
        <h2>🔐 Doctor Login</h2>
        <p style="color:var(--text-muted);font-size:.85rem;margin-bottom:1.5rem">
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
          <td style="color:var(--text-muted);font-size:.8rem">{p['registered_at'][:16]}</td>
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
        <h2 style="color:var(--text);font-size:1.4rem;font-weight:700">Welcome, {doctor['full_name']}</h2>
        <p style="color:var(--text-muted)">{doctor['hospital']} · {len(patients)} patient(s) registered</p>
      </div>
      <a href="/register-patient">
        <button class="btn btn-primary">+ Register Patient</button>
      </a>
    </div>
    <div class="card">
      <!-- Live stats -->
              <div class='stats-row'>
                <div class='stat-card'>
                  <div class='stat-value' id='sc-total-val'>--</div>
                  <div class='stat-label'>Total Analysed</div>
                </div>
                <div class='stat-card critical'>
                  <div class='stat-value' id='sc-crit-val'>--</div>
                  <div class='stat-label'>Critical Alerts</div>
                </div>
                <div class='stat-card high'>
                  <div class='stat-value' id='sc-high-val'>--</div>
                  <div class='stat-label'>High Risk</div>
                </div>
                <div class='stat-card avg'>
                  <div class='stat-value' id='sc-avg-val'>--</div>
                  <div class='stat-label'>Avg Risk Score</div>
                </div>
              </div>
              <h3 style='font-size:1.1rem;font-weight:700;margin-bottom:.75rem'>Your Patients</h3>

            <!-- Search -->
            <div class='search-wrap'>
              <input type='text' id='searchInput'
                     placeholder='Search by name, patient ID, or condition...'
                     oninput='filterPatients()' />
            </div>
      <table>
        <thead><tr>
          <th>Patient ID</th><th>Name</th><th>Age / Gender</th>
          <th>Condition</th><th>Last Risk</th><th>Registered</th><th>Action</th>
        </tr></thead>
        <tbody id='patient-table'>{rows}{empty}</tbody>
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
      <span style="color:var(--text)">{patient['full_name']}</span>
    </div>
    <div class="card">
      <h2>🔬 Clinical Analysis — {disease.name}</h2>
      <div style="color:var(--text-muted);font-size:.85rem;margin-bottom:1.2rem">
        Patient: <strong style="color:var(--text)">{patient['full_name']}</strong> ·
        Age: <strong style="color:var(--text)">{patient['age']}</strong> ·
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

    _db_write_analysis(patient_id, result.risk_score, result.risk_level)
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
        f"<tr><td style='color:var(--text-muted)'>{k.replace('_',' ').title()}</td><td style='color:var(--text)'>{v}</td></tr>"
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
          <p style="color:var(--text-muted);font-size:.85rem;margin-top:.3rem">
            {patient['full_name']} · Age {patient['age']} · {patient['gender']} ·
            <code style="color:#6ee7b7">{row['patient_id']}</code>
          </p>
        </div>
        {_badge(row['risk_level'])}
      </div>
      <div style="margin:1.2rem 0">
        <div style="display:flex;justify-content:space-between;font-size:.85rem;color:var(--text-muted);margin-bottom:.3rem">
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
          <td style="color:var(--text-muted);font-size:.8rem">{a['created_at'][:16]}</td>
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
          <p style="color:var(--text-muted);font-size:.85rem;margin-top:.3rem">
            ID: <code style="color:#6ee7b7">{patient_id}</code> ·
            Age: {patient['age']} · {patient['gender']} ·
            Condition: {disease_name}
          </p>
          <p style="color:var(--text-muted);font-size:.85rem">
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
    </div>
    <div class="card" style="margin-top:1.5rem">
      <h2>Risk Trend</h2>
      <div id="ai-summary" style="margin-bottom:1.2rem;padding:1rem;border-radius:8px;
           background:#1e293b;border-left:4px solid #3b82f6;
           color:var(--text);font-size:0.95rem;min-height:2.5rem">
        Loading summary...
      </div>
      <canvas id="trendChart" height="110"></canvas>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
    <script>
    (function() {{
      var PATIENT_ID = "{patient_id}";
      var LEVEL_COLOR = {{
        CRITICAL: "rgba(220,38,38,1)",
        HIGH:     "rgba(234,88,12,1)",
        MEDIUM:   "rgba(234,179,8,1)",
        LOW:      "rgba(34,197,94,1)"
      }};

      function aiSummary(points) {{
        if (!points || points.length === 0) return "No analysis data available yet.";
        if (points.length === 1) {{
          return "First analysis recorded: " + points[0].risk_level + " (" + points[0].risk_score + "%). Monitor closely.";
        }}
        var first = points[0], last = points[points.length - 1];
        var d1 = new Date(first.timestamp), d2 = new Date(last.timestamp);
        var days = Math.round(Math.abs(d2 - d1) / 86400000);
        var dayStr = days === 0 ? "today" : (days === 1 ? "over 1 day" : "over " + days + " days");
        var diff = last.risk_score - first.risk_score;
        if (diff > 5) {{
          return "Risk has worsened from " + first.risk_level + " (" + first.risk_score + "%) to " +
                 last.risk_level + " (" + last.risk_score + "%) " + dayStr + " - immediate intervention recommended.";
        }} else if (diff < -5) {{
          return "Risk has improved from " + first.risk_level + " (" + first.risk_score + "%) to " +
                 last.risk_level + " (" + last.risk_score + "%) " + dayStr + ".";
        }} else {{
          return "Risk remains stable at approximately " + last.risk_score + "% (" + last.risk_level + ") " + dayStr + ".";
        }}
      }}

      fetch("/patient-trend/" + encodeURIComponent(PATIENT_ID))
        .then(function(r) {{ return r.json(); }})
        .then(function(data) {{
          var points = data.points || [];
          document.getElementById("ai-summary").textContent = aiSummary(points);

          if (points.length === 0) return;

          var labels = points.map(function(p) {{
            var d = new Date(p.timestamp);
            return d.toLocaleDateString([], {{month:"short", day:"numeric"}}) + " " +
                   d.toLocaleTimeString([], {{hour:"2-digit", minute:"2-digit"}});
          }});
          var scores  = points.map(function(p) {{ return p.risk_score; }});
          var colors  = points.map(function(p) {{ return LEVEL_COLOR[p.risk_level] || "#3b82f6"; }});

          new Chart(document.getElementById("trendChart").getContext("2d"), {{
            type: "line",
            data: {{
              labels: labels,
              datasets: [{{
                label: "Risk Score (%)",
                data: scores,
                borderColor: "#3b82f6",
                backgroundColor: "rgba(59,130,246,0.08)",
                pointBackgroundColor: colors,
                pointBorderColor: colors,
                pointRadius: 7,
                pointHoverRadius: 10,
                borderWidth: 2.5,
                tension: 0.3,
                fill: true
              }}]
            }},
            options: {{
              responsive: true,
              scales: {{
                y: {{
                  min: 0, max: 100,
                  title: {{ display: true, text: "Risk Score (%)", color: "#94a3b8" }},
                  ticks: {{ color: "#94a3b8" }},
                  grid:  {{ color: "rgba(148,163,184,0.1)" }}
                }},
                x: {{
                  title: {{ display: true, text: "Analysis Date", color: "#94a3b8" }},
                  ticks: {{ color: "#94a3b8" }},
                  grid:  {{ color: "rgba(148,163,184,0.1)" }}
                }}
              }},
              plugins: {{
                legend: {{ labels: {{ color: "#e2e8f0" }} }},
                tooltip: {{
                  callbacks: {{
                    afterLabel: function(ctx) {{
                      return "Level: " + data.points[ctx.dataIndex].risk_level;
                    }}
                  }}
                }}
              }}
            }}
          }});
        }})
        .catch(function() {{
          document.getElementById("ai-summary").textContent = "Could not load trend data.";
        }});
    }})();
    </script>"""
    body += '''
    <div class='card' style='margin-top:1.5rem'>
      <h3 style='font-size:1rem;font-weight:700;margin-bottom:.75rem'>&#129302; AI Clinical Note Analysis</h3>
      <p style='font-size:.82rem;color:var(--text-muted);margin-bottom:.75rem'>
        Type free-text clinical notes. AI will extract symptoms, diagnoses, medications and vitals automatically.
      </p>
      <textarea id='clinicalNote' rows='4'
        placeholder='e.g. 65F with fever, tachycardia. Suspect sepsis. No chest pain. BP 90/60. Started piperacillin-tazobactam.'
        style='width:100%;padding:.75rem;border-radius:8px;border:1px solid var(--border);background:var(--surface);color:var(--text);font-size:.88rem;font-family:Inter,sans-serif;resize:vertical;box-sizing:border-box'
      ></textarea>
      <button onclick='(async function(){
        var note=document.getElementById("clinicalNote").value.trim();
        if(!note){alert("Please enter a note.");return;}
        this.textContent="Analysing...";this.disabled=true;
        try{
          var pid=window.location.pathname.split("/").pop();
          var r=await fetch("/analyse-note/"+pid,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({note:note})});
          var d=await r.json();
          var res=document.getElementById("noteResults");
          if(d.error){res.innerHTML="<p style=color:#ef4444>"+d.error+"</p>";res.style.display="block";return;}
          function ch(a,c){return a&&a.length?a.map(x=>"<span style=background:"+c+"20;color:"+c+";padding:.2rem .6rem;border-radius:12px;font-size:.78rem;margin:.1rem;display:inline-block>"+x+"</span>").join(""):"<span style=color:#94a3b8;font-size:.8rem>None</span>";}
          var vt=d.vitals&&Object.keys(d.vitals).length?Object.entries(d.vitals).map(([k,v])=>"<span style=background:#f0fdf420;color:#16a34a;padding:.2rem .6rem;border-radius:12px;font-size:.78rem;margin:.1rem;display:inline-block>"+k+": "+v+"</span>").join(""):"<span style=color:#94a3b8;font-size:.8rem>None</span>";
          res.innerHTML="<div style=display:grid;grid-template-columns:1fr_1fr;gap:.75rem>"+
            "<div><p style=font-size:.75rem;font-weight:700;color:#94a3b8;margin-bottom:.3rem>SYMPTOMS/DISEASES</p>"+ch((d.symptoms||[]).concat(d.diagnoses||[]),"#6c3fcf")+"</div>"+
            "<div><p style=font-size:.75rem;font-weight:700;color:#94a3b8;margin-bottom:.3rem>MEDICATIONS</p>"+ch(d.medications||[],"#0ea5e9")+"</div>"+
            "<div><p style=font-size:.75rem;font-weight:700;color:#94a3b8;margin-bottom:.3rem>VITALS</p>"+vt+"</div>"+
            "<div><p style=font-size:.75rem;font-weight:700;color:#94a3b8;margin-bottom:.3rem>NEGATED</p>"+ch(d.negated||[],"#94a3b8")+"</div></div>"+
            "<p style=font-size:.72rem;color:#64748b;margin-top:.5rem>Confidence: "+(d.confidence||"n/a")+" | Entities: "+(d.entity_count||0)+"</p>"+(d.groq_insight?"<div style=margin-top:.75rem;padding:.75rem 1rem;background:linear-gradient(135deg,#1e1b4b,#1e3a5f);border-left:4px solid #6c3fcf;border-radius:8px><p style=font-size:.72rem;font-weight:700;color:#94a3b8;margin-bottom:.3rem>🤖 AI CLINICAL INSIGHT</p><p style=font-size:.9rem;color:#e2e8f0;line-height:1.5;margin:0>"+d.groq_insight+"</p></div>":"");
          res.style.display="block";
        }catch(e){document.getElementById("noteResults").innerHTML="<p style=color:#ef4444>"+e+"</p>";document.getElementById("noteResults").style.display="block";}
        finally{this.textContent="⚡ Analyse Note";this.disabled=false;}
      }).call(this)'
        style='margin-top:.75rem;background:#6c3fcf;color:#fff;border:none;padding:.55rem 1.5rem;border-radius:8px;cursor:pointer;font-size:.9rem;font-weight:600'>
        &#9889; Analyse Note
      </button>
      <div id='noteResults' style='display:none;margin-top:1rem'></div>
    </div>

    <script>
    async function analyseNote() {
        var note = document.getElementById('clinicalNote').value.trim();
        if (!note) { alert('Please enter a clinical note.'); return; }
        var btn = document.querySelector('button[onclick="analyseNote()"]');
        if (btn) { btn.textContent = 'Analysing...'; btn.disabled = true; }
        try {
            var pid = window.location.pathname.split('/').pop();
            var r = await fetch('/analyse-note/' + pid, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({note: note})
            });
            var d = await r.json();
            if (d.error) {
                document.getElementById('noteResults').innerHTML = '<p style="color:#ef4444">Error: ' + d.error + '</p>';
                document.getElementById('noteResults').style.display = 'block';
                return;
            }
            function chips(arr, color) {
                if (!arr || !arr.length) return '<span style="color:#94a3b8;font-size:.8rem">None detected</span>';
                return arr.map(function(x) { return '<span style="background:' + color + '20;color:' + color + ';padding:.2rem .6rem;border-radius:12px;font-size:.78rem;margin:.1rem;display:inline-block">' + x + '</span>'; }).join('');
            }
            var vitals = d.vitals && Object.keys(d.vitals).length
                ? Object.entries(d.vitals).map(function(kv) { return '<span style="background:#f0fdf420;color:#16a34a;padding:.2rem .6rem;border-radius:12px;font-size:.78rem;margin:.1rem;display:inline-block">' + kv[0] + ': ' + kv[1] + '</span>'; }).join('')
                : '<span style="color:#94a3b8;font-size:.8rem">None detected</span>';
            document.getElementById('noteResults').innerHTML =
                '<div style="display:grid;grid-template-columns:1fr 1fr;gap:.75rem;margin-top:.5rem">' +
                '<div><p style="font-size:.75rem;font-weight:700;color:#94a3b8;margin-bottom:.3rem">SYMPTOMS / DISEASES</p>' + chips((d.symptoms||[]).concat(d.diagnoses||[]), '#6c3fcf') + '</div>' +
                '<div><p style="font-size:.75rem;font-weight:700;color:#94a3b8;margin-bottom:.3rem">MEDICATIONS</p>' + chips(d.medications||[], '#0ea5e9') + '</div>' +
                '<div><p style="font-size:.75rem;font-weight:700;color:#94a3b8;margin-bottom:.3rem">VITALS</p>' + vitals + '</div>' +
                '<div><p style="font-size:.75rem;font-weight:700;color:#94a3b8;margin-bottom:.3rem">NEGATED (ruled out)</p>' + chips(d.negated||[], '#94a3b8') + '</div>' +
                '</div><p style="font-size:.72rem;color:#64748b;margin-top:.5rem">Confidence: ' + (d.confidence||'n/a') + ' | Entities: ' + (d.entity_count||0) + '</p>' + (d.groq_insight ? '<div style="margin-top:.75rem;padding:.75rem 1rem;background:linear-gradient(135deg,#1e1b4b,#1e3a5f);border-left:4px solid #6c3fcf;border-radius:8px"><p style="font-size:.72rem;font-weight:700;color:#94a3b8;margin-bottom:.3rem">🤖 AI CLINICAL INSIGHT</p><p style="font-size:.9rem;color:#e2e8f0;line-height:1.5;margin:0">' + d.groq_insight + '</p></div>' : '');
            document.getElementById('noteResults').style.display = 'block';
        } catch(e) {
            document.getElementById('noteResults').innerHTML = '<p style="color:#ef4444">Error: ' + e + '</p>';
            document.getElementById('noteResults').style.display = 'block';
        } finally {
            if (btn) { btn.textContent = '⚡ Analyse Note'; btn.disabled = false; }
        }
    }
    </script>
'''
    return html(_base(patient["full_name"], body, doctor["full_name"]))


# ── Patient Risk Trend ────────────────────────────────────────────────────────

import sqlite3 as _sqlite3

TREND_DB = "logs/analyses.db"

def _get_trend_db():
    conn = _sqlite3.connect(TREND_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id  TEXT NOT NULL,
            risk_score  REAL NOT NULL,
            risk_level  TEXT NOT NULL,
            analysed_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn

def _db_write_analysis(patient_id: str, risk_score: float, risk_level: str) -> None:
    with _get_trend_db() as conn:
        conn.execute(
            "INSERT INTO analyses (patient_id, risk_score, risk_level, analysed_at) VALUES (?, ?, ?, ?)",
            (patient_id, risk_score, risk_level, datetime.now(UTC).isoformat()),
        )

@app.get("/patient-trend/{patient_id}")
async def patient_trend(patient_id: str, session: str | None = Cookie(default=None)):
    require_doctor(session)
    import sqlite3 as _sq2
    rows = []
    try:
        with _get_trend_db() as conn:
            rows = conn.execute(
                "SELECT analysed_at, risk_score, risk_level FROM analyses WHERE patient_id = ? ORDER BY analysed_at ASC LIMIT 20",
                (patient_id,),
            ).fetchall()
    except Exception:
        rows = []
    if not rows:
        db_path = Path("data/clinical.db")
        if db_path.exists():
            con2 = _sq2.connect(str(db_path))
            try:
                rows = con2.execute(
                    "SELECT created_at, risk_score, risk_level FROM analyses WHERE patient_id = ? ORDER BY created_at ASC LIMIT 20",
                    (patient_id,),
                ).fetchall()
            except Exception:
                rows = []
            finally:
                con2.close()
    points = [
        {"timestamp": r[0], "risk_score": round(float(r[1]) * 100, 1), "risk_level": r[2]}
        for r in rows
    ]
    return JSONResponse(content={"patient_id": patient_id, "points": points})


@app.post("/analyse-note/{patient_id}")
async def analyse_note(patient_id: str, request: Request, session: str | None = Cookie(default=None)):
    require_doctor(session)
    data = await request.json()
    note_text = data.get("note", "").strip()
    if not note_text:
        return JSONResponse(content={"error": "No note provided"}, status_code=400)
    try:
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from src.note_parser import ClinicalNoteParser
        parser = ClinicalNoteParser()
        result = parser.parse(note_text)
        # Safely serialize all fields
        def to_str_list(x):
            if not x: return []
            return [str(i) for i in x]
        def safe_vitals(v):
            if not v: return {}
            out = {}
            for item in v:
                key = str(getattr(item, 'vital_type', str(item)))
                val = str(getattr(item, 'value', '')) + ' ' + str(getattr(item, 'unit', ''))
                out[key] = val.strip()
            return out
            if isinstance(v, dict):
                return {str(k): str(val) for k, val in v.items()}
            if isinstance(v, list):
                out = {}
                for item in v:
                    if hasattr(item, "__dict__"):
                        d = item.__dict__
                        key = str(d.get("name", d.get("type", str(item))))
                        val = str(d.get("value", d.get("raw", str(item))))
                        out[key] = val
                    elif hasattr(item, "name"):
                        out[str(item.name)] = str(getattr(item, "value", item))
                    else:
                        out[str(item)] = str(item)
                return out
            return {}
        # --- Groq LLM clinical insight ---
        groq_insight = ""
        try:
            import os as _os
            from groq import Groq
            from dotenv import load_dotenv
            load_dotenv()
            groq_key = _os.getenv("GROQ_API_KEY", "")
            if groq_key:
                groq_client = Groq(api_key=groq_key)
                symptoms_str = ", ".join(to_str_list(result.symptoms)) or "none"
                diseases_str = ", ".join(to_str_list(result.diseases)) or "none"
                meds_str = ", ".join(to_str_list(result.medications)) or "none"
                vitals_str = ", ".join(f"{k}: {v}" for k, v in safe_vitals(result.vitals_mentioned).items()) or "none"
                negated_str = ", ".join(to_str_list(result.negated_entities)) or "none"
                prompt = (
                    "You are a senior clinical decision support AI for an under-resourced Indian hospital.\n"
                    "A doctor wrote a clinical note. The NLP system extracted:\n"
                    f"Symptoms/Diseases: {symptoms_str}\n"
                    f"Diagnoses: {diseases_str}\n"
                    f"Medications: {meds_str}\n"
                    f"Vitals: {vitals_str}\n"
                    f"Negated (absent): {negated_str}\n\n"
                    "Give ONE concise clinical insight the doctor needs to act on RIGHT NOW.\n"
                    "Focus on: sepsis risk, drug-dose warnings, critical vital signs, or urgent referral.\n"
                    "Use Surviving Sepsis Campaign 2021 guidelines where relevant.\n"
                    "Reply in exactly 1-2 sentences. Start with a risk emoji (⚠️ 🔴 💊 ✅).\n"
                    "Do not repeat what the doctor already wrote. Give actionable guidance only."
                )
                chat = groq_client.chat.completions.create(
                    model="groq/compound-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=120,
                    temperature=0.3,
                )
                groq_insight = chat.choices[0].message.content.strip()
        except Exception as ge:
            groq_insight = f"AI insight unavailable: {ge}"

        return JSONResponse(content={
            "symptoms":  to_str_list(result.symptoms),
            "diseases":  to_str_list(result.diseases),
            "diagnoses": to_str_list(result.diagnoses),
            "medications": to_str_list(result.medications),
            "negated":   to_str_list(result.negated_entities),
            "vitals":    safe_vitals(result.vitals_mentioned),
            "confidence": str(result.confidence) if result.confidence else "n/a",
            "entity_count": int(result.entity_count or 0),
            "groq_insight": groq_insight,
        })
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/stats")
async def get_stats(session: str = Cookie(default=None)):
    """Live dashboard stats — auto-detects schema."""
    require_doctor(session)
    import sqlite3 as _sq
    db_path = Path("data/clinical.db")
    if not db_path.exists():
        return {"total_analysed": 0, "critical_count": 0,
                "high_count": 0, "avg_risk_score": 0}
    con = _sq.connect(str(db_path))
    cur = con.cursor()
    try:
        # Discover tables
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cur.fetchall()}

        total, critical, high, avg = 0, 0, 0, 0

        # Try 'analyses' table first, then fall back to 'audit_log'
        for tname in ("analyses", "audit_log", "analysis_log"):
            if tname not in tables:
                continue
            # Discover columns
            cur.execute(f"PRAGMA table_info({tname})")
            cols = {r[1] for r in cur.fetchall()}

            # Total count
            cur.execute(f"SELECT COUNT(*) FROM {tname}")
            total = cur.fetchone()[0]

            # Risk level column — try common names
            risk_col = next((c for c in ("risk_level", "risk", "severity", "level")
                             if c in cols), None)
            if risk_col:
                cur.execute(f"SELECT COUNT(*) FROM {tname} WHERE UPPER({risk_col})='CRITICAL'")
                critical = cur.fetchone()[0]
                cur.execute(f"SELECT COUNT(*) FROM {tname} WHERE UPPER({risk_col})='HIGH'")
                high = cur.fetchone()[0]

            # Risk score column
            score_col = next((c for c in ("risk_score", "score", "risk_value")
                              if c in cols), None)
            if score_col:
                cur.execute(f"SELECT AVG({score_col}) FROM {tname}")
                row = cur.fetchone()[0]
                avg = round(float(row), 1) if row else 0
            break  # used the first matching table

    except Exception:
        print("Stats error: {e}")
        total, critical, high, avg = 0, 0, 0, 0
    finally:
        con.close()
    return {
        "total_analysed": total,
        "critical_count": critical,
        "high_count": high,
        "avg_risk_score": avg,
    }


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0", "diseases": len(DISEASES)}