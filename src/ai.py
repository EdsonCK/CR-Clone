"""
============================================================================
  AI.PY  --  The single-player opponent
============================================================================

Two independent dials (Battle Setup screen, see config.py section 5):

  * INTELLIGENCE level 1-5 -> how well it plays (this file)
  * ELIXIR BOOST 0.5x-2.0x -> how much elixir it gets (engine.py)

Every level keeps the skills of the levels below it:

  1 Novice   slow reactions, often picks a random card, sloppy placement,
             only spells huge clumps, pushes at random.
  2 Casual   scores counters properly (air/ground, splash vs swarm, dps vs
             tanks), value spells, supports its own pushes, deck buildings.
  3 Skilled  lets towers handle tiny threats instead of wasting elixir,
             smart placement (buildings pull tanks to the centre, ranged
             units behind towers, swarms surround big melee), leads moving
             targets with spells, finishes low towers, counter-pushes,
             builds beatdown pushes from the back, keeps a defence reserve,
             picks lanes, wincon spells (Goblin Barrel / Graveyard / Miner
             on towers), times champion abilities.
  4 Expert   counts your elixir (roughly) and punishes when you're low,
             resets Infernos with stuns, cycles to its win condition,
             predicts where troops will be when its own lands.
  5 Master   exact elixir count, tracks the cards you've shown (keeps an
             anti-air card if you play air, spreads its push if you carry
             splash spells), opposite-lane pressure, Freeze / Rage combos.

Upgrades (Chaos / Endless, see endless_upgrades.py): every card is read
through match.card(team, key), so the AI reasons with its upgraded copies
(range, count, radius, cost...). On top of that an "upgrade profile"
(_profile, refreshed once a second) shifts its strategy: it favours the
cards it has upgraded, trusts buffed towers with small pushes, spends more
freely with elixir boons and commits to bigger pushes with army boons.
With no upgrades every factor is exactly 1 and it plays as it always has.

The AI is written in "local" coordinates: its own side is always the TOP of
the arena (small y). That makes it work for either team, which is how the
levels are benchmarked against each other (AI vs AI).
============================================================================
"""

import copy
import dataclasses
import math
import random

import config as cfg
import cards
import towers as towers_mod
from engine import PLAYER, ENEMY, RIVER_TOP, RIVER_BOTTOM, BRIDGE_X, dist

GRID_MID = cfg.GRID_COLS / 2.0
# tuned in Chaos (adaptive vs plain Master AI, same upgrades): these won 56
# of 96 games, +0.16 crowns a game
TRUST_TOWERS = False      # Master: skip planning while buffed towers handle it
FOCUS_WEIGHT = 3.0        # counter-score bonus per upgrade on a card
PUSH_BONUS = 2.0          # how much elixir / army upgrades lower the push bar
TOWER_TRUST = 0.5         # how much buffed towers raise "let the tower take it"
AIR_WINCONS = {"balloon", "lava_hound", "skeleton_barrel", "electro_dragon"}


def _share(card):
    """Rough elixir value of ONE unit of a card (sub-units are cheap)."""
    if card.elixir <= 0:
        return 0.4
    return card.elixir / max(card.count, 1)


def _dps(card):
    """Approximate damage per second of a whole card (all its units)."""
    if card.damage <= 0 or card.hit_speed <= 0:
        return 0.0
    dmg = card.damage
    if card.pellets:
        dmg *= card.pellets * 0.6
    if card.multi_target > 1:
        dmg *= card.multi_target
    if card.ramp:
        dmg *= 3.0
    elif card.ramp_stages:
        dmg *= 2.0
    return max(card.count, 1) * dmg / max(card.hit_speed, 0.2)


def _ehp(card):
    return max(card.count, 1) * (card.hp + card.shield_hp)


