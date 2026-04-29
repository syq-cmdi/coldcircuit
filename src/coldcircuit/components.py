from typing import Literal
from math import pi
from pydantic import BaseModel, Field, model_validator


class HeatSource(BaseModel):
    """Localized heat source mounted on the cold plate."""
    name: str = "Heat source"
    center_xy_mm: tuple[float, float]
    size_mm: tuple[float, float] = Field(..., description="Footprint size in x/y, mm")
    power_w: float = Field(..., gt=0)
    max_temperature_c: float | None = Field(None, description="Design limit")
    thermal_interface_resistance_m2k_w: float = Field(0.0, ge=0, description="Area-normalized TIM resistance, m²-K/W")

    @property
    def area_m2(self) -> float:
        return self.size_mm[0] * 1e-3 * self.size_mm[1] * 1e-3

    @property
    def heat_flux_w_cm2(self) -> float:
        return self.power_w / (self.size_mm[0] * self.size_mm[1] / 100.0)


class InletOutlet(BaseModel):
    inlet_xy_mm: tuple[float, float]
    outlet_xy_mm: tuple[float, float]
    port_diameter_mm: float = Field(..., gt=0)
    flow_rate_lpm: float = Field(..., gt=0)
    max_pressure_drop_bar: float | None = Field(0.5, gt=0)


class ChannelBase(BaseModel):
    type: str
    width_mm: float = Field(..., gt=0)
    depth_mm: float = Field(..., gt=0)
    surface_roughness_um: float = Field(1.6, ge=0)

    def hydraulic_diameter_m(self) -> float:
        w = self.width_mm * 1e-3
        d = self.depth_mm * 1e-3
        return 2 * w * d / (w + d)

    def cross_section_area_m2(self) -> float:
        return self.width_mm * 1e-3 * self.depth_mm * 1e-3

    def total_flow_area_m2(self) -> float:
        return self.cross_section_area_m2()

    def wetted_perimeter_m(self) -> float:
        return 2 * (self.width_mm + self.depth_mm) * 1e-3

    def total_wetted_perimeter_m(self) -> float:
        return self.wetted_perimeter_m()

    def length_m(self, plate_size_mm: tuple[float, float]) -> float:
        raise NotImplementedError

    def equivalent_path_count(self) -> int:
        return 1

    def bend_count(self) -> int:
        return 0


class StraightChannel(ChannelBase):
    type: Literal["straight"] = "straight"
    length_mm: float = Field(..., gt=0)

    def length_m(self, plate_size_mm: tuple[float, float]) -> float:
        return self.length_mm * 1e-3


class SerpentineChannel(ChannelBase):
    type: Literal["serpentine"] = "serpentine"
    pass_count: int = Field(..., ge=2)
    pitch_mm: float = Field(..., gt=0)
    margin_mm: float = Field(6.0, ge=0)
    bend_loss_k: float = Field(0.8, ge=0, description="Minor loss coefficient per 180-degree bend")

    @model_validator(mode="after")
    def validate_pitch(self):
        if self.pitch_mm <= self.width_mm:
            raise ValueError("pitch_mm should be greater than width_mm to maintain web thickness.")
        return self

    def length_m(self, plate_size_mm: tuple[float, float]) -> float:
        plate_x, _ = plate_size_mm
        straight_len = max(plate_x - 2 * self.margin_mm, self.width_mm)
        bend_len = pi * (self.pitch_mm / 2.0)
        total_mm = self.pass_count * straight_len + max(self.pass_count - 1, 0) * bend_len
        return total_mm * 1e-3

    def bend_count(self) -> int:
        return max(self.pass_count - 1, 0)


class ParallelMicrochannelBank(ChannelBase):
    """Parallel microchannel bank. Pressure drop is evaluated along one path; heat transfer area is multiplied."""
    type: Literal["parallel_microchannel_bank"] = "parallel_microchannel_bank"
    channel_count: int = Field(..., ge=2)
    length_mm: float = Field(..., gt=0)
    pitch_mm: float = Field(..., gt=0)
    entrance_loss_k: float = Field(0.5, ge=0)
    exit_loss_k: float = Field(0.5, ge=0)

    @model_validator(mode="after")
    def validate_microchannel_pitch(self):
        if self.pitch_mm <= self.width_mm:
            raise ValueError("pitch_mm must be greater than width_mm.")
        return self

    def length_m(self, plate_size_mm: tuple[float, float]) -> float:
        return self.length_mm * 1e-3

    def equivalent_path_count(self) -> int:
        return self.channel_count

    def total_flow_area_m2(self) -> float:
        return self.channel_count * self.cross_section_area_m2()

    def total_wetted_perimeter_m(self) -> float:
        return self.channel_count * self.wetted_perimeter_m()


class PinFinArray(BaseModel):
    type: Literal["pin_fin_array"] = "pin_fin_array"
    shape: Literal["cylindrical", "square"] = "cylindrical"
    pitch_mm: float = Field(..., gt=0)
    diameter_or_width_mm: float = Field(..., gt=0)
    height_mm: float = Field(..., gt=0)
    count_x: int = Field(..., ge=1)
    count_y: int = Field(..., ge=1)

    @property
    def count(self) -> int:
        return self.count_x * self.count_y

    def projected_blockage_ratio(self) -> float:
        return min(0.85, self.diameter_or_width_mm / max(self.pitch_mm, 1e-9))


class Manifold(BaseModel):
    type: Literal["manifold"] = "manifold"
    strategy: Literal["single_in_single_out", "dual_side", "center_feed"] = "single_in_single_out"
    width_mm: float = Field(6.0, gt=0)
    depth_mm: float = Field(2.0, gt=0)
    balancing_note: str | None = None
