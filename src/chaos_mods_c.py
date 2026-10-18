"""
============================================================================
  CHAOS_MODS_C.PY  --  unique card modifiers, part C
============================================================================

Barbarian Barrel ... Spirit Empress (see chaos_mods.py for how modifiers
work). Every hook here is prefixed c_<card>_ so names never clash.
============================================================================
"""

import math
import random

import cards
import config as cfg
from chaos_hooks import hook
from chaos_mods import U, M, spawn, fwd, _L, _E, _R


# ---------------------------------------------------------------- helpers
def _foes(match, team, x, y, r, ground=False, troops=True):
    out = []
    for o in match.entities:
        if not o.alive or o.team == team or o.untargetable:
            continue
        if troops and (o.is_tower or o.is_building):
            continue
        if ground and o.flying:
            continue
        if math.hypot(o.x - x, o.y - y) <= r + o.radius * 0.5:
            out.append(o)
    return out


def _nearest(match, e, r, ground=False):
    best, bd = None, r
    for o in _foes(match, e.team, e.x, e.y, r, ground):
        d = math.hypot(o.x - e.x, o.y - e.y)
        if d <= bd:
            best, bd = o, d
    return best


def _allies(match, team, x, y, r):
    return [o for o in match.entities
            if o.alive and o.team == team and not o.is_tower and not o.is_building
            and math.hypot(o.x - x, o.y - y) <= r]


def _clamp(x, y):
    return (min(max(x, 0.6), cfg.GRID_COLS - 0.6), min(max(y, 0.6), cfg.GRID_ROWS - 0.6))


def _spell_power(match, team, key):
    return match.level_power(team, key), match.card_level(team, key)


def _owned(match, team, key, cap):
    return sum(1 for o in match.entities if o.alive and o.team == team and o.key == key) >= cap


# ---------------------------------------------------------------- spells
@hook("spell_after")
def c_barbarian_barrel_convoy(match, team, card, x, y, new):
    for fx in new:
        if fx.kind == "log":
            fx.fx_tick_hook = "c_barbarian_barrel_drop"
            fx._drop_y = fx.y
            fx._drops = 0


@hook("fx_tick")
def c_barbarian_barrel_drop(fx, dt, match):
    """Barbarian Barrel: drops a Barbarian every 1.5 tiles it rolls (max 3)."""
    if fx._drops < 3 and abs(fx.y - fx._drop_y) >= 1.5:
        fx._drop_y = fx.y
        fx._drops += 1
        lp, lv = _spell_power(match, fx.team, "barbarian_barrel")
        x, y = _clamp(fx.x, fx.y)
        spawn(match, fx.team, "barbarian", 1, x, y, power=lp, level=lv)


@hook("spell_after")
def c_snowball_roll(match, team, card, x, y, new):
    """Snowball: keeps rolling - 3 more hits, 2 tiles apart, each slowing."""
    lp, _ = _spell_power(match, team, "snowball")
    for i in range(1, 4):
        nx, ny = _clamp(x, y + fwd(team) * 2.0 * i)
        match.later_add(0.25 * i, "blast", team=team, x=nx, y=ny, radius=card.spell_radius,
                        dmg=card.spell_damage * lp[1] * 0.5, slow=(0.65, 2.5),
                        key="snowball", tower_dmg=card.tower_dmg() * lp[1] * 0.5)


@hook("spell_after")
def c_earthquake_after(match, team, card, x, y, new):
    for fx in new:
        if fx.kind == "poison":
            fx.fx_tick_hook = "c_earthquake_shock"


@hook("fx_tick")
def c_earthquake_shock(fx, dt, match):
    """Earthquake: ends with an aftershock that hurls troops out of it."""
    if not getattr(fx, "_shocked", False) and fx.elapsed >= fx.duration - dt * 1.5:
        fx._shocked = True
        lp = match.level_power(fx.team, "earthquake")
        match.area_damage(fx.team, fx.x, fx.y, fx.radius, 120 * lp[1], hit_air=False,
                          stun=0.5, knockback=2.5, tower_damage=40 * lp[1])
        match.emit("impact", "earthquake", fx.x, fx.y, fx.team, radius=fx.radius)


