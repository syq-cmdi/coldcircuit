from copy import deepcopy
from itertools import product
from typing import Any
from pydantic import BaseModel, Field

from .plate import ColdPlate


class OptimizationCandidate(BaseModel):
    variables: dict[str, float | int]
    max_temperature_c: float
    pressure_drop_bar: float
    coolant_delta_t_k: float
    reynolds_number: float
    passed: bool
    score: float
    warnings: list[str] = Field(default_factory=list)


class OptimizationResult(BaseModel):
    objective: str
    candidate_count: int
    feasible_count: int
    best: OptimizationCandidate | None
    candidates: list[OptimizationCandidate]


def _set_nested_attr(plate: ColdPlate, key: str, value: Any) -> ColdPlate:
    p = deepcopy(plate)
    ch = p.channels[0]
    if key == "channel.width_mm":
        ch.width_mm = value
    elif key == "channel.depth_mm":
        ch.depth_mm = value
    elif key == "channel.pitch_mm" and hasattr(ch, "pitch_mm"):
        ch.pitch_mm = value
    elif key == "channel.pass_count" and hasattr(ch, "pass_count"):
        ch.pass_count = int(value)
    elif key == "inlet_outlet.flow_rate_lpm":
        p.inlet_outlet.flow_rate_lpm = value
    else:
        raise ValueError(f"Unsupported optimization variable: {key}")
    return ColdPlate.model_validate(p.model_dump())


def optimize_grid(
    plate: ColdPlate,
    variable_grid: dict[str, list[float | int]],
    *,
    coolant_inlet_c: float = 25.0,
    objective: str = "min_temperature_then_pressure",
    top_k: int = 20,
) -> OptimizationResult:
    """Simple deterministic grid search for early design screening."""
    keys = list(variable_grid.keys())
    candidates: list[OptimizationCandidate] = []

    for values in product(*[variable_grid[k] for k in keys]):
        variables = dict(zip(keys, values))
        try:
            candidate_plate = plate
            for k, v in variables.items():
                candidate_plate = _set_nested_attr(candidate_plate, k, v)
            sim = candidate_plate.simulate_1d(coolant_inlet_c=coolant_inlet_c)
            if objective == "min_pressure_then_temperature":
                score = sim.pressure_drop_bar * 1000 + sim.estimated_max_source_temperature_c
            else:
                score = sim.estimated_max_source_temperature_c * 1000 + sim.pressure_drop_bar
            candidates.append(OptimizationCandidate(variables=variables, max_temperature_c=sim.estimated_max_source_temperature_c, pressure_drop_bar=sim.pressure_drop_bar, coolant_delta_t_k=sim.coolant_delta_t_k, reynolds_number=sim.reynolds_number, passed=sim.passed, score=score, warnings=sim.warnings))
        except Exception as exc:
            candidates.append(OptimizationCandidate(variables=variables, max_temperature_c=1e9, pressure_drop_bar=1e9, coolant_delta_t_k=1e9, reynolds_number=0, passed=False, score=1e12, warnings=[f"Invalid candidate: {exc}"]))

    feasible = [c for c in candidates if c.passed]
    ranked = sorted(feasible or candidates, key=lambda c: c.score)
    return OptimizationResult(objective=objective, candidate_count=len(candidates), feasible_count=len(feasible), best=ranked[0] if ranked else None, candidates=ranked[:top_k])
