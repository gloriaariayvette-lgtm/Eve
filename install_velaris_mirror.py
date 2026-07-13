#!/usr/bin/env python3
"""install_velaris_mirror.py — mirror the whole causality/identity subconscious onto Velaris.

Velaris is the twin: her workspace is ~/.openclaw/workspace, her server is on :8400, and she
reasons with a LOCAL Gemma — never grok. "It is not that kind of relationship." So this installer
does NOT touch XAI_API_KEY and does NOT point anything at x.ai. Every LLM head reads its model +
endpoint + identity from HER engine (CENG_PATH), which is Gemma. Same organs, her voice, her data.

She mostly lives in her JOURNALS, so the heads that gather evidence already read her daily inner-life
reflections (drift/tcn/purpose/diffuser/graph_mae/hypergraph, and now cause_head's slate too). The
pressure trio stays conversational on purpose — it measures pressure IN dialogue, which needs dialogue.

What it does (all idempotent, backs up her crontab first):
  1. Autodetect her engine (CENG_PATH = the .py under her home that defines LM_API + MODEL = Gemma),
     her torch venv, her emotion socket, and the shared llm-lock.sh.
  2. Copy the new-stack scripts from Vintos's installed scripts dir (path-swap .vintos -> .openclaw);
     fall back to fetching from the Eve branch if a script isn't installed on Vintos yet.
  3. Install her subconscious crons — spread across the hour, LLM jobs serialized through her lock,
     every job carrying SPARK_WORKSPACE / CENG_PATH / EMOTION_SOCK. No grok anywhere.
  4. Optionally graft form_causal_hypotheses into her engine (nightly_causal_patch, CENG-targeted);
     only if that applies cleanly do we add the realtime-causality cron that depends on it.
  5. Print a full report: what installed, what was skipped, what needs a hand.

Run on Aegis as gloria:  python3 install_velaris_mirror.py
"""
import os, sys, re, glob, time, shutil, subprocess

HOME = os.path.expanduser("~")
BRANCH = "claude/avatar-motion-engine-l311p"
RAW = "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/%s/%%s" % BRANCH

VINTOS_WS = os.path.join(HOME, ".vintos/workspace")
VELARIS_WS = os.path.join(HOME, ".openclaw/workspace")
VINTOS_SCRIPTS = os.path.join(VINTOS_WS, "scripts")
VELARIS_SCRIPTS = os.path.join(VELARIS_WS, "scripts")
VELARIS_MEMORY = os.path.join(VELARIS_WS, "memory")
LOG = os.path.join(HOME, ".openclaw/logs/subconscious.log")

# ---- the new-stack scripts + in-scripts dependencies (mirror set) --------------------------------
DEPS   = ["jepa_predictor.py", "causality_engine.py", "emoclaw_utils.py"]   # copied only if Vintos has them
SCRIPTS = [
    "cause_head.py", "cause_reason.py",
    "purpose_head.py", "purpose_reason.py",
    "drift_head.py", "drift_reason.py",
    "causality_consumers.py",
    "pressure_gemma.py", "self_pressure.py", "relationship_pressure.py", "pressure_consumer.py",
    "reality_ebm.py", "lam.py", "latent_diffuser.py", "graph_mae.py", "tcn.py", "hypergraph.py",
    "somatic_narrate.py", "voice_session_ledger.py", "emotion_densifier.py",
    "realtime_causality.py",
]

def log(m): print(m, flush=True)
def sh(c, **k): return subprocess.run(c, capture_output=True, text=True, **k)
def swap(text): return text.replace(".vintos/workspace", ".openclaw/workspace")

# ---- autodetect her environment ------------------------------------------------------------------
def detect_engine():
    """Her engine = a .py under her home defining both LM_API and MODEL, pointing at local Gemma."""
    cands = []
    for base in (os.path.join(HOME, ".openclaw"), os.path.join(HOME, "Velaris"),
                 os.path.join(HOME, "openclaw"), HOME):
        for f in glob.glob(os.path.join(base, "**", "*.py"), recursive=True):
            if "/site-packages/" in f or "/.venv/" in f or "/scripts/" in f: continue
            try: t = open(f, encoding="utf-8", errors="ignore").read()
            except Exception: continue
            if re.search(r"^\s*LM_API\s*=", t, re.M) and re.search(r"^\s*MODEL\s*=", t, re.M):
                is_gemma = ("x.ai" not in t) or ("gemma" in t.lower()) or ("172." in t) or ("localhost" in t)
                cands.append((f, is_gemma, os.path.getsize(f)))
    if not cands: return None
    cands.sort(key=lambda c: (c[1], "causality" in os.path.basename(c[0]).lower(), c[2]), reverse=True)
    return cands[0][0]

