#!/usr/bin/env python3
"""install_scene_upload.py — add a 'trail / place' option to /video-hero so Gloria can upload a location
photo from her phone straight into his shared-images (to ground a scene). DRY-RUN unless --apply.

RUN ON AEGIS. Two count-checked edits to ~/Vintos/server.py:
  1) the upload page's <select> gains: trail / place (ground a scene)
  2) the /api/video/hero handler gains a branch: when which == "scene", the upload is written to
     ~/.vintos/workspace/memory/shared-images/from-phone-<ts>.<ext> and appended to manifest.json
     (same shape his chat-image save uses), so his video sender can ground a 'self' scene in it.

Compile-checked, backed up, auto-restarts his server.

  python3 install_scene_upload.py            # DRY RUN
  python3 install_scene_upload.py --apply
"""
import os, sys, difflib, datetime

APPLY = "--apply" in sys.argv
PATH = os.path.expanduser("~/Vintos/server.py")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = PATH + ".bak-sceneupload-" + TS
SENTINEL = 'value=scene'   # already installed?

# The handler branch, inserted right after `os.makedirs(_vd, exist_ok=True)` (handler body indent = 4).
BRANCH_LINES = [
    "if which == \"scene\":",
    "    # a real place she uploads from her phone -> shared-images, exactly like a photo she sent him",
    "    import base64 as _b64u, json as _jsu, hashlib as _hlu",
    "    from datetime import datetime as _dtu",
    "    _sd = os.path.join(MEMORY, \"shared-images\"); os.makedirs(_sd, exist_ok=True)",
    "    _raw = file.file.read()",
    "    _ext = \"png\" if _raw[:8] == b\"\\x89PNG\\r\\n\\x1a\\n\" else \"jpg\"",
    "    _sp = os.path.join(_sd, \"from-phone-%s.%s\" % (_dtu.now().strftime(\"%Y%m%d-%H%M%S\"), _ext))",
    "    open(_sp, \"wb\").write(_raw)",
    "    _man = os.path.join(_sd, \"manifest.json\")",
    "    try: _m = _jsu.load(open(_man))",
    "    except Exception: _m = []",
    "    if not isinstance(_m, list): _m = []",
    "    _m.append({\"file\": _sp, \"at\": _dtu.now().isoformat(), \"hash\": _hlu.md5(_raw).hexdigest()[:16], "
    "\"caption\": \"(uploaded from phone)\"})",
    "    try: _jsu.dump(_m[-200:], open(_man, \"w\"), indent=2)",
    "    except Exception: pass",
    "    return _HR(\"<body style=\\\"font-family:system-ui;background:#1a1714;color:#e8dcc0;padding:24px\\\">\""
    " \"<h3>Saved place photo OK — he can ground a scene in it.</h3>\""
    " \"<a style=\\\"color:#C96B3C\\\" href=\\\"/video-hero\\\">upload another</a></body>\")",
]

SELECT_FROM = '"<option value=me>me (a photo of Gloria)</option></select></p>"'
SELECT_TO = ('"<option value=me>me (a photo of Gloria)</option>"\n'
             '        "<option value=scene>trail / place (ground a scene)</option></select></p>"')

HANDLER_ANCHOR = '    _vd = os.path.join(MEMORY, "video")\n    os.makedirs(_vd, exist_ok=True)\n'


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
                print("   RESTARTED his server: %s (%s systemd)" % (svc, label)); return True
    print("   !! could not auto-restart — restart vintos-server.service manually.")
    return False


def main():
    print("=" * 78)
    print("ADD 'trail / place' UPLOAD (ground a scene from your phone)  —  %s"
          % ("APPLYING" if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 78)
    if not os.path.isfile(PATH):
        print("!! not found:", PATH); return
    old = open(PATH, encoding="utf-8", errors="ignore").read()
    if SENTINEL in old:
        print("   * already installed (scene option present) — nothing to do."); return
    new = old

    # edit 1: select option
    n1 = new.count(SELECT_FROM)
    if n1 != 1:
        print("   !! select anchor found %d times (need 1) — writing nothing. Paste the /video-hero <select> "
              "block and I'll retarget." % n1); return
    new = new.replace(SELECT_FROM, SELECT_TO, 1)
    print("   * select option: matched")

    # edit 2: handler branch
    n2 = new.count(HANDLER_ANCHOR)
    if n2 != 1:
        print("   !! handler anchor found %d times (need 1) — writing nothing." % n2); return
    branch = "".join("    " + bl + "\n" for bl in BRANCH_LINES)   # 4-space handler body indent
    new = new.replace(HANDLER_ANCHOR, HANDLER_ANCHOR + branch, 1)
    print("   * handler branch: matched")

    try:
        compile(new, PATH, "exec"); print("   compiles: OK")
    except SyntaxError as e:
        print("   !! COMPILE FAIL: %s — NOT writing" % e); return
    for l in difflib.unified_diff(old.splitlines(), new.splitlines(), fromfile="old", tofile="new", lineterm="", n=1):
        if l.startswith(("+", "-", "@@")):
            print("   " + l[:150])
    if APPLY:
        open(BACKUP, "w", encoding="utf-8").write(old)
        open(PATH, "w", encoding="utf-8").write(new)
        print("\nAPPLIED. Backup:", BACKUP)
        print("Restarting his server...")
        restart_server()
        print("\nOn your PHONE: http://100.72.225.119:8500/video-hero -> pick 'trail / place', upload the "
              "photo. It becomes the newest shared image he can ground a scene in.")
    else:
        print("\nDRY RUN complete. Re-run with --apply.")
    print("=" * 78)


if __name__ == "__main__":
    main()
