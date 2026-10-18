"""
============================================================================
  CHAOS_MODS_A.PY  --  unique modifiers: small troops, classics, air
============================================================================

One unique modifier per card (see chaos_mods.py for how they work). Hook
names start with "a_" so they never clash with the other batches.
============================================================================
"""

import math
import random

import config as cfg
from chaos_mods import U, M, spawn, fwd, _L, _E, _R
from chaos_hooks import hook


def _clamp(x, y):
    return (min(max(x, 0.5), cfg.GRID_COLS - 0.5), min(max(y, 0.5), cfg.GRID_ROWS - 0.5))


def _foes(match, e, x, y, r, air=True, troops_only=False):
    """Living enemies of `e` within r of (x, y)."""
    out = []
    for o in match.entities:
        if (o.alive and o.team != e.team and not o.untargetable
                and (air or not o.flying)
                and not (troops_only and (o.is_tower or o.is_building))
                and math.hypot(o.x - x, o.y - y) <= r + o.radius * 0.5):
            out.append(o)
    return out


def _allies(match, e, r):
    return [o for o in match.entities
            if o.alive and o.team == e.team and not o.is_tower and not o.is_building
            and math.hypot(o.x - e.x, o.y - e.y) <= r]


def _aoe_fx(match, team, x, y, r, key):
    from engine import Effect
    match.effects.append(Effect("aoe", team, x, y, r, 0.35, card_key=key))


def _every(e, attr, period, dt, first=None):
    """True once every `period` seconds (after deploy) for entity e."""
    if e.deploy_timer > 0:
        return False
    t = getattr(e, attr, period if first is None else first) - dt
    if t <= 0:
        setattr(e, attr, t + period)
        return True
    setattr(e, attr, t)
    return False


# ================================================================ hooks
@hook("death")
def a_skeletons_reassemble(e, match):
    """Skeletons: each one pulls itself back together once."""
    if getattr(e, "_reborn", False) or e.sacrificed:
        return
    for u in spawn(match, e.team, e.key, 1, e.x, e.y, power=e.power, level=e.level,
                   deploy=0.6):
        u._reborn = True


@hook("death")
def a_ice_spirit_nova(e, match):
    """Ice Spirit: bursts into a Frost Nova - freezes everything in 3 tiles."""
    _aoe_fx(match, e.team, e.x, e.y, 3.0, "freeze")
    match.area_damage(e.team, e.x, e.y, 3.0, 0, hit_air=True, freeze=2.0)


@hook("death")
def a_fire_spirit_chain(e, match):
    """Fire Spirit: each blast lights the next spirit (3 in a row)."""
    gen = getattr(e, "_gen", 0)
    if gen >= 2 or e.sacrificed:
        return
    x, y = _clamp(e.x, e.y - fwd(e.team) * 0.8)
    for u in spawn(match, e.team, e.key, 1, x, y, power=e.power, level=e.level, deploy=0.3):
        u._gen = gen + 1


@hook("hit")
def a_goblins_pickpocket(src, target, dmg, x, y, match):
    """Goblins: every stab pockets a little elixir."""
    match.add_elixir(src.seat if src.seat < len(match.elixir) else src.team, 0.08)


@hook("hit")
def a_spear_goblins_pin(src, target, dmg, x, y, match):
    """Spear Goblins: spears pin troops to the ground for a moment."""
    if target is not None and target.alive and not (target.is_tower or target.is_building):
        target.root_timer = max(target.root_timer, 0.6)


@hook("tick")
def a_bats_colony(e, dt, match):
    """Bats: every 4 s each bat calls one more (2 per bat at most)."""
    if getattr(e, "_calls", 0) >= 2:
        return
    if _every(e, "_colony_t", 4.0, dt):
        e._calls = getattr(e, "_calls", 0) + 1
        spawn(match, e.team, "bat", 1, e.x + random.uniform(-0.5, 0.5), e.y,
              power=e.power, level=e.level)


@hook("tick")
def a_skeleton_barrel_rain(e, dt, match):
    """Skeleton Barrel: drops a Skeleton every 1.2 s on its way (6 at most)."""
    if getattr(e, "_drops", 0) >= 6:
        return
    if _every(e, "_rain_t", 1.2, dt):
        e._drops = getattr(e, "_drops", 0) + 1
        spawn(match, e.team, "skeleton", 1, e.x, e.y, power=e.child_power(), level=e.level)


