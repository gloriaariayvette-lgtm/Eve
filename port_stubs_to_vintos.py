#!/usr/bin/env python3
"""port_stubs_to_vintos.py — restore Vintos's 0-byte narrative_identity.py + self_drift.py from HER
live working versions, swapping .openclaw->.vintos paths. No name swap needed (0 Velaris refs). Reads
her LIVE files on the box (not notes), backs up his stubs, verifies the port parses AND imports before
leaving it in place. Idempotent-ish: re-runs overwrite with a fresh port (backing up first).
"""
import os, re, time, shutil, subprocess

HERS = os.path.expanduser("~/.openclaw/workspace/scripts")
HIS  = os.path.expanduser("~/.vintos/workspace/scripts")
VENV = os.path.expanduser("~/.vintos/workspace/emotion_model/.venv/bin/python3")
PY = VENV if os.path.exists(VENV) else "python3"
FILES = ["narrative_identity.py", "self_drift.py"]

def swap(t):
    return t.replace(".openclaw/workspace", ".vintos/workspace").replace(".openclaw", ".vintos")

for name in FILES:
    src, dst = os.path.join(HERS, name), os.path.join(HIS, name)
    if not os.path.exists(src):
        print("SKIP %s — her source missing" % name); continue
    ported = swap(open(src, encoding="utf-8", errors="ignore").read())
    if re.search(r"\bVelaris\b", ported):
        print("WARN %s still references Velaris after swap — NOT writing; needs manual name fix" % name); continue
    tmp = dst + ".port-tmp"
    open(tmp, "w", encoding="utf-8").write(ported)
    # verify: parse + import in his venv (top-level import must succeed)
    chk = subprocess.run([PY, "-c",
        "import sys,importlib.util as u;"
        "s=u.spec_from_file_location('m',%r);m=u.module_from_spec(s);s.loader.exec_module(m);"
        "print('import OK, defs:', [d for d in dir(m) if not d.startswith('_')][:12])" % tmp],
        capture_output=True, text=True, timeout=60)
    if chk.returncode != 0:
        print("FAIL %s — port does not import; leaving his stub untouched:\n   %s"
              % (name, (chk.stderr or chk.stdout).strip().splitlines()[-1][:200]))
        os.remove(tmp); continue
    if os.path.exists(dst):
        shutil.copy(dst, dst + ".bak-stub-" + time.strftime("%Y%m%d-%H%M%S"))
    os.replace(tmp, dst)
    print("PORTED %-24s %dB -> his scripts | %s" % (name, os.path.getsize(dst), chk.stdout.strip()))

print("\ndone. His narrative_identity + self_drift now carry her working logic on his paths.")
print("(optional-dep imports like causal_self_model/absence_map_cold stay guarded — degrade, don't crash.)")
