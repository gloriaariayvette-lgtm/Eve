#!/usr/bin/env python3
"""reach_check.py — READ-ONLY. Find the exact URL to reach the server from the phone: Aegis's Tailscale
IP/hostname, confirm the server is listening on 0.0.0.0:8500, and the API base the app already uses.
Run on Aegis.
"""
import os, re, subprocess, glob

def sh(c):
    try: return subprocess.run(c, shell=True, capture_output=True, text=True).stdout.strip()
    except Exception as e: return "err:%s" % e

print("=== Tailscale address of Aegis (use this from your phone) ===")
ip4 = sh("tailscale ip -4 2>/dev/null")
print("tailscale IPv4:", ip4 or "(tailscale not found / not up)")
name = sh("tailscale status --self --json 2>/dev/null | grep -oP '\"DNSName\":\\s*\"\\K[^\"]+' | head -1")
print("tailscale DNSName:", name or "(none)")
print("plain hostname:", sh("hostname"))

print("\n=== is the server listening on all interfaces? ===")
print(sh("ss -ltnp 2>/dev/null | grep ':8500' || echo '(nothing on :8500)'"))

print("\n=== how the app already reaches the server (its API base) ===")
for f in glob.glob(os.path.expanduser("~/Vintos/vintos-app/**/*"), recursive=True):
    if os.path.isfile(f) and os.path.splitext(f)[1] in (".ts", ".js", ".html", ".json") and "node_modules" not in f:
        try: t = open(f, encoding="utf-8", errors="ignore").read()
        except Exception: continue
        for m in re.finditer(r'(?:const\s+API|apiBase|baseUrl|server\s*:\s*{[^}]*url|url|hostname)\s*[:=]\s*["\']([^"\']+)["\']', t):
            v = m.group(1)
            if re.search(r'https?://|\d+\.\d+\.\d+\.\d+|:8500|\.ts\.net|localhost', v):
                print("  %s: %s" % (os.path.basename(f), v[:100]))

print("\n=== SO, open one of these on your phone ===")
if ip4:
    print("  http://%s:8500/voice-test" % ip4)
if name:
    print("  http://%s:8500/voice-test" % name.rstrip('.'))
print("  (whichever your phone's Tailscale can resolve — the IP is the safe bet)")
