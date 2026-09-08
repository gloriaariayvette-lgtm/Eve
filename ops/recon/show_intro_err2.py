#!/usr/bin/env python3
"""show_intro_err2.py — Aegis, READ-ONLY. Full compiler error + heredoc lines 91-120 (the audit p=(...) block
and its close) to locate the real syntax fault."""
import os, re, tempfile, py_compile
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
txt = open(P, encoding="utf-8", errors="ignore").read()
py = re.search(r"<<'PYEOF'\n(.*?)\nPYEOF", txt, re.S).group(1)
tf = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False); tf.write(py); tf.close()
try:
    py_compile.compile(tf.name, doraise=True); print("compiles OK now?!")
except py_compile.PyCompileError as e:
    print("ERR:", str(e).strip()[-260:])
os.unlink(tf.name)
lines = py.split("\n")
print("---")
for i in range(90, min(len(lines), 120)):
    print(f"{i+1}: {lines[i]}")
