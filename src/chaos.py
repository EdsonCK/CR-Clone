"""
============================================================================
  CHAOS.PY  --  Chaos battles: 1v1 vs the Master AI with upgrades
============================================================================

A normal battle (towers, 3:00 + overtime) against the Master AI, except that
every 45 seconds BOTH sides are offered two upgrades from the Endless
catalogue (endless_upgrades.py) and keep one for the rest of the match:

  * same pool, same rarities: you and the AI are each offered two options of
    the SAME two rarities (say rare + epic) - the exact upgrades depend on
    each side's own deck (card upgrades only for cards in that deck);
  * rarity climbs over the match: the first offer is 25% rare + rare, 50%
    rare + epic, 25% epic + epic; later offers lean epic and legendary, and
    the last possible offer (in overtime) is always two legendaries;
  * nothing stacks: an upgrade, once taken, leaves that side's pool;
  * Endless-only boons (start-of-wave ones) are left out.

The AI takes its pick the moment an offer appears (ai_pick scores each
option for its deck and the state of the match); the game pauses until you
pick yours. The AI controller (ai.py) then plays its upgraded cards with
their upgraded stats.
============================================================================
"""

import random as _random

import cards
import config as cfg
import endless_upgrades as eu
from engine import PLAYER, ENEMY

INTERVAL = 45.0                       # seconds between upgrade offers
TIERS = ("rare", "epic", "legendary")
CHAOS_AI_LEVEL = 5                    # always the Master AI
EXCLUDED = {"boon:war_chest", "boon:second_wind"}   # Endless (per-wave) only

# per-offer chance of each rarity, from the first offer to the one before
# the last (interpolated in between); the last offer is always legendary
FIRST = (0.5, 0.5, 0.0)
BEFORE_LAST = (0.0, 0.35, 0.65)


