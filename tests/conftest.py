"""Reusable, source-free workbook fixture for workflow tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_valid_workbook(path: Path) -> Path:
    """Create a small workbook that follows the required research schema."""
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame([["Synthetic workbook for automated tests only."]]).to_excel(writer, sheet_name="README", index=False, header=False)
        pd.DataFrame([{
            "ID": "C01", "Parameter": "Crisis period", "Low": 1975, "Central (as reported)": None, "High": 1984,
            "Unit": "year", "σ reported": None, "σ assigned (range/4)": None, "Source": "test", "Type": "Reported", "Confidence": "High", "Notes": "test",
        }]).to_excel(writer, sheet_name="Crisis_totals", index=False)
        pd.DataFrame([
            {"ID": "S1", "Segment": "South", "Dataset / model": "single dike model", "Parameter": "Dike opening", "Best / reported": 5.0, "Low (approx.)": 4.0, "High (approx.)": 6.0, "Unit": "m", "σ assigned (range/4)": 0.5, "Source": "test", "Type": "Model", "Confidence": "Low", "Notes": "test"},
            {"ID": "S2", "Segment": "North", "Dataset / model": "single dike model", "Parameter": "Fault slip", "Best / reported": 2.0, "Low (approx.)": 1.5, "High (approx.)": 2.5, "Unit": "m", "σ assigned (range/4)": 0.25, "Source": "test", "Type": "Model", "Confidence": "Low", "Notes": "test"},
        ]).to_excel(writer, sheet_name="Segment_models", index=False)
        pd.DataFrame([
            {"Episode #": 1, "Date (as given)": "20 Dec 1975", "What the papers say": "test", "Opening (m)": None, "Fault slip (m)": 2.0, "Dike top depth (km)": None, "Extent along rift": "test", "Seismic moment (N·m)": 3.3e18, "Source in the supplied papers": "test", "Data status": "Described, no per-dike numbers"},
            {"Episode #": 2, "Date (as given)": "Jan 1978", "What the papers say": "test", "Opening (m)": 4.0, "Fault slip (m)": None, "Dike top depth (km)": 2.2, "Extent along rift": "test", "Seismic moment (N·m)": None, "Source in the supplied papers": "test", "Data status": "Modelled; Low-Medium confidence"},
        ]).to_excel(writer, sheet_name="Episodes", index=False)
        moment_values = [
            ("Shear modulus G", 30e9, 30e9), ("Dike length (rift length)", 70e3, 80e3), ("Dike height", 3e3, 4e3),
            ("Dike opening", 4.3, 5.4), ("Number of faults", 2, 2), ("Fault length", 70e3, 80e3),
            ("Fault width (down-dip)", 1e3, 2e3), ("Fault slip", 4, 4), ("Seismic moment (whole crisis)", 5.8e18, 5.8e18),
        ]
        pd.DataFrame([{"Quantity": quantity, "Low": low, "High": high, "Unit": "test", "Note": "test"} for quantity, low, high in moment_values]).to_excel(writer, sheet_name="Moment_calc", index=False)
        pd.DataFrame([
            {"Case": "South model A", "Unit of observation": "Cumulative, whole crisis", "w0 dike opening (m)": 6.4, "σ w0": 1.0, "s fault slip (m)": 2.8, "σ s": 0.75, "d dike top depth (km)": 0.75, "σ d": 0.23, "H dike height (km)": 2.7, "σ H": 1.25, "Surface extension (m)": 4.75, "σ ext": 0.75, "Source": "test", "Confidence": "Low", "Notes": "test"},
            {"Case": "South model B", "Unit of observation": "Cumulative, whole crisis", "w0 dike opening (m)": 5.0, "σ w0": 0.6, "s fault slip (m)": 2.8, "σ s": None, "d dike top depth (km)": 0.43, "σ d": 0.23, "H dike height (km)": 5.9, "σ H": 1.5, "Surface extension (m)": 4.28, "σ ext": 0.05, "Source": "test", "Confidence": "Low", "Notes": "test"},
            {"Case": "North west fault", "Unit of observation": "Single dike", "w0 dike opening (m)": 4.7, "σ w0": None, "s fault slip (m)": 1.85, "σ s": None, "d dike top depth (km)": 2.2, "σ d": None, "H dike height (km)": 3.7, "σ H": None, "Surface extension (m)": 2.6, "σ ext": None, "Source": "test", "Confidence": "Low", "Notes": "test"},
            {"Case": "North east fault", "Unit of observation": "Single dike", "w0 dike opening (m)": 4.7, "σ w0": None, "s fault slip (m)": 4.9, "σ s": None, "d dike top depth (km)": 2.2, "σ d": None, "H dike height (km)": 3.7, "σ H": None, "Surface extension (m)": 2.6, "σ ext": None, "Source": "test", "Confidence": "Low", "Notes": "test"},
            {"Case": "North updated model", "Unit of observation": "Single dike", "w0 dike opening (m)": 3.8, "σ w0": None, "s fault slip (m)": None, "σ s": None, "d dike top depth (km)": None, "σ d": None, "H dike height (km)": None, "σ H": None, "Surface extension (m)": 2.7, "σ ext": None, "Source": "test", "Confidence": "Low", "Notes": "test"},
        ]).to_excel(writer, sheet_name="Regression_ready", index=False)
        pd.DataFrame([{"Quantity": "EDM length changes", "What the paper says about its uncertainty": "0.1 m", "Where": "test", "How to use it": "Use σ ≈ 0.05 m"}]).to_excel(writer, sheet_name="Uncertainty_basis", index=False)
        pd.DataFrame([{ "#": 1, "Item": "test conflict", "What the papers say": "test", "How I handled it": "Reported without reconciliation" }]).to_excel(writer, sheet_name="Paper_conflicts", index=False)
    return path
