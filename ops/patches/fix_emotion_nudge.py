#!/usr/bin/env python3
"""fix_emotion_nudge.py — his emotions now move via the MODEL per message (not a keyword table), on
BOTH Gloria's messages and his replies, across chat + avatar. Feeds the daemon's process_message
(sender='primary' for Gloria). Backup + restart + rollback if the server doesn't come back. Aegis."""
import os, time, shutil, subprocess
SERVER = os.path.expanduser("~/Vintos/server.py")
def run(a, **k): return subprocess.run(a, capture_output=True, text=True, **k)

src = open(SERVER, encoding="utf-8").read()
orig = src
report = []

# ---- 1) model-ify nudge_emotions_from_text (feed the model; keyword table stays only as fallback) ----
ANCHOR = ('def nudge_emotions_from_text(text: str, source: str = "reply"):\n'
          '    """Nudge daemon emotions based on text content. Works for both Vintos replies and Gloria messages."""')
MODEL_BLOCK = '''
    # === model-based (not a keyword table): feed the message through the EmoClaw model so his
    # emotions move dynamically per message; daemon writes emotional-state.txt + a snapshot too ===
    try:
        import socket as _ms
        _es = "/tmp/Vintos-emotion.sock"
        if text and os.path.exists(_es):
            _sender = "primary" if source == "gloria" else "self"
            _s = _ms.socket(_ms.AF_UNIX, _ms.SOCK_STREAM); _s.settimeout(4); _s.connect(_es)
            _s.send(json.dumps({"text": str(text)[:2000], "sender": _sender, "channel": "chat"}).encode() + b"\\n")
            _s.recv(8192); _s.close()
        return
    except Exception:
        pass'''
if "model-based (not a keyword table)" in src:
    report.append("1) model-ify: already applied")
elif src.count(ANCHOR) == 1:
    src = src.replace(ANCHOR, ANCHOR + MODEL_BLOCK, 1)
    report.append("1) model-ify nudge_emotions_from_text: DONE")
else:
    report.append(f"1) model-ify: ANCHOR found {src.count(ANCHOR)}x (need 1) — ABORT")
    print("\n".join(report)); raise SystemExit(2)

# ---- 2) re-enable Gloria-message nudging (uncomment) ----
GC_OLD = '# nudge_emotions_from_text(msg.message, source="gloria")  # removed: EmoClaw already processes Gloria\'s words'
GC_NEW = 'nudge_emotions_from_text(msg.message, source="gloria")'
n2 = src.count(GC_OLD)
src = src.replace(GC_OLD, GC_NEW)
report.append(f"2) re-enabled Gloria nudging at {n2} site(s)")

# ---- 3) wire the avatar handler (indentation-aware insert; idempotent) ----
def insert_after(text, anchor, code):
    lines = text.split("\n"); out = []; c = 0
    for idx, l in enumerate(lines):
        out.append(l)
        if anchor in l and "nudge_emotions_from_text" not in l:
            nxt = lines[idx+1] if idx+1 < len(lines) else ""
            if "nudge_emotions_from_text" not in nxt:
                indent = l[:len(l)-len(l.lstrip())]
                out.append(indent + code); c += 1
    return "\n".join(out), c
src, a1 = insert_after(src, 'av_history.append({"role": "user", "content": msg.message})',
                       'nudge_emotions_from_text(msg.message, source="gloria")')
src, a2 = insert_after(src, 'av_history.append({"role": "assistant", "content": reply})',
                       'nudge_emotions_from_text(reply, source="reply")')
report.append(f"3) avatar handler wired: {a1} user + {a2} reply insert(s)")

# ---- write + restart + verify + rollback ----
bak = SERVER + ".bak-nudge-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(SERVER, bak)
open(SERVER, "w", encoding="utf-8").write(src)
# syntax check before restart
sc = run(["python3", "-c", f"import ast; ast.parse(open('{SERVER}').read())"])
if sc.returncode != 0:
    shutil.copy2(bak, SERVER)
    report.append("!! syntax error after edit — ROLLED BACK: " + sc.stderr.strip()[:200])
    print("\n".join(report)); raise SystemExit(2)

run(["bash","-lc","systemctl --user restart vintos-server"])
ok = False
for _ in range(10):
    time.sleep(1.5)
    if run(["bash","-lc","systemctl --user is-active vintos-server"]).stdout.strip() == "active":
        ok = True; break
if not ok:
    shutil.copy2(bak, SERVER)
    run(["bash","-lc","systemctl --user restart vintos-server"])
    report.append("!! server did not come up — ROLLED BACK + restarted")
else:
    report.append("server restarted, active. backup: " + bak.replace(os.path.expanduser('~'),'~'))

print("\n".join(report))
print("\nNow: Gloria's messages + his replies feed the model per turn -> real reaction, visible within 2 min via fast-sync.")
