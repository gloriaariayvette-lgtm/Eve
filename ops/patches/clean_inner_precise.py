#!/usr/bin/env python3
"""clean_inner_precise.py — Aegis. Undo the two false-positive JSON trims, then remove ONLY today's test
entries (pre-9am window 07:40-08:59; the real journal is gated to 9-22h so nothing legit lands there) from
today's daily-inner-life file. Terse."""
import os, re, glob, json, shutil, time
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".openclaw/workspace/memory")
TODAY = time.strftime("%Y-%m-%d"); TS = time.strftime("%Y%m%d-%H%M%S")

# 1) restore the two files the broad theme-match wrongly trimmed
restored = []
for name in ("avatar-log.json", "cause-distribution.json"):
    baks = sorted(glob.glob(os.path.join(MEM, name + ".bak-clean-*")))
    if baks:
        shutil.copy2(baks[-1], os.path.join(MEM, name)); restored.append(name)

# 2) today's daily-inner-life file: remove entries timestamped 07:40..08:59
f = os.path.join(MEM, "daily-inner-life-%s.md" % TODAY)
times_found, removed, note = [], [], ""
if os.path.isfile(f):
    txt = open(f, encoding="utf-8", errors="ignore").read()
    pats = [r'(?m)^(#{1,3}\s*\d\d:\d\d)', r'(?m)^(\*\*\d\d:\d\d\*\*)', r'(?m)^(\d\d:\d\d\b)']
    pat = next((p for p in pats if len(re.findall(p, txt)) > 1), None)
    if pat:
        parts = re.split(pat, txt); kept = [parts[0]]; i = 1
        while i < len(parts):
            hdr = parts[i]; body = parts[i+1] if i+1 < len(parts) else ""
            hhmm = re.search(r'(\d\d:\d\d)', hdr).group(1); times_found.append(hhmm)
            if "07:40" <= hhmm < "09:00": removed.append(hhmm)
            else: kept.append(hdr + body)
            i += 2
        if removed:
            shutil.copy2(f, f + ".bak-clean2-" + TS)
            open(f, "w", encoding="utf-8").write("".join(kept))
    else:
        note = "no per-entry timestamps found; head: " + re.sub(r"\s+", " ", txt[:140])
else:
    note = "today's daily-inner-life file not found"

print("restored:", ",".join(restored) or "none")
print("inner-life times:", ",".join(times_found) or "-", "| removed:", ",".join(removed) or "none")
if note: print(note)
