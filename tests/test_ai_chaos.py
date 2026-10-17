"""The AI plays with its upgraded cards (Chaos / Endless upgrades): upgraded
costs, an upgraded range placed further back, an upgrade profile that
reacts, and a full Chaos battle between two AIs runs clean."""
import random

import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import cards
import chaos
import endless_upgrades as eu
from ai import AIController
from engine import Match, PLAYER, ENEMY


def up(card, title):
    return next(u for u in eu.CARD_UPS[card] if u.title == title)


def boon(key):
    return next(u for u in eu.BOONS if u.key == "boon:" + key)


def new_match(deck_a=None, deck_b=None):
    random.seed(0)
    return Match(list(deck_a or cards.DEFAULT_PLAYER_DECK),
                 list(deck_b or cards.DEFAULT_AI_DECK))


# ---- no upgrades: the profile is neutral
m = new_match()
ai = AIController(m, team=ENEMY, level=5)
p = ai._profile()
assert (p["tower"], p["eco"], p["army"], p["focus"], p["any"]) == (1.0, 1.0, 1.0, {}, False), p

# ---- Thrift: the AI sees (and pays) the discounted cost
m = new_match(deck_b=["knight", "musketeer", "fireball", "arrows",
                      "giant", "valkyrie", "minions", "skeletons"])
ai = AIController(m, team=ENEMY, level=5)
boon("thrift").apply(m, ENEMY)
m.hands[ENEMY][0] = "musketeer"
m.elixir[ENEMY] = 3.0
aff = {k: c for _, k, c in ai._affordable()}
assert "musketeer" in aff and aff["musketeer"].elixir == cards.CARDS["musketeer"].elixir - 1

# ---- Empress Ascendant: flying form for 3 elixir
m = new_match(deck_b=["spirit_empress", "knight", "musketeer", "fireball", "arrows",
                      "giant", "valkyrie", "minions"])
ai = AIController(m, team=ENEMY, level=5)
up("spirit_empress", "Empress Ascendant").apply(m, ENEMY)
m.hands[ENEMY][0] = "spirit_empress"
m.elixir[ENEMY] = 3.0
aff = {k: c for _, k, c in ai._affordable()}
assert aff["spirit_empress"].key == "spirit_empress_air" and aff["spirit_empress"].elixir == 3

# ---- an upgraded range (Sharpshooter Musketeer) defends from further back
m = new_match(deck_b=["musketeer", "knight", "fireball", "arrows", "giant",
                      "valkyrie", "minions", "skeletons"])
ai = AIController(m, team=ENEMY, level=5)
k = m.spawn_units(PLAYER, "knight", 1, 3.5, 13.0, deploy=0.0)[0]
gs = ai._group_stats([k])
base_spot = ai._defense_spot(m.card(ENEMY, "musketeer"), k, gs)
up("musketeer", "Sharpshooter").apply(m, ENEMY)
long = m.card(ENEMY, "musketeer")
far_spot = ai._defense_spot(long, k, gs)
assert long.range == 2 * cards.CARDS["musketeer"].range
assert far_spot[1] < base_spot[1] - 1.0, (base_spot, far_spot)    # local y: further back

# ---- the profile reacts to upgrades
ai.clock += 2.0
boon("tower_dmg").apply(m, ENEMY)
boon("elixir").apply(m, ENEMY)
p = ai._profile()
assert p["tower"] > 1.3 and p["eco"] == 1.5 and p["focus"].get("musketeer") and p["any"], p

# ---- a Chaos battle between two Master AIs runs to the end with upgrades
m = new_match(cards.AI_DECK_PRESETS["Hog Cycle"], cards.AI_DECK_PRESETS["Golem Beatdown"])
run = chaos.ChaosRun(m, seed=3)
a = AIController(m, team=PLAYER, level=5)
b = AIController(m, team=ENEMY, level=5)
a.rng.seed(1)
b.rng.seed(2)
f = 0
while not m.finished and f < 30 * 140:
    run.update()
    if run.choice:
        run.choose(chaos.ai_pick(m, PLAYER, run.choice, run.rng, run.picks))
        continue
    m.update(1 / 30)
    a.update(1 / 30)
    b.update(1 / 30)
    f += 1
assert run.round >= 2 and run.ai_picks and run.picks, (run.round, run.picks)
assert len(a.log) + len(b.log) > 10
print("ai chaos ok: %d offers, AI took %s" % (run.round, [u.title for u in run.ai_picks]))
