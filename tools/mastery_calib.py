"""
============================================================================
  MASTERY_CALIB.PY  --  How much a card does in an average match
============================================================================

Card Mastery tasks ask for "deal N damage", "destroy N troops"... To make
every card's tasks take about the same number of matches, this plays AI vs
AI matches with random decks and measures, per card, the average per match
(when the card is in the deck) of:

    dmg     damage dealt by the card (its units / spell)
    tower   damage dealt to crown towers
    kills   enemy units destroyed
    plays   times played

and writes src/mastery_data.py. Usage (from the project root):
    python tools/mastery_calib.py [GAMES]        (default 1600, PROCS=4)
============================================================================
"""

import multiprocessing as mp
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import cards        # noqa: E402

MAX_FRAMES = 30 * 260
KINDS = ("dmg", "tower", "kills", "plays")


def _game(seed):
    from engine import Match, PLAYER, ENEMY
    from ai import AIController
    import mastery
    keys = sorted(c.key for c in cards.DEPLOYABLE_CARDS)
    champs = {c.key for c in cards.DEPLOYABLE_CARDS if c.is_champion}
    rng = random.Random(seed)

    def deck():
        while True:
            d = rng.sample(keys, 8)
            if sum(k in champs for k in d) <= 1:
                return d
    da, db = deck(), deck()
    random.seed(seed)
    m = Match(da, db)
    ais = [AIController(m, PLAYER, 3), AIController(m, ENEMY, 3)]
    for a in ais:
        a.rng.seed(seed * 2 + a.me)
    f = 0
    while not m.finished and f < MAX_FRAMES:
        for a in ais:
            a.update(1 / 30)
        m.update(1 / 30)
        f += 1
    return [mastery.card_stats(m, PLAYER, da), mastery.card_stats(m, ENEMY, db)]


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 1600
    procs = int(os.environ.get("PROCS", "4"))
    tot, n = {}, {}
    with mp.Pool(procs) as p:
        for i, res in enumerate(p.imap_unordered(_game, range(games), chunksize=4)):
            for side in res:
                for k, st in side.items():
                    n[k] = n.get(k, 0) + 1
                    t = tot.setdefault(k, {x: 0.0 for x in KINDS})
                    for x in KINDS:
                        t[x] += st.get(x, 0.0)
            if (i + 1) % 200 == 0:
                print("  %d / %d" % (i + 1, games), flush=True)
    avg = {k: {x: round(tot[k][x] / n[k], 2) for x in KINDS} for k in sorted(tot)}
    lines = ['"""Per-match averages per card (tools/mastery_calib.py, %d AI games).' % games,
             'Used to size Card Mastery task goals. Generated - do not edit."""', "",
             "AVG = {"]
    for k, v in avg.items():
        lines.append("    %r: {%s},  # n=%d" % (k, ", ".join("%r: %s" % (x, v[x]) for x in KINDS),
                                                n[k]))
    lines.append("}")
    with open(os.path.join(ROOT, "src", "mastery_data.py"), "w") as f:
        f.write("\n".join(lines) + "\n")
    missing = [c.key for c in cards.DEPLOYABLE_CARDS if c.key not in avg]
    print("wrote src/mastery_data.py (%d cards; missing %s)" % (len(avg), missing))


if __name__ == "__main__":
    main()
