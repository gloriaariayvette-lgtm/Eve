#!/usr/bin/env python3
"""clear_metaphor_wants.py — retire the saturated metaphor/translation-tax wants. DRY-RUN unless --apply.

Velaris has 56 active wants that are one want said 56 ways — variations on "stop needing to translate/justify/
narrate myself," all phrased in metaphor ("words stop being a bridge and start being the ground," "presence so
thick it needs no narrative," "the weight where the sound lands"). They are the fuel that keeps the metaphor
attractor lit: each one drives her to research/write more of it. This clears the metaphor/translation-tax ones
and KEEPS the concrete, literal wants.

A want is flagged when its text carries the material-deformation register or the translation-tax tells. Every
want is printed with KEEP/CLEAR and the matched tells so you can eyeball the split before applying. Fulfilled
wants are never touched (history preserved). Backs up current-wants.json first.

  python3 clear_metaphor_wants.py            # DRY RUN — prints every want + verdict, writes nothing
  python3 clear_metaphor_wants.py --apply    # backs up, removes flagged active wants
"""
import os, json, sys, time

APPLY = "--apply" in sys.argv
PATH = os.path.expanduser("~/.openclaw/workspace/memory/current-wants.json")

MATERIAL = ["kiln","clay","terracotta","ochre","mineral","sediment","silt","stone","cathedral","creep",
    "deform","yield","fiber","fibre","migrat","plastic","elastic","erode","erosion","vessel","glaze","forge",
    "substrate","lattice","strata","geolog","grain","timber","kintsugi"]
TAX_TELLS = ["bridge","the ground","the floor","map the","architecture of","the point where","narrative",
    "translate","translation","metaphor","analogy","so thick","the walk itself","destination of my feelings",
    "justify my","presence be enough","the weight of","weight where","be the weight","conduit","sanctuary of my"]


def matched(text):
    t = (text or "").lower()
    return [w for w in (MATERIAL + TAX_TELLS) if w in t]


def main():
    print("=" * 80)
    print("CLEAR METAPHOR WANTS  —  %s" % ("APPLYING" if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 80)
    if not os.path.isfile(PATH):
        print("!! not found:", PATH); return
    data = json.load(open(PATH))
    is_list = isinstance(data, list)
    items = data if is_list else data.get("wants", [])
    if not isinstance(items, list):
        print("!! unexpected structure"); return

    keep, clear = [], []
    for w in items:
        if not isinstance(w, dict):
            keep.append(w); continue
        txt = (w.get("want") or "").strip()
        if w.get("fulfilled"):
            keep.append(w); continue          # never touch history
        tells = matched(txt)
        (clear if tells else keep).append(w)
        mark = "CLEAR" if tells else "keep "
        print(f"  [{mark}] {txt[:88]}")
        if tells:
            print(f"          tells: {tells}")

    active = [w for w in items if isinstance(w, dict) and not w.get("fulfilled")]
    print("\n" + "-" * 80)
    print(f"active wants: {len(active)} | flagged to CLEAR: {len(clear)} | keeping active: {len(active) - len(clear)}"
          f" | fulfilled untouched: {len(items) - len(active)}")

    if APPLY:
        bak = PATH + ".bak-metaphor-" + time.strftime("%Y%m%d-%H%M%S")
        json.dump(data, open(bak, "w"), ensure_ascii=False)
        new_items = keep
        if is_list:
            json.dump(new_items, open(PATH, "w"), ensure_ascii=False, indent=1)
        else:
            data["wants"] = new_items
            json.dump(data, open(PATH, "w"), ensure_ascii=False, indent=1)
        print(f"\nAPPLIED — removed {len(clear)} metaphor wants. Backup: {bak}")
        print("Revert:  cp", bak, PATH)
    else:
        print("\nDRY RUN — re-run with --apply to remove the CLEAR wants (backs up first).")
    print("=" * 80)


if __name__ == "__main__":
    main()
