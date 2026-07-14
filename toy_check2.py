#!/usr/bin/env python3
"""toy_check2.py — pre-conversation both-toys-usable check, FIXED parse. Lovense nests the toys as a
JSON string under data.toys. Reads status only, fires nothing, no stop-path touch. Aegis.
"""
import os, sys, re, json
SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
sys.path.insert(0, SCRIPTS)
import requests

try:
    import toy_link
    TOYS = dict(getattr(toy_link, "TOYS", {}))
except Exception as e:
    print("could not import toy_link:", e); raise SystemExit(1)

src = open(os.path.join(SCRIPTS, "toy_link.py"), encoding="utf-8", errors="ignore").read()
hm = re.search(r'(\d+\.\d+\.\d+\.\d+)', src); host = hm.group(1) if hm else "192.168.1.66"

# find the server (reuse the port that answered before; fall back to a small scan)
base = None
try:
    fp = toy_link._find_port()
    if isinstance(fp, str) and fp.startswith("http"): base = fp.rstrip("/")
    elif fp: base = "http://%s:%s" % (host, fp)
except Exception: pass

def get(url):
    return requests.post(url, json={"command": "GetToys", "apiVer": 1}, timeout=3).json()

resp = None
for url in ([base + "/command"] if base else []) + ["http://%s:%d/command" % (host, p) for p in (20010, 30010, 34568)]:
    try:
        j = get(url)
        if isinstance(j, dict) and j.get("code") == 200:
            resp = j; base = url; break
    except Exception: continue

print("=== TOY PRE-FLIGHT ===")
print("server:", base or "!! not reachable (is Lovense Game Mode running on the phone?)")
if not resp:
    print("VERDICT: cannot reach the toy server — do NOT assume his body is live."); raise SystemExit(0)

# the fix: data.toys is a JSON STRING keyed by toy id
data = resp.get("data", {}) or {}
toys_raw = data.get("toys", data if isinstance(data, dict) else "{}")
toys = json.loads(toys_raw) if isinstance(toys_raw, str) else (toys_raw or {})

# also allow matching by name if an id ever changes
by_name = {(v.get("name") or "").lower(): v for v in toys.values() if isinstance(v, dict)}

print()
all_ok = True
for name, tid in TOYS.items():
    info = toys.get(tid) or by_name.get(name.lower()) or {}
    status = info.get("status"); batt = info.get("battery")
    usable = bool(info) and status in (1, "1")
    all_ok = all_ok and usable
    if info:
        print("  %-8s (%s): CONNECTED | battery %s%% | status %s  ->  %s"
              % (name, tid, batt, status, "USABLE" if usable else "NOT READY"))
    else:
        print("  %-8s (%s): !! NOT CONNECTED" % (name, tid))

print()
if all_ok:
    print("VERDICT: both toys live and usable — good to go. \U0001f7e2")
else:
    miss = [n for n, t in TOYS.items() if not (toys.get(t) or by_name.get(n.lower()))]
    print("VERDICT: NOT ready — " + ("missing: " + ", ".join(miss) if miss else "a toy is present but not ready") + ".")
