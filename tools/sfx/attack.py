"""
============================================================================
  ATTACK.PY  --  Recipes for every unit's attack sounds (3 variants each)
============================================================================

ATTACK[key](v) -> signal for variant v (0, 1, 2) of `key`'s attack, played
when the unit swings / shoots.  HIT[key](v) -> the explosion / burst when a
SPLASH projectile of `key` lands (bombs, fireballs, mortar shells...).

Variants use different real takes from the CC0 packs, plus small changes
of pitch, timing and layer balance, so a unit never sounds like a loop.
Each unit gets its own pitch / weight / layer mix, so two units of the same
"family" (Knight vs Barbarian) are still recognisable.

Recipes return dry signals; render.py adds the shared room, loudness
matching (LOUD table) and the final clean-up.
============================================================================
"""

import zlib

import numpy as np

import dsp as D
import kit as K
from kit import at, pitch, head, pick, tk  # noqa: F401

DET = (0.0, -0.55, 0.6)          # per-variant detune (semitones)
ATTACK = {}
HIT = {}
LOUD = {}                        # per-unit loudness target (dB), default -15
ROOM = {}                        # per-unit reverb wet level (dB), default -21


def _off(key):
    """Per-unit offset into the take pools (so units differ)."""
    return zlib.crc32(key.encode()) % 7


def reg(table, keys, fn, loud=None, room=None):
    for k in keys.split():
        table[k] = (lambda v, k=k: fn(v, k))
        if loud is not None:
            LOUD[k] = loud
        if room is not None:
            ROOM[k] = room


def _p(key, v, base=0.0):
    return base + DET[v % 3]


def tp(pool, v, key, st=0.0, ln=None, idx=0):
    """Pick take (v + unit offset + idx) from pool, pitch it, cut it."""
    x = tk(pick(pool, v + _off(key) + idx))
    x = pitch(x, st)
    return head(x, ln) if ln else x


# ======================================================================
#  MELEE: blades
# ======================================================================
def sword(p=0.0, swish=K.SWISH_MED, clash=K.CLASH, clash_db=0.0, swish_db=-7.0,
          ring=0.32, body=0.0, body_f=110.0, extra=None, extra_db=-10.0, t_hit=0.035,
          lp=None):
    """Swing + steel impact (+ optional body thump and an extra layer)."""
    def f(v, key):
        st = _p(key, v, p)
        layers = [at(D.gain(tp(swish, v, key, st), swish_db), 0.0),
                  at(D.gain(tp(clash, v, key, st, ring), clash_db), t_hit)]
        if body:
            layers.append(at(D.gain(K.thump(body_f * D.semis(st), 0.16, 0.55, v), body), t_hit))
        if extra:
            layers.append(at(D.gain(tp(extra, v, key, st, 0.25, 1), extra_db), t_hit))
        y = D.mix(*layers)
        return D.lp(y, lp) if lp else y
    return f


reg(ATTACK, "knight", sword(0.0, clash=K.CLASH, body=-8, extra=K.CHAIN, extra_db=-16))
reg(ATTACK, "barbarians barbarian", sword(-2.0, swish=K.SWISH_HEAVY, clash=K.BLADE_ON_BLADE,
                                          body=-6, body_f=95, ring=0.28))
reg(ATTACK, "elite_barbarians", sword(1.0, swish=K.SWISH_MED, clash=K.CLASH, ring=0.24,
                                      body=-8, extra=K.BLADE_ON_BLADE, extra_db=-6))
reg(ATTACK, "guards", sword(2.0, swish=K.SWISH_LIGHT, clash=K.CLASH_BRIGHT, ring=0.2,
                            extra=K.BONE, extra_db=-8), loud=-17)
reg(ATTACK, "souldier skeletrooper", sword(1.0, swish=K.SWISH_LIGHT, clash=K.BLADE_ON_BLADE,
                                           ring=0.22, extra=K.BONE, extra_db=-6), loud=-17)
reg(ATTACK, "skeleton_general", sword(-1.0, clash=K.CLASH, ring=0.3, extra=K.BONE,
                                      extra_db=-6, body=-9))
reg(ATTACK, "golden_knight", sword(1.5, swish=K.SHING, swish_db=-9, clash=K.CLASH_BRIGHT,
                                   ring=0.4, body=-10, extra=K.CHAIN, extra_db=-16))
reg(ATTACK, "royal_guardian", sword(-3.0, swish=K.SWISH_HEAVY, clash=K.CLASH, ring=0.4,
                                    body=-4, body_f=85, extra=K.SHIELD_HIT, extra_db=-8),
    loud=-14)
reg(ATTACK, "prince", sword(-1.0, swish=K.SWISH_HEAVY, clash=K.CLASH, ring=0.35, body=-4,
                            body_f=90, extra=K.PLATE_MED, extra_db=-7), loud=-14)
reg(ATTACK, "ronin spirit_empress", sword(2.0, swish=K.SHING, swish_db=-6,
                                          clash=K.CLASH_BRIGHT, clash_db=-3, ring=0.3,
                                          t_hit=0.06))
