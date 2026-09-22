from pathlib import Path

text = Path("src/api/main.py").read_text(encoding="utf-8")
lines = text.splitlines()
# Show lines 840-870
for i in range(839, 875):
    print(f"{i+1:4d}  {lines[i][:100]!r}")
