"""
============================================================================
  KINGSCREEN.PY  --  King Tower screen + reward pop-ups (mixed into Game)
============================================================================

The King Tower screen (tap the blue XP badge in the top bar) shows:

  * your King level and XP towards the next one (king.py);
  * the King's reward track: 4 rewards on the way to every level, ticked
    off as you reach them (they're paid automatically);
  * your Tower Troops with their levels and gold upgrades - a Tower Troop
    (and so your Princess Towers) can't go above your King level.

Also here: the reward pop-up ("toast") shown when XP pays a King reward,
and the one-time conversion of saves from before King levels.
============================================================================
"""

import pygame

import config as cfg
import king
import sprites
import towers
import trophy
from engine import PLAYER, ENEMY
from ui import Button, WHITE, lt_c, dk_c, grad_rect

TRACK_ROW = 60
TROOP_ROW = 48
TOAST_TIME = 3.2


class KingMixin:
    # ------------------------------------------------------------ helpers
    def _towers_kw(self, enemy_level=None):
        """Match keyword args for the towers: yours - Princess Towers at the
        level of the Tower Troop manning them, the King Tower at your King
        level - and (if given) the opponent's, all at enemy_level."""
        tt = self._tower_troop()
        out = {"tower_levels": {PLAYER: self.profile.troop_level(tt)},
               "king_levels": {PLAYER: self.profile.king_level()}}
        if enemy_level is not None:
            out["tower_levels"][ENEMY] = enemy_level
            out["king_levels"][ENEMY] = enemy_level
        return out

    def _king_startup(self):
        """First run of a save from before King levels: back-pay what the
        new rewards would have given, then any King rewards reached."""
        import achievements as ach
        pr = self.profile
        lines = []
        if pr.migrated:
            back = ach.backpay(self)
            lines.append(("Welcome to King levels!", {"coins": profile_coins()}))
            if back:
                lines.append(("Achievements back-paid", back))
        for i, rw in pr.pay_king():
            lines.append(("King Lv %d reward" % king.chunk_level(i), rw))
        if pr.migrated or lines:
            pr.migrated = False
            pr.save()
        if lines:
            self._toast(lines)

    def _king_toast(self, paid):
        if paid:
            self._toast([("King Lv %d reward" % king.chunk_level(i), rw) for i, rw in paid])

    def _toast(self, lines):
        """Pop-up of [(label, reward dict)] lines for a few seconds (long
        lists fold into one summed line)."""
        old = getattr(self, "toast", None)
        if old and self._now() - old["t"] < TOAST_TIME:
            lines = old["lines"] + list(lines)
        lines = list(lines)
        if len(lines) > 3:
            head, rest = lines[:2], lines[2:]
            tot = {}
            for _, rw in rest:
                for k, v in rw.items():
                    tot[k] = tot.get(k, 0) + v
            lines = head + [("+ %d more rewards" % len(rest), tot)]
        self.toast = {"t": self._now(), "lines": lines}

    def _draw_toast(self):
        ts = getattr(self, "toast", None)
        if not ts:
            return
        age = self._now() - ts["t"]
        if age > TOAST_TIME:
            self.toast = None
            return
        lines = ts["lines"]
        w = cfg.WINDOW_W - 40
        h = 16 + 24 * len(lines)
        slide = min(1.0, age / 0.2) * min(1.0, (TOAST_TIME - age) / 0.3)
        bottom = cfg.WINDOW_H - 84
        r = pygame.Rect(20, int(cfg.WINDOW_H + (bottom - h - cfg.WINDOW_H) * slide), w, h)
        pygame.draw.rect(self.screen, (8, 10, 16), r.move(0, 3), border_radius=10)
        self.screen.blit(grad_rect(r.w, r.h, (44, 70, 120), (26, 36, 66), 10), r.topleft)
        pygame.draw.rect(self.screen, (120, 180, 255), r, 2, border_radius=10)
        y = r.y + 8 + 12
        for label, rw in lines:
            self._text(self._fit(label, self.font_sb, w // 2), self.font_sb,
                       topleft=(r.x + 12, y - 10))
            self._reward_row(rw, r.right - 12, y)
            y += 24

    # ------------------------------------------------------------ screen
    def _open_king(self, back=None):
        self.king_return = back or ("menu" if self._home_active() else self.state)
        self.king_msg = ""
        self.state = "king"

    def _king_layout(self):
        W = cfg.WINDOW_W
        return {"head": pygame.Rect(10, 52, W - 20, 120),
                "track_y": 196,
                "troops_y": 196 + 5 * TRACK_ROW + 30}

    def _king_troop_rows(self):
        L = self._king_layout()
        y = L["troops_y"] + 4
        return [(pygame.Rect(12, y + i * TROOP_ROW, cfg.WINDOW_W - 24, TROOP_ROW - 6), k)
                for i, k in enumerate(towers.ORDER)]

    def _king_buttons(self):
        out = []
        pr = self.profile
        for r, k in self._king_troop_rows():
            br = pygame.Rect(r.right - 132, r.y + 6, 124, r.h - 12)
            if not self._tower_owned(k):
                b = Button(br, "%d trophies" % towers.get(k).unlock, lambda: None, "dark")
                b.enabled = False
            else:
                c = pr.troop_upgrade_cost(k)
                if c is None:
                    full = pr.troop_level(k) >= king.KING_MAX
                    b = Button(br, "Max level" if full else "King Lv cap", lambda: None, "dark")
                    b.enabled = False
                else:
                    b = Button(br, "Upgrade %d" % c, (lambda k=k: self._king_upgrade(k)), "gold")
                    b.enabled = pr.gold >= c
            b.troop = k
            out.append(b)
        out.append(Button((cfg.WINDOW_W // 2 - 70, cfg.WINDOW_H - 46, 140, 38), "Back",
                          lambda: self._goto(getattr(self, "king_return", "menu")), "dark"))
        return out

    def _king_upgrade(self, k):
        if self.profile.upgrade_troop(k):
            self.sfx.play("crown", 0.7, min_gap=0.0)
            self.king_msg = "%s is now level %d!" % (towers.get(k).name,
                                                     self.profile.troop_level(k))
        else:
            self.king_msg = "Not enough gold."

    def _king_click(self, pos):
        for b in self._king_buttons():
            if b.click(pos):
                return

    def _draw_king(self):
        pr = self.profile
        W = cfg.WINDOW_W
        L = self._king_layout()
        self._screen_title("King Tower", 24)
        lv, into, need = king.progress(pr.king_xp)
        # ---- header: badge, level, XP bar with its 4 reward chunks ----
        hd = self._panel(L["head"], border=(110, 160, 230), top=(40, 58, 96), bottom=(24, 30, 50))
        self._xp_icon(hd.x + 52, hd.centery, 38)
        self._text(str(lv), self.font_xl, center=(hd.x + 52, hd.centery))
        tx = hd.x + 106
        self._text("King Level %d" % lv, self.font_l, topleft=(tx, hd.y + 12))
        bar = pygame.Rect(tx, hd.y + 56, hd.right - tx - 16, 14)
        pygame.draw.rect(self.screen, (16, 20, 34), bar, border_radius=7)
        if need:
            f = into / need
            pygame.draw.rect(self.screen, (96, 170, 255),
                             (bar.x, bar.y, max(4, int(bar.w * f)), bar.h), border_radius=7)
            for j in range(1, king.CHUNKS):
                xx = bar.x + bar.w * j // king.CHUNKS
                pygame.draw.line(self.screen, (220, 236, 255), (xx, bar.y + 2), (xx, bar.bottom - 3), 2)
            s = "%d / %d XP to level %d" % (into, need, lv + 1)
        else:
            pygame.draw.rect(self.screen, (96, 170, 255), bar, border_radius=7)
            s = "Max King level!  %d XP" % pr.king_xp
        pygame.draw.rect(self.screen, (150, 196, 255), bar, 1, border_radius=7)
        self._text(s, self.font_s, (210, 226, 255), topleft=(bar.x, bar.bottom + 5))
        self._text("XP: card upgrades and achievements", self.font_s, (160, 176, 210),
                   topleft=(bar.x, bar.bottom + 23))
        # ---- the reward track ----
        y0 = L["track_y"]
        self._text("King rewards", self.font_m, topleft=(14, y0 - 22))
        nxt = pr.king_paid
        bw = (W - 24 - 60 - 3 * 6) // king.CHUNKS
        for row in range(king.KING_MAX - king.KING_MIN):
            n = king.KING_MIN + 1 + row
            y = y0 + row * TRACK_ROW
            reached = lv >= n
            col = (255, 222, 110) if reached else (170, 176, 196)
            self._xp_icon(32, y + TRACK_ROW // 2 - 3, 15)
            self._text(str(n), self.font_sb, center=(32, y + TRACK_ROW // 2 - 3))
            self._text("Lv", self.font_s, col, center=(32, y + TRACK_ROW // 2 + 19))
            for j in range(king.CHUNKS):
                i = row * king.CHUNKS + j
                r = pygame.Rect(60 + j * (bw + 6), y + 2, bw, TRACK_ROW - 8)
                paid = i < nxt
                here = i == nxt
                bg = (34, 52, 40) if paid else ((54, 60, 86) if here else (32, 34, 46))
                pygame.draw.rect(self.screen, bg, r, border_radius=8)
                pygame.draw.rect(self.screen, (255, 222, 110) if here else
                                 ((90, 170, 110) if paid else (60, 64, 84)), r,
                                 2 if here else 1, border_radius=8)
                rw = king.chunk_reward(i)
                kinds = [k for k in ("gold", "gems", "shards", "coins") if rw.get(k)]
                for q, kd in enumerate(kinds):
                    cy = r.y + 15 + q * 18 if len(kinds) > 1 else r.centery - 6
                    self._reward_icon(kd, r.x + 14, cy, 7)
                    self._text("%d" % rw[kd], self.font_sb,
                               (150, 160, 170) if paid else WHITE, topleft=(r.x + 26, cy - 9))
                need_xp = king.chunk_threshold(i)
                if paid:
                    pygame.draw.circle(self.screen, (90, 190, 110), (r.right - 11, r.y + 11), 7)
                    pygame.draw.lines(self.screen, WHITE, False,
                                      [(r.right - 15, r.y + 11), (r.right - 12, r.y + 14),
                                       (r.right - 7, r.y + 8)], 2)
                elif len(kinds) == 1:
                    self._text("%d XP" % need_xp, self.font_s, (150, 170, 210),
                               topleft=(r.x + 8, r.bottom - 17))
        # ---- Tower Troops ----
        ty = L["troops_y"]
        self._text("Tower Troops", self.font_m, topleft=(14, ty - 24))
        self._text("gold upgrades, up to King level %d" % lv, self.font_s, (170, 176, 196),
                   topleft=(160, ty - 18))
        cur = self._tower_troop() if hasattr(self, "_tower_troop") else towers.DEFAULT
        for r, k in self._king_troop_rows():
            tt = towers.get(k)
            owned = self._tower_owned(k)
            self._panel(r, border=(255, 222, 110) if k == cur else (70, 76, 98), radius=9,
                        top=(40, 44, 60), bottom=(28, 30, 42))
            spr = sprites.get_sprite(k, 38)
            if not owned:
                spr = spr.copy()
                spr.set_alpha(90)
            self.screen.blit(spr, (r.x + 6, r.y + 2))
            self._text(tt.name, self.font_sb, WHITE if owned else (150, 150, 160),
                       topleft=(r.x + 52, r.y + 4))
            sub = ("Lv %d" % pr.troop_level(k)) if owned else "locked"
            if k == cur:
                sub += "   (your towers)"
            self._text(sub, self.font_s, (200, 210, 230), topleft=(r.x + 52, r.y + 23))
        for b in self._king_buttons():
            b.draw(self.screen, self.font_sb if hasattr(b, "troop") else self.font_m)
        if getattr(self, "king_msg", ""):
            self._text(self.king_msg, self.font_sb, (255, 220, 140),
                       center=(W // 2, cfg.WINDOW_H - 60))


def profile_coins():
    import profile_data
    return profile_data.MIGRATION_COINS
