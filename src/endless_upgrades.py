"""
============================================================================
  ENDLESS_UPGRADES.PY  --  Endless Survival upgrades ("pick one of two")
============================================================================

After every 4th wave of an Endless run you pick ONE of two upgrades that
last for the rest of the run:

  * a CARD upgrade - something big for one card in your deck (Witch spawns
    3x as fast, Musketeer range x2, Tombstone spawns Guards...), and
  * a BOON - a boost for your towers or your whole side (Princess Towers
    +75% damage, 1.5x elixir, every card +1 level...).

How it works
------------
Card upgrades never touch cards.CARDS: the match keeps a per-team copy of the
card (Match.overrides, see engine.Match.card) and every unit, spell and
spawn of that card uses the copy. An upgrade is a function that returns the
fields to change on the current copy, so picking two upgrades for one card
stacks. Special behaviours live in the copy's `mods` dict and are read by
small hooks in engine.py:

    freeze=s       hits freeze for s seconds        knockback=t  hits push t tiles
    lifesteal=f    heals f x the damage it deals    spawn_extra=((key, n), ...)
    repeat=(n, s)  comes back n more times, s apart (same spot)
    always_evo     always comes out evolved         vines_loop   Vines never end
    heal_all       Battle Healer heals the whole arena

Boons change the match directly (towers, elixir rate, Match.boons...).

Adding an upgrade: add a line to CARD_UPS (card key -> list of upgrades) or
BOONS. Every card that can be played in Endless must have at least one card
upgrade - tests/test_endless_upgrades.py checks.
============================================================================
"""

import dataclasses
import random as _random
from typing import Callable, Optional

import cards
from engine import PLAYER

LEVEL_EVERY = 4            # an upgrade is offered after every 4th wave
VETERAN_WEIGHT = 0.35      # how often "Veteran" (+3 levels) comes up vs the rest


@dataclasses.dataclass
class Upgrade:
    key: str                    # unique id ("witch:spawn3" / "boon:elixir")
    kind: str                   # "card" | "boon"
    title: str                  # short name shown big on the pick card
    desc: str                   # one or two lines of what it does
    icon: Optional[str]         # card key whose picture is shown (None = boon art)
    apply: Callable             # apply(match, team) -> None
    tier: str = "epic"          # "rare" | "epic" | "legendary" (frame colour)
    card: Optional[str] = None  # the card it upgrades (card upgrades)
    once: bool = False          # can only be picked once per run


# ---------------------------------------------------------------- helpers
def override(match, team, key, **changes):
    """Replace fields on `team`'s copy of card `key` (making the copy)."""
    base = match.card(team, key)
    mods = changes.pop("mods", None)
    if mods:
        m = dict(base.mods or {})
        m.update(mods)
        changes["mods"] = m
    match.overrides.setdefault(team, {})[key] = dataclasses.replace(base, **changes)


def card_up(key, title, desc, fn, tier="epic", subs=(), once=False):
    """A card upgrade: fn(card) returns the fields to change on `key`'s copy.
    `subs`: other keys (the units it spawns) changed with fn too."""
    def apply(match, team):
        for k in (key,) + tuple(subs):
            override(match, team, k, **fn(match.card(team, k)))
    return Upgrade("%s:%s" % (key, title), "card", title, desc, key, apply, tier,
                   card=key, once=once)


CARD_UPS = {}               # card key -> [Upgrade, ...]   (filled below)
BOONS = []                  # [Upgrade, ...]               (filled below)


def eligible(deck):
    """Cards in `deck` that have upgrades."""
    return [k for k in deck if CARD_UPS.get(k)]


def offer(match, deck, rng=None, taken=()):
    """The two choices: one card upgrade for a card in `deck`, one boon.
    `taken`: keys of upgrades already picked (once-only ones won't repeat)."""
    rng = rng or _random
    taken = set(taken)
    pool = [u for k in eligible(deck) for u in CARD_UPS[k]
            if not (u.once and u.key in taken)]
    boons = [u for u in BOONS if not (u.once and u.key in taken)
             and (u.key not in _NEEDS or _NEEDS[u.key](match, deck))]
    out = []
    if pool:
        # the plain "Veteran" level-up turns up a third as often as the rest
        weights = [VETERAN_WEIGHT if u.key.endswith(":veteran") else 1.0 for u in pool]
        out.append(rng.choices(pool, weights)[0])
    if boons:
        out.append(rng.choice(boons))
    return out


_NEEDS = {}                  # boon key -> available(match, deck): game state only
                             #   (e.g. a fallen tower), never what is in your deck


