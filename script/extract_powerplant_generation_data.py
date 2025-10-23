import re
import pandas as pd
import os
import argparse as args
from rename_files_dir import check_daily_reports_folder

def process_daily_report(file_path):
    """
    Processes a daily power generation report from an Excel file, extracts
    plant-wise total electricity generation and fuel cost, and appends it
    to an existing DataFrame.

    Args:
        existing_df (pd.DataFrame): The DataFrame to append the data to.
        file_path (str): The path to the daily report Excel file.

    Returns:
        pd.DataFrame: The updated DataFrame with the appended daily data.
    """
    try:
        # Read the specified sheet from the Excel file
        daily_report = pd.read_excel(file_path, sheet_name='YesterdayGen')

        # Find the row index of 'Plant Name' and 'Fuel Cost'
        start_row = daily_report[daily_report.iloc[:, 0] == 'Plant Name'].index[0]
        end_row = daily_report[daily_report.iloc[:, 0] == 'Fuel Cost'].index[0]

        # Slice the DataFrame to include rows from 'Plant Name' to 'Fuel Cost'
        extracted_df = daily_report.iloc[start_row : end_row + 1].copy()

        # Find the column index of 'Eastern Grid Total' in the header row
        header_row = extracted_df.iloc[0].astype(str)
        eastern_grid_col_index = header_row[header_row.str.contains('Eastern Grid Total', na=False)].index

        # Trim columns after 'Eastern Grid Total' if found
        if not eastern_grid_col_index.empty:
            eastern_grid_col_iloc = extracted_df.columns.get_loc(eastern_grid_col_index[0])
            extracted_df = extracted_df.iloc[:, :eastern_grid_col_iloc + 1]
        else:
            print(f"'Eastern Grid Total' column not found in {file_path}. Processing all columns up to 'Fuel Cost'.")

        # Set the first row as the header
        extracted_df.columns = extracted_df.iloc[0]
        extracted_df = extracted_df[1:].reset_index(drop=True)

        # Drop rows that are entirely empty
        extracted_df.dropna(how='all', inplace=True)

        # Extract the column names as plant names (excluding the first column which is the timestamp/label column)
        plant_names = extracted_df.columns[1:].tolist()

        # Extract the row containing KWH values by its index
        kwh_row = extracted_df[extracted_df.iloc[:, 0] == 'KWH'].iloc[0]

        # Extract the row containing Fuel Cost values by its index
        fuel_cost_row = extracted_df[extracted_df.iloc[:, 0] == 'Fuel Cost'].iloc[0]

        # Create lists of KWH and Fuel Cost values corresponding to the plant names (excluding the first column)
        kwh_values = kwh_row[1:].tolist()
        fuel_cost_values = fuel_cost_row[1:].tolist()

        # Extract the date from the filename and convert to datetime
        file_name = file_path.split('/')[-1]
        date_str = file_name.split('.')[0]
        report_date = pd.to_datetime(date_str)

        # Create the new DataFrame for the daily data
        daily_data = {'date': [report_date] * len(plant_names),
                      'plant_name': plant_names,
                      'electricity_gen': kwh_values,
                      'fuel_cost': fuel_cost_values}

        reshaped_df = pd.DataFrame(daily_data)

        return reshaped_df

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return extracted_df
    except ValueError as ve:
        print(f"Error processing file {file_path}: {ve}")
        return extracted_df
    except Exception as e:
        print(f"An unexpected error occurred while processing {file_path}: {e}")
        return extracted_df

# Initialize an empty DataFrame to store the combined data
# Example usage (you would loop through your list of file paths)
# file_paths = ['/content/2020-06-18.xlsm', '/content/another_report.xlsm'] # Replace with your actual file paths
# for file_path in file_paths:
#     combined_daily_gen_df = process_daily_report(combined_daily_gen_df, file_path)

# Display the combined DataFrame (after processing files)
# display(combined_daily_gen_df.head())

# For demonstration, process the single file you have


def _hhmm(v):
    """Normalize a YesterdayGen time label (datetime/time/'24:00') -> 'HH:MM' or None."""
    import datetime as _dt
    if isinstance(v, _dt.datetime):
        v = v.time()
    if isinstance(v, _dt.time):
        return f"{v.hour:02d}:{v.minute:02d}"
    s = str(v).strip()
    if re.match(r"^\d{1,2}:\d{2}$", s):
        return s if len(s) == 5 else "0" + s
    return None


