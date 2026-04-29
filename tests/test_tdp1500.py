from coldcircuit.tdp1500 import make_tdp1500_reference_design, make_tdp1500_3d_stack, tdp1500_guidance
from coldcircuit.design_rules import all_rules_grouped


def test_tdp1500_reference_runs():
    plate = make_tdp1500_reference_design()
    result = plate.simulate_1d()
    assert result.total_power_w == 1500
    assert result.reynolds_number > 0
    assert result.pressure_drop_bar >= 0


def test_tdp1500_stack_has_layers():
    stack = make_tdp1500_3d_stack()
    assert stack.total_thickness_mm == 10.0
    assert len(stack.layers) >= 3


def test_rules_grouped():
    grouped = all_rules_grouped()
    assert "embedded" in grouped
    assert "hybrid" in grouped
    assert len(grouped["embedded"]) > 0


def test_guidance_mentions_1500w():
    guidance = tdp1500_guidance()
    assert guidance.target_tdp_w == 1500.0
    assert "hybrid" in guidance.recommended_families
