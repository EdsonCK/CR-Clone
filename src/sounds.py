"""
============================================================================
  SOUNDS.PY  --  Music & sound effects: loading, playback, synthesis
============================================================================

ATTACK SOUNDS (v1.4.7) are real recordings: every unit has 3 variants,
assets/sounds/<cardkey>_attack_1..3.ogg, built OFFLINE by tools/sfx from
public-domain (CC0) packs (see assets/sounds/CREDITS.txt), and splash
projectiles (bombs, fireballs, mortar shells...) also get an impact,
<cardkey>_hit_1..3.ogg. Each attack plays one of the variants at random.

Everything else (deploys, spells, UI, music) is synthesised here from
scratch (oscillators, filtered noise, plucked strings...). On first run
(or whenever SOUND_VERSION changes) those are rendered into
assets/sounds/*.wav and loaded from disk afterwards.

>>> To use your own sounds, drop a WAV with the same name into
    assets/sounds/ (e.g. knight_deploy.wav). Files you add yourself are
    never overwritten. Names:
        <cardkey>_deploy.wav   played when the card is placed
        <cardkey>_attack.wav   replaces ALL of that unit's attack variants
        <spellkey>_impact.wav  played when a spell lands
        music_menu / music_battle / music_final .wav  (looping music)
        ui_*, death_*, tower_*, ... (see EXTRA_SOUNDS below)
============================================================================
"""

import array
import json
import math
import os
import random
import wave
import zlib

import cards

SR = 22050                      # sample rate (Hz) of the synthesised WAVs
MIX_SR = 44100                  # the mixer's rate (the recorded .ogg files)
VARIANTS = 3                    # <name>_1..3.ogg per varied sound
SOUND_VERSION = 2

_HERE = os.path.dirname(os.path.abspath(__file__))
SOUND_DIR = os.path.join(os.path.dirname(_HERE), "assets", "sounds")
TAU = 2.0 * math.pi


# ===========================================================================
#  SYNTH PRIMITIVES  (plain Python lists of floats in -1..1)
# ===========================================================================
def silence(dur):
    return [0.0] * max(1, int(dur * SR))


def tone(f0, dur, f1=None, wave_="sine", vol=1.0, attack=0.004, decay=None,
         vib=0.0, vib_rate=5.5, sweep="exp"):
    """Oscillator with optional pitch sweep f0->f1 and an envelope.
    decay=None -> sustain then short release; decay=t -> exponential decay."""
    n = max(1, int(dur * SR))
    f1 = f0 if f1 is None else f1
    out = [0.0] * n
    ph = 0.0
    a_n = max(1, int(attack * SR))
    rel = max(1, int(0.02 * SR))
    lr = math.log(max(f1, 1e-3) / max(f0, 1e-3))
    k = (1.0 / (decay * SR)) if decay else 0.0
    for i in range(n):
        t = i / n
        f = f0 * math.exp(lr * t) if sweep == "exp" else f0 + (f1 - f0) * t
        if vib:
            f *= 1.0 + vib * math.sin(TAU * vib_rate * i / SR)
        ph += f / SR
        ph -= int(ph)
        if wave_ == "sine":
            v = math.sin(TAU * ph)
        elif wave_ == "square":
            v = 1.0 if ph < 0.5 else -1.0
        elif wave_ == "saw":
            v = 2.0 * ph - 1.0
        else:  # triangle
            v = 4.0 * ph - 1.0 if ph < 0.5 else 3.0 - 4.0 * ph
        e = 1.0
        if i < a_n:
            e = i / a_n
        if decay:
            e *= math.exp(-i * k * 6.9)
        elif i > n - rel:
            e *= (n - i) / rel
        out[i] = v * e * vol
    return out


def noise(dur, vol=1.0, attack=0.002, decay=None, seed=1, color="white"):
    """White / brown noise burst with an envelope."""
    r = random.Random(seed)
    n = max(1, int(dur * SR))
    out = [0.0] * n
    a_n = max(1, int(attack * SR))
    k = (1.0 / (decay * SR)) if decay else 0.0
    rel = max(1, int(0.02 * SR))
    b = 0.0
    for i in range(n):
        v = r.uniform(-1.0, 1.0)
        if color == "brown":
            b = (b + 0.08 * v) * 0.985
            v = b * 3.5
        e = i / a_n if i < a_n else 1.0
        if decay:
            e *= math.exp(-i * k * 6.9)
        elif i > n - rel:
            e *= (n - i) / rel
        out[i] = v * e * vol
    return out


def lowpass(sig, cutoff, cutoff_end=None):
    """One-pole low-pass (optionally sweeping its cutoff)."""
    out = [0.0] * len(sig)
    y = 0.0
    n = len(sig)
    c1 = cutoff_end if cutoff_end is not None else cutoff
    for i, x in enumerate(sig):
        c = cutoff + (c1 - cutoff) * (i / n) if c1 != cutoff else cutoff
        a = 1.0 - math.exp(-TAU * c / SR)
        y += a * (x - y)
        out[i] = y
    return out


def highpass(sig, cutoff):
    lp = lowpass(sig, cutoff)
    return [x - l for x, l in zip(sig, lp)]


def bandpass(sig, f, q=4.0):
    """RBJ biquad band-pass (constant skirt gain)."""
    w = TAU * f / SR
    alpha = math.sin(w) / (2 * q)
    b0, b1, b2 = alpha, 0.0, -alpha
    a0, a1, a2 = 1 + alpha, -2 * math.cos(w), 1 - alpha
    b0, b1, b2, a1, a2 = b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0
    x1 = x2 = y1 = y2 = 0.0
    out = [0.0] * len(sig)
    for i, x in enumerate(sig):
        y = b0 * x + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, x, y1, y
        out[i] = y
    return out


def pluck(freq, dur, bright=0.5, vol=1.0, seed=3):
    """Karplus-Strong plucked string."""
    r = random.Random(seed)
    n = max(1, int(dur * SR))
    period = max(2, int(SR / freq))
    buf = [r.uniform(-1, 1) for _ in range(period)]
    mean = sum(buf) / period
    buf = [v - mean for v in buf]              # no DC offset
    out = [0.0] * n
    keep = 0.993 + 0.006 * bright
    idx = 0
    for i in range(n):
        v = buf[idx]
        nxt = buf[(idx + 1) % period]
        buf[idx] = (v + nxt) * 0.5 * keep
        out[i] = v * vol
        idx = (idx + 1) % period
    return out


def fm(fc, ratio, index, dur, vol=1.0, decay=0.3, attack=0.002):
    """Simple FM pair: bells, metal, glass."""
    n = max(1, int(dur * SR))
    out = [0.0] * n
    fmod = fc * ratio
    k = 1.0 / (decay * SR)
    a_n = max(1, int(attack * SR))
    for i in range(n):
        t = i / SR
        env = math.exp(-i * k * 6.9)
        ienv = index * env
        v = math.sin(TAU * fc * t + ienv * math.sin(TAU * fmod * t))
        e = env * (i / a_n if i < a_n else 1.0)
        out[i] = v * e * vol
    return out