# ===========================================================================
#  CARD UPGRADES  --  at least one for every card you can play in Endless
# ===========================================================================
def _x(**kw):
    """fn for card_up: multiply number fields (hp=2 -> double hp)."""
    return lambda c: {f: type(getattr(c, f))(getattr(c, f) * v) for f, v in kw.items()}


def _set(**kw):
    """fn for card_up: set fields outright."""
    return lambda c: dict(kw)


def _both(*fns):
    def f(c):
        out = {}
        for fn in fns:
            out.update(fn(dataclasses.replace(c, **out) if out else c))
        return out
    return f


def _mods(**kw):
    return lambda c: {"mods": dict(kw)}


def _faster(mult):
    """Attacks `mult` times as often."""
    return lambda c: {"hit_speed": c.hit_speed / mult}


def _spawner(interval_div=1.0, count=None, key=None):
    def f(c):
        k, n, t = c.spawner
        return {"spawner": (key or k, count if count is not None else n, t / interval_div)}
    return f


def _death(rmult, dmult):
    return lambda c: {"death_damage": (c.death_damage[0] * rmult,
                                       int(c.death_damage[1] * dmult))}


U = card_up
_L = "legendary"
_R = "rare"
_E = "epic"

def _add(**kw):
    """fn for card_up: add to number fields (count=3 -> 3 more units)."""
    return lambda c: {f: type(getattr(c, f))(getattr(c, f) + v) for f, v in kw.items()}


def _madd(**kw):
    """fn for card_up: add to numbers in the copy's `mods` (stacks)."""
    return lambda c: {"mods": {k: (c.mods or {}).get(k, 0) + v for k, v in kw.items()}}


def _repeat(n, gap):
    """Comes back `n` more times (stacks: each pick adds n more)."""
    return lambda c: {"mods": {"repeat": ((c.mods or {}).get("repeat", (0, gap))[0] + n,
                                          gap)}}


def _range(plus=0.0, mult=1.0):
    """More range - and the sight to go with it (troops stop further away)."""
    def f(c):
        r = c.range * mult + plus
        return {"range": r, "sight": r + max(0.0, c.sight - c.range)}
    return f


def _chain(more, reach):
    return lambda c: {"chain": (c.chain[0] + more, max(c.chain[1], reach))}


