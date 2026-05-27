"""
generate_pdfs.py
Generates 5 synthetic monitoirng visit reports (MVRs) as PDFs for the ETL portfolio project.
All data is entirely fictional — safe for GitHub sharing.
"""

import os
import random
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")

# ── Synthetic data pools ───────────────────────────────────────────────────────

SPONSORS = ["Nexagen Therapeutics", "Orion BioPharma", "Stratum Clinical"]
PROTOCOLS = ["NGX-2201-Ph2", "OBP-4410-Ph3", "STR-0087-Ph2b"]
SITES = {
    "SITE-001": "Dallas Research Institute, Dallas, TX",
    "SITE-002": "Midwest Clinical Center, Chicago, IL",
    "SITE-003": "Pacific Coast Trials, San Diego, CA",
    "SITE-004": "Northeast Medical Research, Boston, MA",
    "SITE-005": "Sunbelt Clinical Studies, Phoenix, AZ",
}
MONITORS = [
    "Jennifer Caldwell, CRA II",
    "Marcus Webb, Senior CRA",
    "Sofia Reyes, CRA I",
    "Derek Fong, Lead CRA",
    "Amanda Torres, CRA II",
]

FINDING_POOL = [
    {
        "id": "F-001",
        "text": (
            "Informed consent forms for subjects 004 and 009 were signed after the "
            "screening visit procedures had already begun. The ICF must be obtained "
            "prior to any study-related procedures per protocol section 6.1."
        ),
        "severity": "Major",
        "status": "Open",
    },
    {
        "id": "F-002",
        "text": (
            "eCRF query #TQ-0047 for subject 011 (Visit 3 vital signs) has been "
            "outstanding for 22 days without response. Per the data management plan, "
            "queries must be resolved within 10 business days."
        ),
        "severity": "Minor",
        "status": "Open",
    },
    {
        "id": "F-003",
        "text": (
            "Investigational product storage temperature log shows a 4-hour excursion "
            "on 14-Mar-2025 (recorded high: 28.3°C, acceptable range: 2–8°C). "
            "No CAPA has been initiated. IP stability must be evaluated by the sponsor."
        ),
        "severity": "Critical",
        "status": "Open",
    },
    {
        "id": "F-004",
        "text": (
            "Subject 007 missed the Visit 4 window by 9 days (window: ±3 days). "
            "This constitutes a protocol deviation. A deviation report was not filed "
            "with the IRB as required by the site's SOPs."
        ),
        "severity": "Major",
        "status": "In Progress",
    },
    {
        "id": "F-005",
        "text": (
            "The delegation log has not been updated to reflect the addition of a new "
            "sub-investigator (Dr. Patricia Nguyen) who has been performing study "
            "procedures since 01-Feb-2025. Training records are also absent."
        ),
        "severity": "Major",
        "status": "Open",
    },
    {
        "id": "F-006",
        "text": (
            "Centrifuge calibration certificate expired on 28-Feb-2025. Samples "
            "processed after this date may be compromised. A calibration log was not "
            "available for review at the time of the monitoring visit."
        ),
        "severity": "Major",
        "status": "Open",
    },
    {
        "id": "F-007",
        "text": (
            "IRB approval letter for the current protocol amendment (v3.1) was not "
            "present in the regulatory binder. The amendment was implemented on "
            "10-Jan-2025; IRB approval must precede implementation."
        ),
        "severity": "Critical",
        "status": "In Progress",
    },
    {
        "id": "F-008",
        "text": (
            "Drug accountability records indicate a discrepancy of 2 units between "
            "IP dispensed and IP returned/destroyed for subject 015. IP log must be "
            "reconciled and supporting documentation provided."
        ),
        "severity": "Major",
        "status": "Open",
    },
    {
        "id": "F-009",
        "text": (
            "An adverse event (mild nausea, onset 22-Mar-2025) for subject 003 was "
            "not entered into the eCRF within the required 24-hour window. The event "
            "was recorded 5 days after the subject reported it to site staff."
        ),
        "severity": "Minor",
        "status": "Closed",
    },
    {
        "id": "F-010",
        "text": (
            "Source document verification for subject 002 (Visit 2) revealed a "
            "transcription error: blood pressure recorded as 128/82 in source notes "
            "but entered as 182/82 in the eCRF. The discrepancy has since been corrected."
        ),
        "severity": "Minor",
        "status": "Closed",
    },
    {
        "id": "F-011",
        "text": (
            "Financial disclosure forms for two co-investigators are missing from the "
            "regulatory binder. Forms must be on file prior to subject enrollment "
            "per 21 CFR Part 54 requirements."
        ),
        "severity": "Major",
        "status": "Open",
    },
    {
        "id": "F-012",
        "text": (
            "Freezer temperature log has multiple missing daily entries between "
            "01-Mar-2025 and 15-Mar-2025. Continuous temperature monitoring documentation "
            "is required for stored biological specimens."
        ),
        "severity": "Minor",
        "status": "Open",
    },
]

