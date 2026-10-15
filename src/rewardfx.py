"""
============================================================================
  REWARDFX.PY  --  Collected rewards fly to the top bar (mixed into Game)
============================================================================

Whenever you gain trophies, King XP, gold, gems, Evo shards or Hero coins -
battle rewards, achievements, the Shop, the Trophy Road, King rewards - each
kind of reward takes its turn: it pops up in the middle of the screen with
its amount, then flies up to its counter in the top bar, which counts up as
it lands.

Screens without the top bar (the battle result, Achievements...) get a
lightweight one for the occasion: just the icons and numbers along the top,
no boxes, which fades out 2 seconds after the last reward has landed.

It watches the profile itself (any increase is a reward), so every way of
earning something is covered without each screen having to ask for it.
============================================================================
"""

import math

import pygame

import config as cfg
import king

KINDS = ("trophy", "xp", "gold", "gems", "shards", "coins")
POP, HOLD, FLY = 0.32, 0.28, 0.48     # seconds of each phase
GAP = POP + HOLD + 0.02               # the next pops as this one flies off
COUNT = 0.35                          # count-up once it lands
LINGER, FADE = 2.0, 0.5               # stand-alone bar: wait, then fade out
TOP_H = 52


class RewardFXMixin:
    def _rfx_values(self):
        p = self.profile
        return {"trophy": p.trophies, "xp": p.king_xp, "gold": p.gold, "gems": p.gems,
                "shards": p.shards, "coins": p.hero_coins}

    def _rfx_init(self):
        self._rfx_seen = self._rfx_values()
        self._rfx_items = []          # [{kind, amount, start}]
        self._rfx_bar_kinds = []      # kinds on the stand-alone bar
        self._rfx_done_at = None      # when the last reward landed

    # ---------------------------------------------------------------- state
    def _rfx_tick(self):
        """Spot new rewards (any increase since last frame) and queue them."""
        if not hasattr(self, "_rfx_seen"):
            self._rfx_init()
        now = self._now()
        vals = self._rfx_values()
        if getattr(self, "sandbox", False):
            self._rfx_seen = vals
            return
        start = max([now] + [it["start"] + GAP for it in self._rfx_items])
        for k in KINDS:
            d = vals[k] - self._rfx_seen.get(k, vals[k])
            if d > 0:
                self._rfx_items.append({"kind": k, "amount": d, "start": start})
                if k not in self._rfx_bar_kinds:
                    self._rfx_bar_kinds.append(k)
                start += GAP
                self._rfx_done_at = None
        self._rfx_seen = vals
        # forget rewards that have landed and finished counting
        end = POP + HOLD + FLY + COUNT
        if self._rfx_items and all(now - it["start"] > end for it in self._rfx_items):
            self._rfx_done_at = max(it["start"] for it in self._rfx_items) + end
            self._rfx_items = []

    def _rfx_pending(self, kind):
        """How much of `kind` hasn't reached its counter yet."""
        now = self._now()
        left = 0.0
        for it in getattr(self, "_rfx_items", []):
            if it["kind"] != kind:
                continue
            t = now - it["start"] - (POP + HOLD + FLY)
            if t < 0:
                left += it["amount"]
            elif t < COUNT:
                left += it["amount"] * (1.0 - t / COUNT)
        return left

    def _rfx_shown(self, kind):
        """The number a counter should show right now (counts up as rewards
        land)."""
        return int(round(self._rfx_values()[kind] - self._rfx_pending(kind)))

    # ---------------------------------------------------------------- drawing
    def _rfx_slots(self, kinds=KINDS):
        """Top-bar layout: {kind: (icon centre, chip rect)} - shared by the
        home top bar and the stand-alone bar."""
        out = {}
        cy = TOP_H // 2
        out["xp"] = ((26, 26), pygame.Rect(6, 6, 40, 40))
        x = 52
        for k in ("trophy", "gold", "gems", "shards", "coins"):
            s = "%d" % self._rfx_shown(k)
            w = self.font_sb.size(s)[0] + 30
            chip = pygame.Rect(x, cy - 13, w, 26)
            out[k] = ((chip.x + 12, cy), chip)
            x = chip.right + 4
        return out

    def _rfx_bar_slots(self):
        """Stand-alone bar: the collected kinds side by side from the left."""
        out = {}
        cy = TOP_H // 2
        x = 14
        for k in self._rfx_bar_kinds or KINDS:
            if k == "xp":
                out[k] = ((x + 14, cy), pygame.Rect(x, cy - 14, 28, 28))
                x += 36
                continue
            w = self.font_sb.size("%d" % self._rfx_shown(k))[0] + 26
            out[k] = ((x + 9, cy), pygame.Rect(x, cy - 13, w, 26))
            x += w + 8
        for k in KINDS:                       # (a reward not on the bar yet)
            out.setdefault(k, ((x + 9, cy), pygame.Rect(x, cy - 13, 20, 26)))
        return out

    def _rfx_draw(self):
        self._rfx_tick()
        now = self._now()
        home = self._home_active()
        slots = self._rfx_slots() if home else self._rfx_bar_slots()
        # the stand-alone bar (no home top bar on this screen)
        alpha = 0
        if self._rfx_items:
            alpha = 255
        elif self._rfx_done_at is not None:
            t = now - self._rfx_done_at
            alpha = 255 if t < LINGER else int(255 * max(0.0, 1.0 - (t - LINGER) / FADE))
            if t > LINGER + FADE:
                self._rfx_done_at = None
                self._rfx_bar_kinds = []
        if not home and alpha > 0 and self._rfx_bar_kinds:
            self._rfx_draw_bar(slots, alpha)
        if home and not self._rfx_items:
            self._rfx_bar_kinds = []
        # the flying rewards
        for it in self._rfx_items:
            self._rfx_draw_item(it, now, slots)

    def _rfx_draw_bar(self, slots, alpha):
        layer = pygame.Surface((cfg.WINDOW_W, TOP_H), pygame.SRCALPHA)
        old = self.screen
        self.screen = layer
        try:
            cy = TOP_H // 2
            for k in self._rfx_bar_kinds:
                (ix, iy), chip = slots[k]
                if k == "xp":
                    lv = king.level_for(self._rfx_shown("xp"))
                    self._xp_icon(ix, iy, 14)
                    self._text(str(lv), self.font_sb, center=(ix, iy))
                    continue
                self._rfx_icon(k, ix, iy, 8)
                self._text("%d" % self._rfx_shown(k), self.font_sb, self._rfx_col(k),
                           topleft=(ix + 11, cy - 9), outline=True)
        finally:
            self.screen = old
        layer.set_alpha(alpha)
        self.screen.blit(layer, (0, 0))

    def _rfx_draw_item(self, it, now, slots):
        t = now - it["start"]
        if t >= 0 and not it.get("popped"):
            it["popped"] = True
            self.sfx.play("ui_select", 0.6, min_gap=0.0)
        if t >= POP + HOLD + FLY and not it.get("landed"):
            it["landed"] = True
            self.sfx.play("ui_click", 0.7, min_gap=0.0)
        if t < 0 or t > POP + HOLD + FLY:
            return
        k = it["kind"]
        cx, cy = cfg.WINDOW_W // 2, int(cfg.WINDOW_H * 0.42)
        (tx, ty), _ = slots[k]
        big, small = 30, (14 if k == "xp" else 8)
        if t < POP:                                   # pop in (overshoot)
            f = t / POP
            scale = math.sin(f * math.pi * 0.75) / math.sin(math.pi * 0.75)
            x, y, r, a = cx, cy, max(2, int(big * scale)), 255
        elif t < POP + HOLD:
            x, y, r, a = cx, cy, big, 255
        else:                                         # fly up to the counter
            f = (t - POP - HOLD) / FLY
            e = f * f * (3 - 2 * f)
            x = cx + (tx - cx) * e
            y = cy + (ty - cy) * e - math.sin(math.pi * e) * 40
            r = int(big + (small - big) * e)
            a = int(255 * (1.0 - max(0.0, f - 0.6) / 0.4 * 0.3))
        if t < POP + HOLD + FLY * 0.5:                # "+N" under the icon
            glow = pygame.Surface((big * 4, big * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 240, 180, 50), (big * 2, big * 2), big * 2)
            self.screen.blit(glow, (int(x) - big * 2, int(y) - big * 2))
        self._rfx_icon(k, x, y, r)
        if t < POP + HOLD + FLY * 0.3:
            label = ("+%d XP" % it["amount"] if k == "xp" else
                     "+%d trophies" % it["amount"] if k == "trophy" else "+%d" % it["amount"])
            self._text(label, self.font_l, self._rfx_col(k),
                       center=(int(x), int(y) + big + 18), outline=True)

    def _rfx_icon(self, kind, x, y, r):
        if kind == "trophy":
            self._trophy_icon(int(x), int(y), r)
        else:
            self._reward_icon(kind, x, y, r)

    @staticmethod
    def _rfx_col(kind):
        return {"trophy": (255, 214, 90), "xp": (150, 200, 255), "gold": (255, 214, 90),
                "gems": (90, 220, 120), "shards": (200, 140, 255),
                "coins": (255, 200, 70)}[kind]
