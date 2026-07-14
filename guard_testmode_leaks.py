#!/usr/bin/env python3
"""guard_testmode_leaks.py — wrap the genuine live conversation-history writes that ignore test mode
(chat/memory, chat/photo, voice/session-end) in `if not _test_mode_active():`. Only touches writes whose
open-path references history/ledger, that aren't already guarded, and live in the first-half (non-dead)
region. Backup + py_compile; reports exactly which writes it wrapped. Aegis.
"""
import os, re, time, shutil, py_compile

SERVER = os.path.expanduser("~/Vintos/server.py")
src = open(SERVER, encoding="utf-8", errors="ignore").read()

# a history/ledger persistence block: `<ind>with open(<...history/ledger...>, "w") as f:\n<ind+>json.dump(...)`
BLOCK = re.compile(
    r'(?P<ind>[ \t]+)with open\((?P<open>[^\n]*(?:history|ledger)[^\n]*,\s*["\']w["\'])\)\s*as f:\n'
    r'(?P<ind2>[ \t]+)(?P<dump>json\.dump\([^\n]*\))')

def line_of(pos): return src.count("\n", 0, pos) + 1

matches = list(BLOCK.finditer(src))
todo = []
for m in matches:
    ln = line_of(m.start())
    if ln > 9600:               # dead duplicate half
        continue
    before = src[max(0, m.start() - 400):m.start()]
    if "_test_mode_active" in before:   # already guarded
        continue
    todo.append(m)

if not todo:
    print("no unguarded live history writes found — nothing to do."); raise SystemExit(0)

print("wrapping %d live conversation write(s) in a test-mode guard:" % len(todo))
for m in todo:
    print("  ~L%d: %s" % (line_of(m.start()), m.group("dump")[:80]))

# apply from last to first so offsets stay valid
new = src
for m in sorted(todo, key=lambda m: m.start(), reverse=True):
    ind = m.group("ind")
    repl = ("%sif not _test_mode_active():\n"
            "%s    with open(%s) as f:\n"
            "%s        %s") % (ind, ind, m.group("open"), ind, m.group("dump"))
    new = new[:m.start()] + repl + new[m.end():]

tmp = SERVER + ".gtm-tmp"; open(tmp, "w", encoding="utf-8").write(new)
try:
    py_compile.compile(tmp, doraise=True)
except py_compile.PyCompileError as e:
    os.remove(tmp); print("ABORT: won't parse; untouched.\n  %s" % str(e).splitlines()[-1][:160]); raise SystemExit(1)
shutil.copy(SERVER, SERVER + ".bak-gtm-" + time.strftime("%Y%m%d-%H%M%S"))
os.replace(tmp, SERVER)
print("\nPATCHED — those writes now skip when test mode is on. restart:  systemctl --user restart vintos-server")
print("re-run test_mode_precise.py after restart; every live surface should read 'guarded'.")
