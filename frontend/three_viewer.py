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
    variant: str = "generic",
    height: int = 650,
):
    """Render a real Three.js draggable cold-plate viewport inside Streamlit.

    variant='generic': hybrid manifold/microchannel concept.
    variant='drawing_based_redesign': STEP-inspired redesign based on the uploaded
    drawing stack: inlet/outlet plate, jet plate, silicone gasket, pin-fin plate.
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
        "variant": variant,
    }
    data_json = json.dumps(payload)
    label = "STEP-inspired redesign: inlet/outlet plate · jet plate · gasket · pin-fin base" if variant == "drawing_based_redesign" else "IN → balanced manifold microchannels → OUT"

    html = f"""
<!doctype html><html><head><meta charset='utf-8'/>
<style>
html,body{{margin:0;padding:0;overflow:hidden;background:#151b24;font-family:Inter,-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif}}
#root{{width:100vw;height:{height}px;position:relative;background:radial-gradient(circle at 50% 35%,#26364d 0%,#151b24 52%,#0b0f16 100%)}}
#hud{{position:absolute;left:16px;top:14px;z-index:5;display:flex;gap:8px;align-items:center;flex-wrap:wrap;color:#dbeafe}}
.chip{{padding:6px 10px;border-radius:999px;background:rgba(15,23,42,.78);border:1px solid rgba(125,211,252,.25);font-size:12px;font-weight:700;backdrop-filter:blur(8px)}}
#hint{{position:absolute;right:16px;bottom:14px;z-index:5;color:#94a3b8;font-size:12px;background:rgba(15,23,42,.68);border:1px solid rgba(148,163,184,.18);border-radius:10px;padding:8px 10px}}
#label{{position:absolute;left:16px;bottom:14px;z-index:5;color:#e5edf8;font-size:13px;background:rgba(15,23,42,.70);border:1px solid rgba(148,163,184,.18);border-radius:10px;padding:8px 10px}}
canvas{{display:block}}
</style></head><body>
<div id='root'><div id='hud'><span class='chip'>Three.js WebGL</span><span class='chip'>{escape(plate_name)}</span><span class='chip'>TDP {tdp_w:.0f} W</span><span class='chip'>Max {max_temp_c:.1f} °C</span><span class='chip'>ΔP {pressure_drop_bar:.3f} bar</span></div><div id='label'>{escape(label)}</div><div id='hint'>Left drag: orbit · Wheel: zoom · Right drag: pan</div></div>
<script type='importmap'>{{"imports":{{"three":"https://unpkg.com/three@0.161.0/build/three.module.js","three/addons/":"https://unpkg.com/three@0.161.0/examples/jsm/"}}}}</script>
<script type='module'>
import * as THREE from 'three';
import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
const cfg={data_json};
const root=document.getElementById('root');
const scene=new THREE.Scene();
scene.fog=new THREE.Fog(0x101722,260,760);
const camera=new THREE.PerspectiveCamera(42,root.clientWidth/root.clientHeight,0.1,2000);
const renderer=new THREE.WebGLRenderer({{antialias:true,alpha:true}});
renderer.setSize(root.clientWidth,root.clientHeight);renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.shadowMap.enabled=true;root.appendChild(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.06;controls.rotateSpeed=.75;controls.zoomSpeed=.85;controls.panSpeed=.65;
const maxDim=Math.max(cfg.width,cfg.depth);
if(cfg.viewMode==='Top')camera.position.set(0,0,maxDim*1.95);else if(cfg.viewMode==='Front')camera.position.set(0,-maxDim*1.8,maxDim*.35);else if(cfg.viewMode==='Back')camera.position.set(0,maxDim*1.8,maxDim*.35);else if(cfg.viewMode==='Left')camera.position.set(-maxDim*1.8,0,maxDim*.35);else if(cfg.viewMode==='Right')camera.position.set(maxDim*1.8,0,maxDim*.35);else camera.position.set(maxDim*1.18,-maxDim*1.05,maxDim*.62);controls.target.set(0,0,0);controls.update();
scene.add(new THREE.HemisphereLight(0xbfe9ff,0x121821,1.35));
const key=new THREE.DirectionalLight(0xffffff,2.25);key.position.set(120,-160,180);key.castShadow=true;scene.add(key);
const rim=new THREE.PointLight(0x1cc8ff,2.6,520);rim.position.set(-cfg.width*.55,-cfg.depth*.52,50);scene.add(rim);
const heatLight=new THREE.PointLight(0xff5630,3.5,420);heatLight.position.set(0,0,42);scene.add(heatLight);
const grid=new THREE.GridHelper(maxDim*1.55,28,0x2d415c,0x1b293d);grid.rotation.x=Math.PI/2;grid.position.z=-cfg.thickness*.70;scene.add(grid);
function mat(color,o={{}}){{return new THREE.MeshPhysicalMaterial({{color,metalness:o.metalness??.35,roughness:o.roughness??.32,transparent:o.transparent??false,opacity:o.opacity??1,transmission:o.transmission??0,clearcoat:o.clearcoat??.25,emissive:o.emissive??0x000000,emissiveIntensity:o.emissiveIntensity??0}})}}
const M={{body:mat(0x64748b,{{metalness:.62,roughness:.26,clearcoat:.55}}),dark:mat(0x38475c,{{metalness:.68,roughness:.30,clearcoat:.52}}),blue:mat(0x0ea5e9,{{transparent:true,opacity:.34,emissive:0x0a70a8,emissiveIntensity:.15}}),cover:mat(0x9bdcff,{{transparent:true,opacity:.18,transmission:.48,clearcoat:1}}),chan:mat(0x25d7ff,{{transparent:true,opacity:.72,emissive:0x0ea5e9,emissiveIntensity:.42}}),hot:mat(0xff3d22,{{transparent:true,opacity:.86,emissive:0xff3d22,emissiveIntensity:.9}}),halo:mat(0xff9a2a,{{transparent:true,opacity:.14,emissive:0xff5a1f,emissiveIntensity:.55}}),gasket:mat(0xffb86b,{{transparent:true,opacity:.34,transmission:.12,emissive:0x7a3108,emissiveIntensity:.08}}),pin:mat(0xb7c4d6,{{metalness:.58,roughness:.28,clearcoat:.35}}),hole:mat(0x06111f,{{metalness:.25,roughness:.55}}),port:mat(0x94a3b8,{{metalness:.82,roughness:.24,clearcoat:.55}})}};
function box(w,d,h,m,x=0,y=0,z=0,name='box'){{const mesh=new THREE.Mesh(new THREE.BoxGeometry(w,d,h),m);mesh.position.set(x,y,z);mesh.castShadow=true;mesh.receiveShadow=true;mesh.name=name;scene.add(mesh);return mesh}}
function cyl(r,h,m,x=0,y=0,z=0,name='cyl',axis='z'){{const mesh=new THREE.Mesh(new THREE.CylinderGeometry(r,r,h,32),m);if(axis==='x')mesh.rotation.z=Math.PI/2;if(axis==='y')mesh.rotation.x=Math.PI/2;mesh.position.set(x,y,z);mesh.castShadow=true;mesh.receiveShadow=true;scene.add(mesh);return mesh}}
function tube(points,color,r){{const curve=new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(p[0],p[1],p[2])));const mesh=new THREE.Mesh(new THREE.TubeGeometry(curve,96,r,10,false),new THREE.MeshBasicMaterial({{color,transparent:true,opacity:.86}}));scene.add(mesh);return mesh}}
function generic(){{const e=cfg.showExploded?cfg.thickness*.28:0,W=cfg.width,D=cfg.depth,T=cfg.thickness;box(W,D,T*.32,M.body,0,0,-T*.30);box(W*.92,D*.84,T*.26,M.blue,0,0,e);box(W,D,T*.20,M.cover,0,0,T*.33+e*2);const n=cfg.channelCount,y0=-D*.34,y1=D*.34;for(let i=0;i<n;i++){{let y=y0+(y1-y0)*i/Math.max(n-1,1);box(W*.66,Math.max(cfg.channelWidth,.45),Math.max(cfg.channelDepth,.45),M.chan,0,y,T*.04+e)}}box(W*.11,D*.74,T*.28,M.blue,-W*.40,0,T*.05+e);box(W*.11,D*.74,T*.28,M.blue,W*.40,0,T*.05+e);if(cfg.showHeat){{box(W*.38,D*.46,T*.16,M.hot,0,0,T*.54+e*2);box(W*.55,D*.62,T*.04,M.halo,0,0,T*.49+e*2)}}cyl(D*.06,W*.16,M.port,-W*.58,0,T*.05+e,'IN','x');cyl(D*.06,W*.16,M.port,W*.58,0,T*.05+e,'OUT','x');if(cfg.showStreamlines){{let z=T*.18+e,sn=Math.min(14,n);for(let i=0;i<sn;i++){{let y=y0+(y1-y0)*i/Math.max(sn-1,1);tube([[-W*.68,0,z],[-W*.48,0,z],[-W*.36,y,z],[-W*.12,y,z],[W*.12,y,z],[W*.36,y,z],[W*.48,0,z],[W*.68,0,z]],i===0||i===sn-1?0x38bdf8:0x67e8f9,i===0||i===sn-1?.75:.48)}}}}}}
function drawingRedesign(){{const gap=cfg.showExploded?cfg.thickness*.22:0,W=cfg.width,D=cfg.depth,T=cfg.thickness;box(W,D,T*.18,M.dark,0,0,-T*.44,'pin-fin base');box(W*.92,D*.82,T*.06,M.gasket,0,0,-T*.20+gap,'silicone gasket');box(W*.92,D*.82,T*.10,M.blue,0,0,-T*.02+gap*2,'jet plate');box(W,D,T*.22,M.body,0,0,T*.26+gap*3,'inlet/outlet plate');if(cfg.showHeat){{box(W*.34,D*.45,T*.09,M.hot,0,0,T*.45+gap*3,'hotspot');box(W*.48,D*.62,T*.025,M.halo,0,0,T*.40+gap*3,'thermal spread')}}for(let i=0;i<15;i++)for(let j=0;j<8;j++){{let x=-W*.32+W*.64*i/14,y=-D*.30+D*.60*j/7;let p=cyl(Math.max(.45,cfg.channelWidth*.42),Math.max(1,T*.23),M.pin,x,y,-T*.12,'pin','z')}}for(let i=0;i<12;i++)for(let j=0;j<5;j++){{let x=-W*.30+W*.60*i/11,y=-D*.22+D*.44*j/4;cyl(Math.max(.45,cfg.channelWidth*.34),T*.018,M.hole,x,y,T*.055+gap*2,'jet hole','z')}}box(W*.12,D*.76,T*.16,M.blue,-W*.42,0,T*.28+gap*3,'left plenum');box(W*.12,D*.76,T*.16,M.blue,W*.42,0,T*.28+gap*3,'right plenum');cyl(D*.055,W*.14,M.port,-W*.60,-D*.20,T*.28+gap*3,'IN A','x');cyl(D*.055,W*.14,M.port,-W*.60,D*.20,T*.28+gap*3,'IN B','x');cyl(D*.055,W*.14,M.port,W*.60,-D*.20,T*.28+gap*3,'OUT A','x');cyl(D*.055,W*.14,M.port,W*.60,D*.20,T*.28+gap*3,'OUT B','x');if(cfg.showStreamlines){{let zTop=T*.34+gap*3,zJet=T*.08+gap*2;for(let j=0;j<8;j++){{let y=-D*.28+D*.56*j/7;tube([[-W*.66,-D*.20,zTop],[-W*.45,y,zTop],[-W*.25,y,zJet],[W*.22,y,zJet],[W*.45,y,zTop],[W*.66,-D*.20,zTop]],0x38bdf8,.42);tube([[-W*.66,D*.20,zTop],[-W*.45,y,zTop],[-W*.25,y,zJet],[W*.22,y,zJet],[W*.45,y,zTop],[W*.66,D*.20,zTop]],0x67e8f9,.34)}}}}}}
if(cfg.variant==='drawing_based_redesign')drawingRedesign();else generic();
const canvas=document.createElement('canvas');canvas.width=1200;canvas.height=256;const ctx=canvas.getContext('2d');ctx.fillStyle='rgba(0,0,0,0)';ctx.fillRect(0,0,1200,256);ctx.fillStyle='#dbeafe';ctx.font='700 48px Inter,Arial';ctx.fillText(cfg.variant==='drawing_based_redesign'?'DUAL IN':'IN',70,142);ctx.fillText(cfg.variant==='drawing_based_redesign'?'DUAL OUT':'OUT',845,142);ctx.fillStyle='#7dd3fc';ctx.font='500 28px Inter,Arial';ctx.fillText(cfg.variant==='drawing_based_redesign'?'redesigned from uploaded STEP stack':'drag / orbit / zoom',340,142);const sprite=new THREE.Sprite(new THREE.SpriteMaterial({{map:new THREE.CanvasTexture(canvas),transparent:true,opacity:.95}}));sprite.position.set(0,-cfg.depth*.72,cfg.thickness*.85);sprite.scale.set(cfg.width*1.05,cfg.width*.23,1);scene.add(sprite);
function animate(){{requestAnimationFrame(animate);controls.update();renderer.render(scene,camera)}}animate();
window.addEventListener('resize',()=>{{const w=root.clientWidth,h=root.clientHeight;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h)}});
</script></body></html>
"""
    components.html(html, height=height, scrolling=False)
