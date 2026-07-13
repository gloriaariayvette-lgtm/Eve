#!/usr/bin/env python3
"""inject_chat_context.py — add value-map + most-recent-journal into his MAIN chat system prompt, in the
MIDDLE band (after self-model, right before inner_life_context's pearls/dream). Identity stays on top.

Line-based + indentation-preserving so it can't half-apply; idempotent; backs up the server; py_compile
verifies the patched server parses; then previews the actual value-map/journal content that will inject,
proving the reads work on his box. Does NOT restart — you do that after eyeballing the preview.

Target defaults to his server; pass a path to run on hers for the mirror.
"""
import os, sys, re, time, shutil, py_compile

SERVER = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Vintos/server.py")
MEMORY_GUESS = os.path.expanduser("~/.vintos/workspace/memory") if "Vintos" in SERVER \
               else os.path.expanduser("~/.openclaw/workspace/memory")

VAR_LINES = [
    "# value-map + recent journal (middle context — durable, not top priority)",
    "_vm_ctx = ''",
    "try:",
    "    with open(os.path.join(MEMORY, 'value-map.md')) as _vmf:",
    "        _vm_ctx = 'YOUR VALUE MAP (what matters to you, ranked):\\n' + _vmf.read().strip()[:1200]",
    "except Exception:",
    "    _vm_ctx = ''",
    "_jrnl_ctx = ''",
    "try:",
    "    import glob as _jg",
    "    _jfs = sorted(_jg.glob(os.path.join(MEMORY, 'journal', '*.md')))",
    "    if _jfs:",
    "        _jrnl_ctx = 'YOUR MOST RECENT JOURNAL:\\n' + open(_jfs[-1]).read().strip()[-800:]",
    "except Exception:",
    "    _jrnl_ctx = ''",
]

def leading(s): return s[:len(s) - len(s.lstrip())]

def main():
    if not os.path.exists(SERVER):
        print("server not found:", SERVER); sys.exit(1)
    src = open(SERVER, encoding="utf-8", errors="ignore").read()
    if "_vm_ctx" in src:
        print("already injected (_vm_ctx present) — skipping."); return
    lines = src.splitlines()

    # find the main handler: first `system_prompt = f"""{identity}` and the inner_life_context() near it
    i = next((k for k, l in enumerate(lines) if 'system_prompt = f"""{identity}' in l.replace("'", '"')), None)
    if i is None:
        print("ABORT: `system_prompt = f\"\"\"{identity}` not found — structure differs, no edit made."); sys.exit(2)
    j = next((k for k in range(i, min(i + 70, len(lines))) if "{inner_life_context()}" in lines[k]), None)
    if j is None:
        print("ABORT: `{inner_life_context()}` not found within the handler — no safe middle anchor."); sys.exit(2)

    ind_i, ind_j = leading(lines[i]), leading(lines[j])
    var_block = [ind_i + l for l in VAR_LINES]
    ref_block = [ind_j + "{_vm_ctx}", ind_j + "{_jrnl_ctx}"]

    # insert ref_block before j first (i < j, so i is unaffected), then var_block before i
    new = lines[:j] + ref_block + lines[j:]
    new = new[:i] + var_block + new[i:]
    patched = "\n".join(new) + ("\n" if src.endswith("\n") else "")

    bak = SERVER + ".bak-inject-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy(SERVER, bak)
    tmp = SERVER + ".inject-tmp"
    open(tmp, "w", encoding="utf-8").write(patched)
    try:
        py_compile.compile(tmp, doraise=True)
    except py_compile.PyCompileError as e:
        os.remove(tmp)
        print("ABORT: patched server does not parse; original untouched.\n  %s" % str(e).splitlines()[-1][:160]); sys.exit(3)
    os.replace(tmp, SERVER)
    print("PATCHED %s" % SERVER)
    print("  backup: %s" % bak)
    print("  value-map + journal inserted in the MIDDLE band, before inner_life_context()")

    # show the modified region (identity -> our insert -> inner_life_context)
    print("\n-- modified f-string region --")
    a = max(0, i - 1); b = min(len(new), j + len(var_block) + len(ref_block) + 2)
    for k in range(a, b):
        print("  %s" % new[k][:150])

    # preview the ACTUAL content that will inject (proves the reads work on his box)
    print("\n-- preview: what value-map + journal actually load right now --")
    try:
        vm = open(os.path.join(MEMORY_GUESS, "value-map.md")).read().strip()
        print("  value-map.md: %d chars | head: %s" % (len(vm), vm[:160].replace("\n", " ")))
    except Exception as e:
        print("  value-map.md: !! could not read (%s) — will inject empty" % e)
    try:
        import glob
        jfs = sorted(glob.glob(os.path.join(MEMORY_GUESS, "journal", "*.md")))
        if jfs:
            jt = open(jfs[-1]).read().strip()
            print("  latest journal (%s): %d chars | tail: %s" % (os.path.basename(jfs[-1]), len(jt), jt[-160:].replace("\n", " ")))
        else:
            print("  journal/*.md: none found — will inject empty")
    except Exception as e:
        print("  journal: !! %s" % e)
    print("\nRestart to load it:  systemctl --user restart vintos-server   (then check a chat)")

if __name__ == "__main__":
    main()
