from pathlib import Path
import sys
from copy import deepcopy

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from coldcircuit.io import load_plate_json
from coldcircuit.design_rules import all_rules_grouped
from coldcircuit.optimization import optimize_grid
from coldcircuit.tdp1500 import make_tdp1500_reference_design, make_tdp1500_3d_stack, tdp1500_guidance
from coldcircuit.plate import ColdPlate

st.set_page_config(page_title="ColdCircuit CAD Studio", page_icon="❄️", layout="wide", initial_sidebar_state="collapsed")

STRUCTURE_OPTIONS = ["serpentine", "parallel_microchannel", "manifold_microchannel", "pin_fin", "impingement", "embedded", "hybrid"]
OPTIMIZATION_OPTIONS = ["grid_search", "rule_based", "pareto_screening", "surrogate_preview"]
VIEW_CAMERAS = {
    "Iso": dict(eye=dict(x=1.55, y=1.45, z=0.95), center=dict(x=0, y=0, z=0), up=dict(x=0, y=0, z=1)),
    "Front": dict(eye=dict(x=0.0, y=-2.25, z=0.35), center=dict(x=0, y=0, z=0), up=dict(x=0, y=0, z=1)),
    "Back": dict(eye=dict(x=0.0, y=2.25, z=0.35), center=dict(x=0, y=0, z=0), up=dict(x=0, y=0, z=1)),
    "Left": dict(eye=dict(x=-2.25, y=0.0, z=0.35), center=dict(x=0, y=0, z=0), up=dict(x=0, y=0, z=1)),
    "Right": dict(eye=dict(x=2.25, y=0.0, z=0.35), center=dict(x=0, y=0, z=0), up=dict(x=0, y=0, z=1)),
    "Top": dict(eye=dict(x=0.0, y=0.0, z=2.45), center=dict(x=0, y=0, z=0), up=dict(x=0, y=1, z=0)),
}

