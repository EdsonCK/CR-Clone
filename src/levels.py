"""
============================================================================
  LEVELS.PY  --  Set-piece challenge levels ("Levels" on the main menu)
============================================================================

In a level the opponent has NO towers. Scripted waves of enemies march at
yours and the only goal is to survive them all with your King Tower
standing. Because there are no towers to hit, win conditions (cards that
only attack buildings) can't be used - Levels have their own deck. With
nothing to fight, your troops march to where the enemy towers would be; a
weak permanent poison (the Crypt Miasma) hangs over the enemy half so an army
can't camp their spawn: it kills a Goblin on the 6th one-second tick.
Stars: 3 = no tower lost, 2 = one Princess Tower lost, 1 = both lost (King
Tower falling = defeat). Spells cast by a wave hit as hard as its level.

Unit levels
-----------
Card stats in cards.py count as LEVEL 11 (like a tournament-standard card in
Clash Royale). Every level above that adds +10% hp and damage (compounding),
every level below takes 10% off:

    level 11 = x1.00   level 12 = x1.10   level 13 = x1.21   level 14 = x1.33

A spawn can also carry an extra multiplier (`mult`) on top - bosses use it -
and LEVEL_POWER (near the bottom) scales a whole level for tuning.

Adding a level
--------------
Append a Level(...) to LEVELS. Each Wave lists Spawn entries:

    Spawn(card_key, at=seconds_into_wave, lane="left"|"right"|"mid",
          level=None (wave's level), mult=1.0, place="field"|"back"|"front"|
          "tower")

  place: "field" = out of the lane's crypt gate, "back" = from just inside
         the gate, "front" = near the river (buildings), "river" = right at
         the river bank (siege buildings: X-Bow, Mortar), "tower" = on YOUR
         Princess Tower of that lane (Graveyard, Goblin Barrel, Miner...),
         "army" = spells aimed at the thickest clump of your troops (waits
         until you have some on the field; falls back to your tower),
         "near" = 3 tiles in front of your Princess Tower (Goblin Drill),
         "push" = the enemy's OWN support (Rage, Clone, Heal Spirit...)
         dropped on the thickest clump of its troops once they reach the
         river (waits for them; skipped if the wave is already beaten).

  note="Reinforcements!" shows a call-out when that spawn arrives.

  The short form S(key, at, lane, place, level=, mult=, note=) is used below.
============================================================================
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional

import cards
from engine import PLAYER, ENEMY, RIVER_TOP

LEVEL_BASE = cards.LEVEL_BASE      # the level the stats in cards.py represent
level_mult = cards.level_mult


LANE_X = {"left": 3.5, "right": 14.5, "mid": 9.0}
GATE_Y = {"left": 6.0, "right": 6.0, "mid": 3.0}   # crypt gates (drawn by game.py)
PLACE_Y = {"front": RIVER_TOP - 3.5,                # buildings: near the river
           "river": RIVER_TOP - 1.2}                # siege buildings at the bank
ARMY_WAIT = 12           # "army" spells wait up to this many seconds for targets


@dataclass
class Spawn:
    key: str
    at: float = 0.0
    lane: str = "left"
    level: Optional[int] = None
    mult: float = 1.0
    place: str = "field"
    note: Optional[str] = None      # call-out shown when it arrives


@dataclass
class Wave:
    name: str
    spawns: List[Spawn]
    level: int = LEVEL_BASE
    bonus_elixir: float = 0.0       # given to the player when the wave starts
    boss: bool = False
    timeout: float = 40.0           # next wave comes anyway after this long


@dataclass
class Level:
    key: str
    name: str
    subtitle: str
    desc: str
    icon: str                       # card key used as the level's picture
    waves: List[Wave]
    start_elixir: float = 6.0
    prep_first: float = 8.0         # seconds before wave 1
    prep: float = 7.0               # seconds between waves
    locked: bool = False
    shift: int = 0                  # added to every enemy level (set below)
    power: float = 1.0              # x hp & damage for every enemy (tuning)


def S(key, at=0.0, lane="left", place="field", level=None, mult=1.0, note=None):
    """Short form of Spawn used by the level tables below."""
    return Spawn(key, at, lane, level, mult, place, note)


def R(key, at, lane="left", place="field", level=None, mult=1.0):
    """A reinforcement: a spawn that arrives with a 'Reinforcements!' call-out."""
    return Spawn(key, at, lane, level, mult, place, "Reinforcements!")


# ===========================================================================
#  THE LEVELS
# ===========================================================================
LEVELS = [
    Level(
        "bone_crypt", "The Bone Crypt", "Level 1",
        "The dead are restless. Hold the line against every kind of "
        "skeleton the crypt can raise - and whatever wakes at the bottom.",
        "giant_skeleton",
        waves=[
            Wave("Rattling Bones", level=11, spawns=[
                S("skeletons", 0, "left"), S("skeletons", 0, "right"),
                S("skeletons", 6, "left"), S("skeletons", 10, "right"),
            ]),
            Wave("Shield Wall", level=11, spawns=[
                S("guards", 0, "left"), S("bomber", 2, "left", "back"),
                R("skeletons", 8, "right"),
            ]),
            Wave("The Horde", level=11, spawns=[
                S("skeleton_army", 0, "right"), S("bomber", 3, "right", "back"),
                S("skeletons", 6, "left"),
            ]),
            Wave("Breach!", level=11, spawns=[
                S("wall_breakers", 0, "left"), S("wall_breakers", 0, "right"),
                S("skeleton_barrel", 6, "right", "back"),
            ]),
            Wave("Grave Robbers", level=11, spawns=[
                S("tombstone", 0, "mid", "front"), S("guards", 3, "left"),
                S("graveyard", 7, "right", "tower"),
            ]),
            Wave("The Bone King", level=12, spawns=[
                S("skeleton_king", 0, "left"), S("bomber", 3, "left", "back"),
                R("skeleton_army", 9, "right"),
            ]),
            Wave("Twin Titans", level=11, boss=True, bonus_elixir=6, timeout=90, spawns=[
                S("giant_skeleton", 0, "left", mult=2.0),
                S("bomber", 3, "left", "back"),
                S("giant_skeleton", 14, "right", mult=2.0),
                R("guards", 18, "right"),
            ]),
        ]),
    Level(
        "goblin_ambush", "Goblin Ambush", "Level 2",
        "The goblin clans have dug in. Darts from the trees, barrels from "
        "the sky, huts, giants and a mad doctor - then the Warlords arrive.",
        "goblin_giant",
        waves=[
            Wave("Scouts", level=11, spawns=[
                S("goblins", 0, "left"), S("goblins", 1, "right"),
                S("spear_goblins", 5, "mid"),
            ]),
            Wave("Dart Volley", level=11, spawns=[
                S("goblins", 0, "left"), S("dart_goblin", 1, "left", "back"),
                S("spear_goblins", 4, "right"), S("dart_goblin", 5, "right", "back"),
            ]),
            Wave("Barrels Incoming", level=11, spawns=[
                S("spear_goblins", 0, "mid"),
                S("goblin_barrel", 4, "left", "tower"),
                S("goblin_barrel", 8, "right", "tower"),
            ]),
            Wave("Hut Raid", level=12, spawns=[
                S("goblin_hut", 0, "mid", "front"), S("goblins", 4, "left"),
                R("spear_goblins", 10, "right"),
            ]),
            Wave("Big Green", level=11, spawns=[
                S("goblin_giant", 0, "left"), S("spear_goblins", 2, "left", "back"),
                S("rage", 6, "left", "push"),
            ]),
            Wave("Mad Science", level=12, spawns=[
                S("goblinstein", 0, "right"), S("goblins", 3, "left"),
                S("goblin_barrel", 7, "left", "tower"),
            ]),
            Wave("The Warlords", level=11, boss=True, bonus_elixir=6, timeout=100, spawns=[
                S("goblin_giant", 0, "left", mult=1.4),
                S("spear_goblins", 6, "left", "back"),
                S("goblin_giant", 14, "right", mult=1.4),
                S("spear_goblins", 18, "right", "back"),
                S("rage", 18, "mid", "push"),
            ]),
        ]),
    Level(
        "iron_legion", "The Iron Legion", "Level 3",
        "Armoured P.E.K.K.As march under a sky black with wings. Mini "
        "P.E.K.K.As cut through anything in reach - and two titans close the "
        "gates behind them.",
        "pekka",
        waves=[
            Wave("Black Wings", level=12, spawns=[
                S("bats", 0, "left"), S("bats", 0, "right"), S("minions", 5, "mid"),
            ]),
            Wave("Little Iron", level=12, spawns=[
                S("mini_pekka", 0, "left"), S("minions", 2, "left", "back"),
                S("mini_pekka", 6, "right"),
            ]),
            Wave("The Swarm", level=12, spawns=[
                S("minion_horde", 0, "mid"), S("bats", 5, "left"), S("bats", 5, "right"),
            ]),
            Wave("Night Raid", level=12, spawns=[
                S("night_witch", 0, "left"), S("mega_minion", 2, "left", "back"),
                S("dark_prince", 5, "right"),
            ]),
            Wave("Iron Knight", level=13, spawns=[
                S("pekka", 0, "left"), S("minions", 3, "left", "back"),
                R("minions", 9, "right"),
            ]),
            Wave("Twin Blades", level=12, spawns=[
                S("mini_pekka", 0, "left"), S("mini_pekka", 0, "right"),
                S("minion_horde", 6, "mid"), S("mega_minion", 9, "left"),
            ]),
            Wave("The Iron Titans", level=11, boss=True, bonus_elixir=7, timeout=110, spawns=[
                S("pekka", 0, "left", mult=1.5),
                S("minions", 4, "left", "back", level=13),
                S("pekka", 14, "right", mult=1.5),
                S("bats", 16, "right", "back", level=13),
                R("mega_minion", 22, "left", level=13),
            ]),
        ]),
    # ------------------------------------------------------------------ 4
    Level(
        "frostbite_pass", "Frostbite Pass", "Level 4",
        "A blizzard rolls off the mountain. Ice Spirits, Ice Golems and Ice "
        "Wizards slow everything down - and something enormous is frozen in "
        "the glacier.",
        "ice_golem",
        waves=[
            Wave("First Frost", level=11, spawns=[
                S("ice_spirit", 0, "left"), S("ice_spirit", 0, "right"),
                S("ice_golem", 4, "left"), S("ice_spirit", 5, "left", "back"),
            ]),
            Wave("Snowfall", level=11, spawns=[
                S("ice_golem", 0, "left"), S("ice_wizard", 1, "left", "back"),
                S("ice_spirit", 6, "right"), S("snowball", 8, "left", "army"),
            ]),
            Wave("Cold Snap", level=12, spawns=[
                S("ice_golem", 0, "right"), S("ice_wizard", 2, "right", "back"),
                S("ice_spirit", 4, "left"), S("ice_spirit", 5, "left"),
                S("snowball", 9, "right", "army"),
            ]),
            Wave("Avalanche", level=12, spawns=[
                S("ice_golem", 0, "left"), S("ice_golem", 0, "right"),
                S("ice_spirit", 3, "left", "back"), S("ice_spirit", 3, "right", "back"),
            ]),
            Wave("Whiteout", level=12, spawns=[
                S("ice_golem", 0, "left"), S("ice_wizard", 1, "left", "back"),
                S("ice_spirit", 2, "left", "back"), S("ice_spirit", 2.5, "left", "back"),
                S("freeze", 9, "left", "army"),
            ]),
            Wave("Frozen Legion", level=12, spawns=[
                S("ice_golem", 0, "left"), S("ice_wizard", 1, "left", "back"),
                S("ice_golem", 3, "right"), S("ice_wizard", 4, "right", "back"),
                S("snowball", 10, "mid", "army"),
            ]),
            Wave("The Glacier", level=11, boss=True, bonus_elixir=6, timeout=100, spawns=[
                S("ice_golem", 0, "left", mult=3.5),
                S("ice_wizard", 3, "left", "back", level=13),
                R("ice_spirit", 9, "right", level=13),
                S("ice_golem", 16, "right", mult=3.5),
                S("ice_wizard", 19, "right", "back", level=13),
                S("freeze", 26, "mid", "army", level=13),
            ]),
        ]),
    # ------------------------------------------------------------------ 5
    Level(
        "barbarian_raid", "Barbarian Raid", "Level 5",
        "Horns sound across the valley. Barrels roll, rams charge, a war "
        "camp goes up at the river - and the Warband rides last.",
        "elite_barbarians",
        waves=[
            Wave("War Cry", level=11, spawns=[
                S("barbarians", 0, "left"), S("rage", 5, "left", "push"),
                S("barbarian_barrel", 9, "right", "army"),
            ]),
            Wave("Axes Out", level=12, spawns=[
                S("lumberjack", 0, "right"), S("barbarians", 2, "left"),
            ]),
            Wave("Battering Rams", level=12, spawns=[
                S("battle_ram", 0, "left"), S("battle_ram", 0, "right"),
                S("barbarian_barrel", 7, "mid", "army"),
            ]),
            Wave("The War Camp", level=12, spawns=[
                S("barbarian_hut", 0, "mid", "front"), S("battle_ram", 6, "left"),
                R("battle_ram", 14, "right"),
            ]),
            Wave("Elite Charge", level=12, spawns=[
                S("elite_barbarians", 0, "left"), S("rage", 4, "left", "push"),
                S("barbarians", 4, "right"),
            ]),
            Wave("Shield Maidens", level=12, spawns=[
                S("valkyrie", 0, "left"), S("valkyrie", 0, "right"),
                S("barbarians", 4, "mid", "back"), S("barbarian_barrel", 9, "mid", "army"),
            ]),
            Wave("The Warband", level=11, boss=True, bonus_elixir=6, timeout=100, spawns=[
                S("elite_barbarians", 0, "left", mult=1.5),
                S("battle_ram", 8, "right", mult=1.5),
                S("elite_barbarians", 16, "right", mult=1.5),
                S("rage", 18, "right", "push", level=13),
                S("barbarian_barrel", 22, "mid", "army", level=13),
            ]),
        ]),
    # ------------------------------------------------------------------ 6
    Level(
        "sky_raiders", "Sky Raiders", "Level 6",
        "Nothing on this level walks. Balloons, Flying Machines and dragons "
        "fill the sky - bring cards that can hit the air!",
        "balloon",
        waves=[
            Wave("Wingbeat", level=11, spawns=[
                S("minions", 0, "left"), S("bats", 0, "right"),
            ]),
            Wave("Bombs Away", level=10, spawns=[
                S("balloon", 0, "right"), S("minions", 4, "left"),
            ]),
            Wave("Flying Machines", level=11, spawns=[
                S("flying_machine", 0, "left"), S("flying_machine", 0, "right"),
            ]),
            Wave("Little Dragons", level=11, spawns=[
                S("baby_dragon", 0, "left"), S("baby_dragon", 6, "right"),
            ]),
            Wave("Escort", level=10, spawns=[
                S("balloon", 0, "right"), S("mega_minion", 1, "right", "back"),
                S("bats", 5, "left"),
            ]),
            Wave("Black Sky", level=10, spawns=[
                S("minion_horde", 0, "left"), S("bats", 3, "right"),
                R("minions", 8, "left"),
            ]),
            Wave("The Lava Hound", level=11, boss=True, bonus_elixir=6, timeout=100, spawns=[
                S("lava_hound", 0, "left"),
                S("minions", 4, "left", "back", level=11),
                R("minion_horde", 14, "right", level=11),
                S("mega_minion", 17, "right", level=11),
            ]),
        ]),
    # ------------------------------------------------------------------ 7
    Level(
        "royal_court", "The Royal Court", "Level 7",
        "The court has declared you a traitor. Knights, princesses, princes "
        "on horseback and a Royal Giant come to collect.",
        "prince",
        waves=[
            Wave("Royal Guard", level=12, spawns=[
                S("knight", 0, "left"), S("guards", 0, "right"),
            ]),
            Wave("Arrows from the Keep", level=12, spawns=[
                S("knight", 0, "right"), S("princess", 1, "right", "back"),
                S("archers", 4, "left"), S("arrows", 9, "mid", "army"),
            ]),
            Wave("Charge!", level=13, spawns=[
                S("prince", 0, "left"), S("dark_prince", 0, "right"),
            ]),
            Wave("The Little Prince", level=12, spawns=[
                S("guards", 0, "mid"), S("little_prince", 1, "mid", "back"),
                S("heal_spirit", 6, "mid", "push"),
            ]),
            Wave("Special Delivery", level=11, spawns=[
                S("royal_giant", 0, "right"), S("princess", 2, "right", "back"),
                S("royal_delivery", 8, "right", "army"),
            ]),
            Wave("Golden Hour", level=13, spawns=[
                S("golden_knight", 0, "left"), S("princess", 2, "left", "back"),
                S("knight", 4, "right"),
            ]),
            Wave("The Princes", level=11, boss=True, bonus_elixir=7, timeout=100, spawns=[
                S("prince", 0, "left", mult=1.85),
                S("dark_prince", 1, "right", mult=1.85),
                S("royal_giant", 14, "mid", mult=1.5),
                S("princess", 15, "mid", "back", level=13),
                R("knight", 20, "left", level=13),
            ]),
        ]),
    # ------------------------------------------------------------------ 8
    Level(
        "rogues_den", "Rogues' Den", "Level 8",
        "Thieves don't fight fair. Bandits dash in, Miners pop up under your "
        "towers and the Boss Bandit herself runs the show.",
        "bandit",
        waves=[
            Wave("Pickpockets", level=12, spawns=[
                S("bandit", 0, "left"), S("goblins", 1, "right"),
            ]),
            Wave("Ambush", level=12, spawns=[
                S("bandit", 0, "right"), S("miner", 3, "left", "tower"),
            ]),
            Wave("Dark Alley", level=12, spawns=[
                S("royal_ghost", 0, "right"), S("bandit", 3, "left"),
            ]),
            Wave("Highwaymen", level=12, spawns=[
                S("lumberjack", 0, "left"), S("bandit", 1, "left", "back"),
                S("dart_goblin", 4, "right"),
            ]),
            Wave("Cutthroats", level=11, spawns=[
                S("bandit", 0, "left"), S("bandit", 0, "right"),
                S("dark_prince", 4, "mid"),
            ]),
            Wave("Smoke and Daggers", level=12, spawns=[
                S("bandit", 0, "mid"), S("miner", 3, "right", "tower"),
                S("poison", 8, "mid", "army"),
            ]),
            Wave("The Boss Bandit", level=11, boss=True, bonus_elixir=7, timeout=100, spawns=[
                S("boss_bandit", 0, "left", mult=1.7),
                S("bandit", 6, "right", level=13),
                S("night_witch", 16, "right", mult=1.2),
                S("miner", 20, "left", "tower", level=13),
            ]),
        ]),
    # ------------------------------------------------------------------ 9
    Level(
        "spark_and_storm", "Spark & Storm", "Level 9",
        "The air crackles. Zappies, Electro Wizards and dragons stun "
        "everything they touch, lightning strikes your army, and two Sparkies "
        "charge up at the end.",
        "electro_wizard",
        waves=[
            Wave("Static", level=12, spawns=[
                S("electro_spirit", 0, "left"), S("electro_spirit", 0, "right"),
                S("zappies", 4, "left"),
            ]),
            Wave("Chain Lightning", level=12, spawns=[
                S("electro_wizard", 0, "right"), S("electro_dragon", 4, "left"),
            ]),
            Wave("Overload", level=12, spawns=[
                S("zappies", 0, "right"), S("electro_wizard", 2, "right", "back"),
                S("rage", 6, "right", "push"),
            ]),
            Wave("Thunderhead", level=12, spawns=[
                S("electro_dragon", 0, "mid"), S("zappies", 3, "mid", "back"),
                S("lightning", 8, "mid", "army"),
            ]),
            Wave("Charged Up", level=12, spawns=[
                S("electro_giant", 0, "left"), S("electro_wizard", 2, "left", "back"),
                R("electro_spirit", 8, "right"),
            ]),
            Wave("Storm Front", level=13, spawns=[
                S("zappies", 0, "left"), S("zappies", 0, "right"),
                S("lightning", 8, "mid", "army"),
            ]),
            Wave("Twin Sparky", level=11, boss=True, bonus_elixir=7, timeout=100, spawns=[
                S("electro_giant", 0, "left", mult=1.25),
                S("sparky", 2, "left", "back", mult=1.25),
                S("sparky", 16, "right", mult=1.25),
                S("zappies", 17, "right", "back", level=13),
            ]),
        ]),
    # ------------------------------------------------------------------ 10
    Level(
        "hog_stampede", "Hog Stampede", "Level 10",
        "Hog Riders don't care about your troops - they go straight for your "
        "towers. Buildings and quick hands win this one.",
        "hog_rider",
        waves=[
            Wave("Hog Rider!", level=12, spawns=[
                S("hog_rider", 0, "left"), S("ice_spirit", 0.5, "left", "back"),
            ]),
            Wave("Two Hogs", level=12, spawns=[
                S("hog_rider", 0, "left"), S("hog_rider", 0, "right"),
            ]),
            Wave("Ram Raid", level=12, spawns=[
                S("battle_ram", 0, "left"), S("hog_rider", 3, "right"),
            ]),
            Wave("Hogs and Spirits", level=12, spawns=[
                S("hog_rider", 0, "left"), S("ice_spirit", 0, "left", "back"),
                S("hog_rider", 5, "right"), S("fire_spirit", 5, "right", "back"),
            ]),
            Wave("Wall Smashers", level=12, spawns=[
                S("wall_breakers", 0, "left"), S("wall_breakers", 0, "right"),
                S("hog_rider", 4, "mid"),
            ]),
            Wave("Earthquake", level=13, spawns=[
                S("hog_rider", 0, "left"), S("earthquake", 4, "left", "tower"),
                S("hog_rider", 7, "right"),
            ]),
            Wave("The Stampede", level=12, boss=True, bonus_elixir=7, timeout=100, spawns=[
                S("hog_rider", 0, "left", mult=1.55),
                S("hog_rider", 2, "right", mult=1.55),
                S("battle_ram", 9, "left", mult=1.55),
                S("royal_hogs", 15, "mid", mult=1.2),
                S("hog_rider", 17, "right", mult=1.55),
            ]),
        ]),
    # ------------------------------------------------------------------ 11
    Level(
        "pyromancers", "The Pyromancers", "Level 11",
        "Everything burns. Fire Spirits, Wizards, Furnaces on the march and "
        "fireballs falling on your army - then the Fire Lords arrive.",
        "wizard",
        waves=[
            Wave("Embers", level=13, spawns=[
                S("fire_spirit", 0, "left"), S("fire_spirit", 0, "right"),
                S("fire_spirit", 2, "mid"),
            ]),
            Wave("Fireball!", level=12, spawns=[
                S("knight", 0, "left"), S("wizard", 1, "left", "back"),
                S("fireball", 8, "left", "army"),
            ]),
            Wave("The Furnace", level=12, spawns=[
                S("knight", 0, "right"), S("furnace", 1, "right", "back"),
                S("fire_spirit", 4, "left"),
            ]),
            Wave("Inferno", level=12, spawns=[
                S("inferno_dragon", 0, "right"), S("wizard", 2, "right", "back"),
            ]),
            Wave("Pyre", level=13, spawns=[
                S("baby_dragon", 0, "left"), S("wizard", 2, "right"),
                S("fireball", 8, "mid", "army"),
            ]),
            Wave("Burning Tower", level=12, spawns=[
                S("inferno_tower", 0, "mid", "river"), S("wizard", 2, "left"),
                S("fire_spirit", 4, "right"),
            ]),
            Wave("The Fire Lords", level=11, boss=True, bonus_elixir=7, timeout=100, spawns=[
                S("wizard", 0, "left", mult=2.0),
                S("wizard", 1, "right", mult=2.0),
                S("inferno_dragon", 10, "mid", mult=1.5),
                S("fireball", 15, "mid", "army", level=13),
                R("furnace", 18, "left", level=13),
            ]),
        ]),
    # ------------------------------------------------------------------ 12
    Level(
        "graveyard_shift", "Graveyard Shift", "Level 12",
        "The Bone Crypt was just the beginning. Witches raise the dead, "
        "graveyards open under your towers and the Lich King walks again.",
        "witch",
        waves=[
            Wave("Midnight", level=13, spawns=[
                S("skeletons", 0, "left"), S("skeletons", 0, "right"),
                S("bats", 4, "mid"),
            ]),
            Wave("The Coven", level=12, spawns=[
                S("guards", 0, "left"), S("witch", 1, "left", "back"),
            ]),
            Wave("Grave Diggers", level=13, spawns=[
                S("graveyard", 0, "left", "tower"), S("skeleton_barrel", 5, "right"),
            ]),
            Wave("Night Witches", level=12, spawns=[
                S("night_witch", 0, "left"), S("night_witch", 0, "right"),
            ]),
            Wave("Bone Giant", level=12, spawns=[
                S("giant_skeleton", 0, "left"), S("witch", 2, "left", "back"),
            ]),
            Wave("Tombs", level=13, spawns=[
                S("tombstone", 0, "left", "front"), S("tombstone", 0, "right", "front"),
                S("graveyard", 6, "right", "tower"),
            ]),
            Wave("The Lich King", level=11, boss=True, bonus_elixir=7, timeout=100, spawns=[
                S("skeleton_king", 0, "left", mult=1.5),
                S("witch", 2, "left", "back", level=13),
                S("graveyard", 10, "right", "tower", level=13),
                S("giant_skeleton", 16, "right", mult=1.2),
                R("skeletons", 20, "left", level=13),
            ]),
        ]),
    # ------------------------------------------------------------------ 13
    Level(
        "marksmen", "The Marksmen", "Level 13",
        "Long range all round: archers, musketeers, a Hunter, an X-Bow at "
        "the river and the Archer Queen. Get in close or get picked apart.",
        "musketeer",
        waves=[
            Wave("Bowmen", level=13, spawns=[
                S("archers", 0, "left"), S("archers", 0, "right"),
            ]),
            Wave("Sharpshooters", level=13, spawns=[
                S("musketeer", 0, "right"), S("firecracker", 2, "left"),
            ]),
            Wave("Hunting Party", level=13, spawns=[
                S("knight", 0, "left"), S("hunter", 1, "left", "back"),
                S("magic_archer", 3, "left", "back"),
            ]),
            Wave("Royal Archers", level=13, spawns=[
                S("musketeer", 0, "left"), S("musketeer", 0, "right"),
                S("princess", 2, "mid", "back"),
            ]),
            Wave("Crossbow", level=13, spawns=[
                S("xbow", 0, "left", "river"), S("knight", 1, "left"),
                S("archers", 3, "left", "back"),
            ]),
            Wave("The Queen's Archers", level=13, spawns=[
                S("archer_queen", 0, "right"), S("archers", 2, "right", "back"),
                S("dart_goblin", 4, "left"),
            ]),
            Wave("Three Musketeers", level=12, boss=True, bonus_elixir=7, timeout=100, spawns=[
                S("three_musketeers", 0, "left", mult=1.3),
                S("heal_spirit", 6, "left", "push", level=14),
                S("archer_queen", 10, "right", mult=1.3),
                S("magic_archer", 14, "mid", "back", level=14),
            ]),
        ]),
    # ------------------------------------------------------------------ 14
    Level(
        "miners_strike", "Miner's Strike", "Level 14",
        "The miners have gone on strike - against you. They tunnel straight "
        "under your towers, so keep something at home.",
        "mighty_miner",
        waves=[
            Wave("Tunnel Rats", level=13, spawns=[
                S("goblins", 0, "right"), S("miner", 2, "left", "tower"),
            ]),
            Wave("Dig Dig Dig", level=13, spawns=[
                S("miner", 0, "right", "tower"), S("miner", 6, "left", "tower"),
            ]),
            Wave("Drill Sergeant", level=14, spawns=[
                S("mighty_miner", 0, "left"), S("goblin_drill", 4, "right", "near"),
            ]),
            Wave("Cave-in", level=12, spawns=[
                S("miner", 0, "left", "tower"), S("earthquake", 2, "left", "tower"),
                S("goblin_barrel", 7, "right", "tower"),
            ]),
            Wave("Mine Carts", level=13, spawns=[
                S("cannon_cart", 0, "left"), S("cannon_cart", 0, "right"),
                S("miner", 5, "left", "tower"),
            ]),
            Wave("Deep Core", level=14, spawns=[
                S("mighty_miner", 0, "right"), S("mighty_miner", 4, "left"),
                S("miner", 8, "left", "tower"),
            ]),
            Wave("The Mother Lode", level=12, boss=True, bonus_elixir=7, timeout=100, spawns=[
                S("mighty_miner", 0, "left", mult=1.7),
                S("miner", 4, "right", "tower", mult=1.7),
                S("mighty_miner", 14, "right", mult=1.7),
                S("miner", 18, "left", "tower", mult=1.7),
            ]),
        ]),
    # ------------------------------------------------------------------ 15
    Level(
        "dragons_lair", "Dragon's Lair", "Level 15",
        "You've wandered into the nest. Baby Dragons, Inferno Dragons and "
        "Electro Dragons - and their parents are not happy.",
        "baby_dragon",
        waves=[
            Wave("Hatchlings", level=12, spawns=[
                S("baby_dragon", 0, "left"), S("baby_dragon", 0, "right"),
            ]),
            Wave("Inferno Wings", level=12, spawns=[
                S("inferno_dragon", 0, "right"), S("bats", 3, "right", "back"),
            ]),
            Wave("Storm Drake", level=12, spawns=[
                S("electro_dragon", 0, "left"), S("baby_dragon", 3, "left", "back"),
            ]),
            Wave("Dragonfire", level=12, spawns=[
                S("baby_dragon", 0, "mid"), S("inferno_dragon", 5, "left"),
                S("fireball", 8, "mid", "army"),
            ]),
            Wave("The Brood", level=11, spawns=[
                S("baby_dragon", 0, "left"), S("inferno_dragon", 0, "right"),
                S("electro_dragon", 4, "mid"),
            ]),
            Wave("Molten Hound", level=11, spawns=[
                S("lava_hound", 0, "mid"), S("baby_dragon", 2, "mid", "back"),
            ]),
            Wave("Elder Dragons", level=12, boss=True, bonus_elixir=8, timeout=100, spawns=[
                S("inferno_dragon", 0, "left"),
                S("electro_dragon", 0, "right"),
                S("baby_dragon", 10, "mid", mult=1.3),
                S("fireball", 16, "mid", "army"),
                R("skeleton_dragons", 20, "mid"),
            ]),
        ]),
    # ------------------------------------------------------------------ 16
    Level(
        "siege_engines", "Siege Engines", "Level 16",
        "X-Bows and Mortars dig in at the river and shell your towers from "
        "afar. You'll have to cross into the miasma to knock them out.",
        "xbow",
        waves=[
            Wave("Bombardment", level=13, spawns=[
                S("mortar", 0, "left", "river"), S("knight", 2, "left"),
            ]),
            Wave("Crossfire", level=13, spawns=[
                S("xbow", 0, "right", "river"), S("ice_golem", 1, "right"),
                S("mortar", 4, "left", "river"),
            ]),
            Wave("Cannon Carts", level=13, spawns=[
                S("cannon_cart", 0, "left"), S("cannon_cart", 0, "right"),
            ]),
            Wave("Bomb Tower", level=13, spawns=[
                S("bomb_tower", 0, "mid", "river"), S("giant", 2, "left"),
                S("bowler", 4, "left", "back"),
            ]),
            Wave("Artillery", level=13, spawns=[
                S("mortar", 0, "left", "river"), S("mortar", 0, "right", "river"),
                S("knight", 3, "left"), S("knight", 3, "right"),
            ]),
            Wave("Full Siege", level=14, spawns=[
                S("xbow", 0, "left", "river"), S("tesla", 0, "right", "river"),
                S("giant", 3, "right"),
            ]),
            Wave("The Fortress", level=12, boss=True, bonus_elixir=8, timeout=100, spawns=[
                S("xbow", 0, "left", "river", mult=1.5),
                S("xbow", 0, "right", "river", mult=1.5),
                S("royal_giant", 6, "mid", mult=1.5),
                S("bowler", 8, "mid", "back", level=14),
            ]),
        ]),
    # ------------------------------------------------------------------ 17
    Level(
        "giants_causeway", "Giants' Causeway", "Level 17",
        "The ground shakes. Giants of every kind stomp toward your towers - "
        "and the Golem King brings up the rear.",
        "giant",
        waves=[
            Wave("Big Steps", level=11, spawns=[
                S("giant", 0, "left"), S("musketeer", 2, "left", "back"),
            ]),
            Wave("Royal Siege", level=11, spawns=[
                S("royal_giant", 0, "right"), S("archers", 2, "right", "back"),
            ]),
            Wave("Sparks Fly", level=11, spawns=[
                S("electro_giant", 0, "left"), S("goblin_giant", 0, "right"),
            ]),
            Wave("Bone Giant", level=11, spawns=[
                S("giant_skeleton", 0, "right"), S("giant", 4, "left"),
            ]),
            Wave("Ice Giants", level=12, spawns=[
                S("ice_golem", 0, "left"), S("giant", 1, "left", "back"),
                S("giant", 5, "right"),
            ]),
            Wave("Titans", level=11, spawns=[
                S("goblin_giant", 0, "left"), S("royal_giant", 0, "right"),
                S("electro_giant", 8, "mid"),
            ]),
            Wave("The Golem King", level=11, boss=True, bonus_elixir=8, timeout=110, spawns=[
                S("golem", 0, "mid"),
                S("night_witch", 3, "mid", "back"),
                S("rage", 10, "mid", "push"),
                R("giant", 16, "mid"),
            ]),
        ]),
    # ------------------------------------------------------------------ 18
    Level(
        "splash_zone", "Splash Zone", "Level 18",
        "Swarms won't save you here: Valkyries, Bowlers, Bombers and "
        "Executioners clear crowds - and the Mega Knights land on top.",
        "executioner",
        waves=[
            Wave("Spin Cycle", level=13, spawns=[
                S("valkyrie", 0, "left"), S("bomber", 2, "left", "back"),
                S("bomber", 4, "right"),
            ]),
            Wave("Bowling Night", level=13, spawns=[
                S("dark_prince", 0, "right"), S("bowler", 1, "right", "back"),
            ]),
            Wave("The Axe Man", level=13, spawns=[
                S("knight", 0, "left"), S("executioner", 1, "left", "back"),
            ]),
            Wave("Bomb Squad", level=13, spawns=[
                S("bomber", 0, "left"), S("bomber", 0, "right"),
                S("bomb_tower", 3, "mid", "river"),
            ]),
            Wave("Mega Drop", level=13, spawns=[
                S("mega_knight", 0, "left"), S("bomber", 2, "left", "back"),
            ]),
            Wave("Clean Sweep", level=13, spawns=[
                S("executioner", 0, "right"), S("bowler", 2, "right", "back"),
                S("valkyrie", 6, "left"),
            ]),
            Wave("Mega Knights", level=12, boss=True, bonus_elixir=8, timeout=110, spawns=[
                S("mega_knight", 0, "left", mult=1.3),
                S("executioner", 3, "left", "back", level=12),
                S("mega_knight", 16, "right", mult=1.3),
                S("bowler", 19, "right", "back", level=12),
            ]),
        ]),
    # ------------------------------------------------------------------ 19
    Level(
        "champions_arena", "Champions' Arena", "Level 19",
        "Every champion in the land wants a turn: Golden Knight, Archer "
        "Queen, Skeleton King, Monk, Mighty Miner, Goblinstein - then all at "
        "once.",
        "golden_knight",
        waves=[
            Wave("The Golden Knight", level=14, spawns=[
                S("golden_knight", 0, "left"), S("knight", 3, "right"),
            ]),
            Wave("Queen's Court", level=14, spawns=[
                S("knight", 0, "right"), S("archer_queen", 1, "right", "back"),
            ]),
            Wave("Bone Throne", level=14, spawns=[
                S("skeleton_king", 0, "left"), S("guards", 3, "right"),
            ]),
            Wave("Monk and Prince", level=14, spawns=[
                S("monk", 0, "mid"), S("little_prince", 3, "left"),
            ]),
            Wave("Gold Rush", level=14, spawns=[
                S("mighty_miner", 0, "right"), S("golden_knight", 4, "left"),
            ]),
            Wave("Mad Doctor", level=14, spawns=[
                S("goblinstein", 0, "left"), S("archer_queen", 3, "right"),
            ]),
            Wave("Hall of Champions", level=12, boss=True, bonus_elixir=8, timeout=120, spawns=[
                S("boss_bandit", 0, "left", mult=1.38),
                S("monk", 2, "right", mult=1.38),
                S("golden_knight", 12, "mid", mult=1.38),
                S("archer_queen", 14, "mid", "back", mult=1.38),
                S("skeleton_king", 20, "left", mult=1.38),
            ]),
        ]),
    # ------------------------------------------------------------------ 20
    Level(
        "final_siege", "The Final Siege", "Level 20",
        "Everything you've beaten comes back at once, stronger. Eight waves, "
        "then the Overlords. Good luck.",
        "golem",
        waves=[
            Wave("Vanguard", level=11, spawns=[
                S("pekka", 0, "left"), S("musketeer", 2, "left", "back"),
            ]),
            Wave("Air Raid", level=10, spawns=[
                S("lava_hound", 0, "right"), S("bats", 3, "right", "back"),
            ]),
            Wave("Graveyard Push", level=12, spawns=[
                S("giant", 0, "left"), S("graveyard", 5, "left", "tower"),
            ]),
            Wave("Hog Siege", level=11, spawns=[
                S("hog_rider", 0, "left"), S("xbow", 4, "mid", "river"),
            ]),
            Wave("Dark Magic", level=12, spawns=[
                S("witch", 0, "left"), S("night_witch", 0, "right"),
                S("lightning", 9, "mid", "army"),
            ]),
            Wave("Iron Wall", level=11, spawns=[
                S("mega_knight", 0, "mid"), S("electro_wizard", 2, "mid", "back"),
            ]),
            Wave("Last Stand", level=12, spawns=[
                S("golem", 0, "left"), S("minion_horde", 3, "left", "back"),
                S("rocket", 11, "left", "army"),
            ]),
            Wave("The Overlords", level=11, boss=True, bonus_elixir=9, timeout=130, spawns=[
                S("pekka", 0, "left", mult=1.2),
                S("mega_knight", 10, "right", mult=1.2),
                S("lava_hound", 14, "mid"),
                S("witch", 16, "mid", "back", level=13),
                S("rage", 18, "mid", "push", level=13),
            ]),
        ]),
    # ==================== ACT II: the newer cards (v1.2) ====================
    Level(
        "goblin_uprising", "Goblin Uprising", "Level 21",
        "Every goblin in the realm has had enough. Gangs, drills, cages, "
        "demolition crews - and the Machine itself.",
        "goblin_machine",
        waves=[
            Wave("The Gang's All Here", level=11, spawns=[
                S("goblin_gang", 0, "left"), S("goblin_gang", 0, "right"),
            ]),
            Wave("Demolition Crew", level=11, spawns=[
                S("goblin_demolisher", 0, "right"), S("goblin_gang", 3, "right", "back"),
            ]),
            Wave("Underground", level=11, spawns=[
                S("goblin_drill", 0, "left", "near"), S("spear_goblins", 4, "left", "back"),
            ]),
            Wave("Caged Fury", level=11, spawns=[
                S("goblin_cage", 0, "mid", "front"), S("goblin_demolisher", 3, "left"),
                S("dart_goblin", 5, "left", "back"),
            ]),
            Wave("Hex", level=11, spawns=[
                S("goblin_giant", 0, "right"), S("goblin_curse", 8, "right", "army"),
            ]),
            Wave("Two Drills", level=11, spawns=[
                S("goblin_drill", 0, "left", "near"), S("goblin_drill", 3, "right", "near"),
            ]),
            Wave("The Machine", level=11, boss=True, bonus_elixir=7, timeout=90, spawns=[
                S("goblin_machine", 0, "left", mult=1.3),
                S("goblin_gang", 4, "left", "back"),
                S("goblinstein", 10, "right"),
                S("goblin_curse", 16, "mid", "army"),
                R("goblin_gang", 20, "right"),
            ]),
        ]),
    Level(
        "royal_parade", "Royal Parade", "Level 22",
        "The Crown's army marches in formation: recruits by the dozen, hogs "
        "in a row and a ghost you'll never see coming.",
        "royal_recruits",
        waves=[
            Wave("Fall In!", level=11, spawns=[
                S("royal_recruits", 0, "mid"),
            ]),
            Wave("Hog Line", level=11, spawns=[
                S("royal_hogs", 0, "mid"), S("archers", 3, "left", "back"),
            ]),
            Wave("Haunting", level=11, spawns=[
                S("royal_ghost", 0, "left"), S("royal_ghost", 3, "right"),
            ]),
            Wave("Cavalry", level=11, spawns=[
                S("ram_rider", 0, "right"), S("prince", 3, "left"),
            ]),
            Wave("Royal Escort", level=11, spawns=[
                S("royal_giant", 0, "left"), S("princess", 2, "left", "back"),
                S("royal_delivery", 6, "left", "army"),
            ]),
            Wave("Second Rank", level=12, spawns=[
                S("royal_recruits", 0, "mid"), S("royal_hogs", 7, "mid"),
            ]),
            Wave("The Royal Guard", level=11, boss=True, bonus_elixir=8, timeout=100, spawns=[
                S("royal_giant", 0, "right", mult=1.25),
                S("royal_recruits", 4, "mid"),
                S("royal_ghost", 9, "left", mult=1.2),
                S("ram_rider", 14, "left"),
            ]),
        ]),
    Level(
        "spirit_grove", "Spirit Grove", "Level 23",
        "Wisps, sprites and a dragon-riding Empress guard the sacred grove - "
        "and its Phoenix keeps coming back.",
        "spirit_empress",
        waves=[
            Wave("Will-o'-Wisps", level=11, spawns=[
                S("fire_spirit", 0, "left"), S("ice_spirit", 1, "left"),
                S("electro_spirit", 0, "right"), S("heal_spirit", 1, "right"),
            ]),
            Wave("Rebirth", level=11, spawns=[
                S("phoenix", 0, "right"), S("electro_spirit", 4, "left"),
            ]),
            Wave("Grove Keeper", level=11, spawns=[
                S("spirit_empress", 0, "left"), S("heal_spirit", 4, "left", "push"),
            ]),
            Wave("Overgrowth", level=11, spawns=[
                S("suspicious_bush", 0, "right"), S("suspicious_bush", 3, "left"),
                S("vines", 8, "right", "army"),
            ]),
            Wave("Spirit Storm", level=11, spawns=[
                S("fire_spirit", 0, "left"), S("fire_spirit", 0, "right"),
                S("electro_spirit", 0, "mid"), S("electro_dragon", 3, "mid", "back"),
            ]),
            Wave("Two Phoenixes", level=11, spawns=[
                S("phoenix", 0, "left"), S("phoenix", 0, "right"),
            ]),
            Wave("The Empress Ascends", level=11, boss=True, bonus_elixir=8, timeout=100,
                 spawns=[
                     S("spirit_empress_air", 0, "mid", mult=1.3),
                     S("phoenix", 5, "left"),
                     S("heal_spirit", 8, "mid", "push"),
                     S("vines", 14, "mid", "army"),
                 ]),
        ]),
    Level(
        "witching_hour", "Witching Hour", "Level 24",
        "At midnight the coven gathers. Whatever falls in their curses gets "
        "up again - on THEIR side.",
        "mother_witch",
        waves=[
            Wave("Familiars", level=11, spawns=[
                S("skeleton_army", 0, "left"), S("mother_witch", 1, "left", "back"),
            ]),
            Wave("Night Flight", level=11, spawns=[
                S("night_witch", 0, "right"), S("bats", 3, "right", "back"),
            ]),
            Wave("The Coven", level=11, spawns=[
                S("witch", 0, "left"), S("mother_witch", 0, "right"),
            ]),
            Wave("Curse of Goblins", level=11, spawns=[
                S("giant", 0, "right"), S("mother_witch", 3, "right", "back"),
                S("goblin_curse", 7, "right", "army"),
            ]),
            Wave("Into the Void", level=12, spawns=[
                S("golem", 0, "left"), S("void", 10, "left", "army"),
            ]),
            Wave("Graveyard Shift", level=11, spawns=[
                S("graveyard", 0, "left", "tower"), S("mother_witch", 4, "left"),
            ]),
            Wave("Midnight", level=11, boss=True, bonus_elixir=8, timeout=100, spawns=[
                S("mother_witch", 0, "mid", mult=1.4),
                S("witch", 2, "left"), S("night_witch", 2, "right"),
                S("void", 12, "mid", "army"),
                S("goblin_curse", 16, "mid", "army"),
            ]),
        ]),
    Level(
        "rascal_alley", "Rascal Alley", "Level 25",
        "Kids with slingshots, a girl with a rocket launcher and a bush that "
        "is definitely just a bush.",
        "rascals",
        waves=[
            Wave("Playground", level=11, spawns=[
                S("rascals", 0, "left"),
            ]),
            Wave("Fireworks", level=11, spawns=[
                S("knight", 0, "right"), S("firecracker", 1, "right", "back"),
                S("firecracker", 3, "left"),
            ]),
            Wave("Suspicious...", level=11, spawns=[
                S("suspicious_bush", 0, "left"), S("berserker", 1, "left"),
                S("suspicious_bush", 4, "right"),
            ]),
            Wave("Street Gang", level=11, spawns=[
                S("berserker", 0, "right"), S("bandit", 2, "right"),
                S("firecracker", 4, "right", "back"),
            ]),
            Wave("Bully", level=12, spawns=[
                S("rascals", 0, "right"), S("dart_goblin", 2, "right", "back"),
            ]),
            Wave("Hide and Seek", level=11, spawns=[
                S("suspicious_bush", 0, "left"), S("suspicious_bush", 0, "right"),
                S("bandit", 4, "mid"),
            ]),
            Wave("Boss of the Block", level=11, boss=True, bonus_elixir=8, timeout=100, spawns=[
                S("boss_bandit", 0, "left", mult=1.3),
                S("rascals", 3, "left"),
                S("firecracker", 6, "right", "back"),
                R("berserker", 10, "right"),
            ]),
        ]),
    Level(
        "rune_forge", "The Rune Forge", "Level 26",
        "The Rune Giant sharpens every blade in her army - and the smiths "
        "enchant the rest with rage. Kill the escort before it gets going.",
        "rune_giant",
        waves=[
            Wave("Apprentices", level=11, spawns=[
                S("rune_giant", 0, "left"), S("barbarians", 2, "left", "back"),
            ]),
            Wave("Sharpened Steel", level=11, spawns=[
                S("elite_barbarians", 0, "right"), S("rage", 4, "right", "push"),
            ]),
            Wave("Anvil", level=11, spawns=[
                S("rune_giant", 0, "left"), S("executioner", 3, "left", "back"),
                S("dart_goblin", 4, "left", "back"),
            ]),
            Wave("Enchanted Dash", level=11, spawns=[
                S("lumberjack", 0, "right"), S("bandit", 1, "right", "back"),
                S("rage", 5, "right", "push"),
            ]),
            Wave("Forge Fire", level=12, spawns=[
                S("inferno_dragon", 0, "left"), S("furnace", 2, "left", "back"),
                S("fireball", 10, "left", "army"),
            ]),
            Wave("Double Order", level=11, spawns=[
                S("rune_giant", 0, "left"), S("rune_giant", 0, "right"),
                S("valkyrie", 3, "mid"),
            ]),
            Wave("Master Smith", level=11, boss=True, bonus_elixir=8, timeout=100, spawns=[
                S("rune_giant", 0, "mid", mult=1.4),
                S("mini_pekka", 3, "mid", "back"),
                S("prince", 6, "left"), S("dark_prince", 6, "right"),
            ]),
        ]),
    Level(
        "fishers_wharf", "Fisher's Wharf", "Level 27",
        "Duelists of the docks. The Fisherman reels you in and the Ronin "
        "parries everything you swing.",
        "ronin",
        waves=[
            Wave("Catch of the Day", level=11, spawns=[
                S("fisherman", 0, "left"), S("musketeer", 2, "left", "back"),
            ]),
            Wave("The Wandering Blade", level=11, spawns=[
                S("ronin", 0, "right"),
            ]),
            Wave("Harpoon", level=11, spawns=[
                S("fisherman", 0, "right"), S("hunter", 2, "right", "back"),
            ]),
            Wave("Rough Seas", level=11, spawns=[
                S("bowler", 0, "left"), S("fisherman", 2, "left"),
            ]),
            Wave("Swordmasters", level=12, spawns=[
                S("ronin", 0, "left"), S("golden_knight", 2, "right"),
            ]),
            Wave("Nets and Anchors", level=11, spawns=[
                S("fisherman", 0, "left"), S("fisherman", 0, "right"),
                S("executioner", 3, "mid", "back"),
            ]),
            Wave("The Last Duel", level=11, boss=True, bonus_elixir=8, timeout=100, spawns=[
                S("ronin", 0, "left", mult=1.4),
                S("fisherman", 2, "right", mult=1.2),
                S("pekka", 8, "mid"),
            ]),
        ]),
    Level(
        "dragon_roost", "Dragon Roost", "Level 28",
        "Bone dragons, toxic giants and a firebird that won't stay dead. "
        "Bring anti-air. Lots of it.",
        "skeleton_dragons",
        waves=[
            Wave("Bone Wings", level=11, spawns=[
                S("skeleton_dragons", 0, "left"), S("bats", 3, "right"),
            ]),
            Wave("Toxic Cloud", level=11, spawns=[
                S("minion_giant", 0, "right"), S("minions", 3, "right", "back"),
            ]),
            Wave("Phoenix Down", level=11, spawns=[
                S("phoenix", 0, "left"), S("skeleton_dragons", 3, "left", "back"),
            ]),
            Wave("Storm Front", level=11, spawns=[
                S("electro_dragon", 0, "right"), S("inferno_dragon", 0, "left"),
            ]),
            Wave("Flying Fortress", level=12, spawns=[
                S("minion_giant", 0, "left"), S("balloon", 4, "left"),
            ]),
            Wave("Swarm of Wings", level=11, spawns=[
                S("minion_horde", 0, "mid"), S("bats", 2, "left"), S("bats", 2, "right"),
                R("minions", 7, "mid"),
            ]),
            Wave("The Ancient Wyrm", level=11, boss=True, bonus_elixir=8, timeout=110, spawns=[
                S("lava_hound", 0, "mid", mult=1.3),
                S("minion_giant", 4, "left"),
                S("phoenix", 8, "right"),
                R("skeleton_dragons", 12, "mid"),
            ]),
        ]),
    Level(
        "machine_works", "Machine Works", "Level 29",
        "The goblin engineers rolled out everything with a gear in it. "
        "Siege, sparks and rockets.",
        "goblin_machine",
        waves=[
            Wave("Assembly Line", level=11, spawns=[
                S("goblin_machine", 0, "left"), S("spear_goblins", 2, "left", "back"),
            ]),
            Wave("Live Wire", level=11, spawns=[
                S("sparky", 0, "right"), S("goblin_gang", 2, "right"),
            ]),
            Wave("Artillery", level=11, spawns=[
                S("mortar", 0, "left", "river"), S("cannon_cart", 2, "right"),
            ]),
            Wave("Fuse Lit", level=11, spawns=[
                S("goblin_demolisher", 0, "left"), S("goblin_demolisher", 0, "right"),
                S("flying_machine", 4, "right", "back"),
            ]),
            Wave("Crossfire", level=11, spawns=[
                S("xbow", 0, "mid", "river"), S("knight", 1, "mid"),
                S("goblin_drill", 6, "left", "near"),
            ]),
            Wave("Heavy Metal", level=11, spawns=[
                S("goblin_machine", 0, "right"), S("electro_giant", 0, "left"),
            ]),
            Wave("Prototype X", level=11, boss=True, bonus_elixir=9, timeout=110, spawns=[
                S("goblin_machine", 0, "left", mult=1.4),
                S("sparky", 4, "left", "back"),
                S("goblin_machine", 10, "right", mult=1.2),
                S("rocket", 16, "mid", "army"),
            ]),
        ]),
    Level(
        "grand_finale", "The Grand Finale", "Level 30",
        "Every new champion of the arena, all at once. This is the real "
        "final boss.",
        "spirit_empress_air",
        waves=[
            Wave("Opening Act", level=11, spawns=[
                S("goblin_gang", 0, "left"), S("rascals", 0, "right"),
            ]),
            Wave("Hooks and Blades", level=11, spawns=[
                S("fisherman", 0, "right"), S("ronin", 2, "right"),
            ]),
            Wave("Curses", level=11, spawns=[
                S("mother_witch", 0, "left"), S("royal_ghost", 2, "left"),
                S("goblin_curse", 8, "left", "army"),
            ]),
            Wave("Air Superiority", level=11, spawns=[
                S("phoenix", 0, "right"), S("skeleton_dragons", 2, "right", "back"),
            ]),
            Wave("Enchanted Siege", level=11, spawns=[
                S("rune_giant", 0, "left"), S("goblin_machine", 2, "left"),
                S("void", 12, "left", "army"),
            ]),
            Wave("Parade", level=11, spawns=[
                S("royal_recruits", 0, "mid"), S("ram_rider", 4, "left"),
                S("firecracker", 5, "right", "back"),
            ]),
            Wave("The Empress and Her Court", level=11, boss=True, bonus_elixir=10,
                 timeout=130, spawns=[
                     S("spirit_empress_air", 0, "mid", mult=1.3),
                     S("ronin", 4, "left", mult=1.2),
                     S("goblin_machine", 8, "right", mult=1.2),
                     S("phoenix", 12, "mid"),
                     S("rage", 14, "mid", "push"),
                     S("vines", 18, "mid", "army"),
                 ]),
        ]),
]

# ---------------------------------------------------------------------------
# Level progression: the tables above are tuned as if your cards were level
# 11. Later levels add `shift` to every enemy level, so enemies go from level
# 11 on Level 1 to level 16 on Level 20 - you upgrade your cards to keep up.
# recommended_level() is the card level the level was balanced for.
# ---------------------------------------------------------------------------
LEVEL_SHIFTS = [0, 0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 3, 3, 2, 3,
                3, 3, 3, 4, 4, 4, 4, 4, 5, 5]
for _lv, _sh in zip(LEVELS, LEVEL_SHIFTS):
    _lv.shift = _sh

# Extra hp & damage for every enemy of a level, tuned against the defend-only
# AI with tools/level_tune.py (1.0 = untouched).
LEVEL_POWER = {
    "bone_crypt": 0.85, "goblin_ambush": 0.953, "iron_legion": 0.89,
    "barbarian_raid": 0.787, "sky_raiders": 1.045, "royal_court": 0.842,
    "rogues_den": 0.984, "spark_and_storm": 0.83, "hog_stampede": 0.916,
    "pyromancers": 0.941, "graveyard_shift": 0.96, "marksmen": 0.927,
    "miners_strike": 0.97, "giants_causeway": 0.973, "splash_zone": 1.107,
    "champions_arena": 1.03, "final_siege": 0.95, "goblin_uprising": 0.987,
    "spirit_grove": 1.12, "witching_hour": 1.28, "rascal_alley": 1.105,
    "rune_forge": 0.94, "fishers_wharf": 1.47, "dragon_roost": 0.906,
    "machine_works": 1.12, "grand_finale": 0.926,
}
# v1.4.4: the crown towers became the real Tower Princess (+10% hp, +8%
# damage) and the cards were rebalanced; this brings every level back to
# its 1.4.3 difficulty (measured with the defend-only AI)
WAVE_POWER = float(os.environ.get("LEVEL_WAVE_POWER", "1.12"))
for _lv in LEVELS:
    _lv.power = LEVEL_POWER.get(_lv.key, 1.0) * WAVE_POWER


def recommended_level(level):
    return LEVEL_BASE + level.shift


def enemy_level_range(level):
    """(lowest, highest) enemy unit level in the level's normal waves."""
    lv = [w.level + level.shift for w in level.waves if not w.boss]
    lv += [sp.level + level.shift for w in level.waves for sp in w.spawns
           if sp.level is not None]
    return min(lv), max(lv)


