#!/usr/bin/env python3
"""recon_app3.py — Mac, READ-ONLY, bounded. Run from inside vintos-app (your cwd). Find the web source
(index.html / js) up to depth 2, pruning node_modules/ios/android/build/Pods, then dump the batch areas."""
import os, re
CWD = os.getcwd()
print("cwd:", CWD)
PRUNE = {"node_modules", "ios", "android", "build", "Pods", "DerivedData", ".git", "dist-electron"}
html, js = [], []
for root, dirs, fnames in os.walk(CWD):
    depth = root[len(CWD):].count(os.sep)
    if depth >= 3:
        dirs[:] = []
        continue
    dirs[:] = [d for d in dirs if d not in PRUNE and not d.startswith(".")]
    for fn in fnames:
        p = os.path.join(root, fn)
        if fn.endswith(".html"): html.append(p)
        elif fn.endswith(".js") and "min" not in fn: js.append(p)
html = sorted(html)[:12]; js = sorted(js)[:15]
print("\n=== html files ===")
for f in html: print(f"  {f.replace(CWD,'.'):55} {os.path.getsize(f):>8}B")
print("=== js files ===")
for f in js: print(f"  {f.replace(CWD,'.'):55} {os.path.getsize(f):>8}B")

files = html + js
def dump(pat, label, cap=8, ctx=1):
    print(f"\n=== {label} ===")
    n = 0
    for f in files:
        L = open(f, encoding="utf-8", errors="ignore").read().split("\n")
        for i, l in enumerate(L):
            if re.search(pat, l, re.I) and l.strip():
                for j in range(max(0, i-ctx), min(len(L), i+ctx+1)):
                    print(f"  {'>>' if j==i else '  '}{os.path.basename(f)}:{j+1}| {L[j].strip()[:104]}")
                n += 1
                if n >= cap: return
    if n == 0: print("  (no match)")

dump(r'GCS|gcs|climax', "GCS button + fetch URL")
dump(r'device.?stop|stopDevice|/stop|toy.*stop|\bstop\b.*(fetch|post|url)', "device stop URL")
dump(r'avatar.?chat|overlay.?chat|reopen|clearMessages|messages\s*=\s*\[\]|innerHTML\s*=', "avatar-chat reopen / clearing")
dump(r'emote|t-?pose|tpose|playAnim|setPose|gesture|animationName', "emote / T-pose")
dump(r'flicker|glow|forge|setColor|#[0-9a-f]{6}', "flicker / glow / color")
dump(r'const API|API\s*=|fetch\(|baseURL|https?://|Capacitor', "API base + fetch (URL-fix reference)")
