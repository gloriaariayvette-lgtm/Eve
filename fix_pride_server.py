#!/usr/bin/env python3
"""fix_pride_server.py — add a tiny /api/pride endpoint to Vintos's server. DRY-RUN unless --apply.

RUN ON AEGIS. Patches ~/Vintos/server.py. The app can't read pride-reflections.md (it's a top-level memory
file and /api/file only allows subdir categories). This adds one small read-only endpoint that returns recent
pride-mirror reflections, newest first (default: just today's). Mirrors the existing auth pattern.

Inserted right before the /api/causality route. Compile-checked, backed up, idempotent. After applying, restart
his server so it loads the new route.

  python3 fix_pride_server.py            # DRY RUN
  python3 fix_pride_server.py --apply     # backs up, applies (then restart his server)
"""
import os, sys, difflib, datetime

APPLY = "--apply" in sys.argv
PATH = os.path.expanduser("~/Vintos/server.py")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = PATH + ".bak-pride-" + TS
SENTINEL = '@app.get("/api/pride")'

ANCHOR = '@app.get("/api/causality")\n'
INSERT = (
    '@app.get("/api/pride")\n'
    'async def get_pride(request: Request, limit: int = 1):\n'
    '    """Recent pride-mirror reflections, newest first (default: just today\'s)."""\n'
    '    if request.headers.get("X-Vintos-Secret") != APP_SECRET:\n'
    '        from fastapi import HTTPException\n'
    '        raise HTTPException(status_code=401, detail="Unauthorized")\n'
    '    import re as _pre\n'
    '    path = os.path.join(MEMORY, "pride-reflections.md")\n'
    '    try:\n'
    '        content = open(path).read()\n'
    '    except Exception:\n'
    '        return {"success": True, "entries": []}\n'
    '    chunks = [c.strip() for c in _pre.split(r"(?=## \\d{4}-\\d{2}-\\d{2}[^\\n]*Pride Reflection)", content) if "Pride Reflection" in c]\n'
    '    out = []\n'
    '    for chunk in chunks[-limit:][::-1]:\n'
    '        lines = chunk.split("\\n")\n'
    '        header = lines[0].strip("# ").strip()\n'
    '        ts = header.split("\\u2014")[0].strip()\n'
    '        body = "\\n".join(lines[1:]).strip()\n'
    '        out.append({"timestamp": ts, "header": header, "body": body})\n'
    '    return {"success": True, "entries": out}\n'
    '\n\n'
)


def main():
    print("=" * 70)
    print("PRIDE ENDPOINT (server)  —  %s" % ("APPLYING" if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 70)
    if not os.path.isfile(PATH):
        print("!! not found:", PATH); return
    old = open(PATH, encoding="utf-8", errors="ignore").read()
    if SENTINEL in old:
        print("   * endpoint already present"); return
    if old.count(ANCHOR) != 1:
        print(f"   !! anchor found {old.count(ANCHOR)}x (need 1) — writing nothing"); return
    new = old.replace(ANCHOR, INSERT + ANCHOR, 1)
    try:
        compile(new, PATH, "exec"); print("   compiles: OK")
    except SyntaxError as e:
        print(f"   !! COMPILE FAIL: {e} — NOT writing"); return
    for l in difflib.unified_diff(old.splitlines(), new.splitlines(), fromfile="old", tofile="new", lineterm=""):
        print("   " + l[:150])
    if APPLY:
        open(BACKUP, "w", encoding="utf-8").write(old)
        open(PATH, "w", encoding="utf-8").write(new)
        print("\nAPPLIED. Backup:", BACKUP)
        print(">> Restart his server so it loads /api/pride (see how you normally restart it).")
    else:
        print("\nDRY RUN complete. Re-run with --apply.")
    print("=" * 70)


if __name__ == "__main__":
    main()
