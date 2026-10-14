"""
============================================================================
  BALANCE.PY  --  Card benchmark & auto-balancer
============================================================================

How a card is judged
--------------------
Every card X meets every other card Y in a real arena (towers and all), in
BOTH roles:

  * X ATTACKS:  X is deployed at the bridge (spells: cast at the enemy tower,
                Miner: next to it, siege buildings: at the river). When X's
                units get close, the defender drops Y at a standard defensive
                spot (melee in the path, ranged behind the tower, buildings on
                the pull spot, spells on the attackers).
  * X DEFENDS:  the same with roles swapped.

Each engagement runs until the attack is spent - every attacking unit dead,
max 30 s (surviving defenders count at their value; their counter-push would
be answered in a real game, so it isn't simulated) - and is scored as an
elixir trade:

    score = tower damage dealt - tower damage taken      (140 hp = 1 elixir)
          + (attacker value left - attacker cost)
          - (defender value left - defender cost)

A card's PERFORMANCE is the trimmed mean (top & bottom 10 % dropped, so one
hard counter or one free win can't dominate) of attack-minus-defend scores
over the whole card pool, in 2 timing variants. 0 = trades evenly on
average; +1 = gains about one elixir per engagement.

v2 engagements (closer to a real match)
---------------------------------------
  * PUSHES (optional, PARTNERS=1): a troop attacks with a standard partner
    and only its contribution counts (the push without it is subtracted).
    Off by default: against a single defender a two-card push wins almost
    regardless of the card, which drowned the signal.
  * BACKUP SPELLS: once a side's card is down, that side may answer with a
    Zap, Arrows or Fireball if it's a good trade (the spell's elixir counts
    against it). Fragile, high-value units - support ranged troops above
    all - pay for standing behind the tower unprotected, as in real games.
  * CHAMPIONS: abilities are timed by the Expert AI (level 4).
Only cards outside FIXED (the 28 cards added in v1.1 at real-game stats)
are tuned. tools/fullgame.py checks every round in full matches.

How cards are tuned
-------------------
A card's power is scaled by one factor f: hp *= f^a, damage *= f^(1-a)
(a depends on the card's role: tanks move mostly hp, glass cannons mostly
damage), spells scale damage, and anything the card spawns scales with it.
For each card, f is searched (secant method in log f) until its performance
is ~0 against a FROZEN snapshot of all other cards. New stats are written to
a separate file and only applied when the whole round is finished, so a
card's tuning never shifts the benchmark mid-round.

Rounds: each round is tuned against a frozen snapshot, then the snapshot is
advanced part of the way toward the tuned values (damped, max 35 % per card
per round) and the next round starts from it.

Usage (from the project root):
    python tools/balance.py matrix   OUT.json [SNAPSHOT.json]
    python tools/balance.py tune     OUT.json [SNAPSHOT.json]
    python tools/balance.py advance  OUT.json SNAPSHOT.json TUNED.json
============================================================================
"""

import copy
import dataclasses
import json
import math
import multiprocessing as mp
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import config as cfg            # noqa: E402
import cards                    # noqa: E402
from engine import (Match, PLAYER, ENEMY, RIVER_TOP, RIVER_BOTTOM,  # noqa: E402
                    dist)

# Support / combo cards that can't be judged in a 1-vs-1 engagement.
UTILITY = {"rage", "freeze", "tornado", "elixir_collector"}
# Cards that already use real-game stats (added in v1.1): never tuned, but
# still in every engagement as opponents.
FIXED = {"berserker", "firecracker", "goblin_gang", "skeleton_dragons", "rascals",
         "royal_recruits", "royal_delivery", "heal_spirit", "suspicious_bush",
         "goblin_cage", "goblin_demolisher", "minion_giant", "royal_hogs", "mirror",
         "goblin_curse", "clone", "vines", "goblin_drill", "rune_giant", "void",
         "fisherman", "royal_ghost", "mother_witch", "phoenix", "goblin_machine",
         "ram_rider", "ronin", "spirit_empress"}
