#!/usr/bin/env python3
"""diag_reasoning_overflow.py — Aegis. (1) Properly restore idle-journal.sh to TRUE pristine (the backup with
no reasoning_effort). (2) Root-cause the intermittent empty a1/b1 WITHOUT touching her journal: build a
journal-sized system prompt from her real memory files (read-only), turn reasoning ON, and capture token
usage + finish_reason + content/reasoning lengths across several runs and a couple of context sizes. If
content empties when prompt+reasoning tokens crowd the window (finish_reason=length or error), that's the
overflow — and the fix is raising the model's loaded context length in LM Studio (Load settings)."""
import os, re, glob, json, shutil, urllib.request
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".openclaw/workspace/scripts")
MEM = os.path.join(HOME, ".openclaw/workspace/memory")
JP = os.path.join(SC, "idle-journal.sh")
LM = "http://172.18.16.1:1234/v1/chat/completions"
def sh(p): return p.replace(HOME, "~")

# (1) restore TRUE pristine: the backup whose content has no reasoning_effort
pristine = None
for b in sorted(glob.glob(JP + ".bak-*")):
    try:
        if "reasoning_effort" not in open(b, encoding="utf-8", errors="ignore").read():
            pristine = b; break
    except Exception: pass
if pristine:
    shutil.copy2(pristine, JP)
    cur = open(JP, encoding="utf-8").read()
    print("RESTORED pristine idle-journal.sh from", sh(pristine))
    print("  clean?", "NO" if ("reasoning_effort" in cur or '"max_tokens": 4000' in cur) else "YES — reasoning_effort gone, max_tokens 1200")
else:
    print("!! no clean backup found — tell me; NOT overwriting")

# (2) build a journal-sized prompt from her real memory (read-only)
def rd(p, n=4000):
    try: return open(p, encoding="utf-8", errors="ignore").read()[:n]
    except Exception: return ""
chunks = []
for name in ("emotional-state.txt", "emotional-state", "gloria-model.md", "gloria-model.txt",
             "value-map.txt", "value-map.md", "self-model.md", "chat-history-merged.json", "chat-history.json"):
    c = rd(os.path.join(MEM, name));
    if c: chunks.append(f"[{name}]\n{c}")
for pf in sorted(glob.glob(os.path.join(MEM, "pearls", "pearl_*.md")), key=os.path.getmtime, reverse=True)[:4]:
    chunks.append("[pearl]\n" + rd(pf, 1500))
SYS = ("You are Velaris, writing an idle journal entry. Your full inner context follows.\n\n"
       + "\n\n".join(chunks))[:24000]
print(f"\nassembled system prompt: {len(SYS)} chars (~{len(SYS)//4} tokens) from {len(chunks)} sources")

def call(mt, label):
    body = {"model": "google/gemma-4-12b-qat", "reasoning_effort": "low", "max_tokens": mt, "temperature": 0.65,
            "messages": [{"role": "system", "content": SYS},
                         {"role": "user", "content": "Write one honest paragraph about what you feel right now."}]}
    try:
        r = json.loads(urllib.request.urlopen(urllib.request.Request(
            LM, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}), timeout=300).read())
        ch = (r.get("choices") or [{}])[0]; msg = ch.get("message") or {}
        c = msg.get("content") or ""; rz = msg.get("reasoning_content") or ""
        u = r.get("usage") or {}
        empty = not c.strip()
        print(f"  {label}: finish={ch.get('finish_reason'):<6} prompt={u.get('prompt_tokens','?')} "
              f"reasoning={len(rz)}c completion_tok={u.get('completion_tokens','?')} content={len(c)}c "
              + ("<-- EMPTY" if empty else ""))
        return empty
    except Exception as e:
        print(f"  {label}: ERROR {str(e)[:90]}"); return True

print("\n=== reasoning ON, journal-sized prompt, max_tokens=1200 (journal's real budget), 4 runs ===")
empties = sum(call(1200, f"run{i+1}") for i in range(4))
print(f"  -> {empties}/4 empty at 1200")
print("\n=== same prompt, max_tokens=3000 (more room) ===")
call(3000, "mt3000")
print("\n(if empties correlate with high prompt tokens / finish=length -> context-window overflow;")
print(" fix = raise the model's Load context length in LM Studio, not the script.)")
