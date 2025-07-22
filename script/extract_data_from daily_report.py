import pandas as pd

# Define the file path
file_path = " "
output_csv_path = 'yesterdaygen_extracted.csv'

# Load the Excel file
data = pd.read_excel(file_path, sheet_name='YesterdayGen', header=None)

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
    'date': [date] * len(power_plant_names),
    'power_plant_name': power_plant_names,
    'energy_produced(kWH)': energy_produced,
    'fuel_cost': fuel_cost,
    'day_peak': day_peak,
    'evening_peak': evening_peak,
    'forecast_day_peak': forecast_day_peak,
    'forecast_evening_peak': forecast_evening_peak,
}

# Convert to DataFrame
result_df = pd.DataFrame(structured_data)

# Save to CSV
result_df.to_csv(output_csv_path, index=False)

print(f"CSV file saved at: {output_csv_path}")
