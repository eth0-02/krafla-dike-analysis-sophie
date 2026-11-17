"""Safe, traceable loading of the Krafla research workbook.

The loader never edits the source Excel file. It keeps workbook-specific logic
in one place so scientific processing code can work only with clean tables.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


EXPECTED_SHEETS = {
    "README",
    "Crisis_totals",
    "Segment_models",
    "Episodes",
    "Moment_calc",
    "Regression_ready",
    "Uncertainty_basis",
    "Paper_conflicts",
}

# These columns are required for the derivative datasets and scientific checks.
# README is intentionally excluded because it is narrative text rather than a table.
REQUIRED_COLUMNS: dict[str, set[str]] = {
    "Crisis_totals": {"ID", "Parameter", "Low", "Central (as reported)", "High", "Unit", "Source", "Confidence"},
    "Segment_models": {"ID", "Segment", "Dataset / model", "Parameter", "Best / reported", "Low (approx.)", "High (approx.)", "Unit", "σ assigned (range/4)", "Source", "Type", "Confidence"},
    "Episodes": {"Episode #", "Date (as given)", "What the papers say", "Opening (m)", "Fault slip (m)", "Dike top depth (km)", "Data status"},
    "Moment_calc": {"Quantity", "Low", "High", "Unit"},
    "Regression_ready": {"Case", "Unit of observation", "w0 dike opening (m)", "s fault slip (m)", "d dike top depth (km)", "Source", "Confidence"},
    "Uncertainty_basis": {"Quantity", "What the paper says about its uncertainty", "Where", "How to use it"},
    "Paper_conflicts": {"#", "Item", "What the papers say", "How I handled it"},
}


@dataclass(frozen=True)
class WorkbookData:
    """Loaded workbook tables and the path they came from."""

    source_path: Path
    sheets: dict[str, pd.DataFrame]


def clean_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Remove blank rows and unlabelled blank columns, leaving real fields intact.

    A named but blank column can be an intentional part of the research schema
    (for example, a central estimate not supplied by a source). It must not be
    discarded merely because all of its values are currently missing.
    """
    # Excel separator rows may contain empty strings rather than true nulls.
    # Treat whitespace-only cells as blank for the sole purpose of dropping rows
    # that have no data at all; named columns and genuine missing values remain.
    blank_cells = frame.isna() | frame.map(lambda value: isinstance(value, str) and not value.strip())
    cleaned = frame.loc[~blank_cells.all(axis=1)].copy()
    unnamed_blank_columns = [
        column for column in cleaned.columns
        if str(column).strip().lower().startswith("unnamed") and cleaned[column].isna().all()
    ]
    cleaned = cleaned.drop(columns=unnamed_blank_columns)
    if not isinstance(cleaned.columns, pd.RangeIndex):
        cleaned.columns = [str(column).strip() for column in cleaned.columns]
    return cleaned


def validate_sheet_structure(sheets: dict[str, pd.DataFrame]) -> list[str]:
    """Return structural errors instead of silently accepting an incompatible file."""
    errors: list[str] = []
    missing_sheets = EXPECTED_SHEETS.difference(sheets)
    if missing_sheets:
        errors.append(f"Missing required worksheets: {', '.join(sorted(missing_sheets))}.")
    for sheet, required in REQUIRED_COLUMNS.items():
        if sheet not in sheets:
            continue
        missing_columns = required.difference(sheets[sheet].columns)
        if missing_columns:
            errors.append(f"{sheet} is missing columns: {', '.join(sorted(missing_columns))}.")
    return errors


def load_workbook(path: Path) -> WorkbookData:
    """Load all expected sheets with their original headers and source values."""
    if not path.is_file():
        raise FileNotFoundError(f"Input workbook not found: {path}")

    book = pd.ExcelFile(path)
    sheets: dict[str, pd.DataFrame] = {}
    for sheet in book.sheet_names:
        # The README contains narrative prose, not a conventional header row.
        header = None if sheet == "README" else 0
        sheets[sheet] = clean_table(pd.read_excel(path, sheet_name=sheet, header=header))

    errors = validate_sheet_structure(sheets)
    if errors:
        raise ValueError("Workbook validation failed:\n- " + "\n- ".join(errors))
    return WorkbookData(source_path=path.resolve(), sheets=sheets)
