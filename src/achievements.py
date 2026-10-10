"""
============================================================================
  ACHIEVEMENTS.PY  --  Milestones with gold / shard rewards
============================================================================

Each achievement measures something you've done (from profile.json,
progress.json and records.json) and pays out once when you press Claim on
the Achievements screen. Add your own by appending to ACHIEVEMENTS:

    (id, title, description, (gold, shards), progress_function)

where progress_function(game) returns (current, goal).

Also here: the FIRST WIN OF THE DAY bonus (any mode) - see daily_bonus().
============================================================================
"""

import datetime

import cards
import levels
import modes

DAILY_GOLD = 60
DAILY_SHARDS = 1


def _tot(g, key):
    return g.profile.totals.get(key, 0)


def _stars(g):
    return sum(g.progress.get(lv.key, {}).get("stars", 0) for lv in levels.LEVELS)


def _three_star(g):
    return sum(1 for lv in levels.LEVELS if g.progress.get(lv.key, {}).get("stars", 0) >= 3)


def _cleared(g, n):
    return 1 if g.progress.get(levels.LEVELS[n - 1].key, {}).get("stars", 0) else 0


def _even_win(g, lv):
    return min(1, g.stats.get("L%d" % lv, {}).get("even_w", 0))


def _max_level(g):
    return max([g.profile.level(c.key) for c in cards.DEPLOYABLE_CARDS] or [11])


def _modes_won(g):
    return sum(1 for k, _, _, _ in modes.MODES
               if k != "endless" and g.profile.special.get(k, {}).get("wins", 0))


ACHIEVEMENTS = [
    ("win1", "First Blood", "Win a Battle against the AI.", (50, 0),
     lambda g: (min(1, _tot(g, "battle_wins")), 1)),
    ("win10", "Veteran", "Win 10 Battles.", (200, 1),
     lambda g: (_tot(g, "battle_wins"), 10)),
    ("win50", "Warlord", "Win 50 Battles.", (800, 3),
     lambda g: (_tot(g, "battle_wins"), 50)),
    ("expert", "Outsmarted", "Beat the Expert AI at 1.0x elixir or more.", (300, 2),
     lambda g: (_even_win(g, 4), 1)),
    ("master", "Grandmaster", "Beat the Master AI at 1.0x elixir or more.", (600, 3),
     lambda g: (_even_win(g, 5), 1)),
    ("lv5", "Crypt Keeper", "Clear Level 5.", (150, 1), lambda g: (_cleared(g, 5), 1)),
    ("lv10", "Halfway There", "Clear Level 10.", (300, 2), lambda g: (_cleared(g, 10), 1)),
    ("lv20", "The Last Siege", "Clear Level 20.", (1000, 5), lambda g: (_cleared(g, 20), 1)),
    ("stars30", "Star Collector", "Earn 30 Level stars.", (300, 2), lambda g: (_stars(g), 30)),
    ("stars60", "Perfectionist", "Earn all 60 Level stars.", (1500, 5),
     lambda g: (_stars(g), 60)),
    ("three5", "Flawless", "3-star 5 Levels.", (200, 1), lambda g: (_three_star(g), 5)),
    ("endless10", "Survivor", "Reach wave 10 in Endless Survival.", (250, 2),
     lambda g: (g.profile.endless_best, 10)),
    ("endless20", "Unbreakable", "Reach wave 20 in Endless Survival.", (800, 4),
     lambda g: (g.profile.endless_best, 20)),
    ("modes3", "Mode Hopper", "Win 3 different Special Battles.", (200, 1),
     lambda g: (_modes_won(g), 3)),
    ("modes7", "Jack of All Modes", "Win all 7 Special Battles.", (600, 3),
     lambda g: (_modes_won(g), 7)),
    ("up1", "Getting Stronger", "Upgrade a card.", (40, 0),
     lambda g: (min(1, _tot(g, "upgrades")), 1)),
    ("up25", "Smith", "Make 25 card upgrades.", (400, 2), lambda g: (_tot(g, "upgrades"), 25)),
    ("max", "Maxed Out", "Get a card to level 16.", (500, 3), lambda g: (_max_level(g), 16)),
    ("evo1", "Evolution", "Unlock an Evolution.", (100, 0),
     lambda g: (min(1, len(g.profile.evos)), 1)),
    ("hero1", "Heroic", "Unlock a Hero.", (100, 0),
     lambda g: (min(1, len(g.profile.heroes)), 1)),
    ("evoplay", "Evolved", "Play 25 evolved cards.", (250, 2),
     lambda g: (_tot(g, "evo_plays"), 25)),
    ("tr1000", "Climber", "Reach 1000 trophies on the Trophy Road.", (200, 1),
     lambda g: (g.profile.best_trophies, 1000)),
    ("tr2300", "Frozen Peak", "Reach Frozen Peak (2300 trophies).", (400, 2),
     lambda g: (g.profile.best_trophies, 2300)),
    ("tr5500", "Legend", "Reach the Legendary Arena (5500 trophies).", (1500, 5),
     lambda g: (g.profile.best_trophies, 5500)),
    ("crowns100", "Crown Hoarder", "Take 100 crowns in Battles.", (400, 2),
     lambda g: (sum(r.get("cf", 0) for r in g.stats.values() if isinstance(r, dict)), 100)),
]


def status(g):
    """[(id, title, desc, reward, cur, goal, done, claimed)]"""
    out = []
    claimed = set(g.profile.totals.get("claimed", []))
    for aid, title, desc, reward, fn in ACHIEVEMENTS:
        try:
            cur, goal = fn(g)
        except Exception:
            cur, goal = 0, 1
        out.append((aid, title, desc, reward, min(cur, goal), goal, cur >= goal,
                    aid in claimed))
    return out


def claimable(g):
    return sum(1 for a in status(g) if a[6] and not a[7])


def claim(g, aid):
    for a in status(g):
        if a[0] == aid and a[6] and not a[7]:
            gold, shards = a[3]
            g.profile.add(gold, shards)
            g.profile.totals.setdefault("claimed", []).append(aid)
            g.profile.save()
            return a
    return None


def daily_bonus(g):
    """First win of the day: returns True (and pays) once per calendar day."""
    today = datetime.date.today().isoformat()
    if g.profile.totals.get("daily") == today:
        return False
    g.profile.totals["daily"] = today
    return True
