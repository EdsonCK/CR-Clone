"""
============================================================================
  ACHIEVEMENTS.PY  --  Milestones with rewards
============================================================================

Each achievement measures something you've done (from profile.json,
progress.json and records.json) and pays out once when you press Claim on
the Achievements screen. Add your own by appending to ACHIEVEMENTS:

    (id, title, description, reward, progress_function)

where reward is R(gold, shards, coins, gems, xp) - Evo shards, Hero coins,
gems and King XP - and progress_function(game) returns (current, goal).
The biggest milestones pay the most gems.

Also here: the FIRST WIN OF THE DAY bonus (any mode) - see daily_bonus().
============================================================================
"""

import datetime

import cards
import evos
import king
import levels
import modes
import towers

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


def R(gold=0, shards=0, coins=0, gems=0, xp=0):
    return {k: v for k, v in (("gold", gold), ("shards", shards), ("coins", coins),
                              ("gems", gems), ("xp", xp)) if v}


def _maxed(g):
    return sum(1 for c in cards.DEPLOYABLE_CARDS if g.profile.level(c.key) >= 16)


def _crowns(g):
    return sum(r.get("cf", 0) for r in g.stats.values() if isinstance(r, dict))


def _troop_max(g):
    return max(g.profile.troop_level(k) for k in towers.ORDER)


