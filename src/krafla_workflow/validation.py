"""Data-quality checks and explicit classification of regression independence."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from .data_loader import WorkbookData


REGRESSION_NUMERIC_COLUMNS = [
    "w0 dike opening (m)",
    "σ w0",
    "s fault slip (m)",
    "σ s",
    "d dike top depth (km)",
    "σ d",
    "H dike height (km)",
    "σ H",
    "Surface extension (m)",
    "σ ext",
]


def numeric_observation_rows(frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Keep rows with at least one numerical observation, excluding prose notes."""
    numeric = frame.copy()
    available = [column for column in columns if column in numeric.columns]
    for column in available:
        numeric[column] = pd.to_numeric(numeric[column], errors="coerce")
    return numeric.loc[numeric[available].notna().any(axis=1)].copy()


def classify_independence(regression_rows: pd.DataFrame) -> pd.DataFrame:
    """Attach a conservative geological-event grouping to seed model rows.

    This classification is a data-management aid, not a claim that the source
    values are direct measurements. South entries are alternative cumulative
    models; north entries are alternative/multi-fault estimates of Jan 1978.
    Neither group provides replicate independent events.
    """
    classified = regression_rows.copy()
    groups: list[str] = []
    statuses: list[str] = []
    scopes: list[str] = []
    reasons: list[str] = []
    for case, observation in zip(classified["Case"].fillna(""), classified["Unit of observation"].fillna("")):
        case_text = str(case).lower()
        observation_text = str(observation).lower()
        if "south" in case_text:
            groups.append("South cumulative deformation")
            statuses.append("Alternative model estimate; not an independent replicate")
            scopes.append("Cumulative deformation across many dikes")
        elif "north" in case_text:
            groups.append("North January 1978 dike")
            statuses.append("Same event / alternative or multi-fault estimate; not an independent replicate")
            scopes.append("Single dike, January 1978")
        else:
            groups.append("Unclassified")
            statuses.append("Independence cannot be established from supplied workbook")
            scopes.append(observation_text or "Not stated")
        reasons.append("Only two geological configurations are represented; do not use for inferential regression.")
    classified["independence_group"] = groups
    classified["independence_status"] = statuses
    classified["deformation_scope"] = scopes
    classified["eligible_for_inferential_regression"] = False
    classified["regression_exclusion_reason"] = reasons
    return classified


def make_data_quality_report(workbook: WorkbookData, regression_rows: pd.DataFrame) -> pd.DataFrame:
    """Create a compact, machine-readable audit of completeness and caveats."""
    rows: list[dict[str, object]] = []
    for sheet_name, frame in workbook.sheets.items():
        unit_values = ""
        if "Unit" in frame.columns:
            unit_values = "; ".join(sorted(str(value) for value in frame["Unit"].dropna().unique()))
        rows.append({
            "sheet": sheet_name,
            "record_count": len(frame),
            "column_count": len(frame.columns),
            "duplicate_row_count": int(frame.duplicated().sum()),
            "missing_cell_count": int(frame.isna().sum().sum()),
            "non_missing_cell_count": int(frame.notna().sum().sum()),
            "units_present": unit_values,
            "quality_note": "Raw values retained; blank cells are not imputed.",
        })

    rows.extend([
        {
            "sheet": "Regression_ready",
            "record_count": len(regression_rows),
            "column_count": len(regression_rows.columns),
            "duplicate_row_count": int(regression_rows.duplicated().sum()),
            "missing_cell_count": int(regression_rows.isna().sum().sum()),
            "non_missing_cell_count": int(regression_rows.notna().sum().sum()),
            "units_present": "opening/slip: m; top depth/height: km",
            "quality_note": "Five numerical seed rows; four rows contain both opening and slip; only two independence groups.",
        },
        {
            "sheet": "Scientific limitations",
            "record_count": int(regression_rows["independence_group"].nunique()),
            "column_count": 0,
            "duplicate_row_count": 0,
            "missing_cell_count": 0,
            "non_missing_cell_count": 0,
            "units_present": "",
            "quality_note": "Alternative models, two faults in one event, and cumulative-versus-single-event values must not be pooled as independent observations.",
        },
    ])
    return pd.DataFrame(rows)
