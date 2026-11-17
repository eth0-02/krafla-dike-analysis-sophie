"""Scientifically conservative regression-readiness assessment.

No p-values, confidence intervals, or trend lines are produced when there are
too few independent geological configurations to support an inferential model.
"""

from __future__ import annotations

import pandas as pd


RELATIONSHIPS = {
    "Fault slip versus dike opening": ("s fault slip (m)", "w0 dike opening (m)"),
    "Fault slip versus dike top depth": ("s fault slip (m)", "d dike top depth (km)"),
    "Dike opening versus dike top depth": ("w0 dike opening (m)", "d dike top depth (km)"),
}


def assess_regression_readiness(regression_data: pd.DataFrame) -> pd.DataFrame:
    """Document complete cases and explain why a fitted model is withheld."""
    records: list[dict[str, object]] = []
    for relationship, (response, predictor) in RELATIONSHIPS.items():
        complete = regression_data.dropna(subset=[response, predictor])
        groups = int(complete["independence_group"].nunique())
        scopes = sorted(complete["deformation_scope"].dropna().unique())
        records.append({
            "relationship": relationship,
            "response": response,
            "predictor": predictor,
            "complete_model_rows": int(len(complete)),
            "independent_geological_configurations": groups,
            "deformation_scopes_present": "; ".join(scopes),
            "inferential_regression_fitted": False,
            "assessment": "Not scientifically defensible with current data.",
            "reason": "Rows are alternative estimates or multiple faults from two geological configurations, and include cumulative versus single-dike deformation. No p-values, confidence intervals, R², or predictions are reported.",
            "next_requirement": "Add independent event-level dike/fault observations with consistent definitions and documented uncertainty.",
        })
    return pd.DataFrame(records)


def regression_readiness(frame: pd.DataFrame) -> dict[str, object]:
    """Backwards-compatible compact summary for the command-line JSON output."""
    from .preparation import clean_regression_data

    data = clean_regression_data(frame)
    return {
        "numeric_seed_rows": int(len(data)),
        "rows_with_opening_and_slip": int(data["complete_opening_slip"].sum()),
        "independent_geological_configurations": int(data["independence_group"].nunique()),
        "fit_inferential_regression": False,
        "warning": "The supplied workbook contains five seed rows but only two non-independent geological configurations. Regression is intentionally withheld.",
    }
