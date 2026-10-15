"""Electric attacks hit instantly; chains ripple 0.2s apart."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import sys; sys.path.insert(0, _util.SRC)
import cards
from engine import Match, PLAYER, ENEMY
def fresh():
    m = Match(list(cards.DEFAULT_PLAYER_DECK), list(cards.DEFAULT_AI_DECK))
    for t in m.towers.values(): t.range = 0; t.attack_cd = 1e9
    return m
# 1) instant zap: damage lands on the frame the attack fires
for key in ("electro_wizard", "zappies", "goblinstein", "electro_dragon", "spirit_empress_air", "tesla"):
    m = fresh()
    sh = m.spawn_units(PLAYER, key, 1, 9, 22, deploy=0)[0]
    tg = m.spawn_units(ENEMY, "giant", 1, 9, 22 - min(sh.range, 3.0), deploy=0)[0]
    tg.speed = 0
    hp0 = tg.hp; fired = None; landed = None
    for f in range(60 * 4):
        n0 = len([1 for e in m.events]) if m.record_events else 0
        a0 = sh.atk_t
        m.update(1/60)
        if fired is None and sh.atk_t != a0: fired = f
        if landed is None and tg.hp < hp0: landed = f
        if fired is not None and landed is not None: break
    print("%-18s fired frame %s, damage frame %s, projectiles in flight %d, bolts %d" % (
        key, fired, landed, len(m.projectiles), sum(1 for x in m.effects if x.kind == "bolt")))
    assert fired is not None and landed == fired, (key, fired, landed)
# 2) rippling chains
for key in ("electro_spirit", "electro_dragon"):
    m = fresh()
    sh = m.spawn_units(PLAYER, key, 1, 9, 21.0, deploy=0)[0]
    tg = m.spawn_units(ENEMY, "skeleton", 5, 9, 19.0, deploy=0)
    for t in tg: t.speed = 0; t.damage = 0; t.dmg = 0
    hits = {}
    for f in range(60 * 3):
        m.update(1/60)
        for t in tg:
            if id(t) not in hits and (t.hp < t.max_hp or not t.alive):
                hits[id(t)] = round(m.elapsed, 3)
    times = sorted(hits.values())
    first = [t for t in times if t - times[0] < 1.0]          # the first chain only
    gaps = [round(b - a, 3) for a, b in zip(first, first[1:])]
    print("%-14s chain hit times %s  gaps %s" % (key, times, gaps))
    assert len(first) >= 3 and all(abs(g - 0.2) < 0.02 for g in gaps), (key, gaps)
print("sparky speed", __import__("engine").PROJ_SPEEDS["sparky"])
assert __import__("engine").PROJ_SPEEDS["sparky"] >= 30
