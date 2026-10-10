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
the troop). Then it starts charging again. Charges start full, so your first
copy is already evolved - just like the real game.

HEROES
------
A Hero is a special version of a card with a one-time activatable ability
(paid with extra elixir, using the ability button). Unlock it with shards,
then put the card in your deck's HERO SLOT (the third deck slot). Every copy
you play from that slot is the Hero. Max one Hero per deck.

Everything here mirrors the real game's Evolutions and Heroes as of the
Minion Giant update (Sept 2026); numbers are scaled into this game's units
the same way the cards are. The mechanics live in evo_engine.py.
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
    # ---- 1-cycle evolutions ----
    "barbarians": Evo("Evolved Barbarians", 1,
                      "+10% HP. Every hit gives them +30% attack and move speed for 5s."),
    "electro_dragon": Evo("Evolved Electro Dragon", 1,
                          "After its 3-target chain, the bolt keeps bouncing between "
                          "troops (33% less damage, no stun)."),
    "elite_barbarians": Evo("Evolved Elite Barbarians", 1,
                            "Throw Rage-tipped spears at ground units 3.5-5 tiles away, "
                            "leaving a trail of Rage (5s cooldown)."),
    "executioner": Evo("Evolved Executioner", 1,
                       "Enemies within 2.5 tiles when he throws take 75% extra axe "
                       "damage and are knocked back."),
    "goblin_giant": Evo("Evolved Goblin Giant", 1,
                        "Below half health, a Goblin jumps off his back every 2.2s."),
    "mega_knight": Evo("Evolved Mega Knight", 1,
                       "Every 2nd hit is an uppercut that launches the target 4 tiles "
                       "toward its own Crown Tower."),
    "minion_horde": Evo("Evolved Minion Horde", 1,
                        "Each Minion's first non-lethal hit makes it invincible and "
                        "untargetable for 3s (slower, but attacks faster)."),
    "pekka": Evo("Evolved P.E.K.K.A", 1,
                 "Heals after every kill (more for bigger victims), overhealing up "
                 "to +50% HP."),
    "royal_giant": Evo("Evolved Royal Giant", 1,
                       "Each shot's recoil damages enemies within 2.5 tiles and "
                       "knocks ground troops back 1 tile."),
    "royal_recruits": Evo("Evolved Royal Recruits", 1,
                          "Once their shield breaks they charge after 2.5 tiles, "
                          "hitting for double damage."),
    "witch": Evo("Evolved Witch", 1,
                 "Heals whenever one of HER skeletons dies, overhealing up to +24% HP."),
    "wizard": Evo("Evolved Wizard", 1,
                  "Fire Shield: when it breaks, enemies within 3 tiles take heavy "
                  "damage and are blown back 3 tiles."),
    # ---- 2-cycle evolutions ----
    "archers": Evo("Evolved Archers", 2,
                   "+1 range. Power Shot: targets 4-6 tiles away take +25% damage "
                   "from a piercing arrow."),
    "baby_dragon": Evo("Evolved Baby Dragon", 2,
                       "Tailwind (8x9 tiles): enemies 30% slower, allies 30% faster. "
                       "Lingers 2s after it dies."),
    "bats": Evo("Evolved Bats", 2,
                "+50% HP. Every bite heals them twice; they can overheal up to "
                "double HP."),
    "battle_ram": Evo("Evolved Battle Ram", 2,
                      "Charging bowls over troops in its path; bounces off buildings to "
                      "charge again. Leaves 2 Evolved Barbarians."),
    "bomber": Evo("Evolved Bomber", 2,
                  "His bomb bounces twice more, 2.5 tiles apart, exploding each time."),
    "cannon": Evo("Evolved Cannon", 2,
                  "On deploy, fires a 9-cannonball barrage (5+4 rows) that knocks "
                  "enemies back."),
    "dart_goblin": Evo("Evolved Dart Goblin", 2,
                       "Darts leave poison puddles that get stronger after 4 and 7 darts."),
    "firecracker": Evo("Evolved Firecracker", 2,
                       "Her firework and its sparks leave burning, slowing embers "
                       "behind them."),
    "furnace": Evo("Evolved Furnace", 2,
                   "While attacking she spawns Fire Spirits every 2.4s, to her sides."),
    "goblin_barrel": Evo("Evolved Goblin Barrel", 2,
                         "A second barrel lands on the mirrored tile in the other lane "
                         "with 3 Decoy Goblins."),
    "goblin_cage": Evo("Evolved Goblin Cage", 2,
                       "Drags the nearest ground troop within 3 tiles into the cage "
                       "and pummels it every second."),
    "goblin_drill": Evo("Evolved Goblin Drill", 2,
                        "At 66% and 33% health it resurfaces nearby, leaving a Goblin "
                        "each time."),
    "hunter": Evo("Evolved Hunter", 2,
                  "Every 5s nets the closest enemy within 4 tiles, trapping it for 3s "
                  "(nets pull fliers down)."),
    "ice_spirit": Evo("Evolved Ice Spirit", 2,
                      "Bigger blast; 3s later the same spot is hit and frozen again."),
    "inferno_dragon": Evo("Evolved Inferno Dragon", 2,
                          "Keeps its beam heat for 9s after a kill; after 20s of "
                          "burning a 4th stage doubles the damage."),
    "knight": Evo("Evolved Knight", 2,
                  "Takes 60% less damage while he isn't attacking."),
    "lumberjack": Evo("Evolved Lumberjack", 2,
                      "Longer Rage on death, and his untouchable ghost keeps chopping."),
    "mortar": Evo("Evolved Mortar", 2,
                  "Fires 1s faster and every shell drops a Goblin."),
    "musketeer": Evo("Evolved Musketeer", 2,
                     "3 sniper shots at troops or buildings anywhere ahead (6-30 "
                     "tiles, never Crown Towers) for 1.8x damage."),
    "princess": Evo("Evolved Princess", 2,
                    "Her first shot (then every 2nd) chills a big area 30% slower; "
                    "leaves a freezing patch when she falls."),
    "royal_ghost": Evo("Evolved Royal Ghost", 2,
                       "Each time he appears he summons 2 invisible Souldiers."),
    "royal_hogs": Evo("Evolved Royal Hogs", 2,
                      "They fly in! When they attack or get hurt they crash down, "
                      "damaging enemies below."),
    "skeleton_army": Evo("Evolved Skeleton Army", 2,
                         "Led by General Gerry: fallen skeletons fight on as untouchable "
                         "shadows until he falls."),
    "skeleton_barrel": Evo("Evolved Skeleton Barrel", 2,
                           "+25% HP, bigger blast, and TWO barrels of 7 Skeletons (one "
                           "dropped at 75% HP)."),
    "skeletons": Evo("Evolved Skeletons", 2,
                     "Every hit summons another Skeleton (up to 8 at once)."),
    "snowball": Evo("Evolved Giant Snowball", 2,
                    "Rolls 4.5 tiles, carrying the enemies it hit; slows 1s longer."),
    "tesla": Evo("Evolved Tesla", 2,
                 "Every time it pops up, a 6-tile shockwave damages and stuns."),
    "valkyrie": Evo("Evolved Valkyrie", 2,
                    "Each spin conjures a tornado that pulls enemies within 5.5 tiles "
                    "toward her."),
    "wall_breakers": Evo("Evolved Wall Breakers", 2,
                         "They explode when defeated too, and a Runner keeps going to "
                         "blow up again."),
    "zap": Evo("Evolved Zap", 2,
               "The zap lingers and strikes a second time, 0.5 tiles wider."),
    "electro_giant": Evo("Evolved Electro Giant", 2,
                         "Every 6s an energy pulse drains a level from every enemy "
                         "within 6 tiles (stacks)."),
}

