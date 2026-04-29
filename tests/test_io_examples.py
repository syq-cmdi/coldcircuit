from coldcircuit.io import load_plate_json


def test_load_serpentine_example():
    plate = load_plate_json("examples/serpentine_250w.json")
    assert plate.name == "serpentine_250w_demo"
    assert plate.simulate_1d().total_power_w == 250
