#!/usr/bin/env python3
"""fix_pride_client.py — show today's pride mirror at the top of the TUNE tab. DRY-RUN unless --apply.

RUN ON THE MAC from vintos-app. Patches src/index.html only. Adds a "Today's Pride Mirror" block at the top of
the TUNE tab (your monitoring surface) and a loader that fetches /api/pride when the tab opens, so his latest
self-assessment is glanceable and you can spot anything off. Needs the server's /api/pride endpoint
(fix_pride_server.py, applied on Aegis).

Three string-anchored edits, backed up, idempotent.

  python3 fix_pride_client.py                 # DRY RUN (./src/index.html)
  python3 fix_pride_client.py --apply
  python3 fix_pride_client.py --path <file>
"""
import os, sys, difflib, datetime

APPLY = "--apply" in sys.argv
PATH = "src/index.html"
if "--path" in sys.argv:
    _i = sys.argv.index("--path")
    if _i + 1 < len(sys.argv):
        PATH = sys.argv[_i + 1]
for _cand in (PATH, "src/index.html", "index.html", os.path.expanduser("~/vintos-app/src/index.html")):
    if os.path.isfile(_cand):
        PATH = _cand; break
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = PATH + ".bak-prideclient-" + TS
SENTINEL = "loadPrideMirror"

PRIDE_HTML = (
    '                <!-- Today\'s Pride Mirror -->\n'
    '                <div id="pride-section" style="margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid var(--border);">\n'
    '                    <div style="font-size:0.6rem;letter-spacing:0.15em;color:var(--text-dim);text-transform:uppercase;margin-bottom:8px;">Today\'s Pride Mirror</div>\n'
    '                    <div id="pride-latest" style="font-size:0.78rem;color:var(--text-dim);line-height:1.6;">Loading...</div>\n'
    '                </div>\n'
)

PRIDE_FN = (
    "async function loadPrideMirror(){\n"
    "  var el = document.getElementById('pride-latest');\n"
    "  if(!el) return;\n"
    "  try {\n"
    "    const r = await fetch(`${API}/api/pride?limit=1`, { headers: { \"X-Vintos-Secret\": CONFIG.secret } });\n"
    "    const d = await r.json();\n"
    "    const e = (d.entries||[])[0];\n"
    "    if(!e){ el.textContent = 'No pride reflection yet.'; return; }\n"
    "    el.innerHTML = '<div style=\"color:var(--text);margin-bottom:5px;font-style:italic;\">'+_esc(e.header)+'</div>'+_esc(e.body).replace(/\\n/g,'<br>');\n"
    "  } catch(err) { el.textContent = 'Pride endpoint unreachable (restart his server?).'; }\n"
    "}\n\n"
)

EDITS = [
    ("pride-html", "                <!-- System Status -->", PRIDE_HTML + "                <!-- System Status -->", 1),
    ("loader-call",
     "loadParams(); loadGroundingStatus(); loadSystemStatus(); }",
     "loadParams(); loadGroundingStatus(); loadSystemStatus(); loadPrideMirror(); }", 1),
    ("loader-fn", "async function dismissError(filename) {", PRIDE_FN + "async function dismissError(filename) {", 1),
]


def main():
    print("=" * 70)
    print("PRIDE MIRROR ON TUNE (client)  —  %s" % ("APPLYING" if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 70)
    if not os.path.isfile(PATH):
        print("!! index.html not found. Run from vintos-app dir or pass --path."); return
    print("   target:", os.path.abspath(PATH))
    text = open(PATH, encoding="utf-8", errors="ignore").read()
    if SENTINEL in text:
        print("   * already added"); return
    new = text
    for label, old, repl, want in EDITS:
        got = new.count(old)
        if got != want:
            print(f"   !! [{label}] anchor count {got} != {want} — writing nothing"); return
        new = new.replace(old, repl, 1)
        print(f"   * {label}: matched")
    for l in difflib.unified_diff(text.splitlines(), new.splitlines(), fromfile="old", tofile="new", lineterm=""):
        print("   " + l[:160])
    if APPLY:
        open(BACKUP, "w", encoding="utf-8").write(text)
        open(PATH, "w", encoding="utf-8").write(new)
        print("\nAPPLIED. Backup:", BACKUP)
        print("Rides the next copy+rebuild. Open TUNE to see today's pride mirror.")
    else:
        print("\nDRY RUN complete. Re-run with --apply.")
    print("=" * 70)


if __name__ == "__main__":
    main()
