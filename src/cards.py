"""
============================================================================
  CARDS.PY  --  The card database (data-driven)
============================================================================

Every card and every spawnable unit is defined here as plain data. To tweak
a card's balance, change its numbers. To add a new card, copy an existing one
and give it a new unique `key`.

FIELD GUIDE
-----------
key          : unique short id (lowercase, no spaces). Used everywhere.
name         : display name shown in-game.
elixir       : elixir cost to play.
category     : "troop" | "spell" | "building"
rarity       : cosmetic label ("common"/"rare"/"epic"/"legendary").
deployable   : True if it shows up in the deck builder. Sub-units that only
               get spawned by other cards are False.

--- Troop / unit combat stats ---
hp           : hit points.
damage       : damage per hit.
hit_speed    : SECONDS between attacks (lower = faster).
range        : attack range in tiles (melee ~1.2, ranged 5-6).
sight        : how far (tiles) it can "see" enemies to notice/chase them.
               It is automatically raised to at least `range`, so increasing a
               card's `range` also increases how far it engages. Set `sight`
               ABOVE `range` to make a unit react to enemies even earlier.
speed        : movement speed in tiles/second (use SPEED_* constants).
count        : how many copies deploy at once (e.g. 3 Goblins).
attacks      : what it can hit ->
                 "ground"     = ground units + buildings (NOT air)
                 "air_ground" = everything
                 "buildings"  = only buildings (win-condition troops)
flying       : True if it is an AIR unit (flies over the river; only
               air_ground attackers can hit it).
splash       : splash damage radius in tiles (0 = single target).

--- Special mechanics (all optional) ---
death_spawn  : (unit_key, count)      -> spawn units when this dies.
death_damage : (radius, damage)       -> explode when this dies.
spawner      : (unit_key, count, secs)-> building periodically spawns units.
lifetime     : seconds a building lives before decaying.
generates_elixir : (amount, seconds)  -> elixir collector.
charge       : True -> deals bonus damage on its first hit after moving.
charge_mult  : first-hit damage multiplier for chargers (default 2.0).
shield_hp    : an extra hp layer that must be broken first.
ramp         : True -> damage ramps up the longer it attacks (Inferno).
spawn_radius : how spread out multi-count / spawned units appear (tiles).

--- Spell fields (category == "spell") ---
spell_radius : area of effect radius in tiles.
spell_damage : damage to troops in the area.
tower_damage : damage to towers (spells hit towers for less; defaults to
               spell_damage if omitted).
stun         : seconds targets are stunned (can't act).
slow         : (factor, seconds) e.g. (0.5, 3) = half speed for 3s.
freeze       : seconds targets are frozen solid.
dot          : True -> spell_damage is dealt per second over `duration`.
duration     : seconds an effect lasts (poison, rage zone, freeze area).
rage         : True -> a friendly zone that speeds up units in it.
rolling      : True -> a projectile that rolls forward (The Log).
knockback    : tiles that troops get pushed back.
============================================================================
"""

import random
from dataclasses import dataclass, field
from typing import Optional, Tuple

from config import (SPEED_SLOW, SPEED_MEDIUM, SPEED_FAST, SPEED_VERY_FAST,
                    DECK_SIZE)


