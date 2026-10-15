"""
SHEET.PY - draw waveform + spectrogram thumbnails of sounds into one PNG
(a way to check renders by eye):

    sheet(list_of_(label, signal), "out.png")
    python tools/sfx/sheet.py out.png file1.ogg file2.wav ...
"""

import sys

import numpy as np

import dsp


def sheet(items, path, cols=4, max_t=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    n = len(items)
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows * 2, cols, figsize=(cols * 3.2, rows * 2.6),
                             gridspec_kw={"height_ratios": [1, 2] * rows}, squeeze=False)
    T = max_t or max(dsp.secs(x) for _, x in items)
    for k in range(rows * cols):
        r, c = divmod(k, cols)
        aw, asp = axes[r * 2][c], axes[r * 2 + 1][c]
        for a in (aw, asp):
            a.set_xticks([])
            a.set_yticks([])
        if k >= n:
            aw.axis("off")
            asp.axis("off")
            continue
        label, x = items[k]
        t = np.arange(len(x)) / dsp.SR
        aw.plot(t, x, lw=0.4, color="#246")
        aw.set_xlim(0, T)
        aw.set_ylim(-1, 1)
        aw.set_title("%s  %.0fms  L%.0f" % (label, dsp.secs(x) * 1000, dsp.db(dsp.loudness(x))),
                     fontsize=7)
        if len(x) > 512:
            asp.specgram(x + 1e-7, NFFT=512, Fs=dsp.SR, noverlap=384, cmap="magma",
                         vmin=-120, vmax=-20)
        asp.set_xlim(0, T)
        asp.set_ylim(0, 16000)
    fig.tight_layout(pad=0.3)
    fig.savefig(path, dpi=90)
    plt.close(fig)


if __name__ == "__main__":
    out = sys.argv[1]
    sheet([(p.split("/")[-1][:24], dsp.load(p)) for p in sys.argv[2:]], out)
