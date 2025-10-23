"""
Phase 5c — daily incremental ETL (the production pipeline).

Each run:
  1. find_new_reports : last-loaded date (Supabase) -> scrape PGCB listing ->
                        reports newer than that and not already on disk
  2. download_reports : fetch only those, saved as yyyy-mm-dd.<ext>
  3. extract_and_load : auto-route extractor -> two-tier load
                        (daily -> Parquet + Supabase ; hourly -> Parquet)

Idempotent and self-healing: if a day is missed, the next run catches every report
on the listing page that's still missing. No new reports -> tasks short-circuit.

Incoming files land in daily_report_incremental/ (GenLog format for current dates).
"""
from __future__ import annotations

import os
import re
import warnings
from datetime import datetime

import pandas as pd
from airflow.decorators import dag, task

warnings.filterwarnings("ignore")

PROJECT_ROOT = "/opt/project"
TARGET_DIR = os.path.join(PROJECT_ROOT, "daily_report_incremental")
TABLE = "daily_plant_generation"
DAILY_DATASET = "daily_plant_generation"
HOURLY_DATASET = "hourly_plant_generation"

_TITLE_DATE = re.compile(r"(\d{2})-(\d{2})-(\d{4})")   # DD-MM-YYYY in "Daily Report 30-06-2026"


@dag(
    dag_id="daily_incremental_etl",
    schedule="@daily",
    start_date=datetime(2026, 6, 30),
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": __import__("datetime").timedelta(minutes=5)},
    tags=["pgcb", "incremental", "production"],
    params={"pages": 2, "load_supabase": True, "load_hourly": True},
)
def daily_incremental_etl():
    @task
    def find_new_reports(params: dict) -> list[dict]:
        import bs4, requests
        from urllib.parse import urlparse, parse_qs
        from config import base_url
        import load

        try:
            last = load.get_last_loaded_date(TABLE)          # 'YYYY-MM-DD' or None
        except Exception as e:  # noqa: BLE001
            print(f"Supabase last-date lookup failed ({e}); will dedup by disk only")
            last = None
        print("last loaded date:", last)

        on_disk = set()
        if os.path.isdir(TARGET_DIR):
            on_disk = {f.rsplit(".", 1)[0] for f in os.listdir(TARGET_DIR)}

        root = base_url.split("page=")[0] + "page="
        found: dict[str, dict] = {}
        for p in range(1, int(params["pages"]) + 1):
            r = requests.get(root + str(p), verify=False, timeout=30)
            soup = bs4.BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=lambda h: h and "erp.powergrid.gov.bd/web/files/download" in h):
                href = a["href"]
                title = parse_qs(urlparse(href).query).get("title", [None])[0]
                if not title:
                    continue
                m = _TITLE_DATE.search(title)
                if not m:
                    continue
                dd, mm, yyyy = m.groups()
                date_iso = f"{yyyy}-{mm}-{dd}"
                if last and date_iso <= last:
                    continue
                if date_iso in on_disk:
                    continue
                found[date_iso] = {"date": date_iso, "href": href}

        new = sorted(found.values(), key=lambda d: d["date"])
        print(f"{len(new)} new report(s): {[d['date'] for d in new]}")
        return new

    @task.short_circuit
    def has_new(new: list[dict]) -> bool:
        return bool(new)

    @task
    def download_reports(new: list[dict]) -> list[str]:
        from bs4_downloader import download_file

        os.makedirs(TARGET_DIR, exist_ok=True)
        paths = []
        for item in new:
            download_file(item["href"], TARGET_DIR, title=item["date"])  # saves <date>.<ext>
            hit = [f for f in os.listdir(TARGET_DIR) if f.startswith(item["date"] + ".")]
            if hit:
                paths.append(os.path.join(TARGET_DIR, hit[0]))
            else:
                print(f"WARN: download produced no file for {item['date']}")
        print(f"downloaded {len(paths)} file(s)")
        return paths

    @task
    def extract_and_load(paths: list[str], params: dict) -> dict:
        from extract_genlog import process_generation_auto
        import load

        daily_frames, hourly_frames, errors = [], [], []
        for f in paths:
            try:
                daily, hourly = process_generation_auto(f)
                if daily is not None and not daily.empty:
                    daily_frames.append(daily)
                if params.get("load_hourly") and hourly is not None and not hourly.empty:
                    hourly_frames.append(hourly)
            except Exception as e:  # noqa: BLE001
                errors.append({"file": os.path.basename(f), "error": str(e)[:200]})

        if not daily_frames:
            raise RuntimeError(f"0 daily rows from {len(paths)} file(s); errors={errors}")

        daily = pd.concat(daily_frames, ignore_index=True)
        daily["date"] = pd.to_datetime(daily["date"])
        daily["year"] = daily["date"].dt.year
        daily = daily[["date", "plant_name", "electricity_gen", "fuel_cost", "year"]]
        for col in ["electricity_gen", "fuel_cost"]:
            cleaned = daily[col].astype(str).str.replace(r"[\s\xa0,]", "", regex=True)
            daily[col] = pd.to_numeric(cleaned.replace({"": None, "nan": None, "None": None}), errors="coerce")
        load.write_parquet(daily, DAILY_DATASET, partition_cols=["year"])

        sent = 0
        if params.get("load_supabase"):
            agg = r"(?i)(?:grid total|grand total|area total|^total$)"
            plant = daily[~daily["plant_name"].astype(str).str.contains(agg, regex=True, na=False)]
            serving = (
                plant.drop(columns=["year"])
                .groupby(["date", "plant_name"], as_index=False)[["electricity_gen", "fuel_cost"]]
                .sum(min_count=1)
                .rename(columns={"electricity_gen": "electricity_gen_kwh"})
            )
            serving["date"] = serving["date"].dt.date
            sent = load.upsert(TABLE, serving, on_conflict="date,plant_name")

        if hourly_frames:
            hourly = pd.concat(hourly_frames, ignore_index=True)
            hourly["date"] = pd.to_datetime(hourly["date"])
            hourly["year"] = hourly["date"].dt.year
            load.write_parquet(hourly, HOURLY_DATASET, partition_cols=["year"])

        result = {
            "files": len(paths),
            "daily_rows": int(len(daily)),
            "supabase_rows_upserted": sent,
            "error_count": len(errors),
            "errors": errors,
        }
        print(result)
        return result

    new = find_new_reports()
    gate = has_new(new)
    paths = download_reports(new)
    gate >> paths
    extract_and_load(paths)


daily_incremental_etl()
