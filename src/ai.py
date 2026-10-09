"""
============================================================================
  AI.PY  --  The single-player opponent
============================================================================

A simple but functional opponent. As you noted, a lightweight AI can't
out-play an experienced human, so it is given RESOURCE advantages instead of
raw skill (see the AI_* knobs in config.py):

  * it regenerates elixir faster (AI_ELIXIR_MULT) and starts with a bonus,
  * it reacts after a short, tunable delay (AI_REACTION_TIME),
  * AI_AGGRESSION decides how eagerly it commits to attacking.

Behaviour each decision tick:
  1. DEFEND  -- if your troops threaten its towers, drop a good counter.
  2. ATTACK  -- if it has spare elixir, start/extend a push down a lane.
  3. VALUE SPELL -- nuke a clump of your troops with a spell when worth it.
============================================================================
"""

import random

import config as cfg
import cards
from engine import PLAYER, ENEMY, RIVER_TOP, RIVER_BOTTOM, dist


class AIController:
    def __init__(self, match):
        self.match = match
        self.decision_timer = 0.0
        self.reaction_accum = 0.0

    # -- helpers -------------------------------------------------------------
    def _towers(self):
        return [self.match.towers[(ENEMY, s)] for s in ("left", "right", "king")
                if self.match.towers[(ENEMY, s)].alive]

    def _player_troops(self):
        return [e for e in self.match.entities
                if e.team == PLAYER and not e.is_tower and not e.is_building]

    def _hand(self):
        return self.match.hands[ENEMY]

    def _affordable(self):
        el = self.match.elixir[ENEMY]
        out = []
        for i, key in enumerate(self._hand()):
            c = cards.CARDS[key]
            if c.elixir <= el:
                out.append((i, key, c))
        return out

    def _smart(self):
        return getattr(cfg, "AI_INTELLIGENCE", 0) >= 1

    # -- counter scoring -----------------------------------------------------
    def _score_counter(self, card, threat):
        """Higher = better answer to `threat`."""
        if card.category == "spell":
            return -1  # spells handled separately
        # siege/spawner buildings can't fight troops - never pick them to defend
        if card.category == "building" and (card.attacks == "buildings"
                                            or card.damage <= 0):
            return -1
        score = 0.0
        threat_air = threat.flying
        # must be able to hit it
        if threat_air and card.attacks != "air_ground":
            return -1
        # tanks (buildings-only or big hp) -> want high dps
        if threat.card.attacks == "buildings" or threat.max_hp > 1200:
            score += (card.damage / max(card.hit_speed, 0.3)) / 100.0
            if card.category == "building":
                score += 3.0  # buildings kite tanks well
        # swarms -> want splash
        if threat.card.count >= 3 or threat.max_hp < 200:
            score += 3.0 if card.splash > 0 else 0.0
        # general value: hp + dps, prefer not to overpay
        score += (card.hp + card.damage) / 400.0
        score -= card.elixir * 0.4
        if self._smart():
            # ramping (inferno) answers melt big tanks
            if card.ramp and threat.max_hp >= 1200:
                score += 4.0
            # prefer positive-elixir-trade answers
            score += max(0, threat.card.elixir - card.elixir) * 0.5
            # don't burn a swarm answer on a single splash unit
            if threat.card.splash > 0 and card.count >= 3:
                score -= 3.0
        return score

    def _best_counter(self, threat):
        best = None
        best_s = -0.5
        for i, key, c in self._affordable():
            s = self._score_counter(c, threat)
            if s > best_s:
                best, best_s = (i, key, c), s
        return best

    # -- placement -----------------------------------------------------------
    def _defensive_pos(self, threat, counter_card=None):
        # nearest own tower to the threat
        tw = min(self._towers(), key=lambda t: dist(t.x, t.y, threat.x, threat.y))
        # smart: a building answering a building-targeter goes to the classic
        # center "pull" spot so the tank walks between both towers
        if (self._smart() and counter_card is not None
                and counter_card.category == "building"
                and threat.card.attacks == "buildings"):
            return cfg.GRID_COLS / 2.0, RIVER_TOP - 6.5
        # place just in front of the tower, toward the threat, on AI's side
        x = threat.x
        y = min(threat.y + 1.0, RIVER_TOP - 1.0)
        y = max(y, tw.y + 0.5)
        return x, y

    def _attack_lane_x(self):
        left = self.match.towers[(PLAYER, "left")]
        right = self.match.towers[(PLAYER, "right")]
        if not left.alive:
            return cfg.PRINCESS_TOWER_INSET_X + 0.5
        if not right.alive:
            return cfg.GRID_COLS - cfg.PRINCESS_TOWER_INSET_X - 0.5
        # push the lane with the weaker tower
        target = left if left.hp <= right.hp else right
        return target.x

    def _try_play(self, hand_index, x, y):
        return self.match.play_card(ENEMY, hand_index, x, y)

    # -- spell value ---------------------------------------------------------
    def _try_value_spell(self):
        for i, key, c in self._affordable():
            if c.category != "spell" or c.spell_radius <= 0 or c.spell_damage <= 0:
                continue
            # find a clump of player troops
            troops = self._player_troops()
            best_pos, best_n = None, 0
            for anchor in troops:
                n = sum(1 for t in troops
                        if dist(anchor.x, anchor.y, t.x, t.y) <= c.spell_radius)
                worth = sum(t.max_hp for t in troops
                            if dist(anchor.x, anchor.y, t.x, t.y) <= c.spell_radius)
                if n > best_n and worth <= c.spell_damage * n * 1.5:
                    best_pos, best_n = (anchor.x, anchor.y), n
            need = 3 if c.elixir <= 3 else 4
            if best_pos and best_n >= need:
                return self._try_play(i, *best_pos)
        return False

    # -- deck-specific building play (all difficulties) -----------------------
    def _try_buildings(self):
        """Play the buildings the deck is built around.

        - Elixir Collector goes down at the back when elixir is overflowing.
        - Siege buildings (X-Bow, Mortar) are planted just behind the river so
          their long range reaches the player's princess tower.
        - Spawner huts go in the middle of the AI's own half.
        """
        m = self.match
        el = m.elixir[ENEMY]
        king_y = m.towers[(ENEMY, "king")].y
        for i, key, c in self._affordable():
            if c.category != "building":
                continue
            if c.generates_elixir and el >= c.elixir + 3:
                return self._try_play(i, cfg.GRID_COLS / 2.0, king_y + 1.5)
            if c.attacks == "buildings" and el >= c.elixir + 3:
                # siege: park at the river aimed at the weaker princess tower
                x = self._attack_lane_x()
                return self._try_play(i, x, RIVER_TOP - 1.5)
            if c.spawner and el >= c.elixir + 4:
                return self._try_play(i, cfg.GRID_COLS / 2.0, RIVER_TOP - 5.5)
        return False

    # -- smart-brain moves (Master / Insane) ----------------------------------
    def _try_finisher_spell(self):
        """Snipe a player tower that a spell can finish off right now."""
        for i, key, c in self._affordable():
            if c.category != "spell" or c.spell_damage <= 0 or c.dot:
                continue
            for s in ("left", "right", "king"):
                tw = self.match.towers[(PLAYER, s)]
                if tw.alive and tw.hp <= c.tower_dmg():
                    if self._try_play(i, tw.x, tw.y):
                        return True
        return False

    def _lead_wincon(self):
        """The AI's own building-targeter that is deepest into player land."""
        lead = None
        for e in self.match.entities:
            if (e.team == ENEMY and not e.is_tower and not e.is_building
                    and e.card.attacks == "buildings" and e.alive):
                if lead is None or e.y > lead.y:
                    lead = e
        return lead

    def _try_support_push(self):
        """Drop ranged support behind a tank that's already pushing."""
        if self.match.elixir[ENEMY] < 6:
            return False
        lead = self._lead_wincon()
        if lead is None or lead.y < RIVER_TOP - 4:
            return False   # no push worth supporting yet
        supports = [(i, k, c) for i, k, c in self._affordable()
                    if c.category == "troop" and c.range >= 3.0]
        if not supports:
            return False
        i, k, c = max(supports, key=lambda t: t[2].damage / max(t[2].hit_speed, 0.3))
        x = lead.x
        y = min(lead.y - 2.0, RIVER_TOP - 1.0)   # behind the tank, legal side
        return self._try_play(i, x, y)

    # -- main tick -----------------------------------------------------------
    def update(self, dt):
        m = self.match
        if m.finished:
            return
        self.decision_timer -= dt

        threats = [t for t in self._player_troops()
                   if min((dist(t.x, t.y, tw.x, tw.y) for tw in self._towers()),
                          default=99) <= cfg.AI_DEFEND_HP_TRIGGER]
        if threats:
            self.reaction_accum += dt
        else:
            self.reaction_accum = 0.0

        # champion ability: fire it whenever it's ready and there's a target
        champ, ready, cost = m.ability_status(ENEMY)
        if champ is not None and ready:
            near = any(champ.can_attack(e) and
                       ((e.x - champ.x) ** 2 + (e.y - champ.y) ** 2) ** 0.5 <= 6.0
                       for e in m.entities)
            typ = champ.card.ability_type
            hurt = champ.hp < champ.max_hp * 0.45
            if typ in ("escape", "getaway"):
                # escapes: bail out when hurt (Mighty Miner also likes to
                # leave his bomb on a tower he's drilling)
                use = near and (hurt or (typ == "escape" and champ.target is not None
                                         and champ.target.is_tower
                                         and champ.ramp_stage() >= 2))
            elif typ == "link":
                use = near and champ.partner is not None and champ.partner.alive
            elif typ == "skeletons":
                use = near or champ.souls >= 4
            else:
                use = near
            if use:
                m.activate_ability(ENEMY)

        if self.decision_timer > 0:
            return
        self.decision_timer = cfg.AI_DECISION_INTERVAL

        # 0) smart: finish a dying tower with a spell (instant win move)
        if self._smart() and self._try_finisher_spell():
            return

        # 1) value spell first
        if self._try_value_spell():
            return

        # 2) defend
        if threats and self.reaction_accum >= cfg.AI_REACTION_TIME:
            threat = min(threats, key=lambda t: min(
                dist(t.x, t.y, tw.x, tw.y) for tw in self._towers()))
            counter = self._best_counter(threat)
            if counter:
                i, key, c = counter
                x, y = self._defensive_pos(threat, c)
                if self._try_play(i, x, y):
                    return

        # 2.5) deck-specific buildings (collector / siege / huts)
        if not threats and self._try_buildings():
            return

        # 2.6) smart: reinforce an ongoing push with ranged support
        if self._smart() and not threats and self._try_support_push():
            return

        # 3) attack when we have spare elixir / feel aggressive
        el = m.elixir[ENEMY]
        want_push = el >= cfg.AI_MAX_ELIXIR_HOARD or random.random() < cfg.AI_AGGRESSION * 0.35
        if want_push and not threats:
            lane_x = self._attack_lane_x()
            king_y = m.towers[(ENEMY, "king")].y
            aff = self._affordable()
            # prefer a win condition / tank to lead
            tanks = [(i, k, c) for (i, k, c) in aff
                     if c.category == "troop" and (c.attacks == "buildings" or c.hp > 1000)]
            support = [(i, k, c) for (i, k, c) in aff
                       if c.category == "troop" and c.range >= 3.0]
            # smart brain applies pressure AT the bridge instead of the back,
            # and leads with a proper win condition when it can
            bridge_y = RIVER_TOP - 1.2
            pick = None
            if tanks and el >= 5:
                if self._smart():
                    wincons = [t for t in tanks if t[2].attacks == "buildings"]
                    pick = (max(wincons, key=lambda t: t[2].hp) if wincons
                            else max(tanks, key=lambda t: t[2].hp))
                    py = bridge_y
                else:
                    pick = random.choice(tanks)
                    py = king_y + 2.0
            elif support:
                pick = random.choice(support)
                py = bridge_y if self._smart() else king_y + 1.5
            elif aff:
                troop_aff = [t for t in aff if t[2].category == "troop"]
                if troop_aff:
                    pick = random.choice(troop_aff)
                    py = king_y + 1.5
            if pick:
                self._try_play(pick[0], lane_x, py)
