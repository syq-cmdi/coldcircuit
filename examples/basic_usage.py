from coldcircuit import ColdPlate, Material, Fluid, InletOutlet, SerpentineChannel, HeatSource

plate = ColdPlate(
    name="basic_python_demo",
    base_size_mm=(100, 80),
    thickness_mm=8,
    material=Material.aluminum_6061(),
    fluid=Fluid.water(),
    inlet_outlet=InletOutlet(inlet_xy_mm=(8, 8), outlet_xy_mm=(92, 72), port_diameter_mm=6, flow_rate_lpm=1.5, max_pressure_drop_bar=0.5),
    channels=[SerpentineChannel(width_mm=2, depth_mm=1.5, pass_count=8, pitch_mm=6, margin_mm=8)],
    heat_sources=[HeatSource(name="250W chip", center_xy_mm=(50, 40), size_mm=(25, 25), power_w=250, max_temperature_c=55)],
    manufacturing_process="cnc_brazed",
)

print(plate.simulate_1d(coolant_inlet_c=25).model_dump_json(indent=2))
print("\nManufacturability notes:")
for note in plate.manufacturability_notes():
    print("-", note)
