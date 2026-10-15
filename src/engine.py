"""
============================================================================
  ENGINE.PY  --  Arena, entities, combat, spells and the match simulation
============================================================================

This is the "rules engine". Most balancing happens in config.py and cards.py;
you normally don't need to edit this file. It is organized as:

  * geometry helpers (tiles <-> pixels, river/bridge logic)
  * Entity      : any troop, building or tower on the field
  * Projectile  : ranged shots in flight
  * Effect      : lingering zones (poison, rage) and The Log
  * Match       : owns everything, steps the simulation, tracks elixir/crowns
============================================================================
"""

import math
import random

import config as cfg
import cards
import evo_engine
import towers
from cards import CardDef

# --- river / bridge geometry (in tile coordinates) ---------------------------
RIVER_TOP = float(min(cfg.RIVER_ROWS))          # y where river starts
RIVER_BOTTOM = float(max(cfg.RIVER_ROWS)) + 1.0  # y where river ends
RIVER_CENTER = (RIVER_TOP + RIVER_BOTTOM) / 2.0
BRIDGE_X = [c + 0.5 for c in cfg.BRIDGE_COLS]

PROJECTILE_RANGE_MIN = 2.5   # attack range at/above which a shot flies as a projectile
# Crown tower footprints (half the side of their square, in tiles):
# nothing can be deployed on a standing tower's tiles, and a building's
# tiles (cards.footprint: 3x3, the Tesla 2x2) can't overlap them either.
# Every placement snaps to the tile grid (Match.snap).
TOWER_HALF = {False: 1.5, True: 2.0}         # princess 3x3, king 4x4
GETAWAY_DASH_CD = 1.0       # Boss Bandit: wait after Getaway before dashing
MELEE_RANGE = 1.75           # below this a unit is "melee" (first-hit delay applies)

TROOP_R = 0.45
BUILDING_R = 1.2
TOWER_R = 1.6

PLAYER, ENEMY = 0, 1


# ---- collisions ----------------------------------------------------------
# Units push each other apart (ground with ground, air with air), heavier ones
# barely budge while light ones get shoved aside. Buildings and towers never
# move. COLLIDE_RATE is how quickly an overlap is resolved (per second).
COLLIDE_RATE = 30.0
BRIDGE_HALF = 0.9            # a bridge is 1.8 tiles wide
# How hard a unit is to push (roughly Clash Royale's "mass" values). Anything
# not listed gets hp / 150, clamped to 1..12. A card's `mass` overrides both.
MASS = {
    "skeleton": 1, "skeletons": 1, "skeleton_army": 1, "bat": 1, "bats": 1,
    "goblin": 2, "goblins": 2, "spear_goblin": 2, "spear_goblins": 2,
    "minion": 2, "minions": 2, "minion_horde": 2, "guards": 2,
    "fire_spirit": 1, "ice_spirit": 1, "heal_spirit": 1, "electro_spirit": 1,
    "wall_breakers": 2, "elixir_blob": 2,
    "pekka": 18, "mega_knight": 18, "giant": 18, "royal_giant": 18,
    "electro_giant": 18, "goblin_giant": 16, "giant_skeleton": 16,
    "golem": 20, "lava_hound": 18, "ice_golem": 8, "golemite": 10,
    "elixir_golem": 10, "elixir_golemite": 6, "goblin_monster": 12,
    "balloon": 8, "battle_ram": 8, "hog_rider": 6, "bowler": 10,
}
# collision radius (tiles) for units that are clearly bigger / smaller
BIG_R = {
    "golem": 0.75, "giant": 0.7, "royal_giant": 0.7, "electro_giant": 0.7,
    "goblin_giant": 0.7, "giant_skeleton": 0.7, "pekka": 0.65,
    "mega_knight": 0.65, "lava_hound": 0.8, "balloon": 0.6, "bowler": 0.55,
    "goblin_monster": 0.6, "ice_golem": 0.55, "elixir_golem": 0.6,
    "golemite": 0.55, "battle_ram": 0.55, "baby_dragon": 0.55,
    "inferno_dragon": 0.55, "electro_dragon": 0.55,
}


def unit_mass(card):
    if card.mass is not None:
        return float(card.mass)
    if card.key in MASS:
        return float(MASS[card.key])
    return float(min(12.0, max(1.0, card.hp / 150.0)))


def unit_crad(card):
    if card.key in BIG_R:
        return BIG_R[card.key]
    return 0.3 if card.hp < 200 else 0.42


def dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


class _Spot:
    """A bare map position used as a movement goal."""
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x, self.y = x, y


def _seg_dist(px, py, ax, ay, bx, by):
    """Distance from point P to segment AB."""
    abx, aby = bx - ax, by - ay
    L = abx * abx + aby * aby
    if L < 1e-9:
        return dist(px, py, ax, ay)
    t = max(0.0, min(1.0, ((px - ax) * abx + (py - ay) * aby) / L))
    return dist(px, py, ax + abx * t, ay + aby * t)


def curse(e, team, spec, power):
    """Mark `e` so that, if it dies while cursed, a `spec[0]` unit appears
    for `team` (Mother Witch's hogs, Goblin Curse's goblins)."""
    key, secs = spec
    e.curse_t = max(e.curse_t, secs)
    e.curse_key = key
    e.curse_team = team
    e.curse_pow = power


def river_side(y):
    """-1 = top (enemy) half, +1 = bottom (player) half, 0 = on the river."""
    if y < RIVER_TOP:
        return -1
    if y > RIVER_BOTTOM:
        return 1
    return 0