_UPS = [
    # Each pick of a stackable upgrade (the default) applies it again, so
    # numbers add up; once=True ones are offered only until you take them.
    # ---- small troops ----
    U("skeletons", "Bone Legion", "Skeletons always come out Evolved.",
      _mods(always_evo=True), _L, once=True),
    U("skeletons", "Skeleton Squad", "+5 Skeletons.", _add(count=5)),
    U("ice_spirit", "Blizzard Spirits", "+2 Ice Spirits, freezing 1.5 s longer.",
      _add(count=2, freeze=1.5)),
    U("fire_spirit", "Inferno Spirits", "+2 Fire Spirits, +50% blast damage.",
      _both(_add(count=2), lambda c: {"death_damage": (c.death_damage[0] * 1.15,
                                                       int(c.death_damage[1] * 1.5))}
            if c.death_damage else {"damage": int(c.damage * 1.5)})),
    U("electro_spirit", "Thunder Spirit", "+1 Electro Spirit; zaps chain to 8 more "
      "targets over a longer reach.", _both(_add(count=1), _chain(8, 3.5))),
    U("heal_spirit", "Spring of Life", "Heals 3x as much over a 60% wider area.",
      lambda c: {"heal_burst": (c.heal_burst[0] * 1.6, c.heal_burst[1] * 3,
                                c.heal_burst[2], c.heal_burst[3])}),
    U("goblins", "Goblin Mob", "+3 Goblins.", _add(count=3), _R),
    U("spear_goblins", "Spear Volley", "+3 Spear Goblins, throwing twice as fast.",
      _both(_add(count=3), _faster(2.0))),
    U("bats", "Bat Cloud", "+7 Bats.", _add(count=7), _R),
    U("skeleton_army", "Army of the Dead", "Skeleton Army rises 2 more times at "
      "the same spot, 10 s apart.", _repeat(2, 10.0), _L),
    U("guards", "Royal Guard", "+3 Guards, shields doubled.",
      _both(_add(count=3), _x(shield_hp=2))),
    U("goblin_gang", "Goblin Army", "The Gang comes back 2 more times, 6 s apart.",
      _repeat(2, 6.0)),
    U("rascals", "Rascal Crew", "+1 Rascal Boy and +2 Rascal Girls.",
      lambda c: {"mixed": tuple((k, n + (1 if k == "rascal_boy" else 2))
                                for k, n in c.mixed)}),
    U("berserker", "Frenzy", "Swings twice as fast and heals 40% of the damage "
      "she deals.", _both(_faster(2.0), _madd(lifesteal=0.4))),
    U("minions", "Minion Squadron", "+3 Minions.", _add(count=3), _R),
    U("minion_horde", "Endless Horde", "+3 Minions, and the Horde comes back once "
      "more 6 s later.", _both(_add(count=3), _repeat(1, 6.0)), _L),
    # ---- ranged ----
    U("archers", "Twin Volley", "Archers shoot twice as fast with +2 range.",
      _both(_faster(2.0), _range(plus=2.0))),
    U("musketeer", "Sharpshooter", "Musketeer range +100% (she stops twice as far "
      "away).", _range(mult=2.0)),
    U("musketeer", "Musket Squad", "+2 Musketeers every time you play her.",
      _add(count=2), _L),
    U("three_musketeers", "Six Musketeers", "+3 Musketeers for the same 9 elixir.",
      _add(count=3), _L),
    U("bomber", "Mega Bomb", "Bombs deal 2.5x damage over a 30% wider blast.",
      _x(damage=2.5, splash=1.3)),
    U("dart_goblin", "Rapid Darts", "Throws 3x as fast.", _faster(3.0)),
    U("princess", "Triple Shot", "Shoots 3x as fast.", _faster(3.0), _L),
    U("wizard", "Fire Mage", "Fireballs knock enemies back and splash 30% wider.",
      _both(_madd(knockback=1.2), _x(splash=1.3))),
    U("ice_wizard", "Absolute Zero", "Freezes what he hits (1 s more per pick) "
      "instead of slowing.", _both(_set(slow=None), _madd(freeze=1.0)), _L),
    U("electro_wizard", "Storm Caller", "Zaps 2 more targets at once, +50% hp.",
      _both(_add(multi_target=2), _x(hp=1.5))),
    U("hunter", "Big Game Hunter", "Double damage and +1.5 range.",
      _both(_x(damage=2), _range(plus=1.5))),
    U("executioner", "Headsman", "Axe 80% stronger with a 30% wider swing.",
      _x(damage=1.8, splash=1.3)),
    U("bowler", "Strike!", "Boulders hit 50% harder and knock back 3x as far.",
      _x(damage=1.5, knockback=3.0)),
    U("magic_archer", "Arcane Arrows", "Arrows deal 2.5x damage.", _x(damage=2.5)),
    U("firecracker", "Grand Finale", "Double damage and twice the sparks.",
      lambda c: {"damage": c.damage * 2,
                 "shrapnel": (c.shrapnel[0] * 2, min(120.0, c.shrapnel[1] * 1.3),
                              c.shrapnel[2])}),
    U("zappies", "Zap Squad", "+3 Zappies.", _add(count=3)),
    U("flying_machine", "Gunship", "Shoots twice as fast with double hp.",
      _both(_faster(2.0), _x(hp=2))),
    U("cannon_cart", "Siege Cart", "Double hp and damage.", _x(hp=2, damage=2)),
    U("goblin_demolisher", "Demolition Expert", "Double damage, 30% wider blasts.",
      _x(damage=2, splash=1.3)),
    U("mother_witch", "Coven Queen", "Shoots twice as fast; cursed troops stay her "
      "Hogs twice as long.", _both(_faster(2.0),
                                    lambda c: {"curse_on_hit": (c.curse_on_hit[0],
                                                                c.curse_on_hit[1] * 2)})),
    U("sparky", "Overcharged", "Sparky charges 60% faster.", _faster(1.6), _L),
    U("baby_dragon", "Fireball Breath", "Every breath deals a Fireball's damage.",
      _set(damage=cards.CARDS["fireball"].spell_damage), _L, once=True),
    U("inferno_dragon", "Twin Infernos", "+1 Inferno Dragon.", _add(count=1)),
    U("electro_dragon", "Storm Dragon", "Lightning chains to 6 more targets over a "
      "longer reach.", _chain(6, 3.0)),
    U("skeleton_dragons", "Bone Wyverns", "+2 Skeleton Dragons.", _add(count=2)),
    U("mega_minion", "Mega Mega Minion", "Double hp and damage, hits splash.",
      _both(_x(hp=2, damage=2), lambda c: {"splash": max(c.splash, 1.0)})),
    U("phoenix", "Eternal Flame", "Double hp and damage.", _x(hp=2, damage=2)),
    U("witch", "Coven Mother", "Summons skeletons twice as fast.", _spawner(2.0), _L,
      once=True),
    U("night_witch", "Night Terror", "+2 Bats per summon, twice as often.",
      lambda c: {"spawner": (c.spawner[0], c.spawner[1] + 2, c.spawner[2] / 2)}),
    # ---- melee ----
    U("knight", "Paladin", "+120% hp; hits knock back and heal him for half the "
      "damage.", _both(_x(hp=2.2), _madd(knockback=0.6, lifesteal=0.5))),
    U("valkyrie", "Whirlwind", "Spins 60% faster with a 40% wider spin.",
      _both(_faster(1.6), _x(splash=1.4))),
    U("mini_pekka", "Pancake Fury", "+50% damage and heals 60% of the damage dealt.",
      _both(_x(damage=1.5), _madd(lifesteal=0.6))),
    U("barbarians", "Horde of the North", "+4 Barbarians.", _add(count=4)),
    U("elite_barbarians", "Endless Rage", "Permanently raged: +35% speed and "
      "attack speed, +30% hp.", _both(_faster(1.35), _x(speed=1.35, hp=1.3))),
    U("pekka", "Executioner's Blade", "Double damage and heals 30% of it.",
      _both(_x(damage=2), _madd(lifesteal=0.3))),
    U("prince", "Royal Lance", "Charge hits twice as hard, +50% hp.",
      _x(charge_mult=2, hp=1.5)),
    U("dark_prince", "Dark Shockwave", "Wider splash (+1 tile) that knocks "
      "enemies back.", _both(_add(splash=1.0), _madd(knockback=0.8))),
    U("giant_skeleton", "Doomsday Bomb", "His bomb is 3x stronger and 40% wider.",
      _death(1.4, 3.0), _L),
    U("lumberjack", "Berserk Axe", "Chops twice as fast.", _faster(2.0)),
    U("bandit", "Gang of Thieves", "+1 Bandit.", _add(count=1)),
    U("mega_knight", "Titan Slam", "His landing deals 4x damage over a wider area.",
      lambda c: {"spawn_damage": (c.spawn_damage[0] + 1.5, c.spawn_damage[1] * 4),
                 "splash": c.splash * 1.3}, _L),
    U("miner", "Iron Miner", "Double hp, triple damage.", _x(hp=2, damage=3)),
    U("battle_healer", "Field Medic", "Every swing heals all your troops on the "
      "whole arena (not buildings), 50% more per pick.",
      lambda c: {"heal_on_attack": (40.0, int(c.heal_on_attack[1] *
                                              (1.5 if c.heal_on_attack[0] >= 40 else 1)))},
      _L),
    U("fisherman", "Master Angler", "Hook recharges 3x as fast, double damage.",
      lambda c: {"hook": (c.hook[0], c.hook[1] + 1.5, c.hook[2] / 3),
                 "damage": c.damage * 2}),
    U("royal_ghost", "Phantom Lord", "Double damage, swing 50% wider.",
      _x(damage=2, splash=1.5)),
    U("royal_recruits", "Royal Legion", "+3 Recruits (up to 12), shields doubled.",
      _both(lambda c: {"count": min(12, c.count + 3), "formation_gap": 1.4},
            _x(shield_hp=2))),
    U("goblin_machine", "Mark II", "Rocket hits 3x harder, +50% hp.",
      lambda c: {"secondary": (c.secondary[0] * 3,) + tuple(c.secondary[1:]),
                 "hp": int(c.hp * 1.5)}),
    U("ronin", "Sword Saint", "Parries twice as often, +50% damage.",
      lambda c: {"parry": (c.parry[0] / 2, c.parry[1]), "damage": int(c.damage * 1.5)}),
    U("spirit_empress", "Empress Ascendant", "Always her flying form, for 3 elixir.",
      lambda c: {"alt_form": (3, c.alt_form[1])}, _L, once=True),
    # ---- champions ----
    U("mighty_miner", "Diamond Drill", "Double damage, +50% hp.", _x(damage=2, hp=1.5)),
    U("archer_queen", "Royal Volley", "Shoots twice as fast.", _faster(2.0)),
    U("little_prince", "Royal Bodyguard", "Double hp and damage.", _x(hp=2, damage=2)),
    U("golden_knight", "Golden Glory", "Double hp and damage.", _x(hp=2, damage=2)),
    U("skeleton_king", "Lich Lord", "+60% hp and a 50% wider slam.",
      _x(hp=1.6, splash=1.5)),
    U("monk", "Grandmaster", "Double damage, heals 50% of it.",
      _both(_x(damage=2), _madd(lifesteal=0.5))),
    U("goblinstein", "Mad Experiment", "Doctor and Monster: double hp and damage.",
      _x(hp=2, damage=2), subs=("goblin_monster",)),
    U("boss_bandit", "Kingpin", "Double damage, +50% hp.", _x(damage=2, hp=1.5)),
    # ---- buildings ----
    U("cannon", "Cannon Battery", "Fires twice as fast and lasts twice as long.",
      _both(_faster(2.0), _x(lifetime=2))),
    U("tesla", "Overclocked", "Double damage, 50% faster, +2 range.",
      _both(_x(damage=2), _faster(1.5), _range(plus=2.0))),
    U("inferno_tower", "Hellfire Core", "Double hp, damage and lifetime.",
      _x(hp=2, damage=2, lifetime=2)),
    U("bomb_tower", "Carpet Bombing", "50% wider blasts, +50% damage.",
      _x(splash=1.5, damage=1.5)),
    U("mortar", "Artillery Barrage", "Fires 3x as fast.", _faster(3.0), _L),
    U("xbow", "Gatling Bow", "Double damage and hp.", _x(damage=2, hp=2)),
    U("tombstone", "Honor Guard", "Spawns Guards instead of Skeletons (+1 per "
      "spawn each extra pick).",
      lambda c: {"spawner": ("guards", c.spawner[1] + (1 if c.spawner[0] == "guards" else 0),
                             c.spawner[2]),
                 "death_spawn": ("guards", c.death_spawn[1])}),
    U("goblin_hut", "Goblin Fortress", "+2 Spear Goblins per spawn.",
      lambda c: {"spawner": (c.spawner[0], c.spawner[1] + 2, c.spawner[2])}),
    U("barbarian_hut", "War Camp", "Spawns Barbarians 2.5x as often.", _spawner(2.5)),
    U("furnace", "Spirit Forge", "Also spawns an Ice, Electro and Heal Spirit with "
      "every Fire Spirit (4x the spirits; more each pick).",
      lambda c: {"mods": {"spawn_extra": tuple((c.mods or {}).get("spawn_extra", ()))
                          + (("ice_spirit", 1), ("electro_spirit", 1),
                             ("heal_spirit", 1))}}, _L),
    U("elixir_collector", "Elixir Pump", "+1 elixir from every pump (2, then 3...).",
      lambda c: {"generates_elixir": (c.generates_elixir[0] + 1, c.generates_elixir[1])},
      _L),
    U("goblin_cage", "Goblin Zoo", "Double hp; +2 Brawlers break out.",
      lambda c: {"hp": c.hp * 2, "death_spawn": (c.death_spawn[0], c.death_spawn[1] + 2)}),
    U("goblin_drill", "Tunnel Network", "Lasts 2.5x as long, spawns twice as fast.",
      _both(_x(lifetime=2.5), _spawner(2.0))),
    # ---- spells ----
    U("zap", "Chain Zap", "Zaps 2 more times at the same spot.", _repeat(2, 0.8)),
    U("the_log", "Mighty Log", "2.5x damage, 50% wider.", _x(spell_damage=2.5,
                                                            spell_radius=1.5)),
    U("arrows", "Arrow Storm", "2 more volleys at the same spot.", _repeat(2, 0.8)),
    U("fireball", "Meteor", "Double damage, 40% wider.", _x(spell_damage=2,
                                                          spell_radius=1.4)),
    U("rage", "Bloodlust", "Lasts twice as long over a 50% wider area.",
      _x(duration=2, spell_radius=1.5)),
    U("freeze", "Ice Age", "Freezes twice as long, 50% wider.",
      _x(freeze=2, spell_radius=1.5)),
    U("poison", "Plague", "Double damage, 45% wider cloud.",
      _x(spell_damage=2, spell_radius=1.45)),
    U("rocket", "Warhead", "Double-wide blast, +50% damage.",
      _x(spell_damage=1.5, spell_radius=2)),
    U("lightning", "Thunderstorm", "Strikes 2 more times at the same spot.",
      _repeat(2, 1.2), _L),
    U("goblin_barrel", "Barrel Bombardment", "+5 Goblins in the barrel.",
      lambda c: {"spawn_troops": (c.spawn_troops[0], c.spawn_troops[1] + 5)}),
    U("barbarian_barrel", "Barrel of Brutes", "+3 Barbarians in the barrel, double "
      "roll damage.", lambda c: {"spawn_troops": (c.spawn_troops[0], c.spawn_troops[1] + 3),
                                 "spell_damage": c.spell_damage * 2}),
    U("snowball", "Avalanche", "60% wider and freezes for 1.5 s (more per pick).",
      _both(_x(spell_radius=1.6), _add(freeze=1.5))),
    U("earthquake", "Tectonic Shift", "Triple damage, 40% wider.",
      _x(spell_damage=3, spell_radius=1.4)),
    U("tornado", "Hurricane", "Triple duration and damage, 30% wider pull.",
      _x(duration=3, spell_damage=3, spell_radius=1.3)),
    U("graveyard", "Necropolis", "Lasts twice as long over a 30% wider area.",
      _x(duration=2, spell_radius=1.3)),
    U("royal_delivery", "Royal Shipment", "+2 Royal Recruits in the delivery.",
      lambda c: {"spawn_troops": (c.spawn_troops[0], c.spawn_troops[1] + 2)}),
    U("goblin_curse", "Hex Storm", "60% wider and lasts 50% longer.",
      _x(spell_radius=1.6, duration=1.5)),
    U("clone", "Twin Souls", "Clones keep half of the original's hp (not 1).",
      _mods(clone_hp=0.5), _L, once=True),
    U("vines", "Overgrowth", "Vines are permanent: they grow straight back where "
      "you cast them (your 3 newest patches stay).", _mods(vines_loop=True), _L,
      once=True),
    U("void", "Black Hole", "60% wider, with twice the strikes.",
      _both(_x(spell_radius=1.6), lambda c: {"hits": c.hits * 2,
                                             "duration": c.duration * 1.5})),
    U("mirror", "Flawless Mirror", "Mirrored cards cost the same as the original "
      "(not +1).", _mods(mirror_free=True), once=True),
    # ---- win conditions (Chaos battles only - Endless bans them) ----
    U("giant", "Colossus", "Double hp, +50% damage.", _x(hp=2, damage=1.5)),
    U("golem", "Titan Golem", "+50% hp and 2 more Golemites when it falls.",
      lambda c: {"hp": int(c.hp * 1.5), "death_spawn": (c.death_spawn[0],
                                                        c.death_spawn[1] + 2)}),
    U("hog_rider", "Hog Stampede", "+1 Hog Rider.", _add(count=1), _L),
    U("hog_rider", "Rampage", "Hits 50% faster.", _faster(1.5), _R),
    U("balloon", "Bomb Bay", "+50% damage; its death bomb is 2.5x stronger.",
      _both(_x(damage=1.5), _death(1.2, 2.5))),
    U("royal_giant", "Royal Cannon", "+2 range, +50% damage.",
      _both(_x(damage=1.5), _range(plus=2.0))),
    U("lava_hound", "Magma Core", "+4 Lava Pups when it pops, +30% hp.",
      lambda c: {"hp": int(c.hp * 1.3), "death_spawn": (c.death_spawn[0],
                                                        c.death_spawn[1] + 4)}),
    U("battle_ram", "Battering Rams", "+50% hp, 2 more Barbarians inside.",
      lambda c: {"hp": int(c.hp * 1.5), "death_spawn": (c.death_spawn[0],
                                                        c.death_spawn[1] + 2)}, _R),
    U("wall_breakers", "Demolition Squad", "+2 Wall Breakers, +50% blast damage.",
      _both(_add(count=2), _death(1.0, 1.5)), _R),
    U("skeleton_barrel", "Bone Bomb", "+6 Skeletons in the barrel.",
      lambda c: {"death_spawn": (c.death_spawn[0], c.death_spawn[1] + 6)}, _R),
    U("goblin_giant", "Goblin Siege Tower", "+2 Spear Goblins on his back (and when "
      "he falls), +30% hp.",
      lambda c: {"hp": int(c.hp * 1.3),
                 "back_riders": (c.back_riders[0], c.back_riders[1] + 2),
                 "death_spawn": (c.death_spawn[0], c.death_spawn[1] + 2)}),
    U("electro_giant", "Tesla Armor", "His counter-zap hits twice as hard over a "
      "wider area.", lambda c: {"reflect": (c.reflect[0] + 1.0, c.reflect[1] * 2,
                                            c.reflect[2])}),
    U("elixir_golem", "Golden Golem", "Double hp, and it no longer gives the "
      "opponent elixir.", _both(_x(hp=2), _set(death_gives_elixir=0.0)), _R, once=True),
    U("ice_golem", "Glacier", "+50% hp; its death freezes-slow is far stronger.",
      lambda c: {"hp": int(c.hp * 1.5), "death_slow": (0.3, 4.0)}, _R),
    U("royal_hogs", "Royal Drove", "+2 Royal Hogs.", _add(count=2)),
    U("ram_rider", "Bola Master", "+50% hp and damage.", _x(hp=1.5, damage=1.5), _R),
    U("rune_giant", "Runemaster", "Enchants 2 more allies with double the bonus.",
      lambda c: {"enchant": (c.enchant[0] + 2, c.enchant[1], c.enchant[2] * 2,
                             c.enchant[3], c.enchant[4])}),
    U("minion_giant", "Toxic Titan", "Double hp, +50% damage.", _x(hp=2, damage=1.5),
      _R),
    U("suspicious_bush", "Goblin Grove", "+3 Goblins burst out of the bush.",
      lambda c: {"death_spawn": (c.death_spawn[0], c.death_spawn[1] + 3)}, _R),
]