reg(ATTACK, "royal_ghost", sword(-1.5, swish=K.SWISH_HEAVY, clash=K.CLASH_LONG, ring=0.45,
                                 swish_db=-4), room=-12)
reg(ATTACK, "lumberjack_ghost", sword(-1.0, swish=K.SWISH_MED, clash=K.CHOP, ring=0.25,
                                      extra=K.BLADE_ON_HAFT, extra_db=-6), room=-12)


def heavy_blade(p=0.0, clash=K.CLASH, plate=K.PLATE, boom=-3.0, ring=0.5, shing=True):
    """P.E.K.K.A-class: big swing, low steel crash, armour plate, boom."""
    def f(v, key):
        st = _p(key, v, p)
        sw = tp(K.SHING if shing else K.SWISH_HEAVY, v, key, st - 3)
        layers = [at(D.gain(D.lp(sw, 7000), -8), 0.0),
                  at(D.gain(tp(clash, v, key, st - 4, ring), -2), 0.05),
                  at(D.gain(tp(plate, v, key, st), -4), 0.05),
                  at(D.gain(K.thump(80 * D.semis(st), 0.28, 0.45, v), boom), 0.05)]
        return D.mix(*layers)
    return f


reg(ATTACK, "pekka", heavy_blade(-1.0, boom=-3, ring=0.6), loud=-13)
reg(ATTACK, "mini_pekka", heavy_blade(1.5, boom=-3, ring=0.45, shing=True), loud=-13)
reg(ATTACK, "mega_knight", heavy_blade(-1.0, clash=K.CLASH, boom=-1, ring=0.4,
                                       shing=False), loud=-13)
reg(ATTACK, "boss_bandit", heavy_blade(2.0, clash=K.BLADE_ON_BLADE, plate=K.PUNCH_MED,
                                       boom=-8, ring=0.3, shing=False), loud=-14)


def mace(p=0.0, swish=K.SWISH_HEAVY, hit=K.MACE, body=-4.0, extra=None, extra_db=-6.0):
    def f(v, key):
        st = _p(key, v, p)
        layers = [at(D.gain(tp(swish, v, key, st), -6), 0.0),
                  at(D.gain(tp(hit, v, key, st, 0.35), 0), 0.04),
                  at(D.gain(K.thump(95 * D.semis(st), 0.2, 0.5, v), body), 0.04)]
        if extra:
            layers.append(at(D.gain(tp(extra, v, key, st, 0.3, 2), extra_db), 0.04))
        return D.mix(*layers)
    return f


reg(ATTACK, "dark_prince", mace(-1.0, extra=K.PLATE_MED, extra_db=-6), loud=-14)
reg(ATTACK, "skeleton_king", mace(-4.0, extra=K.BONE, extra_db=-2, body=-1), loud=-13)
reg(ATTACK, "tomb_queen", mace(-2.0, hit=K.MACE, extra=K.BONE, extra_db=-4, body=-3), loud=-14)


def light_blade(p=0.0, swish=K.SWISH_LIGHT, hit=K.KNIFE, hit_len=0.18, extra=None,
                extra_db=-8.0, hit_db=-2.0):
    """Daggers, small knives, spears."""
    def f(v, key):
        st = _p(key, v, p)
        layers = [at(D.gain(tp(swish, v, key, st), -5), 0.0),
                  at(D.gain(tp(hit, v, key, st, hit_len), hit_db), 0.03)]
        if extra:
            layers.append(at(D.gain(tp(extra, v, key, st, 0.15, 2), extra_db), 0.03))
        return D.mix(*layers)
    return f


reg(ATTACK, "goblins goblin goblin_gang decoy_goblin",
    light_blade(3.0, hit=K.KNIFE, hit_len=0.14), loud=-18)
reg(ATTACK, "bush_goblin", light_blade(2.0, hit=K.SLICE, hit_len=0.2,
                                       extra=K.CLOTH, extra_db=-10), loud=-17)
reg(ATTACK, "skeletons skeleton skeleton_army",
    light_blade(4.0, hit=K.CLASH_BRIGHT, hit_len=0.1, hit_db=-6, extra=K.BONE, extra_db=-2),
    loud=-19)
reg(ATTACK, "bandit", light_blade(1.0, swish=K.SWISH_MED, hit=K.SLICE, hit_len=0.22,
                                  extra=K.KNIFE, extra_db=-6), loud=-16)
reg(ATTACK, "royal_recruits", light_blade(0.0, swish=K.SWISH_MED, hit=K.HAFT, hit_len=0.2,
                                          extra=K.SHIELD_HIT, extra_db=-9), loud=-16)
reg(ATTACK, "berserker", light_blade(1.0, swish=K.SWISH_MED, hit=K.CHOP, hit_len=0.2,
                                     extra=K.BLADE_ON_HAFT, extra_db=-6), loud=-17)
reg(ATTACK, "night_witch", light_blade(-2.0, swish=K.SWISH_HEAVY, hit=K.SLICE, hit_len=0.28,
                                       extra=K.CLASH_LONG, extra_db=-12), room=-14)


