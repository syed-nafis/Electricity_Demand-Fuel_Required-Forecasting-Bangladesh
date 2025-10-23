"""
Two-tier load layer for the PGCB pipeline.

  Tier 1 (analytics, full history): partitioned Parquet under extracted_data/parquet/
  Tier 2 (serving, small tables):   upsert to Supabase Postgres for the dashboard

Both are idempotent — re-running a date overwrites that date's Parquet partition
and upserts (not duplicates) the Supabase rows. That makes the daily DAG safe to retry.

Env:
  SUPABASE_URL, SUPABASE_KEY   (service_role key; backend only)
  PROJECT_ROOT                 (optional; defaults to repo root = parent of script/)
"""
from __future__ import annotations

import os
from functools import lru_cache

import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds

PROJECT_ROOT = os.getenv(
    "PROJECT_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
PARQUET_ROOT = os.path.join(PROJECT_ROOT, "extracted_data", "parquet")


# ---------- Tier 1: Parquet ----------

def write_parquet(df: pd.DataFrame, dataset: str, partition_cols: list[str] | None = None) -> str:
    """Write df into extracted_data/parquet/<dataset>/, partitioned by DAY
    (year/month/day) so each date is an isolated partition. This is what makes the
    write idempotent at day granularity: re-writing a date (or an incremental write
    of one day) replaces only that day's file and can't clobber other days in the
    same year/month. If `date` is absent, falls back to the given partition_cols.

    NOTE: changing the partitioning scheme requires wiping the dataset dir first —
    you cannot mix `year=` and `year=/month=/day=` layouts in one dataset."""
    if df.empty:
        return ""
    df = df.copy()
    if "date" in df.columns:
        dt = pd.to_datetime(df["date"])
        df["year"], df["month"], df["day"] = dt.dt.year, dt.dt.month, dt.dt.day
        partition_cols = ["year", "month", "day"]
    out = os.path.join(PARQUET_ROOT, dataset)
    os.makedirs(out, exist_ok=True)
    table = pa.Table.from_pandas(df, preserve_index=False)
    ds.write_dataset(
        table,
        base_dir=out,
        format="parquet",
        partitioning=partition_cols,
        partitioning_flavor="hive" if partition_cols else None,
        existing_data_behavior="overwrite_or_ignore",
    )
    return out


# ---------- Tier 2: Supabase ----------

@lru_cache(maxsize=1)
def _client():
    from supabase import create_client
    url, key = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_KEY not set")
    return create_client(url, key)


def upsert(table: str, df: pd.DataFrame, on_conflict: str, chunk: int = 500,
           retries: int = 5) -> int:
    """Upsert df rows into a Supabase table, chunked. `on_conflict` = comma-joined
    PK columns. Returns row count sent. NaN -> None so Postgres gets nulls.

    Over a long backfill, Supabase's HTTP/2 connection periodically sends GOAWAY
    (httpx RemoteProtocolError). supabase-py doesn't retry, so we retry each chunk
    with a fresh client + backoff."""
    import time

    if df.empty:
        return 0
    records = df.astype(object).where(pd.notnull(df), None).to_dict("records")
    # dates/timestamps -> ISO strings for JSON transport
    for r in records:
        for k, v in r.items():
            if hasattr(v, "isoformat"):
                r[k] = v.isoformat()

    for i in range(0, len(records), chunk):
        batch = records[i : i + chunk]
        for attempt in range(retries):
            try:
                _client().table(table).upsert(batch, on_conflict=on_conflict).execute()
                break
            except Exception as e:  # noqa: BLE001
                transient = e.__class__.__name__ in (
                    "RemoteProtocolError", "ReadError", "ConnectError",
                    "ConnectTimeout", "ReadTimeout", "WriteError",
                )
                if attempt == retries - 1 or not transient:
                    raise
                _client.cache_clear()          # drop the dead connection
                time.sleep(2 ** attempt)       # 1,2,4,8s backoff
    return len(records)


def get_last_loaded_date(table: str, date_col: str = "date") -> str | None:
    """Max date already in a Supabase serving table — the incremental-state source
    that replaces the old db.get_last_downloaded_report() stub. None if table empty."""
    res = _client().table(table).select(date_col).order(date_col, desc=True).limit(1).execute()
    return res.data[0][date_col] if res.data else None
