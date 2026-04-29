from pathlib import Path
import json
import sys

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from coldcircuit.io import load_plate_json  # noqa: E402
from coldcircuit.design_rules import all_rules_grouped  # noqa: E402
from coldcircuit.tdp1500 import make_tdp1500_reference_design, make_tdp1500_3d_stack, tdp1500_guidance  # noqa: E402

st.set_page_config(page_title="ColdCircuit", page_icon="❄️", layout="wide")

st.markdown(
    """
    <style>
    .main {background: linear-gradient(180deg, #f8fbff 0%, #ffffff 35%);} 
    .metric-card {padding: 1.1rem; border-radius: 1rem; background: white; box-shadow: 0 6px 24px rgba(20,60,120,0.08); border: 1px solid #eaf1fb;}
    .family-card {padding: 1rem; border-radius: 1rem; background: linear-gradient(135deg, #ffffff 0%, #f2f7ff 100%); border: 1px solid #dce9ff; min-height: 135px;}
    .title {font-size: 2.6rem; font-weight: 800; letter-spacing: -0.04em;}
    .subtitle {font-size: 1.05rem; color: #53657d;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="title">❄️ ColdCircuit</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">LLM-friendly 3D liquid cold plate design, embedded cooling rules, 1500W TDP screening, and grouped structure visualization.</div>', unsafe_allow_html=True)
st.divider()

with st.sidebar:
    st.header("Design Source")
    mode = st.radio("Select design", ["1500W reference", "Example JSON", "Upload JSON"], index=0)
    coolant_inlet_c = st.slider("Coolant inlet temperature (°C)", 10.0, 45.0, 25.0, 1.0)

if mode == "1500W reference":
    plate = make_tdp1500_reference_design()
    stack = make_tdp1500_3d_stack()
elif mode == "Example JSON":
    example = st.sidebar.selectbox("Example", ["examples/serpentine_250w.json", "examples/gan_vehicle_coldplate.json"])
    plate = load_plate_json(ROOT / example)
    stack = None
else:
    uploaded = st.sidebar.file_uploader("Upload ColdCircuit JSON", type=["json"])
    if uploaded is None:
        st.info("Upload a ColdCircuit JSON file to begin.")
        st.stop()
    data = json.loads(uploaded.read().decode("utf-8"))
    from coldcircuit.plate import ColdPlate
    plate = ColdPlate.model_validate(data)
    stack = None

result = plate.simulate_1d(coolant_inlet_c=coolant_inlet_c)
checks = plate.manufacturability_checks()

top = st.columns(5)
metrics = [
    ("TDP", f"{result.total_power_w:.0f} W"),
    ("Max source temp", f"{result.estimated_max_source_temperature_c:.1f} °C"),
    ("Pressure drop", f"{result.pressure_drop_bar:.3f} bar"),
    ("Coolant ΔT", f"{result.coolant_delta_t_k:.1f} K"),
    ("Flow regime", result.flow_regime),
]
for col, (label, value) in zip(top, metrics):
    col.markdown(f'<div class="metric-card"><b>{label}</b><br><span style="font-size:1.55rem;font-weight:750;">{value}</span></div>', unsafe_allow_html=True)

st.divider()

left, right = st.columns([1.25, 1.0])

with left:
    st.subheader("3D Cold Plate Structure")
    fig = go.Figure()
    if stack:
        for i, layer in enumerate(stack.layers):
            fig.add_trace(go.Mesh3d(
                x=[0, plate.base_size_mm[0], plate.base_size_mm[0], 0, 0, plate.base_size_mm[0], plate.base_size_mm[0], 0],
                y=[0, 0, plate.base_size_mm[1], plate.base_size_mm[1], 0, 0, plate.base_size_mm[1], plate.base_size_mm[1]],
                z=[layer.z_min_mm]*4 + [layer.z_max_mm]*4,
                i=[0, 0, 0, 4, 4, 4, 0, 1, 2, 3, 0, 1],
                j=[1, 2, 3, 5, 6, 7, 1, 2, 3, 0, 4, 5],
                k=[2, 3, 0, 6, 7, 4, 5, 6, 7, 4, 5, 6],
                opacity=0.34,
                name=f"{layer.name} ({layer.role})",
                hovertext=f"{layer.name}<br>{layer.role}<br>{layer.thickness_mm:.2f} mm",
                showscale=False,
            ))
        for port in stack.ports:
            fig.add_trace(go.Scatter3d(x=[port.center_xyz_mm[0]], y=[port.center_xyz_mm[1]], z=[port.center_xyz_mm[2]], mode="markers+text", marker=dict(size=6), text=[port.name], name=port.name))
    else:
        ch = plate.primary_channel()
        fig.add_trace(go.Mesh3d(
            x=[0, plate.base_size_mm[0], plate.base_size_mm[0], 0, 0, plate.base_size_mm[0], plate.base_size_mm[0], 0],
            y=[0, 0, plate.base_size_mm[1], plate.base_size_mm[1], 0, 0, plate.base_size_mm[1], plate.base_size_mm[1]],
            z=[0]*4 + [plate.thickness_mm]*4,
            opacity=0.28,
            name="plate envelope",
            showscale=False,
        ))
        fig.add_trace(go.Scatter3d(x=[plate.inlet_outlet.inlet_xy_mm[0], plate.inlet_outlet.outlet_xy_mm[0]], y=[plate.inlet_outlet.inlet_xy_mm[1], plate.inlet_outlet.outlet_xy_mm[1]], z=[plate.thickness_mm, plate.thickness_mm], mode="markers+text", marker=dict(size=6), text=["inlet", "outlet"], name="ports"))
    for src in plate.heat_sources:
        sx, sy = src.center_xy_mm
        wx, wy = src.size_mm
        z = plate.thickness_mm + 0.3
        fig.add_trace(go.Scatter3d(x=[sx], y=[sy], z=[z], mode="markers+text", marker=dict(size=8), text=[src.name], name=src.name))
    fig.update_layout(height=560, scene=dict(xaxis_title="X mm", yaxis_title="Y mm", zaxis_title="Z mm", aspectmode="data"), margin=dict(l=0, r=0, b=0, t=20))
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Thermal-Hydraulic Result")
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=result.estimated_max_source_temperature_c,
        title={"text": "Estimated max source temperature (°C)"},
        gauge={"axis": {"range": [0, max(120, result.estimated_max_source_temperature_c * 1.2)]}, "threshold": {"line": {"width": 4}, "thickness": 0.75, "value": max([s.max_temperature_c or 0 for s in plate.heat_sources]) or 90}},
    ))
    gauge.update_layout(height=290, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(gauge, use_container_width=True)

    st.subheader("Manufacturability")
    if checks:
        st.dataframe(pd.DataFrame([c.model_dump() for c in checks]), use_container_width=True, hide_index=True)
    else:
        st.success("No rule-based manufacturability issue detected.")

st.divider()
st.subheader("Structure Families & Design Rules")
rules = all_rules_grouped()
cols = st.columns(3)
for idx, (family, items) in enumerate(rules.items()):
    with cols[idx % 3]:
        st.markdown(f'<div class="family-card"><h4>{family}</h4><p>{len(items)} rules · grouped cold-plate architecture guidance</p></div>', unsafe_allow_html=True)
        with st.expander(f"Rules: {family}"):
            for r in items:
                st.markdown(f"- **{r['severity']} / {r['item']}**: {r['rule']}  ")

st.divider()
st.subheader("1500W TDP Design Guidance")
g = tdp1500_guidance()
c1, c2 = st.columns([1, 1])
with c1:
    st.markdown(g.architecture_summary)
    st.write("Recommended families:", ", ".join(g.recommended_families))
with c2:
    st.write("Hard constraints")
    for h in g.hard_constraints:
        st.markdown(f"- {h}")

st.subheader("Heat Source Table")
st.dataframe(pd.DataFrame([s.model_dump() | {"heat_flux_w_cm2": s.heat_flux_w_cm2} for s in plate.heat_sources]), use_container_width=True, hide_index=True)
