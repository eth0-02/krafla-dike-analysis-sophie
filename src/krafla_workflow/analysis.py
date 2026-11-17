"""Domain calculations with explicit, bounded assumptions."""

from __future__ import annotations

import math
from typing import Mapping


def moment_magnitude(moment_nm: float) -> float:
    """Return Mw using the convention recorded in the workbook."""
    if moment_nm <= 0:
        raise ValueError("Seismic moment must be positive.")
    return (2.0 / 3.0) * (math.log10(moment_nm) - 9.1)


def calculate_moment_ranges(values: Mapping[str, tuple[float, float]]) -> dict[str, float]:
    """Recalculate rectangular-dike and boundary-fault moment bounds.

    Bounds are paired low-with-low and high-with-high, mirroring the supplied
    workbook's calculation; they are bounds, not a statistical confidence interval.
    """
    needed = {"G", "dike_length", "dike_height", "dike_opening", "fault_count", "fault_length", "fault_width", "fault_slip", "seismic_moment"}
    missing = needed.difference(values)
    if missing:
        raise ValueError(f"Missing moment inputs: {', '.join(sorted(missing))}")
    low = lambda key: float(values[key][0])
    high = lambda key: float(values[key][1])
    dike_low = low("G") * low("dike_length") * low("dike_height") * low("dike_opening")
    dike_high = high("G") * high("dike_length") * high("dike_height") * high("dike_opening")
    fault_low = low("G") * low("fault_count") * low("fault_length") * low("fault_width") * low("fault_slip")
    fault_high = high("G") * high("fault_count") * high("fault_length") * high("fault_width") * high("fault_slip")
    total_low, total_high = dike_low + fault_low, dike_high + fault_high
    seismic = low("seismic_moment")
    return {
        "dike_moment_low_nm": dike_low, "dike_moment_high_nm": dike_high,
        "fault_moment_low_nm": fault_low, "fault_moment_high_nm": fault_high,
        "total_geodetic_moment_low_nm": total_low, "total_geodetic_moment_high_nm": total_high,
        "mw_total_low": moment_magnitude(total_low), "mw_total_high": moment_magnitude(total_high),
        "seismic_moment_nm": seismic,
        "seismic_share_total_low": seismic / total_low, "seismic_share_total_high": seismic / total_high,
        "seismic_share_fault_low": seismic / fault_low, "seismic_share_fault_high": seismic / fault_high,
    }

