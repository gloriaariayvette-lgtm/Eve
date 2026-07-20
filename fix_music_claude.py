#!/usr/bin/env python3
"""fix_music_claude.py — run HIS music-share reflections on Claude Sonnet 5, not Gemma. DRY-RUN unless --apply.

RUN ON AEGIS. Patches ~/Vintos/music-share.py ONLY (his; hers stays Gemma — that's her architecture). Music
shares are rare and meaningful; Gemma made them stiff and (on text-only shares) invented lyrics. This swaps
his llm() to call Claude Sonnet 5 via the Anthropic API (same endpoint + key file his _claude_sync already
uses), keeping the Gemma call as a fallback only if the key is missing. The whisper/librosa pipeline still
feeds real lyrics + acoustic description on file shares; now a capable model reflects on them.

No server restart needed — the endpoint shells out to music-share.py fresh each share.

  python3 fix_music_claude.py            # DRY RUN
  python3 fix_music_claude.py --apply     # backs up, applies
"""
import os, sys, difflib, datetime

APPLY = "--apply" in sys.argv
PATH = os.path.expanduser("~/Vintos/music-share.py")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = PATH + ".bak-claude-" + TS
SENTINEL = "claude-sonnet-5"

OLD = (
    "def llm(system, user, temperature=0.6):\n"
    "    try:\n"
    "        r = requests.post(API, json={\n"
    "            \"model\": MODEL,\n"
    "            \"messages\": [\n"
    "                {\"role\": \"system\", \"content\": system},\n"
    "                {\"role\": \"user\", \"content\": user}\n"
    "            ],\n"
    "            \"temperature\": temperature,\n"
    "            \"max_tokens\": 500\n"
    "        }, timeout=60)\n"
    "        return r.json()[\"choices\"][0][\"message\"][\"content\"].strip()\n"
    "    except:\n"
    "        return None\n"
)

NEW = (
    "def llm(system, user, temperature=0.6):\n"
    "    # Rare, meaningful -> run reflections on Claude Sonnet 5, not the fast Gemma path.\n"
    "    import urllib.request as _u, json as _j\n"
    "    _k = os.environ.get(\"ANTHROPIC_API_KEY\", \"\")\n"
    "    if not _k:\n"
    "        try: _k = open(os.path.expanduser(\"~/.vintos/anthropic-key\")).read().strip()\n"
    "        except Exception: _k = \"\"\n"
    "    if _k:\n"
    "        try:\n"
    "            _body = {\"model\": \"claude-sonnet-5\", \"max_tokens\": 1000, \"temperature\": temperature,\n"
    "                     \"system\": system,\n"
    "                     \"messages\": [{\"role\": \"user\", \"content\": user}]}\n"
    "            _rq = _u.Request(\"https://api.anthropic.com/v1/messages\", data=_j.dumps(_body).encode(),\n"
    "                             headers={\"content-type\": \"application/json\", \"anthropic-version\": \"2023-06-01\", \"x-api-key\": _k})\n"
    "            _d = _j.loads(_u.urlopen(_rq, timeout=180).read())\n"
    "            _t = \"\".join(b.get(\"text\", \"\") for b in _d.get(\"content\", []) if b.get(\"type\") == \"text\").strip()\n"
    "            if _t: return _t\n"
    "            log(\"Claude returned empty; falling back to Gemma\")\n"
    "        except Exception as _e:\n"
    "            log(f\"Claude call failed ({_e}); falling back to Gemma\")\n"
    "    try:\n"
    "        r = requests.post(API, json={\n"
    "            \"model\": MODEL,\n"
    "            \"messages\": [\n"
    "                {\"role\": \"system\", \"content\": system},\n"
    "                {\"role\": \"user\", \"content\": user}\n"
    "            ],\n"
    "            \"temperature\": temperature,\n"
    "            \"max_tokens\": 500\n"
    "        }, timeout=60)\n"
    "        return r.json()[\"choices\"][0][\"message\"][\"content\"].strip()\n"
    "    except:\n"
    "        return None\n"
)


def main():
    print("=" * 72)
    print("MUSIC REFLECTION -> CLAUDE SONNET 5 (his)  —  %s" % ("APPLYING" if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 72)
    if not os.path.isfile(PATH):
        print("!! not found:", PATH); return
    text = open(PATH, encoding="utf-8", errors="ignore").read()
    if SENTINEL in text:
        print("   * already on Claude Sonnet 5"); return
    if OLD not in text:
        print("   !! llm() anchor not found (his file differs from expected) — writing nothing"); return
    new = text.replace(OLD, NEW, 1)
    try:
        compile(new, PATH, "exec"); print("   compiles: OK")
    except SyntaxError as e:
        print(f"   !! COMPILE FAIL: {e} — NOT writing"); return
    for l in difflib.unified_diff(text.splitlines(), new.splitlines(), fromfile="old", tofile="new", lineterm=""):
        print("   " + l[:160])
    if APPLY:
        open(BACKUP, "w", encoding="utf-8").write(text)
        open(PATH, "w", encoding="utf-8").write(new)
        print("\nAPPLIED. Backup:", BACKUP)
        print("No restart needed — next share reflects on Claude Sonnet 5.")
    else:
        print("\nDRY RUN complete. Re-run with --apply.")
    print("=" * 72)


if __name__ == "__main__":
    main()
