"""
============================================================================
  TROPHY.PY  --  The Trophy Road (arenas, trophies, who you play)
============================================================================

Trophy Road battles are the "ranked ladder": you win trophies for a win
and lose some for a loss, and your trophy count picks your opponent - the
higher you climb, the smarter the AI and the higher its card levels.

  * ARENAS: a new one every 500 trophies, from Goblin Stadium (0) to Clash
    Fest (10,000); the Legendary Arena is at 6000. You can never drop
    below the trophy gate of an arena you've reached.
  * Every arena has its bot intelligence (Novice -> Master) and a card
    level (11 -> 16, +1 per 1000 trophies); below 5000 trophies the bot's
    cards are never more than one level above your deck's, from 5000 on
    they're always level 16 (bot_card_level).
  * From 5500 trophies every new arena gives the bot +5% elixir (up to
    +50% at 10,000) - bot_elixir().
  * Bots play VARIATIONS of the archetype decks (cards.deck_variant) and
    bring no Evolutions / Heroes at first, up to 2 Evos + a Hero from
    SPECIALS_FULL_AT trophies (bot_specials).
  * REWARDS line the road: gold every 100 trophies; each new arena adds
    gems and Evo shards or Hero coins (taking turns), and the Tower Troops
    unlock at the arenas where they do in Clash Royale (Cannoneer: Frozen
    Peak, Dagger Duchess: Electro Valley, Royal Chef: Rascal's Hideout).

Tune the road here: ARENAS, WIN_TROPHIES / LOSS_TROPHIES and road_rewards().
============================================================================
"""

from dataclasses import dataclass

import cards
import towers


@dataclass
class Arena:
    trophies: int        # gate
    name: str
    ai: int              # AI intelligence 1-5
    color: tuple


ARENAS = [
    Arena(0, "Goblin Stadium", 1, (110, 190, 80)),
    Arena(500, "Bone Pit", 1, (170, 168, 176)),
    Arena(1000, "Barbarian Bowl", 2, (200, 150, 80)),
    Arena(1500, "Spell Valley", 2, (150, 110, 220)),
    Arena(2000, "Builder's Workshop", 3, (110, 150, 190)),
    Arena(2500, "P.E.K.K.A's Playhouse", 3, (80, 100, 160)),
    Arena(3000, "Royal Arena", 3, (230, 190, 70)),
    Arena(3500, "Frozen Peak", 4, (170, 220, 250)),
    Arena(4000, "Jungle Arena", 4, (90, 170, 90)),
    Arena(4500, "Hog Mountain", 4, (220, 150, 120)),
    Arena(5000, "Electro Valley", 5, (110, 214, 255)),
    Arena(5500, "Spooky Town", 5, (140, 100, 170)),
    Arena(6000, "Legendary Arena", 5, (255, 210, 90)),
    Arena(6500, "Rascal's Hideout", 5, (210, 120, 60)),
    Arena(7000, "Serenity Peak", 5, (120, 200, 190)),
    Arena(7500, "Miner's Mine", 5, (240, 190, 50)),
    Arena(8000, "Executioner's Kitchen", 5, (200, 90, 80)),
    Arena(8500, "Royal Crypt", 5, (120, 120, 150)),
    Arena(9000, "Silent Sanctuary", 5, (170, 200, 230)),
    Arena(9500, "Dragon Spa", 5, (230, 120, 170)),
    Arena(10000, "Clash Fest", 5, (255, 160, 60)),
]

LEGENDARY_AT = 6000
WIN_TROPHIES = 60        # + a small bonus per crown margin
LOSS_TROPHIES = 20
CROWN_BONUS = 4
SPECIALS_FULL_AT = 5000  # bots bring a full set of Evos + Hero from here on
MAX_LEVEL_AT = 5000      # bots' cards are level 16 from here on
ELIXIR_FROM = 5500       # +5% bot elixir per arena from here on
ELIXIR_STEP = 0.05


def arena_index(trophies):
    i = 0
    for k, a in enumerate(ARENAS):
        if trophies >= a.trophies:
            i = k
    return i


def arena(trophies):
    return ARENAS[arena_index(trophies)]


def next_arena(trophies):
    i = arena_index(trophies)
    return ARENAS[i + 1] if i + 1 < len(ARENAS) else None


def bot_level(trophies):
    """AI intelligence for this trophy count."""
    return arena(trophies).ai


def bot_specials(trophies):
    """(evolutions, heroes) a Trophy Road bot brings: none at the start of the
    road, growing to the full 2 Evolutions + 1 Hero by SPECIALS_FULL_AT
    (about halfway) and staying there."""
    n = min(3, int(3 * trophies / SPECIALS_FULL_AT))
    return {0: (0, 0), 1: (1, 0), 2: (1, 1), 3: (2, 1)}[n]


def bot_card_level(trophies, player_deck_level):
    """AI card level: +1 per 1000 trophies (11 -> 16); below MAX_LEVEL_AT
    at most one above your deck's level, from there always level 16."""
    if trophies >= MAX_LEVEL_AT:
        return cards.LEVEL_MAX
    lv = cards.LEVEL_BASE + trophies // 1000
    return max(cards.LEVEL_MIN, min(cards.LEVEL_MAX, lv, player_deck_level + 1))


def bot_elixir(trophies):
    """Bot elixir multiplier: 1.0, then +5% for every arena from
    ELIXIR_FROM up (1.5x at 10,000)."""
    n = sum(1 for a in ARENAS if a.trophies >= ELIXIR_FROM and trophies >= a.trophies)
    return 1.0 + ELIXIR_STEP * n


def trophy_change(win, crowns_for, crowns_against, trophies):
    """Trophies won / lost for one battle (losses never cross an arena gate)."""
    if win is None:
        return 0
    if win:
        return WIN_TROPHIES + CROWN_BONUS * max(0, crowns_for - crowns_against)
    floor = arena(trophies).trophies
    return -min(LOSS_TROPHIES, max(0, trophies - floor))


def road_rewards():
    """[(trophies, label, reward dict, tower_troop or None)] along the road.
    The reward dict has gold and, at arenas, gems plus Evo shards or Hero
    coins (alternating)."""
    out = []
    unlocks = {t.unlock: t.key for t in towers.TOWER_TROOPS.values() if t.unlock}
    gates = {a.trophies: (i, a) for i, a in enumerate(ARENAS)}
    top = ARENAS[-1].trophies + 500
    for t in range(100, top + 1, 100):
        if t in gates:
            i, a = gates[t]
            rw = {"gold": 150 + t // 15, "gems": 20 + 5 * i}
            rw["shards" if i % 2 else "coins"] = 3
            if t == LEGENDARY_AT:
                rw["gems"] += 100
            out.append((t, a.name, rw, unlocks.get(t)))
        else:
            out.append((t, "Road reward", {"gold": 40 + t // 40}, None))
    return out


def tower_troop_unlocked(key, best_trophies):
    return best_trophies >= towers.get(key).unlock
