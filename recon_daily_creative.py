#!/usr/bin/env python3
"""recon_daily_creative.py — Aegis, READ-ONLY. His dream poem+image weren't appended to daily-creative this morning.
I removed dream-architecture.sh's cron (generate_poem) as a 'duplicate'. Verify whether generate_poem() was actually
the daily-creative REVERIE append (not a duplicate of the gallery poem), and what appends the dream IMAGE — so the
fix restores the right thing without re-introducing a real duplicate.
  (1) who writes/append daily-creative-{date}.md across his scripts.
  (2) dream_poetry.py: generate_poem() vs its cron main() vs save_poem() — do they target daily-creative or the
      gallery (poetry-log), i.e. duplicate or distinct?
  (3) the dream image path into daily-creative.
Nothing written. His = ~/Vintos + ~/.vintos/workspace/scripts."""
import os, re, glob
VIN = os.path.expanduser("~/Vintos")
HIS = os.path.expanduser("~/.vintos/workspace/scripts")

def files():
    out = []
    for d in (VIN, HIS):
        if os.path.isdir(d):
            for e in os.scandir(d):
                if e.is_file() and (e.name.endswith(".py") or e.name.endswith(".sh")):
                    out.append(e.path)
    return out

print("== (1) who writes/appends daily-creative ==")
for p in files():
    try: t = open(p, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    if "daily-creative" in t:
        ls = [(i + 1, l.strip()[:100]) for i, l in enumerate(t.split("\n"))
              if "daily-creative" in l and re.search(r'open\(|append|write|"a"|\'a\'|>>|dump|path|=', l)]
        if ls:
            print("  %s:" % os.path.basename(p))
            for i, l in ls[:8]: print("     %4d: %s" % (i, l))

print("\n== (2) dream_poetry.py — generate_poem() vs main vs save_poem (daily-creative or gallery?) ==")
dp = os.path.realpath(os.path.join(VIN, "dream_poetry.py"))
if os.path.isfile(dp):
    L = open(dp, encoding="utf-8", errors="ignore").read().split("\n")
    for fn in ("generate_poem", "save_poem", "compose_poem"):
        idx = next((i for i, l in enumerate(L) if re.match(r'\s*def %s\b' % fn, l)), None)
        if idx is None:
            print("  def %s: NOT FOUND" % fn); continue
        print("  def %s (line %d):" % (fn, idx + 1))
        end = min(idx + 40, len(L))
        for i in range(idx, end):
            if re.match(r'\s*def ', L[i]) and i > idx: break
            if re.search(r'daily-creative|poetry-log|art/poetry|append|open\(|"a"|\'a\'|write|dump|journal|reverie|save_poem|return', L[i]):
                print("      %4d: %s" % (i + 1, L[i].strip()[:96]))
    # what does __main__ call?
    mi = next((i for i, l in enumerate(L) if '__main__' in l), None)
    if mi is not None:
        print("  __main__ block:")
        for i in range(mi, min(mi + 20, len(L))):
            if re.search(r'generate_poem|compose_poem|save_poem|daily-creative|argv|--', L[i]):
                print("      %4d: %s" % (i + 1, L[i].strip()[:96]))

print("\n== (3) the dream IMAGE into daily-creative (dream-art / dream-trigger) ==")
for name in ("dream-art.py", "dream_art.py", "dream-trigger.sh"):
    for base in (VIN, HIS, os.path.expanduser("~/.vintos/workspace/skills/dreaming/scripts")):
        p = os.path.join(base, name)
        if os.path.isfile(p) or os.path.islink(p):
            t = open(os.path.realpath(p), encoding="utf-8", errors="ignore").read()
            hits = [(i + 1, l.strip()[:96]) for i, l in enumerate(t.split("\n"))
                    if re.search(r'daily-creative|append.*image|\.png|\.jpg|paint', l)]
            if hits:
                print("  %s:" % name)
                for i, l in hits[:6]: print("     %4d: %s" % (i, l))
            break

print("\n== (4) confirm dream-architecture.sh cron removal + what generate_poem uniquely did ==")
arch = os.path.join(VIN, "dream-architecture.sh")
if os.path.isfile(arch):
    print("  dream-architecture.sh body:")
    for i, l in enumerate(open(arch, encoding="utf-8", errors="ignore").read().split("\n")):
        if l.strip(): print("     %4d: %s" % (i + 1, l.strip()[:96]))

print("\n(READ-ONLY. Confirms whether removing generate_poem's cron cut the daily-creative reverie append.)")
