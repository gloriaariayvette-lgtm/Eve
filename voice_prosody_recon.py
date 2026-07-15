#!/usr/bin/env python3
"""voice_prosody_recon.py — Aegis, READ-ONLY, capped. Spark: expressive voice tags <- felt state.
Before wiring, answer the spark's open Q: which TTS path is LIVE (local voice_kokoro vs hosted builder /
x.ai tts), and where the felt state can be injected as a post-generation prosody pass. Map the bridge:
voice_somatic_driver / voice_somatic_loop / somatic_felt, the emotion socket, and where the spoken line
is finalized. No writes, no secrets."""
import os, re, glob, subprocess
HOME = os.path.expanduser("~")
V = os.path.join(HOME, ".vintos")
WS = os.path.join(V, "workspace")
def sh(p): return p.replace(HOME, "~")
def find(pats):
    out = []
    for base in (os.path.join(WS, "scripts"), os.path.join(HOME, "Vintos"), WS):
        for pat in pats:
            out += glob.glob(os.path.join(base, pat))
    return sorted({f for f in out if os.path.isfile(f)})

print("=== voice/TTS/somatic files present ===")
files = find(["*voice*", "*kokoro*", "*tts*", "*somatic*", "*prosody*", "*speak*"])
for f in files[:30]:
    print(f"  {sh(f):66} {os.path.getsize(f):>7}B")

print("\n=== which TTS is LIVE? (kokoro vs hosted builder vs x.ai/tts) ===")
hits = subprocess.run(["bash","-lc",
    f"grep -rilE 'kokoro|/v1/tts|api\\.x\\.ai.*tts|elevenlabs|hosted|tts_provider|voice_builder' "
    f"{WS} {os.path.join(HOME,'Vintos')} 2>/dev/null | grep -viE '\\.pyc|\\.bak|node_modules' | head -12"],
    capture_output=True, text=True).stdout.strip()
print("  " + (hits.replace(HOME,'~').replace(chr(10),'\n  ') or "(no TTS provider references found)"))

print("\n=== is voice chat wired to a running service? (systemd / ports) ===")
svc = subprocess.run(["bash","-lc","systemctl --user list-units --type=service 2>/dev/null | grep -iE 'voice|tts|kokoro|somatic' | head"],
                     capture_output=True, text=True).stdout.strip()
print("  services:", svc.replace(chr(10),'  ') or "(none named voice/tts/kokoro/somatic)")

print("\n=== the somatic->voice bridge: where felt state meets the spoken line ===")
for name in ("voice_somatic_driver.py", "voice_somatic_loop.py", "somatic_felt.py"):
    p = None
    for base in (os.path.join(WS,"scripts"), os.path.join(HOME,"Vintos"), WS):
        if os.path.isfile(os.path.join(base,name)): p = os.path.join(base,name); break
    if not p:
        print(f"  -- {name}: (not found)"); continue
    print(f"  -- {name} ({sh(p)}) --")
    n = 0
    for i, l in enumerate(open(p, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(r'tag|prosody|\[sigh\]|\[breath\]|<soft>|<whisper>|emotion|felt|nudge|state\[|dim|tts|speak|kokoro|/v1/tts|socket', l, re.I) \
           and l.strip() and not l.strip().startswith("#"):
            print(f"     {i+1:4}| {l.strip()[:112]}"); n += 1
            if n >= 12: break

print("\n=== emotion socket / 11-dim source the prosody pass would read ===")
es = subprocess.run(["bash","-lc",
    f"grep -rlE 'Vintos-emotion\\.sock|emotion_model|process_message|Valence.*Arousal|11.dim' "
    f"{WS} {os.path.join(HOME,'Vintos')} 2>/dev/null | grep -viE '\\.pyc|\\.bak' | head -6"],
    capture_output=True, text=True).stdout.strip()
print("  " + (es.replace(HOME,'~').replace(chr(10),'\n  ') or "(none)"))

print("\n=== the expressive-tag vocabulary — is it defined anywhere already? ===")
tg = subprocess.run(["bash","-lc",
    f"grep -rlE '\\[long-pause\\]|build-intensity|laugh-speak|sing-song|<whisper>' "
    f"{WS} {os.path.join(HOME,'Vintos')} 2>/dev/null | grep -viE '\\.pyc|\\.bak' | head"],
    capture_output=True, text=True).stdout.strip()
print("  tag vocab referenced in:", tg.replace(HOME,'~').replace(chr(10),'  ') or "(nowhere yet — this spark introduces it)")
