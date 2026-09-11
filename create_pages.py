from pathlib import Path

NAV = """<nav>
  <div class="nav-logo"><div class="dot"></div>Clinical AI</div>
  <div class="nav-links">
    <a href="/dashboard">Home</a>
    <a href="/about">About</a>
    <a href="/demo">Live Demo</a>
    <a href="/federated">Federated Learning</a>
    <a href="/audit-page">Audit Log</a>
  </div>
  <div class="nav-right">
    <button class="theme-btn" id="theme-btn" onclick="toggleTheme()">☀ Light</button>
    <a href="/logout" class="nav-logout">Logout</a>
  </div>
</nav>"""

BASE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
:root { --bg:#0a0d14; --card:#111827; --card2:#1a2035; --border:#1f2937; --text:#e2e8f0; --muted:#64748b; --cyan:#06b6d4; --green:#22c55e; }
body.light { --bg:#f0f4f8; --card:#ffffff; --card2:#f8fafc; --border:#e2e8f0; --text:#0f172a; --muted:#475569; }
body { font-family:"DM Sans",sans-serif; background:var(--bg); color:var(--text); min-height:100vh; }
nav { position:fixed; top:0; width:100%; background:var(--card); border-bottom:1px solid var(--border); z-index:100; padding:0 32px; display:flex; align-items:center; justify-content:space-between; height:56px; }
.nav-logo { font-weight:700; font-size:0.95rem; color:var(--cyan); display:flex; align-items:center; gap:8px; }
.dot { width:8px; height:8px; border-radius:50%; background:var(--green); animation:pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1}50%{opacity:0.3} }
.nav-links { display:flex; gap:24px; }
.nav-links a { color:var(--muted); text-decoration:none; font-size:0.88rem; font-weight:500; transition:color 0.2s; }
.nav-links a:hover { color:var(--text); }
.nav-right { display:flex; align-items:center; gap:12px; }
.theme-btn { background:var(--card2); border:1px solid var(--border); color:var(--text); padding:5px 14px; border-radius:999px; cursor:pointer; font-size:0.8rem; font-weight:600; font-family:"DM Sans",sans-serif; transition:all 0.2s; }
.theme-btn:hover { border-color:var(--cyan); color:var(--cyan); }
.nav-logout { color:var(--muted); text-decoration:none; font-size:0.85rem; border:1px solid var(--border); padding:4px 12px; border-radius:6px; transition:all 0.2s; }
.nav-logout:hover { color:#ef4444; border-color:#ef4444; }
main { max-width:1100px; margin:0 auto; padding:88px 32px 60px; }
.page-label { font-size:0.72rem; color:var(--cyan); text-transform:uppercase; letter-spacing:2px; margin-bottom:8px; }
.page-title { font-size:2rem; font-weight:800; margin-bottom:12px; }
.page-sub { color:var(--muted); font-size:1rem; margin-bottom:48px; }
.card { background:var(--card); border:1px solid var(--border); border-radius:12px; padding:28px; margin-bottom:20px; }
.card h3 { font-size:1.1rem; font-weight:700; margin-bottom:12px; }
.card p, .card li { font-size:0.9rem; color:var(--muted); line-height:1.7; }
.card ul { padding-left:18px; }
.grid-3 { display:grid; grid-template-columns:repeat(3,1fr); gap:20px; margin-bottom:32px; }
@media(max-width:768px){.grid-3{grid-template-columns:1fr;}}
.layer-tag { font-size:0.7rem; color:var(--cyan); text-transform:uppercase; letter-spacing:1px; margin-bottom:8px; font-weight:700; }
.tech-grid { display:flex; flex-wrap:wrap; gap:10px; margin-top:24px; }
.tech-badge { background:var(--card2); border:1px solid var(--border); border-radius:8px; padding:8px 16px; font-size:0.85rem; font-weight:600; }
.tech-badge span { color:var(--cyan); }
.stat-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:32px; }
@media(max-width:768px){.stat-grid{grid-template-columns:repeat(2,1fr);}}
.stat-card { background:var(--card); border:1px solid var(--border); border-radius:12px; padding:20px; text-align:center; }
.stat-num { font-size:2rem; font-weight:800; color:var(--cyan); }
.stat-label { font-size:0.75rem; color:var(--muted); text-transform:uppercase; letter-spacing:1px; margin-top:4px; }
.phase-item { display:flex; gap:16px; padding:16px 0; border-bottom:1px solid var(--border); }
.phase-item:last-child { border-bottom:none; }
.phase-num { width:36px; height:36px; border-radius:50%; background:var(--cyan); color:#000; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:0.85rem; flex-shrink:0; }
.phase-name { font-weight:700; margin-bottom:4px; }
.phase-desc { font-size:0.85rem; color:var(--muted); }
.audit-table { width:100%; border-collapse:collapse; font-size:0.85rem; }
.audit-table th { text-align:left; padding:10px 14px; border-bottom:2px solid var(--border); color:var(--cyan); font-size:0.72rem; text-transform:uppercase; letter-spacing:1px; }
.audit-table td { padding:10px 14px; border-bottom:1px solid var(--border); color:var(--muted); }
.badge { display:inline-block; padding:2px 10px; border-radius:999px; font-size:0.72rem; font-weight:700; }
.badge.CRITICAL { background:rgba(239,68,68,0.1); color:#ef4444; }
.badge.HIGH { background:rgba(249,115,22,0.1); color:#f97316; }
.badge.MEDIUM,.badge.MODERATE { background:rgba(251,191,36,0.1); color:#fbbf24; }
.badge.LOW { background:rgba(34,197,94,0.1); color:#22c55e; }
"""

THEME_JS = """
<script>
function toggleTheme(){
  var b=document.body, btn=document.getElementById("theme-btn");
  if(b.classList.contains("light")){b.classList.remove("light");localStorage.setItem("theme","dark");btn.textContent="☀ Light";}
  else{b.classList.add("light");localStorage.setItem("theme","light");btn.textContent="🌙 Dark";}
}
(function(){
  if(localStorage.getItem("theme")==="light"){document.body.classList.add("light");var btn=document.getElementById("theme-btn");if(btn)btn.textContent="🌙 Dark";}
})();
</script>
"""

def page(title, body):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title} | Clinical AI</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>{BASE_CSS}</style>
</head>
<body>
{NAV}
<main>{body}</main>
{THEME_JS}
</body>
</html>"""

# ── ABOUT PAGE ──────────────────────────────────────────────────────────────
about_body = """
<div class="page-label">Research Project 2026</div>
<div class="page-title">About This Project</div>
<div class="page-sub">AI for Real-Time Clinical Decision Support in Under-Resourced Hospitals — a Virtual Junior Doctor for sepsis detection.</div>

<div class="stat-grid">
  <div class="stat-card"><div class="stat-num">6</div><div class="stat-label">Phases Completed</div></div>
  <div class="stat-card"><div class="stat-num">0.965</div><div class="stat-label">Federated AUC</div></div>
  <div class="stat-card"><div class="stat-num">3</div><div class="stat-label">Hospitals Simulated</div></div>
  <div class="stat-card"><div class="stat-num">DISHA</div><div class="stat-label">Compliance Ready</div></div>
</div>

<div class="card" style="margin-bottom:20px">
  <div class="page-label">System Design</div>
  <h3 style="font-size:1.4rem;margin-bottom:8px">3-Layer Architecture</h3>
  <p style="margin-bottom:24px">Every patient interaction flows through three layers — from raw hospital data to actionable clinical treatment plan.</p>
  <div class="grid-3">
    <div class="card" style="margin-bottom:0">
      <div class="layer-tag">Layer 1</div>
      <h3>Data Ingestion</h3>
      <ul><li>FHIR R4 patient bundles</li><li>LOINC-coded vitals and labs</li><li>Clinical notes (free text)</li><li>Completeness validation</li></ul>
    </div>
    <div class="card" style="margin-bottom:0">
      <div class="layer-tag">Layer 2</div>
      <h3>AI Core</h3>
      <ul><li>XGBoost sepsis model + SHAP</li><li>scispaCy NLP (NER + negation)</li><li>Multimodal fusion engine</li><li>LangGraph agent orchestration</li></ul>
    </div>
    <div class="card" style="margin-bottom:0">
      <div class="layer-tag">Layer 3</div>
      <h3>Clinical Output</h3>
      <ul><li>Risk level + score + drivers</li><li>Treatment plan (immediate/urgent/routine)</li><li>Escalation triggers</li><li>HITL mandatory review flag</li></ul>
    </div>
  </div>
</div>

<div class="card">
  <div class="page-label">Tech Stack</div>
  <h3 style="margin-bottom:16px">Technologies Used</h3>
  <div class="tech-grid">
    <div class="tech-badge"><span>FastAPI</span> REST API</div>
    <div class="tech-badge"><span>LangGraph</span> Agent Orchestration</div>
    <div class="tech-badge"><span>XGBoost</span> Sepsis Model</div>
    <div class="tech-badge"><span>scispaCy</span> Clinical NLP</div>
    <div class="tech-badge"><span>Flower</span> Federated Learning</div>
    <div class="tech-badge"><span>FHIR R4</span> Healthcare Standard</div>
    <div class="tech-badge"><span>SHAP</span> Explainable AI</div>
    <div class="tech-badge"><span>DISHA/HIPAA</span> Compliance</div>
  </div>
</div>

<div class="card" style="margin-top:20px">
  <div class="page-label">Project Phases</div>
  <h3 style="margin-bottom:16px">Development Timeline</h3>
  <div class="phase-item"><div class="phase-num">0</div><div><div class="phase-name">Project Setup</div><div class="phase-desc">Repository, environment, FHIR schema design</div></div></div>
  <div class="phase-item"><div class="phase-num">1</div><div><div class="phase-name">FHIR Data Ingestion</div><div class="phase-desc">Parse FHIR R4 bundles, extract vitals and lab values</div></div></div>
  <div class="phase-item"><div class="phase-num">2</div><div><div class="phase-name">XGBoost Sepsis Model</div><div class="phase-desc">Train on synthetic data, SHAP explainability, calibration</div></div></div>
  <div class="phase-item"><div class="phase-num">3</div><div><div class="phase-name">scispaCy NLP</div><div class="phase-desc">Named entity recognition on clinical notes, negation detection</div></div></div>
  <div class="phase-item"><div class="phase-num">4</div><div><div class="phase-name">Multimodal Fusion</div><div class="phase-desc">Combine vitals model + NLP findings into unified risk level</div></div></div>
  <div class="phase-item"><div class="phase-num">5</div><div><div class="phase-name">FastAPI + LangGraph Agent</div><div class="phase-desc">REST API, LangGraph orchestration, HITL review flags</div></div></div>
  <div class="phase-item"><div class="phase-num">6</div><div><div class="phase-name">Federated Learning + Treatment Engine</div><div class="phase-desc">Flower FL across 3 hospitals, Surviving Sepsis Campaign 2021 treatment plans, audit logging</div></div></div>
</div>
"""

# ── FEDERATED PAGE ──────────────────────────────────────────────────────────
federated_body = """
<div class="page-label">Privacy-Preserving AI</div>
<div class="page-title">Federated Learning</div>
<div class="page-sub">Train a shared sepsis model across hospitals without any patient data leaving the hospital. Only model weights are shared.</div>

<div class="stat-grid">
  <div class="stat-card"><div class="stat-num">3</div><div class="stat-label">Hospitals Simulated</div></div>
  <div class="stat-card"><div class="stat-num">0.965</div><div class="stat-label">Global AUC</div></div>
  <div class="stat-card"><div class="stat-num">5</div><div class="stat-label">FL Rounds</div></div>
  <div class="stat-card"><div class="stat-num">0%</div><div class="stat-label">Patient Data Shared</div></div>
</div>

<div class="card">
  <h3>How It Works</h3>
  <p style="margin-bottom:16px">Traditional ML requires centralising patient data — illegal under DISHA and HIPAA. Federated Learning solves this:</p>
  <div class="phase-item"><div class="phase-num">1</div><div><div class="phase-name">Local Training</div><div class="phase-desc">Each hospital trains XGBoost on its own patients. Data never leaves the hospital.</div></div></div>
  <div class="phase-item"><div class="phase-num">2</div><div><div class="phase-name">Weight Upload</div><div class="phase-desc">Only model weights (numbers, not patient records) are sent to the central server.</div></div></div>
  <div class="phase-item"><div class="phase-num">3</div><div><div class="phase-name">Federated Averaging</div><div class="phase-desc">The server averages weights from all hospitals to build a stronger global model.</div></div></div>
  <div class="phase-item"><div class="phase-num">4</div><div><div class="phase-name">Global Model Distribution</div><div class="phase-desc">The improved global model is sent back to all hospitals for the next round.</div></div></div>
</div>

<div class="grid-3" style="margin-top:20px">
  <div class="card" style="margin-bottom:0">
    <div class="layer-tag">Hospital A</div>
    <h3>Urban Tertiary</h3>
    <p>500 patients, high data quality, AUC 0.94</p>
  </div>
  <div class="card" style="margin-bottom:0">
    <div class="layer-tag">Hospital B</div>
    <h3>Tier-2 District</h3>
    <p>300 patients, partial labs, AUC 0.91</p>
  </div>
  <div class="card" style="margin-bottom:0">
    <div class="layer-tag">Hospital C</div>
    <h3>Rural PHC</h3>
    <p>150 patients, vitals only, AUC 0.88</p>
  </div>
</div>

<div class="card" style="margin-top:20px">
  <h3>Why This Matters for India</h3>
  <p style="margin-bottom:12px">India's DISHA Act prohibits centralising patient health records. Federated Learning is the only legally compliant way to train a shared AI model across Indian hospitals.</p>
  <p>Our implementation uses <strong style="color:var(--cyan)">Flower (flwr)</strong> — the leading open-source federated learning framework — with FedAvg aggregation strategy.</p>
</div>
"""

# ── AUDIT PAGE ──────────────────────────────────────────────────────────────
audit_body = """
<div class="page-label">Compliance & Safety</div>
<div class="page-title">Audit Log</div>
<div class="page-sub">Every AI prediction is logged for clinical accountability, regulatory compliance, and model monitoring.</div>

<div class="card" style="margin-bottom:20px">
  <h3 style="margin-bottom:16px">Live Audit Records</h3>
  <div id="audit-loading" style="color:var(--muted);padding:20px 0">Loading audit records...</div>
  <table class="audit-table" id="audit-table" style="display:none">
    <thead><tr><th>Time</th><th>Patient ID</th><th>Risk Level</th><th>Risk Score</th><th>HITL</th><th>Source</th></tr></thead>
    <tbody id="audit-tbody"></tbody>
  </table>
</div>

<div class="card">
  <h3>Why We Audit Every Prediction</h3>
  <p style="margin-bottom:12px">Clinical AI systems must be auditable. Every prediction the system makes is recorded with:</p>
  <ul style="padding-left:18px;line-height:2">
    <li>Patient identifier and timestamp</li>
    <li>Risk level and confidence score</li>
    <li>Whether human review was flagged (HITL)</li>
    <li>Model version used</li>
    <li>Data completeness at time of prediction</li>
  </ul>
  <p style="margin-top:12px">This satisfies <strong style="color:var(--cyan)">DISHA</strong> and <strong style="color:var(--cyan)">HIPAA</strong> audit trail requirements.</p>
</div>

<script>
fetch("/audit?n=50")
  .then(function(r){ return r.json(); })
  .then(function(data){
    var tbody = document.getElementById("audit-tbody");
    var records = data.records || [];
    if(records.length === 0){
      document.getElementById("audit-loading").textContent = "No audit records yet. Run the Live Demo to generate some.";
      return;
    }
    records.forEach(function(r){
      var ts = r.timestamp ? new Date(r.timestamp).toLocaleTimeString() : "--";
      var row = "<tr>" +
        "<td>" + ts + "</td>" +
        "<td style='color:var(--text)'>" + (r.patient_id||"--") + "</td>" +
        "<td><span class='badge " + (r.risk_level||"") + "'>" + (r.risk_level||"--") + "</span></td>" +
        "<td>" + (r.risk_score ? (r.risk_score*100).toFixed(1)+"%" : "--") + "</td>" +
        "<td style='color:" + (r.hitl_required ? "#f97316" : "#22c55e") + "'>" + (r.hitl_required ? "YES" : "NO") + "</td>" +
        "<td>" + (r.source||"--") + "</td>" +
        "</tr>";
      tbody.innerHTML += row;
    });
    document.getElementById("audit-loading").style.display = "none";
    document.getElementById("audit-table").style.display = "table";
  })
  .catch(function(){ document.getElementById("audit-loading").textContent = "Could not load audit records."; });
</script>
"""

Path("src/dashboard/about.html").write_text(page("About", about_body), encoding="utf-8")
print("about.html written OK")

Path("src/dashboard/federated.html").write_text(page("Federated Learning", federated_body), encoding="utf-8")
print("federated.html written OK")

Path("src/dashboard/audit_page.html").write_text(page("Audit Log", audit_body), encoding="utf-8")
print("audit_page.html written OK")