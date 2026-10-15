"""
============================================================================
  ORCH.PY  --  A tiny sampled orchestra (stereo) for music and jingles
============================================================================

Instruments are folders of single-note recordings from the CC0 VSCO-2 CE
library (strings, brass, harp, mallets, drums). Inst.note() picks the
recording nearest in pitch (and loudness layer), retunes it, cuts it to the
note length with a natural release. Song collects notes on a beat grid and
mixes them to a stereo buffer with panning, a hall reverb and a limiter.

Signals here are float32 arrays of shape (n, 2) at dsp.SR.
============================================================================
"""

import functools
import os
import re
import zlib

import numpy as np
from scipy import signal as sps

import dsp as D
import sources as S

NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8,
        "A": 9, "A#": 10, "B": 11}


def midi(name):
    """'A#3' -> 58 (C4 = 60)."""
    m = re.match(r"([A-G]#?)(-?\d)", name)
    return 12 * (int(m.group(2)) + 1) + NOTE[m.group(1)]


def vsco(*parts):
    return os.path.join(S.CACHE, "inst", "vsco", *parts)


@functools.lru_cache(maxsize=2048)
def _load2(path):
    import soundfile as sf
    data, sr = sf.read(path, dtype="float32", always_2d=True)
    if data.shape[1] == 1:
        data = np.repeat(data, 2, axis=1)
    data = data[:, :2]
    if sr != D.SR:
        g = np.gcd(int(sr), D.SR)
        data = sps.resample_poly(data, D.SR // g, int(sr) // g, axis=0).astype(np.float32)
    data -= data.mean(axis=0)
    # start at the attack: drop leading silence
    env = np.abs(data).max(axis=1)
    thr = env.max() * 0.02
    idx = np.nonzero(env > thr)[0]
    a = max(0, idx[0] - D.n_of(0.003)) if len(idx) else 0
    return data[a:].astype(np.float32)


def load2(path):
    return _load2(os.path.abspath(path)).copy()


def speed2(x, factor):
    if abs(factor - 1.0) < 1e-4:
        return x
    up, down = D._ratio(1.0 / factor)
    return sps.resample_poly(x, up, down, axis=0).astype(np.float32)


def fade2(x, fin=0.0, fout=0.05):
    x = x.copy()
    a, b = min(len(x), D.n_of(fin)) if fin else 0, min(len(x), D.n_of(fout))
    if a > 1:
        x[:a] *= np.linspace(0, 1, a, dtype=np.float32)[:, None]
    if b > 1:
        x[-b:] *= (np.linspace(1, 0, b, dtype=np.float32) ** 2)[:, None]
    return x


class Inst:
    """A sampled instrument: a folder of note recordings.

    VSCO names most notes an octave low (its C3 is middle C), measured
    against the recordings' real pitch: transpose=12 fixes that (the harp
    is named correctly, transpose=0).

    pattern: regex with groups (note name, velocity layer) found in names.
    sustain: True = cut to the note length (+release); False = let the
    whole sample ring (plucks, hits).
    """

    def __init__(self, folder, pattern=r"_([A-G]#?\d)_v(\d+)", gain=0.0, release=0.18,
                 sustain=True, fixed=None, lo=None, hi=None, transpose=12):
        self.gain = D.undb(gain)
        self.release = release
        self.sustain = sustain
        self.samples = {}                 # layer -> [(midi, path)]
        files = sorted(os.listdir(folder)) if os.path.isdir(folder) else []
        for f in files:
            if not f.lower().endswith(".wav"):
                continue
            if fixed is not None:          # unpitched (drums): one "note"
                m = re.search(pattern, f)
                if not m:
                    continue
                g1 = m.group(1) if m.groups() else None
                layer = int(g1) if g1 and g1.isdigit() else 1
                self.samples.setdefault(layer, []).append((fixed, os.path.join(folder, f)))
                continue
            m = re.search(pattern, f)
            if not m:
                continue
            n = midi(m.group(1)) + transpose       # VSCO names C3 = middle C
            if (lo is not None and n < lo) or (hi is not None and n > hi):
                continue
            g2 = m.group(2) if len(m.groups()) > 1 else None
            layer = int(g2) if g2 and g2.isdigit() else 1
            self.samples.setdefault(layer, []).append((n, os.path.join(folder, f)))
        self.layers = sorted(self.samples)
        if not self.layers:
            raise FileNotFoundError("no samples in " + folder)

    def note(self, n, dur, vel=0.8, seed=0):
        layer = self.layers[min(len(self.layers) - 1, int(vel * len(self.layers)))]
        cands = self.samples[layer]
        best = min(abs(c[0] - n) for c in cands)
        near = [c for c in cands if abs(c[0] - n) == best]
        sm, path = near[seed % len(near)]
        x = speed2(load2(path), 2.0 ** ((n - sm) / 12.0))
        if self.sustain:
            x = fade2(x[:D.n_of(dur + self.release)], 0.0, self.release)
        else:
            x = fade2(x[:D.n_of(max(dur, 0.05) + 2.5)], 0.0, 0.05)
        return x * (self.gain * (0.45 + 0.55 * vel))


def _pan(x, p):
    """Constant-power pan, p in 0 (left) .. 1 (right)."""
    a = p * np.pi / 2
    out = x.copy()
    out[:, 0] *= np.cos(a) * 1.41421
    out[:, 1] *= np.sin(a) * 1.41421
    return out


class Song:
    def __init__(self, bpm, bars, beats=4):
        self.bpm = bpm
        self.beats = beats
        self.bars = bars
        self.spb = 60.0 / bpm
        self.events = []

    @property
    def length(self):
        return self.bars * self.beats * self.spb

    def add(self, inst, beat, n, dur, vel=0.8, pan=0.5, humanize=True):
        """Note n (midi) at `beat` for `dur` beats."""
        self.events.append((inst, beat, n, dur, vel, pan, humanize))

    def chord(self, inst, beat, notes, dur, vel=0.8, pan=0.5, spread=0.0):
        for i, n in enumerate(notes):
            self.add(inst, beat + i * spread, n, dur, vel, pan)

    def render(self, loop=True, tail=3.0):
        total = D.n_of(self.length + tail)
        buf = np.zeros((total, 2), np.float32)
        for k, (inst, beat, n, dur, vel, pan, hum) in enumerate(self.events):
            seed = zlib.crc32(("%d %s %s" % (k, beat, n)).encode())
            jitter = 0.0
            if hum:                                     # a touch of human timing
                jitter = ((seed % 1000) / 1000.0 - 0.5) * 0.012
                vel = min(1.0, max(0.05, vel * (0.93 + 0.14 * ((seed >> 10) % 100) / 100)))
            x = inst.note(n, dur * self.spb, vel, seed)
            x = _pan(x, pan)
            o = max(0, D.n_of(beat * self.spb + jitter))
            e = min(total, o + len(x))
            buf[o:e] += x[:e - o]
        if loop:                          # wrap the tail over the start
            n = D.n_of(self.length)
            out = buf[:n].copy()
            rest = buf[n:]
            out[:len(rest)] += rest[:n]
            return out
        return buf


# ---------------------------------------------------------------- mix bus
@functools.lru_cache(maxsize=4)
def _hall_ir(t60=1.6, seed=3):
    n = D.n_of(t60)
    rng = np.random.default_rng(seed)
    t = np.arange(n) / D.SR
    ir = rng.standard_normal((n, 2)).astype(np.float32) * np.exp(-6.9 * t / t60)[:, None]
    for c in range(2):
        ir[:, c] = D.sweep_lp(ir[:, c], 8000, 2500, 12)
    ir[:D.n_of(0.02)] = 0.0                                  # pre-delay
    return ir / np.sqrt((ir ** 2).sum(axis=0, keepdims=True))


def hall(x, wet_db=-15.0, t60=1.6, loop=True):
    ir = _hall_ir(round(t60, 2))
    w = np.stack([sps.fftconvolve(x[:, c], ir[:, c]) for c in range(2)], axis=1)
    if loop:                              # reverb tail wraps around the loop
        n = len(x)
        out = w[:n].copy()
        out[:len(w) - n] += w[n:][:n]
        w = out
    else:
        w = w[:len(x) + len(ir)]
        x = np.concatenate([x, np.zeros((len(w) - len(x), 2), np.float32)])
    return (x + w * D.undb(wet_db)).astype(np.float32)


def master(x, loud_db=-16.0, ceiling=0.93):
    """Gentle bus compression + loudness + soft limiting (stereo-linked)."""
    m = x.mean(axis=1)
    env = np.sqrt(sps.lfilter([0.0005], [1, -0.9995], m ** 2) + 1e-9)
    thr = np.percentile(env, 90)
    g = np.where(env > thr, (thr / env) ** 0.35, 1.0).astype(np.float32)
    x = x * g[:, None]
    r = D.rms(x.mean(axis=1))
    x = x * (D.undb(loud_db) / max(r, 1e-9))
    pk = np.abs(x).max()
    if pk > ceiling * 0.7:
        k = 0.7 * ceiling
        a = np.abs(x)
        over = a > k
        x[over] = np.sign(x[over]) * (k + (ceiling - k) * np.tanh((a[over] - k) / (ceiling - k)))
    return x.astype(np.float32)


def write2(path, x, quality=0.6):
    """Write stereo audio. OGG is written block by block (libsndfile can
    crash encoding long Vorbis files in one call)."""
    import soundfile as sf
    x = np.clip(np.nan_to_num(x), -0.999, 0.999).astype(np.float32)
    if path.endswith(".ogg"):
        kw = {}
        try:
            with sf.SoundFile(path, "w", D.SR, 2, format="OGG", subtype="VORBIS",
                              compression_level=1.0 - quality) as f:
                for i in range(0, len(x), D.SR):
                    f.write(x[i:i + D.SR])
            return
        except TypeError:
            pass
        with sf.SoundFile(path, "w", D.SR, 2, format="OGG", subtype="VORBIS", **kw) as f:
            for i in range(0, len(x), D.SR):
                f.write(x[i:i + D.SR])
    else:
        sf.write(path, x, D.SR, subtype="PCM_16")


# ---------------------------------------------------------------- the band
@functools.lru_cache(maxsize=1)
def band():
    V = vsco
    b = {
        "vln_spic": Inst(V("Strings", "Violin Section", "Spic"), gain=-3, release=0.12),
        "vln_pizz": Inst(V("Strings", "Violin Section", "Pizz"), sustain=False, gain=-2),
        "vln_sus": Inst(V("Strings", "Violin Section", "susVib"), gain=-4, release=0.35),
        "vla_pizz": Inst(V("Strings", "Viola Section", "pizz"), sustain=False, gain=-3),
        "vla_sus": Inst(V("Strings", "Viola Section", "susvib"), gain=-5, release=0.35),
        "vc_pizz": Inst(V("Strings", "Cello Section", "pizzT"), sustain=False, gain=-1),
        "vc_spic": Inst(V("Strings", "Cello Section", "spic"), gain=-2, release=0.1),
        "vc_sus": Inst(V("Strings", "Cello Section", "susvib"), gain=-4, release=0.35),
        "cb_pizz": Inst(V("Strings", "Solo Contrabass", "Pizz"), sustain=False, gain=0),
        "harp": Inst(V("Strings", "Harp"), pattern=r"_([A-G]#?\d)_(m)f", sustain=False, gain=-4,
                     transpose=0),
        "horn": Inst(V("Brass", "F Horn", "sus"), gain=-4, release=0.25),
        "horn_stac": Inst(V("Brass", "F Horn", "stac"), gain=-3, release=0.1),
        "tpt": Inst(V("Brass", "Trumpet", "sus"), gain=-6, release=0.2),
        "tpt_stac": Inst(V("Brass", "Trumpet", "stac"), gain=-5, release=0.1),
        "tbn": Inst(V("Brass", "Tenor Trombone", "sus"), gain=-5, release=0.25),
        "tuba": Inst(V("Brass", "Tuba", "sus"), gain=-4, release=0.25),
        "glock": Inst(V("Percussion", "Glock"), pattern=r"_([A-G]#?\d)()", sustain=False,
                      gain=-10),
        "xylo": Inst(V("Percussion", "Xylo"), pattern=r"_([A-G]#?\d)_ff()", sustain=False,
                     gain=-6),
        "bd": Inst(V("Percussion"), pattern=r"^BDrumNewhit_v(\d)", fixed=36, sustain=False),
        "snare": Inst(V("Percussion"), pattern=r"^Snare2-HitSN_v(\d)", fixed=38, sustain=False,
                      gain=-4),
        "snare_roll": Inst(V("Percussion"), pattern=r"^Snare2-rollSN_v(\d)", fixed=38,
                           gain=-6, release=0.2),
        "crash": Inst(V("Percussion"), pattern=r"^cymbal-crash1_(?:pp|mp|mf|ff)_rr()",
                      fixed=49, sustain=False, gain=-8),
        "timp": Inst(V("Percussion", "Timpani"), pattern=r"^Timpani(\d)_Hit", fixed=45,
                     sustain=False, gain=-2),
        "tamb": Inst(V("Percussion"), pattern=r"^Tamb1-Hit_v(\d)", fixed=54, sustain=False,
                     gain=-12),
        "tri": Inst(V("Percussion"), pattern=r"^Triangle3-Hit_v(\d)", fixed=81, sustain=False,
                    gain=-14),
    }
    return b
