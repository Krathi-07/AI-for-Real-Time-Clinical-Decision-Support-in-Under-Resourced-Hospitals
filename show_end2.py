from pathlib import Path

MAIN = Path("src/api/main.py")
text = MAIN.read_text(encoding="utf-8")
lines = text.splitlines(keepends=True)

# Show lines 863-900
for i in range(862, 905):
    if i < len(lines):
        print(f"{i+1:4d}  {lines[i][:100]!r}")
