"""
Write BALANCE.md: every card's benchmark performance before / after and its
stat changes.

    python tools/balance_report.py BEFORE_MATRIX.json AFTER_MATRIX.json \\
                                   FACTORS.json [ROUNDS_TEXT]
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import balance as B   # noqa: E402


def stat_line(key, f):
    base = B.BASE[key]
    new = B.scaled_card(base, f)
    parts = []
    for field, label in (("hp", "HP"), ("shield_hp", "shield"), ("damage", "dmg"),
                         ("spell_damage", "dmg"), ("tower_damage", "tower dmg")):
        ov, nv = getattr(base, field), getattr(new, field)
        if ov and int(round(nv)) != ov:
            parts.append("%s %d → %d" % (label, ov, int(round(nv))))
    for field, label in (("death_damage", "death dmg"), ("spawn_damage", "landing dmg"),
                         ("dash_damage", "jump dmg"), ("heal_on_attack", "heal")):
        ov, nv = getattr(base, field), getattr(new, field)
        if ov and int(round(nv[1])) != ov[1]:
            parts.append("%s %d → %d" % (label, ov[1], int(round(nv[1]))))
    if abs(new.sub_hp_mult - 1) > 0.005 or abs(new.sub_dmg_mult - 1) > 0.005:
        parts.append("spawned units HP x%.2f / dmg x%.2f" % (new.sub_hp_mult, new.sub_dmg_mult))
    return ", ".join(parts) if parts else "-"


def main(before_p, after_p, factors_p, notes=""):
    before = json.load(open(before_p))
    after = json.load(open(after_p))
    fac = json.load(open(factors_p))
    fac = {k: (v["f"] if isinstance(v, dict) else v) for k, v in fac.items()}
    lines = ["# Card balance (v0.3.0)", "",
             "Every card was benchmarked with `tools/balance.py` (see its docstring for",
             "the full method) and tuned over several frozen-snapshot rounds. A card's",
             "**performance** is its average elixir gain per engagement against the",
             "whole card pool (equal-elixir fights, both attacking and defending, weighted",
             "toward similar-cost cards, extremes trimmed). Damage spells are scored on",
             "their best 40% of targets. 0 = a perfectly fair card.", ""]
    if notes:
        lines += [notes, ""]
    lines += ["| Card | Cost | Before | After | Power | Stat changes |",
              "|---|---|---|---|---|---|"]
    rows = []
    for key in B.pool():
        c = B.BASE[key]
        pb = before.get(key, {}).get("perf", 0.0)
        pa = after.get(key, {}).get("perf", 0.0)
        f = fac.get(key, 1.0)
        rows.append((abs(pb), key, c, pb, pa, f))
    rows.sort(key=lambda r: r[1])
    for _, key, c, pb, pa, f in rows:
        if B.is_damage_spell(key):
            pb -= B.SPELL_TARGET
            pa -= B.SPELL_TARGET
        flag = ""
        if f <= B.F_MIN + 1e-3 or f >= B.F_MAX - 1e-3:
            flag = " ⚠"
        lines.append("| %s | %d | %+.2f | %+.2f | x%.2f%s | %s |" % (
            c.name, c.elixir, pb, pa, f, flag, stat_line(key, f)))
    import statistics
    spread_b = statistics.pstdev(r[3] for r in rows)
    spread_a = statistics.pstdev(r[4] for r in rows)
    lines += ["", "Spread of card performance (standard deviation): **%.2f → %.2f** elixir."
              % (spread_b, spread_a), ""]
    with open(os.path.join(ROOT, "BALANCE.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote BALANCE.md; spread %.2f -> %.2f" % (spread_b, spread_a))


if __name__ == "__main__":
    B.SPELL_TARGET = float(os.environ.get("SPELL_TARGET", "0"))
    main(*sys.argv[1:4], notes=(sys.argv[4] if len(sys.argv) > 4 else ""))
