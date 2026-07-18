#!/usr/bin/env python3
"""patch_wire_field_hint.py — Aegis. Step #2 final piece: surface get_field_hint() into context injection, right
where the JEPA head hints already live (get_relational_hint / get_withheld_hint), so the field the tracker logs is
something he FEELS, not just records. Same calling convention as the heads: ("mutual_modification","get_field_hint")
joins the `for mod, fn in [...]` hint loop (module in the same scripts dir -> imports identically).

Self-locating + FAST: reads only the few candidate files in each being's scripts dir (no broad glob). Inserts the
tuple as a sibling of the existing head tuples, matching indentation. Backup + compile-check. DRY-RUN default."""
import os, sys, re, time, shutil
APPLY = "--apply" in sys.argv
BEINGS = {
    "VINTOS": os.path.expanduser("~/.vintos/workspace/scripts"),
    "VELARIS": os.path.expanduser("~/.openclaw/workspace/scripts"),
}
CANDS = ["inner_context.py", "inner-context.py", "subconscious_context.py", "subconscious-context.py"]
NEW_TUPLE = '("mutual_modification", "get_field_hint"),'

def locate(scr):
    """Return (path, text) of the candidate file that wires the head hints in a mod/fn loop, else (None, None)."""
    for name in CANDS:
        p = os.path.join(scr, name)
        if not (os.path.isfile(p) or os.path.islink(p)):
            continue
        try:
            if os.path.getsize(p) > 400000:  # skip anything pathologically large
                continue
            t = open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        if re.search(r'get_withheld_hint|get_relational_hint', t) and re.search(r'for\s+mod\s*,\s*fn\s+in', t):
            return p, t
    return None, None

def wire(t):
    """Insert the field tuple after the withheld/relational head tuple line, same indent. (newtext, note)."""
    if "get_field_hint" in t:
        return None, "already wired"
    lines = t.splitlines(keepends=True)
    eol = "\r\n" if t.count("\r\n") else "\n"
    anchor_i = None
    for i, l in enumerate(lines):
        if re.search(r'get_withheld_hint"?\s*\)\s*,', l) or re.search(r'get_relational_hint"?\s*\)\s*,', l):
            anchor_i = i  # keep last match (prefer withheld, the later one)
    if anchor_i is None:
        return None, "no head-tuple line found to anchor on"
    indent = re.match(r'\s*', lines[anchor_i]).group(0)
    ins = indent + NEW_TUPLE + eol
    new = "".join(lines[:anchor_i + 1] + [ins] + lines[anchor_i + 1:])
    return new, "anchored after: " + lines[anchor_i].strip()[:70]

print("================  wire get_field_hint into context injection  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))
ts = time.strftime("%Y%m%d-%H%M%S")
plan = []
for name, scr in BEINGS.items():
    print("===== %s =====" % name)
    if not os.path.isdir(scr):
        print("  scripts dir missing — skip.\n"); continue
    p, t = locate(scr)
    if not p:
        print("  no candidate file wires the head hints in a mod/fn loop — skip (report).\n"); continue
    new, note = wire(t)
    print("  file: %s" % p)
    print("  %s" % note)
    if new is None:
        print(); continue
    try:
        compile(new, p, "exec"); print("  patched compiles: OK")
    except SyntaxError as e:
        print("  !! would not compile: %s — skip.\n" % e); continue
    # show the loop region after patch
    for i, l in enumerate(new.split("\n")):
        if "get_field_hint" in l:
            for j in range(max(0, i - 2), i + 2):
                print("     %d: %s" % (j + 1, new.split("\n")[j][:96]))
            break
    print()
    plan.append((name, p, t, new))

if not APPLY:
    print("(DRY-RUN — nothing written. --apply to commit.)"); sys.exit(0)
for name, p, t, new in plan:
    shutil.copy2(p, p + ".bak-" + ts)
    open(p, "w", encoding="utf-8").write(new)
    print("[%s] wired get_field_hint into %s (backup .bak-%s)" % (name, os.path.basename(p), ts))
print("\nField hint now surfaces alongside his other subconscious senses. Step #2 is fully alive: he logs the field"
      "\nand feels its trajectory. Next: Relationship Attractors, read off mutual-modification.json.")