# ===========================================================================
#  ENTITY
# ===========================================================================
class Entity:
    def __init__(self, card: CardDef, team, x, y, is_tower=False, is_king=False,
                 deploy=None, power=None):
        self.card = card
        self.key = card.key
        # (hp, damage) multipliers inherited from the card that spawned us
        self.power = power or (1.0, 1.0)
        self.level = None          # unit level badge (Levels mode)
        self.boss = False
        self.team = team
        self.x = x
        self.y = y
        self.is_tower = is_tower
        self.is_king = is_king
        self.is_building = is_tower or card.category == "building"

        self.max_hp = int(card.hp * (1.0 if is_tower else cfg.GLOBAL_HP_MULT)
                          * self.power[0])
        self.hp = self.max_hp
        self.shield = int(card.shield_hp * self.power[0])
        self.flying = card.flying
        self.radius = TOWER_R if is_tower else (BUILDING_R if self.is_building else TROOP_R)
        # body size + weight for unit-vs-unit collisions
        if is_tower:
            self.crad, self.mass = (1.75 if is_king else 1.4), 0.0
        elif self.is_building and card.deployable:
            # a placed building fills its footprint (3x3 / Tesla 2x2); passive
            # ones (spawners, Collector, Cage) have the bigger hitbox
            half = cards.footprint(card) / 2.0
            self.radius = half - 0.05
            self.crad = half - (0.1 if cards.passive_building(card) else 0.35)
            self.mass = 0.0
        elif self.is_building:
            self.crad, self.mass = 0.9, 0.0
        else:
            self.crad, self.mass = unit_crad(card), unit_mass(card)

        self.base_speed = card.speed * cfg.GLOBAL_SPEED_MULT
        self.alive = True
        self._death_done = False

        self.target = None
        self.attack_cd = 0.0
        # deploy delay: placed troops pause briefly; spawned units (from
        # spawner buildings / death spawns) pass deploy=0 for no delay.
        # Buildings deploy too (1s; Mortar and X-Bow 3.5s), as in the real game.
        if is_tower:
            self.deploy_timer = 0.0
        elif deploy is None:
            self.deploy_timer = (card.deploy_time if card.deploy_time is not None
                                 else cfg.DEPLOY_TIME)
        else:
            self.deploy_timer = deploy

        # status effects
        self.stun_timer = 0.0
        self.freeze_timer = 0.0
        self.slow_factor = 1.0
        self.slow_timer = 0.0
        self.rage_timer = 0.0

        # mechanic state
        self.dist_since_attack = 0.0   # for charge cards
        self.charged = False
        self._reflect_pending = False  # Electro Giant counter-zap latch
        self._reflect_at = set()       # ...and who it zaps back
        self.reflect_cd = 0.0
        # champion / status
        self.invis_timer = 0.0     # untargetable (Archer Queen cloak)
        self.immune_timer = 0.0    # takes no damage (Monk pancake, Miner dig)
        self.atk_buff = 1.0        # attack-speed multiplier while buffed
        self.atk_buff_timer = 0.0
        self.ability_cd = 0.0      # champion ability cooldown remaining
        self.ability_uses = card.ability_uses if card.is_champion else 0
        self.souls = 0            # Skeleton King soul counter
        self.protect_timer = 0.0   # Monk: damage reduction + projectile deflect
        self.ability_windup = 0.0  # champion: seconds until its ability fires
        self.partner = None        # Goblinstein Doctor <-> Monster link
        self.combo_n = 0           # Monk combo counter
        self.ramp_time = 0.0           # for inferno ramping / ramp_stages
        # evolutions / heroes (see evo_engine.py)
        self.evo = False
        self.hero = False
        self.hero_def = None
        self.haste_timer = 0.0
        self.last_hitter = None
        # animation state (read by the renderer only - never affects play)
        self.walk = 0.0            # tiles walked (drives the step cycle)
        self.move_t = -9.0         # match time we last moved
        self.mvx = 0.0             # last horizontal move direction (-1..1)
        self.atk_t = -9.0          # match time of the last attack
        self.atk_dir = (0.0, -1.0 if team == 0 else 1.0)
        self.hurt = 0.0            # >0 right after taking damage (hit flash)
        self.born = 0.0            # match time we appeared
        self.anim_seed = (x * 7.31 + y * 3.17) % 1.0
        # dash state (Bandit, Mega Knight jump, Golden Knight, Guardian...)
        self.dash = None           # dict while dashing, else None
        self._engaged = None       # id of the target we've started swinging at
        self._match_ref = None     # set by Match for event emission
        self.dash_cd = 0.0
        # v1.1 card mechanics
        self.curse_t = 0.0         # cursed: dying turns us into curse_key
        self.curse_key = None      #   (for curse_team, at curse_pow)
        self.curse_team = None
        self.curse_pow = None
        self.root_timer = 0.0      # Vines: can't move or attack
        self._grounded = False     # Vines dragged a flier down
        self.rune_t = 0.0          # Rune Giant enchantment (every Nth hit +dmg)
        self.rune_n = 0
        self.rune_bonus = 0.0
        self.parry_cd = 0.0        # Ronin
        self.hook_cd = 0.0         # Fisherman
        self.clone = False         # made by the Clone spell (1 hp)
        # the lane it marches down when nothing is in sight: the side of the
        # arena's centre line THIS unit appeared on (0 = left, 1 = right), so
        # a squad dropped on the centre line splits like in the real game
        self.lane = 0 if x < cfg.GRID_COLS / 2 else 1
        # evolution / hero state (see evo_engine.py)
        self.untargetable = card.untargetable  # troops & buildings can't target
        self.immortal = False      # takes no damage (Skeleton shadows, ghosts)
        self.ghostly = False       # drawn see-through (shadows, ghosts, decoys)
        self.fx_tick = False       # needs evo_engine.tick() every frame
        self.parent = None         # the unit / building that spawned us
        self.charge_enabled = card.charge
        self.charge_dist = 3.0     # tiles walked before a charge is ready
        self.haste_mult = 1.15     # move-speed multiplier while hasted
        self.undying_t = 0.0       # can't drop below 1 hp (Hero Berserker)
        self.channel_t = 0.0       # busy channelling an ability: no moving/attacking
        self.sacrificed = False    # removed by an ability: no death spawns
        # Princess Towers: which Tower Troop mans them (see towers.py)
        self.tower_troop = "tower_princess" if (is_tower and not is_king) else None
        self.daggers = None        # Dagger Duchess magazine (None = no magazine)
        self._reload_t = 0.0
        self.fed = False           # already ate a Royal Chef pancake
        self.spawn_timer = card.spawner[2] if card.spawner else 0.0
        if card.spawner and card.spawn_first is not None:
            self.spawn_timer = card.spawn_first
        self.elixir_timer = card.generates_elixir[1] if card.generates_elixir else 0.0
        self.lifetime = card.lifetime

        # towers
        self.active = True
        if is_king and cfg.KING_ACTIVATES_ALLIES:
            self.active = False  # king sleeps until a princess falls or it's hit

        # tower combat stats override
        if is_tower:
            if is_king:
                self.dmg = cfg.KING_TOWER_DMG * self.power[1]
                self.hit_speed = cfg.KING_TOWER_HITSPD
                self.range = cfg.KING_TOWER_RANGE
            else:
                self.dmg = cfg.PRINCESS_TOWER_DMG * self.power[1]
                self.hit_speed = cfg.PRINCESS_TOWER_HITSPD
                self.range = cfg.PRINCESS_TOWER_RANGE
            self.attacks = "air_ground"
        else:
            self.dmg = card.damage * cfg.GLOBAL_DAMAGE_MULT * self.power[1]
            self.hit_speed = card.hit_speed
            self.range = card.range
            self.attacks = card.attacks

        # Effective sight (aggro range). It is always at least the attack range,
        # so bumping a card's `range` also lets it engage from that far. Set a
        # card's `sight` higher than its range to make it "notice" enemies even
        # sooner. Towers just see as far as they shoot.
        if is_tower:
            self.sight = self.range
        else:
            self.sight = max(card.sight, card.range)

    # ---- helpers -----------------------------------------------------------
    def can_attack(self, other):
        if other.team == self.team or not other.alive:
            return False
        if other.invis_timer > 0 or other.untargetable:
            return False               # cloaked / hidden units can't be targeted
        if self.attacks == "buildings":
            return other.is_building or other.is_tower
        if other.flying and self.attacks != "air_ground":
            return False
        return True

    def effective_speed(self):
        s = self.base_speed * self.slow_factor
        if self.charged and self.charge_enabled and self.card.speed > 0:
            # charging: up to Very Fast (Prince, Battle Ram...: 2x in CR)
            s *= max(1.0, cfg.SPEED_VERY_FAST * self.card.charge_speed / self.card.speed)
        if self.rage_timer > 0:
            s *= 1.35
        if self.haste_timer > 0:
            s *= self.haste_mult
        return s

    def reset_charge(self):
        """Stuns, freezes and knockback cancel a charge (it has to build up
        again over charge_dist tiles)."""
        if self.charge_enabled:
            self.charged = False
            self.dist_since_attack = 0.0

    def effective_hitspeed(self):
        m = (1.35 if self.rage_timer > 0 else 1.0)
        if self.atk_buff_timer > 0:
            m *= self.atk_buff
        if self.card.ramp_stages and self.card.ramp_kind == "speed":
            m *= self.ramp_mult()
        if self.slow_timer > 0 and self.slow_factor < 1.0:
            m *= self.slow_factor     # slows hit attack speed too (as in CR)
        return self.hit_speed / m

    def child_power(self):
        """Power multipliers handed to units this one spawns."""
        return (self.power[0] * self.card.sub_hp_mult,
                self.power[1] * self.card.sub_dmg_mult)

    def first_hit_delay(self):
        """Wind-up before a melee unit's first hit on a new target."""
        if self.card.first_hit is not None:
            base = self.card.first_hit
        else:
            base = max(cfg.MELEE_FIRST_HIT_MIN,
                       self.card.hit_speed * cfg.MELEE_FIRST_HIT_FRAC)
        return base * self.effective_hitspeed() / max(self.hit_speed, 1e-6)

    def is_melee(self):
        return (not self.is_tower and not self.is_building
                and self.range < MELEE_RANGE)

    def is_dashing(self):
        return self.dash is not None

    def ramps(self):
        """True for anything whose attack builds up over time."""
        return self.card.ramp or self.card.ramp_stages is not None

    def ramp_mult(self):
        """Current stage multiplier for ramp_stages units (1.0 otherwise)."""
        m = 1.0
        if self.card.ramp_stages:
            for t, mult in self.card.ramp_stages:
                if self.ramp_time >= t:
                    m = mult
        return m

    def ramp_stage(self):
        """0-based stage index for ramp_stages units (for the HUD pips)."""
        n = 0
        if self.card.ramp_stages:
            for i, (t, _) in enumerate(self.card.ramp_stages):
                if self.ramp_time >= t:
                    n = i
        return n

    def take_damage(self, amount):
        if self.immune_timer > 0 or self.immortal:
            return
        m = self._match_ref
        if self.evo or self.hero:
            amount *= evo_engine.taken_damage_mult(self, m)
        shield_before = self.shield
        if self.dash is not None and self.dash.get("immune"):
            return
        if self.protect_timer > 0:
            amount *= (1.0 - self.card.ability_value)
        if self.is_king:
            self.active = True
        if self.card.reflect and m is not None:
            # counter-zap (fires in Match.update) at whoever hit him; spells
            # (no source unit) don't trigger it
            src = m._src_ent
            if src is not None and src is not self and src.team != self.team:
                self._reflect_pending = True
                self._reflect_at.add(src)
        if self.shield > 0:
            # a shield soaks the WHOLE hit that breaks it - nothing spills
            # over onto the hitpoints underneath
            self.shield = max(0, self.shield - amount)
            if self.shield <= 0 and self.evo and m is not None:
                evo_engine.after_damaged(self, m, shield_before)
            return
        dealt = min(amount, self.hp)
        self.hp -= amount
        if amount > 0:
            self.hurt = 0.14
            m = self._match_ref
            if (m is not None and m._src is not None and m._src[0] in (0, 1)
                    and m._src[0] != self.team):
                st, sk = m._src
                d = m.stats["dmg"][st]
                d[sk] = d.get(sk, 0.0) + dealt
                if self.is_tower:
                    m.stats["tower_dmg"][st] += dealt
                self.last_hit = m._src
                self.last_hitter = m._src_ent
            if m is not None and m.dmg_numbers:
                self._dmg_acc = getattr(self, "_dmg_acc", 0.0) + dealt
        if self.evo and m is not None and self.hp > 0:
            evo_engine.after_damaged(self, m, shield_before)
        if (self.card.transform and self.hp > 0
                and self.hp < self.max_hp * self.card.transform[0]):
            self._transform_pending = True
        if self.hp <= 0 and self.undying_t > 0:
            self.hp = 1                   # Hero Berserker's Savage Survival
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    # ---- per-frame update --------------------------------------------------
    def update(self, dt, match):
        if not self.alive:
            return

        # timers
        if self.hurt > 0:
            self.hurt -= dt
        if getattr(self, "_taunt", 0) > 0:
            self._taunt -= dt
        if (self.evo or self.hero or self.fx_tick or self.haste_timer > 0
                or self.undying_t > 0):
            evo_engine.tick(self, dt, match)
            if not self.alive:
                return
        if self.slow_timer > 0:
            self.slow_timer -= dt
            if self.slow_timer <= 0:
                self.slow_factor = 1.0
        if self.rage_timer > 0:
            self.rage_timer -= dt
        if self.invis_timer > 0:
            self.invis_timer -= dt
        if self.immune_timer > 0:
            self.immune_timer -= dt
        if self.atk_buff_timer > 0:
            self.atk_buff_timer -= dt
        if self.ability_cd > 0:
            self.ability_cd -= dt
        if self.protect_timer > 0:
            self.protect_timer -= dt
        if self.dash_cd > 0:
            self.dash_cd -= dt
        if self.curse_t > 0:
            self.curse_t -= dt
        if self.rune_t > 0:
            self.rune_t -= dt
        if self.parry_cd > 0:
            self.parry_cd -= dt
        if self.hook_cd > 0:
            self.hook_cd -= dt
        if getattr(self, "_transform_pending", False):
            self._transform_pending = False
            self.transform_to(self.card.transform[1], match)
        # Royal Ghost: hidden unless he swung in the last `cloak` seconds
        if self.card.cloak and match.elapsed - self.atk_t > self.card.cloak:
            self.invis_timer = max(self.invis_timer, dt * 1.5)
        # buildings: health IS the clock. They lose max_hp / lifetime every
        # second (frozen or stunned too), so damage shortens their time.
        if self.is_building and self.card.lifetime and self.deploy_timer <= 0:
            rate = self.max_hp / self.card.lifetime
            self.hp -= rate * dt
            self.lifetime = max(0.0, self.hp / rate)
            if self.hp <= 0:
                self.hp = 0
                self.alive = False
                return
        # mid-dash: nothing else happens until we land (stuns can't stop it)
        if self.dash is not None:
            self._dash_update(dt, match)
            return
        if self.stun_timer > 0:
            self.stun_timer -= dt
            self.reset_charge()
            # a stun (Zap, E-Wiz...) breaks the lock: on recovering, the unit
            # or tower picks the closest valid target again
            if getattr(self, "_taunt", 0) <= 0:
                self.target = None
            # a stun interrupts the attack: the wind-up starts over (and
            # Sparky has to charge her whole shot again)
            self._rewind = True
            if self.card.stun_reload and self.attack_cd < self.hit_speed:
                self.attack_cd = self.hit_speed
            if self.ramps():
                self.ramp_time = 0.0   # a zap/stun resets any ramp-up
            return
        if self.freeze_timer > 0:
            self.freeze_timer -= dt
            self.reset_charge()
            return
        if self.root_timer > 0:
            self.root_timer -= dt
            if self.root_timer <= 0 and self._grounded:
                self._grounded = False
                self.flying = True        # Vines let go: back in the air
            return
        if self.protect_timer > 0 and self.card.ability_type == "protect":
            return                        # Monk meditating: no moving, no attacks
        if self.deploy_timer > 0:
            self.deploy_timer -= dt
            return
        if self.channel_t > 0:
            self.channel_t -= dt
            return

        # timed troops (Phoenix Egg, decoys...) just count down
        if self.lifetime and not self.is_tower and not self.is_building:
            self.lifetime -= dt
            if self.lifetime <= 0:
                if self.card.hatch:       # Phoenix Egg hatches
                    match.emit("deploy", self.card.hatch, self.x, self.y, self.team)
                    match.spawn_units(self.team, self.card.hatch, 1, self.x, self.y,
                                      deploy=0.0, power=self.power, level=self.level)
                self.alive = False
                return
        if self.card.passive:
            return

        # Rune Giant: keep up to N nearby allied troops enchanted
        if self.card.enchant:
            self._update_enchant(dt, match)
        # independent second weapon (Goblin Machine's rocket launcher)
        if self.card.secondary:
            self._update_secondary(dt, match)

        # elixir collector
        if self.card.generates_elixir:
            self.elixir_timer -= dt
            if self.elixir_timer <= 0:
                self.elixir_timer += self.card.generates_elixir[1]
                match.add_elixir(self.team, self.card.generates_elixir[0])
                match.emit("elixir_made", self.key, self.x, self.y, self.team,
                           amount=self.card.generates_elixir[0])

        # spawner buildings
        if self.card.spawner:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self.spawn_timer += evo_engine.spawner_interval(
                    self, self.card.spawner[2], match)
                ukey, ucount, _ = self.card.spawner
                ox, oy = evo_engine.spawner_offset(self, match)
                made = match.spawn_units(self.team, ukey, ucount, self.x + ox,
                                         self.y + oy, deploy=0.0,
                                         power=self.child_power(), level=self.level)
                for u in made:
                    u.parent = self

        if self.attack_cd > 0:
            self.attack_cd -= dt
        if self.daggers is not None:
            self._reload_dagger(dt, match)

        # back riders (Goblin Giant): units strapped to this one's back that
        # shoot independently while it lives - they can hit air even though
        # the carrier only attacks buildings.
        if self.card.back_riders:
            self._update_back_riders(dt, match)

        # inactive king does nothing offensive
        if self.is_king and not self.active:
            return

        # Clash-style target lock: keep the current target until it dies or
        # leaves our leash range; only then look for a new one. This stops a
        # unit attacking a tower from abandoning it to chase newly-placed troops.
        if not self._keep_target(match):
            self.target = match.find_target(self)
        elif (self.target is not None and getattr(self, "_taunt", 0) <= 0
              and dist(self.x, self.y, self.target.x, self.target.y)
              > self.range + self.target.radius):
            # our target is stepping out of reach: only follow it if nothing
            # else is in attack range right now
            alt = match.find_target(self, in_range=True)
            if alt is not None:
                self.target = alt
        # inferno-style / drill ramp resets the moment the target changes
        if self.card.ramp or (self.card.ramp_stages
                              and self.card.ramp_kind == "damage"):
            tid = id(self.target) if (self.target and self.target.alive) else None
            if tid != getattr(self, "_ramp_id", None):
                if not (evo_engine.keeps_ramp(self) and tid is not None):
                    self.ramp_time = 0.0
                self._ramp_id = tid
        if self.target is None:
            # Levels: nothing in sight -> keep marching to where the enemy
            # tower would be, until it would be in attack range
            mp = match.march_point(self)
            if mp is not None and not self.is_tower:
                if dist(self.x, self.y, mp[0], mp[1]) > self.range + TOWER_R:
                    self._move_toward(_Spot(mp[0], mp[1]), dt, match)
            return

        d = dist(self.x, self.y, self.target.x, self.target.y)
        reach = self.range + self.target.radius

        # Fisherman: anchor throw at targets a few tiles away
        if self.card.hook and self.hook_cd <= 0 and d > reach:
            if self._try_hook(match, d):
                return

        # dashers (Bandit, Mega Knight, Boss Bandit) leap onto targets that
        # are a few tiles away instead of walking up to them
        if self.card.dash and self.dash_cd <= 0 and d > reach:
            dmin, dmax = self.card.dash
            gap = d - self.target.radius
            same_bank = river_side(self.y) * river_side(self.target.y) >= 0
            if dmin <= gap <= dmax and (same_bank or self.flying):
                self.start_dash(self.target, kind="unit",
                                immune=self.card.dash_immune,
                                speed=9.0 if self.card.dash_damage else 13.0)
                return

        if getattr(self, "_getaway_hold", 0) > 0 and d > reach:
            # Boss Bandit just landed her Getaway: she gathers herself on
            # the spot, then dashes back in (instead of walking up)
            self._getaway_hold -= dt
            return

        if d <= reach:
            # every unit needs its real-game wind-up ("first hit speed")
            # after engaging a NEW target - or after a stun - before the
            # first hit lands (spirits explode on contact; a finished charge
            # hits on impact)
            new = self._engaged != id(self.target)
            if new or getattr(self, "_rewind", False):
                self._rewind = False
                self._engaged = id(self.target)
                if self.evo and new:
                    evo_engine.on_new_target(self, self.target, match)
                if self.is_melee() and not self.card.kamikaze and not self.charged:
                    self.attack_cd = max(self.attack_cd, self.first_hit_delay())
                elif self.card.windup is not None:
                    self.attack_cd = max(self.attack_cd, self.card.windup
                                         * self.effective_hitspeed()
                                         / max(self.hit_speed, 1e-6))
            self._attack(match)
        elif not self.is_building and not self.is_tower:
            self._move_toward(self.target, dt, match)

    # ---- dashing -----------------------------------------------------------
    def start_dash(self, target=None, kind="unit", immune=False, speed=13.0,
                   point=None, sweep=None, **extra):
        """Begin a dash toward `target` (stops at melee reach) or to `point`."""
        if point is not None:
            tx, ty = point
        else:
            d = dist(self.x, self.y, target.x, target.y)
            stop = min(d, self.range * 0.6 + target.radius)
            tx = target.x - (target.x - self.x) / max(d, 1e-6) * stop
            ty = target.y - (target.y - self.y) / max(d, 1e-6) * stop
        self.dash = {"tx": tx, "ty": ty, "target": target, "kind": kind,
                     "immune": immune, "speed": speed, "sweep": sweep,
                     "hit": set(), "sx": self.x, "sy": self.y}
        quiet = extra.pop("quiet", False)
        self.dash.update(extra)
        self.ramp_time = 0.0
        if self._match_ref is not None and not quiet:
            self._match_ref.emit("dash", self.key, self.x, self.y, self.team)

    def _dash_update(self, dt, match):
        dsh = self.dash
        t = dsh["target"]
        if t is not None and t.alive and dsh["kind"] != "point":
            # follow a moving target, stopping at melee reach
            d = dist(self.x, self.y, t.x, t.y)
            stop = min(d, self.range * 0.6 + t.radius)
            if d > 1e-6:
                dsh["tx"] = t.x - (t.x - self.x) / d * stop
                dsh["ty"] = t.y - (t.y - self.y) / d * stop
        dx, dy = dsh["tx"] - self.x, dsh["ty"] - self.y
        dd = math.hypot(dx, dy)
        step = dsh["speed"] * dt
        if dd > step:
            self.x += dx / dd * step
            self.y += dy / dd * step
        else:
            self.x, self.y = dsh["tx"], dsh["ty"]
        # sweeping dash (Royal Guardian charge): bowls over enemies en route
        if dsh["sweep"]:
            sdmg, skb = dsh["sweep"]
            nx, ny = (dx / dd, dy / dd) if dd > 1e-6 else (0.0, 0.0)
            for e in match.entities:
                if (e.alive and e.team != self.team and not e.flying
                        and id(e) not in dsh["hit"]
                        and dist(self.x, self.y, e.x, e.y) <= 0.9 + e.radius):
                    dsh["hit"].add(id(e))
                    e.take_damage(sdmg)
                    if not (e.is_tower or e.is_building):
                        e.x += nx * skb
                        e.y += ny * skb
        if dd <= step:
            self.dash = None
            match._dash_landed(self, dsh)

    def _update_back_riders(self, dt, match):
        """Riders on this unit's back fire at the nearest enemy in their range."""
        rkey, rcount = self.card.back_riders
        rc = cards.CARDS[rkey]
        self.rider_cd = getattr(self, "rider_cd", 0.0) - dt
        if self.rider_cd > 0:
            return
        best, best_d = None, 1e9
        for e in match.entities:
            if e.team == self.team or not e.alive or e.invis_timer > 0:
                continue
            if e.untargetable:
                continue
            if e.flying and rc.attacks != "air_ground":
                continue
            if rc.troops_only and (e.is_building or e.is_tower):
                continue
            if e.is_king and not e.active and any(
                    match.towers[(e.team, s)].alive for s in ("left", "right")):
                continue
            d = dist(self.x, self.y, e.x, e.y)
            if d <= rc.range + e.radius and d < best_d:
                best, best_d = e, d
        if best is None:
            return
        self.rider_cd = rc.hit_speed
        for _ in range(rcount):
            match.projectiles.append(Projectile(
                self.team, self.x, self.y, best,
                rc.damage * cfg.GLOBAL_DAMAGE_MULT * self.child_power()[1], 0, rc.attacks,
                rc.stun, rc.slow, style=rkey, owner=self))

    # ---- v1.1 card mechanics ----------------------------------------------
    def transform_to(self, key, match):
        """Become another unit in place, keeping hp (Goblin Demolisher)."""
        nc = cards.CARDS[key]
        self.card = nc
        self.key = key
        self.dmg = nc.damage * cfg.GLOBAL_DAMAGE_MULT * self.power[1]
        self.hit_speed = nc.hit_speed
        self.range = nc.range
        self.attacks = nc.attacks
        self.base_speed = nc.speed * cfg.GLOBAL_SPEED_MULT
        self.sight = max(nc.sight, nc.range)
        self.lifetime = nc.lifetime
        self.flying = nc.flying
        self.target = None
        self._engaged = None
        self.attack_cd = 0.0
        self.ramp_time = 0.0
        match.emit("deploy", key, self.x, self.y, self.team)

    def _try_hook(self, match, d):
        """Fisherman's anchor: drag a ground troop in, or reel himself over
        to a building. Returns True if it was thrown."""
        lo, hi, cd = self.card.hook
        t = self.target
        gap = d - t.radius
        if not (lo <= gap <= hi) or t.flying or t.is_dashing():
            return False
        if river_side(self.y) * river_side(t.y) < 0:
            return False                     # not across the river
        self.hook_cd = cd
        self.atk_t = match.elapsed
        ux, uy = (t.x - self.x) / d, (t.y - self.y) / d
        self.atk_dir = (ux, uy)
        match.emit("attack", self.key, self.x, self.y, self.team, big=False)
        match.effects.append(Effect("chain", self.team, self.x, self.y, 0, 0.35,
                                    card_key=self.key,
                                    points=[(self.x, self.y), (t.x, t.y)]))
        slow = self.card.slow
        if t.is_building or t.is_tower:
            # reel himself in to the building
            stop = t.radius + 0.5
            self.start_dash(None, kind="point", speed=9.0, quiet=True,
                            point=(t.x - ux * stop, t.y - uy * stop))
        else:
            t.start_dash(None, kind="point", speed=8.0, quiet=True,
                         point=(self.x + ux * 0.9, self.y + uy * 0.9))
            t.target = None
            if slow:
                t.slow_factor, t.slow_timer = slow[0], slow[1]
        return True

    def _update_enchant(self, dt, match):
        n, rad, bonus, every, linger = self.card.enchant
        self._ench_t = getattr(self, "_ench_t", 0.0) - dt
        if self._ench_t > 0:
            return
        self._ench_t = 0.5
        mine = getattr(self, "_enchanted", [])
        mine = [e for e in mine if e.alive and e.rune_t > 0]
        for e in mine:
            e.rune_t = linger            # stays charged while we live
        if len(mine) < n:
            cands = sorted(
                (e for e in match.entities
                 if e.alive and e.team == self.team and e is not self
                 and not e.is_building and not e.is_tower and e.rune_t <= 0
                 and not e.card.kamikaze
                 and dist(self.x, self.y, e.x, e.y) <= rad),
                key=lambda e: dist(self.x, self.y, e.x, e.y))
            for e in cands[:n - len(mine)]:
                e.rune_t = linger
                e.rune_n = 0
                e.rune_bonus = bonus * self.power[1]
                e.rune_every = every
                mine.append(e)
                match.effects.append(Effect("chain", self.team, self.x, self.y, 0,
                                            0.4, card_key=self.key,
                                            points=[(self.x, self.y), (e.x, e.y)]))
        self._enchanted = mine

    def _update_secondary(self, dt, match):
        """A second weapon that fires on its own (Goblin Machine rocket)."""
        dmg, hs, lo, hi, splash, atk, tmult = self.card.secondary
        self.sec_cd = getattr(self, "sec_cd", 1.0) - dt
        if self.sec_cd > 0:
            return
        best, best_d = None, 1e9
        for e in match.entities:
            if not self.can_attack_with(e, atk):
                continue
            if e.is_king and not e.active and any(
                    match.towers[(e.team, s)].alive for s in ("left", "right")):
                continue
            d = dist(self.x, self.y, e.x, e.y) - e.radius
            if lo <= d <= hi and d < best_d:
                best, best_d = e, d
        if best is None:
            return
        self.sec_cd = hs
        p = Projectile(self.team, self.x, self.y, best,
                       dmg * cfg.GLOBAL_DAMAGE_MULT * self.power[1], splash, atk,
                       0.0, None, style=self.key + "_rocket", owner=self)
        p.tower_dmg = p.dmg * tmult
        match.projectiles.append(p)
        match.emit("attack", self.key + "_rocket", self.x, self.y, self.team)

    def can_attack_with(self, other, attacks):
        """can_attack() for a weapon with its own target type."""
        if other.team == self.team or not other.alive:
            return False
        if other.invis_timer > 0 or other.untargetable:
            return False
        if attacks == "buildings":
            return other.is_building or other.is_tower
        if other.flying and attacks != "air_ground":
            return False
        return True

    def _keep_target(self, match):
        """True if we should hold our current target (don't re-scan).

        The lock only applies while the target is inside our ATTACK reach:
        a unit actively attacking something stays on it until it dies or
        walks out of range. A unit still WALKING toward a target it can't
        hit yet re-evaluates every scan, so it turns on a closer valid
        enemy instead of blindly marching past it.
        """
        t = self.target
        if t is None or not t.alive or not self.can_attack(t):
            return False
        if getattr(self, "_taunt", 0) > 0:
            return True                       # taunted (Hero Knight)
        # never stay locked on a sleeping king while its princess towers stand
        if t.is_king and not t.active and any(
                match.towers[(t.team, s)].alive for s in ("left", "right")):
            return False
        reach = self.range + t.radius + 0.3   # small margin against flicker
        d = dist(self.x, self.y, t.x, t.y)
        if self.card.min_range and d < self.card.min_range:
            return False                      # walked into the blind spot
        return d <= reach

    def _move_toward(self, target, dt, match):
        # bridge pathing for ground units crossing the river
        tx, ty = target.x, target.y
        if not self.flying and not self.card.river_jump:
            me_top, t_top = self.y < RIVER_CENTER, ty < RIVER_CENTER
            if me_top != t_top:
                if getattr(target, "is_tower", False):
                    # marching on a tower: cross on our own lane's bridge
                    bx = (BRIDGE_X[self.lane] if target.is_king else
                          min(BRIDGE_X, key=lambda b: abs(tx - b)))
                else:
                    bx = min(BRIDGE_X, key=lambda b: abs(self.x - b))
                if (RIVER_TOP - 0.05 <= self.y <= RIVER_BOTTOM + 0.05
                        and abs(self.x - bx) <= BRIDGE_HALF):
                    # on the bridge: walk off its far end first
                    tx = bx
                    ty = RIVER_TOP - 0.3 if t_top else RIVER_BOTTOM + 0.3
                else:
                    tx, ty = bx, RIVER_CENTER
            elif (RIVER_TOP < self.y < RIVER_BOTTOM
                    and not RIVER_TOP < ty < RIVER_BOTTOM):
                # still on the bridge, target on the near bank: step off
                # straight before cutting across
                bx = min(BRIDGE_X, key=lambda b: abs(self.x - b))
                ty2 = RIVER_TOP - 0.3 if t_top else RIVER_BOTTOM + 0.3
                if abs(tx - bx) > BRIDGE_HALF:
                    tx, ty = bx, ty2
        if not self.flying:
            tx, ty = self._steer_around(tx, ty, target, match)
        dx, dy = tx - self.x, ty - self.y
        dd = math.hypot(dx, dy)
        if dd < 1e-6:
            return
        step = self.effective_speed() * dt
        self.x += dx / dd * step
        self.y += dy / dd * step
        self.walk += step
        self.move_t = match.elapsed
        self.mvx = dx / dd
        self.dist_since_attack += step
        if self.charge_enabled and self.dist_since_attack >= self.charge_dist:
            self.charged = True
        if self.ramps() and not evo_engine.keeps_ramp(self):
            self.ramp_time = 0.0   # moving = not attacking -> ramp decays fully

    def _steer_around(self, tx, ty, target, match):
        """Ground path-finding lite: if a building or tower sits on the
        straight line to (tx, ty), aim for a point beside it instead (on the
        side the destination is on), so troops walk AROUND obstacles the way
        they do in Clash Royale rather than sliding along them."""
        dx, dy = tx - self.x, ty - self.y
        dd = math.hypot(dx, dy)
        if dd < 0.3:
            return tx, ty
        ux, uy = dx / dd, dy / dd
        best, best_t = None, 1e9
        for e in match.entities:
            if not e.alive or e.mass > 0 or e is target or e is self:
                continue                      # only buildings & towers block
            ox, oy = e.x - self.x, e.y - self.y
            t = ox * ux + oy * uy             # distance along our path
            if t <= 0 or t > dd + e.crad:
                continue
            r = e.crad + self.crad + 0.15
            perp = abs(ox * uy - oy * ux)     # distance from our path
            if perp < r and t < best_t:
                best, best_t = e, t
        if best is None:
            return tx, ty
        ox, oy = best.x - self.x, best.y - self.y
        od = math.hypot(ox, oy) or 1e-6
        r = best.crad + self.crad + 0.35
        # go round on the side of the line the destination lies; once a side
        # is picked for this obstacle, stick with it (no dithering)
        mem = getattr(self, "_steer_mem", None)
        marching = (best.is_king                # the King sits across both lanes
                    and getattr(self, "lane", None) is not None
                    and (getattr(target, "is_tower", False)
                         or getattr(target, "is_building", False)))
        if mem is not None and mem[0] == id(best):
            side = mem[1]
        elif marching and abs(oy) > 0.25 * od:
            # marching up our lane (no enemy in sight): go round on our own
            # lane's side - never the long way round the other side of it
            want = -1.0 if self.lane == 0 else 1.0
            side = 1.0 if (-oy / od) * want > 0 else -1.0
            self._steer_mem = (id(best), side)
        else:
            cross = ox * dy - oy * dx
            if abs(cross) < 0.05 * dd * od:
                # dead ahead: go round on the side nearer the arena middle
                mid = cfg.GRID_COLS / 2.0
                cross = (best.x - mid) * (1 if dy < 0 else -1) or (0.5 - self.anim_seed)
            side = 1.0 if cross < 0 else -1.0
            self._steer_mem = (id(best), side)
        px, py = -oy / od * side, ox / od * side
        if od <= r + 0.05:                    # touching it: walk along the rim
            return self.x + px * 2.0 + ux * 0.2, self.y + py * 2.0 + uy * 0.2
        return best.x + px * r, best.y + py * r

    def _attack(self, match):
        before = self.atk_t
        tgt = self.target
        self._attack_core(match)
        if ((self.evo or self.hero) and self.atk_t != before
                and not self.card.kamikaze):
            evo_engine.after_attack(self, match, getattr(self, "_last_dmg", self.dmg))
        # Battle Ram / Skeleton Barrel: break on their first hit on a building
        # and drop what they carry (only the Evolved Battle Ram keeps ramming)
        if (self.card.breaks_on_hit and self.atk_t != before
                and not (self.evo and self.key == "battle_ram")
                and tgt is not None and (tgt.is_building or tgt.is_tower)):
            self.hp = 0
            self.alive = False

    def _reload_dagger(self, dt, match):
        """Dagger Duchess: refill one dagger per `reload` s while not throwing."""
        tt = towers.get(self.tower_troop)
        if self.daggers >= tt.daggers or match.elapsed - self.atk_t < tt.reload:
            self._reload_t = 0.0
            return
        self._reload_t += dt
        if self._reload_t >= tt.reload:
            self._reload_t -= tt.reload
            self.daggers += 1

    def _attack_core(self, match):
        if self.attack_cd > 0:
            return
        self.attack_cd = self.effective_hitspeed()
        if self.daggers is not None:
            tt = towers.get(self.tower_troop)
            if self.daggers > 0:          # a flurry from the full magazine...
                self.daggers -= 1
                self.attack_cd = tt.hit_speed
            else:                         # ...then one dagger at a time
                self.attack_cd = tt.empty_hit_speed
        self.atk_t = match.elapsed
        t = self.target
        ddx, ddy = t.x - self.x, t.y - self.y
        dd = math.hypot(ddx, ddy)
        if dd > 1e-6:
            self.atk_dir = (ddx / dd, ddy / dd)
        match.emit("attack", self.key, self.x, self.y, self.team,
                   big=self.max_hp >= 1500)

        # kamikaze units (spirits, wall breakers): ONE attack = explode & die
        if self.card.kamikaze:
            self._exploded = True
        if self.card.kamikaze and self.card.blast_on_death:
            self.alive = False            # on_death() sets off the blast
            return
        if self.card.kamikaze:
            # Electro Spirit: instead of a blast, its zap chains across targets
            if self.card.chain:
                maxt, jump = self.card.chain
                match.chain_damage(self.team, self.x, self.y, self.target,
                                   self.dmg, self.card.stun, maxt, jump,
                                   self.key)
                self.alive = False
                return
            if self.card.death_damage:
                rad, kdmg = self.card.death_damage
                kdmg *= self.power[1]
            else:
                rad, kdmg = max(self.card.splash, 1.2), self.dmg
            rad = getattr(self, "blast_r", rad)       # Evolved Ice Spirit
            # blast is centered at the point of CONTACT with the target, so
            # big targets (towers) are always inside the explosion
            t = self.target
            bx, by = self.x, self.y
            d = dist(self.x, self.y, t.x, t.y)
            if d > 1e-6:
                pull = max(d - t.radius * 0.5, 0.0)
                bx = self.x + (t.x - self.x) / d * pull
                by = self.y + (t.y - self.y) / d * pull
            match.effects.append(Effect("aoe", self.team, bx, by,
                                        rad, 0.35, card_key=self.key))
            if kdmg > 0:
                match.area_damage(self.team, bx, by, rad,
                                  kdmg * cfg.GLOBAL_DAMAGE_MULT,
                                  hit_air=(self.attacks == "air_ground"),
                                  stun=self.card.stun, freeze=self.card.freeze,
                                  slow=self.card.slow)
            if self.card.heal_burst:          # Heal Spirit
                hr, hamt, pulses, secs = self.card.heal_burst
                for i in range(pulses):
                    match.later_add(i * secs / max(pulses - 1, 1), "heal",
                                    team=self.team, x=bx, y=by, radius=hr,
                                    amount=hamt * self.power[0], key=self.key)
            self.alive = False
            return

        dmg = self.dmg
        if self.evo or self.hero:
            dmg = evo_engine.before_attack(self, match, dmg)
        # Rune Giant enchantment: every Nth hit carries bonus damage
        if self.rune_t > 0:
            self.rune_n += 1
            if self.rune_n % getattr(self, "rune_every", 3) == 0:
                dmg += self.rune_bonus
                match.effects.append(Effect("aoe", self.team, self.target.x,
                                            self.target.y, 0.6, 0.3,
                                            card_key="rune_giant"))
        self._last_dmg = dmg
        # charge bonus
        if self.charged:
            dmg *= self.card.charge_mult
            self.charged = False
            if self.card.knockback == 0:
                self.target.x += 0  # (charge knockback handled via card spells)
        self.dist_since_attack = 0.0

        # stepped ramp (Mighty Miner drill / Little Prince): the multiplier
        # grows with time spent attacking. Damage-kind multiplies the hit;
        # speed-kind is applied in effective_hitspeed().
        if self.card.ramp_stages:
            if self.card.ramp_kind == "damage":
                dmg *= self.ramp_mult()
            self.ramp_time += self.attack_cd

        # Monk-style combo: every Nth hit is a heavy splash + knockback
        if self.card.combo_every:
            self.combo_n += 1
            if self.combo_n >= self.card.combo_every:
                self.combo_n = 0
                t = self.target
                match.effects.append(Effect("aoe", self.team, t.x, t.y, 1.5,
                                            0.35, card_key=self.key))
                match.area_damage(self.team, t.x, t.y, 1.5, dmg * 1.5,
                                  hit_air=False, knockback=self.card.knockback,
                                  kb_from=(self.x, self.y))
                return

        # inferno-style ramp: continuous beam, no projectile, direct damage
        if self.card.ramp:
            self.ramp_time += self.effective_hitspeed()
            mult = 1.0 + self.ramp_time * cfg.INFERNO_RAMP_RATE
            if mult > cfg.INFERNO_LATE_AT:
                mult = cfg.INFERNO_LATE_AT + (mult - cfg.INFERNO_LATE_AT) * (
                    cfg.INFERNO_LATE_RATE / cfg.INFERNO_RAMP_RATE)
            mult = min(mult, cfg.INFERNO_MAX_MULT)
            mult *= evo_engine.ramp_bonus(self)
            match.apply_hit(self, self.target, self.dmg * mult, 0)
            return

        # instant beam attack (Tesla): damage lands immediately and the full
        # bolt is drawn from muzzle to target for a moment - no projectile
        if self.card.beam:
            match.apply_hit(self, self.target, dmg, 0,
                            self.card.stun, self.card.slow)
            match.effects.append(Effect(
                "chain", self.team, self.x, self.y, 0, 0.15,
                card_key=self.key,
                points=[(self.x, self.y), (self.target.x, self.target.y)]))
            return

        stun = self.card.stun
        slow = self.card.slow

        # shotgun spread (Hunter): a fan of pellets that fly toward max range
        # but each STOPS at the first enemy it touches (no pass-through)
        if self.card.pellets > 0 and self.range >= PROJECTILE_RANGE_MIN:
            n = self.card.pellets
            d = self.range + 0.8
            ang = math.atan2(self.target.y - self.y, self.target.x - self.x)
            total = math.radians(self.card.pellet_spread)
            for i in range(n):
                off = ((i / (n - 1)) - 0.5) * total if n > 1 else 0.0
                a = ang + off
                dest = (self.x + math.cos(a) * d, self.y + math.sin(a) * d)
                match.projectiles.append(Projectile(
                    self.team, self.x, self.y, None, dmg, 0, self.attacks,
                    stun, slow, style=self.key, homing=False, dest=dest,
                    hit_radius=0.35, owner=self))
            return

        # piercing shots (Magic Archer arrow, Bowler boulder, Executioner axe):
        # fly the full range in the target's direction, damaging every enemy
        # crossed. Path width comes from the card's splash value.
        if self.card.pierce and self.range >= PROJECTILE_RANGE_MIN:
            d = self.range + 0.8
            ang = math.atan2(self.target.y - self.y, self.target.x - self.x)
            dest = (self.x + math.cos(ang) * d, self.y + math.sin(ang) * d)
            match.projectiles.append(Projectile(
                self.team, self.x, self.y, None, dmg, 0, self.attacks,
                stun, slow, style=self.key, homing=False, dest=dest,
                pierce=True, hit_radius=max(0.35, self.card.splash * 0.5),
                knockback=self.card.knockback, owner=self,
                boomerang=self.card.boomerang))
            return

        # multi-bolt attackers (Electro Wizard): one bolt per target, extra
        # bolts go to other nearby enemies, or all into a lone target
        if self.card.multi_target > 1 and self.range >= PROJECTILE_RANGE_MIN:
            targets = [self.target]
            others = sorted(
                (e for e in match.entities
                 if e is not self.target and self.can_attack(e)
                 and not (e.is_king and not e.active)
                 and dist(self.x, self.y, e.x, e.y) <= self.range + e.radius),
                key=lambda e: dist(self.x, self.y, e.x, e.y))
            targets += others[:self.card.multi_target - 1]
            while len(targets) < self.card.multi_target:
                targets.append(self.target)
            for t in targets:
                match.projectiles.append(Projectile(
                    self.team, self.x, self.y, t, dmg, self.card.splash,
                    self.attacks, stun, slow, style=self.key, owner=self))
            return

        if self.range >= PROJECTILE_RANGE_MIN:
            pj = Projectile(self.team, self.x, self.y, self.target,
                            dmg, self.card.splash, self.attacks, stun, slow,
                            style=self.key, owner=self)
            pj.shrapnel = self.card.shrapnel
            match.projectiles.append(pj)
            if self.card.recoil and not self.is_building:
                # Firecracker: the launcher kicks her back a step
                ux, uy = self.atk_dir
                nx = min(max(self.x - ux * self.card.recoil, 0.5), cfg.GRID_COLS - 0.5)
                ny = min(max(self.y - uy * self.card.recoil, 0.5), cfg.GRID_ROWS - 0.5)
                if self.flying or river_side(ny) == river_side(self.y):
                    self.start_dash(None, kind="point", point=(nx, ny), speed=5.0,
                                    quiet=True)
                    self.dash["keep_target"] = True
        else:
            match.apply_hit(self, self.target, dmg, self.card.splash, stun, slow)

        # Battle Healer: every swing also heals nearby allies
        if self.card.heal_on_attack:
            hrad, hamt = self.card.heal_on_attack
            match.effects.append(Effect("aoe", self.team, self.x, self.y,
                                        hrad, 0.3, card_key=self.key))
            for e in match.entities:
                if (e.alive and e.team == self.team and not e.is_tower
                        and dist(self.x, self.y, e.x, e.y) <= hrad):
                    e.hp = min(e.max_hp, e.hp + hamt)

    def on_death(self, match):
        c = self.card
        # Elixir Golem blobs: dying gifts the OPPONENT elixir
        if c.death_gives_elixir > 0:
            match.add_elixir(1 - self.team, c.death_gives_elixir)
        # kamikaze units already exploded on their attack; if they were killed
        # before attacking they simply die with no blast
        if c.death_damage and c.death_bomb > 0 and not self.sacrificed:
            # Balloon / Giant Skeleton / Bomb Tower: the bomb drops and its
            # fuse burns for a moment before it goes off (dodge it!)
            radius, ddmg = c.death_damage
            bomb = Effect("death_bomb", self.team, self.x, self.y, radius, c.death_bomb,
                          damage=ddmg * self.power[1], knockback=c.death_knockback,
                          slow=c.death_slow, card_key=self.key)
            bomb.drop = 0.3 if self.flying else 0.0      # falls from the sky
            match.effects.append(bomb)
        elif c.death_damage and (not c.kamikaze or c.blast_on_death) and not self.sacrificed:
            radius, ddmg = c.death_damage
            ddmg *= self.power[1]
            match.effects.append(Effect("aoe", self.team, self.x, self.y,
                                        radius, 0.35, card_key=self.key))
            match.area_damage(self.team, self.x, self.y, radius, ddmg, hit_air=True,
                              slow=c.death_slow, knockback=c.death_knockback)
            if c.blast_on_death:
                match.emit("impact", self.key, self.x, self.y, self.team,
                           radius=radius)
        # cursed (Mother Witch / Goblin Curse): come back for the curser
        if (self.curse_t > 0 and self.curse_key and not self.is_building
                and not self.clone):
            match.spawn_units(self.curse_team, self.curse_key, 1, self.x, self.y,
                              deploy=0.3, power=self.curse_pow)
            match.emit("portal", self.curse_key, self.x, self.y, self.curse_team)
        self._death_spawned = []
        if c.death_spawn and not self.sacrificed:
            ukey, ucount = c.death_spawn
            if ukey == "rage_pickup":
                rr, rd = evo_engine.lumberjack_rage(self)
                match.effects.append(Effect("rage", self.team, self.x, self.y, rr, rd))
                # the dropped Rage lands with the Rage spell's hit (his level)
                rc = cards.CARDS["rage"]
                if rc.spell_damage:
                    match.area_damage(self.team, self.x, self.y, rr,
                                      rc.spell_damage * self.power[1], hit_air=True,
                                      tower_damage=rc.tower_dmg() * self.power[1])
            elif ukey in cards.CARDS and ucount > 0:
                self._death_spawned = match.spawn_units(
                    self.team, ukey, ucount, self.x, self.y, deploy=0.0,
                    power=self.child_power(), level=self.level)


