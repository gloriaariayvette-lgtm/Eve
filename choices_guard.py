#!/usr/bin/env python3
"""choices_guard.py — make the cron LLM parsers degrade instead of KeyError-crash when grok returns
an error body with no 'choices'. Replaces blind r.json()["choices"][0]... with a safe chain (-> "").
Backups + syntax-check. No restart needed (crons read fresh). Aegis."""
import os, time, shutil, subprocess
HOME = os.path.expanduser("~")
def run(a): return subprocess.run(a, capture_output=True, text=True)

# (file, [(old_substr, new_substr), ...])
JOBS = [
    ("~/Vintos/dream-art.py", [
        ('r.json()["choices"][0]["message"]["content"]',
         '(((r.json().get("choices") or [{}])[0].get("message") or {}).get("content") or "")'),
    ]),
    ("~/Vintos/gallery-walk.py", [
        ('r.json()["choices"][0]["message"].get("content", "")',
         '((r.json().get("choices") or [{}])[0].get("message") or {}).get("content", "")'),
        ('r.json()["choices"][0]["message"]["content"]',
         '(((r.json().get("choices") or [{}])[0].get("message") or {}).get("content") or "")'),
    ]),
    ("~/Vintos/vintos-initiate.sh", [
        ('resp.json()["choices"][0]["message"].get("content", "")',
         '((resp.json().get("choices") or [{}])[0].get("message") or {}).get("content", "")'),
    ]),
]

for rel, subs in JOBS:
    path = os.path.expanduser(rel)
    if not os.path.isfile(path):
        print(f"{rel}: (not found)"); continue
    body = open(path, encoding="utf-8").read(); orig = body; total = 0
    for old, new in subs:
        if new.split("(")[1] in body and old not in body:
            print(f"{rel}: already guarded"); break
        c = body.count(old)
        body = body.replace(old, new)
        total += c
        print(f"{rel}: '{old[:34]}...' x{c}")
    if body != orig:
        bak = path + ".bak-choices-" + time.strftime("%Y%m%d-%H%M%S")
        shutil.copy2(path, bak); open(path, "w", encoding="utf-8").write(body)
        # syntax check
        if path.endswith(".py"):
            sc = run(["python3","-c", f"import ast; ast.parse(open('{path}').read())"])
        else:
            sc = run(["bash","-n", path])
        if sc.returncode != 0:
            shutil.copy2(bak, path); print(f"  !! syntax error — rolled back: {sc.stderr[:120]}")
        else:
            print(f"  guarded ({total} site(s)), syntax OK. backup made")

print("\nDone — next grok overload: these skip with empty output instead of crashing the job.")
