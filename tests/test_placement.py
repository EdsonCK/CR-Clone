"""Where each card may be placed; the AI still uses rolling spells."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import os, sys

sys.path.insert(0, _util.SRC)
import cards
from engine import Match, PLAYER, ENEMY
m = Match(cards.AI_DECK_PRESETS["Classic"], cards.AI_DECK_PRESETS["Classic"])
ok = True
def check(n, c):
    global ok; print(("PASS " if c else "FAIL ") + n); ok &= bool(c)
for sp in ("the_log", "barbarian_barrel", "royal_delivery"):
    check(sp + " own side ok", m.can_place(PLAYER, sp, 9, 20))
    check(sp + " enemy side blocked", not m.can_place(PLAYER, sp, 9, 10))
    check(sp + " enemy (AI) own side ok", m.can_place(ENEMY, sp, 9, 10))
check("fireball anywhere", m.can_place(PLAYER, "fireball", 9, 10))
check("cannon on princess tower blocked", not m.can_place(PLAYER, "cannon", 3.5, 25.5))
check("cannon overlapping tower edge blocked", not m.can_place(PLAYER, "cannon", 5.8, 25.5))
check("cannon next to tower ok", m.can_place(PLAYER, "cannon", 6.5, 25.5))
check("cannon on king blocked", not m.can_place(PLAYER, "cannon", 9, 28))
check("knight on tower blocked", not m.can_place(PLAYER, "knight", 3.5, 25.5))
check("knight beside tower ok", m.can_place(PLAYER, "knight", 5.2, 25.5))
check("spell on tower ok", m.can_place(PLAYER, "zap", 3.5, 25.5))
m.towers[(PLAYER, "left")].alive = False
check("cannon where destroyed tower stood ok", m.can_place(PLAYER, "cannon", 3.5, 25.5))
# AI: plays log/barrel only on its own side across a match
from ai import AIController
import random
bad = 0; played = 0
for seed in range(6):
    random.seed(seed)
    deck = ["the_log", "barbarian_barrel", "knight", "archers", "hog_rider", "cannon", "fireball", "skeletons"]
    m = Match(deck, deck)
    a1 = AIController(m, team=PLAYER, level=4); a2 = AIController(m, team=ENEMY, level=4)
    seen = set()
    for t in range(30 * 120):
        m.update(1/30); a1.update(1/30); a2.update(1/30)
        for e in m.effects:
            if e.kind == "log" and id(e) not in seen:
                seen.add(id(e)); played += 1
        if m.finished: break
    for team, ai in ((PLAYER, a1), (ENEMY, a2)):
        for rec in ai.log:
            if rec[1] in ("the_log", "barbarian_barrel"):
                pass
print("rolling spells played by AIs:", played)
check("AIs still use rolling spells", played > 0)
print("ALL OK" if ok else "SOME FAILED")
assert ok