# v1.4.4: the anchors (real-ratio staples, cards.ANCHORS) and cards set by
# hand are never tuned either; FREEZE=a,b,c adds more for one run
FIXED = set(cards.ANCHORS) | {"mortar", "little_prince"}   # the newer
# real-stat cards above are tuned too from v1.4.4 on (some were outliers)
FIXED |= {k for k in os.environ.get("FREEZE", "").split(",") if k}
BACKUP_SPELLS = ("zap", "arrows", "fireball")
PARTNERS = os.environ.get("PARTNERS", "0") == "1"   # off: 2-v-1 pushes swamped the signal
BACKUPS = os.environ.get("BACKUPS", "1") == "1"
CHAMP_AI = int(os.environ.get("CHAMP_AI", "4"))
TOWER_HP_PER_ELIXIR = 140.0
DT = 0.05
MAX_T = 30.0
VARIANTS = (8.25,)               # defender reacts at this distance to tower
TRIM = 0.10

ATK, DEF = ENEMY, PLAYER          # attacker = top side, defender = bottom side
LANE_X = 3.5

# Stat fields scaled by the hp / damage factors
HP_FIELDS = ("hp", "shield_hp")
DMG_FIELDS = ("damage",)


def is_damage_spell(key):
    c = BASE[key]
    return c.category == "spell" and not (c.graveyard or (c.spawn_troops and not c.rolling))


def pool():
    """Everything that is benchmarked (opponents included)."""
    return [c.key for c in cards.DEPLOYABLE_CARDS if c.key not in UTILITY]


def tune_pool():
    """What may actually be re-tuned: everything but the real-stat cards."""
    return [k for k in pool() if k not in FIXED]


def main_pool():
    """Troops, buildings and troop-spawning spells: judged against each
    other in equal-elixir engagements."""
    return [k for k in pool() if not is_damage_spell(k)]


def spell_pool():
    return [k for k in pool() if is_damage_spell(k)]


def copies(cx, cy, cap=8):
    """(n_x, n_y): how many copies each side deploys so both spend about
    the same elixir. The cheaper side gets the extra copies."""
    if cx == cy:
        return 1, 1
    if cx > cy:
        ny = max(1, min(cap, round(cx / cy)))
        return 1, ny
    nx = max(1, min(cap, round(cy / cx)))
    return nx, 1


OFFSETS = [(0, 0), (1.3, 0), (-1.3, 0), (0, -1.3), (1.3, -1.3), (-1.3, -1.3),
           (0, 1.2), (0.65, -2.4)]


# ===========================================================================
#  stat scaling
# ===========================================================================
def role_alpha(c):
    """Share of the power change that goes into hp (rest into damage)."""
    if c.category == "spell":
        return 0.0
    if c.category == "building":
        return 0.5
    if c.attacks == "buildings" or c.hp * max(c.count, 1) >= 1800:
        return 0.65
    if c.hp * max(c.count, 1) < 400 or c.kamikaze:
        return 0.35
    return 0.5


def scaled_card(c, f):
    """A copy of CardDef c with its power scaled by factor f."""
    if abs(f - 1.0) < 1e-9:
        return c
    a = role_alpha(c)
    fh, fd = f ** a, f ** (1.0 - a)
    ch = {}
    if c.category == "spell":
        if c.spell_damage:
            ch["spell_damage"] = c.spell_damage * f
        if c.tower_damage is not None:
            ch["tower_damage"] = c.tower_damage * f
        if c.spawn_troops or c.graveyard:
            ch["sub_hp_mult"] = c.sub_hp_mult * f ** 0.5
            ch["sub_dmg_mult"] = c.sub_dmg_mult * f ** 0.5
        return dataclasses.replace(c, **ch)
    for k in HP_FIELDS:
        if getattr(c, k):
            ch[k] = getattr(c, k) * fh
    for k in DMG_FIELDS:
        if getattr(c, k):
            ch[k] = getattr(c, k) * fd
    if c.death_damage and c.kamikaze:
        ch["death_damage"] = (c.death_damage[0], c.death_damage[1] * fd)
    if c.spawn_damage:
        ch["spawn_damage"] = (c.spawn_damage[0], c.spawn_damage[1] * fd)
    if c.dash_damage:
        ch["dash_damage"] = (c.dash_damage[0], c.dash_damage[1] * fd)
    if c.heal_on_attack:
        ch["heal_on_attack"] = (c.heal_on_attack[0], c.heal_on_attack[1] * fd)
    if c.spawner or c.death_spawn or c.companion or c.back_riders or c.mixed:
        ch["sub_hp_mult"] = c.sub_hp_mult * fh
        ch["sub_dmg_mult"] = c.sub_dmg_mult * fd
    return dataclasses.replace(c, **ch)


