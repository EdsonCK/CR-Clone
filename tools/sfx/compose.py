"""
============================================================================
  COMPOSE.PY  --  Music and jingles written for the sampled orchestra
============================================================================

Everything is written out by hand on a beat grid (orch.Song): a heroic
D-minor battle march, a bouncy G-major menu tune, and the short stings
(match start, victory, defeat, crown, King waking, double elixir,
overtime, abilities, evolution).
============================================================================
"""

import numpy as np

import dsp as D
import orch as O
from orch import midi as M

# chord tones (pitch classes relative to C) for the progressions below
CH = {"Dm": (2, 5, 9), "Bb": (10, 2, 5), "C": (0, 4, 7), "A": (9, 1, 4), "F": (5, 9, 0),
      "Gm": (7, 10, 2), "Am": (9, 0, 4), "G": (7, 11, 2), "Em": (4, 7, 11), "D": (2, 6, 9),
      "D7": (2, 6, 9), "Cmaj": (0, 4, 7), "E": (4, 8, 11)}


def tones(ch, lo, hi):
    """All notes of chord `ch` between midi lo and hi (inclusive)."""
    pcs = CH[ch]
    return [n for n in range(lo, hi + 1) if n % 12 in pcs]


def root(ch, octave):
    return 12 * (octave + 1) + CH[ch][0]


def mel(song, inst, notes, start=0.0, vel=0.8, pan=0.5, transpose=0):
    """notes: [(beat, 'D5', dur), ...] relative to `start`."""
    for b, n, d in notes:
        song.add(inst, start + b, M(n) + transpose, d, vel, pan)


# ======================================================================
#  BATTLE: "Siege of the Bridge" - D minor, 138 bpm, 32 bars
# ======================================================================
BATTLE_A = [(0, "A4", 1), (1, "D5", 1), (2, "C5", .5), (2.5, "A#4", .5), (3, "A4", 1),
            (4, "F4", 1.5), (5.5, "G4", .5), (6, "A4", 2),
            (8, "A#4", 1), (9, "A4", 1), (10, "G4", 1), (11, "F4", 1),
            (12, "G4", 3), (15, "E4", 1),
            (16, "A4", 1), (17, "D5", 1), (18, "E5", 1), (19, "F5", 1),
            (20, "E5", .5), (20.5, "D5", .5), (21, "C5", 1), (22, "D5", 2),
            (24, "A#4", 1), (25, "D5", 1), (26, "F5", 1), (27, "D5", 1),
            (28, "E5", 2), (30, "C#5", 1), (31, "A4", 1)]
BATTLE_B = [(0, "C5", .5), (.5, "C5", .5), (1, "C5", 1), (2, "F5", 2),
            (4, "E5", 1), (5, "D5", .5), (5.5, "C5", .5), (6, "G5", 2),
            (8, "F5", 1), (9, "E5", 1), (10, "D5", 1), (11, "A4", 1),
            (12, "D5", 3), (15, "A#4", 1),
            (16, "C5", .5), (16.5, "C5", .5), (17, "C5", 1), (18, "A5", 2),
            (20, "G5", 1), (21, "F5", .5), (21.5, "E5", .5), (22, "G5", 2),
            (24, "A#5", 1), (25, "A5", 1), (26, "G5", 1), (27, "F5", 1),
            (28, "E5", 2), (30, "A5", 2)]
BATTLE_C = [(0, "D5", 4), (4, "E5", 4), (8, "C5", 4), (12, "D5", 4),
            (16, "F5", 2), (18, "D5", 2), (20, "G5", 2), (22, "E5", 2),
            (24, "A#5", 2), (26, "G5", 2), (28, "A5", 2), (30, "C#5", 2)]
PROG_A = ["Dm", "Dm", "Bb", "C", "Dm", "Dm", "Bb", "A"]
PROG_B = ["F", "C", "Dm", "Bb", "F", "C", "Gm", "A"]
PROG_C = ["Bb", "C", "Am", "Dm", "Bb", "C", "Gm", "A"]


