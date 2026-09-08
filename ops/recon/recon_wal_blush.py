#!/usr/bin/env python3
"""recon_wal_blush.py — Aegis, READ-ONLY. Dump the WAL + blush stores in full (all small) so we can see
the test-turn residue and purge it precisely: wal-log.json, wal-buffer.json, wal.md, autonomous-blush.md."""
import os
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")
for name in ("wal-log.json", "wal-buffer.json", "wal.md", "autonomous-blush.md"):
    p = os.path.join(MEM, name)
    print("\n" + "=" * 70)
    print("FILE:", name, "(" + (str(os.path.getsize(p)) + "B" if os.path.isfile(p) else "MISSING") + ")")
    print("=" * 70)
    if os.path.isfile(p):
        print(open(p, encoding="utf-8", errors="ignore").read())