for _u in _UPS:
    CARD_UPS.setdefault(_u.card, []).append(_u)


def _veteran(key):
    def apply(match, team):
        lv = match.card_levels.get(team, cards.LEVEL_BASE)
        if not isinstance(lv, dict):
            lv = {k: lv for k in cards.CARDS}
        lv = dict(lv)
        lv[key] = match.card_level(team, key) + 3
        match.card_levels[team] = lv
    return Upgrade("%s:veteran" % key, "card", "Veteran %s" % cards.CARDS[key].name,
                   "%s is 3 levels higher." % cards.CARDS[key].name, key, apply,
                   _R, card=key)


# every eligible card can also simply level up
for _k in list(CARD_UPS):
    CARD_UPS[_k].append(_veteran(_k))


# ===========================================================================
#  BOONS  --  towers and your whole side
# ===========================================================================
def _towers(match, team, kings=True):
    return [tw for (t, side), tw in match.towers.items()
            if t == team and (kings or not tw.is_king)]


def _boon(key, title, desc, apply, tier=_E, once=False, needs=None):
    u = Upgrade("boon:" + key, "boon", title, desc, None, apply, tier, once=once)
    BOONS.append(u)
    if needs:
        _NEEDS[u.key] = needs
    return u


def _tower_dmg(mult, kings=False):
    def apply(match, team):
        for tw in _towers(match, team, kings):
            tw.dmg *= mult
    return apply