def axe(p=0.0, swish=K.SWISH_HEAVY, body=-6.0, spin=False):
    def f(v, key):
        st = _p(key, v, p)
        layers = [at(D.gain(tp(swish, v, key, st), -4), 0.0),
                  at(D.gain(tp(K.BLADE_ON_HAFT, v, key, st, 0.3), -2), 0.045),
                  at(D.gain(tp(K.CHOP, v, key, st, 0.22), -3), 0.045),
                  at(D.gain(K.thump(100 * D.semis(st), 0.15, 0.55, v), body), 0.045)]
        if spin:
            layers.append(at(D.gain(K.whoosh(0.32, 300, 1600, v + 5), -9), 0.0))
        return D.mix(*layers)
    return f


reg(ATTACK, "valkyrie", axe(-1.0, spin=True), loud=-14)
reg(ATTACK, "lumberjack", axe(1.5, swish=K.SWISH_MED, body=-10), loud=-16)

# ======================================================================
#  MELEE: fists, clubs, bodies, rams
# ======================================================================


def smash(p=0.0, hit=K.PUNCH_HEAVY, swish=K.SWISH_HEAVY, swish_db=-8.0, body=-5.0,
          body_f=70.0, extra=None, extra_db=-6.0, extra_st=0.0, ln=0.45, smack=-7.0):
    def f(v, key):
        st = _p(key, v, p)
        layers = [at(D.gain(tp(swish, v, key, st), swish_db), 0.0),
                  at(D.gain(D.hp(tp(K.FIST, v, key, st, 0.25, 2), 300), smack), 0.04),
                  at(D.gain(D.decay_env(tp(hit, v, key, st, ln), 0.14), 0), 0.04),
                  at(D.gain(K.thump(body_f * D.semis(st), 0.22, 0.45, v), body), 0.04)]
        if extra:
            layers.append(at(D.gain(tp(extra, v, key, st + extra_st, 0.4, 1), extra_db), 0.04))
        return D.mix(*layers)
    return f


reg(ATTACK, "giant", smash(-1.0, extra=K.BODY, extra_db=-6, body=-7, ln=0.35), loud=-13)
reg(ATTACK, "goblin_giant", smash(1.0, hit=K.PUNCH_HEAVY, extra=K.FIST, extra_db=-6, body=-5),
    loud=-14)
reg(ATTACK, "giant_skeleton", smash(-2.0, extra=K.BONE, extra_db=0, extra_st=-3), loud=-13)
reg(ATTACK, "golem golemite", smash(-3.0, hit=K.PUNCH_HEAVY, extra=K.STONE, extra_db=-3,
                                   body=0, body_f=60), loud=-13)
reg(ATTACK, "ice_golem", smash(2.0, hit=K.PUNCH_MED, extra=K.GLASS, extra_db=-5, body=-6),
    loud=-16)
reg(ATTACK, "elixir_golem", smash(-1.0, hit=K.PUNCH_HEAVY, extra=K.SPLATS, extra_db=-4),
    loud=-14)
reg(ATTACK, "elixir_golemite elixir_blob", smash(3.0, hit=K.PUNCH_MED, extra=K.SPLATS,
                                                 extra_db=-2, body=-8, swish=K.SWISH_LIGHT),
    loud=-17)
reg(ATTACK, "electro_giant", smash(-1.0, extra=K.ZAPS, extra_db=-6), loud=-13)
reg(ATTACK, "goblin_monster", smash(-2.0, hit=K.PUNCH_HEAVY, extra=K.BODY, extra_db=-4,
                                    body=-1), loud=-13)
reg(ATTACK, "monk", smash(2.0, hit=K.FIST, swish=K.SWISH_MED, body=-9, ln=0.3), loud=-15)
reg(ATTACK, "rascal_boy goblin_brawler", smash(1.0, hit=K.FIST, swish=K.SWISH_MED, body=-7,
                                               extra=K.PUNCH_MED, extra_db=-6, ln=0.3),
    loud=-15)
reg(ATTACK, "fisherman", smash(0.0, hit=K.SPLATS, swish=K.SWISH_MED, body=-8,
                               extra=K.PUNCH_MED, extra_db=-4, ln=0.35), loud=-15)
reg(ATTACK, "hog_rider", smash(0.0, hit=K.PUNCH_HEAVY, swish=K.SWISH_HEAVY, body=-4,
                               extra=K.WOOD, extra_db=0, smack=-4), loud=-13)
reg(ATTACK, "royal_hogs cursed_hog", smash(3.0, hit=K.PUNCH_MED, swish=K.SWISH_LIGHT,
                                           body=-8, extra=K.WOOD, extra_db=-8, ln=0.3),
    loud=-17)
reg(ATTACK, "battle_ram ram_rider", smash(-1.0, hit=K.WOOD, swish=K.SWISH_HEAVY, body=-2,
                                          extra=K.PUNCH_HEAVY, extra_db=-4), loud=-13)
reg(ATTACK, "rhino", smash(-2.0, hit=K.BODY, swish=K.SWISH_HEAVY, body=-2,
                           extra=K.PUNCH_HEAVY, extra_db=-5), loud=-14)
