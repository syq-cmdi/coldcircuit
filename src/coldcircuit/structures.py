from enum import Enum
from pydantic import BaseModel, Field, model_validator


class StructureFamily(str, Enum):
    SERPENTINE = "serpentine"
    PARALLEL_MICROCHANNEL = "parallel_microchannel"
    MANIFOLD_MICROCHANNEL = "manifold_microchannel"
    PIN_FIN = "pin_fin"
    IMPINGEMENT = "impingement"
    EMBEDDED = "embedded"
    HYBRID = "hybrid"


class Layer3D(BaseModel):
    """3D stack layer definition for an embedded or assembled cold plate."""
    name: str
    z_min_mm: float
    z_max_mm: float
    role: str = Field(..., description="base, channel, cover, manifold, TIM, insert, chip, gasket, etc.")
    material: str | None = None

    @property
    def thickness_mm(self) -> float:
        return self.z_max_mm - self.z_min_mm

    @model_validator(mode="after")
    def validate_layer(self):
        if self.z_max_mm <= self.z_min_mm:
            raise ValueError("Layer z_max_mm must be greater than z_min_mm.")
        return self


class Port3D(BaseModel):
    name: str
    center_xyz_mm: tuple[float, float, float]
    diameter_mm: float = Field(..., gt=0)
    direction: str = Field("+z", description="+x, -x, +y, -y, +z, -z")
    role: str = Field("inlet", description="inlet or outlet")


class EmbeddedRegion(BaseModel):
    """Local embedded cooling region below/near the heat source."""
    name: str
    footprint_center_xy_mm: tuple[float, float]
    footprint_size_mm: tuple[float, float]
    channel_roof_thickness_mm: float = Field(..., gt=0)
    channel_floor_thickness_mm: float = Field(..., gt=0)
    insert_material: str | None = Field(None, description="e.g., copper insert in aluminum plate")
    target_heat_flux_w_cm2: float | None = None


class ColdPlate3D(BaseModel):
    """3D structural metadata for visualization, embedded design checks, and CAD handoff."""
    structure_family: StructureFamily
    layers: list[Layer3D]
    ports: list[Port3D] = Field(default_factory=list)
    embedded_regions: list[EmbeddedRegion] = Field(default_factory=list)
    recommended_cfd_model: str = "CHT"
    notes: str | None = None

    @property
    def total_thickness_mm(self) -> float:
        return max(layer.z_max_mm for layer in self.layers) - min(layer.z_min_mm for layer in self.layers)

    @model_validator(mode="after")
    def validate_layers(self):
        if not self.layers:
            raise ValueError("At least one 3D layer is required.")
        return self


def default_embedded_stack(total_thickness_mm: float = 10.0, channel_depth_mm: float = 2.0, roof_mm: float = 1.2) -> ColdPlate3D:
    floor = total_thickness_mm - channel_depth_mm - roof_mm
    return ColdPlate3D(
        structure_family=StructureFamily.EMBEDDED,
        layers=[
            Layer3D(name="solid_floor", z_min_mm=0.0, z_max_mm=floor, role="base", material="Aluminum/Copper"),
            Layer3D(name="embedded_channel", z_min_mm=floor, z_max_mm=floor + channel_depth_mm, role="channel", material="coolant"),
            Layer3D(name="channel_roof", z_min_mm=floor + channel_depth_mm, z_max_mm=total_thickness_mm, role="cover", material="Aluminum/Copper"),
        ],
        notes="Default embedded stack: channel placed close to heat source while preserving roof strength.",
    )
