"""End-to-end orchestration for the reproducible Krafla research workflow."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .analysis import calculate_moment_ranges
from .data_loader import EXPECTED_SHEETS, WorkbookData, clean_table, load_workbook
from .descriptive_analysis import make_descriptive_statistics, make_episode_completeness
from .preparation import build_clean_datasets
from .regression import assess_regression_readiness, regression_readiness
from .reporting import write_run_manifest, write_technical_report
from .validation import make_data_quality_report
from .visualization import create_figures


MOMENT_KEYS = {
    "Shear modulus G": "G",
    "Dike length (rift length)": "dike_length",
    "Dike height": "dike_height",
    "Dike opening": "dike_opening",
    "Number of faults": "fault_count",
    "Fault length": "fault_length",
    "Fault width (down-dip)": "fault_width",
    "Fault slip": "fault_slip",
    "Seismic moment (whole crisis)": "seismic_moment",
}


def sha256(path: Path) -> str:
    """Hash a file in chunks so provenance tracking also works for large workbooks."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def extract_moment_inputs(frame: pd.DataFrame) -> dict[str, tuple[float, float]]:
    """Read and validate the physical moment inputs named by the workbook."""
    required = {"Quantity", "Low", "High"}
    if not required.issubset(frame.columns):
        raise ValueError("Moment_calc must have Quantity, Low, and High columns.")
    values: dict[str, tuple[float, float]] = {}
    for _, row in frame.iterrows():
        key = MOMENT_KEYS.get(row["Quantity"])
        if key is None:
            continue
        low = pd.to_numeric(pd.Series([row["Low"]]), errors="coerce").iloc[0]
        high = pd.to_numeric(pd.Series([row["High"]]), errors="coerce").iloc[0]
        if not (pd.notna(low) and pd.notna(high) and math.isfinite(float(low)) and math.isfinite(float(high)) and low > 0 and high > 0):
            raise ValueError(f"Moment input '{row['Quantity']}' must have finite positive Low and High values.")
        if low > high:
            raise ValueError(f"Moment input '{row['Quantity']}' has Low greater than High.")
        values[key] = (float(low), float(high))
    missing = set(MOMENT_KEYS.values()).difference(values)
    if missing:
        raise ValueError(f"Moment_calc is missing required inputs: {', '.join(sorted(missing))}.")
    return values


def _create_output_folder(output_root: Path) -> Path:
    """Create an unused timestamped directory without overwriting an earlier run."""
    output_root.mkdir(parents=True, exist_ok=True)
    stem = f"krafla_run_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
    candidate = output_root / stem
    suffix = 1
    while candidate.exists():
        candidate = output_root / f"{stem}_{suffix:02d}"
        suffix += 1
    candidate.mkdir()
    return candidate


def archive_raw_source(source: Path, raw_copy_dir: Path) -> Path:
    """Copy source once without overwriting a differently hashed raw workbook."""
    raw_copy_dir.mkdir(parents=True, exist_ok=True)
    source_hash = sha256(source)
    destination = raw_copy_dir / source.name
    if destination.exists() and sha256(destination) != source_hash:
        destination = raw_copy_dir / f"{source.stem}_{source_hash[:12]}{source.suffix}"
    if not destination.exists():
        shutil.copy2(source, destination)
    return destination.resolve()


def _write_source_sheet_exports(workbook: WorkbookData, destination: Path) -> None:
    """Export source-sheet copies for convenient inspection without touching Excel."""
    for sheet_name, frame in workbook.sheets.items():
        safe_name = sheet_name.replace("/", "_").replace("\\", "_")
        frame.to_csv(destination / f"source_{safe_name}.csv", index=False)


def run(input_path: Path, output_root: Path, raw_copy_dir: Path | None = Path("data/raw")) -> Path:
    """Run validation, cleaning, calculations, figures, and reporting end-to-end."""
    workbook = load_workbook(input_path)
    raw_copy = archive_raw_source(workbook.source_path, raw_copy_dir) if raw_copy_dir is not None else None
    output = _create_output_folder(output_root)
    tables, figures, reports = output / "tables", output / "figures", output / "reports"
    for directory in (tables, figures, reports):
        directory.mkdir()

    _write_source_sheet_exports(workbook, tables)
    cleaned = build_clean_datasets(workbook)
    for name, frame in cleaned.items():
        frame.to_csv(tables / f"{name}.csv", index=False)

    descriptive_statistics = make_descriptive_statistics(cleaned)
    descriptive_statistics.to_csv(tables / "descriptive_statistics.csv", index=False)
    episode_completeness = make_episode_completeness(cleaned["episodes_clean"])
    episode_completeness.to_csv(tables / "episode_data_completeness.csv", index=False)

    data_quality = make_data_quality_report(workbook, cleaned["regression_data_clean"])
    data_quality.to_csv(tables / "data_quality_report.csv", index=False)
    regression_assessment = assess_regression_readiness(cleaned["regression_data_clean"])
    regression_assessment.to_csv(tables / "regression_assessment.csv", index=False)

    moment = calculate_moment_ranges(extract_moment_inputs(workbook.sheets["Moment_calc"]))
    (output / "moment_recalculation.json").write_text(json.dumps(moment, indent=2), encoding="utf-8")
    compact_readiness = regression_readiness(workbook.sheets["Regression_ready"])
    (output / "regression_readiness.json").write_text(json.dumps(compact_readiness, indent=2), encoding="utf-8")

    figure_manifest = create_figures(cleaned["regression_data_clean"], cleaned["segment_models_clean"], cleaned["episodes_clean"], moment, figures)
    figure_manifest.to_csv(figures / "figure_manifest.csv", index=False)
    write_technical_report(reports / "technical_report.md", workbook.source_path, data_quality, descriptive_statistics, regression_assessment, cleaned["episodes_clean"], moment, figure_manifest)
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "input_workbook": str(workbook.source_path),
        "input_sha256": sha256(workbook.source_path),
        "raw_copy": str(raw_copy) if raw_copy else None,
        "worksheets": list(workbook.sheets),
        "output_directory": str(output.resolve()),
        "generated_clean_datasets": [*cleaned, "descriptive_statistics", "episode_data_completeness", "data_quality_report", "regression_assessment"],
        "figures": figure_manifest["figure"].tolist(),
        "scientific_warnings": [
            "Per-episode values absent from the source remain missing.",
            "Moment ranges are deterministic bounds from supplied inputs, not confidence intervals.",
            "Regression is withheld because five seed rows represent two non-independent geological configurations.",
        ],
    }
    write_run_manifest(output / "run_metadata.json", manifest)
    return output


def main() -> None:
    """Parse user-friendly options and report expected input errors without a traceback."""
    parser = argparse.ArgumentParser(description="Validate and analyse Krafla dike data without changing the source workbook.")
    parser.add_argument("--input", required=True, type=Path, help="Path to the source .xlsx workbook")
    parser.add_argument("--output", default=Path("outputs"), type=Path, help="Parent directory for timestamped outputs")
    parser.add_argument("--raw-copy-dir", default=Path("data/raw"), type=Path, help="Directory for a byte-identical raw workbook copy")
    parser.add_argument("--no-raw-copy", action="store_true", help="Do not create or update a raw workbook copy")
    args = parser.parse_args()
    try:
        output = run(args.input, args.output, None if args.no_raw_copy else args.raw_copy_dir)
    except (FileNotFoundError, ValueError, OSError) as error:
        parser.exit(1, f"Workflow stopped: {error}\n")
    print(output.resolve())
