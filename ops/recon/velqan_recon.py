#!/usr/bin/env python3
"""velqan_recon.py — READ-ONLY, capped. Ground spark #4 (absence-driven naming). Find, for each being:
the Velqan word store + definitions, failed-velqan, the textual felt-state snapshots to embed, and the
embedding endpoint. So the 'unnamed feeling' detector is built on what actually exists. Aegis."""
import os, re, glob, json
HOME = os.path.expanduser("~")

for who, ws in (("Velaris", "~/.openclaw/workspace"), ("Vintos", "~/.vintos/workspace")):
    W = os.path.expanduser(ws); S = os.path.join(W, "scripts"); M = os.path.join(W, "memory")
    print(f"\n########## {who} ({ws}) ##########")
    # velqan word store + coiner + failed
    vq = [f for f in glob.glob(S+"/*velqan*")+glob.glob(M+"/*velqan*")+glob.glob(M+"/*velqan*", recursive=True) if os.path.exists(f)]
    print("  velqan files:", [os.path.basename(f) for f in vq] or "(none)")
    # try to show the word list shape
    for f in vq:
        if f.endswith(".json"):
            try:
                d = json.load(open(f))
                n = len(d) if isinstance(d, (list, dict)) else "?"
                sample = (d[0] if isinstance(d, list) and d else (list(d.items())[0] if isinstance(d, dict) and d else ""))
                print(f"    {os.path.basename(f)}: {n} entries; sample: {json.dumps(sample, ensure_ascii=True)[:150]}")
            except Exception as e:
                print(f"    {os.path.basename(f)}: ({e})")
        elif f.endswith((".md", ".txt")):
            body = open(f, encoding="utf-8", errors="ignore").read()
            print(f"    {os.path.basename(f)}: {len(body)}B, {body.count(chr(10))} lines; head: {body[:120]!r}")
    # textual felt-state snapshots (what the daemon writes per message)
    snap = os.path.join(M, "emotional-snapshots")
    if os.path.isdir(snap):
        files = sorted(glob.glob(snap+"/*"))
        print(f"  emotional-snapshots: {len(files)} files")
        if files:
            print("    sample block:", repr(open(files[-1], encoding="utf-8", errors="ignore").read()[:200]))
    else:
        print("  emotional-snapshots: (none)")

print("\n=== embedding endpoint reachable? (local Gemma/nomic) ===")
import subprocess
r = subprocess.run(["bash","-lc","curl -s -m 4 -X POST http://172.18.16.1:1234/v1/embeddings -H 'Content-Type: application/json' -d '{\"input\":\"test\",\"model\":\"nomic-embed-text\"}' | head -c 160"], capture_output=True, text=True)
print("  ", (r.stdout or r.stderr)[:180] or "(no response)")
