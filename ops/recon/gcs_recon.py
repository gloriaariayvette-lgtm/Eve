#!/usr/bin/env python3
"""gcs_recon.py — READ-ONLY. Why didn't GCS fire? Checks: is test mode ON (I just had it enabled), the
GCS handler's logic + any test-mode/key guard, gcs/hardware state, and recent logs. Aegis.
"""
import os, re, json, subprocess

MEM = os.path.expanduser("~/.vintos/workspace/memory")
SERVER = os.path.expanduser("~/Vintos/server.py")
def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True).stdout

print("=== is test mode ON right now? (I told you to touch .test-mode) ===")
tm = os.path.join(MEM, ".test-mode")
print("  .test-mode exists:", os.path.exists(tm), "  <-- if True, test mode is ON")

print("\n=== the GCS handler in server.py ===")
lines = open(SERVER, encoding="utf-8", errors="ignore").read().splitlines()
hits = [i for i, l in enumerate(lines) if re.search(r'gcs|coherence.?collapse|coherence_collapse', l, re.I)]
# show the handler region(s)
regions = []
for i in hits:
    if not any(abs(i - r) < 8 for r in regions): regions.append(i)
for r in regions[:6]:
    # find enclosing route
    route = "?"
    for k in range(r, max(0, r-40), -1):
        m = re.search(r'@app\.\w+\("([^"]+)"', lines[k])
        if m: route = m.group(1); break
    print("\n  -- near L%d (route %s) --" % (r+1, route))
    for k in range(max(0, r-3), min(r+14, len(lines))):
        s = lines[k].strip()
        if s and not s.startswith("#") and re.search(r'gcs|coherence|_test_mode|def |dump|collapse|toy|fire|XAI|return', s, re.I):
            print("    %5d: %s" % (k+1, s[:140]))

print("\n=== does the GCS path check test mode? ===")
gcs_region = "\n".join(lines[max(0, (regions[0] if regions else 7300)-5):(regions[0] if regions else 7300)+40])
print("  _test_mode_active referenced near GCS handler:", "_test_mode_active" in gcs_region)

print("\n=== state files ===")
for f in ("gcs-state.json", "hardware-button.json", "gcs-saved-patterns.json"):
    p = os.path.join(MEM, f)
    if os.path.exists(p):
        try: print("  %s: %s" % (f, json.dumps(json.load(open(p)))[:160]))
        except Exception as e: print("  %s: (%s)" % (f, e))
    else: print("  %s: (none)" % f)

print("\n=== recent logs (gcs / coherence / collapse / button) ===")
logs = sh("journalctl --user -u vintos-server -n 500 --no-pager")
for l in logs.splitlines():
    if re.search(r'gcs|coherence|collapse|hardware.?button|GCS', l, re.I):
        print("  " + l[-150:])
print("  (if nothing here, the GCS press may not have reached the server)")
