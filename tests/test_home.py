"""Tabbed home screen, deck tab, Trophy Road battles."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import os, sys, random

sys.path.insert(0, _util.SRC); os.chdir(_util.ROOT)
import pygame, profile_data, config as cfg, cards, trophy
profile_data.PROFILE_FILE = os.path.join(_util.TMP, "test_profile.json")
if os.path.exists(profile_data.PROFILE_FILE): os.remove(profile_data.PROFILE_FILE)
import game as G
G.DECK_FILE = os.path.join(_util.TMP, "test_deck.json")
from engine import PLAYER, ENEMY
from game import Game
g = Game(); g._save_settings = lambda: None; g._save_progress = lambda: None
def post(t, **kw): pygame.event.post(pygame.event.Event(t, **kw)); g._events(0)
def click(pos, b=1): post(pygame.MOUSEBUTTONDOWN, pos=pos, button=b); post(pygame.MOUSEBUTTONUP, pos=pos, button=b)
def btn(bs, lbl): return [b for b in bs if b.label == lbl][0].rect.center
assert cfg.WINDOW_W == 540 and cfg.WINDOW_H == 800
g.state = "menu"
for lbl, st in (("Shop", "shop"), ("Deck", "deck"), ("Levels", "levels"), ("Modes", "modes"), ("Battle Tab", "menu")):
    click(btn(g.menu_buttons, lbl)); assert g.state == st, (lbl, g.state); g._draw()
# deck tab: remove a card, add another -> saved to the profile slot
click(btn(g.menu_buttons, "Deck")); assert g._home_active()
area = g._home_content()
with g._embedded():
    slot0 = g._deck_slot_rects()[0]
removed = g.player_deck[0]
click((slot0.centerx, slot0.centery + area.y))
assert len(g.player_deck) == 7
with g._embedded():
    grid = g._deck_grid()
    r, c = [(r, c) for r, c in grid if c.key not in g.player_deck and r.y > 0][0]
click((r.centerx, r.centery + area.y)); assert len(g.player_deck) == 8
assert g.profile.decks[g.profile.active_slot]["cards"] == g.player_deck, "deck tab autosaves"
post(pygame.MOUSEWHEEL, x=0, y=-3, flipped=False); assert g.deck_scroll > 0
g._draw()
# levels tab wheel clamps to the embedded height
click(btn(g.menu_buttons, "Levels")); post(pygame.MOUSEWHEEL, x=0, y=-100, flipped=False)
with g._embedded(): assert g.levels_scroll == g._levels_max_scroll()
g._draw()
# ESC from a tab -> Battle tab; dropdown items
post(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode="", scancode=0); assert g.state == "menu"
click(btn(g.menu_buttons, "Menu")); assert g.dropdown; g._draw()
click(btn(g._dropdown_items(), "Settings")); assert g.state == "settings" and not g.dropdown
g.state = "menu"; click(btn(g.menu_buttons, "Menu")); click(btn(g._dropdown_items(), "Records")); assert g.state == "records"
g.state = "menu"; click(btn(g.menu_buttons, "Menu")); click((5, 400)); assert not g.dropdown and g.state == "menu"
# battle tab: Battle -> trophy match; bot specials by trophies
for t, want in ((0, (0, 0)), (1700, (1, 0)), (3400, (1, 1)), (5000, (2, 1)), (9000, (2, 1))):
    assert trophy.bot_specials(t) == want, (t, trophy.bot_specials(t))
g.profile.trophies = 0
click(btn(g.menu_buttons, "Battle")); assert g.state == "match" and g.mode == "trophy"
assert not g.match.evo_cards[ENEMY] and not g.match.hero_cards[ENEMY]
g.match.finished = True; g.match.winner = PLAYER; g.match.crowns = [1, 0]; g._on_match_end()
assert g.profile.trophies == 64, g.profile.trophies       # 60 + 4 per crown margin
g.profile.trophies = 3000; g.state = "menu"; random.seed(5)
click(btn(g.menu_buttons, "Battle"))
print("bot deck", g.trophy_deck_name, g.match.decks[ENEMY] if hasattr(g.match, "decks") else "", "evos", g.match.evo_cards[ENEMY], "hero", g.match.hero_cards[ENEMY])
g._draw()
print("HOME TEST PASSED")