@dataclass
class CardDef:
    key: str
    name: str
    elixir: int
    category: str = "troop"
    rarity: str = "common"
    deployable: bool = True

    # combat
    hp: int = 100
    damage: int = 50
    hit_speed: float = 1.0
    range: float = 1.2
    sight: float = 5.5
    speed: float = SPEED_MEDIUM
    count: int = 1
    attacks: str = "ground"
    flying: bool = False
    splash: float = 0.0

    # mechanics
    death_spawn: Optional[Tuple[str, int]] = None
    death_damage: Optional[Tuple[float, int]] = None
    spawner: Optional[Tuple[str, int, float]] = None
    lifetime: float = 0.0
    generates_elixir: Optional[Tuple[float, float]] = None
    charge: bool = False
    charge_mult: float = 2.0
    shield_hp: int = 0
    ramp: bool = False
    pellets: int = 0            # >0: shotgun attack, this many projectiles...
    pellet_spread: float = 34.0 # ...fanned over this many degrees (Hunter)
    kamikaze: bool = False      # dies on its (single) attack: spirits, wall
                                #   breakers. Explosion uses death_damage stats.
    pierce: bool = False        # projectile flies its FULL range and damages
                                #   every enemy along the path (splash value is
                                #   reused as the path width). No homing.
    back_riders: Optional[Tuple[str, int]] = None  # (unit_key, count) riders
                                #   that shoot from this unit's back while it
                                #   lives (Goblin Giant's spear goblins).
    chain: Optional[Tuple[int, float]] = None
                                # (max_targets, jump_range) lightning that arcs
                                #   from target to target; never hits the same
                                #   target twice per attack (Electro Spirit 12,
                                #   Electro Dragon 4).
    beam: bool = False          # attack renders as an instant full-length beam
                                #   (Tesla) - no projectile travel time.
    reflect: Optional[Tuple[float, int, float]] = None
                                # (radius, damage, stun) zap released when this
                                #   unit TAKES damage (Electro Giant).
    heal_on_attack: Optional[Tuple[float, int]] = None
                                # (radius, hp) heals nearby allies every time
                                #   this unit attacks (Battle Healer).
    death_gives_elixir: float = 0.0
                                # elixir gifted to the OPPONENT when this dies
                                #   (Elixir Golem chain).
    splash_self: bool = False   # splash is centered on the ATTACKER, not the
                                #   target (Valkyrie's spin attack).
    companion: Optional[Tuple[str, int]] = None  # extra unit spawned alongside
                                #   this one on deploy (Goblinstein's Monster).

    # -- champions (activatable ability via the ability button) --
    is_champion: bool = False
    ability_name: str = ""
    ability_type: str = ""      # cloak|bomb|summon|dash|skeletons|immune|
                                #   chain_stun|shield_dash
    ability_cost: int = 0       # extra elixir to activate
    ability_cooldown: float = 8.0
    ability_duration: float = 0.0
    ability_radius: float = 0.0
    ability_value: float = 0.0  # generic magnitude (dmg / shield / count / mult)
    spawn_radius: float = 0.7
    spawn_damage: Optional[Tuple[float, int]] = None   # (radius, dmg) on deploy
    deploy_anywhere: bool = False                      # can be placed on any tile
    death_slow: Optional[Tuple[float, float]] = None   # (factor, secs) on death

    # spell
    spell_radius: float = 0.0
    spell_damage: int = 0
    tower_damage: Optional[int] = None
    stun: float = 0.0
    slow: Optional[Tuple[float, float]] = None
    freeze: float = 0.0
    dot: bool = False
    duration: float = 0.0
    rage: bool = False
    rolling: bool = False
    knockback: float = 0.0
    spawn_troops: Optional[Tuple[str, int]] = None  # spell drops these units
    pull: float = 0.0                               # tornado pull strength
    graveyard: bool = False                         # spawn skeletons over an area

    def tower_dmg(self) -> int:
        return self.tower_damage if self.tower_damage is not None else self.spell_damage


# Convenience shortcuts
G = "ground"
AG = "air_ground"
B = "buildings"


