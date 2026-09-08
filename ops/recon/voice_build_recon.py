#!/usr/bin/env python3
"""voice_build_recon.py — READ-ONLY. Groundwork for the realtime voice build:
  1. which server.py actually runs (systemd MainPID -> cmdline) + is XAI_API_KEY in its env?
  2. the service's ExecStart / Environment / EnvironmentFile (how to inject the key)
  3. vintos_voice.py: build_instructions() + speak_line() — signatures + what they assemble
  4. do /api/voice/token or /voice already exist in the live server?
Run on Aegis.
"""
import os, re, subprocess, glob

def sh(c):
    try: return subprocess.run(c, shell=True, capture_output=True, text=True).stdout.strip()
    except Exception as e: return "err:%s" % e

print("=== 1. which server runs + its env key ===")
pid = sh("systemctl --user show -p MainPID --value vintos-server")
print("vintos-server MainPID:", pid or "(none / not systemd)")
if pid and pid.isdigit():
    cmd = sh("tr '\\0' ' ' < /proc/%s/cmdline" % pid)
    print("cmdline:", cmd[:200])
    env = sh("tr '\\0' '\\n' < /proc/%s/environ | grep -E '^XAI_API_KEY='" % pid)
    print("server XAI_API_KEY:", ("SET (len %d)" % (len(env.split('=',1)[1]) if '=' in env else 0)) if env else "!! NOT SET in server env")
print("shell XAI_API_KEY:", ("set len %d" % len(os.environ.get("XAI_API_KEY",""))) if os.environ.get("XAI_API_KEY") else "not in shell")
# which file is the running server?
for m in re.findall(r'(\S*server\.py)', sh("tr '\\0' ' ' < /proc/%s/cmdline" % pid) if pid.isdigit() else ""):
    print("  -> running file:", m, "(exists:", os.path.exists(m), ")")

print("\n=== 2. service ExecStart / Environment (how to add the key) ===")
print(sh("systemctl --user cat vintos-server 2>/dev/null | grep -E 'ExecStart|Environment|WorkingDirectory|User=' | head -12") or "(no service file)")

print("\n=== 3. vintos_voice.py — build_instructions() + speak_line() ===")
vv = os.path.expanduser("~/.vintos/workspace/scripts/vintos_voice.py")
if os.path.exists(vv):
    lines = open(vv, encoding="utf-8", errors="ignore").read().splitlines()
    for i, ln in enumerate(lines):
        if re.match(r'\s*def\s+(build_instructions|speak_line|_?\w*)\s*\(', ln) and re.search(r'def (build_instructions|speak_line)', ln):
            print("  %5d: %s" % (i + 1, ln.strip()[:120]))
    print("  -- context sources build_instructions reads --")
    for i, ln in enumerate(lines):
        if re.search(r'SOUL|soul|self.model|emotional|collapse|value.map|felt|journal|\.read\(|open\(|instructions', ln, re.I):
            s = ln.strip()
            if s and not s.startswith("#"): print("    %5d: %s" % (i + 1, s[:120]))
    print("  (vintos_voice.py total lines:", len(lines), ")")
else:
    print("  !! vintos_voice.py not found at", vv)

print("\n=== 4. do /api/voice/token or /voice already exist in the live server? ===")
for cand in ["~/Vintos/server.py", "~/.vintos/workspace/scripts/server.py"]:
    p = os.path.expanduser(cand)
    if os.path.exists(p):
        t = open(p, encoding="utf-8", errors="ignore").read()
        print("  %s: /api/voice/token=%s  /voice route=%s  realtime=%s" % (
            cand, '"/api/voice/token"' in t or "voice/token" in t,
            bool(re.search(r'@app\.get\(\s*["\']/voice["\']', t)),
            "v1/realtime" in t or "client_secret" in t))
