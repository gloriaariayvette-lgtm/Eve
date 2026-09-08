#!/usr/bin/env python3
"""inject_voice_tags_prompt.py — teach Vintos's VOICE generation to use xAI speech tags from felt state.

The tags ([pause][sigh][breath] <soft><whisper><emphasis>...) live inline in the text xAI voices. His
voice reply is written by grok in his voice handler, and his felt state (somatic_felt) is already in
that prompt — so he places a [sigh] where THIS sentence lands there, in realtime, per-turn. That is the
fast, correctly-clocked signal; the slow emotion_vector is never sampled for it.

Safe-by-default: finds his voice system prompt, detects how that handler SYNTHESIZES audio, and only
inserts the tag instruction if the path renders through xAI (/v1/tts) — never if it's Kokoro (which
would read "[sigh]" aloud). Backup + py_compile. Reports the wiring either way so nothing's guessed.
"""
import os, re, time, shutil, py_compile

SERVER = os.path.expanduser("~/Vintos/server.py")
ANCHOR = "You are Vintos, speaking softly"

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

def main():
    if not os.path.exists(SERVER):
        print("server not found:", SERVER); return
    src = open(SERVER, encoding="utf-8", errors="ignore").read()
    if "This is your voice, not a performance of one." in src:
        print("already applied — voice-tag instruction present."); return
    lines = src.splitlines()

    idx = [k for k, l in enumerate(lines) if ANCHOR in l]
    if len(idx) != 1:
        print("ABORT: anchor %r found %d times (need exactly 1) — no edit." % (ANCHOR, len(idx))); return
    a = idx[0]

    # bound the voice handler: from the anchor to the next top-level def/@app
    end = len(lines)
    for k in range(a + 1, len(lines)):
        if re.match(r'^(@app\.|async def |def )', lines[k]):
            end = k; break
    region = "\n".join(lines[a:end])
    has_xai = bool(re.search(r'/v1/tts|api\.x\.ai/v1/tts|v1/tts', region)) or bool(re.search(r'/v1/tts', src))
    has_kok = bool(re.search(r'kokoro|KPipeline', region, re.I))

    print("voice handler synth detected: xAI /v1/tts=%s | Kokoro=%s" % (has_xai, has_kok))

    if has_kok and not re.search(r'/v1/tts', region):
        print("\nHOLDING — this voice handler synthesizes through Kokoro, which would READ the tags aloud")
        print("instead of performing them. Not inserting. Point me at where his xAI voice is wired and")
        print("I'll add the prompt there. Kokoro line(s) in this handler:")
        for k in range(a, end):
            if re.search(r'kokoro|KPipeline', lines[k], re.I):
                print("  %5d: %s" % (k + 1, lines[k].strip()[:140]))
        return

    ind = lines[a][:len(lines[a]) - len(lines[a].lstrip())]
    ins = [ind + t if t else t for t in TAG_LINES]
    new = lines[:a + 1] + ins + lines[a + 1:]
    patched = "\n".join(new) + ("\n" if src.endswith("\n") else "")

    bak = SERVER + ".bak-voicetags-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy(SERVER, bak)
    tmp = SERVER + ".vt-tmp"
    open(tmp, "w", encoding="utf-8").write(patched)
    try:
        py_compile.compile(tmp, doraise=True)
    except py_compile.PyCompileError as e:
        os.remove(tmp); print("ABORT: patched server won't parse; original untouched.\n  %s"
                              % str(e).splitlines()[-1][:150]); return
    os.replace(tmp, SERVER)
    print("\nPATCHED %s" % SERVER)
    print("  backup: %s" % bak)
    print("  voice-tag instruction inserted into his voice prompt (after the 'speaking softly' anchor)")
    print("  he'll now place [sigh]/<soft>/[pause] from what he feels in the moment; xAI voices them")
    print("\nrestart to load:  systemctl --user restart vintos-server")

if __name__ == "__main__":
    main()