HEROES = {
    "knight": Hero("Hero Knight", "Triumphant Taunt", 2,
                   "Taunts every enemy troop and building within 7.5 tiles and "
                   "raises a 260 shield for 5s.", 5.0),
    "giant": Hero("Hero Giant", "Heroic Hurl", 2,
                  "Grabs the highest-HP enemy troop within 2 tiles and throws it to "
                  "the other lane (stunned 2s; ground troops take landing damage)."),
    "mini_pekka": Hero("Hero Mini P.E.K.K.A", "Breakfast Boost", 1,
                       "Eats his pancakes: heals 30% and gains 1 level plus 1 per "
                       "pancake meter filled (fights fill them faster)."),
    "musketeer": Hero("Hero Musketeer", "Trusty Turret", 3,
                      "Sets up a sturdy turret 3 tiles ahead for 10s (blasts enemies "
                      "where it lands).", 10.0),
    "ice_golem": Hero("Hero Ice Golem", "Snowstorm", 2,
                      "Three icy blasts around him (4 tiles), each slowing enemies 30%."),
    "goblins": Hero("Hero Goblins", "Banner Brigade", 1,
                    "4 Goblins. When the last one falls their banner stays 5s - use "
                    "it to call 2 more Goblins.", 5.0),
    "valkyrie": Hero("Hero Valkyrie", "Wild Whirlwind", 3,
                     "Dashes up to 5.5 tiles spinning for 3.5s: hits all around 4x a "
                     "second, takes 15% less damage.", 3.5),
    "wizard": Hero("Hero Wizard", "Fiery Flight", 1,
                   "Takes off for 5s (+50% speed); his fireballs leave 2s fire "
                   "tornadoes.", 5.0),
    "mega_minion": Hero("Hero Mega Minion", "Warp Strike", 2,
                        "Warps onto the weakest enemy anywhere and smashes it, then "
                        "returns (after the kill or 3.5s)."),
    "barbarian_barrel": Hero("Hero Barbarian", "Re-Roll", 1,
                             "The Barbarian hops back in his barrel, rolls it again "
                             "(3 tiles) and heals 50%."),
    "magic_archer": Hero("Hero Magic Archer", "Decoy Dodge", 2,
                         "Teleports back leaving a decoy; his next shot is 3 extra-long "
                         "arrows."),
    "balloon": Hero("Hero Balloon", "Skeletrooper Drop", 2,
                    "Drops a Skeletrooper onto the nearest ground enemy within 6 "
                    "tiles; it lands hard and fights on."),
    "bowler": Hero("Hero Bowler", "Boulder Barrage", 2,
                   "After a 2.5s wind-up, lobs huge boulders up to 11.5 tiles for "
                   "7.3s."),
    "dark_prince": Hero("Hero Dark Prince", "Dismount", 3,
                        "Leaps off (slam on landing): his Rhino charges on at "
                        "buildings while he fights on foot."),
    "tombstone": Hero("Hero Tombstone", "Rise of the Queen", 5,
                      "The Tombstone crumbles and the Tomb Queen rises - a huge "
                      "building-hunter that bursts into skeletons."),
    "berserker": Hero("Hero Berserker", "Savage Survival", 3,
                      "4s frenzy: attacks every 0.2s, ultra fast, can't drop below 1 HP "
                      "(-75% vs Crown Towers).", 4.0),
    "ice_wizard": Hero("Hero Ice Wizard", "Frosty Fella", 2,
                       "His next hit on a slowed enemy builds a Snowman behind it that "
                       "freezes everything nearby."),
    "electro_wizard": Hero("Hero Electro Wizard", "Surging Strikes", 2,
                           "For 3s, zaps and stuns 2 enemies within 5 tiles every 0.5s "
                           "(-50% vs Crown Towers).", 3.0),
}

EVO_SLOTS = 2          # deck slots 1-2
HERO_SLOT = 2          # deck slot 3 (0-based index)


def evo_cards():
    return sorted(EVOS)


def hero_cards():
    return sorted(HEROES)
