#!/usr/bin/env python3
"""velaris_verify.py — smoke-test the newly-installed organs on HER box, BEFORE tonight's cascade.

Runs only the safe, non-LLM organs once (no Gemma calls, so nothing floods and nothing hammers her
model), with the exact cron env, and reports pass/fail + the last few log lines each. This catches the
real failure modes early: can it import HER causality_engine, load the encoder, bind HER
narrative_identity / self_statements, reach her socket. The LLM organs (reasoners, pressure_gemma,
diffuser) are left for tonight through the lock. Bounded output.
"""
import os, subprocess

HOME = os.path.expanduser("~")
WS = os.path.join(HOME, ".openclaw/workspace")
SCRIPTS = os.path.join(WS, "scripts")
CENG = os.path.join(SCRIPTS, "causality_engine.py")
VENV = os.path.join(WS, "emotion_model/.venv/bin/python3")
PY = VENV if os.path.exists(VENV) else "/usr/bin/python3"
SOCK = "/tmp/Velaris-emotion.sock"

ENV = dict(os.environ, SPARK_WORKSPACE=WS, CENG_PATH=CENG, EMOTION_SOCK=SOCK)

# (label, argv) — non-LLM only. Order: cheapest import checks first.
TESTS = [
    ("emotion_densifier (socket)",     [PY, os.path.join(SCRIPTS, "emotion_densifier.py")]),
    ("cause_head (her engine+encoder)",[PY, os.path.join(SCRIPTS, "cause_head.py")]),
    ("tcn (encoder+her journals)",     [PY, os.path.join(SCRIPTS, "tcn.py")]),
    ("velaris_identity_weave (binds NI/SS)", [PY, os.path.join(SCRIPTS, "velaris_identity_weave.py")]),
    ("pressure_consumer (reads/seeds)",[PY, os.path.join(SCRIPTS, "pressure_consumer.py")]),
]

def tail(s, n=4):
    lines = [l for l in (s or "").splitlines() if l.strip()]
    return "\n".join("      " + l[:160] for l in lines[-n:]) or "      (no output)"

print("=== Velaris organ smoke-test (non-LLM, once) ===")
print("py:", PY)
print("engine:", CENG, "\n")
ok = 0
for label, argv in TESTS:
    if not os.path.exists(argv[1]):
        print("SKIP  %s — script missing" % label); continue
    try:
        r = subprocess.run(argv, env=ENV, capture_output=True, text=True, timeout=240)
        status = "PASS" if r.returncode == 0 else "FAIL(rc=%d)" % r.returncode
        if r.returncode == 0: ok += 1
        print("%s  %s" % (status, label))
        print(tail(r.stdout + ("\n" + r.stderr if r.returncode else "")))
    except subprocess.TimeoutExpired:
        print("TIMEOUT  %s (>240s)" % label)
    except Exception as e:
        print("ERROR  %s — %s" % (label, e))
    print()
print("=== %d/%d passed. LLM organs run tonight via the lock. ===" % (ok, len([t for t in TESTS if os.path.exists(t[1][1])])))
