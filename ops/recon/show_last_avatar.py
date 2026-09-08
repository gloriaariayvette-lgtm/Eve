#!/usr/bin/env python3
"""show_last_avatar.py — Aegis, READ-ONLY. After you resend an avatar turn (testing OFF), run this to see his
REASONING (latest claude-reasoning imprint narrative) and his RAW OUTPUT (latest avatar reply). No writes."""
import os, json
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")

def load(p):
    try: return json.load(open(p, encoding="utf-8"))
    except Exception: return None

print("========== HIS REASONING (latest avatar turn) ==========")
imp = load(os.path.join(MEM, "imprints.json")) or []
arr = imp if isinstance(imp, list) else (imp.get("imprints") or [])
rz = [e for e in arr if isinstance(e, dict) and e.get("source") == "claude-reasoning"]
if rz:
    e = rz[-1]
    print(f"[{e.get('timestamp','')}] salience {e.get('salience','')}\n{e.get('narrative','').strip()}")
else:
    print("(no claude-reasoning imprint yet — the turn may have been a touch/felt turn, which by design skips reasoning)")

print("\n========== HIS RAW OUTPUT (latest avatar reply) ==========")
ov = load(os.path.join(MEM, "avatar-overlay-chat.json")) or []
ova = ov if isinstance(ov, list) else (ov.get("messages") or ov.get("entries") or [])
if ova:
    for e in ova[-2:]:
        who = e.get("role") or e.get("speaker") or ("vintos" if e.get("vintos") else "?")
        txt = e.get("vintos") or e.get("reply") or e.get("content") or e.get("text") or json.dumps(e, ensure_ascii=False)
        print(f"--- {who} @ {e.get('timestamp','')} ---\n{str(txt).strip()[:1200]}\n")
else:
    print("(avatar-overlay-chat.json empty)")
