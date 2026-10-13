"""
============================================================================
  BALANCE_V2.PY  --  Hybrid balancing: engagements propose, full games decide
============================================================================

One round of the v2 balance run:

  1. tools/fullgame.py measures every card's strength (beta, with a standard
     error) in thousands of full AI-vs-AI matches at the current snapshot.
  2. tools/balance.py tune proposes a power factor for every tunable card
     from the (v2) engagement benchmark.
  3. combine (this file) decides the next snapshot, card by card:

       full games say...        engagements say...      ->  move
       ----------------------   ---------------------       ----------------
       fine (|z| < Z_FINE)      anything                    none
       too strong / too weak    the same direction          the engagement's
                                                            step (damped), but
                                                            no bigger than the
                                                            full-game estimate
       clearly off (|z| >= Z_SOLO,  nothing / the opposite  a small step led by
       |beta| >= B_SOLO)                                    the full games

     so an engagement-only verdict never changes a card, and a strong
     full-game verdict is acted on even when the isolated fights miss it
     (champion abilities, spell pressure on support troops...).

Power factor f scales hp and damage like balance.py does (hp*f^a, dmg*f^(1-a)).
K converts a full-game beta into a power change: f = exp(-K * beta).

Usage:
    python tools/balance_v2.py combine SNAP_IN TUNE.json FULL.json SNAP_OUT
    python tools/balance_v2.py report FULL.json [FULL_BEFORE.json]
============================================================================
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import balance as B             # noqa: E402

Z_FINE = 2.0          # |beta / se| below this: the card is fine
Z_SOLO = 3.0          # full games alone may move a card past this...
B_SOLO = 0.12         # ...if it's also at least this far off (~3% win rate)
K = float(os.environ.get("K", "0.9"))
DAMP = 0.6            # share of the engagement's proposed step taken
SOLO = 0.5            # share of the full-game step taken when it acts alone
MAX_STEP = 0.25       # max |log f| change per round (~ +/-25%)
# A buff that measurably did nothing in full games (the card's result is set
# by how the AI plays it, not by its stats) isn't pushed further: such cards
# are capped at INSENSITIVE_CAP in total and listed as "AI-limited".
INSENSITIVE_CAP = 1.35
MIN_RESPONSE = 0.3    # observed / expected change in beta, below = insensitive


def load(path):
    with open(path) as f:
        return json.load(f)


def response(prev_snap, prev_full, snap, full, key):
    """How much of the expected full-game change a card's last power change
    produced (1 = as expected, 0 = nothing). None if it barely moved."""
    if not prev_full or key not in prev_full["cards"]:
        return None
    dl = math.log(snap.get(key, 1.0) / prev_snap.get(key, 1.0))
    if abs(dl) < 0.1:
        return None
    observed = full["cards"][key]["beta"] - prev_full["cards"][key]["beta"]
    return observed / (dl / K)


def combine(snap, tuned, full, prev_snap=None, prev_full=None):
    cards_ = full["cards"]
    out, notes = dict(snap), []
    for key in B.tune_pool():
        if key not in cards_:
            continue
        f0 = snap.get(key, 1.0)
        beta, se = cards_[key]["beta"], cards_[key]["se"]
        z = beta / se if se > 0 else 0.0
        t = tuned.get(key)
        fe = (t["f"] if isinstance(t, dict) else t) if t is not None else f0
        ge = math.log(fe / f0)                  # engagement step (+ = buff)
        gg = -K * beta                          # full-game step  (+ = buff)
        if abs(z) < Z_FINE:
            step, why = 0.0, "fine in full games"
        elif ge * gg > 0:
            step = math.copysign(min(abs(ge) * DAMP, abs(gg)), gg)
            why = "both agree"
        elif abs(z) >= Z_SOLO and abs(beta) >= B_SOLO:
            step, why = gg * SOLO, "full games (engagements disagree)"
        else:
            step, why = 0.0, "engagements disagree, full-game signal weak"
        step = max(-MAX_STEP, min(MAX_STEP, step))
        f1 = max(B.F_MIN, min(B.F_MAX, f0 * math.exp(step)))
        r = response(prev_snap or {}, prev_full, snap, full, key)
        if r is not None and r < MIN_RESPONSE and f0 > 1.0 and f1 >= f0:
            f1 = min(f1, max(1.0, min(f0, INSENSITIVE_CAP)))
            f1 = min(f1, INSENSITIVE_CAP)
            why = "AI-limited (buff had no effect, response %.2f)" % r
        out[key] = f1
        notes.append((key, f0, f1, beta, se, fe, why))
    return out, notes


def report(full, before=None):
    cs = full["cards"]
    rows = sorted(cs.items(), key=lambda kv: -kv[1]["beta"])
    groups = {"champions": [], "ranged single-target": [], "everything else": []}
    import cards
    for k, v in rows:
        c = cards.CARDS[k]
        if c.is_champion:
            groups["champions"].append(v["wr"])
        elif (c.category == "troop" and c.range >= 3.5 and not c.splash and not c.chain
              and c.attacks != "buildings"):
            groups["ranged single-target"].append(v["wr"])
        else:
            groups["everything else"].append(v["wr"])
    print("games %d (draws %d)" % (full["games"], full["draws"]))
    for g, v in groups.items():
        if v:
            print("  %-22s mean win rate %5.1f%%  (%d cards)" % (g, 100 * sum(v) / len(v), len(v)))
    sd = math.sqrt(sum((v["beta"]) ** 2 for _, v in rows) / len(rows))
    print("  spread (sd of beta) %.3f" % sd)
    if before:
        sd0 = math.sqrt(sum(v["beta"] ** 2 for v in before["cards"].values()) / len(before["cards"]))
        print("  spread before        %.3f" % sd0)
    print("  top:    " + ", ".join("%s %.0f%%" % (k, 100 * v["wr"]) for k, v in rows[:8]))
    print("  bottom: " + ", ".join("%s %.0f%%" % (k, 100 * v["wr"]) for k, v in rows[-8:]))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "combine":
        snap = B.load(sys.argv[2])
        snap = {k: (v["f"] if isinstance(v, dict) else v) for k, v in snap.items()}
        tuned = load(sys.argv[3])
        full = load(sys.argv[4])
        # the previous round (snapR-1 / fullR-1 next to these files), if any
        import re
        prev_snap = prev_full = None
        mm = re.search(r"snap(\d+)\.json$", sys.argv[2])
        if mm and int(mm.group(1)) > 0:
            d = os.path.dirname(sys.argv[2])
            r0 = int(mm.group(1)) - 1
            ps, pf = os.path.join(d, "snap%d.json" % r0), os.path.join(d, "full%d.json" % r0)
            if os.path.exists(ps) and os.path.exists(pf):
                prev_snap, prev_full = B.load(ps), load(pf)
        out, notes = combine(snap, tuned, full, prev_snap, prev_full)
        with open(sys.argv[5], "w") as f:
            json.dump(out, f, indent=1)
        for key, f0, f1, beta, se, fe, why in sorted(notes, key=lambda n: n[2] / n[1]):
            if abs(f1 / f0 - 1) > 1e-6 or why.startswith("AI-limited"):
                print("  %-18s %.3f -> %.3f   (wr %4.1f%%, z %+.1f, engagement %.2f: %s)" % (
                    key, f0, f1, 100 / (1 + math.exp(-beta)), beta / se, fe, why))
    elif cmd == "report":
        before = load(sys.argv[3]) if len(sys.argv) > 3 else None
        report(load(sys.argv[2]), before)