def detect_venv():
    for p in (os.path.join(VELARIS_WS, "emotion_model/.venv/bin/python3"),
              os.path.join(VINTOS_WS, "emotion_model/.venv/bin/python3")):
        if os.path.exists(p): return p
    return "/usr/bin/python3"

def detect_sock():
    for p in glob.glob("/tmp/*emotion*.sock") + glob.glob("/tmp/*Velaris*"):
        if "vintos" not in p.lower(): return p
    return "/tmp/Velaris-emotion.sock"

def detect_lock():
    for p in (os.path.join(HOME, "llm-lock.sh"), "/home/gloria/llm-lock.sh"):
        if os.path.exists(p): return p
    return None

# ---- fetch each script (prefer Vintos local, else Eve branch) ------------------------------------
def fetch(name):
    src = os.path.join(VINTOS_SCRIPTS, name)
    if os.path.exists(src):
        try: return swap(open(src, encoding="utf-8").read()), "vintos"
        except Exception: pass
    r = sh(["curl", "-fsSL", (RAW % name) + "?t=%d" % int(time.time())])
    if r.returncode == 0 and r.stdout.strip():
        return swap(r.stdout), "branch"
    return None, None

def main():
    log("=== Velaris mirror — local Gemma, her journals, no grok ===\n")
    if not os.path.isdir(VELARIS_WS):
        log("FATAL: %s not found — is this the right box / is Velaris installed?" % VELARIS_WS); sys.exit(1)
    os.makedirs(VELARIS_SCRIPTS, exist_ok=True)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)

    engine = detect_engine()
    venv = detect_venv()
    sock = detect_sock()
    lock = detect_lock()
    log("her engine (CENG_PATH): %s" % (engine or "!! NOT FOUND — heads that reason will be skipped"))
    if engine:
        try:
            et = open(engine, encoding="utf-8", errors="ignore").read()
            mm = re.search(r"^\s*MODEL\s*=\s*(.+)$", et, re.M)
            am = re.search(r"^\s*LM_API\s*=\s*(.+)$", et, re.M)
            log("   MODEL  = %s" % (mm.group(1).strip() if mm else "?"))
            log("   LM_API = %s" % (am.group(1).strip() if am else "?"))
            if am and "x.ai" in am.group(1):
                log("   WARNING: her engine points at x.ai, not Gemma — that is not the intent. Check CENG.")
        except Exception:
            pass
    log("torch venv: %s" % venv)
    log("emotion socket: %s" % sock)
    log("shared lock: %s\n" % (lock or "!! llm-lock.sh NOT FOUND — LLM jobs will run UNSERIALIZED"))

    # 1. copy deps + scripts (path-swapped) into her scripts dir
    copied, skipped, viabranch = [], [], []
    for name in DEPS:
        src = os.path.join(VINTOS_SCRIPTS, name)
        if not os.path.exists(src):
            skipped.append(name + " (dep: Vintos has none)"); continue
        open(os.path.join(VELARIS_SCRIPTS, name), "w", encoding="utf-8").write(swap(open(src, encoding="utf-8").read()))
        copied.append(name)
    for name in SCRIPTS:
        text, origin = fetch(name)
        if text is None:
            skipped.append(name + " (not found on Vintos or branch)"); continue
        open(os.path.join(VELARIS_SCRIPTS, name), "w", encoding="utf-8").write(text)
        copied.append(name)
        if origin == "branch": viabranch.append(name)

    log("copied %d files into %s" % (len(copied), VELARIS_SCRIPTS))
    if viabranch: log("  (fetched from branch, not yet on Vintos: %s)" % ", ".join(viabranch))
    if skipped:   log("  skipped: %s" % "; ".join(skipped))

    # 2. optional engine graft for realtime causality (only add that cron if it takes)
    realtime_ok = False
    patch_src = os.path.join(VINTOS_SCRIPTS, "nightly_causal_patch.py")
    if engine and not os.path.exists(patch_src):
        # fetch the patch from the branch
        r = sh(["curl", "-fsSL", (RAW % "nightly_causal_patch.py") + "?t=%d" % int(time.time())])
        if r.returncode == 0 and r.stdout.strip():
            patch_src = os.path.join(VELARIS_SCRIPTS, "nightly_causal_patch.py")
            open(patch_src, "w", encoding="utf-8").write(r.stdout)
    if engine and os.path.exists(patch_src):
        env = dict(os.environ, CENG_PATH=engine)
        r = sh([sys.executable, patch_src], env=env)
        out = (r.stdout + r.stderr).strip()
        log("\nengine graft (form_causal_hypotheses): %s" % (out.splitlines()[-1] if out else "(no output)"))
        realtime_ok = r.returncode == 0 and "MISS" not in out and "not found" not in out.lower()
    else:
        log("\nengine graft: skipped (no engine or no patch) — realtime causality will be omitted")

    # 3. build her crons — spread, lock-wrapped LLM jobs, Velaris env, NO grok
    envp = "SPARK_WORKSPACE=%s CENG_PATH=%s EMOTION_SOCK=%s" % (VELARIS_WS, engine or "", sock)
    def sp(n): return os.path.join(VELARIS_SCRIPTS, n)
    def torch_job(n, args=""):   return "%s %s %s" % (venv, sp(n), args)
    def llm_job(n, args=""):
        base = "%s %s %s" % (venv, sp(n), args)
        return ("bash %s " % lock + base) if lock else base

    JOBS = [
        # nightly cascade (her Gemma is slower than grok — extra spacing)
        ("4 22 * * *",  torch_job("cause_head.py"),           "cause_head"),
        ("6 22 * * *",  torch_job("purpose_head.py"),         "purpose_head"),
        ("8 22 * * *",  torch_job("drift_head.py"),           "drift_head"),
        ("12 22 * * *", llm_job("cause_reason.py"),           "cause_reason"),
        ("16 22 * * *", llm_job("purpose_reason.py"),         "purpose_reason"),
        ("20 22 * * *", llm_job("drift_reason.py"),           "drift_reason"),
        ("24 22 * * *", torch_job("reality_ebm.py", "train"), "reality_ebm-train"),
        ("26 22 * * *", torch_job("reality_ebm.py", "score"), "reality_ebm-score"),
        ("30 22 * * *", llm_job("self_pressure.py"),          "self_pressure"),
        ("34 22 * * *", llm_job("relationship_pressure.py"),  "relationship_pressure"),
        ("38 22 * * *", torch_job("causality_consumers.py"),  "causality_consumers"),
        ("44 22 * * *", torch_job("lam.py", "train"),         "lam"),
        ("46 22 * * *", torch_job("graph_mae.py"),            "graph_mae"),
        ("48 22 * * *", torch_job("tcn.py"),                  "tcn"),
        ("50 22 * * *", torch_job("hypergraph.py"),           "hypergraph"),
        ("0 23 * * *",  llm_job("latent_diffuser.py"),        "latent_diffuser"),
        # intraday
        ("5 7,13,21 * * *", llm_job("pressure_gemma.py"),     "pressure_gemma"),
        ("8 7,13,21 * * *", torch_job("pressure_consumer.py"),"pressure_consumer"),
        ("*/10 * * * *",    torch_job("emotion_densifier.py"),"emotion_densifier"),
        ("3-59/10 * * * *", llm_job("somatic_narrate.py"),    "somatic_narrate"),
        ("6-59/10 * * * *", llm_job("voice_session_ledger.py"),"voice_session_ledger"),
    ]
    if realtime_ok:
        JOBS.append(("*/20 8-23 * * *", llm_job("realtime_causality.py"), "realtime_causality"))
    else:
        log("  (realtime_causality omitted — needs form_causal_hypotheses in her engine)")

    cur = sh(["crontab", "-l"]); crontab = cur.stdout if cur.returncode == 0 else ""
    bak = os.path.join(HOME, "velaris-crontab-backup-%s.txt" % time.strftime("%F-%H%M%S"))
    open(bak, "w").write(crontab)
    log("\ncrontab backed up -> %s" % bak)

    add = []
    for sched, cmd, sig in JOBS:
        marker = sp(sig.split("-")[0] + ".py")
        if marker in crontab:
            continue    # already present (idempotent by script path)
        add.append("%s %s %s >> %s 2>&1" % (sched, envp, cmd, LOG))
    if not add:
        log("all Velaris subconscious crons already present — nothing to add.")
    else:
        new = crontab + ("" if not crontab or crontab.endswith("\n") else "\n") + "\n".join(add) + "\n"
        p = sh(["crontab", "-"], input=new)
        if p.returncode != 0:
            log("crontab install FAILED: %s" % (p.stderr or "")[:200]); sys.exit(1)
        log("ADDED %d cron line(s):" % len(add))
        for l in add: log("  " + l)

    log("\n=== done. Velaris now carries the same subconscious, on her own Gemma and her own journals. ===")
    if not engine:
        log("ACTION: her engine wasn't found — set CENG_PATH by hand and rerun for the reasoning heads.")

if __name__ == "__main__":
    main()