def mix_into(buf, sig, offset=0.0, gain=1.0):
    """Add sig into buf starting at `offset` seconds (buf grows as needed)."""
    o = int(offset * SR)
    need = o + len(sig)
    if need > len(buf):
        buf.extend([0.0] * (need - len(buf)))
    for i, v in enumerate(sig):
        buf[o + i] += v * gain
    return buf


def gain(sig, g):
    return [v * g for v in sig]


def normalize(sig, peak=0.85):
    m = max((abs(v) for v in sig), default=0.0)
    if m < 1e-9:
        return sig
    k = peak / m
    return [v * k for v in sig]


def fade_tail(sig, dur=0.03):
    n = min(len(sig), int(dur * SR))
    for i in range(n):
        sig[len(sig) - n + i] *= (n - i) / n
    return sig


def loop_wrap(sig, length):
    """Fold anything past `length` seconds back onto the start so a music
    loop repeats seamlessly (reverb/decay tails carry over the loop point)."""
    n = int(length * SR)
    out = sig[:n] + [0.0] * max(0, n - len(sig))
    for i in range(n, len(sig)):
        out[(i - n) % n] += sig[i]
    return out


def soft_clip(sig, drive=1.6, rms_target=None):
    """Gentle tanh compression; optionally aim for a loudness (RMS)."""
    if rms_target:
        rms = math.sqrt(sum(v * v for v in sig) / max(len(sig), 1)) or 1e-9
        sig = [v * rms_target / rms for v in sig]
    k = math.tanh(drive)
    return [math.tanh(v * drive) / k for v in sig]


def resample(sig, factor):
    """Speed up (factor>1) / slow down by linear interpolation."""
    n = int(len(sig) / factor)
    out = [0.0] * n
    L = len(sig) - 1
    for i in range(n):
        p = i * factor
        j = int(p)
        f = p - j
        a = sig[j] if j <= L else 0.0
        b = sig[j + 1] if j + 1 <= L else 0.0
        out[i] = a + (b - a) * f
    return out


def write_wav(path, sig):
    data = array.array("h", (int(max(-1.0, min(1.0, v)) * 32000) for v in sig))
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def _rng(key, salt=""):
    return random.Random(zlib.crc32((key + salt).encode()))


# ===========================================================================
#  SOUND FAMILIES
# ===========================================================================
def s_explosion(size=1.0, seed=1, bright=0.5):
    out = []
    mix_into(out, lowpass(noise(0.9 * size, decay=0.55 * size, seed=seed,
                                color="brown"), 900 * (0.6 + bright), 120), 0, 1.0)
    mix_into(out, tone(110 / size, 0.5 * size, 38, decay=0.4 * size), 0, 0.9)
    mix_into(out, highpass(noise(0.18, decay=0.12, seed=seed + 7), 2500), 0, 0.35)
    return out


def s_whoosh(dur=0.35, f0=400, f1=1800, seed=2, vol=1.0):
    n = noise(dur, attack=dur * 0.6, decay=dur * 0.9, seed=seed)
    return gain(bandpass(lowpass(n, f0, f1), (f0 + f1) / 2, 0.9), 2.5 * vol)


def s_clang(f=900, dur=0.45, seed=3, bright=1.0):
    out = []
    for ratio, g in ((1.0, 1.0), (2.76, 0.55), (5.4, 0.3 * bright), (8.93, 0.15 * bright)):
        mix_into(out, tone(f * ratio, dur, decay=dur * (0.9 / ratio ** 0.35)), 0, g)
    mix_into(out, highpass(noise(0.05, decay=0.04, seed=seed), 3000), 0, 0.5)
    return out


def s_thud(f=90, dur=0.35, seed=4, vol=1.0):
    out = tone(f * 1.8, dur, f * 0.6, decay=dur * 0.7)
    mix_into(out, lowpass(noise(dur * 0.6, decay=dur * 0.4, seed=seed), 700), 0, 0.6)
    return gain(out, vol)


def s_zap(f=1200, dur=0.3, seed=5):
    r = random.Random(seed)
    out = []
    t = 0.0
    while t < dur:
        seg = r.uniform(0.012, 0.04)
        ff = f * r.uniform(0.6, 1.6)
        mix_into(out, tone(ff, seg, ff * r.uniform(0.5, 1.5), wave_="square",
                           decay=seg * 2), t, r.uniform(0.4, 0.9))
        t += seg * r.uniform(0.6, 1.0)
    mix_into(out, highpass(noise(dur, decay=dur * 0.7, seed=seed), 2000), 0, 0.5)
    return lowpass(out, 6000)


def s_bolt(dur=0.3, seed=5, bright=1.0):
    """An electric bolt: a sharp crack, then a crackling, fizzing discharge
    over a low mains-style hum. No pitched tones, so it never 'rings'."""
    r = random.Random(seed)
    out = highpass(noise(0.035, attack=0.0005, decay=0.02, seed=seed), 1800)
    out = gain(out, 1.3)
    # crackle: a burst of tiny random sparks that thins out over time
    t = 0.004
    while t < dur:
        life = 1.0 - t / dur
        burst = highpass(noise(r.uniform(0.001, 0.004), attack=0.0002,
                               decay=0.002, seed=r.randint(0, 10 ** 6)), 1200)
        mix_into(out, burst, t, r.uniform(0.3, 1.0) * (0.25 + 0.75 * life))
        t += r.uniform(0.003, 0.016) * (1.0 + 1.5 * (1.0 - life))
    out = bandpass(out, 3200 * bright, 0.9)
    mix_into(out, highpass(noise(dur, decay=dur * 0.5, seed=seed + 1), 5000), 0, 0.25)
    hum = lowpass(tone(100, dur * 0.8, 85, wave_="saw", attack=0.002,
                       decay=dur * 0.45), 700)
    mix_into(out, hum, 0, 0.35)
    return out


def s_shimmer(f=1500, dur=0.6, seed=6, n=5):
    r = random.Random(seed)
    out = []
    for i in range(n):
        mix_into(out, fm(f * r.uniform(0.9, 2.2), 1.41, 2.0, dur * r.uniform(0.5, 1.0),
                         decay=dur * 0.5), i * 0.035, 0.35)
    return out


def s_voice(pitch=180, vowel=0, dur=0.22, seed=7, growl=0.0):
    """A tiny formant 'grunt' - gives every troop its own voice."""
    formants = [(730, 1090), (530, 1840), (270, 2290), (570, 840), (440, 1020),
                (660, 1720)][vowel % 6]
    src = tone(pitch, dur, pitch * 0.82, wave_="saw", attack=0.01, decay=dur * 0.9,
               vib=0.02)
    if growl:
        src = [v + growl * w for v, w in zip(src, noise(dur, decay=dur, seed=seed))]
    out = []
    mix_into(out, bandpass(src, formants[0], 5), 0, 1.0)
    mix_into(out, bandpass(src, formants[1], 6), 0, 0.6)
    return gain(out, 3.0)


