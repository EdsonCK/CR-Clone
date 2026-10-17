"""Endless: the upgrade pick screen pauses the match, a click / key picks,
the upgrades show on the end-of-run screen, and rewards grow with depth."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import os

import pygame
import profile_data
profile_data.PROFILE_FILE = os.path.join(_util.TMP, "test_profile.json")
import endless_upgrades as eu
from game import Game

g = Game()
g._save_settings = lambda: None
g._save_progress = lambda: None
g.mode = "endless"
g._start_endless()
assert g.state == "match" and g.level_run is not None
run = g.level_run


def post(t, **kw):
    pygame.event.post(pygame.event.Event(t, **kw))
    g._events(0)


got = []
a = eu.Upgrade("t:a", "card", "Test Card Up", "A card upgrade.", g.level_deck[0],
               lambda m, t: got.append("a"), "epic", card=g.level_deck[0])
b = eu.Upgrade("t:b", "boon", "Test Boon", "A boon about elixir.", None,
               lambda m, t: got.append("b"), "legendary")

# ---- paused while a choice is pending
for _ in range(30):
    g._update_match(1 / 30)
t0, el0 = g.match.elapsed, g.match.elixir[0]
run.choice = [a, b]
for _ in range(60):
    g._update_match(1 / 30)
assert g.match.elapsed == t0 and g.match.elixir[0] == el0, "match not paused"
g._draw()                                    # overlay draws without errors
assert len(g._choice_rects()) == 2

# ---- clicks on the pick screen never reach the arena / hand
g.selected = 0
post(pygame.MOUSEBUTTONDOWN, pos=(5, 5), button=1)        # outside both cards
assert run.choice and got == []
r = g._choice_rects()[1]
post(pygame.MOUSEBUTTONDOWN, pos=r.center, button=1)
assert got == ["b"] and run.choice is None and run.picks[-1] is b
assert g.selected is None
for _ in range(10):
    g._update_match(1 / 30)
assert g.match.elapsed > t0, "match did not resume"

# ---- key 1 picks the first option
run.choice = [a, b]
post(pygame.KEYDOWN, key=pygame.K_1, mod=0, unicode="1")
assert got == ["b", "a"] and run.choice is None
g._draw()                                    # upgrade list in the margin

# ---- end of run: upgrades listed, rewards paid
g.match.finished = True
g.match.winner = 1
g._on_match_end()
assert g.state == "result" and g._result_upgrade_rows() > 0
g._draw()

# ---- rewards grow with depth
P = profile_data
assert P.endless_gold(0) == 0
assert P.endless_gold(10) == 80 + 55 + 50
assert P.endless_gold(30) > 3 * P.endless_gold(10)
assert [P.endless_gems(n) for n in (9, 10, 30, 40, 50)] == [0, 5, 15, 25, 35]
assert [P.endless_shards(n) for n in (14, 15, 45)] == [0, 1, 3]
assert [P.endless_coins(n) for n in (9, 10, 25)] == [0, 1, 2]
gold0 = g.profile.gold
g.last_rewards = []
g.level_run.waves_survived = lambda: 31
g._mode_rewards(1)
labels = [lbl for lbl, _ in g.last_rewards]
assert any(lbl.startswith("Deep run bonus") for lbl in labels), labels
assert g.profile.gold - gold0 == P.endless_gold(31)
print("endless ui ok:", labels)
