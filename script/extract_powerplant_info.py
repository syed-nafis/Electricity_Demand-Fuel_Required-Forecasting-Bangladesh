import os
import re
import numpy as np
import pandas as pd
import argparse as args
from db import get_area_mappings
from config import powerplantinfo_columns
from rename_files_dir import check_daily_reports_folder



def get_total_rows(powerplant_df):
  total_rows = powerplant_df[powerplant_df['powerplant_name'].str.contains('total', case=False, na=False)]
  return total_rows

# not using this anymore
def assign_area(powerplant_df):
    area_mapping_dict = get_area_mappings()
    total_rows = get_total_rows(powerplant_df)
    start_index = 0
    end_index = total_rows[total_rows['powerplant_name'].str.strip().str.lower() == 'total'].index[0] # Extract the integer index
    new_df= powerplant_df.iloc[:end_index].copy(deep = True)

    # In daily_reports(jan 2019 - dec 2020) powerplant information
    # is given in the format [ rows of power_plants in an area -> followed by that area total ]
    for index, row in total_rows[:9].iterrows():
      new_df.loc[start_index:index, 'area'] = area_mapping_dict.get(row['powerplant_name'].strip().split()[0])
      #new_df.drop(index = index, inplace = True)
      start_index = index + 1
    # Drop the rows "Area Total" rows
    rows_to_drop_mask = new_df['powerplant_name'].str.lower().str.strip().str.contains('area total', na=False)
    # Get the indices of the rows to drop
    indices_to_drop = new_df[rows_to_drop_mask].index
    # Drop the rows using the indices
    new_df.drop(indices_to_drop, inplace = True)
    return new_df # Return the new_df


"""
extracted dataframe structure for "powerplant_info" from each "daily_report" file
powerplantinfo_columns = ['powerplant_name',
                    'fuel', 
                    'installed_capacity', 
                    'present_capacity', 
                    'mw_lost_limitation', 
                    'mw_lost_m/c_problem', 
                    'reason',
                    'area']
"""
# Extract powerplant information from jan 2019 to dec 2024 daily reports
# Because they follow the same format
# not using this anymore
def extract_powerplant_info(file_path):
    df = pd.read_excel(file_path, sheet_name='Forecast')
    powerplant_df = df.iloc[4:, [2, 4, 6, 8, 9, 11, 12, 13, 14, 15]].copy()
    powerplant_df.columns = df.iloc[4, [2, 4, 6, 8, 9, 11, 12, 13, 14, 15]].tolist()
    powerplant_df = powerplant_df.drop([4,5,6])

    # Re-index the dataframe
    powerplant_df = powerplant_df.reset_index(drop=True)

    # Drop columns by index (0-based)
    # The columns to drop are at original indices 4, 5, and 6 based on the user's request
    # These correspond to 'On 2024-12-31 00:00:00', 'during', and 'for Fuel\n'
    powerplant_df = powerplant_df.drop(powerplant_df.columns[[4, 5, 6]], axis=1)
    powerplant_df['area'] = None  # Initialize the 'area' column with None values

    # Assign new column names
    powerplant_df.columns = powerplantinfo_columns

    # drop empty rows
    powerplant_df = powerplant_df.dropna(subset=['powerplant_name'])

    try:
        powerplant_df = assign_area(powerplant_df)
    except:
        print(f"Error assigning area for file: {file_path}")
    return powerplant_df


def normalize_name(name: str) -> str:
    try:
        return name.replace(" ", "").lower()
    except Exception as e:
        print(f"Error normalizing name: {e}")
        return ""

# not using this anymore
def find_new_powerplants(powerplants_info_df, existing_powerplants):
    # Normalize existing powerplant names
    normalized_existing = {normalize_name(p) for p in existing_powerplants}

    # Create a normalized column for comparison
    powerplants_info_df['normalized_name'] = powerplants_info_df['powerplant_name'].apply(normalize_name)

    # Filter out those not in existing set
    new_powerplants = powerplants_info_df[~powerplants_info_df['normalized_name'].isin(normalized_existing)]

    # Drop helper column if you don’t need it
    new_powerplants = new_powerplants.drop(columns=['normalized_name'])

    return new_powerplants
   
# current approach of standardizing power station names
def clean_power_station_name(name):
    if isinstance(name, str):
        name = name.lower()
        name = name.replace(" ", "")
        #remove newline character from name
        name = name.replace("\n", "")
        #remove special characters from name
        keywords = ["ccpp", "tpp", "pp", "gtpp", "mw", "ltd", "lid", "gas", "oil", "unit"]
        for keyword in keywords:
            name = name.replace(keyword, "")
        name = re.sub(r'[^\w\s]', '', name) # Remove punctuation
        return name
    return name

# current appraoch to extrant powerplant info from daily_reports
def process_daily_data(file_path):
  # Load the data
  daily = pd.read_excel(file_path, sheet_name='Forecast')

  # Find the starting row
  row_index, col_index = np.where(daily == "Name of the Power Station")
  if row_index.size == 0:
      raise ValueError("Could not find 'Name of the Power Station' in the file.")
  start_row = row_index[0]
  start_col = col_index[0]

  # Clean the dataframe by removing header rows and unnecessary columns
  daily_cleaned = daily.iloc[row_index[0]:, col_index[0]:]
  daily_cleaned = daily_cleaned.dropna(subset=[daily_cleaned.columns[0]])
  daily_cleaned.reset_index(drop=True, inplace=True)

  row_indices = np.where(daily_cleaned.iloc[:, 0] == "Rangpur Area Total")[0]

  if row_indices.size > 0:
      row_index = row_indices[0]
      daily_cleaned = daily_cleaned.iloc[:row_index + 1, :]

  daily_cleaned = daily_cleaned.dropna(axis=1, how='all')
  daily_cleaned.columns = daily_cleaned.iloc[0]
  daily_cleaned = daily_cleaned.iloc[1:].reset_index(drop=True)

  # Clean the power station names
  daily_cleaned["Name of the Power Station"] = daily_cleaned["Name of the Power Station"].apply(clean_power_station_name)

  # Find the indices of "Area Total" rows
  area_total_indices = daily_cleaned[daily_cleaned.iloc[:, 0].str.contains("areatotal", na=False)].index.tolist()

  # Segment the dataframe by area
  area_dataframes = []
  start_index = 0

  for end_index in area_total_indices:
      area_df = daily_cleaned.iloc[start_index : end_index + 1].copy()
      area_dataframes.append(area_df)
      start_index = end_index + 1

  # Map area names to dataframes
  area_mappings = ["Dhaka", "Chattogram", "Cumilla", "Mymensingh", "Sylhet", "Khulna", "Barisal", "Rajshahi", "Rangpur"]
  area_dataframes_dict = dict(zip(area_mappings, area_dataframes))

  area_info = pd.DataFrame()
  columns_to_drop = [6, 7, 8, 9] # 7th, 8th, 9th, and 10th columns


  # Add 'Area' column and remove the last row (which contains the total)
  for area, df in area_dataframes_dict.items():
      df['Area'] = area # Add an 'Area' column with the area name
      df = df.drop(df.columns[columns_to_drop], axis=1) # Drop unnecessary columns
      #print(f"DataFrame for {area}:")
      #remove the last row of each of these df
      df = df.iloc[:-1]
      area_info = pd.concat([area_info, df], ignore_index=True)
      #display(df)
  
  return area_info

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
    
    

