"""Every Evolution and Hero plays out without errors."""
import _util  # noqa: F401  (sets up paths + a throw-away save folder)
import sys, random; sys.path.insert(0, _util.SRC)
import cards, evos, evo_engine
from engine import Match, PLAYER, ENEMY
random.seed(1)
problems = []
for key in sorted(evos.EVOS):
    m = Match(list(cards.DEFAULT_PLAYER_DECK), list(cards.DEFAULT_AI_DECK), evo_cards={PLAYER: [key]})
    c = cards.CARDS[key]
    # enemies to fight
    m.spawn_units(ENEMY, "knight", 1, 9, 12, deploy=0)
    m.spawn_units(ENEMY, "skeleton_army", 15, 6, 13, deploy=0)
    m.spawn_units(ENEMY, "minions", 3, 12, 13, deploy=0)
    m.elixir[PLAYER] = 10
    m.hands[PLAYER][0] = key
    y = 8 if c.category == "spell" else 18
    if c.category == "building": y = 19
    if key in ("goblin_barrel",): y = 6
    assert not m.evo_ready(PLAYER, key)          # charges start empty
    m.evo_charge[PLAYER][key] = evos.EVOS[key].cycles
    assert m.evo_ready(PLAYER, key)
    ok = m.play_card(PLAYER, 0, 9, y)
    evo_units = [e for e in m.entities if e.evo]
    try:
        for f in range(60 * 12):
            m.update(1/60)
    except Exception as ex:
        import traceback; traceback.print_exc(); problems.append(key); continue
    print("%-16s played=%s evo_units=%d charge=%s dmg=%d" % (key, ok, len(evo_units),
          m.evo_progress(PLAYER, key), sum(m.stats["dmg"][0].values())))
    assert ok and m.evo_progress(PLAYER, key)[0] == 0, key       # played as the Evolution
    if c.category != "spell":
        assert evo_units, key
for key in sorted(evos.HEROES):
    m = Match(list(cards.DEFAULT_PLAYER_DECK), list(cards.DEFAULT_AI_DECK), hero_cards={PLAYER: [key]})
    m.spawn_units(ENEMY, "knight", 1, 9, 15, deploy=0); m.spawn_units(ENEMY, "goblins", 3, 8, 15.5, deploy=0)
    m.elixir[PLAYER] = 10; m.hands[PLAYER][0] = key
    m.play_card(PLAYER, 0, 9, 18)
    for f in range(60 * 3): m.update(1/60)
    h, ready, cost = m.hero_status(PLAYER)
    act = m.activate_hero(PLAYER) if h else None
    try:
        for f in range(60 * 8): m.update(1/60)
    except Exception:
        import traceback; traceback.print_exc(); problems.append(key)
    assert h is not None, key
    print("hero %-12s on_field=%s ready=%s activated=%s uses_left=%s ents=%d" % (key, h is not None, ready, act, h.ability_uses if h else None, len(m.entities)))
print("PROBLEMS", problems)
assert not problems, problems