def _tower_speed(mult):
    def apply(match, team):
        for tw in _towers(match, team):
            tw.hit_speed /= mult
            tw.cd_mult = getattr(tw, "cd_mult", 1.0) / mult   # Dagger Duchess
    return apply


def _tower_range(plus):
    def apply(match, team):
        for tw in _towers(match, team):
            tw.range += plus
            tw.sight = tw.range
    return apply


def _tower_hp(mult):
    def apply(match, team):
        for tw in _towers(match, team):
            add = tw.max_hp * (mult - 1)
            tw.max_hp = int(tw.max_hp * mult)
            if tw.alive:
                tw.hp += add
            if tw.twin is not None:
                tw.twin.max_hp = tw.max_hp
    return apply


def _heal_towers(frac):
    def apply(match, team):
        for tw in _towers(match, team):
            if tw.alive:
                tw.hp = min(tw.max_hp, tw.hp + tw.max_hp * frac)
    return apply


def _rebuild(match, team):
    for tw in _towers(match, team, kings=False):
        if not tw.alive:
            tw.alive = True
            tw._death_done = False
            if match.enemy_towers:              # a battle: its crown is taken back
                match.crowns[1 - team] = max(0, match.crowns[1 - team] - 1)
            tw.hp = tw.max_hp
            tw.target = None
            if tw not in match.entities:
                match.entities.append(tw)


