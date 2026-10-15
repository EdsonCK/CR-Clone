"""
============================================================================
  EVENTS.PY  --  Deploy, death, ability, spawn and battle-FX sounds
============================================================================

SOUNDS[name](v) -> variant v (0..2) of assets/sounds/<name>_<v+1>.ogg:

  <card>_deploy      placing a unit / building: its voice + how it lands
  die_<group>        a unit dying (groups: human, goblin, skeleton, ...;
                     src/sounds.py DEATH_GROUP maps every unit to one)
  <card>_ability     champion / hero / evolution abilities
  <spawner>_spawn    a building (or Witch) bringing out its units
  dash, slam, portal, tower_down     shared battle effects

LOUD / ROOM: per-name loudness (dB) and reverb level, like attack.py.
============================================================================
"""

import zlib

import numpy as np

import dsp as D
import kit as K
from kit import at, pitch, head, pick, tk

DET = (0.0, -0.5, 0.55)
SOUNDS = {}
LOUD = {}
ROOM = {}


def _off(name):
    return zlib.crc32(name.encode()) % 7


def L(pool, v, name, st=0.0, ln=None, db=0.0, t=0.0, idx=0, peak=False):
    """One layer: take (v + offset + idx) of pool, pitched/cut/levelled."""
    x = tk(pick(pool, v + _off(name) + idx))
    if peak:
        x = K.from_peak(x, 0.03)
    x = pitch(x, st)
    if ln:
        x = head(x, ln)
    return at(D.gain(x, db), t)


def S(name, fn, loud=-16.0, room=None):
    SOUNDS[name] = (lambda v, n=name: fn(v, n))
    LOUD[name] = loud
    if room is not None:
        ROOM[name] = room


# ======================================================================
#  LANDINGS (how a deployed unit / building arrives)
# ======================================================================
def land(kind, v, name, st=0.0):
    """Layers for the landing, ~0.15-0.4 s after the start."""
    t = 0.0
    if kind == "foot":
        return [L(K.FOOTSTEP, v, name, st, 0.2, -6, t), L(K.CLOTH, v, name, st, 0.25, -12, t)]
    if kind == "armor":
        return [L(K.FOOTSTEP, v, name, st, 0.2, -6, t), L(K.ARMOR, v, name, st, 0.3, -9, t)]
    if kind == "hooves":
        return [L(K.FOOTSTEP, v, name, st - 4, 0.2, -4, t), L(K.FOOTSTEP, v, name, st - 3, 0.2, -6,
                                                              t + 0.12, 2),
                at(D.gain(K.thump(90, 0.15, 0.6, v), -8), t)]
    if kind == "heavy":
        return [at(D.gain(K.thump(60 * D.semis(st), 0.3, 0.5, v), -2), t),
                L(K.PUNCH_HEAVY, v, name, st - 2, 0.35, -4, t),
                L(K.STONE, v, name, st, 0.35, -10, t + 0.02)]
    if kind == "huge":
        return [at(D.gain(K.thump(48 * D.semis(st), 0.45, 0.5, v), 0), t),
                L(K.LOWBOOM, v, name, st, 0.6, -6, t, peak=True),
                L(K.STONE, v, name, st - 2, 0.4, -6, t + 0.03),
                L(K.PUNCH_HEAVY, v, name, st - 3, 0.35, -5, t)]
    if kind == "fly":
        return [L(K.FLAP, v, name, st, 0.5, -2, t, peak=True)]
    if kind == "bones":
        return [L(K.BONE, v, name, st, 0.15, -2, t), L(K.BONE, v, name, st + 2, 0.15, -4,
                                                       t + 0.06, 2),
                L(K.BONE, v, name, st - 1, 0.15, -5, t + 0.12, 4)]
    if kind == "build_wood":
        return [L(K.WOOD, v, name, st - 2, 0.35, -2, t), L(K.CHOP, v, name, st, 0.25, -6, t + 0.15),
                L(K.HAMMER, v, name, st + 2, 0.25, -12, t + 0.3),
                at(D.gain(K.thump(70, 0.25, 0.5, v), -4), t)]
    if kind == "build_stone":
        return [L(K.STONE, v, name, st - 3, 0.45, -2, t), L(K.MINING, v, name, st - 2, 0.35, -5, t),
                at(D.gain(K.thump(55, 0.35, 0.5, v), -2), t)]
    if kind == "build_metal":
        return [L(K.PLATE, v, name, st, 0.35, -3, t), L(K.METAL_HEAVY, v, name, st - 2, 0.3, -6,
                                                        t + 0.12),
                L(K.CLICKS, v, name, st, 0.15, -12, t + 0.3),
                at(D.gain(K.thump(65, 0.25, 0.5, v), -4), t)]
    if kind == "spirit":
        return [at(D.gain(K.whoosh(0.35, 700, 3800, v), -6), t)]
    if kind == "dig":
        return [L(K.MINING, v, name, st, 0.3, -3, t), L(K.STONE, v, name, st + 2, 0.35, -6, t + 0.1),
                L(K.GRASS, v, name, st, 0.2, -6, t + 0.05)]
    return []


