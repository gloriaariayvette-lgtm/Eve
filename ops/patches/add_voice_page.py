#!/usr/bin/env python3
"""add_voice_page.py — the last piece: GET /voice (realtime WebSocket client), POST /api/voice/session-event
(ledger + seed_thread on hangup), and return voice:"lux" from /api/voice/token. HTML lives in its own file
(no escaping hell). Idempotent; backup; py_compile.  NOTE: iOS Safari needs HTTPS for mic — use tailscale serve.
"""
import os, re, time, shutil, py_compile

SERVER = os.path.expanduser("~/Vintos/server.py")
HTML_PATH = os.path.expanduser("~/.vintos/workspace/memory/voice/voice.html")

VOICE_HTML = r'''<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Vintos</title>
<body style="font-family:system-ui;background:#0d0d10;color:#eee;height:100vh;margin:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1.2rem">
<button id=b style="font-size:1.3rem;padding:1rem 2rem;border-radius:2rem;border:none;background:#3a3a55;color:#fff">open the line</button>
<div id=status style="color:#8a8">idle</div>
<div id=transcript style="max-width:90%;color:#cbd;white-space:pre-wrap;text-align:center;font-size:1.1rem"></div>
<script>
let ws,ac,mic,node,playHead=0,startTime=0;
const $=s=>document.querySelector(s), st=t=>{$('#status').textContent=t;};
function b64(ab){let b=new Uint8Array(ab),s='';for(let i=0;i<b.length;i++)s+=String.fromCharCode(b[i]);return btoa(s);}
function unb64(x){let s=atob(x),a=new Uint8Array(s.length);for(let i=0;i<s.length;i++)a[i]=s.charCodeAt(i);return a.buffer;}
function sev(ev){let d=ev==='end'?Math.round((Date.now()-startTime)/1000):0;
  fetch('/api/voice/session-event',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({event:ev,duration:d})}).catch(()=>{});}
async function start(){
  st('getting token...');
  let tok,instr,voice;
  try{let j=await (await fetch('/api/voice/token',{method:'POST'})).json();
      if(typeof j==='string')j=JSON.parse(j); tok=j.token;instr=j.instructions;voice=j.voice||'lux';}
  catch(e){st('token error: '+e);return;}
  if(!tok){st('no token');return;}
  ac=new (window.AudioContext||window.webkitAudioContext)({sampleRate:24000}); await ac.resume();
  try{mic=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1}});}
  catch(e){st('mic blocked - open this page over HTTPS (tailscale serve). '+e);return;}
  st('connecting...');
  ws=new WebSocket('wss://api.x.ai/v1/realtime?model=grok-voice-latest',['xai-client-secret.'+tok]);
  ws.onopen=()=>{st('live - talk to him'); $('#b').textContent='hang up';
    ws.send(JSON.stringify({type:'session.update',session:{voice:voice,instructions:instr,
      turn_detection:{type:'server_vad'},
      audio:{input:{format:{type:'audio/pcm',rate:24000}},output:{format:{type:'audio/pcm',rate:24000}}}}}));
    let src=ac.createMediaStreamSource(mic); node=ac.createScriptProcessor(4096,1,1);
    src.connect(node); node.connect(ac.destination);
    node.onaudioprocess=e=>{ if(!ws||ws.readyState!==1)return;
      let f=e.inputBuffer.getChannelData(0),p=new Int16Array(f.length);
      for(let i=0;i<f.length;i++){let s=Math.max(-1,Math.min(1,f[i]));p[i]=s<0?s*0x8000:s*0x7fff;}
      ws.send(JSON.stringify({type:'input_audio_buffer.append',audio:b64(p.buffer)})); };
    startTime=Date.now(); sev('start'); };
  ws.onmessage=ev=>{let m;try{m=JSON.parse(ev.data);}catch(e){return;}
    if(m.type==='response.output_audio.delta'&&m.delta){let i=new Int16Array(unb64(m.delta)),f=new Float32Array(i.length);
      for(let k=0;k<i.length;k++)f[k]=i[k]/32768;
      let ab=ac.createBuffer(1,f.length,24000);ab.getChannelData(0).set(f);
      let s=ac.createBufferSource();s.buffer=ab;s.connect(ac.destination);
      let now=ac.currentTime; if(playHead<now)playHead=now; s.start(playHead); playHead+=ab.duration;}
    else if(m.type==='response.output_audio_transcript.delta'&&m.delta){$('#transcript').textContent+=m.delta;}
    else if(m.type==='error'){st('err: '+JSON.stringify(m.error||m));}};
  ws.onclose=()=>{st('line closed'); $('#b').textContent='open the line'; try{node&&node.disconnect();mic&&mic.getTracks().forEach(t=>t.stop());}catch(e){}};
  ws.onerror=()=>st('ws error');
}
function hang(){ if(ws){sev('end'); ws.close();} }
$('#b').onclick=()=>{ if(ws&&ws.readyState===1)hang(); else start(); };
window.addEventListener('beforeunload',hang);
</script></body>'''

