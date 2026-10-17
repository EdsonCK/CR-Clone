"""Chaos: a battle vs the Master AI with a ChaosRun; at 45 s the game pauses
on an upgrade offer of the same rarities the AI got, a click picks and the
match resumes; the next-upgrade countdown sits by the timer."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import os

import pygame
import profile_data
profile_data.PROFILE_FILE = os.path.join(_util.TMP, "test_profile.json")
import chaos
from engine import PLAYER, ENEMY
from game import Game

g = Game()
g._save_settings = lambda: None
g._save_progress = lambda: None
pygame.mouse.get_pos = lambda: (0, 0)
g._start_mode("chaos")
m, run = g.match, g.chaos
assert g.state == "match" and isinstance(run, chaos.ChaosRun) and run.m is m
assert g.ai.level == chaos.CHAOS_AI_LEVEL == 5
assert m.enemy_towers and m.timed and not m.finished
assert m.card_levels[PLAYER] == m.card_levels[ENEMY] == profile_data.SPECIAL_AI_LEVEL
g.ai = None                                  # nobody defends here: keep it idle

# ---- the countdown chip
lbl, left, final = g._chaos_countdown()
assert lbl == "0:45" and not final, lbl
for _ in range(30 * 10):
    g._update_match(1 / 30)
lbl, left, final = g._chaos_countdown()
assert lbl == "0:35", lbl
g._draw()                                    # chip draws without errors

# ---- at 45 s: paused with a choice, the AI already picked (same rarities)
while not run.choice:
    g._update_match(1 / 30)
assert abs(m.elapsed - chaos.INTERVAL) < 0.05, m.elapsed
assert len(run.choice) == 2 and len(run.ai_picks) == 1
assert sorted(u.tier for u in run.choice) == sorted(run.tiers)
assert run.ai_picks[0].tier in run.tiers
t0, el0 = m.elapsed, m.elixir[PLAYER]
for _ in range(60):
    g._update_match(1 / 30)
assert m.elapsed == t0 and m.elixir[PLAYER] == el0, "match not paused"
g._choice_t0 = -10
g._draw()

# ---- a click on a pick card takes it and resumes
r = g._choice_rects()[1]
want = run.choice[1]
pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=r.center))
g._events(0)
assert run.choice is None and run.picks == [want]
for _ in range(30):
    g._update_match(1 / 30)
assert m.elapsed > t0
assert g._ai_toast is not None and g._ai_toast[0] is run.ai_picks[0]
g._draw()

# ---- one-time in Chaos: the same upgrade is never offered again
for _ in range(3):
    while not run.choice and not m.finished:
        g._update_match(1 / 30)
    if m.finished:
        break
    assert want.key not in {u.key for u in run.choice}
    g._choice_pick(0)

# ---- the end screen lists both sides' upgrades and pays Chaos gold
m.finished, m.winner = True, PLAYER
g._on_match_end()
labels = [lbl for lbl, _, _ in g._result_upgrade_lists()]
assert labels[0].startswith("Your upgrades") and labels[1].startswith("Enemy upgrades")
assert g._result_upgrade_rows() == 88
assert any(lbl == "Victory" for lbl, _ in g.last_rewards)
assert profile_data.chaos_gold(True, 0, 2) == profile_data.special_gold(True, 5, 0) + 10
g._draw()

# ---- other modes have no Chaos run
g._start_mode("triple")
assert g.chaos is None and g._chaos_run() is None and g._chaos_countdown() is None
print("chaos ui ok")
