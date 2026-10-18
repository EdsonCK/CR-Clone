"""Unique modifiers, batch B (chaos_mods_b): every one applies and plays for
either side without errors, and a sample does what it says."""
import random

import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import cards
import endless_upgrades as eu  # noqa: F401  (registers every modifier)
import chaos_mods_b as B
from engine import Match, PLAYER, ENEMY

KEYS = ("sparky cannon tesla inferno_tower bomb_tower tombstone goblin_hut furnace "
        "elixir_collector zap the_log arrows fireball freeze rocket lightning "
        "skeleton_army guards zappies hunter executioner bowler magic_archer "
        "night_witch flying_machine electro_dragon mega_knight cannon_cart ice_golem "
        "miner battle_ram wall_breakers electro_spirit electro_giant battle_healer "
        "elixir_golem").split()
assert sorted(u.card for u in B.UNIQUE) == sorted(KEYS)
for u in B.UNIQUE:
    assert u.once and u.tier in ("rare", "epic", "legendary") and u in eu.CARD_UPS[u.card]


def setup(card, team=PLAYER, seed=0):
    random.seed(seed)
    deck = [card] + [k for k in cards.DEFAULT_PLAYER_DECK if k != card][:7]
    m = Match(deck if team == PLAYER else list(cards.DEFAULT_AI_DECK),
              deck if team == ENEMY else list(cards.DEFAULT_PLAYER_DECK))
    return m


def foes(m, team=PLAYER, y=13.5):
    other = 1 - team
    if team == ENEMY:
        y = 32 - y
    for i in range(3):
        m.spawn_units(other, "knight", 1, 6.5 + 2.5 * i, y, deploy=0.0)
    m.spawn_units(other, "minions", 3, 9.5, y - (1 if team == PLAYER else -1), deploy=0.0)


def play(m, card, team=PLAYER):
    c = cards.CARDS[card]
    x, y = (9.5, 13.5) if c.category == "spell" and not c.own_side else (9.5, 22.5)
    if team == ENEMY:
        y = 32 - y
    m.elixir[team] = 10
    m.hands[team][0] = card
    return m.play_card(team, 0, x, y)


def sim(m, secs, watch=None):
    for _ in range(int(secs * 30)):
        m.update(1 / 30)
        if watch:
            watch(m)
        if m.finished:
            break


def mod(card):
    return next(u for u in B.UNIQUE if u.card == card)


# ---- all of them, for the player (and the first few for the enemy too)
for i, u in enumerate(B.UNIQUE):
    for team in ((PLAYER, ENEMY) if i < 8 else (PLAYER,)):
        m = setup(u.card, team)
        u.apply(m, team)
        foes(m, team)
        assert play(m, u.card, team), (u.key, team)
        sim(m, 12)
print("played", len(B.UNIQUE), "modifiers")

# ---- behaviour checks
seen = set()


def keys(m):
    seen.update(e.key for e in m.entities if e.team == PLAYER and not e.is_tower)


# Tombstone -> Giant Skeleton when it breaks
m = setup("tombstone")
mod("tombstone").apply(m, PLAYER)
play(m, "tombstone")
sim(m, 1)
tomb = next(e for e in m.entities if e.key == "tombstone")
tomb.take_damage(tomb.hp + 1)
seen.clear()
sim(m, 1, keys)
assert "giant_skeleton" in seen, seen

# Furnace forges Baby Dragons
m = setup("furnace")
mod("furnace").apply(m, PLAYER)
play(m, "furnace")
seen.clear()
sim(m, 13, keys)
assert "baby_dragon" in seen and "fire_spirit" not in seen, seen

# Cannon -> Cannon Cart
m = setup("cannon")
mod("cannon").apply(m, PLAYER)
play(m, "cannon")
sim(m, 1.5)
next(e for e in m.entities if e.key == "cannon").take_damage(99999)
seen.clear()
sim(m, 0.5, keys)
assert "cannon_cart" in seen, seen

# The Log -> Lumberjack; Arrows -> Archers
for card, unit in (("the_log", "lumberjack"), ("arrows", "archers")):
    m = setup(card)
    mod(card).apply(m, PLAYER)
    foes(m)
    play(m, card)
    seen.clear()
    sim(m, 3, keys)
    assert unit in seen, (card, seen)

# Sparky blasts stun
m = setup("sparky")
mod("sparky").apply(m, PLAYER)
k = m.spawn_units(ENEMY, "knight", 1, 9.5, 18.0, deploy=0.0)[0]
k2 = m.spawn_units(ENEMY, "knight", 1, 10.5, 18.0, deploy=0.0)[0]
play(m, "sparky")
stunned = []
sim(m, 10, lambda m: stunned.append(k2.stun_timer > 0.6 or k.stun_timer > 0.6))
assert any(stunned)

# Hunter nets
m = setup("hunter")
mod("hunter").apply(m, PLAYER)
k = m.spawn_units(ENEMY, "knight", 1, 9.5, 19.0, deploy=0.0)[0]
play(m, "hunter")
roots = []
sim(m, 6, lambda m: roots.append(k.root_timer > 0))
assert any(roots)

# Ice Golem chills
m = setup("ice_golem")
mod("ice_golem").apply(m, PLAYER)
play(m, "ice_golem")
k = m.spawn_units(ENEMY, "knight", 1, 9.5, 20.5, deploy=0.0)[0]
slow = []
sim(m, 3, lambda m: slow.append(k.slow_factor <= 0.6))
assert any(slow)

# Zap repeats 4 more times
m = setup("zap")
mod("zap").apply(m, PLAYER)
foes(m)
play(m, "zap")
sim(m, 0.5)
assert sum(1 for x in m.later if x[1] == "blast") == 4

# Elixir Golem's blobs pay the owner, not the opponent
m = setup("elixir_golem")
mod("elixir_golem").apply(m, PLAYER)
assert m.card(PLAYER, "elixir_blob").death_gives_elixir == 0.0
blob = m.spawn_units(PLAYER, "elixir_blob", 1, 9.5, 20.0, deploy=0.0)[0]
m.elixir = [0.0, 0.0]
blob.take_damage(99999)
m.update(1 / 30)
assert m.elixir[PLAYER] >= 1.0 and m.elixir[ENEMY] < 0.2, m.elixir

# Electro Spirit splits once (2 more, no chain reaction)
m = setup("electro_spirit")
mod("electro_spirit").apply(m, PLAYER)
foes(m)
play(m, "electro_spirit")
made = []
sim(m, 6, lambda m: made.extend(e for e in m.entities if e.key == "electro_spirit"
                                and e.team == PLAYER and e not in made))
assert len(made) == 3, len(made)
print("chaos mods B ok")
