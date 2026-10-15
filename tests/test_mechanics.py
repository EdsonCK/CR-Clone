"""Targeted combat mechanics (charges, spawns, spells, projectiles...)."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import os, sys
sys.path.insert(0, _util.SRC)
import config as cfg, cards
from engine import Match, PLAYER, ENEMY, dist

def fresh():
    m = Match(cards.DEFAULT_PLAYER_DECK, cards.DEFAULT_AI_DECK)
    m.elixir = [10, 10]
    return m

def step(m, secs):
    for _ in range(int(secs * 60)):
        m.update(1 / 60)
        m.elixir = [10, 10]

def get(m, key, team=PLAYER):
    return [e for e in m.entities if e.key == key and e.team == team]

# --- Mighty Miner: drill stages, no beam flag, escape mirrors lane ---
m = fresh()
m._deploy(PLAYER, "mighty_miner", 9, 12)
m._deploy(ENEMY, "golem", 9, 10.6)
mm = get(m, "mighty_miner")[0]; gol = get(m, "golem", ENEMY)[0]; gol.freeze_timer = 99
assert not mm.card.ramp
hp0 = gol.hp; step(m, 2.0); d1 = hp0 - gol.hp
hp0 = gol.hp; step(m, 2.0); d2 = hp0 - gol.hp
hp0 = gol.hp; step(m, 2.0); d3 = hp0 - gol.hp
print("MM dmg per 2s window:", round(d1), round(d2), round(d3), "stage", mm.ramp_stage())
assert d3 > d2 > d1
x0, y0 = mm.x, mm.y
assert m.activate_ability(PLAYER)
step(m, 0.55)   # (ability wind-up)
print("MM escape: %.2f,%.2f -> %.2f,%.2f invis=%s" % (x0, y0, mm.x, mm.y, mm.invis_timer))
assert abs(mm.x - (cfg.GRID_COLS - x0)) < 1e-6 and mm.y == y0 and mm.invis_timer <= 0
bombs = [f for f in m.effects if f.kind == "timed_bomb"]
assert bombs and abs(bombs[0].x - x0) < 1e-6
hp0 = gol.hp; step(m, 1.1)
print("bomb dealt", round(hp0 - gol.hp), "to golem near old spot")
assert not [f for f in m.effects if f.kind == "timed_bomb"]

# --- Little Prince: speed ramp, projectiles (no beam) ---
m = fresh()
m._deploy(PLAYER, "little_prince", 9, 24); m._deploy(ENEMY, "golem", 9, 19)
lp = get(m, "little_prince")[0]
step(m, 1.5); hs0 = lp.effective_hitspeed(); step(m, 5.5); hs1 = lp.effective_hitspeed()
print("LP hit interval %.2f -> %.2f, projectiles in flight: %d" % (hs0, hs1, len(m.projectiles)))
assert hs1 < hs0
m.activate_ability(PLAYER); step(m, 0.45)
g = get(m, "royal_guardian")[0]; assert g.is_dashing()
step(m, 1.0); print("guardian dashed to %.1f,%.1f" % (g.x, g.y))

# --- Golden Knight chain dash ---
m = fresh()
m._deploy(PLAYER, "golden_knight", 9, 22)
for i in range(5):
    m._deploy(ENEMY, "knight", 5 + i * 2, 19.5)
step(m, 1.2)
gk = get(m, "golden_knight")[0]
kn = get(m, "knight", ENEMY); hps = [k.hp for k in kn]
assert m.activate_ability(PLAYER); step(m, 0.3); assert gk.is_dashing()
step(m, 1.5)
hit = sum(1 for k, h in zip(kn, hps) if k.hp < h - 200 or not k.alive)
chains = [f for f in m.effects if f.kind == "chain"]
print("GK chain hit %d knights" % hit)
assert hit >= 4

# --- Monk protect + deflect ---
m = fresh()
m._deploy(PLAYER, "monk", 4.5, 22); m._deploy(ENEMY, "musketeer", 4.5, 16)
monk = get(m, "monk")[0]; mus = get(m, "musketeer", ENEMY)[0]
step(m, 1.2); m.activate_ability(PLAYER)
mhp = mus.hp; step(m, 3.5)
print("Monk protect: musketeer took %d deflected dmg" % (mhp - mus.hp))
assert mus.hp < mhp

# --- Goblinstein link ---
m = fresh()
m._deploy(PLAYER, "goblinstein", 6, 22)
doc = get(m, "goblinstein")[0]; mon = get(m, "goblin_monster")[0]
assert doc.partner is mon and mon.partner is doc
m._deploy(ENEMY, "knight", 6.6, 22.3)
step(m, 1.1); k = get(m, "knight", ENEMY)[0]; h0 = k.hp
m.activate_ability(PLAYER); step(m, 0.6)
print("link dmg to knight on beam:", round(h0 - k.hp), [f.kind for f in m.effects])

# --- Boss Bandit dash + getaway ---
m = fresh()
m._deploy(PLAYER, "boss_bandit", 9, 24); m._deploy(ENEMY, "knight", 9, 19.5)
bb = get(m, "boss_bandit")[0]
dashed = False
for _ in range(120):
    m.update(1/60); dashed |= bb.is_dashing()
print("Boss Bandit dashed:", dashed)
assert dashed
y0 = bb.y; m.activate_ability(PLAYER); step(m, 0.8)
print("getaway: y %.1f -> %.1f invis %.1f" % (y0, bb.y, bb.invis_timer))

# --- Skeleton King soul cap ---
m = fresh(); m._deploy(PLAYER, "skeleton_king", 9, 24)
sk = get(m, "skeleton_king")[0]
for i in range(15):
    m._deploy(ENEMY, "skeleton", 9, 23); 
step(m, 3)
print("SK souls", sk.souls); assert sk.souls <= 10

# --- Bandit, MK, Hog, E-Wiz, Exe ---
m = fresh(); m._deploy(PLAYER, "bandit", 4.5, 26); m._deploy(ENEMY, "knight", 4.5, 21)
b = get(m, "bandit")[0]; seen = False
for _ in range(150):
    m.update(1/60); seen |= b.is_dashing()
print("bandit dashed", seen); assert seen
m = fresh(); m._deploy(PLAYER, "mega_knight", 4.5, 26); m._deploy(ENEMY, "knight", 4.5, 21.5)
mk = get(m, "mega_knight")[0]; seen = False
for _ in range(150):
    m.update(1/60); seen |= mk.is_dashing()
print("MK jumped", seen); assert seen
m = fresh(); m._deploy(PLAYER, "hog_rider", 7, 22)
h = get(m, "hog_rider")[0]; xs = []
for _ in range(200):
    m.update(1/60); xs.append(h.x)
print("hog x range while crossing: %.1f..%.1f (bridges at %s)" % (min(xs), max(xs), cfg.BRIDGE_COLS))
m = fresh(); m._deploy(ENEMY, "knight", 9, 20); m._deploy(ENEMY, "archers", 9, 19)
m._deploy(PLAYER, "electro_wizard", 9, 21)
st = [e.stun_timer for e in m.entities if e.team == ENEMY and not e.is_tower]
print("E-Wiz deploy stun:", [round(x, 2) for x in st]); assert max(st) > 0
step(m, 2.2)
print("E-Wiz projectiles fired so far ok")
m = fresh(); m._deploy(PLAYER, "executioner", 9, 24); m._deploy(ENEMY, "knight", 9, 20)
step(m, 1.3)
ax = [p for p in m.projectiles if p.style == "executioner"]
returned = False
for _ in range(120):
    m.update(1/60)
    returned |= any(p.returning for p in m.projectiles)
print("exe axe returned:", returned); assert returned
print("bomber", cards.CARDS["bomber"].elixir, "skarmy", cards.CARDS["skeleton_army"].elixir,
      "barbs", cards.CARDS["barbarians"].count)
print("MECH TESTS PASSED")
