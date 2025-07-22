import os
import re
import argparse
from datetime import datetime

# Set path for the directory to rename files
path = " "

def standardize_date_format(directory):
    # Define the date patterns to match various formats
    date_patterns = [
        r"(\d{2})[-._](\d{1,2})[-._](\d{2})",  # dd-mm-yy or dd.mm.yy or dd_mm_yy
        r"(\d{2})[-._](\d{1,2})[-._](\d{4})",  # dd-mm-yyyy or dd.mm.yyyy or dd_mm_yyyy
        r"(\d{2})(\d{1,2})[-._](\d{4})",      # ddmm-yyyy
        r"(\d{2})[-._](\d{1,2})(\d{4})"       # dd-mmmyyyy
    ]
    
    # Pattern to detect already correctly formatted files
    desired_format_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}\.\w+$")

    # Normalize variations in "Daily Report"
    report_pattern = re.compile(r"(daily\s*_*\s*report)\s*[-_]*\s*", re.IGNORECASE)
    
    # Detect duplicate files ending with "(1)", "(2)", etc.
    duplicate_pattern = re.compile(r"\(\d+\)$")

    # Special cases: filenames that should be directly renamed
    special_cases = {
        "Daily Report 31.2.2022.xlsm": "2022-12-31.xlsm",
        "Daily Report 149.2.2023.xlsm": "2023-02-18.xlsm",
        "Daily Report.xlsm": "2022-04-25.xlsm",
        "Daily Report 13-10-2024.xlsm": "2024-11-13.xlsm",
        "Daily Report  26-01-2021.xlsm": "2022-01-26.xlsm",
        "Daily Report 04-11-219.xlsm": "2019-11-04.xlsm",
        "Daily Report 149.2.2023.xlsm": "2023-02-19.xlsm",
        "Daily Report 21-8-20223.xlsm": "2023-08-21.xlsm"
    }

    # Iterate through all files in the directory
    for filename in os.listdir(directory):
        original_filename = filename
        new_date = None

        # Check if the file is already in the desired format
        if desired_format_pattern.match(filename):
            print(f"Ignoring already correctly formatted file: {filename}")
            continue

        # Check if this file is in the special cases mapping
        if filename in special_cases:
            new_filename = special_cases[filename]
            new_path = os.path.join(directory, new_filename)

            # Check if the target file already exists
            if os.path.exists(new_path):
                print(f"Skipping renaming {original_filename}: {new_filename} already exists.")
                continue

            # Rename the file using the special case mapping
            original_path = os.path.join(directory, original_filename)
            try:
                os.rename(original_path, new_path)
                print(f"Renamed (special case): {original_filename} -> {new_filename}")
            except OSError as e:
                print(f"Error renaming {original_filename}: {e}")
            continue

        # Delete duplicate files ending with "(1)", "(2)", etc.
        if duplicate_pattern.search(os.path.splitext(filename)[0]):
            try:
                os.remove(os.path.join(directory, filename))
                print(f"Deleted duplicate file: {filename}")
            except OSError as e:
                print(f"Error deleting {filename}: {e}")
            continue

        # Normalize "Daily Report" to standard format
        normalized_filename = report_pattern.sub("Daily_Report_", filename)

        # Try to extract and standardize the date
        for pattern in date_patterns:
            match = re.search(pattern, normalized_filename)
            if match:
                groups = match.groups()
                if len(groups) == 3:  # Standard 3-part formats
                    date_str = '-'.join(groups)
                    try:
                        if len(groups[2]) == 2:  # Year in yy format
                            date_obj = datetime.strptime(date_str, "%d-%m-%y")
                        else:  # Year in yyyy format
                            date_obj = datetime.strptime(date_str, "%d-%m-%Y")
                        new_date = date_obj.strftime("%Y-%m-%d")  # Change here to yyyy-mm-dd
                    except ValueError:
                        continue
                elif len(groups) == 4:  # Special ddmm-yyyy or dd-mmmyyyy formats
                    date_str = f"{groups[0]}-{groups[1]}-{groups[2]}"
                    try:
                        date_obj = datetime.strptime(date_str, "%d-%m-%Y")
                        new_date = date_obj.strftime("%Y-%m-%d")  # Change here to yyyy-mm-dd
                    except ValueError:
                        continue

        # If a valid date was found
        if new_date:
            # Construct the new filename (only the date)
            file_extension = os.path.splitext(filename)[1]
            new_filename = f"{new_date}{file_extension}"

            # Ensure new filename doesn't overwrite an existing file
            new_path = os.path.join(directory, new_filename)
            if os.path.exists(new_path):
                print(f"Skipping renaming {original_filename}: {new_filename} already exists.")
                continue

            # Rename the file
            original_path = os.path.join(directory, original_filename)
            try:
                os.rename(original_path, new_path)
                print(f"Renamed: {original_filename} -> {new_filename}")
            except OSError as e:
                print(f"Error renaming {original_filename}: {e}")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Standardize file naming and date format in a directory.")
    parser.add_argument("--path", help="Path to the directory containing the files to be renamed.")
    args = parser.parse_args()
  
    path = args.path if args.path else path
    
    # Call the function with the provided directory
    print(f"Renaming files in {args.path}...")
    standardize_date_format(path)
