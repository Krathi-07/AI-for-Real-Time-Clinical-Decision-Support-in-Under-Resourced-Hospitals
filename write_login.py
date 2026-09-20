# write_login.py

content = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Login | AI Clinical Decision Support</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --slate-950: #0c0e1a;
      --slate-900: #111322;
      --slate-800: #1a1d30;
      --slate-700: #252840;
      --violet:    #7c3aed;
      --violet-dim:#6d28d9;
      --violet-lit:#a78bfa;
      --text:      #e2e4f0;
      --text-muted:#8b90b0;
      --border:    #2a2d45;
    }

    body {
      font-family: 'Inter', sans-serif;
      background: var(--slate-950);
      color: var(--text);
      min-height: 100vh;
      display: flex;
    }

    /* ── Left panel ── */
    .left {
      width: 45%;
      background: linear-gradient(145deg, #0f1035 0%, #1a1050 60%, #0c0e1a 100%);
      padding: 3rem 3.5rem;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      text-align: center;
      position: relative;
      overflow: hidden;
    }

    .left::before {
      content: '';
      position: absolute;
      top: -80px; right: -80px;
      width: 320px; height: 320px;
      background: radial-gradient(circle, rgba(124,58,237,.25) 0%, transparent 70%);
      pointer-events: none;
    }

    .left::after {
      content: '';
      position: absolute;
      bottom: -60px; left: -60px;
      width: 240px; height: 240px;
      background: radial-gradient(circle, rgba(124,58,237,.15) 0%, transparent 70%);
      pointer-events: none;
    }

    .badge {
      display: inline-block;
      background: rgba(124,58,237,.2);
      border: 1px solid rgba(124,58,237,.4);
      color: var(--violet-lit);
      padding: .3rem .9rem;
      border-radius: 20px;
      font-size: .75rem;
      font-weight: 600;
      letter-spacing: .06em;
      text-transform: uppercase;
      margin-bottom: 2rem;
    }

    .left h1 {
      font-size: 2.6rem;
      font-weight: 800;
      line-height: 1.15;
      color: #fff;
      margin-bottom: 1rem;
    }

    .left h1 span { color: var(--violet-lit); }

    .left .subtitle {
      color: var(--text-muted);
      font-size: 1rem;
      line-height: 1.6;
      margin-bottom: 2.5rem;
    }

    .feature {
      display: flex;
      align-items: flex-start;
      gap: .9rem;
      margin-bottom: 1.2rem;
    }

    .feature-icon {
      width: 36px; height: 36px;
      background: rgba(124,58,237,.2);
      border: 1px solid rgba(124,58,237,.35);
      border-radius: 8px;
      display: flex; align-items: center; justify-content: center;
      font-size: 1rem;
      flex-shrink: 0;
    }

    .feature-text strong {
      display: block;
      font-size: .92rem;
      font-weight: 600;
      color: var(--text);
      margin-bottom: .15rem;
    }

    .feature-text span {
      font-size: .8rem;
      color: var(--text-muted);
    }

    .left-footer {
      font-size: .75rem;
      color: var(--text-muted);
      border-top: 1px solid var(--border);
      padding-top: 1.2rem;
      margin-top: 2rem;
    }

    /* ── Right panel ── */
    .right {
      flex: 1;
      background: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 3rem 2.5rem;
    }

    .form-box {
      width: 100%;
      max-width: 380px;
    }

    .form-box h2 {
      font-size: 1.7rem;
      font-weight: 700;
      color: #0f1035;
      margin-bottom: .4rem;
    }

    .form-box .form-sub {
      color: #6b7280;
      font-size: .9rem;
      margin-bottom: 2rem;
    }

    .field { margin-bottom: 1.2rem; }

    .field label {
      display: block;
      font-size: .8rem;
      font-weight: 600;
      color: #374151;
      text-transform: uppercase;
      letter-spacing: .05em;
      margin-bottom: .45rem;
    }

    .field input {
      width: 100%;
      padding: .75rem 1rem;
      border: 1.5px solid #e5e7eb;
      border-radius: 8px;
      font-size: .95rem;
      font-family: 'Inter', sans-serif;
      color: #111827;
      background: #f9fafb;
      transition: border-color .2s, box-shadow .2s;
    }

    .field input:focus {
      outline: none;
      border-color: #7c3aed;
      box-shadow: 0 0 0 3px rgba(124,58,237,.12);
      background: #fff;
    }

    .btn-signin {
      width: 100%;
      padding: .85rem;
      background: linear-gradient(135deg, #7c3aed, #6d28d9);
      color: #fff;
      border: none;
      border-radius: 8px;
      font-size: 1rem;
      font-weight: 700;
      font-family: 'Inter', sans-serif;
      cursor: pointer;
      margin-top: .5rem;
      transition: opacity .2s, transform .1s;
    }

    .btn-signin:hover { opacity: .92; transform: translateY(-1px); }
    .btn-signin:active { transform: translateY(0); }

    .hint {
      text-align: center;
      margin-top: 1.2rem;
      font-size: .8rem;
      color: #9ca3af;
    }

    .error-msg {
      background: #fef2f2;
      border: 1px solid #fecaca;
      color: #dc2626;
      padding: .7rem 1rem;
      border-radius: 8px;
      font-size: .85rem;
      margin-bottom: 1rem;
      display: none;
    }

    .error-msg.show { display: block; }

    @media (max-width: 640px) {
      .left { display: none; }
      .right { background: var(--slate-950); }
      .form-box h2 { color: #fff; }
      .form-box .form-sub { color: #8b90b0; }
      .field label { color: #a0aec0; }
      .field input { background: #1a1d30; border-color: #2a2d45; color: #fff; }
      .field input:focus { background: #1a1d30; }
      .hint { color: #6b7280; }
    }
  </style>
</head>
<body>
<button style="position:fixed;top:1rem;right:1rem;background:rgba(124,58,237,.15);border:1px solid rgba(124,58,237,.3);color:#a78bfa;padding:.35rem .85rem;border-radius:20px;font-size:.78rem;font-weight:600;font-family:Inter,sans-serif;cursor:pointer;z-index:100" onclick="toggleTheme()" id="themeBtn">&#9728; Light</button>
<!-- Left panel -->
<div class="left">
  <div style="position:relative;z-index:1;width:100%">
    <div class="badge">MHSSCE &middot; Research 2026</div>
    <h1>AI Clinical<br><span>Decision</span><br>Support</h1>
    <p class="subtitle">Virtual Junior Doctor for Tier-2/3 Hospitals</p>

    <div class="feature">
      <div class="feature-icon">&#x1f9e0;</div>
      <div class="feature-text">
        <strong>XGBoost + scispaCy</strong>
        <span>Sepsis detection &amp; NLP</span>
      </div>
    </div>

    <div class="feature">
      <div class="feature-icon">&#x1f512;</div>
      <div class="feature-text">
        <strong>DISHA Compliant</strong>
        <span>Patient data stays local</span>
      </div>
    </div>

    <div class="feature">
      <div class="feature-icon">&#x26a1;</div>
      <div class="feature-text">
        <strong>Real-Time Alerts</strong>
        <span>Critical risk flagged instantly</span>
      </div>
    </div>

    <div class="feature">
      <div class="feature-icon">&#x1f30e;</div>
      <div class="feature-text">
        <strong>Federated Learning</strong>
        <span>Trains across hospitals privately</span>
      </div>
    </div>
  </div>

  <div class="left-footer">
    FastAPI &nbsp;&middot;&nbsp; LangGraph &nbsp;&middot;&nbsp; Flower FL
  </div>
</div>

<!-- Right panel -->
<div class="right">
  <div class="form-box">
    <h2>Doctor login</h2>
    <p class="form-sub">Access the clinical decision support system</p>

    <div class="error-msg" id="errorMsg">
      <span id="errorText">Invalid credentials. Please try again.</span>
    </div>

    <div class="field">
      <label for="username">Username</label>
      <input type="text" id="username" placeholder="e.g. doctor" autocomplete="username">
    </div>

    <div class="field">
      <label for="password">Password</label>
      <input type="password" id="password" placeholder="&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;" autocomplete="current-password">
    </div>

    <button class="btn-signin" onclick="doLogin()">Sign in</button>

    <p class="hint">Default: doctor / clinical2026</p>
  </div>
</div>

<script>
  (function() {
    var t = localStorage.getItem("theme") ||
      (window.matchMedia("(prefers-color-scheme:dark)").matches ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", t);
    document.addEventListener("DOMContentLoaded", function() {
      var btn = document.getElementById("themeBtn");
      if (btn) btn.textContent = t === "dark" ? "☀ Light" : "🌙 Dark";
    });
  })();

  function toggleTheme() {
    var t = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", t);
    localStorage.setItem("theme", t);
    var btn = document.getElementById("themeBtn");
    if (btn) btn.textContent = t === "dark" ? "☀ Light" : "🌙 Dark";
  }
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') doLogin();
  });

  async function doLogin() {
    var u = document.getElementById('username').value.trim();
    var p = document.getElementById('password').value.trim();
    var err = document.getElementById('errorMsg');
    var errTxt = document.getElementById('errorText');

    if (!u || !p) {
      errTxt.textContent = 'Please enter both username and password.';
      err.classList.add('show');
      return;
    }

    var body = new URLSearchParams({ username: u, password: p });
    try {
      var res = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body.toString(),
        redirect: 'follow',
      });
      if (res.ok) {
        window.location.href = '/dashboard';
      } else {
        errTxt.textContent = 'Invalid credentials. Please try again.';
        err.classList.add('show');
        document.getElementById('password').value = '';
      }
    } catch(e) {
      errTxt.textContent = 'Connection error. Please try again.';
      err.classList.add('show');
    }
  }
</script>
</body>
</html>'''
with open("src/dashboard/login.html", "w", encoding="utf-8", errors="xmlcharrefreplace") as f:
    f.write(content)
print("SUCCESS: Midnight Slate split login page written.")
