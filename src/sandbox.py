"""
============================================================================
  SANDBOX.PY  --  Training Sandbox (mixed into game.Game)
============================================================================

A free practice arena for trying out matchups and mechanics:

  * PLACE ANY CARD for either side: pick a card from the strip at the bottom,
    choose the side (You / Enemy), its level (11-16) and whether it comes out
    as its Evolution or Hero, then click the arena. You have infinite elixir
    and can place anywhere except the river and on top of a tower.
  * TIME CONTROLS (top bar): pause / play, step 0.1 s, speed 0.25x-2x,
    reset (fresh towers, empty field).
  * AI OPPONENT: switch an AI (intelligence 1-5) on or off at any moment;
    while it's on it plays its AI deck with normal elixir.
  * INSPECTOR: with no card picked, click any unit (or tower) to follow its
    live stats - health, damage, range (drawn on the arena), what it's
    targeting, wind-up / charge / status effects, remaining lifetime.
    Champions and Heroes on the field can use their ability from here.

Nothing in the sandbox touches your progress or stats.
============================================================================
"""

import pygame

import config as cfg
import cards
import evos
import sprites
from engine import Match, PLAYER, ENEMY, RIVER_TOP, RIVER_BOTTOM, dist
from ai import AIController
from ui import Button, WHITE, lt_c, dk_c, tile_to_px, px_to_tile, render_text

SPEEDS = (0.25, 0.5, 1.0, 2.0)
ICON = 40                     # card icon size in the strip
STRIP_ROWS = 2


