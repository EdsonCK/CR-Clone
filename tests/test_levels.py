"""Levels + Endless: valid waves, titles that match the troops, enemy
support spells on their own push, reinforcement call-outs."""
import random

import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import cards
import levels
from engine import PLAYER, ENEMY, RIVER_TOP

PLACES = {"field", "back", "front", "river", "tower", "army", "near", "push"}
SWARM_WORDS = ("Swarm", "Horde", "Skitter", "Teeming", "Mob")
AIR_WORDS = ("Wings", "Sky", "Air", "Wingbeat")


def troops(w):
    return [s.key for s in w.spawns if cards.CARDS[s.key].category == "troop"
            and s.key not in levels.ENDLESS_SUPPORT]


def check_title(w, where):
    ks = troops(w)
    if any(word in w.name for word in SWARM_WORDS):
        assert not any(levels.is_heavy(k) for k in ks), (where, w.name, ks)
        assert sum(levels.is_swarm(k) for k in ks) * 2 >= len(ks), (where, w.name, ks)
    if any(word in w.name for word in AIR_WORDS):
        assert all(cards.CARDS[k].flying for k in ks), (where, w.name, ks)


# ---- the 30 levels
for lv in levels.LEVELS:
    assert len(lv.waves) == (8 if lv.key == "final_siege" else 7), lv.key
    assert lv.waves[-1].boss and not any(w.boss for w in lv.waves[:-1]), lv.key
    for w in lv.waves:
        assert any(cards.CARDS[s.key].category != "spell" for s in w.spawns), (lv.key, w.name)
        for s in w.spawns:
            c = cards.CARDS[s.key]
            assert s.place in PLACES and s.lane in levels.LANE_X, (lv.key, w.name, s)
            if s.place == "push":
                assert s.key in ("rage", "clone", "heal_spirit"), (lv.key, w.name, s.key)
        check_title(w, lv.key)
names = [w.name for lv in levels.LEVELS for w in lv.waves]
print("levels ok:", len(levels.LEVELS), "levels,", len(names), "waves,",
      sum(1 for lv in levels.LEVELS for w in lv.waves for s in w.spawns if s.note),
      "reinforcements,",
      sum(1 for lv in levels.LEVELS for w in lv.waves for s in w.spawns if s.place == "push"),
      "support drops")

# ---- Endless: names match what spawns
for seed in range(40):
    rng = random.Random(seed)
    for n in range(1, 41):
        w = levels.endless_wave(n, rng)
        ks = troops(w)
        assert ks, (seed, n)
        if w.boss:
            bosses = [cards.CARDS[s.key].name for s in w.spawns if s.mult > 1.0]
            assert w.name == "Boss Rush" if len(bosses) >= 3 else bosses[0] in w.name, \
                (seed, n, w.name, bosses)
            continue
        check_title(w, "endless")
        for theme in ("swarm", "air", "heavy", "rush", "ranged"):
            fits, ns = levels.ENDLESS_THEMES[theme]
            if w.name in ns:
                assert all(fits(k) for k in ks), (seed, n, w.name, ks)
print("endless names ok")


def start(key, idx):
    lv = levels.LEVELS_BY_KEY[key]
    m, run = levels.new_level_match(lv, levels.default_level_deck(), card_levels=11)
    run._start_wave(idx)
    return m, run


# ---- "push": the enemy's Rage lands on its own troops at the river
m, run = start("barbarian_raid", 0)        # War Cry: barbarians + rage on them
rage = None
for f in range(30 * 20):
    m.update(1 / 30)
    run.update(1 / 30)
    rage = next((e for e in m.effects if e.kind == "rage" and e.team == ENEMY), None)
    if rage:
        break
assert rage, "no enemy rage"
near = [e for e in m.entities if e.team == ENEMY and e.alive and not e.is_tower
        and (e.x - rage.x) ** 2 + (e.y - rage.y) ** 2 <= rage.radius ** 2]
assert near and rage.y >= RIVER_TOP - 3.0, (rage.x, rage.y, len(near))
print("rage on push at t=%.1f (%.1f, %.1f) covering %d" % (run.wave_t, rage.x, rage.y, len(near)))

# ---- reinforcements: call-out shown when they arrive
m, run = start("bone_crypt", 1)            # Shield Wall: skeletons at 8s
seen = None
for f in range(30 * 10):
    m.update(1 / 30)
    run.update(1 / 30)
    if run.note and seen is None:
        seen = (run.wave_t, run.note[0])
assert seen and seen[1] == "Reinforcements!" and 7.9 < seen[0] < 8.2, seen
print("reinforcements at", seen)

# ---- a support drop with nothing left to help is skipped, not stuck
m, run = start("barbarian_raid", 0)
for e in m.entities:
    if e.team == ENEMY and not e.is_tower:
        e.alive = False
run.pending = [levels.Spawn("rage", 0.0, "left", None, 1.0, "push")]
for f in range(30 * 16):
    m.update(1 / 30)
    run.update(1 / 30)
    for e in m.entities:
        if e.team == ENEMY and not e.is_tower:
            e.alive = False
assert not run.pending and not any(e.kind == "rage" and e.team == ENEMY for e in m.effects)
print("idle support skipped ok")
