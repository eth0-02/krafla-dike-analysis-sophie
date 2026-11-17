"""Publication-oriented figures that state the data limitations visibly."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import matplotlib

# A non-interactive backend lets the workflow run in a terminal, CI, or .bat file.
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


FIGURE_STYLE = {
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "legend.fontsize": 8,
    "figure.dpi": 150,
}


def _save_figure(fig: plt.Figure, output_dir: Path, stem: str, title: str, caption: str) -> dict[str, str]:
    """Save every scientific figure in raster and vector formats."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {"figure": stem, "title": title, "caption": caption}
    for extension in ("png", "pdf", "svg"):
        destination = output_dir / f"{stem}.{extension}"
        fig.savefig(destination, dpi=300 if extension == "png" else None, bbox_inches="tight")
        paths[extension] = str(destination.name)
    plt.close(fig)
    return paths


def _scientific_note(axis: plt.Axes, text: str) -> None:
    """Place limitations in a footer so they never obscure measurements or labels."""
    figure = axis.get_figure()
    figure.subplots_adjust(bottom=0.21)
    figure.text(0.125, 0.035, text, va="bottom", ha="left", fontsize=8, color="#333333", wrap=True)


def _scatter_relationship(
    regression: pd.DataFrame,
    x: str,
    y: str,
    x_label: str,
    y_label: str,
    x_sigma: str,
    y_sigma: str,
    stem: str,
    output_dir: Path,
) -> dict[str, str]:
    """Plot available model rows only, with no statistically misleading fitted line."""
    subset = regression.dropna(subset=[x, y]).copy()
    with plt.rc_context(FIGURE_STYLE):
        fig, axis = plt.subplots(figsize=(7.2, 5.2))
        colors = {"South cumulative deformation": "#0072B2", "North January 1978 dike": "#D55E00", "Unclassified": "#666666"}
        for group, group_rows in subset.groupby("independence_group", dropna=False):
            color = colors.get(str(group), "#666666")
            for _, row in group_rows.iterrows():
                x_error = float(row[x_sigma]) if x_sigma in row and pd.notna(row[x_sigma]) else None
                y_error = float(row[y_sigma]) if y_sigma in row and pd.notna(row[y_sigma]) else None
                axis.errorbar(row[x], row[y], xerr=x_error, yerr=y_error, fmt="o", color=color, capsize=3, alpha=0.9)
                axis.annotate(str(row["Case"]).replace(" model", ""), (row[x], row[y]), xytext=(5, 5), textcoords="offset points", fontsize=7)
            axis.plot([], [], "o", color=color, label=str(group))
        axis.set_xlabel(x_label)
        axis.set_ylabel(y_label)
        title = f"{y_label} versus {x_label}"
        axis.set_title(title)
        axis.legend(title="Independence group", loc="best")
        axis.grid(alpha=0.25)
        _scientific_note(axis, f"{len(subset)} complete model rows represent {subset['independence_group'].nunique()} geological configurations.\nNo regression line: estimates are not independent replicates. Error bars shown only where σ is supplied.")
        return _save_figure(fig, output_dir, stem, title, "Available paired seed estimates grouped by geological configuration. No fitted trend is shown because the observations are non-independent and mix deformation scopes.")


def _model_comparison(segment_models: pd.DataFrame, category: str, title: str, stem: str, output_dir: Path) -> dict[str, str] | None:
    """Compare model estimates with uncertainty bars only when an assigned sigma exists."""
    value = "Best / reported numeric"
    sigma = "σ assigned (range/4) numeric"
    subset = segment_models.loc[(segment_models["measurement_category"] == category) & segment_models[value].notna()].copy()
    if subset.empty:
        return None
    subset = subset.sort_values(value)
    with plt.rc_context(FIGURE_STYLE):
        height = max(4.0, 0.36 * len(subset) + 1.8)
        fig, axis = plt.subplots(figsize=(8.2, height))
        errors = subset[sigma].fillna(0.0)
        axis.barh(subset["source_row_id"], subset[value], xerr=errors, color="#4C78A8", alpha=0.85, capsize=3)
        axis.set_xlabel("Model estimate (m)")
        axis.set_ylabel("Source row / model parameter")
        axis.set_title(title)
        axis.grid(axis="x", alpha=0.25)
        _scientific_note(axis, "Bars are source-model estimates. Error bars use workbook-assigned σ (range/4),\nnot a newly estimated measurement uncertainty.")
        return _save_figure(fig, output_dir, stem, title, "Comparison of supplied segment-model estimates. Values remain model-dependent and should not be interpreted as independent events.")


MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12}


def _start_date_from_source_text(value: object) -> datetime | None:
    """Extract a start date only when the workbook date string supplies one.

    Month-only and date-range expressions are positioned at the start of their
    stated month/range. The original string remains in the cleaned table.
    """
    text = str(value).lower().replace("~", " ").strip()
    match = re.search(r"(?:(\d{1,2})(?:\s*[-–]\s*\d{1,2})?\s+)?([a-z]+)\s+(\d{4})", text)
    if not match:
        return None
    day_text, month_text, year_text = match.groups()
    month = MONTHS.get(month_text[:4]) or MONTHS.get(month_text[:3])
    if not month:
        return None
    return datetime(int(year_text), month, int(day_text or 1))


def _episode_timeline(episodes: pd.DataFrame, output_dir: Path) -> dict[str, str] | None:
    """Plot only episodes with a workbook-supported date expression."""
    rows = episodes.copy()
    rows["plot_start_date"] = rows["Date (as given)"].map(_start_date_from_source_text)
    rows = rows.dropna(subset=["plot_start_date"])
    if rows.empty:
        return None
    colors = {"Described, no per-dike numbers": "#999999", "Mentioned only": "#999999", "Modelled; Low-Medium confidence": "#0072B2", "Speculative": "#CC79A7", "Eruption only": "#E69F00"}
    with plt.rc_context(FIGURE_STYLE):
        fig, axis = plt.subplots(figsize=(9, 4.8))
        for _, row in rows.iterrows():
            color = colors.get(str(row.get("Data status", "")), "#666666")
            axis.scatter(row["plot_start_date"], row["Episode #"], s=65, color=color, zorder=3)
            axis.annotate(str(row["Date (as given)"]), (row["plot_start_date"], row["Episode #"]), xytext=(4, 4), textcoords="offset points", fontsize=7)
        axis.set_title("Krafla episodes with workbook-supported date expressions")
        axis.set_xlabel("Date (position is start of stated date/month/range)")
        axis.set_ylabel("Episode number in supplied workbook")
        axis.xaxis.set_major_locator(mdates.YearLocator())
        axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        axis.grid(alpha=0.25)
        _scientific_note(axis, "Episodes lacking a date string are not plotted. Date precision is not inferred beyond the source text.\nColour reflects supplied data status; it is not a quantitative quality score.")
        return _save_figure(fig, output_dir, "episode_timeline", "Krafla episodes with workbook-supported date expressions", "Chronology of the source-described episodes with date strings. Positions for month-only or range expressions use the stated start month.")


def _completeness_plot(regression: pd.DataFrame, output_dir: Path) -> dict[str, str]:
    columns = ["w0 dike opening (m)", "s fault slip (m)", "d dike top depth (km)", "H dike height (km)", "Surface extension (m)"]
    labels = ["Dike opening", "Fault slip", "Dike top depth", "Dike height", "Surface extension"]
    counts = [int(regression[column].notna().sum()) for column in columns]
    with plt.rc_context(FIGURE_STYLE):
        fig, axis = plt.subplots(figsize=(8, 4.8))
        bars = axis.bar(labels, counts, color="#009E73")
        axis.bar_label(bars, labels=[f"{count}/{len(regression)}" for count in counts], padding=3)
        axis.set_ylim(0, max(len(regression) + 1, max(counts) + 1))
        axis.set_ylabel("Seed-model rows with a value")
        axis.set_title("Data completeness in the regression seed table")
        axis.tick_params(axis="x", rotation=20)
        axis.grid(axis="y", alpha=0.25)
        _scientific_note(axis, "Completeness counts model rows, not independent geological events.")
        return _save_figure(fig, output_dir, "data_completeness", "Data completeness in the regression seed table", "Availability of each quantitative variable in the five numerical regression seed rows.")