def battle_song(bpm=138):
    b = O.band()
    s = O.Song(bpm, 32)
    sections = [("A", PROG_A, 0), ("B", PROG_B, 8), ("A2", PROG_A, 16), ("C", PROG_C, 24)]
    for name, prog, bar0 in sections:
        full = name in ("A2", "B")
        soft = name == "C"
        for i, ch in enumerate(prog):
            bar = bar0 + i
            t = bar * 4
            # --- strings: spiccato 8th-note ostinato, cellos galloping
            arp = tones(ch, 62, 74)[:3]
            pat = [arp[0], arp[2], arp[1], arp[2]] * 2
            for k, n in enumerate(pat):
                s.add(b["vln_spic"], t + k * 0.5, n, 0.45, (0.55 if soft else 0.75) +
                      (0.12 if k % 2 == 0 else 0), pan=0.3)
            r = root(ch, 2)
            for off in ((0, 1, 1.5, 2, 3, 3.5) if not soft else (0, 2)):
                s.add(b["vc_spic"], t + off, r + 12, 0.45, 0.8 if off in (0, 2) else 0.6, pan=0.65)
            s.add(b["cb_pizz"], t, r, 1.0, 0.85, pan=0.6)
            s.add(b["cb_pizz"], t + 2, r, 1.0, 0.7, pan=0.6)
            # --- brass pads / accents
            pad = tones(ch, 53, 65)[:3]
            if not soft:
                s.chord(b["horn"], t, pad[:2], 2.0, 0.55, pan=0.42)
                s.chord(b["horn"], t + 2, pad[1:3], 2.0, 0.5, pan=0.42)
            else:
                s.chord(b["vla_sus"], t, tones(ch, 55, 67)[:3], 4.0, 0.5, pan=0.4)
            if full:
                s.chord(b["tbn"], t, [r + 12, r + 19], 1.5, 0.7, pan=0.58)
                s.add(b["tuba"], t, r, 3.5, 0.7, pan=0.55)
            # --- percussion
            if not soft:
                s.add(b["bd"], t, 36, 0.5, 0.85, pan=0.5)
                s.add(b["bd"], t + 2, 36, 0.5, 0.7, pan=0.5)
                s.add(b["snare"], t + 1, 38, 0.3, 0.6, pan=0.45)
                s.add(b["snare"], t + 3, 38, 0.3, 0.65, pan=0.45)
                if i % 4 == 3:                      # fill into the next phrase
                    for k in range(4):
                        s.add(b["snare"], t + 3 + k * 0.25, 38, 0.2, 0.35 + 0.15 * k, pan=0.45)
            s.add(b["timp"], t, 45, 1.0, 0.7 if not soft else 0.45, pan=0.5)
        s.add(b["crash"], bar0 * 4, 49, 2.0, 0.75 if name != "C" else 0.5, pan=0.6)
    # --- melodies
    mel(s, b["horn"], BATTLE_A, 0, 0.85, 0.38)
    mel(s, b["tpt"], BATTLE_B, 32, 0.8, 0.6)
    mel(s, b["horn"], BATTLE_B, 32, 0.6, 0.38, transpose=-12)
    mel(s, b["horn"], BATTLE_A, 64, 0.9, 0.38)
    mel(s, b["tpt"], BATTLE_A, 64, 0.65, 0.62, transpose=12)
    mel(s, b["glock"], [(x, n, d) for x, n, d in BATTLE_A], 64, 0.5, 0.7)
    mel(s, b["vln_sus"], BATTLE_C, 96, 0.7, 0.35)
    # last two bars: snare roll + timpani crescendo back into the loop
    for k in range(16):
        s.add(b["snare"], 30 * 4 + k * 0.25, 38, 0.2, 0.3 + 0.04 * k, pan=0.45)
    for k in range(8):
        s.add(b["timp"], 31 * 4 + k * 0.5, 45, 0.5, 0.4 + 0.07 * k, pan=0.5)
    return s


# ======================================================================
#  MENU: "Arena Gates" - G major, 104 bpm, 32 bars, playful
# ======================================================================
MENU_A = [(0, "D5", .5), (.5, "B4", .5), (1, "G4", 1), (2, "B4", 1), (3, "D5", 1),
          (4, "E5", 2), (6, "D5", .5), (6.5, "C5", .5), (7, "B4", 1),
          (8, "C5", 1), (9, "E5", 1), (10, "G5", 1), (11, "E5", 1),
          (12, "F#5", 2), (14, "D5", 2),
          (16, "G5", .5), (16.5, "F#5", .5), (17, "E5", .5), (17.5, "D5", .5), (18, "B4", 1),
          (19, "D5", 1),
          (20, "E5", .5), (20.5, "D5", .5), (21, "E5", 1), (22, "G5", 2),
          (24, "A5", 1), (25, "G5", 1), (26, "F#5", 1), (27, "A5", 1),
          (28, "G5", 3)]