def s_twang(f=300, dur=0.3, seed=8):
    out = pluck(f, dur, bright=0.3, seed=seed)
    mix_into(out, s_whoosh(0.18, 1200, 4000, seed=seed, vol=0.4), 0.02, 1.0)
    return out


def s_gunshot(size=1.0, seed=9):
    out = highpass(noise(0.12 * size, decay=0.09 * size, seed=seed), 900)
    mix_into(out, tone(160 / size, 0.16 * size, 60, decay=0.12), 0, 0.8)
    mix_into(out, lowpass(noise(0.4 * size, decay=0.3, seed=seed + 1), 500), 0.01, 0.35)
    return out


def s_fire(dur=0.45, seed=10, f=600):
    out = lowpass(noise(dur, attack=0.05, decay=dur * 0.8, seed=seed), f * 2, f * 0.6)
    r = random.Random(seed)
    for _ in range(int(dur * 25)):     # crackles
        mix_into(out, highpass(noise(0.006, decay=0.005, seed=r.randint(0, 99999)), 2500),
                 r.uniform(0, dur), r.uniform(0.3, 0.8))
    return gain(out, 1.6)


def s_bones(seed=11, n=4, f=1800):
    r = random.Random(seed)
    out = []
    for i in range(n):
        mix_into(out, bandpass(noise(0.03, decay=0.025, seed=r.randint(0, 9999)),
                               f * r.uniform(0.7, 1.4), 8), i * r.uniform(0.03, 0.06), 2.5)
    return out


def s_mechanical(seed=12, f=220):
    r = random.Random(seed)
    out = []
    for i in range(3):
        mix_into(out, s_clang(f * r.uniform(1.5, 3.0), 0.12, seed + i, 0.5), i * 0.07, 0.5)
    mix_into(out, tone(f, 0.25, f * 0.7, wave_="square", decay=0.2), 0, 0.15)
    return lowpass(out, 5000)


def s_chime(f=880, notes=(0, 4, 7), step=0.07, dur=0.5):
    out = []
    for i, semi in enumerate(notes):
        mix_into(out, fm(f * 2 ** (semi / 12), 2.0, 1.2, dur, decay=dur * 0.6),
                 i * step, 0.5)
    return out


def s_brass(f=220, dur=0.5, notes=(0, 4, 7)):
    out = []
    for semi in notes:
        ff = f * 2 ** (semi / 12)
        sig = lowpass(tone(ff, dur, wave_="saw", attack=0.03, vib=0.004), ff * 4)
        mix_into(out, sig, 0, 0.35)
    return out


# ---------------------------------------------------------------------------
# Unit groups used to pick deploy sounds
# ---------------------------------------------------------------------------
HEAVY = {"pekka", "mega_knight", "giant_skeleton", "golem", "golemite", "giant",
         "goblin_giant", "electro_giant", "elixir_golem", "ice_golem",
         "goblin_monster", "skeleton_king", "royal_guardian", "lava_hound"}
UNDEAD = {"skeletons", "skeleton", "skeleton_army", "skeleton_barrel",
          "giant_skeleton", "skeleton_king", "guards", "tombstone", "graveyard"}
MACHINES = {"xbow", "mortar", "cannon", "tesla", "inferno_tower", "bomb_tower",
            "flying_machine", "cannon_cart", "sparky", "elixir_collector",
            "goblin_hut", "barbarian_hut", "furnace", "royal_giant"}
SMALL = {"skeletons", "skeleton", "skeleton_army", "goblins", "goblin",
         "spear_goblins", "spear_goblin", "bats", "bat", "minions",
         "minion_horde", "lava_pup", "ice_spirit", "fire_spirit",
         "electro_spirit", "elixir_blob", "guards", "dart_goblin",
         "wall_breakers", "bomber", "zappies"}


def make_deploy(c):
    """Placing a card: landing thump + the unit's own 'voice'."""
    r = _rng(c.key, "dep")
    sd = r.randint(0, 10 ** 6)
    p = r.uniform(0.85, 1.2)
    if c.category == "building":
        out = []
        for i in range(3):
            mix_into(out, s_thud(140 * p * (1 + 0.1 * i), 0.18, sd + i), i * 0.11, 0.8)
            mix_into(out, s_clang(700 * p * r.uniform(0.9, 1.3), 0.12, sd + i, 0.5), i * 0.11, 0.3)
        if c.key in MACHINES:
            mix_into(out, s_mechanical(sd, 180 * p), 0.3, 0.6)
        if c.spawner:
            mix_into(out, s_voice(260 * p, r.randint(0, 5), 0.2, sd), 0.32, 0.6)
        return fade_tail(normalize(out, 0.75))
    big = c.hp * max(c.count, 1) >= 1800 or c.key in HEAVY
    small = c.key in SMALL
    out = []
    # landing
    land_f = 70 if big else (180 if small else 120)
    mix_into(out, s_thud(land_f * p, 0.45 if big else 0.25, sd, 1.0), 0, 0.9)
    # voice / character
    vstart = 0.06
    if c.key in UNDEAD:
        mix_into(out, s_bones(sd, 5, 1500 * p), vstart, 0.8)
    elif c.key in MACHINES or c.key in ("battle_ram", "skeleton_barrel"):
        mix_into(out, s_mechanical(sd, 160 * p), vstart, 0.8)
    elif c.flying and c.key in ("baby_dragon", "inferno_dragon", "electro_dragon",
                                "lava_hound"):
        roar = lowpass(tone(110 * p, 0.5, 80 * p, wave_="saw", attack=0.05,
                            decay=0.45, vib=0.03), 900)
        mix_into(roar, lowpass(noise(0.5, attack=0.05, decay=0.4, seed=sd), 700), 0, 0.6)
        mix_into(out, roar, vstart, 0.9)
    elif c.key in ("ice_spirit", "fire_spirit", "electro_spirit", "elixir_blob",
                   "elixir_golem"):
        mix_into(out, s_chime(900 * p, (0, 7, 12), 0.04, 0.3), vstart, 0.6)
    elif c.flying and c.key in ("balloon",):
        mix_into(out, s_whoosh(0.5, 200, 700, sd, 0.6), vstart, 1.0)
    else:
        if small:
            pitch = 330 * p
        elif big:
            pitch = 95 * p
        else:
            pitch = 170 * p
        mix_into(out, s_voice(pitch, r.randint(0, 5), 0.18 if small else 0.28, sd,
                              growl=0.25 if big else 0.0), vstart, 0.8)
        if c.count >= 3:     # a crowd: extra overlapping voices
            for k in range(2):
                mix_into(out, s_voice(pitch * r.uniform(0.85, 1.2), r.randint(0, 5),
                                      0.15, sd + k + 1), vstart + 0.05 * (k + 1), 0.45)
    if c.is_champion:
        mix_into(out, s_brass(196 * p, 0.6, (0, 4, 7, 12)), 0.1, 0.5)
    return fade_tail(normalize(out, 0.8))


