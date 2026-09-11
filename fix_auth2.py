from pathlib import Path

text = Path("src/api/main.py").read_text(encoding="utf-8")
text = text.replace("if not require_login(request):", "user = get_current_user(request)\n    if not user:")
text = text.replace("return RedirectResponse(url=\"/login\", status_code=303)", "return RedirectResponse(url=\"/login\")")
Path("src/api/main.py").write_text(text, encoding="utf-8")
print("done")