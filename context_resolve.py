#!/usr/bin/env python3
"""context_resolve.py — READ-ONLY, decisive. Resolve the two open questions about the chat prompt:
  1. How is the `identity` variable built (does it include SOUL + self-model + value-map, or just SOUL)?
  2. Is the memory-block helper (pearls/dream/mirror/model-of-Gloria) actually CALLED in chat, and is
     value-map.md actually READ into the chat prompt — or generated and orphaned?

Prints: the identity-assembly lines verbatim, the full system_prompt f-string body verbatim (the true
order), the name + call-sites of the memory-block helper, and every value-map.md read with a flag for
whether it's inside the chat handler. Bounded. Vintos + Velaris.
"""
import os, re

HOME = os.path.expanduser("~")
SERVERS = {
    "VINTOS":  os.path.join(HOME, "Vintos", "server.py"),
    "VELARIS": os.path.join(HOME, "velaris-server", "server.py"),
}

def find_memory_helper(lines):
    """The function whose body spans the pearls..thirveel parts[] block (around lines 85-195)."""
    name = None
    for i in range(0, min(220, len(lines))):
        m = re.match(r'\s*def\s+(\w+)\s*\(', lines[i])
        if m:
            name = m.group(1)          # last def before ~line 195 that owns the parts[] block
        if i > 195 and name:
            break
    return name

def block(lines, lo, hi):
    out = []
    for i in range(max(0, lo), min(len(lines), hi)):
        s = lines[i].rstrip()
        if s.strip():
            out.append("  %5d: %s" % (i + 1, s[:150]))
    return out

def dump(name, path):
    print("\n########## %s : %s ##########" % (name, path.replace(HOME, "~")))
    if not os.path.exists(path):
        print("  not found"); return
    lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()

    # locate the system_prompt f-string
    sp_line = None
    for i, ln in enumerate(lines):
        if re.search(r'system_prompt\s*=\s*f?"""', ln):
            sp_line = i; break

    # 1. identity assembly: from first soul_path load up to the system_prompt line
    soul_line = None
    for i, ln in enumerate(lines):
        if i > 1800 and "soul_path" in ln:
            soul_line = i; break
    print("\n-- how `identity` is built (soul load -> system_prompt) --")
    if soul_line is not None:
        hi = sp_line if sp_line and sp_line - soul_line < 120 else soul_line + 90
        # only lines that mention identity/soul/self_model/value/emo/gloria/capabilit/read/join/=
        for i in range(soul_line, min(hi, len(lines))):
            s = lines[i].strip()
            if re.search(r'identity|soul|self[_-]?model|value[-_]?map|emo_state|gloria_model|capabilit|\.read\(|join\(|=\s*f?"', s, re.I) and not s.startswith("#"):
                print("  %5d: %s" % (i + 1, s[:150]))
    else:
        print("  (soul_path not located)")

    # 2. full system_prompt f-string body verbatim (the true order)
    print("\n-- system_prompt f-string body (verbatim, the ORDER) --")
    if sp_line is not None:
        end = sp_line
        for j in range(sp_line, min(sp_line + 80, len(lines))):
            if j > sp_line and re.search(r'"""', lines[j]):
                end = j; break
        for l in block(lines, sp_line, end + 1):
            print(l)
    else:
        print("  (system_prompt f-string not found)")

    # 3. memory-block helper: name + call sites
    helper = find_memory_helper(lines)
    print("\n-- memory-block helper: %s --" % (helper or "??"))
    if helper:
        calls = [i + 1 for i, ln in enumerate(lines) if re.search(r'\b%s\s*\(' % re.escape(helper), ln) and "def " not in ln]
        print("  call sites: %s" % (calls or "!! NEVER CALLED — memory block is orphaned, not in any prompt"))

    # 4. value-map.md reads, flagged if inside the chat handler region
    print("\n-- value-map.md reads (flag = inside chat handler) --")
    vm = [(i + 1, lines[i].strip()[:110]) for i, ln in enumerate(lines) if re.search(r'value[-_]map\.md', ln, re.I)]
    if not vm:
        print("  !! value-map.md never read in server.py — value map is NOT injected into chat")
    else:
        lo = soul_line or 2000
        for n, s in vm[:8]:
            flag = "  <-- in chat handler" if lo <= n <= lo + 260 else ""
            print("  %5d: %s%s" % (n, s, flag))

for name, path in SERVERS.items():
    dump(name, path)
print("\n=== done. identity contents + true order + whether memory-block/value-map reach chat. ===")
