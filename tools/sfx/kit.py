"""
============================================================================
  KIT.PY  --  Building blocks: picked takes from the CC0 packs + synth layers
============================================================================

take(pack, file, i) returns event #i of a recording (trimmed, cleaned) and
caches it. The pools below list the best takes for each kind of sound so
the variants of a unit can use DIFFERENT real recordings (not just a
re-pitch of one), which is what makes repeats sound natural.
============================================================================
"""

import functools

import numpy as np

import dsp as D
import sources as S

# pack keys
SW = "20-sword-sound-effects-attacks-and-clashes"
TINY = "fantasy-sound-effects-tinysized-sfx"
WEAP = "fantasy-weapons-and-apparel-sfx-library"
MI = "medieval-sound-effects-weapon-impacts"
MT = "medieval-sound-effects-weapon-textures"
KI = "kenney/impact-sounds"
KR = "kenney/rpg-audio"
KS = "kenney/sci-fi-sounds"
RPG = "rpg-sound-pack"
SWISH = "swishes-sound-pack"
BSE = "battle-sound-effects"
R80 = "80-cc0-rpg-sfx"
C1 = "80-cc0-creature-sfx"
C2 = "80-cc0-creture-sfx-2"
HITS = "37-hitspunches"
BANG = "25-cc0-bang-firework-sfx"
GUN = "the-free-firearm-sound-library"
GS = "gunshots"
MW = "100-cc0-metal-and-wood-sfx"
SFX100 = "100-cc0-sfx"
SCI = "50-cc0-sci-fi-sfx"
ELEC = "electricity-game-sound-pack"
SPARK = "electricity-sound-effects-0"
ICE = "ice-spells"
FRZ = "freeze-spell-0"
MAG = "magic-spell-sfx"
BONES = "bones-rattle"
GOB = "goblins-sound-pack"
SPLAT = "8-wet-squish-slurp-impacts"
GHAST = "7-ghast-sounds"
FB = "fireball-1"
FLAME = "catching-fire"
SHIELD = "10-impactshield-blocks"
MIMP = "metal-impact-sounds"
DIG = "63-digital-sound-effects-lasers-phasers-space-etc"
TROLL = "big-scary-troll-sounds"
ZOMB = "zombie-skeleton-monster-voice-effects"
MON1 = "monster-sound-effects-pack"
MON2 = "monster-sound-effects-2"
MON3 = "monster-sound-pack-volume-1"


@functools.lru_cache(maxsize=1024)
def _take(pack, name, i, hp, gap):
    x = D.load(S.find(pack, name))
    if hp:
        x = D.hp(x, hp, 2)
    y = D.event(x, i, gap=gap) if i is not None else D.trim(x)
    if D.peak(y) > 1e-6:
        y = y / D.peak(y)
    return y.astype(np.float32)


def take(pack, name, i=0, hp=40, gap=0.07):
    """Event #i of a recording (i=None: the whole file, trimmed),
    high-passed at `hp` Hz and peak-normalised."""
    return _take(pack, name, i, hp, gap).copy()


def pick(pool, v):
    """The v-th entry of a pool (wraps)."""
    return pool[v % len(pool)]


def tk(entry):
    """Load a pool entry: (pack, name[, event[, hp]])."""
    pack, name = entry[0], entry[1]
    i = entry[2] if len(entry) > 2 else 0
    hp = entry[3] if len(entry) > 3 else 40
    return take(pack, name, i, hp)


# ===================================================================== pools
# light, fast air swishes (daggers, small blades)
SWISH_LIGHT = [(SWISH, "swish-10.wav"), (SWISH, "swish-11.wav"), (SWISH, "swish-12.wav"),
               (SWISH, "swish-13.wav"), (RPG, "swing3.wav"), (RPG, "swing2.wav")]
# medium swings (swords, clubs)
SWISH_MED = [(RPG, "swing.wav"), (BSE, "swish_2.wav"), (BSE, "swish_4.wav"),
             (SWISH, "swish-4.wav"), (SWISH, "swish-9.wav"), (SWISH, "swish-1.wav")]
