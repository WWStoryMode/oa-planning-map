"""ONSPD loading and postcode normalization helpers."""

import re

import pandas as pd

DEFAULT_COLUMNS = ["pcds", "east1m", "north1m", "doterm", "lad25cd"]


def normalize_postcode(pc) -> str:
    """Uppercase, strip, and collapse internal whitespace to a single space."""
    if pd.isna(pc):
        return ""
    return re.sub(r"\s+", " ", str(pc).strip().upper())


def load_live_postcodes(
    nspl_csv: str,
    lad_codes: set[str] | None = None,
    lad_prefix: str | None = None,
    columns: list[str] = DEFAULT_COLUMNS,
) -> pd.DataFrame:
    """Load live (non-terminated) postcodes from an ONSPD/NSPL CSV export.

    Filter by an exact set of lad25cd codes, or by a lad25cd prefix
    (e.g. "E09" for all Greater London boroughs). Passing neither returns
    every live postcode in the file.
    """
    df = pd.read_csv(
        nspl_csv,
        usecols=columns,
        dtype={"doterm": "string"},
        low_memory=False,
    )
    df = df[df["doterm"].isna()]
    if lad_codes is not None:
        df = df[df["lad25cd"].isin(lad_codes)]
    elif lad_prefix is not None:
        df = df[df["lad25cd"].str.startswith(lad_prefix)]
    if "east1m" in df.columns and "north1m" in df.columns:
        df = df.dropna(subset=["east1m", "north1m"])
    return df.reset_index(drop=True)