@hook("spell_after")
def c_tornado_wander(match, team, card, x, y, new):
    for fx in new:
        if fx.kind == "tornado":
            fx.duration *= 4
            fx.fx_tick_hook = "c_tornado_drift"


@hook("fx_tick")
def c_tornado_drift(fx, dt, match):
    """Tornado: lasts 4x as long and wanders forward down the lane."""
    from engine import PLAYER
    fx.y += (-1.0 if fx.team == PLAYER else 1.0) * 1.2 * dt
    fx.x, fx.y = _clamp(fx.x, fx.y)


@hook("spell_after")
def c_graveyard_after(match, team, card, x, y, new):
    for fx in new:
        if fx.kind == "graveyard":
            fx.fx_tick_hook = "c_graveyard_king"


@hook("fx_tick")
def c_graveyard_king(fx, dt, match):
    """Graveyard: when it closes, a Giant Skeleton climbs out of it."""
    if not getattr(fx, "_risen", False) and fx.elapsed >= fx.duration - dt * 1.5:
        fx._risen = True
        lp, lv = _spell_power(match, fx.team, "graveyard")
        spawn(match, fx.team, "giant_skeleton", 1, fx.x, fx.y, power=lp, level=lv)


@hook("spell_after")
def c_goblin_curse_after(match, team, card, x, y, new):
    for fx in new:
        if fx.kind == "poison":
            fx.fx_tick_hook = "c_goblin_curse_spawn"
            fx._gob_t, fx._gobs = 0.0, 0


@hook("fx_tick")
def c_goblin_curse_spawn(fx, dt, match):
    """Goblin Curse: a Goblin pops out of the cursed ground every second (max 5)."""
    fx._gob_t -= dt
    if fx._gob_t <= 0 and fx._gobs < 5:
        fx._gob_t = 1.0
        fx._gobs += 1
        lp, lv = _spell_power(match, fx.team, "goblin_curse")
        a = random.uniform(0, math.tau)
        x, y = _clamp(fx.x + math.cos(a) * fx.radius * 0.5, fx.y + math.sin(a) * fx.radius * 0.5)
        spawn(match, fx.team, "goblin", 1, x, y, power=lp, level=lv)


@hook("spell_after")
def c_clone_twins(match, team, card, x, y, new):
    """Clone: also makes 1-hp copies of the ENEMY troops in the area - on your
    side (up to 6)."""
    made = 0
    for o in list(_foes(match, team, x, y, card.spell_radius)):
        if made >= 6 or o.card.is_champion or o.hero or o.clone:
            continue
        nx, ny = _clamp(o.x + 0.4, o.y - fwd(team) * 0.6)
        c = spawn(match, team, o.key, 1, nx, ny, power=o.power, level=o.level)
        if c:
            c[0].max_hp = c[0].hp = 1
            c[0].clone = True
            made += 1


@hook("spell_after")
def c_vines_after(match, team, card, x, y, new):
    for fx in new:
        if fx.kind == "vines":
            fx.fx_tick_hook = "c_vines_field"


@hook("fx_tick")
def c_vines_field(fx, dt, match):
    """Vines: every ground troop that walks into the patch is rooted too."""
    for o in _foes(match, fx.team, fx.x, fx.y, fx.radius, ground=True):
        o.root_timer = max(o.root_timer, 0.4)


@hook("spell_after")
def c_void_after(match, team, card, x, y, new):
    for fx in new:
        if fx.kind == "void":
            fx.fx_tick_hook = "c_void_pull"


@hook("fx_tick")
def c_void_pull(fx, dt, match):
    """Void: an event horizon - drags enemy troops toward its centre."""
    for o in _foes(match, fx.team, fx.x, fx.y, fx.radius + 2.0):
        if o.card.no_knockback:
            continue
        d = math.hypot(fx.x - o.x, fx.y - o.y)
        if d > 0.3:
            o.x += (fx.x - o.x) / d * 2.5 * dt
            o.y += (fx.y - o.y) / d * 2.5 * dt


