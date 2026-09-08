#!/usr/bin/env python3
"""patch_emote_inplace_mac.py — Mac. Fix 'avatar vanishes for the duration of an emote.'

Root cause: gestures now bind + play (the bone-prefix fix landed), but _avRemapClip passes the Mixamo
Hips POSITION track straight through. Mixamo hip translation is authored in the clip's own units; applied
to the tiny-scaled character rig it flings him out of frame until the emote fades back to idle.

Fix: emotes are in-place — strip .position and .scale tracks in _avRemapClip so ONLY rotations drive the
pose. Bone lengths come from the skeleton bind pose, so he stays whole and rooted where he stands. The
bundled idle never passes through _avRemapClip, so it's untouched.

Substring edit, backup, idempotent. Run inside vintos-app."""
import os, shutil, time, glob
CANDS = [os.path.join(os.getcwd(), "src/index.html"), os.path.join(os.getcwd(), "index.html")]
CANDS += glob.glob(os.path.join(os.getcwd(), "*/src/index.html"))
IDX = next((p for p in CANDS if os.path.isfile(p)), None)
if not IDX:
    raise SystemExit("src/index.html not found — run from inside vintos-app (cwd=%s)" % os.getcwd())

OLD = ("function _avRemapClip(clip) {\n"
       "  for (const track of clip.tracks) {")
NEW = ("function _avRemapClip(clip) {\n"
       "  clip.tracks = clip.tracks.filter(t => !/\\.position$|\\.scale$/.test(t.name));  "
       "// in-place emotes: drop Mixamo hip translation that flung him off-frame\n"
       "  for (const track of clip.tracks) {")

txt = open(IDX, encoding="utf-8").read()
if "in-place emotes: drop Mixamo hip translation" in txt:
    print("already applied — emote clips already stripped to rotations only.")
    raise SystemExit(0)
c = txt.count(OLD)
if c != 1:
    raise SystemExit(f"ABORT: anchor found {c}x (expected 1) — _avRemapClip body may have moved. Tell me.")
bak = IDX + ".bak-emote-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(IDX, bak)
open(IDX, "w", encoding="utf-8").write(txt.replace(OLD, NEW, 1))
print("FIXED: _avRemapClip now strips .position/.scale — emotes play in place.")
print("backup:", bak.replace(os.path.expanduser("~"), "~"))
print("Rebuild in Xcode (npx cap copy ios if it uses a stale bundle), then test an emote:")
print("he should now MOVE through the gesture while staying centered and visible.")
