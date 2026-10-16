"""Music: menu and battle themes play in random order (never the same one
twice in a row, a new one when a track ends); a brand-new player's first menu
track is the original theme, later launches are random from the start."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import os
import sounds
from game import Game

DECK = ["knight", "archers", "wizard", "tombstone", "hog_rider", "golden_knight",
        "goblin_hut", "fireball"]
assert not os.listdir(_util.TMP), "starts with no saves"
g = Game()
assert g.first_launch
g._update_audio(1 / 60)
assert g.sfx.music_track == "menu", "first launch opens with the original theme"
assert os.path.exists(os.path.join(_util.TMP, "profile.json")), "first launch creates player data"

seen = []
for i in range(40):
    g.state = "menu"; g.match = None; g._update_audio(1 / 60); seen.append(g.sfx.music_track)
    g.player_deck = list(DECK)
    g._begin_battle(); g.state = "match"; g._update_audio(1 / 60); seen.append(g.sfx.music_track)
    g.match.time_left = 30; g._update_audio(1 / 60); seen.append(g.sfx.music_track)
print(seen[:12])
for k in ("menu", "battle", "final"):
    got = [t for t in seen if t.rstrip("234") == k]
    assert set(got) == {k, k + "2", k + "3", k + "4"}, (k, set(got))
    assert all(a != b for a, b in zip(got, got[1:])), (k, "repeated a track back to back")
# a track that finishes is followed by another (different) random one
g.state = "menu"; g.match = None; g._update_audio(1 / 60)
before = g.sfx.music_track
g.sfx.music_ended = lambda: True
g._update_audio(1 / 60)
assert g.sfx.music_track.startswith("menu") and g.sfx.music_track != before
del g.sfx.music_ended

# relaunch (e.g. after an update): player data exists -> random from the start
firsts = set()
for _ in range(12):
    g2 = Game()
    assert not g2.first_launch
    g2._update_audio(1 / 60)
    firsts.add(g2.sfx.music_track)
print("relaunch first tracks:", sorted(firsts))
assert len(firsts) > 1
import pygame
pygame.mixer.stop()          # (13 test games filled every channel)
for nm in ("victory", "defeat", "crown", "match_start", "ui_click", "fireball_cast",
           "fireball_impact", "tick", "wave", "wave_boss"):
    ok = bool(g2.sfx.play(nm, 0.5, min_gap=0.0))
    print(nm, ok)
    assert ok, nm
print("MUSIC OK", sounds.music_themes("menu"), sounds.music_themes("battle"))
