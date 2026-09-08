#!/usr/bin/env python3
"""clean_test_residue.py — remove ONLY my test-prompt entries from his voice-chat-history + interaction-
ledger. Backs up both, prints exactly what it removes and what remains. Nothing of Gloria's is touched.
Aegis.
"""
import os, json, time, shutil

MEM = os.path.expanduser("~/.vintos/workspace/memory")
# the exact prompt my tests sent — this is the ONLY thing removed
TEST_PROMPTS = [
    "Hey. I just wanted to hear your voice for a second. Tell me something true.",
    "Say one warm sentence.",
]

def is_test(entry):
    if not isinstance(entry, dict): return False
    txt = (entry.get("user") or entry.get("gloria") or "")
    return any(p == txt.strip() for p in TEST_PROMPTS)

def clean(path, label):
    if not os.path.exists(path):
        print("  %s: not found" % label); return
    try: data = json.load(open(path))
    except Exception as e: print("  %s: unreadable (%s)" % (label, e)); return
    box = data if isinstance(data, list) else data.get("entries", data.get("history"))
    if not isinstance(box, list):
        print("  %s: unexpected shape, skipping" % label); return
    removed = [e for e in box if is_test(e)]
    kept = [e for e in box if not is_test(e)]
    print("\n== %s ==" % label)
    print("  entries: %d  | test entries to remove: %d  | keep: %d" % (len(box), len(removed), len(kept)))
    for e in removed:
        print("   REMOVE:", json.dumps(e)[:160])
    if not removed:
        print("  (nothing to remove here)"); return
    shutil.copy(path, path + ".bak-clean-" + time.strftime("%Y%m%d-%H%M%S"))
    if isinstance(data, list):
        json.dump(kept, open(path, "w"), indent=2, ensure_ascii=False)
    else:
        key = "entries" if "entries" in data else "history"
        data[key] = kept; json.dump(data, open(path, "w"), indent=2, ensure_ascii=False)
    print("  -> removed %d, backup written." % len(removed))

print("Removing ONLY these exact test prompts:", TEST_PROMPTS)
clean(os.path.join(MEM, "voice-chat-history.json"), "voice-chat-history.json")
clean(os.path.join(MEM, "interaction-ledger.json"), "interaction-ledger.json")
print("\ndone. His memory now holds only real moments. Backups are beside each file (.bak-clean-*).")