# ---------------------------------------------------------------------------
# Spells: a distinct cast + impact for each one
# ---------------------------------------------------------------------------
def make_spell(c):
    k = c.key
    sd = zlib.crc32(k.encode()) % 100000
    if k == "fireball":
        cast = s_whoosh(0.5, 200, 1200, sd, 1.0)
        mix_into(cast, s_fire(0.5, sd, 400), 0, 0.6)
        hit = s_explosion(1.1, sd, 0.7)
        mix_into(hit, s_fire(0.6, sd + 1, 500), 0.05, 0.6)
    elif k == "arrows":
        cast = []
        for i in range(6):
            mix_into(cast, s_twang(220 + 30 * i, 0.25, sd + i), i * 0.03, 0.5)
        hit = []
        r = random.Random(sd)
        for i in range(14):
            mix_into(hit, s_thud(r.uniform(180, 320), 0.08, sd + i, 0.6), r.uniform(0, 0.25), 0.5)
    elif k == "rocket":
        cast = lowpass(noise(0.9, attack=0.3, decay=0.8, seed=sd, color="brown"), 1500, 3000)
        cast = gain(cast, 2.5)
        mix_into(cast, tone(120, 0.9, 260, wave_="saw", attack=0.2, decay=0.8, vol=0.2), 0)
        hit = s_explosion(1.8, sd, 0.9)
    elif k == "zap":
        cast = s_zap(1800, 0.12, sd)
        hit = s_zap(900, 0.35, sd + 1)
        mix_into(hit, s_explosion(0.4, sd, 1.0), 0, 0.5)
    elif k == "the_log":
        cast = s_thud(110, 0.3, sd)
        hit = gain(lowpass(noise(1.3, attack=0.05, decay=1.2, seed=sd, color="brown"), 350), 3)
        r = random.Random(sd)
        for i in range(8):
            mix_into(hit, s_thud(r.uniform(70, 120), 0.12, sd + i, 0.7), i * 0.15, 0.5)
    elif k == "lightning":
        cast = gain(lowpass(noise(0.8, attack=0.4, decay=0.7, seed=sd, color="brown"), 300), 3)
        hit = []
        for i in range(3):
            mix_into(hit, s_zap(1500, 0.15, sd + i), i * 0.18, 0.9)
            mix_into(hit, s_explosion(0.7, sd + i, 1.0), i * 0.18, 0.7)
    elif k == "freeze":
        cast = s_whoosh(0.35, 1500, 6000, sd, 0.6)
        hit = s_shimmer(1600, 1.0, sd, 8)
        mix_into(hit, highpass(noise(0.4, decay=0.35, seed=sd), 4000), 0, 0.4)
    elif k == "poison":
        cast = s_clang(2400, 0.2, sd, 1.0)                       # flask shatters
        hit = []
        r = random.Random(sd)
        for i in range(16):
            f = r.uniform(200, 600)
            mix_into(hit, tone(f, 0.08, f * 1.8, decay=0.07), r.uniform(0, 1.2), 0.35)
        mix_into(hit, gain(highpass(noise(1.3, attack=0.2, decay=1.2, seed=sd), 2000), 0.25), 0)
    elif k == "rage":
        cast = s_voice(110, 0, 0.5, sd, growl=0.6)
        hit = []
        for i in range(4):
            mix_into(hit, tone(80, 0.3, 60, wave_="saw", decay=0.25, vol=0.4), i * 0.25)
        hit = lowpass(hit, 600)
    elif k == "earthquake":
        cast = s_thud(60, 0.4, sd)
        hit = gain(lowpass(noise(1.6, attack=0.1, decay=1.5, seed=sd, color="brown"), 180), 4)
        mix_into(hit, tone(38, 1.6, 30, decay=1.4, vol=0.6), 0)
    elif k == "tornado":
        cast = s_whoosh(0.4, 200, 800, sd, 0.8)
        hit = []
        for i in range(4):
            mix_into(hit, s_whoosh(0.5, 250 + i * 60, 1400, sd + i, 0.7), i * 0.22, 1.0)
    elif k == "graveyard":
        cast = fm(220, 3.5, 3.0, 1.2, decay=1.0, vol=0.5)          # tolling bell
        hit = []
        for i, semi in enumerate((0, 1, 6)):
            mix_into(hit, tone(330 * 2 ** (semi / 12), 1.4, wave_="triangle",
                               attack=0.3, vib=0.01, vol=0.3), 0)
        mix_into(hit, s_bones(sd, 6), 0.3, 0.6)
    elif k == "goblin_barrel":
        cast = s_thud(140, 0.25, sd)
        mix_into(cast, s_whoosh(0.4, 300, 1200, sd, 0.6), 0.05, 1.0)
        hit = s_thud(120, 0.3, sd)
        mix_into(hit, s_clang(500, 0.2, sd, 0.4), 0, 0.5)             # wood splinters
        for i in range(3):
            mix_into(hit, s_voice(420 + 50 * i, i + 2, 0.15, sd + i), 0.12 + 0.05 * i, 0.6)
    elif k == "barbarian_barrel":
        cast = s_thud(120, 0.3, sd)
        hit = gain(lowpass(noise(0.9, decay=0.8, seed=sd, color="brown"), 400), 2.5)
        mix_into(hit, s_voice(140, 0, 0.35, sd, growl=0.3), 0.6, 0.8)
    elif k == "snowball":
        cast = s_whoosh(0.3, 600, 2400, sd, 0.6)
        hit = lowpass(noise(0.35, decay=0.3, seed=sd), 1800)
        mix_into(hit, s_thud(140, 0.2, sd), 0, 0.6)
    elif k == "royal_delivery":
        cast = s_brass(262, 0.5, (0, 4, 7))                       # royal fanfare
        hit = s_thud(90, 0.4, sd)
        mix_into(hit, s_clang(520, 0.25, sd, 0.5), 0, 0.5)        # crate cracks
        mix_into(hit, s_explosion(0.7, sd, 0.4), 0, 0.6)
    elif k == "void":
        cast = tone(70, 0.7, 45, wave_="saw", attack=0.2, decay=0.5, vol=0.4, vib=0.05)
        cast = lowpass(cast, 700)
        hit = s_zap(420, 0.4, sd)
        mix_into(hit, lowpass(noise(0.5, decay=0.45, seed=sd, color="brown"), 500), 0, 2.0)
        mix_into(hit, tone(55, 0.5, 35, decay=0.45, vol=0.6), 0)
    elif k == "vines":
        cast = bandpass(noise(0.4, attack=0.05, decay=0.35, seed=sd), 1800, 1.5)
        hit = []
        r = random.Random(sd)
        for i in range(6):                                         # creaks + snaps
            mix_into(hit, tone(r.uniform(150, 300), 0.18, r.uniform(90, 140),
                               wave_="saw", decay=0.16, vol=0.3), i * 0.07)
            mix_into(hit, s_thud(r.uniform(160, 260), 0.07, sd + i, 0.5), i * 0.07, 0.5)
        hit = lowpass(hit, 2200)
    elif k == "clone":
        cast = s_shimmer(1200, 0.4, sd, 4)
        hit = s_chime(784, (0, 7, 12, 19), 0.05, 0.6)
        mix_into(hit, s_shimmer(2000, 0.6, sd + 1, 6), 0, 0.6)
    elif k == "goblin_curse":
        cast = s_voice(300, 4, 0.3, sd, growl=0.2)
        hit = []
        for i, semi in enumerate((0, 1, 6)):
            mix_into(hit, tone(220 * 2 ** (semi / 12), 1.0, wave_="triangle",
                               attack=0.1, vib=0.02, vol=0.28), i * 0.05)
        mix_into(hit, s_voice(520, 2, 0.25, sd + 1), 0.4, 0.5)    # goblin cackle
    elif k == "mirror":
        cast = s_shimmer(1800, 0.5, sd, 6)
        hit = s_chime(1318, (0, 7, 12), 0.04, 0.4)
    else:
        cast = s_whoosh(0.3, 400, 2000, sd, 0.8)
        hit = s_explosion(0.8, sd, 0.6)
    return fade_tail(normalize(cast, 0.75)), fade_tail(normalize(hit, 0.85))