# ===========================================================================
#  THE ROSTER  --  ~45 iconic cards + the sub-units they spawn
# ===========================================================================
_CARD_LIST = [

    # -------------------- SMALL / CHEAP TROOPS --------------------
    CardDef("skeletons", "Skeletons", 1, rarity="common",
            hp=32, damage=32, hit_speed=1.0, range=0.9, speed=SPEED_FAST,
            count=3, attacks=G, spawn_radius=0.6),
    CardDef("ice_spirit", "Ice Spirit", 1, rarity="common",
            hp=70, damage=42, hit_speed=1.0, range=0.9, speed=SPEED_VERY_FAST,
            count=1, attacks=AG, freeze=1.0, kamikaze=True,
            death_damage=(1.5, 42)),   # explodes on attack: one hit, then gone
    CardDef("fire_spirit", "Fire Spirit", 1, rarity="common",
            hp=70, damage=120, hit_speed=1.0, range=1.2, speed=SPEED_VERY_FAST,
            count=1, attacks=AG, kamikaze=True,
            death_damage=(1.5, 120)),  # explodes on attack: one hit, then gone
    CardDef("goblins", "Goblins", 2, rarity="common",
            hp=79, damage=47, hit_speed=1.1, range=0.9, speed=SPEED_VERY_FAST,
            count=3, attacks=G, spawn_radius=0.7),
    CardDef("spear_goblins", "Spear Goblins", 2, rarity="common",
            hp=52, damage=32, hit_speed=1.1, range=5.0, speed=SPEED_VERY_FAST,
            count=3, attacks=AG, spawn_radius=0.7),
    CardDef("bats", "Bats", 2, rarity="common",
            hp=32, damage=32, hit_speed=1.1, range=0.9, speed=SPEED_FAST,
            count=5, attacks=AG, flying=True, spawn_radius=0.9),
    CardDef("skeleton_barrel", "Skeleton Barrel", 3, rarity="common",
            hp=310, damage=0, hit_speed=1.0, range=0.9, speed=SPEED_MEDIUM,
            count=1, attacks=B, flying=True,
            death_spawn=("skeleton", 6)),

    # -------------------- CORE GROUND TROOPS --------------------
    CardDef("knight", "Knight", 3, rarity="common",
            hp=690, damage=79, hit_speed=1.1, range=1.2, speed=SPEED_MEDIUM,
            attacks=G),
    CardDef("archers", "Archers", 3, rarity="common",
            hp=125, damage=42, hit_speed=1.2, range=5.5, speed=SPEED_MEDIUM,
            count=2, attacks=AG, spawn_radius=0.8),
    CardDef("bomber", "Bomber", 3, rarity="common",
            hp=130, damage=110, hit_speed=1.9, range=4.5, speed=SPEED_MEDIUM,
            count=1, attacks=G, splash=1.5),
    CardDef("valkyrie", "Valkyrie", 4, rarity="rare",
            hp=880, damage=126, hit_speed=1.5, range=1.2, speed=SPEED_MEDIUM,
            attacks=G, splash=1.3, splash_self=True),   # 360 spin around her
    CardDef("mini_pekka", "Mini P.E.K.K.A", 4, rarity="rare",
            hp=642, damage=340, hit_speed=1.6, range=1.2, speed=SPEED_FAST,
            attacks=G),
    CardDef("musketeer", "Musketeer", 4, rarity="rare",
            hp=340, damage=120, hit_speed=1.1, range=6.0, speed=SPEED_MEDIUM,
            attacks=AG),
    CardDef("barbarians", "Barbarians", 5, rarity="common",
            hp=262, damage=88, hit_speed=1.4, range=1.2, speed=SPEED_MEDIUM,
            count=4, attacks=G, spawn_radius=1.1),
    CardDef("elite_barbarians", "Elite Barbarians", 6, rarity="common",
            hp=524, damage=180, hit_speed=1.7, range=1.2, speed=SPEED_FAST,
            count=2, attacks=G, spawn_radius=1.0),
    CardDef("wizard", "Wizard", 5, rarity="rare",
            hp=340, damage=130, hit_speed=1.4, range=5.5, speed=SPEED_MEDIUM,
            attacks=AG, splash=1.4),
    CardDef("witch", "Witch", 5, rarity="epic",
            hp=460, damage=90, hit_speed=1.1, range=5.0, speed=SPEED_MEDIUM,
            attacks=AG, splash=1.2, spawner=("skeleton", 4, 7.0)),
            # witch: 4 skeletons every 7s
    CardDef("pekka", "P.E.K.K.A", 7, rarity="epic",
            hp=2600, damage=510, hit_speed=1.8, range=1.2, speed=SPEED_SLOW,
            attacks=G),
    CardDef("prince", "Prince", 5, rarity="epic",
            hp=980, damage=245, hit_speed=1.4, range=1.6, speed=SPEED_MEDIUM,
            attacks=G, charge=True, charge_mult=2.0),
    CardDef("dark_prince", "Dark Prince", 4, rarity="epic",
            hp=680, damage=140, hit_speed=1.3, range=1.3, speed=SPEED_MEDIUM,
            attacks=G, splash=1.2, charge=True, shield_hp=180),
    CardDef("giant_skeleton", "Giant Skeleton", 6, rarity="epic",
            hp=2100, damage=140, hit_speed=1.5, range=1.2, speed=SPEED_MEDIUM,
            attacks=G, death_damage=(2.5, 640)),
    CardDef("lumberjack", "Lumberjack", 4, rarity="legendary",
            hp=660, damage=175, hit_speed=0.7, range=1.2, speed=SPEED_VERY_FAST,
            attacks=G, death_spawn=("rage_pickup", 0)),  # rage handled on death
    CardDef("bandit", "Bandit", 3, rarity="legendary",
            hp=750, damage=160, hit_speed=1.0, range=1.2, speed=SPEED_VERY_FAST,
            attacks=G, charge=True, charge_mult=2.0),

    # -------------------- WIN CONDITIONS (target buildings) --------------------
    CardDef("giant", "Giant", 5, rarity="rare",
            hp=2200, damage=120, hit_speed=1.5, range=1.2, speed=SPEED_SLOW,
            attacks=B),   # tanky, but now clearly below P.E.K.K.A (2600 hp)
    CardDef("hog_rider", "Hog Rider", 4, rarity="rare",
            hp=1000, damage=175, hit_speed=1.6, range=1.2, speed=SPEED_VERY_FAST,
            attacks=B),
    CardDef("royal_giant", "Royal Giant", 6, rarity="common",
            hp=2100, damage=180, hit_speed=1.7, range=5.0, speed=SPEED_SLOW,
            attacks=B),
    CardDef("balloon", "Balloon", 5, rarity="epic",
            hp=1050, damage=600, hit_speed=2.5, range=1.2, speed=SPEED_MEDIUM,
            attacks=B, flying=True, death_damage=(2.0, 200)),
    CardDef("golem", "Golem", 8, rarity="epic",
            hp=4200, damage=280, hit_speed=2.5, range=1.2, speed=SPEED_SLOW,
            attacks=B, death_damage=(2.0, 260), death_spawn=("golemite", 2)),

    # -------------------- AIR TROOPS --------------------
    CardDef("minions", "Minions", 3, rarity="common",
            hp=90, damage=42, hit_speed=1.0, range=2.0, speed=SPEED_FAST,
            count=3, attacks=AG, flying=True, spawn_radius=0.9),
    CardDef("minion_horde", "Minion Horde", 5, rarity="common",
            hp=90, damage=42, hit_speed=1.0, range=2.0, speed=SPEED_FAST,
            count=6, attacks=AG, flying=True, spawn_radius=1.3),
    CardDef("mega_minion", "Mega Minion", 3, rarity="rare",
            hp=350, damage=150, hit_speed=1.5, range=1.8, speed=SPEED_FAST,
            attacks=AG, flying=True),
    CardDef("baby_dragon", "Baby Dragon", 4, rarity="epic",
            hp=800, damage=100, hit_speed=1.5, range=3.0, speed=SPEED_FAST,
            attacks=AG, flying=True, splash=1.4),
    CardDef("inferno_dragon", "Inferno Dragon", 4, rarity="legendary",
            hp=1000, damage=45, hit_speed=0.4, range=3.5, speed=SPEED_FAST,
            attacks=AG, flying=True, ramp=True),

    # -------------------- SUPPORT / SPECIALIST --------------------
    CardDef("dart_goblin", "Dart Goblin", 3, rarity="rare",
            hp=115, damage=60, hit_speed=0.7, range=6.0, speed=SPEED_VERY_FAST,
            attacks=AG),   # outranges Cannon, but NOT Tesla (see tesla range)
    CardDef("princess", "Princess", 3, rarity="legendary",
            hp=130, damage=140, hit_speed=3.0, range=9.0, speed=SPEED_MEDIUM,
            attacks=AG, splash=2.0),
    CardDef("electro_wizard", "Electro Wizard", 4, rarity="legendary",
            hp=340, damage=100, hit_speed=1.8, range=5.0, speed=SPEED_MEDIUM,
            attacks=AG, stun=0.5, death_spawn=None),
    CardDef("ice_wizard", "Ice Wizard", 3, rarity="legendary",
            hp=310, damage=55, hit_speed=1.5, range=5.5, speed=SPEED_MEDIUM,
            attacks=AG, splash=1.2, slow=(0.65, 1.5)),
    CardDef("three_musketeers", "Three Musketeers", 9, rarity="rare",
            hp=340, damage=120, hit_speed=1.1, range=6.0, speed=SPEED_MEDIUM,
            count=3, attacks=AG, spawn_radius=1.4),
    CardDef("sparky", "Sparky", 6, rarity="legendary",
            hp=1200, damage=1050, hit_speed=5.0, range=5.0, speed=SPEED_SLOW,
            attacks=G, splash=2.0, charge=True, charge_mult=1.0),
            # nerfed: 1300dmg/4s -> 1050dmg/5s; still one-shots most troops

    # -------------------- BUILDINGS --------------------
    CardDef("cannon", "Cannon", 3, category="building", rarity="common",
            hp=742, damage=127, hit_speed=0.9, range=5.5, attacks=G,
            lifetime=30.0),
    CardDef("tesla", "Tesla", 4, category="building", rarity="common",
            hp=800, damage=132, hit_speed=1.1, range=6.8, attacks=AG,
            lifetime=40.0, beam=True),
            # long zap reach: Dart Goblin can NOT outrange it. beam=True ->
            # instant full-length bolt, no travelling projectile
    CardDef("inferno_tower", "Inferno Tower", 5, category="building",
            rarity="rare", hp=1600, damage=40, hit_speed=0.4, range=6.0,
            attacks=AG, ramp=True, lifetime=40.0),
    CardDef("bomb_tower", "Bomb Tower", 4, category="building", rarity="rare",
            hp=1050, damage=180, hit_speed=1.6, range=6.0, attacks=G,
            splash=1.5, lifetime=35.0, death_damage=(2.0, 250)),
    CardDef("mortar", "Mortar", 4, category="building", rarity="common",
            hp=800, damage=260, hit_speed=5.0, range=11.5, attacks=B,
            splash=1.5, lifetime=30.0),
    CardDef("xbow", "X-Bow", 6, category="building", rarity="epic",
            hp=1000, damage=26, hit_speed=0.3, range=11.5, attacks=B,
            lifetime=40.0),
    CardDef("tombstone", "Tombstone", 3, category="building", rarity="rare",
            hp=400, damage=0, range=0, attacks=G, lifetime=30.0,
            spawner=("skeleton", 2, 3.5), death_spawn=("skeleton", 4)),
            # tombstone: 2 skeletons every 3.5s, 4 on death
    CardDef("goblin_hut", "Goblin Hut", 5, category="building", rarity="rare",
            hp=1000, damage=0, range=0, attacks=G, lifetime=50.0,
            spawner=("spear_goblin", 1, 4.75)),
            # goblin hut: 1 spear goblin every 4.75s
    CardDef("barbarian_hut", "Barbarian Hut", 7, category="building",
            rarity="rare", hp=1300, damage=0, range=0, attacks=G,
            lifetime=50.0, spawner=("barbarian", 3, 15.0)),
            # barb hut: 3 barbarians every 15s
    CardDef("furnace", "Furnace", 4, category="building", rarity="rare",
            hp=600, damage=0, range=0, attacks=G, lifetime=40.0,
            spawner=("fire_spirit", 2, 10.0)),
            # furnace: 2 fire spirits every 10s
    CardDef("elixir_collector", "Elixir Collector", 6, category="building",
            rarity="rare", hp=600, damage=0, range=0, attacks=G,
            lifetime=70.0, generates_elixir=(1.0, 8.5)),

    # -------------------- SPELLS --------------------
    CardDef("zap", "Zap", 2, category="spell", rarity="common",
            spell_radius=2.5, spell_damage=75, tower_damage=45, stun=0.5),
    CardDef("the_log", "The Log", 2, category="spell", rarity="legendary",
            spell_radius=2.0, spell_damage=120, tower_damage=48,
            rolling=True, knockback=1.5),
    CardDef("arrows", "Arrows", 3, category="spell", rarity="common",
            spell_radius=4.0, spell_damage=115, tower_damage=46),
    CardDef("fireball", "Fireball", 4, category="spell", rarity="rare",
            spell_radius=2.5, spell_damage=340, tower_damage=110,
            knockback=1.0),
    CardDef("rage", "Rage", 2, category="spell", rarity="epic",
            spell_radius=4.0, rage=True, duration=8.0),
    CardDef("freeze", "Freeze", 4, category="spell", rarity="epic",
            spell_radius=3.0, spell_damage=60, tower_damage=24, freeze=4.0),
    CardDef("poison", "Poison", 4, category="spell", rarity="epic",
            spell_radius=3.5, spell_damage=55, tower_damage=22, dot=True,
            duration=8.0, slow=(0.85, 0.5)),
    CardDef("rocket", "Rocket", 6, category="spell", rarity="rare",
            spell_radius=2.0, spell_damage=700, tower_damage=280,
            knockback=1.0),
    CardDef("lightning", "Lightning", 6, category="spell", rarity="epic",
            spell_radius=3.5, spell_damage=560, tower_damage=225, stun=0.5),

    # ==================== EXPANSION SET (v0.1.3) ====================
    # -------- swarms & fast cheap troops --------
    CardDef("skeleton_army", "Skeleton Army", 4, rarity="epic",
            hp=32, damage=32, hit_speed=1.0, range=0.9, speed=SPEED_FAST,
            count=15, attacks=G, spawn_radius=1.7),
    CardDef("guards", "Guards", 3, rarity="epic",
            hp=75, damage=60, hit_speed=1.1, range=0.9, speed=SPEED_MEDIUM,
            count=3, attacks=G, shield_hp=150, spawn_radius=0.9),
    CardDef("zappies", "Zappies", 4, rarity="rare",
            hp=140, damage=48, hit_speed=1.8, range=4.5, speed=SPEED_MEDIUM,
            count=3, attacks=AG, stun=0.4, spawn_radius=1.0),
    # -------- ranged / splash specialists --------
    CardDef("hunter", "Hunter", 4, rarity="epic",
            hp=650, damage=45, hit_speed=1.5, range=4.0, sight=6.0,
            speed=SPEED_MEDIUM, attacks=AG,
            pellets=7, pellet_spread=34.0),
            # shotgun: 7 pellets fanned 34 deg. At max range only the middle
            # pellets connect; point-blank all 7 hit (brutal up close).
    CardDef("executioner", "Executioner", 5, rarity="epic",
            hp=650, damage=110, hit_speed=1.6, range=5.0, speed=SPEED_MEDIUM,
            attacks=AG, splash=1.6, pierce=True),
            # axe pierces: full flight, damages everything along the line
    CardDef("bowler", "Bowler", 5, rarity="epic",
            hp=940, damage=145, hit_speed=2.5, range=4.5, speed=SPEED_SLOW,
            attacks=G, splash=1.4, knockback=0.6, pierce=True),
            # boulder rolls its full range, hitting and knocking back all
    CardDef("magic_archer", "Magic Archer", 4, rarity="legendary",
            hp=340, damage=75, hit_speed=1.1, range=6.3, sight=8.0,
            speed=SPEED_MEDIUM, attacks=AG, splash=0.8, pierce=True),
            # arrow pierces: flies full range, hits every enemy on the line.
            # Long range, but can NOT snipe Princess Towers (tower reach wins).
    CardDef("night_witch", "Night Witch", 4, rarity="legendary",
            hp=560, damage=150, hit_speed=1.4, range=1.2, speed=SPEED_MEDIUM,
            attacks=G, spawner=("bat", 2, 5.0), death_spawn=("bat", 2)),
            # night witch: 2 bats every 5s, 2 bats on death
    # -------- air --------
    CardDef("flying_machine", "Flying Machine", 4, rarity="rare",
            hp=340, damage=96, hit_speed=1.1, range=6.0, speed=SPEED_FAST,
            attacks=AG, flying=True),
    CardDef("electro_dragon", "Electro Dragon", 5, rarity="epic",
            hp=640, damage=100, hit_speed=1.9, range=3.5, speed=SPEED_MEDIUM,
            attacks=AG, flying=True, stun=0.5, chain=(4, 2.0)),
            # bolt chains up to 4 targets (2-tile jumps), no repeats
    CardDef("lava_hound", "Lava Hound", 7, rarity="legendary",
            hp=3000, damage=40, hit_speed=1.3, range=2.5, speed=SPEED_SLOW,
            attacks=B, flying=True, death_spawn=("lava_pup", 6)),
    # -------- tanks / bruisers --------
    CardDef("mega_knight", "Mega Knight", 7, rarity="legendary",
            hp=2700, damage=170, hit_speed=1.7, range=1.2, speed=SPEED_MEDIUM,
            attacks=G, splash=1.6, charge=True, charge_mult=1.8,
            spawn_damage=(2.5, 240)),   # slams the ground where it lands
    CardDef("goblin_giant", "Goblin Giant", 6, rarity="epic",
            hp=2400, damage=110, hit_speed=1.7, range=1.2, speed=SPEED_MEDIUM,
            attacks=B, death_spawn=("spear_goblin", 2),
            back_riders=("spear_goblin", 2)),
            # 2 spear goblins ride on his back and shoot while he's alive,
            # then hop off as real units when he dies (death_spawn)
    CardDef("cannon_cart", "Cannon Cart", 5, rarity="epic",
            hp=600, damage=130, hit_speed=1.1, range=5.0, speed=SPEED_MEDIUM,
            attacks=G, shield_hp=440),   # shielded mobile cannon
    CardDef("ice_golem", "Ice Golem", 2, rarity="rare",
            hp=1200, damage=42, hit_speed=1.5, range=1.2, speed=SPEED_SLOW,
            attacks=B, death_damage=(2.0, 60), death_slow=(0.6, 2.0)),
    # -------- win conditions --------
    CardDef("miner", "Miner", 3, rarity="legendary",
            hp=900, damage=75, hit_speed=1.2, range=1.2, speed=SPEED_FAST,
            attacks=G, deploy_anywhere=True),
            # tunnels anywhere; chip damage only (nerfed from 120 - he's a
            # 3-elixir unit you can drop directly on a tower)
    CardDef("battle_ram", "Battle Ram", 4, rarity="rare",
            hp=520, damage=110, hit_speed=1.5, range=1.3, speed=SPEED_VERY_FAST,
            attacks=B, charge=True, charge_mult=2.0, death_spawn=("barbarian", 2)),
    CardDef("wall_breakers", "Wall Breakers", 2, rarity="epic",
            hp=140, damage=180, hit_speed=1.0, range=1.0, speed=SPEED_VERY_FAST,
            count=2, attacks=B, kamikaze=True,
            death_damage=(1.5, 180), spawn_radius=0.8),
            # kamikaze: each barrel explodes on its single attack

    # -------- electro & support pack (v0.1.9) --------
    CardDef("electro_spirit", "Electro Spirit", 1, rarity="common",
            hp=90, damage=39, hit_speed=1.0, range=1.2, speed=SPEED_VERY_FAST,
            count=1, attacks=AG, kamikaze=True, stun=0.5,
            chain=(12, 2.0)),
            # kamikaze zap that arcs up to 12 targets (2-tile jumps),
            # never the same target twice
    CardDef("electro_giant", "Electro Giant", 7, rarity="epic",
            hp=2500, damage=130, hit_speed=1.7, range=1.2, speed=SPEED_SLOW,
            attacks=B, reflect=(3.0, 60, 0.5)),
            # counter-zap: anything within 3 tiles gets damaged+stunned
            # whenever he takes a hit
    CardDef("battle_healer", "Battle Healer", 4, rarity="rare",
            hp=810, damage=70, hit_speed=1.5, range=1.6, speed=SPEED_MEDIUM,
            attacks=G, heal_on_attack=(3.0, 55)),
            # heals all nearby allies with every swing
    CardDef("elixir_golem", "Elixir Golem", 3, rarity="rare",
            hp=1400, damage=150, hit_speed=1.3, range=1.2, speed=SPEED_SLOW,
            attacks=B, death_spawn=("elixir_golemite", 2)),
            # splits twice; the final blobs feed the enemy elixir when killed

    # -------- expansion spells --------
    CardDef("goblin_barrel", "Goblin Barrel", 3, category="spell", rarity="epic",
            spawn_troops=("goblin", 3)),
    CardDef("barbarian_barrel", "Barbarian Barrel", 2, category="spell",
            rarity="epic", spell_radius=1.6, spell_damage=120, tower_damage=48,
            rolling=True, knockback=1.2, spawn_troops=("barbarian", 1)),
    CardDef("snowball", "Giant Snowball", 2, category="spell", rarity="common",
            spell_radius=2.5, spell_damage=80, tower_damage=32,
            knockback=1.2, slow=(0.65, 2.0)),
    CardDef("earthquake", "Earthquake", 3, category="spell", rarity="rare",
            spell_radius=3.5, spell_damage=36, tower_damage=44, dot=True,
            duration=3.0, slow=(0.85, 0.4)),   # shreds buildings
    CardDef("tornado", "Tornado", 3, category="spell", rarity="epic",
            spell_radius=3.5, spell_damage=45, tower_damage=18, pull=2.4,
            duration=1.0),
    CardDef("graveyard", "Graveyard", 5, category="spell", rarity="legendary",
            spell_radius=3.5, graveyard=True, duration=8.0),

    # ==================== CHAMPIONS (v0.2.0) ====================
    # Each has an activatable ability (yellow button in-match). Only ONE
    # champion may be in a deck. Abilities cost extra elixir + have a cooldown.
    CardDef("mighty_miner", "Mighty Miner", 4, rarity="champion",
            hp=1400, damage=57, hit_speed=0.6, range=1.2, speed=SPEED_FAST,
            attacks=G, deploy_anywhere=True, ramp=True, is_champion=True,
            ability_name="Mine Bomb", ability_type="bomb", ability_cost=1,
            ability_cooldown=6.0, ability_duration=1.4, ability_radius=2.6,
            ability_value=520),
    CardDef("archer_queen", "Archer Queen", 5, rarity="champion",
            hp=500, damage=126, hit_speed=1.2, range=5.0, speed=SPEED_MEDIUM,
            attacks=AG, is_champion=True,
            ability_name="Cloaking Cape", ability_type="cloak", ability_cost=1,
            ability_cooldown=8.0, ability_duration=3.0, ability_value=2.0),
    CardDef("little_prince", "Little Prince", 3, rarity="champion",
            hp=560, damage=60, hit_speed=1.3, range=6.0, speed=SPEED_MEDIUM,
            attacks=AG, ramp=True, is_champion=True,
            ability_name="Call the Guardian", ability_type="summon",
            ability_cost=3, ability_cooldown=12.0, ability_value=1),
    CardDef("golden_knight", "Golden Knight", 4, rarity="champion",
            hp=1400, damage=170, hit_speed=1.2, range=1.2, speed=SPEED_FAST,
            attacks=G, is_champion=True,
            ability_name="Dashing Dash", ability_type="dash", ability_cost=1,
            ability_cooldown=7.0, ability_radius=1.7, ability_value=220),
    CardDef("skeleton_king", "Skeleton King", 4, rarity="champion",
            hp=1800, damage=176, hit_speed=1.4, range=1.2, speed=SPEED_MEDIUM,
            attacks=G, splash=1.3, is_champion=True,
            ability_name="Soul Summoning", ability_type="skeletons",
            ability_cost=2, ability_cooldown=10.0, ability_value=6),
    CardDef("monk", "Monk", 5, rarity="champion",
            hp=1900, damage=190, hit_speed=1.5, range=1.2, speed=SPEED_MEDIUM,
            attacks=G, is_champion=True,
            ability_name="Pancake", ability_type="immune", ability_cost=2,
            ability_cooldown=9.0, ability_duration=1.6, ability_radius=3.0,
            ability_value=160),
    CardDef("goblinstein", "Goblinstein", 6, rarity="champion",
            hp=1200, damage=120, hit_speed=1.4, range=4.5, speed=SPEED_MEDIUM,
            attacks=AG, is_champion=True, companion=("goblin_monster", 1),
            ability_name="Electrify", ability_type="chain_stun", ability_cost=1,
            ability_cooldown=7.0, ability_value=6),
    CardDef("boss_bandit", "Boss Bandit", 5, rarity="champion",
            hp=1600, damage=200, hit_speed=1.3, range=1.2, speed=SPEED_FAST,
            attacks=G, charge=True, charge_mult=2.0, is_champion=True,
            ability_name="Boss Dash", ability_type="shield_dash", ability_cost=1,
            ability_cooldown=7.0, ability_radius=1.8, ability_value=400),

    # ==================== NON-DEPLOYABLE SUB-UNITS ====================
    # These are spawned by other cards; they don't appear in the deck builder.
    CardDef("skeleton", "Skeleton", 0, deployable=False,
            hp=32, damage=32, hit_speed=1.0, range=0.9, speed=SPEED_FAST,
            attacks=G),
    CardDef("goblin", "Goblin", 0, deployable=False,
            hp=79, damage=47, hit_speed=1.1, range=0.9, speed=SPEED_VERY_FAST,
            attacks=G),
    CardDef("spear_goblin", "Spear Goblin", 0, deployable=False,
            hp=52, damage=32, hit_speed=1.1, range=5.0, speed=SPEED_VERY_FAST,
            attacks=AG),
    CardDef("barbarian", "Barbarian", 0, deployable=False,
            hp=262, damage=88, hit_speed=1.4, range=1.2, speed=SPEED_MEDIUM,
            attacks=G),
    # NOTE: Furnace spawns the deployable "fire_spirit" card above, so no
    # separate sub-unit entry is needed for it (that would collide on the key).
    CardDef("golemite", "Golemite", 0, deployable=False,
            hp=1050, damage=90, hit_speed=2.5, range=1.2, speed=SPEED_SLOW,
            attacks=B, death_damage=(1.5, 90)),
    CardDef("bat", "Bat", 0, deployable=False,
            hp=32, damage=32, hit_speed=1.1, range=0.9, speed=SPEED_FAST,
            attacks=AG, flying=True),
    CardDef("lava_pup", "Lava Pup", 0, deployable=False,
            hp=100, damage=45, hit_speed=1.3, range=2.0, speed=SPEED_FAST,
            attacks=AG, flying=True),
    CardDef("elixir_golemite", "Elixir Golemite", 0, deployable=False,
            hp=500, damage=70, hit_speed=1.3, range=1.2, speed=SPEED_SLOW,
            attacks=B, death_spawn=("elixir_blob", 2)),
    CardDef("elixir_blob", "Elixir Blob", 0, deployable=False,
            hp=190, damage=40, hit_speed=1.3, range=1.2, speed=SPEED_SLOW,
            attacks=B, death_gives_elixir=1.0),
    CardDef("royal_guardian", "Guardian", 0, deployable=False,
            hp=900, damage=90, hit_speed=1.3, range=1.2, speed=SPEED_MEDIUM,
            attacks=G, shield_hp=250),   # Little Prince's summoned guardian
    CardDef("goblin_monster", "Goblin Monster", 0, deployable=False,
            hp=1100, damage=150, hit_speed=1.5, range=1.2, speed=SPEED_MEDIUM,
            attacks=G),   # Goblinstein's melee companion
]

