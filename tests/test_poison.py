"""Poison: 8 ticks of damage, one a second, over 8s (392 total, 152 to towers)."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import cards
from engine import Match, PLAYER, ENEMY

c = cards.CARDS["poison"]
assert c.duration == 8.0 and c.dot_tick == 1.0
m = Match(list(cards.DEFAULT_PLAYER_DECK), list(cards.DEFAULT_AI_DECK))
for t in m.towers.values():
    t.range = 0; t.attack_cd = 1e9
g = m.spawn_units(ENEMY, "golem", 1, 9, 12, deploy=0)[0]
g.speed = g.base_speed = 0
m.elixir[PLAYER] = 10
m.hands[PLAYER][0] = "poison"
assert m.play_card(PLAYER, 0, 9, 12)
hits, last = [], g.hp
for f in range(60 * 12):
    m.update(1 / 60)
    if g.hp < last:
        hits.append((round(m.elapsed, 3), round(last - g.hp, 1)))
        last = g.hp
print("ticks", hits)
assert len(hits) == 8, hits
gaps = [round(b[0] - a[0], 3) for a, b in zip(hits, hits[1:])]
assert all(abs(x - 1.0) < 0.02 for x in gaps), gaps
total = sum(d for _, d in hits)
lv = cards.level_mult(m.card_level(PLAYER, "poison"))
assert abs(total - 392 * lv) < 2, total
assert 6.9 < hits[-1][0] - hits[0][0] < 8.0
# crown towers: 8 x 19
m = Match(list(cards.DEFAULT_PLAYER_DECK), list(cards.DEFAULT_AI_DECK))
tw = m.towers[(ENEMY, "left")]
hp0 = tw.hp
m.elixir[PLAYER] = 10; m.hands[PLAYER][0] = "poison"
assert m.play_card(PLAYER, 0, tw.x, tw.y)
for f in range(60 * 12):
    m.update(1 / 60)
print("tower damage", hp0 - tw.hp)
assert abs((hp0 - tw.hp) - 152 * lv) < 2, hp0 - tw.hp
print("POISON OK")