reg(ATTACK, "miner", smash(1.0, hit=K.MINING, swish=K.SWISH_MED, body=-10, ln=0.35), loud=-15)
reg(ATTACK, "goblin_machine", smash(-1.0, hit=K.PLATE, swish=K.SWISH_HEAVY, body=-5,
                                    extra=K.METAL_HEAVY, extra_db=-6), loud=-14)
reg(ATTACK, "rune_giant", smash(-2.0, hit=K.HAMMER, swish=K.SWISH_HEAVY, body=-3,
                                extra=K.MAGIC, extra_db=-14), loud=-14)
reg(ATTACK, "battle_healer", smash(1.0, hit=K.PUNCH_MED, swish=K.SWISH_MED, body=-8,
                                   extra=K.METAL_LIGHT, extra_db=-10, ln=0.3), loud=-15)


def mighty_drill(v, key):
    st = DET[v]
    y = D.mix(at(D.gain(K.drill(0.26, 160 * D.semis(st), v), -4), 0.0),
              at(D.gain(tp(K.TOOLS, v, key, st, 0.22), -6), 0.0),
              at(D.gain(tp(K.MINING, v, key, st + 2, 0.2), -6), 0.02))
    return y


reg(ATTACK, "mighty_miner", mighty_drill, loud=-19)


def bite(v, key):
    st = DET[v] + 5
    y = D.mix(at(D.gain(tp(K.SWISH_LIGHT, v, key, st), -8), 0.0),
              at(tk(pick([(K.RPG, "bite-small.wav"), (K.RPG, "bite-small2.wav"),
                          (K.RPG, "bite-small3.wav")], v)), 0.02))
    return D.hp(y, 250)


reg(ATTACK, "bats bat", bite, loud=-20)


def phoenix_claw(v, key):
    st = DET[v]
    return D.mix(at(D.gain(tp(K.SWISH_MED, v, key, st + 2), -4), 0.0),
                 at(D.gain(tp(K.FIRE_SPELL, v, key, st + 3, 0.35), -2), 0.0),
                 at(D.gain(K.crackle_fire(0.3, v), -8), 0.02),
                 at(D.gain(tp(K.SLICE, v, key, st, 0.15), -8), 0.04))


reg(ATTACK, "phoenix phoenix_reborn", phoenix_claw, loud=-15)

# ======================================================================
#  RANGED: bows, guns, cannons, thrown things
# ======================================================================


def bow(p=0.0, pool=K.BOW, fly_db=-14.0, extra=None, extra_db=-10.0, lp=None, ln=0.3):
    def f(v, key):
        st = _p(key, v, p)
        layers = [at(tp(pool, v, key, st, ln), 0.0),
                  at(D.gain(tp(K.ARROW_FLY, v, key, st + 2, 0.22), fly_db), 0.03)]
        if extra is not None:
            layers.append(at(D.gain(extra(v, key, st), extra_db), 0.0))
        y = D.mix(*layers)
        return D.lp(y, lp) if lp else y
    return f


reg(ATTACK, "archers", bow(1.0, ln=0.22, lp=9000), loud=-19)
reg(ATTACK, "princess_tower tower_princess", bow(0.0, ln=0.25), loud=-17)
reg(ATTACK, "princess", bow(-1.0, extra=lambda v, k, st: K.crackle_fire(0.35, v),
                            extra_db=-8), loud=-16)
reg(ATTACK, "magic_archer", bow(1.0, extra=lambda v, k, st: K.shimmer(1800 * D.semis(st), 0.4, v),
                                extra_db=-12), loud=-16)
reg(ATTACK, "little_prince", bow(2.0, pool=K.XBOW, ln=0.2,
                                 extra=lambda v, k, st: tp(K.CLICKS, v, k, st + 3, 0.1),
                                 extra_db=-14), loud=-18)
reg(ATTACK, "archer_queen", bow(-1.0, pool=K.XBOW, ln=0.3,
                                extra=lambda v, k, st: tp(K.XBOW_MECH, v, k, st, 0.12),
                                extra_db=-10), loud=-15)


def xbow(v, key):
    """X-Bow fires 3+ bolts a second: short, tight, mechanical."""
    st = DET[v] * 0.5 - 1
    y = D.mix(at(tp(K.XBOW, v, key, st, 0.12), 0.0),
              at(D.gain(tp(K.CLICKS, v, key, st, 0.08), -12), 0.0))
    return D.hp(y, 160)


reg(ATTACK, "xbow", xbow, loud=-20)


def dart(v, key):
    st = DET[v] + 1
    return D.mix(at(D.gain(K.puff(0.07, 2600 * D.semis(st), v), -2), 0.0),
                 at(D.gain(tp(K.ARROW_FLY, v, key, st + 4, 0.15), -6), 0.015))


reg(ATTACK, "dart_goblin", dart, loud=-18)


def thrown_blade(p=0.0, hit=K.KNIFE):
    def f(v, key):
        st = _p(key, v, p)
        return D.mix(at(D.gain(tp(K.SWISH_LIGHT, v, key, st + 2), -2), 0.0),
                     at(D.gain(tp(hit, v, key, st + 3, 0.12), -8), 0.0))
    return f


