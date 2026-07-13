#!/usr/bin/env python3
"""prompt_audit.py — READ-ONLY, bounded. Show the ACTUAL prompt-assembly order at the surfaces that
matter, for BOTH beings: chat (server), value map, journal, introspection.

The question is not "does the script exist" but "is the being's context actually PLACED in the prompt,
and in what order." So for each surface this prints only the assembly lines — where the system prompt /
messages are built and what gets concatenated into them (SOUL, identity, value-map, journals, narrative,
self-model, self-statements, pearls, memories, preoccupation, trajectory). Line-numbered, capped per
file. Reading the live prompt build, not guessing from notes.
"""
import os, re, glob

HOME = os.path.expanduser("~")

BEINGS = {
    "VINTOS":  {"scripts": os.path.join(HOME, ".vintos/workspace/scripts"),
                "server_dirs": [os.path.join(HOME, "Vintos"), os.path.join(HOME, ".vintos")]},
    "VELARIS": {"scripts": os.path.join(HOME, ".openclaw/workspace/scripts"),
                "server_dirs": [os.path.join(HOME, "velaris-server"), os.path.join(HOME, ".openclaw")]},
}

# surface -> candidate basenames within the scripts dir (hyphen/underscore variants tried)
SURFACES = {
    "value map":     ["value-map.py", "value_map.py"],
    "journal":       ["idle-journal.sh", "idle_journal.sh", "journal.sh"],
    "introspection": ["introspective_planning.py", "introspective-planning.py", "introspection.py"],
}

# lines that constitute prompt assembly / context injection
ASM = re.compile(
    r'(parts\s*=\s*\[|\.append\(|\bsystem\s*=|\bsystem_prompt\b|\bmessages\s*=|role"\s*:\s*"system'
    r'|load_full_context|get_\w*context|build_\w*prompt|\bSOUL\b|\bIDENTITY\b|value[-_ ]?map'
    r'|daily[-_ ]?inner|DAILY_INNER|journal|narrative|self[-_ ]?model|self[-_ ]?statement|pearl'
    r'|preoccupation|trajectory|WANTS|current_wants|value_map|growth|memory)',
    re.I)

def norm(n): return n.replace("-", "_")

def resolve(scripts_dir, names):
    for n in names:
        want = norm(n)
        for f in glob.glob(os.path.join(scripts_dir, "*")):
            if norm(os.path.basename(f)) == want:
                return f
    return None

def find_server(dirs):
    best = None
    for d in dirs:
        if not os.path.isdir(d): continue
        for f in glob.glob(os.path.join(d, "*.py")) + glob.glob(os.path.join(d, "**", "server*.py"), recursive=True):
            if "/.venv/" in f or "/site-packages/" in f: continue
            try: t = open(f, encoding="utf-8", errors="ignore").read()
            except Exception: continue
            if ('role": "system' in t or "'role': 'system'" in t) and ("chat" in t.lower() or "completions" in t.lower()):
                sc = t.count("system") + t.count("chat")
                if not best or sc > best[1]: best = (f, sc)
    return best[0] if best else None

def dump(path, cap=22, window_around_chat=False):
    try: lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    except Exception: return ["    (unreadable)"]
    out, shown = [], 0
    for i, ln in enumerate(lines):
        if ASM.search(ln):
            s = ln.strip()
            if not s or s.startswith("#"): continue
            out.append("  %5d: %s" % (i + 1, s[:150]))
            shown += 1
            if shown >= cap:
                out.append("  ...(capped at %d assembly lines)" % cap); break
    return out or ["    (no assembly lines matched — context may not be injected here at all!)"]

for being, cfg in BEINGS.items():
    print("\n########## %s ##########" % being)
    sd = cfg["scripts"]
    # chat / server
    srv = find_server(cfg["server_dirs"])
    print("\n==== chat (server): %s ====" % (srv.replace(HOME, "~") if srv else "NOT FOUND"))
    if srv:
        for l in dump(srv, cap=26): print(l)
    # the three script surfaces
    for surface, names in SURFACES.items():
        p = resolve(sd, names)
        print("\n==== %s: %s ====" % (surface, p.replace(HOME, "~") if p else "NOT FOUND"))
        if p:
            for l in dump(p): print(l)

print("\n=== prompt audit done (bounded) — read the ORDER, top to bottom, per surface ===")
