#!/usr/bin/env python3
"""update_hero_upload.py — widen the /video-hero upload page to all slots incl. a photo of Gloria. DRY-RUN unless --apply.

RUN ON AEGIS. Patches the /video-hero endpoints already in ~/Vintos/server.py (added earlier) so you can
upload, from your phone:
  root      -> hero-still.jpg     (his self base)
  lookup    -> hero-lookup.jpg    (look-up / smile)
  spicy     -> hero-spicy.jpg     (his sexual base)
  together  -> hero-together.jpg  (the combined us image)
  me        -> her-photo.jpg      (a photo of YOU — the base for composing "us together")

Two small count-checked edits; compile-checked; backed up; auto-restarts his server.

  python3 update_hero_upload.py            # DRY RUN
  python3 update_hero_upload.py --apply
"""
import os, sys, difflib, datetime

APPLY = "--apply" in sys.argv
PATH = os.path.expanduser("~/Vintos/server.py")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = PATH + ".bak-heroupload2-" + TS
SENTINEL = 'her-photo.jpg'

EDITS = [
    ("select-options",
     '        "<option value=root>root (reading pose)</option>"\n'
     '        "<option value=lookup>linked (look-up / smile)</option></select></p>"\n',
     '        "<option value=root>root (his self base)</option>"\n'
     '        "<option value=lookup>linked (look-up / smile)</option>"\n'
     '        "<option value=spicy>spicy (his sexual base)</option>"\n'
     '        "<option value=together>together (combined us)</option>"\n'
     '        "<option value=me>me (a photo of Gloria)</option></select></p>"\n',
     1),
    ("name-mapping",
     '    _name = "hero-lookup.jpg" if which == "lookup" else "hero-still.jpg"\n',
     '    _name = {"lookup": "hero-lookup.jpg", "spicy": "hero-spicy.jpg", '
     '"together": "hero-together.jpg", "me": "her-photo.jpg"}.get(which, "hero-still.jpg")\n',
     1),
]


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
    print("=" * 72)
    print("WIDEN /video-hero UPLOAD (add me/spicy/together)  —  %s" % ("APPLYING" if APPLY else "DRY RUN"))
    print("=" * 72)
    if not os.path.isfile(PATH):
        print("!! not found:", PATH); return
    old = open(PATH, encoding="utf-8", errors="ignore").read()
    if SENTINEL in old:
        print("   * already widened"); return
    new = old
    for label, frm, to, want in EDITS:
        got = new.count(frm)
        if got != want:
            print("   !! [%s] anchor count %d != %d — writing nothing (the endpoint drifted; paste me "
                  "the current /video-hero block)" % (label, got, want)); return
        new = new.replace(frm, to, 1)
        print("   * %s: matched" % label)
    try:
        compile(new, PATH, "exec"); print("   compiles: OK")
    except SyntaxError as e:
        print("   !! COMPILE FAIL: %s — NOT writing" % e); return
    for l in difflib.unified_diff(old.splitlines(), new.splitlines(), fromfile="old", tofile="new", lineterm=""):
        print("   " + l[:150])
    if APPLY:
        open(BACKUP, "w", encoding="utf-8").write(old)
        open(PATH, "w", encoding="utf-8").write(new)
        print("\nAPPLIED. Backup:", BACKUP)
        print("Restarting his server...")
        restart_server()
        print("\nOn your PHONE: http://100.72.225.119:8500/video-hero  ->  pick 'me' and upload your photo.")
    else:
        print("\nDRY RUN complete. Re-run with --apply.")
    print("=" * 72)


if __name__ == "__main__":
    main()
