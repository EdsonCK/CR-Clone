"""
============================================================================
  KING.PY  --  King Level: experience, the King's reward track, tower levels
============================================================================

Your KING LEVEL (11 -> 16, the same scale as card levels) is your King
Tower's level. It grows with EXPERIENCE (XP):

  * every card upgrade gives XP - the bigger the upgrade, the more
    (XP_PER_UPGRADE: a tenth of its gold cost);
  * achievements give XP when you claim them.

Each King level needs exponentially more XP than the last (KING_XP, doubling
every level) and the curve is set so that upgrading 24 cards all the way to
level 16 is about exactly enough for King level 16.

The road to every King level is split into 4 CHUNKS; reaching one pays a
reward (chunk_reward): gold, Evolution shards, Hero coins and - for the
level-up itself - gems.

Your PRINCESS TOWERS are as strong as the Tower Troop manning them, and Tower
Troops are upgraded with gold only (Profile.upgrade_troop) - never above
your King level.
============================================================================
"""

import cards

KING_MIN = cards.LEVEL_MIN          # 11
KING_MAX = cards.LEVEL_MAX          # 16

# XP for upgrading a card FROM this level (a tenth of the gold it costs)
XP_PER_UPGRADE = {11: 10, 12: 25, 13: 60, 14: 120, 15: 250}

# total XP needed to REACH each King level: 360 XP to level 12, then each
# level needs twice the XP of the one before (360, 720, 1440, 2880, 5760).
# 24 cards from 11 to 16 = 24 x 465 = 11160 XP = King level 16.
KING_XP = {11: 0, 12: 360, 13: 1080, 14: 2520, 15: 5400, 16: 11160}

CHUNKS = 4                          # rewards on the way to each level

# Tower Troop upgrades: gold, like cards (but no XP)
TOWER_UPGRADE_COST = {11: 100, 12: 250, 13: 600, 14: 1200, 15: 2500}


def level_for(xp):
    lv = KING_MIN
    for n in range(KING_MIN + 1, KING_MAX + 1):
        if xp >= KING_XP[n]:
            lv = n
    return lv


def progress(xp):
    """(level, xp into this level, xp this level needs) - needs is 0 at max."""
    lv = level_for(xp)
    if lv >= KING_MAX:
        return lv, xp - KING_XP[KING_MAX], 0
    return lv, xp - KING_XP[lv], KING_XP[lv + 1] - KING_XP[lv]


def chunk_count():
    return (KING_MAX - KING_MIN) * CHUNKS


def chunk_threshold(i):
    """XP at which reward chunk i (0-based) is reached."""
    n = KING_MIN + 1 + i // CHUNKS          # the level this chunk leads to
    j = i % CHUNKS + 1
    lo, hi = KING_XP[n - 1], KING_XP[n]
    return lo + (hi - lo) * j // CHUNKS


def chunk_level(i):
    return KING_MIN + 1 + i // CHUNKS


def chunks_reached(xp):
    return sum(1 for i in range(chunk_count()) if xp >= chunk_threshold(i))


def chunk_reward(i):
    """Reward dict for chunk i: gold -> Evo shards -> Hero coins -> gems
    (the level-up), growing with the level."""
    k = chunk_level(i) - KING_MIN            # 1..5
    j = i % CHUNKS
    if j == 0:
        return {"gold": 300 * k}
    if j == 1:
        return {"shards": k}
    if j == 2:
        return {"coins": k + 1}
    return {"gems": 50 * k, "gold": 200 * k}


def card_xp(levels):
    """XP already earned by cards at these levels ({key: level})."""
    total = 0
    for lv in levels.values():
        for n in range(KING_MIN, min(lv, KING_MAX)):
            total += XP_PER_UPGRADE[n]
    return total
