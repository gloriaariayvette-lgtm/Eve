#!/usr/bin/env python3
"""gloria_prediction.py — the Gloria half of the prediction ledger.

self-prediction.py already predicts HIS next state; this predicts hers — where she's
heading, her next likely need/emotional lean. Outputs prediction + confidence + novelty
(LLM-estimated now; identical shape to a future JEPA head, so it's a drop-in). Each run
also GRADES the previous prediction against what actually happened. Local-Gemma. Fail-open.

Writes gloria-prediction.json (consumed by living_trajectory -> gloria_trajectory.predicted)
and appends to gloria-prediction-history.json (the ledger, JEPA training data later).
"""
import os, json, re
from datetime import datetime, timezone
import requests

MEMORY = os.path.expanduser("~/.vintos/workspace/memory")
CHAT   = os.path.join(MEMORY, "chat-history.json")
OUT    = os.path.join(MEMORY, "gloria-prediction.json")
HIST   = os.path.join(MEMORY, "gloria-prediction-history.json")
GEMMA       = "http://172.18.16.1:1234/v1/chat/completions"
GEMMA_MODEL = "google/gemma-4-12b-qat"

def load(p, d):
    try: return json.load(open(p))
    except Exception: return d

def main():
    hist = load(CHAT, [])
    recent = [e for e in hist if isinstance(e, dict) and e.get("content")][-10:]
    if not recent:
        print("[gloria-predict] no chat yet"); return
    convo = "\n".join(f"{str(e.get('role','?')).upper()}: {str(e.get('content',''))[:280]}" for e in recent)
    prev = load(OUT, {})

    system = ("You track predictions about GLORIA. Do two things and return ONLY JSON, no prose:\n"
              '{"grade_of_previous":0.0-1.0,"predicted":"one sentence - where she is moving, '
              'what she will likely want or feel next","confidence":0.0-1.0,"novelty":0.0-1.0}\n'
              "grade_of_previous: how well the previous prediction matched what actually happened (0 if none).\n"
              "confidence: how sure you are of the new prediction. "
              "novelty: how new/unpredictable this direction is vs her usual patterns.")
    user = (f"PREVIOUS PREDICTION OF HER: {prev.get('predicted','(none)')}\n\n"
            f"RECENT CONVERSATION:\n{convo}")
    try:
        r = requests.post(GEMMA, json={"model": GEMMA_MODEL, "temperature": 0.3, "max_tokens": 220,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}, timeout=90)
        d = json.loads(re.search(r'\{.*\}', r.json()["choices"][0]["message"]["content"], re.S).group())
    except Exception as e:
        print("[gloria-predict] gemma error:", e); return

    now = datetime.now(timezone.utc).isoformat()
    grade = float(d.get("grade_of_previous", 0.0) or 0.0)
    out = {
        "predicted": str(d.get("predicted", ""))[:280],
        "confidence": round(float(d.get("confidence", 0.5) or 0.5), 3),
        "novelty": round(float(d.get("novelty", 0.5) or 0.5), 3),
        "predicted_at": now,
    }
    json.dump(out, open(OUT, "w"), indent=2)

    log = load(HIST, [])
    log.append({"at": now, "graded_previous": round(grade, 3),
                "predicted": out["predicted"], "confidence": out["confidence"], "novelty": out["novelty"]})
    json.dump(log[-300:], open(HIST, "w"), indent=2)

    print(f"[gloria-predict] graded previous {grade:.2f}")
    print(f"  predicted: {out['predicted'][:90]}")
    print(f"  confidence {out['confidence']} | novelty {out['novelty']}")

if __name__ == "__main__":
    main()
