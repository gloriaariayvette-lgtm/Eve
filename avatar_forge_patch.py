#!/usr/bin/env python3
"""avatar_forge_patch.py — restore the forge avatar scene into the app.

Replaces the reverted space/stars _avInit + _avAnimate with the working forge
scene (MeshBasicMaterial skin + atlas, baked idle, forge/anvil/embers/smoke),
ported from avatar-test.html and adapted to the app's globals (window.THREE,
bundle FBXLoader, _avScene/_avCamera/_avRenderer). Leaves _avSpawn, the three
buttons, tabs, and everything else untouched. Also fixes the GCS glyph to the flower.
Idempotent; backs up first; anchored slicing so it can't land wrong.
"""
import io, sys, time, shutil

P = "/Users/kevin/Downloads/vintos-repo/vintos-app/src/index.html"
s = io.open(P, encoding="utf-8").read()

if "window._fg" in s and "MeshBasicMaterial({map:tex" in s:
    print("already forge — skipping"); sys.exit(0)

NEW_AVINIT = r'''async function _avInit() {
  const canvas = document.getElementById('avatar-canvas');
  const W = window.innerWidth, H = window.innerHeight;
  const BG = 0x0b0a0c;
  _avClock = new THREE.Clock();
  _avRenderer = new THREE.WebGLRenderer({canvas, antialias:true, alpha:true});
  _avRenderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
  _avRenderer.setSize(W,H);
  _avRenderer.outputColorSpace = THREE.SRGBColorSpace;
  _avScene = new THREE.Scene();
  _avScene.background = new THREE.Color(BG);
  _avScene.fog = new THREE.FogExp2(BG, 0.055);
  _avCamera = new THREE.PerspectiveCamera(52, W/H, 0.01, 200);
  _avCamera.position.set(0, 1.25, 4.0);
  _avCamera.lookAt(0, 0.92, 0);
  _avScene.add(new THREE.AmbientLight(0xffffff, 0.55));
  const dl1 = new THREE.DirectionalLight(0xfff0d8, 2.4); dl1.position.set(0.6,2.2,3.0); _avScene.add(dl1);
  const dl2 = new THREE.DirectionalLight(0xff9040, 1.3); dl2.position.set(-2.0,1.2,0.6); _avScene.add(dl2);
  const forgeLight = new THREE.PointLight(0xff7a30, 6, 7, 2); forgeLight.position.set(-1.8,0.7,-2.4); _avScene.add(forgeLight);

  function radial(r,g,b,a){ const c=document.createElement('canvas'); c.width=c.height=64; const x=c.getContext('2d');
    const gr=x.createRadialGradient(32,32,1,32,32,32); gr.addColorStop(0,`rgba(${r},${g},${b},${a})`); gr.addColorStop(1,`rgba(${r},${g},${b},0)`);
    x.fillStyle=gr; x.fillRect(0,0,64,64); const t=new THREE.CanvasTexture(c); t.colorSpace=THREE.SRGBColorSpace; return t; }
  function brickTex(){ const c=document.createElement('canvas'); c.width=c.height=256; const x=c.getContext('2d');
    x.fillStyle='#241812'; x.fillRect(0,0,256,256);
    const bh=30,bw=58,mg=4;
    for(let row=0,y=0;y<260;row++,y+=bh){ const off=(row%2)*(bw/2);
      for(let bx=-bw;bx<256;bx+=bw){ const sc=0.72+Math.random()*0.36;
        x.fillStyle=`rgb(${Math.floor(96*sc)},${Math.floor(58*sc)},${Math.floor(44*sc)})`;
        x.fillRect(bx+off+mg/2,y+mg/2,bw-mg,bh-mg); } }
    const t=new THREE.CanvasTexture(c); t.colorSpace=THREE.SRGBColorSpace; t.wrapS=t.wrapT=THREE.RepeatWrapping; t.repeat.set(40,40); t.anisotropy=8; return t; }
  function metalTex(){ const c=document.createElement('canvas'); c.width=c.height=128; const x=c.getContext('2d');
    x.fillStyle='#2a251c'; x.fillRect(0,0,128,128);
    for(let i=0;i<2400;i++){ const v=22+Math.random()*32; x.fillStyle=`rgba(${v},${v-4},${v-9},0.4)`; x.fillRect(Math.random()*128,Math.random()*128,2,2); }
    const t=new THREE.CanvasTexture(c); t.colorSpace=THREE.SRGBColorSpace; return t; }
  const floor=new THREE.Mesh(new THREE.CircleGeometry(26,64), new THREE.MeshBasicMaterial({color:0x08070a}));
  floor.rotation.x=-Math.PI/2; _avScene.add(floor);
  const sheenMat=new THREE.MeshBasicMaterial({map:radial(150,80,34,1.0), transparent:true, opacity:0.55, depthWrite:false, fog:false});
  sheenMat.polygonOffset=true; sheenMat.polygonOffsetFactor=-2; sheenMat.polygonOffsetUnits=-2;
  const sheen=new THREE.Mesh(new THREE.PlaneGeometry(4.5,3.2), sheenMat);
  sheen.rotation.x=-Math.PI/2; sheen.position.set(-1.5,0.03,-1.4); _avScene.add(sheen);
  function softShadow(w,h,x,z,a){ const cc=document.createElement('canvas'); cc.width=cc.height=128; const xx=cc.getContext('2d');
    const g=xx.createRadialGradient(64,64,2,64,64,64); g.addColorStop(0,'rgba(0,0,0,'+a+')'); g.addColorStop(0.55,'rgba(0,0,0,'+(a*0.35)+')'); g.addColorStop(1,'rgba(0,0,0,0)');
    xx.fillStyle=g; xx.fillRect(0,0,128,128);
    const mm=new THREE.MeshBasicMaterial({map:new THREE.CanvasTexture(cc), transparent:true, depthWrite:false, fog:false});
    mm.polygonOffset=true; mm.polygonOffsetFactor=-4; mm.polygonOffsetUnits=-4;
    const me=new THREE.Mesh(new THREE.PlaneGeometry(w,h), mm); me.rotation.x=-Math.PI/2; me.position.set(x,0.05,z); _avScene.add(me); }
  softShadow(0.85,0.52,0,0.05,0.5);
  softShadow(1.5,1.0,-1.7,-2.6,0.4);
  const bottomGlow=new THREE.Sprite(new THREE.SpriteMaterial({map:radial(255,150,60,1.0), transparent:true, opacity:0.9, depthWrite:false, blending:THREE.AdditiveBlending, fog:false}));
  bottomGlow.position.set(-1.9,0.4,-2.35); bottomGlow.scale.set(0.7,0.55,1); _avScene.add(bottomGlow);
  function wispTex(){ const c=document.createElement('canvas'); c.width=64; c.height=256; const x=c.getContext('2d');
    for(let i=0;i<22;i++){ const yy=Math.random()*256; const xx=32+(Math.random()-0.5)*(24*(1-yy/300)+6);
      const r=5+Math.random()*11*(1-yy/320); const a=0.05+Math.random()*0.06*(1-yy/256);
      const g=x.createRadialGradient(xx,yy,0,xx,yy,r); g.addColorStop(0,`rgba(186,181,173,${a})`); g.addColorStop(1,'rgba(186,181,173,0)');
      x.fillStyle=g; x.fillRect(0,0,64,256); }
    const t=new THREE.CanvasTexture(c); t.colorSpace=THREE.SRGBColorSpace; return t; }
  const wtex=wispTex(); const wisps=[];
  for(let i=0;i<10;i++){ const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:wtex, transparent:true, opacity:0.72, depthWrite:false, fog:false}));
    const left = i<5; const bx = left ? (-2.4+Math.random()*1.6) : (0.1+Math.random()*1.5);
    sp.userData={x:bx, y:0.3+Math.random()*2, z:0.3-Math.random()*1.4, vy:0.14+Math.random()*0.12, sway:Math.random()*6, w:0.55+Math.random()*0.35, h:2.2+Math.random()*1.2};
    sp.scale.set(sp.userData.w, sp.userData.h, 1); wisps.push(sp); _avScene.add(sp); }
  const etex=radial(255,190,110,1.0);
  const N=110, ep=new Float32Array(N*3), es=new Float32Array(N);
  function er(i){ if(i%2){ ep[i*3]=0.1+Math.random()*1.5; } else { ep[i*3]=-2.4+Math.random()*1.6; } ep[i*3+1]=Math.random()*0.3; ep[i*3+2]=0.3-Math.random()*1.4; }
  for(let i=0;i<N;i++){ er(i); ep[i*3+1]=Math.random()*3.0; es[i]=0.06+Math.random()*0.18; }
  const eg=new THREE.BufferGeometry(); eg.setAttribute('position', new THREE.BufferAttribute(ep,3));
  _avScene.add(new THREE.Points(eg, new THREE.PointsMaterial({map:etex, color:0xffb060, size:0.032, transparent:true, opacity:0.55, blending:THREE.AdditiveBlending, depthWrite:false, fog:false})));

  window._fg = {sheenMat:sheenMat, bottomGlow:bottomGlow, wisps:wisps, eg:eg, es:es, N:N, forgeLight:forgeLight, t:0};

  function loadProp(url, place){
    new FBXLoader().load(url, f=>{
      let single=null, forgePick=null, bronzeMat=null;
      if(place.forgeSkin){
        const brickMat=new THREE.MeshStandardMaterial({map:brickTex(), roughness:0.95, metalness:0.05, side:THREE.DoubleSide});
        const metalMat=new THREE.MeshStandardMaterial({map:metalTex(), roughness:0.6, metalness:0.65, side:THREE.DoubleSide});
        const goldMat=new THREE.MeshStandardMaterial({color:0x9a6428, roughness:0.42, metalness:0.75, side:THREE.DoubleSide});
        bronzeMat=new THREE.MeshStandardMaterial({color:0x9c6a34, roughness:0.4, metalness:0.8, side:THREE.DoubleSide});
        forgePick=n=>{ n=(n||'').toLowerCase(); if(n.indexOf('stone')>=0||n.indexOf('brick')>=0)return brickMat; if(n.indexOf('gold')>=0)return goldMat; return metalMat; };
      } else if(place.pbr){
        const tl=new THREE.TextureLoader();
        const bc=tl.load(place.pbr.base); bc.colorSpace=THREE.SRGBColorSpace; bc.flipY=true;
        const rg=tl.load(place.pbr.rough); rg.flipY=true;
        const nm=tl.load(place.pbr.normal); nm.flipY=true;
        single=()=>new THREE.MeshStandardMaterial({map:bc, roughnessMap:rg, normalMap:nm, metalness:0.6, roughness:0.85, color:place.tint||0xffffff, side:THREE.DoubleSide});
      } else {
        single=()=>new THREE.MeshBasicMaterial({color:place.color, side:THREE.DoubleSide});
      }
      f.traverse(o=>{ if(o.isMesh){
        if(place.keep && place.keep.indexOf(o.name)<0){ o.visible=false; return; }
        o.frustumCulled=false;
        if(forgePick){
          if(o.name.toLowerCase().indexOf('cauldron')>=0){ o.material=bronzeMat; }
          else { o.material = Array.isArray(o.material)? o.material.map(m=>forgePick(m&&m.name)) : forgePick(o.material&&o.material.name); }
        } else { o.material=single(); } }});
      f.updateMatrixWorld(true);
      const vb=new THREE.Box3(); f.traverse(o=>{ if(o.isMesh&&o.visible) vb.expandByObject(o); });
      const z=new THREE.Vector3(); vb.getSize(z);
      const md=Math.max(z.x,z.y,z.z); const sc=place.size/Math.max(0.05,md);
      if(!isFinite(sc)||md<=0){ return; }
      f.scale.setScalar(sc); f.rotation.y=place.ry; f.updateMatrixWorld(true);
      const vb2=new THREE.Box3(); f.traverse(o=>{ if(o.isMesh&&o.visible) vb2.expandByObject(o); });
      const ctr=new THREE.Vector3(); vb2.getCenter(ctr);
      f.position.set(place.x-ctr.x, -vb2.min.y, place.z-ctr.z);
      _avScene.add(f);
    }, undefined, e=>{});
  }

  document.getElementById('av-load-status').textContent = 'loading character...';
  try {
    const tex=new THREE.TextureLoader().load(API+'/avatar-models/mixamo/tex/atlas.png');
    tex.colorSpace=THREE.SRGBColorSpace; tex.flipY=true;
    const fbxLoader = new FBXLoader();
    const f = await new Promise((res,rej) => fbxLoader.load(API+'/avatar-models/mixamo/character.fbx', res, p => { if(p.total>0) document.getElementById('av-load-status').textContent = Math.round(p.loaded/p.total*100)+'%'; }, rej));
    const bb=new THREE.Box3().setFromObject(f); const z=new THREE.Vector3(); bb.getSize(z);
    f.scale.setScalar(1.62/Math.max(0.0001,z.y));
    f.traverse(o=>{ if(o.isMesh){ o.frustumCulled=false; o.material=new THREE.MeshBasicMaterial({map:tex, side:THREE.DoubleSide}); }});
    _avScene.add(f);
    _avXbot = f;
    _avMixer = new THREE.AnimationMixer(f);
    f.traverse(c => { if(c.name === 'mixamorig1RightHand' || c.name === 'mixamorigRightHand') _avHand = c; });
    if(f.animations.length){ _avIdle = _avMixer.clipAction(f.animations[0]); _avIdle.play(); _avCurrent = _avIdle; }
    loadProp(API+'/avatar-models/forge.fbx', {x:-1.7, z:-2.8, size:3.0, ry:0.6, forgeSkin:true});
    loadProp(API+'/avatar-models/anvil.fbx', {x:0.72, z:1.0, size:0.95, ry:1.07, keep:['Anvil'], tint:0x8f8880, pbr:{
      base:API+'/avatar-models/tex_bs/Textures/Anvil/Anvil_BaseColor.png',
      rough:API+'/avatar-models/tex_bs/Textures/Anvil/Anvil_Roughness.png',
      normal:API+'/avatar-models/tex_bs/Textures/Anvil/Anvil_Normal.png'}});
    const loading = document.getElementById('av-loading');
    if(loading){ loading.style.opacity = '0'; setTimeout(() => loading.style.display='none', 800); }
    document.getElementById('av-load-status').textContent = '';
    _avAnimate();
  } catch(e) {
    document.getElementById('av-load-status').textContent = String(e).slice(0,80);
  }
}
'''