@hook("spell_after")
def c_royal_delivery_random(match, team, card, x, y, new):
    """Royal Delivery: a random royal comes in the crate too."""
    key = random.choice(["prince", "dark_prince", "royal_giant", "royal_hogs",
                         "princess", "royal_ghost", "little_prince"
                         if not any(o.card.is_champion and o.team == team
                                    for o in match.entities if o.alive) else "prince"])
    lp, lv = _spell_power(match, team, "royal_delivery")
    spawn(match, team, key, cards.CARDS[key].count, x, y, power=lp, level=lv, deploy=0.5)


# ---------------------------------------------------------------- troops
@hook("tick")
def c_mighty_miner_bombs(e, dt, match):
    """Mighty Miner: drops a lit bomb behind him every 3 s."""
    e._bomb_t = getattr(e, "_bomb_t", 3.0) - dt
    if e._bomb_t <= 0 and e.deploy_timer <= 0:
        e._bomb_t = 3.0
        from engine import Effect
        match.effects.append(Effect("timed_bomb", e.team, e.x, e.y, 2.0, 1.5,
                                    damage=180 * e.power[1], card_key="mighty_miner"))


@hook("deploy")
def c_little_prince_knight(match, team, units, x, y):
    """Little Prince: knighted - a Knight and a Princess march with him."""
    if units:
        u = units[0]
        spawn(match, team, "knight", 1, x - 1.2, y + fwd(team) * 0.6, power=u.power,
              level=u.level, deploy=None)
        spawn(match, team, "princess", 1, x + 1.2, y - fwd(team) * 0.6, power=u.power,
              level=u.level, deploy=None)


@hook("hit")
def c_golden_knight_midas(src, target, dmg, x, y, match):
    """Golden Knight: every troop he finishes off pays 1 elixir."""
    if target is not None and not target.alive and not target.is_tower \
            and not getattr(target, "_midas", False):
        target._midas = True
        match.add_elixir(src.seat if src.seat < len(match.elixir) else src.team, 1.0)
        match.emit("elixir_made", "golden_knight", src.x, src.y, src.team, amount=1)


@hook("tick")
def c_skeleton_king_raise(e, dt, match):
    """Skeleton King: raises 2 Skeletons beside him every 3 s (10 at most)."""
    e._raise_t = getattr(e, "_raise_t", 3.0) - dt
    if e._raise_t <= 0 and e.deploy_timer <= 0:
        e._raise_t = 3.0
        if sum(1 for o in match.entities if o.alive and o.team == e.team
               and getattr(o, "_sk_raised", False)) >= 10:
            return
        for s in (-1, 1):
            x, y = _clamp(e.x + s * 0.9, e.y)
            for u in spawn(match, e.team, "skeleton", 1, x, y, power=e.child_power(),
                           level=e.level):
                u._sk_raised = True


@hook("hit")
def c_monk_palm(src, target, dmg, x, y, match):
    """Monk: every strike heals allied troops within 3 tiles for its damage."""
    for o in _allies(match, src.team, src.x, src.y, 3.0):
        o.hp = min(o.max_hp, o.hp + dmg)


@hook("tick")
def c_goblinstein_rod(e, dt, match):
    """Goblinstein: a lightning rod - every 2 s a bolt arcs through 3 enemies
    within 5 tiles."""
    e._rod_t = getattr(e, "_rod_t", 2.0) - dt
    if e._rod_t > 0 or e.deploy_timer > 0:
        return
    t = _nearest(match, e, 5.0)
    if t is None:
        return
    e._rod_t = 2.0
    match.chain_damage(e.team, e.x, e.y, t, 90 * e.power[1], 0.3, 3, 3.0,
                       "electro_dragon", src=e)


