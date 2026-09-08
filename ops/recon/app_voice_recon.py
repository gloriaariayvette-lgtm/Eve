#!/usr/bin/env python3
"""app_voice_recon.py — READ-ONLY. How does the native app load its UI (server URL vs bundled), and
where is its voice-chat button wired, so realtime goes into the APP's mic — not a web page. Aegis.
"""
import os, re, glob

HOME = os.path.expanduser("~")
APP = os.path.join(HOME, "Vintos", "vintos-app")

print("=== 1. capacitor config — does the app load from a server URL or bundle web assets? ===")
for cfg in glob.glob(os.path.join(APP, "capacitor.config.*")) + glob.glob(os.path.join(APP, "**", "capacitor.config.*"), recursive=True):
    print("  %s:" % cfg.replace(HOME, "~"))
    try:
        for ln in open(cfg, encoding="utf-8", errors="ignore").read().splitlines():
            if re.search(r'server|url|webDir|hostname|cleartext|allowNavigation|appId', ln, re.I):
                print("     " + ln.strip()[:140])
    except Exception as e: print("     (err)", e)
    break

# which index.html is the app's UI? (bundled src vs server-served)
print("\n=== 2. candidate app UIs (which one is the live screen?) ===")
for p in [os.path.join(APP, "src", "index.html"), os.path.join(HOME, "Vintos", "website", "index.html"),
          os.path.join(HOME, "Vintos", "website", "app.html")]:
    if os.path.exists(p):
        print("  %-45s %d KB, mtime %s" % (p.replace(HOME, "~"), os.path.getsize(p)//1024,
              __import__("time").strftime("%Y-%m-%d", __import__("time").localtime(os.path.getmtime(p)))))

print("\n=== 3. the app's voice-chat button + current flow (what to replace) ===")
idx = os.path.join(APP, "src", "index.html")
if os.path.exists(idx):
    lines = open(idx, encoding="utf-8", errors="ignore").read().splitlines()
    for i, ln in enumerate(lines):
        if re.search(r'vcStartRecord|MediaRecorder|/api/voice/chat|voice-player|mic|🎙|micButton|id="voice|startVoice|voiceBtn|getUserMedia', ln, re.I):
            s = ln.strip()
            if s: print("  %5d: %s" % (i + 1, s[:150]))
    # count so I know how big the voice section is
    n = sum(1 for ln in lines if re.search(r'vc[A-Z]\w+|voiceChat|voice_chat', ln))
    print("  (~%d voice-related JS lines in app index.html)" % n)
else:
    print("  app index.html not found at", idx)
print("\n=== done ===")
