from pathlib import Path

text = Path("src/api/main.py").read_text(encoding="utf-8")

new_routes = """
@app.get("/about", include_in_schema=False)
def about_page(request: Request):
    if not require_login(request):
        return RedirectResponse(url="/login", status_code=303)
    return FileResponse("src/dashboard/about.html")


@app.get("/federated", include_in_schema=False)
def federated_page(request: Request):
    if not require_login(request):
        return RedirectResponse(url="/login", status_code=303)
    return FileResponse("src/dashboard/federated.html")


@app.get("/audit-page", include_in_schema=False)
def audit_page(request: Request):
    if not require_login(request):
        return RedirectResponse(url="/login", status_code=303)
    return FileResponse("src/dashboard/audit_page.html")


"""

old = "# --- Health ---"
if old in text:
    text = text.replace(old, new_routes + "# --- Health ---")
    Path("src/api/main.py").write_text(text, encoding="utf-8")
    print("routes added OK")
else:
    print("ERROR: pattern not found")