SVR_CONFIGS = [
    {
        "report_id": "SVR-2025-0041",
        "site_key": "SITE-001",
        "sponsor_idx": 0,
        "protocol_idx": 0,
        "visit_date": "April 2, 2025",
        "monitor_idx": 0,
        "finding_ids": ["F-003", "F-005", "F-009"],
        "subjects_enrolled": 18,
        "subjects_active": 14,
        "visit_type": "Routine Monitoring Visit",
    },
    {
        "report_id": "SVR-2025-0052",
        "site_key": "SITE-002",
        "sponsor_idx": 1,
        "protocol_idx": 1,
        "visit_date": "April 10, 2025",
        "monitor_idx": 1,
        "finding_ids": ["F-001", "F-007", "F-011"],
        "subjects_enrolled": 22,
        "subjects_active": 19,
        "visit_type": "Routine Monitoring Visit",
    },
    {
        "report_id": "SVR-2025-0063",
        "site_key": "SITE-003",
        "sponsor_idx": 2,
        "protocol_idx": 2,
        "visit_date": "April 17, 2025",
        "monitor_idx": 2,
        "finding_ids": ["F-004", "F-008", "F-010", "F-012"],
        "subjects_enrolled": 11,
        "subjects_active": 9,
        "visit_type": "For-Cause Visit",
    },
    {
        "report_id": "SVR-2025-0074",
        "site_key": "SITE-004",
        "sponsor_idx": 0,
        "protocol_idx": 0,
        "visit_date": "April 24, 2025",
        "monitor_idx": 3,
        "finding_ids": ["F-002", "F-006"],
        "subjects_enrolled": 30,
        "subjects_active": 27,
        "visit_type": "Routine Monitoring Visit",
    },
    {
        "report_id": "SVR-2025-0085",
        "site_key": "SITE-005",
        "sponsor_idx": 1,
        "protocol_idx": 1,
        "visit_date": "May 1, 2025",
        "monitor_idx": 4,
        "finding_ids": ["F-001", "F-003", "F-007", "F-009"],
        "subjects_enrolled": 25,
        "subjects_active": 21,
        "visit_type": "Routine Monitoring Visit",
    },
]

FINDING_LOOKUP = {f["id"]: f for f in FINDING_POOL}


# ── PDF builder ────────────────────────────────────────────────────────────────

