from pydantic import BaseModel, Field

from .components import SerpentineChannel, ParallelMicrochannelBank


class ManufacturingCheck(BaseModel):
    severity: str = Field(..., description="info, warning, error")
    item: str
    message: str


def check_manufacturability(plate) -> list[ManufacturingCheck]:
    """Rule-based early manufacturability checker."""
    checks: list[ManufacturingCheck] = []
    process = plate.manufacturing_process

    for ch in plate.channels:
        if ch.width_mm < 0.8 and process in {"cnc_brazed", "vacuum_brazed", "friction_stir_welded"}:
            checks.append(ManufacturingCheck(severity="warning", item="channel_width", message="Conventional machined/brazed cold plates usually need explicit validation below 0.8 mm channel width."))
        if ch.depth_mm / ch.width_mm > 2.5:
            checks.append(ManufacturingCheck(severity="warning", item="aspect_ratio", message="Channel depth/width ratio is high; machining stability and chip evacuation require review."))
        cover_thickness = plate.thickness_mm - ch.depth_mm
        if cover_thickness < 1.0:
            checks.append(ManufacturingCheck(severity="error", item="cover_thickness", message="Remaining cover/base thickness below 1.0 mm; pressure strength and leakage risk are high."))
        elif cover_thickness < 1.5:
            checks.append(ManufacturingCheck(severity="warning", item="cover_thickness", message="Remaining cover/base thickness below 1.5 mm; verify pressure, flatness and brazing deformation."))
        if isinstance(ch, (SerpentineChannel, ParallelMicrochannelBank)):
            web = ch.pitch_mm - ch.width_mm
            if web < 0.8:
                checks.append(ManufacturingCheck(severity="error", item="web_thickness", message=f"Channel web thickness is {web:.2f} mm; too thin for many conventional processes."))
            elif web < 1.2:
                checks.append(ManufacturingCheck(severity="warning", item="web_thickness", message=f"Channel web thickness is {web:.2f} mm; check milling tolerance and deformation."))

    material_name = plate.material.name.lower()
    if "copper" in material_name:
        checks.append(ManufacturingCheck(severity="info", item="material", message="Copper improves spreading and local heat flux handling but increases mass, cost, galvanic corrosion risk and vehicle vibration burden."))
    if "aluminum" in material_name:
        checks.append(ManufacturingCheck(severity="info", item="material", message="Aluminum is usually a strong vehicle baseline; use copper inserts only when local spreading demands it."))
    if plate.inlet_outlet.port_diameter_mm < 4:
        checks.append(ManufacturingCheck(severity="warning", item="port_diameter", message="Small port diameter may dominate pressure drop or be incompatible with vehicle coolant connectors."))
    return checks