# key -> CardDef lookup
CARDS = {c.key: c for c in _CARD_LIST}

# The list shown in the deck builder (only real, playable cards).
DEPLOYABLE_CARDS = [c for c in _CARD_LIST if c.deployable]

# A reasonable default deck for a new player and for the AI.
DEFAULT_PLAYER_DECK = [
    "knight", "archers", "musketeer", "fireball",
    "hog_rider", "cannon", "goblins", "zap",
]

DEFAULT_AI_DECK = [
    "giant", "musketeer", "mini_pekka", "arrows",
    "baby_dragon", "minions", "knight", "fireball",
]

# Preset "archetype" decks the AI can use, chosen on the AI Deck screen.
# "Random" and "Custom" are handled separately (see game.py / random_deck()).
AI_DECK_PRESETS = {
    "Hog Cycle":      ["hog_rider", "ice_spirit", "skeletons", "cannon",
                       "musketeer", "fireball", "the_log", "ice_golem"],
    "P.E.K.K.A Bridge": ["pekka", "battle_ram", "bandit", "electro_wizard",
                         "magic_archer", "minions", "zap", "poison"],
    "Golem Beatdown": ["golem", "baby_dragon", "night_witch", "mega_minion",
                       "lightning", "tornado", "elixir_collector", "lumberjack"],
    "Classic":        ["giant", "musketeer", "minions", "cannon",
                       "knight", "archers", "arrows", "fireball"],
    "Log Bait":       ["goblin_barrel", "princess", "knight", "ice_spirit",
                       "inferno_tower", "the_log", "rocket", "dart_goblin"],
    "Miner Control":  ["miner", "poison", "musketeer", "ice_wizard",
                       "bats", "inferno_tower", "tornado", "spear_goblins"],
    "Lava Loon":      ["lava_hound", "balloon", "mega_minion", "baby_dragon",
                       "minions", "tombstone", "lightning", "zap"],
    "X-Bow":          ["xbow", "tesla", "ice_spirit", "archers",
                       "knight", "the_log", "fireball", "skeletons"],
    "Sparky GG":      ["goblin_giant", "sparky", "electro_dragon", "zappies",
                       "rage", "zap", "cannon", "spear_goblins"],
    "MK Bats WB":     ["mega_knight", "wall_breakers", "bats", "valkyrie",
                       "musketeer", "fireball", "zap", "cannon"],
    "Royal Giant":    ["royal_giant", "fireball", "hunter", "mega_minion",
                       "electro_dragon", "cannon", "zap", "skeletons"],
}


def random_deck():
    """A random legal 8-card deck for the AI."""
    return random.sample([c.key for c in DEPLOYABLE_CARDS], DECK_SIZE)


def get(key: str) -> CardDef:
    return CARDS[key]
