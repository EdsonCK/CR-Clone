"""Unique modifiers, batch A: every one applies (to either side), plays and
runs; the key ones do what they say."""
import random

import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import cards
import chaos_mods_a as A
from engine import Match, PLAYER, ENEMY

CARDS_A = ("skeletons ice_spirit fire_spirit goblins spear_goblins bats skeleton_barrel "
           "knight archers bomber valkyrie mini_pekka musketeer barbarians "
           "elite_barbarians wizard witch pekka prince dark_prince giant_skeleton "
           "lumberjack bandit hog_rider royal_giant balloon golem minions minion_horde "
           "mega_minion baby_dragon inferno_dragon princess electro_wizard ice_wizard "
           "three_musketeers").split()
BY = {u.card: u for u in A.UNIQUE}
assert set(BY) == set(CARDS_A), set(CARDS_A) ^ set(BY)
assert all(u.once and u.tier in ("rare", "epic", "legendary") for u in A.UNIQUE)


def match_with(card, team=PLAYER):
    random.seed(1)
    deck = [card] + [k for k in cards.DEFAULT_PLAYER_DECK if k != card][:7]
    m = Match(deck, deck) if team == ENEMY else Match(deck, list(cards.DEFAULT_AI_DECK))
    BY[card].apply(m, team)
    return m


def foes(m, team=ENEMY, y=13.5):
    out = []
    for i in range(3):
        out += m.spawn_units(team, "knight", 1, 6.5 + 2.5 * i, y, deploy=0.0)
    out += m.spawn_units(team, "minions", 3, 9.5, y - 1.0 if team == ENEMY else y + 1.0,
                         deploy=0.0)
    return out


def play(m, card, team=PLAYER):
    m.elixir[team] = 10
    m.hands[team][0] = card
    c = cards.CARDS[card]
    if team == PLAYER:
        x, y = (9.5, 13.5) if c.category == "spell" and not c.own_side else (9.5, 22.5)
    else:
        x, y = (9.5, 18.5) if c.category == "spell" and not c.own_side else (9.5, 9.5)
    assert m.play_card(team, 0, x, y), card


def sim(m, secs, watch=None):
    seen = set()
    for _ in range(int(secs * 30)):
        m.update(1 / 30)
        if watch is not None:
            seen |= {e.key for e in m.entities if e.team == watch and not e.is_tower}
    return seen


# ---- every modifier plays without errors, on the player's side
for card in CARDS_A:
    m = match_with(card)
    foes(m)
    play(m, card)
    sim(m, 12)
# ...and on the enemy's side too
for card in ("bats", "balloon", "wizard", "electro_wizard", "golem", "skeletons"):
    m = match_with(card, ENEMY)
    foes(m, PLAYER, y=18.5)
    play(m, card, ENEMY)
    sim(m, 12)
print("all", len(CARDS_A), "batch-A modifiers play")

# ---- behaviour
# Witch summons Bats
m = match_with("witch")
play(m, "witch")
assert "bat" in sim(m, 9, PLAYER) and "skeleton" not in sim(m, 0.1, PLAYER)

# Hog Rider: Royal Hogs when he falls
m = match_with("hog_rider")
play(m, "hog_rider")
sim(m, 1.5)
hog = next(e for e in m.entities if e.key == "hog_rider")
hog.take_damage(hog.max_hp * 2)
assert "royal_hogs" in sim(m, 0.5, PLAYER)

# Skeletons reassemble exactly once
m = match_with("skeletons")
play(m, "skeletons")
sim(m, 1.5)
for e in [e for e in m.entities if e.key == "skeletons"]:
    e.take_damage(999)
sim(m, 0.2)
again = [e for e in m.entities if e.key == "skeletons"]
assert len(again) == 3 and all(getattr(e, "_reborn", False) for e in again)
for e in again:
    e.take_damage(999)
sim(m, 0.5)
assert not [e for e in m.entities if e.key == "skeletons" and e.alive]

# Ice Spirit freezes everything around
m = match_with("ice_spirit")
ks = m.spawn_units(ENEMY, "knight", 3, 9.5, 21.0, deploy=0.0)
play(m, "ice_spirit")
froze = False
for _ in range(30 * 3):
    m.update(1 / 30)
    froze = froze or sum(1 for k in ks if k.freeze_timer > 1.0) >= 2
assert froze