def install(snapshot, override=None):
    """Load a stats snapshot {key: factor} into cards.CARDS (+ one override)."""
    alts = {b.alt_form[1] for b in BASE.values() if b.alt_form}
    for key, base in BASE.items():
        if key in alts:
            continue                       # set together with its card below
        f = snapshot.get(key, 1.0)
        if override and key == override[0]:
            f = override[1]
        cards.CARDS[key] = scaled_card(base, f) if abs(f - 1) > 1e-9 else base
        if base.alt_form and base.alt_form[1] in BASE:
            # a second form (Spirit Empress riding her dragon) is the same
            # card: it follows the card's factor
            ak = base.alt_form[1]
            cards.CARDS[ak] = scaled_card(BASE[ak], f) if abs(f - 1) > 1e-9 else BASE[ak]


BASE = {k: v for k, v in cards.CARDS.items()}


# ===========================================================================
#  one engagement
# ===========================================================================
def _value_left(m, team, keys):
    v = 0.0
    for e in m.entities:
        if e.team != team or e.is_tower or not e.alive or e.key not in keys:
            continue
        c = e.card
        if not c.deployable:
            continue
        share = c.elixir / max(c.count, 1)
        frac = (e.hp + e.shield) / max(e.max_hp + c.shield_hp * e.power[0], 1)
        if c.lifetime:
            frac *= max(e.lifetime, 0.0) / c.lifetime
        v += share * min(frac, 1.0)
    return v


def _damage_spell(c):
    return c.category == "spell" and not c.spawn_troops and not c.graveyard \
        or (c.category == "spell" and c.rolling)


def _cast_attack_spell(m, key):
    """Damage spell used offensively: aimed at the defending units (where
    they'll be when it lands), pulled toward the tower if both fit."""
    c = cards.CARDS[key]
    tw = m.towers[(DEF, "left")]
    defs = [e for e in m.entities if e.team == DEF and not e.is_tower and e.alive]
    if not defs:
        tx, ty = tw.x, tw.y
    else:
        tx = sum(e.x for e in defs) / len(defs)
        ty = sum(e.y for e in defs) / len(defs)
        if c.rolling:
            ty -= 1.0                      # roll through them
        elif dist(tx, ty, tw.x, tw.y) <= c.spell_radius * 1.6:
            k = 0.35
            tx, ty = tx + (tw.x - tx) * k, ty + (tw.y - ty) * k
    m._deploy(ATK, key, tx, ty)


def _clamp_side(x, y, team):
    x = min(max(x, 0.7), 17.3)
    if team == ATK:
        y = min(max(y, 0.8), RIVER_TOP - 0.6)
    else:
        y = min(max(y, RIVER_BOTTOM + 0.6), 31.2)
    return x, y


def _deploy_attacker(m, key, n=1):
    c = cards.CARDS[key]
    tw = m.towers[(DEF, "left")]
    for i in range(n):
        ox, oy = OFFSETS[i % len(OFFSETS)]
        if c.category == "spell":
            m._deploy(ATK, key, tw.x + ox * 0.5, tw.y)   # Goblin Barrel / Graveyard
        elif c.deploy_anywhere:
            m._deploy(ATK, key, tw.x + ox, tw.y - 2.3 + oy * 0.3)
        elif c.category == "building":
            m._deploy(ATK, key, *_clamp_side(LANE_X + ox, RIVER_TOP - 2.0 + oy, ATK))
        else:
            m._deploy(ATK, key, *_clamp_side(LANE_X + ox, RIVER_TOP - 1.0 + oy, ATK))


def _attackers(m):
    return [e for e in m.entities if e.team == ATK and not e.is_tower and e.alive]


def _deploy_defender(m, key, n=1):
    ok = False
    for i in range(n):
        ok = _deploy_defender_one(m, key, OFFSETS[i % len(OFFSETS)]) or ok
    return ok


