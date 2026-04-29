# ColdCircuit

**ColdCircuit** is an LLM-friendly liquid cold-plate thermal design library: a declarative, version-controlled, Python-native toolkit for creating, checking, simulating, optimizing, and exporting early-stage liquid cold plate designs.

定位：**React / tscircuit for liquid cold plates**。

ColdCircuit is designed for workflows where a human engineer or an LLM generates a structured design specification, then the library validates it, runs a fast thermal-hydraulic screening model, checks manufacturability constraints, and prepares downstream CAD / CFD / manufacturing artifacts.

> Current version: `0.2.0` engineering MVP.  
> Built-in simulation is for early design screening, not final CFD/qualification.

---

## Features

### Already implemented

- Declarative `ColdPlate` object model
- Pydantic v2 schema validation
- JSON/YAML-style specification support
- Core components:
  - base plate
  - straight channel
  - serpentine channel
  - parallel microchannel bank
  - manifold
  - pin-fin array metadata
  - heat sources
  - inlet/outlet ports
- Fast 1D thermal-hydraulic screening:
  - Reynolds number
  - hydraulic diameter
  - Nusselt number
  - coolant temperature rise
  - pressure drop
  - estimated heat-source temperature
  - pass/fail against constraints
- Manufacturability checks:
  - minimum channel width
  - web thickness
  - aspect ratio
  - cover thickness
  - bend radius / pitch sanity
  - material notes for aluminum/copper/vehicle use
- Optimization:
  - lightweight grid search
  - constraint filtering
  - objective ranking
- Optional backend stubs:
  - build123d/CadQuery CAD adapter
  - OpenFOAM case generator
- CLI:
  - simulate
  - report
  - optimize
  - validate
  - schema
  - openfoam
- GitHub-ready engineering repo:
  - tests
  - GitHub Actions
  - docs
  - examples
  - license
  - contribution guide

### Planned

- production STEP generation through build123d
- robust channel boolean subtraction
- OpenFOAM meshing templates
- conjugate heat-transfer CFD
- response-surface / surrogate optimization
- LLM tool-call playground
- validated empirical correlations for cold-plate families

---

## Install

```bash
pip install -e .
```

Optional dev install:

```bash
pip install -e ".[dev]"
```

---

## Quick Start

```python
from coldcircuit import (
    ColdPlate, Material, Fluid, InletOutlet,
    SerpentineChannel, HeatSource
)

plate = ColdPlate(
    name="serpentine_250w_demo",
    base_size_mm=(100, 80),
    thickness_mm=8,
    material=Material.aluminum_6061(),
    fluid=Fluid.water(),
    inlet_outlet=InletOutlet(
        inlet_xy_mm=(8, 8),
        outlet_xy_mm=(92, 72),
        port_diameter_mm=6,
        flow_rate_lpm=1.5,
        max_pressure_drop_bar=0.5,
    ),
    channels=[
        SerpentineChannel(
            width_mm=2.0,
            depth_mm=1.5,
            pass_count=8,
            pitch_mm=6.0,
            margin_mm=8.0,
        )
    ],
    heat_sources=[
        HeatSource(
            name="250W chip",
            center_xy_mm=(50, 40),
            size_mm=(25, 25),
            power_w=250,
            max_temperature_c=55,
        )
    ],
    manufacturing_process="cnc_brazed",
)

result = plate.simulate_1d(coolant_inlet_c=25)
print(result.model_dump_json(indent=2))
```

---

## CLI

```bash
coldcircuit validate examples/serpentine_250w.json
coldcircuit simulate examples/serpentine_250w.json
coldcircuit report examples/serpentine_250w.json --out report.md
coldcircuit optimize examples/serpentine_250w.json --out optimization.json
coldcircuit schema --out coldcircuit_schema.json
coldcircuit openfoam examples/serpentine_250w.json --case-dir openfoam_case
```

---

## LLM Usage Pattern

Recommended approach:

1. Ask the LLM to output **only JSON** following the ColdCircuit schema.
2. Validate the JSON with `coldcircuit validate`.
3. Run `simulate`.
4. Ask the LLM to revise only failed variables.
5. Run `optimize` for bounded design variables.
6. Export CAD/CFD artifacts for engineering review.

Example prompt:

```text
Output a ColdCircuit JSON only.

Design a 70 × 45 × 6 mm liquid cold plate for two 120 W vehicle GaN modules.
Use 50/50 ethylene-glycol water coolant, 1.2 L/min flow rate, vacuum-brazed aluminum,
serpentine channel, pressure drop below 0.7 bar, max module temperature below 85°C.
```

---

## Engineering warning

This library is intentionally conservative and simplified. Before product release, validate by:

- detailed CFD;
- structural pressure analysis;
- leak testing;
- thermal cycling;
- vibration/shock testing;
- corrosion / coolant compatibility testing;
- manufacturing process qualification;
- inspection and traceability plan.
