"""Level-Up Potion: bought in the Shop for 3 Hero coins, drunk on a card in
the Cards screen; for one real hour the card plays at your King level."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import os
import time

import pygame
import cards
import king
import profile_data
import shop

profile_data.PROFILE_FILE = os.path.join(_util.TMP, "test_potion_profile.json")
if os.path.exists(profile_data.PROFILE_FILE):
    os.remove(profile_data.PROFILE_FILE)

p = profile_data.Profile()
# a King at level 14 (no rewards owed)
xp = 0
while king.level_for(xp) < 14:
    xp += 50
p.king_xp = xp
p.king_paid = king.chunks_reached(xp)
assert p.king_level() == 14
p.levels["musketeer"] = 12

# ---- buying
p.hero_coins = 5
assert shop.can_buy(p, shop.POTION)
assert shop.buy(p, shop.POTION)
assert p.hero_coins == 2 and p.potions == 1
assert not shop.can_buy(p, shop.POTION)            # 2 coins: not enough
assert not shop.buy(p, shop.POTION)
assert p.hero_coins == 2 and p.potions == 1

# ---- using it
now = 1_000_000.0
assert p.effective_level("musketeer", now) == 12
ok, msg = p.use_potion("musketeer", now)
assert ok, msg
assert p.potions == 0
assert p.effective_level("musketeer", now + 10) == 14
assert p.boosted("musketeer", now + 10)
assert abs(p.card_boost_left("musketeer", now + 60) - (3600 - 60)) < 1e-6
assert p.level("musketeer") == 12                   # the real level is untouched

# matches get the boosted level
real_time = time.time
time.time = lambda: now + 100
try:
    lv = p.deck_levels(["musketeer", "knight"])
    assert lv == {"musketeer": 14, "knight": 11}, lv
    from engine import Match, PLAYER
    m = Match(["musketeer", "knight"] * 4, list(cards.DEFAULT_AI_DECK),
              card_levels={PLAYER: lv})
    assert m.card_level(PLAYER, "musketeer") == 14
finally:
    time.time = real_time

# ---- expiry after an hour
assert p.effective_level("musketeer", now + 3599) == 14
assert p.effective_level("musketeer", now + 3601) == 12
assert p.card_boost_left("musketeer", now + 3601) == 0
p.clean_boosts(now + 3601)
assert "musketeer" not in p.potion_boosts

# ---- refused: no potion / already at King level / not a card
ok, msg = p.use_potion("knight", now)
assert not ok and "Shop" in msg
p.potions = 2
p.levels["valkyrie"] = 14
ok, msg = p.use_potion("valkyrie", now)
assert not ok and "King level" in msg and p.potions == 2
ok, msg = p.use_potion("not_a_card", now)
assert not ok and p.potions == 2
# a running boost restarts at a full hour (and costs the potion)
assert p.use_potion("knight", now)[0]
assert p.use_potion("knight", now + 1800)[0]
assert p.potions == 0
assert abs(p.card_boost_left("knight", now + 1800) - 3600) < 1e-6

# ---- saving / loading
p.potions = 3
p.potion_boosts = {"knight": time.time() + 1234, "archers": time.time() - 5}
p.save()
q = profile_data.Profile()
assert q.potions == 3
assert "knight" in q.potion_boosts and "archers" not in q.potion_boosts   # expired: gone
assert q.boosted("knight")
# an old save without the new fields loads with safe defaults
import json
with open(profile_data.PROFILE_FILE) as f:
    d = json.load(f)
d.pop("potions"); d.pop("potion_boosts")
with open(profile_data.PROFILE_FILE, "w") as f:
    json.dump(d, f)
r = profile_data.Profile()
assert r.potions == 0 and r.potion_boosts == {}

# ---- the game screens: buy in the Shop, drink in the Cards screen
import game as G
G.DECK_FILE = os.path.join(_util.TMP, "test_potion_deck.json")
from game import Game
g = Game()
g._save_settings = lambda: None
g._save_progress = lambda: None
g.profile = p
p.potions = 0
p.potion_boosts = {}
p.hero_coins = 3
g.state = "shop"
g._draw()
cell = [c for c in g._shop_layout()[0] if c[1][0] == "potion"][0][0]
g._shop_click(cell.center)
assert p.potions == 1 and p.hero_coins == 0
g._shop_click(cell.center)                      # can't afford a second
assert p.potions == 1 and "Hero coins" in g.shop_msg
g._open_cards()
g.cards_sel = "musketeer"
g._draw()
btn = [b for b in g._cards_buttons() if getattr(b, "kind", "") == "potion"][0]
assert btn.enabled
assert btn.click(btn.rect.center)
assert p.potions == 0 and p.boosted("musketeer"), g.cards_msg
g._draw()
assert "left" in g._potion_status("musketeer")[0]
g.cards_sel = "knight"
btn = [b for b in g._cards_buttons() if getattr(b, "kind", "") == "potion"][0]
assert not btn.enabled                          # no potions left
g._draw()
pygame.quit()
print("potion ok")
