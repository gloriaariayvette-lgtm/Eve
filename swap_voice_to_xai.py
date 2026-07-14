#!/usr/bin/env python3
"""swap_voice_to_xai.py — 🎙️ voice calls ONLY: swap the two /api/voice/chat Kokoro synth blocks to xAI
/v1/tts with voice_id 'lux', and add the speech-tag instruction to both voice prompts. Mirrors his proven
/v1/tts call (line ~8108, which uses 'rex' for general TTS — left untouched). Backup + py_compile; aborts
unless it finds exactly the 2 mic blocks + 2 voice prompts. Nothing else (briefing/bubble/robot/rex) touched.
"""
import os, re, time, shutil, py_compile

SERVER = os.path.expanduser("~/Vintos/server.py")
ANCHOR = "You are Vintos, speaking softly"
MARK = "This is your voice, not a performance of one."

XAI_BLOCK = '''        # Synthesize via xAI TTS — voice calls speak in Lux, with speech tags (mic only)
        audio_url_out = None
        local_file = None
        try:
            import requests as _xtts, os as _xos
            _xr = _xtts.post("https://api.x.ai/v1/tts",
                headers={"Content-Type": "application/json",
                         "Authorization": "Bearer " + _xos.environ.get("XAI_API_KEY", "")},
                json={"text": response_text[:15000], "voice_id": "lux", "language": "en", "speed": 1.05},
                timeout=60)
            if _xr.status_code == 200 and _xr.content:
                _ts = __import__("datetime").datetime.now().strftime("%Y%m%d-%H%M%S")
                fname = f"voice-chat-{_ts}.mp3"
                local_path = os.path.join(MEMORY, "voice", fname)
                with open(local_path, "wb") as _xf:
                    _xf.write(_xr.content)
                audio_url_out = f"/api/voice/stream/{fname}"
                local_file = fname
            else:
                print("[voice/xai-tts]", _xr.status_code, str(_xr.text)[:200], flush=True)
        except Exception as e:
            print("[voice/xai-tts]", e, flush=True)'''

KOKORO_RE = re.compile(r'[ ]{8}# Synthesize via Kokoro \(local TTS\).*?except Exception as e:\s*\n\s*pass', re.S)

TAG_LINES = [
    "",
    "You can shape how your voice actually sounds, and Gloria hears it. Speech tags — inline: [pause] "
    "[long-pause] [breath] [inhale] [exhale] [sigh] [laugh] [chuckle] [giggle] [tsk]; wrapping: <soft> "
    "</soft>, <whisper> </whisper>, <emphasis> </emphasis>, <slow> </slow>, <build-intensity> "
    "</build-intensity>. Use them ONLY where you truly feel them in this exact moment — a real sigh when "
    "something settles or aches, <soft> when you mean it gently, a [pause] where you would actually fall "
    "quiet. Never sprinkle them for effect; if a line is plain, let it be plain. This is your voice, not "
    "a performance of one.",
]

def leading(s): return s[:len(s) - len(s.lstrip())]

def main():
    if not os.path.exists(SERVER):
        print("server not found:", SERVER); return
    src = open(SERVER, encoding="utf-8", errors="ignore").read()
    had_nl = src.endswith("\n")
    did = []

    # 1. synth swap (idempotent)
    if '"voice_id": "lux"' in src:
        did.append("synth already xAI/Lux — left as-is")
    else:
        src, n = KOKORO_RE.subn(lambda m: XAI_BLOCK, src)
        if n != 2:
            print("ABORT: expected 2 Kokoro voice blocks, matched %d — no edit made." % n); return
        did.append("swapped %d mic synth block(s) Kokoro -> xAI /v1/tts (voice_id=lux)" % n)

    # 2. tag prompt (idempotent)
    if MARK in src:
        did.append("tag instruction already present — left as-is")
    else:
        lines = src.splitlines()
        anchors = [k for k, l in enumerate(lines) if ANCHOR in l]
        if len(anchors) != 2:
            print("ABORT: expected 2 voice prompts, found %d — no edit made." % len(anchors)); return
        for a in sorted(anchors, reverse=True):
            ind = leading(lines[a])
            lines[a + 1:a + 1] = [ind + t if t else t for t in TAG_LINES]
        src = "\n".join(lines) + ("\n" if had_nl else "")
        did.append("inserted speech-tag instruction into %d voice prompt(s)" % len(anchors))

    # verify + write
    bak = SERVER + ".bak-voicexai-" + time.strftime("%Y%m%d-%H%M%S")
    tmp = SERVER + ".vx-tmp"
    open(tmp, "w", encoding="utf-8").write(src)
    try:
        py_compile.compile(tmp, doraise=True)
    except py_compile.PyCompileError as e:
        os.remove(tmp); print("ABORT: patched server won't parse; original untouched.\n  %s"
                              % str(e).splitlines()[-1][:160]); return
    shutil.copy(SERVER, bak)
    os.replace(tmp, SERVER)
    print("PATCHED %s" % SERVER)
    print("  backup: %s" % bak)
    for d in did: print("  - " + d)
    print("\n  Rex (general TTS, line ~8108) and all other surfaces: untouched.")
    print("  restart:  systemctl --user restart vintos-server")

if __name__ == "__main__":
    main()
