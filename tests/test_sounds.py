"""Every sound the battles ask for has a file."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import os, sys, random, time

sys.path.insert(0, _util.SRC); os.chdir(_util.ROOT)
from engine import PLAYER
from ai import AIController
from game import Game
g = Game(); g._save_settings = lambda: None; g._save_stats = lambda: None
heard = {}
ov = g.sfx.play_var
def spy(name, *a, **k):
    r = ov(name, *a, **k); heard[name] = heard.get(name, 0) + (1 if g.sfx.variants.get(name) else 0); return r
g.sfx.play_var = spy
decks = [["golden_knight", "monk", "archer_queen", "skeleton_king", "witch", "night_witch", "barbarian_hut", "furnace"],
         ["mighty_miner", "goblinstein", "boss_bandit", "little_prince", "sparky", "mortar", "bomb_tower", "firecracker"],
         ["pekka", "electro_wizard", "tesla", "goblin_drill", "lava_hound", "balloon", "golem", "elixir_golem"]]
for i, d in enumerate(decks):
    random.seed(i); g.ai_level = 4; g.player_deck = d
    g._begin_battle(); m = g.match
    me = AIController(m, team=PLAYER, level=4)
    f = 0
    while not m.finished and f < 60 * 150:
        m.update(1/60); g.ai.update(1/60); me.update(1/60); g._update_audio(1/60); g.sfx.tick(1/60); f += 1
missing = sorted(n for n, c in heard.items() if c == 0)
print("played", len(heard), "distinct names; with no file:", missing)
assert len(heard) > 60 and not missing