reg(ATTACK, "dagger_duchess", thrown_blade(1.0), loud=-18)
reg(ATTACK, "royal_chef", thrown_blade(-1.0, hit=K.METAL_LIGHT), loud=-18)
reg(ATTACK, "spear_goblins spear_goblin", thrown_blade(2.0, hit=K.HAFT), loud=-18)
reg(ATTACK, "ram_rider_bola", thrown_blade(-1.0, hit=K.CHAIN), loud=-17)


def sling(v, key):
    st = DET[v]
    twang = D.karplus(330 * D.semis(st), 0.18, 0.3, v)
    return D.mix(at(D.gain(tp(K.SWISH_MED, v, key, st + 2), -3), 0.0),
                 at(D.gain(D.decay_env(twang, 0.05), -10), 0.01),
                 at(D.gain(tp(K.CLOTH, v, key, st, 0.12), -12), 0.0))


reg(ATTACK, "rascal_girl", sling, loud=-17)


def gun(pool, p=0.0, ln=0.45, lp=None, body=-99.0, mech=None, mech_db=-14.0, hp=None):
    def f(v, key):
        st = _p(key, v, p)
        layers = [at(tp(pool, v, key, st, ln), 0.0)]
        if body > -60:
            layers.append(at(D.gain(K.thump(90 * D.semis(st), 0.15, 0.5, v), body), 0.0))
        if mech:
            layers.append(at(D.gain(tp(mech, v, key, st, 0.12), mech_db), 0.12))
        y = D.mix(*layers)
        if lp:
            y = D.lp(y, lp)
        if hp:
            y = D.hp(y, hp)
        return y
    return f


reg(ATTACK, "musketeer", gun(K.MUSKET, 0.0, ln=0.5, body=-12), loud=-15)
reg(ATTACK, "three_musketeers", gun(K.MUSKET, 1.0, ln=0.4, body=-14), loud=-16)
reg(ATTACK, "hunter", gun(K.SHOTGUN, -1.0, ln=0.55, body=-8, mech=K.CLICKS, mech_db=-16),
    loud=-14)
reg(ATTACK, "flying_machine", gun(K.SMALLSHOT, 3.0, ln=0.3, hp=200), loud=-17)
reg(ATTACK, "hero_turret", gun(K.PISTOL, 0.0, ln=0.3), loud=-18)


def cannon(p=0.0, ln=0.6, boom=-4.0, pool=K.CANNON):
    def f(v, key):
        st = _p(key, v, p)
        return D.mix(at(tp(pool, v, key, st, ln), 0.0),
                     at(D.gain(K.thump(65 * D.semis(st), 0.3, 0.5, v), boom), 0.0))
    return f


reg(ATTACK, "cannon", cannon(0.0), loud=-15)
reg(ATTACK, "cannon_cart", cannon(1.5, ln=0.5, boom=-8), loud=-16)
reg(ATTACK, "royal_giant", cannon(-1.0, boom=-2), loud=-14)
reg(ATTACK, "king_tower", cannon(-2.0, ln=0.55, boom=-4), loud=-15)
reg(ATTACK, "cannoneer", cannon(-0.5, ln=0.55, boom=-6), loud=-15)


def mortar_fire(v, key):
    """A hollow 'thoonk' as the shell leaves the tube."""
    st = DET[v] - 6
    y = D.mix(at(D.lp(tp(K.CANNON, v, key, st, 0.5), 2500 + 600 * v), 0.0),
              at(D.gain(K.thump(55, 0.35, 0.6, v), -5), 0.0),
              at(D.gain(tp(K.WOOD, v, key, st + 4, 0.2), -9), 0.0),
              at(D.gain(K.whoosh(0.5, 300, 1200, v), -12), 0.05))
    return y


reg(ATTACK, "mortar", mortar_fire, loud=-15)


def lob(p=0.0, fuse=True, swish=K.SWISH_MED):
    """Throwing a bomb: a swing and a fizzing fuse."""
    def f(v, key):
        st = _p(key, v, p)
        layers = [at(D.gain(tp(swish, v, key, st), -2), 0.0)]
        if fuse:
            layers.append(at(D.gain(K.fizz(0.3, v), -22), 0.02))
        return D.mix(*layers)
    return f


reg(ATTACK, "bomber", lob(2.0), loud=-19)
reg(ATTACK, "goblin_demolisher", lob(0.0, swish=K.SWISH_HEAVY), loud=-18)


def bomb_tower_fire(v, key):
    st = DET[v]
    return D.mix(at(D.gain(K.thump(90 * D.semis(st), 0.12, 0.6, v), -2), 0.0),
                 at(D.gain(tp(K.WOOD, v, key, st + 3, 0.15), -6), 0.0),
                 at(D.gain(K.fizz(0.25, v), -22), 0.02))


reg(ATTACK, "bomb_tower", bomb_tower_fire, loud=-19)