# ---------------------------------------------------------------------------
# UI, deaths, towers, jingles
# ---------------------------------------------------------------------------
def make_extras():
    S = {}
    S["ui_click"] = normalize(mix_into(tone(1200, 0.05, 900, decay=0.04),
                                       tone(2400, 0.03, decay=0.02), 0, 0.3), 0.5)
    S["ui_select"] = normalize(mix_into(pluck(660, 0.18, 0.6), pluck(990, 0.15, 0.6), 0.04, 0.6), 0.55)
    S["ui_deselect"] = normalize(mix_into(pluck(660, 0.15, 0.6), pluck(440, 0.15, 0.6), 0.04, 0.6), 0.5)
    S["ui_invalid"] = normalize(lowpass(tone(130, 0.18, 110, wave_="square", decay=0.17), 1200), 0.45)
    S["ui_toggle"] = normalize(tone(800, 0.06, 1200, decay=0.05), 0.45)
    S["ability"] = normalize(mix_into(s_whoosh(0.5, 300, 3000, 5, 1.0),
                                      s_chime(784, (0, 4, 7, 12), 0.06, 0.6), 0.1, 0.8), 0.85)
    S["death_small"] = normalize(mix_into(lowpass(noise(0.2, decay=0.15, seed=3), 1500),
                                          tone(500, 0.15, 250, decay=0.12), 0, 0.4), 0.45)
    S["death_big"] = normalize(s_thud(60, 0.6, 9, 1.0), 0.7)
    S["death_building"] = normalize(mix_into(s_explosion(0.9, 21, 0.3), s_bones(4, 6, 800), 0.05, 0.5), 0.7)
    tw = s_explosion(1.8, 31, 0.4)
    mix_into(tw, gain(lowpass(noise(1.5, attack=0.1, decay=1.4, seed=8, color="brown"), 300), 3), 0.2, 1.0)
    S["tower_down"] = normalize(tw, 0.9)
    S["crown"] = normalize(s_chime(1046, (0, 4, 7, 12), 0.09, 0.9), 0.75)
    S["king_wake"] = normalize(s_brass(110, 0.9, (0, 7)), 0.7)
    S["match_start"] = normalize(mix_into(s_brass(196, 0.35, (0, 4, 7)),
                                          s_brass(262, 0.6, (0, 4, 7)), 0.3, 1.0), 0.8)
    S["double_elixir"] = normalize(mix_into(s_chime(523, (0, 7), 0.12, 0.6),
                                            s_chime(784, (0, 7), 0.12, 0.6), 0.3, 1.0), 0.75)
    S["overtime"] = normalize(fm(98, 1.4, 4.0, 2.0, decay=1.8), 0.8)    # gong
    S["tick"] = normalize(tone(1500, 0.04, decay=0.03), 0.35)
    S["dash"] = normalize(s_whoosh(0.25, 500, 3000, 12, 1.0), 0.6)
    S["slam"] = normalize(s_explosion(1.0, 41, 0.3), 0.85)
    por = gain(lowpass(noise(0.7, attack=0.2, decay=0.6, seed=17, color="brown"), 500, 1400), 2.5)
    mix_into(por, tone(90, 0.7, 180, wave_="triangle", attack=0.15, decay=0.6, vol=0.4), 0)
    mix_into(por, s_bones(23, 4, 1300), 0.25, 0.7)
    S["portal"] = normalize(por, 0.7)
    pop = tone(520, 0.12, 900, decay=0.1, vol=0.6)
    mix_into(pop, s_chime(1318, (0, 7), 0.05, 0.35), 0.04, 0.5)
    S["elixir_pop"] = normalize(pop, 0.4)
    ev = s_shimmer(1200, 0.7, 41, 6)
    mix_into(ev, s_whoosh(0.5, 200, 2600, 42, 0.7), 0, 0.8)
    mix_into(ev, tone(220, 0.6, 440, wave_="triangle", attack=0.05, decay=0.5, vol=0.4), 0, 1.0)
    S["evo_deploy"] = normalize(ev, 0.7)
    hr = s_brass(330, 0.45, (0, 4, 7, 12))
    mix_into(hr, s_chime(1318, (0, 7, 12), 0.06, 0.5), 0.1, 0.6)
    S["hero_ability"] = normalize(hr, 0.75)
    vic = []
    for i, semi in enumerate((0, 4, 7, 12)):
        mix_into(vic, s_brass(262 * 2 ** (semi / 12), 0.5 if i < 3 else 1.4, (0, 4, 7)), i * 0.18, 0.6)
    mix_into(vic, s_chime(1046, (0, 4, 7, 12, 16), 0.1, 1.0), 0.6, 0.5)
    S["victory"] = normalize(vic, 0.85)
    dft = []
    for i, semi in enumerate((7, 3, 0, -5)):
        mix_into(dft, s_brass(196 * 2 ** (semi / 12), 0.55 if i < 3 else 1.5, (0, 3)), i * 0.3, 0.6)
    S["defeat"] = normalize(lowpass(dft, 1500), 0.8)
    return S


# ===========================================================================
#  MUSIC  (procedural loops)
# ===========================================================================
def _note(semi, base=440.0):
    return base * 2 ** (semi / 12)


def _kick(seed=1):
    return tone(150, 0.3, 42, decay=0.25)


def _snare(seed=2):
    s = highpass(noise(0.18, decay=0.14, seed=seed), 1200)
    mix_into(s, tone(190, 0.1, 150, decay=0.08), 0, 0.5)
    return s


def _hat(seed=3, dur=0.05):
    return highpass(noise(dur, decay=dur * 0.8, seed=seed), 6000)


def _pad(freqs, dur, vol=0.12):
    out = []
    for f in freqs:
        for det in (0.997, 1.003):
            mix_into(out, tone(f * det, dur, wave_="triangle", attack=0.25), 0, vol)
    return lowpass(out, 1800)


