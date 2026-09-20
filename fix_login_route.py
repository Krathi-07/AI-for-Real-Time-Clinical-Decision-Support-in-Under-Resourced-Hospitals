# fix_login_route.py

with open("src/api/main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find the login_page function and replace it to serve the HTML file
OLD = '''@app.get("/login", response_class=HTMLResponse)
async def login_page(error: str = ""):'''

NEW = '''@app.get("/login", response_class=HTMLResponse)
async def login_page(error: str = ""):
    from fastapi.responses import FileResponse
    return FileResponse("src/dashboard/login.html")

@app.get("/login-OLD", response_class=HTMLResponse)
async def login_page_old(error: str = ""):'''

if OLD not in content:
    print("ERROR: Could not find login_page function.")
else:
    content = content.replace(OLD, NEW, 1)
    with open("src/api/main.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: Login route now serves login.html")
    