with open("src/api/main.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find start and end of the old PDF endpoint (0-indexed: line 1263 = index 1262)
start = 1262
# Find the end by looking for next @app. route after start
end = start + 1
while end < len(lines):
    if lines[end].startswith("@app.") and end > start + 5:
        break
    end += 1

new_pdf = '''@app.get("/report/{analysis_id}")
async def download_report(analysis_id: int, session: str | None = Cookie(default=None)):
    """Generate and stream a professional PDF report."""
    import io
    from fastapi.responses import StreamingResponse
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    doctor = require_doctor(session)
    from src.database.db import get_connection
    conn = get_connection()
    row = conn.execute("SELECT * FROM analyses WHERE id=?", (analysis_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Analysis not found")

    row = dict(row)
    patient = get_patient(row["patient_id"])
    findings = json.loads(row["findings"])
    recs = json.loads(row["recommendations"])
    params = json.loads(row["parameters"])
    pct = int(row["risk_score"] * 100)
    disease = DISEASES.get(row["disease_id"], type("x", (), {"name": row["disease_id"], "icd10": "---"})())
    disease_name = disease.name
    icd10 = getattr(disease, "icd10", "---")
    risk_colors_map = {"CRITICAL": "#dc2626", "HIGH": "#ea580c", "MODERATE": "#2563eb", "LOW": "#16a34a"}
    risk_hex = risk_colors_map.get(row["risk_level"], "#2563eb")

    NORMAL_RANGES = {
        "heart_rate": (60, 100, "bpm"),
        "systolic_bp": (90, 140, "mmHg"),
        "diastolic_bp": (60, 90, "mmHg"),
        "temperature": (36.1, 38.0, "C"),
        "spo2": (95, 100, "%"),
        "respiratory_rate": (12, 20, "/min"),
        "troponin_i": (0, 0.04, "ng/mL"),
        "wbc": (4.5, 11.0, "x10/uL"),
        "creatinine": (0.6, 1.2, "mg/dL"),
        "sodium": (135, 145, "mEq/L"),
        "glucose": (70, 140, "mg/dL"),
        "bmi": (18.5, 24.9, "kg/m2"),
    }

    buf = io.BytesIO()
    W = 17.4 * cm
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=1.8*cm, rightMargin=1.8*cm,
                            topMargin=1.8*cm, bottomMargin=1.8*cm)
    story = []

    def ps(name, **kw):
        return ParagraphStyle(name, **kw)

    sec_s  = ps("sec", fontSize=10, fontName="Helvetica-Bold", textColor=colors.HexColor("#374151"), spaceBefore=10, spaceAfter=4)
    body_s = ps("b", fontSize=9, leading=14, textColor=colors.HexColor("#1f2937"), spaceAfter=4)

    # HEADER
    hdr_data = [[
        Paragraph("<b>ClinicalAI - Decision Support System</b>",
                  ps("hh", fontSize=14, fontName="Helvetica-Bold", textColor=colors.HexColor("#111827"))),
        Paragraph(f"<b>Report ID: {analysis_id}</b>",
                  ps("rid", fontSize=9, textColor=colors.HexColor("#6b7280"), alignment=2)),
    ]]
    ht = Table(hdr_data, colWidths=[W*0.7, W*0.3])
    ht.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("PADDING",(0,0),(-1,-1),0)]))
    story.append(ht)
    story.append(Paragraph(
        "AI-Assisted Medical Report | <b>Confidential</b>",
        ps("conf", fontSize=8, textColor=colors.HexColor("#6b7280"), spaceAfter=2)
    ))
    story.append(Paragraph(
        f"Generated: {datetime.now(UTC).strftime('%d %B %Y, %H:%M UTC')} | Doctor: {doctor['full_name']} | Hospital: {doctor.get('hospital','--')}",
        ps("sub", fontSize=9, textColor=colors.HexColor("#6b7280"), spaceAfter=4)
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#e5e7eb"), spaceAfter=8))

    # PATIENT INFO
    story.append(Paragraph("Patient Information", sec_s))
    pi = [
        ["Patient ID", row["patient_id"], "Full Name", patient["full_name"]],
        ["Age", f"{patient['age']} years", "Gender", patient["gender"]],
        ["Phone", patient.get("phone") or "--", "Address", patient.get("address") or "--"],
        ["Condition", disease_name, "ICD-10", icd10],
        ["Attending Doctor", doctor["full_name"], "Hospital", doctor.get("hospital","--")],
        ["Analysis Date", row.get("created_at","")[:16], "Report Generated", datetime.now(UTC).strftime("%d %B %Y, %H:%M UTC")],
    ]
    pt = Table(pi, colWidths=[3*cm, 5.7*cm, 3*cm, 5.7*cm])
    pt.setStyle(TableStyle([
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
        ("FONTNAME",(2,0),(2,-1),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),8.5),
        ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#f9fafb")),
        ("BACKGROUND",(2,0),(2,-1),colors.HexColor("#f9fafb")),
        ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#e5e7eb")),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white, colors.HexColor("#f9fafb")]),
        ("PADDING",(0,0),(-1,-1),5),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    story.append(pt)
    story.append(Spacer(1, 0.3*cm))

    # RISK SUMMARY
    story.append(Paragraph("Risk Assessment Summary", sec_s))
    risk_data = [
        ["Risk Level", "Risk Score", "Disease", "ICD-10 Code"],
        [row["risk_level"], f"{pct}%", disease_name, icd10],
    ]
    rt = Table(risk_data, colWidths=[3.5*cm, 3*cm, 7.9*cm, 3*cm])
    rt.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#111827")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),9),
        ("BACKGROUND",(0,1),(0,1),colors.HexColor(risk_hex)),
        ("TEXTCOLOR",(0,1),(0,1),colors.white),
        ("FONTNAME",(0,1),(0,1),"Helvetica-Bold"),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#e5e7eb")),
        ("PADDING",(0,0),(-1,-1),6),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    story.append(rt)
    story.append(Spacer(1, 0.3*cm))

    # PARAMETERS WITH NORMAL RANGE
    story.append(Paragraph("Clinical Parameters Recorded", sec_s))
    param_rows = [["Parameter", "Value Recorded", "Normal Range", "Status"]]
    for k, v in params.items():
        norm = NORMAL_RANGES.get(k)
        if norm:
            lo, hi, unit = norm
            try:
                fv = float(v)
                if fv > hi:
                    status = "HIGH"
                elif fv < lo:
                    status = "LOW"
                else:
                    status = "Normal"
                range_str = f"{lo}-{hi} {unit}"
                val_str = f"{v} {unit}"
            except (ValueError, TypeError):
                status = "--"
                range_str = f"{lo}-{hi} {unit}"
                val_str = str(v)
        else:
            status = "--"
            range_str = "--"
            val_str = str(v)
        param_rows.append([k.replace("_"," ").title(), val_str, range_str, status])

    param_t = Table(param_rows, colWidths=[4.5*cm, 4*cm, 5*cm, 3.9*cm])
    param_style = [
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#111827")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),8.5),
        ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#e5e7eb")),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f9fafb")]),
        ("PADDING",(0,0),(-1,-1),5),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]
    for i, rd in enumerate(param_rows[1:], start=1):
        if rd[3] == "HIGH":
            param_style += [("TEXTCOLOR",(3,i),(3,i),colors.HexColor("#dc2626")),("FONTNAME",(3,i),(3,i),"Helvetica-Bold")]
        elif rd[3] == "LOW":
            param_style += [("TEXTCOLOR",(3,i),(3,i),colors.HexColor("#ea580c")),("FONTNAME",(3,i),(3,i),"Helvetica-Bold")]
        elif rd[3] == "Normal":
            param_style.append(("TEXTCOLOR",(3,i),(3,i),colors.HexColor("#16a34a")))
    param_t.setStyle(TableStyle(param_style))
    story.append(param_t)
    story.append(Spacer(1, 0.3*cm))

    # FINDINGS
    story.append(Paragraph("Clinical Findings", sec_s))
    for fi in findings:
        story.append(Paragraph(f"- {fi}", body_s))
    story.append(Spacer(1, 0.2*cm))

    # RECOMMENDATIONS
    story.append(Paragraph("Medical Recommendations", sec_s))
    for r in recs:
        story.append(Paragraph(f"-> {r}", body_s))
    story.append(Spacer(1, 0.4*cm))

    # SIGNATURE
    sig_t = Table([["Doctor Signature: __________________", "Date: __________________"]], colWidths=[W/2, W/2])
    sig_t.setStyle(TableStyle([("FONTSIZE",(0,0),(-1,-1),9),("TEXTCOLOR",(0,0),(-1,-1),colors.HexColor("#374151")),("PADDING",(0,0),(-1,-1),4)]))
    story.append(sig_t)
    story.append(Spacer(1, 0.3*cm))

    # FOOTER
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#e5e7eb")))
    story.append(Paragraph(
        "DISCLAIMER: This report is AI-generated and intended to assist clinical decision-making only. "
        "It does not replace professional medical judgement. The attending doctor must review and validate "
        "all findings before any clinical action is taken. ClinicalAI - DISHA Compliant.",
        ps("disc", fontSize=7.5, textColor=colors.HexColor("#9ca3af"), leading=11, spaceBefore=4)
    ))

    doc.build(story)
    buf.seek(0)
    filename = f"ClinicalAI_Report_{row['patient_id']}_{disease_name.replace(' ','_')}_{analysis_id}.pdf"
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

'''

lines[start:end] = [new_pdf]

with open("src/api/main.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("✅ PDF endpoint upgraded using line replacement")
