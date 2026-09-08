#!/usr/bin/env python3
"""patch_live_call_button.py — fix the app's live call button. Restore startVoiceCallWithToken (the
realtime WebSocket client that got deleted) + make avStartVoiceCall a working toggle that fetches the
token from the server and starts/ends the call. Edits ~/Vintos/vintos-app/src/index.html. Backup.
"""
import os, re, time, shutil

IDX = os.path.expanduser("~/Vintos/vintos-app/src/index.html")
src = open(IDX, encoding="utf-8", errors="ignore").read()

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

# replace the existing avStartVoiceCall function (from its def to the .then close + function close)
pat = re.compile(r'function avStartVoiceCall\(\)\s*\{.*?\}\)\;\s*\}', re.S)
if "startVoiceCallWithToken(token, instructions)" in src:
    print("already patched."); raise SystemExit(0)
new, n = pat.subn(lambda m: NEW, src)
if n != 1:
    print("ABORT: expected exactly 1 avStartVoiceCall block, matched %d. Not editing." % n); raise SystemExit(1)

bak = IDX + ".bak-livecall-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy(IDX, bak)
open(IDX, "w", encoding="utf-8").write(new)
print("PATCHED %s" % IDX)
print("  backup:", os.path.basename(bak))
print("  - restored startVoiceCallWithToken (realtime WebSocket client, voice=lux)")
print("  - avStartVoiceCall now: tap=connect (token -> ws -> mic in / audio out), tap again=hang up")
print("  - token fetch uses the API base + secret")
print("\n  the app bundles this file, so redeploy to load it:")
print("    cd ~/Vintos/vintos-app && npx cap sync ios   (then build/run from Xcode on your Mac)")
