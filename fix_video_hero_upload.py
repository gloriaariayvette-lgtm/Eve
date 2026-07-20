#!/usr/bin/env python3
"""fix_video_hero_upload.py — hero-image upload page + video-serving endpoints (server). DRY-RUN unless --apply.

RUN ON AEGIS. Patches ~/Vintos/server.py. Adds three small endpoints so the hero still can come off Gloria's
phone and clips can be delivered:
  GET  /video-hero            -> a tiny mobile upload form (open on the phone, pick image, upload)
  POST /api/video/hero        -> saves the upload to ~/.vintos/workspace/memory/video/hero-still.jpg (root)
                                 or hero-lookup.jpg (linked look-up/smile still)
  GET  /api/video/file/{name} -> serves a generated mp4 from memory/art/video (for 'arrives like a text' delivery)

Inserted before /api/pride. Compile-checked, backed up, auto-restarts his server (vintos-server.service).

  python3 fix_video_hero_upload.py            # DRY RUN
  python3 fix_video_hero_upload.py --apply     # backs up, applies, restarts server
"""
import os, sys, difflib, datetime

APPLY = "--apply" in sys.argv
PATH = os.path.expanduser("~/Vintos/server.py")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = PATH + ".bak-videohero-" + TS
SENTINEL = '/api/video/hero'

ANCHOR = '@app.get("/api/pride")\n'
INSERT = (
    '@app.get("/video-hero")\n'
    'async def video_hero_page():\n'
    '    from fastapi.responses import HTMLResponse as _HR\n'
    '    _html = ("<!doctype html><meta name=viewport content=\\"width=device-width,initial-scale=1\\">"\n'
    '        "<body style=\\"font-family:system-ui;background:#1a1714;color:#e8dcc0;padding:24px;max-width:480px;margin:auto\\">"\n'
    '        "<h3>Vintos - hero image upload</h3>"\n'
    '        "<form method=post action=\\"/api/video/hero\\" enctype=\\"multipart/form-data\\">"\n'
    '        "<p>Which still? <select name=which style=\\"padding:8px\\">"\n'
    '        "<option value=root>root (reading pose)</option>"\n'
    '        "<option value=lookup>linked (look-up / smile)</option></select></p>"\n'
    '        "<p><input type=file name=file accept=\\"image/*\\" required></p>"\n'
    '        "<p><button style=\\"padding:12px 20px;background:#C96B3C;border:0;border-radius:8px;color:#fff;font-size:16px\\">Upload</button></p>"\n'
    '        "</form></body>")\n'
    '    return _HR(_html)\n'
    '\n'
    '@app.post("/api/video/hero")\n'
    'async def video_hero_upload(which: str = Form("root"), file: UploadFile = File(...)):\n'
    '    import shutil as _sh\n'
    '    from fastapi.responses import HTMLResponse as _HR\n'
    '    _vd = os.path.join(MEMORY, "video")\n'
    '    os.makedirs(_vd, exist_ok=True)\n'
    '    _name = "hero-lookup.jpg" if which == "lookup" else "hero-still.jpg"\n'
    '    with open(os.path.join(_vd, _name), "wb") as _out:\n'
    '        _sh.copyfileobj(file.file, _out)\n'
    '    return _HR("<body style=\\"font-family:system-ui;background:#1a1714;color:#e8dcc0;padding:24px\\">"\n'
    '        "<h3>Saved " + _name + " OK</h3><a style=\\"color:#C96B3C\\" href=\\"/video-hero\\">upload another</a></body>")\n'
    '\n'
    '@app.get("/api/video/file/{filename}")\n'
    'async def video_file(filename: str):\n'
    '    import re as _vre\n'
    '    from fastapi.responses import FileResponse as _FR\n'
    '    from fastapi import HTTPException as _HE\n'
    '    if not _vre.match(r"^[\\w.\\-]+\\.mp4$", filename):\n'
    '        raise _HE(status_code=403)\n'
    '    _fp = os.path.join(MEMORY, "art", "video", filename)\n'
    '    if os.path.exists(_fp):\n'
    '        return _FR(_fp, media_type="video/mp4")\n'
    '    raise _HE(status_code=404)\n'
    '\n\n'
)


def restart_server():
    import subprocess
    for scope, label in ((["--user"], "user"), ([], "system")):
        try:
            out = subprocess.run(["systemctl"] + scope + ["list-units", "--type=service", "--all", "--no-legend"],
                                 capture_output=True, text=True, timeout=10).stdout
        except Exception:
            out = ""
        svc = None
        for l in out.splitlines():
            n = l.replace("●", "").split()[0] if l.split() else ""
            if n.endswith(".service") and "vintos" in n.lower() and ("server" in n.lower() or "8500" in n):
                svc = n; break
        if svc:
            cmd = (["sudo"] if label == "system" else []) + ["systemctl"] + scope + ["restart", svc]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
            if r.returncode == 0:
                print(f"   RESTARTED his server: {svc} ({label} systemd)"); return True
    print("   !! could not auto-restart — restart vintos-server.service manually.")
    return False


def main():
    print("=" * 70)
    print("VIDEO HERO UPLOAD + SERVE (server)  —  %s" % ("APPLYING" if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 70)
    if not os.path.isfile(PATH):
        print("!! not found:", PATH); return
    old = open(PATH, encoding="utf-8", errors="ignore").read()
    if SENTINEL in old:
        print("   * endpoints already present"); return
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
        print("Restarting his server...")
        restart_server()
        print("\nNow, on your PHONE, open:  http://100.72.225.119:8500/video-hero")
        print("Upload the reading pose as 'root', and the look-up/smile as 'lookup'.")
    else:
        print("\nDRY RUN complete. Re-run with --apply.")
    print("=" * 70)


if __name__ == "__main__":
    main()