def deploy(voice=None, vst=0.0, vdb=0.0, vlen=0.6, kind="foot", lst=0.0, extra=None,
           vt=0.06, crowd=0, champion=False):
    """Voice (+ a small crowd of extra voices) + landing + extra layers."""
    def f(v, name):
        st = DET[v]
        layers = land(kind, v, name, lst + st * 0.5)
        if voice is not None:
            layers.append(L(voice, v, name, vst + st, vlen, vdb, vt))
            for c in range(crowd):
                layers.append(L(voice, v, name, vst + st + (1.2, -1.0, 2.0)[c % 3], vlen * 0.8,
                                vdb - 4 - 1.5 * c, vt + 0.07 * (c + 1), 2 + 3 * c))
        if extra is not None:
            layers.extend(extra(v, name, st))
        if champion:
            layers.append(at(D.gain(K.shimmer(1500 * D.semis(st), 0.6, v + 3), -14), 0.05))
            layers.append(at(D.gain(K.thump(55, 0.4, 0.5, v), -6), 0.0))
        return D.mix(*layers)
    return f


def X(fn_or_pool, db=0.0, t=0.0, st=0.0, ln=0.4, peak=False, idx=1):
    """An extra layer: a pool take or a synth function(v, st)."""
    def e(v, name, s):
        if callable(fn_or_pool):
            return [at(D.gain(fn_or_pool(v, s), db), t)]
        return [L(fn_or_pool, v, name, st + s, ln, db, t, idx=idx, peak=peak)]
    return e


def XX(*extras):
    def e(v, name, s):
        out = []
        for x in extras:
            out.extend(x(v, name, s))
        return out
    return e


zap_x = X(lambda v, s: K.zap(0.25, v + 11, 3000 * D.semis(s)), -6, 0.05)
fire_x = X(lambda v, s: K.crackle_fire(0.45, v), -6, 0.05)
fizz_x = X(lambda v, s: K.fizz(0.4, v, 5000), -16, 0.05)
shim_x = X(lambda v, s: K.shimmer(1700 * D.semis(s), 0.5, v), -10, 0.05)
ice_x = X(K.ICY, -6, 0.05, ln=0.4)
glass_x = X(K.GLASS, -8, 0.08, ln=0.3)
bubble_x = X(K.BUBBLES, -6, 0.15, ln=0.4)
slime_x = X(K.SLIME, -4, 0.05, ln=0.4)
metal_x = X(K.PLATE_MED, -8, 0.05, ln=0.3)
clicks_x = X(K.CLICKS, -10, 0.2, ln=0.15)
whoosh_x = X(lambda v, s: K.whoosh(0.35, 400, 2400, v), -8, 0.0)
shing_x = X(K.SHING, -10, 0.05, ln=0.4)
chop_x = X(K.CHOP, -8, 0.2, ln=0.25)
splash_x = X(K.SPLATS, -8, 0.15, ln=0.35)
bones_x = X(K.BONE, -6, 0.05, ln=0.15)
goblin_x = X(K.V_GOBLIN_LAUGH, -6, 0.25, ln=0.6, st=2)
flap_x = X(K.FLAP, -6, 0.0, ln=0.45, peak=True)
creak_x = X(K.CREAK, -10, 0.05, ln=0.4)
drill_x = X(lambda v, s: K.drill(0.4, 160, v), -8, 0.1)
magic_x = X(K.MAGIC, -10, 0.05, ln=0.5)
engine_x = X([(K.KS, "engineCircular_003.ogg"), (K.KS, "engineCircular_001.ogg"),
              (K.KS, "engineCircular_002.ogg")], -6, 0.0, ln=0.6, peak=True)
gong_x = X([(K.SFX100, "gong_01.ogg"), (K.SFX100, "gong_02.ogg")], -8, 0.05, ln=0.8)
chime_x = X(lambda v, s: K.chime(988 * D.semis(s), (0, 4, 7), 0.05, 0.5), -8, 0.05)
rustle_x = X(lambda v, s: D.bp(D.noise(0.4, "pink", v), 1500, 6000) * 0.7, -6, 0.0)

