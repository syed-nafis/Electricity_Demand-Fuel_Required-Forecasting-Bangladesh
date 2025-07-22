import os
import pandas as pd
from datetime import datetime

# Define the directory containing the Excel files and the output CSV file
directory_path = " "
output_csv_path = "yesterdaygen_combined.csv"

# Define the starting date (inclusive)
start_date = datetime.strptime("2019-01-01", "%Y-%m-%d")

# Initialize an empty DataFrame to store combined data
combined_data = pd.DataFrame()

# List to store the names of files that could not be processed
skipped_files = []

# Iterate over all files in the directory
for filename in os.listdir(directory_path):
    # Check if the file is an Excel file (xls or xlsm)
    if filename.endswith(".xls") or filename.endswith(".xlsm"):
        try:
            # Extract the date from the filename
            file_date = datetime.strptime(filename[:10], "%Y-%m-%d")
            
            # Process files only if the date is on or after the start date
            if file_date >= start_date:
                file_path = os.path.join(directory_path, filename)
                try:
                    # Try reading the Excel file
                    data = pd.read_excel(file_path, sheet_name="YesterdayGen", header=None)
                    
                    # Extract data from the specified cells
                    date = data.iloc[1, 0]  # A2
                    power_plant_names = data.iloc[2, 1:].values  # B3:GZ3
                    energy_produced = data.iloc[30, 1:].values  # B31:GZ31
                    fuel_cost = data.iloc[31, 1:].values  # B32:GZ32
                    day_peak = data.iloc[32, 1:].values  # B33:GZ33
                    evening_peak = data.iloc[33, 1:].values  # B34:GZ34
                    forecast_day_peak = data.iloc[34, 1:].values  # B35:GZ35
                    forecast_evening_peak = data.iloc[35, 1:].values  # B36:GZ36
                    
                    # Structure the data
                    structured_data = {
                        "date": [date] * len(power_plant_names),
                        "power_plant_name": power_plant_names,
                        "energy_produced(kWH)": energy_produced,
                        "fuel_cost": fuel_cost,
                        "day_peak": day_peak,
                        "evening_peak": evening_peak,
                        "forecast_day_peak": forecast_day_peak,
                        "forecast_evening_peak": forecast_evening_peak,
                    }
                    
                    # Convert to DataFrame
                    file_data = pd.DataFrame(structured_data)
                    
                    # Append to the combined DataFrame
                    combined_data = pd.concat([combined_data, file_data], ignore_index=True)
                except Exception as e:
                    # Log the filename of the file that could not be processed
                    skipped_files.append((filename, str(e)))
        except ValueError:
            # Skip files that do not have a valid date format in their names
            skipped_files.append((filename, "Invalid date format"))

# Save the combined data to a single CSV file
combined_data.to_csv(output_csv_path, index=False)

# Print the results
if skipped_files:
    print("The following files were skipped due to errors:")
    for file, error in skipped_files:
        print(f"{file}: {error}")
else:
    print("All files processed successfully.")

print(f"Combined CSV file saved at: {output_csv_path}")
