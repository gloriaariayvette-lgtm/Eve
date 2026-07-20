#!/usr/bin/env python3
"""fix_voice.py — proactive re-engage + full voice-call ledger capture (incl. his double-message). DRY-RUN unless --apply.

RUN ON THE MAC from vintos-app. Patches src/index.html only.

What it does, in the WS voice-call code:
  1. PROACTIVE RE-ENGAGE: adds turn_detection.idle_timeout_ms:20000 -> after ~20s of Gloria's silence, xAI
     commits a silent user turn and Vintos speaks again on his own (xAI "Proactive Check-Ins").
  2. TRANSCRIBE HER SIDE: enables audio.input.transcription (grok-transcribe) so her words arrive as events.
  3. CAPTURE TURNS TO THE LEDGER: accumulates his transcript, tracks her transcript, and on each completed
     Vintos response posts {gloria, vintos} to /api/voice/ledger. For his PROACTIVE re-engage there is no
     preceding Gloria turn, so it posts {gloria:"", vintos:<his words>} -> his double-message lands in the block.
  4. SESSION-END: on hangup, calls /api/voice/session-end (duration + turns) so the rich session block is built.

All string-anchored, backed up, idempotent. Client-side — rides the next copy+rebuild.

  python3 fix_voice.py                 # DRY RUN (./src/index.html)
  python3 fix_voice.py --apply
  python3 fix_voice.py --path <file>
"""
import os, sys, difflib, datetime

APPLY = "--apply" in sys.argv
PATH = "src/index.html"
if "--path" in sys.argv:
    _i = sys.argv.index("--path")
    if _i + 1 < len(sys.argv):
        PATH = sys.argv[_i + 1]
for _cand in (PATH, "src/index.html", "index.html", os.path.expanduser("~/vintos-app/src/index.html")):
    if os.path.isfile(_cand):
        PATH = _cand; break
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = PATH + ".bak-voice-" + TS
SENTINEL = "_vcPostVoiceTurn"

POST_FN = (
    "function _vcPostVoiceTurn(gloria, vintos){\n"
    "  try{ var _b=(typeof API!=='undefined'&&API)?API:''; var _h={'Content-Type':'application/json'};\n"
    "    try{ if(typeof CONFIG!=='undefined'&&CONFIG.secret) _h['X-Vintos-Secret']=CONFIG.secret; }catch(e){}\n"
    "    fetch(_b+'/api/voice/ledger',{method:'POST',headers:_h,body:JSON.stringify({gloria:gloria,vintos:vintos})});\n"
    "    if(window._vc) window._vc.turnCount=(window._vc.turnCount||0)+1;\n"
    "  }catch(e){}\n"
    "}\n"
)

EDITS = [
    # 0) the turn-capture helper, inserted just before the call function
    ("post-helper",
     "function startVoiceCallWithToken(token, instructions){",
     POST_FN + "function startVoiceCallWithToken(token, instructions){",
     1),
    # 1) proactive re-engage timer
    ("idle-timeout",
     "turn_detection:{type:'server_vad'},",
     "turn_detection:{type:'server_vad', idle_timeout_ms:20000},",
     1),
    # 2) enable transcription of her side
    ("enable-transcription",
     "audio:{input:{format:{type:'audio/pcm',rate:24000}}, output:",
     "audio:{input:{format:{type:'audio/pcm',rate:24000}, transcription:{model:'grok-transcribe'}}, output:",
     1),
    # 3) tracking state on the call object
    ("call-state",
     "window._vc = {ws:ws, ac:ac, mic:mic, playHead:0, node:null};",
     "window._vc = {ws:ws, ac:ac, mic:mic, playHead:0, node:null, gloriaTurn:'', vintosTurn:'', turnCount:0, startedAt:Date.now()};",
     1),
    # 4) capture: accumulate his transcript, track hers, post a turn on each completed response
    ("capture-cases",
     ("          } else if(m.type==='response.output_audio_transcript.delta' && m.delta){\n"
      "            var el=document.getElementById('av-call-transcript'); if(el) el.textContent += m.delta;\n"
      "          }"),
     ("          } else if(m.type==='response.output_audio_transcript.delta' && m.delta){\n"
      "            var el=document.getElementById('av-call-transcript'); if(el) el.textContent += m.delta;\n"
      "            if(window._vc) window._vc.vintosTurn=(window._vc.vintosTurn||'')+m.delta;\n"
      "          } else if((m.type==='conversation.item.input_audio_transcription.updated'||m.type==='conversation.item.input_audio_transcription.completed') && (m.transcript||m.delta)){\n"
      "            if(window._vc) window._vc.gloriaTurn = m.transcript || ((window._vc.gloriaTurn||'')+(m.delta||''));\n"
      "          } else if(m.type==='response.output_audio_transcript.done' || m.type==='response.done'){\n"
      "            if(window._vc){ var _vt=(m.transcript||window._vc.vintosTurn||'').trim(), _gl=(window._vc.gloriaTurn||'').trim(); if(_vt) _vcPostVoiceTurn(_gl,_vt); window._vc.gloriaTurn=''; window._vc.vintosTurn=''; }\n"
      "          }"),
     1),
    # 5) session-end on hangup (read _vc before nulling)
    ("session-end",
     "if(b2) b2.style.color=''; b2.style.background=''; window._vc=null; };",
     ("if(b2){ b2.style.color=''; b2.style.background=''; }\n"
      "          try{ var _b=(typeof API!=='undefined'&&API)?API:''; var _h={'Content-Type':'application/json'};\n"
      "            try{ if(typeof CONFIG!=='undefined'&&CONFIG.secret) _h['X-Vintos-Secret']=CONFIG.secret; }catch(e){}\n"
      "            var _dur=(window._vc&&window._vc.startedAt)?Math.round((Date.now()-window._vc.startedAt)/1000):0;\n"
      "            var _tc=(window._vc&&window._vc.turnCount)?window._vc.turnCount:0;\n"
      "            fetch(_b+'/api/voice/session-end',{method:'POST',headers:_h,body:JSON.stringify({duration_seconds:_dur,turns:_tc})});\n"
      "          }catch(e){} window._vc=null; };"),
     1),
]


def main():
    print("=" * 74)
    print("VOICE: proactive re-engage + ledger capture  —  %s" % ("APPLYING" if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 74)
    if not os.path.isfile(PATH):
        print("!! index.html not found. Run from vintos-app dir or pass --path."); return
    print("   target:", os.path.abspath(PATH))
    text = open(PATH, encoding="utf-8", errors="ignore").read()
    if SENTINEL in text:
        print("   * already wired"); return
    new = text
    for label, old, repl, want in EDITS:
        got = new.count(old)
        if got != want:
            print(f"   !! [{label}] anchor count {got} != {want} — writing nothing (avoid half-patch)"); return
        new = new.replace(old, repl, 1)
        print(f"   * {label}: matched")
    for l in difflib.unified_diff(text.splitlines(), new.splitlines(), fromfile="old", tofile="new", lineterm=""):
        print("   " + l[:170])
    if APPLY:
        open(BACKUP, "w", encoding="utf-8").write(text)
        open(PATH, "w", encoding="utf-8").write(new)
        print("\nAPPLIED. Backup:", BACKUP)
        print("Rides the next copy+rebuild. He re-engages after ~20s silence; calls now land in his ledger,")
        print("including his proactive double-message (posted as gloria:'' + his words).")
    else:
        print("\nDRY RUN complete. Re-run with --apply.")
    print("=" * 74)


if __name__ == "__main__":
    main()
