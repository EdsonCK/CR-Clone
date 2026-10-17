"""
============================================================================
  SHOP.PY  --  What the Shop sells, and for how much
============================================================================

Gems (from big achievements, arenas and King level-ups) buy:

  * GOLD          1000 gold ~ 60 gems (bigger packs are a little cheaper)
  * EVO SHARDS    40 gems each (an Evolution, 5 shards, ~ 180-200 gems)
  * HERO COINS    30 gems each (a Hero, 8 coins, ~ 220-240 gems)
  * DAILY DEALS   three offers that change every day (one is always a free
                  gift); each can be bought once a day. Some are paid in
                  gold - a way to turn spare gold into shards, coins or gems.

Hero coins buy:

  * LEVEL-UP POTION  3 coins: drink it on a card (Cards screen) and for one
                  real hour that card plays at your King level.

Each offer: (id, name, reward dict, cost) where cost is ("gems"|"gold"|
"coins", n) or None (free). Tune prices right here.
============================================================================
"""

import datetime
import random

import profile_data

GOLD_PACKS = [
    ("gold_s", "Pouch of Gold", {"gold": 1000}, ("gems", 60)),
    ("gold_m", "Sack of Gold", {"gold": 5500}, ("gems", 300)),
    ("gold_l", "Chest of Gold", {"gold": 12000}, ("gems", 600)),
]
SHARD_PACKS = [
    ("shard_1", "Evo Shard", {"shards": 1}, ("gems", 40)),
    ("shard_5", "Shard Bundle", {"shards": 5}, ("gems", 180)),
    ("shard_10", "Shard Trove", {"shards": 10}, ("gems", 340)),
]
COIN_PACKS = [
    ("coin_1", "Hero Coin", {"coins": 1}, ("gems", 30)),
    ("coin_8", "Coin Purse", {"coins": 8}, ("gems", 220)),
    ("coin_16", "Coin Hoard", {"coins": 16}, ("gems", 420)),
]
FREE_DEALS = [
    ("free_gold", "Free Gold", {"gold": 150}, None),
    ("free_gems", "Free Gems", {"gems": 10}, None),
    ("free_mix", "Free Gift", {"gold": 80, "gems": 5}, None),
]
DEAL_POOL = [
    ("deal_gold", "Gold Rush", {"gold": 2500}, ("gems", 100)),
    ("deal_shards", "Shard Deal", {"shards": 3}, ("gems", 90)),
    ("deal_coins", "Coin Deal", {"coins": 4}, ("gems", 80)),
    ("gold_shard", "Evo Shard", {"shards": 1}, ("gold", 1500)),
    ("gold_coin", "Hero Coin", {"coins": 1}, ("gold", 1200)),
    ("gold_gems", "Gem Pouch", {"gems": 25}, ("gold", 2000)),
]
SECTIONS = [("Gold", GOLD_PACKS), ("Evo Shards", SHARD_PACKS), ("Hero Coins", COIN_PACKS)]
POTION = ("potion", "Level-Up Potion", {"potions": 1}, ("coins", profile_data.POTION_COST))


def today():
    return datetime.date.today().isoformat()


def daily_deals(day=None):
    """Today's three deals: a free gift + two from the pool (same all day)."""
    day = day or today()
    rng = random.Random("deals-" + day)
    return [rng.choice(FREE_DEALS)] + rng.sample(DEAL_POOL, 2)


def bought_today(profile):
    st = profile.shop
    if st.get("day") != today():
        st["day"], st["bought"] = today(), []
    return st["bought"]


def can_buy(profile, offer, deal=False):
    oid, _, _, cost = offer
    if deal and oid in bought_today(profile):
        return False
    if cost is None:
        return True
    cur, n = cost
    return {"gems": profile.gems, "gold": profile.gold,
            "coins": profile.hero_coins}[cur] >= n


def buy(profile, offer, deal=False):
    """Buy an offer; returns True if it went through."""
    if not can_buy(profile, offer, deal):
        return False
    oid, _, reward, cost = offer
    if cost is not None:
        cur, n = cost
        if cur == "gems":
            profile.gems -= n
        elif cur == "coins":
            profile.hero_coins -= n
        else:
            profile.gold -= n
    reward = dict(reward)
    profile.potions += reward.pop("potions", 0)
    profile.add(**reward)
    if deal:
        bought_today(profile).append(oid)
    profile.totals["shop_buys"] = profile.totals.get("shop_buys", 0) + 1
    profile.save()
    return True


def time_to_refresh():
    """'hh:mm' until the daily deals change (midnight)."""
    now = datetime.datetime.now()
    nxt = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), datetime.time())
    m = int((nxt - now).total_seconds() // 60)
    return "%d:%02d" % (m // 60, m % 60)
