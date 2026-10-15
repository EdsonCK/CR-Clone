"""
============================================================================
  MUSIC.PY  --  Builds the extra music tracks and the jingles
============================================================================

    python tools/sfx/music.py            (after render.py --fetch)

Menu and battle each rotate through 4 themes in the game. Themes 1-2 are
synthesised by src/sounds.py; this script writes themes 3-4:

  menu3    "Minstrel Dance"     - RandomMind (CC0 recording, loop version)
  menu4    "Arena Gates"        - composed here for the sampled orchestra
  battle3  "Battle Theme A"     - cynicmusic (CC0 recording)
  battle4  "Siege of the Bridge" - composed here
  final3/4 the battle themes a little faster and higher, for the last minute

plus the jingles (match start, victory, defeat, crown, King waking, double
elixir, overtime, abilities, evolution) composed for the sampled orchestra
(tools/sfx/compose.py). Music is stereo .ogg at 44.1 kHz.
============================================================================
"""

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import compose as C      # noqa: E402
import dsp as D          # noqa: E402
import orch as O         # noqa: E402
import sources as S      # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "assets", "sounds")
LOUD = -14.0             # music RMS, matching the synthesised themes
FINAL_SPEED = 1.10       # last-minute version: 10% faster (and a bit higher)


def load_stereo(pack, name):
    return O.load2(S.find(pack, name))


def loop_crossfade(x, fade=1.2):
    """Make a full-length track loop: its last `fade` seconds blend into
    its start (equal power), and the file gets shorter by that much."""
    n = D.n_of(fade)
    if len(x) <= 3 * n:
        return x
    head, tail = x[:n], x[-n:]
    t = np.linspace(0, np.pi / 2, n, dtype=np.float32)[:, None]
    blend = head * np.sin(t) + tail * np.cos(t)
    return np.concatenate([blend, x[n:-n]]).astype(np.float32)


def trim_silence(x, floor_db=-50.0):
    m = np.abs(x).max(axis=1)
    thr = m.max() * D.undb(floor_db)
    idx = np.nonzero(m > thr)[0]
    return x[idx[0]:idx[-1] + 1] if len(idx) else x


def recorded(pack, name, is_loop):
    x = load_stereo(pack, name)
    if not is_loop:
        x = loop_crossfade(trim_silence(x))
    return O.master(x, LOUD, 0.95)


def write_track(key, x):
    O.write2(os.path.join(OUT, "music_%s.ogg" % key), x, quality=0.45)


def build_music():
    tracks = {
        "menu3": recorded("medieval-minstrel-dance", "Loop_Minstrel_Dance_0.wav", True),
        "menu4": O.master(C.render_song(C.menu_song()), LOUD - 1.0),
        "battle3": recorded("battle-theme-a", "battleThemeA.mp3", False),
        "battle4": O.master(C.render_song(C.battle_song()), LOUD),
    }
    for key, x in tracks.items():
        write_track(key, x)
        print("music_%s  %.1fs" % (key, len(x) / D.SR))
        if key.startswith("battle"):
            fin = O.speed2(x, FINAL_SPEED)
            write_track(key.replace("battle", "final"), fin)
            print("music_%s  %.1fs" % (key.replace("battle", "final"), len(fin) / D.SR))


def build_jingles():
    for name in C.JINGLES:
        x = C.jingle(name)
        O.write2(os.path.join(OUT, name + ".ogg"), x)
        print("%s  %.2fs" % (name, len(x) / D.SR))


if __name__ == "__main__":
    build_music()
    build_jingles()
