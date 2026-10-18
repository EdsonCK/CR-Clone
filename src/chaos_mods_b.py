"""
============================================================================
  CHAOS_MODS_B.PY  --  unique card modifiers, batch B
============================================================================

Sparky to Elixir Golem (buildings, big spells and the electric crew). Same
rules as chaos_mods.py: each entry is one-time, rarity by power, and every
mechanic is a data change on the side's card copy or a chaos_hooks hook.
============================================================================
"""

import math
import random

from chaos_hooks import hook
from chaos_mods import U, M, spawn, fwd, _L, _E, _R


def _foes(match, e_or_team, x, y, r, air=True, troops_only=False):
    team = e_or_team if isinstance(e_or_team, int) else e_or_team.team
    out = []
    for o in match.entities:
        if not o.alive or o.team == team or o.untargetable:
            continue
        if o.flying and not air:
            continue
        if troops_only and (o.is_tower or o.is_building):
            continue
        if math.hypot(o.x - x, o.y - y) <= r + o.radius * 0.5:
            out.append(o)
    return out


def _allies(match, team, x, y, r):
    return [o for o in match.entities if o.alive and o.team == team and not o.is_tower
            and not o.is_building and math.hypot(o.x - x, o.y - y) <= r]


def _blast(match, team, x, y, radius, dmg, key, delay=0.0, stun=0.0, air=True,
           tower_mult=0.35):
    match.later_add(delay, "blast", team=team, x=x, y=y, radius=radius, dmg=dmg,
                    key=key, stun=stun, air=air, tower_dmg=dmg * tower_mult)


def _lp(match, team, key):
    return match.level_power(team, key)[1]


def _every(e, attr, period, dt, first=None):
    """True once every `period` seconds (per unit)."""
    t = getattr(e, attr, period if first is None else first) - dt
    if t <= 0 and e.deploy_timer <= 0:
        setattr(e, attr, t + period)
        return True
    setattr(e, attr, t)
    return False


# ================================================================ hooks
@hook("hit")
def b_sparky_shock(src, target, dmg, x, y, match):
    """Sparky: every blast also stuns everything within 3 tiles for 1.5 s."""
    for o in _foes(match, src, x, y, 3.0):
        o.stun_timer = max(o.stun_timer, 1.5)
        o.reset_charge()


@hook("death")
def b_cannon_cart(e, match):
    """Cannon: when it expires or falls it rolls on as a Cannon Cart."""
    spawn(match, e.team, "cannon_cart", 1, e.x, e.y, power=e.power, level=e.level)


@hook("tick")
def b_tesla_storm(e, dt, match):
    """Tesla: every 2.5 s it arcs to up to 3 enemies within 6 tiles (stun)."""
    if not _every(e, "_b_storm", 2.5, dt):
        return
    foes = sorted(_foes(match, e, e.x, e.y, 6.0), key=lambda o: math.hypot(o.x - e.x, o.y - e.y))
    for o in foes[:3]:
        match.bolt(e.team, e, o, "tesla")
        o.take_damage(e.dmg * 0.8)
        o.stun_timer = max(o.stun_timer, 0.5)
        o.reset_charge()


@hook("tick")
def b_inferno_ring(e, dt, match):
    """Inferno Tower: a ring of fire burns everything within 3 tiles."""
    if not _every(e, "_b_ring", 1.0, dt):
        return
    match.area_damage(e.team, e.x, e.y, 3.0, 45 * e.power[1], hit_air=True,
                      tower_damage=10 * e.power[1])
    match.emit("impact", "fireball", e.x, e.y, e.team, radius=3.0)


@hook("death")
def b_bomb_cluster(e, match):
    """Bomb Tower: its death bomb scatters 4 more bombs around it."""
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        _blast(match, e.team, e.x + math.cos(a) * 2.2, e.y + math.sin(a) * 2.2, 1.6,
               150 * e.power[1], "bomb_tower", delay=1.2 + 0.15 * i, air=False)


@hook("death")
def b_elixir_overflow(e, match):
    """Elixir Collector: when it's destroyed or runs out it spills 3 elixir."""
    match.add_elixir(e.team, 3.0)
    match.emit("elixir_made", e.key, e.x, e.y, e.team, amount=3)


