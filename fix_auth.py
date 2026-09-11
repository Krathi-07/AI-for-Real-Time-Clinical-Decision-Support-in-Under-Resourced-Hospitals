from pathlib import Path

text = Path("src/api/main.py").read_text(encoding="utf-8")

text = text.replace(
    '''@app.get("/about", include_in_schema=False)
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
    return FileResponse("src/dashboard/audit_page.html")''',
    '''@app.get("/about", include_in_schema=False)
def about_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return FileResponse("src/dashboard/about.html")


@app.get("/federated", include_in_schema=False)
def federated_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return FileResponse("src/dashboard/federated.html")


@app.get("/audit-page", include_in_schema=False)
def audit_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return FileResponse("src/dashboard/audit_page.html")'''
)

Path("src/api/main.py").write_text(text, encoding="utf-8")
print("auth fixed OK")