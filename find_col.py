from pathlib import Path

text = Path("src/api/main.py").read_text(encoding="utf-8")
lines = text.splitlines()
for i, line in enumerate(lines, 1):
    if "analysed_at" in line or ("patient-trend" in line and "def " in line):
        print(f"{i:4d}  {line!r}")