def _tower_card(**changes):
    def apply(match, team):
        for tw in _towers(match, team):
            tw.card = dataclasses.replace(tw.card, **changes)
    return apply


def _tower_slow(match, team):
    for tw in _towers(match, team):
        f, t = tw.card.slow or (1.0, 0.0)
        tw.card = dataclasses.replace(tw.card, slow=(round(f * 0.65, 3), t + 1.5))


def _tower_splash(match, team):
    for tw in _towers(match, team):
        tw.card = dataclasses.replace(tw.card, splash=(tw.card.splash + 1.0
                                                       if tw.card.splash else 1.5))


def _elixir(mult):
    def apply(match, team):
        b = match.boons.setdefault(team, {})
        b["elixir"] = b.get("elixir", 1.0) * mult
    return apply


def _boon_mult(**kw):
    def apply(match, team):
        b = match.boons.setdefault(team, {})
        for k, v in kw.items():
            b[k] = b.get(k, 1.0) * v
    return apply


def _boon_add(**kw):
    def apply(match, team):
        b = match.boons.setdefault(team, {})
        for k, v in kw.items():
            b[k] = b.get(k, 0) + v
    return apply


def _all_levels(n):
    def apply(match, team):
        lv = match.card_levels.get(team, cards.LEVEL_BASE)
        if isinstance(lv, dict):
            match.card_levels[team] = {k: v + n for k, v in lv.items()}
            match.card_levels[team].update(
                {k: cards.LEVEL_BASE + n for k in match.decks[team]
                 if k not in lv})
        else:
            match.card_levels[team] = lv + n
    return apply


