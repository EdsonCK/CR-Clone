"""
============================================================================
  TROPHYROAD.PY  --  Trophy Road screen + battles (mixed into game.Game)
============================================================================

The Trophy Road screen shows your trophies and arena, who your next
opponent is (picked from your trophy count - see trophy.py), and the road
of rewards. "Battle!" starts a ranked battle: win trophies, lose a few,
unlock arenas, rewards and Tower Troops on the way up.

Tower Troops are chosen per deck on the Decks screen (the "Tower" chip);
the helpers for that live here too.
============================================================================
"""

import random
import pygame

import config as cfg
import cards
import sprites
import towers
import trophy
import profile_data
from engine import Match, PLAYER, ENEMY
from ai import AIController
from ui import lt_c, dk_c, Button, WHITE

ROW_H = 46
GOLD_COL = (255, 214, 92)
SHARD_COL = (200, 140, 255)


class TrophyMixin:
    # ============================================================ tower troops
    def _tower_owned(self, key):
        return self.sandbox or trophy.tower_troop_unlocked(key, self.profile.best_trophies)

    def _tower_troop(self, slot=None):
        """The Tower Troop of a saved deck slot (falls back to the Princess)."""
        pr = self.profile
        slot = pr.active_slot if slot is None else slot
        key = pr.decks[slot].get("tower", towers.DEFAULT)
        return key if key in towers.TOWER_TROOPS and self._tower_owned(key) else towers.DEFAULT

    def _cycle_tower_troop(self):
        owned = [k for k in towers.ORDER if self._tower_owned(k)]
        cur = self._tower_troop()
        nxt = owned[(owned.index(cur) + 1) % len(owned)] if cur in owned else owned[0]
        self.profile.decks[self.profile.active_slot]["tower"] = nxt
        self.profile.save()
        if len(owned) == 1:
            nxt_lock = next((t for t in towers.ORDER if not self._tower_owned(t)), None)
            if nxt_lock:
                self.deck_msg = "%s unlocks at %d trophies (Trophy Road)." % (
                    towers.get(nxt_lock).name, towers.get(nxt_lock).unlock)
        else:
            self.deck_msg = "Tower Troop: " + towers.get(nxt).name

    def _tower_chip_rect(self):
        return pygame.Rect(cfg.WINDOW_W - 150, 45, 138, 22)

    def _draw_tower_chip(self):
        r = self._tower_chip_rect()
        tt = towers.get(self._tower_troop())
        hover = r.collidepoint(pygame.mouse.get_pos())
        bg = (66, 58, 40) if not hover else (86, 76, 52)
        pygame.draw.rect(self.screen, bg, r, border_radius=7)
        pygame.draw.rect(self.screen, (214, 176, 84), r, 1, border_radius=7)
        self.screen.blit(sprites.get_sprite(tt.key, 24), (r.x + 2, r.y - 2))
        self._text(self._fit("Tower: " + tt.name, self.font_s, r.w - 30), self.font_s,
                   (255, 230, 160), topleft=(r.x + 26, r.y + 4))

    def _apply_tower_troops(self, m, ai_key=None):
        """Man the towers of a fresh match (player's deck choice, AI's pick)."""
        m.set_tower_troop(PLAYER, self._tower_troop())
        if ai_key:
            m.set_tower_troop(ENEMY, ai_key)

    # ================================================================ screen
    def _open_trophy(self):
        self.state = "trophy"
        rows = trophy.road_rewards()
        idx = next((i for i, r in enumerate(rows) if r[0] > self.profile.trophies),
                   len(rows) - 1)
        self.trophy_scroll = 0
        self._trophy_set_scroll((len(rows) - 1 - idx) * ROW_H - 140)

    def _trophy_view(self):
        return pygame.Rect(12, 196, cfg.WINDOW_W - 22, cfg.WINDOW_H - 196 - 66)

    def _trophy_set_scroll(self, v):
        rows = trophy.road_rewards()
        view = self._trophy_view()
        mx = max(0, len(rows) * ROW_H - view.h)
        self.trophy_scroll = int(max(0, min(mx, v)))

    def _trophy_buttons(self):
        y = cfg.WINDOW_H - 56
        return [Button((12, y, 96, 44), "Deck", lambda: self._open_player_deck("trophy"),
                       "primary"),
                Button((cfg.WINDOW_W // 2 - 90, y - 4, 180, 52), "Battle!",
                       self._start_trophy_battle, "go"),
                Button((cfg.WINDOW_W - 108, y, 96, 44), "Back", lambda: self._goto("menu"),
                       "dark")]

    def _trophy_click(self, pos):
        for b in self._trophy_buttons():
            if b.click(pos):
                return

    def _trophy_opponent(self):
        t = self.profile.trophies
        ai = trophy.bot_level(t)
        lv = trophy.bot_card_level(t, self.profile.tower_level(self.player_deck))
        return ai, lv

    def _draw_trophy(self):
        pr = self.profile
        cx = cfg.WINDOW_W // 2
        t = pr.trophies
        a = trophy.arena(t)
        ai = trophy.arena_index(t)
        nxt = trophy.next_arena(t)
        self._screen_title("Trophy Road", 24)
        # ---- header: arena, trophies, next arena, opponent ----
        head = pygame.Rect(10, 48, cfg.WINDOW_W - 20, 140)
        self._panel(head, border=a.color, top=dk_c(a.color, 110), bottom=(26, 26, 36))
        self._text(a.name, self.font_l, lt_c(a.color, 40), center=(cx, head.y + 22),
                   outline=True)
        self._text("Arena %d" % (ai + 1) if ai < len(trophy.ARENAS) - 1 else "Top arena",
                   self.font_s, (220, 220, 230), center=(cx, head.y + 44))
        self._trophy_icon(cx - 46, head.y + 68, 10)
        self._text("%d" % t, self.font_l, GOLD_COL, topleft=(cx - 32, head.y + 54))
        self._text("best %d" % pr.best_trophies, self.font_s, (190, 190, 205),
                   topleft=(cx + 44, head.y + 62))
        bar = pygame.Rect(head.x + 16, head.y + 88, head.w - 32, 10)
        pygame.draw.rect(self.screen, (20, 20, 28), bar, border_radius=5)
        if nxt is not None:
            f = (t - a.trophies) / max(1, nxt.trophies - a.trophies)
            pygame.draw.rect(self.screen, a.color, (bar.x, bar.y, int(bar.w * f), bar.h),
                             border_radius=5)
            self._text("next: %s at %d" % (nxt.name, nxt.trophies), self.font_s,
                       (210, 214, 230), center=(cx, bar.bottom + 9))
        else:
            pygame.draw.rect(self.screen, a.color, bar, border_radius=5)
        opp, olv = self._trophy_opponent()
        self._text("Opponent: %d %s AI  -  cards Lv %d  -  1.0x elixir" % (
            opp, cfg.AI_LEVELS[opp]["name"], olv), self.font_s,
            self.LEVEL_COLORS.get(opp, WHITE), center=(cx, head.bottom - 14))
        # ---- the road (highest trophies at the top, like the real game) ----
        rows = trophy.road_rewards()
        view = self._trophy_view()
        self.screen.set_clip(pygame.Rect(0, view.y, cfg.WINDOW_W, view.h))
        next_tro = next((r[0] for r in rows if r[0] > t), None)
        for i, (tro, label, gold, shards, tt) in enumerate(reversed(rows)):
            r = pygame.Rect(view.x, view.y + i * ROW_H - self.trophy_scroll, view.w, ROW_H - 4)
            if r.bottom < view.y or r.y > view.bottom:
                continue
            paid = tro <= pr.road_paid
            here = tro == next_tro
            gate = any(ar.trophies == tro for ar in trophy.ARENAS)
            col = next((ar.color for ar in trophy.ARENAS if ar.trophies == tro), (70, 76, 96))
            bg = dk_c(col, 120) if gate else (36, 40, 52)
            if paid:
                bg = dk_c(bg, 20)
            pygame.draw.rect(self.screen, bg, r, border_radius=8)
            pygame.draw.rect(self.screen, (250, 222, 110) if here else
                             (col if gate else (60, 66, 84)), r, 2 if here else 1,
                             border_radius=8)
            self._trophy_icon(r.x + 16, r.centery, 7)
            self._text(str(tro), self.font_sb, GOLD_COL if not paid else (170, 160, 120),
                       topleft=(r.x + 28, r.centery - 9))
            self._text(self._fit(label, self.font_sb if gate else self.font_s, 150),
                       self.font_sb if gate else self.font_s,
                       WHITE if not paid else (160, 160, 170), topleft=(r.x + 84, r.centery - 9))
            x = r.right - 12
            if tt:
                self.screen.blit(sprites.get_sprite(tt, 38), (x - 38, r.y + 1))
                x -= 44
            if shards:
                self._text("+%d" % shards, self.font_sb, SHARD_COL, topleft=(x - 26, r.centery - 9))
                self._shard(x - 34, r.centery, 7)
                x -= 54
            if gold:
                self._text("+%d" % gold, self.font_sb, GOLD_COL, topleft=(x - 40, r.centery - 9))
                self._coin(x - 48, r.centery, 7)
            if paid:
                pygame.draw.circle(self.screen, (90, 190, 110), (r.x + 76, r.centery), 6)
            if here:                         # next reward: a pointer on the left
                cyy = r.centery
                pygame.draw.polygon(self.screen, (250, 222, 110),
                                    [(r.x - 8, cyy - 7), (r.x - 1, cyy), (r.x - 8, cyy + 7)])
                self._text("next", self.font_s, (250, 222, 110), topleft=(r.x + 84, r.y + 26))
        self.screen.set_clip(None)
        for b in self._trophy_buttons():
            b.draw(self.screen, self.font_l if b.label == "Battle!" else self.font_m)

    def _trophy_icon(self, x, y, r):
        """A little gold trophy cup."""
        x, y = int(x), int(y)
        pygame.draw.rect(self.screen, (150, 110, 30), (x - r // 2, y + r // 2, r, r // 2))
        pygame.draw.rect(self.screen, GOLD_COL, (x - r, y - r, 2 * r, int(r * 1.2)),
                         border_bottom_left_radius=r, border_bottom_right_radius=r)
        pygame.draw.rect(self.screen, (150, 110, 30), (x - r, y - r, 2 * r, int(r * 1.2)), 1,
                         border_bottom_left_radius=r, border_bottom_right_radius=r)
        pygame.draw.line(self.screen, GOLD_COL, (x - r - 3, y - r + 2), (x - r, y), 2)
        pygame.draw.line(self.screen, GOLD_COL, (x + r + 3, y - r + 2), (x + r, y), 2)

    # ================================================================ battle
    def _start_trophy_battle(self):
        if len(self.player_deck) != cfg.DECK_SIZE:
            self._open_player_deck("trophy")
            self.deck_msg = "Pick 8 cards first!"
            return
        t = self.profile.trophies
        ai, alv = self._trophy_opponent()
        rng = random.Random()
        # the opponent: a variation of a preset archetype (sometimes a random
        # deck), and a Tower Troop from those unlocked at your arena
        if rng.random() < 0.85:
            self.trophy_deck_name = rng.choice(sorted(cards.AI_DECK_PRESETS))
            ai_deck = cards.deck_variant(self.trophy_deck_name, rng)
        else:
            self.trophy_deck_name = "Random"
            ai_deck = cards.random_deck()
        ai_tower = rng.choice([k for k in towers.ORDER if trophy.tower_troop_unlocked(k, t)])
        cfg.apply_ai_settings(ai, 1.0)
        self._arena_surf = None
        self.level_run = None
        self.mode = "trophy"
        self.trophy_ai = ai
        # Evolutions / Heroes: yours as unlocked; the bot's by trophy count
        specials = self._match_specials(self.player_deck)
        n_evo, n_hero = trophy.bot_specials(t)
        ae, ah = self._special_cards(ai_deck, owned=False, n_evo=n_evo, n_hero=n_hero)
        specials["evo_cards"][ENEMY] = ae
        specials["hero_cards"][ENEMY] = ah
        self.match = Match(self.player_deck, ai_deck, **specials,
                           card_levels={PLAYER: self.profile.deck_levels(self.player_deck),
                                        ENEMY: alv},
                           tower_levels={PLAYER: self.profile.tower_level(self.player_deck),
                                         ENEMY: alv})
        self.match.record_events = True
        self._apply_tower_troops(self.match, ai_tower)
        self.ai = AIController(self.match, team=ENEMY, level=ai)
        self._audio = {}
        self.fx.clear()
        self.sfx.play("match_start", 0.9, min_gap=0.0)
        self.selected = None
        self.state = "match"

    def _trophy_rewards(self, w):
        """Trophies, battle gold and any Trophy Road rewards crossed."""
        pr = self.profile
        m = self.match
        ai = getattr(self, "trophy_ai", 1)
        before = pr.trophies
        delta = trophy.trophy_change(None if w is None else (w == PLAYER),
                                     m.crowns[PLAYER], m.crowns[ENEMY], before)
        pr.trophies = max(0, before + delta)
        old_best = pr.best_trophies
        pr.best_trophies = max(pr.best_trophies, pr.trophies)
        lbl = "%+d trophies  (%d)" % (delta, pr.trophies)
        self.last_rewards.append((lbl, 0, 0))
        self._reward("Victory" if w == PLAYER else "Played",
                     profile_data.battle_gold(w == PLAYER, ai, 1.0, m.crowns[PLAYER]))
        if w == PLAYER:
            got = pr.add_shard_points(ai)
            if got:
                self.last_rewards.append(("Shard from wins", 0, got))
        # rewards along the road (paid once, the first time you get there)
        for tro, label, gold, shards, tt in trophy.road_rewards():
            if pr.road_paid < tro <= pr.best_trophies:
                self._reward(("Arena: " if shards else "Road: ") + label, gold, shards)
                if tt:
                    self.last_rewards.append(("Unlocked " + towers.get(tt).name, 0, 0))
                pr.road_paid = tro
        if trophy.arena_index(pr.best_trophies) > trophy.arena_index(old_best):
            a = trophy.arena(pr.best_trophies)
            self.last_rewards.append(("New arena: " + a.name, 0, 0))
        rec = self.stats.setdefault("L%d" % ai, self._blank_stats()["L1"])
        rec["cf"] += m.crowns[PLAYER]
        rec["ca"] += m.crowns[ENEMY]
        if w == PLAYER:
            rec["wins"] += 1
            rec["best"] = max(rec["best"], 1.0)
            rec["even_w"] += 1
        elif w == ENEMY:
            rec["losses"] += 1
        else:
            rec["draws"] += 1
        self._save_stats()
