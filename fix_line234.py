# fix_line234.py
# Run from: C:\Projects\clinical-ai
# Command:  uv run python fix_line234.py

from pathlib import Path

MAIN = Path("src/api/main.py")
lines = MAIN.read_text(encoding="utf-8").splitlines(keepends=True)

# Lines 234-235 (0-indexed: 233-234) look like:
#   {"<a href='/dashboard'>...</a><button onclick='toggleDark()' ...>🌙 Dark Mode</button>
#                   <a href='/logout'>Logout</a>" if doctor_name else ""}
#
# We need to strip everything from <button onclick='toggleDark() back to just:
#   {"<a href='/dashboard'>Dashboard</a><a href='/register-patient'>Register Patient</a>
#                   <a href='/logout'>Logout</a>" if doctor_name else ""}

import re

fixed_count = 0
for i, line in enumerate(lines):
    # Find the line that has toggleDark injected inside the f-string nav block
    if "toggleDark" in line and "href='/dashboard'" in line:
        # Remove the injected button — everything from <button onclick='toggleDark() to </button>
        cleaned = re.sub(
            r"<button onclick='toggleDark\(\)'[^>]*>.*?</button>\s*",
            "",
            line
        )
        if cleaned != line:
            lines[i] = cleaned
            fixed_count += 1
            print(f"✅  Line {i+1} fixed.")
            print(f"    Before: {line.strip()[:100]}")
            print(f"    After:  {cleaned.strip()[:100]}")

if fixed_count:
    MAIN.write_text("".join(lines), encoding="utf-8")
    print("\n✅  main.py saved. The injected duplicate dark-mode button is removed.")
else:
    print("⚠️  Pattern not found — checking for alternate form...")
    # Try finding the line by the emoji
    for i, line in enumerate(lines):
        if "🌙 Dark Mode" in line and "href='/dashboard'" in line:
            cleaned = re.sub(r"<button[^>]*>🌙 Dark Mode</button>\s*", "", line)
            if cleaned != line:
                lines[i] = cleaned
                MAIN.write_text("".join(lines), encoding="utf-8")
                print(f"✅  Line {i+1} fixed via emoji pattern.")
                break
    else:
        print("❌  Could not auto-fix. Manual fix needed — see instructions below.")
        print()
        print("Open src/api/main.py, find line 234, and change it to:")
        print("""    {\"<a href='/dashboard'>Dashboard</a><a href='/register-patient'>Register Patient</a>""")
        print("(remove the <button onclick='toggleDark()'...>🌙 Dark Mode</button> part)")

print("\nNext:")
print("  uv run python -m uvicorn src.api.main:app --reload --port 8000")
