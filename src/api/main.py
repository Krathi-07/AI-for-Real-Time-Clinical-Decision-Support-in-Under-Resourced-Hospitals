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
    nav = f"<span style='color:#a78bfa;font-weight:600'>👨‍⚕️ {doctor_name}</span>" if doctor_name else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — ClinicalAI</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  :root{{
    --bg:#0c0e1a;--surface:#111827;--surface2:#1a1f35;--surface3:#252a45;
    --violet:#7c3aed;--violet-dim:#6d28d9;--violet-lit:#a78bfa;--violet-glow:rgba(124,58,237,.18);
    --text:#f1f5f9;--text-muted:#94a3b8;--text-dark:#0f172a;--border:#2a2f4a;
    --success:#10b981;--warning:#f59e0b;--danger:#ef4444;
    --navy:#1e3a5f;--navy-dim:#162d4a;--navy-lit:#2563eb;--navy-glow:rgba(30,58,95,.15);
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
    :root{{--bg:#f0f4ff;--surface:#ffffff;--surface2:#e8eef8;--surface3:#d1ddf5;
      --text:#0f172a;--text-muted:#1e3a5f;--border:#93c5fd}}
    tr:hover td{{background:#e8eef8}}
  }}
  [data-theme="dark"]{{
    --bg:#0c0e1a!important;--surface:#111827!important;--surface2:#1a1f35!important;
    --surface3:#252a45!important;--text:#f1f5f9!important;--text-muted:#94a3b8!important;
    --border:#2a2f4a!important;
  }}
  [data-theme="dark"] td{{color:#f1f5f9!important}}
  [data-theme="dark"] th{{color:#94a3b8!important}}
  [data-theme="dark"] tr:hover td{{background:#1a1f35!important}}
  [data-theme="dark"] .stat-card{{background:#1a1f35!important;border:1px solid #2a2f4a!important}}
  [data-theme="dark"] .stat-card .stat-label{{color:#94a3b8!important;font-weight:600!important}}
  [data-theme="dark"] .stat-card .stat-value{{color:#ffffff!important;font-weight:800!important}}
  [data-theme="dark"] .stat-card.critical .stat-value{{color:#f87171!important}}
  [data-theme="dark"] .stat-card.high .stat-value{{color:#fb923c!important}}
  [data-theme="dark"] .stat-card.avg .stat-value{{color:#818cf8!important}}
  [data-theme="light"]{{
    --bg:#f0f4ff!important;--surface:#ffffff!important;--surface2:#e8eef8!important;
    --surface3:#d1ddf5!important;--text:#0f172a!important;--text-muted:#1e3a5f!important;
    --border:#93c5fd!important;
  }}
  [data-theme="light"] body{{background:#f0f4ff!important;color:#0f172a!important}}
  [data-theme="light"] .navbar{{background:#1e3a5f!important;border-bottom:1px solid #162d4a!important;box-shadow:0 2px 12px rgba(30,58,95,.3)!important}}
  [data-theme="light"] .navbar h1{{color:#ffffff!important}}
  [data-theme="light"] .navbar a{{color:#bfdbfe!important}}
  [data-theme="light"] .navbar a:hover{{color:#ffffff!important}}
  [data-theme="light"] #themeBtn{{background:#162d4a!important;color:#bfdbfe!important;border-color:#2563eb!important}}
  [data-theme="light"] h1,[data-theme="light"] h2,[data-theme="light"] h3{{color:#0f172a!important}}
  [data-theme="light"] td{{color:#0f172a!important}}
  [data-theme="light"] th{{color:#1e3a5f!important;font-weight:700!important}}
  [data-theme="light"] p{{color:#0f172a!important}}
  [data-theme="light"] .card{{background:#ffffff!important;border-color:#93c5fd!important;box-shadow:0 4px 24px rgba(30,58,95,.1)!important}}
  [data-theme="light"] tr:hover td{{background:#e8eef8!important}}
  [data-theme="light"] input,[data-theme="light"] select,[data-theme="light"] textarea{{background:#ffffff!important;color:#0f172a!important;border-color:#93c5fd!important}}
  [data-theme="light"] input::placeholder,[data-theme="light"] textarea::placeholder{{color:#475569!important}}
  [data-theme="light"] .form-group label{{color:#1e3a5f!important;font-weight:600!important}}
  [data-theme="light"] span{{color:#0f172a!important}}
  [data-theme="light"] small{{color:#1e3a5f!important}}
  [data-theme="light"] li{{color:#0f172a!important;font-weight:500}}
  [data-theme="light"] .card li{{color:#0f172a!important}}
  [data-theme="light"] .badge-critical{{color:#dc2626!important}}
  [data-theme="light"] .badge-high{{color:#b45309!important}}
  [data-theme="light"] .badge-moderate{{color:#1d4ed8!important}}
  [data-theme="light"] .badge-low{{color:#059669!important}}
  [data-theme="light"] .btn-primary{{background:linear-gradient(135deg,#1e3a5f,#2563eb)!important;color:#fff!important}}
  [data-theme="light"] .btn-primary:hover{{opacity:.9!important}}
  [data-theme="light"] .btn-danger{{color:#fff!important}}
  [data-theme="light"] .btn-secondary{{background:#e8eef8!important;color:#1e3a5f!important;border:1px solid #93c5fd!important}}
  [data-theme="light"] a{{color:#1d4ed8!important}}
  [data-theme="light"] a:hover{{color:#2563eb!important}}
  [data-theme="light"] .navbar a{{color:#bfdbfe!important}}
  [data-theme="light"] .stat-card{{background:#ffffff!important;border-color:#93c5fd!important}}
  [data-theme="light"] .stat-card .stat-label{{color:#1e3a5f!important;font-weight:600!important}}
  [data-theme="light"] .stat-card .stat-value{{color:#0f172a!important}}
  [data-theme="light"] .stat-card.critical .stat-value{{color:#dc2626!important}}
  [data-theme="light"] .stat-card.high .stat-value{{color:#b45309!important}}
  [data-theme="light"] .stat-card.avg .stat-value{{color:#1d4ed8!important}}
  [data-theme="light"]{{--finding-color:#b45309;--rec-color:#059669}}
  [data-theme="light"] .card{{border-left-color:inherit}}
  [data-theme="light"] h2{{color:#0f172a!important}}
  [data-theme="light"] .card h2{{color:#1e3a5f!important}}
  [data-theme="light"] code{{color:#1d4ed8!important;background:#e8eef8;padding:1px 5px;border-radius:4px}}
  [data-theme="dark"]{{--finding-color:#fcd34d;--rec-color:#4ade80}}

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
        /* AI summary note — always readable */
        [data-theme="light"] #ai-summary {{
            background: #1e293b !important;
            color: #e2e8f0 !important;
            border-left: 4px solid #3b82f6 !important;
        }}
</style>
</head>
<body>
<nav class="navbar">
  <h1>ClinicalAI — Decision Support</h1>
  <div style="display:flex;align-items:center;gap:1rem"><button id='themeBtn' onclick='toggleTheme()' style='background:var(--navy-800,#ede9fe);border:1px solid #c4b5fd;color:#6c3fcf;padding:.25rem .8rem;border-radius:20px;cursor:pointer;font-size:.82rem;font-weight:600;font-family:Inter,sans-serif'>&#9790; Dark</button> 
    
    {nav}
    {"<a href='/dashboard'>Dashboard</a><a href='/discharged'>Discharged</a><a href='/register-patient'>Register Patient</a><a href='/logout'>Logout</a>" if doctor_name else ""}
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
        async function dischargePatient(pid) {{
            if (!confirm('Discharge patient ' + pid + '? They will be hidden from active list.')) return;
            var r = await fetch('/discharge/' + pid, {{method:'POST'}});
            if (r.ok) {{ location.reload(); }}
            else {{ alert('Could not discharge patient.'); }}
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
    err_html = f'<div style="background:rgba(239,68,68,.15);color:#fca5a5;padding:.65rem 1rem;border-radius:8px;margin-bottom:1rem;border:1px solid rgba(239,68,68,.3);font-size:.85rem">{error}</div>' if error else ""
    page = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Login — ClinicalAI</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#f5f3ff}
.wrap{display:flex;width:100%;max-width:900px;min-height:520px;border-radius:20px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.18)}
/* LEFT PANEL */
.left{flex:1;background:linear-gradient(145deg,#0c0e1a 0%,#1a1040 60%,#0f1035 100%);padding:3rem 2.5rem;display:flex;flex-direction:column;justify-content:space-between;position:relative;overflow:hidden}
.left::before{content:'';position:absolute;top:-60px;right:-60px;width:220px;height:220px;background:rgba(124,58,237,.15);border-radius:50%}
.left::after{content:'';position:absolute;bottom:-40px;left:-40px;width:160px;height:160px;background:rgba(59,130,246,.1);border-radius:50%}
.badge{display:inline-block;background:rgba(124,58,237,.25);color:#a78bfa;border:1px solid rgba(124,58,237,.4);padding:.3rem .8rem;border-radius:20px;font-size:.72rem;font-weight:700;letter-spacing:.08em;margin-bottom:1.5rem}
.left h1{color:#fff;font-size:2rem;font-weight:800;line-height:1.2;margin-bottom:.5rem}
.left h1 span{color:#a78bfa}
.tagline{color:#6ee7b7;font-size:.9rem;font-weight:600;margin-bottom:2rem}
.feature{display:flex;align-items:flex-start;gap:.75rem;margin-bottom:1.1rem}
.feature-icon{width:36px;height:36px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:1rem;flex-shrink:0}
.feature-icon.purple{background:rgba(124,58,237,.25)}
.feature-icon.blue{background:rgba(59,130,246,.2)}
.feature-icon.green{background:rgba(16,185,129,.2)}
.feature-icon.orange{background:rgba(249,115,22,.2)}
.feature-text strong{display:block;color:#e2e8f0;font-size:.88rem;font-weight:600}
.feature-text span{color:#8b90b0;font-size:.78rem}
.footer-tech{color:#475569;font-size:.75rem;margin-top:auto;padding-top:1.5rem}
/* RIGHT PANEL */
.right{flex:1;background:#fff;padding:3rem 2.5rem;display:flex;flex-direction:column;justify-content:center}
.right h2{font-size:1.6rem;font-weight:800;color:#1e1b4b;margin-bottom:.3rem}
.right p{color:#64748b;font-size:.88rem;margin-bottom:1.75rem}
label{display:block;font-size:.82rem;font-weight:600;color:#374151;margin-bottom:.4rem}
input{width:100%;padding:.7rem 1rem;border:1.5px solid #e5e7eb;border-radius:10px;font-size:.92rem;font-family:'Inter',sans-serif;color:#1e1b4b;outline:none;transition:.2s}
input:focus{border-color:#7c3aed;box-shadow:0 0 0 3px rgba(124,58,237,.12)}
.form-group{margin-bottom:1.1rem}
.btn-login{width:100%;padding:.8rem;background:linear-gradient(135deg,#7c3aed,#6d28d9);color:#fff;border:none;border-radius:10px;font-size:1rem;font-weight:700;cursor:pointer;margin-top:.5rem;font-family:'Inter',sans-serif;transition:.2s}
.btn-login:hover{opacity:.92;transform:translateY(-1px)}
.hint{font-size:.75rem;color:#9ca3af;text-align:center;margin-top:1rem}
.hint strong{color:#6b7280}
@media(max-width:640px){.wrap{flex-direction:column;border-radius:0;min-height:100vh}.left{padding:2rem 1.5rem}.right{padding:2rem 1.5rem}}
</style>
</head>
<body>
<div class="wrap">
  <!-- LEFT: Project Info -->
  <div class="left">
    <div>
      <div class="badge">MHSSCE &middot; CAPSTONE 2026</div>
      <h1>AI Clinical<br><span>Decision Support</span></h1>
      <p class="tagline">Virtual Junior Doctor for Tier-2/3 Hospitals</p>
      <div class="feature">
        <div class="feature-icon purple">🧠</div>
        <div class="feature-text">
          <strong>XGBoost + scispaCy NLP</strong>
          <span>Sepsis detection &amp; clinical note analysis</span>
        </div>
      </div>
      <div class="feature">
        <div class="feature-icon blue">📊</div>
        <div class="feature-text">
          <strong>Real-Time Risk Scoring</strong>
          <span>SOFA, qSOFA &amp; multi-disease assessment</span>
        </div>
      </div>
      <div class="feature">
        <div class="feature-icon green">🔒</div>
        <div class="feature-text">
          <strong>DISHA Compliant</strong>
          <span>Patient data stays local — no cloud uploads</span>
        </div>
      </div>
      <div class="feature">
        <div class="feature-icon orange">⚡</div>
        <div class="feature-text">
          <strong>LangGraph Agent Pipeline</strong>
          <span>Groq LLM for AI clinical insights</span>
        </div>
      </div>
    </div>
    <div class="footer-tech">FastAPI &middot; LangGraph &middot; XGBoost &middot; scispaCy &middot; ReportLab</div>
  </div>
  <!-- RIGHT: Login Form -->
  <div class="right">
    <h2>Doctor Login</h2>
    <p>Access the clinical decision support system</p>
    """ + err_html + """
    <form method="post" action="/login">
      <div class="form-group">
        <label>Username</label>
        <input name="username" placeholder="doctor" required autocomplete="username">
      </div>
      <div class="form-group">
        <label>Password</label>
        <input type="password" name="password" placeholder="••••••••" required autocomplete="current-password">
      </div>
      <button class="btn-login" type="submit">Sign in</button>
    </form>
    <p class="hint">Default: <strong>doctor</strong> / <strong>clinical2026</strong></p>
  </div>
</div>
</body>
</html>"""
    return HTMLResponse(page)

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
    import sqlite3 as _sqd2
    discharged_ids = set()
    for db_path_d in [Path("logs/analyses.db"), Path("data/clinical.db"), Path("/tmp/clinical.db")]:
        try:
            if not db_path_d.exists():
                continue
            con_d = _sqd2.connect(str(db_path_d))
            rows_d = con_d.execute("SELECT patient_id FROM discharged_patients").fetchall()
            discharged_ids.update(r[0] for r in rows_d)
            con_d.close()
        except Exception:
            pass
    all_patients = get_patients_for_doctor(doctor["id"])
    patients = [p for p in all_patients if p["patient_id"] not in discharged_ids and not p.get("discharged")]

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
          <td style="display:flex;gap:.4rem;align-items:center">
            <a href="/analyse/{p['patient_id']}">
              <button class="btn btn-primary" style="padding:.3rem .8rem;font-size:.8rem">Analyse</button>
            </a>
            <button onclick="dischargePatient('{p['patient_id']}')"
              style="padding:.3rem .8rem;font-size:.8rem;background:#ef4444;color:#fff;border:none;border-radius:8px;cursor:pointer;font-weight:600">
              Discharge
            </button>
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
                <div class='stat-card' style='border-top:3px solid #6b7280'>
                  <div class='stat-value' id='sc-disc-val' style='color:#6b7280'>--</div>
                  <div class='stat-label'>Discharged</div>
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
    # Check for duplicate patient (same name + age)
    import sqlite3 as _sqdup
    db_path_dup = Path("data/clinical.db")
    if db_path_dup.exists():
        con_dup = _sqdup.connect(str(db_path_dup))
        existing = con_dup.execute(
            "SELECT patient_id FROM patients WHERE LOWER(full_name)=LOWER(?) AND age=? AND doctor_id=?",
            (full_name, age, doctor["id"])
        ).fetchone()
        con_dup.close()
        if existing:
            return RedirectResponse(
                f"/register-patient?msg=WARNING:+Patient+{full_name}+age+{age}+already+exists+as+{existing[0]}",
                status_code=303
            )
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

    findings_html = "".join(f"<li style='margin:.4rem 0;color:var(--finding-color,#b45309);font-weight:500'>⚠ {f}</li>" for f in findings)
    recs_html = "".join(f"<li style='margin:.4rem 0;color:var(--rec-color,#059669);font-weight:500'>→ {r}</li>" for r in recs)
    params_html = "".join(
        f"<tr><td style='color:var(--text-muted);font-weight:500'>{k.replace('_',' ').title()}</td><td style='color:var(--text);font-weight:600'>{v}</td></tr>"
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
      <div class="card" style="border-left:4px solid var(--warning)">
        <h2 style="color:var(--warning)">🔍 Clinical Findings</h2>
        <ul style="list-style:none;padding:0">{findings_html}</ul>
      </div>
      <div class="card" style="border-left:4px solid var(--success)">
        <h2 style="color:var(--success)">💊 Recommendations</h2>
        <ul style="list-style:none;padding:0">{recs_html}</ul>
      </div>
    </div>
    <div class="card" style="border-left:4px solid var(--violet-lit)">
      <h2 style="color:var(--violet-lit)">📊 Parameters Entered</h2>
      <table><tbody>{params_html}</tbody></table>
    </div>
    <div style="display:flex;gap:1rem;margin-top:1rem;flex-wrap:wrap">
      <a href="/report/{analysis_id}">
        <button class="btn btn-primary">📄 Download PDF Report</button>
      </a>
      <a href="https://wa.me/?text=Patient%20{row['patient_id']}%20-%20{patient['full_name']}%20Risk%3A%20{row['risk_level']}%20({pct}%25)%20-%20ClinicalAI%20Report%3A%20https%3A%2F%2Fai-for-real-time-clinical-decision.onrender.com%2Freport%2F{analysis_id}" target="_blank">
        <button class="btn btn-secondary" style="background:#25D366;color:#fff">💬 Share via WhatsApp</button>
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
                  title: {{ display: true, text: "Risk Score (%)", color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#94a3b8" }},
                  ticks: {{ color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#94a3b8" }},
                  grid:  {{ color: "rgba(148,163,184,0.1)" }}
                }},
                x: {{
                  title: {{ display: true, text: "Analysis Date", color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#94a3b8" }},
                  ticks: {{ color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#94a3b8" }},
                  grid:  {{ color: "rgba(148,163,184,0.1)" }}
                }}
              }},
              plugins: {{
                legend: {{ labels: {{ color: document.documentElement.getAttribute("data-theme")==="light" ? "#1e1b4b" : "#e2e8f0" }} }},
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
        import os
        import sys
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
            groq_key = _os.environ.get("GROQ_API_KEY", "")
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
                    model="llama3-8b-8192",
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


@app.post("/discharge/{patient_id}")
async def discharge_patient(patient_id: str, session: str | None = Cookie(default=None)):
    require_doctor(session)
    import sqlite3 as _sq
    # Try main db first, fall back to trend db
    for db_path in [Path("logs/analyses.db"), Path("data/clinical.db"), Path("/tmp/clinical.db")]:
        try:
            if not db_path.exists() and str(db_path) not in ["/tmp/clinical.db", "logs/analyses.db"]:
                continue
            Path("logs").mkdir(parents=True, exist_ok=True)
            conn = _sq.connect(str(db_path))
            # Create discharged table if not exists (for fallback DBs)
            conn.execute("""CREATE TABLE IF NOT EXISTS discharged_patients
                (patient_id TEXT PRIMARY KEY, discharged_at TEXT)""")
            conn.execute("INSERT OR REPLACE INTO discharged_patients (patient_id, discharged_at) VALUES (?, ?)",
                (patient_id, datetime.now(UTC).isoformat()))
            # Also try updating patients table
            try:
                conn.execute("UPDATE patients SET discharged=1 WHERE patient_id=?", (patient_id,))
            except Exception:
                pass
            conn.commit()
            conn.close()
            return {"status": "discharged", "patient_id": patient_id}
        except Exception:
            continue
    raise HTTPException(500, "Could not discharge patient")


@app.get("/discharged", response_class=HTMLResponse)
async def discharged_page(session: str | None = Cookie(default=None)):
    doctor = require_doctor(session)
    import sqlite3 as _sqdisp
    rows_data = []
    for db_path_d in [Path("logs/analyses.db"), Path("data/clinical.db"), Path("/tmp/clinical.db")]:
        try:
            con_d = _sqdisp.connect(str(db_path_d))
            results = con_d.execute("""
                SELECT dp.patient_id, dp.discharged_at,
                       p.full_name, p.age, p.gender, p.disease_id
                FROM discharged_patients dp
                LEFT JOIN patients p ON dp.patient_id = p.patient_id
                ORDER BY dp.discharged_at DESC
            """).fetchall()
            con_d.close()
            if results:
                rows_data = results
                break
        except Exception:
            continue

    rows_html = ""
    for r in rows_data:
        pid, disc_at, name, age, gender, disease_id = r
        disease_name = DISEASES.get(disease_id or "", type("x", (), {"name": disease_id or "Unknown"})()).name
        disc_time = disc_at[:16] if disc_at else "—"
        name = name or "Unknown"
        age_gen = f"{age} yrs / {gender}" if age else "—"
        rows_html += f"""<tr>
          <td><a href="/patient/{pid}">{pid}</a></td>
          <td>{name}</td>
          <td>{age_gen}</td>
          <td>{disease_name}</td>
          <td style="color:var(--text-muted);font-size:.85rem">{disc_time}</td>
          <td><span class="badge badge-low">✓ Discharged</span></td>
        </tr>"""

    empty = "<tr><td colspan='6' style='text-align:center;color:var(--text-muted);padding:2rem'>No discharged patients yet</td></tr>" if not rows_html else ""

    body = f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.5rem">
      <div>
        <h2 style="color:var(--text);font-size:1.4rem;font-weight:700">Discharged Patients</h2>
        <p style="color:var(--text-muted)">Patients who have been discharged from care</p>
      </div>
      <a href="/dashboard"><button class="btn btn-secondary">← Back to Dashboard</button></a>
    </div>
    <div class="card">
      <table>
        <thead><tr>
          <th>Patient ID</th><th>Name</th><th>Age / Gender</th>
          <th>Condition</th><th>Discharged At</th><th>Status</th>
        </tr></thead>
        <tbody>{rows_html}{empty}</tbody>
      </table>
    </div>"""
    return html(_base("Discharged Patients", body, doctor["full_name"]))

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
    # Count discharged patients — check all possible DB locations
    discharged = 0
    try:
        import sqlite3 as _sqd
        for db_path2 in [Path("logs/analyses.db"), Path("data/clinical.db"), Path("/tmp/clinical.db")]:
            try:
                con3 = _sqd.connect(str(db_path2))
                row3 = con3.execute("SELECT COUNT(*) FROM discharged_patients").fetchone()
                con3.close()
                if row3 and row3[0] > 0:
                    discharged = row3[0]
                    break
            except Exception:
                continue
    except Exception:
        discharged = 0

    return {
        "total_analysed": total,
        "critical_count": critical,
        "high_count": high,
        "avg_risk_score": avg,
        "discharged_count": discharged,
    }



@app.get("/report/{analysis_id}")
async def download_report(analysis_id: int, session: str | None = Cookie(default=None)):
    """Generate and stream a professional PDF report."""
    import io

    from fastapi.responses import StreamingResponse
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    doctor = require_doctor(session)
    from src.database.db import get_connection
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
    pct = int(row["risk_score"] * 100)
    disease = DISEASES.get(row["disease_id"], type("x", (), {"name": row["disease_id"], "icd10": "---"})())
    disease_name = disease.name
    icd10 = getattr(disease, "icd10", "---")
    risk_colors_map = {"CRITICAL": "#dc2626", "HIGH": "#ea580c", "MODERATE": "#2563eb", "LOW": "#16a34a"}
    risk_hex = risk_colors_map.get(row["risk_level"], "#2563eb")

    NORMAL_RANGES = {
        "heart_rate": (60, 100, "bpm"),
        "systolic_bp": (90, 140, "mmHg"),
        "diastolic_bp": (60, 90, "mmHg"),
        "temperature": (36.1, 38.0, "C"),
        "spo2": (95, 100, "%"),
        "respiratory_rate": (12, 20, "/min"),
        "troponin_i": (0, 0.04, "ng/mL"),
        "wbc": (4.5, 11.0, "x10/uL"),
        "creatinine": (0.6, 1.2, "mg/dL"),
        "sodium": (135, 145, "mEq/L"),
        "glucose": (70, 140, "mg/dL"),
        "bmi": (18.5, 24.9, "kg/m2"),
    }

    buf = io.BytesIO()
    W = 17.4 * cm
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=1.8*cm, rightMargin=1.8*cm,
                            topMargin=1.8*cm, bottomMargin=1.8*cm)
    story = []

    def ps(name, **kw):
        return ParagraphStyle(name, **kw)

    sec_s  = ps("sec", fontSize=10, fontName="Helvetica-Bold", textColor=colors.HexColor("#374151"), spaceBefore=10, spaceAfter=4)
    body_s = ps("b", fontSize=9, leading=14, textColor=colors.HexColor("#1f2937"), spaceAfter=4)

    # HEADER
    hdr_data = [[
        Paragraph("<b>ClinicalAI - Decision Support System</b>",
                  ps("hh", fontSize=14, fontName="Helvetica-Bold", textColor=colors.HexColor("#111827"))),
        Paragraph(f"<b>Report ID: {analysis_id}</b>",
                  ps("rid", fontSize=9, textColor=colors.HexColor("#6b7280"), alignment=2)),
    ]]
    ht = Table(hdr_data, colWidths=[W*0.7, W*0.3])
    ht.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("PADDING",(0,0),(-1,-1),0)]))
    story.append(ht)
    story.append(Paragraph(
        "AI-Assisted Medical Report | <b>Confidential</b>",
        ps("conf", fontSize=8, textColor=colors.HexColor("#6b7280"), spaceAfter=2)
    ))
    story.append(Paragraph(
        f"Generated: {datetime.now(UTC).strftime('%d %B %Y, %H:%M UTC')} | Doctor: {doctor['full_name']} | Hospital: {doctor.get('hospital','--')}",
        ps("sub", fontSize=9, textColor=colors.HexColor("#6b7280"), spaceAfter=4)
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#e5e7eb"), spaceAfter=8))

    # PATIENT INFO
    story.append(Paragraph("Patient Information", sec_s))
    pi = [
        ["Patient ID", row["patient_id"], "Full Name", patient["full_name"]],
        ["Age", f"{patient['age']} years", "Gender", patient["gender"]],
        ["Phone", patient.get("phone") or "--", "Address", patient.get("address") or "--"],
        ["Condition", disease_name, "ICD-10", icd10],
        ["Attending Doctor", doctor["full_name"], "Hospital", doctor.get("hospital","--")],
        ["Analysis Date", row.get("created_at","")[:16], "Report Generated", datetime.now(UTC).strftime("%d %B %Y, %H:%M UTC")],
    ]
    pt = Table(pi, colWidths=[3*cm, 5.7*cm, 3*cm, 5.7*cm])
    pt.setStyle(TableStyle([
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
        ("FONTNAME",(2,0),(2,-1),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),8.5),
        ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#f9fafb")),
        ("BACKGROUND",(2,0),(2,-1),colors.HexColor("#f9fafb")),
        ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#e5e7eb")),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white, colors.HexColor("#f9fafb")]),
        ("PADDING",(0,0),(-1,-1),5),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    story.append(pt)
    story.append(Spacer(1, 0.3*cm))

    # RISK SUMMARY
    story.append(Paragraph("Risk Assessment Summary", sec_s))
    risk_data = [
        ["Risk Level", "Risk Score", "Disease", "ICD-10 Code"],
        [row["risk_level"], f"{pct}%", disease_name, icd10],
    ]
    rt = Table(risk_data, colWidths=[3.5*cm, 3*cm, 7.9*cm, 3*cm])
    rt.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#111827")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),9),
        ("BACKGROUND",(0,1),(0,1),colors.HexColor(risk_hex)),
        ("TEXTCOLOR",(0,1),(0,1),colors.white),
        ("FONTNAME",(0,1),(0,1),"Helvetica-Bold"),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#e5e7eb")),
        ("PADDING",(0,0),(-1,-1),6),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    story.append(rt)
    story.append(Spacer(1, 0.3*cm))

    # PARAMETERS WITH NORMAL RANGE
    story.append(Paragraph("Clinical Parameters Recorded", sec_s))
    param_rows = [["Parameter", "Value Recorded", "Normal Range", "Status"]]
    for k, v in params.items():
        norm = NORMAL_RANGES.get(k)
        if norm:
            lo, hi, unit = norm
            try:
                fv = float(v)
                if fv > hi:
                    status = "HIGH"
                elif fv < lo:
                    status = "LOW"
                else:
                    status = "Normal"
                range_str = f"{lo}-{hi} {unit}"
                val_str = f"{v} {unit}"
            except (ValueError, TypeError):
                status = "--"
                range_str = f"{lo}-{hi} {unit}"
                val_str = str(v)
        else:
            status = "--"
            range_str = "--"
            val_str = str(v)
        param_rows.append([k.replace("_"," ").title(), val_str, range_str, status])

    param_t = Table(param_rows, colWidths=[4.5*cm, 4*cm, 5*cm, 3.9*cm])
    param_style = [
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#111827")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),8.5),
        ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#e5e7eb")),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f9fafb")]),
        ("PADDING",(0,0),(-1,-1),5),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]
    for i, rd in enumerate(param_rows[1:], start=1):
        if rd[3] == "HIGH":
            param_style += [("TEXTCOLOR",(3,i),(3,i),colors.HexColor("#dc2626")),("FONTNAME",(3,i),(3,i),"Helvetica-Bold")]
        elif rd[3] == "LOW":
            param_style += [("TEXTCOLOR",(3,i),(3,i),colors.HexColor("#ea580c")),("FONTNAME",(3,i),(3,i),"Helvetica-Bold")]
        elif rd[3] == "Normal":
            param_style.append(("TEXTCOLOR",(3,i),(3,i),colors.HexColor("#16a34a")))
    param_t.setStyle(TableStyle(param_style))
    story.append(param_t)
    story.append(Spacer(1, 0.3*cm))

    # FINDINGS
    story.append(Paragraph("Clinical Findings", sec_s))
    for fi in findings:
        story.append(Paragraph(f"- {fi}", body_s))
    story.append(Spacer(1, 0.2*cm))

    # RECOMMENDATIONS
    story.append(Paragraph("Medical Recommendations", sec_s))
    for r in recs:
        story.append(Paragraph(f"-> {r}", body_s))
    story.append(Spacer(1, 0.4*cm))

    # SIGNATURE
    sig_t = Table([["Doctor Signature: __________________", "Date: __________________"]], colWidths=[W/2, W/2])
    sig_t.setStyle(TableStyle([("FONTSIZE",(0,0),(-1,-1),9),("TEXTCOLOR",(0,0),(-1,-1),colors.HexColor("#374151")),("PADDING",(0,0),(-1,-1),4)]))
    story.append(sig_t)
    story.append(Spacer(1, 0.3*cm))

    # FOOTER
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#e5e7eb")))
    story.append(Paragraph(
        "DISCLAIMER: This report is AI-generated and intended to assist clinical decision-making only. "
        "It does not replace professional medical judgement. The attending doctor must review and validate "
        "all findings before any clinical action is taken. ClinicalAI - DISHA Compliant.",
        ps("disc", fontSize=7.5, textColor=colors.HexColor("#9ca3af"), leading=11, spaceBefore=4)
    ))

    doc.build(story)
    buf.seek(0)
    filename = f"ClinicalAI_Report_{row['patient_id']}_{disease_name.replace(' ','_')}_{analysis_id}.pdf"
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0", "diseases": len(DISEASES)}

