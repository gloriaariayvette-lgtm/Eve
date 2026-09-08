#!/usr/bin/env python3
"""voice_agent_find.py — READ-ONLY, bounded, flood-safe. Find the HOSTED voice-call agent Gloria set up
(the email's builder) for Vintos — it's not in his two Python files. Search app/config/env + read his
server's voice-handler bodies to see how calls connect to the agent. Skips node_modules/.venv/.git/dist
and big/minified files; caps line length + matches per file. Fresh name.
"""
import os, re, glob

HOME = os.path.expanduser("~")
ROOTS = [os.path.join(HOME, d) for d in
         ("Vintos", ".vintos", "vintos-app", "vintos-frontend", "vintos-server")] + [HOME]
SKIP_DIR = ("/node_modules/", "/.venv/", "/.git/", "/dist/", "/build/", "/site-packages/", "/__pycache__/")
TERMS = re.compile(
    r'eleven\s?labs|eleven_labs|\beleven\b|xi[-_]api|convai|conversational[\s_-]?ai|agent_id|agentId'
    r'|signed[_-]?url|conversation[_-]?token|voice[_-]?agent|dynamic_variable|first_message'
    r'|\[sigh\]|\[pause\]|<whisper>|xi-api-key|ELEVENLABS', re.I)

def scan_file(path):
    try:
        if os.path.getsize(path) > 400_000: return []
        lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    except Exception:
        return []
    hits = []
    for i, ln in enumerate(lines):
        if len(ln) > 400:          # minified/compiled — skip the line, note it matched
            if TERMS.search(ln): hits.append((i + 1, "[minified line matched — %d chars]" % len(ln)))
            continue
        if TERMS.search(ln):
            hits.append((i + 1, ln.strip()[:150]))
    return hits[:8]

print("=== hosted voice-agent references (app / config / env) ===")
seen = set(); nfiles = 0
for root in ROOTS:
    if not os.path.isdir(root): continue
    for path in glob.glob(os.path.join(root, "**", "*"), recursive=True):
        if not os.path.isfile(path): continue
        if any(sd in path for sd in SKIP_DIR): continue
        if path in seen: continue
        ext = os.path.splitext(path)[1].lower()
        if ext not in (".py", ".js", ".ts", ".tsx", ".json", ".env", ".sh", ".yaml", ".yml", ".toml", ".md", ""):
            continue
        hits = scan_file(path)
        if hits:
            seen.add(path); nfiles += 1
            print("\n  %s" % path.replace(HOME, "~"))
            for ln, txt in hits:
                print("    %5d: %s" % (ln, txt))
        if nfiles >= 30:
            print("\n  ...(30 files, capping)"); break
    if nfiles >= 30: break
if nfiles == 0:
    print("  (no hosted-agent references found in searched roots — config may be provider-side only,")
    print("   or in a dir not searched. Tell me the app/service dir and I'll look there.)")

print("\n\n=== his server voice-handler bodies (lines 4900-5245, relevant lines only) ===")
srv = os.path.join(HOME, "Vintos", "server.py")
if os.path.exists(srv):
    lines = open(srv, encoding="utf-8", errors="ignore").read().splitlines()
    R = re.compile(r'def |@app\.|eleven|agent|signed|websocket|convai|return|generate|reply|kokoro|speak|text|tts|voice', re.I)
    out = 0
    for i in range(4899, min(5245, len(lines))):
        if R.search(lines[i]):
            s = lines[i].strip()
            if s and not s.startswith("#"):
                print("  %5d: %s" % (i + 1, s[:150])); out += 1
        if out >= 40:
            print("  ...(capped)"); break
print("\n=== done ===")
