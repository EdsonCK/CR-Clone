"""
============================================================================
  CHAOS_MODS.PY  --  unique card modifiers (Chaos + Endless)
============================================================================

Each card gets at least one modifier that changes HOW it plays, not just its
numbers: a Lava Hound that drops pups as it flies, a Barbarian Hut that
spawns Mega Knights. They join the upgrade pool (endless_upgrades.CARD_UPS)
next to the stat upgrades, one-time each, with a rarity by power.

How a modifier works: card_up(...) changes fields on the side's copy of the
card (see endless_upgrades) - data changes (spawner, attacks, damage...) and
`mods` that name hooks (chaos_hooks.py) for anything data can't do. The
hooks for the first set of cards are below; chaos_mods_*.py hold the rest.
============================================================================
"""

import math
import random

import cards
import endless_upgrades as eu
from chaos_hooks import hook

_L, _E, _R = "legendary", "epic", "rare"


def U(key, title, desc, fn, tier=_E, subs=(), once=True):
    """A unique modifier (one-time by default)."""
    u = eu.card_up(key, title, desc, fn, tier, subs=subs, once=once)
    u.unique = True
    return u


def M(**mods):
    """fn: set these `mods` on the card copy."""
    return lambda c: {"mods": dict(mods)}


def with_mods(changes, **mods):
    """fn: data changes plus mods."""
    return lambda c: dict(changes(c) if callable(changes) else changes, mods=dict(mods))


def spawn(match, team, key, n, x, y, power=None, level=None, deploy=0.0):
    """Units for `team` at (x, y), kept inside the arena."""
    import config as cfg
    x = min(max(x, 0.5), cfg.GRID_COLS - 0.5)
    y = min(max(y, 0.5), cfg.GRID_ROWS - 0.5)
    match.emit("portal", key, x, y, team)
    return match.spawn_units(team, key, n, x, y, deploy=deploy, power=power, level=level)


def fwd(team):
    from engine import PLAYER
    return -1.0 if team == PLAYER else 1.0


# ---------------------------------------------------------------- hooks
@hook("tick")
def lava_pups(e, dt, match):
    """Lava Hound: 2 Lava Pups drop out of it every 2 s."""
    e._pup_t = getattr(e, "_pup_t", 2.0) - dt
    if e._pup_t <= 0 and e.deploy_timer <= 0:
        e._pup_t += 2.0
        spawn(match, e.team, "lava_pup", 2, e.x, e.y, power=e.child_power(), level=e.level)


@hook("hit")
def mortar_barbarian(src, target, dmg, x, y, match):
    """Mortar: a Barbarian drops where each shell lands."""
    spawn(match, src.team, "barbarian", 1, x, y, power=src.child_power(), level=src.level)


@hook("deploy")
def gang_giant(match, team, units, x, y):
    """Goblin Gang: a Goblin Giant leads the Gang."""
    if units:
        spawn(match, team, "goblin_giant", 1, x, y + fwd(team) * 1.2,
              power=units[0].power, level=units[0].level, deploy=None)


@hook("spell_after")
def barrel_brawler(match, team, card, x, y, new):
    """Goblin Barrel: a Goblin Brawler rolls out with the Goblins."""
    lp = match.level_power(team, "goblin_barrel")
    spawn(match, team, "goblin_brawler", 1, x, y, power=lp,
          level=match.card_level(team, "goblin_barrel"))


@hook("deploy")
def bush_sealed(match, team, units, x, y):
    """Suspicious Bush: can't be hurt (not even by spells) until it opens."""
    for u in units:
        u.immortal = True


@hook("death")
def bush_machine(e, match):
    """...and a Goblin Machine bursts out with the Bush Goblins."""
    spawn(match, e.team, "goblin_machine", 1, e.x, e.y, power=e.power, level=e.level)