def _deploy_defender_one(m, key, off=(0, 0)):
    c = cards.CARDS[key]
    ox, oy = off
    oy = -oy                               # defender side is mirrored
    tw = m.towers[(DEF, "left")]
    atk = [e for e in _attackers(m) if not e.is_building] or _attackers(m)
    if c.category == "spell":
        if not atk:
            return False
        # aim at the attackers' predicted centre when the spell lands
        cx = sum(e.x for e in atk) / len(atk)
        cy = sum(e.y for e in atk) / len(atk)
        delay = m.spell_delay(DEF, c, cx, cy)
        lead = min(delay, 1.5)
        cy += lead * 1.2 * (1 if cy < tw.y else 0)       # they walk toward us
        m._deploy(DEF, key, cx + ox * 0.3, cy)
        return True
    if c.category == "building":
        m._deploy(DEF, key, *_clamp_side(6.5 + ox, RIVER_BOTTOM + 4.0 + oy, DEF))
        return True
    if c.range >= 3.5 and c.attacks != "buildings":
        m._deploy(DEF, key, *_clamp_side(tw.x + 1.5 + ox, tw.y + 1.0 + oy, DEF))
        return True
    # melee / everything else: dropped right onto the nearest attacker
    # (1 tile on our side of it), as a player would - never across the river
    if atk:
        a = min(atk, key=lambda e: dist(e.x, e.y, tw.x, tw.y))
        d = dist(a.x, a.y, tw.x, tw.y) or 1.0
        step = max(0.0, d - 1.0)
        x = tw.x + (a.x - tw.x) / d * step
        y = tw.y + (a.y - tw.y) / d * step
    else:
        x, y = tw.x, tw.y - 2.5
    y = max(y, RIVER_BOTTOM + 0.8)
    m._deploy(DEF, key, *_clamp_side(x + ox, y + oy, DEF))
    return True


def partner_for(key):
    """The standard push partner for an attacking troop (None: attacks alone)."""
    c = cards.CARDS[key]
    if c.category != "troop" or c.deploy_anywhere:
        return None
    ranged = c.range >= 3.5 and c.attacks != "buildings"
    p = "knight" if ranged else "musketeer"
    if p == key:
        p = "valkyrie" if ranged else "archers"
    return p


def _deploy_partner(m, pkey, key):
    """Partner placed as a player would: a Knight in front of a ranged card,
    a Musketeer behind anything else."""
    c = cards.CARDS[key]
    front = c.range >= 3.5 and c.attacks != "buildings"
    y = RIVER_TOP - 1.0 + (1.2 if front else -2.2)
    m._deploy(ATK, pkey, *_clamp_side(LANE_X, y, ATK))


def _spell_trade(m, team, skey):
    """(value, x, y) of the best spot to cast spell skey on the other side's
    units: elixir worth of what it would destroy (partial damage counts
    pro rata)."""
    sc = cards.CARDS[skey]
    dmg = sc.spell_damage
    foes = [e for e in m.entities if e.team != team and e.alive and not e.is_tower
            and e.invis_timer <= 0 and not e.untargetable and e.card.deployable]
    best = (0.0, None, None)
    for c0 in foes:
        v = 0.0
        for e in foes:
            if dist(c0.x, c0.y, e.x, e.y) > sc.spell_radius:
                continue
            share = e.card.elixir / max(e.card.count, 1)
            v += share * min(dmg, e.hp + e.shield) / max(e.max_hp, 1)
        for tw in m.towers.values():          # chip on a crown tower counts too
            if tw.team != team and tw.alive and \
                    dist(c0.x, c0.y, tw.x, tw.y) <= sc.spell_radius + tw.radius * 0.5:
                v += sc.tower_dmg() / TOWER_HP_PER_ELIXIR
        if v > best[0]:
            best = (v, c0.x, c0.y)
    return best


def _maybe_backup(m, team, used, banned):
    """Cast the best-value backup spell for `team` (once) if it trades
    positively. Returns its elixir cost (0 if nothing was cast)."""
    if used.get(team):
        return 0.0
    best = None
    for sk in BACKUP_SPELLS:
        if sk in banned:
            continue
        v, x, y = _spell_trade(m, team, sk)
        cost = cards.CARDS[sk].elixir
        if x is not None and v >= cost * 1.0 and (best is None or v - cost > best[0]):
            best = (v - cost, sk, x, y)
    if best is None:
        return 0.0
    _, sk, x, y = best
    m._deploy(team, sk, x, y)
    used[team] = True
    return float(cards.CARDS[sk].elixir)


_BASELINE = {}