def bowler(v, key):
    st = DET[v] - 3
    return D.mix(at(D.gain(tp(K.SWISH_HEAVY, v, key, st), -3), 0.0),
                 at(D.gain(tp(K.STONE, v, key, st, 0.4), -2), 0.05),
                 at(D.gain(K.thump(60, 0.3, 0.6, v), -3), 0.05),
                 at(D.gain(D.lp(K.noise_roll(0.5, v), 900), -10), 0.08))


reg(ATTACK, "bowler", bowler, loud=-14)


def executioner(v, key):
    st = DET[v] - 1
    return D.mix(at(D.gain(tp(K.SWISH_HEAVY, v, key, st), -2), 0.0),
                 at(D.gain(K.whoosh(0.55, 250, 1400, v), -6), 0.05),
                 at(D.gain(tp(K.BLADE_ON_HAFT, v, key, st, 0.2), -10), 0.0))


reg(ATTACK, "executioner", executioner, loud=-15)


def firework_launch(v, key):
    st = DET[v]
    return D.mix(at(D.gain(K.whoosh(0.3, 700, 3500, v), -2), 0.0),
                 at(D.gain(K.fizz(0.3, v + 2, 4000), -14), 0.0),
                 at(D.gain(tp(K.SMALLSHOT, v, key, st + 5, 0.12), -8), 0.0))


reg(ATTACK, "firecracker", firework_launch, loud=-18)


def rocket(v, key):
    st = DET[v]
    return D.mix(at(D.gain(head(K.from_peak(tp([(K.SCI, "rocket_01.ogg")], v, key, st + 4), 0.06),
                                0.6), 0), 0.0),
                 at(D.gain(K.whoosh(0.5, 400, 2500, v), -4), 0.0),
                 at(D.gain(K.fizz(0.4, v, 3000), -16), 0.0))


reg(ATTACK, "goblin_machine_rocket", rocket, loud=-15)

# ======================================================================
#  MAGIC & ELEMENTS
# ======================================================================


def fire_breath(p=0.0, ln=0.45, spit=False):
    def f(v, key):
        st = _p(key, v, p)
        ball = head(K.from_peak(tp(K.FIREBALL, v, key, st), 0.04), ln)
        layers = [at(ball, 0.0),
                  at(D.gain(K.crackle_fire(ln, v), -9), 0.02)]
        if spit:
            layers.append(at(D.gain(K.whoosh(0.25, 300, 1800, v), -6), 0.0))
        return D.decay_env(D.mix(*layers), ln * 0.6)
    return f


reg(ATTACK, "wizard", fire_breath(1.0, 0.4, spit=True), loud=-16)
reg(ATTACK, "furnace", fire_breath(-1.0, 0.4), loud=-17)
reg(ATTACK, "baby_dragon", fire_breath(2.0, 0.4), loud=-16)
reg(ATTACK, "skeleton_dragons", fire_breath(4.0, 0.3), loud=-18)
reg(ATTACK, "lava_hound", fire_breath(-3.0, 0.35), loud=-18)
reg(ATTACK, "lava_pup", fire_breath(5.0, 0.22), loud=-21)


def beam(p=0.0):
    """Inferno beam tick: short sizzle + buzz (it fires ~2.5x a second)."""
    def f(v, key):
        st = _p(key, v, p)
        hum = D.bp(D.osc(110 * D.semis(st), 0.22, 116 * D.semis(st), "saw"), 200, 2500)
        roar = D.lp(D.noise(0.24, "pink", v), 1600)
        roar = D.decay_env(D.adsr(roar, 0.012, 0.05, 0.8, 0.06), 0.1)
        return D.mix(at(roar, 0.0),
                     at(D.gain(D.adsr(hum, 0.01, 0.05, 0.7, 0.08), -9), 0.0),
                     at(D.gain(K.fizz(0.2, v, 5000), -18), 0.0))
    return f


reg(ATTACK, "inferno_tower", beam(-2.0), loud=-22)
reg(ATTACK, "inferno_dragon", beam(1.0), loud=-22)


def electric(p=0.0, t=0.22, rec=True, boom=-99.0, f=3200.0):
    def fn(v, key):
        st = _p(key, v, p)
        layers = [at(K.zap(t, v + _off(key), f * D.semis(st)), 0.0)]
        if rec:
            layers.append(at(D.gain(tp(K.ZAPS, v, key, st, t + 0.05), -3), 0.0))
        if boom > -60:
            layers.append(at(D.gain(K.thump(70, 0.25, 0.5, v), boom), 0.0))
        return D.mix(*layers)
    return fn


reg(ATTACK, "electro_wizard", electric(0.0, 0.24), loud=-16)
reg(ATTACK, "zappies", electric(2.0, 0.18), loud=-19)
reg(ATTACK, "electro_dragon", electric(-2.0, 0.3, boom=-10), loud=-16)
reg(ATTACK, "electro_spirit", electric(3.0, 0.25), loud=-17)
reg(ATTACK, "tesla", electric(-1.0, 0.26, boom=-12), loud=-18)
reg(ATTACK, "goblinstein", electric(-3.0, 0.3, boom=-8), loud=-16)