DEPLOY = {
    # --- small & swarms
    "skeletons": deploy(K.V_TINY, 6, -8, 0.35, "bones", crowd=1),
    "skeleton_army": deploy(K.V_TINY, 7, -8, 0.35, "bones", crowd=3,
                            extra=XX(bones_x, X(K.BONE, -6, 0.2, ln=0.15, idx=3))),
    "guards": deploy(K.V_TINY, 4, -8, 0.35, "bones", crowd=2, extra=metal_x),
    "skeleton_barrel": deploy(None, kind="fly", extra=XX(creak_x, X(K.WOOD, -8, 0.1, ln=0.3))),
    "goblins": deploy(K.V_GOBLIN, 0, 0, 0.45, "foot", crowd=2),
    "goblin_gang": deploy(K.V_GOBLIN, 0, 0, 0.45, "foot", crowd=3),
    "spear_goblins": deploy(K.V_GOBLIN, 1, 0, 0.45, "foot", crowd=2),
    "dart_goblin": deploy(K.V_GOBLIN, 2, 0, 0.45, "foot"),
    "goblin_demolisher": deploy(K.V_GOBLIN_LAUGH, -1, 0, 0.6, "foot", extra=fizz_x),
    "goblin_machine": deploy(K.V_GOBLIN_LAUGH, 0, -2, 0.6, "build_metal", extra=engine_x),
    "goblin_giant": deploy(K.V_GIANT, 1, 0, 0.7, "heavy", extra=goblin_x),
    "bats": deploy(K.V_BUG, 8, -4, 0.3, "fly", lst=6, crowd=2),
    "minions": deploy(K.V_CREATURE, 6, -4, 0.4, "fly", lst=3, crowd=2),
    "minion_horde": deploy(K.V_CREATURE, 6, -4, 0.4, "fly", lst=3, crowd=3),
    "mega_minion": deploy(K.V_CREATURE, 1, 0, 0.5, "fly", extra=metal_x),
    "minion_giant": deploy(K.V_CREATURE, -4, 0, 0.6, "fly", lst=-4),
    "wall_breakers": deploy(K.V_ZOMBIE, 5, -4, 0.4, "bones", crowd=1, extra=fizz_x),
    "bomber": deploy(K.V_ZOMBIE, 4, -4, 0.4, "bones", extra=fizz_x),
    # --- spirits
    "ice_spirit": deploy(K.V_CUTE, 4, -6, 0.4, "spirit", extra=XX(ice_x, glass_x)),
    "fire_spirit": deploy(K.V_CUTE, 2, -6, 0.4, "spirit", extra=fire_x),
    "electro_spirit": deploy(K.V_CUTE, 5, -6, 0.4, "spirit", extra=zap_x),
    "heal_spirit": deploy(K.V_CUTE, 3, -6, 0.4, "spirit", extra=chime_x),
    "suspicious_bush": deploy(None, kind="foot", extra=XX(rustle_x, X(K.CLOTH, -4, 0.0, ln=0.4))),
    # --- humans
    "knight": deploy(K.V_MALE_GRUNT, 0, 0, 0.5, "armor"),
    "archers": deploy(K.V_FEMALE, 1, -2, 0.4, "foot", crowd=1),
    "valkyrie": deploy(K.V_FEMALE, -2, 0, 0.5, "armor", extra=whoosh_x),
    "musketeer": deploy(K.V_FEMALE, 0, -1, 0.45, "armor", extra=clicks_x),
    "three_musketeers": deploy(K.V_FEMALE, 0, -1, 0.45, "armor", crowd=2, extra=clicks_x),
    "barbarians": deploy(K.V_BATTLECRY, -1, 0, 0.8, "armor", crowd=2),
    "elite_barbarians": deploy(K.V_BATTLECRY, 1, 0, 0.7, "armor", crowd=1),
    "wizard": deploy(K.V_MALE_YELL, 1, 0, 0.5, "foot", extra=fire_x),
    "ice_wizard": deploy(K.V_MALE_GRUNT, 2, -2, 0.5, "foot", extra=XX(ice_x, whoosh_x)),
    "electro_wizard": deploy(K.V_MALE_YELL, 2, 0, 0.5, "foot", extra=zap_x),
    "witch": deploy(K.V_WITCH, 0, -2, 0.8, "foot", extra=magic_x),
    "mother_witch": deploy(K.V_WITCH, 2, -2, 0.8, "foot", extra=magic_x),
    "night_witch": deploy(K.V_WITCH, -3, -2, 0.8, "foot", extra=flap_x),
    "prince": deploy(K.V_MALE_YELL, 0, 0, 0.6, "hooves", extra=metal_x),
    "dark_prince": deploy(K.V_MALE_GRUNT, -3, 0, 0.5, "hooves", extra=metal_x),
    "lumberjack": deploy(K.V_MALE_YELL, 3, 0, 0.5, "foot", extra=chop_x),
    "bandit": deploy(K.V_FEMALE, 2, -1, 0.4, "foot", extra=whoosh_x),
    "hog_rider": deploy(K.V_BATTLECRY, 0, 2, 0.9, "hooves"),
    "ram_rider": deploy(K.V_FEMALE, -1, 0, 0.5, "hooves"),
    "royal_hogs": deploy(None, kind="hooves", extra=XX(X(K.FOOTSTEP, -5, 0.1, st=-5, ln=0.2),
                                                       X(K.FOOTSTEP, -6, 0.2, st=-4, ln=0.2))),
    "princess": deploy(K.V_FEMALE, 4, -2, 0.4, "foot"),
    "dagger_duchess": deploy(K.V_FEMALE, 2, -2, 0.4, "foot"),
    "hunter": deploy(K.V_MALE_GRUNT, -4, 0, 0.5, "foot", extra=clicks_x),
    "executioner": deploy(K.V_MALE_YELL, -3, 0, 0.6, "armor", extra=whoosh_x),
    "magic_archer": deploy(K.V_MALE_GRUNT, 2, -2, 0.45, "foot", extra=shim_x),
    "miner": deploy(K.V_MALE_GRUNT, 1, -2, 0.45, "dig"),
    "battle_ram": deploy(K.V_BATTLECRY, -1, 0, 0.7, "build_wood", crowd=1),
    "battle_healer": deploy(K.V_FEMALE, -1, -2, 0.45, "armor", extra=chime_x),
    "berserker": deploy(K.V_FEMALE, -2, 0, 0.45, "foot", extra=whoosh_x),
    "firecracker": deploy(K.V_FEMALE, 3, -2, 0.4, "foot", extra=fizz_x),
    "rascals": deploy(K.V_MALE_YELL, 4, 0, 0.45, "foot", extra=X(K.V_FEMALE, -3, 0.12, st=3, ln=0.4)),
    "royal_recruits": deploy(K.V_MALE_GRUNT, 1, -2, 0.4, "armor", crowd=3,
                             extra=X(K.SHIELD_HIT, -8, 0.1, ln=0.25)),
    "fisherman": deploy(K.V_MALE_YELL, -2, 0, 0.5, "foot", extra=splash_x),
    "ronin": deploy(K.V_MALE_GRUNT, 0, 0, 0.45, "foot", extra=shing_x),
    "royal_ghost": deploy(K.V_GHOST, 3, -2, 0.6, "spirit", extra=shing_x),
    "spirit_empress": deploy(K.V_FEMALE, 1, -1, 0.45, "spirit", extra=shim_x),
    "spirit_empress_air": deploy(None, kind="spirit", extra=XX(shim_x, whoosh_x)),
    # --- big ones
    "giant": deploy(K.V_GIANT, 0, 0, 0.7, "heavy"),
    "royal_giant": deploy(K.V_GIANT, -2, 0, 0.7, "heavy", extra=metal_x),
    "electro_giant": deploy(K.V_GIANT, -1, 0, 0.7, "heavy", extra=zap_x),
    "rune_giant": deploy(K.V_GIANT, -3, 0, 0.7, "heavy", extra=chime_x),
    "goblin_monster": deploy(K.V_TROLL, 0, 0, 0.7, "heavy"),
    "giant_skeleton": deploy(K.V_ZOMBIE, -6, 0, 0.6, "heavy", extra=bones_x),
    "bowler": deploy(K.V_OGRE, 0, 0, 0.6, "heavy", extra=X(K.STONE, -6, 0.2, ln=0.35)),
    "mega_knight": deploy(K.V_MALE_GRUNT, -6, 0, 0.5, "huge", extra=metal_x),
    "golem": deploy(K.V_ROAR, -7, -2, 0.7, "huge", extra=X(K.STONE, -4, 0.15, ln=0.4)),
    "elixir_golem": deploy(K.V_MONSTER, -3, -4, 0.6, "heavy", extra=XX(slime_x, bubble_x)),
    "ice_golem": deploy(K.V_MONSTER, 2, -4, 0.5, "heavy", extra=XX(ice_x, glass_x)),
    "pekka": deploy(None, kind="heavy", extra=XX(X(K.PLATE, -2, 0.0, ln=0.4),
                                                 X(K.METAL_HEAVY, -4, 0.15, ln=0.3),
                                                 X(lambda v, s: K.drill(0.35, 90, v), -14, 0.05))),
    "mini_pekka": deploy(None, kind="armor", extra=XX(X(K.PLATE_MED, -2, 0.0, ln=0.35),
                                                      X(K.CLICKS, -8, 0.15, ln=0.15))),
    # --- flying creatures
    "baby_dragon": deploy(K.V_ROAR, 7, -2, 0.5, "fly"),
    "inferno_dragon": deploy(K.V_ROAR, 3, -2, 0.5, "fly", extra=fizz_x),
    "electro_dragon": deploy(K.V_ROAR, 1, -2, 0.5, "fly", extra=zap_x),
    "skeleton_dragons": deploy(K.V_ROAR, 6, -4, 0.45, "fly", crowd=1, extra=bones_x),
    "lava_hound": deploy(K.V_ROAR, -5, -2, 0.7, "fly", lst=-3, extra=fire_x),
    "phoenix": deploy(K.V_SCREECH, 3, -4, 0.6, "fly", extra=fire_x),
    "phoenix_reborn": deploy(K.V_SCREECH, 5, -4, 0.6, "fly", extra=fire_x),
    "balloon": deploy(None, kind="fly", extra=XX(creak_x, X(lambda v, s: K.crackle_fire(0.5, v),
                                                            -8, 0.0))),
    "flying_machine": deploy(None, kind="fly", extra=XX(engine_x, creak_x)),
    # --- machines
    "sparky": deploy(None, kind="heavy", extra=XX(X(lambda v, s: K.zap(0.5, v, 2500), -4, 0.1),
                                                  X(K.PLATE, -6, 0.0, ln=0.35))),
    "zappies": deploy(None, kind="build_metal", extra=zap_x),
    "cannon_cart": deploy(None, kind="build_metal", extra=creak_x),
    "demolisher_charge": deploy(K.V_GOBLIN, 3, 0, 0.45, "foot", extra=fizz_x),
    # --- champions
    "archer_queen": deploy(K.V_FEMALE, -1, 0, 0.5, "armor", extra=shim_x, champion=True),
    "little_prince": deploy(K.V_MALE_YELL, 5, 0, 0.5, "foot", champion=True),
    "golden_knight": deploy(K.V_MALE_GRUNT, 1, 0, 0.5, "armor", extra=shing_x, champion=True),
    "skeleton_king": deploy(K.V_ZOMBIE, -7, 0, 0.7, "huge", extra=bones_x, champion=True),
    "monk": deploy(K.V_MALE_GRUNT, -1, -2, 0.5, "foot", extra=gong_x, champion=True),
    "goblinstein": deploy(K.V_OGRE, -2, 0, 0.6, "heavy", extra=zap_x, champion=True),
    "boss_bandit": deploy(K.V_FEMALE, -3, 0, 0.5, "foot", extra=whoosh_x, champion=True),
    "mighty_miner": deploy(K.V_MALE_YELL, -1, 0, 0.5, "dig", extra=drill_x, champion=True),
    # --- buildings
    "cannon": deploy(None, kind="build_metal"),
    "tesla": deploy(None, kind="build_metal", extra=zap_x),
    "inferno_tower": deploy(None, kind="build_metal", extra=fire_x),
    "bomb_tower": deploy(None, kind="build_stone", extra=fizz_x),
    "mortar": deploy(None, kind="build_metal", extra=X(K.METAL_HEAVY, -4, 0.25, st=-4, ln=0.35)),
    "xbow": deploy(None, kind="build_metal", extra=XX(clicks_x, X(K.XBOW_MECH, -4, 0.3, ln=0.3))),
    "tombstone": deploy(None, kind="build_stone", extra=bones_x),
    "goblin_hut": deploy(None, kind="build_wood", extra=goblin_x),
    "barbarian_hut": deploy(None, kind="build_wood",
                            extra=X(K.V_BATTLECRY, -6, 0.3, st=-2, ln=0.6)),
    "furnace": deploy(None, kind="build_stone", extra=fire_x),
    "elixir_collector": deploy(None, kind="build_wood", extra=bubble_x),
    "goblin_cage": deploy(None, kind="build_metal", extra=goblin_x),
    "goblin_drill": deploy(None, kind="dig", extra=XX(drill_x, goblin_x)),
}
for k, fn in DEPLOY.items():
    S(k + "_deploy", fn, loud=-15.0 if k not in ("skeleton_army", "minion_horde") else -14.0)