NEW_AVANIMATE = r'''function _avAnimate() {
  if (!_avOpen) return;
  requestAnimationFrame(_avAnimate);
  const dt = _avClock.getDelta();
  if(_avMixer) _avMixer.update(dt);
  const fg = window._fg;
  if(fg){
    fg.t += dt; const t = fg.t;
    const fl = 1 + Math.sin(t*7.3)*0.15 + Math.sin(t*17.1)*0.08 + Math.random()*0.06;
    if(fg.sheenMat) fg.sheenMat.opacity = 0.5*fl;
    if(fg.bottomGlow) fg.bottomGlow.material.opacity = 0.82*fl;
    if(fg.forgeLight) fg.forgeLight.intensity = 6*fl;
    if(fg.wisps) fg.wisps.forEach(sp=>{ const u=sp.userData; u.y += u.vy*dt; const life=u.y/3.4; if(u.y>3.4) u.y=0.3;
      sp.position.set(u.x+Math.sin(t*0.4+u.sway)*0.18, u.y, u.z);
      sp.material.opacity = 0.72*Math.max(0,1-life)*(0.7+0.3*Math.sin(t*0.6+u.sway)); });
    if(fg.eg){ const p=fg.eg.attributes.position;
      for(let i=0;i<fg.N;i++){ let y=p.getY(i)+fg.es[i]*dt;
        if(y>3.4){ if(i%2){ p.setX(i,0.1+Math.random()*1.5); } else { p.setX(i,-2.4+Math.random()*1.6); } p.setZ(i,0.3-Math.random()*1.4); y=0.05; }
        p.setY(i,y); }
      p.needsUpdate=true; }
  }
  if(_avRenderer) _avRenderer.render(_avScene, _avCamera);
}
'''

# --- anchored splice: replace _avInit (up to the SPAWN marker) ---
a = s.index("async function _avInit()")
b = s.index("// ── SPAWN SYSTEM")
s = s[:a] + NEW_AVINIT + "\n\n" + s[b:]

# --- replace _avAnimate (up to _avPlayAnim) ---
c = s.index("function _avAnimate()")
d = s.index("async function _avPlayAnim")
s = s[:c] + NEW_AVANIMATE + "\n\n" + s[d:]

# --- fix GCS glyph -> flower ---
s = s.replace('">△</button>', '">\U0001f338</button>')

shutil.copy(P, P + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(P, "w", encoding="utf-8").write(s)

ok = ("window._fg" in s) and ("MeshBasicMaterial({map:tex" in s) and ("forge.fbx" in s) and ("_avStars" not in s.split("// ── SPAWN SYSTEM")[0])
print("PATCHED - forge scene restored" if ok else "PATCHED (verify markers)")
print("  skin=MeshBasic:", "MeshBasicMaterial({map:tex" in s)
print("  baked_idle:", "f.animations[0]" in s)
print("  forge+anvil:", "forge.fbx" in s and "anvil.fbx" in s)
print("  gcs_flower:", "\U0001f338</button>" in s)
