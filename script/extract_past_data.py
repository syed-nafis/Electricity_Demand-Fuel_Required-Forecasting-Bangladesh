import os
import pandas as pd
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from rename_files_dir import check_daily_reports_folder
from extract_powerplant_info import extract_powerplant_info, find_new_powerplants, process_daily_data
from extract_powerplant_shutdown import extract_powerplant_shutdown_data


def process_file(filename, path):
    """
    Worker function: process a single Excel file and return new powerplants.
    """
    file_path = os.path.join(path, filename)
    try:
        # Extract powerplant information
        extracted_data = process_daily_data(file_path)

        # shutdown data extraction (if needed)
        # shutdown_data = extract_powerplant_shutdown_data(extracted_data, filename)

        print(f"Processed file: {filename}")
        return extracted_data
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return pd.DataFrame()  # return empty if error


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract powerplant_information from All daily reports")
    parser.add_argument("--path", help="Path to the directory where the downloaded files would be saved")
    parser.add_argument("--threads", type=int, default=10, help="Number of threads for parallel processing")
    parser.add_argument("--excel", action="store_true", help="Generate excel file")
    parser.add_argument("--csv", action="store_true", help="Generate csv file")

    args = parser.parse_args()
    path = args.path + "/" if args.path else os.getcwd()
    threads = args.threads

    # Path handling
    if not args.path:
        if check_daily_reports_folder(path):
            path = check_daily_reports_folder(path)
        else:
            print("Error: 'daily_reports' folder not found in the current directory. Please provide a valid path.")
            exit(1)
    else:
        if not os.path.isdir(path):
            print(f"Error: Directory '{path}' not found.")
            exit(1)

    # Collect all Excel files
    excel_files = [
        f for f in os.listdir(path) if f.endswith((".xlsx", ".xlsm", ".xls"))
    ]

    columns = []
    #files where new powerplants are found
    files_with_new_powerplants = []
    #error files
    error_files = []

    powerplant_data = pd.DataFrame()

    # Use ThreadPoolExecutor to process files in parallel
    with ThreadPoolExecutor(max_workers=threads) as executor:  # adjust workers as needed
        futures = {
            executor.submit(process_file, filename, path): filename
            for filename in excel_files
        }

        for future in as_completed(futures):
            daily_data = future.result()
            try:
                if not daily_data.empty:
                    if not daily_data.columns.is_unique:
                        print(f"Warning: Duplicate columns found in {futures[future]}. They will be merged.")
                        daily_data = daily_data.loc[:, ~daily_data.columns.duplicated()]
                    if not daily_data.index.is_unique:
                        print(f"Warning: Duplicate indices found in {futures[future]}. They will be reset.")
                        daily_data.reset_index(drop=True, inplace=True)
                    powerplant_data = pd.concat([powerplant_data, daily_data], ignore_index=True)
                    powerplant_data.drop_duplicates(inplace=True)
                    powerplant_data.reset_index(drop=True, inplace=True)
            except Exception as e:
                print(f"Error merging data from {futures[future]}: {e}")
                error_files.append(futures[future])
                continue


    print(f"Total new powerplants found: {len(powerplant_data)}")

    # print all the error files
    if error_files:
        print(f"Files with errors: {len(error_files)}")
        for ef in error_files:
            print(f"- {ef}")
    # Export to excel or csv
    if args.excel:
        powerplant_data.to_excel("powerplant_info.xlsx", index=False)
        print("Powerplant information exported to Excel (powerplant_info.xlsx)")
    if args.csv:
        powerplant_data.to_csv("powerplant_info.csv", index=False)
        print("Powerplant information exported to CSV (powerplant_info.csv)")