@hook("deploy")
def c_boss_bandit_gang(match, team, units, x, y):
    """Boss Bandit: brings her gang - 2 Bandits."""
    if units:
        u = units[0]
        for s in (-1, 1):
            spawn(match, team, "bandit", 1, x + s * 1.3, y - fwd(team) * 0.8,
                  power=u.power, level=u.level, deploy=None)


@hook("hit")
def c_berserker_feast(src, target, dmg, x, y, match):
    """Berserker: every kill heals her fully and makes her swing 15% faster
    (up to 3 times)."""
    if target is not None and not target.alive and not target.is_tower:
        src.hp = src.max_hp
        n = getattr(src, "_feast", 0)
        if n < 3:
            src._feast = n + 1
            src.hit_speed /= 1.15


@hook("death")
def c_firecracker_finale(e, match):
    """Firecracker: goes out with a bang - a Fireball-sized blast where she falls."""
    match.area_damage(e.team, e.x, e.y, 2.5, 260 * e.power[1], hit_air=True,
                      knockback=1.0, tower_damage=80 * e.power[1])
    match.emit("impact", "fireball", e.x, e.y, e.team, radius=2.5)


@hook("hit")
def c_skeleton_dragons_rain(src, target, dmg, x, y, match):
    """Skeleton Dragons: every other fireball drops a Skeleton where it lands."""
    src._rain = getattr(src, "_rain", 0) + 1
    if src._rain % 2 == 0:
        px, py = _clamp(x, y)
        spawn(match, src.team, "skeleton", 1, px, py, power=src.child_power(), level=src.level)


@hook("death")
def c_rascals_avenge(e, match):
    """Rascals: when the Rascal Boy falls, his sisters are enraged for good."""
    for o in match.entities:
        if o.alive and o.team == e.team and o.key == "rascal_girl":
            o.rage_timer = 1e9


@hook("death")
def c_heal_spirit_ward(e, match):
    """Heal Spirit: its burst also wraps allied troops nearby in a 150 hp shield."""
    for o in _allies(match, e.team, e.x, e.y, 3.0):
        if o is not e:
            o.shield = max(o.shield, int(150 * e.power[0]))


@hook("tick")
def c_goblin_cage_trap(e, dt, match):
    """Goblin Cage: snaps shut on the nearest enemy troop within 2.5 tiles,
    rooting it for 3 s (every 6 s)."""
    e._trap_t = getattr(e, "_trap_t", 0.0) - dt
    if e._trap_t > 0 or e.deploy_timer > 0:
        return
    t = _nearest(match, e, 2.5, ground=True)
    if t is not None:
        e._trap_t = 6.0
        t.root_timer = max(t.root_timer, 3.0)
        match.emit("attack", "goblin_cage", e.x, e.y, e.team)


@hook("death")
def c_goblin_demolisher_boom(e, match):
    """Goblin Demolisher: blows up when destroyed and 3 Goblins scramble out."""
    match.area_damage(e.team, e.x, e.y, 2.5, 220 * e.power[1], hit_air=False,
                      knockback=1.2, tower_damage=90 * e.power[1])
    match.emit("impact", "fireball", e.x, e.y, e.team, radius=2.5)
    spawn(match, e.team, "goblin", 3, e.x, e.y, power=e.child_power(), level=e.level)


@hook("tick")
def c_minion_giant_hive(e, dt, match):
    """Minion Giant: a flying hive - 2 Minions buzz out every 3 s (8 at most)."""
    e._hive_t = getattr(e, "_hive_t", 3.0) - dt
    if e._hive_t <= 0 and e.deploy_timer <= 0:
        e._hive_t = 3.0
        if sum(1 for o in match.entities if o.alive and getattr(o, "_hive_of", None) is e) >= 8:
            return
        for u in spawn(match, e.team, "minions", 2, e.x, e.y, power=e.child_power(),
                       level=e.level):
            u._hive_of = e


@hook("death")
def c_royal_hogs_truffle(e, match):
    """Royal Hogs: each hog bursts like a small bomb when it falls."""
    match.area_damage(e.team, e.x, e.y, 1.5, 110 * e.power[1], hit_air=False,
                      tower_damage=40 * e.power[1])
    match.emit("impact", "fireball", e.x, e.y, e.team, radius=1.5)


