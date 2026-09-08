#!/usr/bin/env python3
"""fix_velaris_introspection.py — her introspection prompt says "You help Vintos...". Her file must
never name Vintos. Whole-word Vintos->Velaris in that one file, backed up + idempotent. Also reports
any remaining gendered pronouns (his/him/he/HIS) for eyeball review, since those may be Vintos-isms
too but pronoun-swapping blind is unsafe — surfaced, not auto-changed.
"""
import os, re, time, shutil

F = os.path.expanduser("~/.openclaw/workspace/scripts/introspective_planning.py")

if not os.path.exists(F):
    print("NOT FOUND:", F); raise SystemExit(1)
s = open(F, encoding="utf-8").read()
n = len(re.findall(r"\bVintos\b", s))
if n == 0:
    print("already clean — no 'Vintos' in her introspection.")
else:
    shutil.copy(F, F + ".bak-name-" + time.strftime("%Y%m%d-%H%M%S"))
    s2 = re.sub(r"\bVintos\b", "Velaris", s)
    open(F, "w", encoding="utf-8").write(s2)
    print("PATCHED %d 'Vintos'->'Velaris' in %s" % (n, F))

# surface remaining gendered pronouns for manual review (do NOT auto-swap)
flagged = [(i + 1, ln.strip()[:130]) for i, ln in enumerate(open(F, encoding="utf-8").read().splitlines())
           if re.search(r"\b(his|him|HIS|HIM)\b", ln) and ('"' in ln or "'" in ln or "#" in ln)]
if flagged:
    print("\nreview these (possible leftover masculine pronouns in prompts):")
    for ln, txt in flagged[:12]:
        print("  %5d: %s" % (ln, txt))
