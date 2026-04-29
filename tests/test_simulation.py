from coldcircuit import ColdPlate, Material, Fluid, InletOutlet, SerpentineChannel, ParallelMicrochannelBank, HeatSource


def test_serpentine_simulates():
    plate = ColdPlate(
        name="test",
        base_size_mm=(100, 80),
        thickness_mm=8,
        material=Material.aluminum_6061(),
        fluid=Fluid.water(),
        inlet_outlet=InletOutlet(inlet_xy_mm=(8, 8), outlet_xy_mm=(92, 72), port_diameter_mm=6, flow_rate_lpm=1.5, max_pressure_drop_bar=0.5),
        channels=[SerpentineChannel(width_mm=2, depth_mm=1.5, pass_count=8, pitch_mm=6, margin_mm=8)],
        heat_sources=[HeatSource(name="chip", center_xy_mm=(50, 40), size_mm=(25, 25), power_w=250, max_temperature_c=80)],
    )
    result = plate.simulate_1d()
    assert result.total_power_w == 250
    assert result.reynolds_number > 0
    assert result.pressure_drop_bar >= 0


def test_parallel_microchannel_simulates():
    plate = ColdPlate(
        name="parallel",
        base_size_mm=(120, 80),
        thickness_mm=6,
        material=Material.copper_c110(),
        fluid=Fluid.water(),
        inlet_outlet=InletOutlet(inlet_xy_mm=(5, 40), outlet_xy_mm=(115, 40), port_diameter_mm=8, flow_rate_lpm=2.0, max_pressure_drop_bar=1.0),
        channels=[ParallelMicrochannelBank(width_mm=0.8, depth_mm=1.0, channel_count=20, length_mm=90, pitch_mm=1.5)],
        heat_sources=[HeatSource(name="gpu", center_xy_mm=(60, 40), size_mm=(40, 40), power_w=400, max_temperature_c=90)],
        manufacturing_process="additive_manufactured",
    )
    result = plate.simulate_1d()
    assert result.total_power_w == 400
    assert result.channel_velocity_m_s > 0
