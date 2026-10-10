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
import levels
import profile_data
from engine import (Match, PLAYER, ENEMY, RIVER_TOP, RIVER_BOTTOM,
                    BRIDGE_X, RIVER_CENTER, dist)
from ai import AIController
from screens import ScreensMixin
from modes import ModesMixin
from ui import (dk_c, lt_c, tile_to_px, px_to_tile, WHITE, render_text,
                grad_rect, BUTTON_STYLES, Button)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECK_FILE = os.path.join(_ROOT, "player_deck.json")
AI_DECK_FILE = os.path.join(_ROOT, "ai_custom_deck.json")
STATS_FILE = os.path.join(_ROOT, "records.json")
SETTINGS_FILE = os.path.join(_ROOT, "settings.json")
PROGRESS_FILE = os.path.join(_ROOT, "progress.json")
LEVEL_DECK_FILE = os.path.join(_ROOT, "level_deck.json")

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


class Game(ModesMixin, ScreensMixin):
    def __init__(self):
        try:
            pygame.mixer.pre_init(sounds.SR, -16, 2, 512)
        except Exception:
            pass
        pygame.init()
        pygame.display.set_caption("Clash Clone - Singleplayer")
        try:
            # SCALED + RESIZABLE: drag the window smaller on small screens and
            # the whole game scales with it (mouse clicks map automatically)
            self.screen = pygame.display.set_mode(
                (cfg.WINDOW_W, cfg.WINDOW_H), pygame.SCALED | pygame.RESIZABLE)
        except pygame.error:
            self.screen = pygame.display.set_mode((cfg.WINDOW_W, cfg.WINDOW_H))
        self.clock = pygame.time.Clock()
        sprites.ensure_sprites()

        self.font_s = pygame.font.SysFont("arial", 13)
        self.font_sb = pygame.font.SysFont("arial", 14, bold=True)
        self.font_m = pygame.font.SysFont("arial", 19, bold=True)
        self.font_l = pygame.font.SysFont("arial", 32, bold=True)
        self.font_xl = pygame.font.SysFont("arial", 46, bold=True)
        self.font_title = pygame.font.SysFont("arial", 50, bold=True)

        # music & sound effects (rendered once into assets/sounds)
        sounds.ensure_sounds(progress=self._loading_screen)
        self.sfx = sounds.SoundManager(cfg.MUSIC_VOLUME, cfg.SFX_VOLUME)
        Button.click_sound = lambda: self.sfx.play("ui_click", 0.6, min_gap=0.02)
        self.music_on = True
        self.sfx_on = True
        self._audio = {}
        self.fx = fxmod.FX()
        self._arena_surf = None
        self.level_run = None          # LevelRun while playing a level
        self.level_key = None
        self.levels_scroll = 0         # Levels screen list scroll (pixels)
        self.levels_drag = None        # (mouse_y, scroll) while dragging the list
        self.progress = self._load_progress()
        self.profile = profile_data.Profile()
        self.sandbox = False           # Settings: unlock everything (free play)
        self.ai_card_mode = "ladder"   # Battles: AI card level "ladder" | "match"
        self.last_rewards = []         # [(label, gold, shards)] for the result screen

        self.state = "menu"
        self.running = True

        self.player_deck = self._load_deck()
        # saved deck slots (profile.json); slot 1 starts as your old deck
        pr = self.profile
        if not pr.decks:
            pr.decks = [{"name": "Deck %d" % (i + 1),
                         "cards": list(self.player_deck if i == 0 else cards.DEFAULT_PLAYER_DECK)}
                        for i in range(profile_data.DECK_SLOTS)]
            pr.active_slot = 0
        while len(pr.decks) < profile_data.DECK_SLOTS:
            pr.decks.append({"name": "Deck %d" % (len(pr.decks) + 1),
                             "cards": list(cards.DEFAULT_PLAYER_DECK)})
        pr.active_slot = max(0, min(pr.active_slot, profile_data.DECK_SLOTS - 1))
        for d in pr.decks:
            d["cards"] = [k for k in d.get("cards", []) if k in cards.CARDS][:cfg.DECK_SIZE]
        self.player_deck = pr.decks[pr.active_slot]["cards"]
        self.drag_card = None          # hand index being dragged (drag to deploy)
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
        self._load_extra_settings({})
        self._load_settings()
        self._apply_settings()
        self.sfx.set_music_on(self.music_on)
        self.sfx.set_sfx_on(self.sfx_on)
        self.mode = None               # special mode key (modes.py) or None
        self.ai_custom_deck = self._load_deck(AI_DECK_FILE, cards.DEFAULT_AI_DECK)
        self.level_deck = self._load_deck(LEVEL_DECK_FILE,
                                          levels.default_level_deck(self.player_deck))
        if levels.banned_in(self.level_deck):         # never keep a banned card
            self.level_deck = levels.default_level_deck(self.level_deck)
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

    def _select_deck_slot(self, i):
        """Switch the battle deck to saved slot i."""
        pr = self.profile
        pr.decks[pr.active_slot]["cards"] = list(self.player_deck)
        pr.active_slot = i
        self.player_deck = pr.decks[i]["cards"]
        if self.state == "deck" and self.deck_mode == "player":
            self.deck_backup = list(self.player_deck)
        pr.save()

    def _save_deck(self):
        if self.deck_mode == "player":
            self.profile.decks[self.profile.active_slot]["cards"] = list(self.player_deck)
            self.profile.save()
        path = {"ai": AI_DECK_FILE, "level": LEVEL_DECK_FILE}.get(self.deck_mode, DECK_FILE)
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
            self.sandbox = bool(d.get("sandbox", False))
            if d.get("ai_card_mode") in ("ladder", "match"):
                self.ai_card_mode = d["ai_card_mode"]
            self._load_extra_settings(d)
        except Exception:
            pass

    def _save_settings(self):
        try:
            with open(SETTINGS_FILE, "w") as f:
                d = {"ai_level": self.ai_level, "ai_elixir": self.ai_elixir,
                     "ai_deck": self.ai_deck_choice,
                     "music": self.music_on, "sfx": self.sfx_on,
                     "sandbox": self.sandbox, "ai_card_mode": self.ai_card_mode}
                d.update(self._extra_settings())
                json.dump(d, f)
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
        if self.deck_mode == "level":
            return self.level_deck
        return self.ai_custom_deck if self.deck_mode == "ai" else self.player_deck

    def _set_active_deck(self, d):
        if self.deck_mode == "ai":
            self.ai_custom_deck = d
        elif self.deck_mode == "level":
            self.level_deck = d
        else:
            self.player_deck = d
            self.profile.decks[self.profile.active_slot]["cards"] = d

    # -------------------------------------------------------------- menu
    def _build_menu_buttons(self):
        cx = cfg.WINDOW_W // 2
        w, h = 300, 46
        big = [
            ("Battle", self._open_prematch, "go"),
            ("Levels", lambda: self._goto("levels"), "gold"),
            ("Special Modes", lambda: self._open_modes(), "gold"),
        ]
        self.menu_buttons = [
            Button((cx - w // 2, 244 + i * 54, w, h), lbl, cb, style)
            for i, (lbl, cb, style) in enumerate(big)
        ]
        small = [
            ("Cards", lambda: self._open_cards("menu")),
            ("Decks", lambda: self._open_player_deck("menu")),
            ("AI Deck", lambda: self._open_aideck("menu")),
            ("Records", lambda: self._goto("records")),
            ("Settings", lambda: self._open_settings()),
            ("How To Play", lambda: self._goto("help")),
        ]
        hw = (w - 8) // 2
        for i, (lbl, cb) in enumerate(small):
            r, c = divmod(i, 2)
            self.menu_buttons.append(Button((cx - w // 2 + c * (hw + 8), 412 + r * 48, hw, 40),
                                            lbl, cb, "primary"))
        self.menu_buttons.append(Button((cx - w // 2, 560, w, 40), "Quit", self._quit,
                                        "danger"))
        # sound toggles (top corners); labels refreshed every frame
        self.music_btn = Button((10, 10, 118, 30), "Music", lambda: self._toggle_music(),
                                "dark")
        self.sfx_btn = Button((cfg.WINDOW_W - 128, 10, 118, 30), "Sound",
                              lambda: self._toggle_sfx(), "dark")
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
        if state == "levels" and self.state != "levels":
            # open the list at the first level you haven't cleared yet
            first = next((i for i, lv in enumerate(levels.LEVELS)
                          if not self.progress.get(lv.key, {}).get("stars")
                          and self._level_unlocked(i)), 0)
            self._set_levels_scroll(first * self.LEVEL_ROW - self.LEVEL_ROW // 2)
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
        self._arena_surf = None
        self.level_run = None
        self.mode = None
        ai_lv = self._ai_card_level()
        ai_deck = self._resolve_ai_deck()
        self.match = Match(self.player_deck, ai_deck,
                           **self._match_specials(self.player_deck, ai_deck),
                           card_levels={PLAYER: self.profile.deck_levels(self.player_deck),
                                        ENEMY: ai_lv},
                           tower_levels={PLAYER: self.profile.tower_level(self.player_deck),
                                         ENEMY: ai_lv})
        self.match.record_events = True
        self.ai = AIController(self.match, team=ENEMY, level=self.ai_level)
        self._audio = {}
        self.fx.clear()
        self.sfx.play("match_start", 0.9, min_gap=0.0)
        self.selected = None
        self.state = "match"

    def _special_cards(self, deck, owned=True, n_evo=None, n_hero=None):
        """(evo card keys, hero card keys) a deck brings: Evolutions in deck
        slots 1-2 and a Hero in slot 3 - your unlocked ones, or (AI) up to
        n_evo / n_hero of whatever its deck has there."""
        import evos
        ev, he = [], []
        for i, k in enumerate(deck[:evos.EVO_SLOTS]):
            if k in evos.EVOS and (self._evo_owned(k) if owned else True):
                ev.append(k)
        if len(deck) > evos.HERO_SLOT:
            k = deck[evos.HERO_SLOT]
            if k in evos.HEROES and (self._hero_owned(k) if owned else True):
                he.append(k)
        if n_evo is not None:
            ev = ev[:n_evo]
        if n_hero is not None:
            he = he[:n_hero]
        return ev, he

    def _match_specials(self, player_deck, ai_deck=None):
        pe, ph = self._special_cards(player_deck)
        out = {"evo_cards": {PLAYER: pe}, "hero_cards": {PLAYER: ph}}
        if ai_deck is not None:
            # fairness: the AI brings as many Evolutions / Heroes as you do
            ae, ah = self._special_cards(ai_deck, owned=False, n_evo=len(pe),
                                         n_hero=len(ph))
            out["evo_cards"][ENEMY] = ae
            out["hero_cards"][ENEMY] = ah
        return out

    def _ai_card_level(self):
        """AI card level in Battles: its ladder level vs this intelligence,
        or (Battle Setup option) the same level as your towers."""
        if self.ai_card_mode == "match":
            return self.profile.tower_level(self.player_deck)
        return self.profile.ladder_level(self.ai_level)

    # ---- Levels ----
    def _total_stars(self):
        return sum(self.progress.get(lv.key, {}).get("stars", 0) for lv in levels.LEVELS)

    def _level_unlocked(self, i):
        return self.sandbox or self._total_stars() >= levels.stars_needed(i)

    def _load_progress(self):
        try:
            with open(PROGRESS_FILE) as f:
                d = json.load(f)
            return d if isinstance(d, dict) else {}
        except Exception:
            return {}

    def _save_progress(self):
        try:
            with open(PROGRESS_FILE, "w") as f:
                json.dump(self.progress, f, indent=1)
        except Exception:
            pass

    def _begin_level(self, key):
        lv = levels.LEVELS_BY_KEY.get(key)
        if lv is None or lv.locked or not self._level_unlocked(levels.LEVELS.index(lv)):
            return
        if len(self.level_deck) != cfg.DECK_SIZE or levels.banned_in(self.level_deck):
            self._open_deck_editor("level", "levels")
            self.deck_msg = "Your Level Deck needs 8 cards (no win conditions)."
            return
        self._arena_surf = None
        self.level_key = key
        self.mode = None
        ev, he = self._special_cards(self.level_deck)
        self.match, self.level_run = levels.new_level_match(
            lv, self.level_deck, self.profile.deck_levels(self.level_deck),
            self.profile.tower_level(self.level_deck), ev, he)
        self.match.record_events = True
        self.ai = None
        self.selected = None
        self._audio = {}
        self.fx.clear()
        self.state = "match"
        self.sfx.play("match_start", 0.9, min_gap=0.0)

    def _retry(self):
        if self.level_run is not None and self.level_key:
            self._begin_level(self.level_key)
        else:
            self._begin_battle()

    # ---- Levels list (scrolls: wheel, drag, arrow keys, scrollbar) ----
    LEVEL_ROW = 120          # card height + gap

    def _levels_view(self):
        return pygame.Rect(0, 74, cfg.WINDOW_W, cfg.WINDOW_H - 150 - 74)

    def _levels_max_scroll(self):
        return max(0, len(levels.LEVELS) * self.LEVEL_ROW + 8 - self._levels_view().h)

    def _set_levels_scroll(self, v):
        self.levels_scroll = int(min(max(0, v), self._levels_max_scroll()))

    def _level_buttons(self):
        out = []
        view = self._levels_view()
        for i, lv in enumerate(levels.LEVELS):
            r = self._level_card_rect(i)
            open_ = not lv.locked and self._level_unlocked(i)
            b = Button((r.right - 96, r.bottom - 42, 86, 34),
                       "Play" if open_ else "Locked",
                       (lambda k=lv.key: self._begin_level(k)), "go")
            # only clickable while (fully) scrolled into view
            b.enabled = open_ and view.contains(b.rect)
            b.level_index = i
            out.append(b)
        y = cfg.WINDOW_H - 60
        bw = (cfg.WINDOW_W - 44) // 2
        out.append(Button((16, y, bw, 42), "Edit Level Deck",
                          lambda: self._open_deck_editor("level", "levels")))
        out.append(Button((cfg.WINDOW_W - 16 - bw, y, bw, 42), "Main Menu",
                          lambda: self._goto("menu"), "dark"))
        return out

    def _level_card_rect(self, i):
        v = self._levels_view()
        return pygame.Rect(14, v.y + 6 + i * self.LEVEL_ROW - self.levels_scroll,
                           cfg.WINDOW_W - 40, self.LEVEL_ROW - 8)

    def _levels_scrollbar(self):
        """(track rect, thumb rect) of the list's scrollbar."""
        v = self._levels_view()
        track = pygame.Rect(cfg.WINDOW_W - 18, v.y + 6, 8, v.h - 12)
        total = len(levels.LEVELS) * self.LEVEL_ROW + 8
        th = max(30, int(track.h * v.h / max(total, 1)))
        mx = self._levels_max_scroll()
        ty = track.y + int((track.h - th) * (self.levels_scroll / mx if mx else 0))
        return track, pygame.Rect(track.x, ty, track.w, th)

    def _levels_click(self, pos):
        for b in self._level_buttons():
            if b.click(pos):
                return
        track, thumb = self._levels_scrollbar()
        if track.inflate(12, 0).collidepoint(pos):
            if not thumb.collidepoint(pos):     # jump so the thumb centres here
                frac = (pos[1] - track.y - thumb.h / 2) / max(track.h - thumb.h, 1)
                self._set_levels_scroll(frac * self._levels_max_scroll())
            self.levels_drag = ("bar", pos[1], self.levels_scroll)
        elif self._levels_view().collidepoint(pos):
            self.levels_drag = ("list", pos[1], self.levels_scroll)

    def _levels_drag_to(self, y):
        kind, y0, s0 = self.levels_drag
        if kind == "bar":
            track, thumb = self._levels_scrollbar()
            k = self._levels_max_scroll() / max(track.h - thumb.h, 1)
            self._set_levels_scroll(s0 + (y - y0) * k)
        else:
            self._set_levels_scroll(s0 - (y - y0))

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
            mdt = dt * self.opt_speed           # Settings > Game speed
            if self.state == "match" and self.match and not self.match.finished:
                self.match.update(mdt)
                if self.ai is not None:
                    self.ai.update(mdt)
                if self.level_run is not None:
                    self.level_run.update(mdt)
                if self.match.finished:
                    self._on_match_end()
            self._update_audio(dt)
            if self.state in ("match", "result") and self.match is not None:
                self.fx.update(mdt, self.match)
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
            if self.level_run is not None:
                w = self.level_run.current_wave()
                final = w is not None and w.boss
            else:
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
                if ev.get("evo"):
                    self.sfx.play("evo_deploy", 0.8, pan, min_gap=0.0)
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
                hero = any(e.hero and e.key == key for e in self.match.entities)
                self.sfx.play("hero_ability" if hero else "ability", 1.0, pan, min_gap=0.0)
            elif kind == "dash":
                self.sfx.play("dash", 0.6, pan)
            elif kind == "wave":
                self.sfx.play("overtime" if key == "boss" else "match_start", 0.9,
                              min_gap=0.0)
            elif kind == "portal":
                self.sfx.play("portal", 0.6, pan, min_gap=0.15)
            elif kind == "land" and ev.get("slam"):
                self.sfx.play("slam", 0.85, pan)
            elif kind == "elixir_made":
                if mine:
                    self.sfx.play("elixir_pop", 0.6, pan, min_gap=0.1)
                for e in self.match.entities:
                    if e.key == key and abs(e.x - ev["x"]) < 0.01 and abs(e.y - ev["y"]) < 0.01:
                        e._gen_t = self.match.elapsed
        self.fx.handle_events(evs, self.match)

    def _on_match_end(self):
        w = self.match.winner
        if self.mode == "endless":
            self.result_text = "GAME OVER"
            self.last_rewards = []
            self._mode_rewards(w)
            self.profile.save()
            self._handle_events(self.match.take_events())
            self.sfx.music(None)
            self.sfx.play("defeat", 1.0, min_gap=0.0)
            self.state = "result"
            return
        if self.level_run is not None:
            run = self.level_run
            self.result_text = "VICTORY!" if w == PLAYER else "DEFEAT"
            rec = self.progress.setdefault(self.level_key, {"stars": 0, "wins": 0,
                                                            "plays": 0})
            rec["plays"] = rec.get("plays", 0) + 1
            before = self._total_stars()
            old_stars = rec.get("stars", 0)
            self.last_rewards = []
            if w == PLAYER:
                rec["wins"] = rec.get("wins", 0) + 1
                rec["stars"] = max(old_stars, run.stars())
                n = levels.LEVELS.index(run.level) + 1
                new_stars = rec["stars"] - old_stars
                self._reward("Victory", profile_data.level_win_gold(n))
                if new_stars:
                    self._reward("%d new star%s" % (new_stars, "s" * (new_stars > 1)),
                                 new_stars * profile_data.level_star_gold(n))
                if old_stars == 0:
                    self._reward("First clear", 0, 1)
                if rec["stars"] == 3 and old_stars < 3:
                    self._reward("3 stars", 0, 1)
                opened = [lv.name for i, lv in enumerate(levels.LEVELS)
                          if levels.stars_needed(i) > before
                          and levels.stars_needed(i) <= self._total_stars()]
                for nm in opened:
                    self.last_rewards.append(("Unlocked: " + nm, 0, 0))
            self._save_progress()
            self.profile.save()
            self._handle_events(self.match.take_events())
            self.sfx.music(None)
            self.sfx.play("victory" if w == PLAYER else "defeat", 1.0, min_gap=0.0)
            self.state = "result"
            return
        if w == PLAYER:
            self.result_text = "VICTORY!"
        elif w == ENEMY:
            self.result_text = "DEFEAT"
        else:
            self.result_text = "DRAW"
        self.last_rewards = []
        if self.mode is not None:
            self._mode_rewards(w)
        else:
            m = self.match
            self._reward("Victory" if w == PLAYER else "Played",
                         profile_data.battle_gold(w == PLAYER, self.ai_level,
                                                  self.ai_elixir, m.crowns[PLAYER]))
            if w == PLAYER:
                before = self.profile.ladder_level(self.ai_level)
                self.profile.add_ladder_win(self.ai_level)
                got = self.profile.add_shard_points(self.ai_level)
                if got:
                    self.last_rewards.append(("Shard from wins", 0, got))
                if self.profile.ladder_level(self.ai_level) > before:
                    self.last_rewards.append(("AI %s is now Lv %d" % (
                        cfg.AI_LEVELS[self.ai_level]["name"],
                        self.profile.ladder_level(self.ai_level)), 0, 0))
        self.profile.save()
        self._handle_events(self.match.take_events())
        self.sfx.music(None)
        self.sfx.play("victory" if w == PLAYER else "defeat", 1.0, min_gap=0.0)
        self._record_result()
        self.state = "result"

    def _reward(self, label, gold=0, shards=0):
        self.profile.add(gold, shards)
        self.last_rewards.append((label, gold, shards))

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
                elif self.state == "levels" and e.key in (pygame.K_UP, pygame.K_DOWN,
                                                          pygame.K_PAGEUP, pygame.K_PAGEDOWN):
                    step = {pygame.K_UP: -60, pygame.K_DOWN: 60,
                            pygame.K_PAGEUP: -360, pygame.K_PAGEDOWN: 360}[e.key]
                    self._set_levels_scroll(self.levels_scroll + step)
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
                    elif self.state in ("help", "result", "prematch", "records",
                                        "levels"):
                        self.state = "menu"
                    elif self.state in self.EXTRA_SCREENS:
                        self._extra_escape()
            elif e.type == pygame.MOUSEWHEEL:
                # the wheel ONLY scrolls - it never selects anything
                if self.state == "deck":
                    self._deck_set_scroll(self.deck_scroll - e.y * 48)
                elif self.state == "levels":
                    self._set_levels_scroll(self.levels_scroll - e.y * 60)
                elif self.state in self.EXTRA_SCREENS:
                    self._extra_wheel(e.y)
                elif self.state == "prematch":
                    mpos = pygame.mouse.get_pos()
                    if self._slider_zone().collidepoint(mpos):
                        self._set_ai_elixir(self.ai_elixir + (1 if e.y > 0 else -1)
                                            * cfg.AI_ELIXIR_MULT_STEP)
            elif e.type == pygame.MOUSEBUTTONUP:
                if e.button == 1:
                    self.deck_drag = False
                    self.levels_drag = None
                    self._extra_mouseup(e.pos)
                    if self.drag_card is not None:
                        i, self.drag_card = self.drag_card, None
                        if (self.state == "match" and self.selected == i
                                and e.pos[1] < cfg.ARENA_Y0 + cfg.ARENA_PX_H
                                and e.pos[1] > cfg.ARENA_Y0):
                            tx, ty = px_to_tile(*e.pos)
                            if self.match.play_card(PLAYER, i, tx, ty):
                                self.selected = None
                            else:
                                self.sfx.play("ui_invalid", 0.6)
                    if self.slider_drag:
                        self.slider_drag = False
                        self._save_settings()
            elif e.type == pygame.MOUSEMOTION:
                if self.state == "deck" and self.deck_drag:
                    self._deck_drag_to(e.pos[1])
                elif self.state == "levels" and self.levels_drag:
                    self._levels_drag_to(e.pos[1])
                elif self.state in self.EXTRA_SCREENS:
                    self._extra_motion(e.pos)
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
                elif self.state == "levels":
                    self._levels_click(e.pos)
                elif self.state in self.EXTRA_SCREENS:
                    getattr(self, "_" + self.state + "_click")(e.pos)
                elif self.state == "help":
                    self.state = "menu"
                elif self.state == "records":
                    self.state = "menu"
                elif self.state == "result":
                    self._result_click(e.pos)
                elif self.state == "match":
                    self._match_click(e.pos, e.button)

    # ================================================================= MATCH INPUT
    NEXT_BOX_W = 60   # reserved width for the "Next:" preview on the right

    def _hand_slot_rects(self):
        n = cfg.HAND_SIZE
        slot_w = 72
        gap = 8
        total = n * slot_w + (n - 1) * gap
        # center the hand in the space left of the Next box, with real margins
        x0 = (cfg.WINDOW_W - self.NEXT_BOX_W - 12 - total) // 2
        x0 = max(10, x0)
        y0 = cfg.HUD_Y + 28
        return [pygame.Rect(x0 + i * (slot_w + gap), y0, slot_w, 88)
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
        # hero ability button (bottom-right)
        h, hready, hcost = self.match.hero_status(PLAYER)
        if h is not None and self._hero_btn_rect().collidepoint(pos):
            if not self.match.activate_hero(PLAYER):
                self.sfx.play("ui_invalid", 0.6)
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
                    if self.opt_drag_deploy:
                        self.drag_card = i       # release over the arena to play
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
    PM_LEVEL_Y = 104        # intelligence buttons
    PM_SLIDER_Y = 262       # elixir slider centre line

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
            Button((16, cfg.WINDOW_H - 182, bw, 44), "Change AI Deck",
                   lambda: self._open_aideck("prematch")),
            Button((cfg.WINDOW_W - 16 - bw, cfg.WINDOW_H - 182, bw, 44),
                   "Edit My Deck", lambda: self._open_player_deck("prematch")),
            Button((16, cfg.WINDOW_H - 126, cfg.WINDOW_W - 32, 54),
                   "Start Battle!", self._begin_battle, "go"),
            Button((cx - 70, cfg.WINDOW_H - 60, 140, 40), "Back",
                   lambda: self._goto("menu"), "dark"),
        ]

    def _slot_tag(self, i, key):
        """('EVO'|'HERO', colour) if deck slot i makes this card special."""
        import evos
        if i < evos.EVO_SLOTS and key in evos.EVOS and (
                self.deck_mode == "ai" or self._evo_owned(key)):
            return ("EVO", (190, 110, 255))
        if i == evos.HERO_SLOT and key in evos.HEROES and (
                self.deck_mode == "ai" or self._hero_owned(key)):
            return ("HERO", (255, 196, 80))
        return None

    def _deck_card_level(self, k, deck):
        if deck is self.player_deck or deck is self.level_deck:
            return self.profile.level(k)
        return self._ai_card_level()

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
        for r, mode, _ in self._prematch_cardlv_rects():
            if r.collidepoint(pos):
                self.ai_card_mode = mode
                self._save_settings()
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
        h, gap_y, top = 34, 7, 80
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
        self._screen_title("AI Deck", 30, "Pick the deck the AI will play")
        rects = self._aideck_preset_rects()
        for r, name in rects:
            sel = (self.ai_deck_choice == name)
            bg = (64, 98, 150) if sel else (48, 54, 70)
            if r.collidepoint(mouse):
                bg = lt_c(bg, 18)
            pygame.draw.rect(self.screen, (10, 12, 18), r.move(0, 3), border_radius=8)
            self.screen.blit(grad_rect(r.w, r.h, lt_c(bg, 16), bg, 8), r.topleft)
            pygame.draw.rect(self.screen, (250, 222, 110) if sel else (20, 24, 34), r,
                             2, border_radius=8)
            self._text(name, self.font_sb, center=r.center, outline=True)

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
            b.draw(self.screen, self.font_sb)

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
        top = 76
        return [pygame.Rect(m + (i % 4) * (w + gap), top + (i // 4) * (h + gap), w, h)
                for i in range(cfg.DECK_SIZE)]

    def _deck_tab_rects(self):
        """Saved deck slots 1-5 (battle deck only)."""
        if self.deck_mode != "player":
            return []
        w, gap = 34, 5
        x0 = cfg.WINDOW_W - 12 - profile_data.DECK_SLOTS * (w + gap) + gap
        return [(pygame.Rect(x0 + i * (w + gap), 8, w, 30), i)
                for i in range(profile_data.DECK_SLOTS)]

    def _deck_arrow_rects(self, r):
        return (pygame.Rect(r.x + 1, r.centery - 12, 15, 24),
                pygame.Rect(r.right - 16, r.centery - 12, 15, 24))

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
        if self.deck_mode == "level":
            d = levels.default_level_deck(self.player_deck)
        else:
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
        if self.deck_mode == "level" and card.key in levels.BANNED:
            self.deck_msg = "Win conditions can't be used in Levels."
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
        for r, i in self._deck_tab_rects():
            if r.collidepoint(pos):
                self._select_deck_slot(i)
                self.deck_msg = "Deck %d" % (i + 1)
                return
        # your 8 cards: arrows move a card, otherwise either button removes
        for i, r in enumerate(self._deck_slot_rects()):
            if r.collidepoint(pos):
                if i < len(deck):
                    left, right = self._deck_arrow_rects(r)
                    if button == 1 and left.collidepoint(pos) and i > 0:
                        deck[i - 1], deck[i] = deck[i], deck[i - 1]
                    elif button == 1 and right.collidepoint(pos) and i < len(deck) - 1:
                        deck[i + 1], deck[i] = deck[i], deck[i + 1]
                    else:
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
    def _result_panel(self):
        cx, cy = cfg.WINDOW_W // 2, cfg.WINDOW_H // 2
        h = 250 + 22 * len(self.last_rewards)
        return pygame.Rect(cx - 175, cy - h // 2 - 20, 350, h)

    def _result_buttons(self):
        cx = cfg.WINDOW_W // 2
        p = self._result_panel()
        y = p.bottom - 96
        out = []
        if self.level_run is not None and self.mode is None:
            out += [Button((cx - 150, y, 145, 40), "Retry", self._retry, "go"),
                    Button((cx + 5, y, 145, 40), "Levels", lambda: self._goto("levels"))]
        elif self.mode is not None:
            out += [Button((cx - 150, y, 145, 40), "Play Again", self._mode_again, "go"),
                    Button((cx + 5, y, 145, 40), "Modes", lambda: self._open_modes())]
        else:
            out += [Button((cx - 150, y, 145, 40), "Play Again", self._begin_battle, "go"),
                    Button((cx + 5, y, 145, 40), "Main Menu", lambda: self._goto("menu"))]
        out += [Button((cx - 150, y + 48, 145, 36), "Match Stats",
                       lambda: self._goto("stats"), "dark"),
                Button((cx + 5, y + 48, 145, 36), "Cards",
                       lambda: self._open_cards("result"), "dark")]
        return out

    def _result_click(self, pos):
        for b in self._result_buttons():
            if b.click(pos):
                return

    # ================================================================= DRAW
    def _draw(self):
        if self.state not in ("match", "result", "menu"):
            self._menu_backdrop(floating=False)
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
        elif self.state == "levels":
            self._draw_levels()
        elif self.state in self.EXTRA_SCREENS:
            getattr(self, "_draw_" + self.state)()
        elif self.state in ("match", "result"):
            self._draw_match()
            if self.state == "result":
                self._draw_result()

    def _text(self, s, font, color=None, center=None, topleft=None, outline=None):
        """Draw text. Bigger fonts default to WHITE with a thin black
        outline; small text stays plain."""
        big = font is not self.font_s
        if color is None:
            color = WHITE
        if outline is None:
            outline = big
        t = render_text(font, s, color, outline)
        if center:
            self.screen.blit(t, (center[0] - t.get_width() // 2,
                                 center[1] - t.get_height() // 2))
        else:
            self.screen.blit(t, topleft)
        return t

    def _menu_backdrop(self, floating=True):
        """Shared menu background: gradient, drifting cards, vignette."""
        t = self._now()
        self.screen.blit(self.bg_grad, (0, 0))
        if floating:
            for fc in self.menu_float:
                y = (fc["y0"] - t * fc["spd"]) % (cfg.WINDOW_H + 60) - 50
                x = fc["x"] + math.sin(t * fc["sway"] + fc["ph"]) * 12
                spr = sprites.get_sprite(fc["key"], fc["size"]).copy()
                spr.set_alpha(55)
                self.screen.blit(spr, (x, y))
        vig = getattr(self, "_vignette", None)
        if vig is None:
            vig = pygame.Surface((cfg.WINDOW_W, cfg.WINDOW_H), pygame.SRCALPHA)
            for i in range(28):
                a = int(5 * (28 - i) / 28 * 7)
                pygame.draw.rect(vig, (0, 0, 0, a),
                                 (i * 2, i * 2, cfg.WINDOW_W - i * 4, cfg.WINDOW_H - i * 4),
                                 2, border_radius=24)
            self._vignette = vig
        self.screen.blit(vig, (0, 0))

    def _screen_title(self, title, y=34, sub=None):
        """Big outlined screen title with a gold underline."""
        cx = cfg.WINDOW_W // 2
        self._text(title, self.font_l, center=(cx, y))
        w = self.font_l.size(title)[0] // 2 + 16
        pygame.draw.line(self.screen, (232, 190, 90), (cx - w, y + 20), (cx + w, y + 20), 2)
        if sub:
            self._text(sub, self.font_s, (190, 196, 214), center=(cx, y + 34))

    def _panel(self, rect, border=(92, 100, 128), radius=12, top=(42, 46, 64),
               bottom=(28, 30, 44)):
        rect = pygame.Rect(rect)
        pygame.draw.rect(self.screen, (8, 10, 16), rect.move(0, 4), border_radius=radius)
        self.screen.blit(grad_rect(rect.w, rect.h, top, bottom, radius), rect.topleft)
        pygame.draw.rect(self.screen, border, rect, 2, border_radius=radius)
        return rect

    def _draw_menu(self):
        cx = cfg.WINDOW_W // 2
        t = self._now()
        self._menu_backdrop()
        # crown + bobbing title
        bob = int(math.sin(t * 2.0) * 4)
        crown_y = 84 + bob
        pts = [(cx - 30, crown_y + 16), (cx - 30, crown_y - 4), (cx - 15, crown_y + 6),
               (cx, crown_y - 14), (cx + 15, crown_y + 6), (cx + 30, crown_y - 4),
               (cx + 30, crown_y + 16)]
        pygame.draw.polygon(self.screen, (0, 0, 0), [(x + 2, y + 3) for x, y in pts])
        pygame.draw.polygon(self.screen, (250, 206, 92), pts)
        pygame.draw.polygon(self.screen, (120, 80, 20), pts, 2)
        for x in (cx - 30, cx, cx + 30):
            pygame.draw.circle(self.screen, (230, 70, 80),
                               (x, crown_y - (14 if x == cx else 4)), 4)
        self._text("CLASH CLONE", self.font_title, center=(cx, 142 + bob))
        self._text("Singleplayer  v" + cfg.GAME_VERSION, self.font_m, (226, 230, 240),
                   center=(cx, 186 + bob))
        self._wallet(cx, 220)
        self.music_btn.label = "Music: %s (M)" % ("On" if self.music_on else "Off")
        self.sfx_btn.label = "Sound: %s (N)" % ("On" if self.sfx_on else "Off")
        for b in self.menu_buttons:
            b.draw(self.screen, self.font_sb if b in (self.music_btn, self.sfx_btn)
                   else self.font_m)
        # your current deck, shown as sprites in a framed strip
        if self.player_deck:
            n = len(self.player_deck)
            sz, gap = 38, 6
            total = n * sz + (n - 1) * gap
            x0 = cx - total // 2
            strip = self._panel((x0 - 12, cfg.WINDOW_H - 92, total + 24, 64))
            self._text("Your Deck", self.font_sb, center=(cx, strip.y - 2))
            for i, k in enumerate(self.player_deck):
                self.screen.blit(sprites.get_sprite(k, sz),
                                 (x0 + i * (sz + gap), strip.y + 14))

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
        self._screen_title("Battle Setup", 30)

        # ---- AI intelligence: 5 big buttons ----
        info = cfg.AI_LEVELS[self.ai_level]
        ly0 = self.PM_LEVEL_Y - 28
        self._text("AI Intelligence", self.font_m, topleft=(12, ly0))
        self._text(info["name"], self.font_m, self.LEVEL_COLORS[self.ai_level],
                   topleft=(cfg.WINDOW_W - 14 - self.font_m.size(info["name"])[0], ly0))
        for r, lv in self._prematch_level_rects():
            sel = lv == self.ai_level
            col = self.LEVEL_COLORS[lv]
            bg = dk_c(col, 120) if sel else (44, 50, 62)
            if r.collidepoint(mouse):
                bg = lt_c(bg, 18)
            pygame.draw.rect(self.screen, (10, 12, 18), r.move(0, 3), border_radius=9)
            self.screen.blit(grad_rect(r.w, r.h, lt_c(bg, 16), bg, 9), r.topleft)
            pygame.draw.rect(self.screen, col if sel else dk_c(col, 70), r,
                             3 if sel else 1, border_radius=9)
            self._text(str(lv), self.font_l, col if sel else WHITE,
                       center=(r.centerx, r.y + 20))
            name = cfg.AI_LEVELS[lv]["name"]
            self._text(self._fit(name, self.font_s, r.w - 4), self.font_s,
                       cfg.COLOR_TEXT, center=(r.centerx, r.bottom - 10))
        self._text(info["desc"], self.font_s, (200, 200, 200),
                   center=(cx, self.PM_LEVEL_Y + 66))

        # ---- AI elixir boost slider ----
        v = self.ai_elixir
        vcol = self._elixir_color(v)
        ly = self.PM_SLIDER_Y - 62
        self._text("AI Elixir", self.font_m, topleft=(12, ly + 4))
        val = render_text(self.font_xl, "%.2fx" % v, vcol)
        self.screen.blit(val, (cfg.WINDOW_W - 12 - val.get_width(), ly - 10))
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


        # ---- AI card level: ladder or match mine ----
        for r, mode, lbl in self._prematch_cardlv_rects():
            sel = mode == self.ai_card_mode
            bg = (70, 110, 170) if sel else (44, 50, 64)
            if r.collidepoint(mouse):
                bg = lt_c(bg, 14)
            pygame.draw.rect(self.screen, bg, r, border_radius=8)
            pygame.draw.rect(self.screen, (250, 222, 110) if sel else (80, 88, 110), r,
                             2 if sel else 1, border_radius=8)
            self._text(lbl, self.font_s, WHITE, center=r.center)
        wins = self.profile.ladder_wins(self.ai_level)
        nxt = profile_data.LADDER_WINS_PER_LEVEL - wins % profile_data.LADDER_WINS_PER_LEVEL
        tip = ("AI cards Lv %d  (%d wins vs %s; next level in %d)" % (
            self.profile.ladder_level(self.ai_level), wins, info["name"], nxt)
            if self.ai_card_mode == "ladder" and self.profile.ladder_level(self.ai_level)
            < profile_data.MAX_LEVEL else
            "AI cards Lv %d   -   your towers Lv %d" % (
                self._ai_card_level(), self.profile.tower_level(self.player_deck)))
        self._text(tip, self.font_s, (200, 204, 220), center=(cx, self.PM_SLIDER_Y + 128))

        # ---- decks ----
        self._deck_preview_panel(self.PM_SLIDER_Y + 140, "AI Deck:  " + self.ai_deck_choice,
                                 (240, 150, 150), self._ai_deck_preview_cards())
        self._deck_preview_panel(self.PM_SLIDER_Y + 244, "Your Deck", (150, 200, 240),
                                 self.player_deck)

        for b in self._prematch_buttons():
            b.draw(self.screen, self.font_m)

    def _prematch_cardlv_rects(self):
        y = self.PM_SLIDER_Y + 88
        w = (cfg.WINDOW_W - 24 - 8) // 2
        lad = "Ladder: AI Lv %d" % self.profile.ladder_level(self.ai_level)
        mat = "Match my level: Lv %d" % self.profile.tower_level(self.player_deck)
        return [(pygame.Rect(12, y, w, 28), "ladder", lad),
                (pygame.Rect(20 + w, y, w, 28), "match", mat)]

    def _deck_preview_panel(self, y, label, col, deck):
        """Framed strip showing an 8-card deck (None = random deck)."""
        panel = self._panel((12, y, cfg.WINDOW_W - 24, 98), border=dk_c(col, 50))
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
        sz = 42
        gap = (panel.w - 20 - sz * 8) // 7
        for i, k in enumerate(deck):
            x = panel.x + 10 + i * (sz + gap)
            self.screen.blit(sprites.get_sprite(k, sz), (x, y + 32))
            self._text("Lv%d" % self._deck_card_level(k, deck), self.font_s,
                       (230, 230, 240), center=(x + sz // 2, y + 84))

    def _draw_records(self):
        cx = cfg.WINDOW_W // 2
        self._screen_title("Records", 30, "per AI intelligence level (any elixir boost)")
        y = 82
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
        self._screen_title("How To Play", 40)
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
            "Levels: survive waves (no enemy towers, no",
            "win conditions). Lose no tower for 3 stars.",
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
        title = {"ai": "AI Deck", "level": "Level Deck"}.get(
            self.deck_mode, "Deck %d" % (self.profile.active_slot + 1))
        tabs = self._deck_tab_rects()
        if tabs:
            self._text(title, self.font_l, topleft=(14, 4))
            for r, i in tabs:
                sel = i == self.profile.active_slot
                bg = (70, 110, 170) if sel else (44, 50, 64)
                if r.collidepoint(mouse):
                    bg = lt_c(bg, 14)
                pygame.draw.rect(self.screen, bg, r, border_radius=8)
                pygame.draw.rect(self.screen, (250, 222, 110) if sel else (80, 88, 110), r,
                                 2 if sel else 1, border_radius=8)
                self._text(str(i + 1), self.font_m, center=r.center)
        else:
            self._text(title, self.font_l, center=(cx, 22))
        avg = (sum(cards.CARDS[k].elixir for k in deck) / len(deck) if deck else 0)
        cyc = sum(sorted(cards.CARDS[k].elixir for k in deck)[:4]) if len(deck) >= 4 else 0
        full = len(deck) == cfg.DECK_SIZE
        lvl = (sum(self.profile.level(k) for k in deck) / len(deck)) if deck else 11
        self._text("%d/8   |   avg elixir %.1f   |   4-card cycle %d   |   avg Lv %.1f"
                   % (len(deck), avg, cyc, lvl),
                   self.font_s, (150, 230, 150) if full else (170, 178, 195),
                   center=(cx, 55))

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
            self._text(self._fit("%s  Lv%d" % (card.name, self._deck_card_level(card.key, deck))
                                 if self.deck_mode != "ai" else card.name,
                                 self.font_s, r.w - 6), self.font_s,
                       cfg.COLOR_TEXT, center=(r.centerx, r.bottom - 10))
            tag = self._slot_tag(i, card.key)
            if tag:
                txt, col = tag
                tw = self.font_s.size(txt)[0] + 8
                tr = pygame.Rect(r.right - tw - 3, r.y + 3, tw, 15)
                pygame.draw.rect(self.screen, (20, 16, 30), tr, border_radius=5)
                pygame.draw.rect(self.screen, col, tr, 1, border_radius=5)
                self._text(txt, self.font_s, col, center=tr.center)
                pygame.draw.rect(self.screen, col, r, 2, border_radius=9)
            if hover:
                for k_, ar in enumerate(self._deck_arrow_rects(r)):
                    if (k_ == 0 and i == 0) or (k_ == 1 and i == len(deck) - 1):
                        continue
                    pygame.draw.rect(self.screen, (20, 24, 34), ar, border_radius=4)
                    self._text("<" if k_ == 0 else ">", self.font_sb, WHITE, center=ar.center)
            if hover:   # "click to remove" mark
                xr = (r.right - 11, r.y + 11)
                pygame.draw.circle(self.screen, (200, 70, 70), xr, 8)
                pygame.draw.line(self.screen, (255, 255, 255), (xr[0] - 3, xr[1] - 3),
                                 (xr[0] + 3, xr[1] + 3), 2)
                pygame.draw.line(self.screen, (255, 255, 255), (xr[0] - 3, xr[1] + 3),
                                 (xr[0] + 3, xr[1] - 3), 2)

        # empty-slot labels for the special slots
        for i, r in enumerate(self._deck_slot_rects()):
            if i >= len(deck) and i < 3:
                self._text("EVO" if i < 2 else "HERO", self.font_s,
                           (150, 110, 200) if i < 2 else (200, 160, 80),
                           center=(r.centerx, r.bottom - 12))
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
            self._text("Slots 1-2: EVO   Slot 3: HERO   < > move   click: remove",
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
            if self.deck_mode == "level" and card.key in levels.BANNED:
                # win conditions are locked out of Levels: grey + "no" sign
                shade = pygame.Surface(r.size, pygame.SRCALPHA)
                pygame.draw.rect(shade, (14, 14, 20, 175), shade.get_rect(), border_radius=7)
                self.screen.blit(shade, r.topleft)
                c0 = (r.centerx, r.y + 26)
                pygame.draw.circle(self.screen, (220, 60, 60), c0, 13, 3)
                pygame.draw.line(self.screen, (220, 60, 60), (c0[0] - 9, c0[1] + 9),
                                 (c0[0] + 9, c0[1] - 9), 3)
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
            b.draw(self.screen, self.font_sb)

    # --------------------------------------------------------- match screen
    def _draw_match(self):
        self._draw_arena()
        m = self.match
        if m.miasma:
            self._draw_miasma()
        self._draw_no_deploy_zone()
        self.fx.draw_decals(self.screen)
        # ground first (back to front), then everything in the air on top
        for e in sorted(m.entities, key=lambda e: (e.flying, e.y)):
            self._draw_entity(e)
        for fx in m.effects:
            self._draw_effect(fx)
        self._draw_beams()
        for p in m.projectiles:
            self._draw_projectile(p)
        self.fx.draw_particles(self.screen)
        self._draw_popups()
        self.fx.draw_flash(self.screen)
        self._draw_placement_preview()
        self._draw_topbar()
        self._draw_hud()
        self._draw_wave_banner()

    def _draw_wave_banner(self):
        run = self.level_run
        if run is None or not run.banner:
            return
        title, sub, age = run.banner
        a = min(1.0, age / 0.25) * min(1.0, (3.0 - age) / 0.6)
        if a <= 0:
            return
        cy = cfg.ARENA_Y0 + int(cfg.ARENA_PX_H * 0.42) - int((1 - min(1.0, age / 0.25)) * 20)
        rib = pygame.Surface((cfg.WINDOW_W, 76), pygame.SRCALPHA)
        rib.fill((10, 8, 18, int(170 * a)))
        pygame.draw.line(rib, (232, 190, 90, int(255 * a)), (0, 1), (cfg.WINDOW_W, 1), 2)
        pygame.draw.line(rib, (232, 190, 90, int(255 * a)), (0, 74), (cfg.WINDOW_W, 74), 2)
        self.screen.blit(rib, (0, cy - 38))
        boss = title.startswith("BOSS")
        t1 = render_text(self.font_l, title, (255, 110, 110) if boss else WHITE).copy()
        t1.set_alpha(int(255 * a))
        self.screen.blit(t1, (cfg.WINDOW_W // 2 - t1.get_width() // 2, cy - 30))
        if sub:
            t2 = render_text(self.font_sb, sub, (230, 220, 190)).copy()
            t2.set_alpha(int(255 * a))
            self.screen.blit(t2, (cfg.WINDOW_W // 2 - t2.get_width() // 2, cy + 12))

    # --------------------------------------------------------- arena
    def _arena_bg(self):
        """The static arena picture (grass, scenery border, river, bridges,
        tower pads), rendered once per match and cached."""
        key = (bool(self.match and self.match.enemy_towers),)
        if getattr(self, "_arena_key", None) == key and self._arena_surf is not None:
            return self._arena_surf
        self._arena_key = key
        enemy_towers = key[0]
        ts = cfg.TILE_SIZE
        BX, BY = cfg.ARENA_BORDER_X, cfg.ARENA_BORDER_Y
        W, H = cfg.WINDOW_W, cfg.ARENA_PX_H + 2 * BY
        surf = pygame.Surface((W, H))
        rng = random.Random(11)
        ox, oy = BX, BY                        # grid origin inside this surface
        # ---- scenery ground around the arena ----
        surf.fill((58, 112, 62))
        for _ in range(900):                   # grass texture
            x, y = rng.randrange(W), rng.randrange(H)
            c = rng.choice(((52, 102, 56), (66, 124, 68), (48, 96, 52), (72, 130, 70)))
            pygame.draw.ellipse(surf, c, (x, y, rng.randint(3, 8), rng.randint(2, 4)))
        # ---- the playfield: checker grass ----
        for r in range(cfg.GRID_ROWS):
            for c in range(cfg.GRID_COLS):
                col = cfg.COLOR_ARENA if (r + c) % 2 == 0 else cfg.COLOR_ARENA_ALT
                if r > RIVER_BOTTOM:
                    col = lt_c(col, 6)
                v = rng.randint(-3, 3)
                col = tuple(max(0, min(255, k + v)) for k in col)
                pygame.draw.rect(surf, col, (ox + c * ts, oy + r * ts, ts + 1, ts + 1))
        for _ in range(260):                   # tufts on the field
            x = ox + rng.uniform(0, cfg.ARENA_PX_W)
            y = oy + rng.uniform(0, cfg.ARENA_PX_H)
            pygame.draw.line(surf, lt_c(cfg.COLOR_ARENA, 22), (x, y), (x + 1, y - 3), 1)
        # worn lane paths toward each bridge
        lane = pygame.Surface((int(1.8 * ts), cfg.ARENA_PX_H), pygame.SRCALPHA)
        lane.fill((214, 196, 140, 26))
        for bx in BRIDGE_X:
            surf.blit(lane, (ox + (bx - 0.9) * ts, oy))
        # ---- river (runs out under the rim to both screen edges) ----
        ry = int(oy + RIVER_TOP * ts)
        rh = int((RIVER_BOTTOM - RIVER_TOP) * ts)
        pygame.draw.rect(surf, dk_c(cfg.COLOR_RIVER, 30), (0, ry - 2, W, rh + 4))
        pygame.draw.rect(surf, cfg.COLOR_RIVER, (0, ry + 3, W, rh - 6))
        pygame.draw.rect(surf, lt_c(cfg.COLOR_RIVER, 18), (0, ry + rh // 2 - 2, W, 4))
        for x in range(0, W, 9):               # pebbly banks
            for yy in (ry - 3, ry + rh + 1):
                pygame.draw.ellipse(surf, (138, 128, 112),
                                    (x + rng.randint(-2, 2), yy + rng.randint(-1, 1),
                                     rng.randint(5, 9), 4))
        # ---- stone rim around the placeable field ----
        rim = pygame.Rect(ox - 5, oy - 5, cfg.ARENA_PX_W + 10, cfg.ARENA_PX_H + 10)
        stone, joint = (170, 164, 150), (118, 112, 102)
        for seg in ((rim.x, rim.y, rim.w, 5), (rim.x, rim.bottom - 5, rim.w, 5)):
            pygame.draw.rect(surf, stone, seg)
            for x in range(seg[0], seg[0] + seg[2], 14):
                pygame.draw.line(surf, joint, (x, seg[1]), (x, seg[1] + 4), 1)
        for side_x in (rim.x, rim.right - 5):
            for (y0, y1) in ((rim.y, ry - 3), (ry + rh + 3, rim.bottom)):
                pygame.draw.rect(surf, stone, (side_x, y0, 5, y1 - y0))
                for y in range(y0, y1, 14):
                    pygame.draw.line(surf, joint, (side_x, y), (side_x + 4, y), 1)
        pygame.draw.rect(surf, (88, 84, 76), rim, 1)
        # ---- trees & bushes in the side margins ----
        def tree(x, y, r):
            pygame.draw.circle(surf, (34, 62, 36), (int(x) + 3, int(y) + 4), r)   # shadow
            pygame.draw.circle(surf, (40, 88, 46), (int(x), int(y)), r)
            pygame.draw.circle(surf, (56, 112, 58), (int(x) - r // 4, int(y) - r // 4),
                               int(r * 0.7))
            pygame.draw.circle(surf, (76, 136, 72), (int(x) - r // 3, int(y) - r // 3),
                               int(r * 0.35))
        for side in (0, 1):
            y = rng.randint(4, 30)
            while y < H - 10:
                if not (ry - 16 < y < ry + rh + 16):
                    for col_ in range(2):          # two staggered rows of trees
                        xx = rng.uniform(4, BX * 0.45) + col_ * BX * 0.45
                        x = xx if side == 0 else W - xx
                        tree(x, y + col_ * 12, rng.randint(10, 15))
                y += rng.randint(24, 40)
        for _ in range(26):                    # bushes / rocks / flowers top & bottom
            x = rng.uniform(BX, W - BX)
            y = rng.choice((rng.uniform(4, BY - 10), H - rng.uniform(4, BY - 10)))
            kind = rng.random()
            if kind < 0.45:
                pygame.draw.circle(surf, (44, 92, 48), (int(x), int(y)), 6)
                pygame.draw.circle(surf, (66, 122, 62), (int(x) - 2, int(y) - 2), 4)
            elif kind < 0.75:
                pygame.draw.ellipse(surf, (120, 116, 108), (x - 6, y - 3, 12, 8))
                pygame.draw.ellipse(surf, (156, 150, 140), (x - 4, y - 3, 7, 4))
            else:
                for k in range(3):
                    pygame.draw.circle(surf, rng.choice(((240, 220, 90), (240, 120, 160),
                                                         (250, 250, 250))),
                                       (int(x + k * 4), int(y + (k % 2) * 3)), 2)
        # team banners in the corners
        for (bx, by, col) in ((14, 14, cfg.COLOR_TEAM_ENEMY), (W - 14, 14, cfg.COLOR_TEAM_ENEMY),
                              (14, H - 34, cfg.COLOR_TEAM_PLAYER),
                              (W - 14, H - 34, cfg.COLOR_TEAM_PLAYER)):
            pygame.draw.line(surf, (90, 70, 50), (bx, by), (bx, by + 22), 2)
            pygame.draw.polygon(surf, col, [(bx + 1, by + 1), (bx + 12, by + 4),
                                            (bx + 1, by + 9)])
            pygame.draw.polygon(surf, dk_c(col, 70), [(bx + 1, by + 1), (bx + 12, by + 4),
                                                      (bx + 1, by + 9)], 1)
        # ---- bridges ----
        for bx in BRIDGE_X:
            bxp = ox + (bx - 0.9) * ts
            bw = 1.8 * ts
            pygame.draw.rect(surf, (40, 30, 22), (bxp + 2, ry + 2, bw, rh + 2))
            pygame.draw.rect(surf, cfg.COLOR_BRIDGE, (bxp, ry - 3, bw, rh + 6))
            for i in range(1, 5):
                yy = ry - 3 + i * (rh + 6) / 5
                pygame.draw.line(surf, dk_c(cfg.COLOR_BRIDGE, 35), (bxp, yy), (bxp + bw, yy), 2)
            for rx in (bxp, bxp + bw - 3):
                pygame.draw.rect(surf, dk_c(cfg.COLOR_BRIDGE, 60), (rx, ry - 5, 3, rh + 10))
        # ---- tower pads ----
        for tw in self.match.towers.values():
            if not tw.alive:
                continue
            px, py = ox + tw.x * ts, oy + tw.y * ts
            rad = int((2.1 if tw.is_king else 1.8) * ts)
            pygame.draw.circle(surf, (120, 116, 106), (int(px), int(py) + 2), rad)
            pygame.draw.circle(surf, (158, 154, 144), (int(px), int(py)), rad)
            for k in range(8):                 # flagstones
                a = k * math.pi / 4
                pygame.draw.line(surf, (134, 130, 120), (px, py),
                                 (px + math.cos(a) * rad, py + math.sin(a) * rad), 1)
            pygame.draw.circle(surf, (110, 106, 98), (int(px), int(py)), rad, 2)
        # ---- Levels: crypt gates where the enemy waves come from ----
        if not enemy_towers:
            for gx in (3.5, 14.5, 9.0):
                px, py = ox + gx * ts, oy + (3.0 if gx == 9.0 else 6.0) * ts
                gate = pygame.Rect(0, 0, 44, 34)
                gate.center = (int(px), int(py))
                pygame.draw.rect(surf, (70, 66, 74), gate.inflate(10, 8), border_top_left_radius=18,
                                 border_top_right_radius=18)
                pygame.draw.rect(surf, (24, 18, 30), gate, border_top_left_radius=16,
                                 border_top_right_radius=16)
                pygame.draw.rect(surf, (120, 110, 130), gate.inflate(10, 8), 2,
                                 border_top_left_radius=18, border_top_right_radius=18)
                for k in (-12, 0, 12):         # skull studs
                    pygame.draw.circle(surf, (220, 214, 196), (gate.centerx + k, gate.y - 1), 3)
        self._arena_surf = surf
        return surf

    def _draw_arena(self):
        t = self._now()
        ts = cfg.TILE_SIZE
        self.screen.blit(self._arena_bg(), (0, cfg.TOP_BAR))
        # drifting ripples on the river (full width, under the bridges' rails)
        ry = cfg.ARENA_Y0 + RIVER_TOP * ts
        rh = (RIVER_BOTTOM - RIVER_TOP) * ts
        self.screen.set_clip(pygame.Rect(0, ry + 3, cfg.WINDOW_W, rh - 6))
        for i in range(9):
            wx = (t * 26 + i * 61) % (cfg.WINDOW_W + 40) - 20
            wy = ry + 6 + (i % 3) * (rh - 14) // 2
            pygame.draw.ellipse(self.screen, lt_c(cfg.COLOR_RIVER, 45), (wx, wy, 22, 4))
        self.screen.set_clip(None)
        for bx in BRIDGE_X:                     # bridges back on top of ripples
            bxp, _ = tile_to_px(bx - 0.9, 0)
            area = pygame.Rect(int(bxp), int(ry - 5) - cfg.TOP_BAR, int(1.8 * ts) + 1, int(rh) + 10)
            self.screen.blit(self._arena_surf, (area.x, area.y + cfg.TOP_BAR), area)
        if cfg.SHOW_TILE_GRID:
            for c in range(cfg.GRID_COLS + 1):
                x, y = tile_to_px(c, 0)
                pygame.draw.line(self.screen, (0, 0, 0), (x, cfg.ARENA_Y0),
                                 (x, cfg.ARENA_Y0 + cfg.ARENA_PX_H))

    def _draw_miasma(self):
        """Levels: the Crypt Miasma - a faint drifting haze on the enemy half."""
        ts = cfg.TILE_SIZE
        h = int(RIVER_TOP * ts)
        surf = getattr(self, "_miasma_surf", None)
        if surf is None:
            surf = pygame.Surface((cfg.ARENA_PX_W, h), pygame.SRCALPHA)
            surf.fill((70, 140, 60, 26))
            rng = random.Random(4)
            for _ in range(40):
                r = rng.randint(14, 34)
                pygame.draw.circle(surf, (110, 170, 80, 18),
                                   (rng.randrange(cfg.ARENA_PX_W), rng.randrange(h)), r)
            self._miasma_surf = surf
        t = self._now()
        dx = int(math.sin(t * 0.4) * 8)
        self.screen.set_clip(pygame.Rect(cfg.ARENA_X0, cfg.ARENA_Y0, cfg.ARENA_PX_W, h))
        self.screen.blit(surf, (cfg.ARENA_X0 + dx, cfg.ARENA_Y0))
        self.screen.set_clip(None)

    def _draw_no_deploy_zone(self):
        """While a card is selected, tint the tiles you can't deploy on."""
        if self.selected is None or self.match is None:
            return
        key = self.match.hands[PLAYER][self.selected]
        if cards.CARDS[key].category == "spell":
            return
        ts = cfg.TILE_SIZE
        tint = getattr(self, "_nodeploy_tile", None)
        if tint is None:
            tint = pygame.Surface((ts, ts), pygame.SRCALPHA)
            tint.fill((220, 50, 50, 46))
            self._nodeploy_tile = tint
        for r in range(cfg.GRID_ROWS):
            for c in range(cfg.GRID_COLS):
                if not self.match.can_place(PLAYER, key, c + 0.5, r + 0.5):
                    self.screen.blit(tint, tile_to_px(c, r))

    def _team_color(self, team):
        return cfg.COLOR_TEAM_PLAYER if team == PLAYER else cfg.COLOR_TEAM_ENEMY

    def _draw_entity(self, e):
        px, py = tile_to_px(e.x, e.y)
        if e.is_tower:
            self._draw_tower(e, px, py)
            return
        base = (2.6 if e.is_building else 1.5) * cfg.TILE_SIZE
        size = int(base * sprites.render_scale(e.key))
        if getattr(e, "general", False):
            size = int(size * 1.35)
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
        # team ring (gold for champions / heroes)
        ring = (245, 205, 85) if (e.card.is_champion or e.hero) else self._team_color(e.team)
        if e.evo:
            # evolved: pulsing purple aura under the unit
            pulse = 0.5 + 0.5 * math.sin(self._now() * 4 + e.anim_seed * 6)
            rr = size // 2 + 6
            aura = self._aura_surf(rr, int(60 + 70 * pulse))
            self.screen.blit(aura, (px - rr - 2, py - rr - 2))
            ring = (196, 120, 255)
        pygame.draw.circle(self.screen, ring, (int(px), int(py)), size // 2 + 2, 3)
        skey = sprites.unit_sprite_key(e.key)
        ox, oy, ang, sx, sy = self._anim_pose(e, size)
        if e.flying and not e.is_building:      # shadow on the ground below
            sh = pygame.Surface((int(size * 0.7), max(4, size // 4)), pygame.SRCALPHA)
            pygame.draw.ellipse(sh, (0, 0, 0, 55), sh.get_rect())
            self.screen.blit(sh, (px - sh.get_width() // 2, py + size // 2 - sh.get_height() + 4))
        spr = self._posed_sprite(skey, size, ang, sx, sy)
        if e.hurt > 0 or cloaked or e.immune_timer > 0:
            spr = spr.copy()
            if e.hurt > 0:                       # brief white hit flash
                a = int(110 * min(1.0, e.hurt / 0.14))
                spr.fill((a, a, a), special_flags=pygame.BLEND_RGB_ADD)
            if cloaked or e.immune_timer > 0:
                spr.set_alpha(110 if cloaked else 200)
        # feet stay planted when squashing: anchor on the bottom centre
        bx = px + ox - spr.get_width() // 2
        by = py + oy + size // 2 - (spr.get_height() + int(size * sy)) // 2
        self.screen.blit(spr, (bx, by))
        if e.card.generates_elixir:
            self._draw_collector_gauge(e, px, py, size)
        self._draw_swing(e, px, py, size)
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
        if e.evo and not e.is_building:   # sparkle above evolved troops
            t = self._now() * 3 + e.anim_seed * 7
            sx_, sy_ = int(px + math.cos(t) * size * 0.4), int(py - size // 2 + math.sin(t * 1.3) * 3)
            pygame.draw.circle(self.screen, (235, 200, 255), (sx_, sy_), 2)
        if e.hero:                # golden star above heroes
            cyy = py - size // 2 - 7
            pts = []
            for k in range(10):
                a = -math.pi / 2 + k * math.pi / 5
                rr_ = 6 if k % 2 == 0 else 2.6
                pts.append((px + math.cos(a) * rr_, cyy + math.sin(a) * rr_))
            pygame.draw.polygon(self.screen, (255, 210, 90), pts)
            pygame.draw.polygon(self.screen, (120, 80, 20), pts, 1)
        if e.card.is_champion:    # little gold crown above
            cyy = py - size // 2 - 6
            pygame.draw.polygon(self.screen, (245, 205, 85),
                                [(px - 6, cyy + 3), (px - 6, cyy - 2), (px - 3, cyy + 1),
                                 (px, cyy - 4), (px + 3, cyy + 1), (px + 6, cyy - 2),
                                 (px + 6, cyy + 3)])
        self._draw_hp_bar(e, px, py - size // 2 - 5, size)
        if e.level is not None and (self.level_run is not None or e.level != 11) and (
                e.team == ENEMY or e.level != 11):
            self._draw_level_badge(e, px, py, size)
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

    # ------------------------------------------------------- unit animation
    # Everything here is a light procedural pose on top of the unit's normal
    # art (bob, squash, lean, lunge). The sprite itself is never redrawn, so
    # every card keeps its exact look and silhouette.
    def _aura_surf(self, rr, a):
        cache = self.__dict__.setdefault("_aura_cache", {})
        key = (rr, a // 10)
        surf = cache.get(key)
        if surf is None:
            surf = pygame.Surface((rr * 2 + 4, rr * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(surf, (170, 90, 255, a // 3), (rr + 2, rr + 2), rr)
            pygame.draw.circle(surf, (210, 150, 255, a), (rr + 2, rr + 2), rr, 2)
            cache[key] = surf
        return surf

    def _anim_pose(self, e, size):
        """-> (dx, dy, angle_deg, scale_x, scale_y) for this frame."""
        m = self.match
        now = m.elapsed
        ox = oy = 0.0
        ang = 0.0
        sx = sy = 1.0
        if e.freeze_timer > 0 or e.stun_timer > 0:
            return 0, 0, 0, 1.0, 1.0
        ph = e.anim_seed * math.tau
        # pop-in when a unit appears (drops in, settles)
        age = now - e.born
        if 0 <= age < 0.2 and not e.is_tower:
            k = 1.0 - age / 0.2
            oy -= k * size * 0.25
            sy *= 1.0 + 0.12 * k
            sx *= 1.0 - 0.08 * k
        since = now - e.atk_t
        if e.is_building:
            if since < 0.18:                     # firing recoil pulse
                k = 1.0 - since / 0.18
                sx *= 1.0 + 0.06 * k
                sy *= 1.0 - 0.05 * k
                ox -= e.atk_dir[0] * k * size * 0.05
                oy -= e.atk_dir[1] * k * size * 0.05
            elif e.card.spawner or e.card.generates_elixir:
                sy *= 1.0 + 0.015 * math.sin(now * 2.2 + ph)
            return int(ox), int(oy), 0, sx, sy
        moving = now - e.move_t < 0.12
        if e.flying:
            oy -= 2.5 + 2.5 * math.sin(now * 4.0 + ph)          # hover
            sx *= 1.0 + 0.045 * math.sin(now * 15.0 + ph)       # wing beat
            if moving:
                ang -= e.mvx * 5.0
        elif moving:
            # step cycle: one bob per step, waddle side to side, lean forward
            p = e.walk / 0.42 * math.pi + ph
            b = abs(math.sin(p))
            oy -= b * size * 0.07
            ang += math.sin(p) * 5.0 - e.mvx * 4.0
            sy *= 0.96 + 0.04 * b
            sx *= 1.03 - 0.03 * b
        else:
            # idle: slow breathing
            br = math.sin(now * 2.6 + ph)
            sy *= 1.0 + 0.025 * br
            sx *= 1.0 - 0.012 * br
        dx, dy = e.atk_dir
        melee = e.is_melee() and not e.card.kamikaze
        if melee:
            # wind-up: lean back just before the blow lands...
            t = e.target
            if (t is not None and t.alive and 0 < e.attack_cd < 0.2
                    and not moving):
                w = 1.0 - e.attack_cd / 0.2
                ox -= dx * w * size * 0.06
                oy -= dy * w * size * 0.06
                ang += (6.0 if dx >= 0 else -6.0) * w
            # ...then lunge into it and recover
            if since < 0.3:
                k = since / 0.06 if since < 0.06 else max(0.0, 1.0 - (since - 0.06) / 0.24)
                ox += dx * k * size * 0.2
                oy += dy * k * size * 0.2
                ang -= (12.0 if dx >= 0 else -12.0) * k
                sx *= 1.0 + 0.05 * k
        elif since < 0.2:
            # ranged: kick back from the shot
            k = 1.0 - since / 0.2
            ox -= dx * k * size * 0.08
            oy -= dy * k * size * 0.08
            sy *= 1.0 - 0.04 * k
        return int(ox), int(oy), ang, sx, sy

    def _posed_sprite(self, skey, size, ang, sx, sy):
        """Scaled/rotated copy of a unit sprite (quantized + cached)."""
        w = max(4, int(round(size * sx / 2.0)) * 2)
        h = max(4, int(round(size * sy / 2.0)) * 2)
        a = int(round(ang))
        if w == size and h == size and a == 0:
            return sprites.get_sprite(skey, size)
        cache = self.__dict__.setdefault("_pose_cache", {})
        key = (skey, size, w, h, a)
        surf = cache.get(key)
        if surf is None:
            if len(cache) > 6000:
                cache.clear()
            base = sprites.get_sprite(skey, size)
            surf = pygame.transform.smoothscale(base, (w, h)) if (w, h) != (size, size) else base
            if a:
                surf = pygame.transform.rotate(surf, a)
            cache[key] = surf
        return surf

    def _draw_swing(self, e, px, py, size):
        """A quick white swoosh arc in front of a melee unit as it hits."""
        if not e.is_melee() or e.card.kamikaze or e.is_building:
            return
        since = self.match.elapsed - e.atk_t
        if not 0 <= since < 0.16:
            return
        k = 1.0 - since / 0.16
        dx, dy = e.atk_dir
        r = int(size * 0.55)
        cx = px + dx * size * 0.32
        cy = py + dy * size * 0.32
        surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        base = math.atan2(-dy, dx)            # pygame arcs: y axis points up
        sweep = 1.6 * (0.35 + 0.65 * (1.0 - k))
        rect = pygame.Rect(2, 2, r * 2, r * 2)
        big = e.max_hp >= 1500
        col = (255, 240, 200) if not big else (255, 210, 150)
        pygame.draw.arc(surf, col + (int(200 * k),), rect, base - sweep / 2,
                        base + sweep / 2, max(2, size // 9))
        self.screen.blit(surf, (cx - r - 2, cy - r - 2))

    def _draw_collector_gauge(self, e, px, py, size):
        """Elixir Collector: the glass tank fills as the next elixir brews."""
        amt, period = e.card.generates_elixir
        frac = 1.0 - max(0.0, e.elixir_timer) / period
        if e.deploy_timer > 0:
            frac = 0.0
        s = size / 128.0
        # tank interior in the art's 128px space: centre (64, 66), r 22 x 24
        cx, cy = px, py + (66 - 64) * s
        rx, ry = max(2, int(21 * s)), max(2, int(23 * s))
        surf = pygame.Surface((rx * 2 + 2, ry * 2 + 2), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (205, 175, 225, 255), (1, 1, rx * 2, ry * 2))
        level = int((ry * 2) * (1.0 - frac))
        liquid = pygame.Surface((rx * 2 + 2, ry * 2 + 2), pygame.SRCALPHA)
        pygame.draw.ellipse(liquid, (215, 60, 225, 255), (1, 1, rx * 2, ry * 2))
        liquid.fill((0, 0, 0, 0), (0, 0, rx * 2 + 2, level + 1))
        surf.blit(liquid, (0, 0))
        if 0.02 < frac < 0.999:                  # bright surface line
            yy = level + 1
            half = rx * math.sqrt(max(0.0, 1 - ((yy - ry - 1) / ry) ** 2))
            pygame.draw.line(surf, (255, 170, 255, 255), (rx + 1 - half, yy),
                             (rx + 1 + half, yy), 1)
        # a couple of rising bubbles
        t = self.match.elapsed
        for i in range(2):
            ph = (t * 0.9 + i * 0.5 + e.anim_seed) % 1.0
            by = int(ry * 2 - ph * (ry * 2 - level))
            if by > level + 2:
                bx = int(rx + 1 + math.sin(t * 3 + i * 2.1) * rx * 0.4)
                pygame.draw.circle(surf, (255, 200, 255, 200), (bx, by), max(1, int(2 * s * 2)))
        pygame.draw.ellipse(surf, (255, 255, 255, 110),
                            (int(rx * 0.45), int(ry * 0.35), max(2, rx // 3), max(3, ry // 2)))
        self.screen.blit(surf, (int(cx - rx - 1), int(cy - ry - 1)))
        # just made elixir: flash the tank
        if self.match.elapsed - getattr(e, "_gen_t", -9) < 0.3:
            k = 1.0 - (self.match.elapsed - e._gen_t) / 0.3
            fl = pygame.Surface((rx * 2 + 8, ry * 2 + 8), pygame.SRCALPHA)
            pygame.draw.ellipse(fl, (255, 160, 255, int(140 * k)), fl.get_rect())
            self.screen.blit(fl, (int(cx - rx - 4), int(cy - ry - 4)))

    def _draw_popups(self):
        """Floating '+1' texts (Elixir Collector)."""
        for pp in self.fx.popups:
            f = pp["age"] / pp["life"]
            a = int(255 * min(1.0, (1.0 - f) * 3.0))
            img = render_text(self.font_m, pp["text"], pp["col"]).copy()
            img.set_alpha(a)
            sc = 0.7 + 0.3 * min(1.0, pp["age"] / 0.12)
            if sc < 0.999:
                img = pygame.transform.smoothscale(
                    img, (max(1, int(img.get_width() * sc)), max(1, int(img.get_height() * sc))))
            self.screen.blit(img, (pp["x"] - img.get_width() // 2,
                                   pp["y"] - 30 * f - img.get_height() // 2))

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

    def _draw_level_badge(self, e, px, py, size):
        """Levels mode: unit level next to the health bar; bosses get a tag."""
        bx, by = int(px - size // 2 - 6), int(py - size // 2 - 4)
        col = (150, 60, 190) if not e.boss else (200, 40, 50)
        if e.team == PLAYER:
            col = (50, 100, 190)
        pygame.draw.circle(self.screen, (0, 0, 0), (bx + 1, by + 1), 8)
        pygame.draw.circle(self.screen, col, (bx, by), 8)
        pygame.draw.circle(self.screen, (240, 220, 255), (bx, by), 8, 1)
        self._text(str(e.level), self.font_s, center=(bx, by), outline=True)
        if e.boss:
            pulse = 0.5 + 0.5 * math.sin(self._now() * 6)
            rr = size // 2 + 7
            aura = pygame.Surface((rr * 2 + 4, rr * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(aura, (220, 40, 60, int(60 + 60 * pulse)), (rr + 2, rr + 2), rr, 3)
            self.screen.blit(aura, (px - rr - 2, py - rr - 2))
            self._text("BOSS", self.font_sb, (255, 90, 90), center=(px, py - size // 2 - 18))

    def _draw_hp_bar(self, e, px, top, width):
        frac = max(0.0, e.hp / e.max_hp)
        over = max(0.0, frac - 1.0)          # Evolved Bats overheal
        frac = min(1.0, frac)
        w = width
        h = 6 if getattr(e, "boss", False) else 4
        x = px - w // 2
        pygame.draw.rect(self.screen, (30, 30, 30), (x, top, w, h))
        col = cfg.COLOR_HP_GOOD if frac > 0.35 else cfg.COLOR_HP_BAD
        if e.team == ENEMY and not e.is_tower:
            col = (230, 90, 90) if frac > 0.35 else (240, 160, 60)
        pygame.draw.rect(self.screen, col, (x, top, int(w * frac), h))
        if over > 0:
            pygame.draw.rect(self.screen, (230, 170, 255), (x, top, int(w * min(1.0, over * 2)), h))
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
        if self.drag_card is not None and pygame.mouse.get_pressed()[0]:
            mx, my = pygame.mouse.get_pos()
            ghost = sprites.get_sprite(key, 44).copy()
            ghost.set_alpha(170)
            self.screen.blit(ghost, (mx - 22, my - 50))
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
        self.screen.blit(grad_rect(cfg.WINDOW_W, cfg.TOP_BAR, (44, 48, 70),
                                   (22, 24, 36), 0), (0, 0))
        pygame.draw.line(self.screen, (92, 84, 64), (0, cfg.TOP_BAR - 1),
                         (cfg.WINDOW_W, cfg.TOP_BAR - 1), 2)
        cy = cfg.TOP_BAR // 2
        if self.level_run is not None:
            # Levels: level name, wave counter and next-wave countdown
            run = self.level_run
            chip = pygame.Rect(0, 0, 150, 30)
            chip.center = (cfg.WINDOW_W // 2, cy)
            boss = run.current_wave() is not None and run.current_wave().boss
            col = (120, 40, 60) if boss else (40, 48, 66)
            self.screen.blit(grad_rect(chip.w, chip.h, lt_c(col, 20), col, 15), chip.topleft)
            pygame.draw.rect(self.screen, (150, 130, 80), chip, 1, border_radius=15)
            nxt = run.next_wave_in()
            if run.total_waves == 0:                    # Endless
                label = ("Wave %d in %d" % (run.wave_number + 1, math.ceil(max(0, nxt)))
                         if run.state == "prep" else "Wave %d" % run.wave_number)
            elif run.state == "prep" and run.wave_number < run.total_waves:
                label = "Wave %d in %d" % (run.wave_number + 1, math.ceil(max(0, nxt)))
            else:
                label = "Wave %d / %d" % (run.wave_number, run.total_waves)
            self._text(label, self.font_m, center=chip.center)
            self._text(run.level.name, self.font_sb, (235, 225, 190),
                       topleft=(10, cy - 9), outline=True)
            alive = sum(1 for s_ in ("left", "right", "king")
                        if m.towers[(PLAYER, s_)].alive)
            self._crown_icon(cfg.WINDOW_W - 52, cy, cfg.COLOR_TEAM_PLAYER)
            self._text("%d/3" % alive, self.font_m, topleft=(cfg.WINDOW_W - 40, cy - 12))
            return
        if self.mode is not None and self.mode != "endless":
            import modes as _modes
            self._text(_modes.MODE_NAMES[self.mode], self.font_s, (240, 210, 140),
                       center=(cfg.WINDOW_W // 2, cfg.TOP_BAR + 10))
        # timer chip (amber during overtime / boosted elixir)
        t = max(0, m.time_left)
        label = "%d:%02d" % (int(t) // 60, int(t) % 60)
        mult = m.elixir_multiplier()
        prefix = "OT " if m.overtime else ""
        if mult > 1:
            prefix += "x%d " % int(mult)
        chip_col = (130, 84, 30) if (m.overtime or mult > 1) else (40, 48, 66)
        chip = pygame.Rect(0, 0, 120, 30)
        chip.center = (cfg.WINDOW_W // 2, cy)
        self.screen.blit(grad_rect(chip.w, chip.h, lt_c(chip_col, 22), chip_col, 15),
                         chip.topleft)
        pygame.draw.rect(self.screen, (150, 130, 80), chip, 1, border_radius=15)
        self._text(prefix + label, self.font_m, center=chip.center)
        # crowns with icons
        self._crown_icon(20, cy, cfg.COLOR_TEAM_ENEMY)
        self._text("%d" % m.crowns[ENEMY], self.font_m, cfg.COLOR_TEAM_ENEMY,
                   topleft=(34, cy - 12))
        self._crown_icon(cfg.WINDOW_W - 46, cy, cfg.COLOR_TEAM_PLAYER)
        self._text("%d" % m.crowns[PLAYER], self.font_m, cfg.COLOR_TEAM_PLAYER,
                   topleft=(cfg.WINDOW_W - 32, cy - 12))

    def _draw_hud(self):
        m = self.match
        hud_y = cfg.HUD_Y
        self.screen.blit(grad_rect(cfg.WINDOW_W, cfg.HUD_HEIGHT, (40, 44, 62),
                                   (20, 22, 32), 0), (0, hud_y))
        pygame.draw.line(self.screen, (92, 84, 64), (0, hud_y), (cfg.WINDOW_W, hud_y), 2)
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
            evo_p = m.evo_progress(PLAYER, key)
            evo_now = evo_p is not None and evo_p[0] >= evo_p[1]
            if evo_now:                       # evolved copy ready: purple glow
                pulse = 0.5 + 0.5 * math.sin(self._now() * 5)
                glow = pygame.Surface((r.w + 12, r.h + 12), pygame.SRCALPHA)
                pygame.draw.rect(glow, (190, 110, 255, int(70 + 80 * pulse)),
                                 glow.get_rect(), 6, border_radius=14)
                self.screen.blit(glow, (r.x - 6, r.y - 6))
                pygame.draw.rect(self.screen, (200, 130, 255), r, 3, border_radius=9)
            if sel:
                pygame.draw.rect(self.screen, (250, 240, 140), r, 3, border_radius=9)
            elif affordable and not evo_now:
                pygame.draw.rect(self.screen, (96, 108, 138), r, 1, border_radius=9)
            spr = sprites.get_sprite(key, 50)
            if not affordable:
                spr = spr.copy()
                spr.fill((90, 90, 90, 160), special_flags=pygame.BLEND_RGBA_MULT)
            self.screen.blit(spr, (r.centerx - 25, r.y + 7))
            # cost badge (top-left, so the name row gets full width)
            pygame.draw.circle(self.screen, dk_c(cfg.COLOR_ELIXIR, 40),
                               (r.x + 11, r.y + 12), 10)
            pygame.draw.circle(self.screen, cfg.COLOR_ELIXIR, (r.x + 10, r.y + 11), 9)
            self._text(str(card.elixir), self.font_s, (255, 255, 255),
                       center=(r.x + 10, r.y + 11))
            self._text(self._fit(card.name, self.font_s, r.w - 6), self.font_s,
                       cfg.COLOR_TEXT, center=(r.centerx, r.bottom - 11))
            if evo_p is not None:
                if evo_now:
                    self._text("EVO", self.font_sb, (220, 160, 255),
                               center=(r.right - 16, r.y + 11), outline=True)
                else:                         # charge pips
                    for k in range(evo_p[1]):
                        pygame.draw.circle(self.screen, (200, 130, 255) if k < evo_p[0]
                                           else (60, 50, 80), (r.right - 10 - k * 9, r.y + 10), 3)
            if key in m.hero_cards[PLAYER]:
                self._text("HERO", self.font_s, (255, 200, 90),
                           center=(r.right - 18, r.y + 24), outline=True)
        # next card in a framed box on the right
        nk = m.next_card[PLAYER]
        if nk:
            hand = self._hand_slot_rects()
            nb = pygame.Rect(hand[-1].right + 12, hand[-1].y + 16,
                             self.NEXT_BOX_W - 8, 62)
            if nb.right > cfg.WINDOW_W - 4:
                nb.right = cfg.WINDOW_W - 4
            pygame.draw.rect(self.screen, (30, 34, 46), nb, border_radius=8)
            pygame.draw.rect(self.screen, (70, 78, 100), nb, 1, border_radius=8)
            self._text("Next", self.font_s, (170, 178, 195),
                       center=(nb.centerx, nb.y + 9))
            self.screen.blit(sprites.get_sprite(nk, 38), (nb.centerx - 19, nb.y + 19))
        self._draw_ability_button()
        self._draw_hero_button()

    def _hero_btn_rect(self):
        r = 24
        return pygame.Rect(cfg.ARENA_X0 + cfg.ARENA_PX_W - 2 * r - 8,
                           cfg.ARENA_Y0 + cfg.ARENA_PX_H - 2 * r - 8, 2 * r, 2 * r)

    def _draw_hero_button(self):
        h, ready, cost = self.match.hero_status(PLAYER)
        if h is None:
            return
        r = self._hero_btn_rect()
        cx, cy = r.center
        rad = r.w // 2
        used = h.ability_uses <= 0
        pygame.draw.circle(self.screen, (15, 18, 26), (cx, cy + 2), rad)
        base = (255, 196, 80) if ready else (95, 88, 70)
        if ready:
            pulse = 0.5 + 0.5 * math.sin(self._now() * 6)
            pygame.draw.circle(self.screen, (255, 220, 120), (cx, cy), rad + 3 + int(2 * pulse), 2)
        pygame.draw.circle(self.screen, base, (cx, cy), rad)
        pygame.draw.circle(self.screen, (255, 240, 160) if ready else (60, 60, 55),
                           (cx, cy), rad, 2)
        self.screen.blit(sprites.get_sprite(h.key, rad + 6),
                         (cx - (rad + 6) // 2, cy - (rad + 6) // 2))
        if used:
            ov = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            pygame.draw.circle(ov, (0, 0, 0, 170), (rad, rad), rad)
            self.screen.blit(ov, r.topleft)
            self._text("USED", self.font_s, (230, 230, 230), center=(cx, cy))
        pygame.draw.circle(self.screen, cfg.COLOR_ELIXIR, (r.x + 4, r.y + 4), 8)
        self._text(str(cost), self.font_s, (255, 255, 255), center=(r.x + 4, r.y + 4))
        label = self.font_s.render(h.hero_def.ability, True,
                                   (255, 226, 150) if not used else (150, 150, 150))
        chip = pygame.Rect(r.x - label.get_width() - 16, cy - 9, label.get_width() + 10, 18)
        pygame.draw.rect(self.screen, (20, 24, 34), chip, border_radius=6)
        pygame.draw.rect(self.screen, (170, 140, 70), chip, 1, border_radius=6)
        self.screen.blit(label, (chip.x + 5, chip.y + 3))

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

    def _star(self, cx, cy, r, filled):
        pts = []
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5
            rr = r if k % 2 == 0 else r * 0.45
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
        pygame.draw.polygon(self.screen, (0, 0, 0), [(x + 2, y + 3) for x, y in pts])
        pygame.draw.polygon(self.screen, (250, 206, 92) if filled else (60, 62, 74), pts)
        pygame.draw.polygon(self.screen, (120, 80, 20) if filled else (30, 32, 40), pts, 2)

    def _draw_result(self):
        overlay = pygame.Surface((cfg.WINDOW_W, cfg.WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))
        cx = cfg.WINDOW_W // 2
        win = self.result_text == "VICTORY!"
        color = (120, 240, 120) if win else \
                (240, 120, 120) if self.result_text == "DEFEAT" else (230, 230, 230)
        panel = self._panel(self._result_panel(), border=color, radius=16)
        top = panel.y
        self._text(self.result_text, self.font_xl, color, center=(cx, top + 38))
        mid = top + 96
        if self.level_run is not None:
            run = self.level_run
            if self.mode == "endless":
                self._text("Survived %d waves" % run.waves_survived(),
                           self.font_m, center=(cx, mid - 6))
                self._text("Best: wave %d" % self.profile.endless_best, self.font_sb,
                           (220, 224, 236), center=(cx, mid + 22))
            else:
                stars = run.stars() if win else 0
                for i in range(3):
                    self._star(cx - 54 + i * 54, mid - 10 - (8 if i == 1 else 0), 22, i < stars)
                msg = ("All %d waves survived" % run.total_waves if win
                       else "Fell on wave %d of %d" % (run.wave_number, run.total_waves))
                self._text(msg, self.font_sb, (220, 224, 236), center=(cx, mid + 24))
        else:
            self._crown_icon(cx - 62, mid - 6, cfg.COLOR_TEAM_PLAYER)
            self._crown_icon(cx + 62, mid - 6, cfg.COLOR_TEAM_ENEMY)
            self._text("%d  -  %d" % (self.match.crowns[PLAYER], self.match.crowns[ENEMY]),
                       self.font_l, center=(cx, mid - 6))
        # rewards
        y = mid + 46
        for label, gold, shards in self.last_rewards:
            self._text(label, self.font_sb, (230, 232, 240), topleft=(panel.x + 24, y))
            x = panel.right - 24
            if shards:
                t = "+%d" % shards
                w = self.font_sb.size(t)[0]
                self._text(t, self.font_sb, (196, 120, 255), topleft=(x - w, y))
                self._shard(x - w - 12, y + 9, 7)
                x -= w + 30
            if gold:
                t = "+%d" % gold
                w = self.font_sb.size(t)[0]
                self._text(t, self.font_sb, (250, 206, 92), topleft=(x - w, y))
                self._coin(x - w - 12, y + 9, 7)
            y += 22
        for b in self._result_buttons():
            b.draw(self.screen, self.font_m if b.rect.h > 38 else self.font_sb)

    # --------------------------------------------------------- levels screen
    def _draw_levels(self):
        cx = cfg.WINDOW_W // 2
        total_stars = sum(self.progress.get(lv.key, {}).get("stars", 0)
                          for lv in levels.LEVELS)
        self._screen_title("Levels", 30, "Survive every wave.   Stars: %d / %d"
                           % (total_stars, 3 * len(levels.LEVELS)))
        btns = self._level_buttons()
        view = self._levels_view()
        self.screen.set_clip(view)
        for i, lv in enumerate(levels.LEVELS):
            r = self._level_card_rect(i)
            if r.bottom < view.top or r.top > view.bottom:
                continue
            rec = self.progress.get(lv.key, {})
            stars = rec.get("stars", 0)
            done = stars > 0
            border = (214, 176, 84) if not done else (120, 200, 120)
            self._panel(r, border=border, radius=14, top=(60, 52, 72),
                        bottom=(34, 30, 46))
            # picture + level number
            pic = pygame.Rect(r.x + 10, r.y + 10, 72, 72)
            pygame.draw.rect(self.screen, (20, 18, 28), pic, border_radius=12)
            self.screen.blit(sprites.get_sprite(lv.icon, 66), (pic.x + 3, pic.y + 3))
            pygame.draw.rect(self.screen, border, pic, 2, border_radius=12)
            badge = pygame.Rect(0, 0, 26, 19)
            badge.center = (pic.x + 10, pic.bottom - 8)
            pygame.draw.rect(self.screen, (40, 32, 56), badge, border_radius=8)
            pygame.draw.rect(self.screen, border, badge, 2, border_radius=8)
            self._text(str(i + 1), self.font_sb, center=badge.center, outline=True)
            for k in range(3):
                self._star(pic.x + 12 + k * 24, r.bottom - 14, 9, k < stars)
            tx = pic.right + 12
            lo, hi = levels.enemy_level_range(lv)
            info = "%d waves  -  enemy Lv %d-%d  -  rec. Lv %d" % (
                len(lv.waves), lo, hi, levels.recommended_level(lv))
            self._text(lv.name, self.font_m, topleft=(tx, r.y + 8))
            self._text(info, self.font_s, (250, 206, 92), topleft=(tx, r.y + 32))
            # description, wrapped to 2 lines (clear of the Play button)
            words, line, yy, n = lv.desc.split(), "", r.y + 52, 0
            maxw = r.right - tx - 10
            for w_ in words:
                test = (line + " " + w_).strip()
                lim = maxw if n == 0 else maxw - 96
                if self.font_s.size(test)[0] > lim:
                    if n == 1:
                        line = line.rstrip(".,- ") + "..."
                        break
                    self._text(line, self.font_s, (206, 210, 224), topleft=(tx, yy))
                    yy += 16
                    n += 1
                    line = w_
                else:
                    line = test
            if line:
                self._text(line, self.font_s, (206, 210, 224), topleft=(tx, yy))
            if not self._level_unlocked(i):
                shade = pygame.Surface(r.size, pygame.SRCALPHA)
                pygame.draw.rect(shade, (10, 10, 16, 150), shade.get_rect(), border_radius=14)
                self.screen.blit(shade, r.topleft)
                need = levels.stars_needed(i)
                self._text("Needs %d stars (have %d)" % (need, self._total_stars()),
                           self.font_sb, (240, 200, 120), topleft=(tx, r.bottom - 26))
            elif rec.get("plays"):
                self._text("won %d / played %d" % (rec.get("wins", 0), rec["plays"]),
                           self.font_s, (170, 176, 196), topleft=(tx, r.bottom - 22))
        for b in btns[:len(levels.LEVELS)]:
            r = b.rect
            if r.bottom >= view.top and r.top <= view.bottom:
                was = b.enabled
                b.enabled = self._level_unlocked(b.level_index)
                b.draw(self.screen, self.font_m)
                b.enabled = was
        self.screen.set_clip(None)
        # soft fade at the list edges so cards don't end in a hard cut
        for top in (True, False):
            fade = pygame.Surface((view.w, 14), pygame.SRCALPHA)
            for k in range(14):
                a = int(150 * (1 - k / 14))
                pygame.draw.line(fade, (14, 12, 22, a), (0, k if top else 13 - k),
                                 (view.w, k if top else 13 - k))
            self.screen.blit(fade, (view.x, view.y if top else view.bottom - 14))
        track, thumb = self._levels_scrollbar()
        pygame.draw.rect(self.screen, (30, 30, 44), track, border_radius=4)
        pygame.draw.rect(self.screen, (214, 176, 84), thumb, border_radius=4)
        for b in btns[len(levels.LEVELS):]:
            b.draw(self.screen, self.font_m)
        # the Levels deck (separate from your battle deck: no win conditions)
        deck = self.level_deck
        sz, gap = 36, 6
        total = 8 * sz + 7 * gap
        x0 = cx - total // 2
        strip = self._panel((x0 - 12, cfg.WINDOW_H - 134, total + 24, 60))
        self._text("Level Deck  (no win conditions)", self.font_sb, center=(cx, strip.y - 2))
        for i, k in enumerate(deck):
            self.screen.blit(sprites.get_sprite(k, sz), (x0 + i * (sz + gap), strip.y + 14))


