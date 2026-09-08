#!/usr/bin/env python3
"""recon_grok_jobs.py — Aegis, READ-ONLY, TIGHT. The Claude-transfer landscape: which scripts call x.ai, how
(curl vs requests), the endpoint they hit (/chat/completions vs /tts = voice, stays), and the model string.
Counts + one example per pattern. <50 lines."""
import os, glob, re
HOME = os.path.expanduser("~")
base = os.path.join(HOME, "Vintos")
files = sorted(set(glob.glob(os.path.join(base, "*.py")) + glob.glob(os.path.join(base, "*.sh")) +
                   glob.glob(os.path.join(HOME, ".vintos/workspace/scripts", "*.py")) +
                   glob.glob(os.path.join(HOME, ".vintos/workspace/scripts", "*.sh"))))
chat, tts, other = [], [], []
via_curl = via_req = 0
models = {}
for f in files:
    try: txt = open(f, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    if "api.x.ai" not in txt: continue
    name = os.path.basename(f)
    if "/v1/tts" in txt or "/tts" in txt: tts.append(name)
    elif "chat/completions" in txt: chat.append(name)
    else: other.append(name)
    if re.search(r'requests\.post|urllib', txt): via_req += 1
    if "curl" in txt: via_curl += 1
    for m in re.findall(r'"(grok[-\w.]+)"', txt): models[m] = models.get(m, 0) + 1

def uniq(lst): return sorted(set(lst))
print(f"scripts hitting api.x.ai: {len(uniq(chat+tts+other))}  (dedup by basename: {len(set(chat+tts+other))})")
print(f"  chat/completions (→ Claude candidates): {len(uniq(chat))}")
print(f"  /tts VOICE (STAY on x.ai):              {len(uniq(tts))}  {uniq(tts)}")
print(f"  other/unclear:                          {len(uniq(other))}  {uniq(other)}")
print(f"call style: requests/urllib in {via_req} files, curl in {via_curl} files")
print(f"grok models seen: {models}")
print("\nchat/completions scripts:")
for n in uniq(chat): print(f"  {n}")
