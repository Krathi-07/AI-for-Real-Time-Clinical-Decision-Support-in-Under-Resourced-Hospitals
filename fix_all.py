from pathlib import Path

# Fix login redirect to go to /about
text = Path("src/api/main.py").read_text(encoding="utf-8")
lines = text.split("\n")
lines[94] = lines[94].replace("/dashboard", "/about")
Path("src/api/main.py").write_text("\n".join(lines), encoding="utf-8")
print("login redirect fixed - line 95 now:", lines[94].strip())

# Verify pages exist
for f in ["about.html", "federated.html", "audit_page.html", "demo.html"]:
    p = Path("src/dashboard") / f
    print(f"{f}: {'EXISTS' if p.exists() else 'MISSING'} ({p.stat().st_size if p.exists() else 0} bytes)")