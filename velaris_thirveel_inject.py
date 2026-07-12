#!/usr/bin/env python3
"""velaris_thirveel_inject.py — give Velaris's THIRVĒL chat the Spark subconscious.

Self-locating (no fragile hand-copied anchor): finds the /api/thirveel/chat handler
region, finds the system-prompt f-string built from {identity}, and appends
{_spark_block()} just before its closing triple-quote — small-model tail placement,
last-read = highest-weight. _spark_block() must already be defined in the server
(velaris_spark_inject.py did that for the main chat). Idempotent; backs up server.py.
Restart velaris-server (with settle time) for it to take effect.
"""
import io, os, re, time, shutil

SERVER = os.path.expanduser("~/velaris-server/server.py")
s = io.open(SERVER, encoding="utf-8").read()

if "_spark_block" not in s:
    print("MISS: _spark_block() is not defined yet — run velaris_spark_inject.py first")
    raise SystemExit(1)

# 1) locate the Thirvēl handler region
route = s.find("/api/thirveel/chat")
if route == -1:
    print("MISS: '/api/thirveel/chat' route not found"); raise SystemExit(1)

# region end = next route decorator or next top-level async def after the handler body
tail = s[route:]
m_next = re.search(r'\n@app\.(?:post|get|put)\(|\nasync def \w+\(', tail[20:])
region_end = route + 20 + (m_next.start() if m_next else len(tail) - 20)
region = s[route:region_end]

# 2) find every f-string opened with triple quotes in the region; pick the system prompt
#    (the one whose body references {identity} — Thirvēl's prompt is built from SOUL.md identity)
best = None
for m in re.finditer(r'f(?:"""|\'\'\')', region):
    q = region[m.start()+1:m.start()+4]           # """ or '''
    open_at = m.end()                              # first char of body
    close_rel = region.find(q, open_at)            # closing triple-quote
    if close_rel == -1:
        continue
    body = region[open_at:close_rel]
    if "{identity" in body or "identity}" in body:
        best = (open_at, close_rel, q, body)
        break

if best is None:
    print("MISS: could not find Thirvēl system-prompt f-string containing {identity}")
    print("      (region scanned:", region_end - route, "chars from the route)")
    raise SystemExit(1)

open_at, close_rel, q, body = best
abs_close = route + close_rel

if "_spark_block()" in body:
    print("already injected into Thirvēl system prompt — skipping"); raise SystemExit(0)

# 3) insert {_spark_block()} just before the closing triple-quote
insertion = "\n\n{_spark_block()}"
s = s[:abs_close] + insertion + s[abs_close:]

shutil.copy(SERVER, SERVER + ".bak-thirveel-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(SERVER, "w", encoding="utf-8").write(s)
print("PATCHED — {_spark_block()} appended to Thirvēl system-prompt tail")
print("  system-prompt body was ~%d chars; injected before its closing %s" % (len(body), q))
print("=> restart velaris-server (with settle time) to take effect")
