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


class _NoRun:
    def update(self, dt):
        pass


def battle_with(card):
    """Win conditions are banned in Endless: try theirs in a battle (Chaos)."""
    from engine import Match
    deck = [card] + [k for k in cards.DEFAULT_PLAYER_DECK if k != card][:7]
    return Match(deck, list(cards.DEFAULT_AI_DECK)), _NoRun()


# ---- every upgrade applies and its card plays (win conditions in a battle,
# for Chaos; for each side)
n = 0
for ups in eu.CARD_UPS.values():
    for u in ups:
        banned = u.card in levels.BANNED
        m, run = battle_with(u.card) if banned else run_with(u.card)
        u.apply(m, PLAYER)
        u.apply(m, PLAYER)                    # stacking twice is fine too
        if banned:
            u.apply(m, ENEMY)
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


# ---- Witch spawns twice as fast (one-time)
m, run = run_with("witch")
up("witch", "Coven Mother").apply(m, PLAYER)
assert up("witch", "Coven Mother").once
assert abs(m.card(PLAYER, "witch").spawner[2] - cards.CARDS["witch"].spawner[2] / 2) < 1e-6
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
assert m.boons[PLAYER]["elixir"] == 1.5 and m.elixir_multiplier() == 1.0
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

# ---- the run offers a choice after every 4th wave and applies the pick
m, run = run_with("knight")
while len(run.level.waves) < 6:
    run.level.waves.append(levels.endless_wave(len(run.level.waves) + 1, run.rng))
run._start_wave(eu.LEVEL_EVERY - 1)
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

# ---- one-time upgrades are never offered again; stackable ones stack
m, run = run_with("vines")
once = up("vines", "Overgrowth")
for _ in range(300):
    for o in eu.offer(m, ["vines"] * 8, random.Random(_), taken=[once.key]):
        assert o.key != once.key
asc = boon("ascend")
assert asc.once and all(asc not in eu.offer(m, ["knight"], random.Random(i), [asc.key])
                        for i in range(300))
m, run = run_with("elixir_collector")
pump = up("elixir_collector", "Elixir Pump")
pump.apply(m, PLAYER)
pump.apply(m, PLAYER)
assert m.card(PLAYER, "elixir_collector").generates_elixir[0] == 3.0
m, run = run_with("knight")
lt = m.towers[(PLAYER, "left")]
d0, r0, h0 = lt.dmg, lt.range, lt.max_hp
for _ in range(2):
    boon("tower_dmg").apply(m, PLAYER)
    boon("tower_range").apply(m, PLAYER)
    boon("tower_hp").apply(m, PLAYER)
assert abs(lt.dmg - d0 * 1.75 ** 2) < 1e-6 and abs(lt.range - (r0 + 5.0)) < 1e-6
assert lt.sight == lt.range and lt.max_hp >= int(h0 * 1.5 * 1.5) - 1
lt.hp = lt.max_hp * 0.3                      # Stone Walls also fully repairs
boon("tower_hp").apply(m, PLAYER)
assert lt.hp == lt.max_hp, "Stone Walls should fully heal"

# ---- boons never depend on your deck (only Rebuild needs a fallen tower)
for deck in (["knight"] * 8, ["fireball"] * 8, ["skeletons"] * 8):
    seen = {o.key for i in range(400)
            for o in eu.offer(m, deck, random.Random(i)) if o.kind == "boon"}
    assert seen == {b.key for b in eu.BOONS} - {"boon:rebuild"}, deck

# ---- range upgrades carry the sight: a doubled Musketeer stops twice as far
m, run = run_with("musketeer")
up("musketeer", "Sharpshooter").apply(m, PLAYER)
c = m.card(PLAYER, "musketeer")
base = cards.CARDS["musketeer"]
assert c.range == base.range * 2 and c.sight >= c.range
play(m, "musketeer")
mus = [e for e in m.entities if e.key == "musketeer" and e.team == PLAYER][0]
for _ in range(30 * 25):
    m.update(1 / 30)
tw = m.towers[(ENEMY, "left" if mus.lane == 0 else "right")]
stop = ((mus.x - tw.x) ** 2 + (mus.y - tw.y) ** 2) ** 0.5
assert stop > base.range * 1.8, (stop, base.range)

# ---- ranged enemies: boss / wave power adds health, never damage
m, run = run_with("knight")
w = levels.Wave("t", [levels.Spawn("musketeer", 0, "left", None, 3.0),
                      levels.Spawn("knight", 0, "right", None, 3.0)],
                level=11, boss=True, power=2.0, ranged_hp_only=True)
run.level.waves.append(w)
run._start_wave(len(run.level.waves) - 1)
sim(m, run, 0.2)
mk = next(e for e in m.entities if e.key == "musketeer" and e.team == ENEMY)
kn = next(e for e in m.entities if e.key == "knight" and e.team == ENEMY)
assert abs(mk.power[0] - kn.power[0]) < 1e-6 and mk.power[0] > 5
assert mk.power[1] < 1.5 and kn.power[1] > 5, (mk.power, kn.power)
print("special upgrades ok")
