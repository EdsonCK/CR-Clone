"""
============================================================================
  HOME.PY  --  The tabbed home screen (mixed into game.Game)
============================================================================

Like Clash Royale, the menus are tabs along the bottom of the screen:

    Shop  |  Deck  |  Battle  |  Levels  |  Modes

  * SHOP    spend gems on gold, Evo shards and Hero coins, plus three
            daily deals (shop.py).
  * DECK    the deck builder, live: changes save as soon as the deck has 8
            cards. "Cards" opens the collection / upgrade screen.
  * BATTLE  the home tab: your arena and trophies, the Battle button (Trophy
            Road), a Friendly Battle (pick the AI yourself), achievements,
            the next road reward, the daily bonus and your deck.
  * LEVELS  the 30 wave levels.
  * MODES   Special Battles, Endless Survival and the Sandbox.

The top bar shows your King level (tap it for the King Tower screen),
trophies, gold, gems, Evo shards and Hero coins; the three-bar button on
the right opens Settings, AI Deck, Records, Last Match, How To Play and
Quit.

Tabs reuse the existing screens: they're drawn into the space between the
top bar and the tab bar (see _embedded()), so each screen lays itself out
for that smaller area without knowing it.
============================================================================
"""

import contextlib
import datetime
import math

import pygame

import config as cfg
import cards
import king
import shop
import sprites
import trophy
import towers
from ui import Button, WHITE, lt_c, dk_c, grad_rect, render_text

TOP_H = 52                    # top bar (resources + menu button)
TAB_H = 72                    # bottom tab bar
TABS = [("shop", "Shop"), ("deck", "Deck"), ("menu", "Battle"),
        ("levels", "Levels"), ("modes", "Modes")]
HOME_STATES = tuple(s for s, _ in TABS)
REAL_H = cfg.WINDOW_H         # the real window height (cfg.WINDOW_H is the
                              # content height while a tab is being drawn)
GOLD_COL = (255, 214, 90)
SHARD_COL = (200, 140, 255)