MENU_B = [(0, "E5", 1), (1, "G5", 1), (2, "C6", 2),
          (4, "B5", 1), (5, "A5", 1), (6, "E5", 2),
          (8, "F5", 1), (9, "A5", 1), (10, "C6", 1), (11, "A5", 1),
          (12, "G5", 3),
          (16, "E5", .5), (16.5, "F5", .5), (17, "G5", 1), (18, "C6", 2),
          (20, "B5", .5), (20.5, "A5", .5), (21, "G5", 1), (22, "E5", 2),
          (24, "F#5", 1), (25, "A5", 1), (26, "D6", 2),
          (28, "C6", 1), (29, "B5", 1), (30, "A5", 2)]
MPROG_A = ["G", "Em", "Cmaj", "D", "G", "Em", "Am", "G"]
MPROG_B = ["Cmaj", "Am", "F", "Cmaj", "Cmaj", "Am", "D", "D7"]


def menu_song(bpm=104):
    b = O.band()
    s = O.Song(bpm, 32)
    sections = [("A", MPROG_A, 0), ("A2", MPROG_A, 8), ("B", MPROG_B, 16), ("A3", MPROG_A, 24)]
    for name, prog, bar0 in sections:
        for i, ch in enumerate(prog):
            t = (bar0 + i) * 4
            r = root(ch, 2)
            # walking pizzicato bass: root, fifth
            s.add(b["cb_pizz"], t, r, 1, 0.8, pan=0.55)
            s.add(b["vc_pizz"], t + 1, r + 7 + 12 if r + 19 <= 70 else r + 7, 1, 0.6, pan=0.6)
            s.add(b["cb_pizz"], t + 2, r + 7, 1, 0.7, pan=0.55)
            s.add(b["vc_pizz"], t + 3, r + 12, 1, 0.6, pan=0.6)
            # off-beat pizzicato chords
            ct = tones(ch, 60, 72)[:3]
            for off in (0.5, 1.5, 2.5, 3.5):
                s.chord(b["vln_pizz"], t + off, ct, 0.4, 0.45, pan=0.35)
            # harp arpeggio up
            arp = tones(ch, 55, 79)[:6]
            for k, n in enumerate(arp[:4] if name == "A" else arp):
                s.add(b["harp"], t + k * 0.5 + (2 if name == "A" else 0), n, 0.5, 0.45, pan=0.7)
            # light percussion
            for off in (1, 3):
                s.add(b["tamb"], t + off, 54, 0.3, 0.5 if name != "A" else 0.35, pan=0.6)
            if i % 2 == 0:
                s.add(b["tri"], t, 81, 1, 0.4, pan=0.75)
            if name in ("A2", "A3"):
                s.chord(b["horn"], t, tones(ch, 55, 67)[:2], 3.5, 0.4, pan=0.4)
        if bar0 % 16 == 0:
            s.add(b["timp"], bar0 * 4, 45, 1, 0.5, pan=0.5)
    mel(s, b["xylo"], MENU_A, 0, 0.7, 0.6)
    mel(s, b["glock"], MENU_A, 32, 0.7, 0.62)
    mel(s, b["vln_sus"], MENU_A, 32, 0.45, 0.35, transpose=-12)
    mel(s, b["xylo"], MENU_B, 64, 0.7, 0.6)
    mel(s, b["horn"], MENU_B, 64, 0.5, 0.4, transpose=-12)
    mel(s, b["xylo"], MENU_A, 96, 0.7, 0.6)
    mel(s, b["glock"], MENU_A, 96, 0.55, 0.65)
    return s


def render_song(s, loud=-17.0, wet=-14.0):
    x = s.render(loop=True)
    x = O.hall(x, wet, 1.7, loop=True)
    return O.master(x, loud)


# ======================================================================
#  JINGLES & STINGS
# ======================================================================
def sting(bpm, beats, build, loud=-15.0, wet=-13.0):
    b = O.band()
    s = O.Song(bpm, 1, beats)
    build(s, b)
    x = s.render(loop=False, tail=2.5)
    x = O.hall(x, wet, 1.5, loop=False)
    x = O.master(x, loud)
    # trim the silent end
    m = np.abs(x).max(axis=1)
    idx = np.nonzero(m > m.max() * 0.004)[0]
    end = idx[-1] + D.n_of(0.05) if len(idx) else len(x)
    return O.fade2(x[:end], 0.0, 0.25)


