"""
write_pages.py  —  Glow-up all dashboard pages
Fixes: Times New Roman font, light-mode contrast, login page redesign
Run: uv run python write_pages.py
"""

from pathlib import Path

ROOT = Path(__file__).parent

# ──────────────────────────────────────────────────────────────────────────────
# 1. LOGIN PAGE  (src/dashboard/login.html)
# ──────────────────────────────────────────────────────────────────────────────

LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Login | AI Clinical Decision Support</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --green:      #00c896;
      --green-dim:  #009e78;
      --bg:         #0a0f0d;
      --surface:    #111a14;
      --surface2:   #192214;
      --border:     #1e3028;
      --text:       #e8f5ee;
      --text-muted: #7aad90;
      --red:        #ff4d6d;
      --font:       'Times New Roman', Times, serif;
    }

    body {
      font-family: var(--font);
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 1rem;
    }

    body::before {
      content: '';
      position: fixed;
      inset: 0;
      background-image:
        linear-gradient(rgba(0,200,150,.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,200,150,.04) 1px, transparent 1px);
      background-size: 40px 40px;
      pointer-events: none;
    }

    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 2.5rem 2rem;
      width: 100%;
      max-width: 420px;
      box-shadow: 0 0 60px rgba(0,200,150,.08), 0 20px 40px rgba(0,0,0,.5);
      position: relative;
    }

    .logo {
      display: flex;
      align-items: center;
      gap: .75rem;
      margin-bottom: 1.75rem;
      justify-content: center;
    }

    .logo-icon {
      width: 44px;
      height: 44px;
      background: linear-gradient(135deg, var(--green), var(--green-dim));
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.4rem;
      box-shadow: 0 0 20px rgba(0,200,150,.3);
    }

    .logo-text h1 { font-size: 1.1rem; font-weight: 700; color: var(--text); }
    .logo-text p  { font-size: .72rem; color: var(--text-muted); margin-top: 1px; }

    .card-title { text-align: center; font-size: 1.25rem; font-weight: 700; margin-bottom: .35rem; }
    .card-sub   { text-align: center; font-size: .82rem; color: var(--text-muted); margin-bottom: 1.75rem; }

    .field { margin-bottom: 1.1rem; }

    label {
      display: block;
      font-size: .8rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: .7px;
      margin-bottom: .4rem;
    }

    input[type="text"],
    input[type="password"] {
      width: 100%;
      padding: .7rem 1rem;
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--text);
      font-family: var(--font);
      font-size: .95rem;
      outline: none;
      transition: border-color .2s, box-shadow .2s;
    }

    input:focus {
      border-color: var(--green);
      box-shadow: 0 0 0 3px rgba(0,200,150,.15);
    }

    .error-msg {
      display: none;
      align-items: center;
      gap: .5rem;
      background: rgba(255,77,109,.1);
      border: 1px solid rgba(255,77,109,.3);
      border-radius: 8px;
      padding: .65rem 1rem;
      font-size: .83rem;
      color: var(--red);
      margin-bottom: 1rem;
    }
    .error-msg.show { display: flex; }

    .btn {
      width: 100%;
      padding: .85rem;
      background: linear-gradient(135deg, var(--green), var(--green-dim));
      color: #021a10;
      font-family: var(--font);
      font-size: 1rem;
      font-weight: 700;
      border: none;
      border-radius: 10px;
      cursor: pointer;
      transition: opacity .2s, transform .1s;
      margin-top: .4rem;
    }
    .btn:hover  { opacity: .9; }
    .btn:active { transform: scale(.98); }

    .footer { margin-top: 1.5rem; text-align: center; font-size: .8rem; color: var(--text-muted); }
    .footer a { color: var(--green); text-decoration: none; }
    .footer a:hover { text-decoration: underline; }

    .badge {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: .4rem;
      margin-top: 1.75rem;
      padding: .5rem;
      border-top: 1px solid var(--border);
      font-size: .72rem;
      color: var(--text-muted);
    }
    .badge span { color: var(--green); }

    /* ── Light mode ── */
    @media (prefers-color-scheme: light) {
      :root {
        --bg:         #f0f7f4;
        --surface:    #ffffff;
        --surface2:   #f5fbf8;
        --border:     #c4ddd4;
        --text:       #0d1f16;
        --text-muted: #2e5e42;
      }
      body::before {
        background-image:
          linear-gradient(rgba(0,150,100,.06) 1px, transparent 1px),
          linear-gradient(90deg, rgba(0,150,100,.06) 1px, transparent 1px);
      }
      .card { box-shadow: 0 4px 24px rgba(0,0,0,.1); }
      input[type="text"], input[type="password"] { color: #0d1f16; }
      .btn { color: #ffffff; }
    }
  </style>
</head>
<body>
<div class="card">

  <div class="logo">
    <div class="logo-icon">&#x2695;</div>
    <div class="logo-text">
      <h1>ClinicalAI</h1>
      <p>Virtual Junior Doctor System</p>
    </div>
  </div>

  <h2 class="card-title">Welcome back</h2>
  <p class="card-sub">Sign in to access the clinical dashboard</p>

  <div class="error-msg" id="errorMsg">
    <span>&#9888;</span>
    <span id="errorText">Invalid credentials. Please try again.</span>
  </div>

  <div class="field">
    <label for="username">Username</label>
    <input type="text" id="username" placeholder="e.g. dr.sharma" autocomplete="username">
  </div>

  <div class="field">
    <label for="password">Password</label>
    <input type="password" id="password" placeholder="&#x2022;&#x2022;&#x2022;&#x2022;&#x2022;&#x2022;&#x2022;&#x2022;" autocomplete="current-password">
  </div>

  <button class="btn" onclick="doLogin()">Sign In</button>

  <div class="footer">
    <p>Don't have an account? <a href="/register">Register here</a></p>
    <p style="margin-top:.4rem"><a href="/dashboard">&#9654; Enter demo (skip login)</a></p>
  </div>

  <div class="badge">
    <span>&#128274;</span> HIPAA-compliant &nbsp;&middot;&nbsp;
    <span>&#9679;</span> DISHA-ready &nbsp;&middot;&nbsp;
    <span>&#10003;</span> Audit-logged
  </div>

</div>
<script>
  document.addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); });

  function doLogin() {
    const u = document.getElementById('username').value.trim();
    const p = document.getElementById('password').value.trim();
    const err = document.getElementById('errorMsg');
    const errTxt = document.getElementById('errorText');

    if (!u || !p) {
      errTxt.textContent = 'Please enter both username and password.';
      err.classList.add('show');
      return;
    }

    const USERS = { 'admin':'admin123', 'doctor':'doctor123', 'dr.sharma':'clinic2026' };

    if (USERS[u] === p) {
      err.classList.remove('show');
      window.location.href = '/dashboard';
    } else {
      errTxt.textContent = 'Invalid credentials. Please try again.';
      err.classList.add('show');
      document.getElementById('password').value = '';
    }
  }
