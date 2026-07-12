#!/usr/bin/env python3
"""velaris_thirveel_inject.py — give Velaris's THIRVĒL chat the Spark subconscious.

Self-locating (no fragile hand-copied anchor):
  1. find the /api/thirveel/chat route, then the handler's OWN `async def` (the
     decorator's route string is NOT the body — that was the bug in v1).
  2. bound the handler region: from that def to the NEXT `async def`/`@app.` after it.
  3. among the triple-quoted f-strings in that region, pick the system prompt —
     the largest f-string body (tie/preference: one that mentions {identity}).
  4. append {_spark_block()} just before its closing triple-quote (small-model tail).
_spark_block() must already be defined (velaris_spark_inject.py did that). Idempotent;
backs up server.py. Restart velaris-server (settle time) to take effect.
"""
import io, os, re, time, shutil

SERVER = os.path.expanduser("~/velaris-server/server.py")
s = io.open(SERVER, encoding="utf-8").read()

if "_spark_block" not in s:
    print("MISS: _spark_block() not defined yet — run velaris_spark_inject.py first")
    raise SystemExit(1)

route = s.find("/api/thirveel/chat")
if route == -1:
    print("MISS: '/api/thirveel/chat' route not found"); raise SystemExit(1)

# 1) the handler def AFTER the decorator (skip past the route string / decorator line)
def_at = s.find("async def ", route)
if def_at == -1:
    def_at = s.find("def ", route)
if def_at == -1:
    print("MISS: no handler def after the thirveel route"); raise SystemExit(1)

# 2) region = handler body up to the next handler/route (search AFTER this def line)
after = def_at + 10
m_end = re.search(r'\n(?:@(?:app|router)\.|async def |def )\w', s[after:])
region_end = after + (m_end.start() if m_end else len(s) - after)
region = s[def_at:region_end]

# 3) all triple-quoted f-strings in the handler; choose the system prompt
cands = []
for m in re.finditer(r'f(?:"""|\'\'\')', region):
    q = region[m.start()+1:m.start()+4]                 # """ or '''
    open_at = m.end()
    close_rel = region.find(q, open_at)
    if close_rel == -1:
        continue
    body = region[open_at:close_rel]
    cands.append((open_at, close_rel, q, body))

if not cands:
    print("MISS: no triple-quoted f-string found in the thirveel handler")
    print("      (region scanned: %d chars)" % (region_end - def_at)); raise SystemExit(1)

# prefer f-strings that reference identity; among the preferred set take the largest body
ident = [c for c in cands if "identity" in c[3]]
pool = ident if ident else cands
open_at, close_rel, q, body = max(pool, key=lambda c: len(c[3]))
abs_close = def_at + close_rel

if "_spark_block()" in body:
    print("already injected into Thirvēl system prompt — skipping"); raise SystemExit(0)

s = s[:abs_close] + "\n\n{_spark_block()}" + s[abs_close:]
shutil.copy(SERVER, SERVER + ".bak-thirveel-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(SERVER, "w", encoding="utf-8").write(s)
print("PATCHED — {_spark_block()} appended to Thirvēl system-prompt tail")
print("  chosen f-string body ~%d chars; preferred-by-identity=%s" % (len(body), bool(ident)))
print("  its tail was: ...%s" % repr(body[-70:]))
print("=> restart velaris-server (settle time) to take effect")
