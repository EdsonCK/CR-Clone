"""
============================================================================
  MASTERY.PY  --  Card Mastery: long-term goals for every card
============================================================================

  * UNLOCK: win 5 Battles with a card in your deck (+100 gold).
  * Then each card has 3 tasks running at the same time, each with 3 tiers:
        task 1  win battles with it            (open as soon as it's unlocked)
        task 2  deal damage / crown tower damage  (opens at card level 13)
        task 3  destroy troops / play it         (opens at card level 15)
    Tier rewards ("pages"): every task's 1st tier pays 500 gold, 2nd tier
    1000 gold, 3rd tier 100 gems - 9 rewards per card, claimed on the
    card's Mastery page (Cards screen).
  * Progress only counts while a task is open, and only in Battles (Trophy
    Road and custom), Special Battles and 2v2 - not Levels, Endless or the
    Sandbox.

Goals are sized from mastery_data.AVG (what the card does in an average
match, measured by tools/mastery_calib.py), so every card's tasks take
about the same number of matches: tier 3 of a task is ~75 wins or ~150-180
matches of that card - fully mastering a card takes a long time even if
you play it every game.
============================================================================
"""

import math

import cards

try:
    from mastery_data import AVG
except Exception:                      # not generated yet
    AVG = {}

UNLOCK_WINS = 5
UNLOCK_REWARD = {"gold": 100}
TASK_LEVEL = (0, 13, 15)               # card level a task needs to open
TIER_REWARDS = ({"gold": 500}, {"gold": 1000}, {"gems": 100})
WIN_TIERS = (10, 30, 75)               # task 1: wins
MATCH_TIERS = ((20, 60, 150), (25, 75, 180))   # tasks 2 / 3: matches' worth
DEFAULT_AVG = {"dmg": 600.0, "tower": 150.0, "kills": 2.0, "plays": 3.0}

LABELS = {
    "wins": ("Win battles", "Win %s Battles with %s in your deck"),
    "dmg": ("Deal damage", "Deal %s damage with %s"),
    "tower": ("Crown Tower damage", "Deal %s damage to Crown Towers with %s"),
    "kills": ("Destroy troops", "Destroy %s enemy troops with %s"),
    "plays": ("Play it", "Play %s %s times"),
}


# ---------------------------------------------------------------- tasks
def _avg(key, kind):
    v = AVG.get(key, {}).get(kind, 0.0)
    return v if v > 0 else DEFAULT_AVG[kind]


def task_kinds(key):
    """The 3 task kinds of card `key`."""
    c = cards.CARDS[key]
    a = AVG.get(key, {})
    wincon = c.attacks == "buildings" or (a.get("tower", 0) > 0.45 * max(a.get("dmg", 1), 1))
    t2 = "tower" if wincon else "dmg"
    t3 = "kills" if a.get("kills", DEFAULT_AVG["kills"]) >= 0.6 else "plays"
    return ("wins", t2, t3)


def _nice(x):
    """Round to 2 significant figures (min 5)."""
    if x < 5:
        return 5
    p = 10 ** max(0, int(math.floor(math.log10(x))) - 1)
    return int(round(x / p) * p)


def goals(key, i):
    """The 3 tier goals of task i (0..2) of card `key`."""
    kind = task_kinds(key)[i]
    if kind == "wins":
        return WIN_TIERS
    mult = MATCH_TIERS[0] if i == 1 else MATCH_TIERS[1]
    return tuple(_nice(_avg(key, kind) * m) for m in mult)


def describe(key, i, goal):
    kind = task_kinds(key)[i]
    name = cards.CARDS[key].name
    n = "{:,}".format(goal)
    if kind == "plays":
        return LABELS[kind][1] % (name, n)
    return LABELS[kind][1] % (n, name)


def title(key, i):
    return LABELS[task_kinds(key)[i]][0]


