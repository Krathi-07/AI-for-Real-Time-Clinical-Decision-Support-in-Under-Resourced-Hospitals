from pathlib import Path

text = Path("src/dashboard/demo.html").read_text(encoding="utf-8")

old_nav = """<nav>
  <div class="nav-logo"><div class="dot"></div>Clinical AI — Live Demo</div>
  <div class="nav-right">
    <a href="/dashboard" class="nav-back">Back to Dashboard</a>
    <a href="/logout" class="nav-logout">Logout</a>
  </div>
</nav>"""

new_nav = """<nav>
  <div class="nav-logo"><div class="dot"></div>Clinical AI</div>
  <div class="nav-links">
    <a href="/about">Home</a>
    <a href="/about">About</a>
    <a href="/demo" style="color:var(--cyan)">Live Demo</a>
    <a href="/federated">Federated Learning</a>
    <a href="/audit-page">Audit Log</a>
  </div>
  <div class="nav-right">
    <button class="theme-btn" id="theme-btn" onclick="toggleTheme()">&#9728; Light</button>
    <a href="/logout" class="nav-logout">Logout</a>
  </div>
</nav>"""

if old_nav in text:
    text = text.replace(old_nav, new_nav)
    print("nav replaced OK")
else:
    # Try partial match
    import re
    text = re.sub(r'<nav>.*?</nav>', new_nav, text, flags=re.DOTALL, count=1)
    print("nav replaced via regex")

# Add nav-links and theme-btn styles if not present
if ".nav-links" not in text:
    extra_css = """
  .nav-links { display:flex; gap:24px; }
  .nav-links a { color:var(--muted); text-decoration:none; font-size:0.88rem; font-weight:500; transition:color 0.2s; }
  .nav-links a:hover { color:var(--text); }
  .theme-btn { background:var(--card2); border:1px solid var(--border); color:var(--text); padding:5px 14px; border-radius:999px; cursor:pointer; font-size:0.8rem; font-weight:600; font-family:"DM Sans",sans-serif; transition:all 0.2s; }
  .theme-btn:hover { border-color:#06b6d4; color:#06b6d4; }"""
    text = text.replace("</style>", extra_css + "\n</style>", 1)
    print("nav styles added")

Path("src/dashboard/demo.html").write_text(text, encoding="utf-8")
print("demo.html updated OK")