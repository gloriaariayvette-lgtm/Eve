#!/usr/bin/env python3
"""test_mode_audit.py — READ-ONLY. Does test mode actually gate ALL logging? Shows how _test_mode_active
is toggled, every check site, and every memory-write in the chat/voice handlers with whether a
test-mode guard is within reach above it. Surfaces any write that leaks past test mode. Aegis.
"""
import os, re

SERVER = os.path.expanduser("~/Vintos/server.py")
lines = open(SERVER, encoding="utf-8", errors="ignore").read().splitlines()

print("=== how test mode is toggled (def _test_mode_active + its flag) ===")
d = next((i for i, l in enumerate(lines) if re.search(r'def\s+_test_mode_active', l)), None)
if d is not None:
    for k in range(d, min(d + 16, len(lines))):
        if lines[k].strip(): print("  %5d: %s" % (k + 1, lines[k].strip()[:150]))
        if k > d and re.match(r'\s*(def|@app)', lines[k]): break
# also how it's SET (the toggle endpoint / flag write)
print("\n  -- where the test flag is set (toggle) --")
for i, l in enumerate(lines):
    if re.search(r'test.?mode|_test_mode|test-mode', l, re.I) and re.search(r'@app|def |\.write|open\(|= *True|= *False|json\.dump|\.txt|\.json', l):
        if "def _test_mode_active" in l: continue
        print("  %5d: %s" % (i + 1, l.strip()[:150]))

print("\n=== every _test_mode_active() CHECK site ===")
for i, l in enumerate(lines):
    if "_test_mode_active(" in l and "def " not in l:
        print("  %5d: %s" % (i + 1, l.strip()[:130]))

print("\n=== memory writes — is each behind a test-mode guard within 15 lines above? ===")
WRITE = re.compile(r'\.append\(\{|json\.dump\(.*(history|ledger|imprint)|open\([^)]*(history|ledger|imprint|wal)[^)]*,\s*["\']w|subprocess\.Popen|_vcp\.Popen|Popen\(\[')
for i, l in enumerate(lines):
    if WRITE.search(l):
        s = l.strip()
        if not s or s.startswith("#"): continue
        guarded = any("_test_mode_active" in lines[j] for j in range(max(0, i - 15), i))
        flag = "  guarded" if guarded else "  <-- NO test-mode guard nearby"
        print("  %5d: %s%s" % (i + 1, s[:110], flag))

print("\n=== READ ===")
print("  Every memory write should say 'guarded'. Any 'NO test-mode guard' = it logs even in test mode = a leak I fix.")