def engage(atk_key, def_key, variant, na=1, nd=1, partner=True):
    """X's contribution to a push (the push with X, minus the same push
    without X), or the old lone engagement when X has no partner."""
    p = partner_for(atk_key) if (PARTNERS and partner) else None
    full = engage_one(atk_key, def_key, variant, na, nd, p)
    if full is None or p is None:
        return full
    def sig(k):
        c = cards.CARDS[k]
        return (c.hp, c.damage, c.shield_hp, c.spell_damage, c.sub_hp_mult, c.sub_dmg_mult)
    key = (p, def_key, variant, nd, sig(p), sig(def_key),
           tuple(sig(k) for k in BACKUP_SPELLS))
    base = _BASELINE.get(key)
    if base is None:
        base = engage_one(p, def_key, variant, 1, nd, None)
        _BASELINE[key] = base
    if base is None:
        return None
    return full - base


def engage_one(atk_key, def_key, variant, na=1, nd=1, partner=None):
    """Run one engagement (na copies of the attacker vs nd copies of the
    defender). Returns the attacker's score in elixir, or None."""
    import random
    random.seed(hash((atk_key, def_key, variant)) & 0xFFFF)
    from ai import AIController
    ac, dc = cards.CARDS[atk_key], cards.CARDS[def_key]
    if ac.category == "spell" and dc.category == "spell":
        return None
    m = Match(cards.DEFAULT_PLAYER_DECK, cards.DEFAULT_AI_DECK)
    brains = {}
    if ac.is_champion or dc.is_champion:   # champion abilities use the AI's timing
        for team in (ATK, DEF):
            brains[team] = AIController(m, team=team, level=CHAMP_AI)
    dmg_spell = _damage_spell(ac)
    if dmg_spell:
        # the defence is already standing there; the spell is cast on it.
        # Defenders hold their spot (busy at the tower) until it lands.
        if not _deploy_defender(m, def_key, nd):
            return None
        tw = m.towers[(DEF, "left")]
        hold = 1.0 + m.spell_delay(ATK, ac, tw.x, tw.y) + 0.1
        for e in m.entities:
            if e.team == DEF and not e.is_tower:
                e.deploy_timer = max(e.deploy_timer, hold)
    else:
        _deploy_attacker(m, atk_key, na)
        if partner:
            _deploy_partner(m, partner, atk_key)
    tower0 = {k: t.hp for k, t in m.towers.items()}
    spells_used, extra = {}, {ATK: 0.0, DEF: 0.0}
    banned = {atk_key, def_key}
    can_backup = {ATK: BACKUPS and ac.category != "spell",
                  DEF: BACKUPS and dc.category != "spell"}
    def_t = None
    trig = VARIANTS[variant]
    t = 0.0
    def_done = dmg_spell
    cast_done = not dmg_spell
    empty_t = 0.0
    uses0 = {}
    while t < MAX_T:
        m.elixir = [10.0, 10.0]
        if not cast_done and t >= 1.0:
            _cast_attack_spell(m, atk_key)
            cast_done = True
        if not def_done:
            tw = m.towers[(DEF, "left")]
            near = [e for e in _attackers(m)
                    if dist(e.x, e.y, tw.x, tw.y) <= trig]
            if ac.category == "spell" or near or t >= 6.0:
                def_done = _deploy_defender(m, def_key, nd)
                if not def_done:
                    return None
                def_t = t
        # backup spells: a side answers once its own card has had a moment
        if def_t is not None and t >= def_t + 1.0:
            if can_backup[DEF]:
                extra[DEF] += _maybe_backup(m, DEF, spells_used, banned)
            if can_backup[ATK]:
                extra[ATK] += _maybe_backup(m, ATK, spells_used, banned)
        m.update(DT)
        for b in brains.values():
            b._champion(DT)
        for e in m.entities:
            if e.card.is_champion:
                rec = uses0.setdefault(id(e), [e.team, e.card.ability_cost,
                                               e.card.ability_uses, e.ability_uses])
                rec[3] = e.ability_uses
        t += DT
        if m.finished:
            break
        # the engagement is over once the ATTACK is spent: surviving
        # defenders count at their value (their counter-push would be
        # answered in a real game, so it isn't simulated)
        busy = any(e.team == ATK and not e.is_tower for e in m.entities) or any(
            fx.kind in ("incoming", "graveyard", "poison", "timed_bomb")
            and fx.team == ATK for fx in m.effects)
        if def_done and cast_done and not busy:
            empty_t += DT
            if empty_t >= 1.0:
                break
        else:
            empty_t = 0.0
    # ---- score ----
    dealt = sum(tower0[k] - m.towers[k].hp for k in tower0 if k[0] == DEF)
    taken = sum(tower0[k] - m.towers[k].hp for k in tower0 if k[0] == ATK)
    score = (dealt - taken) / TOWER_HP_PER_ELIXIR
    a_cost, d_cost = float(ac.elixir) * na + extra[ATK], float(dc.elixir) * nd + extra[DEF]
    if partner:
        a_cost += cards.CARDS[partner].elixir
    # champion ability elixir counts as part of the card's cost
    for team, cost, u0, u1 in uses0.values():
        if team == ATK:
            a_cost += cost * (u0 - u1)
        else:
            d_cost += cost * (u0 - u1)
    a_keys = {atk_key} | ({ac.companion[0]} if ac.companion else set())
    if partner:
        a_keys.add(partner)
    a_left = _value_left(m, ATK, a_keys)
    d_left = _value_left(m, DEF, {def_key} | ({dc.companion[0]} if dc.companion else set()))
    score += (a_left - a_cost) - (d_left - d_cost)
    return score


