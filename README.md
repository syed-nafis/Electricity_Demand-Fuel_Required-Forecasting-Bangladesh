## Electricity Demand Forecasting - Bangladesh

This project automates the data gathering and processing pipeline for forecasting electricity demand in Bangladesh, as well as estimating the required fuel to meet that demand. The scripts provided allow you to download daily reports from the Power Grid Company of Bangladesh (PGCB), process and extract relevant data, and check for missing or misnamed files.

## Data Source

All raw data is sourced from the [Power Grid Company of Bangladesh (PGCB)](https://www.pgcb.gov.bd/).

## Project Structure

- `script/`
  - `download_daily_report.py`: Downloads daily electricity reports from the PGCB website using Selenium.
  - `extract_area_wise_energy_demand_supply.py`: Extracts area-wise demand and supply data from downloaded Excel files.
  - `extract_powerplant_info.py`: Extracts power plant metadata from reports.
  - `extract_powerplant_generation_data.py`: Extracts generation data per power plant.
  - `extract_data_from daily_report.py`: Extracts specific data from a daily report.
  - `monthly_report_script.py`: Processes monthly reports.
  - `missing_files.py`: Checks for missing daily report files in a directory.
  - `rename_files_dir.py`: Renames files for consistency.
- `extracted_Data/`: Contains processed and extracted datasets.
- `monthly_reports/` and `daily_reports/`: Contain example reports. Run the scripts to download and process the full set.

## How to Use

### 1. Clone the Repository

```bash
git clone <repo-url>
cd "Electricity Demand Forecasting - Bangladesh"
```

### 2. Install Dependencies

- Ensure you have Python 3.x installed.
- Install required packages (Selenium, pandas, etc.):
  ```bash
  pip install selenium pandas openpyxl webdriver-manager
  ```
  You may need additional packages depending on the script (e.g., `beautifulsoup4`, `requests`).

- For Selenium, ensure you have Google Chrome installed, as the scripts use ChromeDriver.

### 3. Download Daily Reports

Use the `download_daily_report.py` script to download daily reports from the PGCB website.

```bash
python script/download_daily_report.py --path <download_directory> --last_page_number <number_of_pages>
```

- `--path`: Directory where the downloaded files will be saved.
- `--last_page_number`: (Optional) Last page number to download (default is 132 to download daily_reports till 2024-12-31). Set this is to the last page of the website

Example:
```bash
python script/download_daily_report.py --path ./daily_reports --last_page_number 132
```

### 4. Check for Missing Files

After downloading, you can check if any daily reports are missing:

```bash
python script/missing_files.py --path <download_directory>
```

Example:
```bash
python script/missing_files.py --path ./daily_reports
```

### 5. Extract and Process Data

#### Area-wise Demand and Supply

Extract area-wise demand and supply data from the downloaded Excel files:

```bash
python script/extract_area_wise_energy_demand_supply.py
```

- By default, the script expects the directory path and output CSV to be set in the script. Edit the variables `directory_path` and `output_csv` at the bottom of the script as needed.

#### Other Extraction Scripts

- `extract_powerplant_info.py`, `extract_powerplant_generation_data.py`, and `extract_data_from daily_report.py` are used for extracting specific information from the reports. Refer to the comments and variable settings at the top of each script for usage instructions.

#### Monthly Reports

- Use `monthly_report_script.py` to process monthly reports. Edit the script as needed for your data and run:
  ```bash
  python script/monthly_report_script.py
  ```

#### Renaming Files

- If you need to rename files for consistency, use:
  ```bash
  python script/rename_files_dir.py
  ```

## Notes

- The code is well-commented for ease of understanding and modification.
- Only example reports are included by default. You must run the scripts to download and process the full datasets.
- All extracted and processed data will be available in the `extracted_Data/` directory.

## License

[MIT License](LICENSE) (or specify your license here) 