# ===========================================================================
#  PROJECTILE
# ===========================================================================
# Per-shooter projectile speed (tiles/sec). Anything not listed flies at
# cfg.PROJECTILE_SPEED. Fast = bullets/bolts, slow = lobbed bombs/rocks.
PROJ_SPEEDS = {
    "musketeer": 14, "three_musketeers": 14, "hunter": 13, "xbow": 16,
    "archers": 11, "magic_archer": 12, "dart_goblin": 13, "princess": 10,
    "princess_tower": 12, "king_tower": 10, "cannon": 11, "royal_giant": 9,
    "mortar": 6, "bomber": 7, "bomb_tower": 7, "bowler": 6, "executioner": 7,
    "sparky": 7, "flying_machine": 12, "tesla": 18,
    "firecracker": 9, "firecracker_spark": 8, "goblin_machine_rocket": 8,
    "goblin_demolisher": 7, "skeleton_dragons": 9, "minion_giant": 8,
    "mother_witch": 10, "rascal_girl": 12, "ram_rider_bola": 10,
    "spirit_empress_air": 11,
    "cannoneer": 9, "dagger_duchess": 16, "royal_chef": 12,
}


class Projectile:
    """A shot in flight.

    Homing shots track their target (default). Non-homing shots (Hunter
    pellets) fly to a fixed point and damage whatever is standing there.
    `style` is the shooter's card key - game.py themes the visual from it.
    """

    def __init__(self, team, x, y, target, dmg, splash, attacks, stun, slow,
                 style=None, homing=True, dest=None, hit_radius=0.55,
                 pierce=False, knockback=0.0, owner=None, boomerang=False):
        self.team = team
        self.x = x
        self.y = y
        self.target = target
        self.dmg = dmg
        self.splash = splash
        self.attacks = attacks
        self.stun = stun
        self.slow = slow
        self.style = style
        self.homing = homing
        self.hit_radius = hit_radius
        self.pierce = pierce
        self.knockback = knockback
        self.hits = set()      # ids already damaged (pierce hits once each)
        self.owner = owner     # shooter (deflected shots fly back at it)
        self.boomerang = boomerang
        self.returning = False
        self.deflected = False
        if dest is not None:
            self.tx, self.ty = dest
        else:
            self.tx, self.ty = target.x, target.y
        self.vx, self.vy = 0.0, 1.0   # facing, for the renderer
        self.speed = PROJ_SPEEDS.get(style, cfg.PROJECTILE_SPEED)
        self.alive = True
        self.shrapnel = None   # (pieces, spread, length): burst on impact
        self.tower_dmg = None  # crown-tower damage of a splash shot

    def update(self, dt, match):
        if self.homing and self.target and self.target.alive:
            self.tx, self.ty = self.target.x, self.target.y
        if self.returning and self.owner is not None and self.owner.alive:
            self.tx, self.ty = self.owner.x, self.owner.y
        dx, dy = self.tx - self.x, self.ty - self.y
        dd = math.hypot(dx, dy)
        if dd > 1e-6:
            self.vx, self.vy = dx / dd, dy / dd
        step = self.speed * dt
        if dd <= step:
            self.x, self.y = self.tx, self.ty
            if self.boomerang and not self.returning:
                # boomerang (Executioner axe): turn around and fly home,
                # able to hit everything a second time on the way back
                self.returning = True
                self.hits.clear()
                if self.owner is None or not self.owner.alive:
                    self.alive = False
                return
            self._impact(match)
            self.alive = False
        else:
            self.x += self.vx * step
            self.y += self.vy * step
        if not self.alive:
            return
        # piercing shots damage everything they cross, once each
        if self.pierce:
            for e in match.entities:
                if id(e) in self.hits or not self._can_hit(e):
                    continue
                if dist(self.x, self.y, e.x, e.y) <= self.hit_radius + e.radius * 0.7:
                    self._apply(e, match)
                    if (self.knockback and not (e.is_tower or e.is_building)
                            and not e.card.no_knockback):
                        e.x += self.vx * self.knockback
                        e.y += self.vy * self.knockback
                        e.reset_charge()
                    self.hits.add(id(e))
        # non-homing, non-piercing shots (Hunter pellets) stop at the FIRST
        # enemy they touch - no pass-through
        elif not self.homing:
            for e in match.entities:
                if not self._can_hit(e):
                    continue
                if dist(self.x, self.y, e.x, e.y) <= self.hit_radius + e.radius * 0.7:
                    self._apply(e, match)
                    self.alive = False
                    return

    def _can_hit(self, e):
        if e.team == self.team or not e.alive or e.invis_timer > 0:
            return False
        if e.untargetable:
            return False
        if self.attacks == "buildings":
            return e.is_building or e.is_tower
        if e.flying and self.attacks != "air_ground":
            return False
        return True

    def _apply(self, e, match=None):
        # Monk's Pensive Protection: deflect single-target shots back at the
        # shooter (the Monk still takes the reduced damage)
        if (match is not None and e.protect_timer > 0 and not self.deflected
                and not self.pierce and self.owner is not None
                and self.owner.alive):
            back = Projectile(e.team, e.x, e.y, self.owner, self.dmg, 0,
                              "air_ground", 0.0, None, style=self.style,
                              owner=e)
            back.deflected = True
            match.projectiles.append(back)
            match.effects.append(Effect("aoe", e.team, e.x, e.y, 0.8, 0.25,
                                        card_key=e.key))
        e.take_damage(self.tower_dmg if (e.is_tower and self.tower_dmg is not None)
                      else self.dmg)
        if self.owner is not None and (self.owner.evo or self.owner.hero):
            evo_engine.on_projectile_hit(self, e, match)
        o = self.owner
        if (o is not None and o.card.curse_on_hit and not e.is_building
                and not e.is_tower and match is not None):
            curse(e, o.team, o.card.curse_on_hit, o.child_power())
        if self.stun:
            e.stun_timer = max(e.stun_timer, self.stun)
        if self.slow:
            e.slow_factor = self.slow[0]
            e.slow_timer = self.slow[1]

    def _impact(self, match):
        if self.owner is not None and (self.owner.evo or self.owner.hero):
            evo_engine.on_projectile_impact(self, match)
        if self.pierce:
            return   # damage already dealt along the flight path
        # Firecracker: the firework bursts into sparks that fly on in a cone
        if self.shrapnel:
            n, spread, length = self.shrapnel
            ang = math.atan2(self.vy, self.vx)
            sx, sy = self.x - self.vx * 0.5, self.y - self.vy * 0.5
            for i in range(n):
                a = ang + math.radians(((i / max(n - 1, 1)) - 0.5) * spread)
                match.projectiles.append(Projectile(
                    self.team, sx, sy, None, self.dmg, 0, self.attacks, 0.0,
                    self.slow, style="firecracker_spark", homing=False,
                    dest=(sx + math.cos(a) * length, sy + math.sin(a) * length),
                    pierce=True, hit_radius=0.4, owner=self.owner))
            match.effects.append(Effect("aoe", self.team, self.x, self.y, 0.8,
                                        0.25, card_key="firecracker"))
            match.emit("hit", "firecracker", self.x, self.y, self.team)
            return
        # chain-lightning shooters (Electro Dragon): the bolt arcs onward from
        # the struck target instead of splashing
        card = cards.CARDS.get(self.style)
        if (card is not None and card.chain and self.homing
                and self.target and self.target.alive):
            maxt, jump = card.chain
            maxt = evo_engine.chain_targets(self.owner, maxt)
            match.chain_damage(self.team, self.x, self.y, self.target,
                               self.dmg, self.stun, maxt, jump, self.style)
            if self.owner is not None and self.owner.evo:
                evo_engine.after_chain(self, match)
            return
        if self.splash > 0:
            match.effects.append(Effect("aoe", self.team, self.x, self.y,
                                        self.splash, 0.3, card_key=self.style))
            match.emit("hit", self.style, self.x, self.y, self.team)
            match.area_damage(self.team, self.x, self.y, self.splash, self.dmg,
                              hit_air=(self.attacks == "air_ground"),
                              stun=self.stun, slow=self.slow,
                              tower_damage=self.tower_dmg)
        elif self.homing:
            if self.target and self.target.alive:
                self._apply(self.target, match)
        else:
            # pellet: hit whoever is standing where it lands (nearest first)
            best, best_d = None, self.hit_radius
            for e in match.entities:
                if not self._can_hit(e):
                    continue
                d = dist(self.x, self.y, e.x, e.y) - e.radius * 0.6
                if d < best_d:
                    best, best_d = e, d
            if best is not None:
                self._apply(best, match)