# big, low whooshes (axes, hammers, giants)
SWISH_HEAVY = [(SWISH, "swish-7.wav"), (SWISH, "swish-3.wav"), (SWISH, "swish-5.wav"),
               (BSE, "swish_3.wav"), (SWISH, "swish-8.wav"), (SWISH, "swish-6.wav")]
# a blade sliding through the air with a metallic "shing"
SHING = [(SW, "sword.2.ogg"), (SW, "sword.4.ogg"), (SW, "sword.6.ogg"), (SW, "sword.3.ogg"),
         (SW, "sword.7.ogg"), (SW, "sword.1.ogg")]
# steel on steel
CLASH = [(SW, "sword_clash.2.ogg"), (SW, "sword_clash.5.ogg"), (SW, "sword_clash.8.ogg"),
         (SW, "sword_clash.3.ogg"), (SW, "sword_clash.6.ogg"), (SW, "sword_clash.7.ogg"),
         (SW, "sword_clash.4.ogg"), (SW, "sword_clash.10.ogg")]
CLASH_BRIGHT = [(TINY, "sword-clash-02.wav"), (TINY, "sword-clash-04.wav"),
                (TINY, "sword-clash-01.wav"), (TINY, "sword-clash-05.wav"),
                (WEAP, "sword-knife-clash-08.wav"), (WEAP, "sword-knife-clash-13.wav")]
CLASH_LONG = [(WEAP, "sword-knife-clash-06.wav"), (WEAP, "sword-knife-clash-10.wav"),
              (WEAP, "sword-knife-clash-07.wav"), (WEAP, "sword-knife-clash-09.wav")]
# real weapon-on-weapon recordings (duller, woody/heavy)
BLADE_ON_HAFT = [(MI, "Axe Spear Blade on haft.wav"), (MI, "Seax Axe Blade on Haft.wav"),
                 (MI, "Dagger Axe Blade on Haft.wav"), (MI, "Spear Spear Blade on Haft.wav")]
BLADE_ON_BLADE = [(MI, "Axe Norse Sword Blade on Blade.wav"), (MI, "Axe Katana Blade on Blade.wav"),
                  (MI, "Axe Sabre Blade on Blade.wav"), (MI, "Spear Norse Sword Blade on Blade.wav"),
                  (MI, "Seax Norse Sword Blade on Blade.wav"), (MI, "Dagger Katana Blade on Blade.wav")]
HAFT = [(MI, "Spear Spear Haft on Haft.wav"), (MI, "Axe Spear Haft on Haft.wav"),
        (MI, "Mace Spear Haft.wav")]
MACE = [(MI, "Mace Spear Blade.wav"), (MI, "Mace Norse Sword Blade.wav"),
        (MI, "Mace Sabre Blade.wav"), (MI, "Mace Katana Blade.wav"), (MI, "Mace Axe Blade and Haft.wav")]
CHOP = [(KR, "chop.ogg"), (KI, "impactWood_heavy_000.ogg"), (KI, "impactWood_heavy_001.ogg"),
        (KI, "impactWood_heavy_002.ogg")]
SLICE = [(KR, "knifeSlice.ogg"), (KR, "knifeSlice2.ogg")]
KNIFE = [(R80, "blade_01.ogg"), (R80, "blade_02.ogg"), (R80, "blade_03.ogg")]
# fists, clubs, bodies
PUNCH_MED = [(KI, "impactPunch_medium_000.ogg"), (KI, "impactPunch_medium_001.ogg"),
             (KI, "impactPunch_medium_002.ogg"), (KI, "impactPunch_medium_003.ogg"),
             (KI, "impactPunch_medium_004.ogg")]
PUNCH_HEAVY = [(KI, "impactPunch_heavy_000.ogg"), (KI, "impactPunch_heavy_001.ogg"),
               (KI, "impactPunch_heavy_002.ogg"), (KI, "impactPunch_heavy_003.ogg"),
               (KI, "impactPunch_heavy_004.ogg")]
