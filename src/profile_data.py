"""
============================================================================
  PROFILE_DATA.PY  --  Your progression: gold, card levels, unlocks
============================================================================

Everything you earn is saved in profile.json next to the game:

  * GOLD      - earned by winning Levels, Battles, Special Battles and
                Endless Survival. Spent on card upgrades.
  * SHARDS    - rarer. Earned for first clears / 3-star clears of Levels,
                a stream of Battle wins and Endless milestones. Spent on
                unlocking Evolutions and Heroes.
  * CARD LEVELS - every card starts at level 11 (the stats in cards.py) and
                can be upgraded to level 16. Each level is +10% hp and
                damage. Your crown towers are as strong as your deck: their
                level is the average level of the 8 cards you take into a
                match (rounded down).
  * EVOLUTIONS / HEROES you've unlocked.
  * LADDER    - wins against each AI intelligence level. In Battles the AI's
                cards start at level 11 and go up one level for every
                LADDER_WINS_PER_LEVEL wins against that intelligence level
                (max 16) - or set Battle Setup to "match my level".
  * Endless Survival best wave, saved deck slots, lifetime totals.
  * TROPHIES  - your Trophy Road standing (trophy.py): current, best ever,
                and how far along the road your rewards have been paid.

Tuning: all the reward / cost numbers are the constants right below.
Settings > Sandbox unlocks every Level, Evolution and Hero for free play
(it never touches your saved progress).
============================================================================
"""

import json
import os

import cards

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE_FILE = os.path.join(_ROOT, "profile.json")

START_LEVEL = cards.LEVEL_MIN        # 11
MAX_LEVEL = cards.LEVEL_MAX          # 16

# gold to go FROM the key level to the next one
UPGRADE_COST = {11: 100, 12: 250, 13: 600, 14: 1200, 15: 2500}

EVO_COST = 5          # shards to unlock one card's Evolution
HERO_COST = 8         # shards to unlock one Hero

# Levels: gold for each NEW star on level n, gold for any win on level n
def level_star_gold(n):
    return 30 + 10 * n


def level_win_gold(n):
    return 10 + 2 * n


STARS_PER_UNLOCK = 2   # level n needs 2*(n-1) stars in total to open

# Battles
LADDER_WINS_PER_LEVEL = 3
SHARD_POINTS_PER_SHARD = 12   # a Battle win adds the AI's intelligence level


def battle_gold(win, ai_level, ai_elixir, crowns):
    if win:
        return int((20 + 8 * ai_level) * max(0.5, min(2.0, ai_elixir)) + 4 * crowns)
    return 5 + 2 * crowns


# Special battles (fixed AI card level)
SPECIAL_AI_LEVEL = 12


def special_gold(win, ai_level, crowns):
    return (50 + 10 * ai_level + 4 * crowns) if win else (10 + 2 * crowns)