# ======================================================================
#  DEATHS (per group; src/sounds.py maps units to groups)
# ======================================================================


def fall(v, name, st=0.0, heavy=False):
    if heavy:
        return [at(D.gain(K.thump(55, 0.35, 0.5, v), -2), 0.12),
                L(K.PUNCH_HEAVY, v, name, st - 3, 0.35, -4, 0.12)]
    return [L(K.SOFT_HEAVY, v, name, st, 0.2, -4, 0.1), L(K.CLOTH, v, name, st, 0.2, -10, 0.08)]


def poof(v, st=0.0, db=-6.0):
    return at(D.gain(K.whoosh(0.3, 900 * D.semis(st), 4000, v + 4), db), 0.0)


def die(fn):
    return lambda v, name: fn(v, name, DET[v])


S("die_human", die(lambda v, n, st: D.mix(L(K.V_DEATH_M, v, n, st, 0.45, -3, 0.0),
                                          *fall(v, n, st))), loud=-19)
S("die_female", die(lambda v, n, st: D.mix(L(K.V_FEMALE_HURT, v, n, st, 0.4, -3, 0.0),
                                           *fall(v, n, st))), loud=-19)
S("die_goblin", die(lambda v, n, st: D.mix(L(K.V_GOBLIN, v, n, st + 4, 0.3, -2, 0.0),
                                           poof(v, st), *fall(v, n, st + 3))), loud=-20)