st.markdown(
    """
    <style>
    .stApp {background:#070b12;color:#e5edf8;}
    header[data-testid="stHeader"] {background:rgba(7,11,18,.92); border-bottom:1px solid #1f2937;}
    section[data-testid="stSidebar"] {display:none;}
    .block-container {padding:0.55rem 0.75rem 0.75rem 0.75rem; max-width:100%;}
    div[data-testid="stVerticalBlock"] {gap:0.48rem;}
    .topbar {min-height:42px; display:flex; align-items:center; justify-content:space-between; gap:14px; padding:0 14px; background:#0b1220; border:1px solid #1f2937; border-radius:12px; box-shadow:0 10px 24px rgba(0,0,0,.18);}
    .brand {font-weight:850; color:#eef6ff; letter-spacing:-.02em;}
    .top-left,.top-right{display:flex;align-items:center;gap:10px;}
    .filetab {font-size:12px; color:#9fb3c8; background:#111827; border:1px solid #263244; padding:5px 10px; border-radius:8px;}
    .toolbar-btn {font-size:12px;color:#cfe8ff;background:#10243a;border:1px solid #1f4e79;padding:5px 9px;border-radius:8px;}
    .status-pass {font-size:12px;color:#bbf7d0;background:#052e1b;border:1px solid #166534;padding:5px 10px;border-radius:999px;font-weight:800;}
    .status-warn {font-size:12px;color:#fde68a;background:#422006;border:1px solid #b45309;padding:5px 10px;border-radius:999px;font-weight:800;}
    .panel {background:#0b1220; border:1px solid #1f2937; border-radius:14px; box-shadow:0 16px 30px rgba(0,0,0,.18); overflow:hidden;}
    .panel-title {display:flex; align-items:center; justify-content:space-between; padding:10px 12px; background:#0f172a; border-bottom:1px solid #1f2937; color:#dbeafe; font-weight:800; font-size:13px;}
    .panel-body {padding:12px;}
    .mission {background:linear-gradient(135deg,#08111f 0%,#10243a 55%,#0e7490 120%);border:1px solid #1f4e79;border-radius:12px;padding:12px;margin-bottom:10px;}
    .mission h3 {margin:0 0 6px 0;font-size:18px;color:#f8fbff;}
    .mission p {margin:0;color:#aac0d9;font-size:12px;line-height:1.45;}
    .code-window {background:#050914; border:1px solid #1f2937; border-radius:10px; padding:10px; font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace; font-size:12px; line-height:1.52; color:#d6e6ff; white-space:pre-wrap; min-height:184px;}
    .metric-card {background:#0f172a; border:1px solid #263244; border-radius:12px; padding:8px 10px;}
    .metric-label {font-size:10px; color:#8ca3bd; text-transform:uppercase; font-weight:800; letter-spacing:.04em;}
    .metric-value {font-size:18px; color:#f8fbff; font-weight:850; margin-top:2px;}
    .target-card {background:#0a1322;border:1px solid #263244;border-radius:12px;padding:10px;min-height:78px;}
    .target-card b {color:#f8fbff;font-size:13px;}
    .target-card span {display:block;color:#90a4bc;font-size:12px;margin-top:5px;line-height:1.35;}
    .note {font-size:12px;color:#9fb3c8;line-height:1.52;}
    .pill {display:inline-block; margin:2px 4px 2px 0; padding:4px 8px; border-radius:999px; background:#10243a; color:#7dd3fc; border:1px solid #1f4e79; font-size:11px; font-weight:700;}
    .orange-pill {display:inline-block; margin:2px 4px 2px 0; padding:4px 8px; border-radius:999px; background:#2b1608; color:#fdba74; border:1px solid #9a3412; font-size:11px; font-weight:700;}
    .stButton>button {background:#0b72c9; color:#fff; border:1px solid #38bdf8; border-radius:8px; font-weight:800; height:34px;}
    .stSelectbox label,.stSlider label,.stRadio label,.stCheckbox label {color:#c7d8ee!important; font-size:12px!important; font-weight:700!important;}
    .stDataFrame {border:1px solid #1f2937; border-radius:10px; overflow:hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)


def get_base_plate(structure_family: str) -> tuple[ColdPlate, object | None]:
    if structure_family in {"hybrid", "embedded", "manifold_microchannel", "pin_fin", "impingement", "parallel_microchannel"}:
        plate = make_tdp1500_reference_design()
        plate.name = f"{structure_family}_tdp1500_reference"
        return plate, make_tdp1500_3d_stack() if structure_family in {"hybrid", "embedded", "manifold_microchannel"} else None
    return load_plate_json(ROOT / "examples/serpentine_250w.json"), None


def apply_overrides(plate: ColdPlate, flow_lpm: float, width_mm: float, depth_mm: float, pitch_mm: float | None, heat_scale: float) -> ColdPlate:
    p = deepcopy(plate)
    p.inlet_outlet.flow_rate_lpm = flow_lpm
    ch = p.channels[0]
    ch.width_mm = width_mm
    ch.depth_mm = depth_mm
    if pitch_mm is not None and hasattr(ch, "pitch_mm"):
        ch.pitch_mm = max(pitch_mm, width_mm + 0.05)
    for src in p.heat_sources:
        src.power_w = src.power_w * heat_scale
    return ColdPlate.model_validate(p.model_dump())


def mesh_box(x0, x1, y0, y1, z0, z1):
    return dict(
        x=[x0, x1, x1, x0, x0, x1, x1, x0],
        y=[y0, y0, y1, y1, y0, y0, y1, y1],
        z=[z0, z0, z0, z0, z1, z1, z1, z1],
        i=[0, 0, 0, 4, 4, 4, 0, 1, 2, 3, 0, 1],
        j=[1, 2, 3, 5, 6, 7, 1, 2, 3, 0, 4, 5],
        k=[2, 3, 0, 6, 7, 4, 5, 6, 7, 4, 5, 6],
    )


def add_box(fig, name, x0, x1, y0, y1, z0, z1, color, opacity=0.55):
    fig.add_trace(go.Mesh3d(**mesh_box(x0, x1, y0, y1, z0, z1), name=name, color=color, opacity=opacity, flatshading=True, showscale=False, hovertemplate=f"{name}<extra></extra>"))


def build_cad_3d(plate: ColdPlate, view: str, show_streamlines: bool, show_heat: bool, show_exploded: bool):
    fig = go.Figure()
    x_len, y_len, th = plate.base_size_mm[0], plate.base_size_mm[1], plate.thickness_mm
    z_gap = 1.2 if show_exploded else 0.0
    add_box(fig, "base / cold plate body", 0, x_len, 0, y_len, 0, th * 0.32, "#56677f", 0.95)
    add_box(fig, "microchannel core", 7, x_len - 7, 8, y_len - 8, th * 0.32 + z_gap, th * 0.62 + z_gap, "#0f8bd1", 0.32)
    add_box(fig, "transparent cover", 0, x_len, 0, y_len, th * 0.62 + 2 * z_gap, th + 2 * z_gap, "#8ccfff", 0.24)
    ch = plate.primary_channel()
    n = min(max(int(getattr(ch, "channel_count", 14)), 6), 48)
    y_start, y_end = y_len * 0.18, y_len * 0.82
    for idx in range(n):
        y = y_start + (y_end - y_start) * idx / max(n - 1, 1)
        add_box(fig, "coolant microchannel" if idx == 0 else "", x_len * 0.18, x_len * 0.82, y - 0.23, y + 0.23, th * 0.40 + z_gap, th * 0.55 + z_gap, "#2bd4ff", 0.65)
    for src in plate.heat_sources:
        cx, cy = src.center_xy_mm
        sx, sy = src.size_mm
        if show_heat:
            add_box(fig, f"{src.name} heat source", cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, th + 2 * z_gap + 0.15, th + 2 * z_gap + 0.75, "#ff512f", 0.82)
            add_box(fig, "thermal influence zone", cx - sx * 0.78, cx + sx * 0.78, cy - sy * 0.78, cy + sy * 0.78, th + 2 * z_gap + 0.02, th + 2 * z_gap + 0.10, "#ffb347", 0.11)
    if show_streamlines:
        inlet_y = plate.inlet_outlet.inlet_xy_mm[1]
        outlet_y = plate.inlet_outlet.outlet_xy_mm[1]
        stream_count = min(14, n)
        for i in range(stream_count):
            y = y_start + (y_end - y_start) * i / max(stream_count - 1, 1)
            fig.add_trace(go.Scatter3d(
                x=[-x_len * 0.12, x_len * 0.06, x_len * 0.18, x_len * 0.50, x_len * 0.82, x_len * 0.94, x_len * 1.12],
                y=[inlet_y, inlet_y, y, y, y, outlet_y, outlet_y],
                z=[th * 0.52 + z_gap] * 7,
                mode="lines",
                line=dict(width=5 if i in {0, stream_count - 1} else 3, color="#29c7ff"),
                opacity=0.82,
                name="flow streamlines" if i == 0 else "",
                hovertemplate="coolant streamline<extra></extra>",
            ))
    fig.add_trace(go.Scatter3d(x=[-x_len * 0.12, x_len * 1.12], y=[plate.inlet_outlet.inlet_xy_mm[1], plate.inlet_outlet.outlet_xy_mm[1]], z=[th * 0.52 + z_gap, th * 0.52 + z_gap], mode="markers+text", marker=dict(size=8, color=["#22d3ee", "#10b981"]), text=["IN", "OUT"], textposition="top center", name="ports"))
    fig.update_layout(
        height=610,
        paper_bgcolor="#161b23",
        plot_bgcolor="#161b23",
        font=dict(color="#dbeafe"),
        margin=dict(l=0, r=0, t=8, b=0),
        scene=dict(
            bgcolor="#161b23",
            xaxis=dict(title="X", backgroundcolor="#161b23", gridcolor="#263244", zerolinecolor="#334155", color="#91a4bd"),
            yaxis=dict(title="Y", backgroundcolor="#161b23", gridcolor="#263244", zerolinecolor="#334155", color="#91a4bd"),
            zaxis=dict(title="Z", backgroundcolor="#161b23", gridcolor="#263244", zerolinecolor="#334155", color="#91a4bd"),
            aspectmode="data",
            camera=VIEW_CAMERAS.get(view, VIEW_CAMERAS["Iso"]),
            dragmode="orbit",
        ),
        legend=dict(orientation="h", y=-0.08, x=0.02, font=dict(size=10)),
        uirevision="coldcircuit-cad-studio",
    )
    return fig


def design_code_snippet(plate: ColdPlate, structure_family: str, optimization_method: str) -> str:
    ch = plate.primary_channel()
    return f"""// ColdCircuit parametric design brief
system: coldcircuit
mission: 1500W AI accelerator cold plate
structure: {structure_family}
optimizer: {optimization_method}

ColdPlate({{
  envelope: [{plate.base_size_mm[0]:.0f}, {plate.base_size_mm[1]:.0f}, {plate.thickness_mm:.1f}],
  total_tdp: {sum(s.power_w for s in plate.heat_sources):.0f} W,
  coolant: \"{plate.fluid.name}\",
  flow_rate: {plate.inlet_outlet.flow_rate_lpm:.1f} L/min,
  channel_width: {ch.width_mm:.2f} mm,
  channel_depth: {ch.depth_mm:.2f} mm,
  channel_count: {getattr(ch, 'channel_count', 1)},
  target: max_temp < 75 C, dp < 1.2 bar
}})
"""


def run_optimization(base_plate: ColdPlate, method: str, coolant_inlet_c: float):
    if method == "rule_based":
        grid = {"channel.width_mm": [1.0, 1.2, 1.5], "channel.depth_mm": [1.5, 2.0, 2.5], "inlet_outlet.flow_rate_lpm": [5.0, 8.0, 10.0]}
    else:
        grid = {"channel.width_mm": [0.8, 1.0, 1.2, 1.5, 2.0], "channel.depth_mm": [1.0, 1.5, 2.0, 2.5, 3.0], "inlet_outlet.flow_rate_lpm": [3.0, 5.0, 8.0, 10.0, 12.0]}
        if hasattr(base_plate.primary_channel(), "pitch_mm"):
            grid["channel.pitch_mm"] = [1.5, 2.0, 2.5, 3.0, 4.0]
    return optimize_grid(base_plate, grid, coolant_inlet_c=coolant_inlet_c, top_k=12)


def status_badge(result) -> str:
    if result.passed:
        return '<span class="status-pass">CHECK PASSED</span>'
    return '<span class="status-warn">NEEDS ITERATION</span>'


if "view_mode" not in st.session_state:
    st.session_state.view_mode = "Iso"

left, center, right = st.columns([0.28, 0.48, 0.24], gap="small")

with left:
    st.markdown('<div class="panel"><div class="panel-title">PARAMETRIC DESIGN INPUT <span class="status-pass">LIVE</span></div><div class="panel-body">', unsafe_allow_html=True)
    st.markdown('<div class="mission"><h3>Design Mission</h3><p>Generate and optimize a high-TDP embedded liquid cold plate for AI accelerator cooling. Drag sliders to update the geometry and inspect the 3D model in the main viewport.</p></div>', unsafe_allow_html=True)
    structure_family = st.selectbox("Cold plate structure", STRUCTURE_OPTIONS, index=6)
    optimization_method = st.selectbox("Optimization method", OPTIMIZATION_OPTIONS, index=0)
    base_plate, stack = get_base_plate(structure_family)
    ch0 = base_plate.primary_channel()
    coolant_inlet_c = st.slider("Coolant inlet temperature", 10.0, 50.0, 25.0, 1.0)
    flow_lpm = st.slider("Flow rate", 0.5, 18.0, float(base_plate.inlet_outlet.flow_rate_lpm), 0.1)
    width_mm = st.slider("Channel width", 0.4, 4.0, float(ch0.width_mm), 0.05)
    depth_mm = st.slider("Channel depth", 0.4, min(6.0, float(base_plate.thickness_mm) - 0.3), float(ch0.depth_mm), 0.05)
    pitch_mm = st.slider("Channel pitch", 0.8, 8.0, float(getattr(ch0, "pitch_mm", 2.0)), 0.05) if hasattr(ch0, "pitch_mm") else None
    heat_scale = st.slider("TDP multiplier", 0.3, 1.5, 1.0, 0.05)
    plate = apply_overrides(base_plate, flow_lpm, width_mm, depth_mm, pitch_mm, heat_scale)
    result = plate.simulate_1d(coolant_inlet_c=coolant_inlet_c)
    st.markdown(f'<div class="code-window">{design_code_snippet(plate, structure_family, optimization_method)}</div>', unsafe_allow_html=True)
    run_btn = st.button("Run 3D Optimization", type="primary", use_container_width=True)
    if run_btn:
        st.session_state["opt_result"] = run_optimization(base_plate, optimization_method, coolant_inlet_c)
    st.markdown('</div></div>', unsafe_allow_html=True)

st.markdown(
    f'<div class="topbar"><div class="top-left"><span class="brand">❄ ColdCircuit CAD Studio</span><span class="filetab">{plate.name}.json</span><span class="toolbar-btn">Measure</span><span class="toolbar-btn">Orbit</span><span class="toolbar-btn">Export STEP</span></div><div class="top-right">{status_badge(result)}<span class="toolbar-btn">Publish</span></div></div>',
    unsafe_allow_html=True,
)

with center:
    st.markdown('<div class="panel"><div class="panel-title">MAIN DASHBOARD / DRAGGABLE 3D VIEWPORT <span class="note">drag rotate · wheel zoom · shift pan</span></div><div class="panel-body">', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    for col, label, value in [
        (m1, "TDP", f"{result.total_power_w:.0f} W"),
        (m2, "Max Temp", f"{result.estimated_max_source_temperature_c:.1f} °C"),
        (m3, "Pressure Drop", f"{result.pressure_drop_bar:.3f} bar"),
        (m4, "Regime", result.flow_regime),
    ]:
        col.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)

    t1, t2, t3 = st.columns(3)
    t1.markdown('<div class="target-card"><b>Thermal Target</b><span>Keep accelerator source below 75°C while preserving coolant ΔT margin.</span></div>', unsafe_allow_html=True)
    t2.markdown('<div class="target-card"><b>Hydraulic Target</b><span>Keep pressure drop below 1.2 bar for pump compatibility.</span></div>', unsafe_allow_html=True)
    t3.markdown('<div class="target-card"><b>Manufacturing Target</b><span>Maintain roof/web thickness and avoid fragile microfeatures.</span></div>', unsafe_allow_html=True)

    show_streamlines = st.checkbox("Show coolant streamlines", value=True)
    show_heat = st.checkbox("Show heat source / thermal halo", value=True)
    show_exploded = st.checkbox("Exploded layer view", value=False)
    fig = build_cad_3d(plate, st.session_state.view_mode, show_streamlines, show_heat, show_exploded)
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True, "displaylogo": False, "modeBarButtonsToAdd": ["drawline", "eraseshape"]})
    opt = st.session_state.get("opt_result")
    if opt:
        st.markdown('<div class="panel-title">OPTIMIZATION RESULT</div>', unsafe_allow_html=True)
        if opt.best:
            st.success(f"Best candidate: T={opt.best.max_temperature_c:.1f} °C · ΔP={opt.best.pressure_drop_bar:.3f} bar · {opt.best.variables}")
        st.dataframe(pd.DataFrame([c.model_dump() for c in opt.candidates]), use_container_width=True, hide_index=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel"><div class="panel-title">VIEW / ENGINEERING PANEL</div><div class="panel-body">', unsafe_allow_html=True)
    st.radio("Camera", list(VIEW_CAMERAS.keys()), key="view_mode", horizontal=True)
    st.markdown('<div class="note">Camera presets update the center viewport. Direct drag still works for orbit, zoom, and inspection.</div>', unsafe_allow_html=True)
    st.divider()
    st.markdown('<div class="panel-title">ARCHITECTURE EXPLANATION</div>', unsafe_allow_html=True)
    st.markdown(f'<span class="pill">{structure_family}</span><span class="orange-pill">{optimization_method}</span>', unsafe_allow_html=True)
    rules = all_rules_grouped().get(structure_family, [])
    for rule in rules[:4]:
        st.markdown(f"- **{rule['item']}**: {rule['rule']}")
    st.divider()
    g = tdp1500_guidance()
    st.markdown('<div class="panel-title">1500W STRATEGY</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="note">{g.architecture_summary}</div>', unsafe_allow_html=True)
    st.markdown("".join([f'<span class="pill">{x}</span>' for x in g.recommended_families]), unsafe_allow_html=True)
    st.divider()
    checks = plate.manufacturability_checks()
    st.markdown('<div class="panel-title">DESIGN CHECKS</div>', unsafe_allow_html=True)
    if checks:
        st.dataframe(pd.DataFrame([c.model_dump() for c in checks]), use_container_width=True, hide_index=True)
    else:
        st.success("No rule-based issue detected.")
    st.markdown('</div></div>', unsafe_allow_html=True)
