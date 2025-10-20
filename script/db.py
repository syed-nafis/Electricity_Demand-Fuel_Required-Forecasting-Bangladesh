import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client


# Load environment variables from the .env file
load_dotenv()

# Supabase client (singleton)
_SUPABASE_CLIENT = None
_AREA_MAPPINGS = None
_POWERPLANT_MAPPINGS = None

def get_supabase_client():
    global _SUPABASE_CLIENT
    if _SUPABASE_CLIENT is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Supabase URL/KEY missing. Check .env file.")
        _SUPABASE_CLIENT = create_client(url, key)
    return _SUPABASE_CLIENT

def get_last_downloaded_report():
    supabase = get_supabase_client()
    
def get_area_mappings():
    supabase = get_supabase_client()

    global _AREA_MAPPINGS
    if _AREA_MAPPINGS is None:
        try:
            response = supabase.table("Area").select("id,area").execute()
        except Exception as e:
            print(f"Error reading data: {e}")

        _AREA_MAPPINGS = {mapping['area']: mapping['id'] for mapping in response.data}
    
    return _AREA_MAPPINGS