from pathlib import Path

text = Path("src/dashboard/index.html").read_text(encoding="utf-8")

text = text.replace('href="#about"', 'href="/about"')
text = text.replace('href="#demo"', 'href="/demo"')
text = text.replace('href="#federated"', 'href="/federated"')
text = text.replace('href="#audit"', 'href="/audit-page"')

# Fix Run Live Demo button to go to /demo
text = text.replace('href="#demo-section"', 'href="/demo"')
text = text.replace("document.getElementById('demo').scrollIntoView", "window.location.href='/demo'//")

Path("src/dashboard/index.html").write_text(text, encoding="utf-8")
print("nav links updated OK")