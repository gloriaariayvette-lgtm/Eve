#!/usr/bin/env python3
"""diag_intro_syntax.py — Aegis. Extract the python heredoc from current introspection.sh AND the pre-patch
backup, compile each, report the error line. Tells us if my patch caused the SyntaxError or it was already
corrupt. Terse."""
import os, glob, re, py_compile, tempfile
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")

def heredoc(txt):
    m = re.search(r"<<'PYEOF'\n(.*?)\nPYEOF", txt, re.S)
    return m.group(1) if m else None

def check(path, label):
    txt = open(path, encoding="utf-8", errors="ignore").read()
    py = heredoc(txt)
    if py is None:
        print(f"{label}: no PYEOF heredoc found"); return
    tf = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False); tf.write(py); tf.close()
    try:
        py_compile.compile(tf.name, doraise=True); print(f"{label}: PY OK")
    except py_compile.PyCompileError as e:
        msg = str(e).splitlines()
        line = next((l for l in msg if "line" in l.lower() or "Error" in l), msg[-1] if msg else "?")
        print(f"{label}: PY FAIL -> {line[:120]}")
    os.unlink(tf.name)

check(P, "current (patched)")
baks = sorted(glob.glob(P + ".bak-introreason-*"))
if baks: check(baks[-1], "pre-patch backup")
else: print("no pre-patch backup found")