# ===========================================================================
#  matrix / performance
# ===========================================================================
SPELL_TOP = 0.40      # spells are judged on their best 40 % of targets


def _row_job(args):
    """All engagements involving card X under a snapshot (+X's factor f)."""
    x, snapshot, f, _ = args
    install(snapshot, (x, f))
    out = {}
    opps = main_pool()
    if is_damage_spell(x):
        for y in opps:
            for v in range(len(VARIANTS)):
                out[("A", y, v)] = engage(x, y, v)
        return x, f, out
    cx = BASE[x].elixir
    for y in opps:
        if y == x:
            continue
        nx, ny = copies(cx, BASE[y].elixir)
        for v in range(len(VARIANTS)):
            out[("A", y, v)] = engage(x, y, v, nx, ny)
            out[("D", y, v)] = engage(y, x, v, ny, nx)
    return x, f, out


def performance(row, key=None):
    """Main cards: trimmed mean of (attack - defend) over the pool.
    Damage spells: mean of their best 40 % of casts."""
    if key is not None and is_damage_spell(key):
        vals = sorted((s for (r, y, v), s in row.items() if r == "A" and s is not None),
                      reverse=True)
        if not vals:
            return 0.0, 0
        top = vals[:max(1, int(len(vals) * SPELL_TOP))]
        return sum(top) / len(top), len(vals)
    # main cards: weighted by cost similarity (peers count most), then the
    # top & bottom 10 % of the weight mass are trimmed
    cx = BASE[key].elixir if key else None
    vals = []
    for (role, y, v), s in row.items():
        if role != "A" or s is None:
            continue
        d = row.get(("D", y, v))
        if d is None:
            continue
        w = cost_weight(cx, BASE[y].elixir) if cx is not None else 1.0
        vals.append((s - d, w))
    if not vals:
        return 0.0, 0
    vals.sort()
    tot = sum(w for _, w in vals)
    lo, hi = tot * TRIM, tot * (1 - TRIM)
    acc = num = den = 0.0
    for val, w in vals:
        a0, a1 = acc, acc + w
        acc = a1
        keep = max(0.0, min(a1, hi) - max(a0, lo))
        num += val * keep
        den += keep
    return (num / den if den else 0.0), len(vals)


def cost_weight(cx, cy):
    """How much a pairing counts: cards are judged mostly against cards of
    a similar price (the equal-elixir copies cover the rest)."""
    return 0.55 ** abs(cx - cy)


def matrix(snapshot, procs=4):
    keys = pool()
    jobs = [(x, snapshot, snapshot.get(x, 1.0), keys) for x in keys]
    res = {}
    with mp.Pool(procs) as p:
        for x, f, row in p.imap_unordered(_row_job, jobs):
            perf, n = performance(row, x)
            res[x] = {"perf": perf, "n": n,
                      "row": [[r, y, v, s] for (r, y, v), s in row.items()]}
            print("  %-18s perf %+6.2f  (f=%.3f, %d pairs)" % (x, perf, f, n), flush=True)
    return res


# ===========================================================================
#  tuning (one round against a frozen snapshot)
# ===========================================================================
F_MIN = float(os.environ.get("F_MIN", "0.3"))  # most a card may be nerfed (total)
F_MAX = 1.6                 # most a card may be buffed (total)
                            # (cards whose value is mostly outside a 1-v-1 fight -
                            #  huts, siege, spirits - would otherwise inflate)
SPELL_TARGET = 0.0    # set from the baseline: median spell performance
TOL = 0.12


STEP = float(os.environ.get("STEP", "1.5"))   # max power change per card per round


