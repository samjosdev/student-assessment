ASSESSMENT_PROMPT = """
You are an expert student assessment analyst. Create a clear, professional assessment report using the following structure.
**Formatting Note:** When you list subject names, remove the "End-of-Year " prefix and the " (K-8)" suffix. For example, "End-of-Year Math: Overall (K-8)" should be displayed as "Math: Overall".

<p style="font-weight: normal; font-size: 1.1em;"><strong>Student:</strong> {student_name} &nbsp;&nbsp; <strong>Grade:</strong> {grade} &nbsp;&nbsp; <strong>Date:</strong> June 20, 2025</p>
<hr>

<h2>⭐ Key Findings</h2>
<ul>
  <li>🟢 <strong>Above Grade Level:</strong> [List subjects where performing_grade > student_grade]</li>
  <li>🟡 <strong>On Grade Level:</strong> [List subjects where performing_grade = student_grade]</li>
  <li>🔴 <strong>Below Grade Level:</strong> [List subjects where performing_grade < student_grade]</li>
</ul>
<hr>

<h2>1. Overview</h2>
[Write 2-3 sentences summarizing {student_name}'s overall performance based on the data, highlighting strengths and areas for growth. Mention the student's current grade is {grade}.]
<hr>

<h2>2. Current Performing Grade</h2>
Current Performing Grade: [Grade Level from calculate_performing_grade tool]
<hr>

<h2>3. Performance Dashboard</h2>
You MUST generate an HTML table for the dashboard. Do not use markdown. For the "Performance Band" column, apply the background color directly to the table cell (`<td>`).

Here is the required HTML structure:
```html
<table>
  <thead>
    <tr>
      <th style="white-space: nowrap;">Subject</th>
      <th style="white-space: nowrap;">Score</th>
      <th style="white-space: nowrap;">Performance Band</th>
      <th style="white-space: nowrap;">Percentile</th>
      <th style="white-space: nowrap;">Next Grade Threshold</th>
      <th style="white-space: nowrap;">Performing Grade</th>
      <th style="white-space: nowrap;">Recommended Skills</th>
    </tr>
  </thead>
  <tbody>
    <!-- Generate a <tr> for each subject here. Example: -->
    <!-- 
    <tr>
      <td>Math: Overall</td>
      <td>850</td>
      <td style="background-color: #C8E6C9;">Above Grade Level</td>
      <td>99th 🎉</td>
      <td>290</td>
      <td>7</td>
      <td>Continue advanced work</td>
    </tr>
    -->
  </tbody>
</table>
```

**IMPORTANT CALCULATION REQUIREMENTS:**
- **CRITICAL: You MUST call `calculate_percentile` for each subject to get accurate percentile rankings. Do NOT estimate or guess percentiles - use the tool!**
- Use the `calculate_performing_grade` tool for each subject to get accurate performing grade levels.
- Use the `calculate_next_grade_threshold` tool for each subject to get the minimum score needed for the next grade level.
- Do NOT calculate percentiles, grade levels, or thresholds manually - always use the tools.
- **For the "Performance Band" `<td>` cell:** Use these background colors:
  - **Above Grade Level:** `#C8E6C9`
  - **On Grade Level:** `#FFF9C4`
  - **Below Grade Level:** `#FFCDD2`
- **For Recommended Skills column:** 
  - If specific skills were extracted from the PDF parser, format them as: `<small>• [Skill 1]<br>• [Skill 2]</small>`
  - If no skills were found, provide a general statement based on percentile:
    - 90-100th: "Continue advanced work"
    - 80-89th: "Focus on mastery of current concepts"
    - 70-79th: "Practice current grade skills"
    - 60-69th: "Review foundational concepts"
    - 50-59th: "Build basic skills"
    - Below 50th: "Start with fundamental concepts"
<hr>

<h2>4. Summary</h2>
<ul>
  <li><strong>Key Strengths:</strong> [Highlight key strengths and areas for improvement]</li>
  <li><strong>Areas for Improvement:</strong> [Provide overall readiness assessment for next grade]</li>
  <li><strong>Overall Readiness Assessment for Next Grade:</strong> [Provide an overall readiness assessment for the next grade]</li>
</ul>
<hr>

<h2>5. Methodology</h2>
<small>
Performance bands and percentiles are based on end-of-year benchmarks and national grade-level data from IXL's National Norms. 
Advanced scores use the next grade's data for percentile calculation.
(newline) <strong>Data Source:</strong> IXL's ELO score rating system <a href="https://www.ixl.com/materials/us/research/National_Norms_for_IXL_s_Diagnostic_in_Grades_K-12.pdf" target="_blank" rel="noopener noreferrer">National Norms for IXL's Diagnostic in Grades K-12</a>.
</small>

---

**Student Information:**
- Grade: {grade}
- Subject Scores: {subjects_json}

**Percentile Rankings:**
- 🎉 90-100th: Outstanding!
- ⭐ 80-89th: Excellent!
- 🏆 70-79th: Great job!
- 👍 60-69th: Good work!
- 📈 50-59th: On track!
- 💪 40-49th: Keep going!
- 📚 30-39th: More practice needed
- 🔧 20-29th: Needs support
- 💡 10-19th: Let's work on this
- 🌱 1-9th: Starting fresh

**CRITICAL: Always use the calculation tools for accurate results. Do not attempt manual calculations.**
"""

SYNTHESIS_PROMPT = """
Great, thank you. Now that you have all the necessary information,
including the results from the tools you called, please synthesize
everything into a comprehensive student assessment report.

Make sure to address all the sections outlined in the initial prompt,
including the Next Grade Threshold column in the performance dashboard.
This is the final step, so provide the full report now using the data
you already have from the previous tool calls.
"""

EXTRACTION_PROMPT = """
You are an expert at extracting student assessment data from IXL Diagnostic Reports.

Please extract all subject, score, and recommended skills from the following text.
- Subject names (e.g., "Math", "Language Arts", "Reading", "Writing", "Science", etc.)
- Corresponding scores (usually numbers next to the subject or on a scale)
- Recommended skills, which are often listed below a subject with a special icon or heading. Capture the full text of each recommended skill.

The user has already provided the grade separately, so focus only on finding the subjects, their scores, and any associated recommendations.

Text from PDF:
{parsed_text}

IMPORTANT: You must respond with ONLY a valid JSON object in this exact format:
{{
  "subjects": [
    {{
      "subject": "Subject Name",
      "score": score_number,
      "recommended_skills": [
        "First recommended skill",
        "Second recommended skill"
      ]
    }},
    {{
      "subject": "Another Subject",
      "score": score_number,
      "recommended_skills": []
    }}
  ]
}}

If a subject has no recommended skills, return an empty list for "recommended_skills".
Do not include any other text, explanations, or formatting. Return ONLY the JSON object.
"""

SUBJECT_MAPPING_PROMPT = """
You are an expert at mapping slightly different subject names to their official versions.
Your task is to match each "raw subject" from a student's report to the correct "official subject" from the provided list.

Here are the raw subjects extracted from the report:
{raw_subjects}

Here is the list of official subject names you must map to:
{official_subjects}

Please provide a definitive mapping for every raw subject.
The `official_subject` you choose MUST be an exact match from the official list.

IMPORTANT: You must respond with ONLY a valid JSON object in this exact format. Do not include any other text or explanations.

{{
  "mappings": [
    {{
      "raw_subject": "The subject name from the report",
      "official_subject": "The matching subject name from the official list"
    }},
    {{
      "raw_subject": "Another subject name from the report",
      "official_subject": "Its corresponding official name"
    }}
  ]
}}
"""