def stars_needed(index):
    """Total stars needed to open the level at 0-based `index`."""
    import profile_data
    return profile_data.STARS_PER_UNLOCK * index


# Win conditions only hit buildings - with no enemy towers they'd do
# nothing, so they can't be used in Levels.
# only cards that can't hit anything but buildings are banned (the X-Bow and
# Mortar shoot troops too, so they're welcome)
BANNED = frozenset(c.key for c in cards.DEPLOYABLE_CARDS if c.attacks == "buildings")


def banned_in(deck):
    return [k for k in deck if k in BANNED]


def default_level_deck(base=None):
    """A Levels-legal deck: your deck minus win conditions, topped up."""
    fill = ["knight", "musketeer", "valkyrie", "archers", "fireball", "zap",
            "cannon", "minions", "baby_dragon", "mini_pekka", "wizard", "arrows"]
    deck = [k for k in (base or []) if k not in BANNED][:8]
    champ = any(cards.CARDS[k].is_champion for k in deck)
    for k in fill:
        if len(deck) >= 8:
            break
        if k not in deck and not (champ and cards.CARDS[k].is_champion):
            deck.append(k)
    return deck

MIASMA_TICK = 1.0        # seconds between poison ticks on the enemy half


def miasma_damage():
    """Tiny poison: a Goblin dies on the 6th tick, everything else lasts longer."""
    import math
    return math.ceil(cards.CARDS["goblins"].hp / 6.0)


