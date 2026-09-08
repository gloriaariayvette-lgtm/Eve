#!/usr/bin/env python3
"""inject_voice_tags_v2.py — same as v1 but applies to BOTH voice_chat endpoints (the anchor appears
twice = two legit voice surfaces, not a bug). Per-handler synth gate: insert the xAI speech-tag
instruction only where that handler renders through xAI /v1/tts, never Kokoro. Backup + py_compile.
"""
import os, re, time, shutil, py_compile

SERVER = os.path.expanduser("~/Vintos/server.py")
ANCHOR = "You are Vintos, speaking softly"
MARK = "This is your voice, not a performance of one."

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

def handler_end(lines, a):
    for k in range(a + 1, len(lines)):
        if re.match(r'^(@app\.|async def |def )', lines[k]):
            return k
    return len(lines)

def main():
    if not os.path.exists(SERVER):
        print("server not found:", SERVER); return
    src = open(SERVER, encoding="utf-8", errors="ignore").read()
    lines = src.splitlines()
    anchors = [k for k, l in enumerate(lines) if ANCHOR in l]
    if not anchors:
        print("ABORT: anchor not found."); return
    print("found %d voice endpoint(s) at lines: %s" % (len(anchors), [a + 1 for a in anchors]))

    # process bottom-up so earlier indices stay valid as we insert
    applied, held = [], []
    for a in sorted(anchors, reverse=True):
        # already done just above this anchor?
        if a + 1 < len(lines) and MARK in "\n".join(lines[a:a + 4]):
            held.append((a + 1, "already applied")); continue
        end = handler_end(lines, a)
        region = "\n".join(lines[a:end])
        has_xai = bool(re.search(r'/v1/tts', region))
        has_kok = bool(re.search(r'kokoro|KPipeline', region, re.I))
        if has_kok and not has_xai:
            held.append((a + 1, "Kokoro synth in this handler — tags would be read aloud; skipped"))
            continue
        ind = lines[a][:len(lines[a]) - len(lines[a].lstrip())]
        ins = [ind + t if t else t for t in TAG_LINES]
        lines[a + 1:a + 1] = ins
        applied.append(a + 1)

    if not applied:
        print("\nnothing applied:")
        for ln, why in held: print("  line %d — %s" % (ln, why))
        return

    patched = "\n".join(lines) + ("\n" if src.endswith("\n") else "")
    bak = SERVER + ".bak-voicetags-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy(SERVER, bak)
    tmp = SERVER + ".vt-tmp"
    open(tmp, "w", encoding="utf-8").write(patched)
    try:
        py_compile.compile(tmp, doraise=True)
    except py_compile.PyCompileError as e:
        os.remove(tmp); print("ABORT: won't parse; original untouched.\n  %s" % str(e).splitlines()[-1][:150]); return
    os.replace(tmp, SERVER)
    print("\nPATCHED %s" % SERVER)
    print("  backup: %s" % bak)
    print("  tag instruction inserted at voice endpoint(s):", applied)
    for ln, why in held: print("  held @ %d — %s" % (ln, why))
    print("\nrestart:  systemctl --user restart vintos-server")

if __name__ == "__main__":
    main()