@hook("death")
def c_goblin_drill_tunnel(e, match):
    """Goblin Drill: when it caves in, it resurfaces once 4 tiles further on."""
    if getattr(e, "_tunnel", False):
        return
    x, y = _clamp(e.x, e.y + fwd(e.team) * 4.0)
    from engine import RIVER_TOP, RIVER_BOTTOM
    if RIVER_TOP - 0.5 <= y <= RIVER_BOTTOM + 0.5:
        y += fwd(e.team) * 2.5
    for u in spawn(match, e.team, "goblin_drill", 1, x, y, power=e.power, level=e.level):
        u._tunnel = True


@hook("tick")
def c_rune_giant_pillar(e, dt, match):
    """Rune Giant: every 4 s her runes flare - allies within 4 tiles raged 2 s."""
    e._rune_t = getattr(e, "_rune_t", 2.0) - dt
    if e._rune_t <= 0 and e.deploy_timer <= 0:
        e._rune_t = 4.0
        for o in _allies(match, e.team, e.x, e.y, 4.0):
            o.rage_timer = max(o.rage_timer, 2.0)
        match.effects_rage(e.team, e.x, e.y, 4.0, 0.4)


@hook("deploy")
def c_fisherman_wave(match, team, units, x, y):
    """Fisherman: lands with a tidal wave that throws enemies back and slows them."""
    if units:
        match.area_damage(team, x, y, 3.5, 60 * units[0].power[1], hit_air=False,
                          slow=(0.6, 3.0), knockback=2.0)
        match.emit("impact", "the_log", x, y, team, radius=3.5)


@hook("hit")
def c_royal_ghost_possess(src, target, dmg, x, y, match):
    """Royal Ghost: troops he finishes rise again as ghostly allies at half hp
    (3 per Ghost)."""
    if (target is None or target.alive or target.is_tower or target.is_building
            or getattr(target, "_possessed", False) or target.card.is_champion
            or getattr(src, "_possess", 0) >= 3 or target.key not in cards.CARDS):
        return
    target._possessed = True
    src._possess = getattr(src, "_possess", 0) + 1
    tx, ty = _clamp(target.x, target.y)
    for u in spawn(match, src.team, target.key, 1, tx, ty, power=target.power,
                   level=target.level):
        u.hp = u.max_hp * 0.5
        u.ghostly = True
        u._possessed = True


@hook("tick")
def c_mother_witch_piper(e, dt, match):
    """Mother Witch: every 4 s turns the weakest enemy troop within 5 tiles
    (300 hp or less) into a Hog for her side."""
    e._piper_t = getattr(e, "_piper_t", 4.0) - dt
    if e._piper_t > 0 or e.deploy_timer > 0:
        return
    weak = [o for o in _foes(match, e.team, e.x, e.y, 5.0)
            if o.hp <= 300 * e.power[1] and not o.card.is_champion and not o.immortal]
    if not weak:
        return
    e._piper_t = 4.0
    o = min(weak, key=lambda q: q.hp)
    o.sacrificed = True
    o.alive = False
    x, y = _clamp(o.x, o.y)
    spawn(match, e.team, "cursed_hog", 1, x, y, power=e.child_power(), level=e.level)


@hook("death")
def c_goblin_machine_destruct(e, match):
    """Goblin Machine: self-destructs (big blast) and its 2 Goblin pilots jump out."""
    match.area_damage(e.team, e.x, e.y, 3.0, 300 * e.power[1], hit_air=True,
                      knockback=1.5, tower_damage=100 * e.power[1])
    match.emit("impact", "rocket", e.x, e.y, e.team, radius=3.0)
    spawn(match, e.team, "goblin", 2, e.x, e.y, power=e.child_power(), level=e.level)


