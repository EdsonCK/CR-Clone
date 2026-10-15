"""
PROBE.PY - describe source recordings (to pick material without ears):

    python tools/sfx/probe.py PACK [substring ...]

For every matching file: length, and each separate event in it with its
length, level, brightness (spectral centroid), noisiness (flatness, 0 =
pure tone .. 1 = white noise), attack time and pitch (if tonal).
"""

import sys

import numpy as np

import dsp
import sources


def describe(x):
    if not len(x):
        return "empty"
    x = dsp.hp(x, 90, 2)
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x)), n=1 << int(np.ceil(np.log2(max(len(x), 2048))))))
    freqs = np.fft.rfftfreq((len(spec) - 1) * 2, 1 / dsp.SR)
    p = spec ** 2 + 1e-12
    cen = float(np.sum(freqs * p) / np.sum(p))
    flat = float(np.exp(np.mean(np.log(p[1:]))) / np.mean(p[1:]))
    low = float(np.sum(p[freqs < 250]) / np.sum(p))
    env = dsp.envelope(x, 0.002)
    att = float(np.argmax(env) * 2)
    pk = int(np.argmax(spec[freqs > 60])) if (freqs > 60).any() else 0
    f0 = float(freqs[freqs > 60][pk]) if pk else 0.0
    tonal = spec.max() / (np.mean(spec) + 1e-9)
    return ("%5.0fms pk%5.1fdB loud%5.1f cen%5.0fHz flat%.2f low%.2f att%4.0fms f0~%5.0f%s" %
            (dsp.secs(x) * 1000, dsp.db(dsp.peak(x)), dsp.db(dsp.loudness(x)), cen, flat,
             low, att, f0, " TONAL" if tonal > 60 else ""))


def main():
    args = sys.argv[1:]
    brief = "-b" in args
    args = [a for a in args if a != "-b"]
    pack = args[0]
    subs = [s.lower() for s in args[1:]]
    for name in sources.listing(pack):
        if subs and not any(s in name for s in subs):
            continue
        x = dsp.load(sources.find(pack, name))
        segs = dsp.segments(x)
        if brief:
            print("%-34s %5.2fs %2dev | %s" % (name[:34], dsp.secs(x), len(segs),
                                              describe(dsp.event(x, 0))))
            continue
        print("%-44s %6.2fs  %d event(s)" % (name[:44], dsp.secs(x), len(segs)))
        for i, (a, b) in enumerate(segs[:12]):
            print("    #%-2d @%5.2fs %s" % (i, a, describe(dsp.event(x, i))))


if __name__ == "__main__":
    main()
