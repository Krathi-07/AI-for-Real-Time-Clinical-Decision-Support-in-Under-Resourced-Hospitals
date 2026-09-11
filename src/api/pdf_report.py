from __future__ import annotations

import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

RISK_COLOURS = {
    "LOW":      colors.HexColor("#16a34a"),
    "MEDIUM":   colors.HexColor("#d97706"),
    "HIGH":     colors.HexColor("#ea580c"),
    "CRITICAL": colors.HexColor("#dc2626"),
}
RISK_BG = {
    "LOW":      colors.HexColor("#f0fdf4"),
    "MEDIUM":   colors.HexColor("#fffbeb"),
    "HIGH":     colors.HexColor("#fff7ed"),
    "CRITICAL": colors.HexColor("#fef2f2"),
}


def build_pdf(payload: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=18*mm, bottomMargin=18*mm,
    )
    styles = getSampleStyleSheet()
    story = []

    risk_level  = payload.get("risk_level", "LOW")
    risk_colour = RISK_COLOURS.get(risk_level, colors.grey)
    risk_bg     = RISK_BG.get(risk_level, colors.white)

    # Header
    story.append(Paragraph("AI Clinical Decision Support", ParagraphStyle(
        "h", parent=styles["Normal"], fontSize=18, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f172a"), spaceAfter=2,
    )))
    story.append(Paragraph(
        f"Patient Risk Assessment Report - "
        f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        ParagraphStyle("sub", parent=styles["Normal"], fontSize=10,
                       textColor=colors.HexColor("#64748b"), spaceAfter=8),
    ))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=colors.HexColor("#e2e8f0"), spaceAfter=10))

    # Risk banner
    risk_pct = round(payload.get("risk_score", 0) * 100, 1)
    banner = Table([[
        Paragraph(
            f'<font size="14"><b>{risk_level} RISK</b></font><br/>'
            f'<font size="11">{payload.get("alert_text", "")}</font>',
            styles["Normal"],
        ),
        Paragraph(
            f'<font size="22"><b>{risk_pct}%</b></font>',
            ParagraphStyle("score", parent=styles["Normal"],
                           alignment=2, textColor=risk_colour),
        ),
    ]], colWidths=["75%", "25%"])
    banner.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), risk_bg),
        ("BOX",           (0,0), (-1,-1), 1.5, risk_colour),
        ("LEFTPADDING",   (0,0), (-1,-1), 14),
        ("RIGHTPADDING",  (0,0), (-1,-1), 14),
        ("TOPPADDING",    (0,0), (-1,-1), 12),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(banner)
    story.append(Spacer(1, 10))

    # Patient info row
    info = Table([[
        Paragraph(f"<b>Patient ID:</b> {payload.get('patient_id','N/A')}", styles["Normal"]),
        Paragraph(f"<b>Completeness:</b> {round(payload.get('completeness_score',0)*100)}%", styles["Normal"]),
        Paragraph(f"<b>Human Review:</b> {'Required' if payload.get('requires_human_review') else 'Not required'}", styles["Normal"]),
    ]], colWidths=["33%","33%","34%"])
    info.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ("BOX",           (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(info)
    story.append(Spacer(1, 14))

    section_style = ParagraphStyle(
        "section", parent=styles["Normal"], fontSize=11,
        fontName="Helvetica-Bold", textColor=colors.HexColor("#1e293b"),
        spaceBefore=10, spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "body", parent=styles["Normal"], fontSize=10,
        textColor=colors.HexColor("#374151"), leading=15,
    )

    # Risk drivers
    drivers = payload.get("model_drivers", [])
    if drivers:
        story.append(Paragraph("Top Risk Drivers (SHAP)", section_style))
        t = Table([[Paragraph(f"- {d}", body_style)] for d in drivers], colWidths=["100%"])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ("BOX",           (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ("LEFTPADDING",   (0,0), (-1,-1), 12),
            ("TOPPADDING",    (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ]))
        story.append(t)

    # NLP findings
    nlp = payload.get("nlp_findings", {})
    symptoms    = nlp.get("symptoms", [])
    diagnoses   = nlp.get("diagnoses", [])
    medications = nlp.get("medications", [])
    if symptoms or diagnoses or medications:
        story.append(Paragraph("NLP Clinical Findings", section_style))
        nlp_rows = [
            [Paragraph("<b>Symptoms</b>",    body_style), Paragraph(", ".join(symptoms)    or "None", body_style)],
            [Paragraph("<b>Diagnoses</b>",   body_style), Paragraph(", ".join(diagnoses)   or "None", body_style)],
            [Paragraph("<b>Medications</b>", body_style), Paragraph(", ".join(medications) or "None", body_style)],
        ]
        nlp_t = Table(nlp_rows, colWidths=["25%","75%"])
        nlp_t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ("BOX",           (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ("LINEBELOW",     (0,0), (-1,-2), 0.3, colors.HexColor("#e2e8f0")),
            ("LEFTPADDING",   (0,0), (-1,-1), 10),
            ("TOPPADDING",    (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ]))
        story.append(nlp_t)

    # Treatment plan
    treatment = payload.get("treatment_plan", {})
    if treatment:
        story.append(Paragraph("Treatment Recommendations", section_style))
        rows = [
            [Paragraph(f"<b>{k}</b>", body_style),
             Paragraph(", ".join(v) if isinstance(v, list) else str(v), body_style)]
            for k, v in treatment.items()
        ]
        t = Table(rows, colWidths=["30%","70%"])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ("BOX",           (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ("LINEBELOW",     (0,0), (-1,-2), 0.3, colors.HexColor("#e2e8f0")),
            ("LEFTPADDING",   (0,0), (-1,-1), 10),
            ("TOPPADDING",    (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ]))
        story.append(t)

    # Reasoning trace
    trace = payload.get("reasoning_trace", [])
    if trace:
        story.append(Paragraph("Reasoning Trace", section_style))
        for i, step in enumerate(trace, 1):
            story.append(Paragraph(f"{i}. {step}", body_style))
        story.append(Spacer(1, 6))

    # Footer
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "FOR CLINICAL DECISION SUPPORT ONLY. This report must be reviewed by a licensed "
        "clinician before any treatment decision is made. Complies with India DISHA guidelines.",
        ParagraphStyle("disc", parent=styles["Normal"], fontSize=8,
                       textColor=colors.HexColor("#94a3b8"), leading=12),
    ))

    doc.build(story)
    return buf.getvalue()
