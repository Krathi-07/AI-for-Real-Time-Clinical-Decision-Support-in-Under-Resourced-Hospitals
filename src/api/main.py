"""
Clinical AI Decision Support — FastAPI Backend
Handles: auth, patient registration, disease analysis, dashboard
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from fastapi import Cookie, FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
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


# ── HTML helpers ──────────────────────────────────────────────────────────────

def html(content: str) -> HTMLResponse:
    return HTMLResponse(content)


def _base(title: str, body: str, doctor_name: str = "") -> str:
    nav_links = ""
    if doctor_name:
        nav_links = """
        <a href='/dashboard'>Dashboard</a>
        <a href='/about'>About</a>
        <a href='/register-patient'>Register Patient</a>
        <a href='/logout'>Logout</a>"""

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — ClinicalAI</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root[data-theme="dark"] {{
    --bg: #0a0f1e;
    --surface: #0f1629;
    --surface2: #162040;
    --border: #1e3a5f;
    --text: #f1f5f9;
    --text-muted: #94a3b8;
    --accent: #3b82f6;
    --accent-hover: #2563eb;
    --accent-light: #60a5fa;
    --row-alt: #0d1830;
    --th-bg: #0a0f1e;
    --input-bg: #070d1a;
    --alert-ok-bg: #14532d;
    --alert-ok-text: #86efac;
    --alert-err-bg: #7f1d1d;
    --alert-err-text: #fca5a5;
    --shadow: 0 2px 12px rgba(0,0,0,0.4);
  }}
  :root[data-theme="light"] {{
    --bg: #f0f4f8;
    --surface: #ffffff;
    --surface2: #e8f0fe;
    --border: #c7d7ed;
    --text: #0a1628;
    --text-muted: #3d5a80;
    --accent: #1d4ed8;
    --accent-hover: #1e40af;
    --accent-light: #3b82f6;
    --row-alt: #f8faff;
    --th-bg: #e8f0fe;
    --input-bg: #f8faff;
    --alert-ok-bg: #dcfce7;
    --alert-ok-text: #166534;
    --alert-err-bg: #fee2e2;
    --alert-err-text: #991b1b;
    --shadow: 0 2px 12px rgba(0,0,0,0.08);
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0 }}
  body {{
    font-family: 'Inter', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    font-size: 15px;
    line-height: 1.6;
  }}
  input, select, textarea, button, .btn {{
    font-family: 'Inter', sans-serif;
  }}
  .navbar {{
    background: var(--surface);
    padding: 0.9rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 2px solid var(--accent);
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: var(--shadow);
  }}
  .navbar h1 {{
    color: var(--accent-light);
    font-size: 1.15rem;
    font-weight: 800;
    letter-spacing: -0.3px;
  }}
  .navbar a {{
    color: var(--text-muted);
    text-decoration: none;
    margin-left: 1.5rem;
    font-size: 0.9rem;
    font-weight: 500;
    transition: 0.15s;
  }}
  .navbar a:hover {{ color: var(--accent-light) }}
  .doc-name {{
    color: var(--accent-light);
    font-weight: 600;
    font-size: 0.9rem;
  }}
  .theme-btn {{
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text-muted);
    padding: 0.35rem 0.9rem;
    border-radius: 20px;
    cursor: pointer;
    font-size: 0.82rem;
    margin-left: 1.25rem;
    font-weight: 500;
    transition: 0.15s;
  }}
  .theme-btn:hover {{ border-color: var(--accent); color: var(--accent-light) }}
  .container {{ max-width: 1150px; margin: 2rem auto; padding: 0 1.5rem }}
  .card {{
    background: var(--surface);
    border-radius: 12px;
    padding: 1.75rem;
    margin-bottom: 1.5rem;
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
  }}
  .card h2 {{
    color: var(--accent-light);
    margin-bottom: 1rem;
    font-size: 1.1rem;
    font-weight: 700;
  }}
  input, select, textarea {{
    width: 100%;
    padding: 0.65rem 0.9rem;
    background: var(--input-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    font-size: 0.95rem;
    margin-top: 0.3rem;
    transition: 0.15s;
  }}
  input:focus, select:focus {{
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(59,130,246,0.15);
  }}
  .btn {{
    padding: 0.65rem 1.5rem;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 600;
    transition: 0.2s;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
  }}
  .btn-primary {{ background: var(--accent); color: #fff }}
  .btn-primary:hover {{ background: var(--accent-hover); transform: translateY(-1px) }}
  .btn-secondary {{ background: var(--surface2); color: var(--text); border: 1px solid var(--border) }}
  .btn-secondary:hover {{ border-color: var(--accent) }}
  .btn-whatsapp {{ background: #16a34a; color: #fff }}
  .btn-whatsapp:hover {{ background: #15803d; transform: translateY(-1px) }}
  .btn-danger {{ background: #ef4444; color: #fff }}
  .form-group {{ margin-bottom: 1.1rem }}
  .form-group label {{
    font-size: 0.85rem;
    color: var(--text-muted);
    display: block;
    margin-bottom: 0.25rem;
    font-weight: 600;
  }}
  .form-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.1rem }}
  .badge {{
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.3px;
  }}
  .badge-critical {{ background: #7f1d1d; color: #fca5a5 }}
  .badge-high {{ background: #78350f; color: #fcd34d }}
  .badge-moderate {{ background: #1e3a5f; color: #93c5fd }}
  .badge-low {{ background: #14532d; color: #86efac }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.92rem }}
  th {{
    text-align: left;
    padding: 0.8rem 1rem;
    background: var(--th-bg);
    color: var(--text-muted);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 700;
  }}
  td {{ padding: 0.8rem 1rem; border-bottom: 1px solid var(--border); color: var(--text) }}
  tr:hover td {{ background: var(--row-alt) }}
  .alert-success {{
    background: var(--alert-ok-bg);
    color: var(--alert-ok-text);
    padding: 0.9rem 1.1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    font-weight: 600;
    font-size: 0.9rem;
  }}
  .alert-error {{
    background: var(--alert-err-bg);
    color: var(--alert-err-text);
    padding: 0.9rem 1.1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    font-weight: 600;
    font-size: 0.9rem;
  }}
  .risk-bar {{ height: 10px; border-radius: 5px; background: var(--border); margin-top: 0.5rem }}
  .risk-fill {{ height: 100%; border-radius: 5px }}
  a {{ color: var(--accent-light); text-decoration: none }}
  a:hover {{ text-decoration: underline }}
  code {{
    background: var(--th-bg);
    padding: 0.15rem 0.4rem;
    border-radius: 4px;
    font-size: 0.83rem;
  }}
  .page-title {{
    font-size: 1.4rem;
    font-weight: 800;
    color: var(--text);
  }}
  .page-subtitle {{
    color: var(--text-muted);
    font-size: 0.9rem;
    margin-top: 0.2rem;
  }}
  .section-label {{
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 700;
    color: var(--accent-light);
    margin-bottom: 8px;
  }}
</style>
</head>
<body>
<nav class="navbar">
  <h1>🏥 ClinicalAI — Decision Support</h1>
  <div style="display:flex;align-items:center">
    {"<span class='doc-name'>👨‍⚕️ Dr. Clinical AI</span>" if doctor_name else ""}
    {nav_links}
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
  function toggleTheme() {{
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
    cls = {
        "CRITICAL": "badge-critical",
        "HIGH": "badge-high",
        "MODERATE": "badge-moderate",
        "LOW": "badge-low"
    }.get(level, "badge-low")
    return f'<span class="badge {cls}">{level}</span>'


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse("/login")


@app.get("/login", response_class=HTMLResponse)
async def login_page(error: str = ""):
    err_html = f'<div class="alert-error">{error}</div>' if error else ""
    # Split layout — no navbar, full page
    content = f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Login — ClinicalAI</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root[data-theme="dark"] {{
    --bg: #0a0f1e;
    --surface: #0f1629;
    --border: #1e3a5f;
    --text: #f1f5f9;
    --text-muted: #94a3b8;
    --accent: #3b82f6;
    --accent-hover: #2563eb;
    --accent-light: #60a5fa;
    --input-bg: #070d1a;
    --input-border: #1e3a5f;
    --alert-err-bg: #7f1d1d;
    --alert-err-text: #fca5a5;
  }}
  :root[data-theme="light"] {{
    --bg: #f0f4f8;
    --surface: #ffffff;
    --border: #c7d7ed;
    --text: #0a1628;
    --text-muted: #3d5a80;
    --accent: #1d4ed8;
    --accent-hover: #1e40af;
    --accent-light: #3b82f6;
    --input-bg: #f8faff;
    --input-border: #c7d7ed;
    --alert-err-bg: #fee2e2;
    --alert-err-text: #991b1b;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0 }}
  body {{
    font-family: 'Inter', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .login-wrap {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    width: 860px;
    min-height: 520px;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 24px 64px rgba(0,0,0,0.4);
    border: 1px solid var(--border);
  }}
  .left-panel {{
    background: #0a1628;
    padding: 2.5rem;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  .right-panel {{
    background: var(--surface);
    padding: 2.5rem;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }}
  .brand-label {{
    font-size: 0.68rem;
    color: #60a5fa;
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 700;
    margin-bottom: 1rem;
  }}
  .brand-title {{
    font-size: 1.65rem;
    font-weight: 800;
    color: #f1f5f9;
    line-height: 1.25;
    margin-bottom: 0.5rem;
  }}
  .brand-sub {{
    font-size: 0.85rem;
    color: #60a5fa;
    margin-bottom: 2rem;
  }}
  .feature-item {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 14px;
  }}
  .feature-icon {{
    width: 34px;
    height: 34px;
    border-radius: 8px;
    background: rgba(59,130,246,0.12);
    border: 1px solid rgba(59,130,246,0.25);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
  }}
  .feature-title {{
    font-size: 0.85rem;
    font-weight: 600;
    color: #f1f5f9;
  }}
  .feature-sub {{
    font-size: 0.75rem;
    color: #94a3b8;
  }}
  .left-footer {{
    font-size: 0.75rem;
    color: #334155;
    margin-top: 1.5rem;
  }}
  .login-title {{
    font-size: 1.4rem;
    font-weight: 800;
    color: var(--text);
    margin-bottom: 0.3rem;
  }}
  .login-sub {{
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-bottom: 2rem;
  }}
  .form-group {{ margin-bottom: 1.1rem }}
  .form-group label {{
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--text-muted);
    display: block;
    margin-bottom: 0.4rem;
  }}
  .form-group input {{
    width: 100%;
    padding: 0.7rem 1rem;
    background: var(--input-bg);
    border: 1px solid var(--input-border);
    border-radius: 8px;
    color: var(--text);
    font-size: 0.95rem;
    font-family: 'Inter', sans-serif;
    transition: 0.15s;
  }}
  .form-group input:focus {{
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(59,130,246,0.15);
  }}
  .btn-login {{
    width: 100%;
    padding: 0.75rem;
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: 8px;
    font-size: 0.95rem;
    font-weight: 700;
    cursor: pointer;
    font-family: 'Inter', sans-serif;
    transition: 0.2s;
    margin-top: 0.5rem;
  }}
  .btn-login:hover {{ background: var(--accent-hover); transform: translateY(-1px) }}
  .login-footer {{
    font-size: 0.78rem;
    color: var(--text-muted);
    text-align: center;
    margin-top: 1.25rem;
    padding-top: 1.25rem;
    border-top: 1px solid var(--border);
  }}
  .alert-error {{
    background: var(--alert-err-bg);
    color: var(--alert-err-text);
    padding: 0.75rem 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    font-size: 0.85rem;
    font-weight: 600;
  }}
  .theme-btn {{
    position: fixed;
    top: 1rem;
    right: 1rem;
    background: rgba(15,22,41,0.8);
    border: 1px solid #1e3a5f;
    color: #94a3b8;
    padding: 0.35rem 0.9rem;
    border-radius: 20px;
    cursor: pointer;
    font-size: 0.8rem;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    backdrop-filter: blur(8px);
  }}
  .theme-btn:hover {{ border-color: #3b82f6; color: #60a5fa }}
</style>
</head>
<body>
<button class="theme-btn" onclick="toggleTheme()" id="theme-toggle">☀ Light</button>
<div class="login-wrap">

  <!-- Left: Branding panel -->
  <div class="left-panel">
    <div>
      <div class="brand-label">🎓 MHSSCE · Research 2026</div>
      <div class="brand-title">AI Clinical<br>Decision Support</div>
      <div class="brand-sub">Virtual Junior Doctor for Tier-2/3 Hospitals</div>

      <div class="feature-item">
        <div class="feature-icon">🧠</div>
        <div>
          <div class="feature-title">XGBoost + scispaCy</div>
          <div class="feature-sub">Sepsis detection & clinical NLP</div>
        </div>
      </div>
      <div class="feature-item">
        <div class="feature-icon">🔒</div>
        <div>
          <div class="feature-title">DISHA Compliant</div>
          <div class="feature-sub">Patient data never leaves the hospital</div>
        </div>
      </div>
      <div class="feature-item">
        <div class="feature-icon">📊</div>
        <div>
          <div class="feature-title">0.965 AUC</div>
          <div class="feature-sub">Federated learning across 3 hospitals</div>
        </div>
      </div>
      <div class="feature-item">
        <div class="feature-icon">📋</div>
        <div>
          <div class="feature-title">Full Patient History</div>
          <div class="feature-sub">Track every visit & generate PDF reports</div>
        </div>
      </div>
    </div>
    <div class="left-footer">Powered by FastAPI · LangGraph · Flower FL</div>
  </div>

  <!-- Right: Login form -->
  <div class="right-panel">
    <div class="login-title">Doctor Login</div>
    <div class="login-sub">Access the clinical decision support system</div>
    {err_html}
    <form method="post" action="/login">
      <div class="form-group">
        <label>Username</label>
        <input name="username" placeholder="Enter username" required autocomplete="username">
      </div>
      <div class="form-group">
        <label>Password</label>
        <input type="password" name="password" placeholder="Enter password" required autocomplete="current-password">
      </div>
      <button class="btn-login" type="submit">Sign in →</button>
    </form>
    <div class="login-footer">
      Default credentials: <strong>doctor</strong> / <strong>clinical2026</strong>
    </div>
  </div>

</div>
<script>
  const html = document.documentElement;
  const btn = document.getElementById('theme-toggle');
  const saved = localStorage.getItem('theme') || 'dark';
  html.setAttribute('data-theme', saved);
  btn.textContent = saved === 'dark' ? '☀ Light' : '🌙 Dark';
  function toggleTheme() {{
    const cur = html.getAttribute('data-theme');
    const next = cur === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    btn.textContent = next === 'dark' ? '☀ Light' : '🌙 Dark';
  }}
</script>
</body>
</html>"""
    return HTMLResponse(content)


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


