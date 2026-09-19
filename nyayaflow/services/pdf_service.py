"""PDF generation service for settlement agreements."""
import os
from uuid import uuid4
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY


class PDFService:
    """Generate legally formatted settlement agreement PDFs."""

    @staticmethod
    def generate_settlement_pdf(draft_text: str, case_id: int, output_dir: str = "./uploads/settlements") -> str:
        os.makedirs(output_dir, exist_ok=True)
        # Preserve every generated draft instead of overwriting earlier settlements
        # for the same case.
        file_path = os.path.join(output_dir, f"settlement_case_{case_id}_{uuid4().hex}.pdf")

        doc = SimpleDocTemplate(file_path, pagesize=A4,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#1a1a1a"),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )

        body_style = ParagraphStyle(
            "CustomBody",
            parent=styles["BodyText"],
            fontSize=11,
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
        )

        header_style = ParagraphStyle(
            "CustomHeader",
            parent=styles["Heading2"],
            fontSize=13,
            textColor=colors.HexColor("#2c3e50"),
            spaceAfter=12,
            fontName="Helvetica-Bold",
        )

        story = []

        # Header
        story.append(Paragraph("MEDIATED SETTLEMENT AGREEMENT", title_style))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(f"<b>Case Reference:</b> NYAYA-CASE-{case_id:05d}", body_style))
        story.append(Paragraph(f"<b>Platform:</b> NyayaFlow AI-Assisted ODR Platform", body_style))
        story.append(Paragraph("<b>Jurisdiction:</b> Republic of India", body_style))
        story.append(Spacer(1, 0.3 * inch))

        # Disclaimer
        disclaimer = (
            "<b>IMPORTANT LEGAL DISCLAIMER:</b> This document is a <i>proposed mediated settlement agreement</i> "
            "generated through AI-assisted facilitation on the NyayaFlow platform. It does <b>not</b> constitute a "
            "judicial order or arbitral award. This agreement becomes binding only upon execution by both parties "
            "in accordance with the Mediation Act, 2023 (India), and registration where required. The platform "
            "does not determine civil or criminal liability. Parties are advised to seek independent legal counsel "
            "before execution."
        )
        story.append(Paragraph(disclaimer, body_style))
        story.append(Spacer(1, 0.3 * inch))

        # Content
        story.append(Paragraph("TERMS OF SETTLEMENT", header_style))

        # Split draft text into paragraphs and format
        paragraphs = (draft_text or "").split("\n")
        import re

        def format_markdown(text: str) -> str:
            escaped = escape(text)
            # Convert **bold** to <b>bold</b>
            escaped = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", escaped)
            # Convert *italic* to <i>italic</i>
            escaped = re.sub(r"\*(.*?)\*", r"<i>\1</i>", escaped)
            return escaped

        for para in paragraphs:
            para = para.strip()
            if para:
                if para.startswith("#"):
                    clean_header = format_markdown(para.lstrip("#").strip())
                    story.append(Paragraph(clean_header, header_style))
                elif para.startswith("- ") or para.startswith("* "):
                    clean_item = format_markdown(para[2:].strip())
                    story.append(Paragraph(f"• {clean_item}", body_style))
                else:
                    story.append(Paragraph(format_markdown(para), body_style))

        story.append(Spacer(1, 0.5 * inch))

        # Signature block
        story.append(Paragraph("EXECUTION", header_style))
        sig_data = [
            ["Party A Signature", "Party B Signature"],
            ["_________________________", "_________________________"],
            ["Date: _______________", "Date: _______________"],
        ]
        sig_table = Table(sig_data, colWidths=[2.5 * inch, 2.5 * inch])
        sig_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]))
        story.append(sig_table)

        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph(
            "<b>Admin/Mediator Certification:</b> This settlement draft has been reviewed by the platform administrator. "
            "Final approval and digital execution are subject to administrative review.",
            body_style,
        ))

        doc.build(story)
        return file_path
