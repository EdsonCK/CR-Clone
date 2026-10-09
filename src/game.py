"""
============================================================================
  GAME.PY  --  Window, screens, rendering, input and the main loop
============================================================================

Screens:
  * MENU  -- Battle / Edit Deck / How To Play / Quit
  * DECK  -- pick your 8 cards
  * MATCH -- the live battle (arena + HUD)
  * RESULT-- victory / defeat / draw

Controls in a match:
  * Click a card in your hand (bottom), then click the arena to deploy it.
  * You can only deploy on your side of the river (until you crack a tower).
  * Right-click / click the card again to cancel.  Esc = leave match.
============================================================================
"""

import json
import os
import math
import random
import pygame

import config as cfg
import cards
import sprites
from engine import (Match, PLAYER, ENEMY, RIVER_TOP, RIVER_BOTTOM,
                    BRIDGE_X, RIVER_CENTER, dist)
from ai import AIController

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECK_FILE = os.path.join(_ROOT, "player_deck.json")
AI_DECK_FILE = os.path.join(_ROOT, "ai_custom_deck.json")
STATS_FILE = os.path.join(_ROOT, "records.json")

# Colors for spell telegraphs & detonations, roughly matching each spell.
SPELL_FX_COLORS = {
    "fireball": (250, 150, 60), "rocket": (240, 90, 60),
    "zap": (250, 235, 90), "lightning": (240, 225, 110),
    "arrows": (230, 230, 230), "freeze": (150, 220, 255),
    "poison": (150, 90, 190), "rage": (220, 90, 220),
    "the_log": (170, 120, 70),
    "goblin_barrel": (150, 110, 70), "barbarian_barrel": (160, 115, 72),
    "snowball": (200, 230, 250), "earthquake": (190, 140, 70),
    "tornado": (190, 195, 205), "graveyard": (150, 90, 190),
}

# Themed projectile visuals, keyed by the SHOOTER's card key -> (kind, color).
# Kinds: arrow fire_arrow bullet pellet fire ice magic dart spear bomb axe
#        boulder zap orb cannonball xbolt
PROJ_STYLES = {
    "archers":        ("arrow", (225, 225, 235)),
    "magic_archer":   ("arrow", (120, 240, 215)),
    "princess":       ("fire_arrow", (255, 170, 60)),
    "princess_tower": ("arrow", (245, 235, 200)),
    "king_tower":     ("cannonball", (75, 70, 80)),
    "musketeer":      ("bullet", (255, 235, 160)),
    "three_musketeers": ("bullet", (255, 235, 160)),
    "flying_machine": ("bullet", (255, 210, 140)),
    "hunter":         ("pellet", (255, 205, 120)),
    "wizard":         ("fire", (255, 150, 50)),
    "baby_dragon":    ("fire", (255, 140, 60)),
    "lava_pup":       ("fire", (255, 150, 70)),
    "ice_wizard":     ("ice", (175, 230, 255)),
    "witch":          ("magic", (205, 95, 245)),
    "dart_goblin":    ("dart", (160, 230, 110)),
    "spear_goblins":  ("spear", (185, 145, 95)),
    "spear_goblin":   ("spear", (185, 145, 95)),
    "bomber":         ("bomb", (75, 75, 85)),
    "bomb_tower":     ("bomb", (75, 75, 85)),
    "mortar":         ("bomb", (60, 60, 70)),
    "executioner":    ("axe", (215, 220, 230)),
    "bowler":         ("boulder", (135, 115, 165)),
    "electro_wizard": ("zap", (150, 230, 255)),
    "electro_dragon": ("zap", (140, 190, 255)),
    "zappies":        ("zap", (255, 240, 140)),
    # (tesla now fires an instant beam via the "chain" effect, no projectile)
    "sparky":         ("orb", (255, 240, 150)),
    "royal_giant":    ("cannonball", (65, 62, 72)),
    "cannon":         ("cannonball", (65, 62, 72)),
    "xbow":           ("xbolt", (235, 225, 205)),
}


STEEL_COL = (225, 228, 236)


def dk_c(c, n=40):
    return tuple(max(0, v - n) for v in c)


def lt_c(c, n=40):
    return tuple(min(255, v + n) for v in c)


def tile_to_px(x, y):
    return (cfg.ARENA_X0 + x * cfg.TILE_SIZE, cfg.ARENA_Y0 + y * cfg.TILE_SIZE)


def px_to_tile(px, py):
    return ((px - cfg.ARENA_X0) / cfg.TILE_SIZE, (py - cfg.ARENA_Y0) / cfg.TILE_SIZE)