@hook("spell_after")
def b_zap_storm(match, team, card, x, y, new):
    """Zap: 4 more zaps over 4 s, each 20% wider."""
    pw = _lp(match, team, card.key)
    for i in range(1, 5):
        _blast(match, team, x, y, card.spell_radius * (1 + 0.2 * i),
               card.spell_damage * pw, "zap", delay=float(i), stun=0.5)


@hook("spell_after")
def b_log_lumberjack(match, team, card, x, y, new):
    """The Log: a Lumberjack follows it out (and drops his Rage when he falls)."""
    lp = match.level_power(team, card.key)
    spawn(match, team, "lumberjack", 1, x, y, power=lp,
          level=match.card_level(team, card.key))


@hook("spell_after")
def b_arrows_archers(match, team, card, x, y, new):
    """Arrows: two Archers parachute in where the volley lands."""
    lp = match.level_power(team, card.key)
    spawn(match, team, "archers", 2, x, y, power=lp, level=match.card_level(team, card.key))


@hook("spell_after")
def b_fireball_napalm(match, team, card, x, y, new):
    """Fireball: the ground burns - 3 more fire bursts, a second apart."""
    pw = _lp(match, team, card.key)
    for i in range(1, 4):
        _blast(match, team, x, y, card.spell_radius, card.spell_damage * 0.25 * pw,
               "fireball", delay=float(i))


@hook("spell_after")
def b_freeze_shatter(match, team, card, x, y, new):
    """Freeze: when the ice breaks, everything that was frozen shatters for
    heavy damage."""
    pw = _lp(match, team, card.key)
    _blast(match, team, x, y, card.spell_radius, 260 * pw, "freeze",
           delay=max(0.5, card.freeze))


@hook("spell_after")
def b_rocket_cluster(match, team, card, x, y, new):
    """Rocket: it splits - 4 mini rockets land around the impact."""
    pw = _lp(match, team, card.key)
    for i in range(4):
        a = i * math.pi / 2
        _blast(match, team, x + math.cos(a) * 2.5, y + math.sin(a) * 2.5, 1.6,
               card.spell_damage * 0.3 * pw, "rocket", delay=0.6 + 0.1 * i)


@hook("spell_after")
def b_lightning_storm(match, team, card, x, y, new):
    """Lightning: a storm lingers - 5 more strikes, one a second, each on a
    random enemy within 5 tiles of where it struck."""
    pw = _lp(match, team, card.key)
    foes = _foes(match, team, x, y, 5.0, troops_only=False) or []
    for i in range(1, 6):
        if foes:
            o = random.choice(foes)
            tx, ty = o.x, o.y
        else:
            tx = x + random.uniform(-3, 3)
            ty = y + random.uniform(-3, 3)
        _blast(match, team, tx, ty, 1.2, card.spell_damage * 0.4 * pw, "lightning",
               delay=float(i), stun=0.5)


@hook("death")
def b_skeleton_rise(e, match):
    """Skeleton Army: each Skeleton has a 40% chance to rise once more."""
    if getattr(e, "_b_risen", False) or e.sacrificed or e.clone:
        return
    if random.random() < 0.4:
        for u in spawn(match, e.team, e.key, 1, e.x, e.y, power=e.power, level=e.level):
            u._b_risen = True


@hook("tick")
def b_guards_regen(e, dt, match):
    """Guards: their shields grow back fully 5 s after breaking."""
    full = int(e.card.shield_hp * e.power[0])
    if e.shield > 0 or full <= 0:
        e._b_regen = 5.0
        return
    e._b_regen = getattr(e, "_b_regen", 5.0) - dt
    if e._b_regen <= 0:
        e.shield = full
        e._b_regen = 5.0


@hook("death")
def b_zappies_short(e, match):
    """Zappies: they short-circuit when they fall - stunning everything
    within 2.5 tiles for 2 s."""
    for o in _foes(match, e, e.x, e.y, 2.5):
        o.stun_timer = max(o.stun_timer, 2.0)
        o.take_damage(60 * e.power[1])
    match.emit("impact", "zap", e.x, e.y, e.team, radius=2.5)


