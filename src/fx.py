"""
============================================================================
  FX.PY  --  Particles & spell visuals (purely cosmetic)
============================================================================

  * a small particle system (embers, smoke, sparks, debris, snow, bubbles...)
  * thrown spells (Fireball, Arrows, Rocket, Goblin Barrel, Snowball) are
    drawn flying in an arc from the caster's King Tower to their target
  * every spell has its own telegraph, impact and lingering look
  * ground decals: scorch marks, frost, arrows stuck in the turf, cracks

Nothing here affects the simulation - it only reads engine effects/events.
============================================================================
"""

import math
import random

import pygame

import config as cfg
import cards

TS = cfg.TILE_SIZE


def t2p(x, y):
    return (cfg.ARENA_X0 + x * TS, cfg.ARENA_Y0 + y * TS)


def _lerp(a, b, t):
    return a + (b - a) * t


def _mixc(c1, c2, t):
    return tuple(int(_lerp(a, b, t)) for a, b in zip(c1, c2))


# arc height (px) of each thrown spell
FLIGHT_ARC = {"fireball": 46, "arrows": 80, "rocket": 22, "goblin_barrel": 92,
              "snowball": 56}

TEAM_COL = {0: cfg.COLOR_TEAM_PLAYER, 1: cfg.COLOR_TEAM_ENEMY}


class P:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "size", "grow", "col",
                 "col2", "kind", "grav", "rot", "vr", "drag")

    def __init__(self, x, y, vx, vy, life, size, col, kind="dot", grav=0.0,
                 grow=0.0, col2=None, rot=0.0, vr=0.0, drag=0.0):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.size, self.grow, self.col, self.col2 = size, grow, col, col2 or col
        self.kind, self.grav, self.rot, self.vr, self.drag = kind, grav, rot, vr, drag


class Decal:
    __slots__ = ("x", "y", "r", "life", "max_life", "kind", "data")

    def __init__(self, x, y, r, life, kind, data=None):
        self.x, self.y, self.r = x, y, r
        self.life = self.max_life = life
        self.kind, self.data = kind, data


