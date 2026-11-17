# Krafla dike analysis: handover notes

## Purpose

This project reads the Krafla 1975–1984 Excel workbook and creates cleaned
tables, descriptive plots, a moment recalculation, and a technical report. It
does not alter the Excel workbook.

## Before you start

- Install Python 3.10 or later from [python.org](https://www.python.org/downloads/).
  During installation, select **Add Python to PATH**.
- Keep `Krafla_1975_1984_dike_data.xlsx` somewhere on your computer.
- Download the project folder or unzip the project archive.

## Run the analysis

The simplest option is to drag the Excel workbook onto
`run_krafla_workflow.bat`.

Alternatively, open Command Prompt in the project folder and run:

```bat
run_krafla_workflow.bat "C:\path\to\Krafla_1975_1984_dike_data.xlsx"
```

The first run creates a local `.venv` folder and installs the required Python
packages. Later runs reuse it. The script writes a raw workbook copy to
`data/raw/` and creates a new timestamped folder inside `outputs/`.

## Main outputs

Open the newest `outputs/krafla_run_.../` folder after the script finishes.

- `reports/technical_report.md` is the main written summary.
- `tables/regression_data_clean.csv` contains the regression seed data and its
  independence labels.
- `tables/descriptive_statistics.csv` contains counts, ranges, means, medians,
  and standard deviations, grouped by variable and unit.
- `tables/episode_data_completeness.csv` shows which episode-level values are
  actually available in the workbook.
- `tables/data_quality_report.csv` lists worksheet-level completeness and
  duplicate checks.
- `figures/` contains PNG, PDF, and SVG versions of the plots. The
  `figure_manifest.csv` file gives the figure captions.

## Current data limit

The workbook contains five numerical regression seed rows. Four have both dike
opening and fault slip, but they represent two geological configurations:

1. Alternative models of south cumulative deformation.
2. Alternative estimates and two fault values for the January 1978 northern dike.

These are not independent samples. The project therefore does not fit or
interpret a formal regression, and it does not produce p-values, R² values, or
trend lines. The scatter plots are descriptive only.

## What is needed before regression

An event-level dataset is needed, with one row per independent dike/fault event.
For each row, record the event date or period, dike opening, fault slip, depth
definition, geometry, units, method, source, uncertainty, and whether the
value is observed or model-derived. Cumulative crisis values should remain
separate from single-dike values.

## PyLith

PyLith is not part of this repository. It is a separate second-stage modelling
task that needs a physical model setup, including a mesh, dike/fault geometry,
material properties, boundary conditions, and fault formulation.

## Check the installation

Run `run_tests.bat` after running the analysis once. It checks workbook loading,
numerical validation, data cleaning, independence classification, output files,
and figure generation.
