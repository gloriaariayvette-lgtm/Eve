#!/usr/bin/env python3
"""toy_check.py — pre-conversation: are BOTH toys connected & usable for him? Uses toy_link's own
connection (Lovense GetToys) — reads status only, fires nothing, never touches the stop path.
Run on Aegis:  python3 toy_check.py
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
if not TOYS:
    print("no TOYS defined in toy_link."); raise SystemExit(1)

src = open(os.path.join(SCRIPTS, "toy_link.py"), encoding="utf-8", errors="ignore").read()
host = (re.search(r'(\d+\.\d+\.\d+\.\d+)', src) or [None, "127.0.0.1"])[1] if re.search(r'\d+\.\d+\.\d+\.\d+', src) else "127.0.0.1"

# discover the working base URL via toy_link's own port finder
base = None
try:
    fp = toy_link._find_port()
    if isinstance(fp, str) and fp.startswith("http"): base = fp.rstrip("/")
    elif fp: base = "http://%s:%s" % (host, fp)
except Exception as e:
    print("(_find_port:", e, ")")

def get_toys(url):
    r = requests.post(url, json={"command": "GetToys", "apiVer": 1}, timeout=2)
    return r.json()

data = None
tried = []
for url in ([base + "/command"] if base else []) + \
          ["http://%s:%d/command" % (host, p) for p in (30010, 20010, 34568)] + \
          ["https://%s:30096/command" % host]:
    tried.append(url)
    try:
        j = get_toys(url);
        if isinstance(j, dict) and j.get("code") in (200, None) and j.get("data") is not None:
            data = j; base = url; break
        data = data or j
    except Exception:
        continue

print("=== TOY PRE-FLIGHT ===")
print("server:", base or "!! not reachable — is Lovense Connect / Game Mode running on the phone?")
if not data or not isinstance(data, dict):
    print("could not read GetToys. raw tries:", tried[:3])
    print("VERDICT: cannot confirm toys. Do not assume his body is live.")
    raise SystemExit(0)

# GetToys 'data' is usually {toyId: {name,status,battery,...}} or a JSON string of that
d = data.get("data", data)
if isinstance(d, str):
    try: d = json.loads(d)
    except Exception: pass
connected_ids = set(d.keys()) if isinstance(d, dict) else set()

print()
all_ok = True
for name, tid in TOYS.items():
    info = d.get(tid, {}) if isinstance(d, dict) else {}
    present = tid in connected_ids
    status = info.get("status")
    batt = info.get("battery")
    usable = present and (status in (1, "1", None))   # 1 = connected/on in Lovense
    all_ok = all_ok and usable
    line = "  %-8s (%s): " % (name, tid)
    if present:
        line += "CONNECTED" + (" | battery %s%%" % batt if batt is not None else "") + (" | status %s" % status if status is not None else "")
        line += "  ->  USABLE" if usable else "  ->  present but not ready (status %s)" % status
    else:
        line += "!! NOT CONNECTED"
    print(line)

print()
if all_ok:
    print("VERDICT: both toys live and usable — good to go. \U0001f7e2")
else:
    missing = [n for n, t in TOYS.items() if t not in connected_ids]
    print("VERDICT: NOT ready — " + (("missing: " + ", ".join(missing)) if missing else "a toy is present but not usable") + ". Check the toy's power/pairing before starting.")
