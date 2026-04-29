from pydantic import BaseModel, Field

from .structures import StructureFamily


class DesignRule(BaseModel):
    family: StructureFamily
    item: str
    severity: str = Field(..., description="info, warning, hard_constraint")
    rule: str
    rationale: str


STRUCTURE_RULES: dict[StructureFamily, list[DesignRule]] = {
    StructureFamily.SERPENTINE: [
        DesignRule(family=StructureFamily.SERPENTINE, item="pressure_drop", severity="warning", rule="Use serpentine channels for moderate TDP or compact prototypes; avoid very long single-path routing for 1500 W unless pump head is available.", rationale="Single-path routing improves coverage but accumulates major and bend losses."),
        DesignRule(family=StructureFamily.SERPENTINE, item="temperature_gradient", severity="warning", rule="Place inlet near the highest heat-flux zone or split into multiple parallel serpentine zones.", rationale="Coolant warms along the path, causing downstream temperature non-uniformity."),
    ],
    StructureFamily.PARALLEL_MICROCHANNEL: [
        DesignRule(family=StructureFamily.PARALLEL_MICROCHANNEL, item="flow_balance", severity="hard_constraint", rule="Use inlet/outlet manifolds sized for uniform distribution; check maldistribution by CFD for high TDP.", rationale="Parallel channels reduce pressure drop but introduce flow distribution risk."),
        DesignRule(family=StructureFamily.PARALLEL_MICROCHANNEL, item="clogging", severity="warning", rule="Avoid overly narrow channels for vehicle coolant; include filtration and fouling margin.", rationale="Microchannels are sensitive to particulates and coolant degradation."),
    ],
    StructureFamily.MANIFOLD_MICROCHANNEL: [
        DesignRule(family=StructureFamily.MANIFOLD_MICROCHANNEL, item="1500w_preferred", severity="info", rule="For 1000-1500 W class cold plates, prefer manifold microchannels or hybrid impingement-microchannel structures.", rationale="They combine short flow paths, high area density, and better temperature uniformity."),
        DesignRule(family=StructureFamily.MANIFOLD_MICROCHANNEL, item="manifold_ratio", severity="warning", rule="Manifold hydraulic area should be sufficiently larger than aggregate channel area to reduce maldistribution.", rationale="Small manifolds cause inlet starving and local hot spots."),
    ],
    StructureFamily.PIN_FIN: [
        DesignRule(family=StructureFamily.PIN_FIN, item="local_hotspot", severity="info", rule="Use pin fins below local high heat flux regions or in jet impingement zones.", rationale="Pin fins improve mixing and area density but may raise pressure drop."),
        DesignRule(family=StructureFamily.PIN_FIN, item="manufacturing", severity="warning", rule="Validate fin height, pitch, and minimum feature size against machining/additive constraints.", rationale="Tall slender fins are vulnerable to deformation and clogging."),
    ],
    StructureFamily.IMPINGEMENT: [
        DesignRule(family=StructureFamily.IMPINGEMENT, item="hotspot", severity="info", rule="Use jet impingement for concentrated chiplets or GaN devices with high heat flux.", rationale="Direct normal momentum enhances local convection."),
        DesignRule(family=StructureFamily.IMPINGEMENT, item="uniformity", severity="warning", rule="Use an array of jets or a hybrid return channel to avoid narrow cooling spots.", rationale="Single jets may produce strong local gradients."),
    ],
    StructureFamily.EMBEDDED: [
        DesignRule(family=StructureFamily.EMBEDDED, item="roof_thickness", severity="hard_constraint", rule="Keep channel roof thickness typically >= 1.0-1.5 mm for brazed/machined plates unless validated by structural analysis.", rationale="Embedded channels close to the chip reduce conduction resistance but can weaken the pressure boundary."),
        DesignRule(family=StructureFamily.EMBEDDED, item="chip_alignment", severity="hard_constraint", rule="Align embedded cooling region footprint with chip/package hotspots and include tolerance margin.", rationale="Misalignment negates the benefit of embedded cooling and can create thermal runaway zones."),
        DesignRule(family=StructureFamily.EMBEDDED, item="copper_insert", severity="info", rule="Use copper inserts selectively under 1500 W class high heat flux zones while keeping aluminum body for mass reduction.", rationale="Hybrid materials improve spreading but require galvanic and joining validation."),
    ],
    StructureFamily.HYBRID: [
        DesignRule(family=StructureFamily.HYBRID, item="architecture", severity="info", rule="For 1500 W TDP, combine embedded copper spreading, manifold microchannels, local pin fins, and short parallel paths.", rationale="Single mechanisms rarely satisfy temperature, uniformity, pressure drop, and manufacturability simultaneously."),
    ],
}


def rules_for_family(family: StructureFamily) -> list[DesignRule]:
    return STRUCTURE_RULES.get(family, [])


def all_rules_grouped() -> dict[str, list[dict]]:
    return {family.value: [r.model_dump() for r in rules] for family, rules in STRUCTURE_RULES.items()}