@hook("tick")
def c_ronin_iaido(e, dt, match):
    """Ronin: every 5 s a lightning-quick draw - he dashes through the nearest
    enemy within 5 tiles, cutting everything on the way."""
    e._iai_t = getattr(e, "_iai_t", 2.0) - dt
    if e._iai_t > 0 or e.deploy_timer > 0 or e.dash is not None:
        return
    t = _nearest(match, e, 5.0, ground=True)
    if t is None:
        return
    e._iai_t = 5.0
    d = math.hypot(t.x - e.x, t.y - e.y) or 1.0
    ux, uy = (t.x - e.x) / d, (t.y - e.y) / d
    ex, ey = _clamp(t.x + ux * 1.2, t.y + uy * 1.2)
    from engine import river_side
    if river_side(ey) != river_side(e.y):
        ex, ey = t.x, t.y
    for o in _foes(match, e.team, e.x, e.y, d + 1.5, ground=True):
        # on the line from him to just past the target
        px, py = o.x - e.x, o.y - e.y
        along = px * ux + py * uy
        if -0.3 <= along <= d + 1.2 and abs(px * uy - py * ux) <= 0.9:
            o.take_damage(e.dmg * 2.0)
    e.start_dash(None, kind="point", point=(ex, ey), speed=16.0, quiet=True)
    e.dash["keep_target"] = True
    match.emit("dash", "ronin", e.x, e.y, e.team)


@hook("deploy")
def c_spirit_empress_court(match, team, units, x, y):
    """Spirit Empress: arrives with her court - one of every spirit."""
    if units:
        u = units[0]
        for i, k in enumerate(("fire_spirit", "ice_spirit", "electro_spirit", "heal_spirit")):
            a = math.tau * i / 4
            spawn(match, team, k, 1, x + math.cos(a) * 1.3, y + math.sin(a) * 1.3,
                  power=u.child_power(), level=u.level, deploy=None)


