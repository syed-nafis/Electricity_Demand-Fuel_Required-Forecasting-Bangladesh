import os
import pandas as pd

# Define the directory containing the files and output paths
directory_path = " "  # Edit this
combined_csv_path = "combined_powerplant_info.csv"
log_csv_path = "log_of_new_power_stations.csv"

def process_forecast_file(file_path, existing_power_stations):
    """
    Process a single forecast file, extracting relevant data and returning new power stations.
    """
    # Load the Excel file and the "Forecast" sheet
    excel_file = pd.ExcelFile(file_path)
    forecast_sheet = pd.read_excel(excel_file, sheet_name="Forecast", skiprows=4)
    
    # Rename columns and align data
    forecast_sheet.columns = [
        "Power Station Name",
        "Fuel Type",
        "Producer",
        "Installed Capacity",
        "Present Capacity",
        *forecast_sheet.columns[5:]
    ]
    forecast_sheet = forecast_sheet.iloc[:, :5]  # Keep only the first 5 columns
    forecast_sheet = forecast_sheet.iloc[1:]  # Drop the header row
    forecast_sheet.dropna(subset=["Power Station Name"], inplace=True)

    # Process data for area mapping
    area_name = None
    processed_data = []
    for _, row in forecast_sheet.iterrows():
        power_station = row["Power Station Name"]
        if isinstance(power_station, str) and "total" in power_station.lower():
            if "area total" in power_station.lower():
                area_name = power_station.replace("area total", "").strip()
            continue
        
        row_data = row.to_dict()
        row_data["Area"] = area_name  # Ensure the "Area" column exists
        processed_data.append(row_data)

    # Create a DataFrame from processed data
    processed_df = pd.DataFrame(processed_data)

    # Ensure the "Area" column exists, even if empty
    if "Area" not in processed_df.columns:
        processed_df["Area"] = None

    # Clean "Area" column
    processed_df["Area"] = processed_df["Area"].str.replace(
        r"area total", "", case=False, regex=True
    ).str.strip()

    # Identify new power stations
    new_power_stations = processed_df[~processed_df["Power Station Name"].isin(existing_power_stations)]
    
    return new_power_stations


def main():
    # Initialize storage for combined data and logs
    combined_data = pd.DataFrame()
    log_data = []

    # Track existing power stations
    existing_power_stations = set()

    # Process each file in the directory
    for file_name in os.listdir(directory_path):
        file_path = os.path.join(directory_path, file_name)
        if file_name.endswith(".xls") or file_name.endswith(".xlsm"):
            print(f"Processing file: {file_name}")
            
            # Extract new power stations
            new_data = process_forecast_file(file_path, existing_power_stations)
            
            # If there are new power stations, update records
            if not new_data.empty:
                combined_data = pd.concat([combined_data, new_data], ignore_index=True)
                for _, row in new_data.iterrows():
                    log_data.append({"File": file_name, "Power Station Name": row["Power Station Name"]})
                    existing_power_stations.add(row["Power Station Name"])

    # Save the combined data and log
    combined_data.to_csv(combined_csv_path, index=False)
    pd.DataFrame(log_data).to_csv(log_csv_path, index=False)

    print(f"Combined data saved to {combined_csv_path}")
    print(f"Log of new power stations saved to {log_csv_path}")

if __name__ == "__main__":
    main()