S("die_skeleton", die(lambda v, n, st: D.mix(L(K.BONE, v, n, st, 0.15, 0, 0.0),
                                             L(K.BONE, v, n, st - 2, 0.15, -2, 0.05, 2),
                                             L(K.BONE, v, n, st + 1, 0.15, -4, 0.11, 4),
                                             L(K.BONE, v, n, st - 3, 0.15, -6, 0.18, 6))),
  loud=-21)
S("die_monster", die(lambda v, n, st: D.mix(L(K.V_DEATH_MONSTER, v, n, st, 0.55, -2, 0.0),
                                            *fall(v, n, st, True))), loud=-16)
S("die_giant", die(lambda v, n, st: D.mix(L(K.V_GIANT, v, n, st - 3, 0.6, -3, 0.0),
                                          *fall(v, n, st, True),
                                          L(K.STONE, v, n, st - 2, 0.35, -10, 0.15))), loud=-15)
S("die_golem", die(lambda v, n, st: D.mix(L(K.STONE, v, n, st - 4, 0.5, 0, 0.0),
                                          L(K.STONE, v, n, st - 1, 0.4, -4, 0.08, 1),
                                          at(D.gain(K.thump(50, 0.4, 0.5, v), -2), 0.0),
                                          L(K.MINING, v, n, st - 3, 0.3, -6, 0.04))), loud=-15)
