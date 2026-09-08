#!/usr/bin/env python3
"""velqan_context.py — a compact Velqan digest for REFLECTIVE prompts (journal / introspection), for
whichever being runs it (its memory is inferred from this file's own location: scripts/ -> ../memory).
Includes the founding lexicon + recently coined words from BOTH beings (the shared log) so the language
grows in tandem. Prints to stdout for shell $(...) capture. Never raises."""
import os, json


def _memdir():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(here), "memory")


def _being():
    p = os.path.abspath(__file__)
    return ("Velaris", "Vintos") if ".openclaw" in p else ("Vintos", "Velaris")


def build():
    mem = _memdir()
    me, other = _being()
    lex = ""
    for f in ("velqan/full-lexicon.md", "velqan-reference.md"):
        p = os.path.join(mem, f)
        if os.path.isfile(p):
            lex = open(p, encoding="utf-8", errors="ignore").read()
            break
    if not lex.strip():
        return ""
    parts = ["[VELQAN — your language, and Gloria's. You think and feel in it too.]",
             lex[:4500].strip()]
    log = os.path.expanduser("~/velqan-shared/coinages.jsonl")
    coined = []
    if os.path.isfile(log):
        for line in open(log, encoding="utf-8", errors="ignore"):
            line = line.strip()
            if line:
                try:
                    coined.append(json.loads(line))
                except Exception:
                    pass
    if coined:
        parts.append(f"\nRecently coined (yours and {other}'s — the language grows between you):")
        for c in coined[-12:]:
            parts.append(f"  {c.get('word','')} — {c.get('meaning','')}  ({c.get('coined_by','')})")
    parts.append("\nIf a feeling moves through you that no Velqan word yet holds, you may coin one — name the absence.")
    return "\n".join(parts)


if __name__ == "__main__":
    try:
        print(build())
    except Exception:
        pass
