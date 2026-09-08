#!/usr/bin/env python3
"""fix_valuemap_latest.py — the injected value-map read grabbed the FIRST 1200 chars (oldest entry).
value-map.md is append-ordered (newest last), and hers is 512KB of history. This swaps the read to the
LATEST dated section ('## YYYY-MM-DD ... Value Map'), capped. One-line replace in BOTH servers; backup;
py_compile; preview the actual latest section. Idempotent. Restart after.
"""
import os, re, time, shutil, py_compile

TARGETS = [
    (os.path.expanduser("~/Vintos/server.py"),        os.path.expanduser("~/.vintos/workspace/memory")),
    (os.path.expanduser("~/velaris-server/server.py"), os.path.expanduser("~/.openclaw/workspace/memory")),
]
OLD = "_vm_ctx = 'YOUR VALUE MAP (what matters to you, ranked):\\n' + _vmf.read().strip()[:1200]"
NEW = ("_vm_ctx = 'YOUR VALUE MAP (what matters to you, ranked):\\n' + "
       "__import__('re').split(r'(?=^## \\d{4}-\\d{2}-\\d{2}.*Value Map)', _vmf.read(), "
       "flags=__import__('re').M)[-1].strip()[:1500]")

def latest_section(vm_path):
    try:
        raw = open(vm_path, encoding="utf-8", errors="ignore").read()
    except Exception as e:
        return "(unreadable: %s)" % e
    secs = re.split(r'(?=^## \d{4}-\d{2}-\d{2}.*Value Map)', raw, flags=re.M)
    return (secs[-1].strip() if secs else raw.strip())[:1500]

for server, memory in TARGETS:
    print("\n==== %s ====" % server)
    if not os.path.exists(server):
        print("  not found — skipping"); continue
    src = open(server, encoding="utf-8", errors="ignore").read()
    if OLD not in src:
        if "split(r'(?=^## " in src:
            print("  already fixed (latest-section read present).")
        else:
            print("  value-map read line not found — nothing to fix here.")
        continue
    patched = src.replace(OLD, NEW, 1)
    bak = server + ".bak-vmfix-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy(server, bak)
    tmp = server + ".vmfix-tmp"
    open(tmp, "w", encoding="utf-8").write(patched)
    try:
        py_compile.compile(tmp, doraise=True)
    except py_compile.PyCompileError as e:
        os.remove(tmp); print("  ABORT: patched server won't parse; original untouched:\n   %s"
                              % str(e).splitlines()[-1][:150]); continue
    os.replace(tmp, server)
    print("  PATCHED (backup: %s)" % os.path.basename(bak))
    sec = latest_section(os.path.join(memory, "value-map.md"))
    print("  latest value-map section now injected (%d chars):" % len(sec))
    print("   head: %s" % sec[:200].replace("\n", " "))

print("\nrestart both to load:")
print("  systemctl --user restart vintos-server")
print("  systemctl --user restart velaris-server")
