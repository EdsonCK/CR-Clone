"""Unique modifiers, part C (chaos_mods_c.py): each one applies and plays
without errors for either side, and a good number do what they say."""
import random

import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import cards
import endless_upgrades as eu          # first: it loads chaos_mods, which registers us
import chaos_mods_c
from engine import Match, PLAYER, ENEMY

UPS = {u.card: u for u in chaos_mods_c.UNIQUE}
assert len(UPS) == 36
for u in chaos_mods_c.UNIQUE:                       # registered in the pool
    assert u in eu.CARD_UPS[u.card] and u.once


def match_with(card):
    champ = cards.CARDS[card].is_champion
    fill = [k for k in cards.DEFAULT_PLAYER_DECK
            if k != card and not (champ and cards.CARDS[k].is_champion)]
    random.seed(1)
    m = Match([card] + fill[:7], list(cards.DEFAULT_AI_DECK))
    return m


def foes(m, team=ENEMY):
    y = 13.5 if team == ENEMY else 18.5
    for i in range(3):
        m.spawn_units(team, "knight", 1, 6.5 + 2.5 * i, y, deploy=0.0)
    m.spawn_units(team, "minions", 3, 9.5, y - 1.0 if team == ENEMY else y + 1.0,
                  deploy=0.0)


def spot(card, team=PLAYER):
    c = cards.CARDS[card]
    if c.category == "spell" and not c.own_side:
        return (9.5, 13.5) if team == PLAYER else (9.5, 18.5)
    return (9.5, 22.5) if team == PLAYER else (9.5, 9.5)


def play(m, card, team=PLAYER):
    m.elixir[team] = 10
    m.hands[team][0] = card
    x, y = spot(card, team)
    return m.play_card(team, 0, x, y)


def sim(m, secs):
    for _ in range(int(secs * 30)):
        m.update(1 / 30)
        if m.finished:
            break


def keys(m, team=PLAYER):
    return [e.key for e in m.entities if e.alive and e.team == team and not e.is_tower]


# ---- every modifier plays for the player, and a handful for the enemy
for card, u in UPS.items():
    m = match_with(card)
    u.apply(m, PLAYER)
    foes(m)
    assert play(m, card), card
    sim(m, 12)
for card in ("tornado", "skeleton_king", "royal_ghost", "clone", "mirror", "ronin"):
    random.seed(2)
    m = Match(list(cards.DEFAULT_PLAYER_DECK), [card] + [
        k for k in cards.DEFAULT_AI_DECK if k != card and not (
            cards.CARDS[card].is_champion and cards.CARDS[k].is_champion)][:7])
    UPS[card].apply(m, ENEMY)
    foes(m, PLAYER)
    m.spawn_units(ENEMY, "knight", 1, 9.5, 12.5, deploy=0.0)
    assert play(m, card, ENEMY), card
    sim(m, 10)
print("all %d modifiers played" % len(UPS))

# ---- behaviour
m = match_with("skeleton_king"); UPS["skeleton_king"].apply(m, PLAYER)
play(m, "skeleton_king")
raised = []
for _ in range(30 * 8):
    m.update(1 / 30)
    raised += [e for e in m.entities if getattr(e, "_sk_raised", False)
               and not any(e is r for r in raised)]
assert len(raised) >= 4, len(raised)

m = match_with("minion_giant"); UPS["minion_giant"].apply(m, PLAYER)
play(m, "minion_giant"); sim(m, 7.5)
assert sum(1 for e in m.entities if getattr(e, "_hive_of", None) is not None) >= 2

m = match_with("spirit_empress"); UPS["spirit_empress"].apply(m, PLAYER)
m.elixir[PLAYER] = 3; m.hands[PLAYER][0] = "spirit_empress"
assert m.play_card(PLAYER, 0, 9.5, 22.5)
k = keys(m)
assert all(s in k for s in ("fire_spirit", "ice_spirit", "electro_spirit", "heal_spirit")), k

