"""
============================================================================
  EVO_ENGINE.PY  --  What Evolutions and Heroes actually DO in a match
============================================================================

engine.py calls the small hook functions below at fixed moments (a unit
spawning, attacking, being hit, dying, a projectile landing, a spell
resolving, every frame for evolved / hero units). Each checks `e.evo` /
`e.hero` and the card key, so cards without an Evolution are untouched.

All numbers are the real game's level-11 values converted into this game's
scale (hp and damage x0.506 - the same conversion used for the cards),
and every one of them is multiplied by the unit's level power (e.power), so
upgrades carry over. Distances and timings are the real ones.

Timed follow-ups (a second Zap, a bouncing bomb, a falling Skeletrooper...)
go through Match.later_add(), which stores plain data so the AI's
deep-copied simulations stay independent.
============================================================================
"""

import math
import random

import cards
import config as cfg
import evos

PLAYER, ENEMY = 0, 1

# real-game numbers -> this game's scale
HP = 0.506
DMG = 0.506          # one scale for hp and damage (real level-11 x 0.506)


def _d(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def _fwd(team):
    return -1 if team == PLAYER else 1


def _push(e, fromx, fromy, amount):
    if e.is_tower or e.is_building or not e.alive or e.card.no_knockback:
        return
    dx, dy = e.x - fromx, e.y - fromy
    dd = math.hypot(dx, dy) or 1.0
    e.x += dx / dd * amount
    e.y += dy / dd * amount
    if amount > 0:
        e.reset_charge()


def _enemies(match, e, radius, ground_only=False, troops_only=False, x=None, y=None,
             targetable=False):
    cx = e.x if x is None else x
    cy = e.y if y is None else y
    out = []
    for o in match.entities:
        if not o.alive or o.team == e.team:
            continue
        if ground_only and o.flying:
            continue
        if troops_only and (o.is_tower or o.is_building):
            continue
        if targetable and (o.untargetable or o.invis_timer > 0):
            continue
        if o.is_king and not o.active and troops_only is False and targetable:
            continue
        if math.hypot(o.x - cx, o.y - cy) <= radius + o.radius * 0.5:
            out.append(o)
    return out


def _nearest(match, e, radius, **kw):
    cands = _enemies(match, e, radius, targetable=True, **kw)
    return min(cands, key=lambda o: _d(o, e)) if cands else None


def _fx(match, kind, team, x, y, radius, dur=0.35, key=None):
    from engine import Effect
    fx = Effect(kind, team, x, y, radius, dur, card_key=key)
    match.effects.append(fx)
    return fx


def _hit(match, src, o, dmg, tower_mult=1.0):
    """Ability damage from `src` (credited to it in the match stats)."""
    prev = match._src, match._src_ent
    match._src, match._src_ent = (src.team, src.key), src
    o.take_damage(dmg * (tower_mult if o.is_tower else 1.0))
    match._src, match._src_ent = prev


def _blast(match, src, x, y, radius, dmg, tower_dmg=None, air=True, knockback=0.0,
           stun=0.0, slow=None, key=None, kb_from=None):
    prev = match._src, match._src_ent
    match._src, match._src_ent = (src.team, src.key), src
    _fx(match, "aoe", src.team, x, y, radius, 0.35, key or src.key)
    match.area_damage(src.team, x, y, radius, dmg, hit_air=air, stun=stun, slow=slow,
                      tower_damage=tower_dmg, knockback=knockback, kb_from=kb_from)
    match._src, match._src_ent = prev


def _clamp(x, y):
    return (min(max(x, 0.5), cfg.GRID_COLS - 0.5), min(max(y, 0.5), cfg.GRID_ROWS - 0.5))


def _level_up(e, n):
    """+n levels for a unit on the field (+10% hp and damage each)."""
    m = cards.level_mult(cards.LEVEL_BASE + n)
    e.max_hp = int(e.max_hp * m)
    e.hp = min(e.max_hp, e.hp * m)
    e.dmg *= m
    e.power = (e.power[0] * m, e.power[1] * m)
    if e.level is not None:
        e.level += n


def _ghost(e):
    """Untouchable spirit: can't be targeted or hurt, drawn see-through."""
    e.untargetable = True
    e.immortal = True
    e.ghostly = True


# =================================================================== spawn
def on_spawn_group(match, units, card, evo=False, hero=False):
    """Units from one play: mark evo / hero units, apply deploy effects."""
    if not units:
        return
    k = card.key
    if evo:
        for e in units:
            e.evo = True
            p0 = e.power[0]
            e.base_max = e.max_hp
            if k == "barbarians":
                e.max_hp = int(e.max_hp * 1.1)
                e.hp = e.max_hp
                e.base_max = e.max_hp
            elif k == "bats":
                e.max_hp = int(e.max_hp * 1.5)
                e.hp = e.max_hp
                e.base_max = e.max_hp
            elif k == "skeleton_barrel":
                e.max_hp = int(e.max_hp * 1.25)
                e.hp = e.max_hp
            elif k == "archers":
                e.range += 1.0
                e.sight += 1.0
            elif k == "musketeer":
                e.snipes = 3
            elif k == "wizard":
                e.shield = int(192 * HP * p0)
            elif k == "mortar":
                e.hit_speed = max(1.0, e.hit_speed - 1.0)
            elif k == "ice_spirit":
                e.blast_r = (card.death_damage[0] if card.death_damage else 1.5) + 0.5
            elif k == "royal_hogs":
                e.flying = True               # they fly in...
                e.hog_air = True
            elif k == "electro_giant":
                e.pulse_t = 2.5
            elif k == "goblin_drill":
                e.resurf = [0.66, 0.33]
            elif k == "minion_horde":
                e.mh_guard = True
            elif k == "royal_ghost":
                e.was_cloaked = True
            elif k == "hunter":
                e.net_cd = 0.5
            elif k == "elite_barbarians":
                e.spear_cd = 0.0
            elif k == "tesla":
                e.tesla_idle = 0.0
        if k == "skeleton_army":
            # General Gerry marches at the back of the army
            u0 = units[0]
            gx = sum(u.x for u in units) / len(units)
            gy = sum(u.y for u in units) / len(units) - _fwd(u0.team) * 1.6
            gx, gy = _clamp(gx, gy)
            g = match.spawn_units(u0.team, "skeleton_general", 1, gx, gy,
                                  deploy=u0.deploy_timer, power=u0.power,
                                  level=u0.level)[0]
            g.evo = True
            g.general = True
            for u in units:
                u.army_general = g
        elif k == "tesla":
            _tesla_pulse(match, units[0])
        elif k == "cannon":
            _cannon_barrage(match, units[0])
    if hero:
        hd = evos.HEROES.get(k)
        if k == "goblins":
            # the 4 goblins are the hero squad; their banner holds the ability
            for e in units:
                e.hero = True
                e.hero_def = hd
                e.ability_uses = 0
                e.hero_group = id(units[0])
            units[0].hero_group_lead = True
            return
        h = units[0]
        h.hero = True
        h.hero_def = hd
        h.ability_uses = 1
        h.ability_cd = 0.0
        if k == "mini_pekka":
            h.pancakes = 0.0


def _tesla_pulse(match, e):
    _blast(match, e, e.x, e.y, 6.0, 174 * DMG * e.power[1], tower_dmg=0, stun=0.5,
           key="tesla")
    match.emit("ability", e.key, e.x, e.y, e.team)


def _cannon_barrage(match, e):
    """9 cannonballs: a row of 5 then a row of 4, in front of the cannon."""
    f = _fwd(e.team)
    dmg = 304 * DMG * e.power[1]
    tdm = 89 * DMG * e.power[1]
    spots = [(dx * 2.2, 3.5) for dx in (-2, -1, 0, 1, 2)] + \
            [(dx * 2.2, 6.0) for dx in (-1.5, -0.5, 0.5, 1.5)]
    for i, (ox, oy) in enumerate(spots):
        x, y = _clamp(e.x + ox, e.y + f * oy)
        match.later_add(0.25 + 0.06 * i, "blast", team=e.team, x=x, y=y, radius=2.0,
                        dmg=dmg, key="cannon", air=False, tower_dmg=tdm)
        match.later_add(0.26 + 0.06 * i, "evo_push", team=e.team, x=x, y=y,
                        radius=2.0, amount=1.0)


# ==================================================================== attack
def before_attack(e, match, dmg):
    """Return the (possibly boosted) damage of the attack about to happen."""
    k = e.key
    t = e.target
    p1 = e.power[1]
    if e.evo:
        if k == "archers" and t is not None and 4.0 <= _d(e, t) - t.radius * 0.5 <= 6.5:
            dmg *= 1.25                                     # Power Shot
        elif k == "princess":
            e.pr_shots = getattr(e, "pr_shots", 0) + 1
            e.pr_chill = (e.pr_shots % 2 == 1)              # 1st, 3rd, 5th...
    if e.hero:
        if getattr(e, "berserk_t", 0) > 0:
            dmg = 167 * DMG * p1                            # bear claws
            if t is not None and t.is_tower:
                dmg *= 0.25
        if getattr(e, "ma_triple", False):
            dmg = 48 * DMG * p1                             # 3 long arrows
        if getattr(e, "frosty", False) and t is not None and t.alive \
                and t.slow_timer > 0:
            _snowman(match, e, t)
    return dmg


def after_attack(e, match, dmg):
    """Called after a non-kamikaze attack has been carried out."""
    k = e.key
    t = e.target
    p0, p1 = e.power
    if e.hero:
        if k == "mini_pekka":
            e.pancakes = min(3.0, getattr(e, "pancakes", 0.0) + 10.0 / 22.0)
        if getattr(e, "ma_triple", False):
            e.ma_triple = False
            _triple_arrows(match, e, dmg)
    if not e.evo:
        return
    if k in ("skeletons", "skeleton"):
        alive = sum(1 for o in match.entities
                    if o.alive and o.team == e.team and o.key == e.key and o.evo)
        if alive < 8:
            a = random.uniform(0, math.tau)
            new = match.spawn_units(e.team, e.key, 1, e.x + math.cos(a) * 0.6,
                                    e.y + math.sin(a) * 0.6, deploy=0.0,
                                    power=e.power, level=e.level)
            for n in new:
                n.evo = True
    elif k in ("barbarians", "barbarian"):
        e.atk_buff, e.atk_buff_timer = 1.3, 5.0           # +30% for 5s
        e.haste_mult, e.haste_timer = 1.3, 5.0
    elif k == "bats":
        e.bat_heal = 2                                       # 2 pulses, 0.5s apart
        e.bat_heal_t = 0.0
    elif k == "valkyrie":
        from engine import Effect
        match.effects.append(Effect("tornado", e.team, e.x, e.y, 5.5, 0.5, dps=0,
                                    speed=4.0, card_key="valkyrie"))
        prev = match._src, match._src_ent
        match._src, match._src_ent = (e.team, e.key), e
        match.area_damage(e.team, e.x, e.y, 5.5, 84 * DMG * p1, hit_air=True,
                          tower_damage=37 * DMG * p1)
        match._src, match._src_ent = prev
    elif k == "royal_giant":
        _blast(match, e, e.x, e.y, 2.5, 81 * DMG * p1, air=True, knockback=1.0)
    elif k == "mega_knight" and t is not None:
        e.mk_n = getattr(e, "mk_n", 0) + 1
        if e.mk_n % 2 == 0 and t.alive and not (t.is_building or t.is_tower) \
                and not t.card.no_knockback:
            _uppercut(match, e, t)
    elif k == "executioner":
        for o in _enemies(match, e, 2.5, ground_only=True, troops_only=True):
            _hit(match, e, o, dmg * 0.75)
            _push(o, e.x, e.y, 1.5)
    elif k == "battle_ram" and t is not None and (t.is_building or t.is_tower):
        # bounce back off the building, then charge it again
        dx, dy = e.x - t.x, e.y - t.y
        dd = math.hypot(dx, dy) or 1.0
        bx, by = _clamp(e.x + dx / dd * 2.0, e.y + dy / dd * 2.0)
        e.start_dash(None, kind="point", point=(bx, by), speed=6.0, quiet=True)
        e.dist_since_attack = e.charge_dist
        e.charged = True
    elif k == "royal_hogs":
        _hog_land(match, e)
    elif k == "furnace":
        e.furnace_hot = match.elapsed


def _uppercut(match, e, t):
    """Evolved Mega Knight: launch `t` 4 tiles toward its own nearest tower."""
    towers = [tw for tw in match.towers.values() if tw.team == t.team and tw.alive]
    if towers:
        tw = min(towers, key=lambda q: _d(q, t))
        dx, dy = tw.x - t.x, tw.y - t.y
    else:
        dx, dy = 0.0, -_fwd(e.team)
    dd = math.hypot(dx, dy) or 1.0
    px, py = _clamp(t.x + dx / dd * 4.0, t.y + dy / dd * 4.0)
    t.start_dash(None, kind="point", point=(px, py), speed=10.0, quiet=True)
    t.stun_timer = max(t.stun_timer, 0.5)
    t.target = None
    _fx(match, "aoe", e.team, t.x, t.y, 1.0, 0.35, "mega_knight")


def _triple_arrows(match, e, dmg):
    """Hero Magic Archer: two more extra-long piercing arrows (3 in all)."""
    from engine import Projectile
    if e.target is None:
        return
    ang = math.atan2(e.target.y - e.y, e.target.x - e.x)
    for off in (-0.12, 0.12):
        a = ang + off
        dest = (e.x + math.cos(a) * 13.5, e.y + math.sin(a) * 13.5)
        match.projectiles.append(Projectile(
            e.team, e.x, e.y, None, dmg, 0, e.attacks, 0.0, None, style=e.key,
            homing=False, dest=dest, pierce=True, hit_radius=0.4, owner=e))


def _hog_land(match, e):
    if getattr(e, "hog_air", False):
        e.hog_air = False
        e.flying = False
        _blast(match, e, e.x, e.y, 1.5, 115 * DMG * e.power[1], air=False)


def on_new_target(e, target, match):
    return


def taken_damage_mult(e, match):
    """Damage multiplier for hits this unit takes."""
    m = 1.0
    if e.evo and e.key == "knight" and match is not None:
        if match.elapsed - e.atk_t > 1.3:          # not mid-swing
            m *= 0.4
    if getattr(e, "spin_t", 0) > 0:                # Hero Valkyrie whirlwind
        m *= 0.85
    return m


def after_damaged(e, match, shield_before):
    if match is None or not e.evo:
        return
    k = e.key
    p0, p1 = e.power
    if k == "wizard" and shield_before > 0 and e.shield <= 0 and not getattr(e, "_blast", False):
        e._blast = True
        _fx(match, "blast", e.team, e.x, e.y, 3.0, 0.45, "fireball")
        _blast(match, e, e.x, e.y, 3.0, 281 * DMG * p1, air=True, knockback=3.0,
               key="fireball")
    elif k == "royal_recruits" and shield_before > 0 and e.shield <= 0:
        e.charge_enabled = True                     # shield gone: CHARGE!
        e.charge_dist = 2.5
    elif k == "minion_horde" and getattr(e, "mh_guard", False) and e.hp > 0:
        e.mh_guard = False
        e.immune_timer = max(e.immune_timer, 3.0)
        e.invis_timer = max(e.invis_timer, 3.0)
        e.haste_mult, e.haste_timer = 0.67, 3.0
        e.atk_buff, e.atk_buff_timer = 1.5, 3.0
        _fx(match, "aoe", e.team, e.x, e.y, 0.8, 0.4, "minions")
    elif k == "royal_hogs":
        _hog_land(match, e)
    elif k == "skeleton_barrel" and not getattr(e, "drop75", False) \
            and e.hp <= e.max_hp * 0.75:
        e.drop75 = True
        _barrel_drop(match, e)
    elif k == "goblin_drill" and getattr(e, "resurf", None):
        while e.resurf and e.hp <= e.max_hp * e.resurf[0]:
            e.resurf.pop(0)
            _drill_resurface(match, e)


def _barrel_drop(match, e):
    cp = e.child_power()
    match.later_add(0.6, "blast", team=e.team, x=e.x, y=e.y, radius=2.0,
                    dmg=192 * DMG * e.power[1], key="skeleton_barrel", air=True)
    match.later_add(0.6, "spawn", team=e.team, x=e.x, y=e.y, key="skeleton",
                    count=7, power=cp)


def _drill_resurface(match, e):
    """Evolved Goblin Drill: leave a Goblin and pop up somewhere close."""
    gob = cards.CARDS["goblin_gang"]
    gp = (e.power[0] * gob.sub_hp_mult, e.power[1] * gob.sub_dmg_mult)
    match.spawn_units(e.team, "goblin", 1, e.x, e.y, deploy=0.2, power=gp,
                      level=e.level)
    towers = [tw for tw in match.towers.values()
              if tw.team != e.team and tw.alive and _d(tw, e) <= 5.0]
    if towers:
        tw = min(towers, key=lambda q: _d(q, e))
        a = math.atan2(e.y - tw.y, e.x - tw.x) + math.pi / 2
        r = max(_d(tw, e), 2.6)
        e.x, e.y = _clamp(tw.x + math.cos(a) * r, tw.y + math.sin(a) * r)
    _fx(match, "aoe", e.team, e.x, e.y, 1.0, 0.4, "earthquake")
    _blast(match, e, e.x, e.y, 2.0, 84 * DMG * e.power[1], air=False, knockback=1.0,
           tower_dmg=26 * DMG * e.power[1])
    match.emit("portal", e.key, e.x, e.y, e.team)


def on_projectile_hit(proj, target, match):
    o = proj.owner
    if o is None:
        return
    if o.evo and o.key == "dart_goblin":
        from engine import Effect
        o.darts = getattr(o, "darts", 0) + 1
        n = o.darts
        dmg, crown = ((307, 77) if n >= 7 else (115, 29) if n >= 4 else (51, 13))
        fx = Effect("poison", o.team, target.x, target.y, 1.5, 1.0,
                    dps=dmg * DMG * o.power[1], card_key="poison",
                    building_mult=crown / dmg)
        match.effects.append(fx)


def on_projectile_impact(proj, match):
    o = proj.owner
    if o is None:
        return
    k = o.key
    p1 = o.power[1]
    if o.evo and k == "bomber" and proj.style == "bomber":
        for i, delay in ((1, 0.35), (2, 0.7)):
            match.later_add(delay, "blast", team=proj.team,
                            x=min(max(proj.x + proj.vx * 2.5 * i, 0.4), cfg.GRID_COLS - 0.4),
                            y=min(max(proj.y + proj.vy * 2.5 * i, 0.4), cfg.GRID_ROWS - 0.4),
                            radius=proj.splash or 1.5, dmg=proj.dmg, key="bomber",
                            air=False)
    elif o.evo and k == "mortar":
        gob = cards.CARDS["goblin_gang"]
        match.spawn_units(proj.team, "goblin", 1, proj.x, proj.y, deploy=0.2,
                          power=(o.power[0] * gob.sub_hp_mult, o.power[1] * gob.sub_dmg_mult),
                          level=o.level)
    elif o.evo and k == "firecracker":
        from engine import Effect
        big = proj.style == "firecracker"
        rad, dur = (2.5, 3.0) if big else (1.2, 2.5)
        match.effects.append(Effect("poison", proj.team, proj.x, proj.y, rad, dur,
                                    dps=48 * DMG * p1 * 4, slow=(0.8, 0.3),
                                    building_mult=15 / 48, card_key="firecracker"))
    elif o.evo and k == "princess" and getattr(o, "pr_chill", False):
        prev = match._src
        _fx(match, "aoe", proj.team, proj.x, proj.y, 3.0, 0.5, "freeze")
        match.area_damage(proj.team, proj.x, proj.y, 3.0, 0, hit_air=True,
                          slow=(0.7, 5.5))
        match._src = prev
    elif o.hero and k == "wizard" and getattr(o, "flight_t", 0) > 0:
        from engine import Effect
        match.effects.append(Effect("tornado", proj.team, proj.x, proj.y, 3.0, 2.0,
                                    dps=43 * DMG * p1 / 2.0, speed=2.0,
                                    card_key="wizard"))
    elif o.hero and proj.style == "bowler_barrage":
        _blast(match, o, proj.x, proj.y, 1.8, 508 * DMG * p1,
               tower_dmg=254 * DMG * p1, air=False, knockback=1.0, key="bowler")


def chain_targets(proj_owner, base):
    if proj_owner is not None and getattr(proj_owner, "evo", False) \
            and proj_owner.key == "electro_dragon":
        return 3
    return base


def after_chain(proj, match):
    """Evolved Electro Dragon: the bolt keeps bouncing (weaker, no stun)."""
    o = proj.owner
    if o is None or o.key != "electro_dragon":
        return
    pts = getattr(match, "_last_chain", None)
    if not pts or len(pts) < 2:
        return
    (px, py), (x, y) = pts[-2], pts[-1]
    match.later_add(0.4, "bounce", team=proj.team, x=x, y=y, px=px, py=py,
                    dmg=proj.dmg * 0.67, left=10, key="electro_dragon")


# ===================================================================== later
LATER_KINDS = {"bounce", "evo_push", "evo_spawn", "trooper"}


def run_later(match, kind, d):
    team = d["team"]
    if kind == "bounce":
        best, bd = None, 4.0
        for e in match.entities:
            if (not e.alive or e.team == team or e.is_tower or e.is_building
                    or e.untargetable or e.invis_timer > 0):
                continue
            if math.hypot(e.x - d["x"], e.y - d["y"]) < 0.35:
                continue                                    # the one just hit
            dd = math.hypot(e.x - d["x"], e.y - d["y"])
            if dd < bd:
                best, bd = e, dd
        if best is None:
            return
        from engine import Effect
        best.take_damage(d["dmg"])
        match.effects.append(Effect("chain", team, d["x"], d["y"], 0, 0.3,
                                    card_key=d.get("key"),
                                    points=[(d["x"], d["y"]), (best.x, best.y)]))
        if d["left"] > 1:
            match.later_add(0.4, "bounce", team=team, x=best.x, y=best.y,
                            px=d["x"], py=d["y"], dmg=d["dmg"], left=d["left"] - 1,
                            key=d.get("key"))
    elif kind == "evo_push":
        for e in match.entities:
            if (e.alive and e.team != team and not e.is_tower and not e.is_building
                    and not e.flying
                    and math.hypot(e.x - d["x"], e.y - d["y"]) <= d["radius"]):
                _push(e, d["x"], d["y"], d["amount"])
    elif kind == "evo_spawn":
        made = match.spawn_units(team, d["key"], d["count"], d["x"], d["y"],
                                 deploy=d.get("deploy", 0.0), power=d.get("power"),
                                 level=d.get("level"))
        for u in made:
            if d.get("evo"):
                u.evo = True
    elif kind == "trooper":
        # Hero Balloon's Skeletrooper lands: thump, then fights on
        prev = match._src
        match._src = (team, "balloon")
        match.effects.append(_mk_aoe(team, d["x"], d["y"], 1.5))
        match.area_damage(team, d["x"], d["y"], 1.5, d["dmg"], hit_air=False,
                          tower_damage=d["tower_dmg"])
        match._src = prev
        match.emit("land", "skeletrooper", d["x"], d["y"], team, slam=True)
        match.spawn_units(team, "skeletrooper", 1, d["x"], d["y"], deploy=0.3,
                          power=d.get("power"), level=d.get("level"))


def _mk_aoe(team, x, y, r):
    from engine import Effect
    return Effect("aoe", team, x, y, r, 0.4, card_key="balloon")


# ===================================================================== death
def on_death(e, match):
    k = e.key
    p0, p1 = e.power
    if e.evo:
        if k == "wall_breakers":
            if not getattr(e, "_exploded", False):
                _blast(match, e, e.x, e.y, 1.5, 291 * DMG * p1, tower_dmg=193 * DMG * p1,
                       air=False)
            match.spawn_units(e.team, "wb_runner", 1, e.x, e.y, deploy=0.3,
                              power=e.power, level=e.level)
        elif k == "ice_spirit" and getattr(e, "_exploded", False):
            dd = e.card.death_damage[1] * p1 if e.card.death_damage else e.dmg
            match.later_add(3.0, "blast", team=e.team, x=e.x, y=e.y,
                            radius=getattr(e, "blast_r", 2.0), dmg=dd, key="ice_spirit",
                            air=True, freeze=1.1)
        elif k == "lumberjack":
            g = match.spawn_units(e.team, "lumberjack_ghost", 1, e.x, e.y, deploy=0.2,
                                  power=e.power, level=e.level)[0]
            _ghost(g)
        elif k == "baby_dragon":
            from engine import Effect
            match.effects.append(Effect("wind", e.team, e.x, e.y, 4.5, 2.0,
                                        card_key="baby_dragon"))
        elif k == "battle_ram":
            for b in getattr(e, "_death_spawned", []):
                b.evo = True
                b.max_hp = int(b.max_hp * 1.1)
                b.hp = b.max_hp
                b.base_max = b.max_hp
        elif k == "skeleton_barrel":
            match.later_add(0.5, "blast", team=e.team, x=e.x, y=e.y, radius=2.0,
                            dmg=192 * DMG * p1, key="skeleton_barrel", air=True)
            _blast(match, e, e.x, e.y, 2.0, 192 * DMG * p1, air=True)
            match.spawn_units(e.team, "skeleton", 1, e.x, e.y, deploy=0.0,
                              power=e.child_power(), level=e.level)   # 7th skeleton
        elif k == "goblin_cage":
            pr = getattr(e, "prisoner", None)
            if pr is not None and pr.alive:
                pr.root_timer = 0.0
        elif k == "princess":
            from engine import Effect
            match.effects.append(Effect("poison", e.team, e.x, e.y, 3.0, 4.0,
                                        dps=e.dmg * 0.25, slow=(0.7, 0.4),
                                        building_mult=0.3, card_key="freeze"))
        elif getattr(e, "general", False):
            # General Gerry falls: every shadow of his army fades with him
            for o in match.entities:
                if o.alive and getattr(o, "shadow_of", None) is e:
                    o.immortal = False
                    o.alive = False
    # Evolved Skeleton Army: fallen skeletons rise as untouchable shadows
    g = getattr(e, "army_general", None)
    if g is not None and g.alive and not getattr(e, "shadow_of", None):
        s = match.spawn_units(e.team, e.key, 1, e.x, e.y, deploy=0.3, power=e.power,
                              level=e.level)[0]
        _ghost(s)
        s.shadow_of = g
    # Evolved Witch heals whenever one of HER skeletons falls
    par = getattr(e, "parent", None)
    if (par is not None and par.alive and par.evo and par.key == "witch"
            and k in ("skeleton", "skeletons")):
        cap = getattr(par, "base_max", par.max_hp) * 1.24
        par.hp = min(cap, par.hp + 76 * HP * par.power[0])
        par.max_hp = max(par.max_hp, int(par.hp))
        _fx(match, "aoe", par.team, par.x, par.y, 0.8, 0.35, "heal_spirit")
    # kills
    killer = getattr(e, "last_hitter", None)
    if killer is not None and killer.alive and getattr(killer, "evo", False) \
            and killer.team != e.team and not e.is_tower:
        if killer.key == "pekka":
            vhp = e.max_hp / max(e.power[0], 1e-6)
            heal = 160 if vhp < 990 * HP else 305 if vhp < 1991 * HP else 577
            cap = getattr(killer, "base_max", killer.max_hp) * 1.5
            killer.hp = min(cap, killer.hp + heal * HP * killer.power[0])
            killer.max_hp = max(killer.max_hp, int(killer.hp))
            _fx(match, "aoe", killer.team, killer.x, killer.y, 1.0, 0.45, "heal_spirit")
        elif killer.key == "inferno_dragon":
            killer.keep_t = 9.0
    # Hero Goblins: the last one plants the banner
    if e.hero and k in ("goblin", "goblins"):
        grp = getattr(e, "hero_group", None)
        if grp is not None and not any(
                o.alive and o is not e and getattr(o, "hero_group", None) == grp
                for o in match.entities):
            b = match.spawn_units(e.team, "goblin_banner", 1, e.x, e.y, deploy=0.0,
                                  power=e.power, level=e.level)[0]
            b.hero = True
            b.hero_def = evos.HEROES["goblins"]
            b.ability_uses = 1
            b.hero_goblin_pow = e.power
    # Hero Balloon: its bomb drops and blows up 3s later
    if e.hero and k == "balloon":
        match.later_add(3.0, "blast", team=e.team, x=e.x, y=e.y, radius=3.0,
                        dmg=240 * DMG * p1, key="balloon", air=True)


def lumberjack_rage(e):
    """(radius, duration) of the Lumberjack's death rage."""
    return (3.0, 5.5) if e.evo else (3.0, 4.0)


def spawner_count(e, n):
    return n


def spawner_interval(e, base, match):
    if e.evo and e.key == "furnace" and match.elapsed - getattr(e, "furnace_hot", -9) < 2.5:
        return 2.4                                   # stoked while fighting
    return base


def spawner_offset(e, match):
    """Where a spawner's units appear relative to it."""
    f = _fwd(e.team)
    if e.evo and e.key == "furnace":
        e._side = -getattr(e, "_side", 1)
        return e._side * 1.1, 0.0                    # to her sides
    return 0.0, f * 1.2


def keeps_ramp(e):
    return e.evo and e.key == "inferno_dragon" and getattr(e, "keep_t", 0) > 0


def ramp_bonus(e):
    """Evolved Inferno Dragon's 4th stage after 20s of burning."""
    if e.evo and e.key == "inferno_dragon" and e.ramp_time >= 20.0:
        return 2.0
    return 1.0


# =================================================================== per tick
def tick(e, dt, match):
    """Continuous effects (auras, timers, hero abilities)."""
    if e.haste_timer > 0:
        e.haste_timer -= dt
        if e.haste_timer <= 0:
            e.haste_mult = 1.15
    if e.undying_t > 0:
        e.undying_t -= dt
    k = e.key
    p0, p1 = e.power
    if e.evo:
        if k == "baby_dragon":
            _wind(e, dt, match, e.x, e.y)
        elif k == "bats" and getattr(e, "bat_heal", 0) > 0:
            e.bat_heal_t -= dt
            if e.bat_heal_t <= 0:
                e.bat_heal -= 1
                e.bat_heal_t = 0.5
                cap = getattr(e, "base_max", e.max_hp) * 2.0
                e.hp = min(cap, e.hp + 38 * HP * p0)
                e.max_hp = max(e.max_hp, int(e.hp))
        elif k == "tesla":
            if e.target is None:
                e.tesla_idle = getattr(e, "tesla_idle", 0.0) + dt
            else:
                if getattr(e, "tesla_idle", 0.0) >= 1.5:
                    _tesla_pulse(match, e)               # pops back up: pulse
                e.tesla_idle = 0.0
        elif k == "musketeer" and getattr(e, "snipes", 0) > 0:
            _snipe(e, match)
        elif k == "hunter":
            e.net_cd = getattr(e, "net_cd", 0.0) - dt
            if e.net_cd <= 0 and e.deploy_timer <= 0:
                o = _nearest(match, e, 4.0, troops_only=True)
                if o is not None:
                    e.net_cd = 5.0
                    o.root_timer = max(o.root_timer, 3.0)
                    if o.flying:
                        o.flying = False
                        o._grounded = True
                    _fx(match, "aoe", e.team, o.x, o.y, 0.8, 0.5, "hunter")
                    match.emit("attack", "hunter", e.x, e.y, e.team)
        elif k == "goblin_giant" and e.hp < e.max_hp * 0.5:
            e.gg_t = getattr(e, "gg_t", 0.0) - dt
            if e.gg_t <= 0:
                e.gg_t = 2.2
                gob = cards.CARDS["goblin_gang"]
                match.spawn_units(e.team, "goblin", 1, e.x, e.y - _fwd(e.team) * 0.8,
                                  deploy=0.2, power=(p0 * gob.sub_hp_mult,
                                                     p1 * gob.sub_dmg_mult),
                                  level=e.level)
        elif k == "inferno_dragon":
            if getattr(e, "keep_t", 0) > 0:
                e.keep_t -= dt
                if e.target is not None and e.target.alive and \
                        _d(e, e.target) <= e.range + e.target.radius:
                    e.keep_t = max(e.keep_t, 0.01)
        elif k == "elite_barbarians":
            _rage_spear(e, dt, match)
        elif k in ("royal_ghost", "souldier"):
            cloaked = e.invis_timer > 0
            if k == "royal_ghost" and getattr(e, "was_cloaked", False) and not cloaked \
                    and e.target is not None:
                _souldiers(e, match)
            e.was_cloaked = cloaked
        elif k == "goblin_cage":
            _cage(e, dt, match)
        elif k == "electro_giant":
            e.pulse_t = getattr(e, "pulse_t", 2.5) - dt
            if e.pulse_t <= 0:
                e.pulse_t = 6.0
                _drain_pulse(e, match)
    if k == "snowman":
        # freezes everything nearby while it stands; a Crown Tower or building
        # only for its first 2 seconds (a 2-elixir ability isn't a Freeze)
        e.age_t = getattr(e, "age_t", 0.0) + dt
        for o in _enemies(match, e, 2.5 + 1.0):
            if _d(e, o) - (o.radius if o.is_tower else 0.0) > 2.5:
                continue
            if (o.is_tower or o.is_building) and e.age_t > 2.0:
                continue
            o.freeze_timer = max(o.freeze_timer, 0.25)
    if e.hero:
        _hero_tick(e, dt, match)


def _wind(e, dt, match, x, y):
    """Evolved Baby Dragon tailwind: an 8x9 tile box around it."""
    e._aura_t = getattr(e, "_aura_t", 0.0) - dt
    if e._aura_t > 0:
        return
    e._aura_t = 0.25
    for o in match.entities:
        if not o.alive or o.is_tower or o.is_building:
            continue
        if abs(o.x - x) > 4.0 or abs(o.y - y) > 4.5:
            continue
        if o.team != e.team:
            if o.slow_factor >= 0.7 or o.slow_timer <= 0:
                o.slow_factor = 0.7
            o.slow_timer = max(o.slow_timer, 0.4)
        elif o is not e:
            o.haste_mult = max(getattr(o, "haste_mult", 1.15), 1.3)
            o.haste_timer = max(o.haste_timer, 0.4)


def wind_effect(fx, dt, match):
    """The tailwind lingering after an Evolved Baby Dragon dies."""
    _wind(fx, dt, match, fx.x, fx.y)


def _snipe(e, match):
    """Evolved Musketeer: 3 shots at the nearest enemy 6-30 tiles ahead."""
    from engine import Projectile
    if e.deploy_timer > 0 or e.attack_cd > 0 or e.stun_timer > 0 or e.freeze_timer > 0:
        return
    t = e.target
    if t is not None and t.alive and _d(e, t) <= e.range + t.radius:
        return                                       # busy with a normal shot
    f = _fwd(e.team)
    best, bd = None, 30.0
    for o in match.entities:
        if not e.can_attack(o) or o.is_tower:      # snipes never hit Crown Towers
            continue
        ahead = (o.y - e.y) * f
        d = _d(e, o)
        if ahead <= 0 or d < 6.0 or d > bd:
            continue
        best, bd = o, d
    if best is None:
        return
    e.snipes -= 1
    e.attack_cd = e.effective_hitspeed()
    e.atk_t = match.elapsed
    e.atk_dir = ((best.x - e.x) / bd, (best.y - e.y) / bd)
    pj = Projectile(e.team, e.x, e.y, best, e.dmg * 1.8, 0, e.attacks, 0.0, None,
                    style="musketeer", owner=e)
    pj.speed = 26.0
    match.projectiles.append(pj)
    match.emit("attack", "musketeer", e.x, e.y, e.team)


def _rage_spear(e, dt, match):
    from engine import Effect
    e.spear_cd = getattr(e, "spear_cd", 0.0) - dt
    if e.spear_cd > 0 or e.deploy_timer > 0:
        return
    # ground troops first, else a building or Crown Tower 3.5-5 tiles away
    # (5s cooldown, so they keep throwing). 60% of a swing: kills a Goblin,
    # not a Firecracker.
    cands = [o for o in _enemies(match, e, 5.0 + 1.5, ground_only=True, targetable=True)
             if 3.5 <= _d(e, o) - (o.radius if (o.is_tower or o.is_building) else 0.0) <= 5.0]
    if not cands:
        return
    o = min(cands, key=lambda o: (o.is_tower or o.is_building, _d(e, o)))
    e.spear_cd = 5.0
    _hit(match, e, o, e.dmg * 0.72)          # kills Goblins, not a Firecracker
    for i in range(1, 4):                            # trail of Rage behind the spear
        t = i / 4.0
        match.effects.append(Effect("rage", e.team, e.x + (o.x - e.x) * t,
                                    e.y + (o.y - e.y) * t, 1.2, 3.0, card_key="rage"))
    match.effects.append(Effect("chain", e.team, e.x, e.y, 0, 0.3, card_key="rune_giant",
                                points=[(e.x, e.y), (o.x, o.y)]))
    match.emit("attack", "spear_goblin", e.x, e.y, e.team)


def _souldiers(e, match):
    """Evolved Royal Ghost: 2 Souldiers rise as he appears."""
    _blast(match, e, e.x, e.y, 1.5, 81 * DMG * e.power[1], air=False,
           key="royal_ghost")
    for s in (-1, 1):
        x, y = _clamp(e.x + s * 0.9, e.y)
        match.spawn_units(e.team, "souldier", 1, x, y, deploy=0.2, power=e.power,
                          level=e.level)
    match.emit("portal", "souldier", e.x, e.y, e.team)


def _cage(e, dt, match):
    """Evolved Goblin Cage: drag a ground troop in and pummel it."""
    pr = getattr(e, "prisoner", None)
    if pr is not None and pr.alive:
        pr.x, pr.y = e.x, e.y
        pr.root_timer = max(pr.root_timer, 0.2)
        e.cage_cd = getattr(e, "cage_cd", 1.0) - dt
        if e.cage_cd <= 0:
            e.cage_cd = 1.0
            _hit(match, e, pr, 337 * DMG * e.power[1])
            _fx(match, "aoe", e.team, e.x, e.y, 0.8, 0.25, "goblin_brawler")
            match.emit("attack", "goblin_brawler", e.x, e.y, e.team)
        return
    e.prisoner = None
    if e.deploy_timer > 0:
        return
    o = _nearest(match, e, 3.0, ground_only=True, troops_only=True)
    if o is not None and not o.card.no_knockback:
        e.prisoner = o
        e.cage_cd = 1.0
        o.start_dash(None, kind="point", point=(e.x, e.y), speed=9.0, quiet=True)
        match.effects.append(_chain(e, o, "fisherman"))


def _chain(a, b, key):
    from engine import Effect
    return Effect("chain", a.team, a.x, a.y, 0, 0.35, card_key=key,
                  points=[(a.x, a.y), (b.x, b.y)])


def _drain_pulse(e, match):
    """Evolved Electro Giant: every enemy within 6 tiles loses a level."""
    _fx(match, "blast", e.team, e.x, e.y, 6.0, 0.5, "zap")
    match.emit("ability", e.key, e.x, e.y, e.team)
    for o in _enemies(match, e, 6.0):
        if o.is_tower or o.immortal:
            continue
        m = 1.0 / cards.level_mult(cards.LEVEL_BASE + 1)
        o.max_hp = max(1, int(o.max_hp * m))
        o.hp = min(o.max_hp, o.hp * m)
        o.dmg *= m
        o.power = (o.power[0] * m, o.power[1] * m)
        if o.level is not None:
            o.level -= 1


# =================================================================== heroes
def _snowman(match, e, t):
    """Hero Ice Wizard: a Snowman pops up behind the slowed target."""
    e.frosty = False
    d = _d(e, t) or 1.0
    if t.is_tower or t.is_building:
        # can't stand inside a tower: it pops up at the tower's foot, facing him
        off = -(t.radius + 0.7)
    else:
        off = 1.0                                 # behind the target
    x, y = _clamp(t.x + (t.x - e.x) / d * off, t.y + (t.y - e.y) / d * off)
    _blast(match, e, x, y, 1.0, 89 * DMG * e.power[1], air=False, key="freeze")
    sm = match.spawn_units(e.team, "snowman", 1, x, y, deploy=0.0, power=e.power,
                           level=e.level)[0]
    sm.fx_tick = True
    match.emit("portal", "snowman", x, y, e.team)


def _hero_tick(h, dt, match):
    k = h.key
    p0, p1 = h.power
    if k == "mini_pekka":
        h.pancakes = min(3.0, getattr(h, "pancakes", 0.0) + dt / 22.0)
    if getattr(h, "guard_t", 0) > 0:                 # Hero Knight's shield
        h.guard_t -= dt
        if h.guard_t <= 0:
            h.shield = min(h.shield, int(h.card.shield_hp * p0))
    if getattr(h, "spin_t", 0) > 0:                  # Hero Valkyrie
        h.spin_t -= dt
        h._spin_hit = getattr(h, "_spin_hit", 0.0) - dt
        if h._spin_hit <= 0:
            h._spin_hit = 0.25
            _fx(match, "aoe", h.team, h.x, h.y, 2.5, 0.2, "valkyrie")
            for o in _enemies(match, h, 2.5, ground_only=True):
                _hit(match, h, o, 97 * DMG * p1, tower_mult=0.5)
            h.atk_t = match.elapsed
    if getattr(h, "flight_t", 0) > 0:                # Hero Wizard
        h.flight_t -= dt
        if h.flight_t <= 0:
            h.flying = False
            h.haste_mult, h.haste_timer = 1.15, 0.0
    if getattr(h, "berserk_t", 0) > 0:               # Hero Berserker
        h.berserk_t -= dt
    if getattr(h, "surge_t", 0) > 0:                 # Hero Electro Wizard
        h.surge_t -= dt
        h._surge_cd = getattr(h, "_surge_cd", 0.0) - dt
        if h._surge_cd <= 0:
            h._surge_cd = 0.5
            h._surge_n = getattr(h, "_surge_n", 0) + 1
            dmg = (138 if h._surge_n == 1 else 153) * DMG * p1
            foes = sorted(_enemies(match, h, 5.0, targetable=True),
                          key=lambda o: _d(o, h))
            foes = [o for o in foes if not (o.is_king and not o.active)][:2]
            for o in foes:
                _hit(match, h, o, dmg, tower_mult=0.5)
                o.stun_timer = max(o.stun_timer, 0.5)
                match.effects.append(_chain(h, o, "electro_wizard"))
            if foes:
                match.emit("attack", "electro_wizard", h.x, h.y, h.team)
    if getattr(h, "warp_t", 0) > 0:                  # Hero Mega Minion
        h.warp_t -= dt
        t = getattr(h, "warp_target", None)
        if h.warp_t <= 0 or t is None or not t.alive:
            h.warp_t = 0.0
            hx, hy = h.warp_home
            h.start_dash(None, kind="point", point=(hx, hy), speed=14.0, quiet=True)
            h.target = None
    if getattr(h, "barrage_t", 0) > 0:               # Hero Bowler
        h.barrage_t -= dt
        h.channel_t = max(h.channel_t, 0.1)
        h._bar_cd = getattr(h, "_bar_cd", 2.5) - dt
        if h._bar_cd <= 0:
            h._bar_cd = 1.9
            _boulder(h, match)
        if h.barrage_t <= 0:
            h.channel_t = 0.0


def _boulder(h, match):
    from engine import Projectile
    best, bd = None, 11.5
    for o in match.entities:
        if not h.can_attack(o) or (o.is_king and not o.active):
            continue
        d = _d(h, o)
        if d <= bd:
            best, bd = o, d
    if best is None:
        return
    pj = Projectile(h.team, h.x, h.y, best, 0, 0, "ground", 0.0, None,
                    style="bowler_barrage", owner=h)
    pj.speed = 8.0
    match.projectiles.append(pj)
    h.atk_t = match.elapsed
    match.emit("attack", "bowler", h.x, h.y, h.team)


def hero_ready(h, match):
    """Can the hero's ability be used right now?"""
    if h is None or not h.alive or h.ability_uses <= 0 or h.is_dashing():
        return False
    k = h.key
    if h.deploy_timer > 0 and k != "goblin_banner":
        return False
    if k == "giant":
        return any(not o.is_tower and not o.is_building
                   for o in _enemies(match, h, 2.5, targetable=True))
    if k == "balloon":
        return _nearest(match, h, 6.0, ground_only=True, troops_only=True) is not None
    if k == "mega_minion":
        return any(_enemies(match, h, 99.0, targetable=True))
    if k in ("goblin", "goblins"):
        return False                                  # the banner holds it
    return True


def do_hero_ability(h, match):
    k = h.key
    p0, p1 = h.power
    f = _fwd(h.team)
    match.emit("ability", k, h.x, h.y, h.team)
    if k == "knight":
        h.shield = int(512 * HP * p0)
        h.guard_t = 5.0
        for o in _enemies(match, h, 7.5):
            if o.can_attack(h) and not o.is_tower:
                o.target = h
                o._taunt = 5.0
        _fx(match, "aoe", h.team, h.x, h.y, 7.5, 0.6, "knight")
    elif k == "giant":
        tg = [o for o in _enemies(match, h, 2.5, targetable=True)
              if not o.is_tower and not o.is_building]
        if tg:
            o = max(tg, key=lambda q: q.hp)
            nx = cfg.GRID_COLS - o.x                      # over to the other lane
            if abs(nx - o.x) < 3.0:
                nx = o.x + (9.0 if o.x < cfg.GRID_COLS / 2 else -9.0)
            nx, ny = _clamp(nx, o.y)
            o.start_dash(None, kind="point", point=(nx, ny), speed=11.0, quiet=True)
            o.stun_timer = max(o.stun_timer, 2.0)
            o.target = None
            if not o.flying:
                match.later_add(abs(nx - o.x) / 11.0, "blast", team=h.team, x=nx, y=ny,
                                radius=0.6, dmg=135 * DMG * p1, key="giant", air=False)
            _fx(match, "aoe", h.team, o.x, o.y, 1.2, 0.45, "giant")
    elif k == "mini_pekka":
        meters = int(getattr(h, "pancakes", 0.0))
        n = min(5, 1 + meters + (1 if meters >= 3 else 0))
        _level_up(h, n)
        h.hp = min(h.max_hp, h.hp + h.max_hp * 0.3)
        h.pancakes = 0.0
        _fx(match, "aoe", h.team, h.x, h.y, 1.2, 0.5, "heal_spirit")
    elif k == "musketeer":
        x, y = _clamp(h.x, h.y + f * 3.0)
        match.spawn_units(h.team, "hero_turret", 1, x, y, deploy=0.0, power=h.power,
                          level=h.level)
    elif k == "ice_golem":
        for i in range(3):
            match.later_add(0.05 + i * 0.9, "blast", team=h.team, x=h.x, y=h.y,
                            radius=4.0, dmg=69 * DMG * p1, key="freeze", air=True,
                            slow=(0.7, 2.0))
    elif k == "goblin_banner":
        gob = cards.CARDS["goblin_gang"]
        gp = getattr(h, "hero_goblin_pow", h.power)
        x, y = _clamp(h.x, h.y - f * 0.8)
        match.spawn_units(h.team, "goblin", 2, x, y, deploy=0.3, power=gp,
                          level=h.level)
        h.alive = False
    elif k == "valkyrie":
        h.spin_t = 3.5
        h._spin_hit = 0.0
        o = _nearest(match, h, 5.5, ground_only=True)
        if o is not None:
            d = _d(h, o) or 1.0
            stop = min(d, 5.5)
            h.start_dash(None, kind="point", speed=7.0, quiet=True,
                         point=_clamp(h.x + (o.x - h.x) / d * stop,
                                      h.y + (o.y - h.y) / d * stop))
    elif k == "wizard":
        h.flight_t = 5.0
        h.flying = True
        h.haste_mult, h.haste_timer = 1.5, 5.0
    elif k == "mega_minion":
        foes = [o for o in _enemies(match, h, 99.0, targetable=True)
                if not (o.is_king and not o.active)]
        if foes:
            o = min(foes, key=lambda q: q.hp)
            h.warp_home = (h.x, h.y)
            _fx(match, "aoe", h.team, h.x, h.y, 1.0, 0.4, "tornado")
            h.x, h.y = _clamp(o.x, o.y + f * 0.9)
            _hit(match, h, o, 399 * DMG * p1, tower_mult=0.25)
            _fx(match, "blast", h.team, o.x, o.y, 1.2, 0.4, "mega_minion")
            h.warp_t = 3.5
            h.warp_target = o
            h.target = o
    elif k == "barbarian":                            # Hero Barbarian Barrel
        from engine import Effect
        log = Effect("log", h.team, h.x, h.y + f * 0.5, 1.3, 0.5, direction=f,
                     speed=6.0, damage=116 * DMG * p1, knockback=1.0,
                     card_key="barbarian_barrel")
        log.tower_damage = log.damage * 0.4
        match.effects.append(log)
        h.hp = min(h.max_hp, h.hp + h.max_hp * 0.5)
        h.start_dash(None, kind="point", point=_clamp(h.x, h.y + f * 3.0), speed=6.0,
                     quiet=True)
    elif k == "magic_archer":
        x, y = _clamp(h.x, h.y - f * 3.5)
        d = match.spawn_units(h.team, "ma_decoy", 1, h.x, h.y, deploy=0.0,
                              power=h.power, level=h.level)[0]
        d.ghostly = True
        _fx(match, "aoe", h.team, h.x, h.y, 1.0, 0.4, "magic_archer")
        h.x, h.y = x, y
        h.target = None
        h.ma_triple = True
    elif k == "balloon":
        o = _nearest(match, h, 6.0, ground_only=True, troops_only=True)
        if o is not None:
            match.later_add(0.8, "trooper", team=h.team, x=o.x, y=o.y,
                            dmg=263 * DMG * p1, tower_dmg=27 * DMG * p1,
                            power=h.power, level=h.level)
    elif k == "bowler":
        h.barrage_t = 2.5 + 7.3
        h._bar_cd = 2.5
    elif k == "dark_prince":
        _blast(match, h, h.x, h.y, 1.5, 307 * DMG * p1, air=False, key="dark_prince")
        r = match.spawn_units(h.team, "rhino", 1, h.x + 0.6, h.y, deploy=0.0,
                              power=h.power, level=h.level)[0]
        r.charged = True
        h.charge_enabled = False
        h.charged = False
        h.start_dash(None, kind="point", point=_clamp(h.x - 1.0, h.y - f * 0.6),
                     speed=6.0, quiet=True)
        match.emit("land", "dark_prince", h.x, h.y, h.team, slam=True)
    elif k == "tombstone":
        match.spawn_units(h.team, "tomb_queen", 1, h.x, h.y, deploy=0.5,
                          power=h.power, level=h.level)
        h.sacrificed = True
        h.alive = False
        match.emit("portal", "tomb_queen", h.x, h.y, h.team)
    elif k == "berserker":
        h.berserk_t = 4.0
        h.atk_buff, h.atk_buff_timer = 3.0, 4.0
        h.haste_mult, h.haste_timer = 3.3 / 2.3, 4.0
        h.undying_t = 4.0
    elif k == "ice_wizard":
        h.frosty = True
    elif k == "electro_wizard":
        h.surge_t = 3.0
        h._surge_cd = 0.0
        h._surge_n = 0


# ==================================================================== spells
def on_spell(match, team, card, x, y, evo, power):
    if not evo:
        return
    k = card.key
    if k == "zap":
        match.later_add(0.5, "blast", team=team, x=x, y=y,
                        radius=card.spell_radius + 0.5,
                        dmg=card.spell_damage * power[1], key="zap", air=True,
                        stun=card.stun, tower_dmg=card.tower_dmg() * power[1])
    elif k == "goblin_barrel":
        # a twin barrel lands on the mirrored tile in the other lane
        mx = cfg.GRID_COLS - x
        match.later_add(0.4, "spawn", team=team, x=mx, y=y, key="decoy_goblin",
                        count=3, power=power)
    elif k == "snowball":
        from engine import Effect
        caught = tuple(o for o in match.entities
                       if (o.alive and o.team != team and not o.is_tower
                           and not o.is_building and not o.card.no_knockback
                           and math.hypot(o.x - x, o.y - y) <= card.spell_radius + 0.3))
        fx = Effect("snowroll", team, x, y, 1.6, 4.5 / 4.0, direction=_fwd(team),
                    speed=4.0, card_key="snowball", ends=caught)
        match.effects.append(fx)
        for o in caught:
            if o.slow_timer > 0:
                o.slow_timer += 1.0                      # slows 1s longer


def snowroll_effect(fx, dt, match):
    """Evolved Giant Snowball: the snowball rolls on, carrying its victims."""
    fx.y += fx.direction * fx.speed * dt
    fx.y = min(max(fx.y, 0.5), cfg.GRID_ROWS - 0.5)
    for o in fx.ends:
        if o.alive:
            o.x = min(max(o.x + (fx.x - o.x) * min(1.0, dt * 6), 0.4), cfg.GRID_COLS - 0.4)
            o.y = fx.y
            o.root_timer = max(o.root_timer, 0.05)
