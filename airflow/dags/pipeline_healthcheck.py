"""
Phase 1/2 smoke-test DAG. No real ETL — just proves the stack is wired:
  - deps installed in the image (pandas/bs4/duckdb/pyarrow/openpyxl)
  - the project repo is mounted at /opt/project
  - the data folders are visible and an Excel file is readable

Run it once after `docker compose up`. Delete once the real DAG lands (Phase 5).
"""
from __future__ import annotations

import glob
import os
from datetime import datetime

from airflow.decorators import dag, task

PROJECT_ROOT = "/opt/project"


@dag(
    dag_id="pipeline_healthcheck",
    schedule=None,            # manual trigger only
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["pgcb", "smoke-test"],
)
def pipeline_healthcheck():
    @task
    def check_deps() -> dict:
        import bs4, duckdb, openpyxl, pandas, pyarrow, requests
        return {
            "pandas": pandas.__version__,
            "pyarrow": pyarrow.__version__,
            "duckdb": duckdb.__version__,
            "bs4": bs4.__version__,
            "openpyxl": openpyxl.__version__,
            "requests": requests.__version__,
        }

    @task
    def check_mounts() -> dict:
        folders = sorted(glob.glob(os.path.join(PROJECT_ROOT, "daily_report*")))
        counts = {os.path.basename(f): len(os.listdir(f)) for f in folders if os.path.isdir(f)}
        if not counts:
            raise FileNotFoundError(f"No daily_report* folders under {PROJECT_ROOT} — mount broken")
        return counts

    @task
    def read_one_excel() -> dict:
        import pandas as pd
        # newest 2025-2026 file = .xlsx, read a cheap sheet to confirm engine works
        folder = os.path.join(PROJECT_ROOT, "daily_report (2025-01-01 to 2026-06-29)")
        # skip Excel lock/temp files (~$...) that aren't real workbooks
        files = sorted(
            f for f in glob.glob(os.path.join(folder, "*.xlsx"))
            if not os.path.basename(f).startswith("~$")
        )
        if not files:
            raise FileNotFoundError(f"No .xlsx in {folder}")
        target = files[-1]
        sheets = pd.ExcelFile(target, engine="openpyxl").sheet_names
        return {"file": os.path.basename(target), "sheet_count": len(sheets)}

    check_deps()
    check_mounts()
    read_one_excel()


pipeline_healthcheck()
