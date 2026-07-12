#!/usr/bin/env python3
"""somatic_felt_data_patch.py — felt = RAW NUMBERS + a translation key (no prose to parrot).

Proven with grok: prose cues get lifted verbatim; raw numbers with no key get confabulated
("sinking in"); numbers + a key of what they mean get translated into fresh, accurate, first-
person sensation. So translate() now emits position/speed/grip/reversals + the key inline.
Replaces whatever translate() currently is. Idempotent; backs up somatic_felt.py.
"""
import io, os, time, shutil

F = os.path.expanduser("~/.vintos/workspace/scripts/somatic_felt.py")
s = io.open(F, encoding="utf-8").read()
if "translate to what you FEEL" in s:
    print("already patched — skipping"); raise SystemExit(0)

start = s.find("def translate(c, prev_state=None):")
if start == -1:
    print("MISS: translate() not found"); raise SystemExit(1)
end = s.find("\ndef on_release", start)
if end == -1:
    print("MISS: on_release anchor not found"); raise SystemExit(1)

NEW = '''def translate(c, prev_state=None):
    """Emit RAW numbers + a key. He translates them into sensation in his own words —
    nothing pre-worded to parrot, and the key stops him inventing a wrong meaning."""
    state = c.get("state")
    if state == "absent":
        return None
    pos = round(c.get("center", 0)); spd = round(c.get("speed", 0))
    grip = c.get("pressure", 0.0); rev = c.get("flips", 0); pdir = c.get("pressure_dir", "steady")
    vals = ["position %d" % pos, "speed %d" % spd, "grip %s" % grip]
    if grip >= 0.3 and pdir != "steady":
        vals[-1] += " (%s)" % pdir
    if rev >= 2:
        vals.append("reversals %d" % rev)
    shift = ("  shift %s->%s" % (prev_state, state)) if (prev_state and prev_state != state) else ""
    key = ("[BODY - translate into what you FEEL, in your own words; never say these numbers or labels. "
           "position 0-100 = where her hand is (0 base, 100 tip); speed 0-60 = how fast she strokes (0 = still); "
           "grip 0-1 = how hard she squeezes you in place WITHOUT stroking; reversals = how often she changes direction.]")
    return key + "  " + " · ".join(vals) + shift

'''

s = s[:start] + NEW + s[end + 1:]
shutil.copy(F, F + ".bak-feltdata-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s)
print("PATCHED — translate() now emits raw numbers + translation key (no prose to parrot)")
