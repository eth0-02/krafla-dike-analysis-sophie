# Krafla dike-data workflow

For a short guide written for the researcher who will run the project, see
[SOPHIE_HANDOVER.md](SOPHIE_HANDOVER.md).

A beginner-friendly, reproducible Python workflow for the **first** part of a
PhD project on magma, faults, and earthquakes: preparing data for an empirical
dike–fault relationship. It reads the Krafla 1975–1984 workbook, validates its
structure, preserves a byte-identical raw copy, recalculates documented moment
bounds, and produces traceable datasets, figures, and a technical report.

The workflow deliberately does **not** invent missing per-episode values and it
does **not** fit a regression when the available data cannot support one.

## What this project does—and does not do

| Project objective | Status in this repository |
| --- | --- |
| Prepare, validate, and summarise observed dike–fault data | Included |
| Recalculate dike, fault, and total geodetic moment bounds | Included |
| Check whether the table can support an empirical regression | Included, with an independence guardrail |
| Fit ordinary, weighted, or orthogonal regressions | Deferred until more independent observations are added |
| Model crustal deformation with PyLith | Not included; this is the second project objective |

PyLith is a separate finite-element modelling workflow. It needs a model
geometry, mesh, material properties, fault/friction formulation, and boundary
conditions. The present code is designed to prepare and assess observations
before that modelling stage.

## Easiest way to run it on Windows

1. Install [Python 3.10 or newer](https://www.python.org/downloads/) and tick
   **Add Python to PATH** during installation.
2. Download or clone this repository.
3. Keep your Excel file anywhere on your computer.
4. Drag the Excel file onto `run_krafla_workflow.bat`, or open Command Prompt in
   the repository folder and run:

   ```bat
   run_krafla_workflow.bat "C:\path\to\Krafla_1975_1984_dike_data.xlsx"
   ```

On the first run, the script creates `.venv` and installs the required Python
libraries. Subsequent runs reuse the same environment. It never changes the
source Excel file. By default it saves a byte-identical copy in `data/raw/`,
which is intentionally excluded from Git.

## Command-line method

```powershell
cd path\to\krafla-dike-workflow
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
python -m krafla_workflow --input "C:\path\to\Krafla_1975_1984_dike_data.xlsx" --output outputs
```

You can select a different output folder with `--output`, choose a raw archive
directory with `--raw-copy-dir`, or use `--no-raw-copy` when an approved raw
archive already exists.

## Outputs explained

Every execution creates a time-stamped folder below `outputs/`, so prior
results are never overwritten.

| Output | Meaning |
| --- | --- |
| `run_metadata.json` | Input location, SHA-256 checksum, run time, sheets read, and scientific warnings. |
| `tables/source_*.csv` | Readable source-sheet copies. The original workbook remains unchanged. |
| `tables/crisis_summary_clean.csv` | Crisis-wide reported values, numeric analysis fields, confidence levels, and sources. |
| `tables/segment_models_clean.csv` | Model estimates, source rows, measurement categories, scope labels, and supplied uncertainties. |
| `tables/episodes_clean.csv` | Episode chronology with original date strings and explicit numerical-data completeness. |
| `tables/regression_data_clean.csv` | Five numerical seed rows with provenance, scope, and non-independence classifications. |
| `tables/uncertainty_summary.csv` | Source uncertainty statements labelled as reported/qualitative or assigned guidance. |
| `tables/data_quality_report.csv` | Worksheet-level counts, missingness, units, duplicate checks, and scientific caveats. |
| `tables/regression_assessment.csv` | Complete-case and independence assessment for the three proposed relationships. |
| `tables/descriptive_statistics.csv` | Unit-aware counts, missingness, ranges, means, medians, and sample standard deviations for coherent variables. |
| `tables/episode_data_completeness.csv` | Per-episode record of which numerical measurements are actually supplied. |
| `moment_recalculation.json` | Independently recalculated low/high moments, Mw, and seismic-to-geodetic ratios. Ranges are deterministic bounds, not confidence intervals. |
| `regression_readiness.json` | Five numerical seed rows, four opening/slip pairs, and the warning that these represent only two independent configurations. |
| `figures/` | Nine descriptive figures in 300-DPI PNG, vector PDF, and SVG; `figure_manifest.csv` contains captions. |
| `reports/technical_report.md` | Methods, verified results, regression assessment, scientific limitations, and recommended next data collection. |

## Input requirements

The input workbook must contain these sheets: `README`, `Crisis_totals`,
`Segment_models`, `Episodes`, `Moment_calc`, `Regression_ready`,
`Uncertainty_basis`, and `Paper_conflicts`. The program stops with a readable
error instead of producing incomplete results if a required sheet, required
column, or moment input is absent. It preserves named-but-empty source fields
because an absent central estimate can be meaningful research information.

## Testing

Run the tests after installing dependencies:

```powershell
$env:PYTHONPATH = "src"
python -m pytest -p no:cacheprovider --basetemp .test-artifacts
```

The tests check mathematical calculations, workbook structure, named blank
fields, numeric validation, missing values, non-independence classification,
regression guardrails, raw-file preservation, figure creation, reports, and a
complete synthetic Excel-to-output run. They do not edit the research workbook.

## Extending this for empirical regression

Before adding a regression, add genuinely independent observations from the
primary dike/fault sources. Each record should include a stable event ID,
consistent units, dike opening, fault slip, geometry/depth descriptors, and
measurement uncertainty or standard deviation. Once there are enough
independent records, an extension can compare ordinary least squares, weighted
least squares, and orthogonal distance regression while documenting their
assumptions and diagnostics. The current workbook has five numerical model rows
and four opening/slip pairs, but those values represent only two geological
configurations and mix cumulative with single-dike deformation. That is why this
workflow does not report p-values, R², trend lines, or predictive claims.

