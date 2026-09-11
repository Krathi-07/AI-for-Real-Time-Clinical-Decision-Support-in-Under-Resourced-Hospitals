from pathlib import Path

text = Path("src/api/main.py").read_text(encoding="utf-8")

# After login, go to /about instead of /dashboard
old = 'return RedirectResponse(url="/dashboard", status_code=303)'
new = 'return RedirectResponse(url="/about", status_code=303)'

if old in text:
    text = text.replace(old, new, 1)  # only first occurrence = login redirect
    Path("src/api/main.py").write_text(text, encoding="utf-8")
    print("login redirect updated OK")
else:
    print("ERROR: pattern not found")