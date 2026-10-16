"""Special Battles and 2v2 are played at Tournament Standard: every card and
tower of every player at level 11, whatever your own levels are."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import cards
import game as G
import modes
import profile_data
from engine import PLAYER, ENEMY

g = G.Game()
g._save_settings = lambda: None
p = g.profile
for k in g.player_deck:                       # an upgraded player...
    p.levels[k] = 15
p.troop_levels = {t: 14 for t in ("tower_princess", "cannoneer", "dagger_duchess", "royal_chef")}
p.king_xp = 10 ** 6                           # ...with a maxed King
L = profile_data.SPECIAL_AI_LEVEL
assert L == 11
for key, *_ in modes.MODES:
    if key in ("endless",):
        continue
    if key == "draft":
        g._start_draft()
        while g.state == "draft":
            g._draft_click(g._draft_rects()[0].center)
    else:
        g._start_mode(key)
    m = g.match
    seats = range(len(m.hands))
    for s in seats:
        for c in m.decks[s]:
            assert m.card_level(s % 2, c) == L or s >= 2, (key, s, c, m.card_level(s % 2, c))
    for (team, side), tw in m.towers.items():
        extra = 7 if key == "double" else 0
        assert tw.level == L + extra, (key, team, side, tw.level)
    if m.is_2v2:
        assert m.card_levels[2] == L and m.card_levels[3] == L
    # a played card comes out at level 11
    m.elixir[PLAYER] = 10
    k = m.hands[PLAYER][0]
    if cards.CARDS[m.play_key(PLAYER, k)].category != "spell":
        n0 = len(m.entities)
        m.play_card(PLAYER, 0, 9.5, 24.5)
        new = m.entities[n0:]
        assert all(e.level in (None, L) for e in new), (key, k, [e.level for e in new])
    print("%-8s ok" % key)
# Battles and Trophy Road still use your real levels
g._begin_battle()
assert g.match.card_level(PLAYER, g.player_deck[0]) == 15
print("TOURNAMENT OK")
