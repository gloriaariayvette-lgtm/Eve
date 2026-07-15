#!/usr/bin/env python3
"""patch_app_urls_mac.py — Mac. The two certain fixes: GCS + device-stop were using bare relative URLs
that never leave capacitor://localhost. Point them at the ${API} base (like every other authed call) and
add the X-Vintos-Secret header. Run from inside vintos-app. Backup + reversible. (T-pose/glow/keep-msgs
are separate real work — not touched here.)"""
import os, shutil, time
IDX = os.path.join(os.getcwd(), "src/index.html")
if not os.path.isfile(IDX):
    raise SystemExit("run from inside vintos-app (src/index.html not found here)")
EDITS = [
    ("fetch('/api/gcs', {method:'POST', headers:{'Content-Type':'application/json'},",
     "fetch(`${API}/api/gcs`, {method:'POST', headers:{'Content-Type':'application/json', 'X-Vintos-Secret': CONFIG.secret},"),
    ("fetch('/api/hardware/button', {method:'POST'})",
     "fetch(`${API}/api/hardware/button`, {method:'POST', headers:{'X-Vintos-Secret': CONFIG.secret}})"),
]
txt = open(IDX, encoding="utf-8").read()
applied, problems = 0, []
for old, new in EDITS:
    if new in txt:
        continue
    c = txt.count(old)
    if c != 1:
        problems.append(f"{old[:38]}… ({c}x)"); continue
    txt = txt.replace(old, new, 1); applied += 1
if problems:
    print("!! anchors not unique, nothing changed:", " | ".join(problems)); raise SystemExit(1)
if applied:
    bak = IDX + ".bak-urls-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(IDX, bak)
    open(IDX, "w", encoding="utf-8").write(txt)
    print(f"patched {applied} URL(s): GCS + device-stop now hit ${{API}} with the secret header.")
    print("backup:", bak.replace(os.path.expanduser('~'), '~'))
    print("\nRebuild in Xcode once. GCS and the stop button will reach the server now.")
else:
    print("already patched — nothing to do.")
