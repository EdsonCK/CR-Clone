"""Reward collection animation and the stand-alone currency bar."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import os, sys

S = _util.TMP
os.environ["CLASH_CLONE_SAVE_DIR"] = os.path.join(S, "rfx_saves")
import shutil; shutil.rmtree(os.environ["CLASH_CLONE_SAVE_DIR"], ignore_errors=True)
sys.path.insert(0, _util.SRC); os.chdir(_util.ROOT)
import pygame
import game as G
from game import Game
from engine import PLAYER
g = Game(); g._save_settings = lambda: None
clock = [0.0]
g._now = lambda: clock[0]
def at(t, name):
    clock[0] = t; g._draw(); pygame.image.save(g.screen, os.path.join(S, name))
g.state = "menu"; at(0.0, "rfx_0.png")
g0 = g.profile.gold
g.profile.add(gold=250, gems=30, shards=2)          # e.g. an achievement claim
at(0.1, "rfx_1.png")                                 # gold popping in
print("shown gold at 0.1:", g._rfx_shown("gold"), "actual", g.profile.gold)
assert g._rfx_shown("gold") == g0
at(0.8, "rfx_2.png")                                 # gold flying
at(1.3, "rfx_3.png")                                 # gold landing, gems popping
at(3.5, "rfx_4.png")
assert g._rfx_shown("gold") == g.profile.gold and g._rfx_shown("gems") == g.profile.gems
# a screen without the top bar: the stand-alone bar shows and fades
g._open_achievements(); g.profile.add(coins=3, gems=5)
at(4.0, "rfx_5.png"); at(5.4, "rfx_6.png"); at(7.0, "rfx_7.png")
print("bar kinds", g._rfx_bar_kinds); at(9.5, "rfx_8.png")
print("after fade", g._rfx_bar_kinds, g._rfx_done_at)
print("RFX OK")
