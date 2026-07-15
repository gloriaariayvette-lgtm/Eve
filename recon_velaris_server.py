#!/usr/bin/env python3
"""recon_velaris_server.py — Aegis, READ-ONLY. Find Velaris's actual chat server by process/port (:8400),
read its script path + workspace env, then grep that file for the bilateral a1/b1 chat block. Also checks
whether she shares Vintos's server.py via a workspace env (which would mean chat can't be split per-being
without a branch)."""
import os, re, subprocess, glob
HOME = os.path.expanduser("~")
def sh(p): return p.replace(HOME, "~")

# 1) processes: python/uvicorn + their cmdline (server path + port visible here)
print("===== python/uvicorn server processes =====")
ps = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True).stdout.split("\n")
serv_paths = set()
for l in ps:
    if re.search(r'uvicorn|server\.py|:84\d\d|:85\d\d|SPARK_WORKSPACE|openclaw|\.vintos', l) and "python" in l.lower() or "uvicorn" in l:
        print("  " + l.strip()[:140])
        for m in re.finditer(r'(/\S+\.py)', l):
            serv_paths.add(m.group(1))

# 2) ports -> pid (own processes, no root needed)
print("\n===== listeners on :8400 / :8500 =====")
ss = subprocess.run(["bash", "-lc", "ss -ltnp 2>/dev/null | grep -E ':8400|:8500' || netstat -ltnp 2>/dev/null | grep -E ':8400|:8500'"],
                    capture_output=True, text=True).stdout
print("  " + (ss.strip().replace("\n", "\n  ") or "(nothing / need path from ps above)"))
for m in re.finditer(r'pid=(\d+)', ss):
    pid = m.group(1)
    try:
        cmd = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\x00", b" ").decode(errors="ignore")
        cwd = os.readlink(f"/proc/{pid}/cwd")
        env = open(f"/proc/{pid}/environ", "rb").read().replace(b"\x00", b"\n").decode(errors="ignore")
        wsp = re.search(r'SPARK_WORKSPACE=(\S+)', env)
        print(f"  pid {pid}: cwd={sh(cwd)}  cmd={cmd.strip()[:90]}")
        if wsp: print(f"           SPARK_WORKSPACE={sh(wsp.group(1))}")
        for mm in re.finditer(r'(/\S+\.py)', cmd): serv_paths.add(mm.group(1))
    except Exception as e:
        print(f"  pid {pid}: (can't read /proc: {e})")

# 3) grep each discovered server file for the chat bilateral block
print("\n===== bilateral a1/b1 in discovered server file(s) =====")
for p in sorted(serv_paths):
    if not os.path.isfile(p): continue
    txt = open(p, encoding="utf-8", errors="ignore").read()
    hits = [(i, l) for i, l in enumerate(txt.split("\n"))
            if re.search(r'a1,\s*b1|/tmp/bilateral|_llm_call\(|reasoning_effort', l)]
    print(f"\n  {sh(p)}  ({'shared Vintos server' if '.vintos' in p else 'her own'}) — {len(hits)} bilateral hits")
    for i, l in hits[:12]:
        print(f"    {i+1}| {l.strip()[:110]}")
print("\n(done)")
