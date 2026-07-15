#!/usr/bin/env python3
"""recon_app2.py — Mac, READ-ONLY, bounded (no recursive glob). Dump app code for the one-rebuild batch:
GCS button, device-stop, avatar-chat reopen (keep-messages), emote/T-pose, flicker/glow/color, + API base."""
import os, re, glob
HOME = os.path.expanduser("~")
APP = os.path.join(HOME, "Vintos/vintos-app/src")
def sh(p): return p.replace(HOME, "~")

files = []
for pat in ("*.html", "*.js", "js/*.js", "scripts/*.js", "assets/*.js", "css/*.js"):
    files += glob.glob(os.path.join(APP, pat))
files = [f for f in files if "node_modules" not in f and os.path.isfile(f)]
files = sorted(set(files))[:20]
print("=== app source files (bounded) ===")
for f in files: print(f"  {sh(f):55} {os.path.getsize(f):>8}B")
if not files:
    print("  (nothing at ~/Vintos/vintos-app/src — tell me the real path)"); raise SystemExit(0)

def dump(pat, label, cap=8, ctx=1):
    print(f"\n=== {label} ===")
    n = 0
    for f in files:
        L = open(f, encoding="utf-8", errors="ignore").split("\n") if False else open(f, encoding="utf-8", errors="ignore").read().split("\n")
        for i, l in enumerate(L):
            if re.search(pat, l, re.I) and l.strip():
                for j in range(max(0, i-ctx), min(len(L), i+ctx+1)):
                    print(f"  {'>>' if j==i else '  '}{os.path.basename(f)}:{j+1}| {L[j].strip()[:104]}")
                n += 1
                if n >= cap: return

dump(r'GCS|gcs|climax', "GCS button + fetch URL")
dump(r'device.?stop|stopDevice|/stop|toy.*stop|\bstop\b.*(fetch|post|url)', "device stop URL")
dump(r'avatar.?chat|overlay.?chat|reopen|clearMessages|messages\s*=\s*\[\]|innerHTML\s*=', "avatar-chat reopen / clearing")
dump(r'emote|t-?pose|tpose|playAnim|setPose|gesture|animationName', "emote / T-pose")
dump(r'flicker|glow|forge|setColor|#[0-9a-f]{6}', "flicker / glow / color")
dump(r'const API|API\s*=|fetch\(|baseURL|https?://|Capacitor', "API base + fetch (URL-fix reference)")
