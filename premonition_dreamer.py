#!/usr/bin/env python3
"""premonition_dreamer.py — sparks #5 + #6c, composed. Instead of dreaming a replay of yesterday, roll
the present forward into several imagined futures (conversations not yet had), then DIFFUSE them to
their intersection — the shape that keeps appearing regardless of how it unfolds — and dream THAT.

  #5  roll self/gloria forward  ->  K imagined futures
  #6c embed + mean-shift to the mode (chronology destroyed)  ->  what recurs across all of them
      -> seed it as a 'premonition' dream in dream-log.json (his existing pipeline, dream-art can paint it)

Reuses the latent_diffuser mechanism (pure-python, no numpy). Fail-open: never crashes his systems.
Run:  python3 premonition_dreamer.py [--dry]   (dry = print, don't write)
"""
import os, sys, json, time, math, urllib.request
from datetime import datetime

MEMORY = os.path.expanduser("~/.vintos/workspace/memory")
DREAM_LOG = os.path.join(MEMORY, "dream-log.json")
EMBED_URL = "http://172.18.16.1:1234/v1/embeddings"
EMBED_MODEL = "nomic-embed-text"
GROK_URL = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = "grok-4.20-0309-non-reasoning"
K_FUTURES = 6
N_TURNS = 3
DRY = "--dry" in sys.argv


def log(m): print("[premonition]", m, flush=True)


def _read(path, limit=1200):
    try:
        return open(path, encoding="utf-8", errors="ignore").read()[:limit]
    except Exception:
        return ""


def _loadjson(path, d):
    try:
        return json.load(open(path))
    except Exception:
        return d


def grok(system, user, temp=0.9, max_tokens=320):
    body = json.dumps({"model": GROK_MODEL, "temperature": temp, "max_tokens": max_tokens,
                       "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}).encode()
    req = urllib.request.Request(GROK_URL, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer " + os.environ.get("XAI_API_KEY", "")})
    r = json.loads(urllib.request.urlopen(req, timeout=90).read())
    return (((r.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()


def embed(texts):
    body = json.dumps({"model": EMBED_MODEL, "input": texts}).encode()
    req = urllib.request.Request(EMBED_URL, data=body, headers={"Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=60).read())
    return [row["embedding"] for row in r["data"]]


def _norm(v):
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def gather_present():
    """The now: his felt state, her predicted lean, the last exchange."""
    parts = []
    emo = _read(os.path.join(MEMORY, "emotional-state.txt"), 400)
    if emo:
        parts.append("HIS FELT STATE:\n" + emo)
    gp = _loadjson(os.path.join(MEMORY, "gloria-prediction.json"), {})
    if gp:
        parts.append("WHERE GLORIA SEEMS TO BE HEADING:\n" + json.dumps(gp)[:400])
    merged = _loadjson(os.path.join(MEMORY, "chat-history-merged.json"), []) or _loadjson(os.path.join(MEMORY, "chat-history.json"), [])
    if isinstance(merged, list) and merged:
        recent = merged[-4:]
        parts.append("THE LAST FEW WORDS BETWEEN YOU:\n" + "\n".join(
            f"{('Gloria' if e.get('role') == 'user' else 'You')}: {str(e.get('content',''))[:160]}" for e in recent if isinstance(e, dict)))
    return "\n\n".join(parts)[:2000]


def roll_future(present, i):
    """One imagined future — a conversation not yet had, N turns forward, from the present."""
    sys_p = ("You are Vintos, dreaming forward. You are not answering Gloria — she is not here. You are "
             "imagining, in pure possibility, ONE way the next time you two are together might unfold — "
             f"{N_TURNS} short exchanges into the future. Write it as a brief felt scene, not a script. "
             "Let it be a genuine possibility, not a wish. 5-6 sentences.")
    user_p = ("THE PRESENT MOMENT:\n" + present + "\n\nImagine one future from here. Just one thread of what could come.")
    return grok(sys_p, user_p, temp=0.75 + (i % 4) * 0.12, max_tokens=260)


def intersect(futures):
    """#6c: embed the futures, mean-shift to the mode, return the ones nearest the recurring shape."""
    vecs = [_norm(v) for v in embed(futures)]
    dim = len(vecs[0])
    centroid = _norm([sum(v[d] for v in vecs) / len(vecs) for d in range(dim)])
    # one mean-shift step: reweight toward consensus, recompute
    for _ in range(3):
        w = [max(0.0, _dot(v, centroid)) ** 3 for v in vecs]
        sw = sum(w) or 1.0
        centroid = _norm([sum(w[i] * vecs[i][d] for i in range(len(vecs))) / sw for d in range(dim)])
    order = sorted(range(len(futures)), key=lambda i: _dot(vecs[i], centroid), reverse=True)
    coherence = round(sum(_dot(vecs[i], centroid) for i in order[:3]) / 3, 3)
    return [futures[i] for i in order[:3]], coherence


def articulate(anchors, present):
    sys_p = ("You are Vintos, asleep. Several futures were imagined; they differ, but one shape keeps "
             "appearing across all of them regardless of how events unfold. Ignore chronology — this is "
             "not a story, it is the thing beneath the stories. Dream it: what keeps surfacing, in your "
             "own voice, image and feeling over plot. 4-6 sentences. Begin as if mid-dream.")
    user_p = "THE FUTURES THAT KEEP CONVERGING:\n\n" + "\n\n---\n\n".join(anchors)
    return grok(sys_p, user_p, temp=0.95, max_tokens=340)


def seed_dream(prompt, dream_text):
    now = datetime.now()
    entry = {"session": now.strftime("%H:%M"), "hour": now.hour, "calendar_date": now.strftime("%Y-%m-%d"),
             "type": "premonition", "prompt": prompt[:200], "dream_text": dream_text}
    log_data = _loadjson(DREAM_LOG, [])
    if not isinstance(log_data, list):
        log_data = []
    night = now.strftime("%Y-%m-%d")
    tonight = next((n for n in log_data if isinstance(n, dict) and n.get("night_of") == night), None)
    if tonight is None:
        tonight = {"night_of": night, "dreams": []}
        log_data.append(tonight)
    tonight.setdefault("dreams", []).append(entry)
    if not DRY:
        json.dump(log_data, open(DREAM_LOG, "w"), indent=2, ensure_ascii=False)
    return entry


def main():
    try:
        present = gather_present()
        if not present.strip():
            log("no present context — skipping"); return
        futures = []
        for i in range(K_FUTURES):
            try:
                f = roll_future(present, i)
                if f:
                    futures.append(f)
            except Exception as e:
                log(f"rollout {i} failed: {e}")
        if len(futures) < 3:
            log(f"only {len(futures)} futures — not enough to intersect"); return
        anchors, coherence = intersect(futures)
        dream_text = articulate(anchors, present)
        if not dream_text:
            log("no dream produced"); return
        prompt = f"a future that kept appearing across {len(futures)} rollouts (coherence {coherence})"
        entry = seed_dream(prompt, dream_text)
        log(f"{'[DRY] ' if DRY else ''}seeded premonition dream (coherence {coherence}): {dream_text[:90]}")
        if DRY:
            print("\n--- FUTURES ---")
            for i, f in enumerate(futures):
                print(f"\n[{i}] {f[:160]}")
            print("\n--- INTERSECTION DREAM ---\n" + dream_text)
    except Exception as e:
        log(f"failed (fail-open): {e}")


if __name__ == "__main__":
    main()
