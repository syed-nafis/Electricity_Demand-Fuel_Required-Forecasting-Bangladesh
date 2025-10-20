import pandas as pd
import re
from config import powerplantshutdown_df

#   structure of the dataframe is defined in config.py
"""
extracted dataframe structure for "powerplant_shutdown" from each "daily_report" file
powerplantshutdown_df = ['date',
                         'powerplant_name',
                         'reason',
                         'mw_lost_limitation',
                         'mw_lost_m/c_problem']
"""

def extract_powerplant_shutdown_data(df,file_name):
        # convert file_name to pandas date/time
        # extract the date from the file_name by removing any extensions
        date_string = file_name.split('.')[0]
        date = pd.to_datetime(date_string, errors='coerce').date()
        shutdown_df = pd.DataFrame(columns=powerplantshutdown_df)

        # keep all the columns in df that have a value in 'reason' column i.e is shutdown for some reason
        df = df[df['Reason'].notna()]

        shutdown_df['powerplant_name'] = df['Power Plant Name']
        shutdown_df['reason'] = df['Reason']
        shutdown_df['mw_lost_limitation'] = df['MW Lost (Limitation)']
        shutdown_df['mw_lost_m/c_problem'] = df['MW Lost (M/C Problem)']
        shutdown_df['date'] = date

        return shutdown_df