# ===========================================================================
#  EFFECT  (lingering zones: poison, rage, and rolling The Log)
# ===========================================================================
class Effect:
    def __init__(self, kind, team, x, y, radius, duration,
                 dps=0, slow=None, direction=0, speed=0, damage=0, knockback=0,
                 card_key=None, building_mult=0.4, points=None, ends=None):
        self.kind = kind    # incoming|blast|aoe|poison|rage|log|tornado|graveyard|
                            #   chain|timed_bomb|death_bomb|link
        self.card_key = card_key
        self.building_mult = building_mult
        self.spawn_t = 0.0
        self.points = points or []   # tile-coord polyline for "chain"/beam visuals
        self.team = team
        self.x = x
        self.y = y
        self.radius = radius
        self.duration = duration
        self.elapsed = 0.0
        self.dps = dps
        self.slow = slow
        self.direction = direction  # for log: -1 up / +1 down
        self.speed = speed
        self.damage = damage
        self.knockback = knockback
        self.hit = set()
        self.alive = True
        self.ends = ends             # (entity, entity) for a "link" beam
        self.origin = None           # (x, y) a thrown spell flies from
        self.tick = 0.0
        self.curse = None            # poison zone that curses (Goblin Curse)
        self.curse_pow = None
        self.tiers = ()              # Void damage tiers
        self.tower_damage = damage

    def update(self, dt, match):
        self.elapsed += dt
        if self.kind == "incoming":
            # telegraph window: when it expires, the spell actually lands
            if self.elapsed >= self.duration:
                card = cards.CARDS[self.card_key]
                match.emit("impact", self.card_key, self.x, self.y, self.team,
                           radius=self.radius)
                match._resolve_spell(self.team, card, self.x, self.y,
                                     evo=getattr(self, "evo", False),
                                     boost=getattr(self, "boost", 0),
                                     hero=getattr(self, "hero", False))
                match.effects.append(Effect("blast", self.team, self.x, self.y,
                                            max(self.radius, 1.0), 0.45,
                                            card_key=self.card_key))
                self.alive = False
            return
        if self.kind == "blast":
            if self.elapsed >= self.duration:
                self.alive = False
            return
        if self.kind == "timed_bomb":
            # Mighty Miner's bomb: fuse burns down, then it explodes
            if self.elapsed >= self.duration:
                match.effects.append(Effect("blast", self.team, self.x, self.y,
                                            self.radius, 0.45,
                                            card_key="fireball"))
                match.area_damage(self.team, self.x, self.y, self.radius,
                                  self.damage, hit_air=False,
                                  tower_damage=int(self.damage * 0.35))
                self.alive = False
            return
        if self.kind == "death_bomb":
            # bomb left by a dead Balloon / Giant Skeleton / Bomb Tower
            if self.elapsed >= self.duration:
                match.effects.append(Effect("blast", self.team, self.x, self.y,
                                            self.radius, 0.45, card_key="fireball"))
                match.effects.append(Effect("aoe", self.team, self.x, self.y,
                                            self.radius, 0.35, card_key=self.card_key))
                prev, match._src = match._src, (self.team, self.card_key)
                match.area_damage(self.team, self.x, self.y, self.radius, self.damage,
                                  hit_air=False, slow=self.slow, knockback=self.knockback)
                match._src = prev
                match.emit("impact", "fireball", self.x, self.y, self.team, radius=self.radius)
                self.alive = False
            return
        if self.kind == "link":
            # Goblinstein's Lightning Link between Doctor and Monster
            a, b = self.ends
            if not a.alive:
                self.alive = False
                return
            if b is not None and b.alive:
                bx, by = b.x, b.y
            else:           # Monster gone: beam juts forward from the Doctor
                fwd = -1 if self.team == PLAYER else 1
                bx, by = a.x, a.y + fwd * 3.5
            self.points = [(a.x, a.y), (bx, by)]
            self.x, self.y = a.x, a.y
            self.tick -= dt
            if self.tick <= 0:
                self.tick += 0.25
                for e in match.entities:
                    if not e.alive or e.team == self.team or e.is_tower:
                        continue
                    if _seg_dist(e.x, e.y, a.x, a.y, bx, by) <= self.radius + e.radius:
                        e.take_damage(self.dps * 0.25)
                        if id(e) not in self.hit:     # first touch stuns
                            self.hit.add(id(e))
                            e.stun_timer = max(e.stun_timer, 0.5)
            if self.elapsed >= self.duration:
                self.alive = False
            return
        if self.kind == "void":
            # Void: `hits` strikes over the duration; each one deals more the
            # fewer targets are standing in it
            due = int(self.elapsed / (self.duration / self.hits) + 1e-6)
            while self.tick < min(due, self.hits):
                self.tick += 1
                inside = [e for e in match.entities
                          if e.alive and e.team != self.team
                          and dist(self.x, self.y, e.x, e.y) <= self.radius + e.radius * 0.5]
                n = len(inside)
                dmg = tdmg = 0
                for cap, d1, d2 in self.tiers:
                    if n <= cap:
                        dmg, tdmg = d1, d2
                        break
                for e in inside:
                    e.take_damage((tdmg if e.is_tower else dmg) * self.dps)
                match.effects.append(Effect("blast", self.team, self.x, self.y,
                                            self.radius, 0.35, card_key="void"))
                match.emit("impact", "void", self.x, self.y, self.team,
                           radius=self.radius)
        elif self.kind == "vines":
            # Vines: the chosen targets are rooted (fliers pulled down) and
            # take `hits` ticks of damage
            due = int(self.elapsed / (self.duration / self.hits) + 1e-6) + 1
            while self.tick < min(due, self.hits):
                self.tick += 1
                for e in self.ends:
                    if e.alive:
                        e.take_damage(self.tower_damage if e.is_tower else self.damage)
            self.points = [(e.x, e.y) for e in self.ends if e.alive]
        elif self.kind == "pancake":
            a, b = self.ends               # flies from the tower to the troop
            t = min(1.0, self.elapsed / self.duration)
            self.x = a.x + (b.x - a.x) * t
            self.y = a.y + (b.y - a.y) * t
        elif self.kind == "wind":           # Evolved Baby Dragon's lingering tailwind
            evo_engine.wind_effect(self, dt, match)
        elif self.kind == "snowroll":       # Evolved Giant Snowball rolling on
            evo_engine.snowroll_effect(self, dt, match)
        elif self.kind == "poison":
            for e in match.entities:
                if e.alive and e.team != self.team and dist(self.x, self.y, e.x, e.y) <= self.radius:
                    if self.curse and not e.is_tower and not e.is_building:
                        curse(e, self.team, self.curse, self.curse_pow)
                    # crown towers take reduced spell damage; other buildings
                    # take full damage (Earthquake: bonus vs buildings)
                    if e.is_tower:
                        mult = self.building_mult
                    elif e.is_building:
                        mult = 3.5 if self.card_key == "earthquake" else 1.0
                    else:
                        mult = 1.0
                    e.take_damage(self.dps * dt * mult)
                    if self.slow:
                        e.slow_factor = self.slow[0]
                        e.slow_timer = self.slow[1]
        elif self.kind == "tornado":
            for e in match.entities:
                if not (e.alive and e.team != self.team) or e.is_tower or e.is_building:
                    continue
                d = dist(self.x, self.y, e.x, e.y)
                if d <= self.radius:
                    if d > 0.2:                      # drag toward the eye
                        e.x += (self.x - e.x) / d * self.speed * dt
                        e.y += (self.y - e.y) / d * self.speed * dt
                    e.take_damage(self.dps * dt)
        elif self.kind == "graveyard":
            self.spawn_t -= dt
            if self.spawn_t <= 0:
                self.spawn_t += 0.5
                ang = random.uniform(0, 2 * math.pi)
                rr = random.uniform(0, self.radius)
                gc = cards.CARDS.get(self.card_key or "graveyard")
                tp = match.level_power(self.team, self.card_key or "graveyard")
                match.spawn_units(self.team, "skeleton", 1,
                                  self.x + math.cos(ang) * rr,
                                  self.y + math.sin(ang) * rr, deploy=0.0,
                                  power=((gc.sub_hp_mult if gc else 1) * tp[0],
                                         (gc.sub_dmg_mult if gc else 1) * tp[1]))
        elif self.kind == "rage":
            for e in match.entities:
                if e.alive and e.team == self.team and dist(self.x, self.y, e.x, e.y) <= self.radius:
                    e.rage_timer = max(e.rage_timer, 0.1)
        elif self.kind == "log":
            self.y += self.direction * self.speed * dt
            for e in match.entities:
                if (e.alive and e.team != self.team and not e.flying and id(e) not in self.hit
                        and abs(e.x - self.x) <= self.radius + e.radius
                        and abs(e.y - self.y) <= 0.8 + e.radius):
                    e.take_damage(getattr(self, "tower_damage", self.damage)
                                  if e.is_tower else self.damage)
                    if not (e.is_tower or e.is_building) and (
                            self.card_key == "the_log" or not e.card.no_knockback):
                        # only The Log rolls back even the heavyweights
                        e.y += self.direction * self.knockback
                        if self.knockback:
                            e.reset_charge()
                    self.hit.add(id(e))
        if self.elapsed >= self.duration:
            self.alive = False


