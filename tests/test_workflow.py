import hashlib

import pandas as pd
import pytest

from krafla_workflow.__main__ import EXPECTED_SHEETS, clean_table, extract_moment_inputs, regression_readiness, run
from krafla_workflow.data_loader import load_workbook
from krafla_workflow.regression import assess_regression_readiness
from krafla_workflow.validation import classify_independence

from conftest import write_valid_workbook


def test_clean_table_preserves_named_blank_schema_columns_but_removes_unlabelled_ones():
    frame = pd.DataFrame({"a": [1, "  "], "named_but_blank": [None, None], "Unnamed: 2": [None, None]})
    result = clean_table(frame)
    assert list(result.columns) == ["a", "named_but_blank"]
    assert len(result) == 1


def test_regression_readiness_blocks_fit_for_supplied_structure():
    frame = pd.DataFrame({
        "Case": ["South model", "North west fault", "North east fault"], "Unit of observation": ["Cumulative", "Single dike", "Single dike"],
        "w0 dike opening (m)": [5.0, 4.7, 4.7], "s fault slip (m)": [2.8, 1.8, 4.9], "d dike top depth (km)": [0.4, 2.2, 2.2],
    })
    report = regression_readiness(frame)
    assert report["fit_inferential_regression"] is False
    assert report["independent_geological_configurations"] == 2


def test_expected_sheet_contract_is_complete():
    assert "Moment_calc" in EXPECTED_SHEETS
    assert "Episodes" in EXPECTED_SHEETS


def test_moment_input_rejects_invalid_bounds():
    frame = pd.DataFrame({"Quantity": ["Shear modulus G"], "Low": [2], "High": [1]})
    with pytest.raises(ValueError, match="Low greater"):
        extract_moment_inputs(frame)


def test_end_to_end_run_writes_traceable_outputs(tmp_path):
    """Exercise ingestion, raw-copy preservation, figures, reports, and outputs."""
    source = write_valid_workbook(tmp_path / "source.xlsx")
    original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    output = run(source, tmp_path / "outputs", tmp_path / "raw")
    assert (output / "moment_recalculation.json").is_file()
    assert (output / "figures" / "moment_ranges.png").is_file()
    assert (output / "figures" / "moment_ranges.pdf").is_file()
    assert (output / "figures" / "figure_manifest.csv").is_file()
    assert (output / "tables" / "regression_data_clean.csv").is_file()
    assert (output / "tables" / "data_quality_report.csv").is_file()
    assert (output / "tables" / "descriptive_statistics.csv").is_file()
    assert (output / "tables" / "episode_data_completeness.csv").is_file()
    assert (output / "reports" / "technical_report.md").is_file()
    assert (output / "run_metadata.json").is_file()
    assert (tmp_path / "raw" / "source.xlsx").is_file()
    assert hashlib.sha256(source.read_bytes()).hexdigest() == original_hash


def test_loader_rejects_missing_required_sheet(tmp_path):
    source = tmp_path / "invalid.xlsx"
    pd.DataFrame({"value": [1]}).to_excel(source, sheet_name="Only_sheet", index=False)
    with pytest.raises(ValueError, match="Missing required worksheets"):
        load_workbook(source)


def test_independence_classification_and_assessment_are_conservative():
    frame = pd.DataFrame({
        "Case": ["South KH9 model", "South EDM model", "North west fault", "North east fault"],
        "Unit of observation": ["Cumulative", "Cumulative", "Single dike", "Single dike"],
        "w0 dike opening (m)": [6.4, 5.0, 4.7, 4.7],
        "s fault slip (m)": [2.8, 2.8, 1.85, 4.9],
        "d dike top depth (km)": [0.75, 0.43, 2.2, 2.2],
    })
    classified = classify_independence(frame)
    assessment = assess_regression_readiness(classified)
    assert classified["independence_group"].nunique() == 2
    assert not classified["eligible_for_inferential_regression"].any()
    assert not assessment["inferential_regression_fitted"].any()