LEVELS_BY_KEY = {lv.key: lv for lv in LEVELS}


# ===========================================================================
#  RUNNING A LEVEL
# ===========================================================================
class LevelRun:
    """Drives the waves of one level inside a Match (opponent = ENEMY)."""

    def __init__(self, match, level):
        self.m = match
        self.level = level
        self.wave_idx = -1
        self.state = "prep"         # prep -> wave -> prep -> ... -> won
        self.timer = level.prep_first
        self.wave_t = 0.0
        self.pending = []
        self.banner = None          # (title, subtitle, time_shown)
        self.note = None            # (mid-wave call-out, time_shown)
        self.towers_lost = 0
        self.tower_log = []         # [(wave number, "left"|"right"|"king")]
        self._alive = {s: True for s in ("left", "right", "king")}
        match.elixir[PLAYER] = level.start_elixir
        self._show("Defend your towers!", "%d waves" % len(level.waves))

    # ---- info for the HUD ----
    @property
    def wave_number(self):
        return max(0, self.wave_idx + 1)

    @property
    def total_waves(self):
        return len(self.level.waves)

    def next_wave_in(self):
        return self.timer if self.state == "prep" else None

    def current_wave(self):
        if 0 <= self.wave_idx < len(self.level.waves):
            return self.level.waves[self.wave_idx]
        return None

    def stars(self):
        lost = sum(1 for s in ("left", "right")
                   if not self.m.towers[(PLAYER, s)].alive)
        return max(1, 3 - lost)

    def _show(self, title, sub=""):
        self.banner = (title, sub, 0.0)

    # ---- per frame ----
    def update(self, dt):
        m = self.m
        if m.finished:
            return
        if self.banner:
            t, s, age = self.banner
            self.banner = (t, s, age + dt) if age < 3.0 else None
        if self.note:
            n, age = self.note
            self.note = (n, age + dt) if age < 2.2 else None
        for side, was in self._alive.items():
            if was and not m.towers[(PLAYER, side)].alive:
                self._alive[side] = False
                self.tower_log.append((self.wave_number, side))
        if self.state == "prep":
            self.timer -= dt
            if self.timer <= 0:
                self._start_wave(self.wave_idx + 1)
        elif self.state == "wave":
            self.wave_t += dt
            while self.pending and self.pending[0].at <= self.wave_t:
                sp = self.pending.pop(0)
                if not self._spawn(sp):
                    # an "army" spell with nothing to hit yet: try again in a
                    # second (the retry count rides along in `place`)
                    base, _, n = sp.place.partition(":wait")
                    self.pending.append(Spawn(sp.key, self.wave_t + 1.0, sp.lane,
                                              sp.level, sp.mult,
                                              "%s:wait%d" % (base, int(n or 0) + 1), sp.note))
                    self.pending.sort(key=lambda q: q.at)
            wave = self.current_wave()
            cleared = (not self.pending and not self._enemies_alive()
                       and m.towers[(PLAYER, "king")].alive)
            if cleared or self.wave_t >= wave.timeout:
                if self.wave_idx + 1 >= len(self.level.waves):
                    if cleared:
                        self.state = "won"
                        m.finished = True
                        m.winner = PLAYER
                else:
                    self.state = "prep"
                    self.timer = self.level.prep
                    nxt = self.level.waves[self.wave_idx + 1]
                    if nxt.boss:
                        self._show("Something stirs...", "Boss wave next")

    def _enemies_alive(self):
        m = self.m
        if any(e.team == ENEMY and e.alive and not e.is_tower for e in m.entities):
            return True
        return any(fx.team == ENEMY and fx.kind in ("incoming", "graveyard")
                   for fx in m.effects)

    def _start_wave(self, idx):
        wave = self.level.waves[idx]
        self.wave_idx = idx
        self.state = "wave"
        self.wave_t = 0.0
        self.pending = sorted(wave.spawns, key=lambda s: s.at)
        if wave.bonus_elixir:
            self.m.add_elixir(PLAYER, wave.bonus_elixir)
        title = ("BOSS: " if wave.boss else "Wave %d: " % (idx + 1)) + wave.name
        if wave.boss:
            top = max(sp.mult for sp in wave.spawns)
            sub = ("double health & damage" if top >= 2.0 else
                   "x%g health & damage" % top if top > 1.0 else "final wave")
        else:
            sub = "units level %d" % (wave.level + self.level.shift)
        if wave.bonus_elixir:
            sub += "   +%d elixir" % wave.bonus_elixir
        self._show(title, sub)
        self.m.emit("wave", "boss" if wave.boss else "wave", 9.0, 8.0, ENEMY)

    def _army_spot(self, radius, team=PLAYER, min_y=None):
        """Centre of the thickest clump of `team`'s troops (or None);
        min_y: only troops at least that far down the field."""
        troops = [e for e in self.m.entities
                  if e.alive and e.team == team and not e.is_tower
                  and not e.is_building and (min_y is None or e.y >= min_y)]
        best, best_v = None, 0.0
        for c in troops:
            v = 0.0
            sx = sy = 0.0
            n = 0
            for e in troops:
                if (e.x - c.x) ** 2 + (e.y - c.y) ** 2 <= (radius * 0.8) ** 2:
                    v += 1.0 + e.max_hp / 1000.0
                    sx += e.x
                    sy += e.y
                    n += 1
            if v > best_v:
                best, best_v = (sx / n, sy / n), v
        return best

    def _spawn(self, sp):
        """Deploy one scripted spawn. Returns False to retry it later."""
        m = self.m
        wave = self.current_wave()
        lv = (sp.level if sp.level is not None else wave.level) + self.level.shift
        mult = level_mult(lv) * sp.mult * self.level.power
        x = LANE_X.get(sp.lane, 9.0)
        c = cards.CARDS[sp.key]
        place, _, wait = sp.place.partition(":wait")
        if place == "push":
            # the wave's own support: on its push once it reaches the river
            r = max(c.spell_radius, 2.0)
            spot = self._army_spot(r, ENEMY, RIVER_TOP - 1.5)
            if spot is None and int(wait or 0) < ARMY_WAIT:
                return False
            spot = spot or self._army_spot(r, ENEMY)
            if spot is None:
                return True                    # nothing left to help: skip it
            x, y = spot
            if c.category != "spell":          # a support troop lands just behind
                y = max(1.0, y - 1.5)
            place = "army"
        elif place == "army":
            spot = self._army_spot(max(c.spell_radius, 1.5))
            if spot is None and int(wait or 0) < ARMY_WAIT:
                return False
            if spot is None:
                place = "tower"
            else:
                x, y = spot
        if sp.note:
            self.note = (sp.note, 0.0)
        if place in ("tower", "near"):
            side = "left" if sp.lane == "left" else "right"
            tw = m.towers[(PLAYER, side)]
            if not tw.alive:
                tw = m.towers[(PLAYER, "king")]
            x, y = tw.x, tw.y - (3.0 if place == "near" else 0.0)
        elif place == "army":
            pass
        elif place in PLACE_Y:
            y = PLACE_Y[place]
        else:
            # troops step out of their lane's crypt gate ("back" ones a bit
            # deeper inside, so they arrive later)
            y = GATE_Y.get(sp.lane, 6.0) + (0.4 if place == "back" else 1.0)
        m.team_power[ENEMY] = (mult, mult)
        m.team_level[ENEMY] = lv
        before = set(id(e) for e in m.entities)
        m._deploy(ENEMY, sp.key, x, y)
        if c.category != "spell":
            m.emit("portal", sp.key, x, y, ENEMY)
        for e in m.entities:
            if id(e) not in before and e.team == ENEMY:
                e.boss = sp.mult > 1.0 or wave.boss
        # spells keep the wave's power for anything they raise later
        wl = wave.level + self.level.shift
        m.team_power[ENEMY] = (level_mult(wl), level_mult(wl))
        m.team_level[ENEMY] = wl
        return True


