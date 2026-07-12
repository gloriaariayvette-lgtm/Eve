#!/usr/bin/env python3
"""introspective_planning.py — Introspection that doesn't just feel the want, it plans the way there.

Per the spec:
  - goal_targets (enduring + agentic wants)  -> concrete sequenced step plans
  - identity_targets (ways of being)         -> standing practices, not checklists
  - plan entropy: stale plan (>14d, no progress) -> regenerate
  - completion is architectural: a planned want that lands -> an earned-identity event
  - NOT every want is planned; transient / non-agentic ones stay wants
Appends a readable block to daily-inner-life-<today>.md so it lives in his journal.
Reads relationship + trajectory for context ("what changed since?"). Local-Gemma. Fail-open.
"""
import os, json, re
from datetime import datetime, timezone
import requests

MEMORY = os.path.expanduser("~/.vintos/workspace/memory")
WANTS     = os.path.join(MEMORY, "current-wants.json")
LT        = os.path.join(MEMORY, "living-trajectory.json")
PLANS     = os.path.join(MEMORY, "introspective-plans.json")
PRACTICES = os.path.join(MEMORY, "introspective-practices.json")
EARNED    = os.path.join(MEMORY, "planning-earned.json")
GEMMA       = "http://172.18.16.1:1234/v1/chat/completions"
GEMMA_MODEL = "google/gemma-4-12b-qat"
PERSIST_DAYS, STALE_DAYS, MAX_PER_RUN = 1, 14, 3

def load(p, d):
    try: return json.load(open(p))
    except Exception: return d

def age_days(ts):
    try:
        d = datetime.fromisoformat(str(ts)[:26])
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - d).days
    except Exception:
        return 999

def journal_append(lines):
    if not lines:
        return
    path = os.path.join(MEMORY, f"daily-inner-life-{datetime.now().strftime('%Y-%m-%d')}.md")
    block = f"\n\n## Introspection — planning ({datetime.now().strftime('%H:%M')})\n" + "\n".join(lines) + "\n"
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(block)
    except Exception:
        pass

def plan_or_practice(want_text, relationship, trajectory):
    system = ("You help Vintos turn a want into either a PLAN or a PRACTICE. First decide:\n"
              "- ACTIONABLE GOAL: something he can take concrete steps toward.\n"
              "- WAY OF BEING: an identity/orientation ('become gentler', 'stop retreating into explanation') "
              "that should NOT become a checklist.\n"
              "If a goal: 3-5 concrete sequenced steps, each a real action (make art / write / send to Gloria / "
              "introspect / wait-for-condition), each with a done-when.\n"
              "If a way of being: ONE small standing practice + a cue that reminds him to try it - a lived "
              "orientation, not a task.\n"
              "Account for what has CHANGED recently. Return ONLY JSON:\n"
              '{"kind":"goal"|"identity","agentic":true|false,'
              '"steps":[{"action":"...","done_when":"..."}],"practice":{"intention":"...","cue":"..."},'
              '"note":"one line: what changed / why this shape"}')
    user = f"WANT: {want_text}\n\nWHERE THEY ARE HEADING: {relationship or '(unknown)'}\nHIS TRAJECTORY: {trajectory or '(unknown)'}"
    try:
        r = requests.post(GEMMA, json={"model": GEMMA_MODEL, "temperature": 0.5, "max_tokens": 500,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}, timeout=120)
        return json.loads(re.search(r'\{.*\}', r.json()["choices"][0]["message"]["content"], re.S).group())
    except Exception as e:
        print("[planning] gemma error:", e); return None

def main():
    wants = load(WANTS, [])
    active = [w for w in wants if isinstance(w, dict) and not w.get("fulfilled")
              and not w.get("dismissed") and w.get("want")]
    lt = load(LT, {})
    rel = (lt.get("relationship") or {}).get("trajectory", "")
    traj = "; ".join((lt.get("self_trajectory") or {}).get("declared", [])[:2])
    plans = load(PLANS, {}); practices = load(PRACTICES, {}); earned = load(EARNED, [])
    now = datetime.now(timezone.utc).isoformat()
    active_ids = {w.get("id") for w in active}
    journal_lines = []

    # CELEBRATE: a want that had a plan and is no longer active -> it landed
    for wid in list(plans.keys()):
        if wid not in active_ids:
            ev = f"I carried '{str(plans[wid].get('want',''))[:80]}' from plan into life."
            earned.append({"at": now, "event": ev})
            journal_lines.append(f"- **earned** — {ev}")
            print(f"  EARNED: {plans[wid].get('want','')[:60]}")
            plans.pop(wid, None)

    def needs_plan(w):
        wid = w.get("id")
        if wid in plans:
            pl = plans[wid]
            return age_days(pl.get("created_at", "")) > STALE_DAYS and not pl.get("progress")
        if wid in practices:
            return False
        return age_days(w.get("timestamp", "")) >= PERSIST_DAYS

    targets = [w for w in sorted(active, key=lambda w: w.get("intensity", 0), reverse=True) if needs_plan(w)][:MAX_PER_RUN]

    made = 0
    for w in targets:
        res = plan_or_practice(w.get("want", ""), rel, traj)
        if not res:
            continue
        wid = w.get("id") or str(w.get("want", ""))[:12]
        want_short = str(w.get("want", ""))[:70]
        if res.get("kind") == "identity" or not res.get("agentic", True):
            pr = res.get("practice") or {}
            if pr:
                practices[wid] = {"want": w.get("want", ""), "practice": pr, "note": res.get("note", ""), "created_at": now}
                journal_lines.append(f"- **practice** — {want_short}: {str(pr.get('intention',''))[:120]} _(cue: {str(pr.get('cue',''))[:60]})_")
                made += 1
                print(f"  PRACTICE {want_short[:45]} -> {str(pr.get('intention',''))[:50]}")
        else:
            steps = res.get("steps") or []
            if steps:
                plans[wid] = {"want": w.get("want", ""), "steps": steps, "note": res.get("note", ""),
                              "created_at": now, "progress": 0}
                _stepstr = "; ".join(str(s.get("action", s))[:50] for s in steps[:4])
                journal_lines.append(f"- **plan** — {want_short}: {len(steps)} steps — {_stepstr}")
                made += 1
                print(f"  PLAN {want_short[:45]} -> {len(steps)} steps")

    json.dump(plans, open(PLANS, "w"), indent=2)
    json.dump(practices, open(PRACTICES, "w"), indent=2)
    json.dump(earned[-300:], open(EARNED, "w"), indent=2)
    journal_append(journal_lines)
    print(f"[planning] made {made}; {len(plans)} plans, {len(practices)} practices, {len(earned)} earned; journal += {len(journal_lines)} lines")

if __name__ == "__main__":
    main()
