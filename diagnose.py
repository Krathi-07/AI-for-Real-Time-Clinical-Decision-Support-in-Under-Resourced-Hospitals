# diagnose.py  — paste this into clinical-ai/diagnose.py
import os

MAIN_PATH = r"src\api\main.py"

checks = {
    "/stats endpoint": "@app.get(\"/stats\")",
    "filterPatients JS": "filterPatients",
    "patient-table tbody id": "id=\"patient-table\"",
    "stat cards HTML": "stat-card",
    "dark mode toggle": "dark-mode",
    "search box": "searchInput",
    "require_doctor auth": "require_doctor",
    "sqlite3 import": "import sqlite3",
    "CRITICAL badge": "CRITICAL",
    "Analyse button": "Analyse",
}

print(f"\n{'='*55}")
print("  CLINICAL-AI  main.py  DIAGNOSTIC REPORT")
print(f"{'='*55}\n")

if not os.path.exists(MAIN_PATH):
    print(f"❌  FATAL: {MAIN_PATH} not found!")
else:
    content = open(MAIN_PATH, encoding="utf-8").read()
    line_count = content.count("\n")
    print(f"  File: {MAIN_PATH}")
    print(f"  Size: {len(content):,} bytes  |  Lines: {line_count:,}\n")
    print(f"  {'FEATURE':<30}  STATUS")
    print(f"  {'-'*44}")
    for label, token in checks.items():
        found = token in content
        status = "✅  PRESENT" if found else "❌  MISSING"
        print(f"  {label:<30}  {status}")

print(f"\n{'='*55}\n")