def total_rounds():
    """How many offers a match that goes the full distance gets."""
    return int((cfg.MATCH_LENGTH + cfg.OVERTIME_LENGTH - 1e-6) // INTERVAL)


def tier_weights(rnd, n=None):
    """(rare, epic, legendary) chances for offer `rnd` (1-based) of `n`."""
    n = n or total_rounds()
    if rnd >= n:
        return (0.0, 0.0, 1.0)
    p = 0.0 if n <= 2 else (rnd - 1) / float(n - 2)
    return tuple(a + (b - a) * p for a, b in zip(FIRST, BEFORE_LAST))


def roll_tiers(rnd, rng, n=None):
    """The two rarities of offer `rnd` (lower one first)."""
    w = tier_weights(rnd, n)
    pair = [rng.choices(TIERS, w)[0] for _ in range(2)]
    return sorted(pair, key=TIERS.index)


def pool(match, team, tier, taken):
    """Every upgrade of `tier` this side could be offered right now."""
    deck = match.decks[team]
    card_ups = [u for k in deck for u in eu.CARD_UPS.get(k, ())
                if u.tier == tier and u.key not in taken]
    boons = [u for u in eu.BOONS if u.tier == tier and u.key not in taken
             and u.key not in EXCLUDED
             and (u.key not in eu._NEEDS or eu._NEEDS[u.key](match, deck, team))]
    return card_ups, boons


def offer(match, team, tiers, rng, taken=()):
    """Two options of the given rarities for `team` (a card upgrade and a
    boon when both exist, in random order)."""
    taken = set(taken)
    out = []
    want_card = rng.random() < 0.5
    for i, tier in enumerate(tiers):
        # try this rarity first, then the nearest others
        order = sorted(TIERS, key=lambda t: abs(TIERS.index(t) - TIERS.index(tier)))
        pick = None
        for t in order:
            card_ups, boons = pool(match, team, t, taken | {u.key for u in out})
            first, second = (card_ups, boons) if (want_card if i == 0 else not want_card) \
                else (boons, card_ups)
            src = first or second
            if src:
                pick = rng.choice(src)
                break
        if pick is not None:
            out.append(pick)
    return out


# ---------------------------------------------------------------- AI picks
TIER_VALUE = {"rare": 1.0, "epic": 2.0, "legendary": 3.0}
BOON_VALUE = {
    "boon:elixir": 1.4, "boon:levels2": 1.3, "boon:thrift": 1.2, "boon:levels": 0.9,
    "boon:might": 1.0, "boon:swift": 0.8, "boon:tower_dmg": 0.8,
    "boon:tower_speed": 0.8, "boon:tower_hp": 0.7, "boon:tower_range": 0.6,
    "boon:frost_towers": 0.6, "boon:cannon_towers": 0.7, "boon:bounty": 0.5,
    "boon:king": 0.4, "boon:heal": 0.0, "boon:rebuild": 0.0, "boon:ascend": 0.0,
    "boon:spells": 0.0,
}


def _tower_damage_taken(match, team):
    tws = [tw for (t, s), tw in match.towers.items() if t == team and tw.alive]
    if not tws:
        return 0.0
    return sum(1.0 - tw.hp / max(1, tw.max_hp) for tw in tws) / len(tws)


def ai_score(match, team, u, picks=()):
    """How much the AI wants upgrade `u` (higher = better)."""
    import evos
    deck = match.decks[team]
    s = TIER_VALUE.get(u.tier, 1.0)
    if u.kind == "card":
        c = cards.CARDS[u.card]
        s += 0.6 if c.elixir >= 4 else 0.3            # a card it leans on
        if c.attacks == "buildings" or c.siege:
            s += 0.5                                   # its win condition
        # focus: build on a card it has already upgraded
        s += 0.4 * sum(1 for p in picks if p.kind == "card" and p.card == u.card)
        if u.key.endswith(":veteran"):
            s -= 0.3
        return s
    s += BOON_VALUE.get(u.key, 0.5)
    lost = sum(1 for side in ("left", "right") if not match.towers[(team, side)].alive)
    if u.key == "boon:heal":
        s += 2.5 * _tower_damage_taken(match, team)
    elif u.key == "boon:rebuild":
        s += 2.0 * lost
    elif u.key == "boon:king":
        s += 0.8 * lost
    elif u.key == "boon:ascend":
        s += 0.35 * sum(1 for k in deck if k in evos.EVOS or k in evos.HEROES)
    elif u.key == "boon:spells":
        s += 0.3 * sum(1 for k in deck if cards.CARDS[k].category == "spell")
    elif u.key in ("boon:tower_dmg", "boon:tower_speed", "boon:tower_hp"):
        s += 0.3 * lost                                # fewer towers: each matters
    return s


def ai_pick(match, team, options, rng=None, picks=()):
    """Index of the option the AI takes (a little noise, Master is sharp)."""
    rng = rng or _random
    scores = [ai_score(match, team, u, picks) + rng.uniform(-0.15, 0.15) for u in options]
    return max(range(len(options)), key=lambda i: scores[i])


# ---------------------------------------------------------------- the run
class ChaosRun:
    """Upgrade offers for a Chaos battle. The game calls update(dt) every
    frame (before the match); while `choice` is set the game pauses for the
    player's pick and calls choose(i)."""

    def __init__(self, match, seed=None):
        self.m = match
        self.rng = _random.Random(seed)
        self.n_rounds = total_rounds()
        self.round = 0                    # offers made so far
        self.next_at = INTERVAL           # match time of the next offer
        self.choice = None                # [Upgrade, Upgrade] for the player
        self.tiers = None                 # rarities of the current offer
        self.picks = []                   # the player's upgrades
        self.ai_picks = []                # the AI's upgrades
        self.ai_options = None            # what the AI was offered last
        self.last_ai_pick = None          # (Upgrade, match time) for the HUD

    def time_to_next(self):
        """Seconds until the next offer (None: no more offers)."""
        if self.m.finished or self.round >= self.n_rounds:
            return None
        return max(0.0, self.next_at - self.m.elapsed)

    def next_is_final(self):
        return self.round + 1 >= self.n_rounds

    def update(self, dt=0.0):
        if self.choice or self.m.finished or self.round >= self.n_rounds:
            return
        if self.m.elapsed + 1e-6 >= self.next_at:
            self._start_round()

    def _start_round(self):
        self.round += 1
        self.next_at += INTERVAL
        self.tiers = roll_tiers(self.round, self.rng, self.n_rounds)
        # the AI picks from its own options of the same rarities
        opts = offer(self.m, ENEMY, self.tiers, self.rng, [u.key for u in self.ai_picks])
        self.ai_options = opts
        if opts:
            u = opts[ai_pick(self.m, ENEMY, opts, self.rng, self.ai_picks)]
            u.apply(self.m, ENEMY)
            self.ai_picks.append(u)
            self.last_ai_pick = (u, self.m.elapsed)
        mine = offer(self.m, PLAYER, self.tiers, self.rng, [u.key for u in self.picks])
        self.choice = mine or None

    def choose(self, i):
        u = self.choice[i]
        u.apply(self.m, PLAYER)
        self.picks.append(u)
        self.choice = None
        return u
