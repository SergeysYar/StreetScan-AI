"""Method comparison helpers."""
from __future__ import annotations

import pandas as pd


def compare(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate benchmark table by method."""
    return df.groupby("method", as_index=False).agg({"runtime": "mean", "fps": "mean", "cluster_count": "mean"})
