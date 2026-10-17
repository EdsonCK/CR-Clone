"""
============================================================================
  ENDLESS_UI.PY  --  Endless Survival upgrade picker (mixed into game.Game)
============================================================================

After every 5th Endless wave the run offers two upgrades (see
endless_upgrades.py): while `level_run.choice` is set the match is paused
(game.Game.run skips the updates) and this draws two big pick cards over the
arena. Click one - or press 1 / 2 - to take it.

During the run the upgrades taken so far sit in a small panel in the left
scenery margin (hover it for the full list); the end-of-run screen shows
them as a row of icons.
============================================================================
"""

import math
import pygame

import config as cfg
import cards
import sprites
from ui import lt_c, dk_c, render_text, grad_rect

TIER_COLS = {"rare": (84, 156, 255), "epic": (186, 104, 255),
             "legendary": (255, 196, 64)}
CHOICE_W, CHOICE_H, CHOICE_GAP = 236, 310, 16


def _wrap(text, font, maxw):
    """Split `text` into lines no wider than `maxw`."""
    lines, line = [], ""
    for word in text.split():
        test = (line + " " + word).strip()
        if line and font.size(test)[0] > maxw:
            lines.append(line)
            line = word
        else:
            line = test
    if line:
        lines.append(line)
    return lines


