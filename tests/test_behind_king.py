"""Troops dropped behind the King Tower walk round it on their OWN lane's
side (Levels / Endless march to a spot, battles to a tower)."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import cards
import levels
from engine import Match, PLAYER

bad, total = [], 0
for mode in ("endless", "battle"):
    for key in ("knight", "musketeer", "giant_skeleton", "valkyrie", "barbarians",
                "royal_recruits"):
        for x in (6.5, 7.5, 8.5, 9.5, 10.5, 11.5):
            if mode == "endless":
                m, run = levels.new_endless_match(levels.default_level_deck(),
                                                  card_levels=11, tower_level=11, seed=0)
            else:
                m = Match(list(cards.DEFAULT_PLAYER_DECK), list(cards.DEFAULT_AI_DECK))
            if not m.can_place(PLAYER, key, x, 31.5):
                continue
            m._deploy(PLAYER, key, x, 31.5)
            units = [(e, e.lane) for e in m.entities if e.team == PLAYER and not e.is_tower]
            for _ in range(30 * 8):
                m.update(1 / 30)
            for e, lane in units:
                if e.alive:
                    total += 1
                    if (0 if e.x < 9 else 1) != lane:
                        bad.append((mode, key, x, round(e.x, 1), round(e.y, 1)))
assert not bad, bad
print("behind the King: %d units, all kept their lane" % total)