# Endless Survival
def endless_gold(waves):
    return 6 * waves + (waves // 5) * 15


DECK_SLOTS = 5


class Profile:
    def __init__(self):
        self.gold = 0
        self.shards = 0
        self.shard_points = 0
        self.levels = {}             # card key -> level (missing = 11)
        self.evos = []               # card keys with an unlocked Evolution
        self.heroes = []             # card keys with an unlocked Hero
        self.flex_evo = []           # flex slot: cards you'd rather bring as Evo
        self.ladder = {}             # "L3" -> wins vs that intelligence level
        self.endless_best = 0
        self.endless_runs = 0
        self.decks = []              # saved deck slots: [{"name", "cards"}]
        self.active_slot = 0
        self.totals = {"gold": 0, "shards": 0, "upgrades": 0}
        self.special = {}            # mode key -> {"wins", "plays"}
        self.trophies = 0            # Trophy Road
        self.best_trophies = 0
        self.road_paid = 0           # rewards granted up to this many trophies
        self.load()

    # ---- persistence ----
    def load(self):
        try:
            with open(PROFILE_FILE) as f:
                d = json.load(f)
        except Exception:
            return
        self.gold = int(d.get("gold", 0))
        self.shards = int(d.get("shards", 0))
        self.shard_points = int(d.get("shard_points", 0))
        self.levels = {k: max(START_LEVEL, min(MAX_LEVEL, int(v)))
                       for k, v in d.get("levels", {}).items() if k in cards.CARDS}
        self.evos = [k for k in d.get("evos", []) if k in cards.CARDS]
        self.heroes = [k for k in d.get("heroes", []) if k in cards.CARDS]
        self.flex_evo = [k for k in d.get("flex_evo", []) if k in cards.CARDS]
        self.ladder = {k: int(v) for k, v in d.get("ladder", {}).items()}
        self.endless_best = int(d.get("endless_best", 0))
        self.endless_runs = int(d.get("endless_runs", 0))
        self.decks = [x for x in d.get("decks", []) if isinstance(x, dict)]
        self.active_slot = int(d.get("active_slot", 0))
        self.totals.update(d.get("totals", {}))
        self.special = d.get("special", {})
        self.trophies = max(0, int(d.get("trophies", 0)))
        self.best_trophies = max(self.trophies, int(d.get("best_trophies", 0)))
        self.road_paid = int(d.get("road_paid", 0))

    def save(self):
        try:
            with open(PROFILE_FILE, "w") as f:
                json.dump({
                    "gold": self.gold, "shards": self.shards,
                    "shard_points": self.shard_points, "levels": self.levels,
                    "evos": self.evos, "heroes": self.heroes, "flex_evo": self.flex_evo,
                    "ladder": self.ladder,
                    "endless_best": self.endless_best, "endless_runs": self.endless_runs,
                    "decks": self.decks, "active_slot": self.active_slot,
                    "totals": self.totals, "special": self.special,
                    "trophies": self.trophies, "best_trophies": self.best_trophies,
                    "road_paid": self.road_paid,
                }, f, indent=1)
        except Exception:
            pass

    def reset(self):
        """Wipe progression (keeps your saved deck slots)."""
        decks, slot = self.decks, self.active_slot
        self.levels, self.ladder, self.special = {}, {}, {}
        self.gold = self.shards = self.shard_points = 0
        self.evos, self.heroes, self.flex_evo = [], [], []
        self.endless_best = self.endless_runs = 0
        self.trophies = self.best_trophies = self.road_paid = 0
        self.totals = {"gold": 0, "shards": 0, "upgrades": 0}
        self.decks, self.active_slot = decks, slot
        self.save()

    # ---- card levels ----
    def level(self, key):
        return self.levels.get(key, START_LEVEL)

    def deck_levels(self, deck):
        return {k: self.level(k) for k in deck}

    def tower_level(self, deck):
        """Crown towers are as strong as your deck (average level, floored)."""
        if not deck:
            return START_LEVEL
        return int(sum(self.level(k) for k in deck) / len(deck) + 1e-6)

    def upgrade_cost(self, key):
        lv = self.level(key)
        return UPGRADE_COST.get(lv) if lv < MAX_LEVEL else None

    def can_upgrade(self, key):
        c = self.upgrade_cost(key)
        return c is not None and self.gold >= c

    def upgrade(self, key):
        c = self.upgrade_cost(key)
        if c is None or self.gold < c:
            return False
        self.gold -= c
        self.levels[key] = self.level(key) + 1
        self.totals["upgrades"] = self.totals.get("upgrades", 0) + 1
        self.save()
        return True

    # ---- currencies ----
    def add(self, gold=0, shards=0):
        self.gold += int(gold)
        self.shards += int(shards)
        self.totals["gold"] = self.totals.get("gold", 0) + int(gold)
        self.totals["shards"] = self.totals.get("shards", 0) + int(shards)

    def add_shard_points(self, pts):
        """Battle wins trickle shards in: returns shards gained."""
        self.shard_points += int(pts)
        got = self.shard_points // SHARD_POINTS_PER_SHARD
        self.shard_points %= SHARD_POINTS_PER_SHARD
        if got:
            self.add(shards=got)
        return got

    # ---- evolutions / heroes ----
    def unlock_evo(self, key):
        if key in self.evos or self.shards < EVO_COST:
            return False
        self.shards -= EVO_COST
        self.evos.append(key)
        self.save()
        return True

    def unlock_hero(self, key):
        if key in self.heroes or self.shards < HERO_COST:
            return False
        self.shards -= HERO_COST
        self.heroes.append(key)
        self.save()
        return True

    # ---- battle ladder ----
    def ladder_wins(self, ai_level):
        return self.ladder.get("L%d" % ai_level, 0)

    def ladder_level(self, ai_level):
        return min(MAX_LEVEL, START_LEVEL + self.ladder_wins(ai_level) // LADDER_WINS_PER_LEVEL)

    def add_ladder_win(self, ai_level):
        k = "L%d" % ai_level
        self.ladder[k] = self.ladder.get(k, 0) + 1
