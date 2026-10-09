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
from cards import CardDef

# --- river / bridge geometry (in tile coordinates) ---------------------------
RIVER_TOP = float(min(cfg.RIVER_ROWS))          # y where river starts
RIVER_BOTTOM = float(max(cfg.RIVER_ROWS)) + 1.0  # y where river ends
RIVER_CENTER = (RIVER_TOP + RIVER_BOTTOM) / 2.0
BRIDGE_X = [c + 0.5 for c in cfg.BRIDGE_COLS]

PROJECTILE_RANGE_MIN = 2.5   # attack range at/above which a shot flies as a projectile

TROOP_R = 0.45
BUILDING_R = 1.2
TOWER_R = 1.6

PLAYER, ENEMY = 0, 1


def dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def _seg_dist(px, py, ax, ay, bx, by):
    """Distance from point P to segment AB."""
    abx, aby = bx - ax, by - ay
    L = abx * abx + aby * aby
    if L < 1e-9:
        return dist(px, py, ax, ay)
    t = max(0.0, min(1.0, ((px - ax) * abx + (py - ay) * aby) / L))
    return dist(px, py, ax + abx * t, ay + aby * t)


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
                 deploy=None):
        self.card = card
        self.key = card.key
        self.team = team
        self.x = x
        self.y = y
        self.is_tower = is_tower
        self.is_king = is_king
        self.is_building = is_tower or card.category == "building"

        self.max_hp = int(card.hp * (1.0 if is_tower else cfg.GLOBAL_HP_MULT))
        self.hp = self.max_hp
        self.shield = card.shield_hp
        self.flying = card.flying
        self.radius = TOWER_R if is_tower else (BUILDING_R if self.is_building else TROOP_R)

        self.base_speed = card.speed * cfg.GLOBAL_SPEED_MULT
        self.alive = True
        self._death_done = False

        self.target = None
        self.attack_cd = 0.0
        # deploy delay: placed troops pause briefly; spawned units (from
        # spawner buildings / death spawns) pass deploy=0 for no delay.
        if is_tower or self.is_building:
            self.deploy_timer = 0.0
        else:
            self.deploy_timer = cfg.DEPLOY_TIME if deploy is None else deploy

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
        self.partner = None        # Goblinstein Doctor <-> Monster link
        self.combo_n = 0           # Monk combo counter
        self.ramp_time = 0.0           # for inferno ramping / ramp_stages
        # dash state (Bandit, Mega Knight jump, Golden Knight, Guardian...)
        self.dash = None           # dict while dashing, else None
        self.dash_cd = 0.0
        self.spawn_timer = card.spawner[2] if card.spawner else 0.0
        self.elixir_timer = card.generates_elixir[1] if card.generates_elixir else 0.0
        self.lifetime = card.lifetime

        # towers
        self.active = True
        if is_king and cfg.KING_ACTIVATES_ALLIES:
            self.active = False  # king sleeps until a princess falls or it's hit

        # tower combat stats override
        if is_tower:
            if is_king:
                self.dmg = cfg.KING_TOWER_DMG
                self.hit_speed = cfg.KING_TOWER_HITSPD
                self.range = cfg.KING_TOWER_RANGE
            else:
                self.dmg = cfg.PRINCESS_TOWER_DMG
                self.hit_speed = cfg.PRINCESS_TOWER_HITSPD
                self.range = cfg.PRINCESS_TOWER_RANGE
            self.attacks = "air_ground"
        else:
            self.dmg = card.damage * cfg.GLOBAL_DAMAGE_MULT
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
        if other.invis_timer > 0:      # cloaked units can't be targeted
            return False
        if self.attacks == "buildings":
            return other.is_building or other.is_tower
        if other.flying and self.attacks != "air_ground":
            return False
        return True

    def effective_speed(self):
        s = self.base_speed * self.slow_factor
        if self.rage_timer > 0:
            s *= 1.35
        return s

    def effective_hitspeed(self):
        m = (1.35 if self.rage_timer > 0 else 1.0)
        if self.atk_buff_timer > 0:
            m *= self.atk_buff
        if self.card.ramp_stages and self.card.ramp_kind == "speed":
            m *= self.ramp_mult()
        return self.hit_speed / m

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
        if self.immune_timer > 0:
            return
        if self.dash is not None and self.dash.get("immune"):
            return
        if self.protect_timer > 0:
            amount *= (1.0 - self.card.ability_value)
        if self.is_king:
            self.active = True
        if self.card.reflect:
            self._reflect_pending = True   # counter-zap fires in Match.update
        if self.shield > 0:
            if amount <= self.shield:
                self.shield -= amount
                return
            amount -= self.shield
            self.shield = 0
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    # ---- per-frame update --------------------------------------------------
    def update(self, dt, match):
        if not self.alive:
            return

        # timers
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
        # mid-dash: nothing else happens until we land (stuns can't stop it)
        if self.dash is not None:
            self._dash_update(dt, match)
            return
        if self.stun_timer > 0:
            self.stun_timer -= dt
            if self.ramps():
                self.ramp_time = 0.0   # a zap/stun resets any ramp-up
            return
        if self.freeze_timer > 0:
            self.freeze_timer -= dt
            return
        if self.deploy_timer > 0:
            self.deploy_timer -= dt
            return

        # building lifetime decay
        if self.lifetime and not self.is_tower:
            self.lifetime -= dt
            if self.lifetime <= 0:
                self.alive = False
                return

        # elixir collector
        if self.card.generates_elixir:
            self.elixir_timer -= dt
            if self.elixir_timer <= 0:
                self.elixir_timer += self.card.generates_elixir[1]
                match.add_elixir(self.team, self.card.generates_elixir[0])

        # spawner buildings
        if self.card.spawner:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self.spawn_timer += self.card.spawner[2]
                ukey, ucount, _ = self.card.spawner
                fwd = -1 if self.team == PLAYER else 1
                match.spawn_units(self.team, ukey, ucount, self.x,
                                  self.y + fwd * 1.2, deploy=0.0)

        if self.attack_cd > 0:
            self.attack_cd -= dt

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
        # inferno-style / drill ramp resets the moment the target changes
        if self.card.ramp or (self.card.ramp_stages
                              and self.card.ramp_kind == "damage"):
            tid = id(self.target) if (self.target and self.target.alive) else None
            if tid != getattr(self, "_ramp_id", None):
                self.ramp_time = 0.0
                self._ramp_id = tid
        if self.target is None:
            return

        d = dist(self.x, self.y, self.target.x, self.target.y)
        reach = self.range + self.target.radius

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

        if d <= reach:
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
        self.dash.update(extra)
        self.ramp_time = 0.0

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
            if e.team == self.team or not e.alive:
                continue
            if e.flying and rc.attacks != "air_ground":
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
                rc.damage * cfg.GLOBAL_DAMAGE_MULT, 0, rc.attacks,
                0.0, None, style=rkey, owner=self))

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
        # never stay locked on a sleeping king while its princess towers stand
        if t.is_king and not t.active and any(
                match.towers[(t.team, s)].alive for s in ("left", "right")):
            return False
        reach = self.range + t.radius + 0.3   # small margin against flicker
        return dist(self.x, self.y, t.x, t.y) <= reach

    def _move_toward(self, target, dt, match):
        # bridge pathing for ground units crossing the river
        tx, ty = target.x, target.y
        if (not self.flying and not self.card.river_jump
                and river_side(self.y) * river_side(ty) < 0):
            bx = min(BRIDGE_X, key=lambda b: abs(self.x - b))
            tx, ty = bx, RIVER_CENTER
        dx, dy = tx - self.x, ty - self.y
        dd = math.hypot(dx, dy)
        if dd < 1e-6:
            return
        step = self.effective_speed() * dt
        self.x += dx / dd * step
        self.y += dy / dd * step
        self.dist_since_attack += step
        if self.card.charge and self.dist_since_attack >= 3.0:
            self.charged = True
        if self.ramps():
            self.ramp_time = 0.0   # moving = not attacking -> ramp decays fully

    def _attack(self, match):
        if self.attack_cd > 0:
            return
        self.attack_cd = self.effective_hitspeed()

        # kamikaze units (spirits, wall breakers): ONE attack = explode & die
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
            else:
                rad, kdmg = max(self.card.splash, 1.2), self.dmg
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
            match.area_damage(self.team, bx, by, rad,
                              kdmg * cfg.GLOBAL_DAMAGE_MULT,
                              hit_air=(self.attacks == "air_ground"),
                              stun=self.card.stun, freeze=self.card.freeze,
                              slow=self.card.slow)
            self.alive = False
            return

        dmg = self.dmg
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
            mult = min(1.0 + self.ramp_time * cfg.INFERNO_RAMP_RATE,
                       cfg.INFERNO_MAX_MULT)
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
            match.projectiles.append(Projectile(
                self.team, self.x, self.y, self.target,
                dmg, self.card.splash, self.attacks, stun, slow,
                style=self.key, owner=self))
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
        if c.death_damage and not c.kamikaze:
            radius, ddmg = c.death_damage
            match.effects.append(Effect("aoe", self.team, self.x, self.y,
                                        radius, 0.35, card_key=self.key))
            match.area_damage(self.team, self.x, self.y, radius, ddmg, hit_air=True,
                              slow=c.death_slow)
        if c.death_spawn:
            ukey, ucount = c.death_spawn
            if ukey == "rage_pickup":
                match.effects.append(Effect("rage", self.team, self.x, self.y, 3.0, 4.0))
            elif ukey in cards.CARDS and ucount > 0:
                match.spawn_units(self.team, ukey, ucount, self.x, self.y, deploy=0.0)


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
                    if self.knockback and not (e.is_tower or e.is_building):
                        e.x += self.vx * self.knockback
                        e.y += self.vy * self.knockback
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
        e.take_damage(self.dmg)
        if self.stun:
            e.stun_timer = max(e.stun_timer, self.stun)
        if self.slow:
            e.slow_factor = self.slow[0]
            e.slow_timer = self.slow[1]

    def _impact(self, match):
        if self.pierce:
            return   # damage already dealt along the flight path
        # chain-lightning shooters (Electro Dragon): the bolt arcs onward from
        # the struck target instead of splashing
        card = cards.CARDS.get(self.style)
        if (card is not None and card.chain and self.homing
                and self.target and self.target.alive):
            maxt, jump = card.chain
            match.chain_damage(self.team, self.x, self.y, self.target,
                               self.dmg, self.stun, maxt, jump, self.style)
            return
        if self.splash > 0:
            match.effects.append(Effect("aoe", self.team, self.x, self.y,
                                        self.splash, 0.3, card_key=self.style))
            match.area_damage(self.team, self.x, self.y, self.splash, self.dmg,
                              hit_air=(self.attacks == "air_ground"),
                              stun=self.stun, slow=self.slow)
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
                            #   chain|timed_bomb|link
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
        self.tick = 0.0

    def update(self, dt, match):
        self.elapsed += dt
        if self.kind == "incoming":
            # telegraph window: when it expires, the spell actually lands
            if self.elapsed >= self.duration:
                card = cards.CARDS[self.card_key]
                match._resolve_spell(self.team, card, self.x, self.y)
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
        if self.kind == "poison":
            for e in match.entities:
                if e.alive and e.team != self.team and dist(self.x, self.y, e.x, e.y) <= self.radius:
                    mult = self.building_mult if (e.is_tower or e.is_building) else 1.0
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
                match.spawn_units(self.team, "skeleton", 1,
                                  self.x + math.cos(ang) * rr,
                                  self.y + math.sin(ang) * rr, deploy=0.0)
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
                    e.take_damage(self.damage if not (e.is_tower or e.is_building) else self.damage)
                    if not (e.is_tower or e.is_building):
                        e.y += self.direction * self.knockback
                    self.hit.add(id(e))
        if self.elapsed >= self.duration:
            self.alive = False


