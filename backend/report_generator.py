from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io


def generate_scan_pdf(scan, result):
    """
    scan: the DB row (models.Scan) — used for product_name, category,
          timestamp, scan_id.
    result: the dict returned by rules.run_rule_engine() — must contain
          field_results, compliance_pct, fields_passed, fields_total,
          overall_status, violations, readability_notes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=2.2*cm, bottomMargin=2*cm,
        leftMargin=2*cm, rightMargin=2*cm
    )
    styles = getSampleStyleSheet()

    # ---- Styles ----
    header_label_style = ParagraphStyle(
        "HeaderLabel", parent=styles["Normal"], fontSize=9,
        textColor=colors.HexColor("#6b7280"), spaceAfter=2
    )
    title_style = ParagraphStyle(
        "TitleStyle", parent=styles["Heading1"], fontSize=22,
        textColor=colors.HexColor("#111827"), spaceAfter=4, spaceBefore=0
    )
    subtitle_style = ParagraphStyle(
        "SubtitleStyle", parent=styles["Normal"], fontSize=10.5,
        textColor=colors.HexColor("#6b7280"), spaceAfter=2
    )
    meta_style = ParagraphStyle(
        "MetaStyle", parent=styles["Normal"], fontSize=8.5,
        textColor=colors.HexColor("#9ca3af"), spaceAfter=16
    )
    section_heading_style = ParagraphStyle(
        "SectionHeading", parent=styles["Heading2"], fontSize=13,
        textColor=colors.HexColor("#111827"), spaceBefore=16, spaceAfter=10
    )
    note_style = ParagraphStyle(
        "NoteStyle", parent=styles["Normal"], fontSize=8.5, leading=12,
        textColor=colors.HexColor("#6b7280"), spaceAfter=6
    )

    cell_field_style = ParagraphStyle(
        "CellField", parent=styles["Normal"], fontSize=9, leading=12,
        textColor=colors.HexColor("#111827"), fontName="Helvetica-Bold"
    )
    cell_value_style = ParagraphStyle(
        "CellValue", parent=styles["Normal"], fontSize=9, leading=12,
        textColor=colors.HexColor("#374151")
    )
    cell_pass_style = ParagraphStyle(
        "CellPass", parent=styles["Normal"], fontSize=9, leading=12,
        textColor=colors.HexColor("#16a34a"), fontName="Helvetica-Bold"
    )
    cell_fail_style = ParagraphStyle(
        "CellFail", parent=styles["Normal"], fontSize=9, leading=12,
        textColor=colors.HexColor("#dc2626"), fontName="Helvetica-Bold"
    )
    cell_na_style = ParagraphStyle(
        "CellNA", parent=styles["Normal"], fontSize=9, leading=12,
        textColor=colors.HexColor("#9ca3af"), fontName="Helvetica-Oblique"
    )
    header_cell_style = ParagraphStyle(
        "HeaderCell", parent=styles["Normal"], fontSize=9.5, leading=12,
        textColor=colors.white, fontName="Helvetica-Bold"
    )
    violation_style = ParagraphStyle(
        "ViolationStyle", parent=styles["Normal"], fontSize=9, leading=13,
        textColor=colors.HexColor("#374151"), spaceAfter=4
    )
    footer_style = ParagraphStyle(
        "FooterStyle", parent=styles["Normal"], fontSize=8,
        textColor=colors.HexColor("#9ca3af"), leading=11
    )

    elements = []

    # ---- Header ----
    elements.append(Paragraph("LEGAL METROLOGY COMPLIANCE CHECKER", header_label_style))
    elements.append(Paragraph("Compliance Report", title_style))

    product_name = getattr(scan, "product_name", None) or "Unnamed Product"
    category = f" &nbsp;&bull;&nbsp; {scan.category}" if getattr(scan, "category", None) else ""
    timestamp_str = scan.timestamp.strftime("%d %B %Y, %I:%M %p") if getattr(scan, "timestamp", None) else ""

    elements.append(Paragraph(f"<b>{product_name}</b>{category}", subtitle_style))
    if timestamp_str:
        elements.append(Paragraph(f"Scanned on {timestamp_str}", subtitle_style))
    elements.append(Paragraph(f"Scan ID: {scan.scan_id}", meta_style))

    elements.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#e5e7eb"), spaceAfter=16))

    # ---- Overall status banner ----
    is_compliant = result["overall_status"] == "compliant"
    status_bg = colors.HexColor("#f0fdf4") if is_compliant else colors.HexColor("#fef2f2")
    status_border = colors.HexColor("#16a34a") if is_compliant else colors.HexColor("#dc2626")
    status_text_color = colors.HexColor("#166534") if is_compliant else colors.HexColor("#991b1b")

    status_style = ParagraphStyle(
        "StatusStyle", parent=styles["Normal"], fontSize=16,
        textColor=status_text_color, leading=20
    )

    status_label = "COMPLIANT" if is_compliant else "NON-COMPLIANT"
    status_para = Paragraph(
        f"<b>{result['compliance_pct']}% Compliance &mdash; {status_label}</b>"
        f"<br/><font size=9>{result['fields_passed']} of {result['fields_total']} mandatory fields passed</font>",
        status_style
    )

    status_table = Table([[status_para]], colWidths=[17*cm])
    status_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), status_bg),
        ("BOX", (0, 0), (-1, -1), 1, status_border),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    elements.append(status_table)

    # ---- Field-by-field table ----
    elements.append(Paragraph("Field-by-Field Analysis", section_heading_style))

    table_data = [[
        Paragraph("Field", header_cell_style),
        Paragraph("Tier", header_cell_style),
        Paragraph("Status", header_cell_style),
        Paragraph("Detected Value", header_cell_style),
    ]]

    style_by_status = {
        "pass": cell_pass_style,
        "fail": cell_fail_style,
        "not_applicable": cell_na_style,
    }
    display_by_status = {
        "pass": "PASS",
        "fail": "FAIL",
        "not_applicable": "N/A",
    }

    for field_result in result["field_results"]:
        status = field_result.get("status", "")
        style_cell = style_by_status.get(status, cell_value_style)
        status_display = display_by_status.get(status, status.upper())

        table_data.append([
            Paragraph(field_result.get("label", field_result.get("field", "")), cell_field_style),
            Paragraph(field_result.get("tier", "").capitalize(), cell_value_style),
            Paragraph(status_display, style_cell),
            Paragraph(field_result.get("detected_value") or "Not detected", cell_value_style),
        ])

    table = Table(table_data, colWidths=[4.5*cm, 2.8*cm, 2.2*cm, 7.5*cm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
    ]))
    elements.append(table)

    # ---- Readability notes (informational only — does not affect score) ----
    if result.get("readability_notes"):
        elements.append(Paragraph("Font Readability (Informational)", section_heading_style))
        elements.append(Paragraph(
            "Measured as text height relative to image height, not physical mm \u2014 "
            "does not currently affect the compliance score.",
            note_style
        ))

        read_rows = [[
            Paragraph("Field", header_cell_style),
            Paragraph("Relative Height", header_cell_style),
            Paragraph("Flag", header_cell_style),
        ]]
        for note in result["readability_notes"]:
            flag_text = "Below threshold" if note["small_text_flag"] else "OK"
            flag_style = cell_fail_style if note["small_text_flag"] else cell_pass_style
            read_rows.append([
                Paragraph(note["label"], cell_field_style),
                Paragraph(f"{note['text_height_pct']:.1f}%", cell_value_style),
                Paragraph(flag_text, flag_style),
            ])

        read_table = Table(read_rows, colWidths=[6*cm, 5.5*cm, 5.5*cm])
        read_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#374151")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
        ]))
        elements.append(read_table)

    # ---- Violation summary / offence log ----
    if result.get("violations"):
        elements.append(Paragraph("Violation Summary", section_heading_style))
        for i, v in enumerate(result["violations"], start=1):
            elements.append(Paragraph(
                f"<b>{i}.</b> {v['description']} "
                f"&nbsp;<font color='#9ca3af'>({v['rule']})</font>",
                violation_style
            ))
        elements.append(Spacer(1, 8))

    # ---- Footer ----
    elements.append(Spacer(1, 16))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb"), spaceAfter=8))
    elements.append(Paragraph(
        "Generated automatically by Legal Metrology Compliance Checker. "
        "Font readability is an image-relative heuristic, not a physical measurement, "
        "and does not affect the compliance score shown above. "
        "This report is a compliance aid and does not constitute a legal certification.",
        footer_style
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer