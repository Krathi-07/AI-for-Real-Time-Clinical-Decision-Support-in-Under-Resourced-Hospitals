# show_lines.py
# Run from: C:\Projects\clinical-ai
# Command:  uv run python show_lines.py

from pathlib import Path

MAIN = Path("src/api/main.py")
lines = MAIN.read_text(encoding="utf-8").splitlines()

print("=== Lines 225 – 250 of main.py ===\n")
for i, line in enumerate(lines[224:250], start=225):
    marker = " <<< ERROR" if i == 234 else ""
    print(f"{i:4d}  {line}{marker}")
    