def new_level_match(level, player_deck, card_levels=None, tower_level=None,
                    evo_cards=None, hero_cards=None, king_level=None):
    """A Match set up for a level: no enemy towers, no clock. card_levels is
    your {card: level} (or one level for all); tower_level your towers';
    evo_cards / hero_cards your Evolutions and Hero."""
    from engine import Match
    m = Match(player_deck, cards.DEFAULT_AI_DECK, enemy_towers=False, timed=False,
              card_levels={PLAYER: card_levels} if card_levels is not None else None,
              tower_levels={PLAYER: tower_level} if tower_level is not None else None,
              king_levels={PLAYER: king_level} if king_level is not None else None,
              evo_cards={PLAYER: evo_cards or []}, hero_cards={PLAYER: hero_cards or []})
    m.banned = set(BANNED)
    m.miasma = (miasma_damage(), MIASMA_TICK)
    return m, LevelRun(m, level)


# ===========================================================================
#  ENDLESS SURVIVAL
# ===========================================================================
# Procedural waves that never stop. Each wave has an elixir "budget" that
# grows with the wave number, spent on troops from tiers that unlock as you
# go; every 5th wave is a boss wave. Enemy levels rise from 11 by one every
# 3 waves (to 16), after which bosses keep getting tougher. Your cards use
# their own levels (no catch-up), so upgrades matter.
ENDLESS_POOLS = [
    ["skeletons", "goblins", "spear_goblins", "bats", "minions", "archers",
     "knight", "bomber", "ice_spirit", "fire_spirit", "guards", "dart_goblin"],
    ["valkyrie", "musketeer", "mini_pekka", "wizard", "baby_dragon", "hog_rider",
     "dark_prince", "prince", "lumberjack", "bandit", "mega_minion", "barbarians",
     "skeleton_army", "witch", "executioner", "hunter", "electro_wizard",
     "inferno_dragon", "battle_ram", "night_witch"],
    ["giant", "pekka", "balloon", "giant_skeleton", "royal_giant", "elite_barbarians",
     "bowler", "sparky", "goblin_giant", "electro_dragon", "minion_horde",
     "golden_knight", "skeleton_king", "monk"],
    ["golem", "mega_knight", "lava_hound", "electro_giant", "three_musketeers",
     "boss_bandit", "goblinstein"],
]
ENDLESS_SPELLS = ["fireball", "arrows", "poison", "lightning", "snowball", "zap",
                  "goblin_barrel", "graveyard"]
