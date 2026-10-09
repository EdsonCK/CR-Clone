"""
============================================================================
  GAME.PY  --  Window, screens, rendering, input and the main loop
============================================================================

Screens:
  * MENU     -- Battle / Edit Deck / AI Deck / Records / How To Play / Quit
  * PREMATCH -- Battle Setup: AI intelligence (1-5), AI elixir boost slider
                (0.5x-2.0x), both decks, Start Battle
  * AIDECK   -- choose the AI's deck (returns to wherever you came from)
  * DECK     -- pick 8 cards (left-click add/remove, right-click remove)
  * MATCH    -- the live battle (arena + HUD)
  * RESULT   -- victory / defeat / draw, Play Again / Main Menu

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
import sounds
import fx as fxmod
from engine import (Match, PLAYER, ENEMY, RIVER_TOP, RIVER_BOTTOM,
                    BRIDGE_X, RIVER_CENTER, dist)
from ai import AIController

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECK_FILE = os.path.join(_ROOT, "player_deck.json")
AI_DECK_FILE = os.path.join(_ROOT, "ai_custom_deck.json")
STATS_FILE = os.path.join(_ROOT, "records.json")
SETTINGS_FILE = os.path.join(_ROOT, "settings.json")

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

# Colour of chain / link lightning per source card (default electric blue).
CHAIN_COLORS = {
    "golden_knight": (255, 210, 80),
    "goblinstein": (150, 255, 170),
}


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

    click_sound = None      # set by Game: plays the UI click

    def click(self, pos):
        if self.rect.collidepoint(pos):
            if Button.click_sound:
                Button.click_sound()
            self.cb()
            return True
        return False


class Game:
    def __init__(self):
        try:
            pygame.mixer.pre_init(sounds.SR, -16, 2, 512)
        except Exception:
            pass
        pygame.init()
        pygame.display.set_caption("Clash Clone - Singleplayer")
        self.screen = pygame.display.set_mode((cfg.WINDOW_W, cfg.WINDOW_H))
        self.clock = pygame.time.Clock()
        sprites.ensure_sprites()

        self.font_s = pygame.font.SysFont("arial", 13)
        self.font_m = pygame.font.SysFont("arial", 18, bold=True)
        self.font_l = pygame.font.SysFont("arial", 30, bold=True)
        self.font_xl = pygame.font.SysFont("arial", 44, bold=True)

        # music & sound effects (rendered once into assets/sounds)
        sounds.ensure_sounds(progress=self._loading_screen)
        self.sfx = sounds.SoundManager(cfg.MUSIC_VOLUME, cfg.SFX_VOLUME)
        Button.click_sound = lambda: self.sfx.play("ui_click", 0.6, min_gap=0.02)
        self.music_on = True
        self.sfx_on = True
        self._audio = {}
        self.fx = fxmod.FX()

        self.state = "menu"
        self.running = True

        self.player_deck = self._load_deck()
        self.match = None
        self.ai = None
        self.selected = None       # index into hand while deploying
        self.result_text = ""
        self.deck_msg = ""

        # pre-match setup choices
        self.ai_level = cfg.AI_DEFAULT_LEVEL       # AI intelligence 1-5
        self.ai_elixir = cfg.AI_DEFAULT_ELIXIR     # AI elixir boost 0.5-2.0
        self.slider_drag = False
        self.ai_deck_choice = "Classic"
        self._load_settings()
        self.sfx.set_music_on(self.music_on)
        self.sfx.set_sfx_on(self.sfx_on)
        self.ai_custom_deck = self._load_deck(AI_DECK_FILE, cards.DEFAULT_AI_DECK)
        self.deck_scroll = 0        # vertical scroll offset in the deck builder
        self.deck_mode = "player"   # "player" or "ai" - which deck is being edited
        self.deck_return = "menu"   # screen to return to after editing a deck
        self.deck_backup = []       # deck as it was when the editor opened
        self.deck_drag = False      # dragging the deck-builder scrollbar
        self.aideck_return = "menu" # where the AI Deck screen goes back to
        self.stats = self._load_stats()   # per-intelligence crown/win records

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

    # ---- settings (AI level / elixir / AI deck), remembered between runs ----
    def _load_settings(self):
        try:
            with open(SETTINGS_FILE) as f:
                d = json.load(f)
            if int(d.get("ai_level", 0)) in cfg.AI_LEVELS:
                self.ai_level = int(d["ai_level"])
            self._set_ai_elixir(float(d.get("ai_elixir", self.ai_elixir)), save=False)
            if d.get("ai_deck") in cards.AI_DECK_PRESETS or d.get("ai_deck") in (
                    "Random", "Custom"):
                self.ai_deck_choice = d["ai_deck"]
            self.music_on = bool(d.get("music", True))
            self.sfx_on = bool(d.get("sfx", True))
        except Exception:
            pass

    def _save_settings(self):
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump({"ai_level": self.ai_level, "ai_elixir": self.ai_elixir,
                           "ai_deck": self.ai_deck_choice,
                           "music": self.music_on, "sfx": self.sfx_on}, f)
        except Exception:
            pass

    def _set_ai_elixir(self, v, save=True):
        step = cfg.AI_ELIXIR_MULT_STEP
        v = round(round(v / step) * step, 2)
        self.ai_elixir = min(max(v, cfg.AI_ELIXIR_MULT_MIN), cfg.AI_ELIXIR_MULT_MAX)
        if save:
            self._save_settings()

    def _set_ai_level(self, lv):
        if lv in cfg.AI_LEVELS:
            self.ai_level = lv
            self._save_settings()

    # ---- records / stats (per AI intelligence level) ----
    @staticmethod
    def _level_key(lv):
        return "L%d" % lv

    def _blank_stats(self):
        return {self._level_key(lv): {"wins": 0, "losses": 0, "draws": 0,
                                      "cf": 0, "ca": 0, "best": 0.0, "even_w": 0}
                for lv in cfg.AI_LEVELS}

    def _load_stats(self):
        s = self._blank_stats()
        self._legacy_stats = {}
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE) as f:
                    saved = json.load(f)
                for d, rec in saved.items():
                    if d in s and isinstance(rec, dict):
                        for k in s[d]:
                            if k in rec:
                                s[d][k] = type(s[d][k])(rec[k])
                    else:
                        self._legacy_stats[d] = rec    # old Easy/Hard/... records
            except Exception:
                pass
        return s

    def _save_stats(self):
        try:
            out = dict(self._legacy_stats)
            out.update(self.stats)
            with open(STATS_FILE, "w") as f:
                json.dump(out, f, indent=1)
        except Exception:
            pass

    def _record_result(self):
        m = self.match
        rec = self.stats.setdefault(self._level_key(self.ai_level),
                                    self._blank_stats()["L1"])
        rec["cf"] += m.crowns[PLAYER]
        rec["ca"] += m.crowns[ENEMY]
        if m.winner == PLAYER:
            rec["wins"] += 1
            rec["best"] = max(rec["best"], self.ai_elixir)
            if self.ai_elixir >= 1.0:
                rec["even_w"] += 1
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
            ("Edit Deck", lambda: self._open_player_deck("menu")),
            ("AI Deck", lambda: self._open_aideck("menu")),
            ("Records", lambda: self._goto("records")),
            ("How To Play", lambda: self._goto("help")),
            ("Quit", self._quit),
        ]
        self.menu_buttons = [
            Button((cx - w // 2, y0 + i * gap, w, h), lbl, cb)
            for i, (lbl, cb) in enumerate(labels)
        ]
        # sound toggles (top corners); labels refreshed every frame
        self.music_btn = Button((8, 8, 104, 28), "Music", lambda: self._toggle_music())
        self.sfx_btn = Button((cfg.WINDOW_W - 112, 8, 104, 28), "Sound",
                              lambda: self._toggle_sfx())
        self.menu_buttons += [self.music_btn, self.sfx_btn]

    def _open_deck_editor(self, mode, return_to):
        self.deck_mode = mode
        self.deck_return = return_to
        self.deck_scroll = 0
        self.deck_msg = ""
        self.deck_drag = False
        self.deck_backup = list(self._active_deck())
        self.state = "deck"

    def _open_player_deck(self, return_to="menu"):
        self._open_deck_editor("player", return_to)

    def _open_ai_custom_deck(self):
        # returns to the AI Deck screen, which still remembers where IT
        # should go back to (main menu or Battle Setup)
        self._open_deck_editor("ai", "aideck")

    def _open_aideck(self, return_to="menu"):
        self.aideck_return = return_to
        self.state = "aideck"

    def _goto(self, state):
        self.state = state

    def _quit(self):
        self.running = False

    def _open_prematch(self):
        if len(self.player_deck) != cfg.DECK_SIZE:
            self._open_player_deck("prematch")
            self.deck_msg = "Pick 8 cards first!"
            return
        self.state = "prematch"

    def _begin_battle(self):
        if len(self.player_deck) != cfg.DECK_SIZE:
            self._open_player_deck("prematch")
            self.deck_msg = "Pick 8 cards first!"
            return
        cfg.apply_ai_settings(self.ai_level, self.ai_elixir)
        self._save_settings()
        self.match = Match(self.player_deck, self._resolve_ai_deck())
        self.match.record_events = True
        self.ai = AIController(self.match, team=ENEMY, level=self.ai_level)
        self._audio = {}
        self.fx.clear()
        self.sfx.play("match_start", 0.9, min_gap=0.0)
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
            self._update_audio(dt)
            if self.state in ("match", "result") and self.match is not None:
                self.fx.update(dt, self.match)
            self._draw()
            pygame.display.flip()
        pygame.quit()

    # ================================================================= AUDIO
    def _loading_screen(self, n, total):
        """Shown while sounds are rendered on the very first launch."""
        if n % 6:
            return
        pygame.event.pump()
        self.screen.fill((24, 28, 44))
        cx, cy = cfg.WINDOW_W // 2, cfg.WINDOW_H // 2
        self._text("Composing music & sounds...", self.font_m, (240, 220, 120),
                   center=(cx, cy - 20))
        w = cfg.WINDOW_W - 80
        pygame.draw.rect(self.screen, (50, 56, 74), (40, cy + 6, w, 10), border_radius=5)
        pygame.draw.rect(self.screen, (240, 200, 90),
                         (40, cy + 6, int(w * n / max(total, 1)), 10), border_radius=5)
        self._text("(first launch only)", self.font_s, (170, 178, 195), center=(cx, cy + 34))
        pygame.display.flip()

    def _toggle_music(self):
        self.music_on = not self.music_on
        self.sfx.set_music_on(self.music_on)
        self._save_settings()

    def _toggle_sfx(self):
        self.sfx_on = not self.sfx_on
        self.sfx.set_sfx_on(self.sfx_on)
        if self.sfx_on:
            self.sfx.play("ui_toggle")
        self._save_settings()

    def _pan(self, x):
        return max(0.0, min(1.0, x / cfg.GRID_COLS))

    def _update_audio(self, dt):
        self.sfx.tick(dt)
        m = self.match
        # ---- music follows the screen ----
        if self.state == "match" and m is not None:
            final = m.overtime or m.time_left <= cfg.DOUBLE_ELIXIR_AT
            self.sfx.music("final" if final else "battle")
        elif self.state == "result":
            self.sfx.music(None)
        else:
            self.sfx.music("menu")
        if m is None or self.state not in ("match", "result"):
            return
        evs = m.take_events()
        self._handle_events(evs)
        if self.state != "match":
            return
        a = self._audio
        # announcements: double elixir, overtime, final countdown, king wakes
        mult = m.elixir_multiplier()
        if mult >= 2 and not m.overtime and not a.get("double"):
            a["double"] = True
            self.sfx.play("double_elixir", 0.9)
        if m.overtime and not a.get("ot"):
            a["ot"] = True
            self.sfx.play("overtime", 0.9)
        sec = int(math.ceil(m.time_left))
        if 0 < sec <= 10 and sec != a.get("tick"):
            a["tick"] = sec
            self.sfx.play("tick", 0.7)
        for team in (PLAYER, ENEMY):
            k = m.towers[(team, "king")]
            if k.active and not a.get(("king", team)):
                a[("king", team)] = True
                if k.alive:
                    self.sfx.play("king_wake", 0.8, self._pan(k.x))

    def _handle_events(self, evs):
        for ev in evs:
            kind, key = ev["kind"], ev["key"]
            pan = self._pan(ev["x"])
            mine = ev.get("team") == PLAYER
            if kind == "attack":
                tower = key in ("princess_tower", "king_tower")
                self.sfx.play(key + "_attack", 0.32 if tower else 0.5, pan, min_gap=0.07)
            elif kind == "deploy":
                c = cards.CARDS.get(key)
                if c is not None and c.category == "spell":
                    self.sfx.play(key + "_cast", 0.85 if mine else 0.7, pan, min_gap=0.02)
                else:
                    self.sfx.play(key + "_deploy", 0.85 if mine else 0.7, pan, min_gap=0.02)
            elif kind == "impact":
                self.sfx.play(key + "_impact", 0.95, pan, min_gap=0.02)
            elif kind == "death":
                if ev.get("tower"):
                    self.sfx.play("tower_down", 1.0, pan, min_gap=0.0)
                    self.sfx.play("crown", 0.8, 0.5, min_gap=0.0)
                elif ev.get("building"):
                    self.sfx.play("death_building", 0.7, pan)
                elif ev.get("big"):
                    self.sfx.play("death_big", 0.7, pan)
                else:
                    self.sfx.play("death_small", 0.35, pan, min_gap=0.09)
            elif kind == "ability":
                self.sfx.play("ability", 1.0, pan, min_gap=0.0)
            elif kind == "dash":
                self.sfx.play("dash", 0.6, pan)
            elif kind == "land" and ev.get("slam"):
                self.sfx.play("slam", 0.85, pan)
        self.fx.handle_events(evs, self.match)

    def _on_match_end(self):
        w = self.match.winner
        if w == PLAYER:
            self.result_text = "VICTORY!"
        elif w == ENEMY:
            self.result_text = "DEFEAT"
        else:
            self.result_text = "DRAW"
        self._handle_events(self.match.take_events())
        self.sfx.music(None)
        self.sfx.play("victory" if w == PLAYER else "defeat", 1.0, min_gap=0.0)
        self._record_result()
        self.state = "result"

    # ================================================================= EVENTS
    def _events(self, dt):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_m:
                    self._toggle_music()
                elif e.key == pygame.K_n:
                    self._toggle_sfx()
                if self.state == "prematch" and e.key in (pygame.K_LEFT, pygame.K_RIGHT,
                                                          pygame.K_MINUS, pygame.K_EQUALS,
                                                          pygame.K_KP_MINUS, pygame.K_KP_PLUS):
                    up = e.key in (pygame.K_RIGHT, pygame.K_EQUALS, pygame.K_KP_PLUS)
                    self._set_ai_elixir(self.ai_elixir + (1 if up else -1)
                                        * cfg.AI_ELIXIR_MULT_STEP)
                elif self.state == "prematch" and pygame.K_1 <= e.key <= pygame.K_5:
                    self._set_ai_level(e.key - pygame.K_0)
                if e.key == pygame.K_ESCAPE:
                    if self.state == "match":
                        self.state = "menu"
                    elif self.state == "deck":
                        self._deck_cancel()
                    elif self.state == "aideck":
                        self.state = self.aideck_return
                        self._save_settings()
                    elif self.state in ("help", "result", "prematch", "records"):
                        self.state = "menu"
            elif e.type == pygame.MOUSEWHEEL:
                # the wheel ONLY scrolls - it never selects anything
                if self.state == "deck":
                    self._deck_set_scroll(self.deck_scroll - e.y * 48)
                elif self.state == "prematch":
                    mpos = pygame.mouse.get_pos()
                    if self._slider_zone().collidepoint(mpos):
                        self._set_ai_elixir(self.ai_elixir + (1 if e.y > 0 else -1)
                                            * cfg.AI_ELIXIR_MULT_STEP)
            elif e.type == pygame.MOUSEBUTTONUP:
                if e.button == 1:
                    self.deck_drag = False
                    if self.slider_drag:
                        self.slider_drag = False
                        self._save_settings()
            elif e.type == pygame.MOUSEMOTION:
                if self.state == "deck" and self.deck_drag:
                    self._deck_drag_to(e.pos[1])
                elif self.state == "prematch" and self.slider_drag:
                    self._slider_set_from_x(e.pos[0], save=False)
            elif e.type == pygame.MOUSEBUTTONDOWN:
                # pygame reports wheel turns as buttons 4-7 as well; those
                # must never count as clicks (it used to toggle cards)
                if e.button not in (1, 3):
                    continue
                if self.state == "deck":
                    self._deck_click(e.pos, e.button)
                    continue
                if e.button == 3 and self.state != "match":
                    continue      # right-click only means something in decks/match
                if self.state == "menu":
                    for b in self.menu_buttons:
                        b.click(e.pos)
                elif self.state == "prematch":
                    self._prematch_click(e.pos)
                elif self.state == "aideck":
                    self._aideck_click(e.pos)
                elif self.state == "help":
                    self.state = "menu"
                elif self.state == "records":
                    self.state = "menu"
                elif self.state == "result":
                    self._result_click(e.pos)
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
            if self.selected is not None:
                self.sfx.play("ui_deselect", 0.6, min_gap=0.0)
            self.selected = None
            return
        # champion ability button (bottom-left)
        champ, ready, cost = self.match.ability_status(PLAYER)
        if champ is not None and self._ability_btn_rect().collidepoint(pos):
            if not self.match.activate_ability(PLAYER):
                self.sfx.play("ui_invalid", 0.6)
            return
        rects = self._hand_slot_rects()
        for i, r in enumerate(rects):
            if r.collidepoint(pos):
                if self.selected == i:
                    self.selected = None
                    self.sfx.play("ui_deselect", 0.6, min_gap=0.0)
                else:
                    self.selected = i
                    self.sfx.play("ui_select", 0.6, min_gap=0.0)
                return
        # click on arena to deploy
        if self.selected is not None:
            tx, ty = px_to_tile(*pos)
            if self.match.play_card(PLAYER, self.selected, tx, ty):
                self.selected = None
            else:
                self.sfx.play("ui_invalid", 0.6)

    # ================================================================= PREMATCH
    # Battle Setup layout ------------------------------------------------
    PM_LEVEL_Y = 74         # intelligence buttons
    PM_SLIDER_Y = 214       # elixir slider centre line

    def _prematch_level_rects(self):
        n = len(cfg.AI_LEVELS)
        gap = 6
        w = (cfg.WINDOW_W - 24 - gap * (n - 1)) // n
        return [(pygame.Rect(12 + i * (w + gap), self.PM_LEVEL_Y, w, 52), lv)
                for i, lv in enumerate(sorted(cfg.AI_LEVELS))]

    def _slider_track(self):
        """The draggable track (wide, with room for the -/+ buttons)."""
        return pygame.Rect(62, self.PM_SLIDER_Y - 7, cfg.WINDOW_W - 124, 14)

    def _slider_zone(self):
        """Generous click / wheel area around the track."""
        t = self._slider_track()
        return pygame.Rect(t.x - 14, t.y - 18, t.w + 28, t.h + 36)

    def _slider_pm_rects(self):
        y = self.PM_SLIDER_Y - 20
        return (pygame.Rect(12, y, 40, 40),                       # minus
                pygame.Rect(cfg.WINDOW_W - 52, y, 40, 40))        # plus

    def _slider_presets(self):
        vals = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
        gap = 6
        w = (cfg.WINDOW_W - 24 - gap * (len(vals) - 1)) // len(vals)
        y = self.PM_SLIDER_Y + 34
        return [(pygame.Rect(12 + i * (w + gap), y, w, 28), v)
                for i, v in enumerate(vals)]

    def _slider_x_for(self, v):
        t = self._slider_track()
        f = (v - cfg.AI_ELIXIR_MULT_MIN) / (cfg.AI_ELIXIR_MULT_MAX - cfg.AI_ELIXIR_MULT_MIN)
        return t.x + f * t.w

    def _slider_set_from_x(self, x, save=True):
        t = self._slider_track()
        f = min(max((x - t.x) / t.w, 0.0), 1.0)
        self._set_ai_elixir(cfg.AI_ELIXIR_MULT_MIN
                            + f * (cfg.AI_ELIXIR_MULT_MAX - cfg.AI_ELIXIR_MULT_MIN),
                            save=save)

    def _prematch_buttons(self):
        cx = cfg.WINDOW_W // 2
        bw = (cfg.WINDOW_W - 16 * 2 - 12) // 2
        return [
            Button((16, cfg.WINDOW_H - 168, bw, 40), "Change AI Deck",
                   lambda: self._open_aideck("prematch")),
            Button((cfg.WINDOW_W - 16 - bw, cfg.WINDOW_H - 168, bw, 40),
                   "Edit My Deck", lambda: self._open_player_deck("prematch")),
            Button((16, cfg.WINDOW_H - 116, cfg.WINDOW_W - 32, 48),
                   "Start Battle!", self._begin_battle),
            Button((cx - 60, cfg.WINDOW_H - 56, 120, 34), "Back",
                   lambda: self._goto("menu")),
        ]

    def _prematch_click(self, pos):
        for r, lv in self._prematch_level_rects():
            if r.collidepoint(pos):
                self._set_ai_level(lv)
                return
        minus, plus = self._slider_pm_rects()
        if minus.collidepoint(pos):
            self._set_ai_elixir(self.ai_elixir - cfg.AI_ELIXIR_MULT_STEP)
            return
        if plus.collidepoint(pos):
            self._set_ai_elixir(self.ai_elixir + cfg.AI_ELIXIR_MULT_STEP)
            return
        for r, v in self._slider_presets():
            if r.collidepoint(pos):
                self._set_ai_elixir(v)
                return
        if self._slider_zone().collidepoint(pos):
            self.slider_drag = True
            self._slider_set_from_x(pos[0], save=False)
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
        h, gap_y, top = 30, 6, 60
        rects = []
        for i, name in enumerate(opts):
            r, c = divmod(i, cols)
            rects.append((pygame.Rect(16 + c * (w + 8), top + r * (h + gap_y), w, h), name))
        return rects

    def _aideck_buttons(self):
        cx = cfg.WINDOW_W // 2
        btns = [Button((cx - 115, cfg.WINDOW_H - 112, 230, 40),
                       "Build / Edit Custom Deck", self._open_ai_custom_deck)]
        y = cfg.WINDOW_H - 58
        if self.aideck_return == "prematch":
            # came here from Battle Setup -> go straight back to it
            btns.append(Button((cx - 110, y, 220, 40), "Back to Battle Setup",
                               lambda: self._goto("prematch")))
        else:
            bw = (cfg.WINDOW_W - 32 - 12) // 2
            btns.append(Button((16, y, bw, 40), "Main Menu",
                               lambda: self._goto("menu")))
            btns.append(Button((cfg.WINDOW_W - 16 - bw, y, bw, 40),
                               "Battle Setup", self._open_prematch))
        return btns

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
        self._text("AI Deck", self.font_l, (240, 220, 120), center=(cx, 24))
        self._text("Pick the deck the AI will play", self.font_s,
                   (170, 178, 195), center=(cx, 44))
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
    # Layout (top to bottom): title, your 8 cards as 2 rows of 4 big slots,
    # an info line, the scrollable card collection, then the buttons.
    DECK_COLS = 6
    DECK_CELL_H = 74
    DECK_ICON = 40          # collection icon size (was 30)
    SLOT_ICON = 56          # icon size of your 8 chosen cards
    DECK_MARGIN = 12

    def _deck_slot_rects(self):
        """Your 8 chosen cards: 2 rows of 4 large slots at the top."""
        m, gap = self.DECK_MARGIN, 8
        w = (cfg.WINDOW_W - m * 2 - gap * 3) // 4
        h = 78
        top = 58
        return [pygame.Rect(m + (i % 4) * (w + gap), top + (i // 4) * (h + gap), w, h)
                for i in range(cfg.DECK_SIZE)]

    def _deck_viewport(self):
        """(top, bottom) y of the scrollable card collection."""
        slots = self._deck_slot_rects()
        return slots[-1].bottom + 34, cfg.WINDOW_H - 50

    def _deck_max_scroll(self):
        rows = (len(cards.DEPLOYABLE_CARDS) + self.DECK_COLS - 1) // self.DECK_COLS
        top, bottom = self._deck_viewport()
        return max(0, rows * self.DECK_CELL_H - (bottom - top) + 6)

    def _deck_set_scroll(self, v):
        self.deck_scroll = int(max(0, min(self._deck_max_scroll(), v)))

    def _deck_scrollbar_track(self):
        top, bottom = self._deck_viewport()
        return pygame.Rect(cfg.WINDOW_W - 11, top, 10, bottom - top)

    def _deck_drag_to(self, y):
        top, bottom = self._deck_viewport()
        frac = (y - top) / max(1, bottom - top)
        self._deck_set_scroll(frac * self._deck_max_scroll())

    def _deck_grid(self):
        m = self.DECK_MARGIN
        cell_w = (cfg.WINDOW_W - m * 2) // self.DECK_COLS
        top, _ = self._deck_viewport()
        rects = []
        for idx, card in enumerate(cards.DEPLOYABLE_CARDS):
            r = idx // self.DECK_COLS
            c = idx % self.DECK_COLS
            y = top + r * self.DECK_CELL_H - self.deck_scroll
            rects.append((pygame.Rect(m + c * cell_w, y,
                                      cell_w - 4, self.DECK_CELL_H - 4), card))
        return rects

    def _deck_buttons(self):
        y = cfg.WINDOW_H - 40
        m = self.DECK_MARGIN
        widths = [112, 70, 78]
        gap = (cfg.WINDOW_W - 2 * m - sum(widths) - 78) // 3
        x = m
        out = []
        for w, (lbl, cb) in zip(widths + [78],
                                [("Save & Back", self._deck_save_back),
                                 ("Clear", self._deck_clear),
                                 ("Default", self._deck_default),
                                 ("Cancel", self._deck_cancel)]):
            out.append(Button((x, y, w, 30), lbl, cb))
            x += w + gap
        return out

    def _deck_save_back(self):
        if len(self._active_deck()) == cfg.DECK_SIZE:
            self._save_deck()
            self.deck_msg = ""
            if self.deck_mode == "ai":
                self.ai_deck_choice = "Custom"   # auto-select the deck you built
            self.state = self.deck_return
        else:
            self.deck_msg = "Deck must have exactly 8 cards."

    def _deck_cancel(self):
        """Leave without saving (restores the deck as it was)."""
        self._set_active_deck(list(self.deck_backup))
        self.deck_msg = ""
        self.deck_drag = False
        if self.deck_return == "prematch" and len(self.player_deck) != cfg.DECK_SIZE:
            self.state = "menu"
        else:
            self.state = self.deck_return

    def _deck_clear(self):
        self._set_active_deck([])
        self.deck_msg = ""

    def _deck_default(self):
        d = cards.DEFAULT_AI_DECK if self.deck_mode == "ai" else cards.DEFAULT_PLAYER_DECK
        self._set_active_deck(list(d))
        self.deck_msg = ""

    def _deck_add(self, card):
        deck = self._active_deck()
        if card.key in deck:
            return
        if len(deck) >= cfg.DECK_SIZE:
            self.deck_msg = "Deck is full - remove a card first."
            return
        if card.is_champion and any(cards.CARDS[k].is_champion for k in deck):
            self.deck_msg = "Only 1 Champion per deck."
            return
        deck.append(card.key)
        self.deck_msg = ""

    def _deck_click(self, pos, button=1):
        """Left click: add / remove.  Right click: remove only.
        (Mouse-wheel events never get here - they only scroll.)"""
        deck = self._active_deck()
        if button == 1:
            for b in self._deck_buttons():
                if b.click(pos):
                    return
            if self._deck_scrollbar_track().collidepoint(pos):
                self.deck_drag = True
                self._deck_drag_to(pos[1])
                return
        # your 8 cards: either button removes
        for i, r in enumerate(self._deck_slot_rects()):
            if r.collidepoint(pos):
                if i < len(deck):
                    deck.pop(i)
                    self.deck_msg = ""
                return
        # card collection (only within the scrollable viewport)
        top, bottom = self._deck_viewport()
        if top <= pos[1] <= bottom:
            for r, card in self._deck_grid():
                if r.collidepoint(pos):
                    if card.key in deck:
                        deck.remove(card.key)
                        self.deck_msg = ""
                    elif button == 1:
                        self._deck_add(card)
                    return

    def _deck_hover_card(self):
        mouse = pygame.mouse.get_pos()
        deck = self._active_deck()
        for i, r in enumerate(self._deck_slot_rects()):
            if r.collidepoint(mouse) and i < len(deck):
                return cards.CARDS[deck[i]]
        top, bottom = self._deck_viewport()
        if top <= mouse[1] <= bottom:
            for r, card in self._deck_grid():
                if r.collidepoint(mouse):
                    return card
        return None

    # ================================================================= RESULT
    def _result_buttons(self):
        cx, cy = cfg.WINDOW_W // 2, cfg.WINDOW_H // 2
        return [Button((cx - 132, cy + 40, 124, 36), "Play Again",
                       self._begin_battle),
                Button((cx + 8, cy + 40, 124, 36), "Main Menu",
                       lambda: self._goto("menu"))]

    def _result_click(self, pos):
        for b in self._result_buttons():
            if b.click(pos):
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
        self.music_btn.label = "Music: %s (M)" % ("On" if self.music_on else "Off")
        self.sfx_btn.label = "Sound: %s (N)" % ("On" if self.sfx_on else "Off")
        for b in self.menu_buttons:
            b.draw(self.screen, self.font_s if b in (self.music_btn, self.sfx_btn)
                   else self.font_m)
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

    LEVEL_COLORS = {1: (110, 200, 110), 2: (150, 200, 240), 3: (240, 200, 110),
                    4: (240, 150, 90), 5: (235, 110, 200)}

    @staticmethod
    def _elixir_color(v):
        if v < 0.999:
            return (120, 210, 130)        # AI handicapped
        if v <= 1.001:
            return (235, 235, 235)        # even
        if v < 1.5:
            return (245, 200, 100)
        return (245, 120, 110)

    def _draw_prematch(self):
        cx = cfg.WINDOW_W // 2
        mouse = pygame.mouse.get_pos()
        self._text("Battle Setup", self.font_l, (240, 220, 120), center=(cx, 24))

        # ---- AI intelligence: 5 big buttons ----
        info = cfg.AI_LEVELS[self.ai_level]
        self._text("AI Intelligence", self.font_m, cfg.COLOR_TEXT, topleft=(12, 48))
        self._text(info["name"], self.font_m, self.LEVEL_COLORS[self.ai_level],
                   topleft=(cfg.WINDOW_W - 12 - self.font_m.size(info["name"])[0], 48))
        for r, lv in self._prematch_level_rects():
            sel = lv == self.ai_level
            col = self.LEVEL_COLORS[lv]
            bg = dk_c(col, 120) if sel else (44, 50, 62)
            if r.collidepoint(mouse):
                bg = lt_c(bg, 18)
            pygame.draw.rect(self.screen, (16, 18, 26), r.move(0, 3), border_radius=9)
            pygame.draw.rect(self.screen, bg, r, border_radius=9)
            pygame.draw.rect(self.screen, col if sel else dk_c(col, 70), r,
                             3 if sel else 1, border_radius=9)
            self._text(str(lv), self.font_l, col if sel else (200, 200, 205),
                       center=(r.centerx, r.y + 19))
            name = cfg.AI_LEVELS[lv]["name"]
            self._text(self._fit(name, self.font_s, r.w - 4), self.font_s,
                       cfg.COLOR_TEXT, center=(r.centerx, r.bottom - 10))
        self._text(info["desc"], self.font_s, (200, 200, 200),
                   center=(cx, self.PM_LEVEL_Y + 66))

        # ---- AI elixir boost slider ----
        v = self.ai_elixir
        vcol = self._elixir_color(v)
        ly = self.PM_SLIDER_Y - 62
        self._text("AI Elixir", self.font_m, cfg.COLOR_TEXT, topleft=(12, ly + 4))
        val = self.font_xl.render("%.2fx" % v, True, vcol)
        self.screen.blit(val, (cfg.WINDOW_W - 12 - val.get_width(), ly - 8))
        bonus = (v - 1.0) * cfg.AI_START_BONUS_PER_MULT
        sub = ("even fight" if abs(v - 1.0) < 1e-6 else
               "regen x%.2f, start %+.1f" % (v, bonus))
        self._text(sub, self.font_s, (170, 178, 195), topleft=(12, ly + 26))
        t = self._slider_track()
        # track: green (handicap) -> white (even) -> red (boost)
        for i in range(t.w):
            f = i / max(t.w - 1, 1)
            vv = cfg.AI_ELIXIR_MULT_MIN + f * (cfg.AI_ELIXIR_MULT_MAX - cfg.AI_ELIXIR_MULT_MIN)
            c = dk_c(self._elixir_color(vv), 70)
            pygame.draw.line(self.screen, c, (t.x + i, t.y + 2), (t.x + i, t.bottom - 3))
        kx = int(self._slider_x_for(v))
        fill = pygame.Rect(t.x, t.y, max(0, kx - t.x), t.h)
        pygame.draw.rect(self.screen, (40, 44, 58), t, 2, border_radius=7)
        # ticks: every 0.05, bigger every 0.25, labels every 0.5
        nsteps = int(round((cfg.AI_ELIXIR_MULT_MAX - cfg.AI_ELIXIR_MULT_MIN)
                           / cfg.AI_ELIXIR_MULT_STEP))
        for i in range(nsteps + 1):
            tv = cfg.AI_ELIXIR_MULT_MIN + i * cfg.AI_ELIXIR_MULT_STEP
            x = int(self._slider_x_for(tv))
            big = abs((tv * 4) - round(tv * 4)) < 1e-6
            h = 7 if big else 3
            pygame.draw.line(self.screen, (150, 156, 175) if big else (90, 96, 115),
                             (x, t.bottom + 3), (x, t.bottom + 3 + h), 1)
            if abs(tv * 2 - round(tv * 2)) < 1e-6:
                self._text("%gx" % tv, self.font_s, (170, 178, 195),
                           center=(x, t.bottom + 18))
        # knob
        pygame.draw.circle(self.screen, (15, 18, 26), (kx, t.centery + 2), 15)
        pygame.draw.circle(self.screen, vcol, (kx, t.centery), 15)
        pygame.draw.circle(self.screen, (255, 255, 255) if self.slider_drag else dk_c(vcol, 80),
                           (kx, t.centery), 15, 3)
        # -/+ buttons
        for r, sym in zip(self._slider_pm_rects(), ("-", "+")):
            hov = r.collidepoint(mouse)
            pygame.draw.rect(self.screen, (15, 18, 26), r.move(0, 3), border_radius=10)
            pygame.draw.rect(self.screen, cfg.COLOR_BUTTON_HOVER if hov else cfg.COLOR_BUTTON,
                             r, border_radius=10)
            pygame.draw.rect(self.screen, (20, 24, 32), r, 2, border_radius=10)
            self._text(sym, self.font_l, cfg.COLOR_TEXT, center=(r.centerx, r.centery - 2))
        # presets
        for r, pv in self._slider_presets():
            sel = abs(pv - v) < 1e-6
            bg = (70, 90, 130) if sel else (40, 46, 60)
            if r.collidepoint(mouse):
                bg = lt_c(bg, 16)
            pygame.draw.rect(self.screen, bg, r, border_radius=7)
            pygame.draw.rect(self.screen, self._elixir_color(pv) if sel else (70, 78, 98),
                             r, 2 if sel else 1, border_radius=7)
            self._text("%gx" % pv, self.font_s, cfg.COLOR_TEXT, center=r.center)
        self._text("drag / click  |  -/+ or arrow keys / wheel = 0.05 steps",
                   self.font_s, (130, 138, 158), center=(cx, self.PM_SLIDER_Y + 74))

        # ---- decks ----
        self._deck_preview_panel(self.PM_SLIDER_Y + 88, "AI Deck:  " + self.ai_deck_choice,
                                 (240, 150, 150), self._ai_deck_preview_cards())
        self._deck_preview_panel(self.PM_SLIDER_Y + 198, "Your Deck", (150, 200, 240),
                                 self.player_deck)

        for b in self._prematch_buttons():
            b.draw(self.screen, self.font_m)

    def _deck_preview_panel(self, y, label, col, deck):
        """Framed strip showing an 8-card deck (None = random deck)."""
        panel = pygame.Rect(12, y, cfg.WINDOW_W - 24, 104)
        pygame.draw.rect(self.screen, (28, 32, 46), panel, border_radius=10)
        pygame.draw.rect(self.screen, dk_c(col, 60), panel, 1, border_radius=10)
        self._text(label, self.font_m, col, topleft=(panel.x + 10, y + 6))
        if deck is None:
            self._text("A different random 8-card deck each match.",
                       self.font_s, cfg.COLOR_TEXT, topleft=(panel.x + 10, y + 44))
            return
        if deck:
            avg = sum(cards.CARDS[k].elixir for k in deck) / len(deck)
            self._text("avg %.1f" % avg, self.font_s, (190, 190, 190),
                       topleft=(panel.right - 60, y + 9))
        if len(deck) != cfg.DECK_SIZE:
            self._text("Needs 8 cards - edit it first.", self.font_s,
                       (240, 180, 120), topleft=(panel.x + 10, y + 44))
            return
        sz = 38
        gap = (panel.w - 20 - sz * 8) // 7
        for i, k in enumerate(deck):
            x = panel.x + 10 + i * (sz + gap)
            self.screen.blit(sprites.get_sprite(k, sz), (x, y + 32))
            self._text(str(cards.CARDS[k].elixir), self.font_s, cfg.COLOR_ELIXIR,
                       center=(x + sz // 2, y + 82))

    def _draw_records(self):
        cx = cfg.WINDOW_W // 2
        self._text("Records", self.font_l, (240, 220, 120), center=(cx, 30))
        self._text("per AI intelligence level (any elixir boost)", self.font_s,
                   (170, 178, 195), center=(cx, 54))
        y = 74
        tot_w = tot_l = tot_cf = tot_ca = 0
        for lv in sorted(cfg.AI_LEVELS):
            col = self.LEVEL_COLORS[lv]
            rec = self.stats.get(self._level_key(lv), {})
            w, l, dr = rec.get("wins", 0), rec.get("losses", 0), rec.get("draws", 0)
            cf, ca = rec.get("cf", 0), rec.get("ca", 0)
            tot_w += w; tot_l += l; tot_cf += cf; tot_ca += ca
            games = w + l + dr
            panel = pygame.Rect(14, y, cfg.WINDOW_W - 28, 92)
            pygame.draw.rect(self.screen, (34, 38, 52), panel, border_radius=8)
            pygame.draw.rect(self.screen, col, panel, 1, border_radius=8)
            self._text("%d  %s" % (lv, cfg.AI_LEVELS[lv]["name"]), self.font_m, col,
                       topleft=(24, y + 8))
            wr = (w / games * 100) if games else 0
            self._text("%d-%d-%d   %.0f%% win" % (w, l, dr, wr), self.font_s,
                       cfg.COLOR_TEXT, topleft=(24, y + 32))
            best = rec.get("best", 0.0)
            self._text("best win vs %.2fx elixir   |   %d wins at 1.0x+"
                       % (best, rec.get("even_w", 0)) if w else "no wins yet",
                       self.font_s, (200, 200, 170), topleft=(24, y + 50))
            bx, by, bw = 24, y + 70, cfg.WINDOW_W - 28 - 20
            tot = max(cf + ca, 1)
            gw = int(bw * cf / tot)
            pygame.draw.rect(self.screen, (70, 40, 44), (bx, by, bw, 12), border_radius=6)
            if gw > 0:
                pygame.draw.rect(self.screen, (90, 200, 110), (bx, by, gw, 12),
                                 border_radius=6)
            self._text("%d" % cf, self.font_s, (150, 230, 160), topleft=(bx + 2, by - 1))
            self._text("%d" % ca, self.font_s, (240, 150, 150),
                       topleft=(bx + bw - 18, by - 1))
            y += 98
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
            "Champions (max 1 per deck): once deployed, the",
            "yellow button bottom-left fires their ability.",
            "",
            "Deck editor: click to add/remove, right-click",
            "to remove, mouse wheel or the bar to scroll.",
            "",
            "Elixir refills over time (max 10). It doubles",
            "in the last minute and triples in overtime.",
            "",
            "Battle Setup: pick the AI's intelligence (1-5)",
            "and its elixir boost (0.5x-2x, 1x = even).",
            "",
            "M = music on/off      N = sound on/off",
            "",
            "Click anywhere / Esc to return to the menu.",
        ]
        y = 90
        for ln in lines:
            self._text(ln, self.font_s, cfg.COLOR_TEXT, center=(cx, y))
            y += 22

    # --------------------------------------------------------- deck screen
    @staticmethod
    def _fit(text, font, maxw):
        """Shorten `text` with a trailing '.' until it fits in maxw pixels."""
        if font.size(text)[0] <= maxw:
            return text
        while len(text) > 2 and font.size(text + ".")[0] > maxw:
            text = text[:-1]
        return text.rstrip() + "."

    def _elixir_badge(self, x, y, cost, r=9):
        pygame.draw.circle(self.screen, dk_c(cfg.COLOR_ELIXIR, 50), (x + 1, y + 1), r)
        pygame.draw.circle(self.screen, cfg.COLOR_ELIXIR, (x, y), r)
        pygame.draw.circle(self.screen, lt_c(cfg.COLOR_ELIXIR, 60), (x, y), r, 1)
        self._text(str(cost), self.font_s, (255, 255, 255), center=(x, y))

    def _draw_deck(self):
        cx = cfg.WINDOW_W // 2
        deck = self._active_deck()
        mouse = pygame.mouse.get_pos()
        title = "Edit AI Deck" if self.deck_mode == "ai" else "Edit Your Deck"
        self._text(title, self.font_l, (240, 220, 120), center=(cx, 22))
        avg = (sum(cards.CARDS[k].elixir for k in deck) / len(deck) if deck else 0)
        full = len(deck) == cfg.DECK_SIZE
        self._text("%d/8 cards   |   avg elixir %.1f   |   %d available"
                   % (len(deck), avg, len(cards.DEPLOYABLE_CARDS)),
                   self.font_s, (150, 230, 150) if full else (170, 178, 195),
                   center=(cx, 45))

        # ---- your 8 cards: 2 rows x 4 big slots ----
        for i, r in enumerate(self._deck_slot_rects()):
            filled = i < len(deck)
            hover = r.collidepoint(mouse) and filled
            pygame.draw.rect(self.screen, (16, 18, 26), r.move(0, 3), border_radius=9)
            if not filled:
                pygame.draw.rect(self.screen, (30, 34, 44), r, border_radius=9)
                pygame.draw.rect(self.screen, (64, 72, 92), r, 1, border_radius=9)
                self._text("+", self.font_l, (64, 72, 92), center=r.center)
                continue
            card = cards.CARDS[deck[i]]
            bg = (92, 58, 58) if hover else ((78, 66, 40) if card.is_champion
                                             else (48, 58, 80))
            pygame.draw.rect(self.screen, bg, r, border_radius=9)
            pygame.draw.rect(self.screen, lt_c(bg, 14),
                             (r.x + 2, r.y + 2, r.w - 4, r.h // 2), border_radius=7)
            border = (245, 205, 85) if card.is_champion else (110, 124, 156)
            if hover:
                border = (240, 120, 120)
            pygame.draw.rect(self.screen, border, r, 2, border_radius=9)
            sz = self.SLOT_ICON
            self.screen.blit(sprites.get_sprite(card.key, sz),
                             (r.centerx - sz // 2, r.y + 3))
            self._elixir_badge(r.x + 11, r.y + 11, card.elixir)
            self._text(self._fit(card.name, self.font_s, r.w - 6), self.font_s,
                       cfg.COLOR_TEXT, center=(r.centerx, r.bottom - 10))
            if hover:   # "click to remove" mark
                xr = (r.right - 11, r.y + 11)
                pygame.draw.circle(self.screen, (200, 70, 70), xr, 8)
                pygame.draw.line(self.screen, (255, 255, 255), (xr[0] - 3, xr[1] - 3),
                                 (xr[0] + 3, xr[1] + 3), 2)
                pygame.draw.line(self.screen, (255, 255, 255), (xr[0] - 3, xr[1] + 3),
                                 (xr[0] + 3, xr[1] - 3), 2)

        # ---- info line: message > hovered card > controls hint ----
        top, bottom = self._deck_viewport()
        info_y = top - 17
        hc = self._deck_hover_card()
        if self.deck_msg:
            self._text(self.deck_msg, self.font_m, (240, 140, 140), center=(cx, info_y))
        elif hc is not None:
            if hc.category == "spell":
                stats = "Spell"
                if hc.spell_damage:
                    stats += "  |  dmg %d" % hc.spell_damage
            else:
                kind = "Champion" if hc.is_champion else hc.category.title()
                stats = "%s  |  HP %d  |  dmg %d" % (kind, hc.hp, hc.damage)
                if hc.count > 1:
                    stats += "  x%d" % hc.count
            if hc.is_champion:
                stats += "  |  " + hc.ability_name
            line = "%s (%d):  %s" % (hc.name, hc.elixir, stats)
            self._text(self._fit(line, self.font_s, cfg.WINDOW_W - 20), self.font_s,
                       (225, 225, 200), center=(cx, info_y))
        else:
            self._text("Click: add / remove    Right-click: remove    Wheel: scroll",
                       self.font_s, (150, 158, 178), center=(cx, info_y))
        pygame.draw.line(self.screen, (60, 66, 88), (12, top - 4),
                         (cfg.WINDOW_W - 12, top - 4), 1)

        # ---- card collection ----
        self.screen.set_clip(pygame.Rect(0, top, cfg.WINDOW_W, bottom - top))
        sz = self.DECK_ICON
        for r, card in self._deck_grid():
            if r.bottom < top or r.top > bottom:
                continue   # off-screen; skip
            in_deck = card.key in deck
            bg = (62, 104, 74) if in_deck else (44, 50, 62)
            if card.is_champion:   # gold-tinted cell + border for champions
                bg = (120, 100, 55) if in_deck else (74, 64, 40)
            if r.collidepoint(mouse) and top <= mouse[1] <= bottom:
                bg = lt_c(bg, 20)
            pygame.draw.rect(self.screen, bg, r, border_radius=7)
            if card.is_champion:
                pygame.draw.rect(self.screen, (245, 205, 85), r, 1, border_radius=7)
            elif in_deck:
                pygame.draw.rect(self.screen, (130, 220, 140), r, 2, border_radius=7)
            self.screen.blit(sprites.get_sprite(card.key, sz),
                             (r.centerx - sz // 2, r.y + 6))
            self._elixir_badge(r.x + 9, r.y + 9, card.elixir, r=8)
            if in_deck:            # check mark
                ck = (r.right - 9, r.y + 9)
                pygame.draw.circle(self.screen, (70, 170, 90), ck, 7)
                pygame.draw.lines(self.screen, (255, 255, 255), False,
                                  [(ck[0] - 3, ck[1]), (ck[0] - 1, ck[1] + 3),
                                   (ck[0] + 4, ck[1] - 3)], 2)
            self._text(self._fit(card.name, self.font_s, r.w - 4), self.font_s,
                       cfg.COLOR_TEXT, center=(r.centerx, r.bottom - 11))
        self.screen.set_clip(None)

        # ---- scrollbar (drag it, or use the mouse wheel) ----
        max_scroll = self._deck_max_scroll()
        if max_scroll > 0:
            track = self._deck_scrollbar_track()
            pygame.draw.rect(self.screen, (34, 38, 52), track.inflate(-4, 0),
                             border_radius=3)
            frac = track.h / (track.h + max_scroll)
            bar_h = max(30, int(track.h * frac))
            bar_y = track.y + int((track.h - bar_h) * self.deck_scroll / max_scroll)
            col = (170, 180, 210) if self.deck_drag else (110, 120, 145)
            pygame.draw.rect(self.screen, col, (track.x + 2, bar_y, track.w - 4, bar_h),
                             border_radius=3)
        for b in self._deck_buttons():
            b.draw(self.screen, self.font_s)

    # --------------------------------------------------------- match screen
    def _draw_match(self):
        self._draw_arena()
        m = self.match
        self.fx.draw_decals(self.screen)
        for e in m.entities:
            self._draw_entity(e)
        for fx in m.effects:
            self._draw_effect(fx)
        self._draw_beams()
        for p in m.projectiles:
            self._draw_projectile(p)
        self.fx.draw_particles(self.screen)
        self.fx.draw_flash(self.screen)
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
        dashing = e.dash is not None
        # dash streak (Bandit, Golden Knight, Guardian charge...)
        if dashing:
            sx, sy = tile_to_px(e.dash["sx"], e.dash["sy"])
            col = (255, 215, 90) if e.card.is_champion else self._team_color(e.team)
            streak = pygame.Surface((cfg.WINDOW_W, cfg.WINDOW_H), pygame.SRCALPHA)
            pygame.draw.line(streak, col + (90,), (sx, sy), (px, py), max(4, size // 3))
            self.screen.blit(streak, (0, 0))
        # airborne lift: Mega Knight jump arc, Hog Rider vaulting the river
        lift = 0
        if dashing and e.card.dash_damage:
            done = dist(e.dash["sx"], e.dash["sy"], e.x, e.y)
            left = dist(e.x, e.y, e.dash["tx"], e.dash["ty"])
            lift = int(math.sin(math.pi * done / max(done + left, 1e-6)) * 26)
        elif e.card.river_jump and RIVER_TOP <= e.y <= RIVER_BOTTOM:
            f = (e.y - RIVER_TOP) / max(RIVER_BOTTOM - RIVER_TOP, 1e-6)
            lift = int(math.sin(math.pi * f) * 14)
        if lift:
            sh = pygame.Surface((size, size // 3), pygame.SRCALPHA)
            pygame.draw.ellipse(sh, (0, 0, 0, 70), sh.get_rect())
            self.screen.blit(sh, (px - size // 2, py + size // 4))
        py -= lift
        # team ring (gold for champions)
        ring = (245, 205, 85) if e.card.is_champion else self._team_color(e.team)
        pygame.draw.circle(self.screen, ring, (int(px), int(py)), size // 2 + 2, 3)
        spr = sprites.get_sprite(sprites.unit_sprite_key(e.key), size)
        if cloaked or e.immune_timer > 0:
            spr = spr.copy()
            spr.set_alpha(110 if cloaked else 200)
        self.screen.blit(spr, (px - size // 2, py - size // 2))
        if e.immune_timer > 0 or (dashing and e.dash.get("immune")):   # shimmer
            pygame.draw.circle(self.screen, (180, 230, 255),
                               (int(px), int(py)), size // 2 + 4, 2)
        if e.protect_timer > 0:   # Monk's Pensive Protection: golden bubble
            pulse = 0.5 + 0.5 * math.sin(self._now() * 9)
            rr = size // 2 + 6
            bub = pygame.Surface((rr * 2 + 4, rr * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(bub, (255, 210, 110, 50), (rr + 2, rr + 2), rr)
            pygame.draw.circle(bub, (255, 225, 140, int(150 + 90 * pulse)),
                               (rr + 2, rr + 2), rr, 3)
            self.screen.blit(bub, (px - rr - 2, py - rr - 2))
        if e.card.is_champion:    # little gold crown above
            cyy = py - size // 2 - 6
            pygame.draw.polygon(self.screen, (245, 205, 85),
                                [(px - 6, cyy + 3), (px - 6, cyy - 2), (px - 3, cyy + 1),
                                 (px, cyy - 4), (px + 3, cyy + 1), (px + 6, cyy - 2),
                                 (px + 6, cyy + 3)])
        self._draw_hp_bar(e, px, py - size // 2 - 5, size)
        # ramp-up stage pips (Mighty Miner drill, Little Prince)
        if e.card.ramp_stages:
            n = len(e.card.ramp_stages)
            stage = e.ramp_stage() if e.ramp_time > 0 else -1
            y0 = int(py + size // 2 + 3)
            for i in range(n):
                xx = int(px - (n - 1) * 4 + i * 8)
                lit = i <= stage
                col = (255, 150, 50) if lit else (60, 60, 70)
                pygame.draw.circle(self.screen, col, (xx, y0), 3)
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
        if self.fx.draw_spell(self.screen, fx):
            return                       # spells have bespoke visuals (fx.py)
        px, py = tile_to_px(fx.x, fx.y)
        if fx.kind == "incoming":
            self._draw_incoming(fx, px, py)
            return
        if fx.kind == "blast":
            self._draw_blast(fx, px, py)
            return
        if fx.kind == "timed_bomb":
            self._draw_timed_bomb(fx, px, py)
            return
        if fx.kind in ("chain", "link"):
            # electric arcs between chained points (Electro units, Tesla beam,
            # Goblinstein's Lightning Link) - gold for Golden Knight's dash
            prog = min(1.0, fx.elapsed / fx.duration)
            alpha = 1.0 - prog if fx.kind == "chain" else 0.75 + 0.25 * math.sin(fx.elapsed * 20)
            col = CHAIN_COLORS.get(fx.card_key, (110, 205, 255))
            if len(fx.points) < 2:
                return
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

    def _draw_timed_bomb(self, fx, px, py):
        """Mighty Miner's dropped bomb: fuse sparks + countdown ring."""
        prog = min(1.0, fx.elapsed / fx.duration)
        rad = int(fx.radius * cfg.TILE_SIZE)
        surf = pygame.Surface((rad * 2 + 4, rad * 2 + 4), pygame.SRCALPHA)
        c = (rad + 2, rad + 2)
        pygame.draw.circle(surf, (255, 120, 60, 30 + int(50 * prog)), c, rad)
        pygame.draw.circle(surf, (255, 140, 70, 200), c, rad, 2)
        self.screen.blit(surf, (px - rad - 2, py - rad - 2))
        flash = int(prog * 10) % 2 == 0
        body = (70, 70, 82) if flash else (120, 60, 50)
        pygame.draw.circle(self.screen, (20, 20, 26), (int(px) + 1, int(py) + 2), 8)
        pygame.draw.circle(self.screen, body, (int(px), int(py)), 8)
        pygame.draw.circle(self.screen, (170, 170, 185), (int(px) - 3, int(py) - 3), 2)
        pygame.draw.line(self.screen, (150, 110, 70), (px + 4, py - 6), (px + 7, py - 11), 2)
        spark = 2 + int(2 * math.sin(self._now() * 30))
        pygame.draw.circle(self.screen, (255, 220, 90), (int(px) + 7, int(py) - 11), spark)

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
        used_up = champ.ability_uses <= 0
        if used_up:                        # one-shot ability already spent
            overlay = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            pygame.draw.circle(overlay, (0, 0, 0, 170), (rad, rad), rad)
            self.screen.blit(overlay, r.topleft)
            self._text("USED", self.font_s, (230, 230, 230), center=(cx, cy))
        # uses left (Boss Bandit has 2)
        if champ.card.ability_uses > 1:
            for k in range(champ.card.ability_uses):
                lit = k < champ.ability_uses
                pygame.draw.circle(self.screen, (255, 230, 120) if lit else (60, 60, 60),
                                   (cx - 5 + k * 10, r.bottom + 5), 4)
                pygame.draw.circle(self.screen, (20, 20, 20),
                                   (cx - 5 + k * 10, r.bottom + 5), 4, 1)
        # cooldown wedge (between uses)
        if champ.ability_cd > 0 and not used_up:
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
        label = self.font_s.render(champ.card.ability_name, True,
                                   (240, 230, 170) if not used_up else (150, 150, 150))
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
        panel = pygame.Rect(cx - 150, cy - 92, 300, 190)
        pygame.draw.rect(self.screen, (28, 32, 46), panel, border_radius=14)
        pygame.draw.rect(self.screen, color, panel, 2, border_radius=14)
        self._text(self.result_text, self.font_xl, color, center=(cx, cy - 46))
        self._crown_icon(cx - 62, cy + 4, cfg.COLOR_TEAM_PLAYER)
        self._crown_icon(cx + 62, cy + 4, cfg.COLOR_TEAM_ENEMY)
        self._text("%d  -  %d" % (self.match.crowns[PLAYER], self.match.crowns[ENEMY]),
                   self.font_l, cfg.COLOR_TEXT, center=(cx, cy + 4))
        for b in self._result_buttons():
            b.draw(self.screen, self.font_m)
