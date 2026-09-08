#!/usr/bin/env python3
"""fix_stubs.py — fill self_statements.py stub from the dash file; add load_model() to
causal_self_model.py; and pull the real /api/chat/full traceback frame. Backups + import tests. Aegis."""
import os, re, shutil, time, subprocess
HOME = os.path.expanduser("~")
SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
def run(a): return subprocess.run(a, capture_output=True, text=True)

# ---- #2 fill self_statements.py from the dash source ----
print("=== #2 self_statements.py <- self-statements.py ===")
under = os.path.join(SCRIPTS, "self_statements.py")
dash = os.path.expanduser("~/Vintos/self-statements.py")
if os.path.isfile(dash) and os.path.isfile(under) and os.path.getsize(under) == 0:
    shutil.copy2(under, under + ".bak-stub-" + time.strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(dash, under)
    print("  filled stub from dash source (%dB)" % os.path.getsize(under))
elif os.path.getsize(under) > 0:
    print("  already non-empty — leaving it")
t = run(["python3","-c", f"import sys; sys.path.insert(0,'{SCRIPTS}'); import self_statements as s; print('add_statement:', hasattr(s,'add_statement'))"])
print("  " + (t.stdout.strip() or t.stderr.strip()[:160]))

# ---- #3 add load_model() to causal_self_model.py ----
print("\n=== #3 causal_self_model.load_model() ===")
csm = os.path.join(SCRIPTS, "causal_self_model.py")
body = open(csm, encoding="utf-8").read() if os.path.isfile(csm) else ""
if "def load_model" in body:
    print("  already defined")
elif body:
    shutil.copy2(csm, csm + ".bak-loadmodel-" + time.strftime("%Y%m%d-%H%M%S"))
    add = ('\n\ndef load_model():\n'
           '    """Load the causal self-model (the json the rest of the system reads)."""\n'
           '    import json as _j, os as _o\n'
           '    try:\n'
           '        with open(_o.path.expanduser("~/.vintos/workspace/memory/causal-self-model.json")) as _f:\n'
           '            return _j.load(_f)\n'
           '    except Exception:\n'
           '        return {}\n')
    open(csm, "a", encoding="utf-8").write(add)
    print("  appended load_model()")
t = run(["python3","-c", f"import sys; sys.path.insert(0,'{SCRIPTS}'); import causal_self_model as c; print('load_model:', hasattr(c,'load_model'), '->', type(c.load_model()).__name__)"])
print("  " + (t.stdout.strip() or t.stderr.strip()[:160]))

# ---- #1 the real traceback frame ----
print("\n=== #1 real /api/chat/full traceback (exact frame) ===")
tb = run(["bash","-lc","journalctl --user -u vintos-server -n 3000 --no-pager 2>/dev/null | grep -B15 \"NameError: name 'message'\" | tail -18"]).stdout
print(tb.strip() or "  (no traceback in journal — may need /api/chat/full hit again to capture the frame)")
