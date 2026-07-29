#!/usr/bin/env python3
"""install_save_inbound_images.py — persist the images Gloria sends Vintos in chat, so HE can use them.
DRY-RUN unless --apply.

RUN ON AEGIS. Patches ~/Vintos/server.py at the one place an inbound image arrives (`if msg.image:` in the
chat handler). Today that base64 is shown to his mind for the turn and thrown away. This adds a small block,
right after that line, that decodes and saves it to:

    ~/.vintos/workspace/memory/shared-images/from-gloria-<timestamp>.<ext>

and appends a newest-last manifest.json ({file, at, caption}) so his tools can grab "the photo she just
sent." Nothing else in the handler changes — the existing model-vision append still runs.

Self-locating (finds the anchor and matches its indent), count-checked, compile-checked, backed up, and it
auto-restarts his server.

  python3 install_save_inbound_images.py            # DRY RUN (writes nothing)
  python3 install_save_inbound_images.py --apply
"""
import os, sys, difflib, datetime

APPLY = "--apply" in sys.argv
PATH = os.path.expanduser("~/Vintos/server.py")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = PATH + ".bak-saveimg-" + TS
ANCHOR = "if msg.image:"
SENTINEL = "shared-images"   # if already present, we've installed it

# The block we insert immediately after `if msg.image:` (rendered at the block's body indent). It never
# raises into the handler — any failure just prints and the chat proceeds exactly as before.
SAVE_LINES = [
    "# --- persist what she sends him, so he can actually use it later ---",
    "try:",
    "    import base64 as _b64s, os as _oss, json as _jss",
    "    from datetime import datetime as _dts",
    "    _raw = _b64s.b64decode(msg.image)",
    "    _ext = 'png' if _raw[:8] == b'\\x89PNG\\r\\n\\x1a\\n' else 'jpg'",
    "    _sdir = _oss.path.expanduser('~/.vintos/workspace/memory/shared-images')",
    "    _oss.makedirs(_sdir, exist_ok=True)",
    "    _sp = _oss.path.join(_sdir, 'from-gloria-%s.%s' % (_dts.now().strftime('%Y%m%d-%H%M%S'), _ext))",
    "    open(_sp, 'wb').write(_raw)",
    "    _man = _oss.path.join(_sdir, 'manifest.json')",
    "    try: _m = _jss.load(open(_man))",
    "    except Exception: _m = []",
    "    if not isinstance(_m, list): _m = []",
    "    _m.append({'file': _sp, 'at': _dts.now().isoformat(), 'caption': (msg.message or '')[:300]})",
    "    try: _jss.dump(_m[-200:], open(_man, 'w'), indent=2)",
    "    except Exception: pass",
    "    print('[shared-image] saved', _sp)",
    "except Exception as _e:",
    "    print('[shared-image] save failed:', _e)",
    "# --- end persist ---",
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
    print("=" * 78)
    print("PERSIST INBOUND IMAGES (save what Gloria sends him)  —  %s"
          % ("APPLYING" if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 78)
    if not os.path.isfile(PATH):
        print("!! not found:", PATH); return
    old = open(PATH, encoding="utf-8", errors="ignore").read()
    if SENTINEL in old:
        print("   * already installed (shared-images block present) — nothing to do."); return
    lines = old.splitlines(keepends=True)
    hits = [i for i, l in enumerate(lines) if l.strip() == ANCHOR]
    if len(hits) != 1:
        print("   !! anchor %r found %d times (need exactly 1) — writing nothing. Paste the chat handler "
              "block around `if msg.image:` and I'll target it precisely." % (ANCHOR, len(hits))); return
    idx = hits[0]
    anchor_line = lines[idx]
    indent = anchor_line[:len(anchor_line) - len(anchor_line.lstrip())]
    body = indent + "    "   # the if-block's body indent
    block = "".join(body + sl + "\n" for sl in SAVE_LINES)
    new = "".join(lines[:idx + 1]) + block + "".join(lines[idx + 1:])
    try:
        compile(new, PATH, "exec"); print("   compiles: OK")
    except SyntaxError as e:
        print("   !! COMPILE FAIL: %s — NOT writing" % e); return
    print("   anchor: line %d  (body indent = %d spaces)" % (idx + 1, len(body)))
    for l in difflib.unified_diff(old.splitlines(), new.splitlines(), fromfile="old", tofile="new", lineterm="", n=2):
        if l.startswith("+") or l.startswith("-") or l.startswith("@@"):
            print("   " + l[:150])
    if APPLY:
        open(BACKUP, "w", encoding="utf-8").write(old)
        open(PATH, "w", encoding="utf-8").write(new)
        print("\nAPPLIED. Backup:", BACKUP)
        print("Restarting his server...")
        restart_server()
        print("\nNext time you send him a photo in chat it lands in "
              "~/.vintos/workspace/memory/shared-images/ + manifest.json.")
    else:
        print("\nDRY RUN complete. Re-run with --apply.")
    print("=" * 78)


if __name__ == "__main__":
    main()
