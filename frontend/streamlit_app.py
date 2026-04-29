from pathlib import Path
import json
import sys
from copy import deepcopy

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from coldcircuit.io import load_plate_json  # noqa: E402
from coldcircuit.design_rules import all_rules_grouped  # noqa: E402
from coldcircuit.optimization import optimize_grid  # noqa: E402
from coldcircuit.tdp1500 import make_tdp1500_reference_design, make_tdp1500_3d_stack, tdp1500_guidance  # noqa: E402
from coldcircuit.plate import ColdPlate  # noqa: E402

st.set_page_config(page_title="ColdCircuit", page_icon="❄️", layout="wide")

st.markdown(
    """
    <style>
    .stApp {background: linear-gradient(180deg, #f6faff 0%, #ffffff 42%);} 
    section[data-testid="stSidebar"] {background: #f7fbff; border-right: 1px solid #e5eefb;}
    .hero {padding: 1.4rem 1.6rem; border-radius: 1.35rem; background: linear-gradient(135deg, #0f3b73 0%, #0e8bd1 52%, #65d6ff 100%); color: white; box-shadow: 0 14px 36px rgba(15, 70, 140, 0.22);} 
    .hero-title {font-size: 2.8rem; font-weight: 850; letter-spacing: -0.045em; line-height: 1.05;}
    .hero-subtitle {font-size: 1.05rem; opacity: 0.92; margin-top: .6rem; max-width: 980px;}
    .metric-card {padding: 1.05rem; border-radius: 1rem; background: rgba(255,255,255,0.92); box-shadow: 0 8px 28px rgba(20,60,120,0.08); border: 1px solid #e7f0fc;}
    .metric-label {font-size: .82rem; color: #62728a; font-weight: 700; text-transform: uppercase; letter-spacing: .04em;}
    .metric-value {font-size: 1.65rem; font-weight: 820; color: #12263f; margin-top: .15rem;}
    .family-card {padding: 1rem; border-radius: 1rem; background: linear-gradient(135deg, #ffffff 0%, #f2f7ff 100%); border: 1px solid #dce9ff; min-height: 126px; box-shadow: 0 6px 20px rgba(15,70,140,.06);} 
    .pill {display:inline-block; padding:.22rem .55rem; border-radius:999px; background:#eaf5ff; color:#0f5d99; font-size:.78rem; font-weight:700; margin-right:.35rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def apply_interactive_overrides(plate: ColdPlate, flow_lpm: float, width_mm: float, depth_mm: float, pitch_mm: float | None) -> ColdPlate:
    p = deepcopy(plate)
    p.inlet_outlet.flow_rate_lpm = flow_lpm
    ch = p.channels[0]
    ch.width_mm = width_mm
    ch.depth_mm = depth_mm
    if pitch_mm is not None and hasattr(ch, "pitch_mm"):
        ch.pitch_mm = max(pitch_mm, width_mm + 0.05)
    return ColdPlate.model_validate(p.model_dump())


def build_3d_figure(plate: ColdPlate, stack):
    fig = go.Figure()
    x_len, y_len = plate.base_size_mm
    if stack:
        for layer in stack.layers:
            fig.add_trace(go.Mesh3d(
                x=[0, x_len, x_len, 0, 0, x_len, x_len, 0],
                y=[0, 0, y_len, y_len, 0, 0, y_len, y_len],
                z=[layer.z_min_mm] * 4 + [layer.z_max_mm] * 4,
                i=[0, 0, 0, 4, 4, 4, 0, 1, 2, 3, 0, 1],
                j=[1, 2, 3, 5, 6, 7, 1, 2, 3, 0, 4, 5],
                k=[2, 3, 0, 6, 7, 4, 5, 6, 7, 4, 5, 6],
                opacity=0.36,
                name=f"{layer.name} · {layer.role}",
                hovertext=f"{layer.name}<br>{layer.role}<br>{layer.thickness_mm:.2f} mm",
                showscale=False,
            ))
        for region in stack.embedded_regions:
            cx, cy = region.footprint_center_xy_mm
            sx, sy = region.footprint_size_mm
            fig.add_trace(go.Scatter3d(
                x=[cx - sx / 2, cx + sx / 2, cx + sx / 2, cx - sx / 2, cx - sx / 2],
                y=[cy - sy / 2, cy - sy / 2, cy + sy / 2, cy + sy / 2, cy - sy / 2],
                z=[plate.thickness_mm + .12] * 5,
                mode="lines",
                line=dict(width=6),
                name=region.name,
            ))
        for port in stack.ports:
            fig.add_trace(go.Scatter3d(x=[port.center_xyz_mm[0]], y=[port.center_xyz_mm[1]], z=[port.center_xyz_mm[2]], mode="markers+text", marker=dict(size=7), text=[port.name], name=port.name))
    else:
        fig.add_trace(go.Mesh3d(
            x=[0, x_len, x_len, 0, 0, x_len, x_len, 0],
            y=[0, 0, y_len, y_len, 0, 0, y_len, y_len],
            z=[0] * 4 + [plate.thickness_mm] * 4,
            opacity=0.28,
            name="plate envelope",
            showscale=False,
        ))
        fig.add_trace(go.Scatter3d(x=[plate.inlet_outlet.inlet_xy_mm[0], plate.inlet_outlet.outlet_xy_mm[0]], y=[plate.inlet_outlet.inlet_xy_mm[1], plate.inlet_outlet.outlet_xy_mm[1]], z=[plate.thickness_mm, plate.thickness_mm], mode="markers+text", marker=dict(size=7), text=["inlet", "outlet"], name="ports"))
    for src in plate.heat_sources:
        sx, sy = src.center_xy_mm
        wx, wy = src.size_mm
        z = plate.thickness_mm + 0.35
        fig.add_trace(go.Scatter3d(
            x=[sx - wx/2, sx + wx/2, sx + wx/2, sx - wx/2, sx - wx/2],
            y=[sy - wy/2, sy - wy/2, sy + wy/2, sy + wy/2, sy - wy/2],
            z=[z]*5,
            mode="lines+markers+text",
            text=[src.name, "", "", "", ""],
            line=dict(width=5),
            name=src.name,
        ))
    fig.update_layout(height=620, scene=dict(xaxis_title="X mm", yaxis_title="Y mm", zaxis_title="Z mm", aspectmode="data"), margin=dict(l=0, r=0, b=0, t=20), legend=dict(orientation="h"))
    return fig


def build_streamline_figure(plate: ColdPlate):
    x_len, y_len = plate.base_size_mm
    inlet = plate.inlet_outlet.inlet_xy_mm
    outlet = plate.inlet_outlet.outlet_xy_mm
    fig = go.Figure()
    fig.add_shape(type="rect", x0=0, y0=0, x1=x_len, y1=y_len, line=dict(width=2), fillcolor="rgba(230,242,255,0.35)")
    ch = plate.primary_channel()
    n = getattr(ch, "channel_count", 12)
    n = max(6, min(int(n), 40))
    for idx in range(n):
        y = y_len * (idx + 1) / (n + 1)
        curvature = 0.08 * y_len * ((idx % 3) - 1)
        fig.add_trace(go.Scatter(
            x=[inlet[0], x_len * .25, x_len * .50, x_len * .75, outlet[0]],
            y=[inlet[1], y + curvature, y, y - curvature, outlet[1]],
            mode="lines",
            line=dict(width=1.8 + 2.2 * (idx / n)),
            opacity=0.72,
            name=f"streamline {idx+1}",
            showlegend=False,
        ))
    for src in plate.heat_sources:
        cx, cy = src.center_xy_mm
        sx, sy = src.size_mm
        fig.add_shape(type="rect", x0=cx-sx/2, y0=cy-sy/2, x1=cx+sx/2, y1=cy+sy/2, line=dict(width=2), fillcolor="rgba(255,90,60,0.25)")
        fig.add_annotation(x=cx, y=cy, text=src.name, showarrow=False)
    fig.add_trace(go.Scatter(x=[inlet[0], outlet[0]], y=[inlet[1], outlet[1]], mode="markers+text", marker=dict(size=14), text=["IN", "OUT"], textposition="top center", name="ports"))
    fig.update_layout(height=520, xaxis_title="X mm", yaxis_title="Y mm", margin=dict(l=10, r=10, b=10, t=20), yaxis_scaleanchor="x")
    return fig


def build_temperature_map(plate: ColdPlate, result):
    x_len, y_len = plate.base_size_mm
    xs = [i * x_len / 44 for i in range(45)]
    ys = [i * y_len / 30 for i in range(31)]
    z = []
    base = result.coolant_inlet_c + result.coolant_delta_t_k / 2
    for y in ys:
        row = []
        for x in xs:
            temp = base
            for src in plate.heat_sources:
                cx, cy = src.center_xy_mm
                dx = (x - cx) / max(src.size_mm[0], 1)
                dy = (y - cy) / max(src.size_mm[1], 1)
                temp += (result.estimated_max_source_temperature_c - base) * pow(2.71828, -(dx*dx + dy*dy) * 2.2)
            row.append(temp)
        z.append(row)
    fig = go.Figure(go.Heatmap(x=xs, y=ys, z=z, colorbar=dict(title="°C")))
    fig.update_layout(height=520, xaxis_title="X mm", yaxis_title="Y mm", margin=dict(l=10, r=10, b=10, t=20), yaxis_scaleanchor="x")
    return fig


st.markdown('<div class="hero"><div class="hero-title">❄️ ColdCircuit Studio</div><div class="hero-subtitle">Interactive 3D liquid cold plate design: 1500W TDP screening, embedded cooling rules, grouped architecture guidance, optimization candidates, and visual fluid-flow interpretation.</div></div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

with st.sidebar:
    st.header("Design Source")
    mode = st.radio("Select design", ["1500W reference", "Example JSON", "Upload JSON"], index=0)
    coolant_inlet_c = st.slider("Coolant inlet temperature (°C)", 10.0, 50.0, 25.0, 1.0)

if mode == "1500W reference":
    base_plate = make_tdp1500_reference_design()
    stack = make_tdp1500_3d_stack()
elif mode == "Example JSON":
    example = st.sidebar.selectbox("Example", ["examples/tdp1500_hybrid_reference.json", "examples/serpentine_250w.json", "examples/gan_vehicle_coldplate.json"])
    base_plate = load_plate_json(ROOT / example)
    stack = make_tdp1500_3d_stack() if "tdp1500" in example else None
else:
    uploaded = st.sidebar.file_uploader("Upload ColdCircuit JSON", type=["json"])
    if uploaded is None:
        st.info("Upload a ColdCircuit JSON file to begin.")
        st.stop()
    data = json.loads(uploaded.read().decode("utf-8"))
    base_plate = ColdPlate.model_validate(data)
    stack = None

ch0 = base_plate.primary_channel()
with st.sidebar:
    st.header("Interactive Parameters")
    flow_lpm = st.slider("Flow rate (L/min)", 0.5, 18.0, float(base_plate.inlet_outlet.flow_rate_lpm), 0.1)
    width_mm = st.slider("Channel width (mm)", 0.4, 4.0, float(ch0.width_mm), 0.05)
    depth_mm = st.slider("Channel depth (mm)", 0.4, min(6.0, float(base_plate.thickness_mm) - 0.3), float(ch0.depth_mm), 0.05)
    pitch_mm = None
    if hasattr(ch0, "pitch_mm"):
        pitch_mm = st.slider("Channel pitch (mm)", 0.8, 8.0, float(ch0.pitch_mm), 0.05)

plate = apply_interactive_overrides(base_plate, flow_lpm, width_mm, depth_mm, pitch_mm)
result = plate.simulate_1d(coolant_inlet_c=coolant_inlet_c)
checks = plate.manufacturability_checks()

top = st.columns(5)
metrics = [("TDP", f"{result.total_power_w:.0f} W"), ("Max temp", f"{result.estimated_max_source_temperature_c:.1f} °C"), ("Pressure drop", f"{result.pressure_drop_bar:.3f} bar"), ("Coolant ΔT", f"{result.coolant_delta_t_k:.1f} K"), ("Regime", result.flow_regime)]
for col, (label, value) in zip(top, metrics):
    col.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
tabs = st.tabs(["Design Studio", "Flow & Thermal Map", "Optimization", "Rules", "Data"])

with tabs[0]:
    left, right = st.columns([1.35, .85])
    with left:
        st.subheader("Interactive 3D Structure")
        st.plotly_chart(build_3d_figure(plate, stack), use_container_width=True)
    with right:
        st.subheader("Manufacturability")
        if checks:
            st.dataframe(pd.DataFrame([c.model_dump() for c in checks]), use_container_width=True, hide_index=True)
        else:
            st.success("No rule-based issue detected.")
        st.subheader("1500W Guidance")
        g = tdp1500_guidance()
        st.markdown(g.architecture_summary)
        st.markdown("".join([f'<span class="pill">{x}</span>' for x in g.recommended_families]), unsafe_allow_html=True)

with tabs[1]:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Conceptual Fluid Streamlines")
        st.plotly_chart(build_streamline_figure(plate), use_container_width=True)
    with c2:
        st.subheader("Estimated Surface Temperature Map")
        st.plotly_chart(build_temperature_map(plate, result), use_container_width=True)

with tabs[2]:
    st.subheader("Fast Grid Optimization")
    variable_grid = {"channel.width_mm": [0.8, 1.0, 1.2, 1.5, 2.0], "channel.depth_mm": [1.0, 1.5, 2.0, 2.5, 3.0], "inlet_outlet.flow_rate_lpm": [3.0, 5.0, 8.0, 10.0, 12.0]}
    if hasattr(plate.primary_channel(), "pitch_mm"):
        variable_grid["channel.pitch_mm"] = [1.5, 2.0, 2.5, 3.0, 4.0]
    if st.button("Run optimization preview", type="primary"):
        opt = optimize_grid(base_plate, variable_grid, coolant_inlet_c=coolant_inlet_c, top_k=15)
        st.session_state["opt"] = opt
    opt = st.session_state.get("opt")
    if opt:
        st.metric("Feasible candidates", opt.feasible_count)
        df = pd.DataFrame([c.model_dump() for c in opt.candidates])
        st.dataframe(df, use_container_width=True, hide_index=True)
        if opt.best:
            st.success(f"Best candidate: T={opt.best.max_temperature_c:.1f} °C, ΔP={opt.best.pressure_drop_bar:.3f} bar, variables={opt.best.variables}")
    else:
        st.info("Click the button to evaluate a bounded grid of geometry and flow-rate options.")

with tabs[3]:
    st.subheader("Grouped Structure Rules")
    rules = all_rules_grouped()
    cols = st.columns(3)
    for idx, (family, items) in enumerate(rules.items()):
        with cols[idx % 3]:
            st.markdown(f'<div class="family-card"><h4>{family}</h4><p>{len(items)} rules · grouped architecture guidance</p></div>', unsafe_allow_html=True)
            with st.expander(f"Rules: {family}"):
                for r in items:
                    st.markdown(f"- **{r['severity']} / {r['item']}**: {r['rule']}  ")

with tabs[4]:
    st.subheader("Design JSON")
    st.json(plate.model_dump())
    st.subheader("Simulation JSON")
    st.json(result.model_dump())
    st.subheader("Heat Sources")
    st.dataframe(pd.DataFrame([s.model_dump() | {"heat_flux_w_cm2": s.heat_flux_w_cm2} for s in plate.heat_sources]), use_container_width=True, hide_index=True)