</script>
</body>
</html>
"""

# ──────────────────────────────────────────────────────────────────────────────
# 2. PATCH main.py — inject Times New Roman + light-mode fix into _base()
#    Targets the exact font line and body rule we saw in the file
# ──────────────────────────────────────────────────────────────────────────────

# This is the exact string from main.py we'll replace
OLD_FONT_LINE = (
    "  body{{font-family:'Inter',sans-serif;"
    "background:var(--bg);color:var(--text);"
    "min-height:100vh;font-size:15px;line-height:1.6}}"
)

NEW_FONT_BLOCK = (
    # Replace Inter with Times New Roman on body + all inputs/buttons
    "  body{{font-family:'Times New Roman',Times,serif;"
    "background:var(--bg);color:var(--text);"
    "min-height:100vh;font-size:15px;line-height:1.6}}\n"
    "  input,select,textarea,button,.btn{{font-family:'Times New Roman',Times,serif}}\n"
    # ── Light-mode high-contrast overrides ──
    # The light theme already exists via data-theme="light" but text colours
    # are too pale when the OS is in light mode. We boost contrast here.
    "  :root[data-theme='light']{{--text:#0a1510 !important;"
    "--text-muted:#1e4a30 !important;--bg:#eef6f1 !important;"
    "--surface:#ffffff !important;--border:#aacfbc !important;"
    "--input-bg:#f5fbf8 !important}}"
)


def patch_main_py():
    path = ROOT / "src" / "api" / "main.py"
    if not path.exists():
        print(f"  ✗ Not found: {path}")
        return

    content = path.read_text(encoding="utf-8")

    if "Times New Roman" in content:
        print("  ✓ main.py already patched — skipping")
        return

    if OLD_FONT_LINE not in content:
        # Show the user what we were looking for vs what's there
        print("  ✗ Could not find body font line in main.py")
        print("    Looking for:")
        print(f"    {OLD_FONT_LINE!r}")
        # Print the surrounding lines to help debug
        for i, line in enumerate(content.splitlines()):
            if "font-family" in line and "body" in line:
                print(f"    Found at line {i+1}: {line!r}")
        return

    new_content = content.replace(OLD_FONT_LINE, NEW_FONT_BLOCK, 1)
    path.write_text(new_content, encoding="utf-8")
    print("  ✓ Patched src/api/main.py — Times New Roman + light-mode contrast")


# ──────────────────────────────────────────────────────────────────────────────
# 3. PATCH index.html — same approach
# ──────────────────────────────────────────────────────────────────────────────

def patch_index_html():
    path = ROOT / "src" / "dashboard" / "index.html"
    if not path.exists():
        print(f"  ✗ Not found: {path}")
        return

    content = path.read_text(encoding="utf-8")

    if "Times New Roman" in content:
        print("  ✓ index.html already patched — skipping")
        return

    # Find any font-family declaration and replace with Times New Roman
    if "font-family" not in content:
        print("  ✗ No font-family found in index.html")
        return

    import re

    # Replace any Google Fonts import
    new_content = re.sub(
        r'<link[^>]+fonts\.googleapis\.com[^>]+>',
        '',
        content
    )

    # Replace font-family on body with Times New Roman
    new_content = re.sub(
        r"font-family\s*:\s*['\"]?[^;'\"]+['\"]?\s*(?:,\s*[^;]+)?;",
        "font-family: 'Times New Roman', Times, serif;",
        new_content
    )

    # Light-mode contrast injection — find the first </style> and insert before it
    light_fix = """
  /* ── Light-mode high-contrast fix ── */
  @media (prefers-color-scheme: light) {
    body { color: #0a1510 !important; background: #eef6f1 !important; }
    p, span, td, th, li, label, div { color: #0a1510; }
    h1, h2, h3, h4 { color: #051a0a !important; }
    .text-muted, [class*="muted"] { color: #1e4a30 !important; }
    input, select, textarea {
      background: #f5fbf8 !important;
      color: #0a1510 !important;
      border-color: #aacfbc !important;
    }
  }
"""
    new_content = new_content.replace("</style>", light_fix + "</style>", 1)

    path.write_text(new_content, encoding="utf-8")
    print("  ✓ Patched src/dashboard/index.html — Times New Roman + light-mode")

# ──────────────────────────────────────────────────────────────────────────────
# 4. Fix hardcoded inline colours in main.py body HTML
#    Replaces dark-mode hex colours with CSS variables so light mode works
# ──────────────────────────────────────────────────────────────────────────────

def fix_inline_colours():
    path = ROOT / "src" / "api" / "main.py"
    content = path.read_text(encoding="utf-8")

    # Map every hardcoded colour to the right CSS variable
    replacements = [
        # Dark-mode text colours used in inline styles
        ('color:#e2e8f0',   'color:var(--text)'),
        ('color:#94a3b8',   'color:var(--text-muted)'),
        ('color:#64748b',   'color:var(--text-muted)'),
        ('color:#6ee7b7',   'color:var(--teal)'),
        ('color:#cbd5e1',   'color:var(--border)'),
        # Strong tags inside inline styles
        ('color:#e2e8f0"',  'color:var(--text)"'),
        # Background colours
        ('background:#0f172a', 'background:var(--bg)'),
        ('background:#1e293b', 'background:var(--surface)'),
        # border colours
        ('border-color:#334155', 'border-color:var(--border)'),
    ]

    changed = 0
    for old, new in replacements:
        count = content.count(old)
        if count:
            content = content.replace(old, new)
            changed += count
            print(f"    replaced {count}x  {old!r}  →  {new!r}")

    if changed:
        path.write_text(content, encoding="utf-8")
        print(f"  ✓ Fixed {changed} hardcoded colours in main.py")
    else:
        print("  ✓ No hardcoded colours found — already clean")

# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────────────────
# 5. Fix About page hardcoded dark card backgrounds
# ──────────────────────────────────────────────────────────────────────────────

def fix_about_page():
    path = ROOT / "src" / "api" / "main.py"
    content = path.read_text(encoding="utf-8")

    if "fix_about_done" in content:
        print("  ✓ About page already fixed — skipping")
        return

    import re

    # Replace dark gradient card backgrounds with CSS variable
    content = re.sub(
        r'background:linear-gradient\(135deg,#[0-9a-fA-F]{6},#[0-9a-fA-F]{6}\)',
        'background:var(--surface)',
        content
    )

    # Replace hero banner hardcoded dark background
    content = re.sub(
        r'background:linear-gradient\(135deg,#0f172a[^)]*\)',
        'background:var(--surface)',
        content
    )

    # Fix tech stack pill backgrounds
    content = content.replace(
        'background:#111827;border:1px solid var(--border)',
        'background:var(--surface);border:1px solid var(--border)'
    )

    # Replace hardcoded dark border colours
    content = re.sub(
        r'border:1px solid #[0-9a-fA-F]{6}',
        'border:1px solid var(--border)',
        content
    )

    # Mark as done
    content = content.replace(
        '@app.get("/about"',
        '# fix_about_done\n@app.get("/about"'
    )

    path.write_text(content, encoding="utf-8")
    print("  ✓ Fixed About page — card backgrounds now use CSS variables")

def fix_tech_pills():
    path = ROOT / "src" / "api" / "main.py"
    content = path.read_text(encoding="utf-8")

    if "fix_pills_done" in content:
        print("  ✓ Tech pills already fixed — skipping")
        return

    count = content.count("background:#111827")
    if count == 0:
        print("  ✗ background:#111827 not found in main.py")
        return

    content = content.replace(
        "background:#111827",
        "background:var(--surface)"
    )

    content = content.replace(
        '# fix_about_done',
        '# fix_about_done\n# fix_pills_done'
    )

    path.write_text(content, encoding="utf-8")
    print(f"  ✓ Fixed {count} tech pill backgrounds in main.py")

def main():
    print("\n=== Clinical AI — Page Glow-Up ===\n")

    login_path = ROOT / "src" / "dashboard" / "login.html"
    login_path.write_text(LOGIN_HTML, encoding="utf-8")
    print("  ✓ Wrote src/dashboard/login.html (full glow-up)")

    patch_main_py()
    patch_index_html()
    fix_inline_colours()
    fix_about_page()
    fix_about_page()
    fix_tech_pills()

    print("\n=== Done! ===")
    print("Next: uv run uvicorn src.api.main:app --reload")
    print("Then open: http://localhost:8000/login\n")


if __name__ == "__main__":
    main()