def sparky(v, key):
    st = DET[v]
    return D.mix(at(K.zap(0.5, v, 2500), 0.0),
                 at(D.gain(tp(K.LASER, v, key, st - 4, 0.6), -4), 0.0),
                 at(D.gain(head(K.from_peak(tp(K.LOWBOOM, v, key, st), 0.02), 0.7), -2), 0.0))


reg(ATTACK, "sparky", sparky, loud=-12)


def magic(p=0.0, pool=K.MAGIC, ln=0.45, whoosh=True):
    def f(v, key):
        st = _p(key, v, p)
        layers = [at(D.gain(tp(pool, v, key, st, ln), 0), 0.0)]
        if whoosh:
            layers.append(at(D.gain(K.whoosh(0.3, 600, 2600, v), -8), 0.0))
        return D.mix(*layers)
    return f


reg(ATTACK, "witch", magic(0.0, K.SPELL, 0.4), loud=-17)
reg(ATTACK, "mother_witch", magic(2.0, K.MAGIC, 0.4), loud=-17)
reg(ATTACK, "spirit_empress_air", magic(3.0, K.MAGIC, 0.4), loud=-17)   # spirit blast (not electric)


def frost(p=0.0, ln=0.35):
    def f(v, key):
        st = _p(key, v, p)
        return D.mix(at(D.gain(tp(K.ICY, v, key, st, ln), 0), 0.0),
                     at(D.gain(tp(K.GLASS, v, key, st + 2, 0.25), -8), 0.03),
                     at(D.gain(K.whoosh(0.25, 1500, 6000, v), -10), 0.0))
    return f


reg(ATTACK, "ice_wizard", frost(0.0), loud=-17)
reg(ATTACK, "ice_spirit", frost(3.0, 0.4), loud=-16)


def spit(p=0.0, toxic=False):
    def f(v, key):
        st = _p(key, v, p)
        layers = [at(D.gain(tp(K.SPIT, v, key, st, 0.25), 0), 0.0),
                  at(D.gain(K.puff(0.08, 1500 * D.semis(st), v), -8), 0.0)]
        if toxic:
            layers.append(at(D.gain(head(K.from_peak(tp(K.SPLATS, v, key, st), 0.02), 0.3), -6),
                             0.02))
        return D.mix(*layers)
    return f


reg(ATTACK, "minions minion_horde", spit(4.0), loud=-19)
reg(ATTACK, "mega_minion", spit(-2.0), loud=-16)
reg(ATTACK, "minion_giant", spit(-4.0, toxic=True), loud=-15)


def explode(p=0.0, pool=K.EXPLO, ln=0.7, boom=-3.0, extra=None, extra_db=-6.0):
    def f(v, key):
        st = _p(key, v, p)
        layers = [at(tp(pool, v, key, st, ln), 0.0),
                  at(D.gain(K.thump(60 * D.semis(st), 0.4, 0.5, v), boom), 0.0)]
        if extra is not None:
            layers.append(at(D.gain(extra(v, key, st), extra_db), 0.0))
        return D.decay_env(D.mix(*layers), ln * 0.5)
    return f


reg(ATTACK, "fire_spirit", explode(3.0, ln=0.5, extra=lambda v, k, st: K.crackle_fire(0.4, v)),
    loud=-14)
reg(ATTACK, "wall_breakers wb_runner", explode(1.0, pool=K.BANGS, ln=0.6), loud=-14)
reg(ATTACK, "demolisher_charge", explode(-1.0, pool=K.BANGS, ln=0.7), loud=-13)
reg(ATTACK, "balloon", explode(-2.0, ln=0.75, boom=-2,
                               extra=lambda v, k, st: head(K.from_peak(tp(K.LOWBOOM, v, k, st),
                                                                       0.02), 0.7)),
    loud=-12)


def heal_burst(v, key):
    st = DET[v]
    return D.mix(at(D.gain(K.chime(1046 * D.semis(st), (0, 4, 7, 12), 0.04, 0.5), 0), 0.0),
                 at(D.gain(K.shimmer(2000 * D.semis(st), 0.5, v), -8), 0.03),
                 at(D.gain(K.whoosh(0.35, 800, 3500, v), -8), 0.0))


reg(ATTACK, "heal_spirit", heal_burst, loud=-15)


def rustle(v, key):
    st = DET[v]
    return D.mix(at(D.gain(tp(K.CLOTH, v, key, st + 2, 0.3), 0), 0.0),
                 at(D.gain(D.bp(D.noise(0.3, "pink", v), 1500, 6000), -10), 0.0))


reg(ATTACK, "suspicious_bush", rustle, loud=-18)

# ======================================================================
#  SPLASH PROJECTILE IMPACTS  (HIT)
# ======================================================================


def boom(p=0.0, pool=K.EXPLO, ln=0.7, sub=-3.0, extra=None, extra_db=-6.0):
    def f(v, key):
        st = _p(key, v, p)
        layers = [at(tp(pool, v, key, st, ln), 0.0),
                  at(D.gain(K.thump(55 * D.semis(st), 0.35, 0.5, v), sub), 0.0)]
        if extra is not None:
            layers.append(at(D.gain(extra(v, key, st), extra_db), 0.0))
        return D.decay_env(D.mix(*layers), ln * 0.5)
    return f


