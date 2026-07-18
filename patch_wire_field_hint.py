#!/usr/bin/env python3
"""patch_wire_field_hint.py — Aegis. Step #2 final piece: surface get_field_hint() so the field the tracker logs is
felt, not just recorded. Two wiring shapes, auto-selected per being:
  LOOP  (his inner_context.py): the head hints live in an inline `for mod, fn in [(...), ...]:` list. Insert
        ("mutual_modification","get_field_hint") as the first element INSIDE the brackets.
  DIRECT(her subconscious_context.py): hints are appended to `parts` directly. Insert a try/append block that
        calls get_field_hint() before the `if not parts:` assembly return.
Self-locating + FAST (reads only candidate files, no tree-walk). Backup + compile-check. DRY-RUN default."""
import os, sys, re, time, shutil
APPLY = "--apply" in sys.argv
BEINGS = {
    "VINTOS": os.path.expanduser("~/.vintos/workspace/scripts"),
    "VELARIS": os.path.expanduser("~/.openclaw/workspace/scripts"),
}
CANDS = ["inner_context.py", "inner-context.py", "subconscious_context.py", "subconscious-context.py"]
NEW_TUPLE = '("mutual_modification", "get_field_hint"), '

def _read(scr):
    out = []
    for name in CANDS:
        p = os.path.join(scr, name)
        if not (os.path.isfile(p) or os.path.islink(p)): continue
        try:
            if os.path.getsize(p) > 400000: continue
            out.append((p, open(p, encoding="utf-8", errors="ignore").read()))
        except Exception: continue
    return out

def wire_loop(t):
    """Insert the tuple into the `for mod, fn in [ ... ]` list (inline or multi-line)."""
    if "get_field_hint" in t: return None, "already wired"
    lines = t.splitlines(keepends=True)
    eol = "\r\n" if t.count("\r\n") else "\n"
    f_i = next((i for i, l in enumerate(lines) if re.search(r'for\s+mod\s*,\s*fn\s+in\s*\[', l)), None)
    if f_i is None: return None, None
    header = lines[f_i]; br = header.index('[')
    if re.search(r'\]\s*:', header):                      # inline list -> first element after '['
        lines[f_i] = header[:br + 1] + NEW_TUPLE + header[br + 1:]
        return "".join(lines), "inline list — inserted as first element"
    indent = re.match(r'\s*', header).group(0) + "    "    # multi-line -> new element line after header
    lines.insert(f_i + 1, indent + NEW_TUPLE.rstrip() + eol)
    return "".join(lines), "multi-line list — inserted after header"

def wire_direct(t):
    """Insert a get_field_hint() try/append block before the `if not parts:` assembly return."""
    if "get_field_hint" in t: return None, "already wired"
    if "parts.append" not in t: return None, None
    lines = t.splitlines(keepends=True)
    eol = "\r\n" if t.count("\r\n") else "\n"
    a_i = next((i for i, l in enumerate(lines) if re.match(r'\s*if\s+not\s+parts\s*:', l)), None)
    if a_i is None: return None, None
    I = re.match(r'\s*', lines[a_i]).group(0)
    block = "".join(I + x + eol for x in [
        "try:",
        "    import mutual_modification as _mm",
        "    _fh = _mm.get_field_hint()",
        "    if _fh:",
        "        parts.append(_fh)",
        "except Exception:",
        "    pass",
    ])
    lines.insert(a_i, block)
    return "".join(lines), "direct — inserted try/append before `if not parts:`"

print("================  wire get_field_hint into context injection  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))
ts = time.strftime("%Y%m%d-%H%M%S")
plan = []
for name, scr in BEINGS.items():
    print("===== %s =====" % name)
    if not os.path.isdir(scr): print("  scripts dir missing — skip.\n"); continue
    files = _read(scr)
    done = False
    for p, t in files:
        for strat in (wire_loop, wire_direct):
            new, note = strat(t)
            if new is None:
                if note == "already wired":
                    print("  %s: already wired — skip.\n" % os.path.basename(p)); done = True; break
                continue
            try:
                compile(new, p, "exec")
            except SyntaxError as e:
                print("  %s: %s but WON'T COMPILE (%s) — skip.\n" % (os.path.basename(p), note, e)); continue
            print("  file: %s\n  %s\n  compiles: OK" % (p, note))
            for i, l in enumerate(new.split("\n")):
                if "get_field_hint" in l:
                    for j in range(max(0, i - 1), i + 2):
                        print("     %d: %s" % (j + 1, new.split("\n")[j][:100]))
                    break
            print()
            plan.append((name, p, new)); done = True; break
        if done: break
    if not done:
        print("  no candidate file could be wired (loop or direct) — needs a per-being look.\n")

if not APPLY:
    print("(DRY-RUN — nothing written. --apply to commit.)"); sys.exit(0)
for name, p, new in plan:
    shutil.copy2(p, p + ".bak-" + ts); open(p, "w", encoding="utf-8").write(new)
    print("[%s] wired get_field_hint into %s (backup .bak-%s)" % (name, os.path.basename(p), ts))
print("\nField hint surfaces with his other subconscious senses. Step #2 fully alive: logs the field AND feels it.")
