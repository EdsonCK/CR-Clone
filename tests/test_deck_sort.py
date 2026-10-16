"""Deck builders: sort the collection by level / elixir / rarity / times used,
up-down arrow flips the order; 'times used' counts your plays in matches."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import cards
import game as G
from engine import PLAYER

g = G.Game()
p = g.profile
p.levels["giant"] = 15
p.card_plays["hog_rider"] = 40


def click(k):
    g._deck_click([r for r, kk in g._deck_sort_rects() if kk == k][0].center)


for mode in ("player", "level", "ai"):
    g._open_deck_editor(mode, "menu")
    click("level")
    assert g.opt_deck_sort == "level" and g.opt_deck_desc
    assert g._deck_cards()[0].key == "giant"
    click("order")
    assert not g.opt_deck_desc and g._deck_cards()[-1].key == "giant"
    click("used")
    assert g._deck_cards()[0].key == "hog_rider"
    click("rarity")
    assert g._deck_cards()[0].rarity == "champion"
    click("rarity")                              # tap again: flips
    assert g._deck_cards()[0].rarity == "common"
    click("elixir")
    el = [c.elixir for c in g._deck_cards()]
    assert el == sorted(el)
    # the grid follows the sorted order and a click still adds that card
    r, card = g._deck_grid()[0]
    assert card is g._deck_cards()[0]
    g._draw()
    print(mode, "ok")
# times used: counted at the end of every match
before = dict(p.card_plays)
g._begin_battle()
m = g.match
m.elixir[PLAYER] = 10
k = m.hands[PLAYER][0]
assert m.play_card(PLAYER, 0, 9.5, 24.5)
m._finish(PLAYER)
g._on_match_end()
assert p.card_plays.get(k, 0) == before.get(k, 0) + 1, (k, p.card_plays.get(k))
print("DECK SORT OK")