FIST = [(HITS, "hit09.mp3.flac"), (HITS, "hit10.mp3.flac"), (HITS, "hit06.mp3.flac"),
        (HITS, "hit03.mp3.flac"), (HITS, "hit11.mp3.flac"), (HITS, "hit01.mp3.flac")]
BODY = [(HITS, "hit07.mp3.flac"), (HITS, "hit08.mp3.flac"), (HITS, "hit02.mp3.flac")]
SOFT_HEAVY = [(KI, "impactSoft_heavy_000.ogg"), (KI, "impactSoft_heavy_001.ogg"),
              (KI, "impactSoft_heavy_002.ogg"), (KI, "impactSoft_heavy_003.ogg")]
PLATE = [(KI, "impactPlate_heavy_000.ogg"), (KI, "impactPlate_heavy_001.ogg"),
         (KI, "impactPlate_heavy_002.ogg"), (KI, "impactPlate_heavy_003.ogg")]
PLATE_MED = [(KI, "impactPlate_medium_000.ogg"), (KI, "impactPlate_medium_001.ogg"),
             (KI, "impactPlate_medium_002.ogg"), (KI, "impactPlate_medium_003.ogg")]
METAL_HEAVY = [(KI, "impactMetal_heavy_000.ogg"), (KI, "impactMetal_heavy_001.ogg"),
               (KI, "impactMetal_heavy_002.ogg"), (KI, "impactMetal_heavy_003.ogg")]
METAL_MED = [(KI, "impactMetal_medium_000.ogg"), (KI, "impactMetal_medium_001.ogg"),
             (KI, "impactMetal_medium_002.ogg"), (KI, "impactMetal_medium_003.ogg")]
METAL_LIGHT = [(KI, "impactMetal_light_000.ogg"), (KI, "impactMetal_light_001.ogg"),
               (KI, "impactMetal_light_002.ogg"), (KI, "impactMetal_light_003.ogg")]
SHIELD_HIT = [(SHIELD, "impact.1.ogg"), (SHIELD, "impact.3.ogg"), (SHIELD, "impact.5.ogg"),
              (SHIELD, "impact.7.ogg"), (SHIELD, "impact.9.ogg")]
WOOD = [(KI, "impactPlank_medium_000.ogg"), (KI, "impactPlank_medium_001.ogg"),
        (KI, "impactPlank_medium_002.ogg"), (KI, "impactWood_medium_000.ogg")]
MINING = [(KI, "impactMining_000.ogg"), (KI, "impactMining_001.ogg"),
          (KI, "impactMining_002.ogg"), (KI, "impactMining_003.ogg")]
STONE = [(R80, "stones_04.ogg"), (R80, "stones_01.ogg"), (R80, "item_stone_01.ogg")]
HAMMER = [(TINY, "metal-hammer-hit-01.wav"), (TINY, "metal-hammer-hit-02.wav"),
          (MW, "hammer_01.ogg"), (MW, "hammer_02.ogg"), (MW, "hammer_03.ogg")]
CHAIN = [(R80, "chain_01.ogg"), (R80, "chain_02.ogg"), (RPG, "chainmail1.wav"),
         (RPG, "chainmail2.wav")]
CLOTH = [(KR, "cloth1.ogg"), (KR, "cloth2.ogg"), (KR, "cloth4.ogg")]
BONE = [(BONES, "0.ogg"), (BONES, "2.ogg"), (BONES, "3.ogg"), (BONES, "5.ogg"),
        (BONES, "6.ogg"), (BONES, "8.ogg"), (BONES, "9.ogg"), (BONES, "1.ogg")]
SPLATS = [(SPLAT, "impactsplat03.mp3.flac"), (SPLAT, "impactsplat06.mp3.flac"),
          (SPLAT, "impactsplat02.mp3.flac"), (SPLAT, "impactsplat04.mp3.flac")]
