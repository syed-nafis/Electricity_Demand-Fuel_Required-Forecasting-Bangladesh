import os
import argparse as args
import pandas as pd
from db import get_area_mappings
from config import powerplantinfo_columns


def get_total_rows(powerplant_df):
  total_rows = powerplant_df[powerplant_df['powerplant_name'].str.contains('total', case=False, na=False)]
  return total_rows

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

if __name__ == "__main__":
    #extract all powerplant info from the excel files in the given directory
    parser = args.ArgumentParser(description="Assign area to each powerplant in the powerplant info dataframe")
    path = "/Users/syed/code/green/Electricity Demand Forecasting - Bangladesh/daily_report"

    #read all excel files in the directory
    excel_files = [f for f in os.listdir(path) if f.endswith((".xlsx", ".xlsm", ".xls"))]
    powerplant_data = pd.DataFrame(columns=['powerplant_name',
                                            'fuel', 
                                            'installed_capacity', 
                                            'present_capacity', 
                                            'mw_lost_limitation', 
                                            'mw_lost_m/c_problem', 
                                            'reason',
                                            'area'])
    
    total_rows_empty = []
    error_files = []
    
    #files where new powerplants are found
    for file in excel_files:
        file_path = os.path.join(path, file)
        print(f"Processing file: {file}")
        try:
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

          area_mapping_dict = get_area_mappings()
          total_rows = get_total_rows(powerplant_df)
          if total_rows.empty:
            print(f"Skipping file {file}: No 'Total' rows found.")
            total_rows_empty.append(file)
            
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
          # Merge results into main dataframe
          powerplant_data = pd.concat([powerplant_data, new_df], ignore_index=True)
          powerplant_data.drop_duplicates(inplace=True)
        except Exception as e:
          print(f"Error reading file {file}: {e}")
          error_files.append(file)
          continue
    powerplant_data.reset_index(drop=True, inplace=True)
    print(f"Total powerplants found: {len(powerplant_data)}")
    #save as csv
    powerplant_data.to_csv("powerplant_info_with_area.csv", index=False)
    # print files with empty total rows
    if total_rows_empty:
      print(f"Files with empty 'Total' rows: {len(total_rows_empty)}")
      for f in total_rows_empty:
        print(f"- {f}")
    if error_files:
      print(f"Files with errors: {len(error_files)}")
      for f in error_files:
        print(f"- {f}")