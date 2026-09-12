with open("src/api/main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find and remove the entire team section
start_marker = "\n    <div style=\"background:linear-gradient(135deg,#111827,#0f2820);border:1px solid #14532d;border-radius:14px;padding:1.75rem;margin-bottom:2rem\">\n      <div style=\"font-size:0.72rem;color:#22c55e;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:14px\">👥 Project Team</div>"
end_marker = "\n    <div style=\"background:rgba(6,182,212,0.06)"

idx_start = content.find(start_marker)
idx_end = content.find(end_marker)

if idx_start != -1 and idx_end != -1:
    content = content[:idx_start] + "\n" + content[idx_end:]
    with open("src/api/main.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ Team section removed.")
else:
    print(f"Start found: {idx_start != -1}, End found: {idx_end != -1}")
    print("⚠️ Could not locate section precisely.")
    