class SandboxMixin:
    # ------------------------------------------------------------ open/reset
    def _open_sandbox(self):
        sb = getattr(self, "sb", None)
        if sb is None:
            self.sb = sb = {"side": PLAYER, "level": cards.LEVEL_BASE, "evo": False,
                            "hero": False, "pick": None, "speed": 2, "paused": False,
                            "ai_on": False, "ai_level": 3, "scroll": 0, "inspect": None,
                            "drag": None, "keys": sorted(
                                (c.key for c in cards.DEPLOYABLE_CARDS),
                                key=lambda k: (cards.CARDS[k].elixir, cards.CARDS[k].name))}
        self._sandbox_reset()
        self.state = "sandbox"

    def _sandbox_reset(self):
        sb = self.sb
        ai_deck = self._resolve_ai_deck()
        self.sb_ai_deck = ai_deck
        self._arena_surf = None
        self.level_run = None
        self.mode = "sandbox"
        self.match = Match(self.player_deck if len(self.player_deck) == cfg.DECK_SIZE
                           else cards.DEFAULT_PLAYER_DECK, ai_deck)
        self.match.record_events = True
        self.selected = None
        self.drag_card = None
        self._audio = {}
        self.fx.clear()
        sb["inspect"] = None
        self.sb_ai = (AIController(self.match, team=ENEMY, level=sb["ai_level"])
                      if sb["ai_on"] else None)

    # ------------------------------------------------------------ per frame
    def _sandbox_update(self, dt):
        sb, m = self.sb, self.match
        m.elixir[PLAYER] = cfg.ELIXIR_MAX           # infinite elixir for you
        if not sb["ai_on"]:
            m.elixir[ENEMY] = cfg.ELIXIR_MAX
        step = sb.pop("step", 0.0)
        if sb["paused"] and not step:
            return
        mdt = step if step else dt * SPEEDS[sb["speed"]] * self.opt_speed
        # the clock never runs out in the sandbox
        m.time_left = max(m.time_left, 120.0)
        m.update(mdt)
        if self.sb_ai is not None:
            self.sb_ai.update(mdt)
        if m.finished:                              # a King Tower fell
            m.finished = False
            m.winner = None
        self._handle_events(m.take_events())
        self.fx.update(mdt, m)
        ins = sb["inspect"]
        if ins is not None and not ins.alive:
            sb["inspect"] = None

    # ------------------------------------------------------------ layout
    def _sb_top_buttons(self):
        sb = self.sb
        y, h = 6, 28
        specs = [("Back", 56, self._sb_back, "danger"),
                 ("Play" if sb["paused"] else "Pause", 64, self._sb_pause,
                  "go" if sb["paused"] else "dark"),
                 ("Step", 52, self._sb_step, "dark"),
                 ("%gx" % SPEEDS[sb["speed"]], 52, self._sb_speed, "primary"),
                 ("Reset", 62, self._sandbox_reset, "gold")]
        out, x = [], 6
        for lbl, w, cb, st in specs:
            out.append(Button((x, y, w, h), lbl, cb, st))
            x += w + 5
        return out

    def _sb_ctrl_buttons(self):
        sb = self.sb
        y, h = cfg.HUD_Y + 4, 26
        side = "You" if sb["side"] == PLAYER else "Enemy"
        specs = [("Side: " + side, 86, self._sb_side, "primary" if sb["side"] == PLAYER
                  else "danger"),
                 ("-", 22, lambda: self._sb_level(-1), "dark"),
                 ("Lv %d" % sb["level"], 46, lambda: None, "dark"),
                 ("+", 22, lambda: self._sb_level(1), "dark"),
                 ("Evo", 42, self._sb_evo, "gold" if sb["evo"] else "dark"),
                 ("Hero", 46, self._sb_hero, "gold" if sb["hero"] else "dark"),
                 ("AI: " + ("ON" if sb["ai_on"] else "off"), 62,
                  self._sb_ai_toggle, "go" if sb["ai_on"] else "dark"),
                 ("L%d" % sb["ai_level"], 38, self._sb_cycle_ai_level, "primary")]
        out, x = [], 6
        for lbl, w, cb, st in specs:
            out.append(Button((x, y, w, h), lbl, cb, st))
            x += w + 3
        return out

    def _sb_strip_rect(self):
        y = cfg.HUD_Y + 36
        return pygame.Rect(4, y, cfg.WINDOW_W - 8, cfg.WINDOW_H - y - 4)

    def _sb_icon_rects(self):
        """[(key, rect)] for the card strip (2 rows, scrolls sideways)."""
        r = self._sb_strip_rect()
        step = ICON + 4
        out = []
        for i, k in enumerate(self.sb["keys"]):
            col, row = divmod(i, STRIP_ROWS)
            x = r.x + 2 + col * step - self.sb["scroll"]
            y = r.y + 2 + row * (ICON + 6)
            out.append((k, pygame.Rect(x, y, ICON, ICON + 4)))
        return out

    def _sb_max_scroll(self):
        cols = (len(self.sb["keys"]) + STRIP_ROWS - 1) // STRIP_ROWS
        return max(0, cols * (ICON + 4) - self._sb_strip_rect().w + 4)

    # ------------------------------------------------------------ actions
    def _sb_back(self):
        self.state = "menu"
        self.mode = None
        self.sb_ai = None

    def _sb_pause(self):
        self.sb["paused"] = not self.sb["paused"]

    def _sb_step(self):
        self.sb["paused"] = True
        self.sb["step"] = 0.1

    def _sb_speed(self):
        self.sb["speed"] = (self.sb["speed"] + 1) % len(SPEEDS)

    def _sb_side(self):
        self.sb["side"] = ENEMY if self.sb["side"] == PLAYER else PLAYER

    def _sb_level(self, d):
        self.sb["level"] = max(cards.LEVEL_MIN, min(cards.LEVEL_MAX, self.sb["level"] + d))

    def _sb_evo(self):
        self.sb["evo"] = not self.sb["evo"]
        if self.sb["evo"]:
            self.sb["hero"] = False

    def _sb_hero(self):
        self.sb["hero"] = not self.sb["hero"]
        if self.sb["hero"]:
            self.sb["evo"] = False

    def _sb_ai_toggle(self):
        sb = self.sb
        sb["ai_on"] = not sb["ai_on"]
        if sb["ai_on"]:
            # joins the match as it stands, with a fresh hand of elixir
            self.match.elixir[ENEMY] = cfg.ELIXIR_START
            self.sb_ai = AIController(self.match, team=ENEMY, level=sb["ai_level"])
        else:
            self.sb_ai = None

    def _sb_cycle_ai_level(self):
        sb = self.sb
        sb["ai_level"] = sb["ai_level"] % 5 + 1
        if self.sb_ai is not None:
            self.sb_ai = AIController(self.match, team=ENEMY, level=sb["ai_level"])

    def _sb_can_place(self, key, x, y):
        c = cards.CARDS[key]
        if not (0.3 < x < cfg.GRID_COLS - 0.3 and 0.3 < y < cfg.GRID_ROWS - 0.3):
            return False
        if c.category == "spell":
            return True
        if RIVER_TOP - 0.2 <= y <= RIVER_BOTTOM + 0.2 and not c.flying:
            return False
        return not self.match.on_tower(x, y, c)

    def _sb_deploy(self, x, y):
        sb, m = self.sb, self.match
        key = sb["pick"]
        if key is None or not self._sb_can_place(key, x, y):
            self.sfx.play("ui_invalid", 0.6)
            return
        team = sb["side"]
        lv = sb["level"]
        mult = cards.level_mult(lv)
        evo = sb["evo"] and key in evos.EVOS
        hero = sb["hero"] and key in evos.HEROES
        if hero:
            m.hero_cards[team].add(key)
        had = (m.team_power.get(team), m.team_level.get(team))
        m.team_power[team] = (mult, mult)
        m.team_level[team] = lv
        try:
            m._deploy(team, key, x, y, evo=evo, hero=hero, played=key)
        finally:
            for d, v in zip((m.team_power, m.team_level), had):
                if v is None:
                    d.pop(team, None)
                else:
                    d[team] = v

    def _sb_ability(self, e):
        m = self.match
        m.elixir[e.team] = cfg.ELIXIR_MAX
        if e.card.is_champion:
            ok = m.activate_ability(e.team)
        else:
            ok = m.activate_hero(e.team)
        if not ok:
            self.sfx.play("ui_invalid", 0.6)

    def _sb_inspect_panel_rect(self):
        return pygame.Rect(6, cfg.ARENA_Y0 + 4, 196, getattr(self, "_sb_panel_h", 150))

    def _sb_ability_rect(self):
        p = self._sb_inspect_panel_rect()
        return pygame.Rect(p.x + 8, p.bottom - 30, p.w - 16, 24)

    # ------------------------------------------------------------ input
    def _sandbox_click(self, pos, button=1):
        sb = self.sb
        if button == 3:
            sb["pick"] = None
            sb["inspect"] = None
            return
        for b in self._sb_top_buttons() + self._sb_ctrl_buttons():
            if b.rect.collidepoint(pos):
                b.cb()
                self.sfx.play("ui_toggle", 0.5, min_gap=0.0)
                return
        if self._sb_strip_rect().collidepoint(pos):
            for k, r in self._sb_icon_rects():
                if r.collidepoint(pos):
                    sb["pick"] = None if sb["pick"] == k else k
                    self.sfx.play("ui_select", 0.6, min_gap=0.0)
                    return
            return
        ins = sb["inspect"]
        if (ins is not None and ins.alive and (ins.card.is_champion or ins.hero)
                and self._sb_ability_rect().collidepoint(pos)):
            self._sb_ability(ins)
            return
        if not (cfg.ARENA_Y0 <= pos[1] < cfg.ARENA_Y0 + cfg.ARENA_PX_H):
            return
        tx, ty = px_to_tile(*pos)
        if sb["pick"] is not None:
            self._sb_deploy(tx, ty)
            return
        # inspector: nearest unit under the cursor
        best, bd = None, 1.4
        for e in self.match.entities:
            if not e.alive:
                continue
            d = dist(tx, ty, e.x, e.y) - (e.radius if e.is_tower else 0.0)
            if d < bd:
                best, bd = e, d
        sb["inspect"] = best

    def _sandbox_wheel(self, dy):
        sb = self.sb
        sb["scroll"] = max(0, min(self._sb_max_scroll(), sb["scroll"] - dy * 60))

    # ------------------------------------------------------------ drawing
    def _draw_sandbox(self):
        m, sb = self.match, self.sb
        m.dmg_numbers = self.opt_dmg_numbers
        self._draw_arena()
        self.fx.draw_decals(self.screen)
        for e in sorted(m.entities, key=lambda e: (e.flying, e.y)):
            self._draw_entity(e)
        for fx in m.effects:
            self._draw_effect(fx)
        self._draw_beams()
        for p in m.projectiles:
            self._draw_projectile(p)
        self.fx.draw_particles(self.screen)
        self._draw_popups()
        self._sb_draw_inspect()
        self._sb_draw_preview()
        # top bar
        self.screen.fill((26, 28, 40), (0, 0, cfg.WINDOW_W, cfg.TOP_BAR))
        for b in self._sb_top_buttons():
            b.draw(self.screen, self.font_sb)
        st = "PAUSED" if sb["paused"] else "Sandbox"
        self._text(st, self.font_sb, (255, 220, 120) if sb["paused"] else (200, 205, 220),
                   center=(cfg.WINDOW_W - 44, cfg.TOP_BAR // 2))
        # bottom panel
        self.screen.fill((24, 26, 38), (0, cfg.HUD_Y, cfg.WINDOW_W, cfg.WINDOW_H - cfg.HUD_Y))
        pygame.draw.line(self.screen, (92, 84, 64), (0, cfg.HUD_Y), (cfg.WINDOW_W, cfg.HUD_Y), 2)
        for b in self._sb_ctrl_buttons():
            b.draw(self.screen, self.font_s)
        strip = self._sb_strip_rect()
        pygame.draw.rect(self.screen, (34, 37, 52), strip, border_radius=6)
        clip = self.screen.get_clip()
        self.screen.set_clip(strip)
        for k, r in self._sb_icon_rects():
            if r.right < strip.x or r.x > strip.right:
                continue
            c = cards.CARDS[k]
            picked = sb["pick"] == k
            pygame.draw.rect(self.screen, (80, 70, 30) if picked else (50, 54, 72), r,
                             border_radius=5)
            self.screen.blit(sprites.get_sprite(k, ICON - 4), (r.x + 2, r.y + 1))
            self._text(str(c.elixir), self.font_s, (230, 150, 255), topleft=(r.x + 2, r.y))
            if picked:
                pygame.draw.rect(self.screen, (255, 222, 110), r, 2, border_radius=5)
        self.screen.set_clip(clip)
        # scroll bar
        ms = self._sb_max_scroll()
        if ms > 0:
            frac = sb["scroll"] / ms
            bw = max(30, int(strip.w * strip.w / (strip.w + ms)))
            bx = strip.x + int((strip.w - bw) * frac)
            pygame.draw.rect(self.screen, (120, 126, 150), (bx, strip.bottom - 3, bw, 3))
        if sb["pick"]:
            c = cards.CARDS[sb["pick"]]
            tag = c.name + (" (Evo)" if sb["evo"] and sb["pick"] in evos.EVOS else
                            " (Hero)" if sb["hero"] and sb["pick"] in evos.HEROES else "")
            self._text(tag + "  -  click the arena", self.font_s, (255, 222, 110),
                       topleft=(8, cfg.ARENA_Y0 + cfg.ARENA_PX_H - 16))

    def _sb_draw_preview(self):
        sb = self.sb
        key = sb["pick"]
        if key is None:
            return
        mx, my = pygame.mouse.get_pos()
        if not (cfg.ARENA_Y0 <= my < cfg.ARENA_Y0 + cfg.ARENA_PX_H):
            return
        c = cards.CARDS[key]
        tx, ty = px_to_tile(mx, my)
        ok = self._sb_can_place(key, tx, ty)
        col = (90, 220, 90) if ok else (220, 80, 80)
        if c.category == "spell" and c.spell_radius > 0:
            self._range_ring((mx, my), c.spell_radius, col, 60, 140)
        if c.category == "building" and c.range > 0:
            self._range_ring((mx, my), c.range, (255, 255, 255), 34, 150)
            if c.min_range:
                self._range_ring((mx, my), c.min_range, (40, 40, 40), 46, 120)
        if c.category != "spell" and sb["side"] == PLAYER:
            self._draw_threat_warnings(c, tx, ty)
        ghost = sprites.get_sprite(key, 40).copy()
        ghost.set_alpha(150)
        self.screen.blit(ghost, (mx - 20, my - 44))
        pygame.draw.circle(self.screen, col, (mx, my), 8, 2)

    def _sb_draw_inspect(self):
        e = self.sb["inspect"]
        if e is None or not e.alive:
            return
        px, py = tile_to_px(e.x, e.y)
        teamc = cfg.COLOR_TEAM_PLAYER if e.team == PLAYER else cfg.COLOR_TEAM_ENEMY
        if e.range > 0:
            self._range_ring((px, py), e.range + e.radius * 0, teamc, 26, 170)
        if e.card.min_range:
            self._range_ring((px, py), e.card.min_range, (30, 30, 30), 40, 120)
        pygame.draw.circle(self.screen, (255, 230, 120), (int(px), int(py)),
                           int((e.radius + 0.25) * cfg.TILE_SIZE), 2)
        t = e.target
        if t is not None and t.alive:
            qx, qy = tile_to_px(t.x, t.y)
            pygame.draw.line(self.screen, (255, 230, 120), (px, py), (qx, qy), 2)
            pygame.draw.circle(self.screen, (255, 120, 90), (int(qx), int(qy)), 5, 2)
        # stats panel (sized to its content)
        name = ("King Tower" if e.is_king else "Princess Tower" if e.is_tower
                else e.card.name)
        if e.evo:
            name += " (Evo)"
        if e.hero:
            name += " (Hero)"
        lines = [(name, (255, 230, 150))]
        lines.append(("%s  -  level %s" % ("You" if e.team == PLAYER else "Enemy",
                                           getattr(e, "level", "?") or "?"), (190, 196, 215)))
        hp = "HP %d / %d" % (max(0, e.hp), e.max_hp)
        if e.shield > 0:
            hp += "  +%d shield" % e.shield
        lines.append((hp, WHITE))
        if e.dmg > 0:
            lines.append(("Hit %d every %.2fs  (%s)" % (
                e.dmg, e.effective_hitspeed(), {"ground": "ground", "air_ground": "air+ground",
                                                "buildings": "buildings"}.get(e.attacks, e.attacks)),
                WHITE))
            rng = "Range %.1f" % e.range + ("  (blind <%.1f)" % e.card.min_range
                                             if e.card.min_range else "")
            if not e.is_building and not e.is_tower:
                rng += "   Speed %.1f" % e.effective_speed()
            lines.append((rng, WHITE))
        tgt = "-" if t is None or not t.alive else (
            "King Tower" if t.is_king else "Princess Tower" if t.is_tower else t.card.name)
        lines.append(("Target: " + tgt, (255, 220, 140)))
        st = []
        if e.deploy_timer > 0:
            st.append("deploying %.1fs" % e.deploy_timer)
        if e.attack_cd > 0 and e.dmg > 0:
            st.append("next hit %.1fs" % e.attack_cd)
        if e.charge_enabled:
            st.append("CHARGING" if e.charged else "charge %.1f/%.0f" % (
                min(e.dist_since_attack, e.charge_dist), e.charge_dist))
        for attr, lbl in (("stun_timer", "stunned"), ("freeze_timer", "frozen"),
                          ("slow_timer", "slowed"), ("rage_timer", "raged"),
                          ("invis_timer", "hidden")):
            v = getattr(e, attr, 0)
            if v > 0:
                st.append("%s %.1fs" % (lbl, v))
        if e.is_building and e.card.lifetime and not e.is_tower:
            st.append("%.0fs left" % e.lifetime)
        txt = ", ".join(st) or "idle"
        width = 196 - 16
        words, cur = txt.split(" "), ""
        for w in words:                       # wrap the status line
            trial = (cur + " " + w).strip()
            if self.font_s.size(trial)[0] > width and cur:
                lines.append((cur, (170, 220, 255)))
                cur = w
            else:
                cur = trial
        if cur:
            lines.append((cur, (170, 220, 255)))
        ability = e.card.is_champion or e.hero
        self._sb_panel_h = 12 + 17 * len(lines) + (32 if ability else 0)
        p = self._sb_inspect_panel_rect()
        bg = pygame.Surface(p.size, pygame.SRCALPHA)
        bg.fill((14, 16, 26, 215))
        self.screen.blit(bg, p.topleft)
        pygame.draw.rect(self.screen, lt_c(teamc, 20), p, 2, border_radius=6)
        y = p.y + 6
        for s_, col in lines:
            self._text(s_, self.font_s, col, topleft=(p.x + 8, y))
            y += 17
        if ability:
            r = self._sb_ability_rect()
            used = e.ability_uses <= 0 if e.card.is_champion else False
            Button(r, "Ability (used)" if used else "Use ability", lambda: None,
                   "dark" if used else "gold").draw(self.screen, self.font_s)
