import re

with open("src/api/main.py", "r", encoding="utf-8") as f:
    code = f.read()

old_css = '''  :root{{
    --bg:#0c0e1a;--surface:#111322;--surface2:#1a1d30;--surface3:#252840;
    --violet:#7c3aed;--violet-dim:#6d28d9;--violet-lit:#a78bfa;--violet-glow:rgba(124,58,237,.15);
    --text:#e2e4f0;--text-muted:#8b90b0;--text-dark:#0f1035;--border:#2a2d45;
    --success:#10b981;--warning:#f59e0b;--danger:#ef4444;
  }}'''

new_css = '''  :root{{
    --bg:#0c0e1a;--surface:#111827;--surface2:#1a1f35;--surface3:#252a45;
    --violet:#7c3aed;--violet-dim:#6d28d9;--violet-lit:#a78bfa;--violet-glow:rgba(124,58,237,.18);
    --text:#f1f5f9;--text-muted:#94a3b8;--text-dark:#0f172a;--border:#2a2f4a;
    --success:#10b981;--warning:#f59e0b;--danger:#ef4444;
    --navy:#1e3a5f;--navy-dim:#162d4a;--navy-lit:#2563eb;--navy-glow:rgba(30,58,95,.15);
  }}'''

if old_css in code:
    code = code.replace(old_css, new_css)
    print("✅ CSS variables updated")
else:
    print("❌ CSS variables not found")

old_light = '''  @media(prefers-color-scheme:light){{
    :root{{--bg:#f5f3ff;--surface:#ffffff;--surface2:#ede9fe;--surface3:#ddd6fe;
      --text:#1e1b4b;--text-muted:#4c1d95;--border:#c4b5fd}}
    tr:hover td{{background:#ede9fe}}
  }}'''

new_light = '''  @media(prefers-color-scheme:light){{
    :root{{--bg:#f0f4ff;--surface:#ffffff;--surface2:#e8eef8;--surface3:#d1ddf5;
      --text:#0f172a;--text-muted:#1e3a5f;--border:#93c5fd}}
    tr:hover td{{background:#e8eef8}}
  }}'''

if old_light in code:
    code = code.replace(old_light, new_light)
    print("✅ Light mode media query updated")
else:
    print("❌ Light mode media query not found")

old_light_theme = '''  [data-theme="light"]{{
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
  [data-theme="light"] li{{color:#1e1b4b!important;font-weight:500}}
  [data-theme="light"] .card li{{color:#1e1b4b!important}}
  [data-theme="light"] .badge-critical{{color:#dc2626!important}}
  [data-theme="light"] .badge-high{{color:#d97706!important}}
  [data-theme="light"] .badge-moderate{{color:#7c3aed!important}}
  [data-theme="light"] .badge-low{{color:#059669!important}}
  [data-theme="light"] .btn-primary{{color:#fff!important}}
  [data-theme="light"] .btn-danger{{color:#fff!important}}
  [data-theme="light"] a{{color:#6d28d9!important}}
  [data-theme="light"] a:hover{{color:#7c3aed!important}}
  [data-theme="light"] .navbar a{{color:#5b21b6!important}}
  [data-theme="light"] #themeBtn{{color:#4c1d95!important}}'''

new_light_theme = '''  [data-theme="light"]{{
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
  [data-theme="light"] .stat-card.avg .stat-value{{color:#1d4ed8!important}}'''

if old_light_theme in code:
    code = code.replace(old_light_theme, new_light_theme)
    print("✅ Light theme overrides updated")
else:
    print("❌ Light theme overrides not found")

old_dark_theme = '''  [data-theme="dark"]{{
    --bg:#0c0e1a!important;--surface:#111322!important;--surface2:#1a1d30!important;
    --surface3:#252840!important;--text:#e2e4f0!important;--text-muted:#8b90b0!important;
    --border:#2a2d45!important;
  }}
  [data-theme="dark"] td{{color:#e2e4f0!important}}
  [data-theme="dark"] tr:hover td{{background:#1a1d30!important}}'''

new_dark_theme = '''  [data-theme="dark"]{{
    --bg:#0c0e1a!important;--surface:#111827!important;--surface2:#1a1f35!important;
    --surface3:#252a45!important;--text:#f1f5f9!important;--text-muted:#94a3b8!important;
    --border:#2a2f4a!important;
  }}
  [data-theme="dark"] td{{color:#f1f5f9!important}}
  [data-theme="dark"] th{{color:#94a3b8!important}}
  [data-theme="dark"] tr:hover td{{background:#1a1f35!important}}
  [data-theme="dark"] .stat-card .stat-label{{color:#94a3b8!important}}
  [data-theme="dark"] .stat-card .stat-value{{color:#f1f5f9!important}}'''

if old_dark_theme in code:
    code = code.replace(old_dark_theme, new_dark_theme)
    print("✅ Dark theme overrides updated")
else:
    print("❌ Dark theme overrides not found")

old_navbar_title = "    nav = f\"<span style='color:#6ee7b7'>👨‍⚕️ {doctor_name}</span>\" if doctor_name else \"\""

new_navbar_title = "    nav = f\"<span style='color:#a78bfa;font-weight:600'>👨‍⚕️ {doctor_name}</span>\" if doctor_name else \"\""

if old_navbar_title in code:
    code = code.replace(old_navbar_title, new_navbar_title)
    print("✅ Doctor name colour updated")
else:
    print("❌ Doctor name colour not found")

with open("src/api/main.py", "w", encoding="utf-8") as f:
    f.write(code)

print("✅ All done — saved to main.py")
