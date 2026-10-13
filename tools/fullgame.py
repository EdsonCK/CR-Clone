"""
============================================================================
  FULLGAME.PY  --  Card strength measured in full AI-vs-AI matches
============================================================================

The engagement benchmark in balance.py judges cards in short, isolated
fights. That's fast and precise but it misses everything a real match has:
spells answering support troops, champions' abilities, pushes building up
over time, elixir pressure... This tool measures the other end:

  * thousands of complete 3-minute matches between two "Skilled" (level 3)
    AIs, each with a random legal deck (8 cards, at most one champion);
  * a Bradley-Terry / logistic model fitted on the results:
        P(deck A beats deck B) = sigmoid( sum(beta[a]) - sum(beta[b]) )
    so every card gets a strength beta that is corrected for the other
    cards it happened to share a deck with.

beta = 0 is an average card. A card's "win rate" is reported as
sigmoid(beta): the chance a deck wins against an otherwise identical deck
that has an average card in that slot. Each beta comes with a standard error
(from the model's Fisher information), so noise can be told apart from a
real imbalance.

Usage (from the project root):
    python tools/fullgame.py OUT.json [SNAPSHOT.json] [GAMES]
SNAPSHOT is a {card: power factor} file from balance.py (empty = the stats
in cards.py). PROCS=4 sets the number of worker processes.
============================================================================
"""

import json
import math
import multiprocessing as mp
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import cards                    # noqa: E402
import balance as B             # noqa: E402

AI_LEVEL = int(os.environ.get("AI_LEVEL", "3"))
MAX_FRAMES = 30 * 260           # 3 min + overtime, at 30 fps


def random_deck(rng, keys, champs):
    """8 distinct cards, at most one champion (as in Clash Royale)."""
    while True:
        d = rng.sample(keys, 8)
        if sum(k in champs for k in d) <= 1:
            return d


def _game(args):
    seed, snapshot = args
    from engine import Match, PLAYER, ENEMY
    from ai import AIController
    B.install(snapshot)
    keys = sorted(c.key for c in cards.DEPLOYABLE_CARDS)
    champs = {c.key for c in cards.DEPLOYABLE_CARDS if c.is_champion}
    rng = random.Random(seed)
    da, db = random_deck(rng, keys, champs), random_deck(rng, keys, champs)
    random.seed(seed)
    m = Match(da, db)
    ais = [AIController(m, PLAYER, AI_LEVEL), AIController(m, ENEMY, AI_LEVEL)]
    for a in ais:
        a.rng.seed(seed * 2 + a.me)
    f = 0
    while not m.finished and f < MAX_FRAMES:
        for a in ais:
            a.update(1 / 30)
        m.update(1 / 30)
        f += 1
    w = None if m.winner is None else (1 if m.winner == PLAYER else 0)
    return da, db, w


def play(snapshot, games, procs=4, seed0=0):
    jobs = [(seed0 + i, snapshot) for i in range(games)]
    out = []
    with mp.Pool(procs) as p:
        for i, r in enumerate(p.imap_unordered(_game, jobs, chunksize=8)):
            out.append(r)
            if (i + 1) % 500 == 0:
                print("  %d / %d games" % (i + 1, games), flush=True)
    return out


def fit(results, l2=1.0, iters=60):
    """Bradley-Terry fit by Newton's method on a diagonal approximation
    (cheap, and plenty for ~120 features). Returns {card: (beta, se)}."""
    keys = sorted({k for da, db, w in results for k in da + db})
    idx = {k: i for i, k in enumerate(keys)}
    rows = [([idx[k] for k in da], [idx[k] for k in db], w)
            for da, db, w in results if w is not None]
    beta = [0.0] * len(keys)
    for _ in range(iters):
        g = [-l2 * b for b in beta]
        h = [l2] * len(keys)
        for a, b, w in rows:
            z = sum(beta[i] for i in a) - sum(beta[i] for i in b)
            p = 1.0 / (1.0 + math.exp(-z))
            r = w - p
            v = p * (1 - p)
            for i in a:
                g[i] += r
                h[i] += v
            for i in b:
                g[i] -= r
                h[i] += v
        step = [gi / hi for gi, hi in zip(g, h)]
        beta = [bi + 0.8 * s for bi, s in zip(beta, step)]
        mean = sum(beta) / len(beta)
        beta = [bi - mean for bi in beta]   # only differences are identified
        if max(abs(s) for s in step) < 1e-5:
            break
    se = [1.0 / math.sqrt(hi) for hi in h]
    return {k: (beta[idx[k]], se[idx[k]]) for k in keys}


def summary(fitres):
    return {k: {"beta": b, "se": s, "wr": 1.0 / (1.0 + math.exp(-b))}
            for k, (b, s) in fitres.items()}


if __name__ == "__main__":
    out_path = sys.argv[1]
    snap = B.load(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != "-" else {}
    snap = {k: (v["f"] if isinstance(v, dict) else v) for k, v in snap.items()}
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 10000
    procs = int(os.environ.get("PROCS", "4"))
    seed0 = int(os.environ.get("SEED0", "0"))
    res = play(snap, n, procs, seed0)
    draws = sum(1 for r in res if r[2] is None)
    summ = summary(fit(res))
    with open(out_path, "w") as f:
        json.dump({"games": len(res), "draws": draws, "cards": summ,
                   "results": res}, f)
    for k, v in sorted(summ.items(), key=lambda kv: -kv[1]["beta"]):
        print("  %-18s wr %5.1f%%  beta %+5.2f  se %.2f" % (k, 100 * v["wr"], v["beta"], v["se"]))
