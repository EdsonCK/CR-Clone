"""Firecracker and the King Tower (1v1): a lone enemy Firecracker shooting a
Princess Tower never wakes the King, but your own Firecracker, placed in
front of your King with the right timing, pulls the enemy's shot so its
sparks fly on into your King and wake it."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import cards
import config as cfg
from engine import Match, PLAYER, ENEMY

D = list(cards.DEFAULT_PLAYER_DECK)
assert cards.CARDS["firecracker"].sight == 8.0


def run(lane, mine=None, t_place=0.0):
    """Enemy Firecracker down `lane` (towers fire as normal); `mine` = where
    (x, y) to place yours, `t_place` s later. True if your King wakes."""
    m = Match(D, D)
    m.spawn_units(ENEMY, "firecracker", 1, lane, 14.0, deploy=0)
    side = "left" if lane < cfg.GRID_COLS / 2 else "right"
    pr = m.towers[(PLAYER, side)]
    placed = mine is None
    for _ in range(60 * 12):
        if not placed and m.elapsed >= t_place:
            m.spawn_units(PLAYER, "firecracker", 1, mine[0], mine[1], deploy=1.0)
            placed = True
        m.update(1 / 60)
        if m.towers[(PLAYER, "king")].active:
            return True
        if not pr.alive:
            break
    return False


# a lone Firecracker on a Princess Tower: the King sleeps, either lane
for lane in (2.5, 3.5, 4.5, 13.5, 14.5, 15.5):
    assert not run(lane), "lone firecracker at x=%.1f woke the King" % lane
print("lone firecracker never wakes the King")

# the defensive play: yours in front of the King, ~1.25 s after theirs crosses
for lane, spot in ((3.5, (7.0, 23.5)), (14.5, (11.0, 23.5))):
    assert run(lane, spot, 1.25), "well-timed firecracker should wake the King"
    assert not run(lane, spot, 0.0), "too early: it just trades, King asleep"
print("well-placed, well-timed firecracker wakes the King")
print("FIRECRACKER KING OK")
