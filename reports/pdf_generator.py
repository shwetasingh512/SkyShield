import io
from django.utils import timezone

def generate_incident_pdf_report(incident):
    """
    Generates a formal aviation incident dossier PDF using ReportLab if available,
    or returns a formatted PDF buffer.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#0B1E36'),
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#6c757d'),
            spaceAfter=12
        )
        heading2_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor('#1B365D'),
            spaceBefore=10,
            spaceAfter=6
        )
        normal_style = ParagraphStyle(
            'BodyTextCustom',
            parent=styles['Normal'],
            fontSize=9,
            leading=13
        )
        bold_style = ParagraphStyle(
            'BoldLabel',
            parent=styles['Normal'],
            fontSize=9,
            leading=13,
            fontName='Helvetica-Bold'
        )

        elements = []

        # Header Banner
        elements.append(Paragraph("SkyShield Aviation Safety Management System", title_style))
        elements.append(Paragraph(
            f"OFFICIAL INCIDENT DOSSIER & RISK EVALUATION REPORT &bull; Ref: {incident.reference_number}",
            subtitle_style
        ))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1B365D'), spaceAfter=10))

        # Notice
        elements.append(Paragraph(
            "<b>NOTICE:</b> Internal Safety & Regulatory Compliance Supporting Record. Educational & Demonstration Portfolio System.",
            ParagraphStyle('Notice', parent=normal_style, fontSize=8, textColor=colors.HexColor('#dc3545'), spaceAfter=10)
        ))

        # Section 1: Core Metadata
        elements.append(Paragraph("1. Incident Identification & Operational Metadata", heading2_style))
        meta_data = [
            [Paragraph("<b>Reference Number:</b>", normal_style), incident.reference_number,
             Paragraph("<b>Status:</b>", normal_style), incident.get_status_display()],
            [Paragraph("<b>Incident Title:</b>", normal_style), incident.title,
             Paragraph("<b>Category:</b>", normal_style), incident.get_incident_type_display()],
            [Paragraph("<b>Occurrence Date/Time:</b>", normal_style), incident.occurrence_date.strftime('%Y-%m-%d %H:%M UTC'),
             Paragraph("<b>Reported Date:</b>", normal_style), incident.reported_at.strftime('%Y-%m-%d %H:%M UTC')],
            [Paragraph("<b>Location / Facility:</b>", normal_style), incident.location,
             Paragraph("<b>Flight / Tail Number:</b>", normal_style), f"{incident.flight_number or 'N/A'} / {incident.aircraft_registration or 'N/A'}"],
            [Paragraph("<b>Reporter:</b>", normal_style), incident.reporter.get_full_name() or incident.reporter.username,
             Paragraph("<b>Assigned Investigator:</b>", normal_style), incident.assigned_investigator.get_full_name() if incident.assigned_investigator else "Unassigned"],
        ]
        t1 = Table(meta_data, colWidths=[120, 160, 120, 140])
        t1.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t1)
        elements.append(Spacer(1, 10))

        # Section 2: Risk Assessment
        elements.append(Paragraph("2. Safety Risk Assessment Matrix", heading2_style))
        risk_data = [
            [Paragraph("<b>Calculated Risk Score:</b>", normal_style), f"{incident.risk_score} / 25",
             Paragraph("<b>Risk Band Classification:</b>", normal_style), incident.risk_level],
            [Paragraph("<b>Initial Likelihood Rating:</b>", normal_style), incident.get_initial_likelihood_display(),
             Paragraph("<b>Initial Severity Rating:</b>", normal_style), incident.get_initial_severity_display()]
        ]
        t2 = Table(risk_data, colWidths=[140, 140, 140, 120])
        risk_bg = colors.HexColor('#d1e7dd') if incident.risk_level == 'LOW' else (
            colors.HexColor('#fff3cd') if incident.risk_level == 'MODERATE' else colors.HexColor('#f8d7da')
        )
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), risk_bg),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#b6d4fe')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t2)
        elements.append(Spacer(1, 10))

        # Section 3: Narrative & Immediate Response
        elements.append(Paragraph("3. Occurrence Narrative & Consequences", heading2_style))
        desc_para = Paragraph(f"<b>Narrative Description:</b><br/>{incident.description.replace(chr(10), '<br/>')}", normal_style)
        actions_para = Paragraph(f"<b>Immediate Actions Taken:</b><br/>{incident.immediate_actions_taken or 'None specified'}", normal_style)
        actual_para = Paragraph(f"<b>Actual Consequences:</b><br/>{incident.actual_consequences or 'None specified'}", normal_style)
        potential_para = Paragraph(f"<b>Potential Consequences:</b><br/>{incident.potential_consequences or 'None specified'}", normal_style)

        t3 = Table([[desc_para], [actions_para], [actual_para], [potential_para]], colWidths=[540])
        t3.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ffffff')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#e9ecef')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(t3)
        elements.append(Spacer(1, 10))

        # Section 4: Investigation & 5-Whys
        if hasattr(incident, 'investigation'):
            inv = incident.investigation
            elements.append(Paragraph("4. Formal Safety Investigation Findings", heading2_style))
            inv_data = [
                [Paragraph("<b>Investigation Status:</b>", normal_style), inv.get_status_display(),
                 Paragraph("<b>Lead Investigator:</b>", normal_style), inv.investigator.get_full_name() or inv.investigator.username],
                [Paragraph("<b>Start Date:</b>", normal_style), str(inv.start_date),
                 Paragraph("<b>Completion Date:</b>", normal_style), str(inv.completion_date or 'Underway')],
            ]
            t_inv = Table(inv_data, colWidths=[130, 150, 130, 130])
            t_inv.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                ('PADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t_inv)

            if inv.findings:
                elements.append(Paragraph(f"<b>Investigative Findings:</b><br/>{inv.findings.replace(chr(10), '<br/>')}", normal_style))
                elements.append(Spacer(1, 6))

            # 5 Whys RCA
            if hasattr(inv, 'root_cause_analysis'):
                rca = inv.root_cause_analysis
                elements.append(Paragraph("Structured 5-Whys Root Cause Analysis (RCA):", bold_style))
                rca_table = [
                    [Paragraph("<b>Problem Statement:</b>", normal_style), Paragraph(rca.problem_statement, normal_style)],
                    [Paragraph("<b>Why #1:</b>", normal_style), Paragraph(rca.why_1, normal_style)],
                    [Paragraph("<b>Why #2:</b>", normal_style), Paragraph(rca.why_2, normal_style)],
                    [Paragraph("<b>Why #3:</b>", normal_style), Paragraph(rca.why_3, normal_style)],
                    [Paragraph("<b>Why #4:</b>", normal_style), Paragraph(rca.why_4, normal_style)],
                    [Paragraph("<b>Why #5:</b>", normal_style), Paragraph(rca.why_5, normal_style)],
                    [Paragraph("<b>Systemic Root Cause:</b>", normal_style), Paragraph(rca.root_cause_summary, normal_style)],
                    [Paragraph("<b>Preventive Recommendation:</b>", normal_style), Paragraph(rca.preventive_recommendation, normal_style)],
                ]
                t_rca = Table(rca_table, colWidths=[140, 400])
                t_rca.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fcfcfd')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ced4da')),
                    ('PADDING', (0, 0), (-1, -1), 4),
                ]))
                elements.append(t_rca)
                elements.append(Spacer(1, 10))

        # Section 5: Corrective Actions (CAPA)
        capas = incident.corrective_actions.all()
        elements.append(Paragraph(f"5. Corrective & Preventive Action Register ({capas.count()} Actions)", heading2_style))
        if capas.exists():
            capa_rows = [[
                Paragraph("<b>Action Title</b>", normal_style),
                Paragraph("<b>Assignee</b>", normal_style),
                Paragraph("<b>Priority</b>", normal_style),
                Paragraph("<b>Due Date</b>", normal_style),
                Paragraph("<b>Status</b>", normal_style),
            ]]
            for c in capas:
                capa_rows.append([
                    Paragraph(c.title, normal_style),
                    Paragraph(c.responsible_user.username, normal_style),
                    Paragraph(c.get_priority_display(), normal_style),
                    Paragraph(str(c.due_date), normal_style),
                    Paragraph(c.get_status_display(), normal_style),
                ])
            t_capa = Table(capa_rows, colWidths=[180, 90, 90, 80, 100])
            t_capa.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1B365D')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                ('PADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t_capa)
        else:
            elements.append(Paragraph("<i>No corrective actions logged for this occurrence.</i>", normal_style))

        elements.append(Spacer(1, 14))
        # Footer
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#6c757d'), spaceAfter=6))
        elements.append(Paragraph(
            f"Generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')} &bull; SkyShield Safety Management &bull; Page 1",
            ParagraphStyle('Footer', parent=normal_style, fontSize=8, alignment=1, textColor=colors.HexColor('#6c757d'))
        ))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    except ImportError:
        # Fallback pure-python basic PDF generator if reportlab is not yet installed
        return _generate_fallback_pdf(incident)

def _generate_fallback_pdf(incident):
    """Fallback plain text formatted byte stream when ReportLab is not available."""
    content = (
        f"%PDF-1.4\n"
        f"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        f"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        f"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        f"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        f"4 0 obj << /Length 400 >> stream\n"
        f"BT\n/F1 16 Tf\n50 720 Td\n(SkyShield Aviation Safety Report - Ref: {incident.reference_number}) Tj\n"
        f"/F1 12 Tf\n0 -30 Td\n(Title: {incident.title[:50]}) Tj\n"
        f"0 -20 Td\n(Category: {incident.get_incident_type_display()}) Tj\n"
        f"0 -20 Td\n(Status: {incident.get_status_display()}) Tj\n"
        f"0 -20 Td\n(Risk Level: {incident.risk_level} - Score: {incident.risk_score}) Tj\n"
        f"0 -20 Td\n(Location: {incident.location}) Tj\n"
        f"0 -20 Td\n(Occurrence Date: {incident.occurrence_date}) Tj\n"
        f"0 -30 Td\n(Generated via SkyShield Safety Management Engine) Tj\n"
        f"ET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000280 00000 n\n0000000220 00000 n\ntrailer << /Size 6 /Root 1 0 R >>\nstartxref\n750\n%%EOF\n"
    )
    return content.encode('latin1')
