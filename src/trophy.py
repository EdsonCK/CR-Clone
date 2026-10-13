"""
============================================================================
  TROPHY.PY  --  The Trophy Road (arenas, trophies, who you play)
============================================================================

Trophy Road battles are the "ranked ladder": you win trophies for a win
and lose some for a loss, and your trophy count picks your opponent - the
higher you climb, the smarter the AI and the higher its card levels.

  * ARENAS are the real game's first 15 (Goblin Stadium -> Miner's Mine)
    plus the Legendary Arena at the top. You can never drop below the
    trophy gate of an arena you've reached.
  * Every arena has its bot intelligence (Novice -> Master) and a card
    level (11 -> 16); the bot's cards are never more than one level above
    your crown towers, so upgrading still matters but you can't be
    stonewalled.
  * Bots play VARIATIONS of the archetype decks (cards.deck_variant) and
    bring no Evolutions / Heroes at first, up to 2 Evos + a Hero from
    SPECIALS_FULL_AT trophies (bot_specials).
  * REWARDS line the road: gold every 100 trophies, shards at each new
    arena, and the Tower Troops unlock where they do in Clash Royale
    (Cannoneer: Frozen Peak, Dagger Duchess: Electro Valley, Royal Chef:
    Rascal's Hideout).

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
    Arena(300, "Bone Pit", 1, (170, 168, 176)),
    Arena(600, "Barbarian Bowl", 2, (200, 150, 80)),
    Arena(1000, "Spell Valley", 2, (150, 110, 220)),
    Arena(1300, "Builder's Workshop", 3, (110, 150, 190)),
    Arena(1600, "P.E.K.K.A's Playhouse", 3, (80, 100, 160)),
    Arena(2000, "Royal Arena", 3, (230, 190, 70)),
    Arena(2300, "Frozen Peak", 4, (170, 220, 250)),
    Arena(2600, "Jungle Arena", 4, (90, 170, 90)),
    Arena(3000, "Hog Mountain", 4, (220, 150, 120)),
    Arena(3400, "Electro Valley", 5, (110, 214, 255)),
    Arena(3800, "Spooky Town", 5, (140, 100, 170)),
    Arena(4200, "Rascal's Hideout", 5, (210, 120, 60)),
    Arena(4600, "Serenity Peak", 5, (120, 200, 190)),
    Arena(5000, "Miner's Mine", 5, (240, 190, 50)),
    Arena(5500, "Legendary Arena", 5, (255, 210, 90)),
]

WIN_TROPHIES = 60        # + a small bonus per crown margin
LOSS_TROPHIES = 20
CROWN_BONUS = 4
SPECIALS_FULL_AT = 2750  # bots bring a full set of Evos + Hero from here on


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


def bot_card_level(trophies, player_tower_level):
    """AI card level: +1 per 1000 trophies (11 -> 16), at most one above
    your towers."""
    lv = cards.LEVEL_BASE + trophies // 1000
    return max(cards.LEVEL_MIN, min(cards.LEVEL_MAX, lv, player_tower_level + 1))


def trophy_change(win, crowns_for, crowns_against, trophies):
    """Trophies won / lost for one battle (losses never cross an arena gate)."""
    if win is None:
        return 0
    if win:
        return WIN_TROPHIES + CROWN_BONUS * max(0, crowns_for - crowns_against)
    floor = arena(trophies).trophies
    return -min(LOSS_TROPHIES, max(0, trophies - floor))


def road_rewards():
    """[(trophies, label, gold, shards, tower_troop or None)] along the road."""
    out = []
    unlocks = {t.unlock: t.key for t in towers.TOWER_TROOPS.values() if t.unlock}
    gates = {a.trophies: a for a in ARENAS}
    top = ARENAS[-1].trophies + 500
    for t in range(100, top + 1, 100):
        if t in gates:
            a = gates[t]
            out.append((t, a.name, 150 + t // 15, 3, unlocks.get(t)))
        else:
            out.append((t, "Road reward", 40 + t // 40, 0, None))
    return out


def tower_troop_unlocked(key, best_trophies):
    return best_trophies >= towers.get(key).unlock
