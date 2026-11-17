"""Unit-aware descriptive summaries for the verified Krafla tables."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def _numeric_summary(
    frame: pd.DataFrame,
    value_column: str,
    variable: str,
    unit: str,
    data_origin: str,
    independence_group: str = "Not applicable",
) -> dict[str, object]:
    """Summarise one coherent numerical variable without pooling physical units."""
    values = pd.to_numeric(frame[value_column], errors="coerce")
    available = values.dropna()
    return {
        "data_origin": data_origin,
        "variable": variable,
        "unit": unit,
        "independence_group": independence_group,
        "records_considered": int(len(values)),
        "available_values": int(len(available)),
        "missing_values": int(values.isna().sum()),
        "minimum": available.min() if not available.empty else None,
        "maximum": available.max() if not available.empty else None,
        "mean": available.mean() if not available.empty else None,
        "median": available.median() if not available.empty else None,
        "standard_deviation_sample": available.std(ddof=1) if len(available) > 1 else None,
        "summary_note": "Descriptive model/seed values only; not an independent-event estimate.",
    }


def make_descriptive_statistics(cleaned: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Calculate counts and ranges only within meaningful variable/unit groups."""
    rows: list[dict[str, object]] = []
    segment_models = cleaned["segment_models_clean"]
    for (parameter, unit), subset in segment_models.groupby(["Parameter", "Unit"], dropna=False):
        rows.append(_numeric_summary(subset, "Best / reported numeric", str(parameter), str(unit), "Segment model best/reported value"))

    regression = cleaned["regression_data_clean"]
    regression_variables = [
        ("w0 dike opening (m)", "Dike opening", "m"),
        ("s fault slip (m)", "Fault slip", "m"),
        ("d dike top depth (km)", "Dike top depth", "km"),
        ("H dike height (km)", "Dike height", "km"),
        ("Surface extension (m)", "Surface extension", "m"),
    ]
    for column, label, unit in regression_variables:
        rows.append(_numeric_summary(regression, column, label, unit, "Regression seed table", "All seed rows (non-independent)"))
        for group, subset in regression.groupby("independence_group", dropna=False):
            rows.append(_numeric_summary(subset, column, label, unit, "Regression seed table", str(group)))
    return pd.DataFrame(rows)


def make_episode_completeness(episodes: pd.DataFrame) -> pd.DataFrame:
    """Provide a compact per-episode record of supplied versus missing numerics."""
    columns = [
        "traceable_episode_id",
        "Episode #",
        "Date (as given)",
        "Data status",
        "supported_numeric_measurement_count",
        "has_supported_numeric_measurement",
        "Opening (m) numeric",
        "Fault slip (m) numeric",
        "Dike top depth (km) numeric",
        "Seismic moment (N·m) numeric",
        "Source in the supplied papers",
    ]
    return episodes.loc[:, [column for column in columns if column in episodes.columns]].copy()
