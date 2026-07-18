#!/usr/bin/env python3
"""patch_wire_pressure_hint.py — Aegis. Wire spark_pressure.get_pressure_context_hint into context injection, the
same way get_field_hint is wired. Inert until pressure actually acts (the hint is empty with no applied events), but
PRESENT now so it isn't lost. Two shapes, auto-selected per being:
  LOOP  (his inner_context.py): add ("spark_pressure","get_pressure_context_hint") into the inline mod/fn list.
  DIRECT(her subconscious_context.py): a try/append calling get_pressure_context_hint before `if not parts:`.
Self-locating + FAST (candidate files only). Backup + compile-check. DRY-RUN default; --apply commits."""
import os, sys, re, time, shutil
APPLY = "--apply" in sys.argv
BEINGS = {"VINTOS": os.path.expanduser("~/.vintos/workspace/scripts"),
          "VELARIS": os.path.expanduser("~/.openclaw/workspace/scripts")}
CANDS = ["inner_context.py", "inner-context.py", "subconscious_context.py", "subconscious-context.py"]
NEW_TUPLE = '("spark_pressure", "get_pressure_context_hint"), '

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
    if "get_pressure_context_hint" in t: return None, "already wired"
    lines = t.splitlines(keepends=True)
    eol = "\r\n" if t.count("\r\n") else "\n"
    f_i = next((i for i, l in enumerate(lines) if re.search(r'for\s+mod\s*,\s*fn\s+in\s*\[', l)), None)
    if f_i is None: return None, None
    header = lines[f_i]; br = header.index('[')
    if re.search(r'\]\s*:', header):
        lines[f_i] = header[:br + 1] + NEW_TUPLE + header[br + 1:]
        return "".join(lines), "inline list — inserted as first element"
    indent = re.match(r'\s*', header).group(0) + "    "
    lines.insert(f_i + 1, indent + NEW_TUPLE.rstrip() + eol)
    return "".join(lines), "multi-line list — inserted after header"

def wire_direct(t):
    if "get_pressure_context_hint" in t: return None, "already wired"
    if "parts.append" not in t: return None, None
    lines = t.splitlines(keepends=True)
    eol = "\r\n" if t.count("\r\n") else "\n"
    a_i = next((i for i, l in enumerate(lines) if re.match(r'\s*if\s+not\s+parts\s*:', l)), None)
    if a_i is None: return None, None
    I = re.match(r'\s*', lines[a_i]).group(0)
    block = "".join(I + x + eol for x in [
        "try:",
        "    import spark_pressure as _sp",
        "    _ph = _sp.get_pressure_context_hint()",
        "    if _ph:",
        "        parts.append(_ph)",
        "except Exception:",
        "    pass",
    ])
    lines.insert(a_i, block)
    return "".join(lines), "direct — inserted try/append before `if not parts:`"

print("================  wire get_pressure_context_hint into context  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))
ts = time.strftime("%Y%m%d-%H%M%S")
plan = []
for name, scr in BEINGS.items():
    print("===== %s =====" % name)
    if not os.path.isdir(scr): print("  scripts dir missing — skip.\n"); continue
    done = False
    for p, t in _read(scr):
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
                if "get_pressure_context_hint" in l:
                    for j in range(max(0, i - 1), i + 2): print("     %d: %s" % (j + 1, new.split("\n")[j][:100]))
                    break
            print()
            plan.append((name, p, new)); done = True; break
        if done: break
    if not done:
        print("  no candidate file could be wired — needs a per-being look.\n")

if not APPLY:
    print("(DRY-RUN — nothing written. --apply to commit.)"); sys.exit(0)
for name, p, new in plan:
    shutil.copy2(p, p + ".bak-" + ts); open(p, "w", encoding="utf-8").write(new)
    print("[%s] wired get_pressure_context_hint into %s (backup .bak-%s)" % (name, os.path.basename(p), ts))
print("\nPressure hint now surfaces with his other senses — empty until pressure actually acts.")