S("die_machine", die(lambda v, n, st: D.mix(L(K.METAL_FALL, v, n, st, 0.5, 0, 0.0),
                                            L(K.PLATE, v, n, st - 2, 0.3, -4, 0.05),
                                            L(K.BANGS, v, n, st + 4, 0.35, -10, 0.0))), loud=-17)
S("die_building", die(lambda v, n, st: D.mix(L(K.WOOD_BREAK, v, n, st - 2, 0.5, 0, 0.0),
                                             L(K.STONE, v, n, st - 3, 0.5, -3, 0.05),
                                             at(D.gain(K.thump(50, 0.4, 0.5, v), -3), 0.0),
                                             L(K.EXPLO, v, n, st, 0.5, -10, 0.0))), loud=-15)
S("die_magic", die(lambda v, n, st: D.mix(poof(v, st, -2),
                                          at(D.gain(K.shimmer(1600 * D.semis(st), 0.4, v), -8),
                                             0.02))), loud=-20)
S("die_flyer", die(lambda v, n, st: D.mix(L(K.V_SCREECH, v, n, st + 3, 0.4, -4, 0.0),
                                          L(K.FLAP, v, n, st, 0.35, -6, 0.0, peak=True),
                                          poof(v, st, -10))), loud=-19)
S("die_bug", die(lambda v, n, st: D.mix(L(K.V_BUG, v, n, st + 2, 0.3, -2, 0.0),
                                        poof(v, st + 4, -6))), loud=-21)
S("die_elixir", die(lambda v, n, st: D.mix(L(K.SLIME, v, n, st, 0.4, 0, 0.0),
                                           L(K.BUBBLES, v, n, st + 2, 0.35, -6, 0.05))), loud=-18)
S("die_ghost", die(lambda v, n, st: D.mix(L(K.V_GHOST, v, n, st + 3, 0.6, -4, 0.0),
                                          poof(v, st - 4, -4))), loud=-19)
S("die_fire", die(lambda v, n, st: D.mix(at(D.gain(K.crackle_fire(0.4, v), -2), 0.0),
                                         at(D.gain(K.fizz(0.35, v, 4000), -12), 0.0),
                                         poof(v, st - 3, -6))), loud=-19)
S("die_small", die(lambda v, n, st: D.mix(poof(v, st, -4), *fall(v, n, st + 4))), loud=-21)
S("die_big", die(lambda v, n, st: D.mix(*fall(v, n, st, True),
                                        L(K.STONE, v, n, st - 2, 0.35, -10, 0.15))), loud=-16)


def tower_down(v, n):
    st = DET[v]
    return D.mix(L(K.EXPLO, v, n, st - 2, 1.0, 0, 0.0),
                 L(K.STONE, v, n, st - 4, 0.6, -2, 0.05),
                 L(K.STONE, v, n, st - 2, 0.6, -4, 0.25, 1),
                 L(K.WOOD_BREAK, v, n, st - 3, 0.5, -6, 0.1),
                 at(D.gain(K.thump(42, 0.7, 0.5, v), 0), 0.0),
                 L(K.LOWBOOM, v, n, st, 1.0, -4, 0.0, peak=True))


S("tower_down", tower_down, loud=-12, room=-15)

# ======================================================================
#  SHARED BATTLE FX
# ======================================================================
S("dash", lambda v, n: D.mix(at(K.whoosh(0.3, 400, 3000, v + 20), 0.0),
                             L(K.SWISH_HEAVY, v, n, DET[v], None, -4, 0.0)), loud=-18)
S("slam", lambda v, n: D.mix(at(D.gain(K.thump(45, 0.5, 0.5, v), 0), 0.0),
                             L(K.PUNCH_HEAVY, v, n, DET[v] - 4, 0.4, -3, 0.0),
                             L(K.STONE, v, n, DET[v] - 3, 0.5, -4, 0.04),
                             L(K.EXPLO, v, n, DET[v] - 2, 0.6, -8, 0.0)), loud=-13)
S("portal", lambda v, n: D.mix(L(K.MAGIC, v, n, DET[v] - 2, 0.6, -2, 0.0),
                               at(D.gain(K.whoosh(0.5, 300, 2500, v + 7), -4), 0.0),
                               L([(K.SCI, "teleport_01.ogg"), (K.SCI, "teleport_02.ogg")], v, n,
                                 DET[v], 0.5, -6, 0.0, peak=True)), loud=-17)

# ======================================================================
#  ABILITIES (champions, heroes, evolutions)
# ======================================================================


def ab(*layer_fns, loud=-14.0):
    def f(v, n):
        st = DET[v]
        layers = []
        for fn in layer_fns:
            r = fn(v, n, st)
            layers.extend(r if isinstance(r, list) else [r])
        return D.mix(*layers)
    return f, loud


