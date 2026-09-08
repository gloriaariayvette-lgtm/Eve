#!/usr/bin/env python3
"""patch_live_call_mac.py — run ON THE MAC inside the Capacitor project (e.g. vintos-repo). Finds the
index.html that has avStartVoiceCall and restores startVoiceCallWithToken + the working toggle, so the
iOS build carries the live-call fix. Auto-locates the file from the current directory. Backup.
"""
import os, re, time, shutil, glob

NEW = r'''function startVoiceCallWithToken(token, instructions){
      var ac = new (window.AudioContext||window.webkitAudioContext)({sampleRate:24000});
      ac.resume();
      navigator.mediaDevices.getUserMedia({audio:{channelCount:1}}).then(function(mic){
        var ws = new WebSocket('wss://api.x.ai/v1/realtime?model=grok-voice-latest', ['xai-client-secret.'+token]);
        window._vc = {ws:ws, ac:ac, mic:mic, playHead:0, node:null};
        ws.onopen = function(){
          ws.send(JSON.stringify({type:'session.update', session:{voice:'lux', instructions:instructions,
            turn_detection:{type:'server_vad'},
            audio:{input:{format:{type:'audio/pcm',rate:24000}}, output:{format:{type:'audio/pcm',rate:24000}}}}}));
          var s = ac.createMediaStreamSource(mic), node = ac.createScriptProcessor(4096,1,1);
          s.connect(node); node.connect(ac.destination); window._vc.node = node;
          node.onaudioprocess = function(e){ if(ws.readyState!==1) return;
            var f = e.inputBuffer.getChannelData(0), p = new Int16Array(f.length);
            for(var i=0;i<f.length;i++){var v=Math.max(-1,Math.min(1,f[i]));p[i]=v<0?v*0x8000:v*0x7fff;}
            var u=new Uint8Array(p.buffer), b=''; for(var j=0;j<u.length;j++)b+=String.fromCharCode(u[j]);
            ws.send(JSON.stringify({type:'input_audio_buffer.append', audio:btoa(b)})); };
        };
        ws.onmessage = function(ev){ var m; try{m=JSON.parse(ev.data);}catch(e){return;}
          if(m.type==='response.output_audio.delta' && m.delta){
            var str=atob(m.delta), by=new Uint8Array(str.length); for(var i=0;i<str.length;i++)by[i]=str.charCodeAt(i);
            var i16=new Int16Array(by.buffer), fl=new Float32Array(i16.length);
            for(var k=0;k<i16.length;k++)fl[k]=i16[k]/32768;
            var ab=ac.createBuffer(1,fl.length,24000); ab.getChannelData(0).set(fl);
            var bs=ac.createBufferSource(); bs.buffer=ab; bs.connect(ac.destination);
            var now=ac.currentTime; if(window._vc.playHead<now)window._vc.playHead=now;
            bs.start(window._vc.playHead); window._vc.playHead+=ab.duration;
          } else if(m.type==='response.output_audio_transcript.delta' && m.delta){
            var el=document.getElementById('av-call-transcript'); if(el) el.textContent += m.delta;
          }
        };
        ws.onclose = function(){ try{ window._vc&&window._vc.node&&window._vc.node.disconnect(); mic.getTracks().forEach(function(t){t.stop();}); }catch(e){}
          var b2=document.getElementById('av-call-btn'); if(b2) b2.style.color=''; window._vc=null; };
        ws.onerror = function(){};
      }).catch(function(e){ alert('mic error: '+e.message); var b3=document.getElementById('av-call-btn'); if(b3) b3.style.color=''; });
    }
    function endVintosCall(){ try{ if(window._vc && window._vc.ws) window._vc.ws.close(); }catch(e){} }
    function avStartVoiceCall() {
      var btn = document.getElementById('av-call-btn');
      if (window._vc && window._vc.ws) { endVintosCall(); if(btn) btn.style.color=''; return; }
      if (btn) btn.style.color = 'rgba(100,220,100,0.9)';
      var _base = (typeof API !== 'undefined' && API) ? API : '';
      var _hdrs = {}; try{ if(typeof CONFIG!=='undefined' && CONFIG.secret) _hdrs['X-Vintos-Secret']=CONFIG.secret; }catch(e){}
      fetch(_base + '/api/voice/token', {method:'POST', headers:_hdrs})
        .then(function(r){return r.json();})
        .then(function(d){ if(typeof d==='string'){try{d=JSON.parse(d);}catch(e){}}
          if(d && d.token){ startVoiceCallWithToken(d.token, d.instructions); }
          else { alert('no token from server'); if(btn) btn.style.color=''; }
        }).catch(function(e){ alert('token error: '+e.message); if(btn) btn.style.color=''; });
    }'''

pat = re.compile(r'function avStartVoiceCall\(\)\s*\{.*?\}\)\;\s*\}', re.S)

# find every html that mentions avStartVoiceCall, under cwd
cands = []
for f in glob.glob("**/*.html", recursive=True):
    if "node_modules" in f or "/ios/" in f: continue
    try: t = open(f, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    if "avStartVoiceCall" in t: cands.append(f)

if not cands:
    print("no index.html with avStartVoiceCall found under", os.getcwd())
    print("cd into your Capacitor project (the one with capacitor.config) and rerun."); raise SystemExit(1)

for f in cands:
    t = open(f, encoding="utf-8", errors="ignore").read()
    if "startVoiceCallWithToken(token, instructions)" in t:
        print("already patched:", f); continue
    new, n = pat.subn(lambda m: NEW, t)
    if n != 1:
        print("SKIP %s — matched %d avStartVoiceCall blocks (need 1)" % (f, n)); continue
    shutil.copy(f, f + ".bak-" + time.strftime("%H%M%S"))
    open(f, "w", encoding="utf-8").write(new)
    print("PATCHED", f)

print("\nnow build it:")
print("  npx cap add ios      # this repo has no ios platform yet")
print("  npx cap sync ios")
print("  npx cap open ios     # then Run in Xcode onto your phone")
