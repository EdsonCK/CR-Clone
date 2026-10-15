"""
============================================================================
  MODES.PY  --  Special Battles + Endless Survival (mixed into game.Game)
============================================================================

Special Battles are normal 3-minute battles against the AI with a twist.
The AI's cards are always level SPECIAL_AI_LEVEL (12) so upgrading your own
cards is what makes them easier; its intelligence is picked on the Special
Modes screen. Rewards: gold per battle, +1 shard for the first win in each.

  Triple Elixir   triple elixir the whole match
  Sudden Death    3 minutes of overtime: the first tower to fall decides it
  Mirror Match    the AI plays YOUR deck (and evolutions)
  Draft           take turns picking cards from pairs - you get one, the AI
                  the other - until both have 8
  Rage Battle     every troop is permanently raged (+35% speed & attack)
  Random Decks    both sides get a random deck
  Double Trouble  double elixir, double-strength towers and a 5 minute clock
  2v2 Battle      you and an AI teammate against two AIs, as in the real
                  game: each player has their own deck, hand and elixir bar
                  and deploys anywhere on their side; the towers, crowns and
                  clock are shared. Your teammate's hand and elixir show
                  beside the arena, and "Ally" pops up where it plays.

Endless Survival uses the Levels rules (your Level Deck, no enemy towers,
miasma) with procedurally generated waves that never stop - see
levels.endless_wave(). Your best wave is saved.
============================================================================
"""

import random
import pygame

import config as cfg
import cards
import sprites
import levels
import profile_data
from engine import Match, PLAYER, ENEMY, ALLY, ENEMY2
from ai import AIController
from ui import lt_c, dk_c, Button, WHITE

MODES = [
    ("duo", "2v2 Battle", "You + an AI teammate vs two AIs.", "barbarians"),
    ("triple", "Triple Elixir", "Triple elixir from the first second.", "elixir_collector"),
    ("sudden", "Sudden Death", "All overtime: first tower down wins.", "king_tower"),
    ("mirror", "Mirror Match", "The AI plays your deck.", "archer_queen"),
    ("draft", "Draft", "Pick from pairs - the AI gets the leftovers.", "magic_archer"),
    ("rage", "Rage Battle", "Everyone is permanently raged.", "rage"),
    ("random", "Random Decks", "Both sides get a random deck.", "skeleton_barrel"),
    ("double", "Double Trouble", "x2 elixir, x2 tower HP, 5 minutes.", "princess"),
    ("endless", "Endless Survival", "Survive endless waves (Level Deck).", "skeleton_king"),
]
MODE_NAMES = {k: n for k, n, _, _ in MODES}


