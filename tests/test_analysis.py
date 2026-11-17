import math

import pytest

from krafla_workflow.analysis import calculate_moment_ranges, moment_magnitude


VALUES = {"G": (30e9, 30e9), "dike_length": (70e3, 80e3), "dike_height": (3e3, 4e3), "dike_opening": (4.3, 5.4), "fault_count": (2, 2), "fault_length": (70e3, 80e3), "fault_width": (1e3, 2e3), "fault_slip": (4, 4), "seismic_moment": (5.8e18, 5.8e18)}


def test_calculates_workbook_moment_bounds():
    result = calculate_moment_ranges(VALUES)
    assert result["dike_moment_low_nm"] == pytest.approx(2.709e19)
    assert result["dike_moment_high_nm"] == pytest.approx(5.184e19)
    assert result["fault_moment_low_nm"] == pytest.approx(1.68e19)
    assert result["total_geodetic_moment_high_nm"] == pytest.approx(9.024e19)
    assert result["seismic_share_total_low"] == pytest.approx(5.8e18 / 4.389e19)


def test_magnitude_matches_recorded_convention():
    assert moment_magnitude(5.8e18) == pytest.approx(6.442285, abs=1e-6)


def test_rejects_missing_input():
    with pytest.raises(ValueError, match="fault_slip"):
        calculate_moment_ranges({k: v for k, v in VALUES.items() if k != "fault_slip"})


@pytest.mark.parametrize("value", [0, -1])
def test_rejects_nonpositive_moment(value):
    with pytest.raises(ValueError):
        moment_magnitude(value)

