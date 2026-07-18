#!/usr/bin/env python3
"""recon_wants_creative.py — Aegis, READ-ONLY. #3 (image/poem 'didn't work') and #5 (force a music want) are both
want-driven creation. This morning I edited his LIVE wants-router.py (patch_tell_gloria_live). Check I didn't break
creative dispatch: compile the live router, show ACTION_MAP creative entries, route_want dispatch, the creative
action fns (make_art/write_poem/make_music/animate_painting), and the exact region my tell_gloria patch changed.
Plus: pending creative wants + recent router-log errors. His live router = ~/Vintos/wants-router.py. Nothing written."""
import os, re, json, glob, time
VIN = os.path.expanduser("~/Vintos")
MEM = os.path.expanduser("~/.vintos/workspace/memory")
P = os.path.join(VIN, "wants-router.py")

print("== (1) live wants-router.py: exists + compiles? ==")
if not (os.path.isfile(P) or os.path.islink(P)):
    print("  !! not found at %s" % P); raise SystemExit(1)
real = os.path.realpath(P)
t = open(real, encoding="utf-8", errors="ignore").read()
print("  path: %s%s (%d lines)" % (P, ("  -> " + real) if os.path.islink(P) else "", len(t.split(chr(10)))))
try:
    compile(t, real, "exec"); print("  compiles: OK")
except SyntaxError as e:
    print("  !! COMPILE FAIL: %s  <== THIS is the break" % e)
L = t.split("\n")

print("\n== (2) ACTION_MAP — creative capabilities wired? ==")
for i, l in enumerate(L):
    if re.search(r'ACTION_MAP|make_art|write_poem|make_music|make_video|animate_painting|creative_write|"art"|"poem"|"music"', l):
        print("  %4d: %s" % (i + 1, l.strip()[:100]))

print("\n== (3) the creative action functions (def) ==")
for i, l in enumerate(L):
    if re.match(r'\s*def (make_art|write_poem|make_music|make_video|animate_painting|creative_write)', l):
        print("  %4d: %s" % (i + 1, l.strip()[:100]))
        # show a few lines of body (how it invokes the generator)
        for j in range(i + 1, min(i + 8, len(L))):
            if re.search(r'subprocess|Popen|run\(|python3|\.py|dream-art|dream_music|dream-poetry|dream_poetry|return', L[j]):
                print("        %4d: %s" % (j + 1, L[j].strip()[:96]))

print("\n== (4) route_want dispatch + the tell_gloria region I patched ==")
for i, l in enumerate(L):
    if re.search(r'def route_want|action_fn\s*=|action_fn\(|ACTION_MAP\.get|_is_communicative|def tell_gloria|journal_seeded|FORCED_WANT_TOPIC', l):
        print("  %4d: %s" % (i + 1, l.strip()[:100]))

print("\n== (5) pending creative wants in current-wants.json ==")
try:
    cw = json.load(open(os.path.join(MEM, "current-wants.json")))
    items = cw if isinstance(cw, list) else cw.get("wants", [])
    crea = [w for w in items if isinstance(w, dict) and re.search(r'art|poem|music|paint|image|draw|compose|video|animate', str(w.get("want", "")) + str(w.get("capability", "")), re.I)]
    print("  total wants: %d | creative-ish: %d" % (len(items), len(crea)))
    for w in crea[:6]:
        print("     - %s | cap=%s status=%s" % (str(w.get("want", ""))[:60], w.get("capability", "?"), w.get("status", "?")))
except Exception as e:
    print("  (current-wants unreadable: %s)" % e)

print("\n== (6) recent wants-router log (errors after my morning edit?) ==")
now = time.time()
for lg in sorted(glob.glob("/tmp/*want*") + glob.glob(os.path.expanduser("~/.vintos/logs/*want*")), key=lambda p: -os.path.getmtime(p))[:3]:
    print("  %s (%.1fh ago):" % (lg, (now - os.path.getmtime(lg)) / 3600))
    try:
        for l in open(lg, encoding="utf-8", errors="ignore").read().strip().split("\n")[-6:]:
            print("     " + l[:110])
    except Exception: pass

print("\n(READ-ONLY. If the router miscompiles or creative dispatch is broken, that's what my edit did — and gets fixed.)")