reg(HIT, "bomber", boom(2.0, pool=K.BANGS, ln=0.55, sub=-6), loud=-15)
reg(HIT, "bomb_tower", boom(0.0, pool=K.BANGS, ln=0.6, sub=-4), loud=-15)
reg(HIT, "goblin_demolisher", boom(-1.0, pool=K.BANGS, ln=0.6), loud=-15)
reg(HIT, "mortar", boom(-2.0, pool=K.EXPLO, ln=0.8, sub=-1), loud=-13)
reg(HIT, "sparky", boom(-3.0, pool=K.EXPLO, ln=0.9, sub=0,
                        extra=lambda v, k, st: K.zap(0.4, v, 2500), extra_db=-4), loud=-12)


def fire_hit(p=0.0, ln=0.45):
    def f(v, key):
        st = _p(key, v, p)
        return D.mix(at(D.gain(tp(K.BANGS, v, key, st + 4, ln), -2), 0.0),
                     at(D.gain(K.crackle_fire(ln + 0.1, v), -6), 0.0),
                     at(D.gain(head(K.from_peak(tp(K.FIRE_SPELL, v, key, st), 0.01), ln), -6),
                        0.0))
    return f


reg(HIT, "wizard", fire_hit(1.0), loud=-16)
reg(HIT, "baby_dragon", fire_hit(2.0, 0.35), loud=-17)
reg(HIT, "skeleton_dragons", fire_hit(4.0, 0.3), loud=-19)
reg(HIT, "princess", fire_hit(3.0, 0.35), loud=-19)


def frost_hit(v, key):
    st = DET[v]
    return D.mix(at(D.gain(tp(K.GLASS, v, key, st, 0.3), -2), 0.0),
                 at(D.gain(tp(K.ICY, v, key, st + 2, 0.35), -4), 0.0))


reg(HIT, "ice_wizard", frost_hit, loud=-19)


def witch_hit(v, key):
    st = DET[v]
    return D.mix(at(D.gain(K.shimmer(1300 * D.semis(st), 0.35, v), -2), 0.0),
                 at(D.gain(tp(K.SPLATS, v, key, st + 4, 0.25), -8), 0.0))


reg(HIT, "witch", witch_hit, loud=-20)


def firework_burst(v, key):
    st = DET[v]
    return D.mix(at(tp(K.FIREWORK, v, key, st, 0.7), 0.0),
                 at(D.gain(D.crackle(0.6, 160, v, 3000, 0.25), -4), 0.05))


reg(HIT, "firecracker", firework_burst, loud=-16)


# ======================================================================
#  THE BIGGEST HITS: extra weight (sub punch, crack, debris, a harder
#  transient and a touch of saturation) and more volume, scaled by w
# ======================================================================
HEAVY_HITS = {
    "pekka": 1.0, "mini_pekka": 1.0, "mega_knight": 1.0, "golem": 0.9, "golemite": 0.5,
    "giant": 0.8, "goblin_giant": 0.6, "giant_skeleton": 0.8, "electro_giant": 0.7,
    "rune_giant": 0.7, "goblin_monster": 0.8, "elixir_golem": 0.6, "tomb_queen": 0.8,
    "skeleton_king": 0.8, "boss_bandit": 0.6, "prince": 0.8, "dark_prince": 0.7,
    "hog_rider": 0.7, "ram_rider": 0.6, "battle_ram": 0.8, "royal_guardian": 0.6,
    "valkyrie": 0.6, "elite_barbarians": 0.5, "lumberjack": 0.4, "goblin_brawler": 0.6,
    "bowler": 0.7, "ronin": 0.5, "royal_ghost": 0.5, "rhino": 0.6, "royal_giant": 0.6,
    "goblin_machine": 0.6, "executioner": 0.4,
}
HEAVY_IMPACTS = {"sparky": 1.0, "mortar": 0.8, "bomb_tower": 0.5, "bomber": 0.4,
                 "goblin_demolisher": 0.5}


def enhance(y, w, v):
    """Add impact_core at the main hit and make the hit hit harder."""
    env = D.envelope(y, 0.002)
    i = int(np.argmax(env > 0.5 * env.max())) if len(env) else 0
    t = max(0.0, i * 0.002 - 0.003)
    y = D.mix((y, 0.0, 0.0), (K.impact_core(v, w), t, -5.0 + 3.0 * w))
    y = D.transient(y, attack_db=3.0 + 5.0 * w)
    y = D.normalize(y, 0.9)
    return D.saturate(y, 1.5 + 1.5 * w, 0.4 * w)


def _heavy(table, key, w):
    fn = table[key]
    table[key] = (lambda v, fn=fn, w=w: enhance(fn(v), w, v))
    LOUD[key] = LOUD.get(key, -15.0) + 2.5 * w


for _k, _w in HEAVY_HITS.items():
    _heavy(ATTACK, _k, _w)
for _k, _w in HEAVY_IMPACTS.items():
    _heavy(HIT, _k, _w)
