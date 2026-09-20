# show_login.py
# Run from: C:\Projects\clinical-ai
# Command:  uv run python show_login.py

from pathlib import Path

text = Path("src/api/main.py").read_text(encoding="utf-8")
lines = text.splitlines()

# Find the login page function/route
start = None
for i, line in enumerate(lines):
    if "def login_page" in line or ('"/login"' in line and "@app" in line):
        start = i
        break

if start is None:
    print("Could not find login route — searching for 'themeBtn' instead:")
    for i, line in enumerate(lines):
        if "themeBtn" in line or "toggleTheme" in line or "Dark" in line and "button" in line.lower():
            print(f"{i+1:4d}  {line}")
else:
    print(f"=== Login route starts at line {start+1} ===\n")
    for i, line in enumerate(lines[start:start+120], start=start+1):
        print(f"{i:4d}  {line}")
        