class ModesMixin:
    # ================================================================ screen
    def _open_modes(self):
        self.state = "modes"

    def _mode_items(self):
        """(key, name, description, icon) of every card on the Modes tab:
        the Special Battles, Endless Survival and the Sandbox."""
        return list(MODES) + [("sandbox", "Sandbox",
                               "Place any card for either side, pause, inspect.",
                               "elixir_collector")]

    def _mode_rect(self, i):
        cols = 3 if cfg.WINDOW_W >= 500 else 2
        w = (cfg.WINDOW_W - 24 - 8 * (cols - 1)) // cols
        h = 112
        r, c = divmod(i, cols)
        return pygame.Rect(12 + c * (w + 8), 128 + r * (h + 8), w, h)

    def _modes_level_rects(self):
        n = len(cfg.AI_LEVELS)
        gap = 5
        w = (cfg.WINDOW_W - 24 - gap * (n - 1)) // n
        return [(pygame.Rect(12 + i * (w + gap), 82, w, 34), lv)
                for i, lv in enumerate(sorted(cfg.AI_LEVELS))]

    def _modes_buttons(self):
        out = []
        for i, (k, name, _, _) in enumerate(self._mode_items()):
            r = self._mode_rect(i)
            if k == "sandbox":
                out.append(Button((r.x + 8, r.bottom - 36, r.w - 16, 30), "Open",
                                  self._open_sandbox, "primary"))
                continue
            out.append(Button((r.x + 8, r.bottom - 36, r.w - 16, 30), "Play",
                              (lambda k=k: self._start_mode(k)),
                              "gold" if k == "endless" else "go"))
        if not getattr(self, "embedded", False):
            out.append(Button((cfg.WINDOW_W // 2 - 70, cfg.WINDOW_H - 52, 140, 40), "Back",
                              lambda: self._goto("menu"), "dark"))
        return out

    def _modes_click(self, pos):
        for r, lv in self._modes_level_rects():
            if r.collidepoint(pos):
                self._set_ai_level(lv)
                return
        for b in self._modes_buttons():
            if b.click(pos):
                return

    def _draw_modes(self):
        mouse = pygame.mouse.get_pos()
        self._screen_title("Special Modes", 26)
        self._text("AI intelligence  (AI cards are level %d)" % profile_data.SPECIAL_AI_LEVEL,
                   self.font_s, (200, 204, 220), center=(cfg.WINDOW_W // 2, 70))
        for r, lv in self._modes_level_rects():
            sel = lv == self.ai_level
            col = self.LEVEL_COLORS[lv]
            bg = dk_c(col, 120) if sel else (44, 50, 62)
            if r.collidepoint(mouse):
                bg = lt_c(bg, 16)
            pygame.draw.rect(self.screen, bg, r, border_radius=8)
            pygame.draw.rect(self.screen, col if sel else dk_c(col, 70), r,
                             2 if sel else 1, border_radius=8)
            self._text("%d %s" % (lv, cfg.AI_LEVELS[lv]["name"]), self.font_s,
                       WHITE, center=r.center)
        for i, (k, name, desc, icon) in enumerate(self._mode_items()):
            r = self._mode_rect(i)
            gold = k == "endless"
            self._panel(r, border=(214, 176, 84) if gold else (110, 120, 150),
                        top=(70, 58, 40) if gold else (52, 54, 72),
                        bottom=(36, 30, 24) if gold else (30, 30, 42))
            self.screen.blit(sprites.get_sprite(icon, 40), (r.x + 6, r.y + 6))
            self._text(self._fit(name, self.font_sb, r.w - 54), self.font_sb,
                       topleft=(r.x + 50, r.y + 8))
            for j, ln in enumerate(self._wrap(desc, self.font_s, r.w - 56)[:2]):
                self._text(ln, self.font_s, (200, 204, 220), topleft=(r.x + 50, r.y + 28 + j * 14))
            rec = self.profile.special.get(k, {})
            if k == "sandbox":
                info = "free practice"
            elif k == "endless":
                info = "Best: wave %d" % self.profile.endless_best
            else:
                info = "won %d / %d" % (rec.get("wins", 0), rec.get("plays", 0))
            self._text(info, self.font_s, (240, 210, 140), topleft=(r.x + 50, r.bottom - 52))
        for b in self._modes_buttons():
            b.draw(self.screen, self.font_sb if b.rect.h < 36 else self.font_m)

    # ================================================================ start
    def _start_mode(self, key):
        self.mode = key
        if key == "endless":
            return self._start_endless()
        if key == "draft":
            return self._start_draft()
        deck = list(self.player_deck)
        if len(deck) != cfg.DECK_SIZE:
            self._open_player_deck("modes")
            self.deck_msg = "Pick 8 cards first!"
            return
        if key == "mirror":
            ai_deck = list(deck)
        elif key == "duo":
            ai_deck = self._duo_pick_decks()
        elif key == "random":
            deck, ai_deck = cards.random_deck(), cards.random_deck()
        else:
            ai_deck = self._resolve_ai_deck()
        self._launch_special(deck, ai_deck)

    def _launch_special(self, deck, ai_deck):
        key = self.mode
        cfg.apply_ai_settings(self.ai_level, 1.0)
        self._arena_surf = None
        self.level_run = None
        alv = profile_data.SPECIAL_AI_LEVEL
        tk = self._towers_kw(alv)
        if key == "double":                                     # ~ x2 tower hp
            for d in tk.values():
                for t in d:
                    d[t] += 7
        specials = self._match_specials(deck, ai_deck)
        if key == "mirror":
            specials["evo_cards"][ENEMY] = list(specials["evo_cards"][PLAYER])
            specials["hero_cards"][ENEMY] = list(specials["hero_cards"][PLAYER])
        self.match = Match(deck, ai_deck,
                           card_levels={PLAYER: self.profile.deck_levels(deck), ENEMY: alv},
                           **tk, **specials)
        m = self.match
        if key == "triple":
            m.elixir_rate = 3.0
        elif key == "sudden":
            m.overtime = True
            m.time_left = 180.0
            m.elixir_rate = 2.0
        elif key == "rage":
            m.always_rage = True
        elif key == "double":
            m.elixir_rate = 2.0
            m.time_left = 300.0
        m.record_events = True
        self._apply_tower_troops(m)
        if key == "mirror":
            m.set_tower_troop(ENEMY, self._tower_troop())
        self.mode_decks = (list(deck), list(ai_deck))
        self.ai = AIController(m, team=ENEMY, level=self.ai_level)
        if key == "duo":
            self._duo_setup(m, deck, specials, alv)
        self._audio = {}
        self.fx.clear()
        self.selected = None
        self.state = "match"
        self.sfx.play("match_start", 0.9, min_gap=0.0)

    # ================================================================ 2v2
    def _duo_pick_decks(self):
        """Three different AI decks: enemy 1 (returned), your teammate and
        enemy 2 (kept in self.duo_decks)."""
        names = list(cards.AI_DECK_PRESETS)
        random.shuffle(names)
        foe, ally, foe2 = names[:3]
        self.duo_names = {ENEMY: foe, ALLY: ally, ENEMY2: foe2}
        self.duo_decks = (list(cards.AI_DECK_PRESETS[ally]), list(cards.AI_DECK_PRESETS[foe2]))
        return list(cards.AI_DECK_PRESETS[foe])

    def _duo_setup(self, m, deck, specials, alv):
        """Seat the teammate and the second enemy. Your teammate's cards are
        your deck's level; it brings as many Evolutions / Heroes as you."""
        ally_deck, foe2_deck = self.duo_decks
        n_e, n_h = len(specials["evo_cards"][PLAYER]), len(specials["hero_cards"][PLAYER])
        ae, ah = self._special_cards(ally_deck, owned=False, n_evo=n_e, n_hero=n_h)
        fe, fh = self._special_cards(foe2_deck, owned=False, n_evo=n_e, n_hero=n_h)
        m.add_seats(ally_deck, foe2_deck, ally_level=self.profile.deck_level(deck),
                    foe_level=alv, evo_cards={ALLY: ae, ENEMY2: fe},
                    hero_cards={ALLY: ah, ENEMY2: fh})
        self._extra = (m, [AIController(m, team=PLAYER, level=self.ai_level, seat=ALLY),
                           AIController(m, team=ENEMY, level=self.ai_level, seat=ENEMY2)])

    def _start_endless(self):
        deck = self.level_deck
        if len(deck) != cfg.DECK_SIZE or levels.banned_in(deck):
            self._open_deck_editor("level", "modes")
            self.deck_msg = "Your Level Deck needs 8 cards (no win conditions)."
            return
        self._arena_surf = None
        ev, he = self._special_cards(deck)
        self.match, self.level_run = levels.new_endless_match(
            deck, self.profile.deck_levels(deck), self._towers_kw()["tower_levels"][PLAYER],
            ev, he, king_level=self.profile.king_level())
        self.match.record_events = True
        self._apply_tower_troops(self.match)
        self.level_key = None
        self.ai = None
        self.selected = None
        self._audio = {}
        self.fx.clear()
        self.state = "match"
        self.sfx.play("match_start", 0.9, min_gap=0.0)

    def _mode_again(self):
        if self.mode == "draft":
            self._start_draft()
        elif self.mode is not None:
            self._start_mode(self.mode)
        else:
            self._open_modes()

    # ================================================================ rewards
    def _mode_rewards(self, w):
        p = self.profile
        k = self.mode
        rec = p.special.setdefault(k, {"wins": 0, "plays": 0})
        rec["plays"] += 1
        if k == "endless":
            n = self.level_run.waves_survived()
            new_best = n > p.endless_best
            p.endless_best = max(p.endless_best, n)
            p.endless_runs += 1
            self._reward("Survived %d waves" % n, profile_data.endless_gold(n))
            for mark in range(5, n + 1, 5):
                if mark > rec.get("best", 0):
                    self._reward("Reached wave %d" % mark, coins=1)
            rec["best"] = max(rec.get("best", 0), n)
            if new_best and n:
                self.last_rewards.append(("New best!", {}))
            return
        win = w == PLAYER
        self._reward("Victory" if win else "Played",
                     profile_data.special_gold(win, self.ai_level, self.match.crowns[PLAYER]))
        if win:
            rec["wins"] += 1
            if rec["wins"] == 1:
                self._reward("First %s win" % MODE_NAMES[k], coins=1)

    # ================================================================ draft
    def _start_draft(self):
        pool = [c.key for c in cards.DEPLOYABLE_CARDS]
        random.shuffle(pool)
        self.draft = {"pool": pool, "mine": [], "ai": [], "pair": None}
        self._draft_next()
        self.state = "draft"

    def _draft_next(self):
        d = self.draft
        if len(d["mine"]) >= cfg.DECK_SIZE:
            self._launch_special(d["mine"], d["ai"])
            return
        champ_mine = any(cards.CARDS[k].is_champion for k in d["mine"])
        pair = []
        while len(pair) < 2 and d["pool"]:
            k = d["pool"].pop()
            if cards.CARDS[k].is_champion and champ_mine:
                continue
            pair.append(k)
        d["pair"] = pair

    def _draft_rects(self):
        w = 170
        return [pygame.Rect(cfg.WINDOW_W // 2 - w - 8 + i * (w + 16), 200, w, 230)
                for i in range(2)]

    def _draft_click(self, pos):
        d = self.draft
        for i, r in enumerate(self._draft_rects()):
            if r.collidepoint(pos) and i < len(d["pair"]):
                pick = d["pair"][i]
                d["mine"].append(pick)
                other = d["pair"][1 - i] if len(d["pair"]) > 1 else None
                if other:
                    d["ai"].append(other)
                self.sfx.play("ui_select", 0.7, min_gap=0.0)
                self._draft_next()
                return
        b = Button((cfg.WINDOW_W // 2 - 70, cfg.WINDOW_H - 52, 140, 40), "Back",
                   lambda: self._open_modes(), "dark")
        b.click(pos)

    def _draw_draft(self):
        d = self.draft
        mouse = pygame.mouse.get_pos()
        self._screen_title("Draft  -  pick %d of 8" % (len(d["mine"]) + 1), 30)
        self._text("You keep the card you click. The AI gets the other one.",
                   self.font_s, (200, 204, 220), center=(cfg.WINDOW_W // 2, 70))
        for i, r in enumerate(self._draft_rects()):
            if i >= len(d["pair"]):
                continue
            c = cards.CARDS[d["pair"][i]]
            hov = r.collidepoint(mouse)
            self._panel(r, border=(250, 222, 110) if hov else (110, 120, 150),
                        top=(70, 80, 110) if hov else (52, 54, 72))
            self.screen.blit(sprites.get_sprite(c.key, 110), (r.centerx - 55, r.y + 12))
            self._elixir_badge(r.x + 16, r.y + 16, c.elixir, r=11)
            self._text(self._fit(c.name, self.font_m, r.w - 10), self.font_m,
                       center=(r.centerx, r.y + 140))
            kind = "Champion" if c.is_champion else c.category.title()
            self._text("%s  -  Lv %d" % (kind, self.profile.level(c.key)), self.font_s,
                       (240, 210, 140), center=(r.centerx, r.y + 164))
            if c.category != "spell":
                self._text("HP %d  dmg %d" % (c.hp, c.damage), self.font_s,
                           (200, 204, 220), center=(r.centerx, r.y + 184))
        for row, (label, deck) in enumerate((("Your picks", d["mine"]),
                                             ("AI picks", d["ai"]))):
            y = 470 + row * 100
            self._text(label, self.font_sb, topleft=(16, y))
            for j, k in enumerate(deck):
                self.screen.blit(sprites.get_sprite(k, 42), (16 + j * 48, y + 22))
        Button((cfg.WINDOW_W // 2 - 70, cfg.WINDOW_H - 52, 140, 40), "Back",
               lambda: None, "dark").draw(self.screen, self.font_m)
