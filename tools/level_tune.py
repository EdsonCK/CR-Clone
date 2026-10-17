"""
============================================================================
  LEVEL_TUNE.PY  --  How hard is each Level?  (playtest with the AI)
============================================================================

Plays every Level (or the ones named) with a defend-only AI holding a
Levels-legal version of several AI preset decks, its cards and towers at the
level's recommended level, and reports the win rate and average stars
(a loss = 0 stars). Use it to keep difficulty steady when you change waves:

    python tools/level_tune.py                      all levels -> stdout
    python tools/level_tune.py bone_crypt rogues_den
    python tools/level_tune.py --json out.json      (also save the numbers)
    python tools/level_tune.py --scale 0.9 ...      every enemy x0.9 hp/dmg
    python tools/level_tune.py --scale bone_crypt=0.9,iron_legion=1.1 bone_crypt iron_legion
    SRC=/path/to/other/src python tools/level_tune.py   (measure another copy)

Env: PROCS (default 4), SEEDS (games per deck, default 2), AI (default 3).
============================================================================
"""

import json
import multiprocessing as mp
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.environ.get("SRC", os.path.join(ROOT, "src"))
sys.path.insert(0, SRC)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

DECKS = ["Classic", "Hog Cycle", "P.E.K.K.A Bridge", "Golem Beatdown", "MK Bats WB",
         "Royal Giant"]
MAX_SECONDS = 60 * 12


def play(args):
    key, deck_name, seed, scale, ai_level = args
    import cards
    import levels
    from engine import PLAYER
    from ai import AIController
    lv = levels.LEVELS_BY_KEY[key]
    # a worker plays many games: scale the level's own power, never compound
    if not hasattr(lv, "base_power"):
        lv.base_power = lv.power
    lv.power = lv.base_power * scale
    random.seed(seed)
    deck = levels.default_level_deck(cards.AI_DECK_PRESETS[deck_name])
    rl = levels.recommended_level(lv)
    m, run = levels.new_level_match(lv, deck, card_levels=rl, tower_level=rl, king_level=rl)
    a = AIController(m, team=PLAYER, level=ai_level)
    a.rng.seed(seed)
    a.defend_only = True
    f = 0
    while not m.finished and f < 30 * MAX_SECONDS:
        m.update(1 / 30)
        run.update(1 / 30)
        a.update(1 / 30)
        f += 1
    won = m.winner == PLAYER
    stars = run.stars() if won else 0
    return key, won, stars, run.wave_number


def measure(keys, scale=1.0, seeds=2, ai_level=3, procs=4):
    jobs = [(k, d, s, scale.get(k, 1.0), ai_level)
            for k in keys for d in DECKS for s in range(seeds)]
    out = {k: {"wins": 0, "stars": 0, "n": 0, "waves": 0} for k in keys}
    with mp.Pool(procs) as p:
        for key, won, stars, wave in p.imap_unordered(play, jobs):
            r = out[key]
            r["n"] += 1
            r["wins"] += won
            r["stars"] += stars
            r["waves"] += wave
    for k, r in out.items():
        n = max(1, r["n"])
        r["win"] = round(r["wins"] / n, 3)
        r["score"] = round(r["stars"] / n, 3)
        r["avg_wave"] = round(r["waves"] / n, 2)
    return out


def main():
    args = sys.argv[1:]
    scale_arg, js = "1.0", None
    if "--scale" in args:
        i = args.index("--scale")
        scale_arg = args[i + 1]
        del args[i:i + 2]
    if "--json" in args:
        i = args.index("--json")
        js = args[i + 1]
        del args[i:i + 2]
    import levels
    keys = args or [lv.key for lv in levels.LEVELS]
    if "=" in scale_arg:
        scale = {k: float(v) for k, v in (p.split("=") for p in scale_arg.split(","))}
    else:
        scale = {k: float(scale_arg) for k in keys}
    res = measure(keys, scale, int(os.environ.get("SEEDS", "2")), int(os.environ.get("AI", "3")),
                  int(os.environ.get("PROCS", "4")))
    for k in keys:
        r = res[k]
        print("%-18s win %3.0f%%  stars %.2f  reached wave %.1f" % (k, 100 * r["win"], r["score"],
                                                                   r["avg_wave"]), flush=True)
    if js:
        with open(js, "w") as f:
            json.dump(res, f, indent=1)


if __name__ == "__main__":
    main()
