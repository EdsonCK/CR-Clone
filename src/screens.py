"""
============================================================================
  SCREENS.PY  --  Progression-era screens (mixed into game.Game)
============================================================================

  * CARDS    -- your collection: card levels, upgrades (gold), Evolutions
                and Heroes (Evo shards / Hero coins), stats at this level and the next
  * SETTINGS -- volumes, game speed, colour-blind teams, drag to deploy,
                damage numbers, screen shake, sandbox, reset progress
  * DECKS    -- saved deck slots (see game.py deck editor)
  * MODES    -- Special Battles + Endless Survival (see modes.py)

Everything here draws with the same helpers as game.py (self._text,
self._panel, Button ...).
============================================================================
"""

import math
import pygame

import config as cfg
import cards
import sprites
import evos
import mastery
import profile_data
import icons
from ui import dk_c, lt_c, grad_rect, render_text, Button, WHITE

GOLD_COL = (250, 206, 92)
SHARD_COL = (196, 120, 255)
GEM_COL = (90, 220, 120)
COIN_COL = (255, 200, 70)          # Hero coins
XP_COL = (96, 170, 255)
REWARD_COLS = {"gold": GOLD_COL, "shards": SHARD_COL, "coins": COIN_COL,
               "gems": GEM_COL, "xp": XP_COL}
REWARD_ORDER = ("xp", "gold", "gems", "shards", "coins")
EVO_COL = (190, 110, 255)
HERO_COL = (255, 196, 80)


