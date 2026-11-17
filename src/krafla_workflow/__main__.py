"""Command-line entry point for the Krafla data workflow (legacy wrapper)."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .analysis import calculate_moment_ranges

EXPECTED_SHEETS = {"README", "Crisis_totals", "Segment_models", "Episodes", "Moment_calc", "Regression_ready", "Uncertainty_basis", "Paper_conflicts"}
MOMENT_KEYS = {
    "Shear modulus G": "G", "Dike length (rift length)": "dike_length", "Dike height": "dike_height",
    "Dike opening": "dike_opening", "Number of faults": "fault_count", "Fault length": "fault_length",
    "Fault width (down-dip)": "fault_width", "Fault slip": "fault_slip", "Seismic moment (whole crisis)": "seismic_moment",
}


def clean_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Drop fully empty rows and columns while retaining true missing measurements."""
    return frame.dropna(axis=0, how="all").dropna(axis=1, how="all")


def load_workbook(path: Path) -> dict[str, pd.DataFrame]:
    book = pd.ExcelFile(path)
    missing = EXPECTED_SHEETS.difference(book.sheet_names)
    if missing:
        raise ValueError(f"Input workbook is missing expected sheets: {', '.join(sorted(missing))}")
    return {sheet: clean_table(pd.read_excel(path, sheet_name=sheet)) for sheet in book.sheet_names}


def extract_moment_inputs(frame: pd.DataFrame) -> dict[str, tuple[float, float]]:
    """Read the named physical inputs and reject invalid numerical bounds.

    Checking here is intentional: allowing a blank cell to become NaN would let
    the calculation complete with meaningless `null`/NaN results downstream.
    """
    required = {"Quantity", "Low", "High"}
    if not required.issubset(frame.columns):
        raise ValueError("Moment_calc must have Quantity, Low, and High columns.")
    values: dict[str, tuple[float, float]] = {}
    for _, row in frame.iterrows():
        key = MOMENT_KEYS.get(row["Quantity"])
        if key:
            low, high = float(row["Low"]), float(row["High"])
            if not (math.isfinite(low) and math.isfinite(high) and low > 0 and high > 0):
                raise ValueError(f"Moment input '{row['Quantity']}' must have finite positive Low and High values.")
            if low > high:
                raise ValueError(f"Moment input '{row['Quantity']}' has Low greater than High.")
            values[key] = (low, high)
    return values


def regression_readiness(frame: pd.DataFrame) -> dict[str, object]:
    """Report the supplied table's limitation without fitting an invalid model.

    The two north-fault rows describe two faults in one January 1978 dike model,
    so they are not two independent dike configurations. The workbook itself
    identifies two independent configurations (south and north 1978).
    """
    records = frame.dropna(subset=["Case"]).copy()
    independent = records["Case"].str.contains("west fault|east fault", case=False, na=False)
    configurations = 2 if independent.sum() == 2 else len(records)
    return {
        "populated_rows": int(len(records)), "independent_configurations": configurations,
        "fit_regression": False,
        "warning": "The supplied workbook contains only two independent configurations; add external source rows before fitting a regression.",
    }


def write_range_plot(result: dict[str, float], path: Path) -> None:
    """Create a compact visual record of the recalculated moment bounds."""
    labels = ["Dike", "Fault", "Total geodetic"]
    lows = [result["dike_moment_low_nm"], result["fault_moment_low_nm"], result["total_geodetic_moment_low_nm"]]
    highs = [result["dike_moment_high_nm"], result["fault_moment_high_nm"], result["total_geodetic_moment_high_nm"]]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hlines(range(3), lows, highs, color="#2c7fb8", linewidth=4)
    ax.scatter(lows, range(3), color="#2c7fb8"); ax.scatter(highs, range(3), color="#2c7fb8")
    ax.set_yticks(range(3), labels); ax.set_xscale("log"); ax.set_xlabel("Moment (N m, log scale)")
    ax.set_title("Krafla whole-crisis moment ranges (supplied assumptions)")
    fig.tight_layout(); fig.savefig(path, dpi=180); plt.close(fig)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(input_path: Path, output_root: Path) -> Path:
    """Execute a complete, non-destructive analysis run and return its folder."""
    if not input_path.is_file():
        raise FileNotFoundError(f"Input workbook not found: {input_path}")
    data = load_workbook(input_path)
    output = output_root / f"krafla_run_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
    tables, figures = output / "tables", output / "figures"
    tables.mkdir(parents=True); figures.mkdir()
    # Export cleaned copies so downstream analysis never needs to edit the source workbook.
    for name, frame in data.items():
        frame.to_csv(tables / f"{name}.csv", index=False)
    crisis = data["Crisis_totals"]
    crisis[[c for c in ["ID", "Parameter", "Low", "Central (as reported)", "High", "Unit", "Confidence", "Source"] if c in crisis]].to_csv(output / "crisis_summary.csv", index=False)
    moments = calculate_moment_ranges(extract_moment_inputs(data["Moment_calc"]))
    (output / "moment_recalculation.json").write_text(json.dumps(moments, indent=2), encoding="utf-8")
    (output / "regression_readiness.json").write_text(json.dumps(regression_readiness(data["Regression_ready"]), indent=2), encoding="utf-8")
    write_range_plot(moments, figures / "moment_ranges.png")
    # The checksum makes a result folder traceable to the exact workbook used.
    metadata = {"input": str(input_path.resolve()), "sha256": sha256(input_path), "created_utc": datetime.now(timezone.utc).isoformat(), "sheets": list(data), "warnings": ["Per-episode values absent in source remain missing.", "Moment ranges are deterministic bounds from supplied inputs, not confidence intervals."]}
    (output / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Krafla dike-data workflow.")
    parser.add_argument("--input", required=True, type=Path, help="Path to the source .xlsx workbook")
    parser.add_argument("--output", default=Path("outputs"), type=Path, help="Directory for run outputs")
    args = parser.parse_args()
    print(run(args.input, args.output).resolve())


# The enhanced workflow is implemented in focused modules. These aliases retain
# compatibility for callers that previously imported helpers from __main__.
from .data_loader import EXPECTED_SHEETS as _EXPECTED_SHEETS, clean_table as _clean_table, load_workbook as _load_workbook
from .regression import regression_readiness as _regression_readiness
from .workflow import MOMENT_KEYS as _MOMENT_KEYS, extract_moment_inputs as _extract_moment_inputs, main as _enhanced_main, run as _enhanced_run

EXPECTED_SHEETS = _EXPECTED_SHEETS
MOMENT_KEYS = _MOMENT_KEYS
clean_table = _clean_table
load_workbook = _load_workbook
extract_moment_inputs = _extract_moment_inputs
regression_readiness = _regression_readiness
run = _enhanced_run

if __name__ == "__main__":
    _enhanced_main()

