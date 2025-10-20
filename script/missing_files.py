import os
import re
import argparse
from datetime import datetime, timedelta
from rename_files_dir import check_daily_reports_folder


def find_missing_dates(directory):
    # Define date pattern in filenames, assuming format like yyyy-mm-dd in filenames
    date_pattern = re.compile(r"(\d{4})[-._](\d{2})[-._](\d{2})")

    # List to store all the valid dates found
    date_list = []

    # Iterate through all files in the directory
    for filename in os.listdir(directory):
        match = date_pattern.search(filename)
        if match:
            try:
                # Extract date parts from the filename and create a date object
                year, month, day = map(int, match.groups())
                date_obj = datetime(year, month, day)
                date_list.append(date_obj)
            except ValueError:
                print(f"Skipping invalid date in filename: {filename}")

    # If no valid dates are found, return early
    if not date_list:
        print("No valid dates found in the filenames.")
        return

    # Sort the dates
    date_list.sort()

    # Find the starting and ending dates
    start_date = date_list[0]
    end_date = date_list[-1]

    print(f"Starting date: {start_date.strftime('%Y-%m-%d')}")
    print(f"Ending date: {end_date.strftime('%Y-%m-%d')}")

    # Find missing dates
    missing_dates = []
    current_date = start_date
    while current_date < end_date:
        current_date += timedelta(days=1)
        if current_date not in date_list:
            missing_dates.append(current_date)

    if missing_dates:
        print("Missing dates:")
        for missing in missing_dates:
            print(missing.strftime('%Y-%m-%d'))
    else:
        print("No missing dates.")


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Check if all the files provided in PGCB daily report are downloaded. " \
                                                "Must be run after after all the files are downloaded and renamed to standard format." \
                                                "Run `python rename_files_dir.py --path <path_to_daily_reports>` first if files are not renamed." \
                                                " If no path is provided, current working directory will be used. It will look for 'daily_reports' folder in the current directory.")
    parser.add_argument("--path", help="Path to the dfolder that contains all the PGCB daily report.")
    args = parser.parse_args()

    path = args.path if args.path else os.getcwd()
    # If path not provided, check in current directory if "daily_reports" folder exists
    if not args.path:
        if check_daily_reports_folder(path):   
            path = check_daily_reports_folder(path)
        else:
            print("Error: 'daily_reports' folder not found in the current directory. Please provide a valid path.")
            exit(1)

    # Call the function with the provided directory
    print(f"Checking for missing dates in {path}...")
    find_missing_dates(path)