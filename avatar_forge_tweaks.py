#!/usr/bin/env python3
"""avatar_forge_tweaks.py — fade the forge back into the dark + parchment telemetry bars.
Idempotent; backs up first."""
import io, sys, time, shutil

P = "/Users/kevin/Downloads/vintos-repo/vintos-app/src/index.html"
s = io.open(P, encoding="utf-8").read()

if "FogExp2(BG, 0.075)" in s and "let _avStateColor = '#e8dcc0'" in s:
    print("already tweaked — skipping"); sys.exit(0)

log = []
def rep(old, new):
    global s
    if old in s:
        s = s.replace(old, new, 1); log.append("OK  " + old[:46])
    else:
        log.append("MISS " + old[:46])

# --- forge fade ---
rep("_avScene.fog = new THREE.FogExp2(BG, 0.055);",
    "_avScene.fog = new THREE.FogExp2(BG, 0.075);")
rep("const forgeLight = new THREE.PointLight(0xff7a30, 6, 7, 2); forgeLight.position.set(-1.8,0.7,-2.4);",
    "const forgeLight = new THREE.PointLight(0xff7a30, 4.5, 8, 2); forgeLight.position.set(-1.8,0.7,-3.0);")
rep("bottomGlow.position.set(-1.9,0.4,-2.35); bottomGlow.scale.set(0.7,0.55,1);",
    "bottomGlow.position.set(-1.9,0.4,-2.95); bottomGlow.scale.set(0.6,0.48,1);")
rep("sheen.rotation.x=-Math.PI/2; sheen.position.set(-1.5,0.03,-1.4);",
    "sheen.rotation.x=-Math.PI/2; sheen.position.set(-1.5,0.03,-2.0);")
rep("loadProp(API+'/avatar-models/forge.fbx', {x:-1.7, z:-2.8, size:3.0, ry:0.6, forgeSkin:true});",
    "loadProp(API+'/avatar-models/forge.fbx', {x:-1.7, z:-3.5, size:2.7, ry:0.6, forgeSkin:true});")
rep("if(fg.forgeLight) fg.forgeLight.intensity = 6*fl;",
    "if(fg.forgeLight) fg.forgeLight.intensity = 4.5*fl;")
rep("if(fg.bottomGlow) fg.bottomGlow.material.opacity = 0.82*fl;",
    "if(fg.bottomGlow) fg.bottomGlow.material.opacity = 0.6*fl;")

# --- parchment: avatar overlay bars ---
rep("let _avStateColor = '#C96B3C';", "let _avStateColor = '#e8dcc0';")
rep("_avStateColor = hex;", "_avStateColor = '#e8dcc0';")
rep("el.style.background = hex+'99';", "el.style.background = '#e8dcc0'+'99';")

# --- parchment: main state-card bars (scoped, beats inline meta.color) ---
if ".dim .bar-fill{background:#e8dcc0" not in s:
    s = s.replace("</style>", ".dim .bar-fill{background:#e8dcc0 !important;}\n</style>", 1)
    log.append("OK  main-card .dim .bar-fill CSS")

shutil.copy(P, P + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(P, "w", encoding="utf-8").write(s)
for l in log: print("  " + l)
print("DONE" if all(not l.startswith("MISS") for l in log) else "DONE (some MISS — paste this)")
