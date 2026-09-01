"""Non-regression tests on the pipeline's pure functions.

Small, deterministic checks on functions whose output can be computed by hand: they catch a silent
change in behaviour (a refactor, a dependency bump) that "it runs" would miss. Run from the project
root with:  PYTHONPATH=/opt/conda/lib/python3.11/site-packages python3 -m pytest tests/ -q
(or simply `python3 tests/test_pipeline.py` for the plain-assert fallback).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "utils"))

import geopandas as gpd  # noqa: E402
import numpy as np  # noqa: E402
import xarray as xr  # noqa: E402
from shapely.geometry import LineString  # noqa: E402

import connectivity  # noqa: E402
import routing  # noqa: E402


def test_get_binary_habitat():
    """Habitat codes -> 1, other codes -> 0, NaN -> 0, dtype uint8."""
    da = xr.DataArray(np.array([[10.0, 20.0], [50.0, np.nan]]), dims=("y", "x"))
    out = connectivity.get_binary_habitat(da, [10, 20])
    assert out.dtype == np.uint8
    assert out.values.tolist() == [[1, 1], [0, 0]]


def test_calculate_tortuosity():
    """tortuosity = real/theoretical ; a straight path = 1.0 ; theoretical 0 -> NaN (not inf)."""
    gdf = gpd.GeoDataFrame(
        {
            "real_dist": [100.0, 150.0, 5.0],
            "theoretical_dist": [100.0, 100.0, 0.0],
            "geometry": [LineString([(0, 0), (1, 1)])] * 3,
        }
    )
    out = routing.calculate_tortuosity(gdf)
    assert out["tortuosity"].iloc[0] == 1.0
    assert out["tortuosity"].iloc[1] == 1.5
    assert np.isnan(out["tortuosity"].iloc[2])


if __name__ == "__main__":
    test_get_binary_habitat()
    test_calculate_tortuosity()
    print("OK: 2/2 tests passed")
