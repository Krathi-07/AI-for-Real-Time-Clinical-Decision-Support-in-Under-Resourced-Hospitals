with open("src/api/main.py", "r", encoding="utf-8") as f:
    content = f.read()

old = '["Attending Doctor", doctor["full_name"], "Hospital", doctor["hospital"]]'
new = '["Attending Doctor", "Dr. Clinical AI", "Hospital", doctor["hospital"]]'

if old in content:
    content = content.replace(old, new)
    with open("src/api/main.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ Fixed: Attending Doctor is now Dr. Clinical AI")
else:
    print("⚠️ Not found")
    