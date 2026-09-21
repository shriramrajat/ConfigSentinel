"""
reporting.pdf_generator
~~~~~~~~~~~~~~~~~~~~~~~

Binary PDF generator for ConfigSentinel executive reports using ReportLab.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.api.schemas import AuditResponse
from src.mapping.redaction import redact_secrets


def generate_pdf_report(audit: AuditResponse, audit_id: str) -> bytes:
    """Generate a clean binary PDF executive summary report for an audit result.

    Returns bytes starting with ``%PDF-``.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=6,
    )
    meta_style = ParagraphStyle(
        "ReportMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12,
    )
    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=12,
        spaceAfter=8,
    )
    cell_style = ParagraphStyle(
        "CellText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=11,
    )
    code_style = ParagraphStyle(
        "CodeCellText",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0F766E"),
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("ConfigSentinel Executive Audit Report", title_style))
    created_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    meta_text = (
        f"<b>Audit ID:</b> {audit_id} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Vendor:</b> {audit.summary.vendor.upper()} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Hostname:</b> {audit.summary.hostname or 'N/A'} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Generated:</b> {created_str}"
    )
    story.append(Paragraph(meta_text, meta_style))
    story.append(Spacer(1, 10))

    # Executive Summary Card Table
    summary = audit.summary
    summary_data = [
        ["Pass Count", "Fail Count", "Needs Review", "Total Controls"],
        [str(summary.pass_count), str(summary.fail_count), str(summary.needs_review_count), str(summary.total_controls)],
    ]
    summary_table = Table(summary_data, colWidths=[130, 130, 130, 130])
    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#334155")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("TEXTCOLOR", (0, 1), (0, 1), colors.HexColor("#16A34A")),  # Pass
            ("TEXTCOLOR", (1, 1), (1, 1), colors.HexColor("#DC2626")),  # Fail
            ("TEXTCOLOR", (2, 1), (2, 1), colors.HexColor("#D97706")),  # Review
            ("TEXTCOLOR", (3, 1), (3, 1), colors.HexColor("#0284C7")),  # Total
            ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 1), (-1, 1), 14),
        ])
    )
    story.append(summary_table)
    story.append(Spacer(1, 16))

    # Detailed Audit Results
    story.append(Paragraph("Detailed Control Evaluation Findings", section_style))

    table_data = [
        [
            Paragraph("<b>Control ID</b>", cell_style),
            Paragraph("<b>Control Name</b>", cell_style),
            Paragraph("<b>Severity</b>", cell_style),
            Paragraph("<b>Status</b>", cell_style),
            Paragraph("<b>Risk Score</b>", cell_style),
            Paragraph("<b>Evidence & Guidance</b>", cell_style),
        ]
    ]

    for r in audit.results:
        ev_lines = []
        for e in r.evidence:
            if e.line_number:
                ev_lines.append(f"Line {e.line_number}: {e.note}")
            else:
                ev_lines.append(e.note)
        ev_text = "<br/>".join(ev_lines) if ev_lines else "No evidence recorded"

        rem_text = ""
        if r.remediations:
            rem_hints = [f"• [{rem.vendor}] {rem.guidance}" for rem in r.remediations]
            rem_text = "<br/><b>Remediation:</b><br/>" + "<br/>".join(rem_hints)

        combined_detail = f"{ev_text}{rem_text}"

        table_data.append([
            Paragraph(r.control_id, code_style),
            Paragraph(r.control_name, cell_style),
            Paragraph(r.severity.upper(), cell_style),
            Paragraph(r.status.upper(), cell_style),
            Paragraph(f"{r.risk_score:.1f} ({r.risk_level})", cell_style),
            Paragraph(redact_secrets(combined_detail), cell_style),
        ])

    results_table = Table(table_data, colWidths=[65, 95, 55, 55, 65, 185])
    results_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ])
    )
    story.append(results_table)

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