ACHIEVEMENTS = [
    # ---- battles ----
    ("win1", "First Blood", "Win a Battle.", R(50, xp=10),
     lambda g: (min(1, _tot(g, "battle_wins")), 1)),
    ("win10", "Veteran", "Win 10 Battles.", R(200, 1, 1, xp=30),
     lambda g: (_tot(g, "battle_wins"), 10)),
    ("win50", "Warlord", "Win 50 Battles.", R(800, 3, 2, 30, 80),
     lambda g: (_tot(g, "battle_wins"), 50)),
    ("win100", "Conqueror", "Win 100 Battles.", R(1500, 3, 3, 80, 120),
     lambda g: (_tot(g, "battle_wins"), 100)),
    ("win250", "Unstoppable", "Win 250 Battles.", R(3000, 5, 5, 200, 200),
     lambda g: (_tot(g, "battle_wins"), 250)),
    ("three1", "Three-Crown", "Win a Battle with all 3 crowns.", R(150, 1, xp=20),
     lambda g: (min(1, _tot(g, "three_crowns")), 1)),
    ("three25", "Crown Crusher", "Win 25 Battles with 3 crowns.", R(1000, 2, 2, 60, 80),
     lambda g: (_tot(g, "three_crowns"), 25)),
    ("crowns100", "Crown Hoarder", "Take 100 crowns in Battles.", R(400, 2, 1, xp=50),
     lambda g: (_crowns(g), 100)),
    ("crowns500", "Crown Collector", "Take 500 crowns in Battles.", R(1500, 3, 3, 100, 120),
     lambda g: (_crowns(g), 500)),
    ("expert", "Outsmarted", "Beat the Expert AI at 1.0x elixir or more.", R(300, 2, 1, xp=40),
     lambda g: (_even_win(g, 4), 1)),
    ("master", "Grandmaster", "Beat the Master AI at 1.0x elixir or more.",
     R(600, 3, 2, 50, 60), lambda g: (_even_win(g, 5), 1)),
    # ---- Trophy Road ----
    ("tr1000", "Climber", "Reach 1000 trophies on the Trophy Road.", R(200, 1, 1, xp=30),
     lambda g: (g.profile.best_trophies, 1000)),
    ("tr2300", "Frozen Peak", "Reach Frozen Peak (3500 trophies).", R(400, 2, 2, 30, 50),
     lambda g: (g.profile.best_trophies, 3500)),
    ("tr5000", "Electrified", "Reach Electro Valley (5000 trophies).", R(800, 3, 3, 60, 80),
     lambda g: (g.profile.best_trophies, 5000)),
    ("tr5500", "Legend", "Reach the Legendary Arena (6000 trophies).",
     R(1500, 5, 5, 300, 150), lambda g: (g.profile.best_trophies, 6000)),
    ("tr8000", "Kitchen Nightmare", "Reach Executioner's Kitchen (8000 trophies).",
     R(2500, 5, 5, 400, 200), lambda g: (g.profile.best_trophies, 8000)),
    ("tr10000", "Clash Fest", "Reach 10,000 trophies - the top of the road.",
     R(5000, 10, 10, 1000, 300), lambda g: (g.profile.best_trophies, 10000)),
    # ---- Levels ----
    ("lv5", "Crypt Keeper", "Clear Level 5.", R(150, 1, xp=20), lambda g: (_cleared(g, 5), 1)),
    ("lv10", "Halfway There", "Clear Level 10.", R(300, 2, 1, xp=40),
     lambda g: (_cleared(g, 10), 1)),
    ("lv20", "The Last Siege", "Clear Level 20.", R(1000, 5, 2, 60, 80),
     lambda g: (_cleared(g, 20), 1)),
    ("lv30", "Grand Finale", "Clear Level 30.", R(2000, 6, 4, 200, 120),
     lambda g: (_cleared(g, 30), 1)),
    ("stars30", "Star Collector", "Earn 30 Level stars.", R(300, 2, 1, xp=40),
     lambda g: (_stars(g), 30)),
    ("stars60", "Perfectionist", "Earn 60 Level stars.", R(1500, 5, 2, 100, 100),
     lambda g: (_stars(g), 60)),
    ("stars90", "Flawless Victory", "Earn all 90 Level stars.", R(3000, 8, 6, 400, 200),
     lambda g: (_stars(g), 90)),
    ("three5", "Flawless", "3-star 5 Levels.", R(200, 1, xp=30), lambda g: (_three_star(g), 5)),
    ("three15", "Precision", "3-star 15 Levels.", R(800, 2, 2, 50, 60),
     lambda g: (_three_star(g), 15)),
    # ---- Modes ----
    ("endless10", "Survivor", "Reach wave 10 in Endless Survival.", R(250, 1, 2, xp=30),
     lambda g: (g.profile.endless_best, 10)),
    ("endless20", "Unbreakable", "Reach wave 20 in Endless Survival.", R(800, 2, 3, 50, 60),
     lambda g: (g.profile.endless_best, 20)),
    ("endless30", "Immortal", "Reach wave 30 in Endless Survival.", R(1500, 3, 4, 150, 100),
     lambda g: (g.profile.endless_best, 30)),
    ("modes3", "Mode Hopper", "Win 3 different Special Battles.", R(200, 1, 1, xp=30),
     lambda g: (_modes_won(g), 3)),
    ("modes7", "Jack of All Modes", "Win all 7 Special Battles.", R(600, 3, 3, 80, 80),
     lambda g: (_modes_won(g), 7)),
    # ---- cards & King ----
    ("up1", "Getting Stronger", "Upgrade a card.", R(40, xp=10),
     lambda g: (min(1, _tot(g, "upgrades")), 1)),
    ("up25", "Smith", "Make 25 card upgrades.", R(400, 2, 1, xp=50),
     lambda g: (_tot(g, "upgrades"), 25)),
    ("up100", "Master Smith", "Make 100 card upgrades.", R(2000, 3, 3, 150, 150),
     lambda g: (_tot(g, "upgrades"), 100)),
    ("max", "Maxed Out", "Get a card to level 16.", R(500, 3, 2, 30, 60),
     lambda g: (_max_level(g), 16)),
    ("max8", "Elite Deck", "Get 8 cards to level 16.", R(2000, 4, 4, 200, 150),
     lambda g: (_maxed(g), 8)),
    ("max24", "Fully Loaded", "Get 24 cards to level 16.", R(5000, 8, 8, 500, 300),
     lambda g: (_maxed(g), 24)),
    ("king13", "Crowned", "Reach King level 13.", R(500, 2, 2, 50),
     lambda g: (g.profile.king_level(), 13)),
    ("king15", "High King", "Reach King level 15.", R(1500, 4, 4, 150),
     lambda g: (g.profile.king_level(), 15)),
    ("king16", "King of Kings", "Reach King level 16.", R(3000, 6, 6, 500),
     lambda g: (g.profile.king_level(), 16)),
    ("troop13", "Garrison", "Upgrade a Tower Troop to level 13.", R(300, 1, 1, 20, 40),
     lambda g: (_troop_max(g), 13)),
    ("troop16", "Fortress", "Upgrade a Tower Troop to level 16.", R(1500, 3, 3, 150, 100),
     lambda g: (_troop_max(g), 16)),
    # ---- Evolutions & Heroes ----
    ("evo1", "Evolution", "Unlock an Evolution.", R(100, xp=20),
     lambda g: (min(1, len(g.profile.evos)), 1)),
    ("evo5", "Evolutionist", "Unlock 5 Evolutions.", R(600, 2, 2, 60, 60),
     lambda g: (len(g.profile.evos), 5)),
    ("evo15", "Mad Scientist", "Unlock 15 Evolutions.", R(2000, 4, 4, 250, 150),
     lambda g: (len(g.profile.evos), 15)),
    ("hero1", "Heroic", "Unlock a Hero.", R(100, xp=20),
     lambda g: (min(1, len(g.profile.heroes)), 1)),
    ("hero3", "Hall of Heroes", "Unlock 3 Heroes.", R(600, 2, 2, 60, 60),
     lambda g: (len(g.profile.heroes), 3)),
    ("hero8", "League of Legends", "Unlock 8 Heroes.", R(2000, 4, 4, 250, 150),
     lambda g: (len(g.profile.heroes), 8)),
    ("evoplay", "Evolved", "Play 25 evolved cards.", R(250, 2, 1, xp=30),
     lambda g: (_tot(g, "evo_plays"), 25)),
    ("evoplay200", "Natural Selection", "Play 200 evolved cards.", R(1200, 3, 3, 100, 80),
     lambda g: (_tot(g, "evo_plays"), 200)),
    # ---- the Shop ----
    ("shop1", "Window Shopper", "Buy something in the Shop.", R(100, xp=10),
     lambda g: (min(1, _tot(g, "shop_buys")), 1)),
    ("shop25", "Big Spender", "Make 25 Shop purchases.", R(800, 2, 2, 60, 60),
     lambda g: (_tot(g, "shop_buys"), 25)),
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
    """Pay achievement `aid` if it's done and unclaimed. Returns its status
    row; King rewards its XP reached are in g.profile.last_king."""
    for a in status(g):
        if a[0] == aid and a[6] and not a[7]:
            rw = dict(a[3])
            xp = rw.pop("xp", 0)
            g.profile.add(**rw)
            g.profile.last_king = g.profile.add_xp(xp) if xp else []
            g.profile.totals.setdefault("claimed", []).append(aid)
            g.profile.save()
            return a
    return None


def backpay(g):
    """Saves from before King levels / Hero coins / gems: pay the coins,
    gems and XP of achievements already claimed (their gold and shards were
    paid back then). Returns the reward dict paid."""
    claimed = set(g.profile.totals.get("claimed", []))
    tot = {}
    for aid, _, _, rw, _ in ACHIEVEMENTS:
        if aid in claimed:
            for k in ("coins", "gems", "xp"):
                if rw.get(k):
                    tot[k] = tot.get(k, 0) + rw[k]
    xp = tot.get("xp", 0)
    g.profile.add(coins=tot.get("coins", 0), gems=tot.get("gems", 0))
    if xp:
        g.profile.king_xp += xp            # chunks are paid by the caller
    return tot


def daily_bonus(g):
    """First win of the day: returns True (and pays) once per calendar day."""
    today = datetime.date.today().isoformat()
    if g.profile.totals.get("daily") == today:
        return False
    g.profile.totals["daily"] = today
    return True
