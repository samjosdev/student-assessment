from langchain.tools import StructuredTool
import re
from pydantic import BaseModel, Field
import pandas as pd
from grade_reader import get_grade_data
import traceback


class PercentileCalculationTool(BaseModel):
    subject: str = Field(description="The subject name (e.g., 'Math', 'Language Arts')")
    student_score: int = Field(description="The student's score")
    current_grade: str = Field(description="The student's current grade level (e.g., 'K', '1', '12')")

class PerformingGradeCalculationTool(BaseModel):
    subject: str = Field(description="The subject name (e.g., 'Math', 'Language Arts')")
    student_score: int = Field(description="The student's score")
    current_grade: str = Field(description="The student's current grade level")

#Sanitize tool names to avoid errors
def sanitize_tool_name(tool):
    tool.name = re.sub(r"[^a-zA-Z0-9_]", "_", tool.name)
    return tool


def calculate_percentile(subject: str, student_score: int, current_grade: str) -> str:
    """Calculates the exact percentile for a given score, subject, and grade.
    
    Args:
        subject: The official subject name from the benchmark data (e.g., 'End-of-Year Math: Overall (K-8)').
        student_score: The student's numerical score in the specified subject.
        current_grade: The student's current grade level as a string (e.g., '4').
        
    Returns:
        A string representing the calculated percentile (e.g., "75th percentile").
    """
    try:
        grade_df = get_grade_data()
        
        # Robust filtering by converting both sides to string
        subject_grade_data = grade_df[
            (grade_df['Subject'] == subject) & 
            (grade_df['Grade'].astype(str) == str(current_grade))
        ]

        if subject_grade_data.empty:
            return f"No data found for Subject '{subject}' and Grade '{current_grade}'"
        
        # Find all percentiles where the student's score is >= the benchmark score
        qualifying_percentiles = subject_grade_data[subject_grade_data['Score'] <= student_score]

        if qualifying_percentiles.empty:
            return "0th percentile" # Score is below the lowest benchmark

        # The highest percentile the student has achieved
        # Ensure the 'Percentile' column is numeric before finding the max
        highest_percentile = pd.to_numeric(qualifying_percentiles['Percentile']).max()
        
        return f"{highest_percentile}th percentile"
        
    except Exception as e:
        return f"Error calculating percentile: {str(e)}"

def calculate_performing_grade(subject: str, student_score: int, current_grade: str) -> str:
    """Calculates the highest grade level at which the student is performing.

    This is determined by finding the highest grade where the student's score
    meets or exceeds the 85th percentile benchmark for that grade.
    
    Args:
        subject: The official subject name from the benchmark data.
        student_score: The student's numerical score in the specified subject.
        current_grade: The student's current grade level as a string.
        
    Returns:
        A string representing the student's performing grade level (e.g., '5th Grade').
    """
    try:
        grade_df = get_grade_data()
        
        # Filter for the specific subject and the 85th percentile benchmark
        # Use .copy() to avoid the SettingWithCopyWarning
        benchmark_data = grade_df[
            (grade_df['Subject'] == subject) & 
            (grade_df['Percentile'] == 85)
        ].copy()

        if benchmark_data.empty:
            return f"No 85th percentile data found for Subject '{subject}'"

        # Ensure grade column is string before sorting
        benchmark_data['Grade'] = benchmark_data['Grade'].astype(str)
        
        # Sort grades in the correct order (K, 1, 2, ..., 12)
        grade_order = ['K'] + [str(i) for i in range(1, 13)]
        benchmark_data['Grade'] = pd.Categorical(benchmark_data['Grade'], categories=grade_order, ordered=True)
        benchmark_data = benchmark_data.sort_values('Grade')
        
        # Find the highest grade where the student's score meets or exceeds the benchmark
        performing_grade = current_grade # Default to current grade
        for _, row in benchmark_data.iterrows():
            if not pd.isna(row['Score']) and student_score >= row['Score']:
                performing_grade = row['Grade']
            else:
                # Since the grades are sorted, we can stop once the score is too low
                break
        
        return performing_grade
        
    except Exception as e:
        return f"Error calculating performing grade: {str(e)}"

def calculate_next_grade_threshold(subject: str, current_grade: str) -> str:
    """Calculates the minimum score needed to be considered 'on track' for the next grade level.

    This is defined as the 70th percentile score for the student's *current* grade.

    Args:
        subject: The official subject name from the benchmark data.
        current_grade: The student's current grade level as a string.

    Returns:
        A string representing the numerical score required to reach the next grade threshold.
    """
    try:
        benchmark_data = get_grade_data()
        
        # Robust filtering by converting both sides to string
        grade_data = benchmark_data[
            (benchmark_data['Subject'] == subject) & 
            (benchmark_data['Grade'].astype(str) == str(current_grade))
        ]
        
        if grade_data.empty:
            return f"Error: No benchmark data found for {subject} in grade {current_grade}"
        
        # Get the 70th percentile score for the current grade
        threshold_data = grade_data[grade_data['Percentile'] == 70]
        
        if threshold_data.empty:
            # If 70th percentile is missing, it's a data gap.
            return "N/A (No 70th percentile benchmark for this grade)"
        
        next_grade_threshold = threshold_data['Score'].iloc[0]
        
        return str(next_grade_threshold)
        
    except Exception as e:
        traceback.print_exc()
        return f"Error calculating next grade threshold: {str(e)}"

async def other_tools():
    
    # Add new calculation tools
    percentile_tool = StructuredTool(
        name="calculate_percentile",
        func=calculate_percentile,
        description="Calculate the exact percentile for a student's score using the master grade data DataFrame. Returns the highest percentile where student_score >= that percentile's benchmark.",
        args_schema=PercentileCalculationTool
    )
    
    performing_grade_tool = StructuredTool(
        name="calculate_performing_grade", 
        func=calculate_performing_grade,
        description="Calculate the highest performing grade level using the 85th percentile threshold from the master grade data. Returns the highest grade where student_score >= 85th percentile of that grade's benchmark.",
        args_schema=PerformingGradeCalculationTool
    )
    
    all_tools = [percentile_tool, performing_grade_tool]
    return [sanitize_tool_name(tool) for tool in all_tools]