@hook("hit")
def a_knight_bash(src, target, dmg, x, y, match):
    """Knight: every 3rd swing is a shield bash - stun and shove."""
    src._bash_n = getattr(src, "_bash_n", 0) + 1
    if src._bash_n % 3 or target is None or not target.alive:
        return
    target.stun_timer = max(target.stun_timer, 1.0)
    target.reset_charge()
    if not (target.is_tower or target.is_building or target.card.no_knockback):
        d = math.hypot(target.x - src.x, target.y - src.y) or 1.0
        target.x, target.y = _clamp(target.x + (target.x - src.x) / d * 1.2,
                                    target.y + (target.y - src.y) / d * 1.2)
    _aoe_fx(match, src.team, target.x, target.y, 0.8, "knight")


@hook("tick")
def a_archers_rain(e, dt, match):
    """Archers: every 5 s each archer calls an arrow rain on her target."""
    t = e.target
    if t is None or not t.alive or not _every(e, "_rain_t", 5.0, dt, first=2.0):
        return
    _aoe_fx(match, e.team, t.x, t.y, 2.0, "arrows")
    match.emit("impact", "arrows", t.x, t.y, e.team, radius=2.0)
    match.area_damage(e.team, t.x, t.y, 2.0, e.dmg * 2.0, hit_air=True,
                      tower_damage=e.dmg * 0.6)


@hook("hit")
def a_bomber_cluster(src, target, dmg, x, y, match):
    """Bomber: every bomb splits into 3 bomblets that land around it."""
    for i in range(3):
        a = i * 2 * math.pi / 3 + random.uniform(0, 0.6)
        bx, by = _clamp(x + math.cos(a) * 1.5, y + math.sin(a) * 1.5)
        _aoe_fx(match, src.team, bx, by, 1.0, "bomber")
        match.area_damage(src.team, bx, by, 1.0, dmg * 0.5, hit_air=False,
                          tower_damage=dmg * 0.15)


@hook("hit")
def a_valkyrie_vortex(src, target, dmg, x, y, match):
    """Valkyrie: her spin is a vortex - pulls ground troops within 3.5 tiles in."""
    for o in _foes(match, src, src.x, src.y, 3.5, air=False, troops_only=True):
        if o.card.no_knockback:
            continue
        d = math.hypot(src.x - o.x, src.y - o.y)
        if d > 1.2:
            o.x += (src.x - o.x) / d * 0.7
            o.y += (src.y - o.y) / d * 0.7


@hook("hit")
def a_mini_pekka_frenzy(src, target, dmg, x, y, match):
    """Mini P.E.K.K.A: every kill enrages him and patches him up."""
    if target is not None and not target.alive and not target.is_tower:
        src.rage_timer = max(src.rage_timer, 4.0)
        src.hp = min(src.max_hp, src.hp + src.max_hp * 0.3)


@hook("hit")
def a_musketeer_headshot(src, target, dmg, x, y, match):
    """Musketeer: 1 shot in 4 is a headshot for triple damage."""
    if target is not None and target.alive and random.random() < 0.25:
        target.take_damage(dmg * (0.6 if target.is_tower else 2.0))
        _aoe_fx(match, src.team, target.x, target.y, 0.5, "musketeer")


@hook("death")
def a_barbarians_horn(e, match):
    """Barbarians: a fallen Barbarian's war horn enrages his mates for 4 s."""
    for o in _allies(match, e, 4.5):
        o.rage_timer = max(o.rage_timer, 4.0)


@hook("tick")
def a_elite_barbarians_unstoppable(e, dt, match):
    """Elite Barbarians: can't be stunned, frozen, slowed or rooted."""
    e.stun_timer = e.freeze_timer = e.root_timer = 0.0
    if e.slow_timer > 0:
        e.slow_timer, e.slow_factor = 0.0, 1.0


@hook("hit")
def a_wizard_firewall(src, target, dmg, x, y, match):
    """Wizard: his fireballs leave burning ground behind."""
    if target is not None:
        return                                  # splash shots report the impact point
    from engine import Effect
    fx = Effect("poison", src.team, x, y, 1.3, 2.5, dps=dmg * 0.35, card_key="fire_spirit")
    match.effects.append(fx)


@hook("hit")
def a_pekka_execute(src, target, dmg, x, y, match):
    """P.E.K.K.A: finishes off any troop or building left under 75% hp."""
    if (target is not None and target.alive and not target.is_tower
            and target.hp < target.max_hp * 0.75):
        target.take_damage(target.hp + target.shield + 1)
        _aoe_fx(match, src.team, target.x, target.y, 1.0, "pekka")