def make_menu_music():
    """Mellow medieval loop: plucked lute arpeggios, soft pad, flute."""
    bpm = 92
    beat = 60.0 / bpm
    # D minor: i - VI - VII - v  /  i - iv - VII - i     (semitones from A4)
    prog = [(-7, [0, 3, 7]), (-11, [0, 4, 7]), (-9, [0, 4, 7]), (-12, [0, 3, 7]),
            (-7, [0, 3, 7]), (-14, [0, 3, 7]), (-9, [0, 4, 7]), (-7, [0, 3, 7])]
    bars = len(prog)
    total = bars * 4 * beat
    out = silence(total * 2)
    melody = [None, 5, 3, 0, 3, None, 7, 5, 3, 2, 0, None, -2, 0, 2, None,
              3, None, 5, 7, 8, 7, 5, None, 3, 2, 0, -2, 0, None, None, None]
    for rep in range(2):
        t0 = rep * total
        for b, (root, chord) in enumerate(prog):
            bt = t0 + b * 4 * beat
            freqs = [_note(root + c - 12) for c in chord]
            mix_into(out, _pad(freqs, 4 * beat), bt, 0.9)
            mix_into(out, tone(_note(root - 24), 4 * beat, decay=3.5 * beat), bt, 0.3)
            # lute arpeggio in 8ths
            pat = [0, 1, 2, 1, 0, 2, 1, 2]
            for i, ci in enumerate(pat):
                f = _note(root + chord[ci])
                mix_into(out, pluck(f, beat * 1.2, 0.45, seed=b * 8 + i), bt + i * beat / 2, 0.22)
            # soft tambourine on 2 and 4
            for q in (1, 3):
                mix_into(out, _hat(b * 4 + q, 0.12), bt + q * beat, 0.08)
            # flute melody on the second pass
            if rep == 1:
                for i in range(4):
                    m = melody[(b * 4 + i) % len(melody)]
                    if m is not None:
                        f = _note(m + 3)
                        mix_into(out, lowpass(tone(f, beat * 0.95, wave_="triangle", attack=0.04,
                                                   vib=0.006), 3000), bt + i * beat, 0.16)
    out = loop_wrap(out, total * 2)
    return normalize(soft_clip(normalize(out, 0.9), 1.2), 0.7)


def make_battle_music():
    """Driving battle loop: drums, saw bass, string ostinato, brass hits."""
    bpm = 140
    beat = 60.0 / bpm
    prog = [-5, -5, -8, -8, -10, -10, -6, -6,      # Em Em C C D D B B   (from A4)
            -5, -5, -8, -8, -10, -10, -6, -1]
    quality = {-5: [0, 3, 7], -8: [0, 4, 7], -10: [0, 4, 7], -6: [0, 4, 7], -1: [0, 4, 7]}
    bars = len(prog)
    total = bars * 4 * beat
    out = silence(total)
    kick, snare = _kick(), _snare()
    hats = [_hat(s) for s in range(4)]
    brass_mel = [7, None, 7, 10, 12, None, 10, 7, 5, None, 3, 5, 7, None, None, None]
    for b, root in enumerate(prog):
        bt = b * 4 * beat
        chord = quality[root]
        # drums
        for q in range(4):
            mix_into(out, kick, bt + q * beat, 0.55 if q in (0, 2) else 0.35)
            if q in (1, 3):
                mix_into(out, snare, bt + q * beat, 0.35)
            for h in range(2):
                mix_into(out, hats[(q + h) % 4], bt + q * beat + h * beat / 2, 0.08)
        if b % 4 == 3:   # fill
            for k in range(4):
                mix_into(out, snare, bt + 3 * beat + k * beat / 4, 0.2 + 0.05 * k)
        # bass: driving 8ths
        for i in range(8):
            f = _note(root - 24 + (12 if i % 4 == 3 else 0))
            mix_into(out, lowpass(tone(f, beat / 2, wave_="saw", decay=beat * 0.5), 700),
                     bt + i * beat / 2, 0.28)
        # strings: 16th ostinato
        arp = [0, 1, 2, 1]
        for i in range(16):
            f = _note(root + chord[arp[i % 4]])
            mix_into(out, lowpass(tone(f, beat / 4, wave_="saw", attack=0.004,
                                       decay=beat * 0.3), 2600), bt + i * beat / 4, 0.09)
        # brass melody on the second half
        if b >= 8:
            for i in range(2):
                m = brass_mel[((b - 8) * 2 + i) % len(brass_mel)]
                if m is not None:
                    f = _note(root + m - 12)
                    sig = lowpass(tone(f, beat * 1.9, wave_="saw", attack=0.03, vib=0.004),
                                  f * 5)
                    mix_into(out, sig, bt + i * 2 * beat, 0.13)
        else:   # brass stabs on bar starts
            mix_into(out, s_brass(_note(root - 12), beat * 0.6, chord), bt, 0.25)
    out = loop_wrap(out, total)
    # drums are spiky: compress so the loop is as loud as the menu music
    return normalize(soft_clip(out, 2.2, rms_target=0.16), 0.75)


def _tom(f=110, seed=4):
    t = tone(f, 0.35, f * 0.55, decay=0.22)
    mix_into(t, lowpass(noise(0.08, decay=0.05, seed=seed), 900), 0, 0.3)
    return t


def make_menu_music2():
    """Second menu theme: bright and warm - harp arpeggios, glockenspiel
    melody, a soft hand drum (F major, a little quicker than the first)."""
    bpm = 104
    beat = 60.0 / bpm
    # F - C/E - Dm - Bb  /  F - Am - Bb - C        (semitones from A4)
    prog = [(-4, [0, 4, 7]), (-9, [0, 4, 7]), (-7, [0, 3, 7]), (-11, [0, 4, 7]),
            (-4, [0, 4, 7]), (0, [0, 3, 7]), (-11, [0, 4, 7]), (-9, [0, 4, 7])]
    bars = len(prog)
    total = bars * 4 * beat
    out = silence(total * 2)
    mel = [12, None, 11, 9, 7, None, 9, None, 5, 7, 9, None, 7, None, None, None,
           12, 14, 12, 11, 9, None, 7, 9, 10, 9, 7, 5, 7, None, None, None]
    drum_lo, drum_hi = _tom(140, 5), _tom(220, 6)
    for rep_ in range(2):
        t0 = rep_ * total
        for b, (root, chord) in enumerate(prog):
            bt = t0 + b * 4 * beat
            freqs = [_note(root + c - 12) for c in chord]
            mix_into(out, _pad(freqs, 4 * beat, vol=0.08), bt, 0.8)
            mix_into(out, pluck(_note(root - 24), 4 * beat, 0.3, seed=b), bt, 0.35)
            # harp: rolling 16th arpeggio up and down two octaves
            arp = [0, 1, 2, 3, 4, 5, 4, 3, 2, 1, 2, 3, 4, 5, 4, 2]
            for i, a in enumerate(arp):
                oc, ci = divmod(a, 3)
                f = _note(root + chord[ci] + 12 * oc - 12)
                mix_into(out, pluck(f, beat * 0.9, 0.65, seed=b * 16 + i),
                         bt + i * beat / 4, 0.12)
            # hand drum: low on 1, high on the "and" of 2 and on 4
            mix_into(out, drum_lo, bt, 0.22)
            mix_into(out, drum_hi, bt + 1.5 * beat, 0.12)
            mix_into(out, drum_hi, bt + 3 * beat, 0.14)
            # glockenspiel melody (second pass), with a bell-like overtone
            if rep_ == 1:
                for i in range(4):
                    m = mel[(b * 4 + i) % len(mel)]
                    if m is not None:
                        f = _note(m - 4)
                        bell = tone(f * 2, beat * 1.4, decay=beat * 0.9)
                        mix_into(bell, tone(f * 5.4, beat * 0.6, decay=beat * 0.25), 0, 0.25)
                        mix_into(out, bell, bt + i * beat, 0.12)
    out = loop_wrap(out, total * 2)
    return normalize(soft_clip(normalize(out, 0.9), 1.6, rms_target=0.17), 0.7)


