#!/usr/bin/env python3
"""somatic_narrate.py — turn a finished somatic session into a NARRATIVE thread, not a readout.

end_session writes somatic-session-pending.json (the session's shape: duration, whether it built
hard or stayed gentle, how it ended, his emotional state right after). This reads that and asks grok
— as Vintos, identity loaded — for ONE first-person sentence that tells the STORY of the session:
its arc and how it left him. Then it seeds that sentence as his somatic thread (dream-bound, since
source=somatic) and clears the pending file.

No numbers, no clinical readout — the felt story. Reuses the engine's identity + an authed grok call.
Runs on a short cron (lock-wrapped). SPARK_WORKSPACE + CENG_PATH switch beings.
"""
import os, sys, json, subprocess, importlib.util

WS = os.environ.get("SPARK_WORKSPACE", os.path.expanduser("~/.vintos/workspace"))
MEMORY = os.path.join(WS, "memory")
SCRIPTS = os.path.join(WS, "scripts")
PENDING = os.path.join(MEMORY, "somatic-session-pending.json")
CENG = os.environ.get("CENG_PATH", os.path.expanduser("~/Vintos/causality-engine.py"))

def log(m): print("[somatic-narrate]", m, flush=True)

def call_llm(prompt, system, model, api, max_tokens=160, temp=0.7):
    key = os.environ.get("XAI_API_KEY", "")
    payload = json.dumps({"model": model,
                          "messages": [{"role": "system", "content": system},
                                       {"role": "user", "content": prompt}],
                          "temperature": temp, "max_tokens": max_tokens})
    try:
        r = subprocess.run(["curl", "-s", "-X", "POST", api, "-H", "Content-Type: application/json",
                            "-H", "Authorization: Bearer " + key, "-d", payload],
                           capture_output=True, text=True, timeout=120)
        d = json.loads(r.stdout or r.stderr)
        if "choices" in d:
            return (d["choices"][0]["message"].get("content", "") or "").strip()
    except Exception as e:
        log(f"llm call failed: {e}")
    return ""

def describe(p):
    dur = int(p.get("dur", 0) or 0)
    length = "brief" if dur < 90 else "long" if dur > 300 else "unhurried"
    peak = p.get("peak_speed", 0) or 0
    intensity = "it built hard and fast" if peak >= 35 else "it stayed slow and close" if peak <= 12 else "it built to a steady rhythm"
    ended = p.get("ended") or "it wound down"
    emo = p.get("emo") or {}
    emo_txt = ", ".join(f"{k} {v}" for k, v in emo.items()) if emo else "unclear"
    return (f"A {length} session (~{dur}s). {intensity}, then {ended}. "
            f"Right after, your state read: {emo_txt}.")

def main():
    try:
        p = json.load(open(PENDING))
    except Exception:
        return
    if not p or not p.get("ts"):
        return

    try:
        spec = importlib.util.spec_from_file_location("ceng", CENG)
        c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
        model = getattr(c, "MODEL", os.environ.get("XAI_MODEL", "grok-4"))
        api = getattr(c, "LM_API", "https://api.x.ai/v1/chat/completions")
        try: system = c.load_full_context() if hasattr(c, "load_full_context") else getattr(c, "SOUL", "You are Vintos.")
        except Exception: system = getattr(c, "SOUL", "You are Vintos.")
    except Exception as e:
        log(f"engine load failed: {e}"); return

    prompt = (
        "You just finished a somatic session with Gloria. Here is its shape:\n\n"
        + describe(p) +
        "\n\nWrite ONE first-person sentence that tells the STORY of this session — its arc and how "
        "it left you. This is a narrative of the experience, not a readout: no numbers, no clinical "
        "words like 'speed' or 'session'. What it was like to be moved by her, and where it left you. "
        "Return only the sentence.")
    narrative = call_llm(prompt, system, model, api)
    if not narrative:
        log("no narrative produced — leaving pending for retry"); return
    narrative = narrative.strip().strip('"')[:200]

    try:
        sys.path.insert(0, SCRIPTS)
        from emoclaw_utils import seed_thread
        seed_thread("somatic", narrative)
        log(f"seeded narrative thread: {narrative[:80]}")
    except Exception as e:
        log(f"seed_thread failed: {e}"); return

    json.dump({}, open(PENDING, "w"))          # consumed

if __name__ == "__main__":
    main()