# ===========================================================================
#  MATCH
# ===========================================================================
class Match:
    def __init__(self, player_deck, ai_deck):
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

        # enemy (top)
        self.towers = {
            (ENEMY, "left"): Entity(pdef, ENEMY, px_l, py, is_tower=True),
            (ENEMY, "right"): Entity(pdef, ENEMY, px_r, py, is_tower=True),
            (ENEMY, "king"): Entity(kdef, ENEMY, kx, ky, is_tower=True, is_king=True),
            # player (bottom)
            (PLAYER, "left"): Entity(pdef, PLAYER, px_l, rows - py, is_tower=True),
            (PLAYER, "right"): Entity(pdef, PLAYER, px_r, rows - py, is_tower=True),
            (PLAYER, "king"): Entity(kdef, PLAYER, kx, rows - ky, is_tower=True, is_king=True),
        }
        for tw in self.towers.values():
            self.entities.append(tw)

    # ---- elixir ------------------------------------------------------------
    def elixir_multiplier(self):
        if self.overtime:
            return cfg.TRIPLE_ELIXIR_MULT
        if self.time_left <= cfg.DOUBLE_ELIXIR_AT:
            return cfg.DOUBLE_ELIXIR_MULT
        return 1.0

    def add_elixir(self, team, amount):
        self.elixir[team] = min(cfg.ELIXIR_MAX, self.elixir[team] + amount)

    # ---- placement ---------------------------------------------------------
    def can_place(self, team, key, x, y):
        card = cards.CARDS[key]
        if x < 0.3 or x > cfg.GRID_COLS - 0.3 or y < 0.3 or y > cfg.GRID_ROWS - 0.3:
            return False
        # spells can target anywhere
        if card.category == "spell":
            return True
        # no placing in the river
        if RIVER_TOP - 0.2 <= y <= RIVER_BOTTOM + 0.2:
            return False
        # "deploy anywhere" troops (e.g. Miner) ignore the half-field rule
        if card.deploy_anywhere:
            return True
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

    # ---- playing cards -----------------------------------------------------
    def play_card(self, team, hand_index, x, y):
        if hand_index >= len(self.hands[team]):
            return False
        key = self.hands[team][hand_index]
        card = cards.CARDS[key]
        if self.elixir[team] < card.elixir:
            return False
        if not self.can_place(team, key, x, y):
            return False
        self.elixir[team] -= card.elixir
        self._deploy(team, key, x, y)
        # cycle the card
        self.queues[team].append(key)
        newk = self.queues[team].pop(0)
        self.hands[team][hand_index] = newk
        self.next_card[team] = self.queues[team][0] if self.queues[team] else None
        return True

    def _deploy(self, team, key, x, y):
        card = cards.CARDS[key]
        if card.category == "spell":
            self._cast_spell(team, card, x, y)
        else:
            units = self.spawn_units(team, key, card.count, x, y)
            if card.companion:   # Goblinstein's Monster, etc.
                ck, cc = card.companion
                cx = x + 1.2 if x + 1.2 < cfg.GRID_COLS - 0.5 else x - 1.2
                comp = self.spawn_units(team, ck, cc, cx, y)
                if units and comp:      # remember each other (Lightning Link)
                    units[0].partner = comp[0]
                    comp[0].partner = units[0]

    def spawn_units(self, team, key, count, x, y, deploy=None):
        """Create `count` units of `key` around (x, y); returns them."""
        card = cards.CARDS[key]
        made = []
        if count <= 1:
            made.append(Entity(card, team, x, y, deploy=deploy))
        else:
            r = card.spawn_radius
            for i in range(count):
                ang = 2 * math.pi * i / count
                ox = max(0.4, min(cfg.GRID_COLS - 0.4, x + math.cos(ang) * r))
                oy = max(0.4, min(cfg.GRID_ROWS - 0.4, y + math.sin(ang) * r))
                made.append(Entity(card, team, ox, oy, deploy=deploy))
        self.entities.extend(made)
        # landing shockwave (Mega Knight slam, Electro Wizard zap, Ice Wizard)
        if card.spawn_damage:
            rad, dmg = card.spawn_damage
            self.effects.append(Effect("aoe", team, x, y, rad, 0.35,
                                       card_key=card.key))
            self.area_damage(team, x, y, rad, dmg, hit_air=True,
                             stun=card.spawn_stun, slow=card.spawn_slow)
        return made

    def _cast_spell(self, team, card, x, y):
        # spells no longer hit instantly: show an incoming marker for a short
        # delay, then _resolve_spell() applies the effect (see Effect.update).
        delay = cfg.SPELL_CAST_TIMES.get(card.key, cfg.SPELL_CAST_DELAY)
        self.effects.append(Effect("incoming", team, x, y,
                                   card.spell_radius or 1.2, delay,
                                   card_key=card.key))

    def _resolve_spell(self, team, card, x, y):
        fwd = -1 if team == PLAYER else 1
        # troop-dropping spell (Goblin Barrel)
        if card.spawn_troops and not card.rolling:
            self.spawn_units(team, card.spawn_troops[0], card.spawn_troops[1],
                             x, y, deploy=0.0)
            return
        # graveyard: keeps spawning skeletons in the area over its duration
        if card.graveyard:
            self.effects.append(Effect("graveyard", team, x, y, card.spell_radius,
                                       card.duration))
            return
        # tornado: drag enemy troops to the center while ticking damage
        if card.pull > 0:
            self.effects.append(Effect("tornado", team, x, y, card.spell_radius,
                                       card.duration, dps=card.spell_damage,
                                       speed=card.pull))
            return
        if card.rolling:
            self.effects.append(Effect("log", team, x, y, card.spell_radius, 1.4,
                                       direction=fwd, speed=6.0,
                                       damage=card.spell_damage, knockback=card.knockback))
            if card.spawn_troops:   # Barbarian Barrel drops a barbarian
                self.spawn_units(team, card.spawn_troops[0], card.spawn_troops[1],
                                 x, y, deploy=0.0)
            return
        if card.rage:
            self.effects.append(Effect("rage", team, x, y, card.spell_radius, card.duration))
            return
        if card.dot:
            bm = 2.2 if card.key == "earthquake" else 0.4  # earthquake shreds buildings
            self.effects.append(Effect("poison", team, x, y, card.spell_radius,
                                       card.duration, dps=card.spell_damage,
                                       slow=card.slow, building_mult=bm))
            return
        # instant-hit spells (arrows/fireball/zap/rocket/lightning/freeze/snowball)
        self.area_damage(team, x, y, card.spell_radius, card.spell_damage,
                         hit_air=True, stun=card.stun, freeze=card.freeze,
                         slow=card.slow, tower_damage=card.tower_dmg(),
                         knockback=card.knockback)

    # ---- combat helpers ----------------------------------------------------
    def apply_hit(self, source, target, dmg, splash, stun=0.0, slow=None):
        if splash > 0:
            # Valkyrie-style spin: splash centered on the attacker, not target
            cx, cy = (source.x, source.y) if source.card.splash_self else (target.x, target.y)
            self.effects.append(Effect("aoe", source.team, cx, cy,
                                       splash, 0.3, card_key=source.key))
            self.area_damage(source.team, cx, cy, splash, dmg,
                             hit_air=(source.attacks == "air_ground"), stun=stun, slow=slow)
        else:
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
                if (e.is_tower or e.is_building) and tower_damage is not None:
                    amount = tower_damage
                e.take_damage(amount)
                if stun:
                    e.stun_timer = max(e.stun_timer, stun)
                if freeze:
                    e.freeze_timer = max(e.freeze_timer, freeze)
                if slow:
                    e.slow_factor = slow[0]
                    e.slow_timer = slow[1]
                if knockback and not (e.is_tower or e.is_building):
                    ox, oy = kb_from if kb_from is not None else (x, y)
                    dx, dy = e.x - ox, e.y - oy
                    dd = math.hypot(dx, dy) or 1.0
                    e.x += dx / dd * knockback
                    e.y += dy / dd * knockback

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
        return hits

    # ---- champions ---------------------------------------------------------
    def _collect_souls(self, dead):
        """Skeleton Kings gain a soul for each nearby unit death (capped)."""
        for e in self.entities:
            if (e.alive and e.card.ability_type == "skeletons"
                    and dist(e.x, e.y, dead.x, dead.y) <= 5.0):
                e.souls = min(e.souls + 1, 10)

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
        champ.ability_uses -= 1
        champ.ability_cd = card.ability_cooldown
        self._do_ability(champ, card)
        return True

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
                                 champ.y + fwd * 0.8, deploy=0.0)[0]
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
            self.spawn_units(team, "skeleton", n, champ.x, champ.y, deploy=0.0)
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
            # inside her dash window, so she can dash in again right away
            t = self._getaway_anchor(champ)
            nx, ny = self.getaway_point(champ, t, card.ability_value)
            for (ex, ey) in ((champ.x, champ.y), (nx, ny)):
                self.effects.append(Effect("aoe", team, ex, ey, 1.0, 0.45,
                                           card_key="tornado"))
            champ.x, champ.y = nx, ny
            champ.target = t
            champ.dash_cd = 0.0
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

    def find_target(self, ent):
        """Nearest attackable enemy in sight; else march to nearest enemy tower."""
        best = None
        best_d = 1e9
        sight = ent.sight
        for e in self.entities:
            if not ent.can_attack(e):
                continue
            # don't chase a sleeping king while either of its princess towers stand
            if e.is_king and not e.active and any(
                    self.towers[(e.team, s)].alive for s in ("left", "right")):
                continue
            d = dist(ent.x, ent.y, e.x, e.y)
            if ent.is_tower or ent.is_building:
                if d <= ent.range + e.radius and d < best_d:
                    best, best_d = e, d
            else:
                if d <= sight + e.radius and d < best_d:
                    best, best_d = e, d
        if best is not None:
            return best
        # no one in sight: buildings/towers just wait
        if ent.is_tower or ent.is_building:
            return None
        # march toward nearest enemy tower (win-condition & normal troops)
        for key, tw in self.towers.items():
            if tw.team == ent.team or not tw.alive:
                continue
            if tw.is_king and not tw.active and any(
                    self.towers[(tw.team, s)].alive for s in ("left", "right")):
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

        for e in list(self.entities):
            e.update(dt, self)
            # Electro Giant counter-zap: took a hit -> zap everything nearby
            if e.card.reflect:
                e.reflect_cd = max(0.0, e.reflect_cd - dt)
                if e.alive and e._reflect_pending and e.reflect_cd <= 0:
                    rad, rdmg, rstun = e.card.reflect
                    self.effects.append(Effect("aoe", e.team, e.x, e.y,
                                               rad, 0.3, card_key=e.key))
                    self.area_damage(e.team, e.x, e.y, rad, rdmg,
                                     hit_air=True, stun=rstun)
                    e.reflect_cd = 0.6
                    e._reflect_pending = False
        for p in list(self.projectiles):
            p.update(dt, self)
        for fx in list(self.effects):
            fx.update(dt, self)

        # process deaths
        for e in list(self.entities):
            if not e.alive and not e._death_done:
                e._death_done = True
                if e.is_tower:
                    self._on_tower_destroyed(e)
                else:
                    self._collect_souls(e)
                    e.on_death(self)

        self.entities = [e for e in self.entities if e.alive]
        self.projectiles = [p for p in self.projectiles if p.alive]
        self.effects = [fx for fx in self.effects if fx.alive]

        # timer
        self.time_left -= dt
        if self.time_left <= 0:
            self._advance_phase()

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
