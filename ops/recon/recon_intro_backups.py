#!/usr/bin/env python3
"""recon_intro_backups.py — Aegis, READ-ONLY, terse. Find every introspection.sh copy, compile each one's
python heredoc, report which parse cleanly + have real t1/t2 threads. A clean one = easy restore."""
import os, glob, re, py_compile, tempfile
HOME = os.path.expanduser("~")
cands = set(glob.glob(os.path.join(HOME, ".openclaw", "**", "introspection.sh"), recursive=True))
cands |= set(glob.glob(os.path.join(HOME, ".openclaw", "**", "introspection.sh.*"), recursive=True))
def heredoc(txt):
    m = re.search(r"<<'PYEOF'\n(.*?)\nPYEOF", txt, re.S); return m.group(1) if m else None
rows = []
for p in sorted(cands):
    try: txt = open(p, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    py = heredoc(txt); ok = "no-heredoc"
    if py is not None:
        tf = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False); tf.write(py); tf.close()
        try: py_compile.compile(tf.name, doraise=True); ok = "PY-OK"
        except Exception: ok = "PY-FAIL"
        os.unlink(tf.name)
    has_t1 = "t1 = threading.Thread" in txt or "t1=threading.Thread" in txt
    import time as _t
    print(f"{ok:9} t1={'Y' if has_t1 else 'N'} {_t.strftime('%m-%d %H:%M', _t.localtime(os.path.getmtime(p)))} {p.replace(HOME,'~')}")