@hook("hit")
def b_hunter_net(src, target, dmg, x, y, match):
    """Hunter: every shot nets its target - rooted for 1 s."""
    if target is not None and target.alive and not (target.is_tower or target.is_building):
        target.root_timer = max(target.root_timer, 1.0)


@hook("hit")
def b_exec_vortex(src, target, dmg, x, y, match):
    """Executioner: his axe drags enemies it passes toward its path."""
    if target is None or not target.alive or target.is_tower or target.is_building \
            or target.card.no_knockback:
        return
    d = math.hypot(src.x - target.x, src.y - target.y) or 1.0
    pull = min(1.2, max(0.0, d - 1.5))
    target.x += (src.x - target.x) / d * pull
    target.y += (src.y - target.y) / d * pull


@hook("hit")
def b_bowler_quake(src, target, dmg, x, y, match):
    """Bowler: every boulder shakes the ground - ground troops within 2 tiles
    of it are slowed by 50% for 2 s."""
    if target is None:
        return
    for o in _foes(match, src, target.x, target.y, 2.0, air=False, troops_only=True):
        o.slow_factor, o.slow_timer = 0.5, 2.0


@hook("hit")
def b_ma_ricochet(src, target, dmg, x, y, match):
    """Magic Archer: arrows ricochet to the nearest other enemy within 4
    tiles for 60% damage."""
    if target is None:
        return
    best, bd = None, 4.0
    for o in _foes(match, src, target.x, target.y, 4.0):
        if o is target:
            continue
        d = math.hypot(o.x - target.x, o.y - target.y)
        if d < bd:
            best, bd = o, d
    if best is not None:
        match.bolt(src.team, target, best, "magic_archer")
        best.take_damage(dmg * 0.6)


@hook("tick")
def b_fm_bombs(e, dt, match):
    """Flying Machine: drops a bomb on the ground below every 3 s."""
    if not _every(e, "_b_bomb", 3.0, dt, first=2.0):
        return
    if not _foes(match, e, e.x, e.y, 3.0, air=False):
        e._b_bomb = 0.5                       # nothing below: look again soon
        return
    _blast(match, e.team, e.x, e.y, 1.5, 150 * e.power[1], "bomber", delay=0.4, air=False)


@hook("tick")
def b_edragon_aura(e, dt, match):
    """Electro Dragon: a static aura zaps the nearest enemy within 3.5 tiles
    every second (stuns 0.5 s)."""
    if not _every(e, "_b_aura", 1.0, dt):
        return
    foes = _foes(match, e, e.x, e.y, 3.5)
    if foes:
        o = min(foes, key=lambda f: math.hypot(f.x - e.x, f.y - e.y))
        match.bolt(e.team, e, o, "electro_dragon")
        o.take_damage(60 * e.power[1])
        o.stun_timer = max(o.stun_timer, 0.5)
        o.reset_charge()


@hook("death")
def b_mk_last_stand(e, match):
    """Mega Knight: he slams one last time when he falls - triple damage,
    wide, knocking everything back."""
    r, d = e.card.spawn_damage or (2.5, 150)
    match.area_damage(e.team, e.x, e.y, r + 1.0, d * 3 * e.power[1], hit_air=False,
                      knockback=1.5)
    match.emit("impact", "mega_knight", e.x, e.y, e.team, radius=r + 1.0)


@hook("death")
def b_cart_fort(e, match):
    """Cannon Cart: when its cart breaks, the cannon digs in as a Cannon."""
    spawn(match, e.team, "cannon", 1, e.x, e.y, power=e.power, level=e.level)


@hook("tick")
def b_icegolem_chill(e, dt, match):
    """Ice Golem: a blizzard swirls around him - enemies within 2.5 tiles are
    slowed by 40%."""
    if not _every(e, "_b_chill", 0.25, dt):
        return
    for o in _foes(match, e, e.x, e.y, 2.5, troops_only=True):
        o.slow_factor, o.slow_timer = min(o.slow_factor, 0.6), max(o.slow_timer, 0.4)


