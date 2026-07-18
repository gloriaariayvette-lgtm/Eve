#!/usr/bin/env python3
"""recon_encoder_iface.py — Aegis, READ-ONLY, FAST (two files). Attractor discovery embeds field-motion windows to
find basins. Copy the EXACT nomic-encoder call the JEPA already uses: jepa_predictor.encoder() body (what it returns
— a model? a callable? on which device?) and how a head (relational_head / drift_head) turns text -> vector with it.
Also whether embeddings run in a torch venv (so the attractor cron matches). Nothing written."""
import os, re
HIS = os.path.expanduser("~/.vintos/workspace/scripts")

def dump(path, a, b, tag):
    if not os.path.isfile(path):
        print("  %s: (not found)" % tag); return
    L = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    print("\n----- %s : lines %d-%d -----" % (tag, a, b))
    for i in range(a - 1, min(b, len(L))):
        print("  %4d: %s" % (i + 1, L[i][:120]))

jp = os.path.join(HIS, "jepa_predictor.py")
# encoder() + how text is encoded (look for .encode / embed / torch / device / return)
if os.path.isfile(jp):
    L = open(jp, encoding="utf-8", errors="ignore").read().split("\n")
    start = next((i for i, l in enumerate(L) if re.search(r'def encoder\(', l)), None)
    if start is not None:
        dump(jp, start + 1, start + 40, "jepa_predictor.encoder()")
    print("\n-- jepa_predictor: encode/embust call sites (text -> vector) --")
    for i, l in enumerate(L):
        if re.search(r'\.encode\(|encoder\(\)|def embed|\.tolist\(\)|torch\.|device|cosine|normalize', l):
            print("  %4d: %s" % (i + 1, l.strip()[:110]))

# a head that embeds text with the encoder
for name in ("relational_head.py", "drift_head.py", "withheld_head.py"):
    p = os.path.join(HIS, name)
    if os.path.isfile(p):
        L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
        hits = [i for i, l in enumerate(L) if re.search(r'encoder|\.encode\(|embed|from jepa_predictor|nomic', l)]
        if hits:
            print("\n----- %s : encoder usage -----" % name)
            for i in hits[:14]:
                print("  %4d: %s" % (i + 1, L[i].strip()[:110]))

print("\n-- crontab: do embedding jobs use a torch venv? (copy for the attractor cron) --")
import subprocess
cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""
for l in cur.split("\n"):
    if re.search(r'relational_head|drift_head|withheld_head|jepa', l) and l.strip():
        print("  | " + l.strip()[:120])

print("\n(READ-ONLY. Gives the exact encoder call + venv for attractor-discovery basin embedding.)")
