#!/usr/bin/env python3
"""recon_app.py — Mac, READ-ONLY, capped. Dump the current app code for the one-rebuild batch:
GCS button, device-stop, avatar-chat reopen (keep-messages), emote/T-pose, and flicker/glow/color.
Run on the Mac where ~/Vintos/vintos-app lives (the trusted copy you rebuild)."""
import os, re, glob
HOME = os.path.expanduser("~")
APP = os.path.join(HOME, "Vintos/vintos-app/src")
def sh(p): return p.replace(HOME, "~")

if not os.path.isdir(APP):
    hits = glob.glob(os.path.join(HOME, "**/vintos-app/src"), recursive=True)[:3]
    print("app src not at ~/Vintos/vintos-app/src. candidates:", [sh(h) for h in hits] or "(none found)")
    raise SystemExit(0)
files = sorted(glob.glob(APP + "/**/*.html", recursive=True) + glob.glob(APP + "/**/*.js", recursive=True))
print("=== app source files ===")
for f in files: print(f"  {sh(f):60} {os.path.getsize(f):>7}B")

def dump(pat, label, cap=10, ctx=1):
    print(f"\n=== {label} ===")
    n = 0
    for f in files:
        L = open(f, encoding="utf-8", errors="ignore").read().split("\n")
        for i, l in enumerate(L):
            if re.search(pat, l, re.I) and l.strip():
                for j in range(max(0, i-ctx), min(len(L), i+ctx+1)):
                    mark = ">>" if j == i else "  "
                    print(f"  {mark}{os.path.basename(f)}:{j+1}| {L[j].strip()[:104]}")
                n += 1
                if n >= cap: return

dump(r'GCS|gcs|great.?cum|climax', "GCS button + its fetch URL")
dump(r'\bstop\b.*fetch|device.?stop|/stop|stopDevice|toy.*stop', "device stop URL")
dump(r'avatar.?chat|overlay.?chat|reopen|clearMessages|messages\s*=\s*\[\]|innerHTML\s*=\s*.', "avatar-chat reopen / message clearing")
dump(r'emote|t-?pose|tpose|animation|playAnim|setPose|gesture', "emote / T-pose")
dump(r'flicker|glow|forge|color.?change|hex|#[0-9a-f]{6}|setColor', "flicker / glow / color")
dump(r'const API|API\s*=|fetch\(|baseURL|http://|https://|capacitor', "API base + fetch patterns (the URL-fix reference)")