@hook("hit")
def b_miner_gold(src, target, dmg, x, y, match):
    """Miner: every pick hit on a tower or building digs up 0.25 elixir."""
    if target is not None and (target.is_tower or target.is_building):
        match.add_elixir(src.team, 0.25)


@hook("death")
def b_wb_bomber(e, match):
    """Wall Breakers: each one leaves a Bomber behind in the rubble."""
    if e.sacrificed or e.clone:
        return
    spawn(match, e.team, "bomber", 1, e.x, e.y, power=e.power, level=e.level)


@hook("death")
def b_espirit_split(e, match):
    """Electro Spirit: it splits into 2 more spirits (once)."""
    if getattr(e, "_b_gen", 0) >= 1 or e.clone:
        return
    for u in spawn(match, e.team, "electro_spirit", 2, e.x, e.y - fwd(e.team) * 0.5,
                   power=e.power, level=e.level):
        u._b_gen = 1


@hook("tick")
def b_egiant_storm(e, dt, match):
    """Electro Giant: every 2 s lightning arcs from him to up to 3 enemies
    within 4 tiles (stun 0.5 s)."""
    if not _every(e, "_b_estorm", 2.0, dt):
        return
    foes = sorted(_foes(match, e, e.x, e.y, 4.0), key=lambda o: math.hypot(o.x - e.x, o.y - e.y))
    for o in foes[:3]:
        match.bolt(e.team, e, o, "electro_giant")
        o.take_damage(100 * e.power[1])
        o.stun_timer = max(o.stun_timer, 0.5)
        o.reset_charge()


@hook("death")
def b_healer_martyr(e, match):
    """Battle Healer: her last prayer fully heals every friendly troop within
    5 tiles."""
    for o in _allies(match, e.team, e.x, e.y, 5.0):
        o.hp = o.max_hp
    match.emit("impact", "heal_spirit", e.x, e.y, e.team, radius=5.0)


@hook("death")
def b_egolem_refund(e, match):
    """Elixir Golem: its last blobs pay YOU their elixir instead of the
    opponent."""
    if e.key == "elixir_blob" and not e.clone:
        match.add_elixir(e.team, 1.0)


# ================================================================ the list
_EG = lambda c: {"death_gives_elixir": 0.0, "mods": {"death": "b_egolem_refund"}}

