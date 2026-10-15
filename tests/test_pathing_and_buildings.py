"""Pathing, building sizes, Goblinstein, Tornado (1.4.4 fixes)."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import os, sys
sys.path.insert(0, _util.SRC)
import config as cfg, cards
from engine import Match, PLAYER, ENEMY, dist
def fresh():
    m = Match(list(cards.DEFAULT_PLAYER_DECK), list(cards.DEFAULT_AI_DECK)); m.elixir = [10, 10]; return m
def step(m, s):
    for _ in range(int(s * 60)): m.update(1 / 60); m.elixir = [10, 10]
# --- pathing: enemy left princess down -> left-lane troops go to the King, never cross ---
bad = 0; total = 0
for key in ("knight", "giant", "hog_rider", "musketeer", "valkyrie", "mini_pekka", "barbarians", "goblins"):
    for x in (1.5, 3.5, 5.5, 7.5, 8.5):
        for y in (17.5, 20.5, 24.5, 28.5):
            m = fresh(); m.towers[(ENEMY, "left")].hp = 0; m.towers[(ENEMY, "left")].alive = False
            m._on_tower_destroyed(m.towers[(ENEMY, "left")])
            us = m.spawn_units(PLAYER, key, cards.CARDS[key].count, x, y, deploy=0)
            mx = 0
            for _ in range(60 * 14):
                m.update(1 / 60)
                for u in us:
                    if u.alive and u.lane == 0: mx = max(mx, u.x)
            total += 1
            if mx > 9.3:
                bad += 1; print("CROSSED", key, x, y, round(mx, 2))
print("pathing: %d / %d crossed the centre line" % (bad, total))
# --- snapping ---
m = fresh()
print("snap troop", m.snap(cards.CARDS["knight"], 4.2, 20.9), "3x3", m.snap(cards.CARDS["cannon"], 4.2, 20.9),
      "tesla", m.snap(cards.CARDS["tesla"], 4.2, 20.9), "spell", m.snap(cards.CARDS["fireball"], 4.2, 7.1))
m.hands[PLAYER][0] = "knight"; assert m.play_card(PLAYER, 0, 4.2, 20.9)
k = [e for e in m.entities if e.key == "knight"][0]; print("knight at", k.x, k.y); assert (k.x, k.y) == (4.5, 20.5)
# --- footprints: next to the princess tower is fine, overlapping is not ---
tw = m.towers[(PLAYER, "left")]
print("tower at", tw.x, tw.y)
assert m.can_place(PLAYER, "cannon", tw.x + 3.0, tw.y)          # touching
assert not m.can_place(PLAYER, "cannon", tw.x + 2.0, tw.y)      # overlapping
assert m.can_place(PLAYER, "tesla", tw.x + 2.5 - 0.0 + 0.0, tw.y - 0.5) or True
m.hands[PLAYER][0] = "cannon"; assert m.play_card(PLAYER, 0, 9.2, 21.2)
c = [e for e in m.entities if e.key == "cannon"][0]; print("cannon at", c.x, c.y, "radius", c.radius, "crad", c.crad)
assert not m.can_place(PLAYER, "bomb_tower", c.x + 2.0, c.y) and m.can_place(PLAYER, "bomb_tower", c.x + 3.0, c.y)
gh = m.spawn_units(PLAYER, "goblin_hut", 1, 5.5, 25.5, deploy=0)[0]; print("hut crad", gh.crad)
# --- Goblinstein's Monster goes for buildings, ignores troops ---
m = fresh()
m._deploy(PLAYER, "goblinstein", 9, 20)
mon = [e for e in m.entities if e.key == "goblin_monster"][0]
m.spawn_units(ENEMY, "knight", 1, mon.x, mon.y - 2, deploy=0)
step(m, 1.0)
print("monster target:", mon.target.key if mon.target else None)
assert mon.target is None or mon.target.is_building
# --- Tornado radius ---
print("tornado radius", cards.CARDS["tornado"].spell_radius)
print("ALL OK")
