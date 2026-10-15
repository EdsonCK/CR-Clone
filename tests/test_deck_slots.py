"""Evolution / flex / Hero deck slots."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import os, sys

sys.path.insert(0, _util.SRC); os.chdir(_util.ROOT)
import pygame, profile_data, cards, evos
S = _util.TMP
profile_data.PROFILE_FILE = os.path.join(S, "test_profile.json")
if os.path.exists(profile_data.PROFILE_FILE): os.remove(profile_data.PROFILE_FILE)
import game as G
G.DECK_FILE = os.path.join(S, "test_deck.json")
from game import Game
g = Game(); g._save_settings = lambda: None; g._save_progress = lambda: None
both = sorted(set(evos.EVOS) & set(evos.HEROES))
eo = sorted(set(evos.EVOS) - set(evos.HEROES)); ho = sorted(set(evos.HEROES) - set(evos.EVOS))
pr = g.profile
pr.evos = eo[:3] + both[:1]; pr.heroes = ho[:3] + both[:1]
filler = [c.key for c in cards.DEPLOYABLE_CARDS if c.key not in evos.EVOS and c.key not in evos.HEROES][:5]
def sp(d):
    e, h = g._special_cards(d + filler); return sorted(e), sorted(h)
print("evo,evo,evo:", sp([eo[0], eo[1], eo[2]])); assert sp([eo[0], eo[1], eo[2]]) == ([eo[0], eo[1]], [])
print("evo,hero,hero:", sp([eo[0], ho[0], ho[1]])); assert sp([eo[0], ho[0], ho[1]]) == ([eo[0]], sorted([ho[0], ho[1]]))
print("hero,evo,evo (wrong slots):", sp([ho[0], eo[0], eo[1]])); assert sp([ho[0], eo[0], eo[1]]) == ([eo[0]], [])
print("evo,both,hero:", sp([eo[0], both[0], ho[0]]))
# AI fairness: player 2 evos + hero -> AI total 3
sp2 = g._match_specials([eo[0], eo[1], ho[0]] + filler, [eo[2], ho[1], ho[2]] + filler)
print("AI gets", sp2["evo_cards"][1], sp2["hero_cards"][1]); assert len(sp2["evo_cards"][1]) + len(sp2["hero_cards"][1]) == 3
# preset decks honour slots
for n, d in cards.AI_DECK_PRESETS.items():
    ae, ah = g._special_cards(d, owned=False)
    assert len(ae) <= 2 and len(ah) <= 2 and len(ae) + len(ah) <= 3, (n, ae, ah)
g.player_deck[:] = [eo[0], both[0], ho[0]] + filler; g.deck_mode = "player"; g.state = "deck"
print("tags", [g._slot_tag(i, k) for i, k in enumerate(g.player_deck[:3])])
g._draw(); pygame.image.save(g.screen, os.path.join(S, "slots_deck.png"))
print("SLOTS OK")