@hook("hit")
def a_prince_skewer(src, target, dmg, x, y, match):
    """Prince: a charged hit skewers through - everything 3 tiles behind
    the target takes it too."""
    if target is None or dmg < src.dmg * 1.5:
        return
    d = math.hypot(target.x - src.x, target.y - src.y) or 1.0
    ux, uy = (target.x - src.x) / d, (target.y - src.y) / d
    for step in (1.2, 2.4):
        px, py = _clamp(target.x + ux * step, target.y + uy * step)
        _aoe_fx(match, src.team, px, py, 0.9, "prince")
        match.area_damage(src.team, px, py, 0.9, dmg * 0.6, hit_air=False,
                          tower_damage=dmg * 0.2)


@hook("tick")
def a_giant_skeleton_bombs(e, dt, match):
    """Giant Skeleton: drops a lit bomb behind him every 4 s."""
    if not _every(e, "_bomb_t", 4.0, dt, first=3.0):
        return
    from engine import Effect
    bx, by = _clamp(e.x, e.y - fwd(e.team) * 0.8)
    dd = e.card.death_damage or (2.0, 300)
    match.effects.append(Effect("death_bomb", e.team, bx, by, dd[0] * 0.8, 1.5,
                                damage=dd[1] * e.power[1] * 0.35, knockback=1.0,
                                card_key="giant_skeleton"))


@hook("tick")
def a_lumberjack_trail(e, dt, match):
    """Lumberjack: leaves a small Rage puddle wherever he walks (every 3 s)."""
    if not _every(e, "_rage_t", 3.0, dt, first=1.0):
        return
    from engine import Effect
    match.effects.append(Effect("rage", e.team, e.x, e.y, 2.0, 3.0))


@hook("hit")
def a_bandit_vanish(src, target, dmg, x, y, match):
    """Bandit: vanishes in a puff of smoke after every hit (1.2 s)."""
    src.invis_timer = max(src.invis_timer, 1.2)


@hook("death")
def a_hog_rider_piglets(e, match):
    """Hog Rider: when he falls his hog bolts on - 2 Royal Hogs burst out."""
    if e.sacrificed:
        return
    spawn(match, e.team, "royal_hogs", 2, e.x, e.y, power=e.power, level=e.level)


@hook("tick")
def a_royal_giant_escort(e, dt, match):
    """Royal Giant: a Royal Guard joins him every 6 s (4 at most)."""
    if getattr(e, "_guards", 0) >= 4 or not _every(e, "_guard_t", 6.0, dt, first=2.0):
        return
    e._guards = getattr(e, "_guards", 0) + 1
    side = 1.0 if e._guards % 2 else -1.0
    spawn(match, e.team, "guards", 1, e.x + side * 1.0, e.y, power=e.child_power(),
          level=e.level)


@hook("tick")
def a_balloon_carpet(e, dt, match):
    """Balloon: drops a small bomb every second on whatever it flies over."""
    if not _every(e, "_carpet_t", 1.0, dt):
        return
    _aoe_fx(match, e.team, e.x, e.y, 1.2, "bomber")
    match.area_damage(e.team, e.x, e.y, 1.2, e.dmg * 0.18, hit_air=False,
                      tower_damage=e.dmg * 0.08)


@hook("hit")
def a_golem_quake(src, target, dmg, x, y, match):
    """Golem: every punch is a quake - damages and slows all around him."""
    _aoe_fx(match, src.team, src.x, src.y, 2.5, "earthquake")
    match.area_damage(src.team, src.x, src.y, 2.5, dmg * 0.4, hit_air=False,
                      slow=(0.6, 1.5), tower_damage=dmg * 0.1)


@hook("death")
def a_minions_swarm(e, match):
    """Minions: each one that falls sends a Bat to take its place."""
    if not e.sacrificed:
        spawn(match, e.team, "bat", 1, e.x, e.y, power=e.power, level=e.level)


@hook("death")
def a_minion_horde_kamikaze(e, match):
    """Minion Horde: every Minion dive-bombs as it falls."""
    if e.sacrificed:
        return
    _aoe_fx(match, e.team, e.x, e.y, 1.3, "bomber")
    match.area_damage(e.team, e.x, e.y, 1.3, e.dmg * 2.0, hit_air=True,
                      tower_damage=e.dmg * 0.6)


