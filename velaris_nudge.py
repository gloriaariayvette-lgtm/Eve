#!/usr/bin/env python3
"""velaris_nudge.py — READ-ONLY, capped. How does Velaris turn each chat message into a REAL emotional
update (model, not set numbers)? Show: her server's per-message emotion call, and the EmoClaw daemon's
command set (so I know the 'process text' command to use for Vintos). Aegis."""
import os, re, subprocess
HOME = os.path.expanduser("~")
def run(a): return subprocess.run(a, capture_output=True, text=True).stdout
def peek(path, pat, cap):
    if not os.path.isfile(path): print("  (missing", path.replace(HOME,'~'), ")"); return
    print(f"-- {path.replace(HOME,'~')} --"); n=0
    for i,l in enumerate(open(path,encoding='utf-8',errors='ignore').read().split("\n")):
        if re.search(pat,l,re.I) and l.strip() and not l.strip().startswith("#"):
            print(f"  {i+1:5}| {l.strip()[:140]}"); n+=1
            if n>=cap: break

print("=== 1) Velaris server: per-message emotion processing (not set numbers) ===")
peek(os.path.expanduser("~/velaris-server/server.py"),
     r'emotion.*sock|command.*(process|nudge|observe|feel|message)|process_message|emoclaw|sock\.send|Velaris-emotion|def .*emotion', 16)

print("\n=== 2) EmoClaw daemon — its command set ===")
# find daemon scripts via the services
for svc in ("vintos-emoclaw.service", "velaris-emoclaw.service"):
    ex = run(["bash","-lc", f"systemctl --user cat {svc} 2>/dev/null | grep -i ExecStart"]).strip()
    print(f"  {svc}: {ex[:150]}")
    m = re.search(r'(/\S+\.py)', ex)
    if m and os.path.isfile(m.group(1)):
        d = m.group(1)
        print(f"    commands handled in {d.replace(HOME,'~')}:")
        n=0
        for i,l in enumerate(open(d,encoding='utf-8',errors='ignore').read().split("\n")):
            if re.search(r'command\s*==|\.get\("command"|"command"\)\s*==|elif cmd|process|observe|nudge|def handle|model|infer|predict', l) and l.strip():
                print(f"      {i+1:5}| {l.strip()[:120]}"); n+=1
                if n>=14: break
