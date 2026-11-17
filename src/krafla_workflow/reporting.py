"""Markdown reporting for the technical and scientific audit."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _table(frame: pd.DataFrame, columns: list[str] | None = None) -> str:
    """Render a small DataFrame as Markdown without an optional `tabulate` dependency."""
    selected = frame if columns is None else frame.loc[:, [column for column in columns if column in frame.columns]]
    if selected.empty:
        return "No records available."
    def cell(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    header = "| " + " | ".join(cell(column) for column in selected.columns) + " |"
    separator = "| " + " | ".join("---" for _ in selected.columns) + " |"
    body = ["| " + " | ".join(cell(value) for value in row) + " |" for row in selected.fillna("").itertuples(index=False, name=None)]
    return "\n".join([header, separator, *body])


def write_technical_report(
    path: Path,
    source_path: Path,
    data_quality: pd.DataFrame,
    descriptive_statistics: pd.DataFrame,
    regression_assessment: pd.DataFrame,
    episodes: pd.DataFrame,
    moment: dict[str, float],
    figure_manifest: pd.DataFrame,
) -> None:
    """Write a research-facing report whose claims are tied to generated outputs."""
    episode_count = len(episodes)
    numerical_episodes = int(episodes["has_supported_numeric_measurement"].sum())
    quality_view = data_quality.loc[data_quality["sheet"].isin(["Crisis_totals", "Segment_models", "Episodes", "Regression_ready"])]
    lines = [
        "# Krafla dike analysis technical report",
        "",
        "## Executive summary",
        "",
        f"This run analysed the supplied Krafla workbook at `{source_path}` without modifying it. It produced traceable cleaned tables, recalculated documented moment bounds, and descriptive figures. The workbook contains five numerical regression seed records, but the values represent only two geological configurations: a south cumulative-deformation model and the January 1978 north dike. Formal inferential regression is therefore intentionally withheld.",
        "",
        "## Dataset description and data quality",
        "",
        _table(quality_view, ["sheet", "record_count", "column_count", "duplicate_row_count", "missing_cell_count", "units_present", "quality_note"]),
        "",
        "The source contains reported estimates, model-derived values, visually read ranges, and assigned uncertainty values. These provenance distinctions are preserved in the clean CSV files; no blank measurement has been imputed.",
        "",
        "## Methods",
        "",
        "- Fully blank rows and columns were removed from derivative tables only. Original values, units, source fields, confidence labels, and notes were retained.",
        "- Moment bounds were recalculated with the rectangular tensile-dislocation and boundary-fault expressions recorded in the workbook. Low inputs were paired with low inputs and high inputs with high inputs. These are deterministic bounds, not statistical confidence intervals.",
        "- Regression seed rows were grouped by geological configuration before any model consideration. Alternative south models, two faults from the same northern event, and updated northern alternatives were not treated as independent samples.",
        "- Figures show available values and source-supported uncertainty only. Scatter plots deliberately omit fitted lines.",
        "",
        "## Results",
        "",
        f"The recalculated total geodetic moment bounds are {moment['total_geodetic_moment_low_nm']:.3e} to {moment['total_geodetic_moment_high_nm']:.3e} N m, corresponding to Mw {moment['mw_total_low']:.2f} to {moment['mw_total_high']:.2f} using the workbook convention. The seismic-to-total-geodetic ratio spans {moment['seismic_share_total_high']:.1%} to {moment['seismic_share_total_low']:.1%} depending on which deterministic bound is used.",
        "",
        "### Descriptive statistics",
        "",
        _table(descriptive_statistics.loc[descriptive_statistics["independence_group"].isin(["Not applicable", "All seed rows (non-independent)"])], ["data_origin", "variable", "unit", "records_considered", "available_values", "missing_values", "minimum", "maximum", "mean", "median", "standard_deviation_sample"]),
        "",
        "Statistics are grouped by variable and physical unit. They describe reported/model seed values and do not estimate a population of independent diking events.",
        "",
        f"The episode sheet lists {episode_count} episode rows. Only {numerical_episodes} have at least one supplied numerical opening, slip, depth, or moment field; all other rows remain explicitly missing rather than inferred.",
        "",
        "## Regression assessment",
        "",
        _table(regression_assessment, ["relationship", "complete_model_rows", "independent_geological_configurations", "deformation_scopes_present", "inferential_regression_fitted", "assessment", "reason"]),
        "",
        "No p-values, confidence intervals, R² statistics, prediction metrics, or diagnostic residual plots are reported. A high correlation calculated from alternative models of the same events would not establish a physical relationship.",
        "",
        "## Scientific limitations",
        "",
        "- Per-episode dike opening, fault slip, and depth values are absent for most of the approximately 15–20 injections described in the workbook.",
        "- South values are crisis-cumulative while north values describe a single January 1978 dike. Pooling them conflates spatial and temporal scales.",
        "- Several uncertainty values are ranges read from a figure or assigned as range/4, and therefore should not be treated as equivalent measurement standard deviations.",
        "- The workbook itself records conflicts between source publications. This workflow reports them rather than silently reconciling them.",
        "",
        "## Recommendations",
        "",
        "1. Build an event-level database from the primary cited studies, with one stable event identifier per physically independent dike/fault configuration.",
        "2. Record measurement method, temporal scope, geometry definition, units, uncertainty type, and whether each value is observed or model-derived.",
        "3. Separate cumulative crisis summaries from individual injections before considering regression.",
        "4. Once enough independent observations exist, pre-specify the relationship, error model, and sensitivity analyses before fitting weighted or orthogonal regression.",
        "5. Treat PyLith as a separate second-stage physical modelling workflow, with independently justified geometry, material, and boundary-condition inputs.",
        "",
        "## Figures",
        "",
        _table(figure_manifest, ["figure", "title", "caption", "png", "pdf", "svg"]),
        "",
        "## Reproducibility",
        "",
        "The run manifest records the source checksum, selected settings, generated files, and scientific warnings. Re-run the command with the same workbook to reproduce the calculation and regenerate a new timestamped output folder.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_run_manifest(path: Path, manifest: dict[str, object]) -> None:
    """Persist metadata as formatted JSON for programmatic provenance checks."""
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