class HomeMixin:
    # ------------------------------------------------------------ layout
    def _home_active(self):
        """True while one of the tabs is showing (with the tab bar)."""
        if self.state not in HOME_STATES:
            return False
        if self.state == "deck":
            return self.deck_mode == "player" and self.deck_return == "menu"
        return True

    @staticmethod
    def _home_content():
        return pygame.Rect(0, TOP_H, cfg.WINDOW_W, REAL_H - TOP_H - TAB_H)

    @staticmethod
    def _tab_rects():
        w = cfg.WINDOW_W / len(TABS)
        y = REAL_H - TAB_H
        return [(pygame.Rect(int(i * w), y, int((i + 1) * w) - int(i * w), TAB_H), st, lbl)
                for i, (st, lbl) in enumerate(TABS)]

    @staticmethod
    def _menu_btn_rect():
        return pygame.Rect(cfg.WINDOW_W - 52, 8, 42, 36)

    def _dropdown_items(self):
        items = [("Settings", self._open_settings),
                 ("AI Deck", lambda: self._open_aideck("menu")),
                 ("Records", lambda: self._goto("records")),
                 ("Last Match", lambda: self._open_stats("menu") if self.match else None),
                 ("How To Play", lambda: self._goto("help")),
                 ("Quit", self._quit)]
        x, w, h = cfg.WINDOW_W - 212, 202, 40
        out = []
        for i, (lbl, cb) in enumerate(items):
            b = Button((x, TOP_H + 4 + i * (h + 4), w, h), lbl, cb,
                       "danger" if lbl == "Quit" else "dark")
            b.enabled = not (lbl == "Last Match" and self.match is None)
            out.append(b)
        return out

    @contextlib.contextmanager
    def _embedded(self):
        """Run a screen's drawing / input inside the tab content area: it gets
        a surface of the content size, cfg.WINDOW_H is the content height and
        the mouse is reported relative to the area."""
        area = self._home_content()
        if getattr(self, "embedded", False):       # already inside one
            yield area
            return
        surf = getattr(self, "_home_surf", None)
        if surf is None or surf.get_size() != area.size:
            surf = self._home_surf = pygame.Surface(area.size)
        old_screen, old_h = self.screen, cfg.WINDOW_H
        old_get = pygame.mouse.get_pos
        surf.blit(old_screen, (0, 0), area)       # the backdrop behind it
        self.screen = surf
        cfg.WINDOW_H = area.h
        pygame.mouse.get_pos = lambda: (old_get()[0], old_get()[1] - area.y)
        self.embedded = True
        try:
            yield area
        finally:
            self.embedded = False
            pygame.mouse.get_pos = old_get
            cfg.WINDOW_H = old_h
            self.screen = old_screen

    def _embedded_if(self):
        if self._home_active() and self.state in ("deck", "levels", "modes"):
            return self._embedded()
        return contextlib.nullcontext(None)

    # ------------------------------------------------------------ navigation
    def _go_tab(self, state):
        self.dropdown = False
        if state == self.state and self._home_active():
            return
        if self.state == "deck" and self._home_active():
            self._deck_autosave()
        if state == "deck":
            self._open_deck_editor("player", "menu")
        else:
            self.state = state
            if state == "levels":
                self._set_levels_scroll(getattr(self, "levels_scroll", 0))
        self.sfx.play("ui_click", 0.5, min_gap=0.0)

    def _deck_autosave(self):
        if self.deck_mode == "player" and len(self.player_deck) == cfg.DECK_SIZE:
            self._save_deck()

    def _home_escape(self):
        if getattr(self, "dropdown", False):
            self.dropdown = False
        elif self.state != "menu":
            self._go_tab("menu")

    # ------------------------------------------------------------ input
    def _home_click(self, pos, button=1):
        if getattr(self, "dropdown", False):
            if button == 1:
                for b in self._dropdown_items():
                    if b.rect.collidepoint(pos):
                        self.dropdown = False
                        if b.enabled:
                            b.cb()
                        return
            self.dropdown = False
            return
        if button == 1 and self._menu_btn_rect().collidepoint(pos):
            self.dropdown = True
            self.sfx.play("ui_click", 0.5, min_gap=0.0)
            return
        if pos[1] >= REAL_H - TAB_H:
            if button == 1:
                for r, st, _ in self._tab_rects():
                    if r.collidepoint(pos):
                        self._go_tab(st)
                        return
            return
        if pos[1] < TOP_H:
            if button == 1 and self._xp_badge_rect().collidepoint(pos):
                self._open_king("menu" if self.state == "menu" else self.state)
            return
        area = self._home_content()
        if self.state == "menu":
            if button == 1:
                self._battle_tab_click(pos)
        elif self.state == "shop":
            if button == 1:
                self._shop_click(pos)
        else:
            with self._embedded():
                p = (pos[0], pos[1] - area.y)
                if self.state == "deck":
                    self._deck_click(p, button)
                    self._deck_autosave()
                elif button == 1 and self.state == "levels":
                    self._levels_click(p)
                elif button == 1 and self.state == "modes":
                    self._modes_click(p)

    def _home_motion(self, pos):
        with self._embedded() as area:
            y = pos[1] - area.y
            if self.state == "deck" and self.deck_drag:
                self._deck_drag_to(y)
            elif self.state == "levels" and self.levels_drag:
                self._levels_drag_to(y)

    # ------------------------------------------------------------ drawing
    # ------------------------------------------------------------ backdrop
    # each tab sits on a slowly drifting diagonal checkerboard in its colour
    TAB_COLORS = {
        "menu":   ((34, 74, 150), (54, 104, 188)),      # Battle: royal blue
        "deck":   ((28, 98, 56), (46, 130, 78)),        # Deck: green
        "shop":   ((74, 42, 130), (100, 62, 166)),      # Shop: purple
        "modes":  ((98, 26, 42), (130, 40, 60)),        # Modes: maroon
        "levels": ((170, 88, 34), (200, 112, 50)),      # Levels: burnt orange
    }
    CHECK = 34                    # half the diagonal of one checker square

    def _checker_tile(self, state):
        cache = self.__dict__.setdefault("_checker_cache", {})
        cols = self.TAB_COLORS.get(state, self.TAB_COLORS["menu"])
        if cols in cache:
            return cache[cols]
        s = self.CHECK
        W, H = cfg.WINDOW_W + 4 * s, REAL_H + 4 * s
        surf = pygame.Surface((W, H))
        surf.fill(cols[0])
        # diamonds touching only at their corners: a checkerboard turned 45°
        for i in range(-1, W // (2 * s) + 2):
            for j in range(-1, H // (2 * s) + 2):
                x, y = i * 2 * s, j * 2 * s
                pygame.draw.polygon(surf, cols[1], [(x, y - s), (x + s, y), (x, y + s), (x - s, y)])
        # light from above, darker toward the bottom and the edges
        shade = pygame.Surface((cfg.WINDOW_W, REAL_H), pygame.SRCALPHA)
        for y in range(REAL_H):
            f = y / REAL_H
            a = int(40 * max(0.0, f - 0.25) / 0.75 * 1.6)
            pygame.draw.line(shade, (0, 0, 0, min(90, a)), (0, y), (cfg.WINDOW_W, y))
        glow = pygame.Surface((cfg.WINDOW_W, REAL_H), pygame.SRCALPHA)
        for k in range(14):
            rr = int(cfg.WINDOW_W * (0.9 - k * 0.05))
            pygame.draw.ellipse(glow, (255, 255, 255, 4),
                                pygame.Rect(cfg.WINDOW_W // 2 - rr, -rr // 2, 2 * rr, rr + 60))
        for i in range(22):
            a = int(4 * (22 - i) / 22 * 8)
            pygame.draw.rect(shade, (0, 0, 0, a), (i * 2, i * 2, cfg.WINDOW_W - i * 4,
                                                    REAL_H - i * 4), 2, border_radius=24)
        shade.blit(glow, (0, 0))
        cache[cols] = (surf, shade)
        return cache[cols]

    def _checker_backdrop(self, state):
        tile, shade = self._checker_tile(state)
        s2 = 2 * self.CHECK
        d = (self._now() * 10.0) % s2               # slow diagonal drift
        self.screen.blit(tile, (-s2 + d, -s2 + d))
        self.screen.blit(shade, (0, 0))

    def _draw_home(self):
        self._checker_backdrop(self.state)
        if self.state == "menu":
            self._draw_battle_tab()
        elif self.state == "shop":
            self._draw_shop_tab()
        else:
            with self._embedded() as area:
                if self.state == "deck":
                    self._draw_deck()
                elif self.state == "levels":
                    self._draw_levels()
                elif self.state == "modes":
                    self._draw_modes()
                surf = self.screen
            self.screen.blit(surf, area.topleft)
        self._draw_home_topbar()
        self._draw_tabbar()
        if getattr(self, "dropdown", False):
            self._draw_dropdown()

    @staticmethod
    def _xp_badge_rect():
        return pygame.Rect(6, 6, 40, 40)

    def _draw_home_topbar(self):
        W = cfg.WINDOW_W
        pr = self.profile
        self.screen.blit(grad_rect(W, TOP_H, (40, 44, 66), (24, 26, 40), 0), (0, 0))
        pygame.draw.line(self.screen, (92, 84, 64), (0, TOP_H - 1), (W, TOP_H - 1), 2)
        cy = TOP_H // 2
        # counters lag behind while collected rewards fly in (rewardfx.py)
        slots = self._rfx_slots()
        # King level: blue XP badge with a progress ring
        br = self._xp_badge_rect()
        lv, into, need = king.progress(self._rfx_shown("xp"))
        pygame.draw.circle(self.screen, (16, 20, 34), br.center, 19)
        frac = into / need if need else 1.0
        if frac > 0:
            pygame.draw.arc(self.screen, (120, 200, 255), br.inflate(-2, -2),
                            math.pi / 2 - 2 * math.pi * frac, math.pi / 2, 3)
        self._xp_icon(br.centerx, br.centery, 14)
        self._text(str(lv), self.font_sb, center=br.center)
        if br.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.circle(self.screen, (255, 222, 110), br.center, 20, 1)
        for kind in ("trophy", "gold", "gems", "shards", "coins"):
            (ix, iy), chip = slots[kind]
            pygame.draw.rect(self.screen, (18, 20, 30), chip, border_radius=13)
            pygame.draw.rect(self.screen, (70, 74, 96), chip, 1, border_radius=13)
            if kind == "trophy":
                self._trophy_icon(ix, iy, 8)
            else:
                self._reward_icon(kind, ix, iy, 8)
            self._text("%d" % self._rfx_shown(kind), self.font_sb, self._rfx_col(kind),
                       topleft=(chip.x + 23, cy - 9))
        # the three-bar menu button
        r = self._menu_btn_rect()
        hover = r.collidepoint(pygame.mouse.get_pos()) or getattr(self, "dropdown", False)
        pygame.draw.rect(self.screen, (70, 78, 104) if hover else (52, 58, 80), r,
                         border_radius=8)
        pygame.draw.rect(self.screen, (120, 128, 160), r, 1, border_radius=8)
        for k in range(3):
            y = r.y + 10 + k * 8
            pygame.draw.line(self.screen, WHITE, (r.x + 10, y), (r.right - 11, y), 3)

    def _draw_tabbar(self):
        W, H = cfg.WINDOW_W, cfg.WINDOW_H
        y0 = H - TAB_H
        self.screen.blit(grad_rect(W, TAB_H, (34, 38, 58), (16, 18, 28), 0), (0, y0))
        pygame.draw.line(self.screen, (120, 100, 60), (0, y0), (W, y0), 2)
        mouse = pygame.mouse.get_pos()
        cur = self.state
        for r, st, lbl in self._tab_rects():
            sel = st == cur
            hover = r.collidepoint(mouse)
            if sel:
                tab = r.inflate(-6, 0).move(0, -8)
                tab.h += 8
                self.screen.blit(grad_rect(tab.w, tab.h, (88, 132, 214), (46, 78, 150), 10),
                                 tab.topleft)
                pygame.draw.rect(self.screen, (255, 222, 110), tab, 2, border_radius=10)
            elif hover:
                pygame.draw.rect(self.screen, (50, 56, 80), r.inflate(-6, -8), border_radius=10)
            if r.x > 0:
                pygame.draw.line(self.screen, (52, 56, 76), (r.x, y0 + 10), (r.x, H - 10), 1)
            icy = r.y + (20 if sel else 26)
            self._tab_icon(st, r.centerx, icy, 1.25 if sel else 1.0)
            col = WHITE if sel else (180, 186, 205)
            self._text(lbl, self.font_sb if sel else self.font_s, col,
                       center=(r.centerx, r.bottom - (17 if sel else 13)))
            if st == "menu":
                import achievements as ach
                n = ach.claimable(self)
                if n and not sel:
                    pygame.draw.circle(self.screen, (220, 60, 60), (r.right - 22, r.y + 12), 9)
                    self._text(str(n), self.font_sb, center=(r.right - 22, r.y + 12))

    def _tab_icon(self, st, cx, cy, s):
        """Little vector icons for the tabs."""
        sc = self.screen

        def P(pts):
            return [(cx + x * s, cy + y * s) for x, y in pts]
        if st == "shop":                       # a chest
            body = pygame.Rect(0, 0, int(26 * s), int(16 * s))
            body.center = (cx, cy + int(3 * s))
            lid = pygame.Rect(body.x, body.y - int(8 * s), body.w, int(10 * s))
            pygame.draw.rect(sc, (150, 92, 44), body, border_radius=3)
            pygame.draw.rect(sc, (182, 116, 58), lid, border_top_left_radius=8,
                             border_top_right_radius=8)
            pygame.draw.rect(sc, (250, 206, 92), (cx - 3 * s, body.y - 2 * s, 6 * s, 7 * s))
            pygame.draw.rect(sc, (70, 40, 20), body.union(lid), 2, border_radius=4)
        elif st == "deck":                     # two fanned cards
            for ang, col in ((-14, (88, 132, 214)), (12, (226, 98, 88))):
                surf = pygame.Surface((int(16 * s), int(22 * s)), pygame.SRCALPHA)
                pygame.draw.rect(surf, col, surf.get_rect(), border_radius=3)
                pygame.draw.rect(surf, (20, 20, 30), surf.get_rect(), 2, border_radius=3)
                rs = pygame.transform.rotate(surf, ang)
                sc.blit(rs, rs.get_rect(center=(cx + (-4 if ang < 0 else 4) * s, cy)))
        elif st == "menu":                     # crossed swords
            for d in (-1, 1):
                pygame.draw.line(sc, (225, 230, 240), (cx - 11 * s * d, cy - 11 * s),
                                 (cx + 9 * s * d, cy + 9 * s), max(3, int(4 * s)))
                pygame.draw.line(sc, (250, 206, 92), (cx + 5 * s * d, cy + 11 * s),
                                 (cx + 11 * s * d, cy + 5 * s), max(3, int(4 * s)))
        elif st == "levels":                   # a skull
            pygame.draw.circle(sc, (232, 232, 220), (cx, cy - 2 * s), int(10 * s))
            pygame.draw.rect(sc, (232, 232, 220), (cx - 6 * s, cy + 4 * s, 12 * s, 7 * s),
                             border_radius=2)
            for d in (-1, 1):
                pygame.draw.circle(sc, (30, 30, 40), (cx + 4 * s * d, cy - 2 * s), int(3 * s))
        elif st == "modes":                    # a star burst
            pts = []
            for k in range(10):
                a = -math.pi / 2 + k * math.pi / 5
                rr = (12 if k % 2 == 0 else 5) * s
                pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
            pygame.draw.polygon(sc, (235, 110, 200), pts)
            pygame.draw.polygon(sc, (90, 30, 80), pts, 2)

    def _draw_dropdown(self):
        items = self._dropdown_items()
        box = items[0].rect.unionall([b.rect for b in items]).inflate(12, 12)
        shade = pygame.Surface((cfg.WINDOW_W, cfg.WINDOW_H), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 90))
        self.screen.blit(shade, (0, 0))
        self._panel(box)
        for b in items:
            b.draw(self.screen, self.font_m)
        self._text("v" + cfg.GAME_VERSION, self.font_s, (150, 156, 175),
                   center=(box.centerx, box.bottom + 12))

    # ------------------------------------------------------------ battle tab
    def _battle_tab_layout(self):
        W = cfg.WINDOW_W
        cx = W // 2
        y = TOP_H
        return {
            "banner": pygame.Rect(18, y + 16, W - 36, 206),
            "battle": pygame.Rect(cx - 140, y + 244, 280, 78),
            "friendly": pygame.Rect(18, y + 346, (W - 46) // 2, 48),
            "ach": pygame.Rect(W - 18 - (W - 46) // 2, y + 346, (W - 46) // 2, 48),
            "rewards": pygame.Rect(18, y + 412, W - 36, 124),
            "deck": pygame.Rect(18, y + 552, W - 36, 106),
        }

    def _battle_tab_buttons(self):
        L = self._battle_tab_layout()
        swords = lambda s_, x, y, sz: self._tab_icon_at("menu", x, y, sz / 30.0)
        cup = lambda s_, x, y, sz: self._trophy_icon(x, y, int(sz * 0.42))
        return [Button(L["battle"], "Battle", self._start_trophy_battle, "gold", chunky=True,
                       icon=swords),
                Button(L["friendly"], "Friendly Battle", self._open_prematch, "primary",
                       chunky=True),
                Button(L["ach"], "Achievements", self._open_achievements, "primary",
                       chunky=True, icon=cup)]

    def _tab_icon_at(self, st, cx, cy, s):
        self._tab_icon(st, int(cx), int(cy), s)

    @property
    def menu_buttons(self):
        """Clickable things on the home screen (tabs + Battle-tab buttons),
        kept under the old name for scripts and tests."""
        out = [Button(r, lbl, (lambda st=st: self._go_tab(st)), "dark")
               for r, st, lbl in self._tab_rects()]
        for b in out:
            if b.label == "Battle":
                b.label = "Battle Tab"
        out += self._battle_tab_buttons()
        out.append(Button(self._menu_btn_rect(), "Menu",
                          lambda: setattr(self, "dropdown", True), "dark"))
        return out

    @menu_buttons.setter
    def menu_buttons(self, v):
        pass                                  # built on demand now

    def _battle_tab_click(self, pos):
        L = self._battle_tab_layout()
        for b in self._battle_tab_buttons():
            if b.rect.collidepoint(pos):
                b.cb()
                return
        if L["banner"].collidepoint(pos):
            self._open_trophy()
        elif L["deck"].collidepoint(pos):
            self._go_tab("deck")

    def _draw_battle_tab(self):
        import achievements as ach
        pr = self.profile
        L = self._battle_tab_layout()
        mouse = pygame.mouse.get_pos()
        t = pr.trophies
        a = trophy.arena(t)
        nxt = trophy.next_arena(t)
        # ---- arena banner ----
        r = L["banner"]
        hov = r.collidepoint(mouse)
        col = a.color
        self.screen.blit(grad_rect(r.w, r.h, lt_c(col, 10), dk_c(col, 110), 16), r.topleft)
        pygame.draw.rect(self.screen, (255, 222, 110) if hov else lt_c(col, 40), r, 3,
                         border_radius=16)
        self._mini_arena(pygame.Rect(r.x + 14, r.y + 14, 120, r.h - 28), col)
        tx = r.x + 150
        self._text("Arena %d" % (trophy.arena_index(t) + 1), self.font_sb, (235, 235, 225),
                   topleft=(tx, r.y + 14))
        self._text(self._fit(a.name, self.font_l, r.right - tx - 12), self.font_l,
                   topleft=(tx, r.y + 32))
        self._trophy_icon(tx + 14, r.y + 92, 14)
        self._text("%d" % t, self.font_xl, GOLD_COL, topleft=(tx + 34, r.y + 66))
        self._text("best %d" % pr.best_trophies, self.font_s, (230, 225, 210),
                   topleft=(tx + 40 + self.font_xl.size("%d" % t)[0], r.y + 92))
        bar = pygame.Rect(tx, r.y + 126, r.right - tx - 16, 12)
        pygame.draw.rect(self.screen, (20, 20, 28), bar, border_radius=6)
        if nxt:
            frac = (t - a.trophies) / max(1, nxt.trophies - a.trophies)
            pygame.draw.rect(self.screen, (250, 206, 92),
                             (bar.x, bar.y, int(bar.w * min(1, frac)), bar.h), border_radius=6)
            nx_txt = "next: %s at %d" % (nxt.name, nxt.trophies)
        else:
            pygame.draw.rect(self.screen, (250, 206, 92), bar, border_radius=6)
            nx_txt = "top arena reached"
        self._text(self._fit(nx_txt, self.font_s, bar.w), self.font_s, (235, 235, 225),
                   topleft=(bar.x, bar.bottom + 4))
        ai, lv = self._trophy_opponent()
        ne, nh = trophy.bot_specials(t)
        extra = ("" if not (ne or nh) else
                 ", %s" % " + ".join(([("%d Evo" % ne) + ("s" if ne > 1 else "")] if ne else [])
                                     + (["Hero"] if nh else [])))
        opp = "Opponent: %s AI, cards Lv %d%s" % (cfg.AI_LEVELS[ai]["name"], lv, extra)
        self._text(self._fit(opp, self.font_s, bar.w), self.font_s, (255, 230, 170),
                   topleft=(bar.x, bar.bottom + 22))
        self._text("Trophy Road >", self.font_sb, (255, 240, 200),
                   topleft=(r.right - 14 - self.font_sb.size("Trophy Road >")[0], r.bottom - 24))
        # ---- buttons ----
        for b in self._battle_tab_buttons():
            if b.label == "Battle":
                b.draw(self.screen, self.font_xl)
            else:
                b.draw(self.screen, self.font_m)
                if b.label == "Achievements":
                    n = ach.claimable(self)
                    if n:
                        pygame.draw.circle(self.screen, (220, 60, 60),
                                           (b.rect.right - 8, b.rect.y + 6), 11)
                        self._text(str(n), self.font_sb, center=(b.rect.right - 8, b.rect.y + 6))
        win = trophy.WIN_TROPHIES
        self._text("Trophy Road battle: +%d trophies per win" % win, self.font_s,
                   (210, 214, 230), center=(cfg.WINDOW_W // 2, L["battle"].bottom + 6))
        # ---- rewards ----
        rr = self._panel(L["rewards"])
        self._text("Rewards", self.font_m, topleft=(rr.x + 12, rr.y + 8))
        road = [row for row in trophy.road_rewards() if row[0] > pr.road_paid]
        y = rr.y + 40
        if road:
            tt, label, rw, tt_key = road[0]
            need = max(0, tt - t)
            s = "Next road reward at %d (%d to go):" % (tt, need)
            self._text(s, self.font_s, (220, 224, 240), topleft=(rr.x + 14, y))
            self._reward_row(rw, rr.right - 14, y + 8, gap=6)
            if tt_key:
                self._text("+ unlocks %s" % towers.get(tt_key).name, self.font_s,
                           (255, 220, 140), topleft=(rr.x + 14, y + 18))
        else:
            self._text("Every road reward collected!", self.font_s, (220, 224, 240),
                       topleft=(rr.x + 14, y))
        today = datetime.date.today().isoformat()
        ready = pr.totals.get("daily") != today
        dtxt = ("First win of the day: ready  (+60 gold, +1 shard)" if ready
                else "First win of the day: collected - back tomorrow")
        self._text(dtxt, self.font_s, (150, 230, 150) if ready else (170, 176, 195),
                   topleft=(rr.x + 14, y + 40))
        n = ach.claimable(self)
        self._text("%d achievement reward%s to claim" % (n, "" if n == 1 else "s") if n
                   else "No achievement rewards waiting", self.font_s,
                   (255, 200, 120) if n else (170, 176, 195), topleft=(rr.x + 14, y + 58))
        # ---- your deck ----
        dr = L["deck"]
        hov = dr.collidepoint(mouse)
        self._panel(dr, border=(255, 222, 110) if hov else (92, 100, 128))
        slot = self.profile.active_slot + 1
        tt_name = towers.get(self._tower_troop(self.profile.active_slot)).name \
            if hasattr(self, "_tower_troop") else ""
        head = "Deck %d   -   Tower: %s" % (slot, tt_name)
        self._text(head, self.font_sb, topleft=(dr.x + 12, dr.y + 8))
        if self.player_deck:
            avg = sum(cards.CARDS[k].elixir for k in self.player_deck) / len(self.player_deck)
            at = "avg %.1f" % avg
            self._text(at, self.font_s, (230, 150, 255),
                       topleft=(dr.right - 12 - self.font_s.size(at)[0], dr.y + 10))
        n = max(1, len(self.player_deck))
        sz = 50
        gap = (dr.w - 24 - 8 * sz) // 7
        for i, k in enumerate(self.player_deck):
            x = dr.x + 12 + i * (sz + gap)
            self.screen.blit(sprites.get_sprite(k, sz), (x, dr.y + 42))

    def _mini_arena(self, r, col):
        """A tiny arena picture for the banner: grass, river, six towers."""
        self.screen.blit(grad_rect(r.w, r.h, (96, 168, 82), (70, 138, 64), 10), r.topleft)
        ry = r.centery
        pygame.draw.rect(self.screen, (70, 150, 220), (r.x, ry - 5, r.w, 10))
        for bx in (r.x + r.w * 0.25, r.x + r.w * 0.75):
            pygame.draw.rect(self.screen, (150, 110, 70), (bx - 6, ry - 7, 12, 14))
        for team, y in ((0, r.bottom - 26), (1, r.y + 26)):
            c = cfg.COLOR_TEAM_PLAYER if team == 0 else cfg.COLOR_TEAM_ENEMY
            for x, big in ((r.x + r.w * 0.25, 0), (r.x + r.w * 0.75, 0), (r.centerx, 1)):
                yy = y + (10 if team == 0 else -10) * big
                s = 9 + 3 * big
                pygame.draw.rect(self.screen, (190, 190, 200), (x - s, yy - s, 2 * s, 2 * s),
                                 border_radius=3)
                pygame.draw.rect(self.screen, c, (x - s, yy - s, 2 * s, 6), border_radius=2)
        pygame.draw.rect(self.screen, dk_c(col, 60), r, 2, border_radius=10)

    # ------------------------------------------------------------ shop tab
    SHOP_CARD_H = 104

    def _shop_layout(self):
        """[(rect, offer, is_deal)] and [(y, title)] section headers."""
        W = cfg.WINDOW_W
        y = TOP_H + 74
        w = (W - 32 - 2 * 10) // 3
        cells, heads = [], []
        sections = [("Daily Deals", shop.daily_deals())] + shop.SECTIONS
        for title, offers in sections:
            heads.append((y, title))
            y += 24
            for i, o in enumerate(offers):
                cells.append((pygame.Rect(16 + i * (w + 10), y, w, self.SHOP_CARD_H), o,
                              title == "Daily Deals"))
            y += self.SHOP_CARD_H + 10
        return cells, heads

    def _shop_click(self, pos):
        for r, o, deal in self._shop_layout()[0]:
            if r.collidepoint(pos):
                if shop.buy(self.profile, o, deal):
                    self.sfx.play("crown", 0.7, min_gap=0.0)
                    self.shop_msg = "Bought %s!" % o[1]
                elif deal and o[0] in shop.bought_today(self.profile):
                    self.shop_msg = "Already bought today - new deals in %s." % shop.time_to_refresh()
                else:
                    self.shop_msg = "Not enough %s." % ("gems" if o[3][0] == "gems" else "gold")
                self.shop_msg_t = self._now()
                return

    def _draw_shop_tab(self):
        W = cfg.WINDOW_W
        cx = W // 2
        pr = self.profile
        self._screen_title("Shop", TOP_H + 22)
        self._wallet(cx, TOP_H + 58, ("gems", "gold", "shards", "coins"))
        cells, heads = self._shop_layout()
        for y, title in heads:
            self._text(title, self.font_m, (235, 225, 190), topleft=(18, y - 2))
            if title == "Daily Deals":
                t = "new deals in " + shop.time_to_refresh()
                self._text(t, self.font_s, (170, 176, 196),
                           topleft=(W - 18 - self.font_s.size(t)[0], y + 4))
        mouse = pygame.mouse.get_pos()
        bought = shop.bought_today(pr)
        for r, o, deal in cells:
            oid, name, reward, cost = o
            done = deal and oid in bought
            ok = shop.can_buy(pr, o, deal)
            hov = r.collidepoint(mouse) and not done
            border = (255, 222, 110) if hov else ((120, 200, 255) if deal else (80, 86, 110))
            self._panel(r, top=(46, 50, 68) if not done else (34, 36, 44),
                        bottom=(28, 30, 42), border=border, radius=10)
            kinds = [k for k in ("gold", "gems", "shards", "coins") if reward.get(k)]
            # the goods: a big icon (or two) and the amount
            for q, kd in enumerate(kinds):
                ix = r.centerx + (q - (len(kinds) - 1) / 2.0) * 34
                self._reward_icon(kd, ix, r.y + 26, 14)
            amt = "  ".join("%d" % reward[k] for k in kinds)
            self._text(amt, self.font_sb, WHITE, center=(r.centerx, r.y + 52))
            self._text(self._fit(name, self.font_s, r.w - 8), self.font_s, (200, 204, 220),
                       center=(r.centerx, r.y + 68))
            pb = pygame.Rect(r.x + 8, r.bottom - 26, r.w - 16, 20)
            if done:
                pygame.draw.rect(self.screen, (50, 90, 60), pb, border_radius=6)
                self._text("Bought", self.font_sb, (170, 230, 180), center=pb.center)
            elif cost is None:
                pygame.draw.rect(self.screen, (60, 150, 80), pb, border_radius=6)
                self._text("FREE", self.font_sb, WHITE, center=pb.center)
            else:
                cur, n = cost
                pygame.draw.rect(self.screen, (52, 120, 72) if ok else (70, 60, 64), pb,
                                 border_radius=6)
                t = "%d" % n
                tw = self.font_sb.size(t)[0]
                self._reward_icon(cur, pb.centerx - tw // 2 - 6, pb.centery, 7)
                self._text(t, self.font_sb, WHITE if ok else (220, 160, 160),
                           topleft=(pb.centerx - tw // 2 + 4, pb.centery - 9))
        msg = getattr(self, "shop_msg", "")
        if msg and self._now() - getattr(self, "shop_msg_t", 0) < 3.0:
            self._text(msg, self.font_sb, (255, 220, 140),
                       center=(cx, REAL_H - TAB_H - 14))
