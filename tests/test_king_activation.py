"""King Tower activation: 2v2 twin Kings; Firecracker sparks waking the 2v2
Kings off a Princess Tower; the Tornado + Hog Rider King activation."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import cards
from engine import Match, PLAYER, ENEMY, TOWER_HALF

D = list(cards.DEFAULT_PLAYER_DECK)


def match(duo):
    m = Match(D, D)
    if duo:
        m.add_seats(D, D, 11, 11)
    return m


# ---- 2v2: two Kings side by side, touching, one shared HP pool
m = match(True)
for team in (PLAYER, ENEMY):
    k1, k2 = m.kings(team)
    assert k1.twin is k2 and k2.twin is k1
    assert abs((k2.x - k1.x) - 2 * TOWER_HALF[True]) < 1e-9, "touching, no gap"
    assert k1.radius == 2.0 and k2.radius == 2.0          # 4x4 each
    assert k1.max_hp == k2.max_hp == Match(D, D).towers[(team, "king")].max_hp
    assert not k1.active and not k2.active
k1, k2 = m.kings(ENEMY)
k2.take_damage(300)
assert k1.hp == k2.hp == k1.max_hp - 300 and k1.active and k2.active, "shared HP, wake together"
k1.take_damage(10 ** 6)
for _ in range(3):
    m.update(1 / 60)
assert m.finished and m.winner == PLAYER and m.crowns[PLAYER] == 3
print("twin kings OK")


# ---- Firecracker hitting the Princess Tower wakes the 2v2 Kings
def firecracker(duo, x):
    m = match(duo)
    for t in m.towers.values():                 # geometry only: towers hold fire
        t.range = 0
        t.attack_cd = 1e9
    m.spawn_units(PLAYER, "firecracker", 1, x, 16.0, deploy=0)
    pr = m.towers[(ENEMY, "left")]
    for _ in range(60 * 15):
        m.update(1 / 60)
        if not pr.alive:
            return False
        if any(k.active for k in m.kings(ENEMY)):
            return True
    return False


for x in (2.5, 3.5):
    assert firecracker(True, x), "2v2: firecracker from x=%.1f should wake the kings" % x
    print("2v2 firecracker at x=%.1f wakes the kings" % x)
assert not firecracker(False, 3.5), "1v1: the single King is out of reach"


# ---- Tornado pulls a Hog Rider off the Princess Tower onto the King
def hog_tornado(duo, tx, ty, t_cast, lane_x=3.5):
    m = match(duo)
    hog = m.spawn_units(ENEMY, "hog_rider", 1, lane_x, 12.0, deploy=0)[0]
    cast = t_cast is None
    for _ in range(60 * 12):
        if not cast and m.elapsed >= t_cast:
            m.hands[PLAYER][0] = "tornado"
            m.elixir[PLAYER] = 10
            assert m.play_card(PLAYER, 0, tx, ty)
            cast = True
        m.update(1 / 60)
        if any(k.active for k in m.kings(PLAYER)):
            assert m.towers[(PLAYER, "left")].alive
            return hog.target is not None and hog.target.is_king
        if not hog.alive:
            return False
    return False


assert not hog_tornado(False, 0, 0, None), "no Tornado: the Hog leaves the King asleep"
ok1 = [tc for tc in (3.0, 3.25, 3.5) if hog_tornado(False, 7.5, 25.5, tc)]
ok2 = [tc for tc in (3.0, 3.25, 3.5) if hog_tornado(True, 6.5, 26.5, tc)]
print("tornado king activation: 1v1 casts", ok1, " 2v2 casts", ok2)
assert ok1 and ok2
for lx in (2.5, 4.5):                           # Hogs coming down either edge of the lane
    assert any(hog_tornado(False, 7.5, 25.5, tc, lane_x=lx) for tc in (3.0, 3.25, 3.5, 3.75)), lx
print("KING ACTIVATION OK")
