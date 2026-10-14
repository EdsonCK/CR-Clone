"""
Apply a balance result (per-card power factors relative to the ORIGINAL
stats) to src/cards.py, and write a changelog table.

    python tools/apply_balance.py tools/balance_data/final_factors.json

Only numeric stat fields are rewritten (hp, shield_hp, damage, spell_damage,
tower_damage, death/spawn/dash damage, heal amount, spawned-unit
multipliers); everything else in cards.py is left exactly as it was.
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import balance as B   # noqa: E402

CARDS_PY = os.path.join(ROOT, "src", "cards.py")


def _block_span(text, key):
    m = re.search(r'CardDef\(\s*"%s"\s*,' % re.escape(key), text)
    if not m:
        raise KeyError(key)
    i = m.start() + len("CardDef")
    depth = 0
    for j in range(i, len(text)):
        ch = text[j]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return m.start(), j          # j = index of closing paren
    raise ValueError(key)


def _fmt(v):
    if isinstance(v, float) and abs(v - round(v)) > 1e-9:
        return ("%.2f" % v).rstrip("0").rstrip(".")
    return str(int(round(v)))


def _set_num(block, field, value):
    pat = re.compile(r'(?<![\w])%s=([-\d.]+)' % field)
    if pat.search(block):
        return pat.sub("%s=%s" % (field, _fmt(value)), block, count=1)
    return None


def _set_tuple2(block, field, a, b):
    pat = re.compile(r'(?<![\w])%s=\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)' % field)
    if pat.search(block):
        return pat.sub("%s=(%s, %s)" % (field, _fmt(a), _fmt(b)), block, count=1)
    return None


def apply(factors):
    text = open(CARDS_PY).read()
    rows = []
    for key, f in sorted(factors.items()):
        if abs(f - 1.0) < 0.005:
            continue
        base = B.BASE[key]
        new = B.scaled_card(base, f)
        s, e = _block_span(text, key)
        block = text[s:e]
        extra = []
        change = []
        for field in ("hp", "shield_hp", "damage", "spell_damage", "tower_damage"):
            ov, nv = getattr(base, field), getattr(new, field)
            if ov is None or ov == 0:
                continue
            nv = int(round(nv))
            if nv == ov:
                continue
            nb = _set_num(block, field, nv)
            if nb is None:
                extra.append("%s=%d" % (field, nv))
            else:
                block = nb
            change.append("%s %s->%s" % (field, ov, nv))
        for field in ("death_damage", "spawn_damage", "dash_damage", "heal_on_attack"):
            ov, nv = getattr(base, field), getattr(new, field)
            if ov is None or ov == nv:
                continue
            nb = _set_tuple2(block, field, nv[0], int(round(nv[1])))
            if nb is not None:
                block = nb
                change.append("%s %s->%s" % (field, ov[1], int(round(nv[1]))))
        for field in ("sub_hp_mult", "sub_dmg_mult"):
            ov, nv = getattr(base, field), getattr(new, field)
            if abs(nv - ov) < 0.005:
                continue
            nb = _set_num(block, field, round(nv, 2))
            if nb is None:
                extra.append("%s=%s" % (field, _fmt(round(nv, 2))))
            else:
                block = nb
            change.append("%s %.2f->%.2f" % (field, ov, nv))
        if extra:
            block = block.rstrip() + ",\n            " + ", ".join(extra)
        text = text[:s] + block + text[e:]
        rows.append((key, f, change))
    open(CARDS_PY, "w").write(text)
    return rows


if __name__ == "__main__":
    data = json.load(open(sys.argv[1]))
    factors = {k: (v["f"] if isinstance(v, dict) else v) for k, v in data.items()}
    for k, f in list(factors.items()):        # second forms follow their card
        alt = B.BASE[k].alt_form if k in B.BASE else None
        if alt and alt[1] in B.BASE:
            factors[alt[1]] = f
    rows = apply(factors)
    for key, f, ch in rows:
        print("%-18s x%.2f  %s" % (key, f, "; ".join(ch)))
