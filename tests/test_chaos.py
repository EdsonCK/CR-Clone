"""Chaos battles: offer timing and rarities, same rarities for both sides,
nothing repeats, per-team effects; a full match with two Master AIs runs."""
import collections
import random

import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import cards
import chaos
import endless_upgrades as eu
from ai import AIController
from engine import Match, PLAYER, ENEMY

N = chaos.total_rounds()
assert N == 6, N                                   # 45, 90, ... 270 s (in overtime)

# ---- rarities: first offer 25% R+R / 50% R+E / 25% E+E, last always L+L
rng = random.Random(7)
c = collections.Counter(tuple(chaos.roll_tiers(1, rng)) for _ in range(8000))
share = {k: v / 8000 for k, v in c.items()}
assert set(share) == {("rare", "rare"), ("rare", "epic"), ("epic", "epic")}, share
assert abs(share[("rare", "rare")] - 0.25) < 0.03
assert abs(share[("rare", "epic")] - 0.50) < 0.03
assert abs(share[("epic", "epic")] - 0.25) < 0.03
assert all(chaos.roll_tiers(N, rng) == ["legendary", "legendary"] for _ in range(200))
leg = [chaos.tier_weights(r)[2] for r in range(1, N + 1)]
assert leg == sorted(leg) and leg[0] == 0.0, leg   # rarer tiers grow over the match


# ---- a full match: both sides offered the same rarities, nothing repeats
def full_match(seed):
    random.seed(seed)
    decks = list(cards.AI_DECK_PRESETS.values())
    m = Match(list(decks[seed % len(decks)]), list(decks[(seed + 3) % len(decks)]))
    run = chaos.ChaosRun(m, seed)
    a = AIController(m, team=PLAYER, level=5)
    b = AIController(m, team=ENEMY, level=5)
    rounds = []
    f = 0
    while not m.finished and f < 30 * 320:
        run.update()
        if run.choice:
            assert run.time_to_next() is not None
            mine = [u.tier for u in run.choice]
            theirs = [u.tier for u in run.ai_options]
            rounds.append((run.round, list(run.tiers), mine, theirs))
            run.choose(chaos.ai_pick(m, PLAYER, run.choice, run.rng, run.picks))
            continue
        m.update(1 / 30)
        a.update(1 / 30)
        b.update(1 / 30)
        f += 1
    return m, run, rounds


for seed in range(3):
    m, run, rounds = full_match(seed)
    for rnd, tiers, mine, theirs in rounds:
        assert mine == tiers and theirs == tiers, (rnd, tiers, mine, theirs)
    for picks in (run.picks, run.ai_picks):
        keys = [u.key for u in picks]
        assert len(keys) == len(set(keys)), keys      # one-time in Chaos
    assert len(run.picks) == len(run.ai_picks) == run.round
    print("seed", seed, "rounds", run.round, "winner", m.winner,
          [u.title for u in run.picks], "|", [u.title for u in run.ai_picks])

# ---- the offers only ever hold cards from that side's own deck
m = Match(["knight", "hog_rider", "fireball", "musketeer", "zap", "cannon", "skeletons",
           "valkyrie"], list(cards.DEFAULT_AI_DECK))
for i in range(300):
    for team in (PLAYER, ENEMY):
        for u in chaos.offer(m, team, ["epic", "legendary"], random.Random(i)):
            assert u.kind == "boon" or u.card in m.decks[team], (team, u.key)
            assert u.key not in chaos.EXCLUDED

# ---- effects are per side: Elixir Flow speeds up only the side that took it
m = Match(list(cards.DEFAULT_PLAYER_DECK), list(cards.DEFAULT_AI_DECK))
next(u for u in eu.BOONS if u.key == "boon:elixir").apply(m, ENEMY)
m.elixir = [0.0, 0.0]
for _ in range(30 * 4):
    m.update(1 / 30)
assert m.elixir[ENEMY] > m.elixir[PLAYER] * 1.4, m.elixir

# ---- Rebuild takes back the crown the fallen tower gave away
m = Match(list(cards.DEFAULT_PLAYER_DECK), list(cards.DEFAULT_AI_DECK))
tw = m.towers[(PLAYER, "left")]
tw.take_damage(tw.max_hp * 3)
m.update(1 / 30)
assert m.crowns[ENEMY] == 1
next(u for u in eu.BOONS if u.key == "boon:rebuild").apply(m, PLAYER)
assert tw.alive and m.crowns[ENEMY] == 0
print("chaos ok")
