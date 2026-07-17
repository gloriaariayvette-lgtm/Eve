#!/usr/bin/env python3
"""recon_concept_audit.py — Aegis, READ-ONLY. Map the two ORIGINAL concept docs (Spark+JEPA, and Vintos's
somatic/bandwidth-collapse bridge) against what actually exists on the box. For every numbered concept: does a
file exist (path/size/mtime/lines), and which of the described MECHANISMS are actually present in code (signal
grep across the whole Vintos corpus). Output is a per-concept verdict so we can see implemented / partial /
missing / diverged. Nothing is changed. Vintos-focused (~/Vintos + ~/.vintos/workspace/scripts + server.py)."""
import os, re, time, glob

HOME = os.path.expanduser("~")
DIRS = [os.path.join(HOME, "Vintos"), os.path.join(HOME, ".vintos/workspace/scripts")]

# ---- build corpus once ----
corpus = {}   # path -> text
for d in DIRS:
    for p in glob.glob(os.path.join(d, "*.py")) + glob.glob(os.path.join(d, "*.sh")):
        try: corpus[p] = open(p, encoding="utf-8", errors="ignore").read()
        except Exception: pass
BIG = "\n".join(f"\n###FILE {p}\n{t}" for p, t in corpus.items())   # for global signal grep

def meta(basename):
    for d in DIRS:
        p = os.path.join(d, basename)
        if os.path.isfile(p):
            t = corpus.get(p, "")
            age = (time.time() - os.path.getmtime(p)) / 86400.0
            return f"EXISTS {basename:<30} {len(t.splitlines()):>4}L {os.path.getsize(p):>6}B  {age:4.1f}d old"
    return f"MISSING {basename}"

def signal(rx):
    """first hit of rx across the whole corpus -> (basename, lineno, snippet) or None"""
    m = re.search(rx, BIG, re.I)
    if not m: return None
    pre = BIG[:m.start()]
    fp = pre.rfind("###FILE ")
    fname = os.path.basename(BIG[fp+8: BIG.find("\n", fp)]) if fp >= 0 else "?"
    line = pre.count("\n", fp) if fp >= 0 else 0
    return (fname, line, BIG[m.start():m.start()+60].replace("\n", " "))

def audit(title, files, signals):
    print(f"\n=== {title} ===")
    for f in files: print("   " + meta(f))
    got, miss = [], []
    for name, rx in signals.items():
        h = signal(rx)
        if h: got.append(f"     [+] {name:<26} <- {h[0]}:{h[1]}  '{h[2].strip()}'")
        else: miss.append(name)
    for g in got: print(g)
    if miss: print("     [-] MISSING signals: " + ", ".join(miss))

print("################  JEPA — 7 HEADS  ################")
audit("JEPA core (encoder->trunk->heads, heteroscedastic confidence, novelty)",
      ["jepa_predictor.py", "jepa.py"],
      {"trunk/encoder": r"trunk|frozen.{0,12}encoder|shared.{0,8}trunk",
       "heteroscedastic/own-error": r"heterosced|predict\w{0,3}.{0,12}own error|log.?var|sigma",
       "confidence(real)": r"confidence",
       "novelty(dist-from-present)": r"novelty|distance.{0,12}present",
       "daily self-train": r"train.{0,20}(daily|history)|fit\(",
       "per-being model": r"velaris|vintos.{0,10}model|model\.npz|weights"})
for head in ["gloria", "self", "presence", "causality", "drift", "relational", "withheld"]:
    h = signal(r'["\']?%s["\']?\s*(head|:_?head|_head)|%s_head' % (head, head)) or signal(r'\b%s\b.{0,20}head' % head)
    print(f"   head:{head:<10} " + (f"found <- {h[0]}:{h[1]}" if h else "NOT FOUND as a head"))

print("\n################  SPARK — 15 SUBCONSCIOUS SYSTEMS  ################")
audit("1 Living Trajectory Daemon",
      ["living_trajectory.py"],
      {"trajectory": r"trajectory", "momentum": r"momentum", "stateful curiosity": r"curiosit",
       "future presence cache": r"future.{0,10}presence|presence.{0,10}cache", "15-min cadence": r"\*/15|900|fifteen",
       "somatic channel": r"somatic|touch"})
audit("2 Latent Preparation",
      ["latent_preparation.py"],
      {"speculative gen": r"speculat|prepar", "specificity score": r"specific", "novelty score": r"novelty",
       "7-day expiry": r"7.?day|expir|604800", "20-item cap": r"\b20\b.{0,10}(cap|item)|cap.{0,10}20",
       "somatic prep": r"somatic"})