def _uncertainty_plot(segment_models: pd.DataFrame, output_dir: Path) -> dict[str, str] | None:
    sigma = "σ assigned (range/4) numeric"
    subset = segment_models.dropna(subset=[sigma, "Unit"]).copy()
    if subset.empty:
        return None
    units = list(subset["Unit"].astype(str).unique())
    label_map = {
        "Depth to dike top": "Dike-top depth",
        "Dike width (vertical extent; bottom = top + width)": "Dike width",
        "Dike length (along strike)": "Dike length",
        "Dike opening": "Dike opening",
        "Fault slip (two faults, forced equal; dip 50-80 km deep)": "Fault slip\n(model-specific)",
    }
    def short_parameter_label(parameter: str) -> str:
        """Keep model-specific wording in data, but keep a figure axis readable."""
        if parameter in label_map:
            return label_map[parameter]
        if parameter.lower().startswith("fault slip"):
            return "Fault slip\n(model-specific)"
        return parameter
    with plt.rc_context(FIGURE_STYLE):
        fig, axes = plt.subplots(1, len(units), figsize=(6.8 * len(units), 5.6), squeeze=False)
        for axis, unit in zip(axes.ravel(), units):
            unit_rows = subset.loc[subset["Unit"].astype(str) == unit].copy()
            parameters = list(unit_rows["Parameter"].drop_duplicates())
            x_positions = {parameter: index for index, parameter in enumerate(parameters)}
            colors = ["#CC79A7" if str(kind).lower().startswith("read") else "#0072B2" for kind in unit_rows["Type"]]
            axis.scatter(unit_rows[sigma], [x_positions[p] for p in unit_rows["Parameter"]], c=colors, s=42)
            axis.set_yticks(range(len(parameters)), [short_parameter_label(parameter) for parameter in parameters])
            axis.set_xlabel(f"Assigned σ ({unit})")
            axis.set_title(f"{unit}-valued model parameters")
            axis.grid(axis="x", alpha=0.25)
        fig.suptitle("Workbook-assigned uncertainty by parameter and unit", y=1.02)
        _scientific_note(axes.ravel()[0], "Values are workbook-assigned σ values, often derived from a range/4 rule. They are not uniformly reported measurement uncertainties.")
        caption = "Assigned sigma values from segment-model ranges, separated by physical unit. These are not uniformly reported measurement uncertainties."
        return _save_figure(fig, output_dir, "assigned_uncertainty_comparison", "Workbook-assigned uncertainty by parameter and unit", caption)


def _moment_ranges(moment: dict[str, float], output_dir: Path) -> dict[str, str]:
    labels = ["Dike", "Fault", "Total geodetic"]
    lows = [moment["dike_moment_low_nm"], moment["fault_moment_low_nm"], moment["total_geodetic_moment_low_nm"]]
    highs = [moment["dike_moment_high_nm"], moment["fault_moment_high_nm"], moment["total_geodetic_moment_high_nm"]]
    with plt.rc_context(FIGURE_STYLE):
        fig, axis = plt.subplots(figsize=(7.2, 4.5))
        axis.hlines(range(3), lows, highs, color="#2C7FB8", linewidth=4)
        axis.scatter(lows, range(3), color="#2C7FB8")
        axis.scatter(highs, range(3), color="#2C7FB8")
        axis.set_yticks(range(3), labels)
        axis.set_xscale("log")
        axis.set_xlabel("Moment (N m, logarithmic scale)")
        axis.set_title("Krafla whole-crisis moment bounds")
        axis.grid(axis="x", alpha=0.25)
        _scientific_note(axis, "Low/high bounds pair supplied low/high assumptions. They are not confidence intervals.")
        return _save_figure(fig, output_dir, "moment_ranges", "Krafla whole-crisis moment bounds", "Recalculated moment bounds from the supplied workbook assumptions.")


def create_figures(
    regression: pd.DataFrame,
    segment_models: pd.DataFrame,
    episodes: pd.DataFrame,
    moment: dict[str, float],
    output_dir: Path,
) -> pd.DataFrame:
    """Generate all scientifically supported figures and their caption manifest."""
    figures: list[dict[str, str]] = [
        _scatter_relationship(regression, "w0 dike opening (m)", "s fault slip (m)", "Dike opening (m)", "Fault slip (m)", "σ w0", "σ s", "opening_vs_fault_slip", output_dir),
        _scatter_relationship(regression, "w0 dike opening (m)", "d dike top depth (km)", "Dike opening (m)", "Dike top depth (km)", "σ w0", "σ d", "opening_vs_top_depth", output_dir),
        _scatter_relationship(regression, "d dike top depth (km)", "s fault slip (m)", "Dike top depth (km)", "Fault slip (m)", "σ d", "σ s", "fault_slip_vs_top_depth", output_dir),
        _completeness_plot(regression, output_dir),
        _moment_ranges(moment, output_dir),
    ]
    for optional in (
        _model_comparison(segment_models, "Dike opening", "Dike opening estimates across supplied models", "opening_model_comparison", output_dir),
        _model_comparison(segment_models, "Fault slip", "Fault slip estimates across supplied models", "fault_slip_model_comparison", output_dir),
        _episode_timeline(episodes, output_dir),
        _uncertainty_plot(segment_models, output_dir),
    ):
        if optional is not None:
            figures.append(optional)
    return pd.DataFrame(figures)