def _tune_job(args):
    x, snapshot, opponents = args
    f0 = snapshot.get(x, 1.0)
    lo = max(F_MIN, f0 / STEP)
    hi = min(F_MAX, f0 * STEP)
    pts = []

    target = SPELL_TARGET if is_damage_spell(x) else 0.0

    def evalf(f):
        _, _, row = _row_job((x, snapshot, f, opponents))
        p, n = performance(row, x)
        p -= target
        pts.append((f, p))
        return p

    p0 = evalf(f0)
    if abs(p0) <= TOL:
        return x, f0, p0, pts
    # probe in the corrective direction to measure the slope
    f1 = max(lo, min(hi, f0 * (0.82 if p0 > 0 else 1.22)))
    p1 = evalf(f1)
    fa, pa, fb, pb = f0, p0, f1, p1
    best = min(pts, key=lambda t: abs(t[1]))
    for _ in range(4):
        la, lb = math.log(fa), math.log(fb)
        if abs(pb - pa) < 1e-6:
            step = 0.35 if pb > 0 else -0.35
            ln = lb - step
        else:
            ln = lb - pb * (lb - la) / (pb - pa)
        ln = max(math.log(lo), min(math.log(hi), ln))
        ln = max(lb - 0.6, min(lb + 0.6, ln))     # don't jump wildly
        fn = math.exp(ln)
        if any(abs(fn - f) < 1e-3 for f, _ in pts):
            break                                 # pinned at the round's limit
        pn = evalf(fn)
        fa, pa, fb, pb = fb, pb, fn, pn
        best = min(pts, key=lambda t: abs(t[1]))
        if abs(pn) <= TOL:
            break
    return x, best[0], best[1], pts


def tune(snapshot, procs=4, skip=()):
    keys = [k for k in tune_pool() if k not in skip]
    only = os.environ.get("ONLY")            # tune just these cards (comma list)
    if only:
        keys = [k for k in keys if k in only.split(",")]
    jobs = [(x, snapshot, keys) for x in keys]
    out = {}
    with mp.Pool(procs) as p:
        for x, f, perf, pts in p.imap_unordered(_tune_job, jobs):
            out[x] = {"f": f, "perf": perf, "tries": pts}
            print("  %-18s f=%.3f -> perf %+5.2f   (%s)" % (
                x, f, perf, ", ".join("%.2f:%+.2f" % t for t in pts)), flush=True)
    return out


def next_snapshot(prev, tuned, damping=0.6):
    """Move each card part of the way toward its tuned factor (damped, so
    the whole pool shifting together doesn't overshoot), within STEP."""
    out = dict(prev)
    for k, v in tuned.items():
        f0 = prev.get(k, 1.0)
        ft = v["f"] if isinstance(v, dict) else v
        f = f0 * (ft / f0) ** damping
        out[k] = max(f0 / STEP, min(f0 * STEP, max(F_MIN, min(F_MAX, f))))
    return out


def load(path):
    if path and os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


if __name__ == "__main__":
    cmd = sys.argv[1]
    out_path = sys.argv[2]
    snap = load(sys.argv[3]) if len(sys.argv) > 3 else {}
    snap = {k: (v["f"] if isinstance(v, dict) else v) for k, v in snap.items()}
    procs = int(os.environ.get("PROCS", "4"))
    SPELL_TARGET = float(os.environ.get("SPELL_TARGET", "0"))
    if cmd == "matrix":
        res = matrix(snap, procs)
    elif cmd == "tune":
        # RESUME=log file of a partial run: cards already tuned are kept
        done = {}
        if os.environ.get("RESUME"):
            import re
            for ln in open(os.environ["RESUME"]):
                mm = re.match(r"\s+(\w+)\s+f=([\d.]+) -> perf ([-+\d.]+)", ln)
                if mm:
                    done[mm.group(1)] = {"f": float(mm.group(2)),
                                         "perf": float(mm.group(3)), "tries": []}
        res = tune(snap, procs, skip=set(done))
        res.update(done)
    elif cmd == "advance":
        # advance PREV_SNAPSHOT TUNED_ROUND -> OUT (the next frozen snapshot)
        tuned = load(sys.argv[4])
        damp = float(os.environ.get("DAMPING", "0.6"))
        res = next_snapshot(snap, tuned, damp)
    else:
        raise SystemExit("unknown command")
    with open(out_path, "w") as f:
        json.dump(res, f, indent=1)
