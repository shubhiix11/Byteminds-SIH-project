"""
PDF Report Generator for LabelSure Legal Metrology Compliance Inspection.
Formats computed compliance results into a professional multi-page PDF document using ReportLab.
Does NOT re-run OCR, rules, or measurements. Formats existing computed results only.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

STATUS_COLORS = {
    "COMPLIANT": colors.HexColor("#10b981"),
    "NON_COMPLIANT": colors.HexColor("#f43f5e"),
    "NEEDS_REVIEW": colors.HexColor("#f59e0b"),
    "PASS": colors.HexColor("#10b981"),
    "FAIL": colors.HexColor("#f43f5e"),
    "WARNING": colors.HexColor("#f59e0b"),
    "NOT_VERIFIABLE": colors.HexColor("#60a5fa"),
    "NOT_APPLICABLE": colors.HexColor("#6b7280")
}

class ReportGenerator:
    def __init__(self, reports_dir: str):
        self.reports_dir = reports_dir
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_pdf_report(self, scan_result: dict, annotated_image_path: str = None) -> str:
        """
        Generates PDF report for a scan result and saves to reports/<scan_id>.pdf.
        Returns the relative or absolute file path of the generated PDF.
        """
        scan_id = str(scan_result.get("scan_id") or "scan_demo")
        pdf_filename = f"report_{scan_id}.pdf"
        pdf_path = os.path.join(self.reports_dir, pdf_filename)

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom typography styles
        style_header_title = ParagraphStyle('ReportHeaderTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=22, leading=26, textColor=colors.HexColor("#0f172a"))
        style_header_sub = ParagraphStyle('ReportHeaderSub', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=14, textColor=colors.HexColor("#00f2fe"))
        style_disclaimer = ParagraphStyle('DisclaimerText', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=8.5, leading=12, textColor=colors.HexColor("#1e3a8a"))
        style_verdict = ParagraphStyle('VerdictText', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=14, leading=18, alignment=TA_CENTER)
        style_section_heading = ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=colors.HexColor("#1e293b"))
        style_table_header = ParagraphStyle('TableHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.white)
        style_table_cell = ParagraphStyle('TableCell', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=colors.HexColor("#334155"))
        style_table_cell_bold = ParagraphStyle('TableCellBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=colors.HexColor("#0f172a"))

        story = []

        # --- 1. HEADER SECTION ---
        header_data = [
            [
                Paragraph("<b>LabelSure</b><br/><font size=8 color='#64748b'>LEGAL METROLOGY COMPLIANCE SCANNER</font>", style_header_title),
                Paragraph(f"<b>INSPECTION REPORT</b><br/>Scan ID: #{scan_id}<br/>Date: {scan_result.get('inspection_date', '2026-09-11')}", ParagraphStyle('RightHead', parent=styles['Normal'], alignment=TA_RIGHT, fontSize=9, leading=12, textColor=colors.HexColor("#475569")))
            ]
        ]
        header_table = Table(header_data, colWidths=[300, 240])
        header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
        story.append(header_table)
        story.append(Spacer(1, 10))

        # Horizontal Divider
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#00f2fe"), spaceAfter=12))

        # --- 2. LEGAL DISCLAIMER BANNER ---
        disclaimer_text = (
            "<b>LEGAL SAFETY DISCLAIMER:</b> " +
            (scan_result.get("disclaimer") or "AI-assisted compliance screening tool — Not an official government certification system.")
        )
        disclaimer_table = Table(
            [[Paragraph(disclaimer_text, style_disclaimer)]],
            colWidths=[540]
        )
        disclaimer_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#eff6ff")),
            ('BORDER', (0,0), (-1,-1), 1, colors.HexColor("#bfdbfe")),
            ('PADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]))
        story.append(disclaimer_table)
        story.append(Spacer(1, 12))

        # --- 3. OVERALL VERDICT & SUMMARY COUNTS ---
        overall_status = scan_result.get("overall_status", "NEEDS_REVIEW")
        verdict_color = STATUS_COLORS.get(overall_status, colors.HexColor("#f59e0b"))
        summary_counts = scan_result.get("summary") or {}

        verdict_para = Paragraph(f"<font color='white'>OVERALL STATUS: {overall_status}</font>", style_verdict)
        verdict_box = Table([[verdict_para]], colWidths=[540])
        verdict_box.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), verdict_color),
            ('PADDING', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]))
        story.append(verdict_box)
        story.append(Spacer(1, 8))

        # Summary Counts Bar
        summary_data = [
            [
                Paragraph(f"<b>Rules Checked:</b> {summary_counts.get('rules_checked', 0)}", style_table_cell),
                Paragraph(f"<b>Passed:</b> {summary_counts.get('passed', 0)}", style_table_cell),
                Paragraph(f"<b>Failed:</b> {summary_counts.get('failed', 0)}", style_table_cell),
                Paragraph(f"<b>Not Verifiable:</b> {summary_counts.get('not_verifiable', 0)}", style_table_cell),
                Paragraph(f"<b>Not Applicable:</b> {summary_counts.get('not_applicable', 0)}", style_table_cell)
            ]
        ]
        summary_table = Table(summary_data, colWidths=[108, 108, 108, 108, 108])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('PADDING', (0,0), (-1,-1), 6)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 14))

        # --- 4. DETECTED LABEL DECLARATIONS TABLE ---
        story.append(Paragraph("<b>1. Extracted Package Declarations & Data Origins</b>", style_section_heading))
        story.append(Spacer(1, 6))

        decl = scan_result.get("detected_declarations") or scan_result.get("extracted_facts", {}).get("declarations", {})
        
        decl_rows = [
            [Paragraph("Field Declaration", style_table_header), Paragraph("Detected Value", style_table_header), Paragraph("Source / Data Origin", style_table_header)]
        ]

        def fmt_val(v):
            if isinstance(v, dict):
                return str(v.get("value") or v.get("raw") or v.get("name") or "")
            return str(v or "N/A")

        fields_map = [
            ("Commodity Name", decl.get("commodity_name"), "Image OCR"),
            ("Net Quantity", decl.get("net_quantity"), "Image OCR"),
            ("Maximum Retail Price (MRP)", decl.get("max_retail_price"), "Image OCR"),
            ("Date of Mfg / Packing", decl.get("date_of_manufacture"), "Image OCR"),
            ("Manufacturer / Packer", decl.get("manufacturer"), "Image OCR"),
            ("Consumer Care Contact", decl.get("consumer_care"), "Image OCR"),
            ("Country of Origin", decl.get("country_of_origin"), "Image OCR / Conditional")
        ]

        for fname, fval, fsource in fields_map:
            val_str = fmt_val(fval)
            decl_rows.append([
                Paragraph(f"<b>{fname}</b>", style_table_cell_bold),
                Paragraph(val_str if val_str else "Not Detected", style_table_cell),
                Paragraph(fsource, style_table_cell)
            ])

        decl_table = Table(decl_rows, colWidths=[150, 260, 130])
        decl_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('PADDING', (0,0), (-1,-1), 5),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")])
        ]))
        story.append(decl_table)
        story.append(Spacer(1, 14))

        # --- 5. PRODUCT & BARCODE CROSS-CHECK ---
        enrichment = scan_result.get("product_enrichment") or scan_result.get("enrichment") or {}
        cross_check = scan_result.get("cross_check") or {}

        if enrichment and enrichment.get("available"):
            story.append(Paragraph("<b>2. AI Product & Barcode Enrichment Cross-Check</b>", style_section_heading))
            story.append(Spacer(1, 6))

            enr_info = enrichment.get("enrichment", {})
            cc_status = "✓ DETAILS CONSISTENT" if cross_check.get("details_consistent") else f"⚠ {cross_check.get('mismatches_found', 1)} INFORMATION MISMATCH(ES)"
            
            cc_rows = [
                [Paragraph("Barcode", style_table_cell_bold), Paragraph(str(enr_info.get("barcode", "N/A")), style_table_cell)],
                [Paragraph("AI Enriched Product", style_table_cell_bold), Paragraph(str(enr_info.get("product_name", "N/A")), style_table_cell)],
                [Paragraph("AI Enriched Brand / Mfg", style_table_cell_bold), Paragraph(f"{enr_info.get('brand', '')} ({enr_info.get('manufacturer', '')})", style_table_cell)],
                [Paragraph("Consistency Result", style_table_cell_bold), Paragraph(f"<b>{cc_status}</b> (Informational Only)", style_table_cell)]
            ]
            cc_table = Table(cc_rows, colWidths=[160, 380])
            cc_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f1f5f9")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ('PADDING', (0,0), (-1,-1), 5)
            ]))
            story.append(cc_table)
            story.append(Spacer(1, 14))

        # --- 6. RULE-BY-RULE COMPLIANCE TABLE ---
        story.append(Paragraph("<b>3. Legal Metrology (Packaged Commodities) Rule Evaluation</b>", style_section_heading))
        story.append(Spacer(1, 6))

        rule_rows = [
            [
                Paragraph("Rule Number", style_table_header),
                Paragraph("Requirement Title", style_table_header),
                Paragraph("Evidence / Detected Text", style_table_header),
                Paragraph("Status", style_table_header),
                Paragraph("Reason & Legal Source", style_table_header)
            ]
        ]

        rule_results = scan_result.get("rule_results") or []
        for rule in rule_results:
            st = rule.get("status", "NOT_VERIFIABLE")
            st_color = STATUS_COLORS.get(st, colors.HexColor("#64748b"))
            st_cell = Paragraph(f"<font color='{st_color.hexval()}'><b>{st}</b></font>", style_table_cell_bold)

            rule_rows.append([
                Paragraph(rule.get("rule_number", ""), style_table_cell_bold),
                Paragraph(rule.get("title", ""), style_table_cell),
                Paragraph(rule.get("detected_text") or "N/A", style_table_cell),
                st_cell,
                Paragraph(f"{rule.get('reason', '')}<br/><font color='#64748b' size=6.5>Ref: {rule.get('source_reference', '')}</font>", style_table_cell)
            ])

        rule_table = Table(rule_rows, colWidths=[70, 110, 110, 75, 175])
        rule_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('PADDING', (0,0), (-1,-1), 4),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")])
        ]))
        story.append(rule_table)
        story.append(Spacer(1, 14))

        # --- 7. ANNOTATED EVIDENCE IMAGE ---
        if annotated_image_path and os.path.exists(annotated_image_path):
            story.append(KeepTogether([
                Paragraph("<b>4. Annotated Label Image Evidence</b>", style_section_heading),
                Spacer(1, 6),
                Image(annotated_image_path, width=320, height=240),
                Spacer(1, 4),
                Paragraph("<font size=7 color='#64748b'>Legend: GREEN=PASS | RED=FAIL | AMBER=WARNING/NOT_VERIFIABLE | GRAY=NOT_APPLICABLE</font>", ParagraphStyle('Legend', parent=styles['Normal'], alignment=TA_CENTER))
            ]))
            story.append(Spacer(1, 14))

        # --- 8. OFFICIAL LEGAL SOURCES ---
        story.append(Paragraph("<b>5. Official Legal Source References</b>", style_section_heading))
        story.append(Spacer(1, 4))
        legal_ref_text = (
            "Rule evaluations are based on the official Legal Metrology (Packaged Commodities) Rules, 2011 "
            "and applicable notifications issued by the Department of Consumer Affairs, Government of India. "
            "https://consumeraffairs.gov.in/pages/legal-metrology-act"
        )
        story.append(Paragraph(legal_ref_text, ParagraphStyle('LegalRef', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=7.5, leading=10, textColor=colors.HexColor("#475569"))))

        doc.build(story)
        return pdf_path