@hook("hit")
def a_mega_minion_payload(src, target, dmg, x, y, match):
    """Mega Minion: every 3rd hit drops a heavy payload (splash + stun)."""
    src._pay_n = getattr(src, "_pay_n", 0) + 1
    if src._pay_n % 3 or target is None:
        return
    _aoe_fx(match, src.team, target.x, target.y, 1.8, "bomber")
    match.area_damage(src.team, target.x, target.y, 1.8, dmg * 1.5, hit_air=True,
                      stun=0.6, tower_damage=dmg * 0.5)


@hook("death")
def a_baby_dragon_clutch(e, match):
    """Baby Dragon: a clutch of 2 Skeleton Dragons hatches when she falls."""
    if e.sacrificed:
        return
    spawn(match, e.team, "skeleton_dragons", 2, e.x, e.y, power=e.power, level=e.level)


@hook("hit")
def a_inferno_dragon_split(src, target, dmg, x, y, match):
    """Inferno Dragon: the beam forks onto the nearest other enemy."""
    if target is None:
        return
    others = [o for o in _foes(match, src, target.x, target.y, 3.0)
              if o is not target and not o.is_tower]
    if others:
        o = min(others, key=lambda o: math.hypot(o.x - target.x, o.y - target.y))
        o.take_damage(dmg)
        match.bolt(src.team, target, o, "inferno_dragon", life=0.15)


@hook("hit")
def a_princess_fire(src, target, dmg, x, y, match):
    """Princess: her flaming arrows set the ground ablaze."""
    if target is not None:
        return
    from engine import Effect
    match.effects.append(Effect("poison", src.team, x, y, 1.8, 3.0, dps=dmg * 0.5,
                                card_key="fire_spirit"))


@hook("tick")
def a_electro_wizard_storm(e, dt, match):
    """Electro Wizard: every 2 s lightning arcs to up to 3 enemies in 5 tiles."""
    if not _every(e, "_storm_t", 2.0, dt, first=1.0):
        return
    foes = sorted(_foes(match, e, e.x, e.y, 5.0),
                  key=lambda o: math.hypot(o.x - e.x, o.y - e.y))[:3]
    for o in foes:
        o.take_damage(e.dmg * (0.4 if o.is_tower else 1.0))
        o.stun_timer = max(o.stun_timer, 0.5)
        match.bolt(e.team, e, o, "electro_wizard")


@hook("tick")
def a_ice_wizard_blizzard(e, dt, match):
    """Ice Wizard: a blizzard swirls round him - slows and chills enemies in
    3.5 tiles every half second."""
    if not _every(e, "_bliz_t", 0.5, dt):
        return
    for o in _foes(match, e, e.x, e.y, 3.5, troops_only=True):
        o.slow_factor, o.slow_timer = 0.5, 0.8
        o.take_damage(e.dmg * 0.1)


@hook("death")
def a_three_musketeers_last_stand(e, match):
    """Three Musketeers: when one falls, the others are enraged and healed."""
    if e.sacrificed:
        return
    for o in _allies(match, e, 8.0):
        if o.key == e.key:
            o.rage_timer = max(o.rage_timer, 6.0)
            o.hp = min(o.max_hp, o.hp + o.max_hp * 0.5)


