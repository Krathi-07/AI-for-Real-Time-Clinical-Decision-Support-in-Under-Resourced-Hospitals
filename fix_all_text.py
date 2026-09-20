# fix_all_text.py

with open("src/api/main.py", "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

OLD = "  [data-theme=\"light\"] small{{color:#4c1d95!important}}"

NEW = """  [data-theme="light"] small{{color:#4c1d95!important}}
  [data-theme="light"] *{{color:#1e1b4b}}
  [data-theme="light"] .badge-critical{{color:#dc2626!important}}
  [data-theme="light"] .badge-high{{color:#d97706!important}}
  [data-theme="light"] .badge-moderate{{color:#7c3aed!important}}
  [data-theme="light"] .badge-low{{color:#059669!important}}
  [data-theme="light"] .btn-primary{{color:#fff!important}}
  [data-theme="light"] .btn-danger{{color:#fff!important}}
  [data-theme="light"] a{{color:#6d28d9!important}}
  [data-theme="light"] a:hover{{color:#7c3aed!important}}
  [data-theme="light"] .navbar a{{color:#5b21b6!important}}
  [data-theme="light"] #themeBtn{{color:#4c1d95!important}}"""

if OLD not in content:
    print("ERROR: target not found")
else:
    content = content.replace(OLD, NEW, 1)
    with open("src/api/main.py", "w", encoding="utf-8", errors="xmlcharrefreplace") as f:
        f.write(content)
    print("SUCCESS: All light mode text forced black.")
    