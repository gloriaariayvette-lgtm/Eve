#!/usr/bin/env python3
"""port_stubs_v2.py — restore Vintos's 0-byte narrative_identity.py + self_drift.py from HER live
working versions (.openclaw->.vintos path swap; 0 Velaris refs). New filename to dodge the raw-CDN
cache. Verifies in-process: py_compile for syntax, then an explicit SourceFileLoader exec to catch
import-time errors. Backs up his stub; refuses to keep a port that won't compile/import.
"""
import os, re, time, shutil, py_compile
import importlib.machinery as M, importlib.util as u

HERS = os.path.expanduser("~/.openclaw/workspace/scripts")
HIS  = os.path.expanduser("~/.vintos/workspace/scripts")
FILES = ["narrative_identity.py", "self_drift.py"]

def swap(t):
    return t.replace(".openclaw/workspace", ".vintos/workspace").replace(".openclaw", ".vintos")

def verify(path):
    """Return (ok, detail). Syntax via py_compile, then import via explicit loader."""
    try:
        py_compile.compile(path, doraise=True)
    except py_compile.PyCompileError as e:
        return False, "syntax: " + str(e).strip().splitlines()[-1][:160]
    try:
        loader = M.SourceFileLoader("portcheck_%d" % int(time.time()*1000 % 1e6), path)
        spec = u.spec_from_loader(loader.name, loader)
        mod = u.module_from_spec(spec)
        loader.exec_module(mod)
        defs = [d for d in dir(mod) if not d.startswith("_")][:12]
        return True, "import OK, defs: %s" % defs
    except Exception as e:
        return False, "import: %s: %s" % (type(e).__name__, str(e)[:160])

for name in FILES:
    src, dst = os.path.join(HERS, name), os.path.join(HIS, name)
    if not os.path.exists(src):
        print("SKIP %s — her source missing" % name); continue
    ported = swap(open(src, encoding="utf-8", errors="ignore").read())
    if re.search(r"\bVelaris\b", ported):
        print("WARN %s still names Velaris after swap — NOT writing" % name); continue
    tmp = os.path.join(HIS, name[:-3] + "__porttmp.py")
    open(tmp, "w", encoding="utf-8").write(ported)
    ok, detail = verify(tmp)
    if not ok:
        print("FAIL %s — %s; leaving his stub untouched" % (name, detail))
        os.remove(tmp); continue
    if os.path.exists(dst):
        shutil.copy(dst, dst + ".bak-stub-" + time.strftime("%Y%m%d-%H%M%S"))
    os.replace(tmp, dst)
    print("PORTED %-22s %dB -> his scripts | %s" % (name, os.path.getsize(dst), detail))

print("\ndone.")