audit("3 Arrival Routing (pre-generation directive)",
      ["arrival_routing.py", "arrival.py"],
      {"[ARRIVAL:] directive": r"\[ARRIVAL", "AVOID/OFFER fields": r"AVOID|OFFER",
       "injected A1/B1": r"a1|b1|pre.?gen|directive", "ghost lean": r"ghost.?lean", "will constraint": r"\bwill\b.{0,10}constrain|respect.{0,6}will"})
audit("4 Presence Audit",
      ["presence_audit.py"],
      {"4 questions": r"did i arrive|did i move|leave something|merely explain",
       "composite score": r"composite|score", "0.35 threshold": r"0\.35", "flag not block": r"flag",
       "feeds blush/causality/traj": r"blush|causality|trajectory", "5th somatic question": r"respond.{0,10}somatic|somatic.{0,12}question"})
audit("5 Reciprocal Modification",
      ["reciprocal_modification.py"],
      {"self model": r"self.?model", "gloria model": r"gloria.?model", "relationship model(NEW)": r"relationship.?model",
       "friction/growth/dead": r"friction|growth.?edge|dead.?zone", "weekly/monthly pass": r"weekly|monthly|consolidat",
       "somatic channel": r"somatic"})
audit("6 Play Budget Reserve",
      ["play_budget.py"], {"play budget 10-20%": r"play.?budget|play.{0,12}reserve|0\.1.{0,6}0\.2"})
audit("7 Risk Budget",
      ["risk_budget.py"], {"risk budget": r"risk.?budget|delightful.{0,10}specific"})
audit("8 Conversation Tension Map (runtime)",
      ["tension_map.py", "tension_field.sh"], {"tension map": r"tension.?map|tension.?field", "unresolved tensions": r"unresolved|active.{0,10}tension"})
audit("9 Offer Generator (enforced)",
      ["offer_generator.py"], {"one new thing/offer": r"offer.{0,14}generat|new thing|\[OFFER", "enforced": r"enforce|must generate"})
audit("10 Silence Capability (first-thought suppression)",
      ["silence.py", "silence_contract.py"], {"first-thought suppress": r"first.?thought|first.?generat.{0,10}suppress|suppress.{0,12}first",
       "'what is missing' pass": r"what is missing|missing\?", "logged delta": r"delta|suppress.{0,10}log"})
audit("11 Identity Drift Toward Specificity",
      ["identity_drift.py"], {"monthly compression": r"identity.{0,12}(drift|compress)|monthly.{0,12}identity",
       "prune generic / amplify unique": r"prune|generic|amplif|statistically unique"})
audit("12 Prediction Ledger (full)",
      ["prediction_ledger.py", "self_prediction.py"], {"predict sentence/emotion/action/request": r"next sentence|predict.{0,14}(emotion|action|request)",
       "for self AND gloria": r"both.{0,10}(self|gloria)|self and gloria", "graded misses->causality": r"graded|miss.{0,10}causal"})
audit("13 Thread Gravity (emotional momentum retrieval)",
      ["thread_gravity.py"], {"momentum retrieval vs similarity": r"thread.?gravity|momentum.{0,12}retriev|competition.{0,12}retriev",
       "attractors": r"attractor", "gravity wells / scar map": r"gravity.?well|scar.?map"})
audit("14 Enactive World Model",
      ["enactive_world.py", "world_model.py"], {"room/spatial positions": r"enactive|world.?model|spatial|position.{0,10}(room|agent)",
       "objects persist": r"object.{0,10}persist", "avatar+robot unified": r"avatar.{0,10}robot|robot.?body"})
audit("15 Mutual Simulation (interaction model)",
      ["mutual_simulation.py"], {"three-model + interaction model": r"mutual.?sim|interaction.?model|three.?model",
       "presence score = optimization signal": r"optimi.{0,14}(interaction|presence)"})