@hook("hit")
def giant_hop(src, target, dmg, x, y, match):
    """Giant: after each punch he leaps back, ready to dash in again."""
    if src.dash is not None or target is None or not src.alive:
        return
    dx, dy = src.x - target.x, src.y - target.y
    d = math.hypot(dx, dy) or 1.0
    import config as cfg
    from engine import river_side
    px = min(max(src.x + dx / d * 4.0, 0.6), cfg.GRID_COLS - 0.6)
    py = min(max(src.y + dy / d * 4.0, 0.6), cfg.GRID_ROWS - 0.6)
    if river_side(py) != river_side(src.y):
        return                                  # never hop into the river
    src.start_dash(None, kind="point", point=(px, py), speed=7.0, quiet=True)
    src.dash["keep_target"] = True
    src.dash_cd = 0.0


_RANDOM_TROOPS = None


def _random_troops():
    global _RANDOM_TROOPS
    if _RANDOM_TROOPS is None:
        _RANDOM_TROOPS = sorted(c.key for c in cards.DEPLOYABLE_CARDS
                                if c.category == "troop" and not c.is_champion
                                and not c.mixed and c.key != "royal_recruits")
    return _RANDOM_TROOPS


@hook("deploy")
def random_regiment(match, team, units, x, y):
    """Royal Recruits: 6 of one completely random troop instead."""
    if not units:
        return
    key = random.choice(_random_troops())
    xs = [u.x for u in units][:6]
    while len(xs) < 6:
        xs.append(x)
    lv = units[0].level
    pw = match._boon_power(team, match.level_power(team, key))
    for u in units:
        u.alive = False
        u._death_done = True                     # gone without a trace
        u.sacrificed = True
    match.entities = [e for e in match.entities if e not in units]
    for ux in xs:
        spawn(match, team, key, 1, ux, y, power=pw, level=lv, deploy=None)
    match.emit("deploy", key, x, y, team)


@hook("spell")
def eternal_rage(match, team, card, x, y):
    """Rage never ends - but a new one replaces your last."""
    from engine import Effect
    for fx in match.effects:
        if fx.kind == "rage" and fx.team == team and getattr(fx, "eternal", False):
            fx.alive = False
    fx = Effect("rage", team, x, y, card.spell_radius, 1e9)
    fx.eternal = True
    match.effects.append(fx)
    if card.spell_damage:
        lp = match.level_power(team, card.key)
        match.area_damage(team, x, y, card.spell_radius, card.spell_damage * lp[1],
                          hit_air=True, tower_damage=card.tower_dmg() * lp[1])
    return True


@hook("spell_after")
def poison_spread(match, team, card, x, y, new):
    for fx in new:
        if fx.kind == "poison":
            fx.fx_tick_hook = "poison_grow"


@hook("fx_tick")
def poison_grow(fx, dt, match):
    """Poison: 15% wider and stronger with every tick."""
    done = getattr(fx, "ticks_done", 0)
    seen = getattr(fx, "_grown", 0)
    if done > seen:
        for _ in range(done - seen):
            fx.radius *= 1.15
            fx.dps *= 1.15
        fx._grown = done


@hook("tick")
def ram_rider_net(e, dt, match):
    """Ram Rider: every 3 s she throws a Hunter's net (roots and drags the
    nearest enemy troop toward her)."""
    e._net_t = getattr(e, "_net_t", 1.0) - dt
    if e._net_t > 0 or e.deploy_timer > 0:
        return
    best, bd = None, 6.0
    for o in match.entities:
        if (o.alive and o.team != e.team and not o.is_tower and not o.is_building
                and not o.untargetable and not o.flying):
            d = math.hypot(o.x - e.x, o.y - e.y)
            if d < bd:
                best, bd = o, d
    if best is None:
        return
    e._net_t = 3.0
    best.root_timer = max(best.root_timer, 1.5)
    if not best.card.no_knockback and bd > 1.5:
        pull = min(2.5, bd - 1.2)
        best.x += (e.x - best.x) / bd * pull
        best.y += (e.y - best.y) / bd * pull
    match.bolt(e.team, e, best, "hunter")
    match.emit("attack", "hunter", e.x, e.y, e.team)


@hook("hit")
def ram_rider_charge(src, target, dmg, x, y, match):
    """...and like an Evolved Battle Ram she's charged again after each hit,
    knocking her target back."""
    src.charged = True
    if target is not None and not (target.is_tower or target.is_building) \
            and not target.card.no_knockback:
        d = math.hypot(target.x - src.x, target.y - src.y) or 1.0
        target.x += (target.x - src.x) / d * 1.5
        target.y += (target.y - src.y) / d * 1.5


