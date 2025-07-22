import os
import re
import argparse
from datetime import datetime, timedelta

# set your path here
path = " "

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
    parser = argparse.ArgumentParser(description="Check if all the files provided in PGCB daily report are downloaded")
    parser.add_argument("--path", help="Path to the directory to check if it contains all the files provided in PGCB daily report.")
    args = parser.parse_args()

    path = args.path if args.path else path

    # Call the function with the provided directory
    print(f"Checking for missing dates in {path}...")
    find_missing_dates(path)