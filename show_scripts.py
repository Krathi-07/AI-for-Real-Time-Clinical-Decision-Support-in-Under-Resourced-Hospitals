from pathlib import Path

MAIN = Path("src/api/main.py")
text = MAIN.read_text(encoding="utf-8")

# Count how many times filterPatients appears
count = text.count("filterPatients")
print(f"filterPatients appears {count} times")

# Count script tags
scripts = text.count("<script>")
print(f"<script> tags: {scripts}")

# Show all script blocks
lines = text.splitlines()
in_script = False
for i, line in enumerate(lines, 1):
    if "<script>" in line:
        in_script = True
    if in_script:
        print(f"{i:4d}  {line}")
    if "</script>" in line and in_script:
        in_script = False
        print("---")
