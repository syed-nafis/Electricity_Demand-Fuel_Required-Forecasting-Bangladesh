"""
Phase 5b — backfill DAG for the 2025+ GenLog format.

Mirrors backfill_generation_2019_2024 but uses the GenLog extractor:
  daily totals  -> same two-tier (Parquet daily_plant_generation + Supabase)
  hourly MW     -> Parquet only, dataset hourly_plant_generation (STLF dataset, Paper 1)

3 transitional Jan-2025 files have no GenLog sheet (2025-01-03 is old yesterdayGen;
2025-01-16/19 have no generation sheet) — they surface as errors, not failures.
"""
from __future__ import annotations

import glob
import os
from datetime import datetime

import pandas as pd
from airflow.decorators import dag, task

PROJECT_ROOT = "/opt/project"
SOURCE_DIR = os.path.join(PROJECT_ROOT, "daily_report (2025-01-01 to 2026-06-29)")
DAILY_DATASET = "daily_plant_generation"
HOURLY_DATASET = "hourly_plant_generation"
TABLE = "daily_plant_generation"


@dag(
    dag_id="backfill_generation_2025_2026",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["pgcb", "backfill", "generation", "genlog"],
    params={"start": "2025-01-01", "end": "2026-12-31", "max_files": 0,
            "load_supabase": True, "load_hourly": True},
)
def backfill_generation_2025_2026():
    @task
    def list_reports(params: dict) -> list[str]:
        files = []
        for f in sorted(glob.glob(os.path.join(SOURCE_DIR, "*.xlsx"))):
            name = os.path.basename(f)
            if name.startswith("~$"):
                continue
            d = name.rsplit(".", 1)[0]
            if params["start"] <= d <= params["end"]:
                files.append(f)
        if params.get("max_files"):
            files = files[: int(params["max_files"])]
        if not files:
            raise ValueError(f"No .xlsx in {SOURCE_DIR} within range")
        print(f"{len(files)} reports ({files[0]} .. {files[-1]})")
        return files

    @task
    def extract_and_load(files: list[str], params: dict) -> dict:
        from extract_genlog import process_genlog, process_genlog_hourly
        import load

        daily_frames, hourly_frames, errors = [], [], []
        for f in files:
            try:
                d = process_genlog(f)
                if not d.empty:
                    daily_frames.append(d)
                if params.get("load_hourly"):
                    h = process_genlog_hourly(f)
                    if not h.empty:
                        hourly_frames.append(h)
            except Exception as e:  # noqa: BLE001
                errors.append({"file": os.path.basename(f), "error": str(e)[:200]})

        if not daily_frames:
            raise RuntimeError(f"0 daily rows; {len(errors)} errors")

        # --- daily: two-tier (same table/dataset as 2019-2024) ---
        daily = pd.concat(daily_frames, ignore_index=True)
        daily["date"] = pd.to_datetime(daily["date"])
        daily["year"] = daily["date"].dt.year
        daily = daily[["date", "plant_name", "electricity_gen", "fuel_cost", "year"]]
        parquet_daily = load.write_parquet(daily, DAILY_DATASET, partition_cols=["year"])

        sent = 0
        if params.get("load_supabase"):
            serving = (
                daily.drop(columns=["year"])
                .groupby(["date", "plant_name"], as_index=False)[["electricity_gen", "fuel_cost"]]
                .sum(min_count=1)
                .rename(columns={"electricity_gen": "electricity_gen_kwh"})
            )
            serving["date"] = serving["date"].dt.date
            sent = load.upsert(TABLE, serving, on_conflict="date,plant_name")

        # --- hourly: Parquet only (raw STLF series) ---
        parquet_hourly, hourly_rows = "", 0
        if hourly_frames:
            hourly = pd.concat(hourly_frames, ignore_index=True)
            hourly["date"] = pd.to_datetime(hourly["date"])
            hourly["year"] = hourly["date"].dt.year
            hourly_rows = len(hourly)
            parquet_hourly = load.write_parquet(hourly, HOURLY_DATASET, partition_cols=["year"])

        result = {
            "files": len(files),
            "daily_rows": int(len(daily)),
            "hourly_rows": int(hourly_rows),
            "supabase_rows_upserted": sent,
            "parquet_daily": parquet_daily,
            "parquet_hourly": parquet_hourly,
            "error_count": len(errors),
            "errors": errors[:10],
        }
        print(result)
        return result

    extract_and_load(list_reports())


backfill_generation_2025_2026()
