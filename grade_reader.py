import pandas as pd
import os
import json

def get_grade_data() -> pd.DataFrame:
    """
    Loads the EOY_Grade_levels.json file, processes it from its nested
    JSON structure into a single, tidy Pandas DataFrame, and returns it.

    This function is the single source of truth for all grade-level and
    percentile data in the application.

    The resulting DataFrame has columns:
    - Subject
    - Percentile
    - Grade
    - Score
    """
    file_path = os.path.join("assets", "EOY_Grade_levels.json")
    
    try:
        with open(file_path, 'r') as f:
            eoy_data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"The file {file_path} was not found.")
    except json.JSONDecodeError:
        raise ValueError(f"Could not decode JSON from {file_path}.")

    all_subject_data = []
    
    # The JSON is a list of tables (subjects)
    for subject_table in eoy_data:
        #get title from json. if not available, populate unknown subject
        subject_title = subject_table.get('title', 'Unknown Subject')
        
        # The 'data' key contains a list of dictionaries (rows)
        if 'data' in subject_table and subject_table['data']:
            # Create a DataFrame for the current subject
            temp_df = pd.DataFrame(subject_table['data'])
            
            # Use melt to transform from wide format to long format
            # 'Percentile' is the identifier, other columns are the grades
            melted_df = temp_df.melt(
                id_vars=['Percentile'],
                var_name='Grade',
                value_name='Score'
            )
            
            # Add the subject title to the melted DataFrame
            melted_df['Subject'] = subject_title
            
            all_subject_data.append(melted_df)

    if not all_subject_data:
        raise ValueError("JSON data is empty or in an unexpected format.")

    # Combine all the individual subject DataFrames into one master DataFrame
    combined_df = pd.concat(all_subject_data, ignore_index=True)

    # Clean up data types
    combined_df['Percentile'] = combined_df['Percentile'].astype(int)
    combined_df['Grade'] = combined_df['Grade'].astype(str)
    combined_df['Score'] = pd.to_numeric(combined_df['Score'], errors='coerce').fillna(0).astype(int)
    # print (combined_df)
    return combined_df

