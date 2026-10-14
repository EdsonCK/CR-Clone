"""
============================================================================
  TOWERS.PY  --  Tower Troops (who stands on your Princess Towers)
============================================================================

As in the real game, your two Princess Towers are manned by a TOWER TROOP
you pick per deck (Decks screen, "Tower Troop" button). The Tower Princess
is free; the others unlock on the Trophy Road at the same arenas as in
Clash Royale:

    Tower Princess   balanced arrows                         (start)
    Cannoneer        slow, heavy cannonballs, less hp        Frozen Peak
    Dagger Duchess   8 rapid daggers, then slow reloads      Electro Valley
    Royal Chef       every ~23s a pancake gives your         Rascal's Hideout
                     biggest troop +1 level

Numbers are relative to the Tower Princess (config.PRINCESS_TOWER_*), taken
from the real level-11 stats.
============================================================================
"""

from dataclasses import dataclass


@dataclass
class TowerTroop:
    key: str
    name: str
    hp_mult: float          # x PRINCESS_TOWER_HP
    dmg_mult: float         # x PRINCESS_TOWER_DMG
    hit_speed: float
    range: float
    unlock: int             # trophies needed (Trophy Road)
    rarity: str
    desc: str
    daggers: int = 0        # Dagger Duchess magazine
    reload: float = 0.0     #   seconds to reload one dagger (when not throwing)
    empty_hit_speed: float = 0.0   # hit speed with an empty magazine
    cook: tuple = ()        # Royal Chef: (first, base, slowest) cooking seconds


TOWER_TROOPS = {
    "tower_princess": TowerTroop(
        "tower_princess", "Tower Princess", 1.0, 1.0, 0.8, 8.25, 0, "common",
        "Reliable arrows at air and ground: the all-rounder."),
    "cannoneer": TowerTroop(
        "cannoneer", "Cannoneer", 2616 / 3052, 320 / 109, 2.2, 8.25, 2300, "epic",
        "Slow, heavy cannonballs (3x damage) but less hp. Shreds tanks, "
        "struggles with swarms."),
    "dagger_duchess": TowerTroop(
        "dagger_duchess", "Dagger Duchess", 2768 / 3052, 107 / 109, 0.5, 8.25, 3400,
        "legendary",
        "Stockpiles 8 daggers and unleashes them in a flurry (0.5s), then "
        "reloads one at a time.", daggers=8, reload=0.9, empty_hit_speed=1.4),
    "royal_chef": TowerTroop(
        "royal_chef", "Royal Chef", 2703 / 3052, 1.0, 1.0, 8.25, 4200, "legendary",
        "Every 23s (up to 38s while his towers fight) throws a pancake: your "
        "highest-hp troop gains +1 level.", cook=(7.0, 23.0, 38.0)),
}

ORDER = ["tower_princess", "cannoneer", "dagger_duchess", "royal_chef"]
DEFAULT = "tower_princess"


def get(key):
    return TOWER_TROOPS.get(key, TOWER_TROOPS[DEFAULT])