# ── About ─────────────────────────────────────────────────────────────────────

@app.get("/about", response_class=HTMLResponse)
async def about_page(session: str | None = Cookie(default=None)):
    doctor = require_doctor(session)
    body = """
    <div style="background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:2.5rem;margin-bottom:2rem;position:relative;overflow:hidden">
      <div style="position:absolute;top:-40px;right:-40px;width:200px;height:200px;background:radial-gradient(circle,rgba(59,130,246,0.1) 0%,transparent 70%);pointer-events:none"></div>
      <div class="section-label">🎓 Research Project 2026 — MHSSCE</div>
      <h1 style="font-size:1.9rem;font-weight:800;color:var(--text);line-height:1.25;margin-bottom:14px">
        🏥 AI for Real-Time Clinical<br>Decision Support<br>
        <span style="color:var(--accent-light)">in Under-Resourced Hospitals</span>
      </h1>
      <p style="color:var(--text-muted);font-size:1rem;line-height:1.75;max-width:680px">
        A <strong style="color:var(--text)">Virtual Junior Doctor</strong> that detects sepsis in real time,
        explains every decision, and tells the attending doctor exactly what to do next —
        built for Tier-2 and Tier-3 hospitals in India where specialist doctors are scarce
        and early detection saves lives. 🩺
      </p>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:14px;margin-bottom:2rem">
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:1.5rem;text-align:center">
        <div style="font-size:2.2rem;font-weight:800;color:var(--accent-light)">✅ 6</div>
        <div style="font-size:0.72rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-top:6px;font-weight:700">Phases Completed</div>
      </div>
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:1.5rem;text-align:center">
        <div style="font-size:2.2rem;font-weight:800;color:#8b5cf6">🎯 0.965</div>
        <div style="font-size:0.72rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-top:6px;font-weight:700">Federated AUC</div>
      </div>
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:1.5rem;text-align:center">
        <div style="font-size:2.2rem;font-weight:800;color:#f97316">🏥 3</div>
        <div style="font-size:0.72rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-top:6px;font-weight:700">Hospitals Simulated</div>
      </div>
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:1.5rem;text-align:center">
        <div style="font-size:2.2rem;font-weight:800;color:#22c55e">🛡 DISHA</div>
        <div style="font-size:0.72rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-top:6px;font-weight:700">Compliance Ready</div>
      </div>
    </div>

    <div style="margin-bottom:2rem">
      <div class="section-label">🏗 System Design</div>
      <h2 style="font-size:1.4rem;font-weight:800;color:var(--text);margin-bottom:8px">3-Layer Architecture</h2>
      <p style="color:var(--text-muted);font-size:0.95rem;margin-bottom:1.5rem">Every patient interaction flows through three layers — from raw hospital data to an actionable clinical treatment plan.</p>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px">
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:1.5rem">
          <div style="font-size:0.7rem;color:var(--accent-light);text-transform:uppercase;letter-spacing:1px;font-weight:700;margin-bottom:8px">Layer 1</div>
          <div style="font-size:2rem;margin-bottom:10px">📥</div>
          <div style="font-weight:800;color:var(--text);margin-bottom:12px;font-size:1rem">Data Ingestion</div>
          <ul style="list-style:none;padding:0">
            <li style="font-size:0.84rem;color:var(--text-muted);padding:4px 0 4px 16px;position:relative"><span style="position:absolute;left:0;color:var(--accent-light);font-weight:700">→</span>FHIR R4 patient bundles</li>
            <li style="font-size:0.84rem;color:var(--text-muted);padding:4px 0 4px 16px;position:relative"><span style="position:absolute;left:0;color:var(--accent-light);font-weight:700">→</span>LOINC-coded vitals and labs</li>
            <li style="font-size:0.84rem;color:var(--text-muted);padding:4px 0 4px 16px;position:relative"><span style="position:absolute;left:0;color:var(--accent-light);font-weight:700">→</span>Clinical notes (free text)</li>
            <li style="font-size:0.84rem;color:var(--text-muted);padding:4px 0 4px 16px;position:relative"><span style="position:absolute;left:0;color:var(--accent-light);font-weight:700">→</span>Completeness validation</li>
          </ul>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:1.5rem">
          <div style="font-size:0.7rem;color:#8b5cf6;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin-bottom:8px">Layer 2</div>
          <div style="font-size:2rem;margin-bottom:10px">🤖</div>
          <div style="font-weight:800;color:var(--text);margin-bottom:12px;font-size:1rem">AI Core</div>
          <ul style="list-style:none;padding:0">
            <li style="font-size:0.84rem;color:var(--text-muted);padding:4px 0 4px 16px;position:relative"><span style="position:absolute;left:0;color:#8b5cf6;font-weight:700">→</span>XGBoost sepsis model + SHAP</li>
            <li style="font-size:0.84rem;color:var(--text-muted);padding:4px 0 4px 16px;position:relative"><span style="position:absolute;left:0;color:#8b5cf6;font-weight:700">→</span>scispaCy NLP (NER + negation)</li>
            <li style="font-size:0.84rem;color:var(--text-muted);padding:4px 0 4px 16px;position:relative"><span style="position:absolute;left:0;color:#8b5cf6;font-weight:700">→</span>Multimodal fusion engine</li>
            <li style="font-size:0.84rem;color:var(--text-muted);padding:4px 0 4px 16px;position:relative"><span style="position:absolute;left:0;color:#8b5cf6;font-weight:700">→</span>LangGraph agent orchestration</li>
          </ul>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:1.5rem">
          <div style="font-size:0.7rem;color:#22c55e;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin-bottom:8px">Layer 3</div>
          <div style="font-size:2rem;margin-bottom:10px">📊</div>
          <div style="font-weight:800;color:var(--text);margin-bottom:12px;font-size:1rem">Clinical Output</div>
          <ul style="list-style:none;padding:0">
            <li style="font-size:0.84rem;color:var(--text-muted);padding:4px 0 4px 16px;position:relative"><span style="position:absolute;left:0;color:#22c55e;font-weight:700">→</span>Risk level + score + drivers</li>
            <li style="font-size:0.84rem;color:var(--text-muted);padding:4px 0 4px 16px;position:relative"><span style="position:absolute;left:0;color:#22c55e;font-weight:700">→</span>Treatment plan (immediate/urgent/routine)</li>
            <li style="font-size:0.84rem;color:var(--text-muted);padding:4px 0 4px 16px;position:relative"><span style="position:absolute;left:0;color:#22c55e;font-weight:700">→</span>Escalation triggers</li>
            <li style="font-size:0.84rem;color:var(--text-muted);padding:4px 0 4px 16px;position:relative"><span style="position:absolute;left:0;color:#22c55e;font-weight:700">→</span>HITL mandatory review flag</li>
          </ul>
        </div>
      </div>
    </div>

    <div style="margin-bottom:2rem">
      <div class="section-label">⚙️ Tech Stack</div>
      <div style="display:flex;flex-wrap:wrap;gap:10px">
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 16px;font-size:0.84rem;color:var(--text-muted);display:flex;align-items:center;gap:8px"><span>⚡</span><strong style="color:var(--text)">FastAPI</strong> REST API</div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 16px;font-size:0.84rem;color:var(--text-muted);display:flex;align-items:center;gap:8px"><span>🔗</span><strong style="color:var(--text)">LangGraph</strong> Agent Orchestration</div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 16px;font-size:0.84rem;color:var(--text-muted);display:flex;align-items:center;gap:8px"><span>🌲</span><strong style="color:var(--text)">XGBoost</strong> Sepsis Model</div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 16px;font-size:0.84rem;color:var(--text-muted);display:flex;align-items:center;gap:8px"><span>🧠</span><strong style="color:var(--text)">scispaCy</strong> Clinical NLP</div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 16px;font-size:0.84rem;color:var(--text-muted);display:flex;align-items:center;gap:8px"><span>🌸</span><strong style="color:var(--text)">Flower</strong> Federated Learning</div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 16px;font-size:0.84rem;color:var(--text-muted);display:flex;align-items:center;gap:8px"><span>🏥</span><strong style="color:var(--text)">FHIR R4</strong> Healthcare Standard</div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 16px;font-size:0.84rem;color:var(--text-muted);display:flex;align-items:center;gap:8px"><span>🔍</span><strong style="color:var(--text)">SHAP</strong> Explainable AI</div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 16px;font-size:0.84rem;color:var(--text-muted);display:flex;align-items:center;gap:8px"><span>🛡</span><strong style="color:var(--text)">DISHA/HIPAA</strong> Compliance</div>
      </div>
    </div>

    <div style="background:rgba(59,130,246,0.06);border:1px solid rgba(59,130,246,0.2);border-radius:14px;padding:1.25rem 1.5rem;display:flex;align-items:center;gap:16px">
      <div style="font-size:2rem">🔒</div>
      <div>
        <div style="font-weight:700;color:var(--text);margin-bottom:4px">Privacy &amp; Compliance</div>
        <div style="color:var(--text-muted);font-size:0.87rem">
          Patient data never leaves the hospital &nbsp;·&nbsp;
          Only gradient weights transmitted &nbsp;·&nbsp;
          ✅ Compliant with India DISHA and HIPAA
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
        risk_badge = _badge(last["risk_level"]) if last else "<span style='color:var(--text-muted)'>—</span>"
        disease_name = DISEASES.get(p["disease_id"], type("x", (), {"name": p["disease_id"]})()).name
        rows += f"""<tr>
          <td><a href="/patient/{p['patient_id']}">{p['patient_id']}</a></td>
          <td style="font-weight:600">{p['full_name']}</td>
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

    empty = "<tr><td colspan='7' style='text-align:center;color:var(--text-muted);padding:2rem'>No patients registered yet</td></tr>" if not patients else ""

    body = f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.5rem">
      <div>
        <div class="page-title">🩺 Welcome, Dr. Clinical AI</div>
        <div class="page-subtitle">{doctor['hospital']} · {len(patients)} patient(s) registered</div>
      </div>
      <a href="/register-patient">
        <button class="btn btn-primary">+ Register Patient</button>
      </a>
            </div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:1.5rem;">
          <div class="card" style="text-align:center;padding:1.2rem;">
            <div style="font-size:0.7rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">🔬 Patients Analysed</div>
            <div id="stat-total" style="font-size:2rem;font-weight:800;color:var(--accent);">--</div>
          </div>
          <div class="card" style="text-align:center;padding:1.2rem;">
            <div style="font-size:0.7rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">🚨 Critical Alerts</div>
            <div id="stat-critical" style="font-size:2rem;font-weight:800;color:#ef4444;">--</div>
          </div>
          <div class="card" style="text-align:center;padding:1.2rem;">
            <div style="font-size:0.7rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">⚠️ High Risk</div>
            <div id="stat-high" style="font-size:2rem;font-weight:800;color:#f97316;">--</div>
          </div>
          <div class="card" style="text-align:center;padding:1.2rem;">
            <div style="font-size:0.7rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">🏥 Registered Patients</div>
            <div style="font-size:2rem;font-weight:800;color:var(--accent);">{len(patients)}</div>
          </div>
        </div>
                <div class="card">
          <h2>Your Patients</h2>
          <div style="margin-bottom:1rem;">
            <input id="patient-search" type="text" placeholder="🔍 Search by name, ID or condition..."
              style="width:100%;padding:10px 14px;border-radius:8px;border:1px solid var(--border);
              background:var(--surface);color:var(--text);font-size:0.9rem;outline:none;"
              oninput="filterPatients(this.value)">
          </div>
          <table>
        <thead><tr>
          <th>Patient ID</th><th>Name</th><th>Age / Gender</th>
          <th>Condition</th><th>Last Risk</th><th>Registered</th><th>Action</th>
        </tr></thead>
        <tbody id="patient-table">{rows}{empty}</tbody>
      </table>
    </div>"""
    body += """<script>
