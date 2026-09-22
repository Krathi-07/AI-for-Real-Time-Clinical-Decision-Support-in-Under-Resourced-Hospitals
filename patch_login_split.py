with open("src/api/main.py", "r", encoding="utf-8") as f:
    code = f.read()

old_login = '''async def login_page(error: str = ""):
    err_html = f\'<div class="alert-error">{error}</div>\' if error else ""
    body = f"""
    <div style="min-height:80vh;display:flex;align-items:center;justify-content:center">
      <div class="card" style="width:100%;max-width:400px;padding:2.5rem">
        <div style="text-align:center;margin-bottom:1.5rem">
          <div style="font-size:2.5rem;margin-bottom:.5rem">🏥</div>
          <h2 style="font-size:1.4rem;margin-bottom:.3rem">Doctor Login</h2>
          <p style="color:var(--text-muted);font-size:.85rem">AI Clinical Decision Support System</p>
        </div>
        {err_html}
        <form method="post" action="/login">
          <div class="form-group">
            <label>Username</label>
            <input name="username" placeholder="doctor" required autocomplete="username">
          </div>
          <div class="form-group" style="margin-top:.75rem">
            <label>Password</label>
            <input type="password" name="password" placeholder="••••••••" required autocomplete="current-password">
          </div>
          <button class="btn btn-primary" style="width:100%;margin-top:1.25rem;padding:.75rem">Login</button>
        </form>
        <p style="font-size:.78rem;margin-top:1rem;text-align:center;color:var(--text-muted)">
          Default: <strong>doctor</strong> / <strong>clinical2026</strong>
        </p>
      </div>
    </div>"""
    return html(_base("Login", body))'''

new_login = '''async def login_page(error: str = ""):
    err_html = f\'<div style="background:rgba(239,68,68,.15);color:#fca5a5;padding:.65rem 1rem;border-radius:8px;margin-bottom:1rem;border:1px solid rgba(239,68,68,.3);font-size:.85rem">{error}</div>\' if error else ""
    page = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Login — ClinicalAI</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:\'Inter\',sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#f5f3ff}
.wrap{display:flex;width:100%;max-width:900px;min-height:520px;border-radius:20px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.18)}
/* LEFT PANEL */
.left{flex:1;background:linear-gradient(145deg,#0c0e1a 0%,#1a1040 60%,#0f1035 100%);padding:3rem 2.5rem;display:flex;flex-direction:column;justify-content:space-between;position:relative;overflow:hidden}
.left::before{content:\'\';position:absolute;top:-60px;right:-60px;width:220px;height:220px;background:rgba(124,58,237,.15);border-radius:50%}
.left::after{content:\'\';position:absolute;bottom:-40px;left:-40px;width:160px;height:160px;background:rgba(59,130,246,.1);border-radius:50%}
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
input{width:100%;padding:.7rem 1rem;border:1.5px solid #e5e7eb;border-radius:10px;font-size:.92rem;font-family:\'Inter\',sans-serif;color:#1e1b4b;outline:none;transition:.2s}
input:focus{border-color:#7c3aed;box-shadow:0 0 0 3px rgba(124,58,237,.12)}
.form-group{margin-bottom:1.1rem}
.btn-login{width:100%;padding:.8rem;background:linear-gradient(135deg,#7c3aed,#6d28d9);color:#fff;border:none;border-radius:10px;font-size:1rem;font-weight:700;cursor:pointer;margin-top:.5rem;font-family:\'Inter\',sans-serif;transition:.2s}
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
    return HTMLResponse(page)'''

if old_login in code:
    code = code.replace(old_login, new_login)
    print("✅ Split login page applied")
else:
    print("❌ Pattern not found")

with open("src/api/main.py", "w", encoding="utf-8") as f:
    f.write(code)
