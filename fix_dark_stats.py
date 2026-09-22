with open("src/api/main.py", "r", encoding="utf-8") as f:
    code = f.read()

old = '''  [data-theme="dark"] .stat-card .stat-label{{color:#94a3b8!important}}
  [data-theme="dark"] .stat-card .stat-value{{color:#f1f5f9!important}}'''

new = '''  [data-theme="dark"] .stat-card{{background:#1a1f35!important;border:1px solid #2a2f4a!important}}
  [data-theme="dark"] .stat-card .stat-label{{color:#94a3b8!important;font-weight:600!important}}
  [data-theme="dark"] .stat-card .stat-value{{color:#ffffff!important;font-weight:800!important}}
  [data-theme="dark"] .stat-card.critical .stat-value{{color:#f87171!important}}
  [data-theme="dark"] .stat-card.high .stat-value{{color:#fb923c!important}}
  [data-theme="dark"] .stat-card.avg .stat-value{{color:#818cf8!important}}'''

if old in code:
    code = code.replace(old, new)
    print("✅ Dark mode stat cards fixed")
else:
    print("❌ Pattern not found")

with open("src/api/main.py", "w", encoding="utf-8") as f:
    f.write(code)