m = match_with("boss_bandit"); UPS["boss_bandit"].apply(m, PLAYER)
play(m, "boss_bandit")
assert keys(m).count("bandit") == 2

m = match_with("little_prince"); UPS["little_prince"].apply(m, PLAYER)
play(m, "little_prince")
assert "knight" in keys(m) and "princess" in keys(m)

m = match_with("mirror"); UPS["mirror"].apply(m, PLAYER)
assert m.card_cost(PLAYER, "mirror") == 1 and m.card(PLAYER, "mirror").spell_kind == "clone"
m.spawn_units(PLAYER, "knight", 1, 9.5, 20.5, deploy=0.0)
m.elixir[PLAYER] = 10; m.hands[PLAYER][0] = "mirror"
assert m.play_card(PLAYER, 0, 9.5, 20.5)
sim(m, 2)
assert sum(1 for e in m.entities if e.team == PLAYER and e.clone) >= 1

m = match_with("archer_queen"); UPS["archer_queen"].apply(m, PLAYER)
assert m.card(PLAYER, "archer_queen").multi_target == 3

m = match_with("graveyard"); UPS["graveyard"].apply(m, PLAYER)
play(m, "graveyard"); sim(m, cards.CARDS["graveyard"].duration + 2)
assert "giant_skeleton" in keys(m)

m = match_with("tornado"); UPS["tornado"].apply(m, PLAYER)
play(m, "tornado"); sim(m, 2.0)
tor = [fx for fx in m.effects if fx.kind == "tornado"]
assert tor and tor[0].y < 13.5 - 1.0 and tor[0].duration == cards.CARDS["tornado"].duration * 4

m = match_with("goblin_curse"); UPS["goblin_curse"].apply(m, PLAYER)
play(m, "goblin_curse"); sim(m, 4)
curse = [fx for fx in m.effects if getattr(fx, "fx_tick_hook", None) == "c_goblin_curse_spawn"]
assert curse and curse[0]._gobs >= 3            # (the enemy tower shoots them)

m = match_with("goblin_machine"); UPS["goblin_machine"].apply(m, PLAYER)
play(m, "goblin_machine"); sim(m, 1.5)
gm = next(e for e in m.entities if e.key == "goblin_machine")
gm.take_damage(gm.max_hp * 5); sim(m, 0.2)
assert keys(m).count("goblin") >= 2

m = match_with("royal_delivery"); UPS["royal_delivery"].apply(m, PLAYER)
m.elixir[PLAYER] = 10; m.hands[PLAYER][0] = "royal_delivery"
assert m.play_card(PLAYER, 0, 9.5, 22.5)
sim(m, 4.5)                                    # (the crate takes ~3.3 s to land)
assert len([k for k in keys(m) if k != "royal_recruits"]) >= 1, keys(m)

m = match_with("goblin_cage"); UPS["goblin_cage"].apply(m, PLAYER)
play(m, "goblin_cage")
kn = m.spawn_units(ENEMY, "knight", 1, 9.5, 20.5, deploy=0.0)[0]
sim(m, 2)
assert kn.root_timer > 0 or not kn.alive
print("behaviour ok")

# ---- kills (towers silenced so the card gets the kill itself)
def kill_run(card, foe, upgraded):
    m = match_with(card)
    if upgraded:
        UPS[card].apply(m, PLAYER)
    for t in m.towers.values():
        t.range = t.sight = 0
    play(m, card); sim(m, 1.2)
    m.spawn_units(ENEMY, foe, 2, 9.5, 20.5, deploy=0.0)
    m.elixir[PLAYER] = 0
    sim(m, 6)
    return m


m = kill_run("royal_ghost", "archers", True)
assert sum(1 for e in m.entities if e.team == PLAYER and e.key == "archers") >= 1
gain = kill_run("golden_knight", "skeletons", True).elixir[PLAYER]
base = kill_run("golden_knight", "skeletons", False).elixir[PLAYER]
assert gain >= base + 1.5, (gain, base)            # +1 per kill (2 skeletons)
print("kill modifiers ok")