# ================================================================ the list
UNIQUE = [
    U("skeletons", "Undying Bones", "Every Skeleton pulls itself back together "
      "once when destroyed.", M(death="a_skeletons_reassemble"), _R),
    U("ice_spirit", "Frost Nova", "Bursts into a Frost Nova: freezes everything "
      "within 3 tiles for 2 s.", M(death="a_ice_spirit_nova")),
    U("fire_spirit", "Chain Reaction", "Each blast lights another Fire Spirit - "
      "three in a row.", M(death="a_fire_spirit_chain")),
    U("goblins", "Pickpockets", "Every stab steals 0.08 elixir for you.",
      M(hit="a_goblins_pickpocket"), _R),
    U("spear_goblins", "Pinning Spears", "Spears pin troops in place for 0.6 s.",
      M(hit="a_spear_goblins_pin"), _R),
    U("bats", "Bat Colony", "Every 4 s each Bat calls another (2 each at most).",
      M(tick="a_bats_colony")),
    U("skeleton_barrel", "Bone Rain", "Drops a Skeleton every 1.2 s on the way "
      "(6 in all) before it bursts.", M(tick="a_skeleton_barrel_rain")),
    U("knight", "Shield Bash", "Every 3rd swing is a shield bash: stuns 1 s and "
      "shoves the target back.", M(hit="a_knight_bash"), _R),
    U("archers", "Arrow Rain", "Every 5 s each Archer calls an arrow rain on her "
      "target.", M(tick="a_archers_rain")),
    U("bomber", "Cluster Bombs", "Every bomb splits into 3 bomblets around it.",
      M(hit="a_bomber_cluster")),
    U("valkyrie", "Vortex Spin", "Her spin pulls ground troops within 3.5 tiles "
      "into her axe.", M(hit="a_valkyrie_vortex")),
    U("mini_pekka", "Pancake Frenzy", "Every kill enrages him (4 s) and heals him "
      "30%.", M(hit="a_mini_pekka_frenzy")),
    U("musketeer", "Headshot", "1 shot in 4 is a headshot for triple damage.",
      M(hit="a_musketeer_headshot"), _R),
    U("barbarians", "War Horn", "When a Barbarian falls, his horn enrages every "
      "ally around for 4 s.", M(death="a_barbarians_horn")),
    U("elite_barbarians", "Unstoppable", "Can't be stunned, frozen, slowed or "
      "rooted.", M(tick="a_elite_barbarians_unstoppable")),
    U("wizard", "Wall of Fire", "His fireballs leave burning ground behind.",
      M(hit="a_wizard_firewall")),
    U("witch", "Bat Witch", "Summons 4 Bats instead of Skeletons.",
      lambda c: {"spawner": ("bat", 4, c.spawner[2])}, _R),
    U("pekka", "Execution", "Instantly kills any troop or building (not "
      "towers) left under 75% hp.", M(hit="a_pekka_execute"), _L),
    U("prince", "Skewer", "A charged hit runs through: everything 2-3 tiles "
      "behind the target is hit too.", M(hit="a_prince_skewer")),
    U("dark_prince", "Dark Leap", "Leaps onto targets 3-5 tiles away with a "
      "shield slam (splash).",
      lambda c: {"dash": (3.0, 5.5), "dash_damage": (1.8, int(c.damage * 1.5))}),
    U("giant_skeleton", "Bomb Carrier", "Drops a lit bomb behind him every 4 s.",
      M(tick="a_giant_skeleton_bombs"), _L),
    U("lumberjack", "Rage Trail", "Spills a Rage puddle where he walks every 3 s.",
      M(tick="a_lumberjack_trail")),
    U("bandit", "Smoke Bomb", "Vanishes (untargetable) for 1.2 s after every hit.",
      M(hit="a_bandit_vanish")),
    U("hog_rider", "Hog Wild", "When he falls, 2 Royal Hogs charge on.",
      M(death="a_hog_rider_piglets")),
    U("royal_giant", "Royal Escort", "A Royal Guard joins him every 6 s (up to 4).",
      M(tick="a_royal_giant_escort")),
    U("balloon", "Carpet Bomber", "Drops a small bomb every second on whatever it "
      "flies over.", M(tick="a_balloon_carpet"), _L),
    U("golem", "Earthshaker", "Every punch is a quake that damages and slows "
      "everything around him.", M(hit="a_golem_quake")),
    U("minions", "Swarm Call", "Each Minion that falls sends a Bat in its place.",
      M(death="a_minions_swarm"), _R),
    U("minion_horde", "Dive Bombers", "Every Minion dive-bombs as it falls (splash "
      "damage).", M(death="a_minion_horde_kamikaze")),
    U("mega_minion", "Heavy Payload", "Every 3rd hit drops a payload: big splash "
      "and a stun.", M(hit="a_mega_minion_payload")),
    U("baby_dragon", "Dragon Clutch", "2 Skeleton Dragons hatch when she falls.",
      M(death="a_baby_dragon_clutch")),
    U("inferno_dragon", "Forked Beam", "The beam forks onto the nearest other "
      "enemy, burning both.", M(hit="a_inferno_dragon_split"), _L),
    U("princess", "Flaming Arrows", "Her arrows set the ground ablaze where they "
      "land.", M(hit="a_princess_fire")),
    U("electro_wizard", "Lightning Field", "Every 2 s lightning arcs to up to 3 "
      "enemies within 5 tiles (stun).", M(tick="a_electro_wizard_storm"), _L),
    U("ice_wizard", "Blizzard Aura", "A blizzard swirls round him: slows and chills "
      "every enemy troop within 3.5 tiles.", M(tick="a_ice_wizard_blizzard")),
    U("three_musketeers", "Last Stand", "When one Musketeer falls, the others are "
      "enraged for 6 s and healed 50%.", M(death="a_three_musketeers_last_stand")),
]


from chaos_mods import _register  # noqa: E402
_register(UNIQUE)