def _ascend(match, team):
    """Every card in your deck that has an Evolution evolves (its first copy
    comes out evolved); every card with a Hero becomes one."""
    import evos
    for k in match.decks[team]:
        if k in evos.EVOS:
            match.evo_cards[team].add(k)
            match.evo_charge[team][k] = evos.EVOS[k].cycles
        if k in evos.HEROES:
            match.hero_cards[team].add(k)


def _spell_mastery(match, team):
    for k in match.decks[team]:
        c = match.card(team, k)
        if c.category == "spell":
            override(match, team, k, spell_radius=c.spell_radius * 1.3,
                     spell_damage=int(c.spell_damage * 1.5),
                     tower_damage=(int(c.tower_damage * 1.5)
                                   if c.tower_damage is not None else None))


def _wake_king(match, team):
    for k in match.kings(team):
        k.active = True
        k.dmg *= 2.0


_boon("elixir", "Elixir Flow", "1.5x elixir for the rest of the run.", _elixir(1.5), _L)
_boon("tower_dmg", "Sharpshooter Towers", "Princess Towers deal +75% damage per hit.",
      _tower_dmg(1.75))
_boon("tower_speed", "Rapid Fire", "All your towers shoot 50% faster.",
      _tower_speed(1.5))
_boon("tower_range", "Watchtowers", "All your towers reach 2.5 tiles further.",
      _tower_range(2.5), _R)