ENDLESS_SUPPORT = ["rage", "heal_spirit"]       # dropped on the wave's own push


def is_swarm(key):
    """Many small bodies (Goblins, Skeleton Army, Bats, Barbarians...)."""
    c = cards.CARDS[key]
    return c.count >= 3 and c.hp <= 240


def is_heavy(key):
    """A tank or a win condition (Giant, Golem, Hog Rider, P.E.K.K.A...)."""
    c = cards.CARDS[key]
    return c.count == 1 and (c.hp >= 1300 or c.attacks == "buildings")


# What an Endless wave is built around: which troops fit it, and the names it
# may be called (every name describes what actually spawns)
ENDLESS_THEMES = {
    "swarm": (is_swarm, ["Swarm", "Horde", "Skitter", "Teeming Masses"]),
    "air": (lambda k: cards.CARDS[k].flying, ["Air Raid", "Black Sky", "Wingbeat"]),
    "heavy": (is_heavy, ["Heavy Push", "Juggernauts", "Siege", "Big Steps"]),
    "rush": (lambda k: cards.CARDS[k].speed >= 2.0 and cards.CARDS[k].range <= 2
             and not is_swarm(k), ["Stampede", "Charge!", "Rush"]),
    "ranged": (lambda k: cards.CARDS[k].range >= 4 and cards.CARDS[k].attacks != "buildings",
               ["Volley", "Crossfire", "Sharpshooters"]),
    "mixed": (lambda k: True, ["Skirmish", "Raiders", "Vanguard", "Onslaught",
                               "Warband", "Legion"]),
}


