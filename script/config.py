#   base URL for daily reports
base_url = "https://erp.powergrid.gov.bd/w/report/eyJpdiI6IldsU2ZQTGkvbkRnQU9FMjZ5UHhmeGc9PSIsInZhbHVlIjoiQzhONVl5ZGxRY3E3T3ZVNCtLZGt1Zz09IiwibWFjIjoiN2JiNTI5MzNhOWIxZDVjY2NkMmFlZWU4ZDU1N2I4OWZlYjNlZWM1ZGU4NzRiNWU4ZjQ3ZDc1ODRlMTk3MDc0YyIsInRhZyI6IiJ9/show_report?page=1"

#   Starting date of excel format change, they change from [.xls -> .xlsm -> .xlsx]
excel_format_change_date = [{'start_date': '2014-01-01','end_date': '2018-01-14','file_format': '.xls'},
                            {'start_date': '2018-01-15','end_date': '2024-12-31' ,'file_format': '.xlsm'},
                            {'start_date': '2025-01-01','end_date': 'current', 'file_format': '.xlsx'}
                           ]

#  Dates in file_names is not consistant, has oddities, so we will rename them to a standard format "YYYY-MM-DD.xlsm"
# Define the date patterns to match various formats
date_patterns = [
    r"(\d{2})[-._](\d{1,2})[-._](\d{2})",  # dd-mm-yy or dd.mm.yy or dd_mm_yy
    r"(\d{2})[-._](\d{1,2})[-._](\d{4})",  # dd-mm-yyyy or dd.mm.yyyy or dd_mm_yyyy
    r"(\d{2})(\d{1,2})[-._](\d{4})",      # ddmm-yyyy
    r"(\d{2})[-._](\d{1,2})(\d{4})"       # dd-mmmyyyy
]

# Special cases: filenames that should be directly renamed
# Will be updated as more oddities are found
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

plant_special_cases = {
    "kaptai45": "Chattogram",
    "kaptai123": "Chattogram",
    "summitmadhabdi": "Dhaka",
    "summitashulia": "Dhaka",
    "karnaphulihydro45": "Chattogram",
    "karnaphulihydro123": "Chattogram",
    "sikalbahagt150": "Chattogram",
    "sikalbaha150g": "Chattogram",
    "sikalbahaenergies": "Chattogram",
    "sikalbahaenergies55": "Chattogram",
    "sikalbahagt150": "Chattogram",
    "anlimaenergy116": "Chattogram",
    "khulna60": "Khulna"
}

# extracted dataframe structure for "powerplant_info" from each "daily_report" file
powerplantinfo_columns = ['powerplant_name',
                    'fuel', 
                    'installed_capacity', 
                    'present_capacity', 
                    'mw_lost_limitation', 
                    'mw_lost_m/c_problem', 
                    'reason',
                    'area']

# extracted dataframe structure for "powerplant_shutdown" from each "daily_report" file
powerplantshutdown_df = ['date',
                         'powerplant_name',
                         'reason',
                         'mw_lost_limitation',
                         'mw_lost_m/c_problem']

# power name versions

# Date: 2019-04-21.xlms has the powerplants named differently