SPIT = [(C1, "spit_01.ogg"), (C1, "spit_02.ogg"), (C1, "spit_03.ogg")]
# bows
BOW = [(BSE, "Bow.wav"), (MT, "English Longbow Shoot.wav", 0), (MT, "Scythian Recurve Shoot.wav", 0),
       (MT, "English Longbow Shoot.wav", 2), (MT, "Scythian Recurve Shoot.wav", 2),
       (MT, "English Longbow Shoot.wav", 5)]
XBOW = [(MT, "Crossbow Shoot.wav", 0), (MT, "Crossbow Shoot.wav", 1), (MT, "Crossbow Shoot.wav", 2),
        (MT, "Crossbow Shoot.wav", 3), (MT, "Crossbow Shoot.wav", 4), (MT, "Crossbow Shoot.wav", 5)]
ARROW_FLY = [(MT, "Scythian Recurve Arrow Passby.wav", 0), (MT, "Crossbow Bolt Passby.wav", 0),
             (MT, "Crossbow Bolt Passby.wav", 1), (MT, "Crossbow Bolt Passby.wav", 2),
             (MT, "Scythian Recurve Arrow Passby.wav", 3)]
# firearms
MUSKET = [(GS, "Black Powder.wav", 0), (GS, "Black Powder.wav", 2), (GS, "Black Powder.wav", 4),
          (GUN, "E_25P.wav", 0), (GUN, "M_26P.wav", 0), (GUN, "E_18P.wav", 0)]
RIFLE = [(GUN, "W_29P.wav", 0), (GUN, "I_22P.wav", 0), (GUN, "L_23P.wav", 0),
         (GUN, "T_27P.wav", 0), (GUN, "U_19P.wav", 0)]
SHOTGUN = [(GUN, "N_30P.wav", 0), (GUN, "O_21P.wav", 0), (GUN, "K_22P.wav", 0),
           (GUN, "N_26P.wav", 0), (GUN, "O_17P.wav", 0), (GUN, "K_17P.wav", 0)]
PISTOL = [(GUN, "H_21P.wav", 0), (GUN, "V_27P.wav", 0), (GUN, "R_30P.wav", 0),
          (GUN, "S_11P.wav", 0), (GS, "22 Magnum.wav", 0)]
SMALLSHOT = [(BANG, "shot_01.ogg"), (BANG, "shot_02.ogg"), (BANG, "shot_03.ogg")]
CANNON = [(BANG, "cannon_02.ogg"), (BANG, "cannon_01.ogg"), (BANG, "cannon_04.ogg"),
          (BANG, "cannon_05.ogg"), (BANG, "cannon_03.ogg")]
BANGS = [(BANG, "bang_09.ogg"), (BANG, "bang_03.ogg"), (BANG, "bang_06.ogg"),
         (BANG, "bang_07.ogg"), (BANG, "bang_01.ogg"), (BANG, "bang_10.ogg")]
FIREWORK = [(BANG, "fw_03.ogg"), (BANG, "fw_06.ogg"), (BANG, "fw_05.ogg"), (BANG, "fw_01.ogg")]
EXPLO = [(KS, "explosionCrunch_000.ogg"), (KS, "explosionCrunch_001.ogg"),
         (KS, "explosionCrunch_003.ogg"), (KS, "explosionCrunch_004.ogg"),
         (SCI, "explosion_01.ogg"), (SCI, "explosion_02.ogg")]
LOWBOOM = [(KS, "lowFrequency_explosion_000.ogg"), (KS, "lowFrequency_explosion_001.ogg")]
# elements
FIREBALL = [(GHAST, "ghast_fireball.1.ogg"), (FB, "105016__julien-matthey__jm-fx-fireball-01.wav"),
            (FLAME, "flame.ogg")]
FIRE_SPELL = [(R80, "spell_fire_06.ogg"), (R80, "spell_fire_07.ogg"), (R80, "spell_fire_01.ogg"),
              (R80, "spell_fire_04.ogg")]
ZAPS = [(ELEC, "groundhit.wav"), (SPARK, "spark.wav"), (SPARK, "continuousspark.wav"),
        (ELEC, "hit.wav"), (ELEC, "death_1.wav"), (ELEC, "teleport_1.wav")]
