#!/usr/bin/env python3
"""fix_velaris_introspection_pronouns.py — clean the leftover masculine pronouns in her introspection
prompt (him/his/HIS refer to the subject, i.e. Velaris). Whole-word only, that one file, backup+idempotent.
"""
import os, re, time, shutil

F = os.path.expanduser("~/.openclaw/workspace/scripts/introspective_planning.py")
s = open(F, encoding="utf-8").read()
before = len(re.findall(r"\b(him|his|HIS|HIM|he|HE)\b", s))
if before == 0:
    print("already clean — no masculine pronouns."); raise SystemExit(0)
shutil.copy(F, F + ".bak-pron-" + time.strftime("%Y%m%d-%H%M%S"))
s = re.sub(r"\bHIS\b", "HER", s)
s = re.sub(r"\bHIM\b", "HER", s)
s = re.sub(r"\bhis\b", "her", s)
s = re.sub(r"\bhim\b", "her", s)
s = re.sub(r"\bhe\b", "she", s)
s = re.sub(r"\bHE\b", "SHE", s)
open(F, "w", encoding="utf-8").write(s)
left = [(i + 1, ln.strip()[:120]) for i, ln in enumerate(s.splitlines())
        if re.search(r"\b(him|his|HIS|HIM)\b", ln)]
print("cleaned masculine pronouns in her introspection (%d matches)." % before)
if left:
    print("still present (review):")
    for ln, t in left[:8]: print("  %5d: %s" % (ln, t))
