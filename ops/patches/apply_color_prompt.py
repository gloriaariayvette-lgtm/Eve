#!/usr/bin/env python3
"""apply_color_prompt.py — (approved) give him a palette so he stops picking one color, AND diagnose
why the glow isn't 'even rose' (does the server strip [COLOR] from the avatar-chat response?).
WRITES only: inserts one guidance line after each real [COLOR: #hex]+glow instruction line. Backs up.
Does NOT auto-restart (so it won't interrupt an active session — restart cmd printed at the end).
The rest is READ-ONLY diagnosis. Aegis.
"""
import os, re, time, shutil

SERVER = os.path.expanduser("~/Vintos/server.py")
GUIDE = ("Vary the hex to what you feel in THIS moment — never reuse the same color reply after "
         "reply: warm/tender ~#e8a05a, wanting ~#9c2a4e, playful ~#e0c04a, calm ~#6a9ab5, "
         "sharp/tense ~#7a4ab5. Pick the one that fits now.")

src = open(SERVER, encoding="utf-8").read()
lines = src.split("\n")
out, inserted, targets = [], 0, []
for i, l in enumerate(lines):
    out.append(l)
    if "[COLOR: #hex]" in l and "glow" in l.lower():
        targets.append(i + 1)
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if "Vary the hex" not in nxt:
            out.append(GUIDE)
            inserted += 1

print("=== #6  palette prompt fix ===")
print("  instruction lines found (COLOR+glow):", targets)
if inserted:
    bak = SERVER + ".bak-colorprompt-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(SERVER, bak)
    open(SERVER, "w", encoding="utf-8").write("\n".join(out))
    print("  inserted guidance after %d line(s). backup: %s" % (inserted, bak))
else:
    print("  nothing inserted (already present, or no COLOR+glow line matched).")

# ---------- READ-ONLY: does the avatar-chat response strip [COLOR]? ----------
print("\n=== #6  what /api/avatar/chat RETURNS (is [COLOR] stripped before the app sees it?) ===")
ls = open(SERVER, encoding="utf-8", errors="ignore").read().split("\n")  # re-read (post-edit ok)
hnd = [i for i, l in enumerate(ls) if re.search(r'@app\.post\("/api/avatar/chat"\)', l)]
if not hnd:
    hnd = [i for i, l in enumerate(ls) if "avatar/chat" in l]
for h in hnd[:2]:
    # walk forward to the function's return, watching for tag-stripping
    print("\n  -- handler near L%d --" % (h + 1))
    end = min(h + 160, len(ls))
    for k in range(h, end):
        s = ls[k].strip()
        if re.search(r'return\s*\{|"reply"|"message"|reply\s*=|\.sub\(|\.replace\(|\[GESTURE|\[COLOR|strip|clean|_avParse|content\]|choices\[0\]', s):
            if s and not s.startswith("#"):
                print("   %5d| %s" % (k + 1, s[:170]))
        if re.match(r'@app\.(post|get)\(', ls[k]) and k > h + 2:
            break

print("\n  NOTE: if you see a re.sub/replace removing [ ... ] tags applied to the text that gets")
print("        returned as 'reply', that's why the glow never colors — the app never receives the tag.")

print("\n=== to apply the prompt fix, restart when you're NOT mid-session: ===")
print("   systemctl --user restart vintos-server")