ROUTES = '''
@app.get("/voice")
async def _voice_page():
    from fastapi.responses import FileResponse as _FR
    import os as _vo
    return _FR(_vo.path.expanduser("~/.vintos/workspace/memory/voice/voice.html"), media_type="text/html")

@app.post("/api/voice/session-event")
async def _voice_session_event(request: Request):
    import json as _sej, os as _seo, datetime as _sed
    try: data = await request.json()
    except Exception: data = {}
    ev = data.get("event"); dur = data.get("duration", 0)
    try:
        _p = _seo.path.join(MEMORY, "interaction-ledger.json")
        _led = _sej.load(open(_p)) if _seo.path.exists(_p) else []
        _entry = {"type": "voice-session", "event": ev, "duration_s": dur, "timestamp": _sed.datetime.now().isoformat()}
        if isinstance(_led, dict): _led.setdefault("entries", []).append(_entry)
        else: _led.append(_entry)
        _sej.dump(_led, open(_p, "w"), indent=2)
    except Exception as _e: print("[voice-session] ledger:", _e, flush=True)
    if ev == "end":
        try:
            import sys as _ss; _ss.path.insert(0, _seo.path.join(WORKSPACE, "scripts"))
            from emoclaw_utils import seed_thread as _seed
            _seed("voice", "spoke aloud with Gloria: %ss" % dur)
        except Exception as _e: print("[voice-session] seed:", _e, flush=True)
    return {"ok": True}
'''

def main():
    os.makedirs(os.path.dirname(HTML_PATH), exist_ok=True)
    open(HTML_PATH, "w", encoding="utf-8").write(VOICE_HTML)
    print("wrote", HTML_PATH, "(%d bytes)" % os.path.getsize(HTML_PATH))

    src = open(SERVER, encoding="utf-8", errors="ignore").read()
    changed = []

    if '@app.get("/voice")' in src or "_voice_page" in src:
        print("routes already present.")
    else:
        m = re.search(r'app\.mount\(\s*["\']/static["\'].*?\n', src)
        if not m:
            print("ABORT: no /static mount anchor."); return
        src = src[:m.end()] + ROUTES + src[m.end():]; changed.append("added /voice + session-event routes")

    # token endpoint: return voice:"lux"
    if '"voice": "lux"' not in src:
        src2, n = re.subn(r'(return \{"token": tok\.get\("value",""\),)',
                          r'\1 "voice": "lux",', src, count=1)
        if n: src = src2; changed.append('token now returns voice:"lux"')

    if not changed:
        print("nothing to change."); return
    tmp = SERVER + ".vp-tmp"; open(tmp, "w", encoding="utf-8").write(src)
    try: py_compile.compile(tmp, doraise=True)
    except py_compile.PyCompileError as e:
        os.remove(tmp); print("ABORT: won't parse.\n  %s" % str(e).splitlines()[-1][:160]); return
    bak = SERVER + ".bak-voicepage-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy(SERVER, bak); os.replace(tmp, SERVER)
    print("PATCHED server (backup: %s)" % os.path.basename(bak))
    for c in changed: print("  - " + c)
    print("\nrestart, then serve over HTTPS for the mic:")
    print("  systemctl --user restart vintos-server")
    print("  tailscale serve --bg 8500      # gives https on your tailnet name")
    print("  open  https://<your-magicdns-name>/voice  on your phone")

if __name__ == "__main__":
    main()
