"""
============================================================================
  RENDER.PY  --  Build the game's attack sounds from the CC0 recordings
============================================================================

    pip install numpy scipy soundfile py7zr     (only needed to REBUILD)
    python tools/sfx/render.py --fetch          download the source packs
    python tools/sfx/render.py                  render everything
    python tools/sfx/render.py knight pekka     render just these units
    python tools/sfx/render.py --sheet out.png knight   + a spectrogram sheet

Writes assets/sounds/<key>_attack_1..3.ogg (and <key>_hit_1..3.ogg for
splash projectiles) plus assets/sounds/CREDITS.txt. The game itself needs
none of this - it just plays the finished .ogg files.
============================================================================
"""

import os
import sys
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import dsp as D          # noqa: E402
import sources as S      # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "assets", "sounds")
VARIANTS = 3
MAX_LEN = 1.4


def finish(y, loud=-15.0, room=-21.0):
    y = D.hp(y, 45, 2)
    y = D.tame_low(y)
    y = D.reverb(y, room, size=0.22, damp=0.5)
    y = D.level(y, loud, 0.86)
    y = D.tail_trim(y, -56)
    if D.secs(y) > MAX_LEN:
        y = D.shorten(y, MAX_LEN, 0.15)
    return D.fade(y, 0.0008, 0.02)


def _job(args):
    table, key, v = args
    import attack as A
    fn = (A.ATTACK if table == "attack" else A.HIT)[key]
    try:
        y = finish(fn(v), A.LOUD.get(key, -15.0), A.ROOM.get(key, -21.0))
    except Exception as ex:                      # report, keep going
        return key, table, v, "ERROR %s: %r" % (type(ex).__name__, ex)
    path = os.path.join(OUT, "%s_%s_%d.ogg" % (key, table, v + 1))
    D.write(path, y)
    return key, table, v, path


def jobs(keys=None):
    import attack as A
    out = []
    for table, reg in (("attack", A.ATTACK), ("hit", A.HIT)):
        for key in sorted(reg):
            if keys and key not in keys:
                continue
            for v in range(VARIANTS):
                out.append((table, key, v))
    return out


def credits():
    lines = ["Sound effects: attack sounds are built from these public-domain",
             "(CC0) recordings, processed with tools/sfx (numpy). CC0 needs no",
             "credit - thank you anyway!", ""]
    for key, (title, author, _) in S.PACKS.items():
        lines.append("  %s - %s  (%s)" % (title, author, S.page(key)))
    lines += ["", "Every other sound is synthesised by src/sounds.py."]
    with open(os.path.join(OUT, "CREDITS.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    args = sys.argv[1:]
    if "--fetch" in args:
        S.fetch()
        args.remove("--fetch")
    sheet_path = None
    if "--sheet" in args:
        i = args.index("--sheet")
        sheet_path = args[i + 1]
        del args[i:i + 2]
    todo = jobs(set(args) or None)
    os.makedirs(OUT, exist_ok=True)
    with Pool(max(1, (os.cpu_count() or 2))) as pool:
        done = pool.map(_job, todo, chunksize=2)
    errs = [d for d in done if d[3].startswith("ERROR")]
    for e in errs:
        print(*e)
    done = [d for d in done if not d[3].startswith("ERROR")]
    print("rendered %d files" % len(done))
    if not args:
        credits()
    if sheet_path:
        import sheet
        sheet.sheet([("%s %s%d" % (k, t[0], v + 1), D.load(p)) for k, t, v, p in done],
                    sheet_path, cols=3, max_t=1.0)


if __name__ == "__main__":
    main()