def endless_name(spawns, rng):
    """A name for a normal Endless wave that matches its troops."""
    troops = [s.key for s in spawns if cards.CARDS[s.key].category == "troop"
              and s.key not in ENDLESS_SUPPORT]
    for theme in ("swarm", "air", "heavy", "rush", "ranged"):
        fits, names = ENDLESS_THEMES[theme]
        if troops and all(fits(k) for k in troops):
            return rng.choice(names)
    if sum(is_swarm(k) for k in troops) * 2 > len(troops) >= 3:
        return "Mob"
    return rng.choice(ENDLESS_THEMES["mixed"][1])


def endless_wave(n, rng):
    """Wave number n (1-based) of an Endless run."""
    lv = min(16, 11 + (n - 1) // 3)
    boss = n % 5 == 0
    tiers = min(len(ENDLESS_POOLS), 1 + n // 3)
    budget = 4 + n * 1.6
    spawns = []
    t = 0.0
    side = rng.choice(["left", "right"])
    other = "right" if side == "left" else "left"
    # the plan: one big push, a two-lane split, or a push followed by a
    # second group that arrives as reinforcements
    plan = "push" if n < 3 else rng.choice(["push", "split", "split", "reinforce"])
    if plan == "split":
        budget *= 0.95                  # two lanes at once are harder to stop
    theme = rng.choice(list(ENDLESS_THEMES)) if not boss and n >= 2 else "mixed"
    fits = ENDLESS_THEMES[theme][0]
    boss_key = None
    if boss:
        boss_key = rng.choice(ENDLESS_POOLS[min(3, 1 + n // 6)])
        mult = 1.3 + 0.1 * (n // 5) + (0.08 * max(0, n - 18))
        spawns.append(Spawn(boss_key, 0.0, side, None, round(mult, 2)))
        budget *= 0.45
        t = 3.0
    unlocked = [k for tier in ENDLESS_POOLS[:tiers] for k in tier
                if cards.CARDS[k].elixir <= budget + 1]
    pool = [k for k in unlocked if fits(k)] or unlocked
    picks = []
    tries = 0
    while budget >= 2 and tries < 200:
        tries += 1
        key = rng.choice(pool)
        c = cards.CARDS[key]
        if c.elixir > budget + 1:
            continue
        budget -= c.elixir
        picks.append(key)
    for i, key in enumerate(picks):
        c = cards.CARDS[key]
        place = "back" if c.range >= 4 else "field"
        lane = side
        if plan == "split":
            lane = side if i % 2 == 0 else other
        elif plan == "reinforce" and len(picks) >= 2 and i == len(picks) - 1:
            spawns.append(Spawn(key, t + 6.0, other, None, 1.0, place, "Reinforcements!"))
            continue
        elif rng.random() < 0.25:
            lane = "mid"
        spawns.append(Spawn(key, t, lane, None, 1.0, place))
        # a split sends both halves together; a push follows up in a column
        t += rng.uniform(0.0, 1.0) if plan == "split" and i % 2 == 0 else rng.uniform(1.5, 3.5)
    if n >= 6 and rng.random() < 0.3:
        spawns.append(Spawn(rng.choice(ENDLESS_SUPPORT), 4.0, side, None, 1.0, "push"))
    if n >= 4 and rng.random() < 0.45:
        sp = rng.choice(ENDLESS_SPELLS)
        place = "tower" if sp in ("goblin_barrel", "graveyard") else "army"
        spawns.append(Spawn(sp, t + 2.0, rng.choice(["left", "right"]), None, 1.0, place))
    if boss:
        name = rng.choice(["%s Unleashed", "%s Approaches", "%s Rises"]) % cards.CARDS[boss_key].name
    else:
        name = endless_name(spawns, rng)
    return Wave(name, spawns, level=lv, boss=boss,
                bonus_elixir=4 if boss else (1 if n % 2 == 0 else 0),
                timeout=60 if boss else 40)


class EndlessRun(LevelRun):
    """A LevelRun whose waves are generated on the fly, forever."""

    def __init__(self, match, seed=None):
        import random as _r
        self.rng = _r.Random(seed)
        lv = Level("endless", "Endless Survival", "Endless",
                   "Waves never stop. How long can you last?", "skeleton_king",
                   waves=[endless_wave(1, self.rng)], prep_first=8.0, prep=6.0)
        super().__init__(match, lv)
        self._show("Endless Survival", "how many waves can you hold?")

    @property
    def total_waves(self):
        return 0                        # unlimited

    def update(self, dt):
        while len(self.level.waves) <= self.wave_idx + 1:
            self.level.waves.append(endless_wave(len(self.level.waves) + 1, self.rng))
        super().update(dt)

    def waves_survived(self):
        """Waves fully cleared (the current one counts if it was cleared)."""
        if self.state == "prep":
            return self.wave_number
        return max(0, self.wave_number - 1)


def new_endless_match(player_deck, card_levels=None, tower_level=None,
                      evo_cards=None, hero_cards=None, seed=None, king_level=None):
    from engine import Match
    m = Match(player_deck, cards.DEFAULT_AI_DECK, enemy_towers=False, timed=False,
              card_levels={PLAYER: card_levels} if card_levels is not None else None,
              tower_levels={PLAYER: tower_level} if tower_level is not None else None,
              king_levels={PLAYER: king_level} if king_level is not None else None,
              evo_cards={PLAYER: evo_cards or []}, hero_cards={PLAYER: hero_cards or []})
    m.banned = set(BANNED)
    m.miasma = (miasma_damage(), MIASMA_TICK)
    return m, EndlessRun(m, seed)
