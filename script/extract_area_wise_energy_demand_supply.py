import os
import pandas as pd

# Function to extract data from a single file
def extract_data_from_file(file_path):
    try:
        # Load the Excel file
        excel_file = pd.ExcelFile(file_path)
        forecast_sheet = excel_file.parse('Forecast', header=None)

        # Locate "Area wise Demand" cell
        matching_cell = forecast_sheet[forecast_sheet.apply(
            lambda row: row.astype(str).str.contains("Area wise Demand", case=False, na=False).any(), axis=1
        )]
        if matching_cell.empty:
            print(f"Skipping file {file_path}: 'Area wise Demand' not found.")
            return None

        matching_cell_index = matching_cell.index[0]
        header_row_index = matching_cell_index + 2  # Two rows below the matching cell
        data_start_index = header_row_index + 1

        # Extract headers and relevant data
        headers = ['Area', 'Demand', 'Supply', 'Loadshed']
        data = forecast_sheet.loc[data_start_index:data_start_index+8, 9:12].copy()  # Adjust column indices if needed
        data.columns = headers[:len(data.columns)]  # Ensure correct headers

        # Drop empty rows and exclude 'Loadshed'
        data = data[['Area', 'Demand', 'Supply']].dropna(how='all')

        # Locate "(Yesterday)" cell and extract the date
        yesterday_cell = forecast_sheet[forecast_sheet.apply(
            lambda row: row.astype(str).str.contains(r"\(Yesterday\)", case=False, na=False).any(), axis=1
        )]
        if not yesterday_cell.empty:
            yesterday_cell_index = yesterday_cell.index[0]
            date_cell = forecast_sheet.loc[yesterday_cell_index, 3]  # Column 3 for the date
            date_value = pd.to_datetime(str(date_cell), errors='coerce')
            if pd.notnull(date_value):
                adjusted_date_value = date_value.date()
                data['Date'] = adjusted_date_value
            else:
                print(f"Invalid date in file {file_path}. Skipping.")
                return None

        return data

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None

# Main function to process all files in a directory
def process_directory(directory_path, output_csv):
    all_data = []

    # Iterate through all files in the directory
    for filename in os.listdir(directory_path):
        if filename.endswith(".xlsm"):
            file_path = os.path.join(directory_path, filename)
            print(f"Processing file: {filename}")
            data = extract_data_from_file(file_path)
            if data is not None:
                all_data.append(data)

    # Combine all data into a single DataFrame
    if all_data:
        combined_data = pd.concat(all_data, ignore_index=True)
        combined_data.to_csv(output_csv, index=False)
        print(f"Data successfully saved to {output_csv}")
    else:
        print("No data extracted from the files.")

# Directory containing the files and output file path
directory_path = " "
output_csv = "combined_data.csv"

# Run the script
process_directory(directory_path, output_csv)
