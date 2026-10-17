"""Endless upgrades: every card has one, every upgrade applies and plays
without errors, and the special ones do what they say."""
import random

import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import cards
import endless_upgrades as eu
import levels
from engine import PLAYER, ENEMY

ELIGIBLE = [c.key for c in cards.DEPLOYABLE_CARDS if c.key not in levels.BANNED]
missing = [k for k in ELIGIBLE
           if not any(not u.key.endswith(":veteran") for u in eu.CARD_UPS.get(k, []))]
assert not missing, missing
keys = [u.key for ups in eu.CARD_UPS.values() for u in ups] + [u.key for u in eu.BOONS]
assert len(keys) == len(set(keys)), "duplicate upgrade keys"


def run_with(card, seed=0):
    deck = levels.default_level_deck([card])
    random.seed(seed)
    m, run = levels.new_endless_match(deck, card_levels=11, tower_level=11, seed=seed)
    return m, run


def spot(key):
    c = cards.CARDS[key]
    return (9.5, 13.5) if c.category == "spell" and not c.own_side else (9.5, 22.5)


def play(m, key):
    m.elixir[PLAYER] = 10
    m.hands[PLAYER][0] = key
    x, y = spot(key)
    return m.play_card(PLAYER, 0, x, y)


def enemies(m, n=3):
    for i in range(n):
        m.spawn_units(ENEMY, "knight", 1, 6.5 + 2.5 * i, 13.5, deploy=0.0)
    m.spawn_units(ENEMY, "minions", 3, 9.5, 12.5, deploy=0.0)


def sim(m, run, secs):
    for _ in range(int(secs * 30)):
        m.update(1 / 30)
        run.update(1 / 30)
        if m.finished:
            break


# ---- every upgrade applies and its card plays
n = 0
for ups in eu.CARD_UPS.values():
    for u in ups:
        m, run = run_with(u.card)
        u.apply(m, PLAYER)
        u.apply(m, PLAYER)                    # stacking twice is fine too
        enemies(m)
        assert play(m, u.card) or u.card == "mirror", u.key
        sim(m, run, 6)
        n += 1
for u in eu.BOONS:
    m, run = run_with("knight")
    u.apply(m, PLAYER)
    enemies(m)
    assert play(m, "knight"), u.key
    sim(m, run, 4)
    n += 1
print("applied + played", n, "upgrades")


def up(card, title):
    return next(u for u in eu.CARD_UPS[card] if u.title == title)


def boon(key):
    return next(u for u in eu.BOONS if u.key == "boon:" + key)


# ---- Witch spawns 3x as fast
m, run = run_with("witch")
up("witch", "Coven Mother").apply(m, PLAYER)
assert abs(m.card(PLAYER, "witch").spawner[2] - cards.CARDS["witch"].spawner[2] / 3) < 1e-6
assert cards.CARDS["witch"].spawner[2] == 5.0           # the real card is untouched

# ---- Tombstone spawns Guards
m, run = run_with("tombstone")
up("tombstone", "Honor Guard").apply(m, PLAYER)
play(m, "tombstone")
sim(m, run, 6)
assert any(e.key == "guards" and e.team == PLAYER for e in m.entities)
assert not any(e.key == "skeleton" and e.team == PLAYER for e in m.entities)

# ---- Furnace spawns every spirit
m, run = run_with("furnace")
up("furnace", "Spirit Forge").apply(m, PLAYER)
play(m, "furnace")
seen = set()
for _ in range(30 * 10):
    m.update(1 / 30)
    seen |= {e.key for e in m.entities if e.team == PLAYER and e.key.endswith("_spirit")}
assert {"fire_spirit", "ice_spirit", "electro_spirit", "heal_spirit"} <= seen, seen

# ---- Ice Wizard freezes
m, run = run_with("ice_wizard")
up("ice_wizard", "Absolute Zero").apply(m, PLAYER)
k = m.spawn_units(ENEMY, "knight", 1, 9.5, 18.0, deploy=0.0)[0]
play(m, "ice_wizard")
frozen = False
for _ in range(30 * 6):
    m.update(1 / 30)
    frozen = frozen or k.freeze_timer > 0
assert frozen

# ---- Skeleton Army rises 3 times
m, run = run_with("skeleton_army")
up("skeleton_army", "Army of the Dead").apply(m, PLAYER)
play(m, "skeleton_army")
seen = []                                # keep them alive: ids get reused
for _ in range(30 * 22):
    m.update(1 / 30)
    seen += [e for e in m.entities if e.key == "skeleton_army" and e.team == PLAYER
             and not any(e is s for s in seen[-60:])]
assert len(seen) >= 45, len(seen)

# ---- Spirit Empress: flying form for 3 elixir
m, run = run_with("spirit_empress")
up("spirit_empress", "Empress Ascendant").apply(m, PLAYER)
m.elixir[PLAYER] = 3
assert m.card_cost(PLAYER, "spirit_empress") == 3
assert m.play_key(PLAYER, "spirit_empress") == "spirit_empress_air"

# ---- Elixir Pump: 2 per pump
m, run = run_with("elixir_collector")
up("elixir_collector", "Elixir Pump").apply(m, PLAYER)
assert m.card(PLAYER, "elixir_collector").generates_elixir[0] == 2.0

# ---- Vines never end
m, run = run_with("vines")
up("vines", "Overgrowth").apply(m, PLAYER)
enemies(m)
play(m, "vines")
sim(m, run, 12)
assert any(fx.kind == "vines" for fx in m.effects)

# ---- boons
m, run = run_with("knight")
before = m.towers[(PLAYER, "left")].dmg
boon("tower_dmg").apply(m, PLAYER)
assert abs(m.towers[(PLAYER, "left")].dmg - before * 1.75) < 1e-6
boon("elixir").apply(m, PLAYER)
assert m.elixir_multiplier() == 1.5
boon("thrift").apply(m, PLAYER)
assert m.card_cost(PLAYER, "knight") == cards.CARDS["knight"].elixir - 1
lv = m.card_level(PLAYER, "knight")
boon("levels").apply(m, PLAYER)
assert m.card_level(PLAYER, "knight") == lv + 1
tw = m.towers[(PLAYER, "right")]
tw.take_damage(tw.max_hp * 2)
m.update(1 / 30)
assert not tw.alive
boon("rebuild").apply(m, PLAYER)
m.update(1 / 30)
assert tw.alive and tw.hp == tw.max_hp and tw in m.entities

# ---- the run offers a choice after wave 5 and applies the pick
m, run = run_with("knight")
while len(run.level.waves) < 6:
    run.level.waves.append(levels.endless_wave(len(run.level.waves) + 1, run.rng))
run._start_wave(4)
run.pending = []
for e in m.entities:
    if e.team == ENEMY and not e.is_tower:
        e.alive = False
sim(m, run, 1)
assert run.choice and len(run.choice) == 2, run.choice
assert run.choice[0].kind == "card" and run.choice[1].kind == "boon"
t0 = m.elapsed
run.update(1.0)                          # paused while choosing
u = run.choose(1)
assert run.picks == [u] and run.choice is None
print("special upgrades ok")
