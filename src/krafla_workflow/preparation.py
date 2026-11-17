"""Creation of traceable, cleaned derivative research datasets."""

from __future__ import annotations

import pandas as pd

from .data_loader import WorkbookData
from .validation import REGRESSION_NUMERIC_COLUMNS, classify_independence, numeric_observation_rows


def _measurement_category(parameter: object) -> str:
    text = str(parameter).lower()
    if "dike" in text and "opening" in text:
        return "Dike opening"
    if "fault" in text and "slip" in text:
        return "Fault slip"
    if "depth" in text or "top" in text or "width" in text or "height" in text:
        return "Dike geometry"
    return "Other model parameter"


def clean_crisis_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Keep source fields while adding typed numerical bounds for analysis."""
    cleaned = frame.copy()
    for column in ["Low", "Central (as reported)", "High", "σ reported", "σ assigned (range/4)"]:
        if column in cleaned.columns:
            cleaned[f"{column} numeric"] = pd.to_numeric(cleaned[column], errors="coerce")
    return cleaned


def clean_segment_models(frame: pd.DataFrame) -> pd.DataFrame:
    """Add transparent category and scope labels without changing source values."""
    cleaned = frame.copy()
    for column in ["Best / reported", "Low (approx.)", "High (approx.)", "σ assigned (range/4)"]:
        cleaned[f"{column} numeric"] = pd.to_numeric(cleaned[column], errors="coerce")
    cleaned["measurement_category"] = cleaned["Parameter"].map(_measurement_category)
    source_text = cleaned["Dataset / model"].fillna("").astype(str).str.lower()
    cleaned["deformation_scope"] = source_text.map(
        lambda text: "Single dike" if "single dike" in text else "Cumulative or model scope not explicitly single-dike"
    )
    cleaned["source_row_id"] = cleaned["ID"].astype(str)
    return cleaned


def clean_episodes(frame: pd.DataFrame) -> pd.DataFrame:
    """Preserve narrative episode dates and count supported numerical values."""
    cleaned = frame.copy()
    numeric_columns = ["Opening (m)", "Fault slip (m)", "Dike top depth (km)", "Seismic moment (N·m)"]
    for column in numeric_columns:
        if column in cleaned.columns:
            cleaned[f"{column} numeric"] = pd.to_numeric(cleaned[column], errors="coerce")
    typed_columns = [f"{column} numeric" for column in numeric_columns if f"{column} numeric" in cleaned.columns]
    cleaned["supported_numeric_measurement_count"] = cleaned[typed_columns].notna().sum(axis=1)
    cleaned["has_supported_numeric_measurement"] = cleaned["supported_numeric_measurement_count"] > 0
    episode_number = pd.to_numeric(cleaned["Episode #"], errors="coerce").astype("Int64")
    cleaned["traceable_episode_id"] = episode_number.map(lambda value: f"KRAFLA_EP_{value:02d}" if pd.notna(value) else pd.NA)
    cleaned["date_interpretation_note"] = "Original date string retained; no unsupported date precision added."
    return cleaned


def clean_regression_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Select genuine seed data rows and mark their non-independence explicitly."""
    rows = numeric_observation_rows(frame, REGRESSION_NUMERIC_COLUMNS)
    rows = classify_independence(rows)
    rows["complete_opening_slip"] = rows[["w0 dike opening (m)", "s fault slip (m)"]].notna().all(axis=1)
    rows["complete_opening_top_depth"] = rows[["w0 dike opening (m)", "d dike top depth (km)"]].notna().all(axis=1)
    rows["complete_slip_top_depth"] = rows[["s fault slip (m)", "d dike top depth (km)"]].notna().all(axis=1)
    return rows


def clean_uncertainty_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Label reported and assumption-based uncertainty notes without inventing sigma."""
    cleaned = frame.copy()
    text = cleaned["How to use it"].fillna("").astype(str).str.lower()
    cleaned["uncertainty_basis"] = text.map(
        lambda note: "Assigned/placeholder or interpretation guidance" if any(word in note for word in ("assign", "placeholder", "take ~")) else "Reported or qualitative source statement"
    )
    return cleaned


def build_clean_datasets(workbook: WorkbookData) -> dict[str, pd.DataFrame]:
    """Build every requested derivative table from the untouched source tables."""
    regression = clean_regression_data(workbook.sheets["Regression_ready"])
    return {
        "crisis_summary_clean": clean_crisis_summary(workbook.sheets["Crisis_totals"]),
        "segment_models_clean": clean_segment_models(workbook.sheets["Segment_models"]),
        "episodes_clean": clean_episodes(workbook.sheets["Episodes"]),
        "regression_data_clean": regression,
        "uncertainty_summary": clean_uncertainty_summary(workbook.sheets["Uncertainty_basis"]),
    }