class EndlessUIMixin:
    # ------------------------------------------------------------ state
    def _endless_choice(self):
        """The pending upgrade choice of an Endless run, else None."""
        run = self.level_run
        if self.state != "match" or self.mode != "endless" or run is None:
            return None
        return getattr(run, "choice", None) or None

    def _choice_rects(self):
        ch = self._endless_choice() or []
        n = len(ch)
        total = n * CHOICE_W + max(0, n - 1) * CHOICE_GAP
        x0 = (cfg.WINDOW_W - total) // 2
        y = cfg.ARENA_Y0 + 118
        return [pygame.Rect(x0 + i * (CHOICE_W + CHOICE_GAP), y, CHOICE_W, CHOICE_H)
                for i in range(n)]

    def _choice_tick(self):
        """Once per frame: a cue when a new choice appears."""
        ch = self._endless_choice()
        if ch is not None and ch is not getattr(self, "_choice_seen", None):
            self._choice_seen = ch
            self._choice_t0 = self._now()
            self.selected = None
            self.drag_card = None
            self.sfx.play("crown", 0.8, min_gap=0.0)

    def _choice_pick(self, i):
        ch = self._endless_choice()
        if not ch or not 0 <= i < len(ch):
            return False
        self.level_run.choose(i)
        self.selected = None
        self.drag_card = None
        self.sfx.play("evo_deploy", 0.6, min_gap=0.0)
        return True

    def _choice_click(self, pos):
        for i, r in enumerate(self._choice_rects()):
            if r.collidepoint(pos):
                self._choice_pick(i)
                return

    # ------------------------------------------------------------ icons
    def _upgrade_icon(self, u, size):
        """Picture for an upgrade: its card, or a drawn emblem for boons."""
        if u.icon and u.icon in cards.CARDS:
            return sprites.get_sprite(u.icon, size)
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        col = TIER_COLS.get(u.tier, TIER_COLS["epic"])
        c = size // 2
        pygame.draw.circle(surf, dk_c(col, 70), (c, c), c - 1)
        pygame.draw.circle(surf, dk_c(col, 30), (c, c), c - 1, max(2, size // 22))
        text = (u.title + " " + u.desc).lower()
        if "elixir" in text:
            # elixir drop
            s = size / 100.0
            pts = [(c, c - 34 * s), (c + 22 * s, c + 4 * s), (c + 20 * s, c + 18 * s),
                   (c, c + 32 * s), (c - 20 * s, c + 18 * s), (c - 22 * s, c + 4 * s)]
            pygame.draw.polygon(surf, (214, 72, 230), pts)
            pygame.draw.polygon(surf, (250, 190, 255), pts, max(1, size // 40))
            pygame.draw.circle(surf, (255, 230, 255), (int(c - 8 * s), int(c + 2 * s)),
                               max(2, int(6 * s)))
        else:
            # a little crown tower: body, battlements, door
            s = size / 100.0
            body = pygame.Rect(0, 0, int(44 * s), int(46 * s))
            body.midbottom = (c, int(c + 30 * s))
            pygame.draw.rect(surf, (226, 214, 190), body)
            for k in range(4):
                bx = body.x + int(k * 13 * s)
                pygame.draw.rect(surf, (226, 214, 190), (bx, body.y - int(10 * s),
                                                         int(8 * s), int(11 * s)))
            pygame.draw.rect(surf, (120, 92, 62), body, max(1, size // 40))
            door = pygame.Rect(0, 0, int(14 * s), int(18 * s))
            door.midbottom = body.midbottom
            pygame.draw.rect(surf, (90, 60, 40), door, border_radius=max(1, int(6 * s)))
            # banner in the tier colour
            pole = (int(c), int(body.y - 10 * s))
            pygame.draw.line(surf, (60, 50, 40), pole, (pole[0], pole[1] - int(22 * s)),
                             max(1, size // 40))
            pygame.draw.polygon(surf, col, [(pole[0], pole[1] - int(22 * s)),
                                            (pole[0] + int(20 * s), pole[1] - int(16 * s)),
                                            (pole[0], pole[1] - int(10 * s))])
        return surf

    # ------------------------------------------------------------ drawing
    def _draw_upgrade_choice(self):
        ch = self._endless_choice()
        if not ch:
            return
        t = self._now()
        age = t - getattr(self, "_choice_t0", t)
        shade = pygame.Surface((cfg.WINDOW_W, cfg.WINDOW_H), pygame.SRCALPHA)
        shade.fill((6, 8, 16, 185))
        self.screen.blit(shade, (0, 0))
        cx = cfg.WINDOW_W // 2
        run = self.level_run
        self._text("Choose an upgrade", self.font_l, (255, 214, 110),
                   center=(cx, cfg.ARENA_Y0 + 46))
        self._text("Wave %d cleared - it lasts the rest of the run" % run.wave_number,
                   self.font_sb, (220, 224, 236), center=(cx, cfg.ARENA_Y0 + 82))
        mouse = pygame.mouse.get_pos()
        rise = min(1.0, age / 0.3)
        for i, (u, r) in enumerate(zip(ch, self._choice_rects())):
            hover = r.collidepoint(mouse)
            rr = r.move(0, int((1 - rise) * 40) - (6 if hover else 0))
            self._draw_pick_card(u, rr, hover, i, t)
        self._text("Click a card  -  or press 1 / 2", self.font_sb, (190, 196, 214),
                   center=(cx, cfg.ARENA_Y0 + 118 + CHOICE_H + 34))
        n = len(getattr(run, "picks", []))
        if n:
            self._text("Upgrades so far: %d" % n, self.font_s, (170, 176, 196),
                       center=(cx, cfg.ARENA_Y0 + 118 + CHOICE_H + 56))

    def _draw_pick_card(self, u, r, hover, i, t):
        col = TIER_COLS.get(u.tier, TIER_COLS["epic"])
        # glow
        pulse = 0.5 + 0.5 * math.sin(t * 4 + i * 1.7)
        glow = pygame.Surface((r.w + 24, r.h + 24), pygame.SRCALPHA)
        a = int((110 if hover else 55) + 50 * pulse)
        pygame.draw.rect(glow, col + (a,), glow.get_rect(), 10, border_radius=22)
        self.screen.blit(glow, (r.x - 12, r.y - 12))
        # body
        pygame.draw.rect(self.screen, (4, 6, 12), r.move(0, 5), border_radius=16)
        top = lt_c(dk_c(col, 120), 10 if hover else 0)
        self.screen.blit(grad_rect(r.w, r.h, top, (18, 18, 30), 16), r.topleft)
        pygame.draw.rect(self.screen, lt_c(col, 40) if hover else col, r, 3,
                         border_radius=16)
        # kind ribbon
        kind = "CARD UPGRADE" if u.kind == "card" else "BOON"
        rib = pygame.Rect(0, 0, 118, 22)
        rib.midtop = (r.centerx, r.y + 10)
        pygame.draw.rect(self.screen, dk_c(col, 40), rib, border_radius=11)
        pygame.draw.rect(self.screen, lt_c(col, 30), rib, 1, border_radius=11)
        self._text(kind, self.font_s, (255, 255, 255), center=rib.center, outline=True)
        # key hint
        self._text(str(i + 1), self.font_m, lt_c(col, 50), center=(r.x + 18, r.y + 20))
        # tier gem along the bottom edge
        gem = pygame.Rect(0, 0, 96, 20)
        gem.center = (r.centerx, r.bottom - 16)
        pygame.draw.rect(self.screen, dk_c(col, 60), gem, border_radius=10)
        pygame.draw.rect(self.screen, col, gem, 1, border_radius=10)
        self._text(u.tier.upper(), self.font_s, lt_c(col, 60), center=gem.center,
                   outline=True)
        # picture
        pic = pygame.Rect(0, 0, 112, 112)
        pic.midtop = (r.centerx, r.y + 42)
        pygame.draw.rect(self.screen, (12, 12, 22), pic, border_radius=14)
        pygame.draw.rect(self.screen, dk_c(col, 20), pic, 2, border_radius=14)
        bob = int(math.sin(t * 2.4 + i) * 3) if hover else 0
        self.screen.blit(self._upgrade_icon(u, 100), (pic.x + 6, pic.y + 6 + bob))
        y = pic.bottom + 8
        if u.kind == "card" and u.card in cards.CARDS:
            self._text(cards.CARDS[u.card].name, self.font_sb, lt_c(col, 50),
                       center=(r.centerx, y + 8), outline=True)
            y += 20
        # title
        for line in _wrap(u.title, self.font_m, r.w - 22)[:2]:
            self._text(line, self.font_m, (255, 255, 255), center=(r.centerx, y + 12))
            y += 24
        y += 6
        pygame.draw.line(self.screen, dk_c(col, 30), (r.x + 30, y), (r.right - 30, y), 1)
        y += 8
        # description
        for line in _wrap(u.desc, self.font_s, r.w - 26)[:5]:
            self._text(line, self.font_s, (222, 226, 238), center=(r.centerx, y + 8))
            y += 17
        # one-time or stacking (and how many you already have)
        owned = sum(1 for p in getattr(self.level_run, "picks", []) if p.key == u.key)
        note = ("One-time upgrade" if u.once else
                "Stacks - you have x%d" % owned if owned else "Stacks if picked again")
        self._text(note, self.font_s, (255, 214, 120) if owned else (170, 176, 196),
                   center=(r.centerx, r.bottom - 40), outline=True)

    def _draw_upgrade_list(self):
        """Upgrades taken so far, in the left scenery margin (hover: details)."""
        run = self.level_run
        picks = getattr(run, "picks", None) if run is not None else None
        if self.mode != "endless" or not picks or self._endless_choice():
            return
        shown = picks[-9:]
        w = cfg.ARENA_X0 - 10
        r = pygame.Rect(5, cfg.ARENA_Y0 + 8, w, 26 + 24 * len(shown))
        panel = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, (14, 16, 28, 200), panel.get_rect(), border_radius=9)
        self.screen.blit(panel, r.topleft)
        pygame.draw.rect(self.screen, (214, 176, 84), r, 1, border_radius=9)
        self._text("Upgrades %d" % len(picks), self.font_s, (255, 214, 110),
                   center=(r.centerx, r.y + 11), outline=True)
        for k, u in enumerate(shown):
            y = r.y + 22 + 24 * k
            self.screen.blit(self._upgrade_icon(u, 22), (r.x + 4, y))
            col = TIER_COLS.get(u.tier, TIER_COLS["epic"])
            self._text(self._fit(u.title, self.font_s, w - 32), self.font_s,
                       lt_c(col, 60), topleft=(r.x + 29, y + 4))
        if r.collidepoint(pygame.mouse.get_pos()):
            self._draw_upgrade_details(picks, r)

    def _draw_upgrade_details(self, picks, anchor):
        """Hover panel: every upgrade with its description."""
        w = 300
        rows = []
        for u in picks:
            lines = _wrap(u.desc, self.font_s, w - 44)[:3]
            rows.append((u, lines))
        h = 30 + sum(22 + 15 * len(ls) for _, ls in rows)
        r = pygame.Rect(anchor.right + 6, anchor.y, w, min(h, cfg.HUD_Y - anchor.y - 6))
        panel = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, (12, 14, 26, 235), panel.get_rect(), border_radius=10)
        self.screen.blit(panel, r.topleft)
        pygame.draw.rect(self.screen, (214, 176, 84), r, 1, border_radius=10)
        self._text("Your upgrades", self.font_sb, (255, 214, 110),
                   center=(r.centerx, r.y + 14), outline=True)
        self.screen.set_clip(r)
        y = r.y + 30
        for u, lines in rows:
            col = TIER_COLS.get(u.tier, TIER_COLS["epic"])
            self.screen.blit(self._upgrade_icon(u, 22), (r.x + 8, y))
            self._text(self._fit(u.title, self.font_sb, w - 44), self.font_sb, lt_c(col, 60),
                       topleft=(r.x + 36, y + 2))
            y += 20
            for ln in lines:
                self._text(ln, self.font_s, (210, 214, 228), topleft=(r.x + 36, y))
                y += 15
            y += 2
        self.screen.set_clip(None)

    def _result_upgrade_rows(self):
        """Extra panel height the end-of-run screen needs for the upgrades."""
        run = self.level_run
        if self.mode == "endless" and run is not None and getattr(run, "picks", None):
            return 44
        return 0

    def _draw_result_upgrades(self, panel, y):
        """A row of upgrade icons on the Endless end-of-run screen."""
        picks = self.level_run.picks
        self._text("Upgrades taken: %d" % len(picks), self.font_sb, (255, 214, 110),
                   topleft=(panel.x + 24, y))
        sz = 22
        room = panel.w - 48
        per = max(1, room // (sz + 4))
        x = panel.x + 24
        for k, u in enumerate(picks[:per]):
            self.screen.blit(self._upgrade_icon(u, sz), (x + k * (sz + 4), y + 18))
