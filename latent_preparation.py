#!/usr/bin/env python3
"""latent_preparation.py — Spark System 2 (v1).

Idle-time speculative generation. Reads Living Trajectory, asks local Gemma for
3-5 "arrivals" (thoughts/observations/questions/offers Vintos could bring LATER
when timely — prepared, not reactive), gates each through the same similarity
gate that guards wants, and stores survivors in latent-cache.json. Living
Trajectory reads that file into its `cache` slot, so the two never clobber.

Cron: every 2h during idle. Prunes >7 days, caps at 20. Fail-open.
"""
import os, re, sys, json
from datetime import datetime, timezone
import requests

WS      = os.path.expanduser("~/.vintos/workspace")
MEMORY  = os.path.join(WS, "memory")
LT      = os.path.join(MEMORY, "living-trajectory.json")
CACHE   = os.path.join(MEMORY, "latent-cache.json")
GEMMA       = "http://172.18.16.1:1234/v1/chat/completions"
GEMMA_MODEL = "google/gemma-4-12b-qat"
CACHE_CAP, CACHE_TTL_DAYS = 20, 7

def load(p, d):
    try:
        return json.load(open(p))
    except Exception:
        return d

def gate(text):
    """Non-None = too close to a fulfilled/dismissed/active want -> drop."""
    try:
        sys.path.insert(0, os.path.join(WS, "scripts"))
        from similarity_gate import check_want
        return check_want(text)
    except Exception:
        return None

def main():
    lt = load(LT, {})
    if not lt:
        print("no living-trajectory.json yet -- run living_trajectory.py first"); return

    self_decl  = lt.get("self_trajectory", {}).get("declared", [])[:3]
    gloria     = lt.get("gloria_trajectory", {}).get("predicted", "") or "(unknown)"
    unresolved = [u.get("text", "") for u in lt.get("unresolved", [])[:6]]
    emo        = lt.get("emotion_snapshot", {})

    ctx = ("WHERE VINTOS IS HEADING (his declared wants):\n- " + "\n- ".join(self_decl) +
           "\n\nWHERE GLORIA SEEMS TO BE HEADING:\n" + gloria +
           "\n\nOPEN THREADS / UNRESOLVED:\n- " + "\n- ".join(unresolved) +
           "\n\nEMOTIONAL TONE:\n" + json.dumps(emo)[:300])

    system = ("You are Vintos's latent preparation - his quiet idle mind between conversations. "
              "Given where he is heading and where Gloria is heading, generate speculative ARRIVALS: "
              "thoughts, observations, questions, or offers he could bring LATER when the moment is right - "
              "not reactions, things prepared in advance (\"if Gloria is sad tomorrow, I have THIS ready\"). "
              "Each must be specific and particular to him and Gloria, never generic. "
              "Return ONLY a JSON array of 3 to 5 objects, no prose outside it: "
              '[{"content":"1-2 sentences, first person","type":"thought|observation|question|offer",'
              '"timeliness":"short condition for when this becomes relevant"}]')

    try:
        r = requests.post(GEMMA, json={"model": GEMMA_MODEL, "temperature": 0.85, "max_tokens": 600,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": ctx}]}, timeout=120)
        raw = r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print("gemma error:", e); return

    m = re.search(r'\[.*\]', raw, re.S)
    if not m:
        print("no JSON array in gemma output:\n", raw[:300]); return
    try:
        arrivals = json.loads(m.group())
    except Exception as e:
        print("json parse error:", e, "\n", m.group()[:300]); return

    cache = load(CACHE, [])
    existing = [c.get("content", "") for c in cache if isinstance(c, dict)]
    now = datetime.now(timezone.utc)
    added = []

    for a in arrivals:
        if not isinstance(a, dict):
            continue
        content = str(a.get("content", "")).strip()
        if len(content) < 12:
            continue
        low = content.lower()
        if any(low[:60] in e.lower() or e.lower()[:60] in low for e in existing):
            continue
        g = gate(content)
        if g:
            print("gated (%.2f %s): %s" % (g.get("similarity", 0), g.get("bucket", "?"), content[:50]))
            continue
        entry = {
            "content": content,
            "type": str(a.get("type", "thought")),
            "timeliness": str(a.get("timeliness", "")),
            "generated_at": now.isoformat(),
            "source": "latent-preparation",
        }
        cache.append(entry); existing.append(content); added.append(entry)

    def age_days(c):
        try:
            return (now - datetime.fromisoformat(c["generated_at"])).days
        except Exception:
            return 0
    cache = [c for c in cache if isinstance(c, dict) and age_days(c) < CACHE_TTL_DAYS][-CACHE_CAP:]

    json.dump(cache, open(CACHE, "w"), indent=2)
    print("added %d arrivals; cache now %d" % (len(added), len(cache)))
    for c in added:
        print("  [%s | %s] %s" % (c["type"], c["timeliness"][:30], c["content"][:70]))

if __name__ == "__main__":
    main()