def P(pool, db=0.0, t=0.0, st=0.0, ln=0.5, idx=0, peak=False):
    return lambda v, n, s: L(pool, v, n, st + s, ln, db, t, idx, peak)


def F(fn, db=0.0, t=0.0):
    return lambda v, n, s: at(D.gain(fn(v, s), db), t)


hero_sting = F(lambda v, s: K.chime(784 * D.semis(s), (0, 7, 12), 0.06, 0.6), -8, 0.0)
champ_sting = F(lambda v, s: K.shimmer(1300 * D.semis(s), 0.7, v + 9), -6, 0.0)

ABILITY = {
    # champions
    "archer_queen": ab(champ_sting, F(lambda v, s: K.whoosh(0.6, 3000, 600, v), -2, 0.0),
                       P(K.MAGIC, -4, 0.0, -3, 0.7)),
    "golden_knight": ab(champ_sting, P(K.SHING, 0, 0.0, 2, 0.4),
                        P(K.SWISH_MED, -2, 0.12, 3, None, 1), P(K.SWISH_MED, -2, 0.24, 4, None, 2),
                        P(K.V_MALE_YELL, -4, 0.0, 1, 0.5)),
    "skeleton_king": ab(champ_sting, P(K.V_ZOMBIE, -2, 0.0, -7, 0.7),
                        P(K.BONE, 0, 0.1, 0, 0.15), P(K.BONE, -2, 0.18, 2, 0.15, 2),
                        P(K.BONE, -3, 0.26, -2, 0.15, 4), F(lambda v, s: K.thump(45, 0.5, 0.5, v), -2)),
    "mighty_miner": ab(champ_sting, F(lambda v, s: K.fizz(0.35, v, 5000), -10),
                       P(K.BANGS, 0, 0.25, 0, 0.6), P(K.MINING, -4, 0.0, 0, 0.3)),
    "monk": ab(champ_sting, P([(K.SFX100, "gong_01.ogg"), (K.SFX100, "gong_02.ogg"),
                               (K.SFX100, "bell_01.ogg")], 0, 0.0, 0, 1.0),
               F(lambda v, s: K.shimmer(900 * D.semis(s), 0.9, v), -6, 0.05)),
    "little_prince": ab(champ_sting, P(K.V_BATTLECRY, -2, 0.0, 4, 0.8),
                        P(K.FOOTSTEP, -6, 0.1, -4, 0.2), P(K.FOOTSTEP, -6, 0.22, -4, 0.2, 2)),
    "goblinstein": ab(champ_sting, F(lambda v, s: K.zap(0.6, v, 2600), 0),
                      P(K.V_OGRE, -4, 0.0, -2, 0.6), P(K.LOWBOOM, -6, 0.0, 0, 0.6, peak=True)),
    "boss_bandit": ab(champ_sting, F(lambda v, s: K.whoosh(0.4, 500, 3500, v), 0),
                      P(K.SMALLSHOT, -6, 0.0, 6, 0.2), P(K.V_FEMALE, -4, 0.05, -3, 0.4)),
    # heroes
    "knight": ab(hero_sting, P(K.V_BATTLECRY, 0, 0.0, 0, 0.8), P(K.SHIELD_HIT, -4, 0.1, 0, 0.3)),
    "giant": ab(hero_sting, P(K.V_GIANT, 0, 0.0, -1, 0.7), P(K.SWISH_HEAVY, -2, 0.1, -3, None)),
    "mini_pekka": ab(hero_sting, P(K.PLATE_MED, 0, 0.0, 0, 0.35), P(K.CLICKS, -6, 0.1, 0, 0.2),
                     F(lambda v, s: K.chime(1046, (0, 4, 7, 12), 0.05, 0.5), -6, 0.15)),
    "musketeer": ab(hero_sting, P(K.XBOW_MECH, 0, 0.0, -3, 0.3), P(K.PLATE_MED, -4, 0.15, 2, 0.3),
                    P(K.CLICKS, -6, 0.3, 0, 0.2)),
    "ice_golem": ab(hero_sting, P(K.ICY, 0, 0.0, -2, 0.8),
                    F(lambda v, s: K.whoosh(0.9, 800, 5000, v), -4)),
    "goblins": ab(hero_sting, P(K.V_GOBLIN_LAUGH, 0, 0.0, 0, 0.7), P(K.CLOTH, -4, 0.1, 0, 0.3)),
    "goblin_banner": ab(hero_sting, P(K.V_GOBLIN_LAUGH, 0, 0.0, 0, 0.7)),
    "valkyrie": ab(hero_sting, P(K.SWISH_HEAVY, 0, 0.0, 0, None),
                   P(K.SWISH_HEAVY, -2, 0.15, 1, None, 1), P(K.SWISH_HEAVY, -4, 0.3, 2, None, 2),
                   P(K.V_FEMALE, -4, 0.0, -2, 0.5)),
    "wizard": ab(hero_sting, P(K.FIREBALL, 0, 0.0, -2, 0.7, peak=True),
                 F(lambda v, s: K.whoosh(0.6, 300, 2000, v), -4)),
    "mega_minion": ab(hero_sting, P([(K.SCI, "teleport_01.ogg"), (K.SCI, "teleport_02.ogg")], 0,
                                    0.0, 0, 0.5, peak=True), P(K.FLAP, -6, 0.1, 0, 0.4, peak=True)),
    "barbarian": ab(hero_sting, P(K.V_BATTLECRY, 0, 0.0, 1, 0.7), P(K.WOOD, -4, 0.1, 0, 0.3)),
    "magic_archer": ab(hero_sting, P(K.MAGIC, 0, 0.0, 2, 0.6),
                       F(lambda v, s: K.whoosh(0.4, 900, 4000, v), -4)),
    "balloon": ab(hero_sting, F(lambda v, s: K.whoosh(0.5, 300, 1500, v), 0),
                  P(K.BONE, -2, 0.2, 0, 0.15), P(K.BONE, -4, 0.3, 2, 0.15, 2)),
    "bowler": ab(hero_sting, P(K.STONE, 0, 0.0, -3, 0.4), P(K.STONE, -2, 0.15, -1, 0.4, 1),
                 P(K.STONE, -4, 0.3, -2, 0.4, 2), P(K.V_OGRE, -4, 0.0, 0, 0.6)),
    "dark_prince": ab(hero_sting, P(K.PLATE, 0, 0.0, 0, 0.35), P(K.FOOTSTEP, -4, 0.1, -4, 0.2),
                      P(K.V_MALE_GRUNT, -4, 0.0, -3, 0.5)),
    "tombstone": ab(hero_sting, P(K.MAGIC, -2, 0.0, -5, 0.8), P(K.V_WITCH, -6, 0.2, -3, 0.7),
                    P(K.STONE, -4, 0.0, -3, 0.4)),
    "berserker": ab(hero_sting, P(K.V_FEMALE, 0, 0.0, -2, 0.5),
                    F(lambda v, s: K.thump(60, 0.25, 0.5, v), -4, 0.1),
                    F(lambda v, s: K.thump(60, 0.25, 0.5, v + 1), -6, 0.4)),
    "ice_wizard": ab(hero_sting, P(K.ICY, 0, 0.0, 0, 0.7), P(K.GLASS, -4, 0.1, 2, 0.3)),
    "electro_wizard": ab(hero_sting, F(lambda v, s: K.zap(0.5, v, 3200), 0),
                         F(lambda v, s: K.zap(0.3, v + 5, 3600), -3, 0.2)),
    # evolutions / others
    "tesla": ab(F(lambda v, s: K.zap(0.6, v + 2, 2400), 0),
                P(K.LOWBOOM, -4, 0.0, 0, 0.6, peak=True)),
    "electro_giant": ab(F(lambda v, s: K.zap(0.5, v + 7, 2000), 0),
                        P([(K.ELEC, "powerdown.wav")], -4, 0.0, 0, 0.8)),
    "royal_chef": ab(P(K.METAL_LIGHT, 0, 0.0, 0, 0.3),
                     F(lambda v, s: K.fizz(0.5, v, 3500), -10, 0.05),
                     F(lambda v, s: K.chime(1175, (0, 4, 7), 0.05, 0.4), -6, 0.1)),
}
for k, (fn, loud) in ABILITY.items():
    S(k + "_ability", fn, loud=loud)

