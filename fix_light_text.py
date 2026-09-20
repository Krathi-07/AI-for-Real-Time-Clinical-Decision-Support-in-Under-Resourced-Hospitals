# fix_light_text.py

with open("src/api/main.py", "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

OLD = "  [data-theme=\"light\"] input,[data-theme=\"light\"] select{{background:#f5f3ff!important;color:#1e1b4b!important;border-color:#c4b5fd!important}}"

NEW = """  [data-theme="light"] input,[data-theme="light"] select,[data-theme="light"] textarea{{background:#ffffff!important;color:#1e1b4b!important;border-color:#c4b5fd!important}}
  [data-theme="light"] input::placeholder,[data-theme="light"] textarea::placeholder{{color:#6b7280!important}}
  [data-theme="light"] .form-group label{{color:#4c1d95!important}}
  [data-theme="light"] .card{{box-shadow:0 4px 24px rgba(124,58,237,.08)!important}}
  [data-theme="light"] span{{color:#1e1b4b!important}}
  [data-theme="light"] small{{color:#4c1d95!important}}"""

if OLD not in content:
    print("ERROR: Could not find target line")
else:
    content = content.replace(OLD, NEW, 1)
    with open("src/api/main.py", "w", encoding="utf-8", errors="xmlcharrefreplace") as f:
        f.write(content)
    print("SUCCESS: Light mode text contrast fixed.")
    