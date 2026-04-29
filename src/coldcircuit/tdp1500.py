from pydantic import BaseModel, Field

from .materials import Material, Fluid
from .components import HeatSource, InletOutlet, ParallelMicrochannelBank, PinFinArray, Manifold
from .plate import ColdPlate
from .structures import ColdPlate3D, StructureFamily, Layer3D, EmbeddedRegion, Port3D


class TDP1500Guidance(BaseModel):
    target_tdp_w: float = 1500.0
    recommended_families: list[str]
    architecture_summary: str
    hard_constraints: list[str]
    optimization_variables: dict[str, tuple[float, float]]
    validation_plan: list[str]


def tdp1500_guidance() -> TDP1500Guidance:
    return TDP1500Guidance(
        recommended_families=["manifold_microchannel", "embedded", "pin_fin", "hybrid"],
        architecture_summary="For 1500 W class TDP, use short parallel flow paths, embedded cooling near hotspots, high-conductivity spreading under chiplets, and manifold-balanced distribution. Avoid one long serpentine path as the default architecture.",
        hard_constraints=[
            "Use multi-inlet/multi-outlet or low-loss manifolds to control pressure drop.",
            "Keep roof/cover thickness above process-specific structural limit, typically >= 1.0-1.5 mm before validation.",
            "Use local copper spreading or copper insert only where heat flux requires it; validate galvanic isolation and joining.",
            "Check flow maldistribution and conjugate heat transfer by CFD before release.",
            "Validate leak tightness, pressure cycling, thermal cycling, vibration and coolant compatibility.",
        ],
        optimization_variables={
            "channel.width_mm": (0.6, 2.0),
            "channel.depth_mm": (1.0, 4.0),
            "channel.pitch_mm": (1.2, 4.0),
            "channel.channel_count": (20, 160),
            "inlet_outlet.flow_rate_lpm": (3.0, 15.0),
            "embedded.channel_roof_thickness_mm": (1.0, 2.5),
            "manifold.width_mm": (8.0, 30.0),
        },
        validation_plan=[
            "Run fast 1D screening to eliminate infeasible pressure/temperature combinations.",
            "Run 3D conjugate CFD for top candidates.",
            "Run structural pressure analysis on roof and cover plate.",
            "Prototype leak, burst, thermal cycling, and vibration tests.",
            "Inspect dimensional tolerance and flatness after joining process.",
        ],
    )


def make_tdp1500_reference_design() -> ColdPlate:
    """Reference 1500 W high-density cold plate concept for screening.

    This is not a released product design; it is a starting point for optimization.
    """
    return ColdPlate(
        name="tdp1500_hybrid_manifold_microchannel_reference",
        base_size_mm=(180.0, 120.0),
        thickness_mm=10.0,
        material=Material.copper_c110(),
        fluid=Fluid.water(),
        inlet_outlet=InletOutlet(inlet_xy_mm=(10.0, 60.0), outlet_xy_mm=(170.0, 60.0), port_diameter_mm=12.0, flow_rate_lpm=8.0, max_pressure_drop_bar=1.2),
        channels=[
            ParallelMicrochannelBank(
                width_mm=1.0,
                depth_mm=2.5,
                channel_count=80,
                length_mm=120.0,
                pitch_mm=2.0,
                entrance_loss_k=0.6,
                exit_loss_k=0.6,
            )
        ],
        fins=PinFinArray(shape="cylindrical", pitch_mm=2.5, diameter_or_width_mm=1.0, height_mm=2.0, count_x=40, count_y=24),
        manifolds=[Manifold(strategy="dual_side", width_mm=18.0, depth_mm=4.0, balancing_note="Use dual-side manifold and short channel paths for 1500 W class designs.")],
        heat_sources=[
            HeatSource(name="AI accelerator module", center_xy_mm=(90.0, 60.0), size_mm=(70.0, 70.0), power_w=1500.0, max_temperature_c=75.0, thermal_interface_resistance_m2k_w=0.000005)
        ],
        manufacturing_process="additive_manufactured",
        design_notes="1500 W reference: copper-equivalent hybrid manifold microchannel with local pin-fin metadata. Use as screening baseline only.",
    )


def make_tdp1500_3d_stack() -> ColdPlate3D:
    return ColdPlate3D(
        structure_family=StructureFamily.HYBRID,
        layers=[
            Layer3D(name="copper_spreader_floor", z_min_mm=0.0, z_max_mm=3.5, role="base", material="Copper C110"),
            Layer3D(name="manifold_microchannel_core", z_min_mm=3.5, z_max_mm=6.0, role="channel", material="Water"),
            Layer3D(name="integrated_pin_fin_zone", z_min_mm=3.5, z_max_mm=5.5, role="enhanced_surface", material="Copper C110"),
            Layer3D(name="structural_cover", z_min_mm=6.0, z_max_mm=10.0, role="cover", material="Copper/Aluminum cover"),
        ],
        ports=[
            Port3D(name="inlet", center_xyz_mm=(10.0, 60.0, 10.0), diameter_mm=12.0, direction="+z", role="inlet"),
            Port3D(name="outlet", center_xyz_mm=(170.0, 60.0, 10.0), diameter_mm=12.0, direction="+z", role="outlet"),
        ],
        embedded_regions=[
            EmbeddedRegion(name="accelerator_embedded_zone", footprint_center_xy_mm=(90.0, 60.0), footprint_size_mm=(80.0, 80.0), channel_roof_thickness_mm=1.2, channel_floor_thickness_mm=3.5, insert_material="Copper C110", target_heat_flux_w_cm2=30.6)
        ],
        recommended_cfd_model="3D conjugate heat transfer with manifold-resolved flow distribution",
        notes="Hybrid 1500 W concept: embedded high-conductivity spreading + manifold microchannels + local fins.",
    )
