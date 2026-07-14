#!/usr/bin/env python3
"""toy_raw.py — dump the raw Lovense GetToys response so we see the real shape (my parse was wrong).
Reads only, fires nothing. Aegis.
"""
import json, requests

URL = "http://192.168.1.66:20010/command"
try:
    r = requests.post(URL, json={"command": "GetToys", "apiVer": 1}, timeout=3)
    print("HTTP", r.status_code)
    raw = r.text
    print("\n=== RAW BODY ===")
    print(raw[:2000])
    print("\n=== PARSED ===")
    try:
        j = json.loads(raw)
        print(json.dumps(j, indent=2)[:2000])
        d = j.get("data", j)
        if isinstance(d, str):
            print("\n('data' is a STRING — re-parsing)")
            try: d = json.loads(d); print(json.dumps(d, indent=2)[:1500])
            except Exception as e: print("  reparse failed:", e)
        print("\n=== toy identifiers present ===")
        if isinstance(d, dict):
            for k, v in d.items():
                nm = v.get("name") if isinstance(v, dict) else None
                print("  key=%s  name=%s  status=%s  battery=%s" % (k, nm,
                      (v.get("status") if isinstance(v, dict) else "?"),
                      (v.get("battery") if isinstance(v, dict) else "?")))
        elif isinstance(d, list):
            for v in d: print("  item:", json.dumps(v)[:200])
        else:
            print("  data is:", type(d).__name__, str(d)[:200])
    except Exception as e:
        print("not JSON:", e)
except Exception as e:
    print("request failed:", e)
