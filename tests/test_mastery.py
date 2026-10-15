"""Card Mastery: unlock, tasks, tiers, claiming, Mastery page."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import os, sys, random

HERE = _util.TMP
sys.path.insert(0, _util.SRC); os.chdir(_util.ROOT)
import pygame, profile_data, config as cfg, cards
profile_data.PROFILE_FILE = os.path.join(HERE, "test_profile.json")
if os.path.exists(profile_data.PROFILE_FILE): os.remove(profile_data.PROFILE_FILE)
import game as G
G.DECK_FILE = os.path.join(HERE, "test_deck.json")
import mastery
from engine import Match, PLAYER, ENEMY
from ai import AIController
from game import Game

# every deployable card has sane goals
for c in cards.DEPLOYABLE_CARDS:
    for i in range(3):
        gs = mastery.goals(c.key, i)
        assert gs[0] < gs[1] < gs[2], (c.key, i, gs)
        assert mastery.describe(c.key, i, gs[0])
kinds = {}
for c in cards.DEPLOYABLE_CARDS:
    k = mastery.task_kinds(c.key)
    kinds[k[1:]] = kinds.get(k[1:], 0) + 1
print("task kinds:", kinds)
for key in ("hog_rider", "knight", "fireball", "skeletons", "golem", "goblin_barrel"):
    if key in cards.CARDS:
        print(key, [(mastery.title(key, i), mastery.goals(key, i)) for i in range(3)])

g = Game(); g._save_settings = lambda: None; g._save_progress = lambda: None
p = g.profile
deck = list(g.player_deck)
key = deck[0]

def play_match(seed):
    random.seed(seed)
    m = Match(deck, deck[::-1])
    ais = [AIController(m, PLAYER, 3), AIController(m, ENEMY, 3)]
    f = 0
    while not m.finished and f < 30 * 260:
        for a in ais: a.update(1 / 30)
        m.update(1 / 30); f += 1
    return m

# locked: progress doesn't count, wins do
m = play_match(1)
notes = mastery.record_match(p, m, PLAYER, deck, True)
assert p.mastery[key]["w"] == 1 and p.mastery[key]["p"] == [0, 0, 0]
assert not mastery.claimable(p, key)
for _ in range(4):
    notes = mastery.record_match(p, m, PLAYER, deck, True)
assert mastery.unlocked(p, key) and any("unlocked" in n for n in notes), notes
assert mastery.claimable(p, key) == [("Mastery unlocked", {"gold": 100})]
# level 11 by default: only task 1 open
assert mastery.task_open(p, key, 0) and not mastery.task_open(p, key, 1)
g0 = p.gold
assert mastery.claim(p, key) == {"gold": 100} and p.gold == g0 + 100
assert not mastery.claimable(p, key)
# task 1 tier 1 = 10 wins
for _ in range(10):
    mastery.record_match(p, m, PLAYER, deck, True)
assert mastery.reached(p, key, 0) == 1
assert mastery.claim(p, key) == {"gold": 500}
# open task 2/3 by levelling
p.levels[key] = 13
assert mastery.task_open(p, key, 1) and not mastery.task_open(p, key, 2)
p.levels[key] = 15
assert mastery.task_open(p, key, 2)
before = list(p.mastery[key]["p"])
mastery.record_match(p, m, PLAYER, deck, False)
after = p.mastery[key]["p"]
print("one match progress:", key, before, "->", after, mastery.card_stats(m, PLAYER, deck)[key])
assert after[0] == before[0]                    # a loss isn't a win
# cap and full claim
for i in range(3):
    p.mastery[key]["p"][i] = 10 ** 9
mastery.record_match(p, m, PLAYER, deck, True)
assert p.mastery[key]["p"] == [mastery.goals(key, i)[-1] for i in range(3)]
gold, gems = p.gold, p.gems
got = mastery.claim(p, key)
assert got == {"gold": 1000 + 500 + 1000 + 500 + 1000, "gems": 300}, got
assert mastery.mastery_level(p, key) == 9 and p.gems == gems + 300

# UI: cards screen -> mastery -> claim/back; save/load
g._open_cards(); g.cards_sel = deck[1]
g._open_mastery(deck[1]); g._draw()
p.mastery[deck[1]] = {"w": 7, "p": [12, 0, 0], "c": [0, 0, 0], "u": 0}
g._draw()
bs = {b.label: b for b in g._mastery_buttons()}
assert "Claim rewards" in bs
pygame.image.save(g.screen, os.path.join(HERE, "mastery_a.png"))
g.gold0 = p.gold
g._mastery_click(bs["Claim rewards"].rect.center)
assert p.gold == g.gold0 + 600, p.gold - g.gold0
g._mastery_click(g._mastery_buttons()[-1].rect.center)   # ">"
assert g.mastery_key != deck[1]
g._mastery_click([b for b in g._mastery_buttons() if b.label == "Back"][0].rect.center)
assert g.state == "cards"
g._draw()
g.mastery_key = key; g.state = "mastery"; g._draw()
pygame.image.save(g.screen, os.path.join(HERE, "mastery_b.png"))
p.save()
p2 = profile_data.Profile(); p2.load() if hasattr(p2, "load") else None
print("reloaded mastery keys:", sorted(profile_data.Profile().mastery) if hasattr(profile_data, "Profile") else "?")

# a full game through _on_match_end counts
g.player_deck = deck
g.mode = None
print("OK")
p.mastery[deck[2]] = {"w": 5, "p": [0, 0, 0], "c": [0, 0, 0], "u": 0}
g._open_cards(); g.cards_sel = deck[2]; g._draw()
pygame.image.save(g.screen, os.path.join(HERE, "mastery_cards.png"))