def make_battle_music2():
    """Second battle theme: war drums and toms, staccato strings, a horn
    call over a choir-like pad (D minor, 150 bpm)."""
    bpm = 150
    beat = 60.0 / bpm
    prog = [-7, -7, -11, -11, -9, -9, -12, -12,      # Dm Dm Bb Bb C C A A
            -7, -7, -2, -2, -9, -9, -12, -12]        # Dm Dm G G C C A A
    quality = {-7: [0, 3, 7], -11: [0, 4, 7], -9: [0, 4, 7], -12: [0, 4, 7],
               -2: [0, 3, 7]}
    bars = len(prog)
    total = bars * 4 * beat
    out = silence(total)
    kick, snare = _kick(), _snare(7)
    toms = [_tom(95, 8), _tom(130, 9), _tom(175, 10)]
    hats = [_hat(s + 10) for s in range(4)]
    horn = [0, None, 3, 5, 7, None, None, 5, 3, None, 2, 3, 0, None, None, None]
    for b, root in enumerate(prog):
        bt = b * 4 * beat
        chord = quality[root]
        # war drums: kick on 1 and the "and" of 2, snare on 3, tom roll at the end
        mix_into(out, kick, bt, 0.55)
        mix_into(out, kick, bt + 1.5 * beat, 0.4)
        mix_into(out, snare, bt + 2 * beat, 0.32)
        mix_into(out, toms[0], bt + 3 * beat, 0.28)
        for q in range(8):
            mix_into(out, hats[q % 4], bt + q * beat / 2, 0.06)
        if b % 4 == 3:
            for k in range(6):
                mix_into(out, toms[2 - k // 2], bt + 2.5 * beat + k * beat / 4, 0.18 + 0.03 * k)
        # bass: root pulses
        for i in (0, 3, 4, 6):
            f = _note(root - 24)
            mix_into(out, lowpass(tone(f, beat / 2, wave_="saw", decay=beat * 0.45), 600),
                     bt + i * beat / 2, 0.3)
        # staccato strings in 8ths
        for i in range(8):
            f = _note(root + chord[(i // 2) % 3])
            mix_into(out, lowpass(tone(f, beat * 0.22, wave_="saw", attack=0.003,
                                       decay=beat * 0.15), 3000), bt + i * beat / 2, 0.1)
        # choir-ish pad
        mix_into(out, _pad([_note(root + c) for c in chord], 4 * beat, vol=0.05), bt, 0.9)
        # horn call on the second half
        if b >= 8:
            for i in range(2):
                m = horn[((b - 8) * 2 + i) % len(horn)]
                if m is not None:
                    f = _note(root + m)
                    sig = lowpass(tone(f, beat * 1.9, wave_="saw", attack=0.05, vib=0.005),
                                  f * 4)
                    mix_into(out, sig, bt + i * 2 * beat, 0.14)
    out = loop_wrap(out, total)
    return normalize(soft_clip(out, 2.2, rms_target=0.16), 0.75)


# ===========================================================================
#  GENERATION / MANIFEST
# ===========================================================================
def _jobs():
    """(name, builder) for every sound file."""
    jobs = []
    for key, c in cards.CARDS.items():
        if c.category == "spell":
            jobs.append((key + "_spell", (lambda c=c: make_spell(c))))
        elif c.deployable:
            jobs.append((key + "_deploy", (lambda c=c: make_deploy(c))))
    # forms that appear mid-match announce themselves too
    for key in ("spirit_empress_air", "demolisher_charge", "phoenix_reborn"):
        jobs.append((key + "_deploy", (lambda c=cards.CARDS[key]: make_deploy(c))))
    jobs.append(("_extras", make_extras))
    jobs.append(("music_menu", make_menu_music))
    jobs.append(("music_battle", make_battle_music))
    jobs.append(("music_menu2", make_menu_music2))
    jobs.append(("music_battle2", make_battle_music2))
    return jobs


def _manifest_path():
    return os.path.join(SOUND_DIR, ".soundgen.json")


EXTRA_NAMES = ["ui_click", "ui_select", "ui_deselect", "ui_invalid", "ui_toggle",
               "ability", "death_small", "death_big", "death_building",
               "tower_down", "crown", "king_wake", "match_start", "double_elixir",
               "overtime", "tick", "dash", "slam", "victory", "defeat", "portal",
               "elixir_pop", "evo_deploy", "hero_ability"]

# Sounds re-rendered since they were first shipped: bump a name's number to
# regenerate just that file on the next launch (without a full SOUND_VERSION
# rebuild). Your own replacement WAVs are still never overwritten.
SOUND_REVS = {"elixir_pop": 3, "evo_deploy": 3, "hero_ability": 3}


def ensure_sounds(progress=None):
    """Render any missing (or outdated, self-generated) WAV files.
    WAVs you put in assets/sounds yourself are never overwritten."""
    os.makedirs(SOUND_DIR, exist_ok=True)
    mp = _manifest_path()
    man = {}
    if os.path.exists(mp):
        try:
            with open(mp) as f:
                man = json.load(f)
        except Exception:
            man = {}
    fresh_install = not man
    old_v = man.get("version")
    generated = set(man.get("generated", []))
    old_revs = man.get("revs", {})
    now = set()

    def needs(nm):
        path = os.path.join(SOUND_DIR, nm + ".wav")
        if not os.path.exists(path):
            return True
        if nm in generated and nm in SOUND_REVS and old_revs.get(nm) != SOUND_REVS[nm]:
            return True
        return nm in generated and old_v != SOUND_VERSION

    def write(nm, sig):
        path = os.path.join(SOUND_DIR, nm + ".wav")
        if os.path.exists(path) and nm not in generated and not fresh_install:
            return                       # the user's own sound
        write_wav(path, sig)
        now.add(nm)

    jobs = _jobs()
    for n, (name, build) in enumerate(jobs):
        if progress:
            progress(n, len(jobs))
        if name == "_extras":
            names = EXTRA_NAMES
        elif name.endswith("_spell"):
            names = [name[:-6] + "_cast", name[:-6] + "_impact"]
        elif name == "music_battle":
            names = ["music_battle", "music_final"]
        elif name == "music_battle2":
            names = ["music_battle2", "music_final2"]
        else:
            names = [name]
        if not any(needs(nm) for nm in names):
            now.update(nm for nm in names if nm in generated or fresh_install)
            continue
        res = build()
        if name == "_extras":
            for nm in names:
                write(nm, res[nm])
        elif name == "music_battle":
            write("music_battle", res)
            # the last-minute track: same loop, faster and a tone higher
            write("music_final", resample(res, 1.12))
        elif name == "music_battle2":
            write("music_battle2", res)
            write("music_final2", resample(res, 1.12))
        elif isinstance(res, tuple):
            for nm, sig in zip(names, res):
                write(nm, sig)
        else:
            write(names[0], res)
    try:
        with open(mp, "w") as f:
            json.dump({"version": SOUND_VERSION, "generated": sorted(now),
                       "revs": SOUND_REVS}, f, indent=0)
    except Exception:
        pass


# ===========================================================================
#  WHICH SOUNDS A MATCH NEEDS  (preloaded when it starts)
# ===========================================================================
_RELATED = {}


def _related(key):
    """`key` plus every unit it can bring onto the field (spawns, death
    spawns, squad members, alternate forms...), found by scanning the
    card's fields for other card keys. Cached."""
    out = _RELATED.get(key)
    if out is not None:
        return out
    out = {key}
    c = cards.CARDS.get(key)
    if c is not None:
        stack = list(vars(c).values())
        while stack:
            v = stack.pop()
            if isinstance(v, str):
                if v in cards.CARDS:
                    out.add(v)
            elif isinstance(v, (list, tuple, set)):
                stack.extend(v)
            elif isinstance(v, dict):
                stack.extend(v.keys())
                stack.extend(v.values())
    _RELATED[key] = out
    return out


def match_sound_names(m):
    """Attack / impact sound names for everything that can appear in match m."""
    keys = {"princess_tower", "king_tower"}
    keys.update(getattr(m, "tower_troops", {}).values())
    for deck in getattr(m, "decks", ()):
        for k in deck:
            for r in _related(k):
                keys.update(_related(r))
    names = []
    for k in sorted(keys):
        names.append(k + "_attack")
        names.append(k + "_hit")
    return names


# ===========================================================================
#  PLAYBACK
# ===========================================================================
class SoundManager:
    """Plays sound effects (with stereo panning + anti-spam) and music."""

    def __init__(self, music_volume=0.45, sfx_volume=0.7):
        self.ok = False
        self.sounds = {}
        self.last = {}
        self.music_track = None
        self.music_on = True
        self.sfx_on = True
        self.music_volume = music_volume
        self.sfx_volume = sfx_volume
        self.clock = 0.0
        self.variants = {}         # name -> [Sound, ...] (loaded once)
        self.last_var = {}         # name -> index played last time
        self._rr = 0               # tiny random generator state (see _pick)
        try:
            import pygame
            self.pg = pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=MIX_SR, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(32)
            self.ok = True
        except Exception:
            self.ok = False

    # ---- loading ----
    def _load(self, name):
        """name.wav (yours / synthesised) or name.ogg (recorded), or None."""
        if not self.ok:
            return None
        for ext in (".wav", ".ogg"):
            path = os.path.join(SOUND_DIR, name + ext)
            if os.path.exists(path):
                try:
                    return self.pg.mixer.Sound(path)
                except Exception:
                    return None
        return None

    def _get(self, name):
        if name in self.sounds:
            return self.sounds[name]
        snd = self._load(name)
        self.sounds[name] = snd
        return snd

    def _variants(self, name):
        """All variants of a sound: your own name.wav alone if you added
        one, else name_1..3.ogg. Loaded on first use, then kept."""
        vs = self.variants.get(name)
        if vs is None:
            own = self._load(name)
            if own is not None:
                vs = [own]
            else:
                vs = [s for s in (self._load("%s_%d" % (name, i + 1))
                                  for i in range(VARIANTS)) if s is not None]
            self.variants[name] = vs
        return vs

    def preload(self, names):
        """Load these sounds' variants now (at match start), so the first
        swing of each unit doesn't touch the disk mid-battle."""
        for n in names:
            self._variants(n)

    def _pick(self, name, n):
        """A random-enough variant index: a tiny 8-bit LCG (one multiply,
        one add) and no immediate repeats - far cheaper than random()."""
        self._rr = (self._rr * 5 + 3) & 255
        i = (self._rr >> 3) % n
        if n > 1 and i == self.last_var.get(name):
            i = (i + 1) % n
        self.last_var[name] = i
        return i

    def tick(self, dt):
        self.clock += dt

    # ---- effects ----
    def play_var(self, name, vol=1.0, pan=0.5, min_gap=0.06):
        """Play one of the variants of `name` (name_1..3) at random."""
        if not (self.ok and self.sfx_on):
            return False
        if self.clock - self.last.get(name, -9.0) < min_gap:
            return False
        vs = self._variants(name)
        if not vs:
            return False
        snd = vs[self._pick(name, len(vs))] if len(vs) > 1 else vs[0]
        return self._start(name, snd, vol, pan)

    def play(self, name, vol=1.0, pan=0.5, min_gap=0.06):
        if not (self.ok and self.sfx_on):
            return
        t = self.last.get(name, -9.0)
        if self.clock - t < min_gap:
            return
        snd = self._get(name)
        if snd is None:
            return
        self._start(name, snd, vol, pan)

    def _start(self, name, snd, vol, pan):
        self.last[name] = self.clock
        ch = self.pg.mixer.find_channel()
        if ch is None:
            return False
        v = max(0.0, min(1.0, vol * self.sfx_volume))
        pan = max(0.0, min(1.0, pan))
        ch.set_volume(v * min(1.0, 2 * (1 - pan)), v * min(1.0, 2 * pan))
        ch.play(snd)
        return True

    # ---- music ----
    def music(self, track):
        """track: 'menu' | 'menu2' | 'battle' | 'battle2' | 'final' | 'final2' |
        None (stop)."""
        if not self.ok:
            return
        if not self.music_on:
            track = None
        if track == self.music_track:
            return
        self.music_track = track
        try:
            if track is None:
                # (music.fadeout() can block the game loop on some systems)
                self.pg.mixer.music.stop()
                return
            path = os.path.join(SOUND_DIR, "music_%s.wav" % track)
            if not os.path.exists(path):
                return
            self.pg.mixer.music.load(path)
            self.pg.mixer.music.set_volume(self.music_volume)
            self.pg.mixer.music.play(-1, fade_ms=700)
        except Exception:
            pass

    def set_music_on(self, on):
        self.music_on = on
        if not on:
            self.music(None)

    def set_sfx_on(self, on):
        self.sfx_on = on
        if not on and self.ok:
            self.pg.mixer.stop()