PARALYZE = [(TINY, "paralyzer-discharge-01.wav"), (TINY, "paralyzer-discharge-02.wav")]
ICY = [(ICE, "coldsnap.wav", 0), (ICE, "ice.wav", 0), (ICE, "coldsnap.wav", 1), (FRZ, "freeze.wav", 0)]
GLASS = [(KI, "impactGlass_light_000.ogg"), (KI, "impactGlass_light_001.ogg"),
         (KI, "impactGlass_light_002.ogg"), (KI, "impactGlass_medium_000.ogg"),
         (KI, "impactGlass_medium_001.ogg")]
MAGIC = [(MAG, "magical_3.ogg"), (MAG, "magical_2.ogg"), (MAG, "magical_5.ogg"),
         (MAG, "magical_4.ogg"), (MAG, "magical_1.ogg"), (MAG, "magical_6.ogg")]
SPELL = [(R80, "spell_01.ogg"), (R80, "spell_02.ogg"), (RPG, "magic1.wav"), (RPG, "spell.wav")]
LASER = [(KS, "laserLarge_000.ogg"), (KS, "laserLarge_001.ogg"), (KS, "laserLarge_002.ogg")]
# mechanisms
CLICKS = [(KR, "metalClick.ogg"), (KR, "metalLatch.ogg"), (MW, "metal_spring_01.ogg"),
          (MW, "metal_spring_02.ogg")]
XBOW_MECH = [(MT, "Crossbow Lever Trigger.wav", 0), (MT, "Crossbow Set Nut Against Sear.wav", 0),
             (MT, "Crossbow Lever Trigger.wav", 1), (MT, "Crossbow Place Bolt.wav", 0)]
TOOLS = [(MW, "tools_01.ogg"), (MW, "tools_03.ogg"), (MW, "tools_05.ogg"), (MW, "tools_07.ogg"),
         (SFX100, "tools_02.ogg"), (SFX100, "tools_04.ogg")]


# ===================================================================== synth
def thump(f=70.0, t=0.18, drop=0.5, seed=0):  # noqa: C901
    """A low body hit (a sine that drops in pitch, plus a little noise).
    The seed also nudges pitch, length and drop, so variants differ."""
    j = (seed % 3) - 1
    f *= 1.0 + 0.09 * j
    t *= 1.0 - 0.14 * j
    drop *= 1.0 + 0.12 * (((seed + 1) % 3) - 1)
    y = D.osc(f, t, f * drop, "sine")
    y = D.decay_env(y, t / 4.0)
    n = D.lp(D.noise(min(t, 0.06), "pink", seed), 400)
    n = D.decay_env(n, 0.012)
    out = np.zeros(len(y), np.float32)
    out += y
    out[:len(n)] += n * 0.5
    return D.fade(out, 0.001, 0.03)


def puff(t=0.08, f=2500.0, seed=0):
    """A short breath of air (blowgun, dart)."""
    n = D.bp(D.noise(t, "white", seed), f * 0.6, f * 1.6)
    return D.fade(D.decay_env(D.adsr(n, 0.004, t, 0.6, 0.02), t / 2.5), 0.002, 0.02)


def whoosh(t=0.25, f0=500.0, f1=2500.0, seed=0):
    """Synth air whoosh: band-passed noise that rises and falls."""
    n = D.noise(t, "pink", seed)
    y = D.sweep_lp(n, f0, f1, 16)
    y = D.hp(y, f0 * 0.4)
    env = np.sin(np.linspace(0, np.pi, len(y))) ** 1.6
    return (y * env).astype(np.float32)