def j_match_start(s, b):
    # brass fanfare: D major call + timpani & cymbal
    for bt, n, d in [(0, "A4", .5), (.5, "A4", .5), (1, "D5", 1), (2, "F#5", .75), (2.75, "E5", .25),
                     (3, "A5", 2.5)]:
        s.add(b["tpt"], bt, M(n), d, 0.9, 0.55)
        s.add(b["horn"], bt, M(n) - 12, d, 0.7, 0.4)
    s.chord(b["tbn"], 3, [M("D3"), M("A3")], 2.5, 0.8, 0.6)
    s.add(b["tuba"], 3, M("D2"), 2.5, 0.8, 0.5)
    for k in range(6):
        s.add(b["snare"], 2 + k * 0.17, 38, 0.2, 0.4 + 0.08 * k, 0.45)
    s.add(b["timp"], 3, 45, 1, 0.9, 0.5)
    s.add(b["crash"], 3, 49, 2, 0.8, 0.6)


def j_victory(s, b):
    seq = [(0, "C5", .5), (.5, "E5", .5), (1, "G5", .5), (1.5, "C6", 1.5), (3, "A5", .5),
           (3.5, "B5", .5), (4, "C6", 3)]
    for bt, n, d in seq:
        s.add(b["tpt"], bt, M(n) - 12, d, 0.9, 0.55)
        s.add(b["glock"], bt, M(n), d, 0.6, 0.7)
    for bt, ch in ((0, ["C4", "E4", "G4"]), (1.5, ["E4", "G4", "C5"]), (4, ["C4", "E4", "G4", "C5"])):
        s.chord(b["horn"], bt, [M(n) - 12 for n in ch], 3 if bt == 4 else 1.5, 0.75, 0.4)
        s.chord(b["vln_sus"], bt, [M(n) for n in ch], 3 if bt == 4 else 1.5, 0.6, 0.35)
    s.add(b["tuba"], 4, M("C2"), 3, 0.8, 0.5)
    for k in range(8):
        s.add(b["snare"], 3 + k * 0.125, 38, 0.15, 0.4 + 0.06 * k, 0.45)
    s.add(b["timp"], 4, 45, 1, 0.9, 0.5)
    s.add(b["crash"], 4, 49, 2, 0.85, 0.6)
    for k, n in enumerate(["C5", "E5", "G5", "C6", "E6", "G6"]):
        s.add(b["harp"], 4 + k * 0.12, M(n), 1, 0.6, 0.7)


def j_defeat(s, b):
    seq = [(0, "G4", 1), (1, "F4", 1), (2, "D#4", 1), (3, "D4", 3)]
    for bt, n, d in seq:
        s.add(b["horn"], bt, M(n) - 12, d, 0.7, 0.45)
        s.add(b["vln_sus"], bt, M(n), d, 0.5, 0.35)
    s.chord(b["vc_sus"], 3, [M("G2"), M("D3")], 3, 0.6, 0.6)
    s.add(b["tuba"], 3, M("G1"), 3, 0.6, 0.5)
    s.add(b["timp"], 3, 45, 1, 0.5, 0.5)


def j_crown(s, b):
    for k, n in enumerate(["G5", "B5", "D6", "G6"]):
        s.add(b["glock"], k * 0.18, M(n), 1, 0.8, 0.6)
        s.add(b["harp"], k * 0.18, M(n) - 12, 1, 0.6, 0.4)
    s.chord(b["tpt"], 0.6, [M("G4"), M("D5")], 1.2, 0.7, 0.55)
    s.add(b["tri"], 0.6, 81, 1, 0.6, 0.7)


def j_king_wake(s, b):
    s.chord(b["horn"], 0, [M("D3"), M("A3")], 2.5, 0.85, 0.45)
    s.chord(b["tbn"], 0, [M("D2"), M("A2")], 2.5, 0.85, 0.55)
    s.add(b["tuba"], 0, M("D1"), 2.5, 0.8, 0.5)
    s.add(b["timp"], 0, 45, 1, 0.9, 0.5)
    s.add(b["timp"], 1, 45, 1, 0.7, 0.5)
    s.add(b["crash"], 0, 49, 2, 0.6, 0.6)


def j_double_elixir(s, b):
    for k, n in enumerate(["E5", "A5", "C#6", "E6"]):
        s.add(b["glock"], k * 0.25, M(n), 1, 0.8, 0.65)
        s.add(b["harp"], k * 0.25, M(n) - 12, 1, 0.6, 0.4)
    s.chord(b["tpt"], 1.0, [M("A4"), M("E5")], 1.0, 0.7, 0.55)
    s.chord(b["horn"], 1.0, [M("A3"), M("C#4")], 1.2, 0.6, 0.4)
    s.add(b["tamb"], 1.0, 54, 0.5, 0.7, 0.6)


