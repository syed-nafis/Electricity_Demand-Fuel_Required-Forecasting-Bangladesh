"""
Phase 5d — hourly backfill for 2019-2024 (YesterdayGen sheet).

Extends the hourly STLF dataset back to 2019: the 2025-2026 GenLog backfill already
filled hourly_plant_generation for those years; this fills 2019-2024 from the
YesterdayGen hourly block. Parquet only (raw STLF series), no Supabase.
"""
from __future__ import annotations

import glob
import os
from datetime import datetime

import pandas as pd
from airflow.decorators import dag, task

PROJECT_ROOT = "/opt/project"
SOURCE_DIR = os.path.join(PROJECT_ROOT, "daily_report")
HOURLY_DATASET = "hourly_plant_generation"


@dag(
    dag_id="backfill_hourly_2019_2024",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["pgcb", "backfill", "hourly"],
    params={"start": "2019-01-01", "end": "2024-12-31", "max_files": 0},
)
def backfill_hourly_2019_2024():
    @task
    def list_reports(params: dict) -> list[str]:
        files = []
        for f in sorted(glob.glob(os.path.join(SOURCE_DIR, "*.xlsm"))):
            name = os.path.basename(f)
            if name.startswith("~$"):
                continue
            d = name.rsplit(".", 1)[0]
            if params["start"] <= d <= params["end"]:
                files.append(f)
        if params.get("max_files"):
            files = files[: int(params["max_files"])]
        if not files:
            raise ValueError(f"No .xlsm in {SOURCE_DIR} within range")
        print(f"{len(files)} reports ({files[0]} .. {files[-1]})")
        return files

    @task
    def extract_and_load(files: list[str]) -> dict:
        from extract_powerplant_generation_data import process_yesterdaygen_hourly
        import load

        frames, errors = [], []
        for f in files:
            try:
                df = process_yesterdaygen_hourly(f)
                if df is not None and not df.empty:
                    frames.append(df)
            except Exception as e:  # noqa: BLE001
                errors.append({"file": os.path.basename(f), "error": str(e)[:200]})

        if not frames:
            raise RuntimeError(f"0 hourly rows; {len(errors)} errors")

        hourly = pd.concat(frames, ignore_index=True)
        hourly["date"] = pd.to_datetime(hourly["date"])
        hourly["year"] = hourly["date"].dt.year
        path = load.write_parquet(hourly, HOURLY_DATASET, partition_cols=["year"])

        result = {
            "files": len(files),
            "hourly_rows": int(len(hourly)),
            "parquet_path": path,
            "error_count": len(errors),
            "errors": errors[:10],
        }
        print(result)
        return result

    extract_and_load(list_reports())


backfill_hourly_2019_2024()