def build_svr_pdf(cfg: dict, output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
    )

    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        "Title", parent=styles["Title"], fontSize=16, spaceAfter=4
    )
    heading1 = ParagraphStyle(
        "H1", parent=styles["Heading1"], fontSize=12, spaceAfter=4, spaceBefore=12,
        textColor=colors.HexColor("#1a3a5c")
    )
    heading2 = ParagraphStyle(
        "H2", parent=styles["Heading2"], fontSize=10, spaceAfter=2, spaceBefore=8
    )
    normal = styles["Normal"]
    small = ParagraphStyle("Small", parent=normal, fontSize=8, textColor=colors.grey)
    bold_normal = ParagraphStyle("Bold", parent=normal, fontName="Helvetica-Bold")

    sponsor = SPONSORS[cfg["sponsor_idx"]]
    protocol = PROTOCOLS[cfg["protocol_idx"]]
    site_id = cfg["site_key"]
    site_name = SITES[site_id]
    monitor = MONITORS[cfg["monitor_idx"]]

    # ── Header ──
    story.append(Paragraph("SITE VISIT REPORT", title_style))
    story.append(Paragraph(f"Clinical Monitoring — {sponsor}", styles["Heading2"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1a3a5c")))
    story.append(Spacer(1, 10))

    # ── Cover table ──
    cover_data = [
        ["Report ID:", cfg["report_id"], "Visit Type:", cfg["visit_type"]],
        ["Protocol:", protocol, "Visit Date:", cfg["visit_date"]],
        ["Site ID:", site_id, "Monitor:", monitor],
        ["Site Name:", site_name, "", ""],
        ["Subjects Enrolled:", str(cfg["subjects_enrolled"]),
         "Subjects Active:", str(cfg["subjects_active"])],
    ]
    cover_table = Table(cover_data, colWidths=[1.4 * inch, 2.3 * inch, 1.4 * inch, 2.3 * inch])
    cover_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f0fb")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 16))

    # ── Purpose ──
    story.append(Paragraph("1. Purpose & Scope", heading1))
    story.append(Paragraph(
        f"This Site Visit Report documents findings from the {cfg['visit_type']} "
        f"conducted at {site_name} ({site_id}) on {cfg['visit_date']} for "
        f"Protocol {protocol} sponsored by {sponsor}. The visit was conducted in "
        "accordance with ICH E6(R2) Good Clinical Practice guidelines and applicable "
        "regulatory requirements. Areas reviewed included informed consent, eCRF "
        "completeness, investigational product accountability, regulatory documentation, "
        "adverse event reporting, and source document verification.",
        normal,
    ))
    story.append(Spacer(1, 8))

    # ── Summary ──
    findings = [FINDING_LOOKUP[fid] for fid in cfg["finding_ids"]]
    critical = sum(1 for f in findings if f["severity"] == "Critical")
    major = sum(1 for f in findings if f["severity"] == "Major")
    minor = sum(1 for f in findings if f["severity"] == "Minor")
    open_ct = sum(1 for f in findings if f["status"] == "Open")
    inprog_ct = sum(1 for f in findings if f["status"] == "In Progress")
    closed_ct = sum(1 for f in findings if f["status"] == "Closed")

    story.append(Paragraph("2. Visit Summary", heading1))
    summary_data = [
        ["Finding Severity", "Count", "Finding Status", "Count"],
        ["Critical", str(critical), "Open", str(open_ct)],
        ["Major", str(major), "In Progress", str(inprog_ct)],
        ["Minor", str(minor), "Closed", str(closed_ct)],
        ["TOTAL", str(len(findings)), "TOTAL", str(len(findings))],
    ]
    summary_table = Table(summary_data, colWidths=[2 * inch, 1 * inch, 2 * inch, 1 * inch])
    summary_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8f0fb")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f5f7fa")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("ALIGN", (3, 0), (3, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 12))

    # ── Findings ──
    story.append(Paragraph("3. Findings Detail", heading1))

    severity_colors = {
        "Critical": colors.HexColor("#c0392b"),
        "Major": colors.HexColor("#e67e22"),
        "Minor": colors.HexColor("#2980b9"),
    }

    for i, finding in enumerate(findings, 1):
        sev_color = severity_colors.get(finding["severity"], colors.black)
        story.append(Paragraph(
            f"Finding {i} of {len(findings)} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<font color='#{sev_color.hexval()[2:]}'><b>{finding['severity']}</b></font>"
            f"&nbsp;&nbsp;|&nbsp;&nbsp; Status: <b>{finding['status']}</b>",
            heading2,
        ))
        story.append(Paragraph(finding["text"], normal))
        story.append(Spacer(1, 8))

    # ── Action Items ──
    story.append(Paragraph("4. Required Actions", heading1))
    open_findings = [f for f in findings if f["status"] in ("Open", "In Progress")]
    if open_findings:
        for f in open_findings:
            story.append(Paragraph(
                f"<b>\u2022 [{f['severity']}]</b> {f['text'][:80]}... "
                f"<i>(Status: {f['status']})</i>",
                normal,
            ))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("No open action items at time of report issuance.", normal))

    story.append(Spacer(1, 16))

    # ── Footer ──
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"<b>CONFIDENTIAL</b> — This report is intended solely for use by {sponsor} "
        "and authorized personnel. All data herein is entirely synthetic and fictional, "
        "generated for portfolio/demonstration purposes only. Not for clinical use.",
        small,
    ))

    doc.build(story)
    print(f"  Generated: {os.path.basename(output_path)}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Generating {len(SVR_CONFIGS)} synthetic Site Visit Report PDFs...")
    for cfg in SVR_CONFIGS:
        filename = f"{cfg['report_id']}.pdf"
        output_path = os.path.join(OUTPUT_DIR, filename)
        build_svr_pdf(cfg, output_path)
    print(f"\nDone. PDFs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
