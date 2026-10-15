"""
============================================================================
  SOUNDS.PY  --  Music & sound effects: loading, playback, synthesis
============================================================================

Almost every sound is a finished file in assets/sounds, built OFFLINE by
tools/sfx (see assets/sounds/CREDITS.txt):

  * battle sounds - attacks, splash impacts, deploys, deaths, abilities,
    spawns, spells (cast + impact), UI clicks - are public-domain (CC0)
    recordings processed with numpy, 3 variants each (<name>_1..3.ogg),
    one picked at random every time;
  * jingles (match start, victory, crown...) and music themes 3-4 are
    played by a sampled orchestra (CC0 VSCO-2 samples) or are CC0
    recordings (stereo .ogg).

Only music themes 1-2 are still synthesised here from scratch (oscillators,
filtered noise, plucked strings): on first run (or whenever SOUND_VERSION
changes) they are rendered into assets/sounds/music_*.wav.

>>> To use your own sounds, drop a WAV with the same name (without the
    variant number) into assets/sounds/ - e.g. knight_attack.wav replaces
    all three Knight attack variants, victory.wav the victory jingle. Files
    you add yourself are never overwritten.
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


# ===========================================================================
#  SYNTH VOICES (used by the synthesised music themes)
# ===========================================================================
def s_whoosh(dur=0.35, f0=400, f1=1800, seed=2, vol=1.0):
    n = noise(dur, attack=dur * 0.6, decay=dur * 0.9, seed=seed)
    return gain(bandpass(lowpass(n, f0, f1), (f0 + f1) / 2, 0.9), 2.5 * vol)


def s_clang(f=900, dur=0.45, seed=3, bright=1.0):
    out = []
    for ratio, g in ((1.0, 1.0), (2.76, 0.55), (5.4, 0.3 * bright), (8.93, 0.15 * bright)):
        mix_into(out, tone(f * ratio, dur, decay=dur * (0.9 / ratio ** 0.35)), 0, g)
    mix_into(out, highpass(noise(0.05, decay=0.04, seed=seed), 3000), 0, 0.5)
    return out


def s_brass(f=220, dur=0.5, notes=(0, 4, 7)):
    out = []
    for semi in notes:
        ff = f * 2 ** (semi / 12)
        sig = lowpass(tone(ff, dur, wave_="saw", attack=0.03, vib=0.004), ff * 4)
        mix_into(out, sig, 0, 0.35)
    return out


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
    jobs.append(("music_menu", make_menu_music))
    jobs.append(("music_battle", make_battle_music))
    jobs.append(("music_menu2", make_menu_music2))
    jobs.append(("music_battle2", make_battle_music2))
    return jobs


def _manifest_path():
    return os.path.join(SOUND_DIR, ".soundgen.json")



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
        if name == "music_battle":
            names = ["music_battle", "music_final"]
        elif name == "music_battle2":
            names = ["music_battle2", "music_final2"]
        else:
            names = [name]
        if not any(needs(nm) for nm in names):
            now.update(nm for nm in names if nm in generated or fresh_install)
            continue
        res = build()
        if name == "music_battle":
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


# Which death sound (assets/sounds/die_<group>_1..3.ogg) each unit makes.
# Units not listed: buildings -> "building", big ones -> "big", else "small".
_DEATH_GROUPS = {
    "human": "knight barbarians barbarian elite_barbarians wizard ice_wizard electro_wizard "
             "prince dark_prince lumberjack hog_rider executioner hunter magic_archer miner "
             "mighty_miner little_prince golden_knight monk ronin fisherman rascal_boy "
             "royal_recruits royal_guardian",
    "female": "archers musketeer three_musketeers valkyrie princess witch mother_witch "
              "night_witch bandit battle_healer ram_rider archer_queen firecracker berserker "
              "rascal_girl boss_bandit dagger_duchess spirit_empress tower_princess",
    "goblin": "goblins goblin goblin_gang spear_goblins spear_goblin dart_goblin goblin_brawler "
              "bush_goblin decoy_goblin goblin_demolisher demolisher_charge",
    "skeleton": "skeletons skeleton skeleton_army guards bomber wall_breakers wb_runner "
                "giant_skeleton skeleton_king skeletrooper souldier skeleton_general tomb_queen",
    "giant": "giant royal_giant goblin_giant electro_giant rune_giant bowler mega_knight",
    "golem": "golem golemite ice_golem",
    "machine": "pekka mini_pekka flying_machine cannon_cart sparky zappies goblin_machine "
               "hero_turret balloon battle_ram",
    "monster": "goblinstein goblin_monster rhino royal_hogs cursed_hog",
    "flyer": "baby_dragon inferno_dragon electro_dragon lava_hound lava_pup phoenix "
             "phoenix_reborn mega_minion minions minion_horde minion_giant skeleton_dragons",
    "bug": "bats bat",
    "magic": "ice_spirit electro_spirit heal_spirit spirit_empress_air ma_decoy phoenix_egg "
             "suspicious_bush",
    "fire": "fire_spirit",
    "elixir": "elixir_golem elixir_golemite elixir_blob",
    "ghost": "royal_ghost lumberjack_ghost",
    "building": "skeleton_barrel furnace",
}
DEATH_GROUP = {k: g for g, ks in _DEATH_GROUPS.items() for k in ks.split()}
DEATH_NAMES = ["die_" + g for g in list(_DEATH_GROUPS) + ["big", "small"]]


def death_sound(key, building=False, big=False):
    """The death sound name for unit `key`."""
    g = DEATH_GROUP.get(key)
    if g is None:
        g = "building" if building else ("big" if big else "small")
    return "die_" + g


def match_sound_names(m):
    """The recorded sounds everything that can appear in match m may need."""
    keys = {"princess_tower", "king_tower"}
    keys.update(getattr(m, "tower_troops", {}).values())
    for deck in getattr(m, "decks", ()):
        for k in deck:
            for r in _related(k):
                keys.update(_related(r))
    names = list(DEATH_NAMES) + ["tower_down", "dash", "slam", "portal"]
    for k in sorted(keys):
        for kind in ("attack", "hit", "deploy", "ability", "spawn", "cast", "impact"):
            names.append(k + "_" + kind)
    return names


def music_themes(kind):
    """How many themes of `kind` ('menu' or 'battle') are installed (1..4):
    music_<kind>.wav, music_<kind>2.wav, music_<kind>3.ogg, ..."""
    n = 1
    while n < 9:
        nm = "music_%s%d" % (kind, n + 1)
        if not any(os.path.exists(os.path.join(SOUND_DIR, nm + e)) for e in (".wav", ".ogg")):
            break
        n += 1
    return n


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

    def preload(self, names, background=True):
        """Load these sounds' variants ahead of time (at match start), so
        the first swing of each unit doesn't touch the disk mid-battle.
        Runs on a background thread (each file takes ~1 ms to decode, so the
        game never stalls); anything played before it gets there simply
        loads on the spot."""
        names = [n for n in names if n not in self.variants]
        if not names:
            return

        def work():
            for n in names:
                self._variants(n)
        if background:
            try:
                import threading
                threading.Thread(target=work, daemon=True).start()
                return
            except Exception:
                pass
        work()

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
        """Play `name` (name.wav / name.ogg, or one of its name_1..3
        variants)."""
        if not (self.ok and self.sfx_on):
            return False
        t = self.last.get(name, -9.0)
        if self.clock - t < min_gap:
            return False
        snd = self._get(name)
        if snd is None:
            return self.play_var(name, vol, pan, 0.0)
        return self._start(name, snd, vol, pan)

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
        """track: 'menu' | 'menu2..4' | 'battle' | 'battle2..4' | 'final' |
        'final2..4' | None (stop). Themes 1-2 are synthesised WAVs, 3-4 are
        .ogg files built by tools/sfx/music.py."""
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
                path = path[:-4] + ".ogg"
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
