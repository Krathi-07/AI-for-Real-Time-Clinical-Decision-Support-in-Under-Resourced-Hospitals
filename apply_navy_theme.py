# apply_navy_theme.py

OLD = """  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh}}
  .navbar{{background:#1e293b;padding:1rem 2rem;display:flex;justify-content:space-between;
           align-items:center;border-bottom:1px solid #334155}}
  .navbar h1{{color:#6ee7b7;font-size:1.2rem;font-weight:700}}
  .navbar a{{color:#94a3b8;text-decoration:none;margin-left:1.5rem;font-size:.9rem}}
  .navbar a:hover{{color:#6ee7b7}}
  .container{{max-width:1100px;margin:2rem auto;padding:0 1.5rem}}
  .card{{background:#1e293b;border-radius:12px;padding:1.5rem;margin-bottom:1.5rem;
         border:1px solid #334155}}
  .card h2{{color:#6ee7b7;margin-bottom:1rem;font-size:1.1rem}}
  input,select,textarea{{width:100%;padding:.6rem .8rem;background:#0f172a;border:1px solid #334155;
    border-radius:6px;color:#e2e8f0;font-size:.9rem;margin-top:.3rem}}
  input:focus,select:focus{{outline:none;border-color:#6ee7b7}}
  .btn{{padding:.6rem 1.4rem;border:none;border-radius:6px;cursor:pointer;
        font-size:.9rem;font-weight:600;transition:.2s}}
  .btn-primary{{background:#10b981;color:#fff}}
  .btn-primary:hover{{background:#059669}}
  .btn-secondary{{background:#334155;color:#e2e8f0}}
  .btn-danger{{background:#ef4444;color:#fff}}
  .form-group{{margin-bottom:1rem}}
  .form-group label{{font-size:.85rem;color:#94a3b8;display:block;margin-bottom:.2rem}}
  .form-row{{display:grid;grid-template-columns:1fr 1fr;gap:1rem}}
  .badge{{display:inline-block;padding:.2rem .6rem;border-radius:20px;font-size:.75rem;font-weight:600}}
  .badge-critical{{background:#7f1d1d;color:#fca5a5}}
  .badge-high{{background:#78350f;color:#fcd34d}}
  .badge-moderate{{background:#1e3a5f;color:#93c5fd}}
  .badge-low{{background:#14532d;color:#86efac}}
  table{{width:100%;border-collapse:collapse;font-size:.9rem}}
  th{{text-align:left;padding:.7rem 1rem;background:#0f172a;color:#64748b;font-size:.8rem;text-transform:uppercase}}
  td{{padding:.7rem 1rem;border-bottom:1px solid #1e293b}}
  tr:hover td{{background:#1e293b}}
  .alert-success{{background:#14532d;color:#86efac;padding:.8rem 1rem;border-radius:8px;margin-bottom:1rem}}
  .alert-error{{background:#7f1d1d;color:#fca5a5;padding:.8rem 1rem;border-radius:8px;margin-bottom:1rem}}
  .risk-bar{{height:8px;border-radius:4px;background:#1e293b;margin-top:.4rem}}
  .risk-fill{{height:100%;border-radius:4px}}
  a{{color:#6ee7b7;text-decoration:none}}
  a:hover{{text-decoration:underline}}"""

NEW = """  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
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
  }}"""

with open("src/api/main.py", "r", encoding="utf-8") as f:
    content = f.read()

if OLD not in content:
    print("ERROR: Could not find CSS block.")
    # Debug: show what the file actually has around line 85
    lines = content.split("\n")
    for i, line in enumerate(lines[83:100], start=84):
        print(f"{i}: {line!r}")
else:
    content = content.replace(OLD, NEW, 1)
    with open("src/api/main.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: Clinical Navy theme applied.")
    