# ===========================================================================
#  MATCH
# ===========================================================================
class Match:
    def __init__(self, player_deck, ai_deck, enemy_towers=True, timed=True,
                 card_levels=None, tower_levels=None, evo_cards=None, hero_cards=None,
                 king_levels=None):
        # sound / visual-effect events for the game layer (off in simulations)
        self.record_events = False
        self.events = []
        # Levels mode: the opponent has no towers and the clock doesn't run
        self.enemy_towers = enemy_towers
        self.timed = timed
        self.elapsed = 0.0
        self.team_power = {}       # team -> (hp, dmg) multiplier for its spawns
        self.team_level = {}       # team -> unit level shown on its spawns
        # card levels: per team either one level for every card or a
        # {card_key: level} dict (missing cards = LEVEL_BASE). Played cards
        # get +10% hp/damage per level above 11 (see cards.level_mult).
        self.card_levels = {PLAYER: cards.LEVEL_BASE, ENEMY: cards.LEVEL_BASE}
        if card_levels:
            self.card_levels.update(card_levels)
        # crown tower levels (hp and damage scale the same way)
        self.tower_levels = {PLAYER: cards.LEVEL_BASE, ENEMY: cards.LEVEL_BASE}
        if tower_levels:
            self.tower_levels.update(tower_levels)
        # the King Tower has its own level (your King level); by default the
        # same as the Princess Towers'
        self.king_levels = dict(self.tower_levels)
        if king_levels:
            self.king_levels.update(king_levels)
        self.banned = set()        # cards that can't be played (Levels: win
                                   #   conditions - there are no towers)
        # Levels: a weak permanent poison over the enemy half, so you can't
        # camp an army at their spawn. (damage per tick, seconds per tick)
        self.miasma = None
        self._miasma_t = 0.0
        # post-match stats (see stats_summary)
        self.stats = {"dmg": [{}, {}], "kills": [{}, {}], "played": [{}, {}],
                      "spent": [0.0, 0.0], "leaked": [0.0, 0.0], "tower_dmg": [0.0, 0.0]}
        self._src = None           # (team, card key) dealing damage right now
        self._src_ent = None       # ...and the entity, if a unit
        self.later = []            # [(time, kind, data)] delayed actions
        # special modes (modes.py)
        self.dmg_numbers = False   # emit "dmg" events for floating numbers
        self.elixir_rate = None    # fixed elixir multiplier (Triple Elixir...)
        self.always_rage = False   # Rage Battle: everyone is permanently raged
        # Evolutions: per team the card keys that evolve, and their charge
        # (plays since the last evolved copy). Charges start EMPTY, as in
        # Clash Royale: the first copy is the normal card and the Evolution
        # comes out once it has been cycled `cycles` times.
        self.last_played = {PLAYER: None, ENEMY: None}   # for Mirror
        self.tower_troops = {PLAYER: towers.DEFAULT, ENEMY: towers.DEFAULT}
        self.chef = {}             # team -> Royal Chef cooking state
        self.pending_abilities = []  # champions winding up their ability
        self.evo_cards = {PLAYER: set(), ENEMY: set()}
        self.hero_cards = {PLAYER: set(), ENEMY: set()}
        for t in (PLAYER, ENEMY):
            if evo_cards and evo_cards.get(t):
                self.evo_cards[t] = set(evo_cards[t])
            if hero_cards and hero_cards.get(t):
                self.hero_cards[t] = set(hero_cards[t])
        import evos as _evos
        self.evo_charge = {t: {k: 0 for k in self.evo_cards[t]
                               if k in _evos.EVOS} for t in (PLAYER, ENEMY)}
        self.entities = []
        self.projectiles = []
        self.effects = []

        self.elixir = [cfg.ELIXIR_START, cfg.ELIXIR_START + cfg.AI_ELIXIR_START_BONUS]
        self.crowns = [0, 0]

        self.time_left = cfg.MATCH_LENGTH
        self.overtime = False
        self.finished = False
        self.winner = None  # 0 player, 1 ai, None ongoing/draw

        # hands / decks
        self.decks = [list(player_deck), list(ai_deck)]
        self.hands = [[], []]
        self.queues = [[], []]
        for t in (PLAYER, ENEMY):
            d = list(self.decks[t])
            random.shuffle(d)
            self.hands[t] = d[:cfg.HAND_SIZE]
            self.queues[t] = d[cfg.HAND_SIZE:]
        self.next_card = [self.queues[t][0] if self.queues[t] else None for t in (PLAYER, ENEMY)]

        self._setup_towers()
        if not enemy_towers:
            # the towers exist (so rules code stays simple) but are gone
            for side in ("left", "right", "king"):
                tw = self.towers[(ENEMY, side)]
                tw.alive = False
                tw.hp = 0
                tw._death_done = True
                self.entities.remove(tw)

    # ---- setup -------------------------------------------------------------
    def _setup_towers(self):
        cols = cfg.GRID_COLS
        rows = cfg.GRID_ROWS
        px_l = cfg.PRINCESS_TOWER_INSET_X + 0.5
        px_r = cols - cfg.PRINCESS_TOWER_INSET_X - 0.5
        py = cfg.PRINCESS_TOWER_INSET_Y + 0.5
        ky = cfg.KING_INSET_Y + 1.0
        kx = cols / 2.0

        pdef = CardDef("princess_tower", "Princess Tower", 0, hp=cfg.PRINCESS_TOWER_HP)
        kdef = CardDef("king_tower", "King Tower", 0, hp=cfg.KING_TOWER_HP)
        tp = {t: (cards.level_mult(self.tower_levels[t]),) * 2 for t in (PLAYER, ENEMY)}
        kp = {t: (cards.level_mult(self.king_levels[t]),) * 2 for t in (PLAYER, ENEMY)}

        # enemy (top)
        self.towers = {
            (ENEMY, "left"): Entity(pdef, ENEMY, px_l, py, is_tower=True, power=tp[ENEMY]),
            (ENEMY, "right"): Entity(pdef, ENEMY, px_r, py, is_tower=True, power=tp[ENEMY]),
            (ENEMY, "king"): Entity(kdef, ENEMY, kx, ky, is_tower=True, is_king=True,
                                    power=kp[ENEMY]),
            # player (bottom)
            (PLAYER, "left"): Entity(pdef, PLAYER, px_l, rows - py, is_tower=True,
                                     power=tp[PLAYER]),
            (PLAYER, "right"): Entity(pdef, PLAYER, px_r, rows - py, is_tower=True,
                                      power=tp[PLAYER]),
            (PLAYER, "king"): Entity(kdef, PLAYER, kx, rows - ky, is_tower=True, is_king=True,
                                     power=kp[PLAYER]),
        }
        for tw in self.towers.values():
            tw.level = (self.king_levels if tw.is_king else self.tower_levels)[tw.team]
            tw._match_ref = self
            self.entities.append(tw)

    # ---- tower troops ------------------------------------------------------
    def set_tower_troop(self, team, key):
        """Man `team`'s Princess Towers with a Tower Troop (towers.py)."""
        tt = towers.get(key)
        self.tower_troops[team] = tt.key
        for side in ("left", "right"):
            tw = self.towers[(team, side)]
            if not tw.alive:
                continue
            frac = tw.hp / max(tw.max_hp, 1)
            tw.max_hp = int(cfg.PRINCESS_TOWER_HP * tt.hp_mult * tw.power[0])
            tw.hp = tw.max_hp * frac
            tw.dmg = cfg.PRINCESS_TOWER_DMG * tt.dmg_mult * tw.power[1]
            tw.hit_speed = tt.hit_speed
            tw.range = tw.sight = tt.range
            tw.tower_troop = tt.key
            # attack style / sound follow the troop (the Princess keeps the
            # classic tower arrow)
            tw.key = "princess_tower" if tt.key == towers.DEFAULT else tt.key
            tw.daggers = tt.daggers if tt.daggers else None
        if tt.cook:
            self.chef[team] = {"t": -tt.cook[0], "ready": False}
        else:
            self.chef.pop(team, None)

    def _update_chef(self, dt):
        """Royal Chef: cook a pancake (slower while his towers fight), then
        throw it to the highest-hp troop that hasn't eaten yet (+1 level)."""
        for team, st in self.chef.items():
            alive = [self.towers[(team, s)] for s in ("left", "right")
                     if self.towers[(team, s)].alive]
            if not alive:
                continue                  # both towers down: no more cooking
            _, base, slow = towers.get("royal_chef").cook
            busy = sum(1 for t in alive if self.elapsed - t.atk_t < 1.0) + (2 - len(alive))
            rate = base / (base + (slow - base) * min(busy, 2) / 2.0)
            if not st["ready"]:
                st["t"] += dt * rate
                if st["t"] >= base:
                    st["ready"] = True
                continue
            cands = [e for e in self.entities
                     if e.alive and e.team == team and not e.is_tower
                     and not e.is_building and not e.fed and not e.clone
                     and not e.immortal and e.deploy_timer <= 0
                     and e.hp >= e.max_hp * 0.33]
            if not cands:
                continue                  # keeps the pancake warm
            tgt = max(cands, key=lambda e: e.max_hp)
            src = min(alive, key=lambda t: dist(t.x, t.y, tgt.x, tgt.y))
            evo_engine._level_up(tgt, 1)
            tgt.fed = True
            self.effects.append(Effect("pancake", team, src.x, src.y, 0.6, 0.6,
                                       card_key="royal_chef", ends=(src, tgt)))
            self.emit("ability", "royal_chef", tgt.x, tgt.y, team)
            st["t"], st["ready"] = 0.0, False

    def chef_progress(self, team):
        """0..1 cooking progress for the HUD (None = no Royal Chef)."""
        st = self.chef.get(team)
        if st is None:
            return None
        return 1.0 if st["ready"] else max(0.0, st["t"]) / towers.get("royal_chef").cook[1]

    # ---- card levels -------------------------------------------------------
    def card_level(self, team, key):
        lv = self.card_levels.get(team, cards.LEVEL_BASE)
        if isinstance(lv, dict):
            return lv.get(key, cards.LEVEL_BASE)
        return lv

    def level_power(self, team, key):
        """(hp, dmg) multiplier for a card this team plays."""
        if team in self.team_power:            # Levels waves: set per spawn
            return self.team_power[team]
        m = cards.level_mult(self.card_level(team, key))
        return (m, m)

    def emit(self, kind, key=None, x=0.0, y=0.0, team=None, **extra):
        """Queue a presentation event (sound / particles). Pure no-op unless
        the game turned recording on, so simulations stay fast."""
        if self.record_events:
            ev = {"kind": kind, "key": key, "x": x, "y": y, "team": team}
            ev.update(extra)
            self.events.append(ev)

    def take_events(self):
        ev, self.events = self.events, []
        return ev

    # ---- elixir ------------------------------------------------------------
    def elixir_multiplier(self):
        if self.elixir_rate is not None:          # special modes: fixed rate
            return self.elixir_rate
        if not self.timed:
            return 1.0
        if self.overtime:
            return cfg.TRIPLE_ELIXIR_MULT
        if self.time_left <= cfg.DOUBLE_ELIXIR_AT:
            return cfg.DOUBLE_ELIXIR_MULT
        return 1.0

    def add_elixir(self, team, amount):
        new = self.elixir[team] + amount
        if new > cfg.ELIXIR_MAX:
            self.stats["leaked"][team] += new - max(cfg.ELIXIR_MAX, self.elixir[team])
        self.elixir[team] = min(cfg.ELIXIR_MAX, new)

    # ---- placement ---------------------------------------------------------
    def can_place(self, team, key, x, y):
        card = cards.CARDS[key]
        if x < 0.3 or x > cfg.GRID_COLS - 0.3 or y < 0.3 or y > cfg.GRID_ROWS - 0.3:
            return False
        # spells can target anywhere (The Log, Barbarian Barrel and Royal
        # Delivery: only where you could deploy a troop)
        if card.category == "spell" and not card.own_side:
            return True
        # troops and buildings can't go on a standing tower's tiles
        if card.category != "spell" and self.on_tower(x, y, card):
            return False
        # ...and a building can't go on top of another building
        if card.category == "building" and self.on_building(x, y, card):
            return False
        # no placing in the river
        if RIVER_TOP - 0.2 <= y <= RIVER_BOTTOM + 0.2:
            return False
        # "deploy anywhere" troops (e.g. Miner) ignore the half-field rule
        if card.deploy_anywhere and self.enemy_towers:
            return True
        if not self.enemy_towers and team == PLAYER:
            return y > RIVER_BOTTOM               # Levels: defend your half
        own_bottom = (team == PLAYER)
        if own_bottom:
            if y > RIVER_BOTTOM:
                return True
            # forward deploy allowed on a lane whose enemy princess tower is down
            if x < cfg.GRID_COLS / 2 and not self.towers[(ENEMY, "left")].alive:
                return y > RIVER_TOP - 6
            if x >= cfg.GRID_COLS / 2 and not self.towers[(ENEMY, "right")].alive:
                return y > RIVER_TOP - 6
            return False
        else:
            if y < RIVER_TOP:
                return True
            if x < cfg.GRID_COLS / 2 and not self.towers[(PLAYER, "left")].alive:
                return y < RIVER_BOTTOM + 6
            if x >= cfg.GRID_COLS / 2 and not self.towers[(PLAYER, "right")].alive:
                return y < RIVER_BOTTOM + 6
            return False

    def snap(self, card, x, y):
        """Where a card placed at (x, y) actually lands: on the tile grid.
        Odd-sized footprints (troops, spells, 3x3 buildings) centre on a
        tile, the 2x2 Tesla on a tile corner; a building stays inside the
        arena."""
        f = cards.footprint(card)
        if f % 2:
            sx, sy = math.floor(x) + 0.5, math.floor(y) + 0.5
        else:
            sx, sy = float(round(x)), float(round(y))
        h = f / 2.0
        sx = min(max(sx, h), cfg.GRID_COLS - h)
        sy = min(max(sy, h), cfg.GRID_ROWS - h)
        return sx, sy

    def on_tower(self, x, y, card):
        """True if deploying `card` at (x, y) would overlap a standing crown
        tower (a destroyed tower's spot is free to build on)."""
        pad = cards.footprint(card) / 2.0 if card.category == "building" else 0.0
        for tw in self.towers.values():
            if not tw.alive:
                continue
            h = TOWER_HALF[tw.is_king] + pad
            if abs(x - tw.x) < h and abs(y - tw.y) < h:
                return True
        return False

    def on_building(self, x, y, card):
        """True if `card` placed at (x, y) would overlap a standing building's
        footprint (either team's)."""
        mine = cards.footprint(card) / 2.0
        for e in self.entities:
            if not (e.alive and e.is_building and not e.is_tower):
                continue
            h = mine + (cards.footprint(e.card) / 2.0 if e.card.deployable else e.crad)
            if abs(x - e.x) < h - 1e-6 and abs(y - e.y) < h - 1e-6:
                return True
        return False

    # ---- playing cards -----------------------------------------------------
    def card_cost(self, team, key):
        """Elixir this card costs right now (Mirror and Spirit Empress vary)."""
        card = cards.CARDS[key]
        if card.spell_kind == "mirror":
            last = self.last_played.get(team)
            return cards.CARDS[last].elixir + 1 if last else None
        if card.alt_form and self.elixir[team] >= card.alt_form[0]:
            return card.alt_form[0]
        return card.elixir

    def play_key(self, team, key):
        """The card that actually comes out when `key` is played (Mirror ->
        your last card; Spirit Empress -> her dragon form at 6 elixir)."""
        card = cards.CARDS[key]
        if card.spell_kind == "mirror":
            return self.last_played.get(team)
        if card.alt_form and self.elixir[team] >= card.alt_form[0]:
            return card.alt_form[1]
        return key

    def play_card(self, team, hand_index, x, y):
        if hand_index >= len(self.hands[team]):
            return False
        key = self.hands[team][hand_index]
        if key in self.banned and team == PLAYER:
            return False
        cost = self.card_cost(team, key)
        dkey = self.play_key(team, key)
        if cost is None or dkey is None or self.elixir[team] < cost:
            return False
        x, y = self.snap(cards.CARDS[dkey], x, y)     # every placement snaps
        if not self.can_place(team, dkey, x, y):
            return False
        mirrored = cards.CARDS[key].spell_kind == "mirror"
        self.elixir[team] -= cost
        self.stats["spent"][team] += cost
        pl = self.stats["played"][team]
        pl[key] = pl.get(key, 0) + 1
        evo = hero = False
        if not mirrored:
            evo = self.evo_ready(team, key)
            if key in self.evo_charge[team]:
                if evo:
                    self.evo_charge[team][key] = 0
                else:
                    self.evo_charge[team][key] += 1
            hero = key in self.hero_cards[team]
            self.last_played[team] = key
        self._deploy(team, dkey, x, y, evo=evo, hero=hero,
                     boost=1 if mirrored else 0, played=key)
        # cycle the card
        self.queues[team].append(key)
        newk = self.queues[team].pop(0)
        self.hands[team][hand_index] = newk
        self.next_card[team] = self.queues[team][0] if self.queues[team] else None
        return True

    def evo_ready(self, team, key):
        import evos as _evos
        ch = self.evo_charge[team].get(key)
        return ch is not None and ch >= _evos.EVOS[key].cycles

    def evo_progress(self, team, key):
        """(charge, cycles) or None for the HUD."""
        import evos as _evos
        ch = self.evo_charge[team].get(key)
        return None if ch is None else (ch, _evos.EVOS[key].cycles)

    def later_add(self, delay, kind, **data):
        self.later.append((self.elapsed + delay, kind, data))

    def _run_later(self):
        if not self.later:
            return
        due = [x for x in self.later if x[0] <= self.elapsed]
        if not due:
            return
        self.later = [x for x in self.later if x[0] > self.elapsed]
        for _, kind, d in due:
            team = d["team"]
            self._src = (team, d.get("key", kind))
            self._src_ent = None
            if kind == "blast":
                self.effects.append(Effect("aoe", team, d["x"], d["y"], d["radius"],
                                           0.35, card_key=d.get("key")))
                self.area_damage(team, d["x"], d["y"], d["radius"], d["dmg"],
                                 hit_air=d.get("air", True), stun=d.get("stun", 0.0),
                                 freeze=d.get("freeze", 0.0), slow=d.get("slow"),
                                 tower_damage=d.get("tower_dmg"))
                self.emit("impact", d.get("key"), d["x"], d["y"], team,
                          radius=d["radius"])
            elif kind in evo_engine.LATER_KINDS:
                evo_engine.run_later(self, kind, d)
            elif kind == "heal":
                self.effects.append(Effect("aoe", team, d["x"], d["y"], d["radius"],
                                           0.3, card_key=d.get("key")))
                for e in self.entities:
                    if (e.alive and e.team == team and not e.is_tower
                            and not e.is_building
                            and dist(d["x"], d["y"], e.x, e.y) <= d["radius"]):
                        e.hp = min(e.max_hp, e.hp + d["amount"])
            elif kind == "spawn":
                self.emit("portal", d["key"], d["x"], d["y"], team)
                self.spawn_units(team, d["key"], d["count"], d["x"], d["y"], deploy=0.0,
                                 power=d.get("power"))
        self._src = None

    def effects_rage(self, team, x, y, radius, duration):
        self.effects.append(Effect("rage", team, x, y, radius, duration))

    def _deploy(self, team, key, x, y, evo=False, hero=False, boost=0, played=None):
        """Put a played card on the field. `played` is the hand card (when it
        differs from `key`: Mirror, Spirit Empress); `boost` adds levels."""
        card = cards.CARDS[key]
        lkey = key if played is None or played == "mirror" else played
        self.emit("deploy", key, x, y, team, evo=evo, hero=hero)
        if card.category == "spell":
            self._cast_spell(team, card, x, y, evo=evo, boost=boost, hero=hero)
            return
        power = level = None
        if team not in self.team_power:
            m = cards.level_mult(self.card_level(team, lkey) + boost)
            power, level = (m, m), self.card_level(team, lkey) + boost
        if card.mixed:
            # mixed squad: first group up front, the rest behind it
            fwd = -1 if team == PLAYER else 1
            pw = power or self.level_power(team, lkey)
            sp = (pw[0] * card.sub_hp_mult, pw[1] * card.sub_dmg_mult)
            units = []
            for gi, (uk, n) in enumerate(card.mixed):
                gy = y + fwd * (0.55 if gi == 0 else -0.6)
                gy = min(max(gy, 0.5), cfg.GRID_ROWS - 0.5)
                units += self.spawn_units(team, uk, n, x, gy, power=sp, level=level)
        else:
            units = self.spawn_units(team, key, card.count, x, y, power=power,
                                     level=level)
        if not units:
            return
        if evo or hero:
            evo_engine.on_spawn_group(self, units, cards.CARDS[lkey], evo=evo,
                                      hero=hero)
        if card.companion:   # Goblinstein's Monster, etc.
            ck, cc = card.companion
            cx = x + 1.2 if x + 1.2 < cfg.GRID_COLS - 0.5 else x - 1.2
            comp = self.spawn_units(team, ck, cc, cx, y,
                                    power=(card.sub_hp_mult * units[0].power[0],
                                           card.sub_dmg_mult * units[0].power[1]),
                                    level=units[0].level)
            if comp:      # remember each other (Lightning Link)
                units[0].partner = comp[0]
                comp[0].partner = units[0]

    def spawn_units(self, team, key, count, x, y, deploy=None, power=None, level=None):
        """Create `count` units of `key` around (x, y); returns them."""
        card = cards.CARDS[key]
        made = []
        if power is None and team in self.team_power:
            power = self.team_power[team]          # Levels: wave unit level
        elif power is None:
            power = self.level_power(team, key)    # the played card's level
            if level is None:
                level = self.card_level(team, key)
        if level is None:
            level = self.team_level.get(team)
        if count <= 1:
            made.append(Entity(card, team, x, y, deploy=deploy, power=power))
        elif card.formation == "line":
            # a row across the arena (Royal Recruits, Royal Hogs)
            gap = card.formation_gap
            x0 = min(max(x, 0.5 + gap * (count - 1) / 2),
                     cfg.GRID_COLS - 0.5 - gap * (count - 1) / 2)
            for i in range(count):
                ox = x0 + (i - (count - 1) / 2.0) * gap
                ox = max(0.4, min(cfg.GRID_COLS - 0.4, ox))
                made.append(Entity(card, team, ox, y, deploy=deploy, power=power))
        else:
            r = card.spawn_radius
            # mirror-symmetric rings: pairs side by side, odd squads with
            # their point toward the enemy - so a squad on the centre line
            # splits evenly between the lanes whichever side you favour
            a0 = 0.0 if count % 2 == 0 else (-math.pi / 2 if team == PLAYER else math.pi / 2)
            for i in range(count):
                ang = a0 + 2 * math.pi * i / count
                ox = max(0.4, min(cfg.GRID_COLS - 0.4, x + math.cos(ang) * r))
                oy = max(0.4, min(cfg.GRID_ROWS - 0.4, y + math.sin(ang) * r))
                made.append(Entity(card, team, ox, oy, deploy=deploy, power=power))
        for e in made:
            e._match_ref = self
            e.level = level
            e.born = self.elapsed
        self.entities.extend(made)
        # landing shockwave (Mega Knight slam, Electro Wizard zap, Ice Wizard)
        if card.spawn_damage:
            rad, dmg = card.spawn_damage
            self.effects.append(Effect("aoe", team, x, y, rad, 0.35,
                                       card_key=card.key))
            self.area_damage(team, x, y, rad, dmg * power[1], hit_air=True,
                             stun=card.spawn_stun, slow=card.spawn_slow,
                             knockback=card.spawn_knockback)
        return made

    def spell_origin(self, team):
        """Where thrown spells start: the caster's King Tower."""
        k = self.towers[(team, "king")]
        return k.x, k.y

    def spell_delay(self, team, card, x, y):
        """Seconds between casting `card` at (x, y) and it landing."""
        base = cfg.SPELL_CAST_TIMES.get(card.key, cfg.SPELL_CAST_DELAY)
        spd = cfg.SPELL_FLIGHT_SPEED.get(card.key)
        if spd:
            ox, oy = self.spell_origin(team)
            return max(base * 0.5, dist(ox, oy, x, y) / spd)
        return base

    def _cast_spell(self, team, card, x, y, evo=False, boost=0, hero=False):
        # spells don't hit instantly: an incoming marker shows for a delay (or
        # the spell visibly FLIES from the king tower), then _resolve_spell()
        # applies the effect (see Effect.update).
        delay = self.spell_delay(team, card, x, y)
        fx = Effect("incoming", team, x, y, card.spell_radius or 1.2, delay,
                    card_key=card.key)
        fx.evo = evo
        fx.hero = hero
        fx.boost = boost
        if card.key in cfg.SPELL_FLIGHT_SPEED:
            fx.origin = self.spell_origin(team)
        self.effects.append(fx)

    def _resolve_spell(self, team, card, x, y, evo=False, boost=0, hero=False):
        fwd = -1 if team == PLAYER else 1
        # spells hit harder at higher card levels (Levels waves: wave level)
        lp = self.level_power(team, card.key)
        lvl = self.team_level.get(team) if team in self.team_power else \
            self.card_level(team, card.key)
        if boost:                                   # Mirror: one level higher
            b = cards.level_mult(cards.LEVEL_BASE + boost)
            lp = (lp[0] * b, lp[1] * b)
            lvl = (lvl or cards.LEVEL_BASE) + boost
        if evo:
            evo_engine.on_spell(self, team, card, x, y, evo, lp)
        pw = lp[1]
        if card.spell_kind:
            self._special_spell(team, card, x, y, lp, lvl)
            return
        # troop-dropping spell (Goblin Barrel, Royal Delivery)
        if card.spawn_troops and not card.rolling:
            if card.spell_damage:
                self.area_damage(team, x, y, card.spell_radius,
                                 card.spell_damage * pw, hit_air=True,
                                 tower_damage=card.tower_dmg() * pw)
            self.spawn_units(team, card.spawn_troops[0], card.spawn_troops[1],
                             x, y, deploy=0.25 if card.spell_damage else 0.0,
                             power=(card.sub_hp_mult * lp[0], card.sub_dmg_mult * lp[1]),
                             level=lvl)
            return
        # graveyard: keeps spawning skeletons in the area over its duration
        if card.graveyard:
            self.effects.append(Effect("graveyard", team, x, y, card.spell_radius,
                                       card.duration, card_key=card.key))
            return
        # tornado: drag enemy troops to the center while ticking damage
        if card.pull > 0:
            self.effects.append(Effect("tornado", team, x, y, card.spell_radius,
                                       card.duration, dps=card.spell_damage * pw,
                                       speed=card.pull))
            return
        if card.rolling:
            log = Effect("log", team, x, y, card.spell_radius, 1.4,
                         direction=fwd, speed=6.0,
                         damage=card.spell_damage * pw, knockback=card.knockback,
                         card_key=card.key)
            log.tower_damage = card.tower_dmg() * pw
            self.effects.append(log)
            if card.spawn_troops:   # Barbarian Barrel drops a barbarian
                made = self.spawn_units(team, card.spawn_troops[0], card.spawn_troops[1],
                                        x, y, deploy=0.0,
                                        power=(card.sub_hp_mult * lp[0], card.sub_dmg_mult * lp[1]),
                                        level=lvl)
                if hero:
                    evo_engine.on_spawn_group(self, made, card, hero=True)
            return
        if card.rage:
            self.effects.append(Effect("rage", team, x, y, card.spell_radius, card.duration))
            if card.spell_damage:
                self.area_damage(team, x, y, card.spell_radius, card.spell_damage * lp[1],
                                 hit_air=True, tower_damage=card.tower_dmg() * lp[1])
            return
        if card.dot:
            # crown-tower multiplier from the card's tower_damage
            bm = (card.tower_damage / card.spell_damage
                  if card.tower_damage is not None and card.spell_damage else 1.0)
            self.effects.append(Effect("poison", team, x, y, card.spell_radius,
                                       card.duration, dps=card.spell_damage * pw,
                                       slow=card.slow, building_mult=bm,
                                       card_key=card.key))
            return
        # instant-hit spells (arrows/fireball/zap/rocket/lightning/freeze/snowball)
        self.area_damage(team, x, y, card.spell_radius, card.spell_damage * pw,
                         hit_air=True, stun=card.stun, freeze=card.freeze,
                         slow=card.slow, tower_damage=card.tower_dmg() * pw,
                         knockback=card.knockback)

    def _special_spell(self, team, card, x, y, lp, lvl):
        """Void, Vines, Clone and Goblin Curse."""
        k = card.spell_kind
        pw = lp[1]
        if k == "void":
            fx = Effect("void", team, x, y, card.spell_radius, card.duration,
                        dps=pw, card_key=card.key)
            fx.tiers = card.void_tiers
            fx.hits = card.hits
            self.effects.append(fx)
        elif k == "vines":
            foes = [e for e in self.entities
                    if e.alive and e.team != team and not e.untargetable
                    and dist(x, y, e.x, e.y) <= card.spell_radius + e.radius * 0.5]
            foes.sort(key=lambda e: -e.hp)
            picked = foes[:card.pick]
            for e in picked:
                if e.is_tower:
                    continue
                e.root_timer = max(e.root_timer, card.duration)
                if e.flying:
                    e.flying = False          # dragged down to the ground
                    e._grounded = True
            fx = Effect("vines", team, x, y, card.spell_radius, card.duration,
                        damage=card.spell_damage * pw, card_key=card.key,
                        ends=tuple(picked))
            fx.tower_damage = card.tower_dmg() * pw
            fx.hits = card.hits
            fx.points = [(e.x, e.y) for e in picked]
            self.effects.append(fx)
        elif k == "clone":
            fwd = -1 if team == PLAYER else 1
            for e in list(self.entities):
                if (not e.alive or e.team != team or e.is_building or e.is_tower
                        or e.card.is_champion or e.hero or e.clone
                        or dist(x, y, e.x, e.y) > card.spell_radius + e.radius * 0.5):
                    continue
                cx = min(max(e.x + 0.45, 0.4), cfg.GRID_COLS - 0.4)
                cy = min(max(e.y - fwd * 0.45, 0.4), cfg.GRID_ROWS - 0.4)
                c = self.spawn_units(team, e.key, 1, cx, cy, deploy=0.0,
                                     power=e.power, level=e.level)[0]
                c.max_hp = c.hp = 1
                c.shield = 1 if e.card.shield_hp else 0
                c.clone = True
                c.evo = e.evo
                c.flying = e.flying
                self.emit("portal", e.key, cx, cy, team)
        elif k == "curse":
            fx = Effect("poison", team, x, y, card.spell_radius, card.duration,
                        dps=card.spell_damage * pw, card_key=card.key,
                        building_mult=(card.tower_dmg() / card.spell_damage))
            fx.curse = card.curse_on_hit
            gob = cards.CARDS["goblin_gang"]
            fx.curse_pow = (lp[0] * gob.sub_hp_mult, lp[1] * gob.sub_dmg_mult)
            self.effects.append(fx)

    # ---- combat helpers ----------------------------------------------------
    def _counter_zap(self, e):
        rad, rdmg, rstun = e.card.reflect
        hit = [a for a in e._reflect_at
               if a.alive and dist(e.x, e.y, a.x, a.y) <= rad + a.radius]
        e._reflect_pending = False
        e._reflect_at = set()
        if not e.alive or not hit:
            return
        prev = self._src, self._src_ent
        self._src, self._src_ent = (e.team, e.key), e
        for a in hit:
            self.effects.append(Effect("chain", e.team, e.x, e.y, 0.3, 0.25,
                                       card_key="zap", points=[(e.x, e.y), (a.x, a.y)]))
            a.take_damage(rdmg * e.power[1])
            a.stun_timer = max(a.stun_timer, rstun)
        self.emit("impact", "zap", e.x, e.y, e.team, radius=rad)
        self._src, self._src_ent = prev

    def apply_hit(self, source, target, dmg, splash, stun=0.0, slow=None):
        if splash > 0:
            # Valkyrie-style spin: splash centered on the attacker, not target
            cx, cy = (source.x, source.y) if source.card.splash_self else (target.x, target.y)
            self.effects.append(Effect("aoe", source.team, cx, cy,
                                       splash, 0.3, card_key=source.key))
            self.area_damage(source.team, cx, cy, splash, dmg,
                             hit_air=(source.attacks == "air_ground"), stun=stun, slow=slow)
            # the unit being swung at always takes the hit, even at the very
            # edge of a spin attack's reach
            if (target.alive and dist(cx, cy, target.x, target.y)
                    > splash + target.radius * 0.5):
                target.take_damage(dmg)
                if stun:
                    target.stun_timer = max(target.stun_timer, stun)
                if slow:
                    target.slow_factor, target.slow_timer = slow
        else:
            # Ronin's parry: blocks a ground melee hit and strikes back harder
            pc = target.card.parry
            if (pc and target.alive and target.parry_cd <= 0 and source.is_melee()
                    and not source.flying and target.stun_timer <= 0
                    and target.freeze_timer <= 0):
                target.parry_cd = pc[0]
                target.atk_t = self.elapsed
                self.effects.append(Effect("aoe", target.team, source.x, source.y,
                                           0.7, 0.3, card_key=target.key))
                self.emit("attack", target.key, target.x, target.y, target.team)
                prev = self._src, self._src_ent
                self._src, self._src_ent = (target.team, target.key), target
                source.take_damage(dmg * pc[1])
                self._src, self._src_ent = prev
                return
            if target.alive:
                target.take_damage(dmg)
                if stun:
                    target.stun_timer = max(target.stun_timer, stun)
                if slow:
                    target.slow_factor = slow[0]
                    target.slow_timer = slow[1]

    def area_damage(self, team, x, y, radius, dmg, hit_air=True, stun=0.0,
                    freeze=0.0, slow=None, tower_damage=None, knockback=0.0,
                    kb_from=None):
        for e in self.entities:
            if not e.alive or e.team == team:
                continue
            if e.flying and not hit_air:
                continue
            if dist(x, y, e.x, e.y) <= radius + e.radius * 0.5:
                amount = dmg
                if e.is_tower and tower_damage is not None:   # crown towers only
                    amount = tower_damage
                e.take_damage(amount)
                if stun:
                    e.stun_timer = max(e.stun_timer, stun)
                if freeze:
                    e.freeze_timer = max(e.freeze_timer, freeze)
                if slow:
                    e.slow_factor = slow[0]
                    e.slow_timer = slow[1]
                if (knockback and not (e.is_tower or e.is_building)
                        and not e.card.no_knockback):
                    ox, oy = kb_from if kb_from is not None else (x, y)
                    dx, dy = e.x - ox, e.y - oy
                    dd = math.hypot(dx, dy) or 1.0
                    e.x += dx / dd * knockback
                    e.y += dy / dd * knockback
                    e.reset_charge()

    def chain_damage(self, team, origin_x, origin_y, first_target, dmg,
                     stun, max_targets, jump_range, source_key):
        """Lightning that arcs from target to nearest target.

        Starts at `first_target`, then repeatedly jumps to the closest enemy
        within `jump_range` of the last victim. Each entity is hit at most
        once; the whole chain stops after `max_targets` hits. Emits a "chain"
        effect whose points trace the arcs (drawn as blue bolts).
        """
        pts = [(origin_x, origin_y)]
        visited = set()
        cur = first_target
        hits = 0
        while cur is not None and hits < max_targets:
            if cur.alive:
                cur.take_damage(dmg)
                if stun:
                    cur.stun_timer = max(cur.stun_timer, stun)
            visited.add(id(cur))
            pts.append((cur.x, cur.y))
            hits += 1
            nxt, nd = None, 1e9
            for e in self.entities:
                if id(e) in visited or not e.alive or e.team == team:
                    continue
                d = dist(cur.x, cur.y, e.x, e.y)
                if d <= jump_range + e.radius * 0.5 and d < nd:
                    nxt, nd = e, d
            cur = nxt
        if len(pts) >= 2:
            self.effects.append(Effect("chain", team, pts[0][0], pts[0][1],
                                       0, 0.3, card_key=source_key, points=pts))
        self._last_chain = pts
        return hits

    # ---- champions ---------------------------------------------------------
    def _collect_souls(self, dead):
        """Skeleton Kings gain a soul for each nearby unit death (capped)."""
        for e in self.entities:
            if (e.alive and e.card.ability_type == "skeletons"
                    and dist(e.x, e.y, dead.x, dead.y) <= 5.0):
                e.souls = min(e.souls + 1, 10)

    def hero_on_field(self, team):
        best = None
        for e in self.entities:
            if e.team == team and e.alive and e.hero:
                if e.ability_uses > 0:
                    return e
                best = best or e
        return best

    def hero_status(self, team):
        """(hero, ready, cost) for the HUD; hero is None if none deployed."""
        h = self.hero_on_field(team)
        if h is None or h.hero_def is None:
            return None, False, 0
        cost = h.hero_def.cost
        ready = evo_engine.hero_ready(h, self) and self.elixir[team] >= cost
        return h, ready, cost

    def activate_hero(self, team):
        h, ready, cost = self.hero_status(team)
        if h is None or not ready:
            return False
        self.elixir[team] -= cost
        h.ability_uses -= 1
        evo_engine.do_hero_ability(h, self)
        return True

    def champion_on_field(self, team):
        for e in self.entities:
            if e.team == team and e.alive and e.card.is_champion:
                return e
        return None

    def ability_status(self, team):
        """(champion, ready, cost) for HUD; champion is None if not deployed."""
        champ = self.champion_on_field(team)
        if champ is None:
            return None, False, 0
        cost = champ.card.ability_cost
        ready = (champ.ability_uses > 0 and champ.ability_cd <= 0
                 and self.elixir[team] >= cost and not champ.is_dashing())
        return champ, ready, cost

    def activate_ability(self, team):
        champ = self.champion_on_field(team)
        if champ is None or champ.ability_cd > 0 or champ.ability_uses <= 0:
            return False
        card = champ.card
        if self.elixir[team] < card.ability_cost:
            return False
        if not self.ability_has_target(champ):
            return False
        self.elixir[team] -= card.ability_cost
        self.emit("ability", champ.key, champ.x, champ.y, team)
        champ.ability_uses -= 1
        champ.ability_cd = card.ability_cooldown
        if card.ability_delay > 0:
            # a short wind-up (0.25-0.5s, per champion) before it happens
            champ.ability_windup = card.ability_delay
            self.pending_abilities.append(champ)
        else:
            self._do_ability(champ, card)
        return True

    def _update_pending_abilities(self, dt):
        for champ in list(self.pending_abilities):
            champ.ability_windup -= dt
            if not champ.alive:
                self.pending_abilities.remove(champ)
            elif champ.ability_windup <= 0:
                if champ.is_dashing():
                    continue                  # lands first, then it fires
                self.pending_abilities.remove(champ)
                if not self.ability_has_target(champ):
                    # its target vanished during the wind-up: refunded
                    champ.ability_uses += 1
                    champ.ability_cd = 0.0
                    self.add_elixir(champ.team, champ.card.ability_cost)
                    continue
                prev = self._src, self._src_ent
                self._src, self._src_ent = (champ.team, champ.key), champ
                self._do_ability(champ, champ.card)
                self._src, self._src_ent = prev

    def ability_has_target(self, champ):
        """Abilities that need someone to hit refuse to fire into thin air."""
        if champ.is_dashing():
            return False
        if champ.card.ability_type == "chain_dash":
            return self._nearest_enemy(champ, champ.card.ability_radius) is not None
        if champ.card.ability_type == "getaway":
            return self._getaway_anchor(champ) is not None
        return True

    def _nearest_enemy(self, champ, rng, ground_only=False):
        best, bd = None, rng
        for e in self.entities:
            if ground_only and e.flying:
                continue
            if e.is_king and not e.active:
                continue
            if champ.can_attack(e):
                d = dist(champ.x, champ.y, e.x, e.y)
                if d < bd:
                    best, bd = e, d
        return best

    def _do_ability(self, champ, card):
        team = champ.team
        fwd = -1 if team == PLAYER else 1
        typ = card.ability_type
        if typ == "cloak":
            # Archer Queen: invisible + rapid fire
            champ.invis_timer = card.ability_duration
            champ.atk_buff = card.ability_value
            champ.atk_buff_timer = card.ability_duration
        elif typ == "escape":
            # Mighty Miner: drop a timed bomb, burrow to the mirrored spot
            # in the other lane (reflected across the vertical centre line)
            self.effects.append(Effect("timed_bomb", team, champ.x, champ.y,
                                       card.ability_radius,
                                       card.ability_duration,
                                       damage=card.ability_value,
                                       card_key=champ.key))
            self.effects.append(Effect("aoe", team, champ.x, champ.y, 0.9,
                                       0.3, card_key="earthquake"))
            champ.x = min(max(cfg.GRID_COLS - champ.x, 0.5), cfg.GRID_COLS - 0.5)
            champ.target = None
            champ.ramp_time = 0.0
            champ.deploy_timer = 0.5        # pops back out of the ground
            self.effects.append(Effect("aoe", team, champ.x, champ.y, 0.9,
                                       0.4, card_key="earthquake"))
        elif typ == "rescue":
            # Little Prince: the Guardian charges in and bowls enemies over
            g = self.spawn_units(team, "royal_guardian", 1, champ.x,
                                 champ.y + fwd * 0.8, deploy=0.0,
                                 power=champ.child_power())[0]
            tgt = self._nearest_enemy(g, 6.0, ground_only=True)
            if tgt is not None:
                pt = (tgt.x, tgt.y)
            else:
                pt = (champ.x, champ.y + fwd * 4.0)
            pt = (pt[0], min(max(pt[1], 0.5), cfg.GRID_ROWS - 0.5))
            g.start_dash(None, kind="point", point=pt, speed=10.0,
                         sweep=(card.ability_value, card.ability_radius))
        elif typ == "chain_dash":
            # Golden Knight: dash through up to 10 enemies in a row
            tgt = self._nearest_enemy(champ, card.ability_radius)
            if tgt is not None:
                champ.start_dash(tgt, kind="chain", immune=True, speed=16.0,
                                 left=9, visited={id(tgt)},
                                 pts=[(champ.x, champ.y)])
        elif typ == "skeletons":
            n = int(card.ability_value) + champ.souls
            champ.souls = 0
            self.spawn_units(team, "skeleton", n, champ.x, champ.y, deploy=0.0,
                             power=champ.child_power())
        elif typ == "protect":
            # Monk: big damage reduction + deflect projectiles
            champ.protect_timer = card.ability_duration
        elif typ == "link":
            # Goblinstein: lightning beam between the Doctor and his Monster
            self.effects.append(Effect("link", team, champ.x, champ.y,
                                       card.ability_radius,
                                       card.ability_duration,
                                       dps=card.ability_value,
                                       card_key=champ.key,
                                       ends=(champ, champ.partner)))
        elif typ == "getaway":
            # Boss Bandit: teleport straight back from her target to a spot
            # inside her dash window; she dashes in again after a recovery
            t = self._getaway_anchor(champ)
            nx, ny = self.getaway_point(champ, t, card.ability_value)
            for (ex, ey) in ((champ.x, champ.y), (nx, ny)):
                self.effects.append(Effect("aoe", team, ex, ey, 1.0, 0.45,
                                           card_key="tornado"))
            champ.x, champ.y = nx, ny
            champ.target = t
            champ.dash_cd = GETAWAY_DASH_CD
            champ._getaway_hold = GETAWAY_DASH_CD
            champ.ramp_time = 0.0

    def _getaway_anchor(self, champ):
        """The enemy the Boss Bandit escapes FROM (her target, else nearest)."""
        t = champ.target
        if t is not None and t.alive and champ.can_attack(t):
            return t
        return self._nearest_enemy(champ, champ.sight + 2)

    def getaway_point(self, champ, t, gap):
        """Where Getaway Grenade lands: `gap` tiles (edge to edge) straight
        back from target `t`. If straight back is blocked (arena wall, river,
        or the far bank) she angles off to the nearest open direction so she
        can still dash back in; as a last resort she stops at the bank."""
        dx, dy = champ.x - t.x, champ.y - t.y
        d = math.hypot(dx, dy)
        if d < 0.3:                          # on top of it: back toward home
            dx, dy, d = 0.0, (1.0 if champ.team == PLAYER else -1.0), 1.0
        base = math.atan2(dy, dx)
        reach = t.radius + gap
        side_t = river_side(t.y)
        lo, hi = 0.6, cfg.GRID_COLS - 0.6

        def ok(x, y):
            if not (lo <= x <= hi and 0.6 <= y <= cfg.GRID_ROWS - 0.6):
                return False
            if champ.flying:
                return True
            side = river_side(y)
            if side == 0:     # only on a bridge
                return min(abs(x - b) for b in BRIDGE_X) <= 0.9
            return side_t == 0 or side == side_t

        for deg in (0, 20, -20, 40, -40, 60, -60, 85, -85, 110, -110, 140, -140):
            a = base + math.radians(deg)
            nx, ny = t.x + math.cos(a) * reach, t.y + math.sin(a) * reach
            if ok(nx, ny):
                return nx, ny
        # fallback: clamp the straight-back spot into the arena / onto the bank
        nx = min(max(t.x + math.cos(base) * reach, lo), hi)
        ny = min(max(t.y + math.sin(base) * reach, 0.6), cfg.GRID_ROWS - 0.6)
        if not champ.flying and river_side(ny) != side_t and side_t != 0:
            ny = RIVER_TOP - 0.6 if side_t < 0 else RIVER_BOTTOM + 0.6
        return nx, ny

    def _dash_landed(self, ent, dsh):
        """Called when a dash reaches its destination."""
        kind = dsh["kind"]
        self.emit("land", ent.key, ent.x, ent.y, ent.team,
                  slam=bool(ent.card.dash_damage))
        t = dsh["target"]
        if kind == "unit":
            ent.dash_cd = 1.2
            if ent.card.dash_damage:          # Mega Knight jump slam
                rad, dmg = ent.card.dash_damage
                self.effects.append(Effect("aoe", ent.team, ent.x, ent.y, rad,
                                           0.4, card_key=ent.key))
                self.area_damage(ent.team, ent.x, ent.y, rad,
                                 dmg * cfg.GLOBAL_DAMAGE_MULT, hit_air=False)
            elif t is not None and t.alive:   # Bandit: double-damage strike
                t.take_damage(ent.dmg * ent.card.charge_mult)
                self.effects.append(Effect("aoe", ent.team, t.x, t.y, 0.7,
                                           0.25, card_key=ent.key))
            ent.attack_cd = ent.effective_hitspeed()
            ent.target = t if (t is not None and t.alive) else None
            ent._engaged = id(t) if t is not None else None
        elif kind == "chain":                 # Golden Knight
            card = ent.card
            pts = dsh["pts"] + [(ent.x, ent.y)]
            if t is not None and t.alive:
                t.take_damage(card.ability_value)
            left = dsh["left"]
            nxt = None
            if left > 0:
                best = card.ability_radius
                for e in self.entities:
                    if id(e) in dsh["visited"] or not ent.can_attack(e):
                        continue
                    if e.is_king and not e.active:
                        continue
                    d = dist(ent.x, ent.y, e.x, e.y)
                    if d < best:
                        nxt, best = e, d
            if nxt is not None:
                dsh["visited"].add(id(nxt))
                ent.start_dash(nxt, kind="chain", immune=True, speed=16.0,
                               left=left - 1, visited=dsh["visited"], pts=pts)
            else:
                self.effects.append(Effect("chain", ent.team, pts[0][0],
                                           pts[0][1], 0, 0.45,
                                           card_key=ent.key, points=pts))
                ent.target = None
        # "point" dashes (Guardian charge, Boss Bandit getaway) just stop

    def march_point(self, ent):
        """Levels (no enemy towers): where a troop with nothing to fight walks
        to - the spot the enemy Princess Tower of its lane would stand on."""
        if self.enemy_towers or ent.team != PLAYER or ent.is_building:
            return None
        side = "left" if ent.lane == 0 else "right"
        tw = self.towers[(ENEMY, side)]
        return tw.x, tw.y

    def find_target(self, ent, in_range=False):
        """Nearest attackable enemy in sight (an enemy already within attack
        range beats one that's only in sight); else march to the nearest
        enemy tower. in_range=True: only enemies within attack range."""
        best = None
        best_d = 1e9
        near = None                           # nearest within attack range
        near_d = 1e9
        sight = ent.sight
        mid = cfg.GRID_COLS / 2
        my_side = (ent.lane if abs(ent.x - mid) <= 0.3 else (0 if ent.x < mid else 1))
        for e in self.entities:
            if not ent.can_attack(e):
                continue
            # a troop never takes the OTHER lane's Princess Tower as a target
            # (towers don't lure it over the centre line - troops do)
            if (e.is_tower and not e.is_king and not ent.is_building
                    and (0 if e.x < mid else 1) != my_side):
                continue
            # don't chase a sleeping king while either of its princess towers stand
            if e.is_king and not e.active and any(
                    self.towers[(e.team, s)].alive for s in ("left", "right")):
                continue
            d = dist(ent.x, ent.y, e.x, e.y)
            if ent.card.min_range and d < ent.card.min_range:
                continue                      # inside the blind spot (Mortar)
            if ent.is_tower or ent.is_building:
                if d <= ent.range + e.radius and d < best_d:
                    best, best_d = e, d
            else:
                if d <= sight + e.radius and d < best_d:
                    best, best_d = e, d
                if d <= ent.range + e.radius and d < near_d:
                    near, near_d = e, d
        if in_range:
            return near if not (ent.is_tower or ent.is_building) else best
        if near is not None:
            return near
        if best is not None:
            return best
        # no one in sight: buildings/towers just wait
        if ent.is_tower or ent.is_building:
            return None
        # nothing in sight: march down OUR side of the centre line to its
        # Princess Tower, and once that one is down to the King - never over
        # to the other lane's tower (only an enemy in sight may draw a unit
        # across the centre line). Our side is where we stand now (a unit
        # that chased something across stays on that side).
        if abs(ent.x - cfg.GRID_COLS / 2) > 0.3:
            ent.lane = 0 if ent.x < cfg.GRID_COLS / 2 else 1
        lane_tw = self.towers.get((1 - ent.team, "left" if ent.lane == 0 else "right"))
        if lane_tw is not None and lane_tw.alive:
            return lane_tw
        king = self.towers.get((1 - ent.team, "king"))
        if king is not None and king.alive:
            return king
        for key, tw in self.towers.items():         # (Levels: no King)
            if tw.team == ent.team or not tw.alive:
                continue
            d = dist(ent.x, ent.y, tw.x, tw.y)
            if d < best_d:
                best, best_d = tw, d
        return best

    # ---- main step ---------------------------------------------------------
    def update(self, dt):
        if self.finished:
            return

        # elixir regen
        mult = self.elixir_multiplier()
        self.add_elixir(PLAYER, cfg.ELIXIR_PER_SECOND * mult * dt)
        self.add_elixir(ENEMY, cfg.ELIXIR_PER_SECOND * mult * cfg.AI_ELIXIR_MULT * dt)

        if self.always_rage:
            for e in self.entities:
                if not e.is_tower:
                    e.rage_timer = max(e.rage_timer, 0.2)
        for e in list(self.entities):
            self._src = (e.team, e.key)
            self._src_ent = e
            e.update(dt, self)
            # Electro Giant counter-zap: whoever just hit him gets zapped
            # and stunned back - but only if it's within his reach
            if e.card.reflect and e._reflect_pending:
                self._counter_zap(e)
        self._src = None
        self._src_ent = None
        self._update_pending_abilities(dt)
        self._resolve_collisions(dt)
        for p in list(self.projectiles):
            self._src = (p.team, p.owner.key if p.owner is not None else (p.style or "?"))
            self._src_ent = p.owner
            p.update(dt, self)
        self._src_ent = None
        self._run_later()
        if self.chef:
            self._update_chef(dt)
        self._src = ("miasma", "miasma")
        if self.miasma:
            self._miasma_t += dt
            dmg, every = self.miasma
            while self._miasma_t >= every:
                self._miasma_t -= every
                for e in self.entities:
                    if (e.alive and e.team == PLAYER and not e.is_tower
                            and e.y < RIVER_TOP):
                        e.take_damage(dmg)
                        self.emit("miasma", e.key, e.x, e.y, PLAYER)
        for fx in list(self.effects):
            self._src = (fx.team, fx.card_key or fx.kind)
            fx.update(dt, self)

        # process deaths (repeat: a death can kill more - e.g. a death bomb)
        while any(not e.alive and not e._death_done for e in self.entities):
            for e in list(self.entities):
                if e.alive or e._death_done:
                    continue
                e._death_done = True
                self.emit("death", e.key, e.x, e.y, e.team, tower=e.is_tower,
                          king=e.is_king, building=e.is_building,
                          big=e.max_hp >= 1500)
                lh = getattr(e, "last_hit", None)
                if lh is not None and not e.is_tower and lh[0] in (PLAYER, ENEMY):
                    k = self.stats["kills"][lh[0]]
                    k[lh[1]] = k.get(lh[1], 0) + 1
                self._src = (e.team, e.key)
                self._src_ent = e
                if e.is_tower:
                    self._on_tower_destroyed(e)
                else:
                    self._collect_souls(e)
                    e.on_death(self)
                    evo_engine.on_death(e, self)
        self._src = None
        self._src_ent = None

        if self.dmg_numbers and self.record_events:
            for e in self.entities:
                acc = getattr(e, "_dmg_acc", 0.0)
                if acc >= 1 and self.elapsed - getattr(e, "_dmg_t", -9) >= 0.3:
                    self.emit("dmg", e.key, e.x, e.y, e.team, amount=acc,
                              tower=e.is_tower)
                    e._dmg_acc = 0.0
                    e._dmg_t = self.elapsed
        self.entities = [e for e in self.entities if e.alive]
        self.projectiles = [p for p in self.projectiles if p.alive]
        self.effects = [fx for fx in self.effects if fx.alive]

        # timer
        self.elapsed += dt
        if not self.timed:
            return
        self.time_left -= dt
        if self.time_left <= 0:
            self._advance_phase()

    def _resolve_collisions(self, dt):
        """Soft unit-vs-unit pushing + river banks for ground units.

        Overlapping bodies are pushed apart a fraction of the overlap each
        frame, split by mass: a Giant walks through Skeletons shoving them
        aside, a whole Skeleton Army can nudge a Knight, and nothing ever
        moves a building. Ground units can't be pushed into the river (only
        onto the bridges); air units only bump other air units.
        """
        k = min(1.0, COLLIDE_RATE * dt)
        bodies, grid = [], {}
        for e in self.entities:
            if not e.alive or e.dash is not None:
                continue
            # a Hog Rider mid-vault is in the air
            if e.card.river_jump and RIVER_TOP - 0.3 < e.y < RIVER_BOTTOM + 0.3:
                continue
            i = len(bodies)
            bodies.append(e)
            cell = (int(e.x // 2.0), int(e.y // 2.0))
            grid.setdefault(cell, []).append(i)
        for i, a in enumerate(bodies):
            cx, cy = int(a.x // 2.0), int(a.y // 2.0)
            for gx in (cx - 1, cx, cx + 1):
                for gy in (cy - 1, cy, cy + 1):
                    for j in grid.get((gx, gy), ()):
                        if j <= i:
                            continue
                        b = bodies[j]
                        if a.flying != b.flying:
                            continue
                        if a.mass <= 0 and b.mass <= 0:
                            continue        # two buildings
                        dx, dy = b.x - a.x, b.y - a.y
                        rr = a.crad + b.crad
                        if abs(dx) >= rr or abs(dy) >= rr:
                            continue
                        d2 = dx * dx + dy * dy
                        if d2 >= rr * rr:
                            continue
                        d = math.sqrt(d2)
                        if d < 1e-4:
                            # exactly stacked: split sideways, deterministically
                            dx, dy, d = (0.01 if i % 2 else -0.01), 0.002, 0.0102
                        push = (rr - d) * k
                        nx, ny = dx / d, dy / d
                        if a.mass <= 0:
                            fa, fb = 0.0, 1.0
                        elif b.mass <= 0:
                            fa, fb = 1.0, 0.0
                        else:
                            fa = b.mass / (a.mass + b.mass)
                            fb = 1.0 - fa
                        a.x -= nx * push * fa
                        a.y -= ny * push * fa
                        b.x += nx * push * fb
                        b.y += ny * push * fb
        cols, rows = cfg.GRID_COLS, cfg.GRID_ROWS
        for e in bodies:
            if e.mass <= 0:
                continue
            e.x = min(cols - 0.35, max(0.35, e.x))
            e.y = min(rows - 0.35, max(0.35, e.y))
            if not e.flying and not e.card.river_jump:
                self._keep_out_of_river(e)

    @staticmethod
    def _keep_out_of_river(e):
        """Ground units bounce off the river banks unless they're on a bridge."""
        if not (RIVER_TOP < e.y < RIVER_BOTTOM):
            return
        bx = min(BRIDGE_X, key=lambda b: abs(e.x - b))
        off = abs(e.x - bx)
        if off <= BRIDGE_HALF:
            return
        to_bank = min(e.y - RIVER_TOP, RIVER_BOTTOM - e.y)
        to_bridge = off - BRIDGE_HALF
        if to_bridge < to_bank:
            e.x = bx + (BRIDGE_HALF if e.x > bx else -BRIDGE_HALF)
        elif e.y - RIVER_TOP < RIVER_BOTTOM - e.y:
            e.y = RIVER_TOP
        else:
            e.y = RIVER_BOTTOM

    def _on_tower_destroyed(self, tw):
        # which team lost it -> the other team gains a crown
        winner = PLAYER if tw.team == ENEMY else ENEMY
        self.crowns[winner] += 1
        # activate the owner's king if a princess fell
        if not tw.is_king and cfg.KING_ACTIVATES_ALLIES:
            self.towers[(tw.team, "king")].active = True
        if tw.is_king:
            self.crowns[winner] = 3   # king down = 3 crowns, instant win
            self._finish(winner)
            return
        if self.overtime:
            self._finish(winner)   # sudden death

    def _advance_phase(self):
        if not self.overtime:
            if self.crowns[PLAYER] != self.crowns[ENEMY]:
                self._finish(PLAYER if self.crowns[PLAYER] > self.crowns[ENEMY] else ENEMY)
            else:
                self.overtime = True
                self.time_left = cfg.OVERTIME_LENGTH
        else:
            # overtime expired: decide by crowns, then by lowest tower hp
            if self.crowns[PLAYER] != self.crowns[ENEMY]:
                self._finish(PLAYER if self.crowns[PLAYER] > self.crowns[ENEMY] else ENEMY)
            else:
                self._finish(self._decide_by_tower_hp())

    def _decide_by_tower_hp(self):
        def lowest(team):
            hp = min((self.towers[(team, s)].hp for s in ("left", "right", "king")
                      if self.towers[(team, s)].alive), default=0)
            return hp
        p, e = lowest(PLAYER), lowest(ENEMY)
        if p == e:
            return None  # draw
        return PLAYER if p > e else ENEMY

    def _finish(self, winner):
        self.finished = True
        self.winner = winner