# ---------------------------------------------------------------- the list
UNIQUE = [
    U("lava_hound", "Pup Bomber", "Drops 2 Lava Pups every 2 s while it flies.",
      M(tick="lava_pups"), _L),
    U("barbarian_hut", "Mega Barracks", "Spawns a Mega Knight (who lands with his "
      "slam) instead of Barbarians.",
      lambda c: {"spawner": ("mega_knight", 1, c.spawner[2])}, _L),
    U("xbow", "Fireball Bow", "Shoots Wizard fireballs (splash) at air and ground.",
      lambda c: {"attacks": "air_ground", "damage": cards.CARDS["wizard"].damage,
                 "splash": cards.CARDS["wizard"].splash, "hit_speed": 0.6,
                 "mods": {"proj_style": "wizard"}}, _L),
    U("mortar", "Barbarian Barrage", "A Barbarian drops wherever a shell lands.",
      M(hit="mortar_barbarian")),
    U("dart_goblin", "Spark Darts", "Shoots Sparky blasts - 50% slower than his "
      "darts.", lambda c: {"damage": cards.CARDS["sparky"].damage,
                           "splash": cards.CARDS["sparky"].splash,
                           "hit_speed": c.hit_speed * 1.5,
                           "mods": {"proj_style": "sparky"}}, _L),
    U("goblin_gang", "Big Brother", "A Goblin Giant comes with the Gang.",
      M(deploy="gang_giant"), _L),
    U("goblin_barrel", "Brawler Barrel", "A Goblin Brawler rolls out with the "
      "Goblins.", M(spell_after="barrel_brawler")),
    U("suspicious_bush", "Machine in the Bush", "Can't be damaged until it opens - "
      "and a Goblin Machine bursts out.", M(deploy="bush_sealed", death="bush_machine"),
      _L),
    U("giant", "Leaping Giant", "Dashes onto targets 3-6 tiles away, and after each "
      "punch leaps back to dash in again.",
      lambda c: {"dash": (3.0, 6.0), "dash_damage": (1.5, c.damage),
                 "mods": {"hit": "giant_hop"}}, _L),
    U("royal_recruits", "Random Regiment", "6 of one completely random troop (6 "
      "Skeletons... or 6 Sparkies).", M(deploy="random_regiment"), _L),
    U("rage", "Eternal Rage", "Rage never ends - casting it again moves it (your "
      "last one disappears).", M(spell="eternal_rage"), _L),
    U("poison", "Spreading Plague", "Poison grows 15% wider and stronger with every "
      "tick.", M(spell_after="poison_spread")),
    U("ram_rider", "Net Rider", "Throws a Hunter's net every 3 s (roots and drags "
      "the nearest troop) and, like an Evo Battle Ram, is charged again after "
      "every hit, knocking her target back.",
      M(tick="ram_rider_net", hit="ram_rider_charge"), _L),
    U("goblin_giant", "Rocket Riders", "The Spear Goblins on his back throw 3x as "
      "fast with 3x the range.", M(rider_atk=3.0, rider_range=3.0)),
    U("phoenix", "Endless Phoenix", "Every reborn Phoenix lays an egg again - she "
      "keeps coming back until an egg is destroyed.",
      lambda c: {"death_spawn": ("phoenix_egg", 1)}, _L, subs=("phoenix_reborn",)),
]


def _register(ups):
    """Add modifiers to the upgrade pool (safe to call twice)."""
    for u in ups:
        have = eu.CARD_UPS.setdefault(u.card, [])
        if all(x.key != u.key for x in have):
            have.append(u)


_register(UNIQUE)

# the rest of the cards' modifiers live in chaos_mods_a/b/c.py: each one
# registers itself when it loads (endless_upgrades loads them)
PARTS = ("chaos_mods_a", "chaos_mods_b", "chaos_mods_c")
if getattr(eu, "_LOADED", False):          # we were imported first
    import importlib as _il
    for _p in PARTS:
        _il.import_module(_p)