# Goblins pocket elixir (compared with the same fight without the modifier)
def goblin_elixir(upgraded):
    random.seed(1)
    deck = ["goblins"] + [k for k in cards.DEFAULT_PLAYER_DECK if k != "goblins"][:7]
    m = Match(deck, list(cards.DEFAULT_AI_DECK))
    if upgraded:
        BY["goblins"].apply(m, PLAYER)
    k = m.spawn_units(ENEMY, "giant", 1, 9.5, 21.0, deploy=0.0)[0]
    k.speed = k.base_speed = 0
    play(m, "goblins")
    m.elixir[PLAYER] = 0.0
    for _ in range(30 * 4):
        m.update(1 / 30)
    return m.elixir[PLAYER]


assert goblin_elixir(True) > goblin_elixir(False) + 0.3

# Skeleton Barrel drops skeletons on the way
m = match_with("skeleton_barrel")
play(m, "skeleton_barrel")
n = 0
for _ in range(30 * 6):
    m.update(1 / 30)
    n = max(n, sum(1 for e in m.entities if e.key == "skeleton" and e.team == PLAYER))
assert n >= 3, n

# Royal Giant gets an escort of Guards
m = match_with("royal_giant")
play(m, "royal_giant")
assert "guards" in sim(m, 10, PLAYER)

# Electro Wizard's storm stuns several enemies at once
m = match_with("electro_wizard")
ks = m.spawn_units(ENEMY, "knight", 3, 9.5, 19.5, deploy=0.0)
for k in ks:
    k.speed = k.base_speed = 0
play(m, "electro_wizard")
stunned = 0
for _ in range(30 * 5):
    m.update(1 / 30)
    stunned = max(stunned, sum(1 for k in ks if k.alive and k.stun_timer > 0))
assert stunned >= 2, stunned

# Elite Barbarians shrug off stuns and freezes
m = match_with("elite_barbarians")
play(m, "elite_barbarians")
sim(m, 1.5)
eb = [e for e in m.entities if e.key == "elite_barbarians"]
for e in eb:
    e.stun_timer = e.freeze_timer = 3.0
sim(m, 0.1)
assert all(e.stun_timer == 0 and e.freeze_timer == 0 for e in eb)

# Baby Dragon: 2 Skeleton Dragons when she falls
m = match_with("baby_dragon")
play(m, "baby_dragon")
sim(m, 1.5)
bd = next(e for e in m.entities if e.key == "baby_dragon")
bd.take_damage(bd.max_hp * 2)
sd = [e for e in m.entities if e.key == "skeleton_dragons"]
sim(m, 0.2)
assert sum(1 for e in m.entities if e.key == "skeleton_dragons") == 2

# P.E.K.K.A executes a weakened troop
m = match_with("pekka")
k = m.spawn_units(ENEMY, "giant", 1, 9.5, 20.0, deploy=0.0)[0]
k.speed = k.base_speed = 0
for tw in m.towers.values():                   # only the P.E.K.K.A hits it
    tw.range = 0
k.hp = h0 = k.max_hp * 0.74                   # under 75%: one hit is enough
assert h0 > 2 * m.card(PLAYER, "pekka").damage * 1.3
play(m, "pekka")
for _ in range(30 * 8):
    m.update(1 / 30)
    if k.hp < h0 or not k.alive:
        break
assert not k.alive, "first P.E.K.K.A hit should execute under 75%"
# Wizard leaves burning ground; Princess too
for card in ("wizard", "princess"):
    m = match_with(card)
    k = m.spawn_units(ENEMY, "giant", 1, 9.5, 19.0, deploy=0.0)[0]
    k.speed = k.base_speed = 0
    play(m, card)
    fire = False
    for _ in range(30 * 6):
        m.update(1 / 30)
        fire = fire or any(fx.kind == "poison" and fx.team == PLAYER for fx in m.effects)
    assert fire, card

# Bomber's bomblets hit troops around the target
m = match_with("bomber")
ks = m.spawn_units(ENEMY, "knight", 5, 9.5, 19.0, deploy=0.0)
for k in ks:
    k.speed = k.base_speed = 0
play(m, "bomber")
n_fx = 0
for _ in range(30 * 5):
    m.update(1 / 30)
    n_fx = max(n_fx, sum(1 for fx in m.effects if fx.kind == "aoe" and fx.team == PLAYER))
assert n_fx >= 3, n_fx

# Balloon carpet-bombs troops it flies over
m = match_with("balloon")
k = m.spawn_units(ENEMY, "giant", 1, 9.5, 21.0, deploy=0.0)[0]
k.speed = k.base_speed = 0
k.attacks = "buildings"
m.elixir[PLAYER] = 10
m.hands[PLAYER][0] = "balloon"
assert m.play_card(PLAYER, 0, 9.5, 23.5)
for _ in range(30 * 4):
    m.update(1 / 30)
assert k.hp < k.max_hp
print("batch-A behaviours ok")
