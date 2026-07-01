import io
import pandas as pd
from typing import Dict, Any, List
from loguru import logger

# Import ReportLab elements safely
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab is not installed or available. PDF report generation will fallback to simple text.")

def generate_pdf_report(match_report: Dict[str, Any]) -> bytes:
    """
    Generates a beautifully styled, professional PDF evaluation report for a candidate.
    Returns the PDF as raw bytes.
    """
    if not REPORTLAB_AVAILABLE:
        # Fallback text representation as bytes
        fallback_text = (
            f"EVALUATION REPORT: {match_report.get('candidate', {}).get('candidate_info', {}).get('name', 'N/A')}\n"
            f"ATS Score: {match_report.get('ats_score', 0)}/100\n"
            f"Eligibility: {match_report.get('eligibility', 'N/A')}\n"
            f"Semantic Match: {match_report.get('semantic_score', 0)}%\n"
            f"Skill Match: {match_report.get('skill_match', 0)}%\n"
            f"Experience Match: {match_report.get('experience_match', 0)}%\n"
        )
        return fallback_text.encode('utf-8')
        
    buffer = io.BytesIO()
    
    # Establish document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom color palette (sleek slate blue design)
    PRIMARY_COLOR = colors.HexColor("#1A365D")  # Deep Blue
    SECONDARY_COLOR = colors.HexColor("#2B6CB0") # Medium Blue
    TEXT_DARK = colors.HexColor("#2D3748")      # Charcoal
    LIGHT_BG = colors.HexColor("#EDF2F7")       # Light grey
    SUCCESS_COLOR = colors.HexColor("#48BB78")   # Green
    WARNING_COLOR = colors.HexColor("#ECC94B")   # Yellow
    DANGER_COLOR = colors.HexColor("#F56565")    # Red
    
    # Define custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=PRIMARY_COLOR,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=SECONDARY_COLOR,
        spaceAfter=25
    )
    
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=PRIMARY_COLOR,
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=TEXT_DARK,
        spaceAfter=8
    )
    
    bold_body_style = ParagraphStyle(
        'BoldBodyTextCustom',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    # 1. Document Header
    cand_info = match_report.get("candidate", {}).get("candidate_info", {})
    cand_name = cand_info.get("name") or "Unnamed Candidate"
    job_info = match_report.get("job", {})
    job_title = job_info.get("title") or "Target Role"
    
    story.append(Paragraph(f"Resume Intelligence Report", title_style))
    story.append(Paragraph(f"Candidate: {cand_name} | Target Role: {job_title}", subtitle_style))
    story.append(Spacer(1, 10))
    
    # 2. Score Summary Card (Table)
    ats_score = match_report.get("ats_score", 0)
    semantic_score = match_report.get("semantic_score", 0)
    skill_match = match_report.get("skill_match", 0)
    experience_match = match_report.get("experience_match", 0)
    education_match = match_report.get("education_match", 0)
    
    eligibility = match_report.get("eligibility", "Not Evaluated")
    eligibility_color = SUCCESS_COLOR
    if eligibility == "Partially Eligible":
        eligibility_color = WARNING_COLOR
    elif eligibility == "Not Eligible":
        eligibility_color = DANGER_COLOR
        
    score_data = [
        [
            Paragraph("<b>Overall ATS Score</b>", bold_body_style),
            Paragraph("<b>Semantic Match</b>", bold_body_style),
            Paragraph("<b>Skill Match</b>", bold_body_style),
            Paragraph("<b>Eligibility</b>", bold_body_style)
        ],
        [
            Paragraph(f"<font size=16 color='{PRIMARY_COLOR.hexval()}'><b>{ats_score}/100</b></font>", body_style),
            Paragraph(f"<font size=14><b>{semantic_score}%</b></font>", body_style),
            Paragraph(f"<font size=14><b>{skill_match}%</b></font>", body_style),
            Paragraph(f"<font size=14 color='{eligibility_color.hexval()}'><b>{eligibility}</b></font>", body_style)
        ]
    ]
    
    score_table = Table(score_data, colWidths=[1.8*inch, 1.8*inch, 1.8*inch, 1.8*inch])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), LIGHT_BG),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 12),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E0")),
        ('BOTTOMPADDING', (0,1), (-1,1), 16),
    ]))
    
    story.append(score_table)
    story.append(Spacer(1, 20))
    
    # 3. Contact & Context Info
    story.append(Paragraph("Candidate Information", h2_style))
    contact_data = [
        [Paragraph("<b>Email:</b>", bold_body_style), Paragraph(cand_info.get("email") or "N/A", body_style),
         Paragraph("<b>Phone:</b>", bold_body_style), Paragraph(cand_info.get("phone") or "N/A", body_style)],
        [Paragraph("<b>Location:</b>", bold_body_style), Paragraph(cand_info.get("location") or "N/A", body_style),
         Paragraph("<b>Experience:</b>", bold_body_style), Paragraph(f"{cand_info.get('total_experience_years') or 0} Years", body_style)],
        [Paragraph("<b>LinkedIn:</b>", bold_body_style), Paragraph(cand_info.get("linkedin") or "N/A", body_style),
         Paragraph("<b>GitHub:</b>", bold_body_style), Paragraph(cand_info.get("github") or "N/A", body_style)]
    ]
    contact_table = Table(contact_data, colWidths=[1*inch, 2.4*inch, 1.2*inch, 2.6*inch])
    contact_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(contact_table)
    story.append(Spacer(1, 15))
    
    # 4. Eligibility Reasons
    story.append(Paragraph("Eligibility Assessment", h2_style))
    reasons = match_report.get("eligibility_reasons", [])
    for r in reasons:
        story.append(Paragraph(f"• {r}", body_style))
    story.append(Spacer(1, 15))
    
    # 5. Missing Skills Gap
    story.append(Paragraph("Key Missing Skills", h2_style))
    missing_skills = match_report.get("missing_skills", [])
    if missing_skills:
        # Flow wrap them in blocks of 4
        chunks = [missing_skills[i:i+4] for i in range(0, len(missing_skills), 4)]
        skill_table_data = [[Paragraph(s, body_style) for s in chunk] for chunk in chunks]
        # Pad the last row if uneven
        if skill_table_data and len(skill_table_data[-1]) < 4:
            skill_table_data[-1].extend([Paragraph("", body_style)] * (4 - len(skill_table_data[-1])))
            
        skill_table = Table(skill_table_data, colWidths=[1.8*inch]*4)
        skill_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFF5F5")), # slight red warning background
            ('PADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#FED7D7")),
        ]))
        story.append(skill_table)
    else:
        story.append(Paragraph("No major required skills are missing. Great fit!", body_style))
    story.append(Spacer(1, 15))
    
    # 6. Priority Recommendations
    story.append(Paragraph("Top Recommendations for Resume Improvement", h2_style))
    recommendations = match_report.get("recommendations", [])
    if recommendations:
        rec_data = [[Paragraph("<b>Priority</b>", bold_body_style), Paragraph("<b>Recommendation</b>", bold_body_style), Paragraph("<b>Section</b>", bold_body_style)]]
        
        # Sort recommendations: High first
        sorted_recs = sorted(recommendations, key=lambda x: {"High": 0, "Medium": 1, "Low": 2}.get(x.get("priority", "Low"), 3))
        
        for item in sorted_recs[:10]:  # limit to top 10 for space
            priority = item.get("priority", "Low")
            p_color = DANGER_COLOR.hexval() if priority == "High" else (WARNING_COLOR.hexval() if priority == "Medium" else PRIMARY_COLOR.hexval())
            rec_data.append([
                Paragraph(f"<font color='{p_color}'><b>{priority}</b></font>", body_style),
                Paragraph(item.get("recommendation", "N/A"), body_style),
                Paragraph(item.get("section", "General"), body_style)
            ])
            
        rec_table = Table(rec_data, colWidths=[1.0*inch, 4.8*inch, 1.4*inch])
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), LIGHT_BG),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('PADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ]))
        story.append(rec_table)
    else:
        story.append(Paragraph("No improvements suggested. The resume layout and content look optimal.", body_style))
        
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def export_candidates_to_excel(candidates_reports: List[Dict[str, Any]]) -> bytes:
    """
    Exports summary statistics of parsed resumes and matching scores to a downloadable Excel workbook.
    """
    rows = []
    for report in candidates_reports:
        cand = report.get("candidate", {})
        cand_info = cand.get("candidate_info", {})
        job = report.get("job", {})
        
        row = {
            "Candidate Name": cand_info.get("name") or "N/A",
            "Email": cand_info.get("email") or "N/A",
            "Phone": cand_info.get("phone") or "N/A",
            "Location": cand_info.get("location") or "N/A",
            "Target Job Title": job.get("title") or "N/A",
            "ATS Score": report.get("ats_score", 0),
            "Semantic Match %": report.get("semantic_score", 0),
            "Skill Match %": report.get("skill_match", 0),
            "Experience Match %": report.get("experience_match", 0),
            "Education Match %": report.get("education_match", 0),
            "Keyword Match %": report.get("keyword_match", 0),
            "Eligibility": report.get("eligibility", "N/A"),
            "Total Experience (Years)": cand_info.get("total_experience_years") or 0,
            "Current Company": cand_info.get("current_company") or "N/A",
            "Current Role": cand_info.get("current_role") or "N/A"
        }
        rows.append(row)
        
    df = pd.DataFrame(rows)
    
    # Save to buffer
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='ATS Match Results', index=False)
        
        # Access openpyxl workbook to adjust column widths
        workbook = writer.book
        worksheet = writer.sheets['ATS Match Results']
        
        # Auto-adjust column width based on length of content
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)
            
    output.seek(0)
    return output.getvalue()