# ======================================================================
#  SPAWNERS (a building or unit bringing out its units)
# ======================================================================
SPAWN = {
    "tombstone": ab(P(K.STONE, 0, 0.0, -4, 0.35), P(K.BONE, -2, 0.08, 0, 0.15),
                    P(K.BONE, -4, 0.14, 2, 0.15, 2), loud=-19),
    "goblin_hut": ab(P(K.DOOR, -4, 0.0, 2, 0.3), P(K.V_GOBLIN, 0, 0.1, 1, 0.4), loud=-19),
    "barbarian_hut": ab(P(K.DOOR, -2, 0.0, -2, 0.4), P(K.V_BATTLECRY, 0, 0.15, -1, 0.7), loud=-16),
    "furnace": ab(P(K.FIREBALL, 0, 0.0, 2, 0.5, peak=True),
                  F(lambda v, s: K.crackle_fire(0.4, v), -6), loud=-18),
    "witch": ab(P(K.MAGIC, 0, 0.0, -2, 0.5), P(K.BONE, -4, 0.15, 0, 0.15),
                P(K.BONE, -6, 0.22, 2, 0.15, 2), loud=-18),
    "night_witch": ab(P(K.MAGIC, -2, 0.0, -5, 0.5), P(K.FLAP, -2, 0.1, 6, 0.4, peak=True), loud=-18),
    "goblin_drill": ab(P(K.MINING, 0, 0.0, 2, 0.3), P(K.STONE, -4, 0.05, 2, 0.3),
                       P(K.V_GOBLIN, -2, 0.15, 2, 0.4), loud=-18),
}
for k, (fn, loud) in SPAWN.items():
    S(k + "_spawn", fn, loud=loud)
