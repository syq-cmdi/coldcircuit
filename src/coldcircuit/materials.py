from pydantic import BaseModel, Field


class Material(BaseModel):
    """Solid cold-plate material."""

    name: str
    conductivity_w_mk: float = Field(..., gt=0, description="Thermal conductivity, W/m-K")
    density_kg_m3: float | None = Field(None, gt=0)
    specific_heat_j_kgk: float | None = Field(None, gt=0)
    yield_strength_mpa: float | None = Field(None, gt=0)
    notes: str | None = None

    @classmethod
    def aluminum_6061(cls) -> "Material":
        return cls(
            name="Aluminum 6061-T6",
            conductivity_w_mk=167.0,
            density_kg_m3=2700,
            specific_heat_j_kgk=896,
            yield_strength_mpa=276,
            notes="Good lightweight baseline for vehicle cold plates; conductivity lower than copper.",
        )

    @classmethod
    def aluminum_3003(cls) -> "Material":
        return cls(
            name="Aluminum 3003",
            conductivity_w_mk=193.0,
            density_kg_m3=2730,
            specific_heat_j_kgk=893,
            yield_strength_mpa=145,
            notes="Common for brazed heat exchangers; mechanical strength lower than 6061.",
        )

    @classmethod
    def copper_c110(cls) -> "Material":
        return cls(
            name="Copper C110",
            conductivity_w_mk=385.0,
            density_kg_m3=8960,
            specific_heat_j_kgk=385,
            yield_strength_mpa=210,
            notes="Excellent conductivity; heavier, costlier, and more complex for vehicle systems.",
        )


class Fluid(BaseModel):
    """Coolant properties at approximate operating temperature."""

    name: str
    density_kg_m3: float = Field(..., gt=0)
    viscosity_pa_s: float = Field(..., gt=0)
    conductivity_w_mk: float = Field(..., gt=0)
    specific_heat_j_kgk: float = Field(..., gt=0)
    freezing_point_c: float | None = None
    notes: str | None = None

    @classmethod
    def water(cls) -> "Fluid":
        return cls(
            name="Water",
            density_kg_m3=997,
            viscosity_pa_s=0.00089,
            conductivity_w_mk=0.6,
            specific_heat_j_kgk=4182,
            freezing_point_c=0.0,
        )

    @classmethod
    def egw_50_50(cls) -> "Fluid":
        return cls(
            name="50/50 Ethylene Glycol-Water",
            density_kg_m3=1070,
            viscosity_pa_s=0.0034,
            conductivity_w_mk=0.37,
            specific_heat_j_kgk=3300,
            freezing_point_c=-37.0,
            notes="Vehicle-relevant coolant; higher viscosity and lower conductivity than water.",
        )
