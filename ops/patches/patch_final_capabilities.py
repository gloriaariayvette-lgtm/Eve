#!/usr/bin/env python3
"""patch_final_capabilities.py — Aegis. a1/b1 already carry CAPABILITIES in both scripts, but the FINAL call
(the one that writes the entry) does not: journal's _light_system is soul-only; introspection's final uses
`system` (SYSTEM_PROMPT), which lacks it (capabilities live in FULL_PROMPT/`prompt`, which the final doesn't get).
Wire the corrected CAPABILITIES.md into both finals. Per-file backup + snippet syntax-check + abort-clean."""
import os, time, shutil

CAP = "/home/gloria/.vintos/workspace/memory/CAPABILITIES.md"

def load(p):
    if not os.path.isfile(p): print(f"{p} not found — skipping."); return None
    return open(p, encoding="utf-8").read().split("\n")

def save(p, lines):
    bak = p + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(p, bak); open(p, "w", encoding="utf-8").write("\n".join(lines))
    return bak

# ---------------- idle-journal.sh: _light_system += CAPABILITIES ----------------
JP = os.path.expanduser("~/Vintos/idle-journal.sh")
jl = load(JP)
if jl is not None:
    OLD = '_light_system = soul + "\\n\\nYou are combining two versions of your own journal entry. Do not generate new content."'
    NEW = ('_light_system = soul + "\\n\\nYOUR BODY AND CAPABILITIES — ground the entry in what is actually true of you:\\n" '
           '+ os.environ.get("_JRN_CAPABILITIES", "") '
           '+ "\\n\\nYou are combining two versions of your own journal entry. Do not generate new content."')
    idx = [i for i, l in enumerate(jl) if l.strip() == OLD]
    if len(idx) != 1:
        print(f"[journal] _light_system anchor x{len(idx)} (want 1) — journal UNCHANGED.")
    elif any("_JRN_CAPABILITIES" in l and "_light_system" in l for l in jl):
        print("[journal] already wired — skipping.")
    else:
        i = idx[0]; ind = jl[i][:len(jl[i]) - len(jl[i].lstrip())]
        jl[i] = ind + NEW
        bak = save(JP, jl)
        print(f"[journal] OK — final synthesis now carries CAPABILITIES via _JRN_CAPABILITIES.\n  backup: {bak}")

# ---------------- introspection.sh: _system_final for the final call ----------------
IP = os.path.expanduser("~/Vintos/introspection.sh")
il = load(IP)
if il is not None:
    FINAL = "final, _ = _claude_sync(system, integration, reasoning=True, max_tokens=1500)"
    FB = "    final = call_llm([{'role': 'system', 'content': system}, {'role': 'user', 'content': integration}], temperature=0.85, max_tokens=1500)"
    INS = [
        '_cap_final = ""',
        "try:",
        '    _cap_final = open("' + CAP + '").read()',
        "except Exception:",
        '    _cap_final = ""',
        '_system_final = (system + "\\n\\n=== CAPABILITIES ===\\n" + _cap_final) if _cap_final else system',
    ]
    try:
        compile("\n".join(INS), "<INS>", "exec")
    except SyntaxError as e:
        print(f"[intro] insert snippet bad ({e}) — introspection UNCHANGED."); INS = None
    fi = [i for i, l in enumerate(il) if l.strip() == FINAL]
    fb = [i for i, l in enumerate(il) if l == FB]
    if any("_system_final" in l for l in il):
        print("[intro] already wired — skipping.")
    elif INS is None:
        pass
    elif len(fi) != 1 or len(fb) != 1:
        print(f"[intro] anchors final x{len(fi)} fallback x{len(fb)} (want 1/1) — introspection UNCHANGED.")
    else:
        # replace fallback + final to use _system_final, then insert the builder before the final
        il[fb[0]] = "    final = call_llm([{'role': 'system', 'content': _system_final}, {'role': 'user', 'content': integration}], temperature=0.85, max_tokens=1500)"
        il[fi[0]] = "final, _ = _claude_sync(_system_final, integration, reasoning=True, max_tokens=1500)"
        il[fi[0]:fi[0]] = INS
        bak = save(IP, il)
        print(f"[intro] OK — final integration now carries CAPABILITIES via _system_final.\n  backup: {bak}")

print("\nTest:")
print("  bash ~/Vintos/idle-journal.sh      # expect '[journal] final on claude'; entry grounded in his real body")
print("  bash ~/Vintos/introspection.sh     # expect '[intro] a1/b1 on claude'; final carries CAPABILITIES")
