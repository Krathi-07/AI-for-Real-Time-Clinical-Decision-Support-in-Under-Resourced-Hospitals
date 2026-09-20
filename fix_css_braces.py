# fix_css_braces.py
# Run from: C:\Projects\clinical-ai
# Command:  uv run python fix_css_braces.py
#
# The injected CSS landed inside a Python f-string.
# Python f-strings interpret { } as expression slots.
# CSS rules like  body.dark { background: #0f0f1a; }
# must be written  body.dark {{ background: #0f0f1a; }}
# inside an f-string so Python ignores them.
# -------------------------------------------------------

from pathlib import Path

MAIN = Path("src/api/main.py")
text = MAIN.read_text(encoding="utf-8")

# ── Strategy ──────────────────────────────────────────
# Find the block we injected (starts with the dark-mode
# comment) and double every { } that is NOT already doubled.
# We target only our injected block, not the whole file.
# ──────────────────────────────────────────────────────

START_MARKER = "/* ── Dark mode ── */"
END_MARKER   = ".search-wrap input:focus { border-color: #6c3fcf;"

if START_MARKER not in text:
    print("❌  Injected CSS block not found — nothing to fix.")
    raise SystemExit(1)

start = text.index(START_MARKER)
end   = text.index(END_MARKER) + len(END_MARKER)

# Grab the CSS block
css_block = text[start:end]

# Check if it's already doubled (idempotent)
if "{{" in css_block:
    print("ℹ️  Braces already doubled — checking if error persists for another reason.")
else:
    # Double every single { and } that is not yet doubled
    # Step 1: temporarily replace already-doubled ones with placeholders
    css_fixed = css_block.replace("{{", "\x00L\x00").replace("}}", "\x00R\x00")
    # Step 2: double all remaining singles
    css_fixed = css_fixed.replace("{", "{{").replace("}", "}}")
    # Step 3: restore placeholders
    css_fixed = css_fixed.replace("\x00L\x00", "{{").replace("\x00R\x00", "}}")

    text = text[:start] + css_fixed + text[end:]
    MAIN.write_text(text, encoding="utf-8")
    print("✅  All CSS curly braces inside f-string are now doubled.")

# Also fix the JS block if it has the same problem
JS_MARKER = "// ── Patient search filter ──"
if JS_MARKER in text:
    # Re-read after potential write above
    text = MAIN.read_text(encoding="utf-8")
    js_start = text.index(JS_MARKER)
    # Find the closing </script> after the JS block
    js_end_marker = "setInterval(refreshStats, 30000);"
    if js_end_marker in text:
        js_end = text.index(js_end_marker) + len(js_end_marker)
        js_block = text[js_start:js_end]
        if "{{" not in js_block and "{" in js_block:
            js_fixed = js_block.replace("{", "{{").replace("}", "}}")
            text = text[:js_start] + js_fixed + text[js_end:]
            MAIN.write_text(text, encoding="utf-8")
            print("✅  JS block curly braces doubled too.")
        else:
            print("ℹ️  JS block braces already OK.")

print("\nNow run:")
print("  uv run python -m uvicorn src.api.main:app --reload --port 8000")
print("  Then open http://localhost:8000/dashboard")
