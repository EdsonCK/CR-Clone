"""
============================================================================
  EVO_ENGINE.PY  --  What Evolutions and Heroes actually DO in a match
============================================================================

engine.py calls the small hook functions below at fixed moments (a unit
spawning, attacking, being hit, dying, a projectile landing, a spell
resolving). Each checks `e.evo` / `e.hero` and the card key, so cards
without an Evolution are untouched. Numbers are in tiles / seconds / hp and
scale with the unit's level via e.power.

Timed follow-ups (a second Zap, a bouncing bomb...) go through
Match.later_add(), which stores plain data (no lambdas) so the AI's
deep-copied simulations stay independent.
============================================================================
"""

import math
import random

import cards
import evos

PLAYER, ENEMY = 0, 1


def _d(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def _push(e, fromx, fromy, amount):
    if e.is_tower or e.is_building or not e.alive:
        return
    dx, dy = e.x - fromx, e.y - fromy
    dd = math.hypot(dx, dy) or 1.0
    e.x += dx / dd * amount
    e.y += dy / dd * amount


def _enemies(match, e, radius, ground_only=False, troops_only=False):
    out = []
    for o in match.entities:
        if not o.alive or o.team == e.team:
            continue
        if ground_only and o.flying:
            continue
        if troops_only and (o.is_tower or o.is_building):
            continue
        if _d(o, e) <= radius + o.radius * 0.5:
            out.append(o)
    return out


def _fx(match, kind, team, x, y, radius, dur=0.35, key=None):
    from engine import Effect
    match.effects.append(Effect(kind, team, x, y, radius, dur, card_key=key))


# ===================================================================== spawn
def on_spawn_group(match, units, card, evo=False, hero=False):
    """Units from one play. Marks evo / hero units and applies on-deploy
    effects (Tesla shockwave, Cannon barrage, Skeleton General...)."""
    if not units:
        return
    for e in units:
        e.evo = evo
    if evo:
        k = card.key
        if k == "skeleton_army":
            for e in units:
                e.max_hp = int(e.max_hp * 1.5)
                e.hp = e.max_hp
            g = units[0]
            g.general = True
            g.shield = int(300 * g.power[0])
        elif k == "battle_ram":
            for e in units:
                e.charged = True
                e.base_speed *= 1.3
        elif k == "musketeer":
            for e in units:
                e.range += 3.0
                e.sight += 3.0
                e.evo_shots = 3
        elif k == "wizard":
            for e in units:
                e.shield = int(200 * e.power[0])
        elif k == "tesla":
            _tesla_wave(match, units[0])
        elif k == "cannon":
            _cannon_barrage(match, units[0])
    if hero and units:
        h = units[0]
        h.hero = True
        h.hero_def = evos.HEROES.get(card.key)
        h.ability_uses = 1
        h.ability_cd = 0.0


def _tesla_wave(match, e):
    _fx(match, "aoe", e.team, e.x, e.y, 3.0, 0.45, "tesla")
    match.area_damage(e.team, e.x, e.y, 3.0, 90 * e.power[1], hit_air=True, stun=0.5)
    match.emit("ability", e.key, e.x, e.y, e.team)


def _cannon_barrage(match, e):
    from engine import Projectile
    tg = sorted(_enemies(match, e, 6.0, ground_only=True), key=lambda o: _d(o, e))[:6]
    for o in tg:
        match.projectiles.append(Projectile(e.team, e.x, e.y, o, e.dmg, 0, "ground",
                                            0.0, None, style="cannon", owner=e))


# ==================================================================== attack
def before_attack(e, match, dmg):
    """Return the (possibly boosted) damage of the attack about to happen."""
    if not e.evo:
        return dmg
    k = e.key
    if k == "archers" and e.target is not None and _d(e, e.target) >= 4.0:
        return dmg * 1.5
    if k == "musketeer" and getattr(e, "evo_shots", 0) > 0:
        e.evo_shots -= 1
        if e.evo_shots == 0:
            e.range -= 3.0
            e.sight -= 3.0
        return dmg * 1.5
    return dmg


def after_attack(e, match, dmg):
    """Called after a non-kamikaze attack has been carried out."""
    if not e.evo:
        return
    k = e.key
    t = e.target
    if k == "skeletons":
        alive = sum(1 for o in match.entities
                    if o.alive and o.team == e.team and o.key == "skeletons" and o.evo)
        if alive < 8:
            a = random.uniform(0, math.tau)
            new = match.spawn_units(e.team, "skeletons", 1, e.x + math.cos(a) * 0.6,
                                    e.y + math.sin(a) * 0.6, deploy=0.0,
                                    power=e.power, level=e.level)
            for n in new:
                n.evo = True
    elif k == "barbarians":
        e.rage_timer = max(e.rage_timer, 3.0)
    elif k == "bats":
        e.hp = min(e.max_hp * 1.5, e.hp + dmg)
    elif k == "valkyrie":
        for o in _enemies(match, e, 3.0, ground_only=True, troops_only=True):
            dd = _d(o, e)
            if dd > 1.0:
                pull = min(0.6, dd - 1.0)
                o.x += (e.x - o.x) / dd * pull
                o.y += (e.y - o.y) / dd * pull
    elif k == "royal_giant":
        for o in _enemies(match, e, 2.5, ground_only=True, troops_only=True):
            _push(o, e.x, e.y, 1.0)
    elif k == "mega_knight" and t is not None:
        _push(t, e.x, e.y, 2.0)
    elif k == "executioner":
        for o in _enemies(match, e, 1.8, ground_only=True, troops_only=True):
            _push(o, e.x, e.y, 1.5)


def on_new_target(e, target, match):
    if e.evo and e.key == "hunter" and target.alive and not target.is_tower:
        target.stun_timer = max(target.stun_timer, 1.5)
        _fx(match, "aoe", e.team, target.x, target.y, 0.8, 0.4, "hunter")


def taken_damage_mult(e, match):
    """Damage multiplier for hits this unit takes."""
    if e.evo and e.key == "knight" and match is not None:
        if match.elapsed - e.atk_t > 1.2:          # not mid-swing
            return 0.4
    if getattr(e, "hero_guard", 0) > 0:            # Hero Knight taunt
        return 0.3
    return 1.0


def after_damaged(e, match, shield_before):
    if not e.evo or match is None:
        return
    k = e.key
    if k == "wizard" and shield_before > 0 and e.shield <= 0 and not getattr(e, "_blast", False):
        e._blast = True
        _fx(match, "aoe", e.team, e.x, e.y, 2.5, 0.45, "fireball")
        match.area_damage(e.team, e.x, e.y, 2.5, 150 * e.power[1], hit_air=True,
                          knockback=1.5)
    elif k == "goblin_giant" and e.alive and e.hp < e.max_hp / 2 and not getattr(e, "_half", False):
        e._half = True
        match.spawn_units(e.team, "spear_goblin", 2, e.x, e.y + 0.6, deploy=0.0,
                          power=e.child_power(), level=e.level)


def on_projectile_hit(proj, target, match):
    o = proj.owner
    if o is None or not getattr(o, "evo", False):
        return
    if o.key == "dart_goblin" and target.alive and not target.is_tower:
        target.poison_t = min(getattr(target, "poison_t", 0.0) + 3.0, 9.0)
        target.poison_dps = 30 * o.power[1]


def on_projectile_impact(proj, match):
    o = proj.owner
    if o is None or not getattr(o, "evo", False):
        return
    if o.key == "bomber":
        for i, delay in ((1, 0.35), (2, 0.7)):
            match.later_add(delay, "blast", team=proj.team,
                            x=proj.x + proj.vx * 1.8 * i, y=proj.y + proj.vy * 1.8 * i,
                            radius=proj.splash or 1.5, dmg=proj.dmg, key="bomber",
                            air=False)
    elif o.key == "mortar":
        match.spawn_units(proj.team, "goblin", 1, proj.x, proj.y, deploy=0.3,
                          power=o.power, level=o.level)


def chain_targets(proj_owner, base):
    if proj_owner is not None and getattr(proj_owner, "evo", False) \
            and proj_owner.key == "electro_dragon":
        return 6
    return base


# ===================================================================== death
def on_death(e, match):
    k = e.key
    if e.evo:
        if k == "tesla":
            _tesla_wave(match, e)
        elif k == "wall_breakers" and not getattr(e, "runner", False):
            new = match.spawn_units(e.team, "wall_breakers", 1, e.x, e.y, deploy=0.2,
                                    power=e.power, level=e.level)
            for n in new:
                n.runner = True
        elif k == "ice_spirit":
            match.later_add(2.0, "blast", team=e.team, x=e.x, y=e.y, radius=1.5,
                            dmg=0, key="ice_spirit", air=True, freeze=1.0)
    # Evolved Witch heals whenever one of her skeletons falls nearby
    if k in ("skeleton", "skeletons"):
        for w in match.entities:
            if (w.alive and w.team == e.team and w.key == "witch" and w.evo
                    and _d(w, e) <= 5.0):
                w.hp = min(w.max_hp, w.hp + 80 * w.power[0])
    # Evolved P.E.K.K.A heals on every troop she defeats
    killer = getattr(e, "last_hitter", None)
    if (killer is not None and killer.alive and getattr(killer, "evo", False)
            and killer.key == "pekka" and not e.is_tower and not e.is_building):
        killer.hp = min(killer.max_hp, killer.hp + killer.max_hp * 0.3)
        _fx(match, "aoe", killer.team, killer.x, killer.y, 1.0, 0.4, "heal_spirit")


def lumberjack_rage(e):
    """(radius, duration) of the Lumberjack's death rage."""
    return (4.5, 8.0) if e.evo else (3.0, 4.0)


def spawner_count(e, n):
    return n * 2 if (e.evo and e.key == "furnace") else n


def keeps_ramp(e):
    return e.evo and e.key == "inferno_dragon"


# =================================================================== per tick
def tick(e, dt, match):
    """Continuous effects (auras, poison, hero buffs)."""
    if getattr(e, "poison_t", 0) > 0:
        e.poison_t -= dt
        e.take_damage(getattr(e, "poison_dps", 0) * dt)
    if getattr(e, "haste_timer", 0) > 0:
        e.haste_timer -= dt
    if getattr(e, "hero_guard", 0) > 0:
        e.hero_guard -= dt
    if getattr(e, "hero_spin", 0) > 0:
        e.hero_spin -= dt
        e._spin_t = getattr(e, "_spin_t", 0.0) - dt
        if e._spin_t <= 0:
            e._spin_t = 0.25
            _fx(match, "aoe", e.team, e.x, e.y, 2.0, 0.2, "valkyrie")
            for o in _enemies(match, e, 2.4, ground_only=True):
                o.take_damage(e.dmg * 0.45)
                if not (o.is_tower or o.is_building):
                    dd = _d(o, e)
                    if dd > 0.9:
                        o.x += (e.x - o.x) / dd * 0.25
                        o.y += (e.y - o.y) / dd * 0.25
    if e.evo and e.key == "baby_dragon":
        e._aura_t = getattr(e, "_aura_t", 0.0) - dt
        if e._aura_t <= 0:
            e._aura_t = 0.25
            for o in match.entities:
                if not o.alive or o.is_tower or _d(o, e) > 3.5:
                    continue
                if o.team != e.team:
                    o.slow_factor = min(o.slow_factor, 0.7)
                    o.slow_timer = max(o.slow_timer, 0.4)
                else:
                    o.haste_timer = 0.4


# ==================================================================== spells
def on_spell(match, team, card, x, y, evo, power):
    if not evo:
        return
    k = card.key
    fwd = -1 if team == PLAYER else 1
    if k == "zap":
        match.later_add(0.5, "blast", team=team, x=x, y=y, radius=card.spell_radius,
                        dmg=card.spell_damage * power[1], key="zap", air=True,
                        stun=card.stun, tower_dmg=card.tower_dmg() * power[1])
    elif k == "goblin_barrel":
        ox = 2.2 if x < 9 else -2.2
        match.later_add(0.7, "spawn", team=team, x=x + ox, y=y + fwd * 0.5,
                        key="goblin", count=3, power=(power[0] * card.sub_hp_mult,
                                                      power[1] * card.sub_dmg_mult))
    elif k == "snowball":
        for o in match.entities:
            if (o.alive and o.team != team and not o.is_tower and not o.is_building
                    and math.hypot(o.x - x, o.y - y) <= card.spell_radius + 0.3):
                o.y += fwd * 2.5


# ===================================================================== heroes
def hero_ready(h, match):
    """Can the hero's ability be used right now?"""
    if h is None or not h.alive or h.ability_uses <= 0 or h.is_dashing():
        return False
    k = h.key
    if k == "giant":
        return any(not o.flying for o in _enemies(match, h, 3.0, troops_only=True))
    return True


def do_hero_ability(h, match):
    k = h.key
    p = h.power
    match.emit("ability", k, h.x, h.y, h.team)
    if k == "knight":
        h.hero_guard = 4.0
        for o in _enemies(match, h, 5.0, troops_only=True):
            if o.can_attack(h):
                o.target = h
                o._taunt = 4.0
        _fx(match, "aoe", h.team, h.x, h.y, 5.0, 0.5, "knight")
    elif k == "giant":
        tg = [o for o in _enemies(match, h, 3.0, troops_only=True) if not o.flying]
        if tg:
            o = max(tg, key=lambda q: q.max_hp)
            dx, dy = o.x - h.x, o.y - h.y
            dd = math.hypot(dx, dy) or 1.0
            fwd = -1 if h.team == PLAYER else 1
            o.x = min(17.5, max(0.5, o.x + dx / dd * 2.0))
            o.y = min(31.5, max(0.5, o.y + fwd * 6.0))
            o.take_damage(300 * p[1])
            o.stun_timer = max(o.stun_timer, 1.0)
            _fx(match, "aoe", h.team, o.x, o.y, 1.5, 0.45, "giant")
    elif k == "mini_pekka":
        h.hp = min(h.max_hp * 1.1, h.hp + h.max_hp * 0.4)
        h.max_hp = int(h.max_hp * 1.1)
        h.dmg *= 1.1
        h.power = (h.power[0] * 1.1, h.power[1] * 1.1)
        if h.level is not None:
            h.level += 1
        _fx(match, "aoe", h.team, h.x, h.y, 1.2, 0.5, "heal_spirit")
    elif k == "musketeer":
        tur = match.spawn_units(h.team, "hero_turret", 1, h.x + 1.0, h.y, deploy=0.0,
                                power=p, level=h.level)
        _fx(match, "aoe", h.team, h.x + 1.0, h.y, 1.0, 0.4, "musketeer")
    elif k == "ice_golem":
        _fx(match, "aoe", h.team, h.x, h.y, 3.0, 0.6, "freeze")
        match.area_damage(h.team, h.x, h.y, 3.0, 50 * p[1], hit_air=True, freeze=2.0)
        match.later_add(2.0, "blast", team=h.team, x=h.x, y=h.y, radius=3.0, dmg=0,
                        key="snowball", air=True, slow=(0.65, 4.0))
    elif k == "goblins":
        match.spawn_units(h.team, "goblin", 3, h.x, h.y + 0.5, deploy=0.0,
                          power=p, level=h.level)
        match.effects_rage(h.team, h.x, h.y, 3.5, 6.0)
    elif k == "valkyrie":
        h.hero_spin = 3.0
        h._spin_t = 0.0
