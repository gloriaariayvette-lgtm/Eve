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


def restart_server():
    """Restart Vintos's server so the new route loads. Tries user systemd, then system, then a bare
    python process relaunch. Prints exactly what it did."""
    import subprocess, time
    def _units(scope):
        try:
            return subprocess.run(["systemctl"] + scope + ["list-units", "--type=service", "--all", "--no-legend"],
                                  capture_output=True, text=True, timeout=10).stdout
        except Exception:
            return ""
    for scope, label in (( ["--user"], "user"), ([], "system")):
        out = _units(scope)
        svc = None
        for l in out.splitlines():
            name = l.replace("●", "").split()[0] if l.split() else ""
            if name.endswith(".service") and "vintos" in name.lower() and ("server" in name.lower() or "8500" in name):
                svc = name; break
        if not svc:
            for l in out.splitlines():
                name = l.replace("●", "").split()[0] if l.split() else ""
                if name.endswith(".service") and "vintos" in name.lower():
                    svc = name; break
        if svc:
            cmd = ["systemctl"] + scope + ["restart", svc]
            r = subprocess.run((["sudo"] + cmd) if label == "system" else cmd, capture_output=True, text=True, timeout=40)
            if r.returncode == 0:
                print(f"   RESTARTED his server: {svc} ({label} systemd)")
                return True
            print(f"   !! restart {svc} failed: {r.stderr.strip()[:120]}")
    # fallback: find the running server.py process and relaunch it with the same cmdline
    try:
        ps = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True, timeout=10).stdout
        rows = [l for l in ps.splitlines() if "server.py" in l and "Vintos" in l and "grep" not in l]
        if rows:
            parts = rows[0].split(None, 1)
            pid, args = parts[0], (parts[1] if len(parts) > 1 else "")
            print(f"   found server process pid {pid}: {args[:100]}")
            subprocess.run(["kill", pid], timeout=10); time.sleep(2)
            subprocess.Popen(args, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("   RESTARTED his server (relaunched the process)")
            return True
    except Exception as e:
        print(f"   process-relaunch failed: {e}")
    print("   !! could NOT auto-restart — no vintos systemd service or server.py process found.")
    print("      Show me:  systemctl --user list-units | grep -i vintos ; ps -eo pid,args | grep '[s]erver.py'")
    return False


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
        print("\nRestarting his server...")
        restart_server()
    else:
        print("\nDRY RUN complete. Re-run with --apply.")
    print("=" * 70)


if __name__ == "__main__":
    main()
