#!/usr/bin/env python3
"""fix_all_chats.py — temporal + conversation-rhythm read chat-history.json only, so avatar/voice
talks don't count -> false 'Gloria last spoke: 4 days ago' -> false 'four days of silence' outreach.
Fix: build a merged view of ALL 3 chats (main + voice + avatar) in the same shape, and point those
scripts at it. Backups + idempotent. Then refresh temporal so it's correct now. Aegis.
"""
import os, time, shutil, subprocess

HOME = os.path.expanduser("~")
SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
MEM = os.path.expanduser("~/.vintos/workspace/memory")

# ---------- 1) install the merge helper ----------
BUILDER = os.path.join(SCRIPTS, "build_merged_chat.py")
BUILDER_SRC = r'''#!/usr/bin/env python3
"""build_merged_chat.py — unify main + voice + avatar chats into chat-history-merged.json (same
{role,content,timestamp} shape) so time/silence calcs see ALL conversations. Avatar has no per-turn
ts -> use the file mtime. Never worse than before: falls back to copying main on any error."""
import os, json, shutil
from datetime import datetime
MEM = os.path.expanduser("~/.vintos/workspace/memory")
main   = os.path.join(MEM, "chat-history.json")
voice  = os.path.join(MEM, "voice-chat-history.json")
avatar = os.path.join(MEM, "avatar-overlay-chat.json")
merged = os.path.join(MEM, "chat-history-merged.json")
def load(p):
    try:
        with open(p) as f: return json.load(f)
    except Exception: return []
def pts(s):
    try: return datetime.fromisoformat(str(s).replace("Z","+00:00")).timestamp()
    except Exception: return 0.0
out = []
try:
    for e in load(main):
        if isinstance(e, dict) and e.get("timestamp"):
            out.append({"role": e.get("role","user"), "content": e.get("content",""), "timestamp": e["timestamp"]})
    for e in load(voice):
        if not isinstance(e, dict): continue
        ts = e.get("timestamp") or ""
        if e.get("user"):   out.append({"role":"user","content":str(e["user"]),"timestamp":ts})
        if e.get("vintos"): out.append({"role":"assistant","content":str(e["vintos"]),"timestamp":ts})
    if os.path.exists(avatar):
        amt = datetime.fromtimestamp(os.path.getmtime(avatar)).isoformat()
        for e in load(avatar):
            if isinstance(e, dict) and e.get("content"):
                out.append({"role": e.get("role","user"), "content": str(e.get("content","")), "timestamp": e.get("timestamp") or amt})
    out = [e for e in out if pts(e.get("timestamp")) > 0]
    out.sort(key=lambda e: pts(e["timestamp"]))
    if not out: raise ValueError("empty")
    with open(merged, "w") as f: json.dump(out, f)
except Exception:
    try: shutil.copy2(main, merged)
    except Exception: pass
'''
open(BUILDER, "w").write(BUILDER_SRC)
os.chmod(BUILDER, 0o755)
print("installed:", BUILDER.replace(HOME, "~"))

# ---------- 2) patch the readers ----------
BUILD_CALL = 'python3 "$HOME/.vintos/workspace/scripts/build_merged_chat.py" >/dev/null 2>&1 || true'
targets = [
    os.path.join(SCRIPTS, "temporal-context.sh"),
    os.path.join(HOME, "Vintos", "temporal-context.sh"),
    os.path.join(SCRIPTS, "conversation-rhythm.sh"),
    os.path.join(HOME, "Vintos", "conversation-rhythm.sh"),
]
for f in targets:
    if not os.path.isfile(f): continue
    src = open(f, encoding="utf-8").read()
    if "chat-history-merged.json" in src:
        print("  already merged:", f.replace(HOME, "~")); continue
    new = src
    new = new.replace('CHAT_HISTORY="$MEMORY/chat-history.json"',
                      BUILD_CALL + '\nCHAT_HISTORY="$MEMORY/chat-history-merged.json"', 1)
    new = new.replace('os.path.expanduser("~/.vintos/workspace/memory/chat-history.json")',
                      'os.path.expanduser("~/.vintos/workspace/memory/chat-history-merged.json")', 1)
    if new == src:
        print("  !! no anchor changed in", f.replace(HOME, "~"), "(left untouched)"); continue
    shutil.copy2(f, f + ".bak-allchats-" + time.strftime("%Y%m%d-%H%M%S"))
    open(f, "w", encoding="utf-8").write(new)
    print("  patched:", f.replace(HOME, "~"))

# ---------- 3) build now + refresh temporal ----------
print("\nbuilding merged view now...")
subprocess.run(["python3", BUILDER], timeout=30)
mp = os.path.join(MEM, "chat-history-merged.json")
if os.path.isfile(mp):
    import json
    m = json.load(open(mp))
    last_user = next((e for e in reversed(m) if e.get("role") == "user"), None)
    print("  merged entries:", len(m))
    if last_user: print("  last Gloria message in merged:", last_user.get("timestamp"))

# refresh temporal-context.txt from whichever temporal script the cron uses
cron = subprocess.run(["bash", "-lc", "crontab -l 2>/dev/null | grep -i temporal-context | grep -v '^#' | head -1"],
                      capture_output=True, text=True).stdout
tsh = None
for cand in (os.path.join(HOME, "Vintos", "temporal-context.sh"), os.path.join(SCRIPTS, "temporal-context.sh")):
    if cand in cron and os.path.isfile(cand): tsh = cand; break
tsh = tsh or (os.path.join(HOME, "Vintos", "temporal-context.sh") if os.path.isfile(os.path.join(HOME, "Vintos", "temporal-context.sh")) else None)
if tsh:
    print("\nrefreshing temporal via", tsh.replace(HOME, "~"), "...")
    try: subprocess.run(["bash", tsh], timeout=60, capture_output=True, text=True)
    except Exception as e: print("  (run note:", e, ")")
tct = os.path.join(MEM, "temporal-context.txt")
if os.path.isfile(tct):
    print("\n=== temporal-context.txt now ===")
    for line in open(tct, encoding="utf-8", errors="ignore").read().split("\n"):
        if any(k in line for k in ("last spoke", "Conversations with Gloria today", "Day density")):
            print("  " + line)
