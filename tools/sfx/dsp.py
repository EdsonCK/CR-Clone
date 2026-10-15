"""
============================================================================
  DSP.PY  --  numpy sound toolkit for the offline SFX renderer
============================================================================

Everything here runs OFFLINE (tools/sfx/render.py), never in the game: the
game only plays the finished files. Needs:  pip install numpy scipy soundfile

Signals are mono float32 numpy arrays at SR (44.1 kHz), roughly -1..1.
============================================================================
"""

import functools
import os

import numpy as np
from scipy import signal as sps

SR = 44100
_RNG = np.random.default_rng(1)


# ---------------------------------------------------------------- basics
def secs(x):
    return len(x) / SR


def n_of(t):
    return max(1, int(round(t * SR)))


def silence(t):
    return np.zeros(n_of(t), np.float32)


def peak(x):
    return float(np.max(np.abs(x))) if len(x) else 0.0


def rms(x):
    return float(np.sqrt(np.mean(np.square(x, dtype=np.float64)))) if len(x) else 0.0


def db(v):
    return 20.0 * np.log10(max(v, 1e-9))


def undb(d):
    return 10.0 ** (d / 20.0)


# ---------------------------------------------------------------- file I/O
@functools.lru_cache(maxsize=512)
def _load_cached(path):
    import soundfile as sf
    data, sr = sf.read(path, dtype="float32", always_2d=True)
    x = data.mean(axis=1)
    if sr != SR:
        g = np.gcd(int(sr), SR)
        x = sps.resample_poly(x, SR // g, int(sr) // g).astype(np.float32)
    x = x - np.mean(x)                                    # no DC offset
    return x.astype(np.float32)


def load(path):
    """A sound file as mono float32 at SR (cached; returns a copy)."""
    return _load_cached(os.path.abspath(path)).copy()


def write(path, x, quality=0.62):
    """Write .ogg (Vorbis) or .wav, 16-bit mono at SR, peak-limited."""
    import soundfile as sf
    x = np.clip(np.nan_to_num(x), -0.999, 0.999).astype(np.float32)
    if path.endswith(".ogg"):
        try:
            sf.write(path, x, SR, format="OGG", subtype="VORBIS",
                     compression_level=1.0 - quality)
        except TypeError:                                # older soundfile
            sf.write(path, x, SR, format="OGG", subtype="VORBIS")
    else:
        sf.write(path, x, SR, subtype="PCM_16")


# ---------------------------------------------------------------- envelopes
def envelope(x, win=0.01):
    """RMS envelope sampled every `win` seconds."""
    hop = n_of(win)
    n = len(x) // hop
    if n == 0:
        return np.array([rms(x)])
    return np.sqrt(np.mean(np.square(x[:n * hop].reshape(n, hop)), axis=1))


def trim(x, floor_db=-48.0, pre=0.004, post=0.03):
    """Cut leading/trailing silence (relative to the peak)."""
    if not len(x):
        return x
    thr = peak(x) * undb(floor_db)
    idx = np.nonzero(np.abs(x) > thr)[0]
    if not len(idx):
        return x[:0]
    a = max(0, idx[0] - n_of(pre))
    b = min(len(x), idx[-1] + n_of(post))
    return x[a:b]


def segments(x, gap=0.07, floor_db=-36.0, min_len=0.04):
    """Split a recording of several hits into separate events: anything
    quieter than floor_db (re. the loudest part) for `gap` seconds is a
    break. Returns a list of (start_sec, end_sec)."""
    win = 0.005
    env = envelope(x, win)
    if not len(env):
        return []
    thr = env.max() * undb(floor_db)
    on = env > thr
    out, start, quiet = [], None, 0
    need = max(1, int(gap / win))
    for i, v in enumerate(on):
        if v:
            if start is None:
                start = i
            quiet = 0
        elif start is not None:
            quiet += 1
            if quiet >= need:
                end = i - quiet + 1
                if (end - start) * win >= min_len:
                    out.append((start * win, end * win))
                start, quiet = None, 0
    if start is not None:
        end = len(on) - quiet
        if (end - start) * win >= min_len:
            out.append((start * win, end * win))
    return out


def event(x, i=0, **kw):
    """The i-th separate event of a multi-hit recording, trimmed, with a
    natural tail (we keep 120 ms past the detected end, faded)."""
    segs = segments(x, **kw)
    if not segs:
        return trim(x)
    i = min(i, len(segs) - 1)
    a, b = segs[i]
    nxt = segs[i + 1][0] if i + 1 < len(segs) else secs(x)
    b2 = min(nxt - 0.01, b + 0.12)
    y = x[max(0, n_of(a) - n_of(0.003)): n_of(max(b, b2))]
    return fade(trim(y), 0.001, 0.06)


def fade(x, fin=0.002, fout=0.03):
    x = x.copy()
    a, b = min(len(x), n_of(fin)), min(len(x), n_of(fout))
    if a > 1:
        x[:a] *= np.linspace(0, 1, a, dtype=np.float32)
    if b > 1:
        x[-b:] *= np.linspace(1, 0, b, dtype=np.float32) ** 2
    return x


def cut(x, start=0.0, length=None):
    a = n_of(start) if start else 0
    b = len(x) if length is None else min(len(x), a + n_of(length))
    return x[a:b].copy()


def decay_env(x, tau):
    """Multiply by an exponential decay (time constant tau seconds)."""
    t = np.arange(len(x), dtype=np.float32) / SR
    return x * np.exp(-t / max(tau, 1e-4)).astype(np.float32)


def shorten(x, length, tail=0.04):
    """Keep `length` seconds and fade the end smoothly."""
    if secs(x) <= length:
        return fade(x, 0.0005, tail)
    return fade(x[:n_of(length)], 0.0005, tail)


# ---------------------------------------------------------------- mixing
def mix(*layers):
    """mix((sig, offset_sec, gain_db), ...) - offsets may be negative only
    for the first layer."""
    total = 0
    for sig, off, _ in layers:
        total = max(total, n_of(off) + len(sig) if off else len(sig))
    out = np.zeros(total, np.float32)
    for sig, off, g in layers:
        o = n_of(off) if off else 0
        out[o:o + len(sig)] += sig * undb(g)
    return out


def gain(x, g_db):
    return x * undb(g_db)


def normalize(x, peak_to=0.9):
    p = peak(x)
    return x * (peak_to / p) if p > 1e-9 else x


def loudness(x, win=0.08):
    """Perceived punch: RMS of the loudest `win` window after a gentle
    low cut (so rumble doesn't count as loud)."""
    y = hp(x, 120, order=2)
    hop = n_of(win)
    if len(y) <= hop:
        return rms(y)
    c = np.convolve(np.square(y), np.ones(hop, np.float32) / hop, mode="valid")
    return float(np.sqrt(c.max()))


def level(x, target_db=-16.0, ceiling=0.95):
    """Match loudness to target (dB), then soft-limit to ceiling."""
    l = loudness(x)
    if l < 1e-9:
        return x
    y = x * (undb(target_db) / l)
    return limit(y, ceiling)


def limit(x, ceiling=0.95):
    """Smooth peak limiter: tanh knee above 70% of the ceiling."""
    k = 0.7 * ceiling
    a = np.abs(x)
    over = a > k
    if not over.any():
        return x
    y = x.copy()
    r = ceiling - k
    y[over] = np.sign(x[over]) * (k + r * np.tanh((a[over] - k) / r))
    return y


# ---------------------------------------------------------------- pitch/time
def speed(x, factor):
    """Varispeed: factor 1.2 = 20% faster AND higher (like tape)."""
    if abs(factor - 1.0) < 1e-3:
        return x.copy()
    # rational approximation of the factor for polyphase resampling
    up, down = _ratio(1.0 / factor)
    return sps.resample_poly(x, up, down).astype(np.float32)


def _ratio(r, max_den=400):
    from fractions import Fraction
    f = Fraction(r).limit_denominator(max_den)
    return f.numerator, f.denominator


def semis(n):
    return 2.0 ** (n / 12.0)


def reverse(x):
    return x[::-1].copy()


# ---------------------------------------------------------------- filters
def _sos(kind, f, order=2, q=None):
    nyq = SR / 2.0
    if kind == "band":
        lo, hi = f
        return sps.butter(order, [max(lo, 10) / nyq, min(hi, nyq * 0.98) / nyq],
                          btype="band", output="sos")
    return sps.butter(order, min(f, nyq * 0.98) / nyq, btype=kind, output="sos")


def lp(x, f, order=2):
    return sps.sosfilt(_sos("low", f, order), x).astype(np.float32)


def hp(x, f, order=2):
    return sps.sosfilt(_sos("high", f, order), x).astype(np.float32)


def bp(x, lo, hi, order=2):
    return sps.sosfilt(_sos("band", (lo, hi), order), x).astype(np.float32)


def _biquad(x, b, a):
    return sps.lfilter(b, a, x).astype(np.float32)


def peq(x, f, gain_db, q=1.0):
    """Peaking EQ (RBJ cookbook)."""
    A = 10 ** (gain_db / 40.0)
    w = 2 * np.pi * f / SR
    al = np.sin(w) / (2 * q)
    b = [1 + al * A, -2 * np.cos(w), 1 - al * A]
    a = [1 + al / A, -2 * np.cos(w), 1 - al / A]
    return _biquad(x, np.array(b) / a[0], np.array(a) / a[0])


def shelf(x, f, gain_db, high=True):
    """High (or low) shelf, slope 1 (RBJ cookbook)."""
    A = 10 ** (gain_db / 40.0)
    w = 2 * np.pi * f / SR
    cw, sw = np.cos(w), np.sin(w)
    al = sw / 2 * np.sqrt(2)
    sA = 2 * np.sqrt(A) * al
    if high:
        b = [A * ((A + 1) + (A - 1) * cw + sA), -2 * A * ((A - 1) + (A + 1) * cw),
             A * ((A + 1) + (A - 1) * cw - sA)]
        a = [(A + 1) - (A - 1) * cw + sA, 2 * ((A - 1) - (A + 1) * cw),
             (A + 1) - (A - 1) * cw - sA]
    else:
        b = [A * ((A + 1) - (A - 1) * cw + sA), 2 * A * ((A - 1) - (A + 1) * cw),
             A * ((A + 1) - (A - 1) * cw - sA)]
        a = [(A + 1) + (A - 1) * cw + sA, -2 * ((A - 1) + (A + 1) * cw),
             (A + 1) + (A - 1) * cw - sA]
    return _biquad(x, np.array(b) / a[0], np.array(a) / a[0])


def sweep_lp(x, f0, f1, steps=24):
    """Low-pass whose cutoff glides f0 -> f1 (block-wise, smooth enough)."""
    n = len(x)
    out = np.zeros_like(x)
    edges = np.linspace(0, n, steps + 1).astype(int)
    zi = None
    for k in range(steps):
        f = f0 * (f1 / f0) ** (k / max(steps - 1, 1))
        sos = _sos("low", f, 2)
        if zi is None:
            zi = sps.sosfilt_zi(sos) * 0.0
        seg, zi = sps.sosfilt(sos, x[edges[k]:edges[k + 1]], zi=zi)
        out[edges[k]:edges[k + 1]] = seg
    return out


# ---------------------------------------------------------------- dynamics/colour
def saturate(x, drive=2.0, mix_=1.0):
    y = np.tanh(x * drive) / np.tanh(drive)
    return (x * (1 - mix_) + y * mix_).astype(np.float32)


def transient(x, attack_db=4.0, sustain_db=0.0):
    """Simple transient shaper: boost/cut the onset vs the body using a
    fast/slow envelope difference."""
    a = np.abs(x)
    fast = sps.lfilter([1 - np.exp(-1 / (0.0015 * SR))],
                       [1, -np.exp(-1 / (0.0015 * SR))], a)
    slow = sps.lfilter([1 - np.exp(-1 / (0.025 * SR))],
                       [1, -np.exp(-1 / (0.025 * SR))], a)
    d = np.clip((fast - slow) / (slow + 1e-4), 0, 4) / 4.0
    g = undb(attack_db) ** d * undb(sustain_db) ** (1 - d)
    return (x * g).astype(np.float32)


# ---------------------------------------------------------------- space
@functools.lru_cache(maxsize=16)
def _ir(size, damp, seed):
    """A synthetic room impulse response: decaying, darkening noise."""
    t60 = 0.18 + 0.9 * size
    n = n_of(t60)
    rng = np.random.default_rng(seed)
    ir = rng.standard_normal(n).astype(np.float32)
    t = np.arange(n) / SR
    ir *= np.exp(-6.9 * t / t60)
    # darken over time (air absorption)
    ir = sweep_lp(ir, 9000 * (1 - 0.5 * damp), 1800 * (1 - 0.6 * damp), 16)
    ir[:n_of(0.008)] *= np.linspace(0, 1, n_of(0.008))       # pre-delay feel
    return ir / np.sqrt(np.sum(ir ** 2))


def reverb(x, wet_db=-16.0, size=0.25, damp=0.5, seed=7):
    """Convolve with a small arena-like room; returns dry + wet (longer)."""
    ir = _ir(round(size, 3), round(damp, 3), seed)
    w = sps.fftconvolve(x, ir).astype(np.float32)
    out = np.zeros(len(w), np.float32)
    out[:len(x)] += x
    return out + w * undb(wet_db)


def tame_low(x, f=150.0, hold=0.09, tau=0.07):
    """Stop low 'boing' ringing: the part of the sound below f Hz is let
    through for `hold` seconds after the loudest moment, then faded out
    quickly (zero-phase split, so nothing smears)."""
    sos = _sos("low", f, 2)
    low = sps.sosfiltfilt(sos, x).astype(np.float32)
    high = x - low
    t0 = int(np.argmax(np.abs(low))) + n_of(hold)
    env = np.ones(len(x), np.float32)
    if t0 < len(x):
        k = np.arange(len(x) - t0, dtype=np.float32) / SR
        env[t0:] = np.exp(-k / tau)
    return high + low * env


def tail_trim(x, floor_db=-58.0):
    """Drop the inaudible end of a tail (saves file size)."""
    thr = peak(x) * undb(floor_db)
    idx = np.nonzero(np.abs(x) > thr)[0]
    if not len(idx):
        return x
    return fade(x[:idx[-1] + n_of(0.02)], 0.0, 0.02)


# ---------------------------------------------------------------- synthesis
def rng(seed):
    return np.random.default_rng(seed)


def noise(t, color="white", seed=1):
    r = rng(seed)
    n = n_of(t)
    w = r.standard_normal(n).astype(np.float32)
    if color == "white":
        return w * 0.3
    if color == "pink":
        # Paul Kellet's economy filter
        b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
        a = [1, -2.494956002, 2.017265875, -0.522189400]
        return (sps.lfilter(b, a, w) * 3.0).astype(np.float32)
    # brown
    y = np.cumsum(w) * 0.02
    y = hp(y.astype(np.float32), 25, 1)
    return y / (peak(y) + 1e-9) * 0.5


def osc(f0, t, f1=None, shape="sine", curve="exp"):
    """Oscillator with a pitch glide f0 -> f1."""
    n = n_of(t)
    f1 = f0 if f1 is None else f1
    u = np.linspace(0, 1, n, dtype=np.float64)
    f = f0 * (f1 / f0) ** u if curve == "exp" else f0 + (f1 - f0) * u
    ph = np.cumsum(f) / SR
    ph -= np.floor(ph)
    if shape == "sine":
        y = np.sin(2 * np.pi * ph)
    elif shape == "saw":
        y = 2 * ph - 1
    elif shape == "square":
        y = np.where(ph < 0.5, 1.0, -1.0)
    else:
        y = 1 - 4 * np.abs(ph - 0.5)
    return y.astype(np.float32)


def adsr(x, a=0.005, d=0.1, s=0.6, r=0.1):
    n = len(x)
    e = np.ones(n, np.float32) * s
    na, nd, nr = min(n, n_of(a)), n_of(d), min(n, n_of(r))
    e[:na] = np.linspace(0, 1, na)
    e[na:na + nd] = np.linspace(1, s, len(e[na:na + nd]))
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return x * e


def modal(f, t, partials, seed=0, strike=0.002):
    """Modal synthesis: a struck object = a sum of exponentially decaying
    sine partials [(ratio, gain, decay_sec)] + a short strike click."""
    n = n_of(t)
    tt = np.arange(n, dtype=np.float64) / SR
    y = np.zeros(n, np.float64)
    r = rng(seed)
    for ratio, g, dec in partials:
        ph = r.uniform(0, 2 * np.pi)
        y += g * np.sin(2 * np.pi * f * ratio * tt + ph) * np.exp(-tt / dec)
    y = y.astype(np.float32)
    click = hp(noise(strike * 4, seed=seed), 2500) * decay_env(np.ones(n_of(strike * 4), np.float32), strike)
    y[:len(click)] += click * 0.6
    return y


def karplus(f, t, bright=0.5, seed=0):
    """Plucked string (Karplus-Strong), vectorised period by period."""
    n = n_of(t)
    p = max(2, int(SR / f))
    r = rng(seed)
    buf = r.uniform(-1, 1, p).astype(np.float64)
    buf -= buf.mean()
    out = np.empty(n + p, np.float64)
    out[:p] = buf
    keep = 0.990 + 0.009 * bright
    i = p
    while i < n + p:
        k = min(p - 1, n + p - i)
        out[i:i + k] = 0.5 * (out[i - p:i - p + k] + out[i - p + 1:i - p + k + 1]) * keep
        i += k
    return out[p:p + n].astype(np.float32)


def crackle(t, rate=180.0, seed=0, bright=4000.0, decay=None):
    """Sparse random clicks (fire, electricity, sparks)."""
    n = n_of(t)
    r = rng(seed)
    y = np.zeros(n, np.float32)
    count = int(rate * t)
    pos = r.integers(0, n, count)
    amp = r.uniform(0.2, 1.0, count).astype(np.float32)
    if decay:
        amp *= np.exp(-pos / (decay * SR)).astype(np.float32)
    np.add.at(y, pos, amp * r.choice([-1.0, 1.0], count))
    y = sps.lfilter([1.0], [1.0, -0.6], y).astype(np.float32)
    return hp(y, bright * 0.5) if bright else y


def ring(x, f):
    """Ring modulation (metallic / magical)."""
    t = np.arange(len(x)) / SR
    return (x * np.sin(2 * np.pi * f * t)).astype(np.float32)
