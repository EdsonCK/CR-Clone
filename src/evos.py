"""
============================================================================
  EVOS.PY  --  Evolutions and Heroes (data + descriptions)
============================================================================

EVOLUTIONS
----------
An Evolution upgrades a card with an extra mechanic. Unlock it (Cards
screen, shards), then put the card in one of your deck's two EVO SLOTS (the
first two deck slots). In a match the card has to "cycle": each time you play
it normally it gains a charge, and once it has `cycles` charges the next copy
you play comes out EVOLVED (glowing purple card in your hand, purple aura on
the troop). Then it starts charging again.

HEROES
------
A Hero is a special version of a card with a one-time activatable ability
(like a Champion's, using the same ability button). Unlock it with shards,
then put the card in your deck's HERO SLOT (the third deck slot). Every copy
you play from that slot is the Hero. Max one Hero per deck.

The mechanics live in engine.py (search for "evo" / "hero"); this file only
holds the catalogue the game and the Cards screen read.
============================================================================
"""

from dataclasses import dataclass


@dataclass
class Evo:
    name: str
    cycles: int          # normal plays needed before the evolved copy
    desc: str


@dataclass
class Hero:
    name: str
    ability: str
    cost: int            # elixir to activate
    desc: str
    duration: float = 0.0


EVOS = {
    "knight": Evo("Evolved Knight", 2,
                  "Takes 60% less damage while he isn't swinging."),
    "archers": Evo("Evolved Archers", 2,
                   "Power Shot: arrows at targets 4+ tiles away deal 1.5x damage."),
    "skeletons": Evo("Evolved Skeletons", 2,
                     "Every hit summons another Skeleton (up to 8 at once)."),
    "barbarians": Evo("Evolved Barbarians", 1,
                      "Each hit enrages them: +35% attack and move speed for 3s."),
    "bats": Evo("Evolved Bats", 2,
                "Life-steal: heal by the damage they deal (overheal up to +50%)."),
    "bomber": Evo("Evolved Bomber", 1,
                  "His bomb bounces on twice more, exploding each time."),
    "valkyrie": Evo("Evolved Valkyrie", 2,
                    "Her spin creates a whirlwind that pulls enemies in."),
    "royal_giant": Evo("Evolved Royal Giant", 1,
                       "Recoil: each shot knocks back nearby enemy troops."),
    "mortar": Evo("Evolved Mortar", 2,
                  "Every shell drops a Goblin where it lands."),
    "tesla": Evo("Evolved Tesla", 2,
                 "Releases a stunning shockwave when deployed and when destroyed."),
    "wall_breakers": Evo("Evolved Wall Breakers", 2,
                         "After the blast, a runner keeps going and explodes again."),
    "zap": Evo("Evolved Zap", 2, "Zaps a second time half a second later."),
    "ice_spirit": Evo("Evolved Ice Spirit", 2,
                      "Freezes the area a second time 2 seconds later."),
    "witch": Evo("Evolved Witch", 1,
                 "Heals 80 HP whenever one of her skeletons dies nearby."),
    "battle_ram": Evo("Evolved Battle Ram", 1,
                      "Always arrives charged and runs 30% faster."),
    "electro_dragon": Evo("Evolved Electro Dragon", 2,
                          "Its chain jumps to 6 targets instead of 3."),
    "wizard": Evo("Evolved Wizard", 1,
                  "Gets a shield; when it breaks a fiery blast knocks enemies back."),
    "goblin_barrel": Evo("Evolved Goblin Barrel", 2,
                         "A decoy barrel lands nearby with 3 more Goblins."),
    "goblin_giant": Evo("Evolved Goblin Giant", 1,
                        "At half health two more Spear Goblins jump off to fight."),
    "pekka": Evo("Evolved P.E.K.K.A", 1,
                 "Heals 30% of her max HP whenever she defeats a troop."),
    "mega_knight": Evo("Evolved Mega Knight", 1,
                       "Uppercuts: his hits launch troops 2 tiles back."),
    "musketeer": Evo("Evolved Musketeer", 2,
                     "Sniper: her first 3 shots reach 3 tiles further for 1.5x damage."),
    "hunter": Evo("Evolved Hunter", 2,
                  "Fires a net at each new target, stunning it for 1.5s."),
    "executioner": Evo("Evolved Executioner", 1,
                       "Enemies that get close are knocked back by his axe."),
    "furnace": Evo("Evolved Furnace", 1,
                   "Spawns two Fire Spirits at a time."),
    "inferno_dragon": Evo("Evolved Inferno Dragon", 2,
                          "Keeps its beam heat when it switches targets."),
    "lumberjack": Evo("Evolved Lumberjack", 1,
                      "His death Rage lasts twice as long and covers more ground."),
    "dart_goblin": Evo("Evolved Dart Goblin", 2,
                       "Poison darts: every hit adds 3s of poison (stacks)."),
    "cannon": Evo("Evolved Cannon", 2,
                  "Fires a spinning barrage at everything around it on deploy."),
    "skeleton_army": Evo("Evolved Skeleton Army", 2,
                         "Led by a Skeleton General with a 300 HP shield; +50% HP."),
    "baby_dragon": Evo("Evolved Baby Dragon", 1,
                       "Tailwind: slows nearby enemies 30% and speeds up allies 15%."),
    "snowball": Evo("Evolved Snowball", 2,
                    "Rolls 3 tiles forward, dragging enemies with it."),
}

HEROES = {
    "knight": Hero("Hero Knight", "Triumphant Taunt", 1,
                   "Every enemy troop within 5 tiles targets him, and he takes "
                   "70% less damage for 4s.", 4.0),
    "giant": Hero("Hero Giant", "Heroic Hurl", 2,
                  "Picks up the biggest enemy troop within 3 tiles and hurls it "
                  "6 tiles away (300 damage)."),
    "mini_pekka": Hero("Hero Mini P.E.K.K.A", "Breakfast Boost", 1,
                       "Eats pancakes: heals 40% and permanently gains +1 level "
                       "(+10% HP and damage)."),
    "musketeer": Hero("Hero Musketeer", "Trusty Turret", 2,
                      "Sets up a turret next to her that shoots air and ground "
                      "for 15s.", 15.0),
    "ice_golem": Hero("Hero Ice Golem", "Snowstorm", 1,
                      "Freezes enemies within 3 tiles for 2s, then slows them "
                      "for 4s."),
    "goblins": Hero("Hero Goblins", "Banner Brigade", 2,
                    "Plants a war banner: 3 more Goblins join and every Goblin "
                    "nearby is enraged for 6s.", 6.0),
    "valkyrie": Hero("Hero Valkyrie", "Whirlwind", 1,
                     "Spins non-stop for 3s, hitting everything around her 4x a "
                     "second and pulling enemies in.", 3.0),
}

EVO_SLOTS = 2          # deck slots 1-2
HERO_SLOT = 2          # deck slot 3 (0-based index)


def evo_cards():
    return sorted(EVOS)


def hero_cards():
    return sorted(HEROES)
