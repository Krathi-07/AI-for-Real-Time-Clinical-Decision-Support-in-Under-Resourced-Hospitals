from pathlib import Path

text = Path("src/api/main.py").read_text(encoding="utf-8")
lines = text.splitlines()
start = next(i for i,l in enumerate(lines) if "patient-trend/{patient_id}" in l)
for i, line in enumerate(lines[start:start+40], start+1):
    print(f"{i:4d}  {line}")
