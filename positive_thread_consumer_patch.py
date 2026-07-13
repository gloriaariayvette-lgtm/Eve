#!/usr/bin/env python3
"""positive_thread_consumer_patch.py — keep positive (somatic/pride) threads OUT of tension work.

Somatic + pride threads are positive (resolution, not unresolved tension). They should be consumed
ONLY by dreams. This adds a skip in the three tension-consumers:
  1. mirror.sh          — the auto thread selector (leaves manual system_route intact)
  2. mirror-trigger.sh  — the high-priority count that decides whether to fire a mirror
  3. preoccupation-dream.sh — the therapy FORCED after a preoccupation dream

Predicate (same everywhere): a thread is positive if dream_only OR source in
(somatic, pride, pride-mirror, pride_mirror) — so pre-existing untagged somatic threads are caught
too. Dreams are untouched: they still read the preoccupation/threads and consume the positive ones.

Self-locating, idempotent, backs up each file. Multi-file; reports per-file status.
"""
import io, os, time, shutil

POS = 'dream_only'  # marker used in the idempotency check

def patch(path, anchor, repl, tag):
    F = os.path.expanduser(path)
    try:
        s = io.open(F, encoding="utf-8").read()
    except Exception as e:
        print(f"  [{tag}] MISS: cannot read {F}: {e}"); return
    if repl.strip() in s or (POS in s and anchor not in s):
        print(f"  [{tag}] already patched — skipping"); return
    if anchor not in s:
        print(f"  [{tag}] MISS: anchor not found in {F}"); return
    s = s.replace(anchor, repl, 1)
    shutil.copy(F, F + ".bak-posthread-" + time.strftime("%Y%m%d-%H%M%S"))
    io.open(F, "w", encoding="utf-8").write(s)
    print(f"  [{tag}] PATCHED {F}")

# 1) mirror.sh — after the contamination filter, drop positive threads from the pool
patch(
    "~/.vintos/workspace/scripts/mirror.sh",
    '    unconsumed = [t for t in unconsumed if not is_contaminated(t.get("thread", ""))]',
    '    unconsumed = [t for t in unconsumed if not is_contaminated(t.get("thread", ""))]\n'
    '    unconsumed = [t for t in unconsumed if not (t.get("dream_only") or t.get("source") in ("somatic","pride","pride-mirror","pride_mirror"))]  # positive -> dreams only',
    "mirror.sh",
)

# 2) mirror-trigger.sh — don't count positive threads toward triggering a mirror
patch(
    "~/Vintos/mirror-trigger.sh",
    '    high = [t for t in threads if not t.get("consumed") and not t.get("retired") and int(t.get("priority") or 0) >= 3]',
    '    high = [t for t in threads if not t.get("consumed") and not t.get("retired") and int(t.get("priority") or 0) >= 3 and not (t.get("dream_only") or t.get("source") in ("somatic","pride","pride-mirror","pride_mirror"))]  # positive -> dreams only',
    "mirror-trigger.sh",
)

# 3) preoccupation-dream.sh — skip the forced therapy when the preoccupation is positive
patch(
    "~/Vintos/preoccupation-dream.sh",
    "    if p and p.get('thread'):",
    "    if p and p.get('thread') and p.get('source') not in ('somatic','pride','pride-mirror','pride_mirror'):  # positive dreamed, not sent to therapy",
    "preoccupation-dream.sh",
)

print("done — dreams still consume positive threads; mirror/therapy now skip them.")