async function loadStats(){
  try{
    var r=await fetch("/stats");
    if(!r.ok)return;
    var d=await r.json();
    var t=document.getElementById("stat-total");
    var c=document.getElementById("stat-critical");
    var h=document.getElementById("stat-high");
    if(t)t.textContent=d.total_analysed;
    if(c)c.textContent=d.critical_count;
    if(h)h.textContent=d.high_count;
  }catch(e){}
}
loadStats();
setInterval(loadStats,30000);

function filterPatients(q){
  q=q.toLowerCase();
  var rows=document.querySelectorAll("#patient-table tr");
  rows.forEach(function(row){
    row.style.display=row.textContent.toLowerCase().includes(q)?"":"none";
  });
}
</script>"""
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
    <div style="margin-bottom:1rem"><a href="/dashboard">← Dashboard</a></div>
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
            <label>Phone (for WhatsApp reports)</label>
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
            <span style="color:var(--text-muted);font-size:.75rem;font-weight:400"> ({param.unit})</span>
            {"<span style='color:#ef4444'> *</span>" if param.required else ""}
          </label>
          {field}
        </div>"""

    msg_html = f'<div class="alert-success">✅ {msg}</div>' if msg else ""
    body = f"""
    {msg_html}
    <div style="display:flex;gap:.5rem;align-items:center;margin-bottom:1rem">
      <a href="/dashboard">← Dashboard</a>
      <span style="color:var(--text-muted)"> / </span>
      <a href="/patient/{patient_id}">{patient['full_name']}</a>
      <span style="color:var(--text-muted)"> / </span>
      <span style="color:var(--text)">Analysis</span>
    </div>
    <div class="card">
      <h2>🔬 Clinical Analysis — {disease.name}</h2>
      <div style="color:var(--text-muted);font-size:.85rem;margin-bottom:1.2rem">
        Patient: <strong style="color:var(--text)">{patient['full_name']}</strong> ·
        Age: <strong style="color:var(--text)">{patient['age']}</strong> ·
        ID: <code style="color:var(--accent-light)">{patient_id}</code>
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

    parameters = {k: v for k, v in parameters.items() if v is not None}
    result = analyse(patient["disease_id"], parameters)

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
        f"<tr><td style='color:var(--text-muted)'>{k.replace('_',' ').title()}</td><td style='color:var(--text);font-weight:500'>{v}</td></tr>"
        for k, v in params.items()
    )

    pct = int(row["risk_score"] * 100)
    fill_color = {
        "CRITICAL": "#ef4444",
        "HIGH": "#f97316",
        "MODERATE": "#3b82f6",
        "LOW": "#10b981"
    }.get(row["risk_level"], "#10b981")

    # WhatsApp share
    phone = patient.get("phone", "").strip().replace(" ", "").replace("+", "")
    findings_text = "%0A".join([f"• {f}" for f in findings[:3]])
    recs_text = "%0A".join([f"• {r}" for r in recs[:2]])
    wa_message = (
        f"🏥 *ClinicalAI Report — {patient['full_name']}*%0A"
        f"📋 Patient ID: {row['patient_id']}%0A"
        f"⚠ Risk Level: *{row['risk_level']}* ({pct}%25)%0A"
        f"🔬 Condition: {DISEASES[row['disease_id']].name}%0A%0A"
        f"*Key Findings:*%0A{findings_text}%0A%0A"
        f"*Immediate Actions:*%0A{recs_text}%0A%0A"
        f"📄 Full PDF report shared separately by your doctor.%0A"
        f"— {doctor['full_name']}, {doctor['hospital']}"
    )
    wa_link = f"https://wa.me/{phone}?text={wa_message}" if phone else ""
    wa_btn = f'<a href="{wa_link}" target="_blank"><button class="btn btn-whatsapp">💬 Share via WhatsApp</button></a>' if wa_link else \
             '<button class="btn btn-secondary" disabled title="No phone number registered">💬 WhatsApp (no number)</button>'

    body = f"""
    <div style="display:flex;gap:.5rem;align-items:center;margin-bottom:1rem">
      <a href="/dashboard">← Dashboard</a>
      <span style="color:var(--text-muted)"> / </span>
      <a href="/patient/{row['patient_id']}">{patient['full_name']}</a>
      <span style="color:var(--text-muted)"> / </span>
      <span style="color:var(--text)">Result</span>
    </div>
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div>
          <h2>{DISEASES[row['disease_id']].name} — Analysis Result</h2>
          <p style="color:var(--text-muted);font-size:.85rem;margin-top:.3rem">
            <strong style="color:var(--text)">{patient['full_name']}</strong> ·
            Age {patient['age']} · {patient['gender']} ·
            <code style="color:var(--accent-light)">{row['patient_id']}</code>
          </p>
        </div>
        {_badge(row['risk_level'])}
      </div>
      <div style="margin:1.2rem 0">
        <div style="display:flex;justify-content:space-between;font-size:.85rem;color:var(--text-muted);margin-bottom:.3rem">
          <span style="font-weight:600">Risk Score</span>
          <span style="color:{fill_color};font-weight:700">{pct}%</span>
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
    <div style="display:flex;gap:1rem;margin-top:1rem;flex-wrap:wrap">
      <a href="/report/{analysis_id}">
        <button class="btn btn-primary">📄 Download PDF Report</button>
      </a>
      {wa_btn}
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
          <td>{_badge(a['risk_level'])} <span style="font-weight:600">{pct}%</span></td>
          <td>
            <a href="/result/{a['id']}">View</a> &nbsp;
            <a href="/report/{a['id']}">PDF</a>
          </td>
        </tr>"""

    disease_name = DISEASES.get(patient["disease_id"], type("x", (), {"name": patient["disease_id"]})()).name
    body = f"""
    <div style="margin-bottom:1rem"><a href="/dashboard">← Dashboard</a></div>
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div>
          <h2>{patient['full_name']}</h2>
          <p style="color:var(--text-muted);font-size:.85rem;margin-top:.3rem">
            ID: <code style="color:var(--accent-light)">{patient_id}</code> ·
            Age: <strong>{patient['age']}</strong> · {patient['gender']} ·
            Condition: <strong>{disease_name}</strong>
          </p>
          <p style="color:var(--text-muted);font-size:.85rem;margin-top:.25rem">
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
      <h2>Analysis History <span style="color:var(--text-muted);font-weight:500;font-size:.9rem">({len(analyses)} records)</span></h2>
      <table>
        <thead><tr><th>Date</th><th>Condition</th><th>Risk</th><th>Actions</th></tr></thead>
        <tbody>
          {rows if rows else "<tr><td colspan='4' style='text-align:center;color:var(--text-muted);padding:2rem'>No analyses yet</td></tr>"}
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
    import io
    import json

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

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
    now = datetime.now(tz=UTC).strftime("%d %B %Y, %H:%M UTC")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            topMargin=1.5*cm, bottomMargin=1.5*cm,
                            leftMargin=2*cm, rightMargin=2*cm)

    getSampleStyleSheet()
    navy   = colors.HexColor("#0a1628")
    blue   = colors.HexColor("#1d4ed8")
    gray   = colors.HexColor("#64748b")
    red    = colors.HexColor("#dc2626")
    orange = colors.HexColor("#ea580c")
    med_blue = colors.HexColor("#2563eb")
    green  = colors.HexColor("#16a34a")

    risk_color = {"CRITICAL": red, "HIGH": orange, "MODERATE": med_blue, "LOW": green}.get(row["risk_level"], green)

    H1   = ParagraphStyle("H1",   fontSize=18, textColor=blue,  spaceAfter=4,  fontName="Helvetica-Bold")
    H2   = ParagraphStyle("H2",   fontSize=11, textColor=navy,  spaceAfter=4,  fontName="Helvetica-Bold", spaceBefore=10)
    BODY = ParagraphStyle("BODY", fontSize=9,  textColor=navy,  spaceAfter=3,  leading=14)
    SMALL= ParagraphStyle("SMALL",fontSize=8,  textColor=gray,  spaceAfter=2)

    story = []

    story.append(Paragraph("ClinicalAI — Decision Support System", H1))
    story.append(Paragraph("AI-Assisted Medical Report &nbsp;|&nbsp; Confidential", SMALL))
    story.append(Paragraph(f"Generated: {now} &nbsp;|&nbsp; Report ID: {analysis_id}", SMALL))
    story.append(HRFlowable(width="100%", thickness=2, color=blue, spaceAfter=10))

    story.append(Paragraph("Patient Information", H2))
    info_data = [
        ["Patient ID", row["patient_id"], "Full Name", patient["full_name"]],
        ["Age", f"{patient['age']} years", "Gender", patient["gender"]],
        ["Phone", patient.get("phone") or "—", "Address", patient.get("address") or "—"],
        ["Condition", disease.name if disease else row["disease_id"], "ICD-10", disease.icd10_code if disease else "—"],
        ["Attending Doctor", "Dr. Clinical AI", "Hospital", doctor["hospital"]],
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
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, colors.HexColor("#f1f5f9")]),
        ("GRID",      (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING",   (0,0), (-1,-1), 6),
        ("VALIGN",    (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(info_table)

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Risk Assessment Summary", H2))
    pct = int(row["risk_score"] * 100)
    risk_data = [["Risk Level", "Risk Score", "Disease", "ICD-10 Code"],
                 [row["risk_level"], f"{pct}%", disease.name if disease else "—", disease.icd10_code if disease else "—"]]
    risk_table = Table(risk_data, colWidths=[4*cm, 3*cm, 8*cm, 4*cm])
    risk_table.setStyle(TableStyle([
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("BACKGROUND",  (0,0), (-1,0), navy),
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
        ("BACKGROUND",     (0,0), (-1,0), navy),
        ("TEXTCOLOR",      (0,0), (-1,0), colors.white),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ("GRID",           (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING",        (0,0), (-1,-1), 6),
        ("ALIGN",          (1,0), (-1,-1), "CENTER"),
    ]))
    story.append(param_table)

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Clinical Findings", H2))
    for f in findings:
        story.append(Paragraph(f"⚠ {f}", BODY))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Medical Recommendations", H2))
    for r in recs:
        story.append(Paragraph(f"→ {r}", BODY))

    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=gray, spaceAfter=6))
    story.append(Paragraph(
        "DISCLAIMER: This report is AI-generated and intended to assist clinical decision-making only. "
        "It does not replace professional medical judgement. The attending doctor must review and validate "
        "all findings before any clinical action is taken. ClinicalAI — DISHA Compliant.",
        SMALL))
    story.append(Paragraph("Doctor Signature: __________________ &nbsp;&nbsp; Date: __________________", SMALL))

    doc.build(story)
    buffer.seek(0)

    filename = f"ClinicalReport_{row['patient_id']}_{row['disease_id']}_{analysis_id}.pdf"
    from fastapi.responses import StreamingResponse
    return StreamingResponse(buffer, media_type="application/pdf",
                             headers={"Content-Disposition": f"attachment; filename={filename}"})

# ── Live Stats ─────────────────────────────────────────────────────────────────

@app.get("/stats")
def get_stats(session: str | None = Cookie(default=None)):
    require_doctor(session)
    import sqlite3
    from datetime import datetime
    db_path = "data/clinical.db"
    try:
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT risk_level, risk_score FROM analyses")
        rows = cur.fetchall()
        con.close()
    except Exception:
        rows = []
    total    = len(rows)
    critical = sum(1 for r in rows if r["risk_level"] == "CRITICAL")
    high     = sum(1 for r in rows if r["risk_level"] == "HIGH")
    scores   = [r["risk_score"] for r in rows if r["risk_score"] is not None]
    avg_score = round(sum(scores) / len(scores), 3) if scores else 0.0
    return {
        "total_analysed": total,
        "critical_count": critical,
        "high_count":     high,
        "avg_risk_score": avg_score,
        "last_updated":   datetime.now(UTC).isoformat(),
    }