class Button:
    def __init__(self, rect, label, cb):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.cb = cb

    def draw(self, surf, font):
        mouse = pygame.mouse.get_pos()
        hover = self.rect.collidepoint(mouse)
        r = self.rect.inflate(6, 4) if hover else self.rect
        # drop shadow
        sh = r.move(0, 3)
        pygame.draw.rect(surf, (15, 18, 26), sh, border_radius=10)
        color = cfg.COLOR_BUTTON_HOVER if hover else cfg.COLOR_BUTTON
        pygame.draw.rect(surf, color, r, border_radius=10)
        # top sheen + border
        sheen = pygame.Rect(r.x + 3, r.y + 3, r.w - 6, r.h // 2 - 3)
        pygame.draw.rect(surf, tuple(min(255, c + 22) for c in color), sheen,
                         border_radius=8)
        pygame.draw.rect(surf, (250, 240, 150) if hover else (20, 24, 32), r,
                         2, border_radius=10)
        txt = font.render(self.label, True, cfg.COLOR_TEXT)
        surf.blit(txt, (r.centerx - txt.get_width() // 2,
                        r.centery - txt.get_height() // 2))

    def click(self, pos):
        if self.rect.collidepoint(pos):
            self.cb()
            return True
        return False


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Clash Clone - Singleplayer")
        self.screen = pygame.display.set_mode((cfg.WINDOW_W, cfg.WINDOW_H))
        self.clock = pygame.time.Clock()
        sprites.ensure_sprites()

        self.font_s = pygame.font.SysFont("arial", 13)
        self.font_m = pygame.font.SysFont("arial", 18, bold=True)
        self.font_l = pygame.font.SysFont("arial", 30, bold=True)
        self.font_xl = pygame.font.SysFont("arial", 44, bold=True)

        self.state = "menu"
        self.running = True

        self.player_deck = self._load_deck()
        self.match = None
        self.ai = None
        self.selected = None       # index into hand while deploying
        self.result_text = ""
        self.deck_msg = ""

        # pre-match setup choices
        self.difficulty = cfg.DEFAULT_DIFFICULTY
        self.ai_deck_choice = "Classic"
        self.ai_custom_deck = self._load_deck(AI_DECK_FILE, cards.DEFAULT_AI_DECK)
        self.deck_scroll = 0        # vertical scroll offset in the deck builder
        self.deck_mode = "player"   # "player" or "ai" - which deck is being edited
        self.deck_return = "menu"   # screen to return to after editing a deck
        self.stats = self._load_stats()   # per-difficulty crown/win records

        self._build_menu_buttons()

        # --- menu ambience: cached gradient + floating card sprites ---
        self.bg_grad = self._make_vgrad(cfg.WINDOW_W, cfg.WINDOW_H,
                                        (24, 28, 44), (44, 36, 62))
        rng = random.Random(7)
        pool = [c.key for c in cards.DEPLOYABLE_CARDS]
        rng.shuffle(pool)
        self.menu_float = []
        for i, key in enumerate(pool[:14]):
            self.menu_float.append({
                "key": key,
                "x": rng.randint(16, cfg.WINDOW_W - 48),
                "y0": rng.randint(0, cfg.WINDOW_H),
                "spd": rng.uniform(12, 30),
                "sway": rng.uniform(0.4, 1.2),
                "ph": rng.uniform(0, 6.28),
                "size": rng.choice((30, 36, 44)),
            })

    @staticmethod
    def _make_vgrad(w, h, c1, c2):
        surf = pygame.Surface((w, h))
        for y in range(h):
            t = y / max(1, h - 1)
            col = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
            pygame.draw.line(surf, col, (0, y), (w, y))
        return surf

    @staticmethod
    def _now():
        return pygame.time.get_ticks() / 1000.0

    # ----------------------------------------------------------------- decks
    def _load_deck(self, path=DECK_FILE, default=None):
        default = default if default is not None else cards.DEFAULT_PLAYER_DECK
        if os.path.exists(path):
            try:
                with open(path) as f:
                    d = json.load(f)
                d = [k for k in d if k in cards.CARDS and cards.CARDS[k].deployable]
                if len(d) == cfg.DECK_SIZE:
                    return d
            except Exception:
                pass
        return list(default)

    def _save_deck(self):
        path = AI_DECK_FILE if self.deck_mode == "ai" else DECK_FILE
        try:
            with open(path, "w") as f:
                json.dump(self._active_deck(), f)
        except Exception:
            pass

    # ---- records / stats ----
    def _blank_stats(self):
        return {d: {"wins": 0, "losses": 0, "draws": 0, "cf": 0, "ca": 0}
                for d in cfg.DIFFICULTIES}

    def _load_stats(self):
        s = self._blank_stats()
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE) as f:
                    saved = json.load(f)
                for d, rec in saved.items():
                    if d in s and isinstance(rec, dict):
                        s[d].update({k: int(rec.get(k, 0)) for k in s[d]})
            except Exception:
                pass
        return s

    def _save_stats(self):
        try:
            with open(STATS_FILE, "w") as f:
                json.dump(self.stats, f, indent=1)
        except Exception:
            pass

    def _record_result(self):
        m, d = self.match, self.difficulty
        rec = self.stats.setdefault(d, {"wins": 0, "losses": 0, "draws": 0,
                                        "cf": 0, "ca": 0})
        rec["cf"] += m.crowns[PLAYER]
        rec["ca"] += m.crowns[ENEMY]
        if m.winner == PLAYER:
            rec["wins"] += 1
        elif m.winner == ENEMY:
            rec["losses"] += 1
        else:
            rec["draws"] += 1
        self._save_stats()

    # which deck the builder is currently editing
    def _active_deck(self):
        return self.ai_custom_deck if self.deck_mode == "ai" else self.player_deck

    def _set_active_deck(self, d):
        if self.deck_mode == "ai":
            self.ai_custom_deck = d
        else:
            self.player_deck = d

    # -------------------------------------------------------------- menu
    def _build_menu_buttons(self):
        cx = cfg.WINDOW_W // 2
        w, h = 220, 42
        y0 = 196
        gap = 50
        labels = [
            ("Battle", self._open_prematch),
            ("Edit Deck", self._open_player_deck),
            ("AI Deck", lambda: self._goto("aideck")),
            ("Records", lambda: self._goto("records")),
            ("How To Play", lambda: self._goto("help")),
            ("Quit", self._quit),
        ]
        self.menu_buttons = [
            Button((cx - w // 2, y0 + i * gap, w, h), lbl, cb)
            for i, (lbl, cb) in enumerate(labels)
        ]

    def _open_player_deck(self):
        self.deck_mode = "player"
        self.deck_return = "menu"
        self.deck_scroll = 0
        self.deck_msg = ""
        self.state = "deck"

    def _open_ai_custom_deck(self):
        self.deck_mode = "ai"
        self.deck_return = "aideck"
        self.deck_scroll = 0
        self.deck_msg = ""
        self.state = "deck"

    def _goto(self, state):
        self.state = state

    def _quit(self):
        self.running = False

    def _open_prematch(self):
        if len(self.player_deck) != cfg.DECK_SIZE:
            self.deck_msg = "Pick 8 cards first!"
            self.state = "deck"
            return
        self.state = "prematch"

    def _begin_battle(self):
        if len(self.player_deck) != cfg.DECK_SIZE:
            self._open_player_deck()
            return
        cfg.apply_difficulty(self.difficulty)
        self.match = Match(self.player_deck, self._resolve_ai_deck())
        self.ai = AIController(self.match)
        self.selected = None
        self.state = "match"

    def _resolve_ai_deck(self):
        if self.ai_deck_choice == "Random":
            return cards.random_deck()
        if self.ai_deck_choice == "Custom":
            if len(self.ai_custom_deck) == cfg.DECK_SIZE:
                return list(self.ai_custom_deck)
            return list(cards.DEFAULT_AI_DECK)
        return cards.AI_DECK_PRESETS.get(self.ai_deck_choice, cards.DEFAULT_AI_DECK)

    def _ai_deck_preview_cards(self):
        """The 8 cards the current AI-deck choice will use (for previews)."""
        if self.ai_deck_choice == "Random":
            return None
        if self.ai_deck_choice == "Custom":
            return self.ai_custom_deck
        return cards.AI_DECK_PRESETS.get(self.ai_deck_choice, cards.DEFAULT_AI_DECK)

    # test/back-compat helper used by tooling
    def _start_match(self):
        self._begin_battle()

    # ================================================================= LOOP
    def run(self):
        while self.running:
            dt = self.clock.tick(cfg.FPS) / 1000.0
            dt = min(dt, 0.05)
            self._events(dt)
            if self.state == "match" and self.match and not self.match.finished:
                self.match.update(dt)
                self.ai.update(dt)
                if self.match.finished:
                    self._on_match_end()
            self._draw()
            pygame.display.flip()
        pygame.quit()

    def _on_match_end(self):
        w = self.match.winner
        if w == PLAYER:
            self.result_text = "VICTORY!"
        elif w == ENEMY:
            self.result_text = "DEFEAT"
        else:
            self.result_text = "DRAW"
        self._record_result()
        self.state = "result"

    # ================================================================= EVENTS
    def _events(self, dt):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if self.state == "match":
                        self.state = "menu"
                    elif self.state == "deck":
                        self.state = self.deck_return
                    elif self.state in ("help", "result", "prematch", "aideck",
                                        "records"):
                        self.state = "menu"
            elif e.type == pygame.MOUSEWHEEL:
                if self.state == "deck":
                    self.deck_scroll = max(0, min(self._deck_max_scroll(),
                                                  self.deck_scroll - e.y * 40))
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if self.state == "menu":
                    for b in self.menu_buttons:
                        b.click(e.pos)
                elif self.state == "prematch":
                    self._prematch_click(e.pos)
                elif self.state == "aideck":
                    self._aideck_click(e.pos)
                elif self.state == "deck":
                    self._deck_click(e.pos)
                elif self.state == "help":
                    self.state = "menu"
                elif self.state == "records":
                    self.state = "menu"
                elif self.state == "result":
                    self.state = "menu"
                elif self.state == "match":
                    self._match_click(e.pos, e.button)

    # ================================================================= MATCH INPUT
    NEXT_BOX_W = 52   # reserved width for the "Next:" preview on the right

    def _hand_slot_rects(self):
        n = cfg.HAND_SIZE
        slot_w = 62
        gap = 8
        total = n * slot_w + (n - 1) * gap
        # center the hand in the space left of the Next box, with real margins
        x0 = (cfg.WINDOW_W - self.NEXT_BOX_W - 12 - total) // 2
        x0 = max(10, x0)
        y0 = cfg.ARENA_Y0 + cfg.ARENA_PX_H + 26
        return [pygame.Rect(x0 + i * (slot_w + gap), y0, slot_w, 84)
                for i in range(n)]

    def _ability_btn_rect(self):
        # sits in the arena's bottom-left corner, just above the card hand
        r = 24
        return pygame.Rect(cfg.ARENA_X0 + 8,
                           cfg.ARENA_Y0 + cfg.ARENA_PX_H - 2 * r - 8, 2 * r, 2 * r)

    def _match_click(self, pos, button):
        if button == 3:
            self.selected = None
            return
        # champion ability button (bottom-left)
        champ, ready, cost = self.match.ability_status(PLAYER)
        if champ is not None and self._ability_btn_rect().collidepoint(pos):
            self.match.activate_ability(PLAYER)
            return
        rects = self._hand_slot_rects()
        for i, r in enumerate(rects):
            if r.collidepoint(pos):
                self.selected = None if self.selected == i else i
                return
        # click on arena to deploy
        if self.selected is not None:
            tx, ty = px_to_tile(*pos)
            if self.match.play_card(PLAYER, self.selected, tx, ty):
                self.selected = None

    # ================================================================= PREMATCH
    def _prematch_diff_rects(self):
        names = ["Easy", "Medium", "Hard", "Master", "Insane"]
        w = (cfg.WINDOW_W - 48) // 3
        rects = []
        for i, n in enumerate(names):
            r, c = divmod(i, 3)
            rects.append((pygame.Rect(16 + c * (w + 8), 96 + r * 48, w, 42), n))
        return rects

    def _prematch_buttons(self):
        cx = cfg.WINDOW_W // 2
        bw = (cfg.WINDOW_W - 16 * 2 - 12) // 2
        return [
            Button((16, cfg.WINDOW_H - 116, bw, 46), "Change AI Deck",
                   lambda: self._goto("aideck")),
            Button((cfg.WINDOW_W - 16 - bw, cfg.WINDOW_H - 116, bw, 46),
                   "Start Battle", self._begin_battle),
            Button((cx - 60, cfg.WINDOW_H - 58, 120, 34), "Back",
                   lambda: self._goto("menu")),
        ]

    def _prematch_click(self, pos):
        for r, name in self._prematch_diff_rects():
            if r.collidepoint(pos):
                self.difficulty = name
                return
        for b in self._prematch_buttons():
            if b.click(pos):
                return

    # ================================================================= AI DECK
    def _aideck_options(self):
        return list(cards.AI_DECK_PRESETS.keys()) + ["Random", "Custom"]

    def _aideck_preset_rects(self):
        opts = self._aideck_options()
        cols = 2
        w = (cfg.WINDOW_W - 32 - 8) // cols
        h, gap_y, top = 30, 6, 56
        rects = []
        for i, name in enumerate(opts):
            r, c = divmod(i, cols)
            rects.append((pygame.Rect(16 + c * (w + 8), top + r * (h + gap_y), w, h), name))
        return rects

    def _aideck_buttons(self):
        cx = cfg.WINDOW_W // 2
        return [
            Button((cx - 115, cfg.WINDOW_H - 104, 230, 40),
                   "Build / Edit Custom Deck", self._open_ai_custom_deck),
            Button((cx - 60, cfg.WINDOW_H - 52, 120, 34), "Back",
                   lambda: self._goto("menu")),
        ]

    def _aideck_click(self, pos):
        for r, name in self._aideck_preset_rects():
            if r.collidepoint(pos):
                self.ai_deck_choice = name
                return
        for b in self._aideck_buttons():
            if b.click(pos):
                return

    def _draw_aideck(self):
        cx = cfg.WINDOW_W // 2
        mouse = pygame.mouse.get_pos()
        self._text("AI Deck", self.font_l, (240, 220, 120), center=(cx, 26))
        rects = self._aideck_preset_rects()
        for r, name in rects:
            sel = (self.ai_deck_choice == name)
            bg = (70, 100, 130) if sel else (44, 50, 62)
            if r.collidepoint(mouse):
                bg = tuple(min(255, c + 18) for c in bg)
            pygame.draw.rect(self.screen, bg, r, border_radius=6)
            if sel:
                pygame.draw.rect(self.screen, (250, 240, 140), r, 2, border_radius=6)
            self._text(name, self.font_s, cfg.COLOR_TEXT, center=r.center)

        py = rects[-1][0].bottom + 16
        self._text("Selected:  " + self.ai_deck_choice, self.font_m,
                   (150, 200, 240), topleft=(16, py))
        py += 28
        preview = self._ai_deck_preview_cards()
        if preview is None:
            self._text("A different random 8-card deck each match.",
                       self.font_s, cfg.COLOR_TEXT, topleft=(16, py))
        elif self.ai_deck_choice == "Custom" and len(preview) != cfg.DECK_SIZE:
            self._text("Custom deck needs 8 cards - build it below.",
                       self.font_s, (240, 180, 120), topleft=(16, py))
        else:
            sz = 38
            gap = max(2, min(12, (cfg.WINDOW_W - 32 - sz * len(preview)) //
                             max(1, len(preview) - 1)))
            x = 16
            for k in preview:
                self.screen.blit(sprites.get_sprite(k, sz), (x, py))
                x += sz + gap
            avg = sum(cards.CARDS[k].elixir for k in preview) / len(preview)
            self._text("avg elixir %.1f" % avg, self.font_s, (190, 190, 190),
                       topleft=(16, py + sz + 6))
        for b in self._aideck_buttons():
            b.draw(self.screen, self.font_s)

    # ================================================================= DECK INPUT
    DECK_COLS = 6
    DECK_CELL_H = 60

    def _deck_viewport(self):
        return 52, cfg.WINDOW_H - 112   # (top, bottom) y of the scrollable grid

    def _deck_max_scroll(self):
        rows = (len(cards.DEPLOYABLE_CARDS) + self.DECK_COLS - 1) // self.DECK_COLS
        top, bottom = self._deck_viewport()
        return max(0, rows * self.DECK_CELL_H - (bottom - top) + 6)

    def _deck_grid(self):
        margin = 12
        cell_w = (cfg.WINDOW_W - margin * 2) // self.DECK_COLS
        top, _ = self._deck_viewport()
        rects = []
        for idx, card in enumerate(cards.DEPLOYABLE_CARDS):
            r = idx // self.DECK_COLS
            c = idx % self.DECK_COLS
            y = top + r * self.DECK_CELL_H - self.deck_scroll
            rects.append((pygame.Rect(margin + c * cell_w, y,
                                      cell_w - 4, self.DECK_CELL_H - 4), card))
        return rects

    def _deck_slot_rects(self):
        n = cfg.DECK_SIZE
        slot_w = 40
        gap = 4
        total = n * slot_w + (n - 1) * gap
        x0 = (cfg.WINDOW_W - total) // 2
        y0 = cfg.WINDOW_H - 96
        return [pygame.Rect(x0 + i * (slot_w + gap), y0, slot_w, 52) for i in range(n)]

    def _deck_buttons(self):
        y = cfg.WINDOW_H - 36
        return [
            Button((12, y, 110, 28), "Save & Back", self._deck_save_back),
            Button((132, y, 80, 28), "Clear", self._deck_clear),
            Button((222, y, 90, 28), "Default", self._deck_default),
        ]

    def _deck_save_back(self):
        if len(self._active_deck()) == cfg.DECK_SIZE:
            self._save_deck()
            self.deck_msg = ""
            if self.deck_mode == "ai":
                self.ai_deck_choice = "Custom"   # auto-select the deck you built
            self.state = self.deck_return
        else:
            self.deck_msg = "Deck must have exactly 8 cards."

    def _deck_clear(self):
        self._set_active_deck([])

    def _deck_default(self):
        d = cards.DEFAULT_AI_DECK if self.deck_mode == "ai" else cards.DEFAULT_PLAYER_DECK
        self._set_active_deck(list(d))

    def _deck_click(self, pos):
        deck = self._active_deck()
        for b in self._deck_buttons():
            if b.click(pos):
                return
        # remove from deck slots
        for i, r in enumerate(self._deck_slot_rects()):
            if r.collidepoint(pos) and i < len(deck):
                deck.pop(i)
                return
        # add/remove from grid (only within the scrollable viewport)
        top, bottom = self._deck_viewport()
        if top <= pos[1] <= bottom:
            for r, card in self._deck_grid():
                if r.collidepoint(pos):
                    if card.key in deck:
                        deck.remove(card.key)
                    elif len(deck) < cfg.DECK_SIZE:
                        # only one champion allowed per deck
                        if card.is_champion and any(
                                cards.CARDS[k].is_champion for k in deck):
                            self.deck_msg = "Only 1 Champion per deck."
                            return
                        deck.append(card.key)
                        self.deck_msg = ""
                    return

    # ================================================================= DRAW
    def _draw(self):
        self.screen.blit(self.bg_grad, (0, 0))
        if self.state == "menu":
            self._draw_menu()
        elif self.state == "prematch":
            self._draw_prematch()
        elif self.state == "aideck":
            self._draw_aideck()
        elif self.state == "deck":
            self._draw_deck()
        elif self.state == "help":
            self._draw_help()
        elif self.state == "records":
            self._draw_records()
        elif self.state in ("match", "result"):
            self._draw_match()
            if self.state == "result":
                self._draw_result()

    def _text(self, s, font, color, center=None, topleft=None):
        t = font.render(s, True, color)
        if center:
            self.screen.blit(t, (center[0] - t.get_width() // 2,
                                 center[1] - t.get_height() // 2))
        else:
            self.screen.blit(t, topleft)
        return t

    def _draw_menu(self):
        cx = cfg.WINDOW_W // 2
        t = self._now()
        self.screen.blit(self.bg_grad, (0, 0))
        # floating card sprites drifting upward with a gentle sway
        for fc in self.menu_float:
            y = (fc["y0"] - t * fc["spd"]) % (cfg.WINDOW_H + 60) - 50
            x = fc["x"] + math.sin(t * fc["sway"] + fc["ph"]) * 12
            spr = sprites.get_sprite(fc["key"], fc["size"]).copy()
            spr.set_alpha(70)
            self.screen.blit(spr, (x, y))
        # bobbing title with drop shadow + underline
        bob = int(math.sin(t * 2.0) * 4)
        self._text("CLASH CLONE", self.font_xl, (25, 22, 40),
                   center=(cx + 3, 118 + bob + 3))
        self._text("CLASH CLONE", self.font_xl, (250, 214, 100),
                   center=(cx, 118 + bob))
        pygame.draw.line(self.screen, (250, 214, 100),
                         (cx - 120, 148 + bob), (cx + 120, 148 + bob), 2)
        self._text("Singleplayer  v" + cfg.GAME_VERSION, self.font_m,
                   (205, 210, 225), center=(cx, 170 + bob))
        for b in self.menu_buttons:
            b.draw(self.screen, self.font_m)
        # your current deck, shown as sprites in a framed strip
        if self.player_deck:
            n = len(self.player_deck)
            sz, gap = 34, 6
            total = n * sz + (n - 1) * gap
            x0 = cx - total // 2
            strip = pygame.Rect(x0 - 10, cfg.WINDOW_H - 74, total + 20, 54)
            pygame.draw.rect(self.screen, (22, 26, 38), strip, border_radius=10)
            pygame.draw.rect(self.screen, (70, 80, 105), strip, 1, border_radius=10)
            self._text("Your Deck", self.font_s, (170, 178, 195),
                       center=(cx, cfg.WINDOW_H - 84))
            for i, k in enumerate(self.player_deck):
                self.screen.blit(sprites.get_sprite(k, sz),
                                 (x0 + i * (sz + gap), cfg.WINDOW_H - 64))

    def _draw_prematch(self):
        cx = cfg.WINDOW_W // 2
        mouse = pygame.mouse.get_pos()
        self._text("Battle Setup", self.font_l, (240, 220, 120), center=(cx, 28))

        # difficulty
        self._text("Difficulty", self.font_m, cfg.COLOR_TEXT, topleft=(16, 68))
        for r, name in self._prematch_diff_rects():
            sel = (self.difficulty == name)
            bg = (70, 120, 90) if sel else (44, 50, 62)
            if r.collidepoint(mouse):
                bg = tuple(min(255, c + 18) for c in bg)
            pygame.draw.rect(self.screen, bg, r, border_radius=8)
            if sel:
                pygame.draw.rect(self.screen, (250, 240, 140), r, 3, border_radius=8)
            self._text(name, self.font_m, cfg.COLOR_TEXT, center=r.center)
        self._text(cfg.DIFFICULTY_DESC.get(self.difficulty, ""), self.font_s,
                   (190, 190, 190), center=(cx, 200))

        # AI deck (chosen on the AI Deck screen; shown read-only here)
        self._text("AI Deck:  " + self.ai_deck_choice, self.font_m,
                   (150, 200, 240), topleft=(16, 226))
        py = 274
        preview = self._ai_deck_preview_cards()
        if preview is None:
            self._text("A different random 8-card deck each match.",
                       self.font_s, cfg.COLOR_TEXT, topleft=(16, py))
        else:
            sz = 38
            gap = max(2, min(12, (cfg.WINDOW_W - 32 - sz * len(preview)) //
                             max(1, len(preview) - 1)))
            x = 16
            for k in preview:
                self.screen.blit(sprites.get_sprite(k, sz), (x, py))
                x += sz + gap
            avg = sum(cards.CARDS[k].elixir for k in preview) / len(preview)
            self._text("avg elixir %.1f" % avg, self.font_s, (190, 190, 190),
                       topleft=(16, py + sz + 6))

        for b in self._prematch_buttons():
            b.draw(self.screen, self.font_m)

    def _draw_records(self):
        cx = cfg.WINDOW_W // 2
        self._text("Records", self.font_l, (240, 220, 120), center=(cx, 30))
        self._text("crowns won vs lost, per AI level", self.font_s,
                   (170, 178, 195), center=(cx, 54))
        order = ["Easy", "Medium", "Hard", "Master", "Insane"]
        diff_col = {"Easy": (110, 200, 110), "Medium": (150, 200, 240),
                    "Hard": (240, 190, 110), "Master": (230, 140, 220),
                    "Insane": (240, 110, 110)}
        y = 80
        tot_w = tot_l = tot_cf = tot_ca = 0
        for d in order:
            rec = self.stats.get(d, {})
            w, l, dr = rec.get("wins", 0), rec.get("losses", 0), rec.get("draws", 0)
            cf, ca = rec.get("cf", 0), rec.get("ca", 0)
            tot_w += w; tot_l += l; tot_cf += cf; tot_ca += ca
            games = w + l + dr
            panel = pygame.Rect(14, y, cfg.WINDOW_W - 28, 78)
            pygame.draw.rect(self.screen, (34, 38, 52), panel, border_radius=8)
            pygame.draw.rect(self.screen, diff_col[d], panel, 1, border_radius=8)
            self._text(d, self.font_m, diff_col[d], topleft=(24, y + 8))
            wr = (w / games * 100) if games else 0
            self._text("%d-%d-%d   %.0f%% win" % (w, l, dr, wr), self.font_s,
                       cfg.COLOR_TEXT, topleft=(24, y + 30))
            # crown tally bar (won green vs lost red)
            bx, by, bw = 24, y + 54, cfg.WINDOW_W - 28 - 20
            tot = max(cf + ca, 1)
            gw = int(bw * cf / tot)
            pygame.draw.rect(self.screen, (70, 40, 44), (bx, by, bw, 12), border_radius=6)
            if gw > 0:
                pygame.draw.rect(self.screen, (90, 200, 110), (bx, by, gw, 12),
                                 border_radius=6)
            self._text("%d" % cf, self.font_s, (150, 230, 160),
                       topleft=(bx + 2, by - 1))
            self._text("%d" % ca, self.font_s, (240, 150, 150),
                       topleft=(bx + bw - 18, by - 1))
            y += 84
        self._text("Total crowns  won %d  -  lost %d   (W-L %d-%d)"
                   % (tot_cf, tot_ca, tot_w, tot_l), self.font_s,
                   (220, 220, 160), center=(cx, y + 6))
        self._text("Click / Esc to return", self.font_s, (170, 170, 170),
                   center=(cx, cfg.WINDOW_H - 16))

    def _draw_help(self):
        cx = cfg.WINDOW_W // 2
        self._text("How To Play", self.font_l, (240, 220, 120), center=(cx, 40))
        lines = [
            "Goal: destroy more enemy towers than the AI.",
            "Destroy the King Tower for an instant win.",
            "",
            "Click a card in your hand, then click your",
            "side of the arena to deploy it.",
            "Right-click cancels the selected card.",
            "",
            "Elixir refills over time (max 10). It doubles",
            "in the last minute and triples in overtime.",
            "",
            "The AI gets an elixir advantage on purpose -",
            "tune it in config.py (AI_* settings).",
            "",
            "Click anywhere / Esc to return to the menu.",
        ]
        y = 90
        for ln in lines:
            self._text(ln, self.font_s, cfg.COLOR_TEXT, center=(cx, y))
            y += 22

    # --------------------------------------------------------- deck screen
    def _draw_deck(self):
        cx = cfg.WINDOW_W // 2
        deck = self._active_deck()
        title = "Edit AI Deck" if self.deck_mode == "ai" else "Edit Your Deck"
        self._text("%s  (%d/8)" % (title, len(deck)), self.font_l,
                   (240, 220, 120), center=(cx, 22))
        self._text("%d cards available" % len(cards.DEPLOYABLE_CARDS),
                   self.font_s, (170, 178, 195), center=(cx, 42))
        mouse = pygame.mouse.get_pos()
        top, bottom = self._deck_viewport()
        self.screen.set_clip(pygame.Rect(0, top, cfg.WINDOW_W, bottom - top))
        for r, card in self._deck_grid():
            if r.bottom < top or r.top > bottom:
                continue   # off-screen; skip
            in_deck = card.key in deck
            bg = (70, 110, 80) if in_deck else (44, 50, 62)
            if r.collidepoint(mouse):
                bg = tuple(min(255, c + 20) for c in bg)
            if card.is_champion:   # gold-tinted cell + border for champions
                bg = (120, 100, 55) if in_deck else (74, 64, 40)
            pygame.draw.rect(self.screen, bg, r, border_radius=6)
            if card.is_champion:
                pygame.draw.rect(self.screen, (245, 205, 85), r, 1, border_radius=6)
            spr = sprites.get_sprite(card.key, 30)
            self.screen.blit(spr, (r.x + 4, r.y + 4))
            self._text(str(card.elixir), self.font_m, cfg.COLOR_ELIXIR,
                       topleft=(r.right - 14, r.y + 2))
            name = card.name if len(card.name) <= 12 else card.name[:11] + "."
            self._text(name, self.font_s, cfg.COLOR_TEXT, topleft=(r.x + 2, r.bottom - 16))
        self.screen.set_clip(None)
        # scrollbar
        max_scroll = self._deck_max_scroll()
        if max_scroll > 0:
            track_h = bottom - top
            frac = track_h / (track_h + max_scroll)
            bar_h = max(24, int(track_h * frac))
            bar_y = top + int((track_h - bar_h) * self.deck_scroll / max_scroll)
            pygame.draw.rect(self.screen, (90, 100, 120),
                             (cfg.WINDOW_W - 6, bar_y, 4, bar_h), border_radius=2)
        # deck slots
        for i, r in enumerate(self._deck_slot_rects()):
            pygame.draw.rect(self.screen, (30, 34, 44), r, border_radius=6)
            pygame.draw.rect(self.screen, (80, 90, 110), r, 1, border_radius=6)
            if i < len(deck):
                spr = sprites.get_sprite(deck[i], 34)
                self.screen.blit(spr, (r.x + 3, r.y + 3))
        avg = (sum(cards.CARDS[k].elixir for k in deck) / len(deck) if deck else 0)
        self._text("Avg elixir: %.1f" % avg, self.font_s, cfg.COLOR_TEXT,
                   topleft=(cfg.WINDOW_W - 100, cfg.WINDOW_H - 110))
        if self.deck_msg:
            self._text(self.deck_msg, self.font_s, (240, 140, 140),
                       topleft=(16, cfg.WINDOW_H - 110))
        for b in self._deck_buttons():
            b.draw(self.screen, self.font_s)

    # --------------------------------------------------------- match screen
    def _draw_match(self):
        self._draw_arena()
        m = self.match
        for e in m.entities:
            self._draw_entity(e)
        for fx in m.effects:
            self._draw_effect(fx)
        self._draw_beams()
        for p in m.projectiles:
            self._draw_projectile(p)
        self._draw_placement_preview()
        self._draw_topbar()
        self._draw_hud()

    def _draw_arena(self):
        t = self._now()
        ts = cfg.TILE_SIZE
        # grass checker with a slightly warmer tint on your half
        for r in range(cfg.GRID_ROWS):
            for c in range(cfg.GRID_COLS):
                col = cfg.COLOR_ARENA if (r + c) % 2 == 0 else cfg.COLOR_ARENA_ALT
                if r > RIVER_BOTTOM:                    # your side: touch brighter
                    col = tuple(min(255, v + 6) for v in col)
                x, y = tile_to_px(c, r)
                pygame.draw.rect(self.screen, col, (x, y, ts + 1, ts + 1))
        # mowed lane stripes toward each bridge
        lane = pygame.Surface((int(1.8 * ts), cfg.ARENA_PX_H), pygame.SRCALPHA)
        lane.fill((255, 255, 255, 10))
        for bx in BRIDGE_X:
            lx, _ = tile_to_px(bx - 0.9, 0)
            self.screen.blit(lane, (lx, cfg.ARENA_Y0))
        # river: deep-to-light gradient bands + drifting ripples
        rx, ry = tile_to_px(0, RIVER_TOP)
        rh = (RIVER_BOTTOM - RIVER_TOP) * ts
        pygame.draw.rect(self.screen, dk_c(cfg.COLOR_RIVER, 25), (rx, ry, cfg.ARENA_PX_W, rh))
        pygame.draw.rect(self.screen, cfg.COLOR_RIVER,
                         (rx, ry + 4, cfg.ARENA_PX_W, rh - 8))
        self.screen.set_clip(pygame.Rect(rx, ry, cfg.ARENA_PX_W, rh))
        for i in range(7):
            wx = (t * 26 + i * 67) % (cfg.ARENA_PX_W + 40) - 20
            wy = ry + 6 + (i % 3) * (rh - 14) // 2
            pygame.draw.ellipse(self.screen, lt_c(cfg.COLOR_RIVER, 45),
                                (rx + wx, wy, 22, 4))
        self.screen.set_clip(None)
        # banks
        pygame.draw.line(self.screen, lt_c(cfg.COLOR_ARENA, 30), (rx, ry),
                         (rx + cfg.ARENA_PX_W, ry), 2)
        pygame.draw.line(self.screen, lt_c(cfg.COLOR_ARENA, 30), (rx, ry + rh),
                         (rx + cfg.ARENA_PX_W, ry + rh), 2)
        # bridges: wooden planks with rails
        for bx in BRIDGE_X:
            bxp, byp = tile_to_px(bx - 0.9, RIVER_TOP)
            bw = 1.8 * ts
            pygame.draw.rect(self.screen, cfg.COLOR_BRIDGE, (bxp, byp - 2, bw, rh + 4))
            for i in range(1, 4):
                pygame.draw.line(self.screen, dk_c(cfg.COLOR_BRIDGE, 35),
                                 (bxp, byp - 2 + i * (rh + 4) / 4),
                                 (bxp + bw, byp - 2 + i * (rh + 4) / 4), 2)
            pygame.draw.rect(self.screen, dk_c(cfg.COLOR_BRIDGE, 55),
                             (bxp, byp - 3, bw, 3))
            pygame.draw.rect(self.screen, dk_c(cfg.COLOR_BRIDGE, 55),
                             (bxp, byp + rh, bw, 3))
        # stone pads under towers
        for tw in self.match.towers.values():
            if not tw.alive:
                continue
            px, py = tile_to_px(tw.x, tw.y)
            rad = int((2.1 if tw.is_king else 1.8) * ts)
            pygame.draw.circle(self.screen, (150, 148, 138), (int(px), int(py)), rad)
            pygame.draw.circle(self.screen, (120, 118, 110), (int(px), int(py)), rad, 2)
        # arena frame
        pygame.draw.rect(self.screen, (52, 44, 38),
                         (cfg.ARENA_X0 - 4, cfg.ARENA_Y0 - 4,
                          cfg.ARENA_PX_W + 8, cfg.ARENA_PX_H + 8), 4, border_radius=6)
        pygame.draw.rect(self.screen, (20, 24, 32),
                         (cfg.ARENA_X0, cfg.ARENA_Y0, cfg.ARENA_PX_W, cfg.ARENA_PX_H), 2)
        if cfg.SHOW_TILE_GRID:
            for c in range(cfg.GRID_COLS + 1):
                x, y = tile_to_px(c, 0)
                pygame.draw.line(self.screen, (0, 0, 0), (x, cfg.ARENA_Y0),
                                 (x, cfg.ARENA_Y0 + cfg.ARENA_PX_H))

    def _team_color(self, team):
        return cfg.COLOR_TEAM_PLAYER if team == PLAYER else cfg.COLOR_TEAM_ENEMY

    def _draw_entity(self, e):
        px, py = tile_to_px(e.x, e.y)
        if e.is_tower:
            self._draw_tower(e, px, py)
            return
        base = (2.6 if e.is_building else 1.5) * cfg.TILE_SIZE
        size = int(base * sprites.render_scale(e.key))
        cloaked = e.invis_timer > 0
        # team ring (gold for champions)
        ring = (245, 205, 85) if e.card.is_champion else self._team_color(e.team)
        pygame.draw.circle(self.screen, ring, (int(px), int(py)), size // 2 + 2, 3)
        spr = sprites.get_sprite(sprites.unit_sprite_key(e.key), size)
        if cloaked or e.immune_timer > 0:
            spr = spr.copy()
            spr.set_alpha(110 if cloaked else 200)
        self.screen.blit(spr, (px - size // 2, py - size // 2))
        if e.immune_timer > 0:   # shield shimmer
            pygame.draw.circle(self.screen, (180, 230, 255),
                               (int(px), int(py)), size // 2 + 4, 2)
        if e.card.is_champion:    # little gold crown above
            cyy = py - size // 2 - 6
            pygame.draw.polygon(self.screen, (245, 205, 85),
                                [(px - 6, cyy + 3), (px - 6, cyy - 2), (px - 3, cyy + 1),
                                 (px, cyy - 4), (px + 3, cyy + 1), (px + 6, cyy - 2),
                                 (px + 6, cyy + 3)])
        self._draw_hp_bar(e, px, py - size // 2 - 5, size)
        # status tint markers
        if e.freeze_timer > 0:
            pygame.draw.circle(self.screen, (150, 220, 255), (int(px), int(py)), size // 2 + 2, 2)
        elif e.stun_timer > 0:
            pygame.draw.circle(self.screen, (255, 240, 120), (int(px), int(py)), size // 2 + 2, 2)

    def _draw_tower(self, e, px, py):
        size = int(3.2 * cfg.TILE_SIZE) if e.is_king else int(2.8 * cfg.TILE_SIZE)
        col = self._team_color(e.team)
        dark = dk_c(col, 60)
        stone = (172, 168, 158)
        stone_dk = (128, 124, 116)
        r = pygame.Rect(px - size // 2, py - size // 2, size, size)
        # stone body with brick lines
        pygame.draw.rect(self.screen, stone, r, border_radius=5)
        pygame.draw.rect(self.screen, stone_dk, r, 3, border_radius=5)
        for i in (1, 2):
            yy = r.y + i * size // 3
            pygame.draw.line(self.screen, stone_dk, (r.x + 3, yy), (r.right - 3, yy), 1)
        pygame.draw.line(self.screen, stone_dk, (r.centerx, r.y + 3),
                         (r.centerx, r.y + size // 3), 1)
        # team-colored roof band + battlements
        band = pygame.Rect(r.x, r.y, size, size // 4)
        pygame.draw.rect(self.screen, col, band, border_radius=5)
        pygame.draw.rect(self.screen, dark, band, 2, border_radius=5)
        bw = size // 5
        for i in range(3):
            pygame.draw.rect(self.screen, col, (r.x + i * 2 * bw, r.y - bw // 2, bw, bw))
            pygame.draw.rect(self.screen, dark, (r.x + i * 2 * bw, r.y - bw // 2, bw, bw), 1)
        # flag
        fx = r.centerx
        pygame.draw.line(self.screen, (70, 60, 50), (fx, r.y - bw // 2),
                         (fx, r.y - bw // 2 - 10), 2)
        pygame.draw.polygon(self.screen, col, [(fx, r.y - bw // 2 - 10),
                                               (fx + 9, r.y - bw // 2 - 7),
                                               (fx, r.y - bw // 2 - 4)])
        if e.is_king:
            # gold crown emblem
            cy0 = r.centery + 2
            pts = [(px - 7, cy0 + 4), (px - 7, cy0 - 2), (px - 3, cy0 + 1),
                   (px, cy0 - 4), (px + 3, cy0 + 1), (px + 7, cy0 - 2),
                   (px + 7, cy0 + 4)]
            pygame.draw.polygon(self.screen, (245, 205, 85), pts)
            pygame.draw.polygon(self.screen, (170, 135, 40), pts, 1)
            if not e.active:
                self._text("Zzz", self.font_s, (240, 240, 245),
                           center=(px, r.y + size // 4 + 2))
        self._draw_hp_bar(e, px, r.y - 14, size + 6)

    def _draw_hp_bar(self, e, px, top, width):
        if e.hp >= e.max_hp and e.shield <= 0:
            frac = 1.0
        frac = max(0.0, e.hp / e.max_hp)
        w = width
        h = 4
        x = px - w // 2
        pygame.draw.rect(self.screen, (30, 30, 30), (x, top, w, h))
        col = cfg.COLOR_HP_GOOD if frac > 0.35 else cfg.COLOR_HP_BAD
        pygame.draw.rect(self.screen, col, (x, top, int(w * frac), h))
        if e.shield > 0:
            pygame.draw.rect(self.screen, (150, 200, 255), (x, top - 3, w, 2))

    def _draw_effect(self, fx):
        px, py = tile_to_px(fx.x, fx.y)
        if fx.kind == "incoming":
            self._draw_incoming(fx, px, py)
            return
        if fx.kind == "blast":
            self._draw_blast(fx, px, py)
            return
        if fx.kind == "chain":
            # electric arcs between chained points (Electro units, Tesla beam)
            prog = min(1.0, fx.elapsed / fx.duration)
            alpha = 1.0 - prog
            col = (110, 205, 255)
            t = self._now()
            pts = [tile_to_px(x, y) for (x, y) in fx.points]
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                mx = (x1 + x2) / 2 + math.sin(t * 45 + x2) * 3
                my = (y1 + y2) / 2 + math.cos(t * 45 + y2) * 3
                seg = [(x1, y1), (mx, my), (x2, y2)]
                pygame.draw.lines(self.screen, dk_c(col, 70), False, seg,
                                  max(1, int(5 * alpha)))
                pygame.draw.lines(self.screen, col, False, seg,
                                  max(1, int(3 * alpha)))
                pygame.draw.lines(self.screen, (240, 250, 255), False, seg, 1)
            for (x2, y2) in pts[1:]:
                pygame.draw.circle(self.screen, col, (int(x2), int(y2)),
                                   max(1, int(4 * alpha)), 1)
            return
        if fx.kind == "aoe":
            # brief expanding ring showing a splash hit's true radius
            prog = min(1.0, fx.elapsed / fx.duration)
            col = sprites.CARD_COLORS.get(fx.card_key, (255, 245, 220))
            rad = int(fx.radius * cfg.TILE_SIZE * (0.55 + 0.45 * prog))
            alpha = int(160 * (1.0 - prog))
            surf = pygame.Surface((rad * 2 + 4, rad * 2 + 4), pygame.SRCALPHA)
            c = (rad + 2, rad + 2)
            pygame.draw.circle(surf, col + (alpha // 4,), c, rad)
            pygame.draw.circle(surf, col + (alpha,), c, rad,
                               max(2, int(4 * (1.0 - prog))))
            self.screen.blit(surf, (px - rad - 2, py - rad - 2))
            return
        rad = int(fx.radius * cfg.TILE_SIZE)
        surf = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
        if fx.kind == "tornado":
            for i, rr in enumerate((rad, int(rad * 0.66), int(rad * 0.33))):
                pygame.draw.circle(surf, (200, 205, 215, 60 - i * 12), (rad, rad), rr)
            for k in range(6):                       # spinning arms
                ang = fx.elapsed * 8 + k * math.pi / 3
                pygame.draw.line(surf, (235, 240, 250, 130), (rad, rad),
                                 (rad + int(math.cos(ang) * rad * 0.85),
                                  rad + int(math.sin(ang) * rad * 0.85)), 2)
            self.screen.blit(surf, (px - rad, py - rad))
            return
        if fx.kind == "poison":
            color = (120, 60, 160, 90)
        elif fx.kind == "rage":
            color = (200, 60, 200, 80)
        elif fx.kind == "graveyard":
            color = (80, 45, 110, 80)
        else:  # log
            color = (150, 110, 70, 160)
        pygame.draw.circle(surf, color, (rad, rad), rad)
        self.screen.blit(surf, (px - rad, py - rad))

    def _draw_incoming(self, fx, px, py):
        """Telegraph shown while a spell is inbound (before it detonates)."""
        prog = min(1.0, fx.elapsed / fx.duration)
        fxcol = SPELL_FX_COLORS.get(fx.card_key, (240, 240, 240))
        team_col = self._team_color(fx.team)   # red = enemy cast, blue = you
        rad = int(fx.radius * cfg.TILE_SIZE)
        pad = 6
        surf = pygame.Surface((rad * 2 + pad * 2, rad * 2 + pad * 2), pygame.SRCALPHA)
        c = (rad + pad, rad + pad)
        pygame.draw.circle(surf, fxcol + (45,), c, rad)               # faint area
        pulse = 2 + int(2 * (0.5 + 0.5 * math.sin(fx.elapsed * 12)))  # pulsing ring
        pygame.draw.circle(surf, team_col + (230,), c, rad, pulse)
        # corner ticks
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            x1 = c[0] + dx * rad
            y1 = c[1] + dy * rad
            pygame.draw.line(surf, team_col + (210,), (x1, y1),
                             (x1 - dx * 6, y1 - dy * 6), 2)
        inner = int(rad * (1 - prog)) + 3      # shrinking "dropping in" marker
        pygame.draw.circle(surf, fxcol + (170,), c, inner, 3)
        self.screen.blit(surf, (px - rad - pad, py - rad - pad))

    def _draw_blast(self, fx, px, py):
        """Detonation flash when a spell lands."""
        prog = min(1.0, fx.elapsed / fx.duration)
        fxcol = SPELL_FX_COLORS.get(fx.card_key, (240, 240, 240))
        rad = int(fx.radius * cfg.TILE_SIZE * (0.45 + 0.75 * prog))
        alpha = int(200 * (1 - prog))
        surf = pygame.Surface((rad * 2 + 4, rad * 2 + 4), pygame.SRCALPHA)
        c = (rad + 2, rad + 2)
        pygame.draw.circle(surf, fxcol + (alpha,), c, rad, max(2, int(5 * (1 - prog)) + 1))
        pygame.draw.circle(surf, (255, 255, 255, int(160 * (1 - prog))), c, int(rad * 0.5))
        self.screen.blit(surf, (px - rad - 2, py - rad - 2))

    def _draw_projectile(self, p):
        px, py = tile_to_px(p.x, p.y)
        px, py = int(px), int(py)
        kind, col = PROJ_STYLES.get(p.style, ("dot", (255, 240, 160)))
        ax, ay = p.vx, p.vy   # unit facing vector
        t = self._now()
        if kind in ("arrow", "fire_arrow", "xbolt", "dart", "spear"):
            ln = {"arrow": 10, "fire_arrow": 10, "xbolt": 9,
                  "dart": 8, "spear": 13}[kind]
            w = 3 if kind == "spear" else 2
            tail = (px - ax * ln, py - ay * ln)
            pygame.draw.line(self.screen, col, tail, (px, py), w)
            # arrowhead
            pygame.draw.circle(self.screen, lt_c(col, 30), (px, py), 2)
            if kind == "fire_arrow":
                pygame.draw.circle(self.screen, (255, 210, 90),
                                   (int(px - ax * ln), int(py - ay * ln)), 3)
            if kind == "spear":
                pygame.draw.line(self.screen, STEEL_COL,
                                 (px - ax * 3, py - ay * 3), (px, py), 3)
        elif kind == "bullet":
            pygame.draw.line(self.screen, col, (px - ax * 7, py - ay * 7),
                             (px, py), 2)
            pygame.draw.circle(self.screen, (255, 255, 230), (px, py), 1)
        elif kind == "pellet":
            pygame.draw.circle(self.screen, col, (px, py), 2)
        elif kind == "fire":
            pygame.draw.circle(self.screen, dk_c(col, 60),
                               (int(px - ax * 5), int(py - ay * 5)), 3)
            pygame.draw.circle(self.screen, col, (px, py), 4)
            pygame.draw.circle(self.screen, (255, 235, 150), (px, py), 2)
        elif kind == "ice":
            pts = [(px + ax * 6, py + ay * 6), (px - ay * 3, py + ax * 3),
                   (px - ax * 6, py - ay * 6), (px + ay * 3, py - ax * 3)]
            pygame.draw.polygon(self.screen, col, pts)
            pygame.draw.polygon(self.screen, (240, 252, 255), pts, 1)
        elif kind == "magic":
            pygame.draw.circle(self.screen, col, (px, py), 3)
            for a in (0.0, 1.57, 3.14, 4.71):
                aa = a + t * 6
                pygame.draw.line(self.screen, lt_c(col, 50), (px, py),
                                 (px + math.cos(aa) * 6, py + math.sin(aa) * 6), 1)
        elif kind == "bomb":
            pygame.draw.circle(self.screen, col, (px, py), 4)
            pygame.draw.circle(self.screen, lt_c(col, 60), (px - 1, py - 1), 1)
            pygame.draw.line(self.screen, (255, 200, 90), (px + 2, py - 4),
                             (px + 4, py - 6), 2)
        elif kind == "axe":
            aa = t * 14
            for a0 in (aa, aa + 1.57):
                pygame.draw.line(self.screen, col,
                                 (px - math.cos(a0) * 6, py - math.sin(a0) * 6),
                                 (px + math.cos(a0) * 6, py + math.sin(a0) * 6), 3)
            pygame.draw.circle(self.screen, (120, 90, 60), (px, py), 2)
        elif kind == "boulder":
            pygame.draw.circle(self.screen, col, (px, py), 7)
            pygame.draw.circle(self.screen, dk_c(col, 40), (px, py), 7, 2)
            pygame.draw.circle(self.screen, dk_c(col, 40), (px - 2, py + 1), 1)
        elif kind == "laser":
            # elongated blue bolt with a white-hot core and jitter crackle
            ln = 14
            x1, y1 = px - ax * ln, py - ay * ln
            pygame.draw.line(self.screen, dk_c(col, 60), (x1, y1), (px, py), 6)
            pygame.draw.line(self.screen, col, (x1, y1), (px, py), 3)
            pygame.draw.line(self.screen, (240, 250, 255), (x1, y1), (px, py), 1)
            # small perpendicular crackles that flicker along the bolt
            nx, ny = -ay, ax
            for f, s in ((0.3, 4), (0.7, -4)):
                jx = x1 + (px - x1) * f + math.sin(t * 40 + f * 9) * 1.5
                jy = y1 + (py - y1) * f + math.cos(t * 40 + f * 9) * 1.5
                pygame.draw.line(self.screen, (200, 240, 255),
                                 (jx, jy), (jx + nx * s, jy + ny * s), 1)
            pygame.draw.circle(self.screen, (240, 250, 255), (px, py), 2)
        elif kind == "zap":
            pygame.draw.circle(self.screen, col, (px, py), 3)
            for i in range(3):
                a = t * 20 + i * 2.09
                pygame.draw.line(self.screen, (255, 255, 210), (px, py),
                                 (px + math.cos(a) * 6, py + math.sin(a) * 6), 1)
        elif kind == "orb":
            pygame.draw.circle(self.screen, dk_c(col, 60), (px, py), 8)
            pygame.draw.circle(self.screen, col, (px, py), 6)
            pygame.draw.circle(self.screen, (255, 255, 240), (px, py), 3)
        elif kind == "cannonball":
            pygame.draw.circle(self.screen, col, (px, py), 5)
            pygame.draw.circle(self.screen, lt_c(col, 50), (px - 1, py - 2), 1)
        else:
            pygame.draw.circle(self.screen, col, (px, py), 3)

    def _draw_beams(self):
        """Continuous beams for ramping attackers (Inferno Tower / Dragon)."""
        for e in self.match.entities:
            if not (e.alive and e.card.ramp and e.target and e.target.alive):
                continue
            if e.deploy_timer > 0 or e.stun_timer > 0 or e.freeze_timer > 0:
                continue
            d = dist(e.x, e.y, e.target.x, e.target.y)
            if d > e.range + e.target.radius + 0.25:
                continue
            x1, y1 = tile_to_px(e.x, e.y)
            x2, y2 = tile_to_px(e.target.x, e.target.y)
            prog = min(e.ramp_time * 1.6 / 7.0, 1.0)  # 0 -> max ramp
            col = (255, int(200 - 140 * prog), int(90 - 60 * prog))
            pygame.draw.line(self.screen, dk_c(col, 80), (x1, y1), (x2, y2),
                             4 + int(3 * prog))
            pygame.draw.line(self.screen, col, (x1, y1), (x2, y2),
                             2 + int(2 * prog))
            if prog > 0.5:
                pygame.draw.line(self.screen, (255, 255, 230), (x1, y1),
                                 (x2, y2), 1)
            pygame.draw.circle(self.screen, col, (int(x2), int(y2)),
                               3 + int(2 * prog))

    def _draw_placement_preview(self):
        if self.selected is None:
            return
        key = self.match.hands[PLAYER][self.selected]
        card = cards.CARDS[key]
        mx, my = pygame.mouse.get_pos()
        if my > cfg.ARENA_Y0 + cfg.ARENA_PX_H:
            return
        tx, ty = px_to_tile(mx, my)
        ok = (self.match.elixir[PLAYER] >= card.elixir
              and self.match.can_place(PLAYER, key, tx, ty))
        color = (90, 220, 90) if ok else (220, 80, 80)
        if card.category == "spell" and card.spell_radius > 0:
            rad = int(card.spell_radius * cfg.TILE_SIZE)
            surf = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color + (70,), (rad, rad), rad)
            self.screen.blit(surf, (mx - rad, my - rad))
        pygame.draw.circle(self.screen, color, (mx, my), 8, 2)

    def _crown_icon(self, x, y, col):
        pts = [(x - 8, y + 5), (x - 8, y - 2), (x - 4, y + 1), (x, y - 5),
               (x + 4, y + 1), (x + 8, y - 2), (x + 8, y + 5)]
        pygame.draw.polygon(self.screen, col, pts)
        pygame.draw.polygon(self.screen, dk_c(col, 70), pts, 1)

    def _draw_topbar(self):
        m = self.match
        pygame.draw.rect(self.screen, (22, 26, 38), (0, 0, cfg.WINDOW_W, cfg.TOP_BAR))
        pygame.draw.line(self.screen, (60, 66, 88), (0, cfg.TOP_BAR - 1),
                         (cfg.WINDOW_W, cfg.TOP_BAR - 1), 1)
        # timer chip (amber during overtime / boosted elixir)
        t = max(0, m.time_left)
        label = "%d:%02d" % (int(t) // 60, int(t) % 60)
        mult = m.elixir_multiplier()
        prefix = "OT " if m.overtime else ""
        if mult > 1:
            prefix += "x%d " % int(mult)
        chip_col = (120, 80, 30) if (m.overtime or mult > 1) else (40, 48, 66)
        chip = pygame.Rect(0, 0, 110, 26)
        chip.center = (cfg.WINDOW_W // 2, cfg.TOP_BAR // 2)
        pygame.draw.rect(self.screen, chip_col, chip, border_radius=13)
        pygame.draw.rect(self.screen, lt_c(chip_col, 40), chip, 1, border_radius=13)
        self._text(prefix + label, self.font_m, cfg.COLOR_TEXT, center=chip.center)
        # crowns with icons
        self._crown_icon(18, cfg.TOP_BAR // 2, cfg.COLOR_TEAM_ENEMY)
        self._text("%d" % m.crowns[ENEMY], self.font_m, cfg.COLOR_TEAM_ENEMY,
                   topleft=(32, cfg.TOP_BAR // 2 - 10))
        self._crown_icon(cfg.WINDOW_W - 44, cfg.TOP_BAR // 2, cfg.COLOR_TEAM_PLAYER)
        self._text("%d" % m.crowns[PLAYER], self.font_m, cfg.COLOR_TEAM_PLAYER,
                   topleft=(cfg.WINDOW_W - 30, cfg.TOP_BAR // 2 - 10))

    def _draw_hud(self):
        m = self.match
        hud_y = cfg.ARENA_Y0 + cfg.ARENA_PX_H
        pygame.draw.rect(self.screen, cfg.COLOR_HUD_BG,
                         (0, hud_y, cfg.WINDOW_W, cfg.HUD_HEIGHT))
        pygame.draw.line(self.screen, (60, 66, 88), (0, hud_y),
                         (cfg.WINDOW_W, hud_y), 1)
        # elixir bar with droplet icon
        el = m.elixir[PLAYER]
        bar_x, bar_y, bar_w, bar_h = 36, hud_y + 8, cfg.WINDOW_W - 70, 12
        pygame.draw.polygon(self.screen, cfg.COLOR_ELIXIR,
                            [(20, bar_y - 2), (14, bar_y + 8), (20, bar_y + 13),
                             (26, bar_y + 8)])
        pygame.draw.rect(self.screen, (38, 22, 40), (bar_x, bar_y, bar_w, bar_h),
                         border_radius=6)
        fill_w = int(bar_w * el / cfg.ELIXIR_MAX)
        if fill_w > 4:
            pygame.draw.rect(self.screen, cfg.COLOR_ELIXIR,
                             (bar_x, bar_y, fill_w, bar_h), border_radius=6)
            pygame.draw.rect(self.screen, lt_c(cfg.COLOR_ELIXIR, 50),
                             (bar_x + 2, bar_y + 2, max(0, fill_w - 4), 3),
                             border_radius=2)
        for i in range(1, int(cfg.ELIXIR_MAX)):
            x = bar_x + int(bar_w * i / cfg.ELIXIR_MAX)
            pygame.draw.line(self.screen, (20, 10, 20), (x, bar_y), (x, bar_y + bar_h))
        self._text("%d" % int(el), self.font_m, lt_c(cfg.COLOR_ELIXIR, 60),
                   topleft=(bar_x + bar_w + 8, bar_y - 3))
        # hand
        for i, r in enumerate(self._hand_slot_rects()):
            if i >= len(m.hands[PLAYER]):
                continue
            key = m.hands[PLAYER][i]
            card = cards.CARDS[key]
            affordable = el >= card.elixir
            sel = (self.selected == i)
            # slot with shadow + gradient
            pygame.draw.rect(self.screen, (16, 18, 26), r.move(0, 3), border_radius=9)
            bg = (58, 78, 118) if sel else (44, 50, 62)
            pygame.draw.rect(self.screen, bg, r, border_radius=9)
            pygame.draw.rect(self.screen, lt_c(bg, 16),
                             (r.x + 2, r.y + 2, r.w - 4, r.h // 2), border_radius=7)
            if sel:
                pygame.draw.rect(self.screen, (250, 240, 140), r, 3, border_radius=9)
            elif affordable:
                pygame.draw.rect(self.screen, (96, 108, 138), r, 1, border_radius=9)
            spr = sprites.get_sprite(key, 44)
            if not affordable:
                spr = spr.copy()
                spr.fill((90, 90, 90, 160), special_flags=pygame.BLEND_RGBA_MULT)
            self.screen.blit(spr, (r.centerx - 22, r.y + 6))
            # cost badge (top-left, so the name row gets full width)
            pygame.draw.circle(self.screen, dk_c(cfg.COLOR_ELIXIR, 40),
                               (r.x + 11, r.y + 12), 10)
            pygame.draw.circle(self.screen, cfg.COLOR_ELIXIR, (r.x + 10, r.y + 11), 9)
            self._text(str(card.elixir), self.font_s, (255, 255, 255),
                       center=(r.x + 10, r.y + 11))
            name = card.name if len(card.name) <= 9 else card.name[:8] + "."
            self._text(name, self.font_s, cfg.COLOR_TEXT,
                       center=(r.centerx, r.bottom - 10))
        # next card in a framed box on the right
        nk = m.next_card[PLAYER]
        if nk:
            hand = self._hand_slot_rects()
            nb = pygame.Rect(hand[-1].right + 12, hand[-1].y + 14,
                             self.NEXT_BOX_W - 8, 56)
            if nb.right > cfg.WINDOW_W - 4:
                nb.right = cfg.WINDOW_W - 4
            pygame.draw.rect(self.screen, (30, 34, 46), nb, border_radius=8)
            pygame.draw.rect(self.screen, (70, 78, 100), nb, 1, border_radius=8)
            self._text("Next", self.font_s, (170, 178, 195),
                       center=(nb.centerx, nb.y + 9))
            self.screen.blit(sprites.get_sprite(nk, 32), (nb.centerx - 16, nb.y + 18))
        self._draw_ability_button()

    def _draw_ability_button(self):
        champ, ready, cost = self.match.ability_status(PLAYER)
        if champ is None:
            return
        r = self._ability_btn_rect()
        cx, cy = r.center
        rad = r.w // 2
        pygame.draw.circle(self.screen, (15, 18, 26), (cx, cy + 2), rad)
        base = (250, 210, 70) if ready else (95, 92, 70)
        pygame.draw.circle(self.screen, base, (cx, cy), rad)
        pygame.draw.circle(self.screen, (255, 240, 160) if ready else (60, 60, 55),
                           (cx, cy), rad, 2)
        # champion face icon
        self.screen.blit(sprites.get_sprite(champ.key, rad + 6),
                         (cx - (rad + 6) // 2, cy - (rad + 6) // 2))
        # cooldown wedge
        if champ.ability_cd > 0:
            frac = min(1.0, champ.ability_cd / max(champ.card.ability_cooldown, 0.1))
            overlay = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            pygame.draw.circle(overlay, (0, 0, 0, 150), (rad, rad), rad)
            self.screen.blit(overlay, r.topleft)
            self._text("%d" % math.ceil(champ.ability_cd), self.font_m,
                       (255, 255, 255), center=(cx, cy))
        # elixir cost badge
        pygame.draw.circle(self.screen, cfg.COLOR_ELIXIR, (r.right - 4, r.y + 4), 8)
        self._text(str(cost), self.font_s, (255, 255, 255), center=(r.right - 4, r.y + 4))
        # ability name on a small chip to the right of the button
        label = self.font_s.render(champ.card.ability_name, True, (240, 230, 170))
        chip = pygame.Rect(r.right + 6, cy - 9, label.get_width() + 10, 18)
        pygame.draw.rect(self.screen, (20, 24, 34), chip, border_radius=6)
        pygame.draw.rect(self.screen, (150, 130, 70), chip, 1, border_radius=6)
        self.screen.blit(label, (chip.x + 5, chip.y + 3))

    def _draw_result(self):
        overlay = pygame.Surface((cfg.WINDOW_W, cfg.WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))
        cx, cy = cfg.WINDOW_W // 2, cfg.WINDOW_H // 2
        color = (120, 240, 120) if self.result_text == "VICTORY!" else \
                (240, 120, 120) if self.result_text == "DEFEAT" else (230, 230, 230)
        panel = pygame.Rect(cx - 150, cy - 92, 300, 178)
        pygame.draw.rect(self.screen, (28, 32, 46), panel, border_radius=14)
        pygame.draw.rect(self.screen, color, panel, 2, border_radius=14)
        self._text(self.result_text, self.font_xl, color, center=(cx, cy - 46))
        self._crown_icon(cx - 62, cy + 4, cfg.COLOR_TEAM_PLAYER)
        self._crown_icon(cx + 62, cy + 4, cfg.COLOR_TEAM_ENEMY)
        self._text("%d  -  %d" % (self.match.crowns[PLAYER], self.match.crowns[ENEMY]),
                   self.font_l, cfg.COLOR_TEXT, center=(cx, cy + 4))
        self._text("Click anywhere to return to the menu", self.font_s,
                   (200, 200, 200), center=(cx, cy + 58))
