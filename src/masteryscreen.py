"""
============================================================================
  MASTERYSCREEN.PY  --  A card's Mastery page (mixed into Game)
============================================================================

Opened from the Cards screen ("Mastery" button). Shows the unlock progress
(5 wins), the 3 tasks with their 3 tiers each, what each tier pays, and a
Claim button for everything that's ready. The rules live in mastery.py.
============================================================================
"""

import pygame

import cards
import config as cfg
import mastery
import sprites
from ui import Button, WHITE, dk_c

TASK_Y = 186
TASK_H = 160
GOLD_COL = (250, 206, 92)
DONE_COL = (120, 200, 120)


class MasteryMixin:
    def _open_mastery(self, key):
        self.mastery_key = key
        self.mastery_msg = ""
        self.state = "mastery"

    def _mastery_buttons(self):
        key = self.mastery_key
        out = []
        if mastery.claimable(self.profile, key):
            out.append(Button((cfg.WINDOW_W // 2 - 90, cfg.WINDOW_H - 98, 180, 40),
                              "Claim rewards", self._mastery_claim, "gold"))
        out.append(Button((cfg.WINDOW_W // 2 - 70, cfg.WINDOW_H - 50, 140, 38), "Back",
                          lambda: self._goto("cards"), "dark"))
        # browse the other cards without going back
        out.append(Button((14, 96, 34, 34), "<", lambda: self._mastery_step(-1), "dark"))
        out.append(Button((cfg.WINDOW_W - 48, 96, 34, 34), ">", lambda: self._mastery_step(1),
                          "dark"))
        return out

    def _mastery_step(self, d):
        self._cards_init()
        keys = [c.key for c in self._cards_list()] or [c.key for c in cards.DEPLOYABLE_CARDS]
        i = keys.index(self.mastery_key) if self.mastery_key in keys else 0
        self.mastery_key = keys[(i + d) % len(keys)]
        self.cards_sel = self.mastery_key
        self.mastery_msg = ""

    def _mastery_claim(self):
        got = mastery.claim(self.profile, self.mastery_key)
        if got:
            self.sfx.play("crown", 0.8, min_gap=0.0)
            self.mastery_msg = "Claimed!"

    def _mastery_click(self, pos):
        for b in self._mastery_buttons():
            if b.click(pos):
                return

    # ---------------------------------------------------------------- draw
    def _draw_mastery(self):
        key = self.mastery_key
        c = cards.CARDS[key]
        p = self.profile
        W = cfg.WINDOW_W
        self._screen_title("Card Mastery", 26)
        self._wallet(W // 2, 62, ("gold", "gems"))
        # ---- header
        hd = self._panel((56, 84, W - 112, 92), border=(150, 130, 80))
        self.screen.blit(sprites.get_sprite(key, 70), (hd.x + 8, hd.y + 10))
        self._text(c.name, self.font_m, topleft=(hd.x + 88, hd.y + 8))
        lvl = mastery.mastery_level(p, key)
        r = p.mastery.get(key, {})
        if mastery.unlocked(p, key):
            self._text("Mastery %d / 9" % lvl, self.font_sb, GOLD_COL,
                       topleft=(hd.x + 88, hd.y + 34))
            stars = pygame.Rect(hd.x + 88, hd.y + 58, 9 * 18, 16)
            for i in range(9):
                col = GOLD_COL if i < lvl else (60, 64, 84)
                self._mastery_star(stars.x + 8 + i * 18, stars.centery, 7, col)
        else:
            w = r.get("w", 0)
            self._text("Win %d Battles with %s to unlock Mastery" % (mastery.UNLOCK_WINS, c.name),
                       self.font_s, (220, 224, 236), topleft=(hd.x + 88, hd.y + 36))
            bar = pygame.Rect(hd.x + 88, hd.y + 58, hd.w - 150, 12)
            pygame.draw.rect(self.screen, (30, 34, 46), bar, border_radius=6)
            pygame.draw.rect(self.screen, (110, 150, 230),
                             (bar.x, bar.y, int(bar.w * min(w, 5) / 5), bar.h), border_radius=6)
            self._text("%d/%d" % (min(w, 5), mastery.UNLOCK_WINS), self.font_s, WHITE,
                       topleft=(bar.right + 6, bar.y - 2))
            self._reward_row(mastery.UNLOCK_REWARD, hd.right - 10, hd.y + 16, self.font_s, r=6)
        # ---- tasks
        for i in range(3):
            self._draw_mastery_task(key, i, pygame.Rect(12, TASK_Y + i * (TASK_H + 8),
                                                         W - 24, TASK_H))
        for b in self._mastery_buttons():
            b.draw(self.screen, self.font_m if b.label not in ("<", ">") else self.font_sb)
        if self.mastery_msg:
            self._text(self.mastery_msg, self.font_sb, (150, 240, 160),
                       center=(W // 2, cfg.WINDOW_H - 112))

    def _mastery_star(self, x, y, r, col):
        import math
        pts = []
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5
            rr = r if k % 2 == 0 else r * 0.45
            pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
        pygame.draw.polygon(self.screen, col, pts)
        pygame.draw.polygon(self.screen, dk_c(col, 60), pts, 1)

    def _draw_mastery_task(self, key, i, rect):
        p = self.profile
        is_open = mastery.task_open(p, key, i)
        rec = p.mastery.get(key, {})
        prog = rec.get("p", [0, 0, 0])[i]
        claimed = rec.get("c", [0, 0, 0])[i]
        goals = mastery.goals(key, i)
        done = mastery.reached(p, key, i)
        self._panel(rect, border=GOLD_COL if is_open else (70, 76, 98),
                    top=(42, 46, 64) if is_open else (32, 34, 44),
                    bottom=(28, 30, 44) if is_open else (24, 25, 32))
        head = "Task %d - %s" % (i + 1, mastery.title(key, i))
        self._text(head, self.font_sb, WHITE if is_open else (150, 152, 166),
                   topleft=(rect.x + 12, rect.y + 8))
        if not is_open:
            if not mastery.unlocked(p, key):
                why = "Unlock Mastery first (5 wins)"
            else:
                why = "Opens at card level %d (now %d)" % (mastery.TASK_LEVEL[i],
                                                            p.level(key))
            self._text(why, self.font_s, (240, 180, 120),
                       topleft=(rect.right - 12 - self.font_s.size(why)[0], rect.y + 10))
        cur_goal = goals[min(done, 2)]
        desc = mastery.describe(key, i, cur_goal)
        self._text(self._fit(desc, self.font_s, rect.w - 24), self.font_s,
                   (210, 214, 230) if is_open else (130, 132, 146),
                   topleft=(rect.x + 12, rect.y + 30))
        # progress bar towards the current tier
        bar = pygame.Rect(rect.x + 12, rect.y + 52, rect.w - 130, 12)
        pygame.draw.rect(self.screen, (30, 34, 46), bar, border_radius=6)
        frac = min(1.0, prog / max(cur_goal, 1))
        pygame.draw.rect(self.screen, DONE_COL if done >= 3 else (110, 150, 230),
                         (bar.x, bar.y, max(0, int(bar.w * frac)), bar.h), border_radius=6)
        self._text("{:,} / {:,}".format(min(prog, cur_goal), cur_goal), self.font_s,
                   (220, 224, 236), topleft=(bar.right + 8, bar.y - 2))
        # the 3 tiers
        tw = (rect.w - 24 - 2 * 8) // 3
        for t in range(3):
            tr = pygame.Rect(rect.x + 12 + t * (tw + 8), rect.y + 74, tw, rect.h - 84)
            got = t < claimed
            ready = (not got) and t < done
            bg = (34, 52, 40) if got else ((70, 64, 34) if ready else (34, 36, 48))
            pygame.draw.rect(self.screen, bg, tr, border_radius=8)
            pygame.draw.rect(self.screen, DONE_COL if got else (GOLD_COL if ready else (64, 68, 88)),
                             tr, 2 if ready else 1, border_radius=8)
            self._text("Tier %d" % (t + 1), self.font_s, (200, 204, 220),
                       topleft=(tr.x + 8, tr.y + 5))
            self._text("{:,}".format(goals[t]), self.font_s, (160, 166, 186),
                       topleft=(tr.right - 8 - self.font_s.size("{:,}".format(goals[t]))[0],
                                tr.y + 5))
            rw = mastery.TIER_REWARDS[t]
            kind, n = next(iter(rw.items()))
            self._reward_icon(kind, tr.centerx - 22, tr.y + 44, 11)
            self._text("%d" % n, self.font_m, (255, 214, 90) if kind == "gold" else (90, 220, 120),
                       topleft=(tr.centerx - 6, tr.y + 32))
            if got:
                self._text("Claimed", self.font_s, DONE_COL, center=(tr.centerx, tr.bottom - 10))
            elif ready:
                self._text("Ready!", self.font_s, GOLD_COL, center=(tr.centerx, tr.bottom - 10))
