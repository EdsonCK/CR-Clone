"""2v2 Battle from the Modes tab to the result and stats screens."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import os, sys

HERE = _util.TMP
sys.path.insert(0, _util.SRC); os.chdir(_util.ROOT)
import pygame, profile_data
profile_data.PROFILE_FILE = os.path.join(HERE, "test_profile.json")
if os.path.exists(profile_data.PROFILE_FILE): os.remove(profile_data.PROFILE_FILE)
import game as G
G.DECK_FILE = os.path.join(HERE, "test_deck.json")
from engine import PLAYER, ENEMY, ALLY, ENEMY2
from ai import AIController
g = G.Game(); g._save_settings = lambda: None; g._save_progress = lambda: None
# modes tab shows 2v2
g.state = "modes"; g._draw(); pygame.image.save(g.screen, os.path.join(HERE, "duo_modes.png"))
b = [b for b in g._modes_buttons() if b.label == "Play"][0]
g._modes_click(b.rect.center)
assert g.mode == "duo" and g.state == "match" and g.match.is_2v2
m = g.match
assert len(g._extra_ais()) == 2
assert m.card_levels[ALLY] == g.profile.deck_level(g.player_deck)
me = AIController(m, PLAYER, 3, seat=PLAYER)
gold0 = g.profile.gold
f = 0
while g.state == "match" and f < 30 * 400:
    me.update(1/30)
    m.update(1/30)
    if g.ai: g.ai.update(1/30)
    for a in g._extra_ais(): a.update(1/30)
    g._handle_events(m.take_events())
    if m.finished:
        g._on_match_end()
    f += 1
    if f == 1500:
        g._draw(); pygame.image.save(g.screen, os.path.join(HERE, "duo_mid.png"))
print("winner", m.winner, "crowns", m.crowns, "frames", f, "rewards", g.last_rewards)
assert g.state == "result"
assert g.profile.special["duo"]["plays"] == 1
print("mastery", {k: v for k, v in g.profile.mastery.items()})
assert all(g.profile.mastery[k]["w"] == (1 if m.winner == PLAYER else 0) for k in set(m.decks[PLAYER]))
g._draw(); pygame.image.save(g.screen, os.path.join(HERE, "duo_result.png"))
g.state = "stats"; g._draw(); pygame.image.save(g.screen, os.path.join(HERE, "duo_stats.png"))
# a normal battle afterwards: no 2v2 leftovers
g._begin_battle()
assert not g.match.is_2v2 and not g._extra_ais()
g._draw()
print("DUO OK")
# engine level: 4 AIs, every unit belongs to a seat of its own team, each
# seat plays from its own hand / elixir
import random as _r
from engine import Match
keys = sorted(c.key for c in __import__("cards").DEPLOYABLE_CARDS)
for seed in range(2):
    rng = _r.Random(seed)
    ds = [rng.sample(keys, 8) for _ in range(4)]
    m = Match(ds[0], ds[1])
    m.add_seats(ds[2], ds[3], 11, 11)
    ais = [AIController(m, s % 2, 3, seat=s) for s in range(4)]
    f = 0
    while not m.finished and f < 30 * 200:
        for a in ais: a.update(1 / 30)
        m.update(1 / 30); f += 1
        for e in m.entities:
            assert e.seat % 2 == e.team, (e.key, e.seat, e.team)
    plays = [sum(m.stats["played"][s].values()) for s in range(4)]
    print("2v2 AI game", seed, "winner", m.winner, "plays per seat", plays)
    assert all(p > 3 for p in plays), plays
    for s in range(4):
        assert set(m.stats["played"][s]) <= set(ds[s]), s     # only its own cards
print("2v2 ENGINE OK")
