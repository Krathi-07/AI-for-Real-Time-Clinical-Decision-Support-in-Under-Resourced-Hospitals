# fix_inline_colors.py

with open("src/api/main.py", "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

# Replace all hardcoded light/muted colors with CSS variables
replacements = [
    ('style="color:#64748b;font-size:.85rem;margin-bottom:1.5rem"',
     'style="color:var(--text-muted);font-size:.85rem;margin-bottom:1.5rem"'),
    ('style="color:#64748b;font-size:.8rem"',
     'style="color:var(--text-muted);font-size:.8rem"'),
    ('style="color:#e2e8f0;font-size:1.4rem"',
     'style="color:var(--text);font-size:1.4rem;font-weight:700"'),
    ('style="color:#64748b"',
     'style="color:var(--text-muted)"'),
    ('style="color:#e2e8f0"',
     'style="color:var(--text)"'),
    ('style="color:#64748b;font-size:.85rem;margin-bottom:1.2rem"',
     'style="color:var(--text-muted);font-size:.85rem;margin-bottom:1.2rem"'),
    ("style='color:#94a3b8'",
     "style='color:var(--text-muted)'"),
    ("style='color:#e2e8f0'",
     "style='color:var(--text)'"),
    ('style="color:#64748b;font-size:.85rem;margin-top:.3rem"',
     'style="color:var(--text-muted);font-size:.85rem;margin-top:.3rem"'),
    ('display:flex;justify-content:space-between;font-size:.85rem;color:#94a3b8;margin-bottom:.3rem',
     'display:flex;justify-content:space-between;font-size:.85rem;color:var(--text-muted);margin-bottom:.3rem'),
    ('style="color:#64748b;font-size:.85rem;margin-top:.3rem"',
     'style="color:var(--text-muted);font-size:.85rem;margin-top:.3rem"'),
    ('style="color:#64748b;font-size:.85rem"',
     'style="color:var(--text-muted);font-size:.85rem"'),
    ('color:#e2e8f0;font-size:0.95rem;min-height:2.5rem',
     'color:var(--text);font-size:0.95rem;min-height:2.5rem'),
]

count = 0
for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        count += 1

with open("src/api/main.py", "w", encoding="utf-8", errors="xmlcharrefreplace") as f:
    f.write(content)
print(f"SUCCESS: Fixed {count} inline color styles.")
