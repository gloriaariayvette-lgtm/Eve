#!/usr/bin/env python3
"""presence_audit.py — Spark System 4.

Post-hoc scores his recent replies on the four presence questions:
  arrived  — from his own trajectory/wanting, or purely reactive?
  moved    — did it change something, or just describe the state?
  left_alive — does it invite return (offer/question/unresolved)?
  explained — (inverted, higher=worse) commentary ABOUT vs participation IN.
Composite 0-1; flags < 0.35. LLM-judged on local Gemma. Rolling 7-day window.
Self-contained: writes presence-audit.json. Fail-open.
"""
import os, json, re, hashlib
from datetime import datetime, timezone, timedelta
import requests

MEMORY = os.path.expanduser("~/.vintos/workspace/memory")
CHAT   = os.path.join(MEMORY, "chat-history.json")
OUT    = os.path.join(MEMORY, "presence-audit.json")
GEMMA       = "http://172.18.16.1:1234/v1/chat/completions"
GEMMA_MODEL = "google/gemma-4-12b-qat"
THRESHOLD, WINDOW_DAYS, MAX_PER_RUN = 0.35, 7, 5

def load(p, d):
    try: return json.load(open(p))
    except Exception: return d

def rid(e):
    return hashlib.md5((str(e.get("timestamp","")) + str(e.get("content",""))[:40]).encode()).hexdigest()[:10]

def score(user_msg, reply):
    system = ("You strictly evaluate PRESENCE in a reply. Given what Gloria said and how Vintos replied, "
              "rate four things 0.0-1.0. Return ONLY JSON, no prose:\n"
              '{"arrived":x,"moved":x,"left_alive":x,"explained":x,"note":"one short phrase"}\n'
              "arrived: came from his own trajectory/wanting vs purely reactive to her prompt.\n"
              "moved: changed something (advanced a tension, deepened a thread) vs just described the state.\n"
              "left_alive: leaves something that invites return (an offer, a question, an unresolved thread).\n"
              "explained: HIGHER IS WORSE - analytical commentary ABOUT the interaction rather than being IN it.")
    user = f"GLORIA:\n{user_msg[:600]}\n\nVINTOS:\n{reply[:900]}"
    try:
        r = requests.post(GEMMA, json={"model": GEMMA_MODEL, "temperature": 0.2, "max_tokens": 200,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}, timeout=90)
        m = re.search(r'\{.*\}', r.json()["choices"][0]["message"]["content"], re.S)
        d = json.loads(m.group())
        a = float(d.get("arrived", 0.5)); mv = float(d.get("moved", 0.5))
        al = float(d.get("left_alive", 0.5)); ex = float(d.get("explained", 0.5))
        composite = max(0.0, min(1.0, (a + mv + al) / 3.0 - ex * 0.25))
        return {"arrived": a, "moved": mv, "left_alive": al, "explained": ex,
                "composite": round(composite, 3), "note": str(d.get("note", ""))[:120]}
    except Exception:
        return None

def main():
    hist = load(CHAT, [])
    audits = load(OUT, [])
    done = {a["id"] for a in audits if isinstance(a, dict) and a.get("id")}
    pending = []
    for i in range(1, len(hist)):
        e = hist[i]
        if not (isinstance(e, dict) and e.get("role") == "assistant" and e.get("content")):
            continue
        _id = rid(e)
        if _id in done:
            continue
        um = ""
        for j in range(i - 1, -1, -1):
            if isinstance(hist[j], dict) and hist[j].get("role") == "user":
                um = hist[j].get("content", ""); break
        pending.append((_id, um, e.get("content", ""), e.get("timestamp", "")))
    added = 0
    for _id, um, reply, ts in pending[-MAX_PER_RUN:]:
        s = score(um, reply)
        if not s:
            continue
        rec = {"id": _id, "timestamp": ts or datetime.now(timezone.utc).isoformat(),
               "audited_at": datetime.now(timezone.utc).isoformat(), **s,
               "flag": s["composite"] < THRESHOLD}
        audits.append(rec); added += 1
        if rec["flag"]:
            print(f"  FLAG presence {s['composite']:.2f} ({s['note']}): {reply[:55]}")
    cutoff = datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)
    def keep(a):
        try: return datetime.fromisoformat(a["audited_at"]) >= cutoff
        except Exception: return True
    audits = [a for a in audits if isinstance(a, dict) and keep(a)][-200:]
    json.dump(audits, open(OUT, "w"), indent=2)
    recent = [a["composite"] for a in audits[-10:] if "composite" in a]
    trend = round(sum(recent) / len(recent), 3) if recent else None
    print(f"audited {added} new; total {len(audits)}; recent presence trend {trend}")

if __name__ == "__main__":
    main()