def zap(t=0.22, seed=0, f=3200.0):
    """An electric discharge: a sharp crack, then a run of short, buzzing
    sparks (each a burst of band-passed noise + a jittery arc tone) that
    thins out - not a steady hiss."""
    r = D.rng(seed)
    n = D.n_of(t)
    y = np.zeros(n + D.n_of(0.06), np.float32)
    crack = D.hp(D.noise(0.006, "white", seed), 1500) * 3.0
    y[:len(crack)] += crack * np.linspace(1, 0, len(crack))
    pos, k = D.n_of(0.004), 0
    while pos < n:
        life = 1.0 - pos / n
        bl = r.uniform(0.006, 0.03)
        m = D.n_of(bl)
        burst = D.bp(D.noise(bl, "white", seed + 7 + k), f * 0.3, min(f * 1.8, 16000))
        fa = r.uniform(70, 190)
        arc = D.osc(fa, bl, fa * r.uniform(0.8, 1.25), "saw")
        arc = D.bp(arc, 250, 4500)
        seg = (burst * 2.2 + arc * 0.7) * np.exp(-np.arange(m) / (m / 2.2)).astype(np.float32)
        y[pos:pos + m] += seg * r.uniform(0.5, 1.0) * (0.3 + 0.7 * life)
        pos += int(m * r.uniform(0.5, 1.4)) + D.n_of(r.uniform(0.0, 0.012) * (1.5 - life))
        k += 1
    return D.fade(y, 0.0003, 0.03)


def fizz(t=0.3, seed=0, f=6000.0):
    """Fuse / sizzle hiss: band-limited, flickering, dying away."""
    n = D.bp(D.noise(t, "white", seed), f * 0.6, min(f * 2.2, 18000))
    am = D.lp(D.rng(seed).random(D.n_of(t)).astype(np.float32), 40)
    am = 0.4 + 1.2 * (am - am.min()) / (np.ptp(am) + 1e-9) * 0.5
    return D.fade(D.decay_env(n * am, t / 2.5), 0.01, 0.06)


def crackle_fire(t=0.4, seed=0):
    """Burning: soft low roar + a few small, rounded pops."""
    c = D.crackle(t, 45, seed, bright=0, decay=t / 1.5)
    c = D.bp(c, 700, 5000) * 0.5
    roar = D.lp(D.noise(t, "brown", seed + 3), 900)
    roar = D.adsr(roar, 0.03, 0.1, 0.6, t * 0.6)
    return c + roar * 0.8


def shimmer(f=1500.0, t=0.5, seed=0, n=5):
    """Glassy magic shimmer: detuned decaying partials."""
    r = D.rng(seed)
    parts = []
    for _ in range(n):
        parts.append((r.uniform(1.0, 2.6), r.uniform(0.3, 1.0), r.uniform(0.08, 0.3)))
    y = D.modal(f, t, parts, seed, strike=0.0005)
    return D.fade(y, 0.002, 0.05)


def drill(t=0.3, f=170.0, seed=0):
    """Motor whine + grinding."""
    m = D.osc(f, t, f * 1.08, "saw")
    m = D.lp(m, 2400) * 0.5
    g = D.bp(D.noise(t, "white", seed), 1500, 5000)
    am = 0.5 + 0.5 * np.sin(2 * np.pi * 37 * np.arange(D.n_of(t)) / D.SR)
    y = m + g * am.astype(np.float32) * 0.8
    return D.fade(D.adsr(y, 0.01, 0.05, 0.9, 0.06), 0.005, 0.05)


def chime(f=1046.0, notes=(0, 4, 7), step=0.05, t=0.5):
    out = []
    for i, s in enumerate(notes):
        tone = D.modal(f * D.semis(s), t, [(1, 1, t / 3), (2.0, 0.25, t / 6), (3.0, 0.1, t / 9)], i)
        out.append((tone, i * step, -4.0))
    return D.mix(*out)


# ===================================================================== helpers
def at(sig, t):
    return (sig, t, 0.0)


def pitch(x, st):
    return D.speed(x, D.semis(st)) if st else x


def from_peak(x, pre=0.03, fin=0.02):
    """Start a slow-swelling take just before its loudest moment."""
    env = D.envelope(x, 0.005)
    a = max(0, int(np.argmax(env) * 0.005 * D.SR) - D.n_of(pre))
    return D.fade(x[a:], fin, 0.02)


def head(x, t, tail=0.03):
    """First t seconds (faded)."""
    return D.shorten(x, t, tail)
