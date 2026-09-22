from pathlib import Path

text = Path("src/api/main.py").read_text(encoding="utf-8")
lines = text.splitlines()
for i, line in enumerate(lines, 1):
    if "patient_id" in line and ("def " in line or "async" in line):
        print(f"\n=== Route at line {i}: {line.strip()} ===")
    if "trendChart" in line or "Chart.js" in line or "return html(" in line:
        print(f"{i:4d}  {line[:80]!r}")