class AIController:
    def __init__(self, match, team=ENEMY, level=None, seat=None):
        self.match = match
        self.me = team
        # whose hand / elixir it plays with: the team in 1v1, a 2v2 seat
        # (2 = your teammate, 3 = the 2nd enemy) otherwise
        self.seat = team if seat is None else seat
        self.opp = 1 - team
        self.flip = (team == PLAYER)      # local coords: my side = top
        self.level = level if level in cfg.AI_LEVELS else cfg.AI_LEVEL
        self.p = cfg.AI_LEVELS[self.level]
        self.rng = random.Random()
        self.decision_timer = 0.4
        self.reaction_accum = 0.0
        self.clock = 0.0
        # memory
        self.seen_opp = set()              # opponent cards seen (card tracking)
        self._prev = {}                    # entity id -> (x, y)
        self.vel = {}                      # entity id -> (vx, vy) tiles/s
        self._noise = 0.0
        self._noise_t = 0.0
        self.last_def_lane = None
        self.defend_only = False           # Levels playtests: never attack
        self.plan = None                   # lookahead search in progress
        self.search_horizon = 10.0 if self.lv(5) else 4.0
        self.search_wide = self.lv(5)      # more cards / spots per search
        self.search_spells = self.lv(5)    # damage spells are candidates too
        self.search_policy = self.lv(4)    # rollouts: both sides keep playing
        self.search_all = self.lv(5)       # search offence + spells, not just defence
        self.search_samples = 2 if self.lv(5) else 1   # rollouts per candidate
        self.hold = 0.0                    # "waiting is best" - don't re-plan yet
        self.log = []                      # (time, card, why, x, local y, el)
        self._why = ""
        self._prof = None                  # upgrade profile (see _profile)
        self._prof_t = -9.0
        self._baseline()

    # ================================================================ coords
    def L(self, y):
        """World y -> local y (my side is the top)."""
        return cfg.GRID_ROWS - y if self.flip else y

    W = L   # local -> world is the same flip

    def lv(self, n):
        return self.level >= n

    # ============================================================ upgrades
    def _card(self, key, team=None):
        """The card as `team` (default: me) plays it - its upgraded copy."""
        return self.match.card(self.me if team is None else team, key)

    def _baseline(self):
        """Remember card levels as they were before any upgrade, on the
        match (so simulated copies share them)."""
        m = self.match
        if getattr(m, "_ai_base", None) is not None:
            return
        lv = {}
        for t in (PLAYER, ENEMY):
            for k in set(m.decks[t]):
                lv[(t, k)] = m.card_level(t, k)
        m._ai_base = {"lv": lv}

    def _lv_ratio(self, team, key):
        """hp / dmg multiplier from levels gained since the match started."""
        base = self.match._ai_base["lv"].get((team, key))
        if base is None:
            return 1.0
        now = self.match.card_level(team, key)
        if now == base:
            return 1.0
        return cards.level_mult(now) / cards.level_mult(base)

    def _mult(self, team, key, what):
        """Upgrade multiplier on a card's "dps", "dmg" or "hp" (boons x
        levels gained)."""
        b = self.match.boons.get(team) or {}
        r = self._lv_ratio(team, key)
        if what == "hp":
            return r * b.get("hp", 1.0)
        if what == "dmg":
            return r * b.get("dmg", 1.0)
        return r * b.get("dmg", 1.0) * b.get("atk", 1.0)

    def _profile(self):
        """What my upgrades say about how to play (refreshed once a second):
        tower  - how much stronger my towers shoot than at the start
        eco    - how much faster elixir comes (rate, discount, bounty)
        army   - how much stronger my troops are (boons and levels)
        focus  - {card: weight} cards I've upgraded (play them more)
        With no upgrades: tower = eco = army = 1.0 and focus is empty."""
        if self._prof is not None and self.clock - self._prof_t < 1.0:
            return self._prof
        m = self.match
        b = m.boons.get(self.me) or {}
        ratios = []
        for (t, side), e in m.towers.items():
            if t != self.me or not e.alive:
                continue
            d0, h0, r0 = self._tower_natural(e)
            r = (e.dmg / max(d0, 1e-6)) * (h0 / max(e.hit_speed, 1e-6))
            r *= 1.0 + 0.15 * max(0.0, e.range - r0)
            if e.card.slow:
                r *= 1.15
            if e.card.splash:
                r *= 1.2
            ratios.append(r)
        tower = (sum(ratios) / len(ratios)) if ratios else 1.0
        eco = b.get("elixir", 1.0) * (1.0 + 0.2 * b.get("discount", 0)) \
            * (1.0 + 0.8 * b.get("bounty", 0.0))
        deck = m.decks[self.seat]
        lvl = [self._lv_ratio(self.me, k) for k in deck] or [1.0]
        army = b.get("hp", 1.0) * b.get("dmg", 1.0) * b.get("atk", 1.0) \
            * b.get("speed", 1.0) * (sum(lvl) / len(lvl))
        ov = m.overrides.get(self.me) or {}
        focus = {}
        for k in deck:
            w = (1.0 if k in ov else 0.0) + max(0.0, self._lv_ratio(self.me, k) - 1.0) * 2.0
            if w > 0:
                focus[k] = w
        self._prof = {"tower": tower, "eco": eco, "army": army, "focus": focus,
                      "any": tower != 1.0 or eco != 1.0 or army != 1.0 or bool(focus)}
        self._prof_t = self.clock
        return self._prof

    @staticmethod
    def _tower_natural(e):
        """(damage, hit speed, range) a tower has with no upgrades."""
        if e.is_king:
            return (cfg.KING_TOWER_DMG * e.power[1], cfg.KING_TOWER_HITSPD,
                    cfg.KING_TOWER_RANGE)
        tt = towers_mod.get(e.tower_troop or towers_mod.DEFAULT)
        return (cfg.PRINCESS_TOWER_DMG * tt.dmg_mult * e.power[1], tt.hit_speed, tt.range)

    def _focus(self, key):
        """How much I've upgraded hand card `key` (0 = not at all)."""
        return self._profile()["focus"].get(key, 0.0)

    # ============================================================== queries
    def _towers(self, team=None):
        team = self.me if team is None else team
        return [self.match.towers[(team, s)] for s in ("left", "right", "king", "king2")
                if (team, s) in self.match.towers and self.match.towers[(team, s)].alive]

    def _opp_units(self):
        return [e for e in self.match.entities
                if e.team == self.opp and e.alive and not e.is_tower]

    def _my_units(self):
        return [e for e in self.match.entities
                if e.team == self.me and e.alive and not e.is_tower
                and not e.is_building]

    def _hand(self):
        return self.match.hands[self.seat]

    def _el(self):
        return self.match.elixir[self.seat]

    def _affordable(self, budget=None):
        """[(hand index, key, card)] the AI can pay for. The card is what
        actually comes out: Mirror -> a copy of the last card played (at its
        mirrored cost), Spirit Empress -> her dragon form at 6+ elixir."""
        el = self._el() if budget is None else budget
        out = []
        for i, k in enumerate(self._hand()):
            cost = self.match.card_cost(self.seat, k)
            pk = self.match.play_key(self.seat, k)
            if cost is None or pk is None or cost > el:
                continue
            c = self._card(pk)
            if pk != k or c.elixir != cost:
                c = dataclasses.replace(c, elixir=cost)
            out.append((i, k, c))
        return out

    def _lane(self, x):
        return 0 if x < GRID_MID else 1

    def _lane_x(self, lane):
        return BRIDGE_X[lane]

    def _predict(self, e, t):
        """Where entity e will be in t seconds (straight-line guess)."""
        vx, vy = self.vel.get(id(e), (0.0, 0.0))
        return e.x + vx * t, e.y + vy * t

    def _team_elixir(self, team):
        """A team's elixir (2v2: the most either of its players has)."""
        el = self.match.elixir
        return max(el[s] for s in range(team, len(el), 2))

    def opp_elixir(self):
        """Estimated opponent elixir (None = this level doesn't count it)."""
        if self.lv(5):
            return self._team_elixir(self.opp)
        if self.lv(4):
            return max(0.0, min(10.0, self._team_elixir(self.opp) + self._noise))
        return None

    def _deck_has_air_threat(self):
        return bool(self.seen_opp & AIR_WINCONS) or any(
            self._card(k, self.opp).flying and self._card(k, self.opp).attacks == "buildings"
            for k in self.seen_opp if k in cards.CARDS)

    def _opp_has_splash_spell(self):
        return bool(self.seen_opp & {"fireball", "poison", "lightning", "rocket",
                                     "arrows", "zap", "the_log", "tornado"})

    # ============================================================ placement
    def _roll_start(self, card, target_ly):
        """Where to start a rolling spell (local y) so it rolls through a
        target: just behind it - but The Log and Barbarian Barrel can only be
        placed on our own side, so from there it rolls into them."""
        ly = target_ly - 0.6
        if card.own_side:
            ly = min(ly, RIVER_TOP - 0.7)
        return ly

    def _place(self, idx, x, ly, card=None, exact=False):
        """Play hand card `idx` at (x, local y). Applies the level's sloppy
        placement jitter, keeps troops on a legal tile, retries nearby."""
        m = self.match
        key = self._hand()[idx]
        card = card or self._card(key)
        jit = 0.0 if exact else self.p["jitter"]
        if jit > 0:
            x += self.rng.gauss(0, jit * 0.6)
            ly += self.rng.gauss(0, jit * 0.6)
        x = min(max(x, 0.7), cfg.GRID_COLS - 0.7)
        ly = min(max(ly, 0.7), cfg.GRID_ROWS - 0.7)
        tries = [(x, ly)]
        if card.category != "spell" and not card.deploy_anywhere:
            cl = min(ly, RIVER_TOP - 0.7)
            tries += [(x, cl), (x, cl - 1.0), (x, cl - 2.5)]
        if card.category != "spell":
            # spot blocked (e.g. on top of a tower): spiral out to the
            # nearest legal tile instead of giving up on the play
            top = cfg.GRID_ROWS - 0.7 if card.deploy_anywhere else RIVER_TOP - 0.7
            for r in (1.0, 1.8, 2.6, 3.4):
                for k in range(8):
                    a = k * math.pi / 4
                    tries.append((min(max(x + math.cos(a) * r, 0.7), cfg.GRID_COLS - 0.7),
                                  min(max(ly + math.sin(a) * r, 0.7), top)))
        for (tx, tly) in tries:
            if m.play_card(self.seat, idx, tx, self.W(tly)):
                self.log.append((round(self.clock, 1), key, self._why,
                                 round(tx, 1), round(tly, 1),
                                 round(m.elixir[self.seat] + card.elixir, 1)))
                return True
        return False

    def _mistake(self):
        return self.rng.random() < self.p["mistakes"]

    # ============================================================== threats
    def _threats(self):
        """Opponent units that need answering, nearest-to-my-towers first."""
        towers = self._towers()
        if not towers:
            return []
        out = []
        for e in self._opp_units():
            dmin = min(dist(e.x, e.y, t.x, t.y) for t in towers)
            ly = self.L(e.y)
            if e.is_building:
                # only siege buildings that can reach my towers matter
                if (e.card.attacks == "buildings" or e.card.siege) and e.card.range > 0 and \
                        dmin <= e.card.range + 2.5:
                    out.append((dmin, e))
                continue
            if dmin <= self.p["defend_at"] or (self.lv(3) and ly < RIVER_TOP - 0.3):
                out.append((dmin, e))
        out.sort(key=lambda t: t[0])
        return [e for _, e in out]

    def _group(self, primary, threats):
        return [e for e in threats if dist(e.x, e.y, primary.x, primary.y) <= 4.0]

    def _group_stats(self, group):
        hp = sum(e.hp + e.shield for e in group)
        value = sum(_share(e.card) * (e.hp + e.shield) / max(e.max_hp + e.card.shield_hp, 1)
                    for e in group)
        dps_ground = sum(_dps(e.card) / max(e.card.count, 1)
                         * self._mult(e.team, e.key, "dps") for e in group
                         if e.card.attacks != "buildings")
        dps_air = sum(_dps(e.card) / max(e.card.count, 1)
                      * self._mult(e.team, e.key, "dps") for e in group
                      if e.card.attacks == "air_ground")
        return dict(
            hp=hp, value=value, dps_ground=dps_ground, dps_air=dps_air,
            air=any(e.flying for e in group),
            ground=any(not e.flying for e in group),
            swarm=len(group) >= 3 or any(e.card.count >= 3 for e in group),
            splash=any(e.card.splash > 0 or e.card.chain for e in group),
            tank=max((e.max_hp for e in group), default=0) >= 1200,
            bldg=any(e.card.attacks == "buildings" or e.card.siege for e in group),
        )

    # =============================================================== counters
    def _score_counter(self, card, prim, gs):
        if card.category == "spell":
            return None
        if card.category == "building" and (card.attacks == "buildings" or card.siege
                                            or card.damage <= 0):
            return None
        if card.category == "troop" and card.attacks == "buildings":
            return None                       # win conditions can't defend
        hits_air = card.attacks == "air_ground"
        if prim.flying and not hits_air:
            return None
        # ---- how fast it kills them vs how long it survives ----
        dps = max(_dps(card) * self._mult(self.me, card.key, "dps"), 1.0)
        target_hp = gs["hp"] if hits_air or not gs["air"] else max(gs["hp"] * 0.5, 1)
        ttk = target_hp / dps
        if card.flying:
            incoming = gs["dps_air"]
        else:
            incoming = gs["dps_ground"]
        if card.category == "building" or prim.card.attacks == "buildings":
            incoming = max(incoming, sum(_dps(e.card) / max(e.card.count, 1)
                                         for e in [prim]))
        survive = _ehp(card) * self._mult(self.me, card.key, "hp") / max(incoming, 1.0)
        score = min(survive / max(ttk, 0.1), 4.0) * 2.0
        # ---- matchup knowledge ----
        if gs["swarm"] and (card.splash > 0 or card.chain or card.death_damage):
            score += 3.0
        if gs["tank"] and dps >= 200:
            score += 1.5
        if self.lv(2):
            if gs["bldg"] and card.category == "building":
                score += 3.0                  # buildings pull tanks away
            if gs["tank"] and (card.ramp or card.count >= 3):
                score += 2.5                  # infernos / swarms melt tanks
            if gs["splash"] and card.count >= 3:
                score -= 3.0                  # don't feed swarms to splash
            if gs["air"] and hits_air and card.range >= 3:
                score += 1.0
        # ---- price: prefer cheap, positive trades ----
        score -= card.elixir * 0.35
        if self.lv(3):
            score -= max(0.0, card.elixir - gs["value"] - 1.0) * 0.6
        # ---- card memory: keep an anti-air card if they play air ----
        if self.lv(5) and hits_air and not gs["air"] and self._deck_has_air_threat():
            others = [k for k in self._hand()
                      if self._card(k).attacks == "air_ground"
                      and self._card(k).category != "spell"]
            if len(others) <= 1:
                score -= 2.5
        # ---- upgrades: lean on the cards I've powered up ----
        f = self._focus(card.key)
        if f:
            score += FOCUS_WEIGHT * f
        return score

    def _best_counter(self, prim, gs):
        aff = self._affordable()
        if self._mistake():
            fighters = [t for t in aff if t[2].category == "troop"
                        and t[2].attacks != "buildings"
                        and (not prim.flying or t[2].attacks == "air_ground")]
            return self.rng.choice(fighters) if fighters else None
        best, best_s = None, 0.3
        for i, k, c in aff:
            s = self._score_counter(c, prim, gs)
            if s is not None and s > best_s:
                best, best_s = (i, k, c), s
        return best

    def _defense_spot(self, card, prim, gs):
        """Local (x, y) for a defensive card."""
        towers = [t for t in self._towers() if not t.is_king] or self._towers()
        tw = min(towers, key=lambda t: dist(t.x, t.y, prim.x, prim.y))
        twx, twy = tw.x, self.L(tw.y)
        lead = 1.0 if self.lv(4) else 0.0
        px, py = self._predict(prim, lead) if lead else (prim.x, prim.y)
        ply = self.L(py)
        toward_mid = 1.0 if twx < GRID_MID else -1.0
        if not self.lv(3):
            return px, min(ply - 1.0, RIVER_TOP - 1.0)
        if card.category == "building":
            if gs["bldg"]:
                # classic pull spot: centre, ~4 tiles from the river, so the
                # tank walks across both princess towers' fire
                side = -1.0 if px < GRID_MID else 1.0
                return GRID_MID + side * 0.5, RIVER_TOP - 4.5
            return twx + toward_mid * 2.0, twy + 2.5
        if card.range >= 3.5:
            if gs["air"] and not gs["ground"]:
                return twx + toward_mid * 0.8, twy + 0.5    # under the tower
            # behind the tower line, toward the middle: the threat has to walk
            # through tower fire to reach it (an upgraded range sits further
            # back still and outranges it)
            extra = self._extra_range(card)
            return twx + toward_mid * 1.5, max(0.7, twy - 1.5 - 0.6 * extra)
        if card.count >= 3 and gs["tank"] and not gs["splash"]:
            return px, ply - 0.3                             # surround it
        if gs["swarm"] and (card.splash > 0 or card.death_damage):
            return px, ply - 1.2
        # melee: intercept between the threat and the tower
        dx, dy = twx - px, twy - ply
        d = math.hypot(dx, dy) or 1.0
        step = min(1.6, d)
        return px + dx / d * step, ply + dy / d * step

    def _extra_range(self, card):
        """Tiles of range an upgrade added to `card` (0 normally)."""
        base = cards.CARDS.get(card.key)
        return max(0.0, card.range - base.range) if base is not None else 0.0

    def _tower_can_handle(self, gs, group):
        if not self.lv(3):
            return False
        if any(e.card.kamikaze and e.card.attacks == "buildings" for e in group):
            return False
        t = 1.0 + (self._profile()["tower"] - 1.0) * TOWER_TRUST
        if t > 1.0:
            # buffed towers deal with bigger pushes on their own
            t = min(t, 4.0)
            return gs["hp"] <= 230 * t and gs["value"] <= 2.0 * t and not gs["bldg"]
        return gs["hp"] <= 230 and gs["value"] <= 2.0 and not gs["bldg"]

    def _try_defend(self, threats):
        self._why = "defend"
        prim = threats[0]
        group = self._group(prim, threats)
        gs = self._group_stats(group)
        flush = self._el() >= 9.0          # full on elixir: never just watch
        if not flush and self._tower_can_handle(gs, group):
            return False
        # defended enough already? (lots of my units near the threat)
        if self.lv(3) and not flush:
            mine = [u for u in self._my_units()
                    if dist(u.x, u.y, prim.x, prim.y) <= 4.0]
            mine_val = sum(_share(u.card) * u.hp / max(u.max_hp, 1) for u in mine)
            if mine_val >= gs["value"] * 1.3 + 1.0:
                return False
        counter = self._best_counter(prim, gs)
        if counter is None:
            return False
        i, k, c = counter
        x, ly = self._defense_spot(c, prim, gs)
        if self._place(i, x, ly, c):
            self.last_def_lane = self._lane(prim.x)
            return True
        return False

    # ================================================================= spells
    def _spell_damage_total(self, card, building=False, tower=False):
        mods = card.mods
        if mods or self.match.boons.get(self.me) or self._lv_ratio(self.me, card.key) != 1.0:
            # an upgraded spell: boons / levels, and repeats (Arrow Storm...)
            n = 1 + ((mods or {}).get("repeat") or (0, 0))[0]
            plain = dataclasses.replace(card, mods=None)
            return (self._spell_damage_total_base(plain, building, tower) * n
                    * self._mult(self.me, card.key, "dmg"))
        return self._spell_damage_total_base(card, building, tower)

    def _spell_damage_total_base(self, card, building=False, tower=False):
        if card.dot:
            mult = (2.2 if card.key == "earthquake" else 0.4) if (building or tower) else 1.0
            return card.spell_damage * card.duration * mult
        if card.pull:
            return card.spell_damage * card.duration
        if card.spell_kind == "void":
            return card.void_tiers[1][2 if tower else 1] * card.hits
        if tower and card.tower_damage is not None:
            return card.tower_damage * card.hits
        return card.spell_damage * card.hits

    def _void_value(self, card, x, y, units):
        """Void hits harder the fewer targets are inside: value = tier damage
        x 3 strikes on whatever stands in it (towers count as targets)."""
        inside = [e for e in units if dist(x, y, e.x, e.y) <= card.spell_radius + e.radius * 0.5]
        towers = [t for t in self._towers(self.opp)
                  if dist(x, y, t.x, t.y) <= card.spell_radius + t.radius * 0.5]
        n = len(inside) + len(towers)
        if not n:
            return 0.0, 0
        dmg = next(d for cap, d, _ in card.void_tiers if n <= cap) * card.hits
        v = 0.0
        for e in inside:
            ehp = e.hp + e.shield
            share = _share(e.card) * (ehp / max(e.max_hp + e.card.shield_hp, 1))
            v += share if ehp <= dmg else share * dmg / ehp * 0.8
        return v + 0.3 * len(towers), len(inside)

    def _spell_value(self, card, x, y, units):
        if card.spell_kind == "void":
            return self._void_value(card, x, y, units)
        v, n = 0.0, 0
        rolling = card.rolling
        for e in units:
            if card.rolling and e.flying:
                continue
            if rolling:
                lx0, ly0 = x, self.L(y)
                ely = self.L(e.y)
                if not (abs(e.x - lx0) <= card.spell_radius + e.radius
                        and ly0 - 0.8 <= ely <= ly0 + 8.0):
                    continue
            elif dist(x, y, e.x, e.y) > card.spell_radius + e.radius * 0.5:
                continue
            dmg = self._spell_damage_total(card, building=e.is_building)
            ehp = e.hp + e.shield
            share = _share(e.card) * (ehp / max(e.max_hp + e.card.shield_hp, 1))
            if ehp <= dmg:
                v += share
            else:
                v += share * dmg / ehp * 0.7
            if card.stun and e.card.ramp:
                v += 1.0
            if card.spell_kind == "vines" and e.flying and e.card.attacks == "buildings":
                v += 2.0                  # pulls a Balloon / Lava Hound down
            n += 1
        # chip damage on towers is worth something too
        for tw in self._towers(self.opp):
            if dist(x, y, tw.x, tw.y) <= card.spell_radius + tw.radius * 0.5 and not rolling:
                v += self._spell_damage_total(card, tower=True) / 300.0
        return v, n

    def _try_value_spell(self):
        self._why = "value"
        units = self._opp_units()
        if not units:
            return False
        need_n = 3 if not self.lv(2) else (2 if not self.lv(4) else 1)
        for i, k, c in self._affordable():
            if c.category != "spell" or (c.spawn_troops and not c.rolling
                                         and not c.own_side):
                continue
            if self._spell_damage_total(c) <= 0 or c.graveyard:
                continue
            cands = []
            for e in units:
                lead = (self.match.spell_delay(self.me, c, e.x, e.y)
                        if self.lv(3) else 0.0)
                if c.spell_kind == "void" and self.lv(3):
                    lead += 1.5           # strikes land over 4s: aim ahead
                x, y = self._predict(e, lead)
                if c.rolling:
                    y = self.W(self._roll_start(c, self.L(y)))
                cands.append((x, y))
            if self.lv(4):
                for a in units:
                    for b in units:
                        if id(a) < id(b) and dist(a.x, a.y, b.x, b.y) <= c.spell_radius * 1.6:
                            ax, ay = self._predict(a, lead)
                            bx, by = self._predict(b, lead)
                            cands.append(((ax + bx) / 2, (ay + by) / 2))
            best, best_v, best_n = None, 0.0, 0
            for (x, y) in cands:
                v, n = self._spell_value(c, x, y, units)
                if v > best_v:
                    best, best_v, best_n = (x, y), v, n
            if best and best_n >= need_n and best_v >= c.elixir * self.p["spell_need"]:
                if self._place(i, best[0], self.L(best[1]), c, exact=True):
                    return True
        return False

    def _try_finisher_spell(self):
        """Snipe an opponent tower that a spell can finish right now."""
        self._why = "finisher"
        for i, k, c in self._affordable():
            if c.category != "spell" or c.spell_damage <= 0:
                continue
            dmg = self._spell_damage_total(c, tower=True)
            for tw in self._towers(self.opp):
                if tw.hp <= dmg * 0.95 and not self._troops_will_take(tw):
                    if self._place(i, tw.x, self.L(tw.y), c, exact=True):
                        return True
        return False

    def _troops_will_take(self, tw):
        """True if my units already hitting tower `tw` will bring it down on
        their own (and before the clock runs out) - no spell needed."""
        m = self.match
        hitters = [u for u in m.entities
                   if u.team == self.me and u.alive and u.target is tw and not u.is_tower
                   and dist(u.x, u.y, tw.x, tw.y) <= u.range + tw.radius + 0.6]
        if not hitters:
            return False
        dps = sum(u.dmg / max(u.hit_speed, 0.2) for u in hitters)
        if dps <= 0:
            return False
        ttk = tw.hp / dps
        # how long the hitters last against the tower and nearby defenders
        tower_dps = tw.dmg / max(tw.hit_speed, 0.2) if tw.active or not tw.is_king else 0.0
        foes = [e for e in self._opp_units()
                if dist(e.x, e.y, tw.x, tw.y) < 5.0 and e.dmg > 0]
        threat = tower_dps + sum(e.dmg / max(e.hit_speed, 0.2) for e in foes)
        last = sum(u.hp + u.shield for u in hitters) / max(threat, 1.0)
        return ttk < min(last * 0.8, 4.0) and ttk + 1.0 < m.time_left

    def _try_inferno_reset(self):
        """Zap / stun an Inferno that is melting one of my big units."""
        self._why = "reset"
        for e in self._opp_units():
            if not (e.card.ramp and e.target is not None and e.target.team == self.me
                    and e.target.max_hp >= 900 and e.ramp_time >= 0.8):
                continue
            for i, k, c in self._affordable():
                if c.category == "spell" and (c.stun > 0 or c.freeze > 0
                                              or c.spell_damage >= e.hp):
                    return self._place(i, e.x, self.L(e.y), c, exact=True)
        return False

    def _has_buff_spell(self):
        return any(c.rage or c.spell_kind == "clone" for _, _, c in self._affordable())

    def _try_freeze_rage(self):
        """Master: Freeze defenders / Rage a big push at the enemy tower."""
        self._why = "freeze/rage"
        mine = [u for u in self._my_units() if self.L(u.y) > RIVER_BOTTOM]
        if not mine:
            return False
        push_val = sum(_share(u.card) for u in mine)
        cx = sum(u.x for u in mine) / len(mine)
        cy = sum(u.y for u in mine) / len(mine)
        for i, k, c in self._affordable():
            if c.key == "rage" and push_val >= 7 and len(mine) >= 3:
                return self._place(i, cx, self.L(cy), c, exact=True)
            if c.spell_kind == "clone" and push_val >= 6 and len(mine) >= 2:
                return self._place(i, cx, self.L(cy), c, exact=True)
            if c.freeze > 0 and push_val >= 6:
                defenders = [e for e in self._opp_units()
                             if dist(e.x, e.y, cx, cy) <= 4.5]
                tw_near = [t for t in self._towers(self.opp)
                           if dist(t.x, t.y, cx, cy) <= 4.5]
                if len(defenders) + 2 * len(tw_near) >= 3:
                    pts = defenders + tw_near
                    fx = sum(p.x for p in pts) / len(pts)
                    fy = sum(p.y for p in pts) / len(pts)
                    return self._place(i, fx, self.L(fy), c, exact=True)
        return False

    # ================================================================ offense
    def _is_wincon(self, c):
        if c.category == "troop" and c.attacks == "buildings":
            return True
        if c.deploy_anywhere:                                 # Miner
            return True
        if c.category == "spell" and (c.graveyard or (c.spawn_troops and not c.rolling
                                                      and not c.own_side)):
            return True
        if c.category == "building" and c.siege:
            return True                                       # X-Bow, Mortar
        return False

    def _pick_lane(self):
        m = self.match
        opp_l = m.towers[(self.opp, "left")]
        opp_r = m.towers[(self.opp, "right")]
        if not opp_l.alive and opp_r.alive:
            return 0 if self.lv(3) and opp_r.hp > 900 else 1
        if not opp_r.alive and opp_l.alive:
            return 1 if self.lv(3) and opp_l.hp > 900 else 0
        if not self.lv(2):
            return self.rng.randint(0, 1)
        score = [0.0, 0.0]
        for lane, tw in ((0, opp_l), (1, opp_r)):
            if tw.alive:
                score[lane] += (1.0 - tw.hp / tw.max_hp) * 3.0
        if self.lv(3):
            # go where my own troops already are (counter-push)
            for u in self._my_units():
                score[self._lane(u.x)] += _share(u.card) * 0.3
            # avoid lanes guarded by their defensive buildings
            for e in self._opp_units():
                if e.is_building and e.card.damage > 0:
                    score[self._lane(e.x)] -= 1.0
        if self.lv(5):
            # opposite-lane pressure: they're committed in one lane
            for e in self._opp_units():
                if self.L(e.y) < RIVER_TOP + 3:
                    score[1 - self._lane(e.x)] += _share(e.card) * 0.4
        return 0 if score[0] >= score[1] else 1

    def _wincon_spot(self, c, lane, from_back=False):
        """Local (x, y) where a win condition goes for a push down `lane`."""
        m = self.match
        side = "left" if lane == 0 else "right"
        tw = m.towers[(self.opp, side)]
        if not tw.alive:
            tw = m.towers[(self.opp, "king")]
        tly = self.L(tw.y)
        if c.category == "spell":                     # barrel / graveyard
            return tw.x, tly + (0.0 if c.graveyard else -1.2)
        if c.deploy_anywhere:                         # Miner: onto the tower
            return tw.x + (0.9 if lane == 0 else -0.9), tly - 1.9
        if c.category == "building":                  # siege at the bridge
            return self._lane_x(lane), RIVER_TOP - 2.0
        if from_back:                                 # behind my princess tower
            return m.towers[(self.me, side)].x, 2.4
        return self._lane_x(lane), RIVER_TOP - 0.9    # bridge

    def _play_wincon(self, i, c, lane, from_back=False):
        bridge = ((c.category == "building" and c.siege)
                  or (c.category == "troop" and c.attacks == "buildings" and not from_back))
        if bridge:
            # X-Bow / Mortar / Hog-style pushes at the bridge go down a lane
            # that still has a Princess Tower, never an empty one
            m = self.match
            here = m.towers[(self.opp, "left" if lane == 0 else "right")]
            there = m.towers[(self.opp, "right" if lane == 0 else "left")]
            if not here.alive and there.alive:
                lane = 1 - lane
        x, ly = self._wincon_spot(c, lane, from_back)
        exact = c.category == "spell" and self.lv(3)
        return self._place(i, x, ly, c, exact=exact)

    def _reserve(self):
        """Elixir to keep for defence when attacking (level 3+)."""
        if not self.lv(3):
            return 0.0
        oe = self.opp_elixir()
        eco = self._profile()["eco"]
        if oe is None:
            return 2.0 / eco if eco > 1.0 else 2.0
        r = min(4.0, max(0.0, oe - 3.0))
        return r / eco if eco > 1.0 else r

    def _push_bonus(self):
        """Elixir off the 'wait until I'm nearly full' bar when my elixir or
        army is boosted (0 with no upgrades, up to 2)."""
        p = self._profile()
        if not p["any"]:
            return 0.0
        return PUSH_BONUS * min(2.0, max(0.0, (p["eco"] - 1.0) * 2.0
                                         + (p["army"] - 1.0) * 1.5))

    def _try_offense(self, threats):
        self._why = "offense"
        m = self.match
        el = self._el()
        if threats and not self.lv(4):
            return False
        mult = m.elixir_multiplier()
        aff = self._affordable()
        if not aff:
            return False
        oe = self.opp_elixir()
        reserve = self._reserve() if not threats else 3.0
        lane = self._pick_lane()
        wincons = [t for t in aff if self._is_wincon(t[2])]
        supports = [t for t in aff if t[2].category == "troop"
                    and t[2].attacks != "buildings" and t[2].range >= 3.0
                    and not self._is_wincon(t[2])]
        tanks = [t for t in aff if t[2].category == "troop"
                 and (t[2].hp >= 1500 or (t[2].enchant and t[2].hp >= 1200))]

        def ok(c):
            return el - c.elixir >= reserve

        # 1) punish: they're low on elixir -> hit hard right now
        self._why = "punish"
        if self.lv(4) and oe is not None and oe <= 2.5 and wincons:
            i, k, c = max(wincons, key=lambda t: t[2].elixir)
            if self._play_wincon(i, c, lane):
                return True

        # 2) support a push that's already rolling (my units crossing over)
        self._why = "support"
        if self.lv(2):
            pushers = [u for u in self._my_units()
                       if self.L(u.y) >= RIVER_TOP - 4 and u.target is not None]
            pval = sum(_share(u.card) for u in pushers)
            if pushers and (pval >= 3 or any(u.card.attacks == "buildings" for u in pushers)):
                lead = max(pushers, key=lambda u: self.L(u.y))
                pick = None
                if supports:
                    pick = max(supports, key=lambda t: _dps(t[2]) * (1.0 + 0.6 * self._focus(t[1])))
                elif self.lv(3) and wincons and not any(
                        u.card.attacks == "buildings" for u in pushers):
                    pick = wincons[0]           # counter-push: add the wincon
                if pick and (ok(pick[2]) or el >= 8.5 - self._push_bonus()):
                    i, k, c = pick
                    if self._is_wincon(c):
                        if self._play_wincon(i, c, self._lane(lead.x)):
                            return True
                    else:
                        spread = 0.0
                        if self.lv(5) and self._opp_has_splash_spell():
                            spread = 1.8 if lead.x < GRID_MID else -1.8
                        ly = min(self.L(lead.y) - 2.0, RIVER_TOP - 0.9)
                        if self._place(i, lead.x + spread, ly, c):
                            return True

        # 2b) a Rune Giant on the field wants fast hitters to enchant
        self._why = "enchant"
        if self.lv(2):
            rgs = [u for u in self._my_units() if u.card.enchant
                   and len([e for e in getattr(u, "_enchanted", []) if e.alive]) < 2]
            if rgs:
                rg = rgs[0]
                hitters = [t for t in aff if t[2].category == "troop"
                           and t[2].attacks != "buildings" and not self._is_wincon(t[2])
                           and not t[2].kamikaze and t[2].hit_speed <= 1.4]
                if hitters and (ok(min(hitters, key=lambda t: t[2].elixir)[2]) or el >= 7):
                    i, k, c = max(hitters, key=lambda t: _dps(t[2]) / max(t[2].elixir, 1))
                    ly = min(self.L(rg.y) - 1.5, RIVER_TOP - 0.9)
                    if self._place(i, rg.x, ly, c):
                        return True

        # 3) freeze / rage / clone combos
        if (self.lv(5) or (self.lv(3) and self._has_buff_spell())) and self._try_freeze_rage():
            return True

        # 4) start a push
        self._why = "push"
        hoard = 9.0 if self.lv(2) else 9.8
        aggressive = 0.25 + 0.08 * self.level
        if mult > 1:
            aggressive += 0.15
        bonus = self._push_bonus()
        if bonus:
            # elixir / army upgrades: push sooner and more often
            hoard -= bonus
            aggressive += 0.12 * bonus
        want = el >= hoard or self.rng.random() < aggressive * 0.35
        if not want:
            return False
        if self.lv(3) and tanks and el >= 8.0 - bonus and mult <= 2.0:
            # beatdown: heavy tank from the back, support it at the bridge
            i, k, c = max(tanks, key=lambda t: t[2].hp * (1.0 + 0.5 * self._focus(t[1])))
            if self._is_wincon(c) or c.elixir >= 6 or c.enchant:
                return self._play_wincon(i, c, lane, from_back=True) \
                    if self._is_wincon(c) else self._place(
                        i, self.match.towers[(self.me, "left" if lane == 0 else "right")].x,
                        2.4, c)
        if wincons:
            pick = (max(wincons, key=lambda t: t[2].hp * (1.0 + 0.5 * self._focus(t[1])))
                    if self.lv(2) else self.rng.choice(wincons))
            if ok(pick[2]) or el >= hoard:
                return self._play_wincon(pick[0], pick[2], lane)
        if self.lv(2) and supports and el >= hoard:
            fav = [t for t in supports if self._focus(t[1])]
            i, k, c = self.rng.choice(fav or supports)
            return self._place(i, self._lane_x(lane), RIVER_TOP - 3.0, c)
        if not self.lv(2):
            troops = [t for t in aff if t[2].category == "troop"]
            if troops:
                i, k, c = self.rng.choice(troops)
                return self._place(i, self._lane_x(lane), RIVER_TOP - 2.0, c)
        return False

    def _try_buildings(self):
        """Deck buildings: collector at the back, spawner huts mid-field."""
        self._why = "building"
        el = self._el()
        king = self.match.towers[(self.me, "king")]
        for i, k, c in self._affordable():
            if c.category != "building":
                continue
            if c.generates_elixir and el >= c.elixir + 3:
                oe = self.opp_elixir()
                if oe is not None and oe >= 8:
                    continue                 # they'd punish it
                x = king.x + (self.rng.choice((-3.5, 3.5)) if self.lv(3) else 0)
                return self._place(i, x, self.L(king.y) + (0.5 if self.lv(3) else 1.5), c)
            if c.spawner and el >= c.elixir + 3:
                return self._place(i, GRID_MID, RIVER_TOP - 5.5, c)
        return False

    def _try_cycle(self):
        """Expert: play a cheap card safely at the back to reach the wincon."""
        self._why = "cycle"
        if any(self._is_wincon(self._card(k)) for k in self._hand()):
            return False
        if self._el() < 7:
            return False
        cheap = [t for t in self._affordable() if t[2].category == "troop"
                 and t[2].elixir <= 3 and t[2].attacks != "buildings"]
        if not cheap:
            return False
        i, k, c = min(cheap, key=lambda t: t[2].elixir)
        king = self.match.towers[(self.me, "king")]
        return self._place(i, king.x + self.rng.choice((-2.5, 2.5)),
                           self.L(king.y) + 1.5, c)

    def _defend_cycle(self, threats):
        """Defend-only (Levels autopilot): at full elixir with no useful
        defensive play, cycle the cheapest card - a troop behind the King
        Tower, or a spell onto the nearest threat - to dig for an answer."""
        self._why = "cycle"
        aff = self._affordable()
        if not aff:
            return False
        nonspell = [t for t in aff if t[2].category != "spell"
                    and not self._is_wincon(t[2])]
        if nonspell:
            i, k, c = min(nonspell, key=lambda t: t[2].elixir)
            king = self.match.towers[(self.me, "king")]
            return self._place(i, king.x + self.rng.choice((-2.5, 2.5)),
                               self.L(king.y) + 1.5, c)
        if threats:
            i, k, c = min(aff, key=lambda t: t[2].elixir)
            e = threats[0]
            return self._place(i, e.x, self.L(e.y), c, exact=True)
        return False

    def _avoid_leak(self):
        """Never sit at full elixir: dump the cheapest sensible card."""
        self._why = "leak"
        if self._el() < 9.8:
            return False
        aff = self._affordable()
        troops = [t for t in aff if t[2].category != "spell"]
        if not troops:
            # a hand of spells only: cast the cheapest somewhere useful so
            # the cycle keeps moving (buffs on my units, damage on theirs)
            if not aff:
                return False
            i, k, c = min(aff, key=lambda t: t[2].elixir)
            mine = self._my_units()
            if (c.rage or c.spell_kind == "clone") and mine:
                u = max(mine, key=lambda u: u.max_hp)
                return self._place(i, u.x, self.L(u.y), c, exact=True)
            foes = self._opp_units() or self._towers(self.opp)
            if foes and not c.own_side:
                e = min(foes, key=lambda e: e.hp)
                return self._place(i, e.x, self.L(e.y), c, exact=True)
            king = self.match.towers[(self.me, "king")]
            return self._place(i, king.x, self.L(king.y) + 2.0, c, exact=True)
        i, k, c = min(troops, key=lambda t: t[2].elixir)
        if self._is_wincon(c):
            return self._play_wincon(i, c, self._pick_lane())
        return self._place(i, self._lane_x(self._pick_lane()), RIVER_TOP - 2.5, c)

    # ============================================================= lookahead
    # Expert/Master defend by SEARCH: they clone the match, try each candidate
    # play (card x position, or doing nothing) in a quick simulation, score the
    # outcome and pick the best. One or two candidates are simulated per frame
    # so the game never stutters - the "thinking" doubles as reaction time.
    def _memo(self):
        return {id(c): c for c in cards.CARDS.values()}

    def _evaluate(self, sim):
        """Score a (simulated) match state from my point of view, in elixir."""
        me, op = self.me, self.opp
        if sim.finished:
            return 200.0 if sim.winner == me else (-200.0 if sim.winner == op else 0.0)
        v = 0.0
        for s in ("left", "right", "king"):
            kw = 1.4 if s == "king" else 1.0
            v += kw * (sim.towers[(me, s)].hp - sim.towers[(op, s)].hp) / 110.0
        v += 12.0 * (sim.crowns[me] - sim.crowns[op])
        for e in sim.entities:
            if e.is_tower or not e.alive:
                continue
            frac = (e.hp + e.shield) / max(e.max_hp + e.card.shield_hp, 1)
            val = _share(e.card) * frac
            if sim.overrides or sim.boons[me] or sim.boons[op]:
                val *= self._worth(sim, e)
            if e.card.lifetime:
                val *= max(e.lifetime, 0.0) / e.card.lifetime
            ly = self.L(e.y)
            if e.team == me:
                depth = max(0.0, ly - RIVER_BOTTOM) / (cfg.GRID_ROWS - RIVER_BOTTOM)
                v += val * (1.0 + 0.5 * depth)
            else:
                depth = max(0.0, RIVER_TOP - ly) / RIVER_TOP
                v -= val * (1.0 + 0.8 * depth)
        v += sum(sim.elixir[me::2]) - sum(sim.elixir[op::2])
        return v

    def _worth(self, sim, e):
        """Value multiplier of a unit carrying upgrades (1.0 otherwise)."""
        w = 1.0
        if e.key in (sim.overrides.get(e.team) or {}):
            w += 0.4
        b = sim.boons.get(e.team) or {}
        w *= (b.get("hp", 1.0) * b.get("dmg", 1.0)) ** 0.5
        return w

    def _rollout(self, cand, horizon, seed=0):
        sim = copy.deepcopy(self.match, self._memo())
        sim.record_events = False
        sim.events = []
        if cand is not None:
            idx, key, x, ly = cand
            if sim.hands[self.seat][idx] != key:
                return None
            if not sim.play_card(self.seat, idx, x, self.W(ly)):
                return None
        pols = []
        if self.search_policy:
            # both sides keep playing a solid (Skilled) game after this move,
            # so attacks get answered and "wait" means "play normally"
            for seat in range(len(sim.hands)):
                team = seat % 2
                pa = AIController(sim, team=team, level=3, seat=seat)
                pa.rng.seed(seed * 2 + seat)
                pa.decision_timer = 0.3 + 0.2 * seat
                pols.append(pa)
        dt = 0.1
        for _ in range(int(horizon / dt)):
            sim.update(dt)
            for pa in pols:
                pa.update(dt)
            if sim.finished:
                break
        return self._evaluate(sim)

    def _defense_candidates(self, threats):
        if not threats:
            return [None] + self._spell_candidates()
        prim = threats[0]
        group = self._group(prim, threats)
        gs = self._group_stats(group)
        towers = [t for t in self._towers() if not t.is_king] or self._towers()
        tw = min(towers, key=lambda t: dist(t.x, t.y, prim.x, prim.y))
        twx, twy = tw.x, self.L(tw.y)
        mid = 1.0 if twx < GRID_MID else -1.0
        px, py = self._predict(prim, 1.0)
        ply = self.L(py)
        scored = []
        for i, k, c in self._affordable():
            sc = self._score_counter(c, prim, gs)
            if sc is not None:
                scored.append((sc, i, k, c))
        scored.sort(key=lambda t: -t[0])         # (upgraded cards score higher)
        if not self.search_wide:
            scored = scored[:2]
        cands = [None]                                   # None = wait
        for sc, i, k, c in scored:
            spots = [self._defense_spot(c, prim, gs)]
            if c.category == "building":
                spots.append((GRID_MID + (-0.5 if px < GRID_MID else 0.5),
                              RIVER_TOP - 4.5))
                spots.append((twx + mid * 2.0, twy + 2.5))
            else:
                spots.append((px, ply - 0.4))                      # on top
                spots.append((twx + mid * 1.5, twy - 1.0))         # behind tower
                if self.search_wide:
                    spots.append((twx + mid * 3.5, twy + 2.0))     # pull to centre
            if not self.search_wide:
                spots = spots[:2]
            for (x, ly) in spots:
                x = min(max(x, 0.7), cfg.GRID_COLS - 0.7)
                ly = min(max(ly, 0.7), RIVER_TOP - 0.7)
                cands.append((i, k, x, ly))
        if self.search_spells:
            cands += self._spell_candidates()
        return cands

    def _spell_candidates(self):
        """Damage spells aimed by the value heuristic."""
        cands = []
        if True:
            units = self._opp_units()
            for i, k, c in self._affordable():
                if c.category != "spell" or c.spell_damage <= 0 or c.graveyard \
                        or (c.spawn_troops and not c.rolling):
                    continue
                best, bv = None, 0.0
                for e in units:
                    x, y = self._predict(e, self.match.spell_delay(self.me, c, e.x, e.y))
                    if c.rolling:
                        y = self.W(self._roll_start(c, self.L(y)))
                    v, n = self._spell_value(c, x, y, units)
                    if v > bv:
                        best, bv = (x, y), v
                if best and bv >= c.elixir * 0.6:
                    cands.append((i, k, best[0], self.L(best[1])))
        return cands

    def _offense_candidates(self):
        """Master: attacking plays worth simulating."""
        out = []
        aff = self._affordable()
        m = self.match
        lanes = [ln for ln, s in ((0, "left"), (1, "right"))
                 if m.towers[(self.opp, s)].alive] or [0, 1]
        pushers = [u for u in self._my_units()
                   if self.L(u.y) >= RIVER_TOP - 4 and u.target is not None]
        lead = max(pushers, key=lambda u: self.L(u.y)) if pushers else None
        for i, k, c in aff:
            if self._is_wincon(c):
                for ln in lanes:
                    out.append((i, k) + self._wincon_spot(c, ln))
                    if c.category == "troop" and c.hp >= 1500:
                        out.append((i, k) + self._wincon_spot(c, ln, from_back=True))
            elif c.category == "troop" and lead is not None:
                ly = min(self.L(lead.y) - 2.0, RIVER_TOP - 0.9)
                out.append((i, k, lead.x, ly))
            elif c.category == "troop" and c.range >= 3.0 and self._el() >= 8:
                for ln in lanes:
                    out.append((i, k, self._lane_x(ln), RIVER_TOP - 2.5))
            elif c.category == "troop" and self._focus(k) and self._el() >= 6:
                # an upgraded troop can lead a push on its own: try it at
                # the bridge (the search judges whether it's worth it)
                for ln in lanes:
                    out.append((i, k, self._lane_x(ln), RIVER_TOP - 0.9))
        return out

    def _start_plan(self, threats):
        horizon = self.search_horizon
        if self.match.is_2v2:
            horizon = min(horizon, 6.0)       # 4 players: cheaper look-ahead
        cands = self._defense_candidates(threats) if threats else [None]
        if self.search_all:
            cands += self._offense_candidates()
            if not threats and self.search_spells:
                cands += [c for c in self._defense_candidates([])[1:]]
        # de-duplicate, keep it to a sensible number of simulations
        seen, uniq = set(), []
        for c in cands:
            key = None if c is None else (c[0], round(c[2]), round(c[3]))
            if key in seen:
                continue
            seen.add(key)
            uniq.append(c)
        uniq = uniq[:16]
        jobs = [(ci, k) for ci in range(len(uniq)) for k in range(self.search_samples)]
        self.plan = {"cands": uniq, "jobs": jobs, "i": 0,
                     "vals": [[] for _ in uniq], "horizon": horizon,
                     "seed": self.rng.randint(0, 10 ** 6)}

    def _plan_step(self):
        """Simulate the next candidate(s); act once all are scored."""
        pl = self.plan
        per_tick = 1 if self.search_policy else 2     # ~4-12 ms per simulation
        m = self.match
        if m.is_2v2:
            # 3 AIs share one frame's thinking budget: one simulation per
            # frame between them, so a 2v2 never stutters
            if getattr(m, "_think_t", None) == m.elapsed:
                return
            m._think_t = m.elapsed
            per_tick = 1
        while pl["i"] < len(pl["jobs"]) and per_tick > 0:
            ci, k = pl["jobs"][pl["i"]]
            v = self._rollout(pl["cands"][ci], pl["horizon"], pl["seed"] + 977 * k)
            if v is not None:
                pl["vals"][ci].append(v)
            pl["i"] += 1
            per_tick -= 1
        if pl["i"] < len(pl["jobs"]):
            return
        self.plan = None
        results = [(sum(v) / len(v), c) for v, c in zip(pl["vals"], pl["cands"]) if v]
        if not results:
            return
        wait = next((s for s, c in results if c is None), -1e9)
        best_s, best_c = max(results, key=lambda t: t[0])
        if best_c is None or best_s < wait + 0.4:
            self.hold = 0.5                  # nothing beats the default plan
            if self.search_policy:
                # rollouts assumed "wait" = play my normal (Skilled) game
                self._heuristic_turn(self._threats(), allow_search=False)
            return
        i, k, x, ly = best_c
        if i < len(self._hand()) and self._hand()[i] == k:
            self._why = "search"
            if self._place(i, x, ly, exact=True):
                self.hold = 0.3

    # ============================================================== champions
    def _hero(self):
        """Use a Hero's one-shot ability at a sensible moment."""
        m = self.match
        h, ready, cost = m.hero_status(self.seat)
        if h is None or not ready:
            return
        near = [e for e in m.entities if e.alive and e.team == self.opp and not e.is_tower
                and dist(e.x, e.y, h.x, h.y) <= 4.0]
        hpf = h.hp / max(h.max_hp, 1)
        k = h.key
        tgt = h.target
        on_tower = tgt is not None and tgt.alive and tgt.is_tower
        close = [e for e in near if dist(e.x, e.y, h.x, h.y) <= 2.6]
        ground_close = [e for e in close if not e.flying]
        use = False
        if k == "knight":
            use = len(near) >= 2 or (near and hpf < 0.6)
        elif k == "giant":
            use = any(e.max_hp >= 500 for e in close if not e.is_building)
        elif k == "mini_pekka":
            use = hpf < 0.5 or on_tower or getattr(h, "pancakes", 0) >= 2.0
        elif k in ("musketeer", "goblin_banner"):
            use = len(near) >= 1 or on_tower or k == "goblin_banner"
        elif k == "ice_golem":
            use = len(near) >= 2
        elif k == "valkyrie":
            use = len(ground_close) >= 2 or (ground_close and hpf < 0.5)
        elif k == "wizard":
            use = len(near) >= 2 or (near and hpf < 0.5)
        elif k == "mega_minion":
            weak = [e for e in m.entities if e.alive and e.team == self.opp
                    and not e.is_tower and e.hp <= 399 * 0.506 * h.power[1]]
            use = bool(weak) or hpf < 0.4
        elif k == "barbarian":
            use = hpf < 0.5 or len(ground_close) >= 2
        elif k == "magic_archer":
            use = (near and hpf < 0.6) or on_tower
        elif k == "balloon":
            use = bool(ground_close) or hpf < 0.4
        elif k == "bowler":
            use = len(near) >= 2 or on_tower
        elif k == "dark_prince":
            use = on_tower or len(near) >= 2 or hpf < 0.5
        elif k == "tombstone":
            use = True
        elif k == "berserker":
            use = (tgt is not None and tgt.alive and not tgt.is_tower
                   and dist(tgt.x, tgt.y, h.x, h.y) <= 2.0) or hpf < 0.35
        elif k == "ice_wizard":
            use = bool(near)
        elif k == "electro_wizard":
            use = len(near) >= 2 or (near and hpf < 0.5)
        if use or (self.lv(1) and not self.lv(3) and near):
            m.activate_hero(self.seat)

    def _champion(self, dt):
        m = self.match
        self._hero()
        champ, ready, cost = m.ability_status(self.seat)
        if champ is None or not ready:
            return
        enemies = [e for e in m.entities if champ.can_attack(e)
                   and not (e.is_king and not e.active)]
        near = [e for e in enemies if dist(e.x, e.y, champ.x, champ.y) <= 6.0]
        if not self.lv(3):
            # basic brain: fire as soon as anything is close
            if near and m.ability_has_target(champ):
                m.activate_ability(self.seat)
            return
        typ = champ.card.ability_type
        hpf = champ.hp / max(champ.max_hp, 1)
        attackers = [e for e in m.entities if e.team == self.opp and e.alive
                     and e.target is champ]
        shots = [p for p in m.projectiles if p.team == self.opp and p.target is champ]
        use = False
        if typ == "cloak":
            use = len(attackers) >= 2 or (attackers and hpf < 0.6)
        elif typ == "escape":
            bombable = [e for e in near if not e.flying and
                        dist(e.x, e.y, champ.x, champ.y) <= champ.card.ability_radius]
            bomb_val = sum(_share(e.card) for e in bombable if not e.is_tower)
            on_tower = champ.target is not None and champ.target.is_tower
            use = (hpf < 0.4 and near) or bomb_val >= 4 or \
                  (on_tower and hpf < 0.55 and len(attackers) >= 2)
        elif typ == "rescue":
            close = [e for e in near if not e.flying and not e.is_building
                     and dist(e.x, e.y, champ.x, champ.y) <= 3.0]
            use = bool(close) or (attackers and hpf < 0.6)
        elif typ == "chain_dash":
            in_r = [e for e in enemies if not e.is_tower and
                    dist(e.x, e.y, champ.x, champ.y) <= champ.card.ability_radius]
            use = len(in_r) >= 3 or (len(in_r) >= 2 and hpf < 0.5) or \
                (in_r and hpf < 0.3)
        elif typ == "skeletons":
            use = champ.souls >= 6 or (near and hpf < 0.35) or len(near) >= 4
        elif typ == "protect":
            use = len(shots) >= 2 or len(attackers) >= 3 or \
                (attackers and hpf < 0.5) or \
                (champ.target is not None and champ.target.is_tower and attackers)
        elif typ == "link":
            part = champ.partner
            if part is not None and part.alive:
                from engine import _seg_dist
                on_line = [e for e in near if _seg_dist(
                    e.x, e.y, champ.x, champ.y, part.x, part.y) <= 1.2]
                use = len(on_line) >= 2 or sum(
                    _share(e.card) for e in on_line if not e.is_tower) >= 4
        elif typ == "getaway":
            t = champ.target
            # in melee with a sturdy target -> hop out and dash back in for
            # another double-damage hit; or escape when hurt
            in_melee = (t is not None and t.alive and
                        dist(champ.x, champ.y, t.x, t.y) <= champ.range + t.radius + 0.2)
            use = (in_melee and t.hp > champ.dmg * 1.5) or (hpf < 0.35 and near)
        if use and m.ability_has_target(champ):
            m.activate_ability(self.seat)

    # ============================================================== tracking
    def _track(self, dt):
        m = self.match
        seen_now = {}
        for e in m.entities:
            if e.team != self.opp or e.is_tower:
                continue
            eid = id(e)
            self.seen_opp.add(e.key)      # (not keyed by id(): ids get reused)
            px, py = self._prev.get(eid, (e.x, e.y))
            if dt > 0:
                vx, vy = (e.x - px) / dt, (e.y - py) / dt
                ox, oy = self.vel.get(eid, (vx, vy))
                self.vel[eid] = (ox * 0.7 + vx * 0.3, oy * 0.7 + vy * 0.3)
            seen_now[eid] = (e.x, e.y)
        self._prev = seen_now
        self.vel = {k: v for k, v in self.vel.items() if k in seen_now}
        for fx in m.effects:
            if fx.kind == "incoming" and fx.team == self.opp and fx.card_key:
                self.seen_opp.add(fx.card_key)
        # Expert's elixir count drifts a little (re-rolled every 2s)
        self._noise_t -= dt
        if self._noise_t <= 0:
            self._noise_t = 2.0
            self._noise = self.rng.gauss(0, 0.9) if not self.lv(5) else 0.0

    # =============================================================== main tick
    def update(self, dt):
        m = self.match
        if m.finished:
            return
        self.clock += dt
        self._track(dt)
        self._champion(dt)
        self.decision_timer -= dt
        if m.is_2v2:
            # 2v2: when my partner just played, give its card a moment to
            # land before deciding, so we don't both answer the same push
            spent = m.stats["spent"][self.seat ^ 2]
            if spent > getattr(self, "_partner_spent", 0.0):
                self.decision_timer = max(self.decision_timer, 0.45)
            self._partner_spent = spent
        if self.hold > 0:
            self.hold -= dt
        if self.plan is not None:
            self._plan_step()
            return

        threats = self._threats()
        if threats:
            self.reaction_accum += dt
        else:
            self.reaction_accum = 0.0

        if self.decision_timer > 0:
            return
        self.decision_timer = self.p["interval"] * self.rng.uniform(0.85, 1.15)

        if self.lv(3) and self._try_finisher_spell():
            return
        if self.lv(4) and self._try_inferno_reset():
            return
        if self.search_all:
            # Master: every decision is searched (defence, attack, spells)
            min_el = 4.0
            p = self._profile()
            if p["any"]:
                min_el -= min(1.5, self._push_bonus())
                if (threats and p["tower"] > 1.15 and self._el() < 9.0
                        and TRUST_TOWERS):
                    group = self._group(threats[0], threats)
                    if self._tower_can_handle(self._group_stats(group), group):
                        return                  # my buffed towers have this
            if self.hold <= 0 and (not threats or self.reaction_accum >= self.p["reaction"]) \
                    and (threats or self._el() >= min_el):
                self._start_plan(threats)
            return
        self._heuristic_turn(threats)

    def _heuristic_turn(self, threats, allow_search=True):
        """One decision using the rule-based brain (all levels)."""
        if threats and (self.reaction_accum >= self.p["reaction"] or not allow_search):
            if self.lv(4) and allow_search:
                if self.hold <= 0:
                    self._start_plan(threats)
                    return
            elif self._try_defend(threats):
                return
        if self._try_value_spell():
            return
        if self.defend_only:
            # nothing in hand answers the threat: cycle like a player would
            if self._el() >= 9.5:
                self._defend_cycle(threats)
            return
        if not threats and self._try_buildings():
            return
        if self._try_offense(threats):
            return
        if self.lv(4) and not threats and self._try_cycle():
            return
        self._avoid_leak()
