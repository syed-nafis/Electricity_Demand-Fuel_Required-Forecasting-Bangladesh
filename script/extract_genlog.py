"""
Extractor for the 2025+ daily-report format, whose generation sheet is `GenLog`
(2026) / `Genlog` (2025) — case varies. It replaces the 2019-2024 `YesterdayGen`
sheet but is laid out transposed:

    row 10  ("Hour" in col 0): plant names across columns 1..N
    row 11                    : installed/present capacity ("102.000 MW")
    rows 12-36                : hourly MW per plant (00:00..23:00, plus a 19:30 peak)
    row 37  ("Total KWH")     : daily total kWh per plant

Tail columns are aggregates, not plants: "Western Total", "National Grid Total",
"Water Level" — filtered out here.

Two entry points:
  process_genlog(path)        -> daily per-plant, same schema as the YesterdayGen
                                 extractor (date, plant_name, electricity_gen, fuel_cost)
                                 so it feeds the SAME daily_plant_generation table.
                                 fuel_cost is None (GenLog has no fuel cost).
  process_genlog_hourly(path) -> long hourly series (date, time, plant_name, mw)
                                 — the core STLF dataset.
"""
from __future__ import annotations

import os
import re

import pandas as pd

_NONPLANT = re.compile(r"(?i)(total|water level)")
_TIME = re.compile(r"^\d{1,2}:\d{2}$")


def _load_genlog(path: str) -> pd.DataFrame:
    xl = pd.ExcelFile(path, engine="openpyxl")
    matches = [s for s in xl.sheet_names if s.lower() == "genlog"]
    if not matches:
        raise ValueError(f"No GenLog/Genlog sheet in {os.path.basename(path)}")
    return xl.parse(matches[0], header=None)


def _markers(g: pd.DataFrame) -> tuple[int, int]:
    col0 = g.iloc[:, 0].astype(str).str.strip()
    hdr = g.index[col0 == "Hour"]
    tot = g.index[col0.str.lower() == "total kwh"]
    if len(hdr) == 0 or len(tot) == 0:
        raise ValueError("GenLog layout markers ('Hour' / 'Total KWH') not found")
    return int(hdr[0]), int(tot[0])


def _date(path: str):
    return pd.to_datetime(os.path.basename(path).rsplit(".", 1)[0])


def _plant_cols(g: pd.DataFrame, hdr: int) -> dict[int, str]:
    """{column_index: plant_name} for real plants only (aggregates filtered)."""
    cols = {}
    for ci, v in g.iloc[hdr, 1:].items():
        if pd.isna(v):
            continue
        name = str(v).strip()
        if name and not _NONPLANT.search(name):
            cols[ci] = name
    return cols


def _to_num(values) -> pd.Series:
    s = pd.Series(values).astype(str).str.replace(r"[\s\xa0,]", "", regex=True)
    return pd.to_numeric(s.replace({"": None, "nan": None, "None": None}), errors="coerce")


def process_genlog(path: str) -> pd.DataFrame:
    """Daily per-plant total generation. Same columns as the YesterdayGen extractor."""
    g = _load_genlog(path)
    hdr, tot = _markers(g)
    date = _date(path)
    cols = _plant_cols(g, hdr)
    kwh_row = g.iloc[tot]
    df = pd.DataFrame(
        {
            "date": date,
            "plant_name": list(cols.values()),
            "electricity_gen": [kwh_row[ci] for ci in cols],
            "fuel_cost": None,
        }
    )
    df["electricity_gen"] = _to_num(df["electricity_gen"])
    return df


def process_genlog_hourly(path: str) -> pd.DataFrame:
    """Long-format hourly MW per plant: date, time (HH:MM), plant_name, mw."""
    g = _load_genlog(path)
    hdr, tot = _markers(g)
    date = _date(path)
    cols = _plant_cols(g, hdr)
    out = []
    for ri in range(hdr + 1, tot):                       # skips capacity row (col0 NaN)
        label = g.iloc[ri, 0]
        if pd.isna(label) or not _TIME.match(str(label).strip()):
            continue
        t = str(label).strip()
        for ci, nm in cols.items():
            out.append({"date": date, "time": t, "plant_name": nm, "mw": g.iloc[ri, ci]})
    df = pd.DataFrame(out)
    if not df.empty:
        df["mw"] = _to_num(df["mw"])
    return df


def process_generation_auto(path: str):
    """Route by whichever generation sheet the file has. Returns
    (daily_df, hourly_df_or_None). GenLog (2025+) gives hourly; the older
    YesterdayGen (2019-2024) gives daily only."""
    sheets = {s.lower() for s in pd.ExcelFile(path, engine="openpyxl").sheet_names}
    if "genlog" in sheets:
        return process_genlog(path), process_genlog_hourly(path)
    if "yesterdaygen" in sheets:
        from extract_powerplant_generation_data import process_daily_report
        return process_daily_report(path), None
    raise ValueError(f"No generation sheet (genlog/yesterdaygen) in {os.path.basename(path)}")


if __name__ == "__main__":
    import argparse, glob

    ap = argparse.ArgumentParser(description="Extract GenLog (2025+) generation data")
    ap.add_argument("--path", required=True, help="a daily report .xlsx or a folder of them")
    ap.add_argument("--hourly", action="store_true", help="emit hourly series instead of daily totals")
    a = ap.parse_args()

    files = (
        sorted(f for f in glob.glob(os.path.join(a.path, "*.xlsx")) if not os.path.basename(f).startswith("~$"))
        if os.path.isdir(a.path)
        else [a.path]
    )
    fn = process_genlog_hourly if a.hourly else process_genlog
    frames, errs = [], []
    for f in files:
        try:
            frames.append(fn(f))
        except Exception as e:  # noqa: BLE001
            errs.append((os.path.basename(f), str(e)[:120]))
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    print(f"files={len(files)} rows={len(df)} errors={len(errs)}")
    print(df.head(10).to_string())
    for name, e in errs[:10]:
        print("ERR", name, e)
