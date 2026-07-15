#!/usr/bin/env python3
"""wire_temperature.py — Aegis. Make temperature triage-native. (1) Install the refactored, import-safe
thread_temperature.py into the scripts dir. (2) Patch thread-triage.py so its __main__ block calls
thread_temperature.run(apply=True, quiet=True) right after main() — every triage pass tags temperature +
stability just after it sets pull. Backup + py_compile + rollback. Idempotent. Aborts (never mangles) if
the __main__ anchor isn't the standard plain main() call."""
import os, shutil, time, urllib.request, py_compile
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
DEST = os.path.join(SC, "thread_temperature.py")
TT = os.path.join(SC, "thread-triage.py")
RAW = "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/claude/avatar-motion-engine-l311p/thread_temperature.py"
TS = time.strftime("%Y%m%d-%H%M%S")
def sh(p): return p.replace(HOME, "~")

# ---- (1) install the module
data = urllib.request.urlopen(RAW + "?t=" + str(int(time.time())), timeout=30).read().decode()
if "def run(apply=False" not in data:
    raise SystemExit("ABORT: fetched module isn't the refactored run()-exposing version.")
open(DEST, "w", encoding="utf-8").write(data); os.chmod(DEST, 0o755)
try:
    py_compile.compile(DEST, doraise=True)
except py_compile.PyCompileError as e:
    raise SystemExit("ABORT: installed module failed to compile: " + str(e)[:160])
print("(1) installed", sh(DEST))

# ---- (2) patch thread-triage.py __main__ block
src = open(TT, encoding="utf-8", errors="ignore").read()
if "thread_temperature" in src:
    print("(2) thread-triage.py already wired — skipping."); raise SystemExit(0)
lines = src.split("\n")
# find the __main__ block
mi = None
for i, l in enumerate(lines):
    if l.strip().replace('"', "'") == "if __name__ == '__main__':":
        mi = i
if mi is None:
    print("(2) ABORT: no __main__ block found. bottom 20 lines for manual wiring:")
    for l in lines[-20:]:
        print("   |", l)
    raise SystemExit(1)
# find the main() call line within the block
main_line = None
body_indent = 4
for j in range(mi + 1, len(lines)):
    s = lines[j].strip()
    if s == "":
        continue
    ind = len(lines[j]) - len(lines[j].lstrip())
    if ind == 0:
        break
    body_indent = ind
    if s == "main()":
        main_line = j
    elif "main(" in s:
        # wrapped call (sys.exit(main()) etc.) — don't guess
        print(f"(2) ABORT: __main__ calls main() in a non-plain form ('{s}'). bottom lines:")
        for l in lines[mi:]:
            print("   |", l)
        raise SystemExit(1)
if main_line is None:
    print("(2) ABORT: could not find a plain main() call in the __main__ block. bottom lines:")
    for l in lines[mi:]:
        print("   |", l)
    raise SystemExit(1)
ind = " " * body_indent
block = [
    f"{ind}try:",
    f"{ind}    import thread_temperature as _tt",
    f"{ind}    _tt.run(apply=True, quiet=True)   # 6b: tag temperature+stability at triage",
    f"{ind}except Exception as _te:",
    f"{ind}    log(f'[temperature] pass failed (non-fatal): {{_te}}')",
]
lines[main_line + 1:main_line + 1] = block
new = "\n".join(lines)
bak = TT + f".bak-tempwire-{TS}"
shutil.copy2(TT, bak)
open(TT, "w", encoding="utf-8").write(new)
try:
    py_compile.compile(TT, doraise=True)
    print(f"(2) wired thread-triage.py: temperature pass runs after main() (line {main_line+1}). backup:", sh(bak))
except py_compile.PyCompileError as e:
    shutil.copy2(bak, TT)
    print("(2) syntax error — rolled back:", str(e)[:160]); raise SystemExit(1)
print("\nTriage-native. Each triage pass now tags temperature + stability right after pull. Reversible via the .bak files.")