def j_overtime(s, b):
    s.add(b["timp"], 0, 45, 1, 0.9, 0.5)
    for k in range(10):
        s.add(b["timp"], 0.5 + k * 0.12, 45, 0.2, 0.4 + 0.05 * k, 0.5)
    s.chord(b["tbn"], 1.8, [M("D3"), M("F3"), M("A3")], 2.0, 0.85, 0.55)
    s.chord(b["horn"], 1.8, [M("D4"), M("A4")], 2.0, 0.8, 0.4)
    s.add(b["tuba"], 1.8, M("D2"), 2.0, 0.8, 0.5)
    s.add(b["crash"], 1.8, 49, 2, 0.8, 0.6)


def j_ability(s, b):
    for k, n in enumerate(["D5", "F#5", "A5", "D6"]):
        s.add(b["harp"], k * 0.1, M(n), 1, 0.7, 0.4 + 0.1 * k)
    s.chord(b["vln_sus"], 0.3, [M("D5"), M("A5")], 1.0, 0.5, 0.35)
    s.add(b["glock"], 0.4, M("A6"), 1, 0.6, 0.7)


def j_hero_ability(s, b):
    for bt, n, d in [(0, "G4", .33), (.33, "C5", .33), (.66, "E5", .33), (1, "G5", 1.5)]:
        s.add(b["tpt"], bt, M(n), d, 0.85, 0.55)
    s.chord(b["horn"], 1, [M("C4"), M("E4"), M("G4")], 1.5, 0.75, 0.4)
    s.add(b["timp"], 1, 45, 1, 0.8, 0.5)
    s.add(b["glock"], 1, M("G6"), 1, 0.6, 0.7)


def j_evo_deploy(s, b):
    # an Evolution takes the field: a short, soft heroic horn call (rising
    # fifth, then the octave) over a gentle timpani tap - valiant, not loud
    for bt, n, d, v in ((0, "A3", 0.4, 0.55), (0.4, "E4", 0.4, 0.6), (0.8, "A4", 1.1, 0.62)):
        s.add(b["horn"], bt, M(n), d, v, 0.45)
    s.chord(b["horn"], 0.8, [M("C#4"), M("E4")], 1.1, 0.35, 0.4)
    s.add(b["timp"], 0.8, 45, 0.6, 0.4, 0.5)
    s.add(b["glock"], 0.8, M("A5"), 0.8, 0.25, 0.6)


def j_wave(s, b):
    # Levels / Endless: the next wave is coming - two soft war-drum hits and
    # a quiet low horn (mostly percussion, so it sits under the music)
    s.add(b["bd"], 0, 36, 0.5, 0.75, 0.5)
    s.add(b["timp"], 0, 45, 1.0, 0.55, 0.5)
    s.add(b["bd"], 0.5, 36, 0.5, 0.6, 0.5)
    s.add(b["timp"], 0.5, 45, 1.0, 0.45, 0.5)
    s.add(b["horn"], 0.5, M("D3"), 1.2, 0.45, 0.42)


def j_wave_boss(s, b):
    # a boss wave: three building timpani hits and a low, darker brass swell
    for k, v in enumerate((0.5, 0.6, 0.8)):
        s.add(b["timp"], k * 0.33, 45, 0.6, v, 0.5)
        s.add(b["bd"], k * 0.33, 36, 0.4, v * 0.8, 0.5)
    s.chord(b["tbn"], 1.0, [M("D2"), M("A2")], 1.6, 0.55, 0.55)
    s.chord(b["horn"], 1.0, [M("D3"), M("F3")], 1.6, 0.45, 0.42)


JINGLES = {
    "match_start": (120, 6, j_match_start, -14),
    "wave": (120, 2, j_wave, -23),
    "wave_boss": (110, 3, j_wave_boss, -20),
    "victory": (120, 8, j_victory, -14),
    "defeat": (84, 7, j_defeat, -17),
    "crown": (120, 3, j_crown, -16),
    "king_wake": (96, 4, j_king_wake, -15),
    "double_elixir": (120, 3, j_double_elixir, -16),
    "overtime": (120, 5, j_overtime, -14),
    "ability": (140, 2, j_ability, -18),
    "hero_ability": (130, 3, j_hero_ability, -16),
    "evo_deploy": (140, 3, j_evo_deploy, -22),
}


def jingle(name):
    bpm, beats, build, loud = JINGLES[name]
    return sting(bpm, beats, build, loud)