# ---------------------------------------------------------------- state
def rec(profile, key):
    """profile.mastery[key]: {"w": wins with the card, "p": [progress x3],
    "c": [tiers claimed x3], "u": unlock reward claimed (0/1)}."""
    r = profile.mastery.setdefault(key, {})
    r.setdefault("w", 0)
    r.setdefault("p", [0, 0, 0])
    r.setdefault("c", [0, 0, 0])
    r.setdefault("u", 0)
    return r


def unlocked(profile, key):
    return profile.mastery.get(key, {}).get("w", 0) >= UNLOCK_WINS


def task_open(profile, key, i):
    return unlocked(profile, key) and profile.level(key) >= max(TASK_LEVEL[i], 0)


def reached(profile, key, i):
    """How many tiers of task i are done."""
    p = profile.mastery.get(key, {}).get("p", [0, 0, 0])[i]
    return sum(1 for g in goals(key, i) if p >= g)


def mastery_level(profile, key):
    """Tiers claimed (0..9)."""
    return sum(profile.mastery.get(key, {}).get("c", [0, 0, 0]))


def claimable(profile, key):
    """Rewards waiting to be claimed for card `key`: [(label, reward)]."""
    if not unlocked(profile, key):
        return []
    r = rec(profile, key)
    out = []
    if not r["u"]:
        out.append(("Mastery unlocked", dict(UNLOCK_REWARD)))
    for i in range(3):
        for t in range(r["c"][i], reached(profile, key, i)):
            out.append(("%s tier %d" % (title(key, i), t + 1), dict(TIER_REWARDS[t])))
    return out


def claim(profile, key):
    """Pay everything claimable for `key`. Returns the total reward dict."""
    total = {}
    for _, rw in claimable(profile, key):
        for k, v in rw.items():
            total[k] = total.get(k, 0) + v
    if not total:
        return {}
    r = rec(profile, key)
    r["u"] = 1
    r["c"] = [reached(profile, key, i) for i in range(3)]
    profile.add(gold=total.get("gold", 0), gems=total.get("gems", 0))
    profile.save()
    return total


def any_claimable(profile):
    return any(claimable(profile, k) for k in list(profile.mastery))


# ---------------------------------------------------------------- recording
def card_stats(m, team, deck):
    """What each card of `deck` did for `team` in match m:
    {card: {"dmg", "tower", "kills", "plays"}} (a card is credited with
    what its spawned units / squad members did too)."""
    st = m.stats
    dmg, tower = st["dmg"][team], st.get("tower_dmg_by", [{}, {}])[team]
    kills, played = st["kills"][team], st["played"][team]
    out = {}
    for card in deck:
        keys = set()
        for r in cards.related_keys(card):
            keys |= cards.related_keys(r)
        out[card] = {"dmg": sum(dmg.get(k, 0.0) for k in keys),
                     "tower": sum(tower.get(k, 0.0) for k in keys),
                     "kills": sum(kills.get(k, 0) for k in keys),
                     "plays": played.get(card, 0)}
    return out


def record_match(profile, m, team, deck, won):
    """Count a finished match towards every deck card's mastery. Returns
    notices [(text)] for the result screen (unlocks, tiers reached)."""
    stats = card_stats(m, team, deck)
    notes = []
    for card in deck:
        if card not in cards.CARDS:
            continue
        r = rec(profile, card)
        was_open = [task_open(profile, card, i) for i in range(3)]
        before = [reached(profile, card, i) for i in range(3)]
        if won:
            r["w"] += 1
            if r["w"] == UNLOCK_WINS:
                notes.append("%s: Mastery unlocked!" % cards.CARDS[card].name)
        s = stats.get(card, {})
        for i, kind in enumerate(task_kinds(card)):
            if not was_open[i]:
                continue
            add = (1 if won else 0) if kind == "wins" else s.get(kind, 0)
            cap = goals(card, i)[-1]
            r["p"][i] = min(cap, r["p"][i] + int(round(add)))
            if reached(profile, card, i) > before[i]:
                notes.append("%s: %s tier %d done!" % (cards.CARDS[card].name,
                                                       title(card, i), reached(profile, card, i)))
    return notes
