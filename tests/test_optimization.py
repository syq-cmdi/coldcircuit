from coldcircuit.io import load_plate_json
from coldcircuit.optimization import optimize_grid


def test_optimize_grid_runs():
    plate = load_plate_json("examples/serpentine_250w.json")
    result = optimize_grid(plate, {"channel.width_mm": [1.5, 2.0], "inlet_outlet.flow_rate_lpm": [1.0, 1.5]}, top_k=3)
    assert result.candidate_count == 4
    assert result.best is not None
