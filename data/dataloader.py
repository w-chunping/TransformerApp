import pandas as pd

def extract_sections(df_raw: pd.DataFrame):

    section_indices = df_raw[df_raw[0].astype(str).str.contains("TYPE")].index.tolist() # find the indices where cells contain "TYPE"
    # Extract the columns. The last three columns contain info only at the next row.
    header_row = df_raw.iloc[section_indices[0]]
    next_row = df_raw.iloc[section_indices[0] + 1]
    override_count = 0
    columns = [
        str(next_row[i]).strip() if i >= len(header_row) - override_count
        else str(header_row[i]).strip() if pd.notna(header_row[i]) else ''
        for i in range(len(header_row))
    ]
    # print(columns)

    sections = []
    # Loop through each section
    for i in range(len(section_indices)):
        start = section_indices[i]
        end = section_indices[i+1] if i+1 < len(section_indices) else len(df_raw) 
        section_data = df_raw.iloc[start:end].reset_index(drop=True)
        section_data = section_data.dropna(how='all') # remove rows that are all NaN (optional)
        if section_data.empty or len(section_data) < 2: # skip if no data
           continue
        # Apply the columns and omit the TYPE row
        section_data.columns = columns
        section_data = section_data[1:].reset_index(drop=True)

        # Add section label (like EC, EE, etc.)
        section_name = df_raw.iloc[section_indices[i], 0]
        section_data['Section'] = section_name

        sections.append(section_data)

    df_cleaned = pd.concat(sections, ignore_index=True) # combine all sections
    return df_cleaned[1:]

'''
def load_cores(file_path: str):
    df_raw = load_excel_file(filepath=file_path)
    df_clean = extract_sections(df_raw=df_raw)
    cores = []
    for _, row in df_clean.iterrows():
        try:
            core = Core(
                core_area = row.get('Ae') * 1e-6,
                al_value = row.get('AL') * 1e-9,
                window_area = row.get('Aw') * 1e-6,
                winding_width = row.get('幅寬') * 1e-3,
                name = row.get('TYPE'),
                core_type = row.get('Section')
            )
            cores.append(core)
        except Exception as e:
            print("Skipping row due to error: {e}")
'''