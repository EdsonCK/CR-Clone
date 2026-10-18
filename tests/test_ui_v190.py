"""v1.9.0 UI: one ability button per champion / hero on the field (right
margin, then left, then stacked), the Tie Breaker banner (no result until
the engine finishes), the inner outline on upgraded hand cards, and Chaos
Draft end to end (8 card picks, 3 starting upgrades, then a ChaosRun)."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import os

import pygame
import profile_data
profile_data.PROFILE_FILE = os.path.join(_util.TMP, "test_profile.json")
import cards
import chaos
import config as cfg
import endless_upgrades as eu
import evos
from engine import Match, PLAYER, ENEMY
from game import Game
import modes

g = Game()
g._save_settings = lambda: None
g._save_progress = lambda: None
pygame.mouse.get_pos = lambda: (0, 0)


def battle(deck=None):
    g.mode = None
    g.chaos = None
    g.level_run = None
    g.match = Match(list(deck or cards.DEFAULT_PLAYER_DECK), list(cards.DEFAULT_AI_DECK))
    g.match.record_events = True
    g.ai = None
    g._audio = {}
    g.fx.clear()
    g.selected = None
    g.state = "match"
    return g.match


def click(pos):
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    g._events(0)


# ---- two ability units: two buttons, right margin then left, each its own
m = battle()
m.elixir[PLAYER] = 10.0
aq = m.spawn_units(PLAYER, "archer_queen", 1, 4.5, 26.0, deploy=0.0)[0]
aq.deploy_timer = 0.0
gp = m.spawn_units(PLAYER, "monk", 1, 13.5, 26.0, deploy=0.0)[0]
gp.deploy_timer = 0.0
btns = g._ability_buttons()
assert [e for _, e, _ in btns] == [aq, gp], btns
(_, _, r0), (_, _, r1) = btns
arena_r = cfg.ARENA_X0 + cfg.ARENA_PX_W
assert r0.left >= arena_r and r1.right <= cfg.ARENA_X0, (r0, r1)   # right, then left
assert not r0.colliderect(r1)
g._draw()
assert aq.ability_uses == 1 and gp.ability_uses >= 1
uses_gk = gp.ability_uses
click(r1.center)                                 # the LEFT button: Monk
assert gp.ability_uses == uses_gk - 1 and aq.ability_uses == 1, (gp.ability_uses, aq.ability_uses)
m.elixir[PLAYER] = 10.0
click(r0.center)                                 # the RIGHT button: Archer Queen
assert aq.ability_uses == 0
# a third (a hero) stacks above the first, right margin
kn = m.spawn_units(PLAYER, "knight", 1, 9.0, 27.0, deploy=0.0)[0]
kn.hero, kn.hero_def, kn.ability_uses, kn.deploy_timer = True, evos.HEROES["knight"], 1, 0.0
btns = g._ability_buttons()
assert len(btns) == 3 and btns[2][0] == "hero" and btns[2][1] is kn
r2 = btns[2][2]
assert r2.left >= arena_r and r2.bottom < r0.top, (r2, r0)
assert not any(r2.colliderect(b[2]) for b in btns[:2])
g._draw()
print("ability buttons ok")

# ---- Tie Breaker: frozen, then drain; red text; no result until finished
m = battle()
m.overtime = True
m.time_left = 0.01
for _ in range(15):
    g._update_match(1 / 30)
assert m.tiebreak_phase() == "pause" and not m.finished
assert g.state == "match"
g._draw()
cx, cy = cfg.WINDOW_W // 2, cfg.ARENA_Y0 + cfg.ARENA_PX_H // 2
reds = 0
for dx in range(-150, 151, 3):
    for dy in range(-25, 26, 3):
        c = g.screen.get_at((cx + dx, cy + dy))
        if c.r > 200 and c.g < 140 and c.b < 120:
            reds += 1
assert reds > 30, reds                           # big red "Tie Breaker"
hp0 = {k: t.hp for k, t in m.towers.items() if t.alive}
n = 0
while not m.finished:
    assert g.state == "match", "result screen before the tiebreak ended"
    g._update_match(1 / 30)
    if m.tiebreak_phase() == "drain" and n % 10 == 0:
        g._draw()
    n += 1
    assert n < 30 * 10
assert any(m.towers[k].hp < hp for k, hp in hp0.items())
assert g.state == "result", g.state
print("tie breaker ok (%.1f s)" % (n / 30))

# ---- an epic-upgraded hand card gets an epic inner outline (not the Evo look)
m = battle()
key = m.hands[PLAYER][0]
plain = m.hands[PLAYER][1]
ups = [u for u in eu.CARD_UPS.get(key, ()) if u.tier == "epic"]
if not ups:                                      # make sure we have an epic one
    key = next(k for k in m.hands[PLAYER] if any(u.tier == "epic" for u in eu.CARD_UPS.get(k, ())))
    ups = [u for u in eu.CARD_UPS[key] if u.tier == "epic"]

plain = next(k for k in m.hands[PLAYER] if k != key)
g.mode = "chaos"
g.chaos = chaos.ChaosRun(m, 1, picks=[ups[0]])
assert g._card_upgrade(key) == ("epic", getattr(ups[0], "unique", False))
assert g._card_upgrade(plain) == (None, False)
g._draw()
slots = g._hand_slot_rects()
i, j = m.hands[PLAYER].index(key), m.hands[PLAYER].index(plain)
ri, rj = slots[i].inflate(-6, -6), slots[j].inflate(-6, -6)
mid = lambda r: (r.x, r.centery + 6)             # on the left inner edge
ci = g.screen.get_at(mid(ri))
cj = g.screen.get_at(mid(rj))
ec = g.UPG_COLS["epic"]
assert abs(ci.r - ec[0]) < 30 and abs(ci.g - ec[1]) < 30 and abs(ci.b - ec[2]) < 30, ci
assert abs(cj.b - ci.b) + abs(cj.r - ci.r) + abs(cj.g - ci.g) > 60, (ci, cj)
# the epic outline is clearly not the Evo violet, the legendary one not Hero gold
assert sum(abs(a - b) for a, b in zip(ec, (200, 130, 255))) > 100
assert all(sum(abs(a - b) for a, b in zip(g._upg_col("legendary", t / 10), (255, 200, 90))) > 40
           for t in range(3, 9))
g.chaos = None
print("hand outline ok", ci, cj)

# ---- Chaos Draft end to end
assert "chaos_draft" in modes.MODE_NAMES
g.state = "modes"
g._start_mode("chaos_draft")
assert g.state == "draft" and g.mode == "chaos_draft"
for _ in range(cfg.DECK_SIZE):
    assert g.state == "draft"
    click(g._draft_rects()[0].center)
assert g.state == "match", g.state
m = g.match
assert len(m.decks[PLAYER]) == len(m.decks[ENEMY]) == 8
assert m.card_levels[PLAYER] == m.card_levels[ENEMY] == profile_data.SPECIAL_AI_LEVEL
assert g.ai.level == chaos.CHAOS_AI_LEVEL
start = g.chaos
assert isinstance(start, modes.DraftStart) and start.choice
for k, tier in enumerate(chaos.DRAFT_TIERS):
    assert g._chaos_run() is start and start.start_no == k
    assert [u.tier for u in start.choice] == [tier, tier], start.choice
    t0 = m.elapsed
    for _ in range(20):
        g._update_match(1 / 30)
    assert m.elapsed == t0, "clock ran during the starting picks"
    g._choice_t0 = -10
    g._draw()
    click(g._choice_rects()[k % 2].center)
run = g.chaos
assert isinstance(run, chaos.ChaosRun) and not isinstance(run, modes.DraftStart)
assert run.m is m and len(run.picks) == 3 and len(run.ai_picks) == 3
assert [u.tier for u in run.picks] == list(chaos.DRAFT_TIERS)
assert all(u.kind == "boon" or u.card in m.decks[ENEMY] for u in run.ai_picks)
for _ in range(30):
    g._update_match(1 / 30)
assert m.elapsed > 0.5 and run.choice is None
g._draw()
lists = g._result_upgrade_lists()
assert [len(p) for _, _, p in lists] == [3, 3], lists
g.last_rewards = []
g._mode_rewards(PLAYER)
assert g.profile.special["chaos_draft"]["wins"] == 1
print("chaos draft ok", [u.title for u in run.picks], "|", [u.title for u in run.ai_picks])
print("ui v190 ok")
