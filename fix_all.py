# fix_all.py

with open("src/api/main.py", "r", encoding="utf-8") as f:
    content = f.read()

# ── 1. Add theme toggle to navbar + fix light mode text ──
OLD_NAV = """<nav class="navbar">
  <h1>🏥 ClinicalAI — Decision Support</h1>
  <div>{nav}
    {"<a href='/dashboard'>Dashboard</a><a href='/register-patient'>Register Patient</a><a href='/logout'>Logout</a>" if doctor_name else ""}
  </div>
</nav>
<div class="container">
{body}
</div>
</body>
</html>"""

NEW_NAV = """<nav class="navbar">
  <h1>\xf0\x9f\x8f\xa5 ClinicalAI \xe2\x80\x93 Decision Support</h1>
  <div style="display:flex;align-items:center;gap:1rem">
    <button id="themeBtn" onclick="toggleTheme()"
      style="background:var(--navy-800);border:1px solid var(--border);color:var(--text);
             padding:.3rem .8rem;border-radius:20px;cursor:pointer;font-size:.78rem;
             font-weight:600;font-family:Inter,sans-serif;transition:.2s">
      &#9728; Light
    </button>
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
  var btn=document.getElementById('themeBtn');
  if(btn)btn.textContent=t==='dark'?'&#9728; Light':'&#127769; Dark';
}})();
function toggleTheme(){{
  var t=document.documentElement.getAttribute('data-theme')==='dark'?'light':'dark';
  document.documentElement.setAttribute('data-theme',t);
  localStorage.setItem('theme',t);
  var btn=document.getElementById('themeBtn');
  if(btn)btn.textContent=t==='dark'?'&#9728; Light':'&#127769; Dark';
}}
</script>
</body>
</html>"""

# ── 2. Fix light mode — proper contrast for all text ──
OLD_MEDIA = """  @media(prefers-color-scheme:light){{
    :root{{--navy-950:#f0f4ff;--navy-900:#ffffff;--navy-800:#e8edf8;--navy-700:#d1daf0;
      --text:#0f1c3f;--text-muted:#4a6080;--border:#c5d0e8}}
    tr:hover td{{background:#e8edf8}}
  }}"""

NEW_MEDIA = """  @media(prefers-color-scheme:light){{
    :root{{--navy-950:#f0f4ff;--navy-900:#ffffff;--navy-800:#e8edf8;--navy-700:#d1daf0;
      --text:#0f1c3f;--text-muted:#4a6080;--border:#c5d0e8}}
    tr:hover td{{background:#e8edf8}}
  }}
  [data-theme="dark"]{{
    --navy-950:#060d1f!important;--navy-900:#0a1628!important;
    --navy-800:#0f2044!important;--navy-700:#1a3160!important;
    --text:#e8edf5!important;--text-muted:#8fa3c0!important;--border:#1e3358!important;
  }}
  [data-theme="light"]{{
    --navy-950:#f0f4ff!important;--navy-900:#ffffff!important;
    --navy-800:#e8edf8!important;--navy-700:#d1daf0!important;
    --text:#0f1c3f!important;--text-muted:#4a6080!important;--border:#c5d0e8!important;
  }}
  [data-theme="light"] .navbar h1{{color:#1d4ed8}}
  [data-theme="light"] .navbar a{{color:#4a6080}}
  [data-theme="light"] .navbar a:hover{{color:#1d4ed8}}
  [data-theme="light"] h1,[data-theme="light"] h2,[data-theme="light"] h3{{color:#0f1c3f}}
  [data-theme="light"] td{{color:#0f1c3f}}
  [data-theme="light"] tr:hover td{{background:#e8edf8}}"""

ok = True
if OLD_NAV not in content:
    print("ERROR: navbar block not found")
    ok = False
if OLD_MEDIA not in content:
    print("ERROR: media query block not found")
    ok = False

if ok:
    content = content.replace(OLD_NAV, NEW_NAV, 1)
    content = content.replace(OLD_MEDIA, NEW_MEDIA, 1)
    with open("src/api/main.py", "w", encoding="utf-8", errors="xmlcharrefreplace") as f:
        f.write(content)
    print("SUCCESS: Theme toggle + light mode contrast fixed on all dashboard pages.")
    