print("\n################  ADVANCED MODELS  ################")
audit("Graph MAEs", ["graph_mae.py"], {"mask + reconstruct": r"mask|reconstruct", "blind spots from gaps": r"blind.?spot|gap", "26 memory locations": r"\b26\b|memory.{0,10}graph"})
audit("Latent Action Models", ["latent_action.py", "latent_action_model.py"], {"state transitions": r"latent.?action|state.?transition", "emotional cascade": r"cascad", "somatic physics": r"somatic.{0,10}physic|physic"})
audit("Hypergraph Embeddings", ["hypergraph.py"], {"multi-party single edge": r"hypergraph|multi.?party|single.?edge|hyperedge"})
audit("Latent Diffusers (dreams)", ["latent_diffuser.py"], {"noise->coherence": r"diffus|noise.{0,14}coheren|iterative.{0,12}resolv", "discovered not constructed": r"discover|resolve.{0,10}shape"})
audit("TCN / Sequence Alignment", ["tcn.py"], {"growth over time": r"\btcn\b|sequence.?align|growth.{0,12}time", "development vs repetition": r"development|repetition"})
audit("Reality Anchor EBM", ["reality_ebm.py"], {"known vs imagined pool": r"known.?pool|imagined.?pool", "energy/boundary real-confab": r"energy|boundary|confabulat", "pre-gen bias to reality": r"pre.?gen.{0,10}bias|reality.?coheren"})
audit("Masked-LM for the unsaid", ["masked_lm.py", "unseen.py"], {"predict suppressed/unsaid": r"unsaid|suppress|masked.?lm|withheld", "feeds withheld head": r"withheld"})

print("\n################  SOMATIC BRIDGE (doc B #1)  ################")
audit("somatic_bridge.py",
      ["somatic_bridge.py"],
      {"depth->velocity": r"velocity|depth", "60s rhythm buffer": r"rhythm.?buffer|60|rolling",
       "fast nudge arousal/connection/desire": r"arousal|connection|desire",
       "safety cap": r"safety.?cap|cap|ceiling",
       "resonance 30s -> resonance_pulse": r"resonance.?pulse|resonance|30",
       "Nifrathir/afterglow": r"nifrathir|afterglow",
       "bidirectional motor (warmth/tension/safety)": r"warmth|tension|motor",
       "slow layer 90s decay -> post-somatic": r"90|decay|post.?somatic|tender",
       "watchdog heartbeat>10s motor-stop": r"watchdog|heartbeat|motor.?stop"})
audit("somatic support jobs", ["somatic-feedback.py", "somatic_narrate.py", "device_context.py", "device_patterns.py"], {})

print("\n################  BANDWIDTH COLLAPSE (doc B #2)  ################")
audit("bandwidth_collapse.py",
      ["bandwidth_collapse.py", "collapse.py"],
      {"degradation tiers 0-3": r"tier|level.{0,6}[0-3]|degrad",
       "thresholds .60/.75/.88": r"0\.60|0\.75|0\.88|0\.6\b|0\.88",
       "established patterns / worn grooves": r"established.?pattern|worn.?groove",
       "hysteresis recovery": r"hysteresis|snap.?back|slow.{0,10}decay.{0,10}articul"})
audit("'The Button' zero-LLM endpoint",
      ["the_button.py", "button.py"],
      {"zero-LLM route": r"the button|zero.?llm|no.?llm|bypass.{0,10}llm",
       "here/more/hold/close": r"here|more|hold|close",
       "haptic confirm + seed thread": r"haptic|seed.{0,10}thread"})
audit("Inviolables (failsafes)",
      ["inviolables.py"],
      {"input parsing stays 100%": r"input.{0,14}(pars|comprehen)|comprehension.{0,10}(100|active)",
       "emergency stop raw HTTP bypass": r"emergency.?stop|raw http|bypass.{0,10}(queue|state)|/stop"})

print("\n################  FLOW WIRING (server.py) ################")
S = os.path.join(HOME, "Vintos", "server.py")
if os.path.isfile(S):
    st = open(S, encoding="utf-8", errors="ignore").read()
    for name, rx in {"Arrival directive injected": r"\[ARRIVAL|arrival", "Bilateral A1/B1/synthesis": r"a1|b1|synthes",
                     "BIS": r"\bbis\b|behavioral.?intercept", "Presence audit call": r"presence.?audit",
                     "Offer enforced": r"\[OFFER|offer", "Silence/first-thought": r"first.?thought|what is missing",
                     "Bandwidth collapse hook": r"collapse|bandwidth", "The Button route": r"the.?button|/button|zero.?llm",
                     "Somatic bridge read": r"somatic"}.items():
        m = re.search(rx, st, re.I)
        print(f"   {name:<32} {'wired (server.py:'+str(st.count(chr(10),0,m.start())+1)+')' if m else 'NOT in server.py'}")
