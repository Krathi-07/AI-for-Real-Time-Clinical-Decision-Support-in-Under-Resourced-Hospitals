with open("src/api/main.py", "r", encoding="utf-8") as f:
    content = f.read()

old = "        <h2 style=\"color:#e2e8f0;font-size:1.4rem\">Welcome, {doctor['full_name']}</h2>"
new = "        <h2 style=\"color:#e2e8f0;font-size:1.4rem\">🩺 Welcome, Dr. Clinical AI</h2>"

if old in content:
    content = content.replace(old, new)
    with open("src/api/main.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: Welcome message fixed.")
else:
    print("NOT FOUND - paste the exact line from your file.")
    