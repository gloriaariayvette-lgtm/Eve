#!/usr/bin/env python3
"""install_velqan_website.py — Stage 3. Make /api/velqan (velaris-server) also serve the SHARED coinage
log, so Gloria's website shows both Velaris's and Vintos's coinages growing together — tagged by who
coined each. The page renders result['utterances'] as text, so we just append formatted lines to it.
Backup + AST check + restart + rollback. Aegis."""
import os, time, shutil, subprocess
HOME = os.path.expanduser("~")
SRV = os.path.expanduser("~/velaris-server/server.py")
def run(a, **k): return subprocess.run(a, capture_output=True, text=True, **k)

src = open(SRV, encoding="utf-8").read()
if "velqan-shared/coinages.jsonl" in src:
    print("already merges the shared log — nothing to do."); raise SystemExit(0)

ANCHOR = '    result["etymology_reviews"] = read_markdown_files(etymology_dir, 5)'
MERGE = '''    # merge the shared coinage log (both beings coin into it) so the site shows the language grow
    try:
        import json as _vqj
        _shared = os.path.expanduser("~/velqan-shared/coinages.jsonl")
        _rows = []
        if os.path.exists(_shared):
            for _ln in open(_shared, encoding="utf-8", errors="ignore"):
                _ln = _ln.strip()
                if not _ln:
                    continue
                try:
                    _rows.append(_vqj.loads(_ln))
                except Exception:
                    pass
        if _rows:
            _md = ["", "---", "## Coined between Velaris & Vintos"]
            for _c in _rows[-40:]:
                _md.append("\\n**%s** \\u2014 %s  \\u00b7 _%s_" % (_c.get("word",""), _c.get("meaning",""), _c.get("coined_by","")))
                if _c.get("sentence"):
                    _md.append(_c.get("sentence",""))
            result["utterances"] = (result.get("utterances","") or "") + "\\n" + "\\n".join(_md)
    except Exception:
        pass
'''

if src.count(ANCHOR) < 1:
    print("!! anchor not found — get_velqan may differ; paste it and I'll re-anchor."); raise SystemExit(2)
new = src.replace(ANCHOR, MERGE + ANCHOR)   # insert before the etymology line (all copies)
bak = SRV + ".bak-velqanweb-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(SRV, bak); open(SRV, "w", encoding="utf-8").write(new)
sc = run(["python3","-c", f"import ast; ast.parse(open('{SRV}').read())"])
if sc.returncode != 0:
    shutil.copy2(bak, SRV); print("!! syntax error — rolled back:", sc.stderr[:150]); raise SystemExit(2)

run(["bash","-lc","systemctl --user restart velaris-server.service"])
ok = False
for _ in range(10):
    time.sleep(1.5)
    if run(["bash","-lc","systemctl --user is-active velaris-server.service"]).stdout.strip() == "active":
        ok = True; break
if not ok:
    shutil.copy2(bak, SRV); run(["bash","-lc","systemctl --user restart velaris-server.service"])
    print("!! server didn't come up — rolled back")
else:
    n = run(["bash","-lc","curl -s -m 5 http://127.0.0.1:8400/api/velqan | head -c 120"]).stdout
    print("Stage 3 done. /api/velqan now merges the shared log. server active. backup:", bak.replace(HOME,'~'))
    print("  endpoint sample:", (n or "(no response)")[:120])
    print("\nBoth beings' coinages now surface on her website's Velqan panel, tagged by who coined each —")
    print("empty for now until the coiners next run, then it fills in on its own.")