def process_yesterdaygen_hourly(file_path):
    """Extract the hourly MW-per-plant block from a 2019-2024 YesterdayGen sheet.
    Returns long format: date, time (HH:MM), plant_name, mw. Columns past
    'Eastern Grid Total' (fuel-mix/summary) and aggregate names are excluded."""
    g = pd.read_excel(file_path, sheet_name='YesterdayGen', header=None)
    col0 = g.iloc[:, 0].astype(str).str.strip()
    hdr = col0[col0 == 'Plant Name'].index
    kwh = col0[col0 == 'KWH'].index
    if len(hdr) == 0 or len(kwh) == 0:
        raise ValueError("YesterdayGen markers ('Plant Name'/'KWH') not found")
    hdr, kwh = int(hdr[0]), int(kwh[0])

    header = g.iloc[hdr].astype(str)
    egt = header[header.str.contains('Eastern Grid Total', na=False)].index
    end_col = int(egt[0]) + 1 if len(egt) else g.shape[1]

    nonplant = re.compile(r"(?i)(total|grid|water level|shortage)")
    cols = {}
    for ci in range(1, end_col):
        v = g.iloc[hdr, ci]
        if pd.isna(v):
            continue
        name = str(v).strip()
        if name and not nonplant.search(name):
            cols[ci] = name

    date = pd.to_datetime(os.path.basename(file_path).rsplit('.', 1)[0])
    out = []
    for ri in range(hdr + 1, kwh):
        t = _hhmm(g.iloc[ri, 0])
        if t is None:
            continue
        for ci, nm in cols.items():
            out.append({"date": date, "time": t, "plant_name": nm, "mw": g.iloc[ri, ci]})
    df = pd.DataFrame(out)
    if not df.empty:
        df["mw"] = pd.to_numeric(
            df["mw"].astype(str).str.replace(r"[\s\xa0,]", "", regex=True)
            .replace({"": None, "nan": None, "None": None}),
            errors="coerce",
        )
    return df


if __name__ == "__main__":
    path = ""
    parser = args.ArgumentParser(description="Extract powerplant_information from All daily reports")
    parser.add_argument("--path", help="Path to the directory where the downloaded files would be saved")
    parser.add_argument("--excel", action="store_true",  help="Generate excel file")
    parser.add_argument("--csv", action="store_true",  help="Generate csv file")

    args = parser.parse_args()  # Parse the arguments here!
    path = args.path + "/" if args.path else os.getcwd()

    # If path not provided, check in current directory if "daily_reports" folder exists
    if not args.path:
        if check_daily_reports_folder(path):   
            path = check_daily_reports_folder(path)
        else:
            print("Error: 'daily_reports' folder not found in the current directory. Please provide a valid path.")
            exit(1)
    else:
        # Ensure the directory exists
        if not os.path.isdir(path):
            print(f"Error: Directory '{path}' not found.")
            exit(1)


    # Iterate through all files in the directory
    combined_daily_gen_df = pd.DataFrame(columns=['date', 'plant_name', 'electricity_gen', 'fuel_cost'])
    error_files = []
    for filename in os.listdir(path):
        if filename.endswith(".xlsm"):
            file_path = os.path.join(path, filename)
            print(f"Processing file: {filename}")
            try:
                extracted_data = process_daily_report(file_path)
            except Exception as e:
                print(f"Error processing file {filename}: {e}")
                error_files.append(filename)
                continue
            combined_daily_gen_df = pd.concat([combined_daily_gen_df, extracted_data], ignore_index=True)
    
    # depending on the option selected, save the combined dataframe to excel or csv
    combined_daily_gen_df.reset_index(drop=True, inplace=True)
    if args.excel:
        combined_daily_gen_df.to_excel(os.path.join(path, "combined_powerplant_generation_data.xlsx"), index=False)
    if args.csv:
        combined_daily_gen_df.to_csv(os.path.join(path, "combined_powerplant_generation_data.csv"), index=False)

    # print all the files that caused errors
    if error_files:
        print("The following files caused errors during processing:")
        for ef in error_files:
            print(ef)