class ScreensMixin:
    # screens drawn/handled by this mixin: _draw_<name>, _<name>_click
    EXTRA_SCREENS = ("cards", "settings", "modes", "draft", "stats", "achievements",
                     "trophy", "king", "mastery")

    def _extra_escape(self):
        back = {"cards": getattr(self, "cards_return", "menu"),
                "king": getattr(self, "king_return", "menu"),
                "draft": "modes", "mastery": "cards"}.get(self.state, "menu")
        if self.state == "stats":
            back = getattr(self, "stats_return", "result")
        self.state = back

    def _extra_wheel(self, dy):
        if self.state == "cards":
            self._cards_set_scroll(self.cards_scroll - dy * 60)
        elif self.state == "achievements":
            self._ach_set_scroll(getattr(self, "ach_scroll", 0) - dy * 60)
        elif self.state == "modes":
            pass
        elif self.state == "trophy":
            self._trophy_set_scroll(self.trophy_scroll - dy * 60)

    def _extra_mouseup(self, pos):
        self.cards_drag = False
        self.settings_drag = None

    def _extra_motion(self, pos):
        if self.state == "cards" and getattr(self, "cards_drag", False):
            self._cards_drag_to(pos[1])
        elif self.state == "settings" and getattr(self, "settings_drag", None):
            self._settings_drag_to(pos[0])

    def _open_stats(self, back="result"):
        self.stats_return = back
        self.state = "stats"

    def _stats_buttons(self):
        return [Button((cfg.WINDOW_W // 2 - 70, cfg.WINDOW_H - 52, 140, 40), "Back",
                       lambda: self._goto(getattr(self, "stats_return", "result")), "dark")]

    def _stats_click(self, pos):
        for b in self._stats_buttons():
            if b.click(pos):
                return

    def _stat_bars(self, y, title, dmg, col, n, kills):
        self._text(title, self.font_m, col, topleft=(16, y))
        y += 26
        items = sorted(dmg.items(), key=lambda kv: -kv[1])[:n]
        if not items:
            self._text("(nothing)", self.font_s, (150, 156, 175), topleft=(24, y))
            return y + 20
        top = max(v for _, v in items) or 1
        for key, v in items:
            sk = key if key in cards.CARDS else None
            if sk:
                self.screen.blit(sprites.get_sprite(sk, 26), (16, y - 2))
            name = cards.CARDS[key].name if key in cards.CARDS else key.replace("_", " ").title()
            bw = int((cfg.WINDOW_W - 200) * v / top)
            pygame.draw.rect(self.screen, (30, 34, 46), (48, y + 12, cfg.WINDOW_W - 200, 8),
                             border_radius=4)
            pygame.draw.rect(self.screen, col, (48, y + 12, max(2, bw), 8), border_radius=4)
            self._text(self._fit(name, self.font_s, 150), self.font_s, (225, 228, 238),
                       topleft=(48, y - 3))
            k = kills.get(key, 0)
            self._text("%d dmg%s" % (round(v), ("  %d KO" % k) if k else ""), self.font_s,
                       (220, 220, 200), topleft=(cfg.WINDOW_W - 146, y + 4))
            y += 28
        return y

    def _draw_stats(self):
        m = self.match
        st = m.stats
        self._screen_title("Match Stats", 28)
        duo = m.is_2v2

        def both(k, a, b):                 # 2v2: the two enemies together
            if isinstance(st[k][a], dict):
                out = dict(st[k][a])
                for kk, v in st[k][b].items():
                    out[kk] = out.get(kk, 0) + v
                return out
            return st[k][a] + st[k][b]
        cols = [("You", cfg.COLOR_TEAM_PLAYER, 0)]
        if duo:
            cols.append(("Ally", (150, 230, 255), 2))
        cols.append(("Enemy", cfg.COLOR_TEAM_ENEMY, 1))

        def get(k, seat):
            return both(k, 1, 3) if duo and seat == 1 else st[k][seat]
        y = self._stat_bars(62, "Your damage", st["dmg"][0], cfg.COLOR_TEAM_PLAYER,
                            5 if duo else 7, st["kills"][0])
        if duo:
            y = self._stat_bars(y + 6, "Ally damage", st["dmg"][2], (150, 230, 255), 3,
                                st["kills"][2])
        y = self._stat_bars(y + 6, "Enemy damage", get("dmg", 1), cfg.COLOR_TEAM_ENEMY,
                            3 if duo else 4, get("kills", 1))
        y += 8
        panel = self._panel((12, y, cfg.WINDOW_W - 24, 112), border=(150, 130, 80))
        yy = y + 10
        rows = [("Elixir spent", lambda s_: "%d" % get("spent", s_)),
                ("Elixir wasted (full bar)", lambda s_: "%.1f" % get("leaked", s_)),
                ("Tower damage", lambda s_: "%d" % get("tower_dmg", s_)),
                ("Cards played", lambda s_: "%d" % sum(get("played", s_).values()))]
        xs = [panel.right - 64 * (len(cols) - i) - 2 for i in range(len(cols))]
        for (name, col, _), x in zip(cols, xs):
            self._text(name, self.font_sb, col, topleft=(x, yy - 4))
        yy += 16
        for lbl, fn in rows:
            self._text(lbl, self.font_s, (220, 224, 236), topleft=(panel.x + 12, yy))
            for (_, _, seat), x in zip(cols, xs):
                self._text(fn(seat), self.font_sb, topleft=(x, yy - 1))
            yy += 21
        run = self.level_run
        if run is not None and getattr(run, "tower_log", None) is not None:
            y = panel.bottom + 10
            if run.tower_log:
                txt = "Towers lost: " + ", ".join("wave %d (%s)" % (w, sd)
                                                  for w, sd in run.tower_log)
            else:
                txt = "No towers lost!"
            for ln in self._wrap(txt, self.font_sb, cfg.WINDOW_W - 32):
                self._text(ln, self.font_sb, (240, 210, 150), topleft=(16, y))
                y += 18
        for b in self._stats_buttons():
            b.draw(self.screen, self.font_m)

    # ================================================================ icons
    # currency icons: drawn in the real game's style by icons.py
    def _coin(self, x, y, r=8):
        icons.blit(self.screen, "gold", x, y, r)

    def _shard(self, x, y, r=8):
        icons.blit(self.screen, "shards", x, y, r)

    def _gem(self, x, y, r=8):
        icons.blit(self.screen, "gems", x, y, r)

    def _hcoin(self, x, y, r=8):
        """A Hero coin."""
        icons.blit(self.screen, "coins", x, y, r)

    def _xp_icon(self, x, y, r=8):
        """King XP / level badge: the blue 12-point star."""
        icons.blit(self.screen, "xp", x, y, r)

    def _reward_icon(self, kind, x, y, r=8):
        {"gold": self._coin, "shards": self._shard, "coins": self._hcoin,
         "gems": self._gem, "xp": self._xp_icon}[kind](int(x), int(y), r)

    def _reward_row(self, rw, right, cy, font=None, r=7, gap=10):
        """Draw a reward dict right-aligned at `right` (icon + "+n" each);
        returns the x where it starts."""
        font = font or self.font_sb
        x = right
        for kind in reversed(REWARD_ORDER):
            n = rw.get(kind, 0) if rw else 0
            if not n:
                continue
            t = "+%d" % n
            w = font.size(t)[0]
            self._text(t, font, REWARD_COLS[kind], topleft=(x - w, cy - font.get_height() // 2))
            self._reward_icon(kind, x - w - r - 3, cy, r)
            x -= w + 2 * r + 4 + gap
        return x + gap

    def _wallet(self, cx, y, kinds=("gold", "shards", "coins")):
        """Currency readout centred on cx."""
        vals = {"gold": self.profile.gold, "shards": self.profile.shards,
                "coins": self.profile.hero_coins, "gems": self.profile.gems}
        parts = [(k, "%d" % vals[k]) for k in kinds]
        total = sum(20 + self.font_m.size(t)[0] for _, t in parts) + 20 * (len(parts) - 1)
        x = cx - total // 2
        for k, t in parts:
            self._reward_icon(k, x + 8, y, 9)
            self._text(t, self.font_m, REWARD_COLS[k], topleft=(x + 20, y - 12))
            x += 20 + self.font_m.size(t)[0] + 20


    # ================================================================ CARDS
    CARD_COLS = 5
    CARD_CELL_H = 92
    CARD_FILTERS = [("all", "All"), ("troop", "Troops"), ("spell", "Spells"),
                    ("building", "Bldgs"), ("evo", "Evos"), ("hero", "Heroes")]

    def _cards_init(self):
        if not hasattr(self, "cards_sel"):
            self.cards_sel = cards.DEPLOYABLE_CARDS[0].key
            self.cards_scroll = 0
            self.cards_filter = "all"
            self.cards_drag = False
            self.cards_msg = ""

    def _open_cards(self, return_to="menu"):
        self._cards_init()
        self.cards_return = return_to
        self.cards_msg = ""
        self.state = "cards"

    def _cards_list(self):
        f = self.cards_filter
        out = []
        for c in cards.DEPLOYABLE_CARDS:
            if f in ("troop", "spell", "building") and c.category != f:
                continue
            if f == "evo" and c.key not in evos.EVOS:
                continue
            if f == "hero" and c.key not in evos.HEROES:
                continue
            out.append(c)
        return sorted(out, key=lambda c: (c.elixir, c.name))

    def _cards_view(self):
        return pygame.Rect(0, 108, cfg.WINDOW_W, cfg.WINDOW_H - 306 - 108)

    def _cards_max_scroll(self):
        rows = (len(self._cards_list()) + self.CARD_COLS - 1) // self.CARD_COLS
        return max(0, rows * self.CARD_CELL_H + 6 - self._cards_view().h)

    def _cards_set_scroll(self, v):
        self.cards_scroll = int(max(0, min(self._cards_max_scroll(), v)))

    def _cards_grid(self):
        v = self._cards_view()
        m = 10
        cw = (cfg.WINDOW_W - m * 2 - 10) // self.CARD_COLS
        out = []
        for i, c in enumerate(self._cards_list()):
            r, col = divmod(i, self.CARD_COLS)
            out.append((pygame.Rect(m + col * cw, v.y + 4 + r * self.CARD_CELL_H - self.cards_scroll,
                                    cw - 4, self.CARD_CELL_H - 4), c))
        return out

    def _cards_tab_rects(self):
        n = len(self.CARD_FILTERS)
        gap = 4
        w = (cfg.WINDOW_W - 20 - gap * (n - 1)) // n
        return [(pygame.Rect(10 + i * (w + gap), 74, w, 28), k)
                for i, (k, _) in enumerate(self.CARD_FILTERS)]

    def _evo_owned(self, key):
        return self.sandbox or key in self.profile.evos

    def _hero_owned(self, key):
        return self.sandbox or key in self.profile.heroes

    def _cards_buttons(self):
        key = self.cards_sel
        p = self.profile
        y = cfg.WINDOW_H - 306 + 102
        out = []
        cost = p.upgrade_cost(key)
        if cost is None:
            b = Button((16, y, 124, 36), "Max level", lambda: None, "dark")
            b.enabled = False
        else:
            b = Button((16, y, 124, 36), "Upgrade %d" % cost, self._cards_upgrade, "gold")
            b.enabled = p.gold >= cost
        out.append(b)
        if key in evos.EVOS:
            if self._evo_owned(key):
                b = Button((148, y, 124, 36), "Evo unlocked", lambda: None, "dark")
                b.enabled = False
            else:
                b = Button((148, y, 124, 36), "Evo  %d" % profile_data.EVO_COST,
                           self._cards_unlock_evo, "primary")
                b.enabled = p.shards >= profile_data.EVO_COST
            b.kind = "evo"
            out.append(b)
        if key in evos.HEROES:
            if self._hero_owned(key):
                b = Button((280, y, 124, 36), "Hero unlocked", lambda: None, "dark")
                b.enabled = False
            else:
                b = Button((280, y, 124, 36), "Hero  %d" % profile_data.HERO_COST,
                           self._cards_unlock_hero, "primary")
                b.enabled = p.hero_coins >= profile_data.HERO_COST
            b.kind = "hero"
            out.append(b)
        b = Button((412, y, 112, 36), "Mastery", lambda: self._open_mastery(key), "primary")
        b.kind = "mastery"
        out.append(b)
        out.append(Button((cfg.WINDOW_W // 2 - 70, cfg.WINDOW_H - 42, 140, 34), "Back",
                          lambda: self._goto(getattr(self, "cards_return", "menu")), "dark"))
        return out

    def _cards_upgrade(self):
        old = self.profile.level(self.cards_sel)
        k_before = self.profile.king_level()
        if self.profile.upgrade(self.cards_sel):
            self.sfx.play("crown", 0.7, min_gap=0.0)
            import king
            self.cards_msg = "%s is now level %d!  +%d XP" % (
                cards.CARDS[self.cards_sel].name, self.profile.level(self.cards_sel),
                king.XP_PER_UPGRADE[old])
            if self.profile.king_level() > k_before:
                self.cards_msg = "King level %d!  %s" % (self.profile.king_level(),
                                                        self.cards_msg)
            self._king_toast(self.profile.last_king)
        else:
            self.cards_msg = "Not enough gold."

    def _cards_unlock_evo(self):
        if self.profile.unlock_evo(self.cards_sel):
            self.sfx.play("ability", 0.8, min_gap=0.0)
            self.cards_msg = "Evolution unlocked! Put it in deck slot 1 (or the flex slot 2)."
        else:
            self.cards_msg = "Not enough Evo shards."

    def _cards_unlock_hero(self):
        if self.profile.unlock_hero(self.cards_sel):
            self.sfx.play("ability", 0.8, min_gap=0.0)
            self.cards_msg = "Hero unlocked! Put it in deck slot 3 (or the flex slot 2)."
        else:
            self.cards_msg = "Not enough Hero coins."

    def _cards_click(self, pos):
        for r, k in self._cards_tab_rects():
            if r.collidepoint(pos):
                self.cards_filter = k
                self.cards_scroll = 0
                return
        for b in self._cards_buttons():
            if b.click(pos):
                return
        v = self._cards_view()
        track = pygame.Rect(cfg.WINDOW_W - 12, v.y, 10, v.h)
        if track.collidepoint(pos):
            self.cards_drag = True
            self._cards_drag_to(pos[1])
            return
        if v.collidepoint(pos):
            for r, c in self._cards_grid():
                if r.collidepoint(pos):
                    self.cards_sel = c.key
                    self.cards_msg = ""
                    self.sfx.play("ui_select", 0.5, min_gap=0.0)
                    return

    def _cards_drag_to(self, y):
        v = self._cards_view()
        self._cards_set_scroll((y - v.y) / max(1, v.h) * self._cards_max_scroll())

    def _card_stat_lines(self, c, lv):
        m = cards.level_mult(lv)
        if c.category == "spell":
            out = []
            if c.spell_damage:
                out.append(("Damage", c.spell_damage * m))
            if c.spawn_troops:
                sub = cards.CARDS[c.spawn_troops[0]]
                out.append(("%s HP" % sub.name, sub.hp * c.sub_hp_mult * m))
            return out
        out = [("HP", c.hp * m)]
        if c.damage:
            out.append(("Damage", c.damage * m))
            if c.hit_speed:
                out.append(("DPS", c.damage * m / c.hit_speed))
        if c.spawner:
            sub = cards.CARDS[c.spawner[0]]
            out.append(("%s HP" % sub.name, sub.hp * c.sub_hp_mult * m))
        return out

    def _draw_cards(self):
        self._cards_init()
        cx = cfg.WINDOW_W // 2
        mouse = pygame.mouse.get_pos()
        p = self.profile
        self._screen_title("Cards", 26)
        self._wallet(cx, 60)
        # tabs
        for r, k in self._cards_tab_rects():
            sel = k == self.cards_filter
            bg = (70, 90, 130) if sel else (40, 46, 60)
            if r.collidepoint(mouse):
                bg = lt_c(bg, 14)
            pygame.draw.rect(self.screen, bg, r, border_radius=7)
            pygame.draw.rect(self.screen, (250, 222, 110) if sel else (70, 78, 98), r,
                             2 if sel else 1, border_radius=7)
            lbl = dict(self.CARD_FILTERS)[k]
            self._text(lbl, self.font_s, WHITE, center=r.center)
        # grid
        v = self._cards_view()
        self.screen.set_clip(v)
        for r, c in self._cards_grid():
            if r.bottom < v.top or r.top > v.bottom:
                continue
            lv = p.level(c.key)
            sel = c.key == self.cards_sel
            bg = (58, 78, 118) if sel else (44, 50, 62)
            if r.collidepoint(mouse):
                bg = lt_c(bg, 14)
            pygame.draw.rect(self.screen, (14, 16, 22), r.move(0, 2), border_radius=8)
            pygame.draw.rect(self.screen, bg, r, border_radius=8)
            border = (90, 100, 128)
            if c.key in evos.EVOS and self._evo_owned(c.key):
                border = EVO_COL
            if c.key in evos.HEROES and self._hero_owned(c.key):
                border = HERO_COL
            if sel:
                border = (250, 240, 140)
            pygame.draw.rect(self.screen, border, r, 2, border_radius=8)
            self.screen.blit(sprites.get_sprite(c.key, 46), (r.centerx - 23, r.y + 8))
            self._elixir_badge(r.x + 9, r.y + 9, c.elixir, r=8)
            # level pill
            pill = pygame.Rect(0, 0, 40, 16)
            pill.midbottom = (r.centerx, r.bottom - 3)
            lvcol = (80, 140, 220) if lv < profile_data.MAX_LEVEL else (220, 160, 40)
            pygame.draw.rect(self.screen, dk_c(lvcol, 50), pill, border_radius=8)
            pygame.draw.rect(self.screen, lvcol, pill, 1, border_radius=8)
            self._text("Lv %d" % lv, self.font_s, WHITE, center=pill.center)
            if mastery.claimable(p, c.key):   # Mastery rewards waiting: gold star
                self._star(r.right - 10, r.bottom - 28, 6, (250, 206, 92))
            if p.can_upgrade(c.key):          # upgrade available: green arrow
                ax, ay = r.right - 10, r.y + 12
                pygame.draw.polygon(self.screen, (60, 200, 90),
                                    [(ax, ay - 7), (ax + 6, ay), (ax + 2, ay), (ax + 2, ay + 6),
                                     (ax - 2, ay + 6), (ax - 2, ay), (ax - 6, ay)])
            tags = []
            if c.key in evos.EVOS:
                tags.append(("EVO", EVO_COL if self._evo_owned(c.key) else (90, 80, 110)))
            if c.key in evos.HEROES:
                tags.append(("HERO", HERO_COL if self._hero_owned(c.key) else (110, 100, 80)))
            ty = r.bottom - 34
            for t, col in tags:
                tw = self.font_s.size(t)[0] + 6
                tr = pygame.Rect(r.x + 3, ty, tw, 13)
                pygame.draw.rect(self.screen, (20, 18, 28), tr, border_radius=4)
                self._text(t, self.font_s, col, center=tr.center)
                ty -= 14
        self.screen.set_clip(None)
        # scrollbar
        mx = self._cards_max_scroll()
        if mx:
            track = pygame.Rect(cfg.WINDOW_W - 10, v.y, 6, v.h)
            pygame.draw.rect(self.screen, (34, 38, 52), track, border_radius=3)
            th = max(30, int(track.h * v.h / (v.h + mx)))
            ty = track.y + int((track.h - th) * self.cards_scroll / mx)
            pygame.draw.rect(self.screen, (214, 176, 84), (track.x, ty, track.w, th),
                             border_radius=3)
        # detail panel
        c = cards.CARDS[self.cards_sel]
        lv = p.level(c.key)
        top = cfg.WINDOW_H - 306 + 4
        panel = self._panel((8, top, cfg.WINDOW_W - 16, 254), border=(150, 130, 80))
        self.screen.blit(sprites.get_sprite(c.key, 70), (panel.x + 8, top + 8))
        self._text(c.name, self.font_m, topleft=(panel.x + 86, top + 6))
        kind = "Champion" if c.is_champion else c.category.title()
        self._text("%s  -  %d elixir  -  Level %d / %d" % (kind, c.elixir, lv,
                                                           profile_data.MAX_LEVEL),
                   self.font_s, (250, 206, 92), topleft=(panel.x + 86, top + 30))
        stats = self._card_stat_lines(c, lv)
        nxt = self._card_stat_lines(c, lv + 1) if lv < profile_data.MAX_LEVEL else None
        yy = top + 48
        for i, (lbl, val) in enumerate(stats[:3]):
            s = "%s %d" % (lbl, round(val))
            if nxt:
                s += "  ->  %d" % round(nxt[i][1])
            self._text(s, self.font_s, (220, 224, 236), topleft=(panel.x + 86, yy))
            yy += 15
        for b in self._cards_buttons()[:-1]:
            b.draw(self.screen, self.font_sb)
            if getattr(b, "kind", "") == "mastery" and mastery.claimable(p, c.key):
                pygame.draw.circle(self.screen, (230, 60, 60), (b.rect.right - 4, b.rect.y + 4), 6)
        # descriptions
        yy = top + 144
        import carddesc
        lines = [(carddesc.describe(c.key), (232, 232, 240))]
        if c.key in evos.EVOS:
            e = evos.EVOS[c.key]
            lines.append(("EVO (%d-cycle): " % e.cycles + e.desc, EVO_COL))
        if c.key in evos.HEROES:
            h = evos.HEROES[c.key]
            lines.append(("HERO - %s (%d elixir): " % (h.ability, h.cost) + h.desc, HERO_COL))
        if c.is_champion:
            lines.append(("Champion ability: " + c.ability_name, HERO_COL))

        for text, col in lines:
            for ln in self._wrap(text, self.font_s, panel.w - 20):
                if yy > panel.bottom - 16:
                    break
                self._text(ln, self.font_s, col, topleft=(panel.x + 10, yy))
                yy += 15
            yy += 3
        if self.cards_msg:
            self._text(self.cards_msg, self.font_sb, (150, 240, 160), center=(cx, top - 8))
        for b in self._cards_buttons()[-1:]:
            b.draw(self.screen, self.font_m)

    def _wrap(self, text, font, maxw):
        words, line, out = text.split(), "", []
        for w in words:
            t = (line + " " + w).strip()
            if font.size(t)[0] > maxw and line:
                out.append(line)
                line = w
            else:
                line = t
        if line:
            out.append(line)
        return out

    # ============================================================ SETTINGS
    SETTING_DEFAULTS = {"music_vol": 0.45, "sfx_vol": 0.7, "speed": 1.0,
                        "colorblind": False, "drag_deploy": True,
                        "dmg_numbers": False, "shake": True, "fullscreen": False,
                        "deck_sort": "elixir", "deck_desc": False}

    def _load_extra_settings(self, d):
        for k, v in self.SETTING_DEFAULTS.items():
            setattr(self, "opt_" + k, type(v)(d.get(k, v)))

    def _extra_settings(self):
        return {k: getattr(self, "opt_" + k, v) for k, v in self.SETTING_DEFAULTS.items()}

    def _apply_settings(self):
        """Push the options into the sound manager / colours."""
        self.sfx.music_volume = self.opt_music_vol
        self.sfx.sfx_volume = self.opt_sfx_vol
        try:
            if self.sfx.ok:
                self.sfx.pg.mixer.music.set_volume(self.opt_music_vol)
        except Exception:
            pass
        import fx as fxmod
        if self.opt_colorblind:
            cfg.COLOR_TEAM_PLAYER, cfg.COLOR_TEAM_ENEMY = (60, 140, 255), (245, 150, 30)
        else:
            cfg.COLOR_TEAM_PLAYER, cfg.COLOR_TEAM_ENEMY = (70, 130, 220), (220, 80, 80)
        fxmod.TEAM_COL[0], fxmod.TEAM_COL[1] = cfg.COLOR_TEAM_PLAYER, cfg.COLOR_TEAM_ENEMY
        self._apply_display()
        self._arena_surf = None
        cache = getattr(self, "_arena_bg_cache", None)
        if isinstance(cache, dict):
            cache.clear()

    def _open_settings(self):
        self.settings_confirm = False
        self.settings_drag = None
        self.state = "settings"

    SETTINGS_ROWS = [
        ("music_vol", "Music volume", "slider"),
        ("sfx_vol", "Sound volume", "slider"),
        ("speed", "Game speed", "speed"),
        ("colorblind", "Colour-blind team colours", "toggle"),
        ("drag_deploy", "Drag cards to deploy", "toggle"),
        ("dmg_numbers", "Floating damage numbers", "toggle"),
        ("shake", "Screen shake", "toggle"),
        ("fullscreen", "Borderless fullscreen  (F11)", "toggle"),
        ("sandbox", "Sandbox: unlock all Levels, Evos, Heroes", "toggle"),
    ]

    def _settings_row_rect(self, i):
        return pygame.Rect(14, 78 + i * 62, cfg.WINDOW_W - 28, 54)

    def _settings_control(self, i):
        r = self._settings_row_rect(i)
        key, _, kind = self.SETTINGS_ROWS[i]
        if kind == "slider":
            return pygame.Rect(r.x + 16, r.y + 34, r.w - 90, 10)
        if kind == "toggle":
            return pygame.Rect(r.right - 70, r.y + 12, 58, 30)
        if kind == "speed":
            return [(pygame.Rect(r.right - 196 + j * 64, r.y + 12, 58, 30), v)
                    for j, v in enumerate((1.0, 1.5, 2.0))]

    def _settings_buttons(self):
        cx = cfg.WINDOW_W // 2
        y = 78 + len(self.SETTINGS_ROWS) * 62 + 6
        lbl = "Really reset? Click again" if self.settings_confirm else "Reset progress"
        return [Button((cx - 250, y, 240, 40), lbl, self._settings_reset, "danger"),
                Button((cx + 10, y, 240, 40), "Open save folder", self._open_saves, "primary"),
                Button((cx - 70, cfg.WINDOW_H - 54, 140, 40), "Back",
                       lambda: self._goto("menu"), "dark")]

    def _open_saves(self):
        import savedata
        if not savedata.open_folder():
            self.settings_msg = "Couldn't open it - see the path below."

    def _settings_reset(self):
        if not self.settings_confirm:
            self.settings_confirm = True
            return
        self.settings_confirm = False
        self.profile.reset()
        self.progress = {}
        self._save_progress()
        self.sfx.play("defeat", 0.6, min_gap=0.0)

    def _apply_display(self):
        """Borderless fullscreen on / off. The window is SCALED, so in
        fullscreen SDL uses the desktop resolution without a border and
        scales the game up to fit (keeping its shape, black bars at the
        sides); mouse clicks are mapped back automatically."""
        surf = pygame.display.get_surface()
        if surf is None:
            return
        want = bool(getattr(self, "opt_fullscreen", False))
        if want == bool(surf.get_flags() & pygame.FULLSCREEN):
            return
        try:
            pygame.display.toggle_fullscreen()
        except pygame.error:
            try:
                flags = pygame.SCALED | (pygame.FULLSCREEN if want else pygame.RESIZABLE)
                pygame.display.set_mode((cfg.WINDOW_W, cfg.WINDOW_H), flags)
            except pygame.error:
                return
        self.screen = pygame.display.get_surface()

    def _toggle_fullscreen(self):
        self._set_opt("fullscreen", not getattr(self, "opt_fullscreen", False))

    def _get_opt(self, key):
        return self.sandbox if key == "sandbox" else getattr(self, "opt_" + key)

    def _set_opt(self, key, v):
        if key == "sandbox":
            self.sandbox = v
        else:
            setattr(self, "opt_" + key, v)
        self._apply_settings()
        self._save_settings()

    def _settings_click(self, pos):
        for b in self._settings_buttons():
            if b.click(pos):
                return
        self.settings_confirm = False
        for i, (key, _, kind) in enumerate(self.SETTINGS_ROWS):
            ctl = self._settings_control(i)
            if kind == "slider":
                if ctl.inflate(24, 24).collidepoint(pos):
                    self.settings_drag = key
                    self._settings_drag_to(pos[0])
                    return
            elif kind == "toggle":
                if self._settings_row_rect(i).collidepoint(pos):
                    self._set_opt(key, not self._get_opt(key))
                    self.sfx.play("ui_toggle", 0.6, min_gap=0.0)
                    return
            elif kind == "speed":
                for r, v in ctl:
                    if r.collidepoint(pos):
                        self._set_opt(key, v)
                        return

    def _settings_drag_to(self, x):
        key = self.settings_drag
        i = [k for k, _, _ in self.SETTINGS_ROWS].index(key)
        t = self._settings_control(i)
        v = min(1.0, max(0.0, (x - t.x) / t.w))
        setattr(self, "opt_" + key, round(v, 2))
        self._apply_settings()
        self._save_settings()

    def _draw_settings(self):
        mouse = pygame.mouse.get_pos()
        self._screen_title("Settings", 30)
        for i, (key, label, kind) in enumerate(self.SETTINGS_ROWS):
            r = self._settings_row_rect(i)
            self._panel(r, border=(80, 88, 112))
            self._text(label, self.font_sb, topleft=(r.x + 14, r.y + 8))
            ctl = self._settings_control(i)
            v = self._get_opt(key)
            if kind == "slider":
                pygame.draw.rect(self.screen, (30, 34, 46), ctl, border_radius=5)
                pygame.draw.rect(self.screen, (120, 170, 250),
                                 (ctl.x, ctl.y, int(ctl.w * v), ctl.h), border_radius=5)
                kx = ctl.x + int(ctl.w * v)
                pygame.draw.circle(self.screen, (240, 240, 250), (kx, ctl.centery), 9)
                pygame.draw.circle(self.screen, (60, 80, 120), (kx, ctl.centery), 9, 2)
                self._text("%d%%" % round(v * 100), self.font_sb,
                           topleft=(ctl.right + 14, ctl.y - 6))
            elif kind == "toggle":
                on = bool(v)
                col = (70, 170, 90) if on else (70, 74, 90)
                pygame.draw.rect(self.screen, col, ctl, border_radius=15)
                kx = ctl.right - 15 if on else ctl.x + 15
                pygame.draw.circle(self.screen, (240, 240, 245), (kx, ctl.centery), 12)
                self._text("ON" if on else "OFF", self.font_s, WHITE,
                           center=(ctl.x + 20 if on else ctl.right - 20, ctl.centery))
            elif kind == "speed":
                for rr, sv in ctl:
                    sel = abs(sv - v) < 1e-6
                    bg = (70, 110, 170) if sel else (44, 50, 64)
                    if rr.collidepoint(mouse):
                        bg = lt_c(bg, 14)
                    pygame.draw.rect(self.screen, bg, rr, border_radius=8)
                    pygame.draw.rect(self.screen, (250, 222, 110) if sel else (80, 88, 110),
                                     rr, 2 if sel else 1, border_radius=8)
                    self._text("%gx" % sv, self.font_sb, WHITE, center=rr.center)
        for b in self._settings_buttons():
            b.draw(self.screen, self.font_m)
        self._text("Sandbox never changes your saved progress or rewards.",
                   self.font_s, (160, 166, 186),
                   center=(cfg.WINDOW_W // 2, cfg.WINDOW_H - 70))
        import savedata
        y = 78 + len(self.SETTINGS_ROWS) * 62 + 6 + 50
        self._text("Progress is saved outside the game folder (kept across updates):",
                   self.font_s, (190, 196, 214), center=(cfg.WINDOW_W // 2, y))
        self._text(self._fit(savedata.SAVE_DIR, self.font_s, cfg.WINDOW_W - 24), self.font_s,
                   (150, 220, 160), center=(cfg.WINDOW_W // 2, y + 17))

    # ======================================================== ACHIEVEMENTS
    ACH_ROW = 66

    def _open_achievements(self):
        self.ach_scroll = 0
        self.ach_msg = ""
        self.state = "achievements"

    def _ach_view(self):
        return pygame.Rect(0, 84, cfg.WINDOW_W, cfg.WINDOW_H - 84 - 70)

    def _ach_set_scroll(self, v):
        import achievements as ach
        mx = max(0, len(ach.ACHIEVEMENTS) * self.ACH_ROW + 8 - self._ach_view().h)
        self.ach_scroll = int(max(0, min(mx, v)))

    def _ach_rows(self):
        import achievements as ach
        v = self._ach_view()
        out = []
        for i, a in enumerate(ach.status(self)):
            r = pygame.Rect(12, v.y + 4 + i * self.ACH_ROW - getattr(self, "ach_scroll", 0),
                            cfg.WINDOW_W - 24, self.ACH_ROW - 6)
            out.append((r, a))
        return out

    def _achievements_click(self, pos):
        import achievements as ach
        if Button((cfg.WINDOW_W // 2 - 70, cfg.WINDOW_H - 52, 140, 40), "Back",
                  lambda: self._goto("menu"), "dark").click(pos):
            return
        v = self._ach_view()
        if not v.collidepoint(pos):
            return
        for r, a in self._ach_rows():
            btn = pygame.Rect(r.right - 84, r.y + 14, 74, 30)
            if btn.collidepoint(pos) and a[6] and not a[7]:
                got = ach.claim(self, a[0])
                if got:
                    self.sfx.play("crown", 0.8, min_gap=0.0)
                    self.ach_msg = "Claimed: %s" % got[1]
                    self._king_toast(self.profile.last_king)
                return

    def _draw_achievements(self):
        import achievements as ach
        mouse = pygame.mouse.get_pos()
        self._screen_title("Achievements", 26)
        self._wallet(cfg.WINDOW_W // 2, 62, ("gold", "gems", "shards", "coins"))
        v = self._ach_view()
        self.screen.set_clip(v)
        for r, (aid, title, desc, reward, cur, goal, done, claimed) in self._ach_rows():
            if r.bottom < v.top or r.top > v.bottom:
                continue
            border = (120, 200, 120) if claimed else ((250, 206, 92) if done else (80, 88, 112))
            self._panel(r, border=border)
            self._text(title, self.font_sb, topleft=(r.x + 10, r.y + 6))
            self._text(self._fit(desc, self.font_s, r.w - 110), self.font_s,
                       (200, 204, 220), topleft=(r.x + 10, r.y + 24))
            bw = r.w - 160
            pygame.draw.rect(self.screen, (30, 34, 46), (r.x + 10, r.y + 42, bw, 8),
                             border_radius=4)
            pygame.draw.rect(self.screen, (120, 200, 120) if done else (110, 150, 230),
                             (r.x + 10, r.y + 42, int(bw * cur / max(goal, 1)), 8),
                             border_radius=4)
            self._text("%d/%d" % (cur, goal), self.font_s, (200, 204, 220),
                       topleft=(r.x + 14 + bw, r.y + 38))
            btn = pygame.Rect(r.right - 84, r.y + 14, 74, 30)
            if claimed:
                self._text("Done", self.font_sb, (120, 200, 120), center=btn.center)
            elif done:
                Button(btn, "Claim", lambda: None, "gold").draw(self.screen, self.font_sb)
            else:
                self._text("%d%%" % (100 * cur // max(goal, 1)), self.font_sb,
                           (170, 176, 196), center=btn.center)
            if not claimed:
                self._reward_row(reward, btn.x - 6, r.y + 13, self.font_s, r=6, gap=5)
        self.screen.set_clip(None)
        if getattr(self, "ach_msg", ""):
            self._text(self.ach_msg, self.font_sb, (150, 240, 160),
                       center=(cfg.WINDOW_W // 2, cfg.WINDOW_H - 64))
        Button((cfg.WINDOW_W // 2 - 70, cfg.WINDOW_H - 52, 140, 40), "Back",
               lambda: None, "dark").draw(self.screen, self.font_m)