class FX:
    MAX_PARTICLES = 700

    def __init__(self):
        self.parts = []
        self.decals = []
        self.flash = 0.0            # full-screen lightning flash (0..1)
        self.rng = random.Random(5)
        self._alpha_cache = {}
        self._fx_data = {}          # per engine-effect cached shapes
        self.now = 0.0
        self.popups = []            # floating texts: {"x","y","text","col","age","life"}

    def clear(self):
        self.popups.clear()
        self.parts.clear()
        self.decals.clear()
        self._fx_data.clear()
        self.flash = 0.0

    # ------------------------------------------------------------ helpers
    def _circle(self, r, col, a):
        """Cached alpha circle surface."""
        r = max(1, int(r))
        a = max(0, min(255, int(a) // 12 * 12))
        key = (r, col, a)
        s = self._alpha_cache.get(key)
        if s is None:
            if len(self._alpha_cache) > 3000:
                self._alpha_cache.clear()
            s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, col + (a,), (r + 1, r + 1), r)
            self._alpha_cache[key] = s
        return s

    def _blit_circle(self, surf, x, y, r, col, a):
        c = self._circle(r, col, a)
        surf.blit(c, (int(x) - c.get_width() // 2, int(y) - c.get_height() // 2))

    def add(self, p):
        if len(self.parts) < self.MAX_PARTICLES:
            self.parts.append(p)

    def burst(self, x, y, n, speed, life, size, col, kind="dot", grav=0.0,
              spread=1.0, grow=0.0, col2=None, drag=1.5, up=0.0):
        r = self.rng
        for _ in range(n):
            a = r.uniform(0, math.tau)
            s = speed * r.uniform(0.35, 1.0)
            self.add(P(x, y, math.cos(a) * s * spread, math.sin(a) * s - up,
                       life * r.uniform(0.6, 1.2), size * r.uniform(0.6, 1.3), col,
                       kind, grav, grow, col2, r.uniform(0, 6), r.uniform(-8, 8), drag))

    # ------------------------------------------------------------ events
    def handle_events(self, evs, match=None):
        for ev in evs:
            k = ev["kind"]
            x, y = t2p(ev["x"], ev["y"])
            if k == "impact":
                self._impact(ev["key"], x, y, ev["x"], ev["y"], match)
            elif k == "deploy":
                c = cards.CARDS.get(ev["key"])
                if ev.get("evo"):
                    self.burst(x, y, 24, 110, 0.9, 3, (200, 130, 255), "spark", up=30)
                    self.burst(x, y, 8, 40, 1.0, 9, (150, 80, 220), "smoke", grow=12)
                if c is not None and c.category != "spell":
                    big = c.hp * max(c.count, 1) >= 1500 or c.category == "building"
                    self.burst(x, y + 6, 14 if big else 8, 70 if big else 45, 0.5,
                               5 if big else 3.5, (196, 170, 120), "dust", grow=10)
                    if c.is_champion:
                        self.burst(x, y, 18, 90, 0.8, 2.5, (255, 220, 110), "spark")
            elif k == "death":
                if ev.get("tower"):
                    self.burst(x, y, 40, 160, 1.2, 4, (150, 146, 136), "debris",
                               grav=320, up=140)
                    self.burst(x, y, 24, 50, 1.8, 10, (90, 86, 82), "smoke", grow=16)
                    self.decals.append(Decal(x, y, 2.2 * TS, 6.0, "scorch"))
                elif ev.get("building"):
                    self.burst(x, y, 18, 120, 0.9, 3.5, (130, 110, 90), "debris",
                               grav=300, up=100)
                    self.burst(x, y, 10, 40, 1.2, 8, (110, 106, 100), "smoke", grow=12)
                else:
                    n = 9 if ev.get("big") else 5
                    self.burst(x, y, n, 40, 0.55, 5 if ev.get("big") else 3.5,
                               (215, 215, 220), "smoke", grow=10)
                    # a little ghost floats up from every fallen troop
                    self.add(P(x, y - 4, 0, -28, 0.9, 6 if ev.get("big") else 4.5,
                               TEAM_COL.get(ev.get("team"), (220, 220, 230)), "ghost"))
            elif k == "land" and ev.get("slam"):
                self.burst(x, y + 4, 22, 120, 0.6, 5, (190, 160, 110), "dust", grow=8)
            elif k == "miasma":
                self.burst(x, y, 3, 18, 0.6, 2.5, (140, 210, 90), "bubble")
            elif k == "portal":
                self.burst(x, y, 22, 70, 0.9, 7, (110, 60, 150), "smoke", grow=10)
                self.burst(x, y, 16, 120, 0.6, 2.5, (200, 150, 255), "spark", up=20)
            elif k == "dmg":
                amt = ev.get("amount", 0)
                col = (255, 120, 110) if ev.get("tower") else (255, 255, 255)
                if amt >= 300:
                    col = (255, 210, 90)
                self.popups.append({"x": x + self.rng.uniform(-6, 6), "y": y - TS * 0.8,
                                    "text": "%d" % round(amt), "col": col, "age": 0.0,
                                    "life": 0.7, "small": True})
            elif k == "elixir_made":
                amt = ev.get("amount", 1)
                txt = "+%d" % amt if float(amt).is_integer() else "+%.1f" % amt
                self.popups.append({"x": x, "y": y - TS * 1.4, "text": txt + " elixir",
                                    "col": (250, 140, 255), "age": 0.0, "life": 1.2})
                self.burst(x, y - TS * 0.4, 10, 60, 0.6, 2.5, (240, 130, 255), "spark", up=40)
            elif k == "ability":
                self.burst(x, y, 26, 110, 0.8, 3, (255, 225, 120), "spark", up=30)

    def _impact(self, key, x, y, tx, ty, match):
        c = cards.CARDS.get(key)
        R = (c.spell_radius if c and c.spell_radius else 1.5) * TS
        r = self.rng
        if key == "fireball":
            self.burst(x, y, 30, 150, 0.7, 3.2, (255, 170, 60), "ember", grav=60,
                       col2=(180, 40, 20))
            self.burst(x, y, 10, 40, 1.3, 9, (80, 74, 70), "smoke", grow=14, up=20)
            self.decals.append(Decal(x, y, R * 0.8, 3.5, "scorch"))
        elif key == "rocket":
            self.burst(x, y, 50, 220, 0.9, 3.6, (255, 200, 90), "ember", grav=80,
                       col2=(200, 30, 20))
            self.burst(x, y, 22, 110, 1.0, 3.5, (110, 100, 90), "debris", grav=320, up=120)
            self.burst(x, y, 16, 60, 1.8, 12, (70, 66, 64), "smoke", grow=18, up=25)
            self.decals.append(Decal(x, y, R * 0.9, 5.0, "scorch"))
            self.flash = max(self.flash, 0.35)
        elif key == "arrows":
            for _ in range(22):
                a, d = r.uniform(0, math.tau), R * math.sqrt(r.random())
                px, py = x + math.cos(a) * d, y + math.sin(a) * d
                self.burst(px, py, 2, 25, 0.45, 3, (196, 176, 130), "dust", grow=6)
            self.decals.append(Decal(x, y, R, 1.6, "arrows",
                                     [(r.uniform(0, math.tau), R * math.sqrt(r.random()),
                                       r.uniform(-0.5, 0.5)) for _ in range(18)]))
        elif key == "zap":
            self.burst(x, y, 26, 200, 0.35, 2.5, (200, 240, 255), "spark")
        elif key == "lightning":
            self.flash = max(self.flash, 0.6)
            self.burst(x, y, 20, 160, 0.4, 2.5, (255, 250, 200), "spark")
        elif key == "freeze":
            self.burst(x, y, 34, 170, 0.8, 3, (190, 240, 255), "shard", drag=2.5)
            self.burst(x, y, 16, 50, 1.2, 3, (240, 250, 255), "snow", grav=-10)
            dur = c.freeze if c else 3.0
            self.decals.append(Decal(x, y, R, dur, "frost",
                                     [r.uniform(0, math.tau) for _ in range(9)]))
        elif key == "snowball":
            self.burst(x, y, 34, 140, 0.8, 3.2, (245, 250, 255), "snow", grav=200, up=60)
            self.burst(x, y, 10, 50, 0.8, 7, (225, 240, 255), "smoke", grow=10)
        elif key == "goblin_barrel":
            self.burst(x, y, 16, 130, 0.9, 3.5, (150, 100, 55), "debris", grav=330, up=110)
            self.burst(x, y, 12, 60, 0.7, 6, (200, 180, 130), "dust", grow=10)
        elif key == "barbarian_barrel":
            self.burst(x, y, 10, 70, 0.6, 5, (200, 180, 130), "dust", grow=8)
        elif key == "poison":
            self.burst(x, y, 18, 90, 0.6, 3, (140, 220, 90), "bubble")
        elif key == "earthquake":
            self.burst(x, y, 24, 120, 0.8, 3.5, (150, 110, 70), "debris", grav=300, up=80)
        elif key == "rage":
            self.burst(x, y, 30, 140, 0.8, 3, (230, 110, 240), "spark", up=40)
        elif key == "graveyard":
            self.burst(x, y, 20, 60, 1.2, 9, (90, 60, 120), "smoke", grow=10)
        elif key == "tornado":
            self.burst(x, y, 20, 90, 0.8, 5, (210, 214, 225), "dust", grow=8)
        elif key == "the_log":
            pass

    # ------------------------------------------------------------ update
    def update(self, dt, match=None):
        self.now += dt
        self.flash = max(0.0, self.flash - dt * 2.5)
        keep = []
        for p in self.parts:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vy += p.grav * dt
            if p.drag:
                k = max(0.0, 1.0 - p.drag * dt)
                p.vx *= k
                p.vy *= k
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.size += p.grow * dt * 0.3
            p.rot += p.vr * dt
            keep.append(p)
        self.parts = keep
        for pp in self.popups:
            pp["age"] += dt
        self.popups = [pp for pp in self.popups if pp["age"] < pp["life"]]
        self.decals = [d for d in self.decals if self._age(d, dt)]
        if match is not None:
            self._emit_from_effects(dt, match)

    @staticmethod
    def _age(d, dt):
        d.life -= dt
        return d.life > 0

    def _emit_from_effects(self, dt, match):
        """Continuous particles from flying spells and lingering zones."""
        r = self.rng
        for fx in match.effects:
            k = fx.kind
            if k == "incoming" and fx.origin is not None:
                (x, y), _ = self._flight_pos(fx)
                ck = fx.card_key
                if ck == "fireball":
                    for _ in range(2):
                        self.add(P(x + r.uniform(-3, 3), y + r.uniform(-3, 3),
                                   r.uniform(-15, 15), r.uniform(-15, 15), 0.35,
                                   r.uniform(2, 4), (255, 160, 50), "ember",
                                   col2=(160, 30, 10)))
                elif ck == "rocket":
                    self.add(P(x, y, r.uniform(-10, 10), r.uniform(-10, 10), 0.9,
                               r.uniform(4, 6), (200, 196, 190), "smoke", grow=14))
                elif ck == "snowball":
                    self.add(P(x, y, r.uniform(-10, 10), r.uniform(-10, 10), 0.4,
                               2, (240, 248, 255), "snow"))
            elif k == "poison" and fx.card_key == "poison":
                if r.random() < dt * 30:
                    a, d = r.uniform(0, math.tau), fx.radius * TS * math.sqrt(r.random())
                    x, y = t2p(fx.x, fx.y)
                    self.add(P(x + math.cos(a) * d, y + math.sin(a) * d, 0, -18,
                               r.uniform(0.6, 1.1), r.uniform(2, 4), (150, 230, 90), "bubble"))
            elif k == "poison" and fx.card_key == "earthquake":
                if r.random() < dt * 40:
                    a, d = r.uniform(0, math.tau), fx.radius * TS * math.sqrt(r.random())
                    x, y = t2p(fx.x, fx.y)
                    self.add(P(x + math.cos(a) * d, y + math.sin(a) * d,
                               r.uniform(-20, 20), r.uniform(-50, -20), 0.6,
                               r.uniform(2, 3.5), (150, 115, 75), "debris", grav=200))
            elif k == "rage":
                if r.random() < dt * 25:
                    a, d = r.uniform(0, math.tau), fx.radius * TS * math.sqrt(r.random())
                    x, y = t2p(fx.x, fx.y)
                    self.add(P(x + math.cos(a) * d, y + math.sin(a) * d, 0, -40,
                               0.7, 2.2, (235, 120, 245), "spark"))
            elif k == "graveyard":
                if r.random() < dt * 14:
                    a, d = r.uniform(0, math.tau), fx.radius * TS * math.sqrt(r.random())
                    x, y = t2p(fx.x, fx.y)
                    self.add(P(x + math.cos(a) * d, y + math.sin(a) * d, r.uniform(-6, 6),
                               -12, 1.6, r.uniform(5, 8), (150, 120, 190), "smoke", grow=6))
            elif k == "tornado":
                x, y = t2p(fx.x, fx.y)
                for _ in range(2):
                    a = r.uniform(0, math.tau)
                    d = fx.radius * TS * r.uniform(0.3, 1.0)
                    sp = 160
                    self.add(P(x + math.cos(a) * d, y + math.sin(a) * d,
                               -math.sin(a) * sp - math.cos(a) * 30,
                               math.cos(a) * sp - math.sin(a) * 30, 0.35,
                               r.uniform(2, 3), (215, 205, 180), "dust", grow=3))
            elif k == "log":
                if r.random() < dt * 30:
                    x, y = t2p(fx.x, fx.y)
                    w = fx.radius * TS
                    self.add(P(x + r.uniform(-w, w), y - fx.direction * 6, 0,
                               -fx.direction * 10, 0.5, 4, (190, 170, 125), "dust", grow=8))

    # ------------------------------------------------------------ drawing
    def draw_decals(self, surf):
        for d in self.decals:
            f = d.life / d.max_life
            if d.kind == "scorch":
                self._blit_circle(surf, d.x, d.y, d.r, (30, 24, 20), 90 * f)
                self._blit_circle(surf, d.x, d.y, d.r * 0.6, (20, 16, 14), 70 * f)
            elif d.kind == "frost":
                self._blit_circle(surf, d.x, d.y, d.r, (170, 225, 255), 70 * min(1, f * 2))
                col = (235, 248, 255)
                for a in d.data:
                    ex = d.x + math.cos(a) * d.r * 0.9
                    ey = d.y + math.sin(a) * d.r * 0.9
                    pygame.draw.line(surf, col, (d.x, d.y), (ex, ey), 1)
                    mx, my = _lerp(d.x, ex, 0.6), _lerp(d.y, ey, 0.6)
                    for s in (-0.6, 0.6):
                        pygame.draw.line(surf, col, (mx, my),
                                         (mx + math.cos(a + s) * 6, my + math.sin(a + s) * 6), 1)
                pygame.draw.circle(surf, (210, 240, 255), (int(d.x), int(d.y)), int(d.r), 1)
            elif d.kind == "arrows":
                for a, dd, tilt in d.data:
                    x = d.x + math.cos(a) * dd
                    y = d.y + math.sin(a) * dd
                    pygame.draw.line(surf, (110, 80, 50), (x, y), (x + tilt * 5, y - 7), 2)
                    pygame.draw.line(surf, (235, 235, 240), (x + tilt * 5, y - 7),
                                     (x + tilt * 6, y - 9), 2)

    def draw_particles(self, surf):
        for p in self.parts:
            f = p.life / p.max_life
            k = p.kind
            if k == "smoke" or k == "dust":
                # fade IN quickly, then out (no dark blob on top of a flash)
                a = 150 * f * min(1.0, (1.0 - f) * 5.0 + (0.3 if k == "dust" else 0.0))
                self._blit_circle(surf, p.x, p.y, p.size, p.col, a)
            elif k == "ember":
                col = _mixc(p.col2, p.col, f)
                pygame.draw.circle(surf, col, (int(p.x), int(p.y)), max(1, int(p.size * f + 0.5)))
            elif k == "spark":
                pygame.draw.line(surf, p.col, (p.x, p.y),
                                 (p.x - p.vx * 0.04, p.y - p.vy * 0.04), 2)
            elif k == "debris":
                s = p.size
                c, sn = math.cos(p.rot) * s, math.sin(p.rot) * s
                pts = [(p.x + c, p.y + sn), (p.x - sn, p.y + c),
                       (p.x - c, p.y - sn), (p.x + sn, p.y - c)]
                pygame.draw.polygon(surf, p.col, pts)
            elif k == "snow":
                pygame.draw.circle(surf, p.col, (int(p.x), int(p.y)), max(1, int(p.size)))
            elif k == "shard":
                dx, dy = math.cos(p.rot) * p.size * 2, math.sin(p.rot) * p.size * 2
                pygame.draw.line(surf, p.col, (p.x - dx, p.y - dy), (p.x + dx, p.y + dy), 2)
            elif k == "bubble":
                pygame.draw.circle(surf, p.col, (int(p.x), int(p.y)), max(1, int(p.size)), 1)
            elif k == "ghost":
                a = int(170 * f)
                gx, gy, r = int(p.x + math.sin((1 - f) * 9) * 3), int(p.y), int(p.size)
                g = self._circle(r, (240, 244, 255), a)
                surf.blit(g, (gx - g.get_width() // 2, gy - g.get_height() // 2))
                body = pygame.Surface((r * 2 + 2, r + 3), pygame.SRCALPHA)
                pygame.draw.rect(body, (240, 244, 255, a), (1, 0, r * 2, r))
                for i in range(3):                      # wavy hem
                    pygame.draw.circle(body, (0, 0, 0, 0), (1 + r // 3 + i * (2 * r // 3), r + 1), max(1, r // 3))
                surf.blit(body, (gx - r - 1, gy))
                pygame.draw.circle(surf, p.col, (gx - r // 3, gy - 1), 1)
                pygame.draw.circle(surf, p.col, (gx + r // 3, gy - 1), 1)
            else:
                pygame.draw.circle(surf, p.col, (int(p.x), int(p.y)), max(1, int(p.size)))

    def draw_flash(self, surf):
        if self.flash > 0.01:
            s = pygame.Surface((cfg.ARENA_PX_W, cfg.ARENA_PX_H), pygame.SRCALPHA)
            s.fill((255, 255, 240, int(120 * self.flash)))
            surf.blit(s, (cfg.ARENA_X0, cfg.ARENA_Y0))

    # ------------------------------------------------------------ spells
    def _flight_pos(self, fx):
        """(screen pos in the air, ground pos) of a thrown spell."""
        p = min(1.0, fx.elapsed / max(fx.duration, 1e-6))
        ox, oy = t2p(*fx.origin)
        tx, ty = t2p(fx.x, fx.y)
        gx, gy = _lerp(ox, tx, p), _lerp(oy, ty, p)
        h = FLIGHT_ARC.get(fx.card_key, 40) * 4 * p * (1 - p)
        return (gx, gy - h), (gx, gy)

    def _data(self, fx, maker):
        d = self._fx_data.get(id(fx))
        if d is None:
            if len(self._fx_data) > 200:
                self._fx_data.clear()
            d = self._fx_data[id(fx)] = maker()
        return d

    def draw_spell(self, surf, fx):
        """Draw an engine Effect if it's a spell visual. True = handled."""
        k = fx.kind
        if k == "incoming":
            if fx.origin is not None:
                self._draw_flight(surf, fx)
                return True
            return self._draw_telegraph(surf, fx)
        if k == "blast":
            return self._draw_blast(surf, fx)
        if k == "poison":
            if fx.card_key == "earthquake":
                self._draw_quake(surf, fx)
            else:
                self._draw_poison(surf, fx)
            return True
        if k == "rage":
            self._draw_rage(surf, fx)
            return True
        if k == "graveyard":
            self._draw_graveyard(surf, fx)
            return True
        if k == "tornado":
            self._draw_tornado(surf, fx)
            return True
        if k == "log":
            self._draw_log(surf, fx)
            return True
        return False

    def _target_ring(self, surf, fx, col, prog):
        x, y = t2p(fx.x, fx.y)
        R = int(fx.radius * TS)
        team = TEAM_COL.get(fx.team, (240, 240, 240))
        self._blit_circle(surf, x, y, R, col, 40)
        n = 16
        rot = self.now * 1.5
        for i in range(n):           # dashed, rotating team-coloured ring
            a0 = rot + i * math.tau / n
            a1 = a0 + math.tau / n * 0.55
            pygame.draw.arc(surf, team, (x - R, y - R, 2 * R, 2 * R), a0, a1, 2)
        inner = int(R * (1 - prog)) + 2
        pygame.draw.circle(surf, col, (int(x), int(y)), inner, 2)

    def _draw_flight(self, surf, fx):
        prog = min(1.0, fx.elapsed / max(fx.duration, 1e-6))
        col = {"fireball": (255, 150, 60), "rocket": (240, 90, 60),
               "arrows": (235, 235, 235), "goblin_barrel": (170, 120, 70),
               "snowball": (220, 240, 255)}.get(fx.card_key, (240, 240, 240))
        self._target_ring(surf, fx, col, prog)
        (x, y), (gx, gy) = self._flight_pos(fx)
        # shadow on the ground
        sh = 4 + int(6 * prog)
        self._blit_circle(surf, gx, gy, sh, (0, 0, 0), 60 + 60 * prog)
        # direction of travel on screen
        p2 = min(1.0, prog + 0.02)
        ox, oy = t2p(*fx.origin)
        tx, ty = t2p(fx.x, fx.y)
        h2 = FLIGHT_ARC.get(fx.card_key, 40) * 4 * p2 * (1 - p2)
        nx, ny = _lerp(ox, tx, p2), _lerp(oy, ty, p2) - h2
        ang = math.atan2(ny - y, nx - x) if (nx, ny) != (x, y) else math.atan2(ty - oy, tx - ox)
        ca, sa = math.cos(ang), math.sin(ang)
        k = fx.card_key
        if k == "fireball":
            self._blit_circle(surf, x, y, 13, (255, 120, 30), 80)
            pygame.draw.circle(surf, (255, 150, 50), (int(x), int(y)), 8)
            pygame.draw.circle(surf, (255, 220, 120), (int(x), int(y)), 5)
            pygame.draw.circle(surf, (255, 255, 230), (int(x - ca * 1), int(y - sa * 1)), 2)
        elif k == "rocket":
            L = 16
            tail = (x - ca * L, y - sa * L)
            pygame.draw.line(surf, (190, 50, 45), tail, (x, y), 6)
            pygame.draw.line(surf, (235, 235, 240), (x - ca * 3, y - sa * 3), (x + ca * 3, y + sa * 3), 6)
            for s in (-1, 1):   # fins
                fx_, fy_ = tail[0] + -sa * 5 * s, tail[1] + ca * 5 * s
                pygame.draw.line(surf, (120, 120, 130), tail, (fx_, fy_), 3)
            fl = 7 + 4 * math.sin(self.now * 40)
            pygame.draw.polygon(surf, (255, 200, 80), [
                (tail[0] - sa * 3, tail[1] + ca * 3), (tail[0] + sa * 3, tail[1] - ca * 3),
                (tail[0] - ca * fl, tail[1] - sa * fl)])
        elif k == "arrows":
            r = random.Random(id(fx) & 0xFFFF)
            for i in range(9):
                ox_ = r.uniform(-11, 11)
                oy_ = r.uniform(-8, 8)
                ax, ay = x + ox_, y + oy_
                L = 11
                pygame.draw.line(surf, (120, 86, 52), (ax - ca * L, ay - sa * L), (ax, ay), 2)
                pygame.draw.line(surf, (230, 232, 240), (ax, ay), (ax + ca * 3, ay + sa * 3), 2)
                pygame.draw.line(surf, (245, 245, 245), (ax - ca * L, ay - sa * L),
                                 (ax - ca * (L - 3) - sa * 2, ay - sa * (L - 3) + ca * 2), 1)
        elif k == "goblin_barrel":
            spin = self.now * 10
            w, h = 11, 8
            c, s = math.cos(spin), math.sin(spin)
            pts = [(x + c * dx - s * dy, y + s * dx + c * dy)
                   for dx, dy in ((-w, -h), (w, -h), (w, h), (-w, h))]
            pygame.draw.polygon(surf, (150, 100, 55), pts)
            pygame.draw.polygon(surf, (80, 52, 28), pts, 2)
            for band in (-0.45, 0.45):
                b0 = (x + c * w * band - s * -h, y + s * w * band + c * -h)
                b1 = (x + c * w * band - s * h, y + s * w * band + c * h)
                pygame.draw.line(surf, (90, 90, 100), b0, b1, 2)
            pygame.draw.circle(surf, (110, 200, 80), (int(x - s * 9), int(y + c * -9)), 4)
        elif k == "snowball":
            pygame.draw.circle(surf, (200, 225, 245), (int(x), int(y)), 8)
            pygame.draw.circle(surf, (250, 252, 255), (int(x - 2), int(y - 2)), 6)
        else:
            pygame.draw.circle(surf, col, (int(x), int(y)), 6)

    def _draw_telegraph(self, surf, fx):
        k = fx.card_key
        prog = min(1.0, fx.elapsed / max(fx.duration, 1e-6))
        x, y = t2p(fx.x, fx.y)
        R = fx.radius * TS
        if k == "zap":
            self._target_ring(surf, fx, (150, 220, 255), prog)
            r = random.Random(int(self.now * 30))
            for _ in range(5):
                a = r.uniform(0, math.tau)
                pts = [(x + math.cos(a) * R * t + r.uniform(-4, 4),
                        y + math.sin(a) * R * t + r.uniform(-4, 4)) for t in (0.6, 0.8, 1.0)]
                pygame.draw.lines(surf, (200, 240, 255), False, pts, 1)
            return True
        if k == "lightning":
            self._target_ring(surf, fx, (255, 240, 140), prog)
            for i in range(6):     # storm cloud gathering overhead
                cx = x + math.cos(i * 1.1 + self.now) * R * 0.5
                cy = y - 38 + math.sin(i * 1.7) * 6
                self._blit_circle(surf, cx, cy, 10 + 4 * (i % 3), (60, 60, 75), 120 + 100 * prog)
            return True
        if k == "freeze":
            self._target_ring(surf, fx, (170, 230, 255), prog)
            s = R * 0.5 * prog
            for i in range(6):
                a = i * math.pi / 3
                pygame.draw.line(surf, (230, 248, 255), (x, y),
                                 (x + math.cos(a) * s, y + math.sin(a) * s), 2)
            return True
        if k in ("poison", "earthquake", "rage", "graveyard", "tornado"):
            col = {"poison": (130, 210, 80), "earthquake": (170, 120, 70),
                   "rage": (220, 100, 230), "graveyard": (150, 110, 190),
                   "tornado": (210, 214, 225)}[k]
            self._target_ring(surf, fx, col, prog)
            return True
        if k in ("the_log", "barbarian_barrel"):
            self._target_ring(surf, fx, (190, 140, 80), prog)
            return True
        return False

    def _draw_blast(self, surf, fx):
        k = fx.card_key
        prog = min(1.0, fx.elapsed / max(fx.duration, 1e-6))
        x, y = t2p(fx.x, fx.y)
        R = fx.radius * TS
        if k in ("fireball", "rocket"):
            big = k == "rocket"
            rr = R * (0.4 + 0.8 * prog)
            self._blit_circle(surf, x, y, rr, (255, 120, 30), 170 * (1 - prog))
            self._blit_circle(surf, x, y, rr * 0.65, (255, 200, 80), 200 * (1 - prog))
            if prog < 0.4:
                self._blit_circle(surf, x, y, rr * 0.35, (255, 255, 230), 255 * (1 - prog / 0.4))
            pygame.draw.circle(surf, (255, 230, 170), (int(x), int(y)),
                               int(R * (0.5 + 0.9 * prog)), max(1, int((4 if big else 3) * (1 - prog))))
            return True
        if k == "zap":
            self._blit_circle(surf, x, y, R * (0.6 + 0.4 * prog), (170, 220, 255), 150 * (1 - prog))
            bolts = self._data(fx, lambda: [random.uniform(0, math.tau) for _ in range(7)])
            r = random.Random(int(self.now * 40))
            for a in bolts:
                pts = [(x, y)]
                for t in (0.3, 0.55, 0.8, 1.0):
                    pts.append((x + math.cos(a) * R * t + r.uniform(-5, 5),
                                y + math.sin(a) * R * t + r.uniform(-5, 5)))
                pygame.draw.lines(surf, (120, 200, 255), False, pts, 4)
                pygame.draw.lines(surf, (240, 250, 255), False, pts, 1)
            return True
        if k == "lightning":
            strikes = self._data(fx, lambda: [(random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6))
                                              for _ in range(3)])
            r = random.Random(int(self.now * 30))
            for i, (ox, oy) in enumerate(strikes):
                if prog > 0.25 + i * 0.25:
                    continue
                sx, sy = x + ox * R, y + oy * R
                pts = [(sx + r.uniform(-20, 20), cfg.ARENA_Y0)]
                steps = 7
                for j in range(1, steps + 1):
                    t = j / steps
                    pts.append((_lerp(pts[0][0], sx, t) + r.uniform(-9, 9) * (1 - t),
                                _lerp(cfg.ARENA_Y0, sy, t)))
                pygame.draw.lines(surf, (255, 240, 150), False, pts, 6)
                pygame.draw.lines(surf, (255, 255, 255), False, pts, 2)
                self._blit_circle(surf, sx, sy, 16, (255, 250, 200), 200)
            return True
        if k == "freeze":
            self._blit_circle(surf, x, y, R * (0.5 + 0.6 * prog), (200, 240, 255), 180 * (1 - prog))
            return True
        if k == "snowball":
            pygame.draw.circle(surf, (245, 250, 255), (int(x), int(y)),
                               int(R * (0.3 + 0.8 * prog)), max(1, int(4 * (1 - prog))))
            return True
        if k == "arrows":
            return True            # dust puffs + stuck arrows do the work
        if k == "goblin_barrel":
            pygame.draw.circle(surf, (200, 180, 130), (int(x), int(y)),
                               int(R * (0.4 + 0.8 * prog)), max(1, int(3 * (1 - prog))))
            return True
        if k in ("poison", "earthquake", "rage", "graveyard", "tornado", "the_log",
                 "barbarian_barrel"):
            return True            # the lingering zone draws itself
        return False

    def _draw_poison(self, surf, fx):
        x, y = t2p(fx.x, fx.y)
        R = fx.radius * TS
        f = min(1.0, fx.elapsed / 0.3) * min(1.0, (fx.duration - fx.elapsed) / 0.4)
        self._blit_circle(surf, x, y, R, (70, 130, 40), 70 * f)
        self._blit_circle(surf, x, y, R * 0.7, (110, 170, 50), 50 * f)
        for i in range(10):     # swirling haze blobs
            a = self.now * 0.8 + i * math.tau / 10
            d = R * (0.45 + 0.25 * math.sin(self.now * 1.3 + i))
            self._blit_circle(surf, x + math.cos(a) * d, y + math.sin(a) * d, R * 0.28,
                              (140, 200, 70), 45 * f)
        pygame.draw.circle(surf, (170, 230, 90), (int(x), int(y)), int(R), 2)

    def _draw_quake(self, surf, fx):
        x, y = t2p(fx.x, fx.y)
        R = fx.radius * TS
        f = min(1.0, fx.elapsed / 0.2) * min(1.0, (fx.duration - fx.elapsed) / 0.4)
        self._blit_circle(surf, x, y, R, (120, 85, 50), 60 * f)

        def mk():
            r = random.Random(id(fx) & 0xFFFF)
            cracks = []
            for i in range(7):
                a = i * math.tau / 7 + r.uniform(-0.3, 0.3)
                pts = [(0.0, 0.0)]
                for t in (0.3, 0.55, 0.8, 1.0):
                    aa = a + r.uniform(-0.35, 0.35)
                    pts.append((math.cos(aa) * t, math.sin(aa) * t))
                cracks.append(pts)
            return cracks
        shake = math.sin(self.now * 60) * 1.5
        for pts in self._data(fx, mk):
            sp = [(x + px * R * 0.95 + shake, y + py * R * 0.95) for px, py in pts]
            pygame.draw.lines(surf, (60, 40, 25), False, sp, 3)
            pygame.draw.lines(surf, (200, 150, 90), False, sp, 1)

    def _draw_rage(self, surf, fx):
        x, y = t2p(fx.x, fx.y)
        R = fx.radius * TS
        pulse = 0.5 + 0.5 * math.sin(self.now * 6)
        f = min(1.0, (fx.duration - fx.elapsed) / 0.5)
        self._blit_circle(surf, x, y, R, (180, 60, 200), (50 + 30 * pulse) * f)
        n = 12
        for i in range(n):
            a0 = self.now * 2 + i * math.tau / n
            pygame.draw.arc(surf, (240, 140, 250), (x - R, y - R, 2 * R, 2 * R),
                            a0, a0 + 0.3, 3)
        pygame.draw.circle(surf, (230, 120, 240), (int(x), int(y)),
                           int(R * (0.8 + 0.2 * pulse)), 1)

    def _draw_graveyard(self, surf, fx):
        x, y = t2p(fx.x, fx.y)
        R = fx.radius * TS
        f = min(1.0, fx.elapsed / 0.4) * min(1.0, (fx.duration - fx.elapsed) / 0.6)
        self._blit_circle(surf, x, y, R, (50, 30, 70), 90 * f)

        def mk():
            r = random.Random(id(fx) & 0xFFFF)
            return [(r.uniform(0, math.tau), R * math.sqrt(r.uniform(0.05, 0.9)))
                    for _ in range(6)]
        for a, d in self._data(fx, mk):     # little tombstones
            tx, ty = x + math.cos(a) * d, y + math.sin(a) * d
            rect = pygame.Rect(int(tx) - 4, int(ty) - 6, 8, 9)
            pygame.draw.rect(surf, (150, 146, 160), rect, border_top_left_radius=4,
                             border_top_right_radius=4)
            pygame.draw.rect(surf, (80, 76, 92), rect, 1, border_top_left_radius=4,
                             border_top_right_radius=4)

    def _draw_tornado(self, surf, fx):
        x, y = t2p(fx.x, fx.y)
        R = fx.radius * TS
        self._blit_circle(surf, x, y, R, (190, 196, 210), 45)
        for ring in range(4):
            rr = R * (0.25 + 0.25 * ring)
            for i in range(3):
                a0 = -self.now * (7 - ring) + i * math.tau / 3 + ring
                pygame.draw.arc(surf, (235, 238, 248), (x - rr, y - rr, 2 * rr, 2 * rr),
                                a0, a0 + 1.2, 2)

    def _draw_log(self, surf, fx):
        x, y = t2p(fx.x, fx.y)
        w = fx.radius * TS
        h = 11
        barrel = fx.card_key == "barbarian_barrel"
        body = (150, 100, 55) if barrel else (140, 96, 56)
        rect = pygame.Rect(int(x - w), int(y - h / 2), int(2 * w), h)
        pygame.draw.rect(surf, (50, 34, 20), rect.move(0, 3), border_radius=5)
        pygame.draw.rect(surf, body, rect, border_radius=5)
        pygame.draw.rect(surf, (90, 60, 32), rect, 2, border_radius=5)
        # rolling grain / hoops
        spin = (fx.elapsed * 14) % 1.0
        n = 4 if barrel else 7
        for i in range(n):
            t = (i + spin) / n
            yy = rect.y + 1 + t * (h - 2)
            col = (90, 90, 100) if barrel else (110, 74, 40)
            pygame.draw.line(surf, col, (rect.x + 3, yy), (rect.right - 3, yy), 1)
        for ex in (rect.x + 3, rect.right - 3):     # cut ends with rings
            pygame.draw.ellipse(surf, (196, 150, 96), (ex - 3, rect.y, 6, h))
            pygame.draw.ellipse(surf, (120, 80, 45), (ex - 2, rect.y + 3, 4, h - 6), 1)
