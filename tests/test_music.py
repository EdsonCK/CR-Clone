"""Menu / battle music rotates through all 4 themes."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import os, sys

sys.path.insert(0, _util.SRC); os.chdir(_util.ROOT)
from game import Game
g = Game()
seen = []
for i in range(5):
    g.state = "menu"; g.match = None; g._update_audio(1/60); seen.append(g.sfx.music_track)
    g.player_deck = ["knight", "archers", "wizard", "tombstone", "hog_rider", "golden_knight", "goblin_hut", "fireball"]
    g._begin_battle(); g.state = "match"; g._update_audio(1/60); seen.append(g.sfx.music_track)
    g.match.time_left = 30; g._update_audio(1/60); seen.append(g.sfx.music_track)
print(seen)
for k in ("menu", "battle", "final"):
    assert {t for t in seen if t.startswith(k)} == {k, k + "2", k + "3", k + "4"}, (k, seen)
for nm in ("victory", "defeat", "crown", "match_start", "ui_click", "fireball_cast", "fireball_impact", "tick"):
    ok = bool(g.sfx.play(nm, 0.5, min_gap=0.0))
    print(nm, ok)
    assert ok, nm
