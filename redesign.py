# redesign.py

with open("src/api/main.py", "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

OLD_CSS = """  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  :root{{
    --navy-950:#060d1f;--navy-900:#0a1628;--navy-800:#0f2044;--navy-700:#1a3160;
    --blue-500:#3b82f6;--blue-400:#60a5fa;--blue-300:#93c5fd;
    --text:#e8edf5;--text-muted:#8fa3c0;--border:#1e3358;
    --success:#10b981;--warning:#f59e0b;--danger:#ef4444;
  }}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Inter',sans-serif;background:var(--navy-950);color:var(--text);min-height:100vh}}
  .navbar{{background:var(--navy-900);padding:1rem 2rem;display:flex;justify-content:space-between;
           align-items:center;border-bottom:1px solid var(--border);
           box-shadow:0 1px 12px rgba(59,130,246,.08)}}
  .navbar h1{{color:var(--blue-400);font-size:1.2rem;font-weight:700;letter-spacing:-.01em}}
  .navbar a{{color:var(--text-muted);text-decoration:none;margin-left:1.5rem;font-size:.9rem;
             font-weight:500;transition:color .15s}}
  .navbar a:hover{{color:var(--blue-400)}}
  .container{{max-width:1100px;margin:2rem auto;padding:0 1.5rem}}
  .card{{background:var(--navy-900);border-radius:12px;padding:1.5rem;margin-bottom:1.5rem;
         border:1px solid var(--border);box-shadow:0 2px 16px rgba(0,0,0,.3)}}
  .card h2{{color:var(--blue-400);margin-bottom:1rem;font-size:1.1rem;font-weight:700}}
  input,select,textarea{{width:100%;padding:.6rem .8rem;background:var(--navy-800);
    border:1px solid var(--border);border-radius:6px;color:var(--text);
    font-size:.9rem;margin-top:.3rem;font-family:'Inter',sans-serif}}
  input:focus,select:focus{{outline:none;border-color:var(--blue-500);
    box-shadow:0 0 0 3px rgba(59,130,246,.15)}}
  .btn{{padding:.6rem 1.4rem;border:none;border-radius:6px;cursor:pointer;
        font-size:.9rem;font-weight:600;transition:.2s;font-family:'Inter',sans-serif}}
  .btn-primary{{background:var(--blue-500);color:#fff}}
  .btn-primary:hover{{background:#2563eb}}
  .btn-secondary{{background:var(--navy-700);color:var(--text)}}
  .btn-secondary:hover{{background:var(--navy-800)}}
  .btn-danger{{background:var(--danger);color:#fff}}
  .form-group{{margin-bottom:1rem}}
  .form-group label{{font-size:.85rem;color:var(--text-muted);display:block;
    margin-bottom:.2rem;font-weight:500}}
  .form-row{{display:grid;grid-template-columns:1fr 1fr;gap:1rem}}
  .badge{{display:inline-block;padding:.2rem .7rem;border-radius:20px;
    font-size:.75rem;font-weight:700;letter-spacing:.02em}}
  .badge-critical{{background:rgba(239,68,68,.2);color:#fca5a5;border:1px solid rgba(239,68,68,.3)}}
  .badge-high{{background:rgba(245,158,11,.2);color:#fcd34d;border:1px solid rgba(245,158,11,.3)}}
  .badge-moderate{{background:rgba(59,130,246,.2);color:#93c5fd;border:1px solid rgba(59,130,246,.3)}}
  .badge-low{{background:rgba(16,185,129,.2);color:#6ee7b7;border:1px solid rgba(16,185,129,.3)}}
  table{{width:100%;border-collapse:collapse;font-size:.9rem}}
  th{{text-align:left;padding:.7rem 1rem;background:var(--navy-950);color:var(--text-muted);
     font-size:.78rem;text-transform:uppercase;letter-spacing:.05em;font-weight:600}}
  td{{padding:.7rem 1rem;border-bottom:1px solid var(--border)}}
  tr:hover td{{background:var(--navy-800)}}
  .alert-success{{background:rgba(16,185,129,.15);color:#6ee7b7;padding:.8rem 1rem;
    border-radius:8px;margin-bottom:1rem;border:1px solid rgba(16,185,129,.3)}}
  .alert-error{{background:rgba(239,68,68,.15);color:#fca5a5;padding:.8rem 1rem;
    border-radius:8px;margin-bottom:1rem;border:1px solid rgba(239,68,68,.3)}}
  .risk-bar{{height:8px;border-radius:4px;background:var(--navy-800);margin-top:.4rem}}
  .risk-fill{{height:100%;border-radius:4px}}
  a{{color:var(--blue-400);text-decoration:none}}
  a:hover{{color:var(--blue-300);text-decoration:underline}}
  h1,h2,h3{{font-weight:700}}
  @media(prefers-color-scheme:light){{
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
  [data-theme="light"] .navbar{{background:#ffffff;border-bottom:1px solid #c5d0e8}}
  [data-theme="light"] .navbar h1{{color:#1d4ed8!important}}
  [data-theme="light"] .navbar a{{color:#4a6080!important}}
  [data-theme="light"] .navbar a:hover{{color:#1d4ed8!important}}
  [data-theme="light"] h1,[data-theme="light"] h2,[data-theme="light"] h3{{color:#0f1c3f!important}}
  [data-theme="light"] td{{color:#0f1c3f!important}}
  [data-theme="light"] p,[data-theme="light"] span,[data-theme="light"] div{{color:#0f1c3f}}
  [data-theme="light"] tr:hover td{{background:#e8edf8}}
  [data-theme="light"] #themeBtn{{background:#e8edf8;color:#0f1c3f;border-color:#c5d0e8}}"""

NEW_CSS = """  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
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
  [data-theme="light"] input,[data-theme="light"] select{{background:#f5f3ff!important;color:#1e1b4b!important;border-color:#c4b5fd!important}}"""

# Fix navbar title and doctor name color
OLD_NAV_H1 = "  nav = f\"<span style='color:#6ee7b7'>\xf0\x9f\x91\xa8\xe2\x80\x8d\xe2\x9a\x95\xef\xb8\x8f {doctor_name}</span>\" if doctor_name else \"\""
NEW_NAV_H1 = "  nav = f\"<span style='color:#a78bfa;font-weight:600'>&#x1f9d1;&#x200d;&#x2695;&#xfe0f; {doctor_name}</span>\" if doctor_name else \"\""

OLD_TITLE = "<title>{title} \xe2\x80\x93 ClinicalAI</title>"
NEW_TITLE = "<title>{title} — ClinicalAI</title>"

OLD_H1 = "<h1>ClinicalAI \xe2\x80\x94 Decision Support</h1>"
NEW_H1 = "<h1>&#x1fa7a; ClinicalAI — Decision Support</h1>"

if OLD_CSS not in content:
    print("ERROR: CSS block not found")
else:
    content = content.replace(OLD_CSS, NEW_CSS, 1)
    # Fix nav doctor color if found
    if OLD_NAV_H1 in content:
        content = content.replace(OLD_NAV_H1, NEW_NAV_H1, 1)
    print("SUCCESS: Midnight Slate violet theme applied to all dashboard pages.")
    with open("src/api/main.py", "w", encoding="utf-8", errors="xmlcharrefreplace") as f:
        f.write(content)
        