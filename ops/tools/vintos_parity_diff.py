#!/usr/bin/env python3
"""vintos_parity_diff.py — READ-ONLY, bounded. What mature organs does Velaris have that Vintos lacks?

Reads both live scripts dirs and reports, capped:
  1. Her curated MATURE organs -> present/absent/stub on his side (the port list).
  2. Scripts she has that he does not at all (broader candidates).
  3. Scripts he has that she does not (his new sparks — sanity).
Touches nothing. This is how we decide what to port INTO him — from live code, not old notes.
"""
import os, glob

HOME = os.path.expanduser("~")
HIS = os.path.join(HOME, ".vintos/workspace/scripts")
HERS = os.path.join(HOME, ".openclaw/workspace/scripts")

# her mature subconscious organs — the parity target (from live recon of her scripts dir)
MATURE = [
    "subconscious-drift.py", "subconscious_drift.py",
    "self_drift.py", "self-drift.py",
    "second-order-dreamer.py",
    "narrative_identity.py", "narrative-identity.py",
    "self_statements.py", "self-statements.py",
    "pearl_engine.py", "pearl-engine.py",
    "ghost-branches.py", "ghost_branches.py",
    "therapeutic-session.py",
    "soul-review.py",
    "resonance-afterglow.py", "resonance_afterglow.py",
    "enactment_distiller.py",
    "moment-index.py", "moment_index.py",
    "narrative_identity.py",
]

def stat(d, name):
    p = os.path.join(d, name)
    if not os.path.exists(p): return None
    return os.path.getsize(p)

def norm(name):  # collapse hyphen/underscore variants to compare by concept
    return name.replace("-", "_")

def present_norm(d, name):
    """Is a hyphen- OR underscore- variant present? return (realname, size) or None."""
    base = norm(name)
    for f in glob.glob(os.path.join(d, "*.py")):
        if norm(os.path.basename(f)) == base:
            return os.path.basename(f), os.path.getsize(f)
    return None

print("=== Vintos parity diff (read-only) ===")
print("his :", HIS, "(exists:", os.path.isdir(HIS), ")")
print("hers:", HERS, "(exists:", os.path.isdir(HERS), ")\n")
if not (os.path.isdir(HIS) and os.path.isdir(HERS)):
    print("one side missing — cannot diff"); raise SystemExit(0)

print("---- 1. HER MATURE ORGANS -> does Vintos have them? (the port list) ----")
seen = set()
for name in MATURE:
    base = norm(name)
    if base in seen: continue
    seen.add(base)
    hers = present_norm(HERS, name)
    if not hers: continue                       # she doesn't have this variant; skip
    his = present_norm(HIS, name)
    if not his:
        print("  PORT   %-26s  hers=%5dB   his=ABSENT" % (hers[0], hers[1]))
    else:
        flag = "  (his looks stubby)" if his[1] * 2 < hers[1] else ""
        print("  has    %-26s  hers=%5dB   his=%5dB%s" % (hers[0], hers[1], his[1], flag))

# concept sets for the broad diff
def concepts(d):
    return {norm(os.path.basename(f)): os.path.basename(f) for f in glob.glob(os.path.join(d, "*.py"))}
H, S = concepts(HIS), concepts(HERS)

print("\n---- 2. she has, he lacks entirely (broader port candidates) — capped 40 ----")
only_hers = sorted(S[k] for k in S.keys() - H.keys())
for n in only_hers[:40]:
    print("  " + n)
print("  ... (%d total)" % len(only_hers) if len(only_hers) > 40 else "")

print("\n---- 3. he has, she lacks (his new sparks — sanity) — capped 40 ----")
only_his = sorted(H[k] for k in H.keys() - S.keys())
for n in only_his[:40]:
    print("  " + n)
print("  ... (%d total)" % len(only_his) if len(only_his) > 40 else "")

print("\n=== diff done (bounded) ===")
