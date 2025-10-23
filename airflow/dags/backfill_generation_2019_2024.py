"""
Phase 5 — backfill DAG: existing 2019-2024 daily reports -> two-tier load.

For each daily report in the date range:
  extract per-plant generation (YesterdayGen sheet)
   -> Tier 1: partitioned Parquet  (extracted_data/parquet/daily_plant_generation/year=YYYY/)
   -> Tier 2: upsert Supabase      (daily_plant_generation, PK=(date, plant_name))

Both tiers are idempotent, so the DAG is safe to re-run. Manual trigger only.
Scope is 2019-2024 (YesterdayGen format). 2025+ (GenLog format) needs a separate
extractor — deferred.

Trigger with optional conf to test a slice, e.g.:
  {"start": "2024-12-01", "end": "2024-12-31", "max_files": 5, "load_supabase": false}
"""
from __future__ import annotations

import glob
import os
from datetime import datetime

import pandas as pd
from airflow.decorators import dag, task

PROJECT_ROOT = "/opt/project"
SOURCE_DIR = os.path.join(PROJECT_ROOT, "daily_report")          # 2019-2024 .xlsm
DATASET = "daily_plant_generation"
TABLE = "daily_plant_generation"


@dag(
    dag_id="backfill_generation_2019_2024",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["pgcb", "backfill", "generation"],
    params={"start": "2019-01-01", "end": "2024-12-31", "max_files": 0, "load_supabase": True},
)
def backfill_generation_2019_2024():
    @task
    def list_reports(params: dict) -> list[str]:
        start, end = params["start"], params["end"]
        files = []
        for f in sorted(glob.glob(os.path.join(SOURCE_DIR, "*.xlsm"))):
            name = os.path.basename(f)
            if name.startswith("~$"):
                continue
            date_str = name.rsplit(".", 1)[0]
            if start <= date_str <= end:
                files.append(f)
        if params.get("max_files"):
            files = files[: int(params["max_files"])]
        if not files:
            raise ValueError(f"No .xlsm in {SOURCE_DIR} within {start}..{end}")
        print(f"{len(files)} reports to process ({files[0]} .. {files[-1]})")
        return files

    @task
    def extract_and_load(files: list[str], params: dict) -> dict:
        from extract_powerplant_generation_data import process_daily_report
        import load

        frames, errors = [], []
        for f in files:
            try:
                df = process_daily_report(f)
                if df is not None and not df.empty:
                    frames.append(df)
            except Exception as e:  # noqa: BLE001 — keep going, collect failures
                errors.append({"file": os.path.basename(f), "error": str(e)[:200]})

        if not frames:
            raise RuntimeError(f"Extracted 0 rows; {len(errors)} errors")

        all_df = pd.concat(frames, ignore_index=True)
        all_df["date"] = pd.to_datetime(all_df["date"])
        all_df["year"] = all_df["date"].dt.year

        # Some reports store numbers as strings with non-breaking spaces / commas
        # (e.g. '\xa0853440') -> object dtype that breaks Parquet + Supabase.
        # Strip formatting chars and coerce; unparseable -> NaN.
        for col in ["electricity_gen", "fuel_cost"]:
            cleaned = all_df[col].astype(str).str.replace(r"[\s\xa0,]", "", regex=True)
            all_df[col] = pd.to_numeric(cleaned.replace({"": None, "nan": None, "None": None}), errors="coerce")
        out_cols = ["date", "plant_name", "electricity_gen", "fuel_cost", "year"]
        all_df = all_df[out_cols]

        # Tier 1 — Parquet
        parquet_path = load.write_parquet(all_df, DATASET, partition_cols=["year"])

        # Tier 2 — Supabase. Parquet (Tier 1) keeps raw rows; the serving table has a
        # (date, plant_name) PK, but the extractor's name-cleaning collides distinct
        # units to the same name -> dup PKs in a batch -> upsert error 21000.
        # Aggregate by (date, plant_name) sum so each PK is unique.
        sent = 0
        if params.get("load_supabase"):
            # exclude aggregate/summary rows (e.g. "Eastern Grid Total") from the
            # plant-level serving table; Parquet (Tier 1) already kept them.
            agg_pat = r"(?i)(?:grid total|grand total|area total|^total$)"
            plant_only = all_df[~all_df["plant_name"].astype(str).str.contains(agg_pat, regex=True, na=False)]
            serving = (
                plant_only.drop(columns=["year"])
                .groupby(["date", "plant_name"], as_index=False)[["electricity_gen", "fuel_cost"]]
                .sum()
                .rename(columns={"electricity_gen": "electricity_gen_kwh"})
            )
            serving["date"] = serving["date"].dt.date
            sent = load.upsert(TABLE, serving, on_conflict="date,plant_name")

        result = {
            "files": len(files),
            "rows": int(len(all_df)),
            "parquet_path": parquet_path,
            "supabase_rows_upserted": sent,
            "error_count": len(errors),
            "errors": errors[:10],
        }
        print(result)
        return result

    params_files = list_reports()
    extract_and_load(params_files)


backfill_generation_2019_2024()
