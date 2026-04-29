from pydantic import BaseModel, Field

from .materials import Fluid
from .components import ChannelBase, SerpentineChannel, ParallelMicrochannelBank, HeatSource


class SimulationResult(BaseModel):
    total_power_w: float
    flow_rate_lpm: float
    mass_flow_kg_s: float
    coolant_inlet_c: float
    coolant_outlet_c: float
    coolant_delta_t_k: float
    reynolds_number: float
    flow_regime: str
    hydraulic_diameter_mm: float
    channel_velocity_m_s: float
    nusselt_number: float
    heat_transfer_coefficient_w_m2k: float
    pressure_drop_pa: float
    pressure_drop_bar: float
    estimated_max_source_temperature_c: float
    source_temperatures_c: dict[str, float]
    warnings: list[str] = Field(default_factory=list)
    passed: bool


def _friction_factor(re: float) -> tuple[float, str]:
    if re < 1e-9:
        return 0.0, "no_flow"
    if re < 2300:
        return 64.0 / re, "laminar"
    if re < 4000:
        f_lam = 64.0 / 2300.0
        f_turb = 0.3164 / (4000.0 ** 0.25)
        ratio = (re - 2300.0) / 1700.0
        return f_lam * (1 - ratio) + f_turb * ratio, "transition"
    return 0.3164 / (re ** 0.25), "turbulent"


def _nusselt_number(re: float, pr: float) -> float:
    if re < 2300:
        return 4.36
    return 0.023 * (re ** 0.8) * (pr ** 0.4)


def simulate_1d(
    *,
    plate_size_mm: tuple[float, float],
    plate_thickness_mm: float,
    material_conductivity_w_mk: float,
    fluid: Fluid,
    channel: ChannelBase,
    heat_sources: list[HeatSource],
    flow_rate_lpm: float,
    coolant_inlet_c: float = 25.0,
    max_pressure_drop_bar: float | None = None,
) -> SimulationResult:
    """Fast screening model for one equivalent channel or parallel channel bank.

    The model is intentionally conservative and simplified. It is useful for early
    design-space exploration and LLM feedback loops, not final qualification.
    """

    warnings: list[str] = []
    total_power = sum(h.power_w for h in heat_sources)

    q_total_m3_s = flow_rate_lpm / 1000.0 / 60.0
    mass_flow = q_total_m3_s * fluid.density_kg_m3

    path_count = max(channel.equivalent_path_count(), 1)
    q_per_path = q_total_m3_s / path_count
    area_per_path = channel.cross_section_area_m2()
    velocity = q_per_path / max(area_per_path, 1e-12)
    dh = channel.hydraulic_diameter_m()
    re = fluid.density_kg_m3 * velocity * dh / fluid.viscosity_pa_s
    pr = fluid.specific_heat_j_kgk * fluid.viscosity_pa_s / fluid.conductivity_w_mk
    f, regime = _friction_factor(re)
    nu = _nusselt_number(re, pr)
    h = nu * fluid.conductivity_w_mk / dh

    length = channel.length_m(plate_size_mm)
    dp_major = f * (length / dh) * 0.5 * fluid.density_kg_m3 * velocity**2

    minor_k = 0.0
    if isinstance(channel, SerpentineChannel):
        minor_k += channel.bend_count() * channel.bend_loss_k
    if isinstance(channel, ParallelMicrochannelBank):
        minor_k += channel.entrance_loss_k + channel.exit_loss_k
    dp_minor = minor_k * 0.5 * fluid.density_kg_m3 * velocity**2
    dp = dp_major + dp_minor

    coolant_dt = total_power / max(mass_flow * fluid.specific_heat_j_kgk, 1e-12)
    coolant_out = coolant_inlet_c + coolant_dt
    coolant_bulk_mean = coolant_inlet_c + coolant_dt / 2

    wetted_area = channel.total_wetted_perimeter_m() * length
    r_conv_total = 1.0 / max(h * wetted_area, 1e-12)

    channel_depth_m = channel.depth_mm * 1e-3
    remaining_thickness_m = max(0.5e-3, plate_thickness_mm * 1e-3 - channel_depth_m)
    source_temps: dict[str, float] = {}

    for src in heat_sources:
        r_cond = remaining_thickness_m / max(material_conductivity_w_mk * src.area_m2, 1e-12)
        r_tim = src.thermal_interface_resistance_m2k_w / max(src.area_m2, 1e-12)
        # Share convective resistance by power fraction so small sources are not assigned full-plate h unrealistically.
        power_fraction = src.power_w / max(total_power, 1e-12)
        r_conv_allocated = r_conv_total * power_fraction
        source_temps[src.name] = coolant_bulk_mean + src.power_w * (r_cond + r_tim + r_conv_allocated)

    max_t = max(source_temps.values()) if source_temps else coolant_out

    if regime == "laminar":
        warnings.append("Laminar flow: heat transfer may be limited; consider higher flow, smaller hydraulic diameter, or enhanced surfaces.")
    if re > 20000:
        warnings.append("High Reynolds number: pressure drop and erosion/noise risks should be checked.")
    if max_pressure_drop_bar is not None and dp / 1e5 > max_pressure_drop_bar:
        warnings.append("Pressure drop exceeds the specified limit.")
    for src in heat_sources:
        if src.max_temperature_c is not None and source_temps[src.name] > src.max_temperature_c:
            warnings.append(f"{src.name} exceeds max_temperature_c.")
        if src.heat_flux_w_cm2 > 100:
            warnings.append(f"{src.name} heat flux is high; consider copper insert, impingement, microchannels, or pin-fin enhancement.")

    passed = len([w for w in warnings if "exceeds" in w or "Pressure drop exceeds" in w]) == 0

    return SimulationResult(
        total_power_w=total_power,
        flow_rate_lpm=flow_rate_lpm,
        mass_flow_kg_s=mass_flow,
        coolant_inlet_c=coolant_inlet_c,
        coolant_outlet_c=coolant_out,
        coolant_delta_t_k=coolant_dt,
        reynolds_number=re,
        flow_regime=regime,
        hydraulic_diameter_mm=dh * 1e3,
        channel_velocity_m_s=velocity,
        nusselt_number=nu,
        heat_transfer_coefficient_w_m2k=h,
        pressure_drop_pa=dp,
        pressure_drop_bar=dp / 1e5,
        estimated_max_source_temperature_c=max_t,
        source_temperatures_c=source_temps,
        warnings=warnings,
        passed=passed,
    )