# ---------------------------------------------------------------- the list
UNIQUE = [
    U("barbarian_barrel", "Barbarian Convoy", "The barrel drops a Barbarian every "
      "1.5 tiles it rolls (3 more).", M(spell_after="c_barbarian_barrel_convoy")),
    U("snowball", "Rolling Snowball", "Keeps rolling on: 3 more slowing hits, 2 "
      "tiles apart.", M(spell_after="c_snowball_roll"), _R),
    U("earthquake", "Aftershock", "Ends with an aftershock that stuns and hurls "
      "troops out of it.", M(spell_after="c_earthquake_after")),
    U("tornado", "Wandering Twister", "Lasts 4x as long and wanders forward down "
      "the lane, dragging everything with it.", M(spell_after="c_tornado_wander"), _L),
    U("graveyard", "Bone Lord", "When the Graveyard closes, a Giant Skeleton climbs "
      "out of it.", M(spell_after="c_graveyard_after"), _L),
    U("mighty_miner", "Dynamite Trail", "Drops a lit bomb behind him every 3 s.",
      M(tick="c_mighty_miner_bombs")),
    U("archer_queen", "Triple Draw", "Every shot is 3 arrows at 3 different targets.",
      lambda c: {"multi_target": 3}),
    U("little_prince", "Royal Retinue", "A Knight and a Princess march with him.",
      M(deploy="c_little_prince_knight")),
    U("golden_knight", "Midas Touch", "Every troop he finishes off pays you 1 elixir.",
      M(hit="c_golden_knight_midas"), _L),
    U("skeleton_king", "Lord of Bones", "Raises 2 Skeletons beside him every 3 s "
      "(10 at most).", M(tick="c_skeleton_king_raise")),
    U("monk", "Healing Palm", "Every strike heals your troops within 3 tiles for "
      "its damage.", M(hit="c_monk_palm")),
    U("goblinstein", "Lightning Rod", "Every 2 s a bolt arcs through 3 enemies "
      "near the Doctor.", M(tick="c_goblinstein_rod")),
    U("boss_bandit", "The Gang", "Two Bandits come with her.",
      M(deploy="c_boss_bandit_gang"), _L),
    U("berserker", "Feast", "Every kill heals her fully and makes her swing 15% "
      "faster (3 times).", M(hit="c_berserker_feast"), _R),
    U("firecracker", "Big Finish", "Goes out with a Fireball-sized blast.",
      M(death="c_firecracker_finale"), _R),
    U("skeleton_dragons", "Bone Rain", "Every other fireball drops a Skeleton where "
      "it lands.", M(hit="c_skeleton_dragons_rain")),
    U("rascals", "Avenge the Boy", "If the Rascal Boy falls, the Girls are enraged "
      "for good.", M(death="c_rascals_avenge"), _R, subs=("rascal_boy",)),
    U("royal_delivery", "Royal Surprise", "A random royal (Prince, Dark Prince, "
      "Royal Giant, Royal Hogs, Princess, Ghost...) comes in the crate too.",
      M(spell_after="c_royal_delivery_random"), _L),
    U("heal_spirit", "Spirit Ward", "Its burst also shields your troops nearby "
      "(150 hp).", M(death="c_heal_spirit_ward"), _R),
    U("goblin_cage", "Snap Trap", "Snaps shut on the nearest enemy troop within "
      "2.5 tiles - rooted for 3 s (every 6 s).", M(tick="c_goblin_cage_trap")),
    U("goblin_demolisher", "Last Resort", "Blows up when destroyed and 3 Goblins "
      "scramble out.", M(death="c_goblin_demolisher_boom")),
    U("minion_giant", "Flying Hive", "2 Minions buzz out of him every 3 s (8 at "
      "most).", M(tick="c_minion_giant_hive"), _L),
    U("royal_hogs", "Truffle Bombs", "Each hog bursts like a small bomb when it "
      "falls.", M(death="c_royal_hogs_truffle")),
    U("mirror", "Mirror Image", "Mirror becomes a 1-elixir Clone: copies your "
      "troops in the area.", lambda c: {"spell_kind": "clone", "spell_radius": 3.0,
                                        "elixir": 1}, _L),
    U("goblin_curse", "Goblin Plague", "A Goblin pops out of the cursed ground "
      "every second (5 in all).", M(spell_after="c_goblin_curse_after")),
    U("clone", "Evil Twins", "Also copies the ENEMY troops in the area onto your "
      "side (1 hp, up to 6).", M(spell_after="c_clone_twins"), _L),
    U("vines", "Thorn Field", "Every ground troop that walks into the patch is "
      "rooted too.", M(spell_after="c_vines_after")),
    U("goblin_drill", "Tunnel Hop", "When it caves in, it resurfaces once 4 tiles "
      "further on.", M(death="c_goblin_drill_tunnel")),
    U("rune_giant", "Rune Pillar", "Every 4 s her runes flare: your troops within 4 "
      "tiles are raged for 2 s.", M(tick="c_rune_giant_pillar")),
    U("void", "Event Horizon", "Drags enemy troops toward its centre while it "
      "strikes.", M(spell_after="c_void_after")),
    U("fisherman", "Tidal Wave", "Lands with a wave that throws enemies back and "
      "slows them.", M(deploy="c_fisherman_wave"), _R),
    U("royal_ghost", "Possession", "Troops he finishes rise again as ghostly allies "
      "at half hp (3 per Ghost).", M(hit="c_royal_ghost_possess"), _L),
    U("mother_witch", "Pied Piper", "Every 4 s turns the weakest enemy troop within "
      "5 tiles (300 hp or less) into a Hog for her side.",
      M(tick="c_mother_witch_piper"), _L),
    U("goblin_machine", "Self-Destruct", "Explodes when destroyed and its 2 Goblin "
      "pilots jump out.", M(death="c_goblin_machine_destruct")),
    U("ronin", "Iaido", "Every 5 s he dashes through the nearest enemy, cutting "
      "everything on the way for double damage.", M(tick="c_ronin_iaido")),
    U("spirit_empress", "Spirit Court", "Arrives with one of every spirit (Fire, "
      "Ice, Electro and Heal).", M(deploy="c_spirit_empress_court")),
]


from chaos_mods import _register  # noqa: E402
_register(UNIQUE)
