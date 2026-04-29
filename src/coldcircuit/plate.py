from typing import Annotated, Union, Literal
from pydantic import BaseModel, Field, model_validator

from .materials import Material, Fluid
from .components import HeatSource, InletOutlet, StraightChannel, SerpentineChannel, ParallelMicrochannelBank, PinFinArray, Manifold
from .simulation import SimulationResult, simulate_1d
from .manufacturing import check_manufacturability


Channel = Annotated[Union[StraightChannel, SerpentineChannel, ParallelMicrochannelBank], Field(discriminator="type")]


class ColdPlate(BaseModel):
    """Top-level declarative liquid cold plate model."""

    name: str = "ColdPlate"
    base_size_mm: tuple[float, float] = Field(..., description="Plate length x width, mm")
    thickness_mm: float = Field(..., gt=0)
    material: Material = Field(default_factory=Material.aluminum_6061)
    fluid: Fluid = Field(default_factory=Fluid.water)
    inlet_outlet: InletOutlet
    channels: list[Channel] = Field(default_factory=list)
    fins: PinFinArray | None = None
    manifolds: list[Manifold] = Field(default_factory=list)
    heat_sources: list[HeatSource] = Field(default_factory=list)
    manufacturing_process: Literal["cnc_brazed", "friction_stir_welded", "vacuum_brazed", "additive_manufactured", "prototype_unknown"] = "prototype_unknown"
    design_notes: str | None = None

    @model_validator(mode="after")
    def validate_plate(self):
        if not self.channels:
            raise ValueError("At least one channel is required.")
        if not self.heat_sources:
            raise ValueError("At least one heat source is required.")
        x, y = self.base_size_mm
        for src in self.heat_sources:
            sx, sy = src.center_xy_mm
            if not (0 <= sx <= x and 0 <= sy <= y):
                raise ValueError(f"Heat source {src.name} center is outside plate boundary.")
        for ch in self.channels:
            if ch.depth_mm >= self.thickness_mm:
                raise ValueError("Channel depth must be smaller than total plate thickness.")
        return self

    def primary_channel(self):
        return self.channels[0]

    def simulate_1d(self, coolant_inlet_c: float = 25.0) -> SimulationResult:
        return simulate_1d(
            plate_size_mm=self.base_size_mm,
            plate_thickness_mm=self.thickness_mm,
            material_conductivity_w_mk=self.material.conductivity_w_mk,
            fluid=self.fluid,
            channel=self.primary_channel(),
            heat_sources=self.heat_sources,
            flow_rate_lpm=self.inlet_outlet.flow_rate_lpm,
            coolant_inlet_c=coolant_inlet_c,
            max_pressure_drop_bar=self.inlet_outlet.max_pressure_drop_bar,
        )

    def manufacturability_checks(self):
        return check_manufacturability(self)

    def manufacturability_notes(self) -> list[str]:
        return [f"{c.severity.upper()} [{c.item}] {c.message}" for c in self.manufacturability_checks()]

    def export_step_placeholder(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write("STEP export placeholder. Use coldcircuit.backends.cad_build123d when installed.\n")
