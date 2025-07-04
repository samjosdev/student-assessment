def format_sections_to_report(report, student_name: str, grade: str, date: str) -> str:
    """Combines the structured sections into a complete formatted report."""
    
    # Generate dashboard HTML directly from structured data
    dashboard_html = """
    <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-family: Arial, sans-serif;">
        <thead>
            <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Subject</th>
                <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">Score</th>
                <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">Performing Grade</th>
                <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">Percentile</th>
                <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">Next Grade Threshold</th>
                <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Recommended Skills</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for row in report.performance_dashboard.table_rows:
        # Calculate color based on performing_grade vs student grade
        try:
            # Convert student grade to number (handle K as 0)
            student_grade_num = 0 if grade.upper() == 'K' else int(grade)
            # Extract performing grade number from the performing_grade text
            import re
            pg_text = str(row.performing_grade).lower().strip()
            match = re.search(r'(\d+)(?:st|nd|rd|th)?\s*grade', pg_text)
            if match:
                performing_grade_num = int(match.group(1))
            elif pg_text.isdigit():
                performing_grade_num = int(pg_text)
            elif 'k' in pg_text:
                performing_grade_num = 0
            else:
                performing_grade_num = student_grade_num  # fallback
            # Determine color
            if performing_grade_num > student_grade_num:
                band_color = "#C8E6C9"  # Green
            elif performing_grade_num == student_grade_num:
                band_color = "#FFF9C4"  # Yellow
            else:
                band_color = "#FFCDD2"  # Red
        except Exception:
            band_color = "#C8E6C9"  # fallback
        # Format recommended skills
        skills_html = ""
        if row.recommended_skills:
            skills_html = "<ul style='margin: 0; padding-left: 20px;'>"
            for skill in row.recommended_skills:
                skills_html += f"<li style='margin: 2px 0;'>{skill}</li>"
            skills_html += "</ul>"
        else:
            skills_html = "<em>No specific recommendations</em>"
        dashboard_html += f"""
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">{row.subject_name}</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: center; font-weight: bold;">{row.score}</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: center; background-color: {band_color};">{row.performing_grade}</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{row.percentile}</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{row.next_grade_threshold}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{skills_html}</td>
            </tr>
        """
    
    dashboard_html += """
        </tbody>
    </table>
    """

    # Fallbacks for empty sections
    summary_html = report.summary.strip() if getattr(report, 'summary', '').strip() else '<em>No summary provided.</em>'
    methodology_html = report.methodology.strip() if getattr(report, 'methodology', '').strip() else ''
    
    # Ensure your exact citation and PDF link is present in methodology
    ixl_pdf_link = '<a href="https://www.ixl.com/materials/us/research/National_Norms_for_IXL_s_Diagnostic_in_Grades_K-12.pdf" target="_blank" rel="noopener noreferrer">National Norms for IXL\'s Diagnostic in Grades K-12</a>'
    required_citation = (
        "Performance bands and percentiles are based on end-of-year benchmarks and national grade-level data from IXL's National Norms. "
        "Advanced scores use the next grade's data for percentile calculation.<br><br>"
        "<strong>Data Source:</strong> IXL's ELO score rating system "
        f"{ixl_pdf_link}."
    )
    if 'ixl.com/materials/us/research/national_norms_for_ixl_s_diagnostic_in_grades_k-12.pdf' not in methodology_html.lower():
        methodology_html += f"<br><br>{required_citation}"
    
    # Render Key Findings as colored cards with bulleted lists from JSON structure
    import json
    key_findings_html = ''
    try:
        key_findings_data = report.key_findings
        if isinstance(key_findings_data, str):
            key_findings_data = json.loads(key_findings_data) if key_findings_data.strip() else {}
        if key_findings_data:
            group_styles = {
                'above_grade_level': ('Above Grade Level', '#d4edda'),
                'on_grade_level': ('On Grade Level', '#fff3cd'),
                'below_grade_level': ('Below Grade Level', '#f8d7da'),
            }
            for group, (label, color) in group_styles.items():
                subjects = key_findings_data.get(group, [])
                if subjects:
                    key_findings_html += f"""
                    <div style='background: {color}; border-radius: 8px; padding: 16px; margin-bottom: 12px;'>
                        <strong>{label}:</strong>
                        <ul style='margin: 8px 0 0 18px;'>
                            {''.join(f'<li>{s}</li>' for s in subjects)}
                        </ul>
                    </div>
                    """
    except Exception:
        key_findings_html = ''

    # Only render the section if there is content
    key_findings_section = ''
    if key_findings_html.strip():
        key_findings_section = f"""
        <div style="background: #fff; padding: 28px; border-radius: 12px; box-shadow: 0 2px 8px 0 rgba(80, 80, 120, 0.04); margin-bottom: 28px;">
          <h2 style="color: #2c3e50; border-bottom: 2px solid #7ed957; padding-bottom: 10px; font-size: 1.4em; font-weight: 700; margin: 0 0 18px 0;">⭐ Key Findings</h2>
          {key_findings_html}
        </div>
        """

    return f"""
    <div style="background: linear-gradient(135deg, #f8fafc 0%, #e3e9f3 100%); min-height: 100vh; padding: 40px 0;">
      <div style="max-width: 1200px; margin: 0 auto;">
        <div style="background: #fff; border-radius: 18px; box-shadow: 0 4px 24px 0 rgba(80, 80, 120, 0.08); padding: 32px 32px 24px 32px; margin-bottom: 32px;">
          <div style="background: linear-gradient(135deg, #667eea 0%, #7ed957 100%); color: white; padding: 24px; border-radius: 12px; margin-bottom: 28px; box-shadow: 0 2px 8px 0 rgba(80, 80, 120, 0.08);">
            <h1 style="margin: 0; text-align: center; font-size: 2.2em; font-weight: 800; letter-spacing: 0.01em;">📊 Student Assessment Report</h1>
          </div>
          <div style="background: #f8f9fa; padding: 18px; border-radius: 10px; margin-bottom: 28px; display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: 600; font-size: 1.15em;"><strong>Student:</strong> {student_name}</span>
            <span style="font-weight: 600; font-size: 1.15em;"><strong>Grade:</strong> {grade}</span>
            <span style="font-weight: 600; font-size: 1.15em;"><strong>Date:</strong> {date}</span>
          </div>

          <!-- Main sections, all aligned, no extra wrappers -->
          <div style="background: #fff; padding: 28px; border-radius: 12px; box-shadow: 0 2px 8px 0 rgba(80, 80, 120, 0.04); margin-bottom: 28px;">
            {key_findings_section}
          </div>
          <div style="background: #fff; padding: 28px; border-radius: 12px; box-shadow: 0 2px 8px 0 rgba(80, 80, 120, 0.04); margin-bottom: 28px;">
            <h2 style="color: #2c3e50; border-bottom: 2px solid #7ed957; padding-bottom: 10px; font-size: 1.4em; font-weight: 700; margin: 0 0 18px 0;">1. Overview</h2>
            <div style="margin: 0; padding: 0; display: block; white-space: normal; overflow: visible; word-break: break-word;">{report.overview}</div>
          </div>
          <div style="background: #fff; padding: 28px; border-radius: 12px; box-shadow: 0 2px 8px 0 rgba(80, 80, 120, 0.04); margin-bottom: 28px;">
            <h2 style="color: #2c3e50; border-bottom: 2px solid #7ed957; padding-bottom: 10px; font-size: 1.4em; font-weight: 700; margin: 0 0 18px 0;">2. Performance Dashboard</h2>
            {dashboard_html}
          </div>
          <div style="background: #fff; padding: 28px; border-radius: 12px; box-shadow: 0 2px 8px 0 rgba(80, 80, 120, 0.04); margin-bottom: 28px;">
            <h2 style="color: #2c3e50; border-bottom: 2px solid #7ed957; padding-bottom: 10px; font-size: 1.4em; font-weight: 700; margin: 0 0 18px 0;">3. Summary</h2>
            {summary_html}
          </div>
          <div style="background: #f8f9fa; padding: 22px; border-radius: 12px; border-left: 5px solid #7ed957; margin-bottom: 0;">
            <h2 style="color: #2c3e50; border-bottom: 2px solid #6c757d; padding-bottom: 10px; font-size: 1.2em; font-weight: 700; margin: 0 0 18px 0;">4. Methodology</h2>
            <div style="color: #444; line-height: 1.7; font-size: 1.05em;">{methodology_html}</div>
          </div>
        </div>
      </div>
    </div>
    """ 