UNIQUE = [
    U("sparky", "Shockwave", "Every blast also stuns everything within 3 tiles for "
      "1.5 s.", M(hit="b_sparky_shock"), _L),
    U("cannon", "Rolling Cannon", "When it expires or falls it rolls on as a Cannon "
      "Cart.", M(death="b_cannon_cart")),
    U("tesla", "Storm Coil", "Every 2.5 s it arcs to up to 3 enemies within 6 tiles, "
      "stunning them.", M(tick="b_tesla_storm")),
    U("inferno_tower", "Ring of Fire", "A ring of fire burns everything within 3 "
      "tiles every second.", M(tick="b_inferno_ring")),
    U("bomb_tower", "Cluster Bombs", "Its death bomb scatters 4 more bombs around "
      "it.", M(death="b_bomb_cluster"), _R),
    U("tombstone", "Tomb of the Giant", "Breaks open into a Giant Skeleton instead "
      "of 4 Skeletons.", lambda c: {"death_spawn": ("giant_skeleton", 1)}, _L),
    U("goblin_hut", "Dart Academy", "Trains Dart Goblins instead of Spear Goblins.",
      lambda c: {"spawner": ("dart_goblin", 1, c.spawner[2] * 1.2)}),
    U("furnace", "Dragon Forge", "Forges a Baby Dragon instead of a Fire Spirit "
      "(a bit less often).", lambda c: {"spawner": ("baby_dragon", 1, c.spawner[2] * 1.5)},
      _L),
    U("elixir_collector", "Overflow", "When it's destroyed or runs dry it spills 3 "
      "elixir.", M(death="b_elixir_overflow"), _R),
    U("zap", "Ion Storm", "Zaps 4 more times over 4 s, each 20% wider.",
      M(spell_after="b_zap_storm")),
    U("the_log", "Timber!", "A Lumberjack follows the Log out.",
      M(spell_after="b_log_lumberjack")),
    U("arrows", "Paratroopers", "Two Archers parachute in where the volley lands.",
      M(spell_after="b_arrows_archers")),
    U("fireball", "Napalm", "The ground burns: 3 more fire bursts, a second apart.",
      M(spell_after="b_fireball_napalm")),
    U("freeze", "Shatter", "When the ice breaks, everything that was frozen shatters "
      "for heavy damage.", M(spell_after="b_freeze_shatter")),
    U("rocket", "Cluster Rocket", "It splits: 4 mini rockets land around the impact.",
      M(spell_after="b_rocket_cluster"), _L),
    U("lightning", "Lingering Storm", "5 more strikes, one a second, on random "
      "enemies near where it struck.", M(spell_after="b_lightning_storm"), _L),
    U("skeleton_army", "Restless Dead", "Each Skeleton has a 40% chance to rise "
      "once more when it falls.", M(death="b_skeleton_rise")),
    U("guards", "Phalanx", "Their shields grow back fully 5 s after breaking.",
      M(tick="b_guards_regen")),
    U("zappies", "Short Circuit", "When a Zappy falls it stuns everything within "
      "2.5 tiles for 2 s.", M(death="b_zappies_short"), _R),
    U("hunter", "Net Gun", "Every shot nets its target: rooted for 1 s.",
      M(hit="b_hunter_net")),
    U("executioner", "Vortex Axe", "His axe drags the enemies it hits toward him.",
      M(hit="b_exec_vortex")),
    U("bowler", "Earthshaker", "Every boulder slows ground troops within 2 tiles by "
      "50% for 2 s.", M(hit="b_bowler_quake"), _R),
    U("magic_archer", "Ricochet", "Arrows ricochet to the nearest other enemy within "
      "4 tiles for 60% damage.", M(hit="b_ma_ricochet")),
    U("night_witch", "Bat Storm", "Summons 3 Bats twice as often, and 6 burst out "
      "when she falls.", lambda c: {"spawner": (c.spawner[0], 3, c.spawner[2] / 2),
                                    "death_spawn": (c.death_spawn[0], 6)}, _L),
    U("flying_machine", "Bombing Run", "Drops a bomb on ground troops below it "
      "every 3 s.", M(tick="b_fm_bombs")),
    U("electro_dragon", "Static Aura", "Zaps the nearest enemy within 3.5 tiles "
      "every second (0.5 s stun).", M(tick="b_edragon_aura")),
    U("mega_knight", "Last Stand", "Slams one last time when he falls: triple "
      "damage over a wider area, knocking everything back.", M(death="b_mk_last_stand")),
    U("cannon_cart", "Dig In", "When the cart breaks, the cannon digs in as a "
      "Cannon.", M(death="b_cart_fort")),
    U("ice_golem", "Blizzard Golem", "A blizzard swirls around him: enemies within "
      "2.5 tiles are slowed by 40%.", M(tick="b_icegolem_chill")),
    U("miner", "Prospector", "Every hit on a tower or building digs up 0.25 elixir.",
      M(hit="b_miner_gold"), _R),
    U("battle_ram", "Elite Convoy", "Two Elite Barbarians jump out when it breaks "
      "(instead of Barbarians).", lambda c: {"death_spawn": ("elite_barbarians", 2)},
      _L),
    U("wall_breakers", "Demolition Crew", "Each one leaves a Bomber behind in the "
      "rubble.", M(death="b_wb_bomber")),
    U("electro_spirit", "Spirit Split", "It splits into 2 more Electro Spirits when "
      "it zaps (once).", M(death="b_espirit_split")),
    U("electro_giant", "Storm Giant", "Every 2 s lightning arcs from him to up to 3 "
      "enemies within 4 tiles.", M(tick="b_egiant_storm"), _L),
    U("battle_healer", "Last Prayer", "When she falls, every friendly troop within "
      "5 tiles is fully healed.", M(death="b_healer_martyr")),
    U("elixir_golem", "Elixir Reversal", "Its Elixir Blobs pay YOU their elixir "
      "instead of the opponent.", _EG, _L, subs=("elixir_golemite", "elixir_blob")),
]


from chaos_mods import _register  # noqa: E402
_register(UNIQUE)