_boon("tower_hp", "Stone Walls", "All your towers get +50% max hp (and heal it).",
      _tower_hp(1.5))
_boon("heal", "Restoration", "All your towers fully heal.", _heal_towers(1.0), _R)
_boon("rebuild", "Rebuild", "Fallen Princess Towers are rebuilt at full hp.",
      _rebuild, _L,
      needs=lambda m, d, team=PLAYER: any(not tw.alive
                                          for tw in _towers(m, team, kings=False)))
_boon("frost_towers", "Frost Towers", "Tower shots slow enemies by 35% for 1.5 s "
      "(each pick slows harder and longer).",
      _tower_slow, _R)
_boon("cannon_towers", "Cannon Towers", "Tower shots splash 1.5 tiles (+1 tile "
      "per extra pick).", _tower_splash, _E)
_boon("king", "King's Wrath", "Your King Tower wakes up now and deals double damage.",
      _wake_king, _R)
_boon("levels", "Royal Training", "Every card in your deck +1 level.", _all_levels(1))
_boon("levels2", "Royal Academy", "Every card in your deck +2 levels.", _all_levels(2),
      _L)
_boon("ascend", "Ascension", "Every card in your deck that has an Evolution evolves, "
      "and every one with a Hero becomes one.", _ascend, _L, once=True)
_boon("might", "Battle Hardened", "All your troops and spells: +30% hp and damage.",
      _boon_mult(hp=1.3, dmg=1.3))
_boon("swift", "Swiftness", "All your troops move and attack 20% faster.",
      _boon_mult(speed=1.2, atk=1.2))
_boon("thrift", "Thrift", "Every card costs 1 elixir less (min 1).",
      _boon_add(discount=1), _L, once=True)
_boon("bounty", "Bounty Hunter", "+0.2 elixir for every enemy you kill.",
      _boon_add(bounty=0.2))
_boon("war_chest", "War Chest", "+3 elixir at the start of every wave.",
      _boon_add(wave_elixir=3))
_boon("second_wind", "Second Wind", "Your towers heal 20% at the start of every wave.",
      _boon_add(wave_heal=0.2), _R)
_boon("spells", "Spell Mastery", "Your spells: +30% radius and +50% damage.",
      _spell_mastery, _E)
