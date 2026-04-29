import json
from html import escape

import streamlit.components.v1 as components


def render_three_coldplate(
    *,
    plate_name: str,
    width_mm: float,
    depth_mm: float,
    thickness_mm: float,
    channel_count: int,
    channel_width_mm: float,
    channel_depth_mm: float,
    tdp_w: float,
    max_temp_c: float,
    pressure_drop_bar: float,
    view_mode: str = "Iso",
    show_streamlines: bool = True,
    show_heat: bool = True,
    show_exploded: bool = False,
    height: int = 650,
):
    """Render a real Three.js draggable cold-plate viewport inside Streamlit.

    This is intentionally self-contained so the dashboard does not require a custom
    Streamlit component build step. OrbitControls provides drag/zoom/pan.
    """

    payload = {
        "plateName": plate_name,
        "width": width_mm,
        "depth": depth_mm,
        "thickness": thickness_mm,
        "channelCount": max(4, min(int(channel_count), 96)),
        "channelWidth": channel_width_mm,
        "channelDepth": channel_depth_mm,
        "tdp": tdp_w,
        "maxTemp": max_temp_c,
        "pressureDrop": pressure_drop_bar,
        "viewMode": view_mode,
        "showStreamlines": bool(show_streamlines),
        "showHeat": bool(show_heat),
        "showExploded": bool(show_exploded),
    }
    data_json = json.dumps(payload)

    html = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    html, body {{ margin:0; padding:0; overflow:hidden; background:#151b24; font-family: Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Arial, sans-serif; }}
    #root {{ width:100vw; height:{height}px; position:relative; background: radial-gradient(circle at 50% 35%, #26364d 0%, #151b24 52%, #0b0f16 100%); }}
    #hud {{ position:absolute; left:16px; top:14px; z-index:5; display:flex; gap:8px; align-items:center; color:#dbeafe; }}
    .chip {{ padding:6px 10px; border-radius:999px; background:rgba(15,23,42,.78); border:1px solid rgba(125,211,252,.25); font-size:12px; font-weight:700; backdrop-filter: blur(8px); }}
    #hint {{ position:absolute; right:16px; bottom:14px; z-index:5; color:#94a3b8; font-size:12px; background:rgba(15,23,42,.68); border:1px solid rgba(148,163,184,.18); border-radius:10px; padding:8px 10px; backdrop-filter: blur(8px); }}
    #label {{ position:absolute; left:16px; bottom:14px; z-index:5; color:#e5edf8; font-size:13px; background:rgba(15,23,42,.70); border:1px solid rgba(148,163,184,.18); border-radius:10px; padding:8px 10px; backdrop-filter: blur(8px); }}
    canvas {{ display:block; }}
  </style>
</head>
<body>
  <div id="root">
    <div id="hud">
      <span class="chip">Three.js WebGL Viewport</span>
      <span class="chip">{escape(plate_name)}</span>
      <span class="chip">TDP {tdp_w:.0f} W</span>
      <span class="chip">Max {max_temp_c:.1f} °C</span>
      <span class="chip">ΔP {pressure_drop_bar:.3f} bar</span>
    </div>
    <div id="label">IN → balanced manifold microchannels → OUT</div>
    <div id="hint">Left drag: orbit · Wheel: zoom · Right drag: pan</div>
  </div>

<script type="importmap">
{{
  "imports": {{
    "three": "https://unpkg.com/three@0.161.0/build/three.module.js",
    "three/addons/": "https://unpkg.com/three@0.161.0/examples/jsm/"
  }}
}}
</script>
<script type="module">
import * as THREE from 'three';
import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';

const cfg = {data_json};
const root = document.getElementById('root');
const W = root.clientWidth;
const H = root.clientHeight;

const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x101722, 260, 760);

const camera = new THREE.PerspectiveCamera(42, W/H, 0.1, 2000);
const renderer = new THREE.WebGLRenderer({{ antialias:true, alpha:true }});
renderer.setSize(W, H);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
root.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.rotateSpeed = 0.75;
controls.zoomSpeed = 0.85;
controls.panSpeed = 0.65;

const view = cfg.viewMode;
const maxDim = Math.max(cfg.width, cfg.depth);
if (view === 'Top') camera.position.set(0, 0, maxDim * 1.85);
else if (view === 'Front') camera.position.set(0, -maxDim * 1.8, maxDim * 0.35);
else if (view === 'Back') camera.position.set(0, maxDim * 1.8, maxDim * 0.35);
else if (view === 'Left') camera.position.set(-maxDim * 1.8, 0, maxDim * 0.35);
else if (view === 'Right') camera.position.set(maxDim * 1.8, 0, maxDim * 0.35);
else camera.position.set(maxDim * 1.18, -maxDim * 1.05, maxDim * 0.62);
controls.target.set(0, 0, 0);
controls.update();

scene.add(new THREE.HemisphereLight(0xbfe9ff, 0x121821, 1.3));
const key = new THREE.DirectionalLight(0xffffff, 2.2);
key.position.set(120, -160, 180);
key.castShadow = true;
scene.add(key);
const rim = new THREE.PointLight(0x1cc8ff, 2.6, 520);
rim.position.set(-cfg.width * 0.55, -cfg.depth * 0.52, 50);
scene.add(rim);
const heatLight = new THREE.PointLight(0xff5630, 3.5, 420);
heatLight.position.set(0, 0, 42);
scene.add(heatLight);

const grid = new THREE.GridHelper(maxDim * 1.55, 28, 0x2d415c, 0x1b293d);
grid.rotation.x = Math.PI / 2;
grid.position.z = -cfg.thickness * 0.58;
scene.add(grid);

function mat(color, opts={{}}) {{
  return new THREE.MeshPhysicalMaterial({{
    color,
    metalness: opts.metalness ?? 0.35,
    roughness: opts.roughness ?? 0.32,
    transparent: opts.transparent ?? false,
    opacity: opts.opacity ?? 1,
    transmission: opts.transmission ?? 0,
    clearcoat: opts.clearcoat ?? 0.25,
    emissive: opts.emissive ?? 0x000000,
    emissiveIntensity: opts.emissiveIntensity ?? 0,
  }});
}}

const bodyMat = mat(0x64748b, {{metalness:0.62, roughness:0.26, clearcoat:0.55}});
const coreMat = mat(0x0ea5e9, {{transparent:true, opacity:0.32, metalness:0.08, roughness:0.18, transmission:0.22, clearcoat:0.8}});
const coverMat = mat(0x9bdcff, {{transparent:true, opacity:0.18, metalness:0.03, roughness:0.05, transmission:0.48, clearcoat:1.0}});
const channelMat = mat(0x25d7ff, {{transparent:true, opacity:0.72, emissive:0x0ea5e9, emissiveIntensity:0.42, roughness:0.12}});
const hotMat = mat(0xff3d22, {{transparent:true, opacity:0.86, emissive:0xff3d22, emissiveIntensity:0.9, roughness:0.18}});
const haloMat = mat(0xff9a2a, {{transparent:true, opacity:0.14, emissive:0xff5a1f, emissiveIntensity:0.55}});

function roundedBox(w,d,h, material, z, name) {{
  const geo = new THREE.BoxGeometry(w, d, h, 1, 1, 1);
  const mesh = new THREE.Mesh(geo, material);
  mesh.position.set(0, 0, z);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  mesh.name = name;
  scene.add(mesh);
  return mesh;
}}

const exploded = cfg.showExploded ? cfg.thickness * 0.28 : 0;
roundedBox(cfg.width, cfg.depth, cfg.thickness * 0.32, bodyMat, -cfg.thickness * 0.30, 'base plate');
roundedBox(cfg.width * 0.92, cfg.depth * 0.84, cfg.thickness * 0.26, coreMat, 0 + exploded, 'microchannel core');
roundedBox(cfg.width, cfg.depth, cfg.thickness * 0.20, coverMat, cfg.thickness * 0.33 + exploded * 2, 'transparent cover');

const chN = cfg.channelCount;
const y0 = -cfg.depth * 0.34;
const y1 = cfg.depth * 0.34;
for (let i=0; i<chN; i++) {{
  const y = y0 + (y1-y0) * i / Math.max(chN-1, 1);
  const ch = roundedBox(cfg.width * 0.66, Math.max(cfg.channelWidth, 0.45), Math.max(cfg.channelDepth, 0.45), channelMat, cfg.thickness * 0.04 + exploded, 'microchannel');
  ch.position.y = y;
}}

const manifoldMat = mat(0x1e3a5f, {{transparent:true, opacity:0.55, emissive:0x0a70a8, emissiveIntensity:0.18}});
const leftManifold = roundedBox(cfg.width*0.11, cfg.depth*0.74, cfg.thickness*0.28, manifoldMat, cfg.thickness*0.05+exploded, 'inlet manifold');
leftManifold.position.x = -cfg.width*0.40;
const rightManifold = roundedBox(cfg.width*0.11, cfg.depth*0.74, cfg.thickness*0.28, manifoldMat, cfg.thickness*0.05+exploded, 'outlet manifold');
rightManifold.position.x = cfg.width*0.40;

if (cfg.showHeat) {{
  roundedBox(cfg.width*0.38, cfg.depth*0.46, cfg.thickness*0.16, hotMat, cfg.thickness*0.54+exploded*2, 'AI accelerator hotspot');
  roundedBox(cfg.width*0.55, cfg.depth*0.62, cfg.thickness*0.04, haloMat, cfg.thickness*0.49+exploded*2, 'thermal halo');
}}

const portMat = mat(0x94a3b8, {{metalness:0.82, roughness:0.24, clearcoat:0.55}});
function cylinderPort(x, label, color) {{
  const geo = new THREE.CylinderGeometry(cfg.depth*0.06, cfg.depth*0.06, cfg.width*0.16, 48);
  const mesh = new THREE.Mesh(geo, portMat);
  mesh.rotation.z = Math.PI / 2;
  mesh.position.set(x, 0, cfg.thickness*0.05+exploded);
  mesh.castShadow = true;
  scene.add(mesh);
  const light = new THREE.PointLight(color, 1.7, 160);
  light.position.set(x, 0, cfg.thickness*0.1+exploded);
  scene.add(light);
}}
cylinderPort(-cfg.width*0.58, 'IN', 0x22d3ee);
cylinderPort(cfg.width*0.58, 'OUT', 0x10b981);

function makeStreamline(points, color, radius) {{
  const curve = new THREE.CatmullRomCurve3(points.map(p => new THREE.Vector3(p[0], p[1], p[2])));
  const geo = new THREE.TubeGeometry(curve, 96, radius, 10, false);
  const m = new THREE.MeshBasicMaterial({{ color, transparent:true, opacity:0.86 }});
  const mesh = new THREE.Mesh(geo, m);
  scene.add(mesh);
  return mesh;
}}
if (cfg.showStreamlines) {{
  const z = cfg.thickness*0.18 + exploded;
  const streamN = Math.min(14, chN);
  for (let i=0; i<streamN; i++) {{
    const y = y0 + (y1-y0) * i / Math.max(streamN-1, 1);
    makeStreamline([
      [-cfg.width*0.68,0,z],[-cfg.width*0.48,0,z],[-cfg.width*0.36,y,z],[-cfg.width*0.12,y,z],[cfg.width*0.12,y,z],[cfg.width*0.36,y,z],[cfg.width*0.48,0,z],[cfg.width*0.68,0,z]
    ], i===0 || i===streamN-1 ? 0x38bdf8 : 0x67e8f9, i===0 || i===streamN-1 ? 0.75 : 0.48);
  }}
}}

const labelCanvas = document.createElement('canvas');
labelCanvas.width = 1024; labelCanvas.height = 256;
const ctx = labelCanvas.getContext('2d');
ctx.fillStyle = 'rgba(0,0,0,0)'; ctx.fillRect(0,0,1024,256);
ctx.fillStyle = '#dbeafe'; ctx.font = '700 54px Inter, Arial';
ctx.fillText('IN', 90, 142); ctx.fillText('OUT', 815, 142);
ctx.fillStyle = '#7dd3fc'; ctx.font = '500 30px Inter, Arial';
ctx.fillText('drag / orbit / zoom', 365, 142);
const tex = new THREE.CanvasTexture(labelCanvas);
const spriteMat = new THREE.SpriteMaterial({{ map: tex, transparent:true, opacity:.95 }});
const sprite = new THREE.Sprite(spriteMat);
sprite.position.set(0, -cfg.depth*0.72, cfg.thickness*0.72);
sprite.scale.set(cfg.width*0.95, cfg.width*0.24, 1);
scene.add(sprite);

function animate() {{
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}}
animate();

window.addEventListener('resize', () => {{
  const w = root.clientWidth, h = root.clientHeight;
  camera.aspect = w/h;
  camera.updateProjectionMatrix();
  renderer.setSize(w,h);
}});
</script>
</body>
</html>
"""
    components.html(html, height=height, scrolling=False)
