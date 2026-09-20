# apply_toggle.py

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
    --navy-950:#060d1f;--navy-900:#0a1628;--navy-800:#0f2044;--navy-700:#1a3160;
    --text:#e8edf5;--text-muted:#8fa3c0;--border:#1e3358;
  }}
  [data-theme="dark"] tr:hover td{{background:#0f2044}}
  [data-theme="light"]{{
    --navy-950:#f0f4ff;--navy-900:#ffffff;--navy-800:#e8edf8;--navy-700:#d1daf0;
    --text:#0f1c3f;--text-muted:#4a6080;--border:#c5d0e8;
  }}
  [data-theme="light"] tr:hover td{{background:#e8edf8}}
  .theme-toggle{{background:var(--navy-800);border:1px solid var(--border);
    color:var(--text);padding:.35rem .8rem;border-radius:20px;cursor:pointer;
    font-size:.8rem;font-weight:600;font-family:'Inter',sans-serif;transition:.2s}}
  .theme-toggle:hover{{border-color:var(--blue-500)}}"""

OLD_NAV = """<nav class="navbar">
  <h1>ðŸ¥ ClinicalAI â€" Decision Support</h1>
  <div>{nav}
    {"<a href='/dashboard'>Dashboard</a><a href='/register-patient'>Register Patient</a><a href='/logout'>Logout</a>" if doctor_name else ""}
  </div>
</nav>"""

NEW_NAV = """<nav class="navbar">
  <h1>🏥 ClinicalAI — Decision Support</h1>
  <div style="display:flex;align-items:center;gap:1rem">
    <button class="theme-toggle" onclick="toggleTheme()" id="themeBtn">☀ Light</button>
    {nav}
    {"<a href='/dashboard'>Dashboard</a><a href='/register-patient'>Register Patient</a><a href='/logout'>Logout</a>" if doctor_name else ""}
  </div>
</nav>
<script>
  (function(){{
    var t=localStorage.getItem('theme')||(window.matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');
    document.documentElement.setAttribute('data-theme',t);
    document.addEventListener('DOMContentLoaded',function(){{
      var btn=document.getElementById('themeBtn');
      if(btn)btn.textContent=t==='dark'?'☀ Light':'🌙 Dark';
    }});
  }})();
  function toggleTheme(){{
    var t=document.documentElement.getAttribute('data-theme')==='dark'?'light':'dark';
    document.documentElement.setAttribute('data-theme',t);
    localStorage.setItem('theme',t);
    var btn=document.getElementById('themeBtn');
    if(btn)btn.textContent=t==='dark'?'☀ Light':'🌙 Dark';
  }}
</script>"""

with open("src/api/main.py", "r", encoding="utf-8") as f:
    content = f.read()

ok = True
if OLD_MEDIA not in content:
    print("ERROR: Could not find media query block.")
    ok = False
if OLD_NAV not in content:
    print("ERROR: Could not find navbar block.")
    ok = False

if ok:
    content = content.replace(OLD_MEDIA, NEW_MEDIA, 1)
    content = content.replace(OLD_NAV, NEW_NAV, 1)
    with open("src/api/main.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: Dark/light toggle added to navbar.")
    