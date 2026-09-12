with open("src/api/main.py", "r", encoding="utf-8") as f:
    content = f.read()

# ── FIX 1: Welcome message ────────────────────────────────────────────────────
old_welcome = "        <h2 style=\"color:#e2e8f0;font-size:1.4rem\">Welcome, {doctor['full_name']}</h2>"
new_welcome = "        <h2 style=\"color:#e2e8f0;font-size:1.4rem\">🩺 Welcome, Dr. Clinical AI</h2>"

if old_welcome in content:
    content = content.replace(old_welcome, new_welcome)
    print("✅ FIX 1 done: Welcome message updated.")
else:
    print("⚠️  FIX 1 SKIPPED: Welcome text not found — may already be fixed.")

# ── FIX 2: About page body ────────────────────────────────────────────────────
# Find the about route body and replace it entirely
OLD_ABOUT_START = '    body = """\n    <div class="card">\n      <h2>🏥 About ClinicalAI</h2>'
OLD_ABOUT_END   = '    return html(_base("About", body, doctor["full_name"]))'

NEW_ABOUT_BODY = '''    body = """
    <div style="background:linear-gradient(135deg,#0f172a 0%,#0f2820 100%);border:1px solid #1f4035;border-radius:16px;padding:2.5rem;margin-bottom:2rem;position:relative;overflow:hidden">
      <div style="position:absolute;top:-40px;right:-40px;width:180px;height:180px;background:radial-gradient(circle,rgba(16,185,129,0.12) 0%,transparent 70%);pointer-events:none"></div>
      <div style="font-size:0.72rem;color:#6ee7b7;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:12px">🎓 Research Project 2026 — MHSSCE</div>
      <h1 style="font-size:1.9rem;font-weight:800;color:#e2e8f0;line-height:1.25;margin-bottom:14px">
        🏥 AI for Real-Time Clinical<br>Decision Support<br>
        <span style="color:#6ee7b7">in Under-Resourced Hospitals</span>
      </h1>
      <p style="color:#94a3b8;font-size:1rem;line-height:1.75;max-width:680px">
        A <strong style="color:#e2e8f0">Virtual Junior Doctor</strong> that detects sepsis in real time,
        explains every decision, and tells the attending doctor exactly what to do next —
        built for Tier-2 and Tier-3 hospitals in India where specialist doctors are scarce
        and early detection saves lives. 🩺
      </p>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:14px;margin-bottom:2rem">
      <div style="background:linear-gradient(135deg,#111827,#0f1f35);border:1px solid #1e3a5f;border-radius:14px;padding:1.5rem;text-align:center">
        <div style="font-size:2.2rem;font-weight:800;color:#6ee7b7">✅ 6</div>
        <div style="font-size:0.72rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-top:6px;font-weight:700">Phases Completed</div>
      </div>
      <div style="background:linear-gradient(135deg,#111827,#1a1035);border:1px solid #2d1b5e;border-radius:14px;padding:1.5rem;text-align:center">
        <div style="font-size:2.2rem;font-weight:800;color:#8b5cf6">🎯 0.965</div>
        <div style="font-size:0.72rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-top:6px;font-weight:700">Federated AUC</div>
      </div>
      <div style="background:linear-gradient(135deg,#111827,#1f1506);border:1px solid #3d2a07;border-radius:14px;padding:1.5rem;text-align:center">
        <div style="font-size:2.2rem;font-weight:800;color:#f97316">🏥 3</div>
        <div style="font-size:0.72rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-top:6px;font-weight:700">Hospitals Simulated</div>
      </div>
      <div style="background:linear-gradient(135deg,#111827,#0f2820);border:1px solid #14532d;border-radius:14px;padding:1.5rem;text-align:center">
        <div style="font-size:2.2rem;font-weight:800;color:#22c55e">🛡 DISHA</div>
        <div style="font-size:0.72rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-top:6px;font-weight:700">Compliance Ready</div>
      </div>
    </div>

    <div style="margin-bottom:2rem">
      <div style="font-size:0.72rem;color:#6ee7b7;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:8px">🏗 System Design</div>
      <h2 style="font-size:1.5rem;font-weight:800;color:#e2e8f0;margin-bottom:8px">3-Layer Architecture</h2>
      <p style="color:#64748b;font-size:0.95rem;margin-bottom:1.5rem">Every patient interaction flows through three layers — from raw hospital data to an actionable clinical treatment plan.</p>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px">
        <div style="background:linear-gradient(135deg,#111827,#0f1f35);border:1px solid #1e3a5f;border-radius:14px;padding:1.5rem">
          <div style="font-size:0.7rem;color:#6ee7b7;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin-bottom:8px">Layer 1</div>
          <div style="font-size:2rem;margin-bottom:10px">📥</div>
          <div style="font-weight:800;color:#e2e8f0;margin-bottom:12px;font-size:1rem">Data Ingestion</div>
          <ul style="list-style:none;padding:0">
            <li style="font-size:0.84rem;color:#64748b;padding:4px 0 4px 16px;position:relative">
              <span style="position:absolute;left:0;color:#6ee7b7;font-weight:700">→</span>FHIR R4 patient bundles</li>
            <li style="font-size:0.84rem;color:#64748b;padding:4px 0 4px 16px;position:relative">
              <span style="position:absolute;left:0;color:#6ee7b7;font-weight:700">→</span>LOINC-coded vitals and labs</li>
            <li style="font-size:0.84rem;color:#64748b;padding:4px 0 4px 16px;position:relative">
              <span style="position:absolute;left:0;color:#6ee7b7;font-weight:700">→</span>Clinical notes (free text)</li>
            <li style="font-size:0.84rem;color:#64748b;padding:4px 0 4px 16px;position:relative">
              <span style="position:absolute;left:0;color:#6ee7b7;font-weight:700">→</span>Completeness validation</li>
          </ul>
        </div>
        <div style="background:linear-gradient(135deg,#111827,#1a1035);border:1px solid #2d1b5e;border-radius:14px;padding:1.5rem">
          <div style="font-size:0.7rem;color:#8b5cf6;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin-bottom:8px">Layer 2</div>
          <div style="font-size:2rem;margin-bottom:10px">🤖</div>
          <div style="font-weight:800;color:#e2e8f0;margin-bottom:12px;font-size:1rem">AI Core</div>
          <ul style="list-style:none;padding:0">
            <li style="font-size:0.84rem;color:#64748b;padding:4px 0 4px 16px;position:relative">
              <span style="position:absolute;left:0;color:#8b5cf6;font-weight:700">→</span>XGBoost sepsis model + SHAP</li>
            <li style="font-size:0.84rem;color:#64748b;padding:4px 0 4px 16px;position:relative">
              <span style="position:absolute;left:0;color:#8b5cf6;font-weight:700">→</span>scispaCy NLP (NER + negation)</li>
            <li style="font-size:0.84rem;color:#64748b;padding:4px 0 4px 16px;position:relative">
              <span style="position:absolute;left:0;color:#8b5cf6;font-weight:700">→</span>Multimodal fusion engine</li>
            <li style="font-size:0.84rem;color:#64748b;padding:4px 0 4px 16px;position:relative">
              <span style="position:absolute;left:0;color:#8b5cf6;font-weight:700">→</span>LangGraph agent orchestration</li>
          </ul>
        </div>
        <div style="background:linear-gradient(135deg,#111827,#0f2820);border:1px solid #14532d;border-radius:14px;padding:1.5rem">
          <div style="font-size:0.7rem;color:#22c55e;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin-bottom:8px">Layer 3</div>
          <div style="font-size:2rem;margin-bottom:10px">📊</div>
          <div style="font-weight:800;color:#e2e8f0;margin-bottom:12px;font-size:1rem">Clinical Output</div>
          <ul style="list-style:none;padding:0">
            <li style="font-size:0.84rem;color:#64748b;padding:4px 0 4px 16px;position:relative">
              <span style="position:absolute;left:0;color:#22c55e;font-weight:700">→</span>Risk level + score + drivers</li>
            <li style="font-size:0.84rem;color:#64748b;padding:4px 0 4px 16px;position:relative">
              <span style="position:absolute;left:0;color:#22c55e;font-weight:700">→</span>Treatment plan (immediate/urgent/routine)</li>
            <li style="font-size:0.84rem;color:#64748b;padding:4px 0 4px 16px;position:relative">
              <span style="position:absolute;left:0;color:#22c55e;font-weight:700">→</span>Escalation triggers</li>
            <li style="font-size:0.84rem;color:#64748b;padding:4px 0 4px 16px;position:relative">
              <span style="position:absolute;left:0;color:#22c55e;font-weight:700">→</span>HITL mandatory review flag</li>
          </ul>
        </div>
      </div>
    </div>

    <div style="margin-bottom:2rem">
      <div style="font-size:0.72rem;color:#6ee7b7;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:16px">⚙️ Tech Stack</div>
      <div style="display:flex;flex-wrap:wrap;gap:10px">
        <div style="background:#111827;border:1px solid #1f2937;border-radius:10px;padding:10px 16px;font-size:0.84rem;color:#64748b;display:flex;align-items:center;gap:8px"><span style="font-size:1.1rem">⚡</span><strong style="color:#e2e8f0">FastAPI</strong> REST API</div>
        <div style="background:#111827;border:1px solid #1f2937;border-radius:10px;padding:10px 16px;font-size:0.84rem;color:#64748b;display:flex;align-items:center;gap:8px"><span style="font-size:1.1rem">🔗</span><strong style="color:#e2e8f0">LangGraph</strong> Agent Orchestration</div>
        <div style="background:#111827;border:1px solid #1f2937;border-radius:10px;padding:10px 16px;font-size:0.84rem;color:#64748b;display:flex;align-items:center;gap:8px"><span style="font-size:1.1rem">🌲</span><strong style="color:#e2e8f0">XGBoost</strong> Sepsis Model</div>
        <div style="background:#111827;border:1px solid #1f2937;border-radius:10px;padding:10px 16px;font-size:0.84rem;color:#64748b;display:flex;align-items:center;gap:8px"><span style="font-size:1.1rem">🧠</span><strong style="color:#e2e8f0">scispaCy</strong> Clinical NLP</div>
        <div style="background:#111827;border:1px solid #1f2937;border-radius:10px;padding:10px 16px;font-size:0.84rem;color:#64748b;display:flex;align-items:center;gap:8px"><span style="font-size:1.1rem">🌸</span><strong style="color:#e2e8f0">Flower</strong> Federated Learning</div>
        <div style="background:#111827;border:1px solid #1f2937;border-radius:10px;padding:10px 16px;font-size:0.84rem;color:#64748b;display:flex;align-items:center;gap:8px"><span style="font-size:1.1rem">🏥</span><strong style="color:#e2e8f0">FHIR R4</strong> Healthcare Standard</div>
        <div style="background:#111827;border:1px solid #1f2937;border-radius:10px;padding:10px 16px;font-size:0.84rem;color:#64748b;display:flex;align-items:center;gap:8px"><span style="font-size:1.1rem">🔍</span><strong style="color:#e2e8f0">SHAP</strong> Explainable AI</div>
        <div style="background:#111827;border:1px solid #1f2937;border-radius:10px;padding:10px 16px;font-size:0.84rem;color:#64748b;display:flex;align-items:center;gap:8px"><span style="font-size:1.1rem">🛡</span><strong style="color:#e2e8f0">DISHA/HIPAA</strong> Compliance</div>
      </div>
    </div>

    <div style="background:linear-gradient(135deg,#111827,#0f2820);border:1px solid #14532d;border-radius:14px;padding:1.75rem;margin-bottom:2rem">
      <div style="font-size:0.72rem;color:#22c55e;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:14px">👥 Project Team</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
        <div style="background:rgba(0,0,0,0.25);border:1px solid #1f2937;border-radius:10px;padding:1rem;display:flex;align-items:center;gap:14px">
          <div style="font-size:2rem">👩‍💻</div>
          <div>
            <div style="font-weight:700;color:#e2e8f0;font-size:0.95rem">Krathika</div>
            <div style="color:#6ee7b7;font-size:0.78rem;font-weight:600">Lead Developer — AI &amp; Backend</div>
            <div style="color:#475569;font-size:0.75rem;margin-top:2px">M.H. Saboo Siddik College of Engineering</div>
          </div>
        </div>
        <div style="background:rgba(0,0,0,0.25);border:1px solid #1f2937;border-radius:10px;padding:1rem;display:flex;align-items:center;gap:14px">
          <div style="font-size:2rem">👩‍💻</div>
          <div>
            <div style="font-weight:700;color:#e2e8f0;font-size:0.95rem">Divya</div>
            <div style="color:#8b5cf6;font-size:0.78rem;font-weight:600">Developer — NLP &amp; Data Pipeline</div>
            <div style="color:#475569;font-size:0.75rem;margin-top:2px">M.H. Saboo Siddik College of Engineering</div>
          </div>
        </div>
        <div style="background:rgba(0,0,0,0.25);border:1px solid #1f2937;border-radius:10px;padding:1rem;display:flex;align-items:center;gap:14px">
          <div style="font-size:2rem">👩‍💻</div>
          <div>
            <div style="font-weight:700;color:#e2e8f0;font-size:0.95rem">Grishma</div>
            <div style="color:#f97316;font-size:0.78rem;font-weight:600">Developer — Frontend &amp; Integration</div>
            <div style="color:#475569;font-size:0.75rem;margin-top:2px">M.H. Saboo Siddik College of Engineering</div>
          </div>
        </div>
        <div style="background:rgba(0,0,0,0.25);border:1px solid #1f2937;border-radius:10px;padding:1rem;display:flex;align-items:center;gap:14px">
          <div style="font-size:2rem">👨‍🏫</div>
          <div>
            <div style="font-weight:700;color:#e2e8f0;font-size:0.95rem">Mr. Suraj Hindurao Chopade</div>
            <div style="color:#fbbf24;font-size:0.78rem;font-weight:600">Project Guide</div>
            <div style="color:#475569;font-size:0.75rem;margin-top:2px">M.H. Saboo Siddik College of Engineering</div>
          </div>
        </div>
      </div>
    </div>

    <div style="background:rgba(6,182,212,0.06);border:1px solid rgba(6,182,212,0.25);border-radius:14px;padding:1.25rem 1.5rem;display:flex;align-items:center;gap:16px">
      <div style="font-size:2rem">🔒</div>
      <div>
        <div style="font-weight:700;color:#e2e8f0;margin-bottom:4px">Privacy &amp; Compliance</div>
        <div style="color:#64748b;font-size:0.87rem">
          Patient data never leaves the hospital &nbsp;·&nbsp;
          Only gradient weights transmitted &nbsp;·&nbsp;
          ✅ Compliant with India DISHA and HIPAA
        </div>
      </div>
    </div>"""
    return html(_base("About", body, doctor["full_name"]))'''

# Find old about body start
idx_start = content.find('    body = """\n    <div class="card">\n      <h2>🏥 About ClinicalAI</h2>')
idx_end   = content.find('    return html(_base("About", body, doctor["full_name"]))')

if idx_start == -1:
    print("⚠️  FIX 2 SKIPPED: About body start not found.")
elif idx_end == -1:
    print("⚠️  FIX 2 SKIPPED: About return line not found.")
else:
    end_of_return = idx_end + len('    return html(_base("About", body, doctor["full_name"]))')
    content = content[:idx_start] + NEW_ABOUT_BODY + content[end_of_return:]
    print("✅ FIX 2 done: About page redesigned.")

with open("src/api/main.py", "w", encoding="utf-8") as f:
    f.write(content)

print("\n✅ All done! Restart uvicorn and check /dashboard and /about")
