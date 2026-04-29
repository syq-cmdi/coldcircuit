from .plate import ColdPlate


def render_markdown_report(plate: ColdPlate, coolant_inlet_c: float = 25.0) -> str:
    result = plate.simulate_1d(coolant_inlet_c=coolant_inlet_c)
    checks = plate.manufacturability_checks()
    ch = plate.primary_channel()
    lines = [
        f"# ColdCircuit Report: {plate.name}", "",
        "## 1. Design Summary", "",
        f"- Plate size: {plate.base_size_mm[0]} × {plate.base_size_mm[1]} mm",
        f"- Thickness: {plate.thickness_mm} mm",
        f"- Material: {plate.material.name}, k = {plate.material.conductivity_w_mk} W/m-K",
        f"- Coolant: {plate.fluid.name}",
        f"- Flow rate: {plate.inlet_outlet.flow_rate_lpm} L/min",
        f"- Manufacturing process: {plate.manufacturing_process}", "",
        "## 2. Heat Sources", "",
    ]
    for src in plate.heat_sources:
        lines.append(f"- {src.name}: {src.power_w} W, footprint {src.size_mm[0]} × {src.size_mm[1]} mm, center {src.center_xy_mm}, heat flux {src.heat_flux_w_cm2:.1f} W/cm²")
    lines += ["", "## 3. Primary Channel", "", f"- Type: {ch.type}", f"- Width × depth: {ch.width_mm} × {ch.depth_mm} mm", f"- Hydraulic diameter: {result.hydraulic_diameter_mm:.2f} mm", "", "## 4. Fast 1D Simulation", "", f"- Total power: {result.total_power_w:.2f} W", f"- Coolant outlet temperature: {result.coolant_outlet_c:.2f} °C", f"- Coolant temperature rise: {result.coolant_delta_t_k:.2f} K", f"- Reynolds number: {result.reynolds_number:.0f} ({result.flow_regime})", f"- Channel velocity: {result.channel_velocity_m_s:.2f} m/s", f"- Nusselt number: {result.nusselt_number:.2f}", f"- Heat-transfer coefficient: {result.heat_transfer_coefficient_w_m2k:.0f} W/m²-K", f"- Pressure drop: {result.pressure_drop_bar:.3f} bar", f"- Estimated max source temperature: {result.estimated_max_source_temperature_c:.2f} °C", f"- Pass: {'YES' if result.passed else 'NO'}", "", "## 5. Source Temperature Estimates", ""]
    for name, temp in result.source_temperatures_c.items():
        lines.append(f"- {name}: {temp:.2f} °C")
    lines += ["", "## 6. Warnings", ""]
    lines.extend([f"- {w}" for w in result.warnings] if result.warnings else ["- None"])
    lines += ["", "## 7. Manufacturability Checks", ""]
    lines.extend([f"- **{c.severity.upper()}** `{c.item}`: {c.message}" for c in checks] if checks else ["- No rule-based issues detected."])
    lines += ["", "## 8. Qualification Reminder", "", "This MVP model is for early design screening only. Final product design should be validated by detailed CFD, structural pressure testing, leak testing, thermal cycling, corrosion compatibility, vibration/shock, and manufacturing process qualification.", ""]
    return "\n".join(lines)
