"""
============================================================================
  SPRITE_ART.PY  --  Original procedural card art (no copyrighted assets)
============================================================================

Every card / unit is painted by its own small function below (look for the
`@art("card_key")` lines). The style is chunky and cartoony, inspired by the
look of Clash Royale: bold dark outlines, two-tone cel shading, big heads.

Art is painted on a 3x-sized canvas and smoothly scaled down, so all edges
are anti-aliased. sprites.py saves the results as PNGs in assets/sprites/
and loads them for the game - this file only knows how to DRAW.

Want to tweak a card's look? Find its @art function and change colors or
shapes. Coordinates are on a 128 x 128 grid (0,0 = top-left).
============================================================================
"""

import contextlib
import math
import pygame

BASE = 128   # authored resolution of every sprite
SS = 3       # supersampling factor (painted at 3x, then scaled down)

# ---------------------------------------------------------------- palette
OUT = (38, 30, 44)            # outline colour
WHITE = (255, 255, 255)
SKIN = (255, 206, 162)
SKIN_TAN = (236, 170, 118)
SKIN_PALE = (246, 224, 216)
GOB = (126, 206, 72)
BONE = (242, 240, 226)
STEEL = (200, 209, 226)
DSTEEL = (122, 130, 152)
IRON = (72, 74, 90)
GOLD = (255, 202, 58)
WOOD = (182, 120, 62)
DWOOD = (124, 82, 46)
LEATHER = (150, 96, 56)
BOOT = (96, 64, 44)
BLOND = (255, 214, 92)
RED = (228, 64, 58)
BLUE = (72, 124, 224)
PURPLE = (150, 82, 204)
PINK = (255, 122, 172)
BLACK = (54, 50, 64)
FIRE = (255, 146, 36)
FIRE_Y = (255, 230, 96)
ICE = (172, 228, 255)
ELEC = (110, 214, 255)
ELIXIR = (226, 84, 222)
GRASS = (110, 190, 90)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def dk(c, t=0.28):
    return mix(c, (0, 0, 0), t)


def lt(c, t=0.38):
    return mix(c, (255, 255, 255), t)


# ---------------------------------------------------------------- geometry
def vec(a, d):
    """Vector of length d at angle a (degrees, 0 = right, 90 = up)."""
    r = math.radians(a)
    return (d * math.cos(r), -d * math.sin(r))


def pol(x, y, a, d):
    v = vec(a, d)
    return (x + v[0], y + v[1])


def perp(a, d):
    return vec(a + 90, d)


def add(pt, v, k=1.0):
    return (pt[0] + v[0] * k, pt[1] + v[1] * k)


def arcpts(cx, cy, rx, ry, a0, a1, n=16):
    out = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        out.append((cx + rx * math.cos(a), cy - ry * math.sin(a)))
    return out


def mirror(pts, cx=64):
    return [(2 * cx - x, y) for x, y in pts]


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def ring_on(p, a, b, t, width, col, thick=5.0):
    """A ring/band wrapped around the tube a->b at fraction t of its length."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy) or 1.0
    c = lerp(a, b, t)
    u = (dx / d * thick / 2, dy / d * thick / 2)
    p.band((c[0] - u[0], c[1] - u[1]), (c[0] + u[0], c[1] + u[1]), width, col, w=2)


# ---------------------------------------------------------------- painter
OW = 2.7   # default outline width (in 128-grid units)


class P:
    """A supersampled canvas with a transform stack.

    All public methods take 128-grid coordinates. `at()` lets a drawing
    function be reused at another position / scale (riders, squads...).
    """

    def __init__(self):
        self.surf = pygame.Surface((BASE * SS, BASE * SS), pygame.SRCALPHA)
        self.T = [(0.0, 0.0, 1.0)]

    # --- transform ---------------------------------------------------
    @contextlib.contextmanager
    def at(self, tx, ty, k):
        """Draw the 128-grid scaled by k with its centre placed at (tx, ty)."""
        ox, oy, kk = self.T[-1]
        self.T.append((ox + (tx - 64 * k) * kk, oy + (ty - 64 * k) * kk, k * kk))
        try:
            yield
        finally:
            self.T.pop()

    def X(self, x):
        ox, oy, k = self.T[-1]
        return (ox + x * k) * SS

    def Y(self, y):
        ox, oy, k = self.T[-1]
        return (oy + y * k) * SS

    def L(self, v):
        return v * self.T[-1][2] * SS

    def pt(self, x, y):
        return (self.X(x), self.Y(y))

    # --- raw primitives (no outline) ---------------------------------
    def _circle(self, x, y, r, col):
        pygame.draw.circle(self.surf, col, (round(self.X(x)), round(self.Y(y))),
                           max(1, round(self.L(r))))

    def _ellipse(self, x, y, rx, ry, col):
        X, Y, RX, RY = self.X(x), self.Y(y), self.L(rx), self.L(ry)
        pygame.draw.ellipse(self.surf, col, pygame.Rect(
            round(X - RX), round(Y - RY), max(1, round(2 * RX)), max(1, round(2 * RY))))

    def _poly(self, pts, col):
        if len(pts) >= 3:
            pygame.draw.polygon(self.surf, col, [self.pt(*q) for q in pts])

    def _seg(self, a, b, w, col):
        (x1, y1), (x2, y2) = self.pt(*a), self.pt(*b)
        W = self.L(w) / 2.0
        dx, dy = x2 - x1, y2 - y1
        d = math.hypot(dx, dy)
        if d > 1e-6:
            nx, ny = -dy / d * W, dx / d * W
            pygame.draw.polygon(self.surf, col, [(x1 + nx, y1 + ny), (x2 + nx, y2 + ny),
                                                 (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)])
        r = max(1, round(W))
        pygame.draw.circle(self.surf, col, (round(x1), round(y1)), r)
        pygame.draw.circle(self.surf, col, (round(x2), round(y2)), r)

    # --- outlined, shaded shapes -------------------------------------
    def ball(self, x, y, r, col, ol=OUT, w=OW, shade=True, hl=True):
        if ol:
            self._circle(x, y, r + w, ol)
        if shade:
            self._circle(x, y, r, dk(col, 0.2))
            self._circle(x - r * 0.09, y - r * 0.09, r * 0.86, col)
        else:
            self._circle(x, y, r, col)
        if hl:
            self._ellipse(x - r * 0.36, y - r * 0.42, r * 0.28, r * 0.17, lt(col, 0.5))

    def oval(self, x, y, rx, ry, col, ol=OUT, w=OW, shade=True, hl=False):
        if ol:
            self._ellipse(x, y, rx + w, ry + w, ol)
        if shade:
            self._ellipse(x, y, rx, ry, dk(col, 0.2))
            self._ellipse(x - rx * 0.08, y - ry * 0.08, rx * 0.86, ry * 0.86, col)
        else:
            self._ellipse(x, y, rx, ry, col)
        if hl:
            self._ellipse(x - rx * 0.36, y - ry * 0.45, rx * 0.3, ry * 0.18, lt(col, 0.5))

    def shape(self, pts, col, ol=OUT, w=OW):
        if ol:
            n = len(pts)
            for i in range(n):
                self._seg(pts[i], pts[(i + 1) % n], w * 2, ol)
        self._poly(pts, col)

    def stroke(self, pts, width, col, ol=OUT, w=OW, closed=False):
        segs = list(zip(pts, pts[1:]))
        if closed:
            segs.append((pts[-1], pts[0]))
        if ol:
            for a, b in segs:
                self._seg(a, b, width + 2 * w, ol)
        for a, b in segs:
            self._seg(a, b, width, col)

    def line(self, a, b, width, col, ol=OUT, w=OW):
        self.stroke([a, b], width, col, ol, w)

    def band(self, a, b, width, col, ol=OUT, w=OW):
        """Straight strip with SQUARE ends (rings around barrels, straps)."""
        (ax, ay), (bx, by) = a, b
        dx, dy = bx - ax, by - ay
        d = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / d * width / 2, dx / d * width / 2
        self.shape([(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny),
                    (ax - nx, ay - ny)], col, ol, w)

    # --- alpha effects (painted on a temporary layer) -----------------
    @contextlib.contextmanager
    def layer(self, alpha=255):
        old = self.surf
        tmp = pygame.Surface(old.get_size(), pygame.SRCALPHA)
        self.surf = tmp
        try:
            yield
        finally:
            self.surf = old
            if alpha < 255:
                tmp.set_alpha(alpha)
            old.blit(tmp, (0, 0))

    def shadow(self, x=64, y=117, rx=30, ry=7.5, a=70):
        with self.layer():
            self._ellipse(x, y, rx, ry, (0, 0, 0, a))

    def glow(self, x, y, r, col, a=120, steps=6):
        with self.layer():
            for i in range(steps):
                t = i / steps
                self._circle(x, y, r * (1 - t * 0.75),
                             (col[0], col[1], col[2], int(a * (0.25 + 0.75 * t))))

    def spark(self, x, y, r, col=FIRE_Y, n=4):
        pts = []
        for i in range(n * 2):
            rr = r if i % 2 == 0 else r * 0.38
            pts.append(pol(x, y, 90 + i * 180 / n, rr))
        self._poly(pts, col)

    def bolt(self, pts, col=FIRE_Y, width=3.0, glowcol=None):
        if glowcol:
            with self.layer(150):
                for a, b in zip(pts, pts[1:]):
                    self._seg(a, b, width + 6, glowcol)
        for a, b in zip(pts, pts[1:]):
            self._seg(a, b, width + 2.4, dk(col, 0.45))
        for a, b in zip(pts, pts[1:]):
            self._seg(a, b, width, col)


# ---------------------------------------------------------------- registry
ART = {}


def art(*keys):
    def deco(fn):
        for k in keys:
            ART[k] = fn
        return fn
    return deco


# ===========================================================================
#  FIGURE PARTS
# ===========================================================================
BUILDS = {
    "normal": dict(hx=64, hy=45, hr=24, tx=64, ty=89, trx=19, try_=17,
                   lx=(56, 72), ly=105, lrx=7, lry=8, ax=(43, 85), ay=87,
                   arx=7, hand=((41, 100), (87, 100)), handr=6.5, gy=117),
    "slim":   dict(hx=64, hy=45, hr=24, tx=64, ty=89, trx=16, try_=17,
                   lx=(58, 70), ly=105, lrx=6, lry=8, ax=(46, 82), ay=87,
                   arx=6, hand=((44, 100), (84, 100)), handr=6, gy=117),
    "small":  dict(hx=64, hy=50, hr=27, tx=64, ty=93, trx=15, try_=13,
                   lx=(58, 70), ly=106, lrx=6, lry=7, ax=(48, 80), ay=92,
                   arx=5.5, hand=((46, 102), (82, 102)), handr=5.5, gy=116),
    "big":    dict(hx=64, hy=33, hr=19, tx=64, ty=79, trx=31, try_=26,
                   lx=(50, 78), ly=106, lrx=11, lry=10, ax=(31, 97), ay=74,
                   arx=11, hand=((25, 98), (103, 98)), handr=11, gy=118),
    "bulky":  dict(hx=64, hy=40, hr=22, tx=64, ty=85, trx=25, try_=21,
                   lx=(54, 74), ly=106, lrx=8.5, lry=9, ax=(38, 90), ay=84,
                   arx=8.5, hand=((33, 100), (95, 100)), handr=8, gy=118),
}


class Fig:
    def __init__(self, kind="normal"):
        self.__dict__.update(BUILDS[kind])
        self.kind = kind


def legs(p, f, col, boot=BOOT):
    for x in f.lx:
        p.oval(x, f.ly, f.lrx, f.lry, col)
    if boot:
        for x in f.lx:
            p.oval(x, f.ly + f.lry - 1.5, f.lrx + 1.5, 4.5, boot)


def torso(p, f, col, hl=True):
    p.oval(f.tx, f.ty, f.trx, f.try_, col, hl=hl)


def robe(p, f, col, trim=None, flare=1.3):
    top = f.ty - f.try_ * 0.55
    bot = f.gy - 4
    pts = [(f.tx - f.trx * 0.85, top), (f.tx + f.trx * 0.85, top),
           (f.tx + f.trx * flare, bot), (f.tx - f.trx * flare, bot)]
    p.shape(pts, col)
    p._poly([(f.tx + f.trx * 0.2, top + 2), (f.tx + f.trx * 0.8, top + 2),
             (f.tx + f.trx * flare - 2, bot - 2), (f.tx + f.trx * 0.45, bot - 2)],
            dk(col, 0.18))
    if trim:
        p.line((f.tx - f.trx * flare + 1, bot - 2), (f.tx + f.trx * flare - 1, bot - 2),
               4.5, trim)


def belt(p, f, col=LEATHER, buckle=GOLD, dy=0.32):
    y = f.ty + f.try_ * dy
    p.line((f.tx - f.trx + 3, y), (f.tx + f.trx - 3, y), 5, col)
    if buckle:
        p.oval(f.tx, y, 4, 3.4, buckle, w=1.8)


def arm(p, f, i, col, hand=SKIN, to=None):
    sx, sy = f.ax[i], f.ay - 7
    hx, hy = to if to else f.hand[i]
    p.line((sx, sy), (hx, hy), f.arx * 1.9, col)
    if hand:
        p.ball(hx, hy, f.handr, hand, hl=False)
    return hx, hy


def head(p, f, skin=SKIN):
    p.ball(f.hx, f.hy, f.hr, skin)


def face(p, f, eyes="dot", mouth="smile", brows=None, eyecol=None,
         blush=False, dy=0.0):
    hx, hy, hr = f.hx, f.hy + dy, f.hr
    ey = hy + hr * 0.1
    for s in (-1, 1):
        ex = hx + s * hr * 0.37
        if eyes == "dot":
            p.oval(ex, ey, hr * 0.11, hr * 0.15, eyecol or OUT, ol=None, shade=False)
            p._circle(ex - hr * 0.03, ey - hr * 0.06, hr * 0.045, WHITE)
        elif eyes == "big":
            p.oval(ex, ey, hr * 0.17, hr * 0.21, WHITE, w=1.4, shade=False)
            p.oval(ex + s * hr * 0.03, ey + hr * 0.03, hr * 0.1, hr * 0.13,
                   eyecol or OUT, ol=None, shade=False)
            p._circle(ex - hr * 0.02, ey - hr * 0.03, hr * 0.045, WHITE)
        elif eyes == "glow":
            p.oval(ex, ey, hr * 0.17, hr * 0.1, eyecol or ELEC, w=1.6, shade=False)
            p._ellipse(ex, ey, hr * 0.08, hr * 0.05, WHITE)
        elif eyes == "socket":
            p.oval(ex, ey, hr * 0.19, hr * 0.21, (46, 38, 52), ol=None, shade=False)
            if eyecol:
                p._circle(ex, ey, hr * 0.085, eyecol)
        elif eyes == "closed":
            p.stroke(arcpts(ex, ey + hr * 0.06, hr * 0.13, hr * 0.08, 20, 160, 6),
                     hr * 0.06, OUT, ol=None)
        elif eyes == "slit":
            p.line((ex - hr * 0.13, ey), (ex + hr * 0.13, ey), hr * 0.07, OUT, ol=None)
    if brows == "angry":
        for s in (-1, 1):
            ex = hx + s * hr * 0.37
            p.line((ex - s * hr * 0.21, ey - hr * 0.37), (ex + s * hr * 0.13, ey - hr * 0.21),
                   hr * 0.11, OUT, ol=None)
    elif brows == "flat":
        for s in (-1, 1):
            ex = hx + s * hr * 0.37
            p.line((ex - hr * 0.16, ey - hr * 0.28), (ex + hr * 0.16, ey - hr * 0.28),
                   hr * 0.1, OUT, ol=None)
    if blush:
        with p.layer(110):
            for s in (-1, 1):
                p._ellipse(hx + s * hr * 0.56, hy + hr * 0.36, hr * 0.15, hr * 0.08,
                           (255, 110, 120))
    my = hy + hr * 0.5
    if mouth == "smile":
        p.stroke(arcpts(hx, my - hr * 0.14, hr * 0.22, hr * 0.15, 205, 335, 8),
                 hr * 0.07, OUT, ol=None)
    elif mouth == "grin":
        pts = [(hx - hr * 0.32, my - hr * 0.08), (hx + hr * 0.32, my - hr * 0.08)]
        pts += arcpts(hx, my - hr * 0.08, hr * 0.32, hr * 0.24, 0, -180, 10)
        p.shape(pts, WHITE, w=1.8)
        p.line((hx, my - hr * 0.06), (hx, my + hr * 0.12), 1.2, (150, 150, 160), ol=None)
    elif mouth == "open":
        p.oval(hx, my, hr * 0.16, hr * 0.13, (130, 34, 46), w=1.8, shade=False)
    elif mouth == "flat":
        p.line((hx - hr * 0.17, my), (hx + hr * 0.17, my), hr * 0.07, OUT, ol=None)
    elif mouth == "frown":
        p.stroke(arcpts(hx, my + hr * 0.08, hr * 0.18, hr * 0.1, 25, 155, 8),
                 hr * 0.07, OUT, ol=None)


def cap_pts(f, depth=0.42, extra=1.5, bangs=0, bang_len=0.2):
    """Polygon covering the top of the head (hair, hats, hoods, helmets)."""
    R = f.hr + extra
    yb = f.hy - f.hr + depth * 2 * f.hr
    s = max(-0.97, min(0.97, (f.hy - yb) / R))
    a = math.degrees(math.asin(s))
    top = arcpts(f.hx, f.hy, R, R, a, 180 - a, 18)
    xl, xr = top[-1][0], top[0][0]
    bottom = []
    if bangs:
        n = bangs * 2
        for i in range(1, n):
            x = xl + (xr - xl) * i / n
            y = yb + (f.hr * bang_len if i % 2 else 0)
            bottom.append((x, y))
    return top + bottom


def hair_cap(p, f, col, depth=0.42, extra=1.5, bangs=0, bang_len=0.2):
    p.shape(cap_pts(f, depth, extra, bangs, bang_len), col)


def hair_back(p, f, col, length=1.15, width=1.08, dy=0.35):
    p.oval(f.hx, f.hy + f.hr * dy, f.hr * width, f.hr * length, col)


def hood_back(p, f, col, extra=5):
    p.ball(f.hx, f.hy + 1, f.hr + extra, col, hl=False)


def hood_front(p, f, col, extra=5, depth=0.32):
    p.shape(cap_pts(f, depth, extra), col)


def helmet(p, f, col, depth=0.5, nose=True, band=None, extra=2.5):
    p.shape(cap_pts(f, depth, extra), col)
    yb = f.hy - f.hr + depth * 2 * f.hr
    p._ellipse(f.hx - f.hr * 0.38, f.hy - f.hr * 0.62, f.hr * 0.22, f.hr * 0.12,
               lt(col, 0.5))
    if band:
        p.line((f.hx - f.hr - extra + 1.5, yb - 1), (f.hx + f.hr + extra - 1.5, yb - 1),
               4.5, band)
    if nose:
        p.shape([(f.hx - 2.6, yb - 2), (f.hx + 2.6, yb - 2),
                 (f.hx + 2.2, yb + f.hr * 0.42), (f.hx - 2.2, yb + f.hr * 0.42)],
                band or col, w=2)


def horns(p, f, col=(250, 244, 222), size=1.0, rise=1.0):
    for s in (-1, 1):
        hx, hy, hr = f.hx, f.hy, f.hr
        pts = [(hx + s * hr * 0.62, hy - hr * 0.78),
               (hx + s * hr * 1.12, hy - hr * (0.75 + 0.1 * rise)),
               (hx + s * hr * 1.45 * size, hy - hr * 1.35 * rise),
               (hx + s * hr * 1.5 * size, hy - hr * 0.55),
               (hx + s * hr * 1.0, hy - hr * 0.22)]
        p.shape(pts, col, w=2.3)


def crown(p, f, col=GOLD, w=0.62, h=0.55, dy=0.0, gem=RED):
    by = f.hy - f.hr * 0.72 + dy
    x0, x1 = f.hx - f.hr * w, f.hx + f.hr * w
    hh = f.hr * h
    pts = [(x0, by), (x0 - 1, by - hh), (x0 + (x1 - x0) * 0.25, by - hh * 0.45),
           (f.hx, by - hh * 1.2), (x0 + (x1 - x0) * 0.75, by - hh * 0.45),
           (x1 + 1, by - hh), (x1, by)]
    p.shape(pts, col, w=2.2)
    p._ellipse(f.hx - f.hr * 0.2, by - hh * 0.55, f.hr * 0.1, f.hr * 0.06, lt(col, 0.6))
    if gem:
        p.ball(f.hx, by - hh * 0.3, f.hr * 0.11, gem, w=1.4, hl=False)


def mustache(p, f, col, size=1.0, droop=1.0):
    hx, hy, hr = f.hx, f.hy, f.hr * size
    left = [(hx, hy + hr * 0.28), (hx - hr * 0.2, hy + hr * 0.24),
            (hx - hr * 0.48, hy + hr * 0.32), (hx - hr * 0.68, hy + hr * (0.42 + 0.22 * droop)),
            (hx - hr * 0.44, hy + hr * 0.5), (hx - hr * 0.14, hy + hr * 0.48),
            (hx, hy + hr * 0.42)]
    p.shape(left, col, w=2.2)
    p.shape(mirror(left, hx), col, w=2.2)


def beard(p, f, col, length=1.0, width=0.82):
    hx, hy, hr = f.hx, f.hy, f.hr
    pts = arcpts(hx, hy + hr * 0.12, hr * width, hr * 0.32, 195, 345, 8)
    pts = [pts[-1]] + [(hx + hr * width * 0.95, hy + hr * 0.55),
                       (hx + hr * 0.45, hy + hr * (0.9 + 0.45 * length)),
                       (hx, hy + hr * (1.0 + 0.55 * length)),
                       (hx - hr * 0.45, hy + hr * (0.9 + 0.45 * length)),
                       (hx - hr * width * 0.95, hy + hr * 0.55)] + [pts[0]]
    p.shape(pts, col, w=2.3)
    p._ellipse(hx - hr * 0.3, hy + hr * 0.75, hr * 0.14, hr * 0.08, lt(col, 0.45))


def goblin_ears(p, f, skin=GOB, length=1.0):
    for s in (-1, 1):
        hx, hy, hr = f.hx, f.hy, f.hr
        pts = [(hx + s * hr * 0.7, hy - hr * 0.25), (hx + s * hr * (1.55 * length), hy - hr * 0.55),
               (hx + s * hr * 0.78, hy + hr * 0.3)]
        p.shape(pts, skin, w=2.3)
        p._poly([(hx + s * hr * 0.82, hy - hr * 0.12), (hx + s * hr * (1.3 * length), hy - hr * 0.42),
                 (hx + s * hr * 0.86, hy + hr * 0.14)], dk(skin, 0.25))


def nose(p, f, col=None, size=1.0):
    p.oval(f.hx, f.hy + f.hr * 0.3, f.hr * 0.13 * size, f.hr * 0.1 * size,
           col or dk(SKIN, 0.12), w=1.4, shade=False)


def skull(p, f, eyecol=None, jaw=True):
    hx, hy, hr = f.hx, f.hy, f.hr
    if jaw:
        p.oval(hx, hy + hr * 0.62, hr * 0.5, hr * 0.3, BONE, w=2.3)
    p.ball(hx, hy, hr, BONE)
    face(p, f, "socket", None, eyecol=eyecol)
    p._poly([(hx, hy + hr * 0.24), (hx - hr * 0.09, hy + hr * 0.42),
             (hx + hr * 0.09, hy + hr * 0.42)], (60, 50, 66))
    if jaw:
        for i in range(-2, 3):
            x = hx + i * hr * 0.13
            p.line((x, hy + hr * 0.6), (x, hy + hr * 0.8), 1.4, (150, 146, 136), ol=None)


def skel_body(p, f, arm_to=None, arms_on=True):
    for x in f.lx:
        p.line((x, f.ly - 9), (x, f.ly + 5), 4.4, BONE)
        p.oval(x + (x - 64) * 0.2, f.ly + 7, 5.2, 3.2, BONE, w=2)
    p.oval(f.tx, f.ty + f.try_ * 0.7, f.trx * 0.7, 4.5, BONE, w=2.2)
    p.line((f.tx, f.ty - f.try_ - 2), (f.tx, f.ty + f.try_ * 0.6), 4.2, BONE)
    for i in range(3):
        y = f.ty - f.try_ * 0.62 + i * 5.6
        w = f.trx * (1.0 - i * 0.14)
        p.stroke(arcpts(f.tx, y + 4, w, 5.5, 165, 15, 8), 3.4, BONE, w=2.2)


def bone_arm(p, f, i, to=None):
    sx, sy = f.ax[i], f.ay - 6
    hx, hy = to if to else f.hand[i]
    p.line((sx, sy), (hx, hy), 4.0, BONE, w=2.2)
    p.ball(hx, hy, f.handr * 0.85, BONE, hl=False, w=2.2)
    return hx, hy


# ===========================================================================
#  WEAPONS & PROPS
# ===========================================================================
def sword(p, x, y, a=70, L=46, blade=STEEL, guard=GOLD, w=6.5, grip=DWOOD):
    base = pol(x, y, a, 6)
    pv = perp(a, w / 2)
    p.line(pol(x, y, a, -8), pol(x, y, a, 4), 4.2, grip)
    p.ball(*pol(x, y, a, -10), 3.3, guard, hl=False, w=2)
    tip = pol(x, y, a, L)
    near = pol(x, y, a, L - 8)
    p.shape([add(base, pv), add(near, pv), tip, add(near, pv, -1), add(base, pv, -1)], blade)
    p.line(pol(x, y, a, 10), pol(x, y, a, L - 10), max(1.2, w * 0.22), lt(blade, 0.55), ol=None)
    g = perp(a, w * 1.25)
    p.line(add(base, g, -1), add(base, g), 4.6, guard)


def axe(p, x, y, a=75, L=46, head=STEEL, double=False, size=1.0, shaft=WOOD):
    p.line(pol(x, y, a, -12), pol(x, y, a, L + 3), 4.6, shaft)
    hc = pol(x, y, a, L - 7 * size)
    sides = (1, -1) if double else (1,)
    for s in sides:
        def q(along, side):
            return add(add(hc, vec(a, along * size)), perp(a, side * s * size))
        pts = [q(-8, 2), q(-15, 13), q(-6, 20), q(6, 20), q(15, 13), q(8, 2)]
        p.shape(pts, head)
        p._poly([q(-10, 13), q(-5, 18), q(5, 18), q(10, 13)], lt(head, 0.4))
    p.ball(*pol(x, y, a, L + 3), 3, shaft, hl=False, w=2)


def bow(p, x, y, h=46, col=WOOD, face_dir=-1, arrow=True, arrow_col=STEEL,
        string=(235, 235, 235), bend=11):
    pts = []
    for i in range(13):
        t = -1 + 2 * i / 12
        pts.append((x + face_dir * bend * (1 - t * t), y + t * h / 2))
    p.line(pts[0], pts[-1], 1.4, string, ol=None)
    p.stroke(pts, 4.6, col)
    if arrow:
        p.line((x - face_dir * 6, y), (x + face_dir * 22, y), 2.2, (230, 220, 200), w=1.6)
        tip = (x + face_dir * 22, y)
        p.shape([add(tip, (face_dir * 7, 0)), add(tip, (0, -3.8)), add(tip, (0, 3.8))],
                arrow_col, w=1.6)


def musket(p, x, y, a=42, L=54, barrel=IRON, stock=WOOD):
    p.line(pol(x, y, a, -18), pol(x, y, a, -2), 8, stock)
    p.line(pol(x, y, a, -2), pol(x, y, a, L), 4.6, barrel)
    p.ball(*pol(x, y, a, L), 2.8, barrel, hl=False, w=2)
    p.line(pol(x, y, a, 6), pol(x, y, a, 14), 6, GOLD, w=2)


def spear(p, x, y, a=82, L=56, tip=STEEL, shaft=WOOD, w=3.6):
    p.line(pol(x, y, a, -18), pol(x, y, a, L), w, shaft)
    c = pol(x, y, a, L)
    pv = perp(a, 5.2)
    p.shape([add(c, pv), pol(x, y, a, L + 15), add(c, pv, -1)], tip, w=2.2)


def staff(p, x, y, top_y, kind="orb", col=FIRE, shaft=DWOOD):
    p.line((x, y + 16), (x, top_y), 4.4, shaft)
    if kind == "orb":
        p.glow(x, top_y - 7, 16, col, 140)
        p.ball(x, top_y - 7, 7.5, col)
    elif kind == "skull":
        p.glow(x, top_y - 8, 16, (120, 255, 120), 120)
        p.ball(x, top_y - 8, 8.5, BONE, w=2.2)
        for s in (-1, 1):
            p._circle(x + s * 3.2, top_y - 8, 2.1, (60, 200, 90))
    elif kind == "crystal":
        p.glow(x, top_y - 9, 16, col, 140)
        p.shape([(x, top_y - 20), (x + 7, top_y - 9), (x, top_y + 1), (x - 7, top_y - 9)], col)
        p._poly([(x, top_y - 17), (x + 3, top_y - 9), (x, top_y - 3)], lt(col, 0.6))


def hammer(p, x, y, a=80, L=40, head=IRON, size=1.0, shaft=WOOD):
    p.line(pol(x, y, a, -10), pol(x, y, a, L), 4.6, shaft)
    c = pol(x, y, a, L)
    v = vec(a, 7 * size)
    pv = perp(a, 13 * size)
    p.shape([add(add(c, pv), v), add(add(c, pv), v, -1), add(add(c, pv, -1), v, -1),
             add(add(c, pv, -1), v)], head)
    p.line(add(add(c, pv, 0.75), v, 0.55), add(add(c, pv, -0.75), v, 0.55), 1.6,
           lt(head, 0.5), ol=None)


def dagger(p, x, y, a=60, L=24, blade=STEEL):
    sword(p, x, y, a, L, blade=blade, guard=DSTEEL, w=5)


def bomb(p, x, y, r=12, lit=True):
    p.ball(x, y, r, (58, 56, 72))
    fx, fy = x + r * 0.45, y - r * 0.9
    p.oval(fx - r * 0.12, fy + r * 0.05, r * 0.28, r * 0.18, DSTEEL, w=1.8, shade=False)
    if lit:
        end = (x + r * 0.75, y - r * 1.35)
        p.line((fx, fy), end, 2.4, (210, 180, 130), w=1.8)
        p.glow(*end, r * 0.7, FIRE, 150)
        p.spark(*end, r * 0.45, FIRE_Y, 4)


def shield(p, x, y, r, col, rim=STEEL, boss=STEEL, emblem=None):
    p.ball(x, y, r, col)
    p._circle(x, y, r * 0.78, dk(col, 0.12))
    p._circle(x - r * 0.06, y - r * 0.06, r * 0.7, col)
    p.stroke(arcpts(x, y, r * 0.88, r * 0.88, 0, 360, 24), r * 0.2, rim, ol=None)
    if emblem:
        emblem(x, y, r)
    p.ball(x, y, r * 0.24, boss, w=1.8)


def mace(p, x, y, a=75, L=34, head=IRON, spikes=STEEL, size=1.0):
    p.line(pol(x, y, a, -10), pol(x, y, a, L), 4.4, DWOOD)
    c = pol(x, y, a, L + 8 * size)
    for i in range(8):
        aa = i * 45
        p.shape([pol(*c, aa - 14, 9 * size), pol(*c, aa, 15 * size), pol(*c, aa + 14, 9 * size)],
                spikes, w=1.8)
    p.ball(*c, 9.5 * size, head)


def pickaxe(p, x, y, a=70, L=40, head=DSTEEL):
    p.line(pol(x, y, a, -10), pol(x, y, a, L), 4.4, WOOD)
    c = pol(x, y, a, L)
    p.stroke([add(c, perp(a, -17)), add(add(c, perp(a, -6)), vec(a, 4)),
              add(add(c, perp(a, 6)), vec(a, 4)), add(c, perp(a, 17))], 5, head)


def shovel(p, x, y, a=78, L=42):
    p.line(pol(x, y, a, -12), pol(x, y, a, L), 4.2, WOOD)
    c = pol(x, y, a, L + 6)
    pv = perp(a, 8)
    p.shape([add(pol(*c, a, -7), pv), add(pol(*c, a, -7), pv, -1),
             add(pol(*c, a, 6), perp(a, -6)), pol(*c, a, 13), add(pol(*c, a, 6), perp(a, 6))],
            DSTEEL)


def crossbow(p, x, y, col=DWOOD, limb=IRON, bolt=GOLD):
    p.line((x - 4, y + 6), (x + 22, y - 6), 6.5, col)
    c = (x + 15, y - 3)
    p.stroke(arcpts(c[0] + 6, c[1] + 3, 7, 18, 120, 240, 8), 3.6, limb)
    p.line((x - 2, y + 5), (x + 30, y - 9), 2.2, bolt, w=1.6)


def wing(p, x, y, s, col, size=1.0, membrane=None, spread=1.0):
    """Bat/dragon wing anchored at (x, y); s = -1 left, +1 right."""
    k = size
    pts = [(x, y - 4 * k), (x + s * 20 * k * spread, y - 22 * k),
           (x + s * 34 * k * spread, y - 18 * k), (x + s * 30 * k * spread, y - 6 * k),
           (x + s * 26 * k * spread, y + 2 * k), (x + s * 18 * k * spread, y - 1 * k),
           (x + s * 12 * k * spread, y + 8 * k), (x, y + 6 * k)]
    p.shape(pts, membrane or col)
    p.stroke([(x, y - 3 * k), (x + s * 20 * k * spread, y - 22 * k),
              (x + s * 34 * k * spread, y - 18 * k)], 3.2 * k, col, ol=None)


def plinth(p, col=(170, 166, 158), y=110, rx=42, ry=12):
    p.shadow(64, y + 7, rx + 4, ry * 0.7, 70)
    p.oval(64, y, rx, ry, col)
    p._ellipse(64, y - 2, rx * 0.86, ry * 0.62, lt(col, 0.18))


# ===========================================================================
#  SMALL / SWARM UNITS
# ===========================================================================
@art("skeleton", "skeletons", "skeleton_army")
def _skeleton(p):
    f = Fig("small")
    p.shadow(rx=24)
    skel_body(p, f)
    bone_arm(p, f, 0)
    skull(p, f)
    sword(p, f.hand[1][0], f.hand[1][1], a=70, L=30, w=5, guard=DSTEEL)
    bone_arm(p, f, 1)


@art("goblin", "goblins")
def _goblin(p):
    f = Fig("small")
    p.shadow(rx=24)
    legs(p, f, (110, 76, 46), boot=(80, 56, 36))
    torso(p, f, LEATHER)
    belt(p, f, (100, 64, 38), DSTEEL)
    arm(p, f, 0, GOB, GOB)
    goblin_ears(p, f)
    head(p, f, GOB)
    face(p, f, "dot", "grin", brows="angry")
    nose(p, f, dk(GOB, 0.15), 1.4)
    p.shape(cap_pts(f, 0.3, 1.5), (176, 98, 52))          # little leather cap
    dagger(p, f.hand[1][0], f.hand[1][1], a=62, L=24)
    arm(p, f, 1, GOB, GOB)


@art("spear_goblin", "spear_goblins")
def _spear_goblin(p):
    f = Fig("small")
    p.shadow(rx=24)
    spear(p, f.hand[1][0], f.hand[1][1], a=86, L=62)
    legs(p, f, (110, 76, 46), boot=(80, 56, 36))
    torso(p, f, (196, 160, 96))
    belt(p, f, (120, 78, 42), None)
    arm(p, f, 0, GOB, GOB)
    goblin_ears(p, f)
    head(p, f, GOB)
    face(p, f, "dot", "smile")
    nose(p, f, dk(GOB, 0.15), 1.4)
    hood_front(p, f, (120, 160, 70), extra=2, depth=0.36)      # leafy hood
    for s in (-0.5, 0, 0.5):
        p.shape([(64 + s * 30 - 5, f.hy - f.hr - 1), (64 + s * 30, f.hy - f.hr - 12),
                 (64 + s * 30 + 5, f.hy - f.hr - 1)], (100, 150, 60), w=1.8)
    arm(p, f, 1, GOB, GOB)


@art("bat", "bats")
def _bat(p):
    p.shadow(64, 118, 18, 5, 50)
    cx, cy = 64, 62
    for s in (-1, 1):
        wing(p, cx + s * 10, cy, s, (110, 70, 140), 1.25, (150, 110, 190))
    for s in (-1, 1):
        p.shape([(cx + s * 6, cy - 14), (cx + s * 14, cy - 30), (cx + s * 16, cy - 10)],
                (130, 90, 170), w=2.2)
    p.ball(cx, cy, 17, (130, 90, 170))
    for s in (-1, 1):
        p.oval(cx + s * 7, cy - 2, 5.5, 6.5, WHITE, w=1.6, shade=False)
        p._ellipse(cx + s * 7 + s, cy - 1, 2.8, 3.6, (220, 40, 70))
    p.shape([(cx - 6, cy + 9), (cx - 3, cy + 15), (cx, cy + 9)], WHITE, w=1.4)
    p.shape([(cx + 6, cy + 9), (cx + 3, cy + 15), (cx, cy + 9)], WHITE, w=1.4)


def _spirit(p, col, kind):
    p.shadow(64, 116, 20, 5.5, 60)
    cx, cy = 64, 74
    if kind == "fire":
        p.glow(cx, cy - 6, 40, FIRE, 110)
        pts = [(cx - 22, cy + 8), (cx - 26, cy - 10), (cx - 16, cy - 4), (cx - 18, cy - 28),
               (cx - 6, cy - 14), (cx, cy - 44), (cx + 8, cy - 16), (cx + 18, cy - 30),
               (cx + 18, cy - 6), (cx + 27, cy - 12), (cx + 22, cy + 8)]
        p.shape(pts, col)
        p._poly([(cx - 14, cy + 6), (cx - 10, cy - 10), (cx, cy - 28), (cx + 9, cy - 10),
                 (cx + 14, cy + 6)], FIRE_Y)
    elif kind == "ice":
        p.glow(cx, cy - 6, 40, ICE, 110)
        for i, a in enumerate(range(40, 150, 22)):
            ln = 34 if i % 2 == 0 else 26
            p.shape([pol(cx, cy, a - 9, 16), pol(cx, cy, a, ln), pol(cx, cy, a + 9, 16)],
                    lt(ICE, 0.35), w=2.2)
    elif kind == "elec":
        p.glow(cx, cy - 6, 42, ELEC, 130)
        for a in (40, 75, 105, 140):
            q = pol(cx, cy, a, 18)
            p.bolt([q, pol(*q, a + 25, 8), pol(*q, a - 15, 18)], FIRE_Y, 2.6)
    p.ball(cx, cy + 2, 22, col)
    f = Fig("small")
    f.hx, f.hy, f.hr = cx, cy + 2, 22
    face(p, f, "big", "smile", blush=True, eyecol=(40, 40, 70))


@art("fire_spirit")
def _fire_spirit(p):
    _spirit(p, (255, 160, 50), "fire")


@art("ice_spirit")
def _ice_spirit(p):
    _spirit(p, (196, 236, 255), "ice")


@art("electro_spirit")
def _electro_spirit(p):
    _spirit(p, (110, 196, 255), "elec")


@art("wall_breakers")
def _wall_breaker(p):
    f = Fig("small")
    p.shadow(rx=26)
    skel_body(p, f)
    skull(p, f)
    hair_cap(p, f, RED, depth=0.3, extra=1.0)         # red bandana
    p.shape([(f.hx + f.hr * 0.75, f.hy - f.hr * 0.5), (f.hx + f.hr * 1.35, f.hy - f.hr * 0.25),
             (f.hx + f.hr * 1.2, f.hy - f.hr * 0.05)], RED, w=2)
    # big barrel-bomb hugged in front
    p.oval(64, 98, 19, 14, (66, 62, 78))
    for y in (90, 106):
        p.line((47, y), (81, y), 2.6, DSTEEL, ol=None)
    p.line((76, 86), (86, 78), 2.4, (210, 180, 130), w=1.8)
    p.glow(86, 78, 9, FIRE, 160)
    p.spark(86, 78, 6, FIRE_Y)
    bone_arm(p, f, 0, to=(48, 96))
    bone_arm(p, f, 1, to=(80, 96))


@art("guards")
def _guard(p):
    f = Fig("small")
    p.shadow(rx=26)
    spear(p, f.hand[1][0], f.hand[1][1], a=84, L=60)
    skel_body(p, f)
    skull(p, f)
    helmet(p, f, (184, 150, 72), depth=0.45, nose=True, band=(130, 100, 44))
    p.shape([(f.hx - 4, f.hy - f.hr - 2), (f.hx - 2, f.hy - f.hr - 16), (f.hx + 14, f.hy - f.hr - 12),
             (f.hx + 6, f.hy - f.hr + 2)], RED, w=2.2)                     # crest
    bone_arm(p, f, 1)
    bone_arm(p, f, 0, to=(44, 98))
    shield(p, 42, 96, 17, (196, 70, 60), rim=(214, 176, 80), boss=(214, 176, 80))


# ===========================================================================
#  CORE GROUND TROOPS
# ===========================================================================
@art("knight")
def _knight(p):
    f = Fig("normal")
    p.shadow()
    legs(p, f, (86, 92, 116))
    torso(p, f, STEEL)
    p.oval(f.tx, f.ty - 2, 9, 11, lt(STEEL, 0.25), ol=None, shade=False)
    belt(p, f, LEATHER, GOLD)
    arm(p, f, 0, STEEL, SKIN)
    head(p, f, SKIN)
    face(p, f, "dot", None, brows="angry")
    mustache(p, f, BLOND, size=1.15, droop=1.1)
    helmet(p, f, STEEL, depth=0.5, nose=True, band=DSTEEL)
    sword(p, f.hand[1][0], f.hand[1][1], a=66, L=48)
    arm(p, f, 1, STEEL, SKIN)


@art("archers")
def _archer(p):
    f = Fig("slim")
    p.shadow()
    p.shape([(76, 62), (88, 58), (92, 92), (80, 96)], LEATHER)          # quiver
    for x in (80, 85, 89):
        p.shape([(x - 3, 60), (x, 50), (x + 3, 60)], WHITE, w=1.6)
    hair_back(p, f, PINK, length=1.2, width=1.12)
    legs(p, f, (70, 104, 74))
    torso(p, f, (84, 168, 112))
    belt(p, f, LEATHER, None)
    arm(p, f, 0, (84, 168, 112), SKIN, to=(30, 84))
    bow(p, 30, 84, h=50, face_dir=-1)
    p.ball(30, 84, f.handr, SKIN, hl=False)
    head(p, f, SKIN)
    face(p, f, "dot", "smile", blush=True)
    hair_cap(p, f, PINK, depth=0.4, bangs=3)
    p.ball(f.hx + f.hr * 0.95, f.hy - f.hr * 0.7, 7, PINK)                # bun
    arm(p, f, 1, (84, 168, 112), SKIN)


@art("bomber")
def _bomber(p):
    f = Fig("small")
    p.shadow(rx=24)
    bomb(p, 100, 26, 14)                                  # bomb raised to throw
    skel_body(p, f)
    belt(p, f, LEATHER, None, dy=0.5)
    p.oval(78, 98, 7, 8, (66, 62, 78), w=2)               # spare bomb on belt
    bone_arm(p, f, 0)
    bone_arm(p, f, 1, to=(94, 38))
    skull(p, f)
    hair_cap(p, f, (110, 76, 46), depth=0.26, extra=1.2)  # little leather cap


@art("valkyrie")
def _valkyrie(p):
    f = Fig("normal")
    p.shadow()
    axe(p, 92, 98, a=95, L=58, double=True, size=1.05)
    for s in (-1, 1):                                                        # braids
        p.stroke([(64 + s * 22, 40), (64 + s * 27, 62), (64 + s * 25, 80)], 8,
                 (238, 104, 48))
        p.ball(64 + s * 25, 82, 4.5, (238, 104, 48), hl=False, w=2)
    legs(p, f, (150, 96, 60))
    torso(p, f, (170, 110, 70))
    p.oval(f.tx, f.ty - 7, 14, 6, STEEL, w=2.2)
    belt(p, f, (110, 70, 40), GOLD)
    arm(p, f, 0, SKIN_TAN, SKIN_TAN)
    head(p, f, SKIN_TAN)
    face(p, f, "dot", "grin", brows="angry")
    hair_cap(p, f, (238, 104, 48), depth=0.38, bangs=2)
    arm(p, f, 1, SKIN_TAN, SKIN_TAN, to=(92, 98))


@art("mini_pekka")
def _mini_pekka(p):
    f = Fig("small")
    armor = (64, 92, 132)
    p.shadow(rx=26)
    legs(p, f, dk(armor, 0.2), boot=(40, 50, 70))
    torso(p, f, armor)
    p.oval(f.tx, f.ty - 3, 7, 6, ELEC, w=2, shade=False)
    arm(p, f, 0, armor, DSTEEL)
    horns(p, f, (238, 232, 214), size=0.95, rise=0.9)
    p.ball(f.hx, f.hy, f.hr, armor)
    p.oval(f.hx, f.hy + 4, f.hr * 0.72, f.hr * 0.3, (30, 30, 46), w=2, shade=False)
    for s in (-1, 1):
        p._ellipse(f.hx + s * 8, f.hy + 4, 5, 3, ELEC)
    p.glow(f.hx, f.hy + 4, 18, ELEC, 70)
    sword(p, f.hand[1][0], f.hand[1][1], a=70, L=50, w=9, guard=DSTEEL)
    arm(p, f, 1, armor, DSTEEL)


@art("musketeer", "three_musketeers")
def _musketeer(p):
    f = Fig("slim")
    coat = (156, 56, 78)
    p.shadow()
    hair_back(p, f, (60, 44, 40), length=1.05)
    legs(p, f, (70, 60, 80))
    torso(p, f, coat)
    p.line((f.tx, f.ty - 14), (f.tx, f.ty + 14), 3.4, GOLD, ol=None)
    belt(p, f, (90, 60, 40), GOLD)
    arm(p, f, 0, coat, SKIN, to=(46, 92))
    head(p, f, SKIN)
    face(p, f, "dot", "flat", brows="flat")
    # morion helmet with curled brim + plume
    p.oval(f.hx, f.hy - f.hr * 0.4, f.hr * 1.3, f.hr * 0.26, STEEL, w=2.4)
    hair_cap(p, f, STEEL, depth=0.4, extra=1.5)
    p.shape([(f.hx - 5, f.hy - f.hr - 1), (f.hx, f.hy - f.hr - 12), (f.hx + 5, f.hy - f.hr - 1)],
            STEEL, w=2)
    p.stroke([(f.hx + 6, f.hy - f.hr), (f.hx + 18, f.hy - f.hr - 14), (f.hx + 28, f.hy - f.hr - 10)],
             6, (140, 90, 220))
    musket(p, 46, 92, a=36, L=62)
    arm(p, f, 1, coat, SKIN, to=(76, 82))


@art("barbarian", "barbarians")
def _barbarian(p):
    f = Fig("normal")
    p.shadow()
    hair_back(p, f, BLOND, length=1.0, width=1.15)
    legs(p, f, (130, 88, 54), boot=(90, 60, 40))
    torso(p, f, SKIN_TAN)
    p.line((f.tx - 15, f.ty - 12), (f.tx + 14, f.ty + 10), 5, LEATHER)          # strap
    belt(p, f, (120, 80, 50), DSTEEL, dy=0.45)
    arm(p, f, 0, SKIN_TAN, SKIN_TAN)
    head(p, f, SKIN_TAN)
    face(p, f, "dot", "open", brows="angry")
    mustache(p, f, BLOND, size=1.25, droop=1.4)
    helmet(p, f, STEEL, depth=0.42, nose=False, band=DSTEEL)
    horns(p, f)
    sword(p, f.hand[1][0], f.hand[1][1], a=72, L=46)
    arm(p, f, 1, SKIN_TAN, SKIN_TAN)


@art("elite_barbarians")
def _elite_barbarian(p):
    f = Fig("normal")
    hair = (64, 44, 38)
    p.shadow()
    sword(p, f.hand[0][0], f.hand[0][1], a=112, L=44)
    legs(p, f, (70, 80, 100), boot=(50, 50, 60))
    torso(p, f, (110, 126, 160))
    p.line((f.tx + 15, f.ty - 12), (f.tx - 14, f.ty + 10), 5, (60, 60, 70))
    belt(p, f, (60, 60, 70), GOLD, dy=0.45)
    arm(p, f, 0, SKIN_TAN, SKIN_TAN)
    head(p, f, SKIN_TAN)
    face(p, f, "glow", "open", brows="angry", eyecol=(255, 70, 60))
    mustache(p, f, hair, size=1.3, droop=1.6)
    helmet(p, f, (220, 180, 70), depth=0.42, nose=False, band=(160, 120, 40))
    horns(p, f, (250, 244, 222), size=1.1, rise=1.2)
    sword(p, f.hand[1][0], f.hand[1][1], a=68, L=46)
    arm(p, f, 1, SKIN_TAN, SKIN_TAN)


@art("wizard")
def _wizard(p):
    f = Fig("normal")
    robe_c = (64, 104, 214)
    p.shadow()
    robe(p, f, robe_c, trim=GOLD)
    torso(p, f, robe_c)
    arm(p, f, 0, robe_c, SKIN)
    head(p, f, SKIN)
    face(p, f, "dot", None, brows="flat")
    beard(p, f, (238, 238, 238), length=0.9)
    mustache(p, f, (246, 246, 246), size=0.9, droop=0.6)
    p.oval(f.hx, f.hy - f.hr * 0.45, f.hr * 1.35, f.hr * 0.3, dk(robe_c, 0.12), w=2.4)
    p.shape([(f.hx - f.hr * 0.95, f.hy - f.hr * 0.5), (f.hx - f.hr * 0.3, f.hy - f.hr * 1.3),
             (f.hx + f.hr * 0.55, f.hy - f.hr * 2.05), (f.hx + f.hr * 0.6, f.hy - f.hr * 1.2),
             (f.hx + f.hr * 0.95, f.hy - f.hr * 0.5)], robe_c)
    p.line((f.hx - f.hr * 0.9, f.hy - f.hr * 0.55), (f.hx + f.hr * 0.9, f.hy - f.hr * 0.55),
           4, GOLD, ol=None)
    hx, hy = arm(p, f, 1, robe_c, SKIN, to=(94, 76))
    p.glow(hx + 4, hy - 12, 22, FIRE, 160)
    p.ball(hx + 4, hy - 12, 10, FIRE)
    p.ball(hx + 3, hy - 13, 5, FIRE_Y, ol=None, hl=False)


@art("witch")
def _witch(p):
    f = Fig("slim")
    dress = (128, 60, 170)
    p.shadow()
    hair_back(p, f, (90, 40, 120), length=1.25)
    robe(p, f, dress, trim=(90, 40, 120))
    torso(p, f, dress)
    arm(p, f, 0, dress, SKIN_PALE)
    head(p, f, SKIN_PALE)
    face(p, f, "dot", "smile", eyecol=(120, 40, 140))
    # floppy pointed witch hood
    p.shape([(f.hx - f.hr * 1.1, f.hy - f.hr * 0.15), (f.hx - f.hr * 0.6, f.hy - f.hr * 1.1),
             (f.hx + f.hr * 0.2, f.hy - f.hr * 1.75), (f.hx + f.hr * 1.4, f.hy - f.hr * 1.5),
             (f.hx + f.hr * 0.9, f.hy - f.hr * 1.15), (f.hx + f.hr * 1.1, f.hy - f.hr * 0.15),
             (f.hx + f.hr * 0.75, f.hy - f.hr * 0.45), (f.hx - f.hr * 0.75, f.hy - f.hr * 0.45)],
            (100, 46, 140))
    staff(p, f.hand[1][0] + 2, f.hand[1][1], 40, kind="skull")
    arm(p, f, 1, dress, SKIN_PALE)


@art("pekka")
def _pekka(p):
    f = Fig("big")
    armor = (58, 64, 112)
    p.shadow(rx=40)
    sword(p, f.hand[1][0], f.hand[1][1], a=78, L=88, w=13, blade=(206, 214, 236),
          guard=(120, 90, 200))
    legs(p, f, dk(armor, 0.15), boot=(36, 40, 70))
    torso(p, f, armor)
    for s in (-1, 1):
        p.ball(64 + s * 30, 58, 13, lt(armor, 0.12))                       # pauldrons
    p.oval(f.tx, f.ty - 6, 9, 7, (220, 120, 255), w=2.2, shade=False)
    p.glow(f.tx, f.ty - 6, 16, (220, 120, 255), 90)
    arm(p, f, 0, armor, DSTEEL)
    horns(p, f, (226, 222, 232), size=1.05, rise=1.1)
    p.ball(f.hx, f.hy, f.hr, armor)
    p.oval(f.hx, f.hy + 3, f.hr * 0.78, f.hr * 0.3, (24, 22, 40), w=2, shade=False)
    for s in (-1, 1):
        p._ellipse(f.hx + s * 7, f.hy + 3, 4.6, 2.6, (230, 120, 255))
    p.glow(f.hx, f.hy + 3, 16, (220, 120, 255), 90)
    arm(p, f, 1, armor, DSTEEL)


@art("mega_knight")
def _mega_knight(p):
    f = Fig("big")
    armor = (74, 80, 108)
    trim = (214, 172, 70)
    p.shadow(rx=42)
    with p.layer(120):                                                       # slam dust
        for x, y, r in ((22, 112, 8), (106, 112, 8), (14, 104, 5), (114, 104, 5)):
            p._circle(x, y, r, (200, 190, 170))
    legs(p, f, dk(armor, 0.15), boot=(40, 42, 58))
    torso(p, f, armor)
    p.shape([(f.tx - 18, f.ty - 20), (f.tx + 18, f.ty - 20), (f.tx + 14, f.ty + 6),
             (f.tx - 14, f.ty + 6)], lt(armor, 0.15))                         # breastplate
    belt(p, f, (50, 46, 60), trim, dy=0.5)
    p.oval(f.tx, f.ty + 13, 7, 6, trim, w=2.2)                                # big buckle
    for s in (-1, 1):                                                        # spiked pauldrons
        cx = 64 + s * 31
        for a in (60, 90, 120):
            p.shape([pol(cx, 58, a - 16, 10), pol(cx, 58, a, 22), pol(cx, 58, a + 16, 10)],
                    STEEL, w=2)
        p.ball(cx, 58, 13, dk(armor, 0.05))
    for i in (0, 1):                                                         # huge gauntlets
        hx, hy = f.hand[i]
        p.line((f.ax[i], f.ay - 6), (hx, hy), 20, armor)
        for a in (0, 50, 130, 180):
            p.shape([pol(hx, hy, a - 18, 10), pol(hx, hy, a, 20), pol(hx, hy, a + 18, 10)],
                    STEEL, w=2)
        p.ball(hx, hy, 14, (62, 66, 86))
        p.line((hx - 8, hy + 2), (hx + 8, hy + 2), 1.6, (30, 30, 40), ol=None)
    for a in (55, 90, 125):                                                  # helmet spikes
        p.shape([pol(f.hx, f.hy, a - 12, f.hr), pol(f.hx, f.hy, a, f.hr + 15),
                 pol(f.hx, f.hy, a + 12, f.hr)], STEEL, w=2)
    p.ball(f.hx, f.hy, f.hr + 2, armor)
    p.oval(f.hx, f.hy + 3, f.hr * 0.8, f.hr * 0.3, (20, 18, 30), w=2, shade=False)
    for s in (-1, 1):
        p._ellipse(f.hx + s * 7, f.hy + 3, 4.4, 2.6, (255, 196, 70))
    p.glow(f.hx, f.hy + 3, 16, (255, 180, 60), 90)
    p.line((f.hx, f.hy - f.hr + 2), (f.hx, f.hy - 4), 3, trim, ol=None)


def horse(p, body, mane, barding=None, cx=64):
    p.shadow(cx + 2, 118, 40, 7)
    for x in (cx - 22, cx - 8, cx + 10, cx + 24):
        p.line((x, 96), (x, 112), 6.5, dk(body, 0.08))
        p.oval(x, 113, 5, 3, (60, 50, 50), w=1.8, shade=False)
    p.oval(cx + 2, 88, 34, 17, body)
    if barding:
        p.shape([(cx - 22, 78), (cx + 26, 78), (cx + 30, 100), (cx - 26, 100)], barding)
        p.line((cx - 26, 99), (cx + 30, 99), 3.5, GOLD, ol=None)
    p.stroke([(cx + 36, 92), (cx + 44, 100), (cx + 42, 110)], 6, mane)       # tail
    p.line((cx - 26, 84), (cx - 32, 62), 15, body)                          # neck
    p.oval(cx - 36, 58, 10, 14, body)                                     # head
    p.oval(cx - 39, 70, 7.5, 6, dk(body, 0.1), w=2)                        # muzzle
    p._circle(cx - 41, 70, 1.6, OUT)
    p.shape([(cx - 32, 46), (cx - 28, 36), (cx - 26, 48)], body, w=2)      # ear
    p._circle(cx - 39, 55, 2.2, OUT)
    p.stroke([(cx - 28, 46), (cx - 22, 58), (cx - 20, 74)], 6, mane)


@art("prince")
def _prince(p):
    horse(p, (238, 236, 230), (200, 196, 190), barding=(60, 96, 200))
    f = Fig("normal")
    with p.at(70, 50, 0.72):
        torso(p, f, (60, 96, 200))
        belt(p, f, GOLD, None)
        arm(p, f, 0, (60, 96, 200), STEEL)
        head(p, f, SKIN)
        face(p, f, "dot", "flat", brows="angry")
        helmet(p, f, GOLD, depth=0.56, nose=True, band=(200, 150, 40))
        p.stroke([(f.hx, f.hy - f.hr - 2), (f.hx + 10, f.hy - f.hr - 18),
                  (f.hx + 24, f.hy - f.hr - 16)], 8, (80, 130, 230))
        spear(p, f.hand[1][0], f.hand[1][1], a=150, L=58, tip=STEEL, w=4.5)
        arm(p, f, 1, (60, 96, 200), STEEL)


@art("dark_prince")
def _dark_prince(p):
    horse(p, (66, 60, 76), (120, 40, 50), barding=(40, 36, 50))
    f = Fig("normal")
    armor = (60, 56, 74)
    with p.at(70, 50, 0.72):
        torso(p, f, armor)
        belt(p, f, (150, 40, 50), DSTEEL)
        arm(p, f, 0, armor, IRON, to=(36, 92))
        shield(p, 36, 92, 16, (150, 40, 50), rim=DSTEEL, boss=DSTEEL)
        horns(p, f, (60, 56, 74), size=0.9, rise=1.1)
        p.ball(f.hx, f.hy, f.hr, armor)
        p.oval(f.hx, f.hy + 3, f.hr * 0.7, f.hr * 0.24, (20, 16, 26), w=2, shade=False)
        for s in (-1, 1):
            p._ellipse(f.hx + s * 7, f.hy + 3, 4, 2.4, (255, 70, 60))
        mace(p, f.hand[1][0], f.hand[1][1], a=60, L=30, head=IRON, size=1.0)
        arm(p, f, 1, armor, IRON)


@art("giant_skeleton")
def _giant_skeleton(p):
    f = Fig("big")
    p.shadow(rx=40)
    bomb(p, 98, 30, 20)                                                     # bomb on back
    for x in f.lx:
        p.line((x, f.ly - 14), (x, f.ly + 6), 7, BONE)
        p.oval(x + (x - 64) * 0.2, f.ly + 8, 8, 4.5, BONE)
    p.oval(f.tx, f.ty + 18, 20, 6, BONE)
    p.line((f.tx, f.ty - 28), (f.tx, f.ty + 16), 6.5, BONE)
    for i in range(4):
        y = f.ty - 18 + i * 8
        w = 28 - i * 4
        p.stroke(arcpts(f.tx, y + 6, w, 7, 165, 15, 8), 5, BONE)
    bone_arm_big = lambda i: (p.line((f.ax[i], f.ay - 12), f.hand[i], 7, BONE),
                              p.ball(f.hand[i][0], f.hand[i][1], 10, BONE))
    bone_arm_big(0)
    skull(p, f, eyecol=(255, 120, 60))
    bone_arm_big(1)


@art("lumberjack")
def _lumberjack(p):
    f = Fig("normal")
    shirt = (204, 54, 50)
    p.shadow()
    legs(p, f, (74, 92, 140), boot=(80, 54, 36))
    torso(p, f, shirt)
    for x in (-10, 0, 10):                                                  # flannel
        p.line((f.tx + x, f.ty - 15), (f.tx + x, f.ty + 15), 2.4, dk(shirt, 0.35), ol=None)
    p.line((f.tx - 18, f.ty - 3), (f.tx + 18, f.ty - 3), 2.4, dk(shirt, 0.35), ol=None)
    belt(p, f, (90, 60, 40), DSTEEL, dy=0.45)
    p.oval(f.tx - 13, f.ty + 12, 4.5, 6, (200, 90, 220), w=2)                  # rage bottle
    arm(p, f, 0, shirt, SKIN)
    head(p, f, SKIN)
    face(p, f, "dot", None, brows="angry")
    beard(p, f, (210, 96, 44), length=1.0, width=0.86)
    mustache(p, f, (226, 110, 52), size=1.0, droop=0.8)
    p._ellipse(f.hx - 6, f.hy - f.hr * 0.6, 7, 3.5, lt(SKIN, 0.5))           # bald shine
    axe(p, f.hand[1][0], f.hand[1][1], a=74, L=46)
    arm(p, f, 1, shirt, SKIN)


@art("bandit")
def _bandit(p):
    f = Fig("slim")
    suit = (90, 60, 110)
    hair = (170, 90, 210)
    p.shadow()
    p.stroke([(f.hx + 16, f.hy - 18), (f.hx + 32, f.hy - 6), (f.hx + 34, f.hy + 18)], 9, hair)
    legs(p, f, dk(suit, 0.2), boot=(50, 40, 60))
    torso(p, f, suit)
    belt(p, f, (60, 40, 70), GOLD)
    arm(p, f, 0, suit, SKIN)
    head(p, f, SKIN)
    p.line((f.hx - f.hr - 1, f.hy + 2), (f.hx + f.hr + 1, f.hy + 2), 11, (50, 34, 60))   # mask
    face(p, f, "dot", "smile", eyecol=WHITE)
    hair_cap(p, f, hair, depth=0.38, bangs=2)
    dagger(p, f.hand[1][0], f.hand[1][1], a=50, L=26)
    arm(p, f, 1, suit, SKIN)


# ===========================================================================
#  WIN CONDITIONS & GIANTS
# ===========================================================================
@art("giant")
def _giant(p):
    f = Fig("big")
    p.shadow(rx=40)
    legs(p, f, (130, 92, 58), boot=(90, 60, 40))
    torso(p, f, (214, 176, 120))
    p.shape([(f.tx - 30, f.ty - 10), (f.tx + 30, f.ty - 10), (f.tx + 26, f.ty + 20),
             (f.tx - 26, f.ty + 20)], (150, 104, 62))                       # vest
    belt(p, f, (100, 66, 40), DSTEEL, dy=0.55)
    arm(p, f, 0, SKIN_TAN, SKIN_TAN)
    head(p, f, SKIN_TAN)
    face(p, f, "dot", None, brows="angry")
    beard(p, f, (232, 120, 50), length=0.7)
    p.shape([(f.hx - 7, f.hy - f.hr + 2), (f.hx - 2, f.hy - f.hr - 9), (f.hx + 3, f.hy - f.hr - 3),
             (f.hx + 9, f.hy - f.hr - 8), (f.hx + 8, f.hy - f.hr + 3)], (232, 120, 50), w=2.2)
    arm(p, f, 1, SKIN_TAN, SKIN_TAN)


@art("royal_giant")
def _royal_giant(p):
    f = Fig("big")
    tunic = (66, 104, 196)
    p.shadow(rx=40)
    legs(p, f, (80, 66, 60), boot=(60, 44, 36))
    torso(p, f, tunic)
    p.line((f.tx, f.ty - 24), (f.tx, f.ty + 24), 5, GOLD, ol=None)
    belt(p, f, (120, 80, 40), GOLD, dy=0.5)
    head(p, f, SKIN_TAN)
    face(p, f, "dot", None, brows="angry")
    beard(p, f, (120, 74, 44), length=0.8)
    hair_cap(p, f, (120, 74, 44), depth=0.3, extra=1)
    # the cannon he hauls, held low across the body: arms first, then the
    # cannon, then his hands gripping it so the barrel stays readable
    l_hand, r_hand = (40, 96), (82, 76)
    arm(p, f, 0, SKIN_TAN, None, to=l_hand)
    arm(p, f, 1, SKIN_TAN, None, to=r_hand)
    a, b = (28, 104), (108, 60)
    iron = (64, 64, 80)
    p.line(a, b, 18, iron)
    p.oval(b[0], b[1], 8, 12, lt(iron, 0.1), w=2.4)
    p._ellipse(b[0] + 1, b[1], 4.5, 7.5, (22, 22, 30))
    p.ball(a[0], a[1], 9, iron, hl=False)
    for t in (0.22, 0.62, 0.9):
        ring_on(p, a, b, t, 22, GOLD, thick=4.5)
    for q in (l_hand, r_hand):
        p.ball(q[0], q[1], 9, SKIN_TAN, hl=False)


@art("hog_rider")
def _hog_rider(p):
    cx = 64
    p.shadow(66, 118, 40, 7)
    pig = (232, 156, 132)
    for x in (cx - 22, cx - 6, cx + 12, cx + 26):
        p.line((x, 98), (x, 112), 7, dk(pig, 0.1))
        p.oval(x, 113, 5, 3, (90, 60, 50), w=1.8, shade=False)
    p.stroke([(cx + 36, 90), (cx + 44, 86), (cx + 42, 94), (cx + 48, 92)], 3, pig)
    p.oval(cx + 4, 92, 36, 19, pig)
    p.oval(cx - 30, 88, 18, 16, pig)                                       # head
    for s in (-1, 1):
        p.shape([(cx - 30 + s * 10, 76), (cx - 30 + s * 17, 68), (cx - 30 + s * 15, 80)],
                pig, w=2)
    p.oval(cx - 38, 96, 9.5, 7, lt(pig, 0.15), w=2.2)                       # snout
    for s in (-1, 1):
        p._circle(cx - 38 + s * 3, 96, 1.8, (110, 50, 50))
        p.shape([(cx - 38 + s * 8, 98), (cx - 38 + s * 13, 90), (cx - 38 + s * 10, 101)],
                BONE, w=1.8)
    p._circle(cx - 35, 84, 2.2, OUT)
    p._circle(cx - 25, 84, 2.2, OUT)
    f = Fig("normal")
    with p.at(cx + 6, 50, 0.74):
        torso(p, f, SKIN_TAN)
        belt(p, f, LEATHER, DSTEEL)
        arm(p, f, 0, SKIN_TAN, SKIN_TAN, to=(36, 96))
        head(p, f, SKIN_TAN)
        face(p, f, "dot", "open", brows="angry")
        p.shape([(f.hx - 6, f.hy - f.hr + 4), (f.hx - 8, f.hy - f.hr - 20), (f.hx + 2, f.hy - f.hr - 26),
                 (f.hx + 22, f.hy - f.hr - 18), (f.hx + 16, f.hy - f.hr - 6), (f.hx + 8, f.hy - f.hr + 4)],
                (44, 38, 44))                                                # mohawk
        hammer(p, f.hand[1][0], f.hand[1][1], a=58, L=46, size=1.2)
        arm(p, f, 1, SKIN_TAN, SKIN_TAN)


@art("balloon")
def _balloon(p):
    p.shadow(64, 120, 18, 5, 50)
    env = (214, 54, 54)
    for s in (-1, 1):
        p.line((64 + s * 18, 66), (64 + s * 12, 84), 1.8, (100, 80, 60), ol=None)
    p.ball(64, 40, 34, env)
    seam = dk(env, 0.3)
    p.stroke(arcpts(64, 40, 17, 33, 90, 270, 14), 2.4, seam, ol=None)       # gores
    p.stroke(arcpts(64, 40, 17, 33, 90, -90, 14), 2.4, seam, ol=None)
    p.line((64, 7), (64, 73), 2.4, seam, ol=None)
    for s in (-1, 1):                                                        # crossbones
        p.line((64 - 11 * s, 30), (64 + 11 * s, 52), 3.4, BONE, w=1.8)
        for q in ((64 - 11 * s, 30), (64 + 11 * s, 52)):
            p.ball(q[0], q[1], 3, BONE, w=1.6, hl=False)
    skull_f = Fig("small")
    skull_f.hx, skull_f.hy, skull_f.hr = 64, 38, 10
    p.oval(64, 45, 5.5, 3.5, BONE, w=1.8, shade=False)
    p.ball(64, 38, 10, BONE, w=2)
    face(p, skull_f, "socket", None)
    p.oval(64, 90, 16, 9, WOOD)
    p.line((48, 86), (80, 86), 3, DWOOD, ol=None)
    f = Fig("small")
    with p.at(64, 70, 0.34):
        skull(p, f)
    bomb(p, 64, 108, 8, lit=False)


@art("golem", "golemite")
def _golem(p, rock=(132, 126, 146), crystal=(196, 104, 255)):
    p.shadow(rx=40)
    for s in (-1, 1):                                                      # arms
        p.oval(64 + s * 34, 72, 11, 24, rock)
        p.ball(64 + s * 37, 98, 12, dk(rock, 0.05))
    for x in (50, 78):
        p.oval(x, 106, 11, 10, dk(rock, 0.08))
    pts = [(38, 104), (34, 70), (42, 44), (58, 32), (76, 33), (90, 46), (94, 72), (90, 104)]
    p.shape(pts, rock)
    p._poly([(42, 46), (58, 34), (74, 36), (64, 50), (48, 56)], lt(rock, 0.22))
    p.stroke([(52, 60), (60, 74), (56, 88)], 1.8, dk(rock, 0.35), ol=None)
    p.stroke([(80, 56), (74, 70)], 1.8, dk(rock, 0.35), ol=None)
    for (x, y, r) in ((50, 84, 5), (78, 82, 6), (66, 96, 4.5), (84, 64, 4)):
        p.glow(x, y, r * 2.4, crystal, 110)
        p.shape([(x, y - r * 1.4), (x + r, y), (x, y + r * 1.4), (x - r, y)], crystal, w=1.8)
    for s in (-1, 1):
        p._ellipse(64 + s * 9, 52, 4.5, 3, crystal)
    p.glow(64, 52, 16, crystal, 70)


@art("elixir_golem", "elixir_golemite")
def _elixir_golem(p):
    _jelly(p, big=True)


@art("elixir_blob")
def _elixir_blob(p):
    _jelly(p, big=False)


def _jelly(p, big):
    col = (232, 104, 230)
    p.shadow(rx=36 if big else 24)
    if big:
        for s in (-1, 1):
            p.oval(64 + s * 32, 80, 11, 20, col)
            p.ball(64 + s * 34, 100, 10, dk(col, 0.05))
        p.shape([(36, 106), (34, 70), (48, 40), (64, 32), (80, 40), (94, 70), (92, 106)], col)
        p._poly([(48, 44), (64, 36), (76, 42), (60, 52)], lt(col, 0.45))
        for (x, y) in ((54, 88), (78, 92), (72, 78)):
            p.ball(x, y, 4, lt(col, 0.55), ol=None)
        # elixir-drop crest on top
        p.glow(64, 22, 16, ELIXIR, 110)
        p.shape([(64, 6), (72, 20)] + arcpts(64, 22, 8, 8, -10, -170, 8) + [(56, 20)],
                (250, 150, 250))
        p._ellipse(61, 19, 2.2, 3.4, WHITE)
        f = Fig("normal")
        f.hx, f.hy, f.hr = 64, 62, 20
    else:
        p.shape([(64, 40), (82, 74), (84, 92)] + arcpts(64, 92, 20, 18, 0, -180, 10)[1:-1] +
                [(44, 92), (46, 74)], col)
        p._poly([(60, 52), (66, 50), (58, 70)], lt(col, 0.5))
        f = Fig("normal")
        f.hx, f.hy, f.hr = 64, 86, 16
    face(p, f, "big", "smile", eyecol=(80, 20, 90))


@art("lava_hound")
def _lava_hound(p):
    rock = (120, 58, 44)
    lava = (255, 120, 40)
    p.shadow(64, 120, 26, 6, 50)
    for s in (-1, 1):
        wing(p, 64 + s * 18, 52, s, dk(rock, 0.1), 1.2, (150, 76, 56))
    p.oval(64, 66, 32, 26, rock)
    for s in (-1, 1):
        p.oval(64 + s * 22, 92, 8, 9, dk(rock, 0.1))
    for pts in ([(44, 58), (52, 70), (46, 82)], [(80, 56), (74, 68), (84, 80)],
                [(60, 78), (68, 88)]):
        p.stroke(pts, 3, lava, ol=None)
    p.glow(64, 70, 30, lava, 70)
    p.oval(64, 54, 18, 14, dk(rock, 0.05))
    for s in (-1, 1):
        p._ellipse(64 + s * 8, 52, 5, 3.4, FIRE_Y)
    p.shape([(52, 62), (64, 70), (76, 62), (64, 66)], lava, w=1.8)
    for s in (-1, 1):
        p.shape([(64 + s * 10, 42), (64 + s * 20, 26), (64 + s * 18, 44)], dk(rock, 0.15), w=2)


@art("lava_pup")
def _lava_pup(p):
    rock = (150, 70, 46)
    p.shadow(64, 118, 18, 5, 50)
    for s in (-1, 1):
        wing(p, 64 + s * 10, 60, s, dk(rock, 0.1), 0.9, (170, 90, 60))
    p.glow(64, 68, 28, FIRE, 110)
    p.ball(64, 68, 20, rock)
    p.stroke([(52, 62), (58, 74)], 2.6, FIRE, ol=None)
    p.stroke([(74, 60), (70, 76)], 2.6, FIRE, ol=None)
    for s in (-1, 1):
        p._ellipse(64 + s * 7, 66, 4, 3, FIRE_Y)


@art("ice_golem")
def _ice_golem(p):
    ice = (176, 222, 248)
    p.shadow(rx=36)
    for s in (-1, 1):
        p.oval(64 + s * 31, 76, 10, 20, ice)
        p.ball(64 + s * 33, 98, 11, dk(ice, 0.05))
    for x in (52, 76):
        p.oval(x, 106, 10, 9, dk(ice, 0.08))
    pts = [(38, 104), (36, 64), (44, 44), (64, 36), (84, 44), (92, 64), (90, 104)]
    p.shape(pts, ice)
    p._poly([(44, 46), (64, 38), (80, 44), (62, 56), (46, 60)], lt(ice, 0.5))
    p.shape([(40, 48), (50, 34), (64, 30), (80, 34), (88, 48), (76, 44), (64, 42), (52, 44)],
            WHITE, w=2.2)                                                   # snow cap
    for s in (-1, 1):
        p._ellipse(64 + s * 9, 58, 4.5, 4.5, (40, 90, 150))
    p.stroke(arcpts(64, 74, 10, 6, 200, 340, 6), 2.4, (40, 90, 150), ol=None)


# ===========================================================================
#  AIR UNITS
# ===========================================================================
def _imp(p, body, size=1.0, helmet_c=None, armored=False):
    cx, cy = 64, 64
    p.shadow(64, 120, 18 * size, 5, 50)
    for s in (-1, 1):
        wing(p, cx + s * 14 * size, cy - 6 * size, s, dk(body, 0.25), 1.1 * size,
             lt(body, 0.25))
    p.oval(cx, cy + 22 * size, 14 * size, 12 * size, body)                  # body
    for s in (-1, 1):
        p.line((cx + s * 12 * size, cy + 16 * size), (cx + s * 22 * size, cy + 30 * size),
               7 * size, body)
        p.ball(cx + s * 22 * size, cy + 31 * size, 5 * size, dk(body, 0.08), hl=False)
    if armored:
        for s in (-1, 1):
            p.ball(cx + s * 15 * size, cy + 12 * size, 8 * size, STEEL)
    f = Fig("small")
    f.hx, f.hy, f.hr = cx, cy - 4 * size, 20 * size
    for s in (-1, 1):
        p.shape([(cx + s * 9 * size, f.hy - 16 * size), (cx + s * 16 * size, f.hy - 30 * size),
                 (cx + s * 18 * size, f.hy - 12 * size)], lt(body, 0.6), w=2)
    head(p, f, body)
    face(p, f, "big", "grin", brows="angry", eyecol=(30, 30, 60))
    if helmet_c:
        helmet(p, f, helmet_c, depth=0.42, nose=True, band=dk(helmet_c, 0.25))


@art("minions", "minion_horde")
def _minion(p):
    _imp(p, (96, 144, 240))


@art("mega_minion")
def _mega_minion(p):
    _imp(p, (70, 90, 190), size=1.12, helmet_c=STEEL, armored=True)


def _dragon(p, body, belly, wing_m, horn=(250, 240, 210), kind="baby"):
    cx, cy = 64, 64
    p.shadow(64, 120, 22, 6, 50)
    for s in (-1, 1):
        wing(p, cx + s * 14, cy - 2, s, dk(body, 0.2), 1.25, wing_m)
    p.stroke([(cx + 18, cy + 26), (cx + 34, cy + 34), (cx + 42, cy + 26)], 9, body)
    p.shape([(cx + 40, cy + 22), (cx + 50, cy + 22), (cx + 44, cy + 30)], horn, w=2)
    p.oval(cx, cy + 20, 22, 18, body)
    p.oval(cx, cy + 24, 13, 12, belly, ol=None)
    for i in range(3):
        p.line((cx - 9, cy + 18 + i * 5), (cx + 9, cy + 18 + i * 5), 1.4, dk(belly, 0.2), ol=None)
    for s in (-1, 1):
        p.ball(cx + s * 13, cy + 36, 6, body, hl=False)
    f = Fig("small")
    f.hx, f.hy, f.hr = cx, cy - 12, 21
    for s in (-1, 1):
        p.shape([(cx + s * 8, f.hy - 14), (cx + s * 15, f.hy - 32), (cx + s * 18, f.hy - 10)], horn, w=2)
    head(p, f, body)
    p.oval(cx, f.hy + 11, 12, 8, lt(body, 0.15), w=2)                       # snout
    for s in (-1, 1):
        p._circle(cx + s * 4, f.hy + 9, 1.6, OUT)
    if kind == "inferno":
        hair_cap(p, f, (110, 112, 128), depth=0.48, extra=2)
        p.line((cx - 16, f.hy - 3), (cx + 16, f.hy - 3), 5, (70, 72, 86))
        for s in (-1, 1):
            p._ellipse(cx + s * 8, f.hy + 1, 4, 3, FIRE_Y)
        p.glow(cx, f.hy + 18, 12, FIRE, 160)
        p.ball(cx, f.hy + 17, 4.5, FIRE_Y, w=1.6, hl=False)
    else:
        face(p, f, "big", None, eyecol=(40, 30, 50), dy=-3)
        if kind == "electro":
            p.bolt([(cx - 2, f.hy - 26), (cx + 4, f.hy - 18), (cx - 3, f.hy - 14),
                    (cx + 3, f.hy - 4)], FIRE_Y, 2.6, ELEC)


@art("baby_dragon")
def _baby_dragon(p):
    _dragon(p, (114, 196, 82), (250, 226, 120), (240, 180, 70))


@art("inferno_dragon")
def _inferno_dragon(p):
    _dragon(p, (218, 90, 50), (255, 190, 100), (250, 130, 60), kind="inferno")


@art("electro_dragon")
def _electro_dragon(p):
    _dragon(p, (74, 130, 226), (180, 220, 255), (120, 200, 255), kind="electro")


@art("skeleton_barrel")
def _skeleton_barrel(p):
    p.shadow(64, 120, 18, 5, 50)
    for s in (-1, 1):
        p.line((64 + s * 14, 44), (64 + s * 16, 66), 1.8, (110, 90, 70), ol=None)
    p.ball(64, 28, 22, (150, 120, 190))
    p.ball(64, 26, 8, BONE, w=2)
    for s in (-1, 1):
        p._circle(64 + s * 3, 26, 2, (60, 50, 66))
    p.oval(64, 88, 24, 26, WOOD)
    for y in (70, 88, 106):
        p.stroke(arcpts(64, y - 4, 23, 5, 200, 340, 8), 3.4, DSTEEL)
    for s in (-1, 1):
        p.shape([(64 + s * 22, 80), (64 + s * 40, 70), (64 + s * 34, 86)], (240, 240, 245), w=2)
    p.ball(64, 90, 8, BONE, w=2)
    for s in (-1, 1):
        p._circle(64 + s * 3, 89, 2, (60, 50, 66))


@art("flying_machine")
def _flying_machine(p):
    p.shadow(64, 120, 22, 6, 50)
    p.line((64, 40), (64, 22), 4, DWOOD)
    p.oval(64, 20, 40, 5, (226, 210, 170), w=2.2)                            # rotor
    p.ball(64, 20, 5, DSTEEL, w=2, hl=False)
    f = Fig("small")
    with p.at(64, 48, 0.62):                                                  # goblin pilot
        goblin_ears(p, f)
        head(p, f, GOB)
        face(p, f, "dot", "grin")
        p.line((f.hx - f.hr, f.hy - 4), (f.hx + f.hr, f.hy - 4), 6, (110, 70, 40))
        for s in (-1, 1):
            p.ball(f.hx + s * 10, f.hy - 4, 7, (180, 220, 240), w=2.2)
    p.oval(64, 80, 30, 20, WOOD)
    for y in (72, 82, 92):
        p.line((38, y), (90, y), 1.6, dk(WOOD, 0.3), ol=None)
    p.line((70, 84), (100, 70), 9, IRON)                                     # cannon
    p.ball(100, 70, 5, IRON, hl=False)
    for s in (-1, 1):
        wing(p, 64 + s * 26, 82, s, DWOOD, 0.75, (220, 200, 160))


# ===========================================================================
#  SUPPORT / SPECIALISTS
# ===========================================================================
@art("dart_goblin")
def _dart_goblin(p):
    f = Fig("small")
    p.shadow(rx=24)
    legs(p, f, (110, 76, 46), boot=None)
    p.shape([(49, 92), (79, 92), (82, 110), (46, 110)], (110, 170, 70))       # leaf skirt
    for x in range(48, 82, 6):
        p.line((x, 100), (x + 2, 111), 1.4, (70, 120, 40), ol=None)
    torso(p, f, GOB)
    arm(p, f, 0, GOB, GOB, to=(60, 66))
    goblin_ears(p, f, length=1.1)
    head(p, f, GOB)
    # wooden tribal mask
    p.oval(f.hx, f.hy + 4, f.hr * 0.78, f.hr * 0.86, (196, 140, 80))
    for s in (-1, 1):
        p.oval(f.hx + s * 9, f.hy, 4, 5, (40, 30, 30), ol=None, shade=False)
    p.line((f.hx - 8, f.hy + 14), (f.hx + 8, f.hy + 14), 2.4, (120, 70, 40), ol=None)
    for i, c in enumerate(((240, 80, 60), (250, 200, 60), (90, 180, 240))):
        p.shape([(f.hx - 10 + i * 10, f.hy - f.hr + 2), (f.hx - 6 + i * 10, f.hy - f.hr - 18),
                 (f.hx - 2 + i * 10, f.hy - f.hr + 2)], c, w=1.8)
    p.line((58, 70), (108, 64), 4.2, (120, 160, 70))                         # blowgun
    arm(p, f, 1, GOB, GOB, to=(70, 70))


@art("princess")
def _princess(p):
    f = Fig("slim")
    dress = (250, 128, 180)
    p.shadow()
    hair_back(p, f, BLOND, length=1.35, width=1.15, dy=0.5)
    robe(p, f, dress, trim=WHITE, flare=1.45)
    torso(p, f, dress)
    arm(p, f, 0, dress, SKIN, to=(30, 82))
    bow(p, 30, 82, h=50, col=(240, 200, 80), face_dir=-1, arrow_col=FIRE)
    p.glow(8, 82, 9, FIRE, 160)
    p.ball(30, 82, f.handr, SKIN, hl=False)
    head(p, f, SKIN)
    face(p, f, "big", "smile", blush=True, eyecol=(70, 110, 200))
    hair_cap(p, f, BLOND, depth=0.4, bangs=3)
    crown(p, f, GOLD, w=0.45, h=0.45, dy=-2, gem=(120, 180, 255))
    arm(p, f, 1, dress, SKIN)


@art("electro_wizard")
def _electro_wizard(p):
    f = Fig("normal")
    robe_c = (52, 70, 140)
    p.shadow()
    p.shape([(42, 70), (86, 70), (98, 114), (30, 114)], (40, 140, 220))      # cape
    robe(p, f, robe_c, trim=ELEC)
    torso(p, f, robe_c)
    head(p, f, SKIN)
    face(p, f, "glow", "flat", brows="angry", eyecol=ELEC)
    spikes = [(f.hx - f.hr - 2, f.hy - 2), (f.hx - f.hr - 8, f.hy - f.hr * 0.9),
              (f.hx - f.hr * 0.5, f.hy - f.hr * 0.95), (f.hx - f.hr * 0.6, f.hy - f.hr * 1.65),
              (f.hx, f.hy - f.hr * 1.05), (f.hx + f.hr * 0.4, f.hy - f.hr * 1.8),
              (f.hx + f.hr * 0.55, f.hy - f.hr * 0.95), (f.hx + f.hr + 8, f.hy - f.hr * 1.1),
              (f.hx + f.hr + 2, f.hy - 2), (f.hx + f.hr * 0.7, f.hy - f.hr * 0.4),
              (f.hx - f.hr * 0.7, f.hy - f.hr * 0.4)]
    p.shape(spikes, (236, 244, 255))
    for i in (0, 1):
        hx, hy = arm(p, f, i, robe_c, SKIN, to=((28, 82), (100, 82))[i])
        p.glow(hx, hy, 18, ELEC, 160)
        p.bolt([(hx, hy - 4), (hx + (6 if i else -6), hy - 14), (hx - (2 if i else -2), hy - 18),
                (hx + (8 if i else -8), hy - 30)], WHITE, 2.4, ELEC)


@art("ice_wizard")
def _ice_wizard(p):
    f = Fig("normal")
    robe_c = (150, 206, 240)
    p.shadow()
    hood_back(p, f, robe_c)
    robe(p, f, robe_c, trim=WHITE)
    torso(p, f, robe_c)
    arm(p, f, 0, robe_c, (210, 236, 250))
    head(p, f, (214, 236, 250))
    face(p, f, "dot", None, eyecol=(40, 90, 150))
    beard(p, f, WHITE, length=1.1)
    mustache(p, f, WHITE, size=0.95, droop=0.7)
    hood_front(p, f, robe_c, depth=0.34)
    for s in (-0.5, 0.5):
        p.shape([(64 + s * 28 - 3, f.hy - f.hr - 4), (64 + s * 28, f.hy - f.hr - 14),
                 (64 + s * 28 + 3, f.hy - f.hr - 4)], WHITE, w=1.6)
    hx, hy = arm(p, f, 1, robe_c, (210, 236, 250), to=(96, 80))
    p.glow(hx + 2, hy - 12, 20, ICE, 170)
    p.shape([(hx + 2, hy - 26), (hx + 10, hy - 12), (hx + 2, hy + 2), (hx - 6, hy - 12)], ICE)


@art("sparky")
def _sparky(p):
    p.shadow(rx=40)
    for x in (34, 94):
        p.ball(x, 102, 13, DWOOD)
        p.ball(x, 102, 5, DSTEEL, w=2, hl=False)
    p.shape([(26, 78), (102, 78), (98, 100), (30, 100)], WOOD)
    for x in (44, 64, 84):
        p.line((x, 80), (x, 98), 2, dk(WOOD, 0.3), ol=None)
    p.shape([(46, 78), (82, 78), (76, 52), (52, 52)], DSTEEL)
    for y in (58, 66, 74):
        p.line((50, y), (78, y), 3, (200, 160, 80), ol=None)
    p.glow(64, 38, 34, (255, 230, 100), 170)
    p.ball(64, 38, 18, (255, 226, 96))
    p.ball(64, 38, 9, WHITE, ol=None, hl=False)
    for a in (30, 90, 150, 210):
        q = pol(64, 38, a, 18)
        p.bolt([q, pol(*q, a + 30, 8), pol(*q, a - 10, 16)], (255, 250, 200), 2.2)


@art("hunter")
def _hunter(p):
    f = Fig("bulky")
    coat = (110, 120, 76)
    p.shadow(rx=36)
    legs(p, f, (100, 78, 60), boot=(70, 50, 36))
    torso(p, f, coat)
    belt(p, f, LEATHER, DSTEEL, dy=0.45)
    for i in range(4):
        p.ball(f.tx - 12 + i * 8, f.ty - 6, 2.6, (240, 200, 80), w=1.4, hl=False)   # shells
    arm(p, f, 0, coat, SKIN_TAN, to=(42, 98))
    head(p, f, SKIN_TAN)
    face(p, f, "dot", None, brows="angry")
    beard(p, f, (210, 210, 214), length=1.1, width=0.9)
    mustache(p, f, (232, 232, 236), size=1.1)
    p.oval(f.hx, f.hy - f.hr * 0.45, f.hr * 1.2, f.hr * 0.28, (112, 82, 52), w=2.4)
    hair_cap(p, f, (130, 96, 60), depth=0.44, extra=1.8)
    # blunderbuss
    p.line((40, 100), (60, 92), 10, WOOD)
    p.line((58, 92), (104, 76), 6.5, IRON)
    p.line((58, 98), (104, 82), 6.5, IRON)
    p.oval(105, 79, 4, 7.5, IRON, w=2)
    arm(p, f, 1, coat, SKIN_TAN, to=(78, 88))


@art("executioner")
def _executioner(p):
    f = Fig("bulky")
    skin = (200, 170, 190)
    p.shadow(rx=36)
    axe(p, f.hand[1][0], f.hand[1][1], a=82, L=58, double=True, size=1.15, head=(210, 216, 230))
    legs(p, f, (60, 50, 70), boot=(40, 34, 48))
    torso(p, f, skin)
    p.shape([(f.tx - 25, f.ty + 2), (f.tx + 25, f.ty + 2), (f.tx + 20, f.ty + 22),
             (f.tx - 20, f.ty + 22)], (70, 56, 86))
    belt(p, f, (40, 34, 48), DSTEEL, dy=0.12)
    arm(p, f, 0, skin, skin)
    p.ball(f.hx, f.hy, f.hr, (52, 46, 62))                                    # hood mask
    p.shape([(f.hx, f.hy - f.hr - 14), (f.hx + 9, f.hy - f.hr + 4), (f.hx - 9, f.hy - f.hr + 4)],
            (52, 46, 62), w=2.2)
    for s in (-1, 1):
        p.oval(f.hx + s * 8, f.hy, 5.5, 4, (250, 230, 120), w=1.6, shade=False)
        p._circle(f.hx + s * 8, f.hy, 2, OUT)
    arm(p, f, 1, skin, skin)


@art("bowler")
def _bowler(p):
    f = Fig("big")
    skin = (110, 140, 220)
    p.shadow(rx=40)
    legs(p, f, (90, 70, 110), boot=(60, 50, 70))
    torso(p, f, skin)
    p.shape([(f.tx - 30, f.ty + 4), (f.tx + 30, f.ty + 4), (f.tx + 26, f.ty + 24),
             (f.tx - 26, f.ty + 24)], (124, 84, 150))
    head(p, f, skin)
    face(p, f, "dot", "smile", brows="flat")
    p._ellipse(f.hx - 5, f.hy - f.hr * 0.6, 6, 3, lt(skin, 0.5))
    arm(p, f, 0, skin, skin, to=(44, 92))
    arm(p, f, 1, skin, skin, to=(84, 92))
    p.ball(64, 92, 22, (150, 120, 176))                                      # boulder
    p._poly([(52, 84), (60, 78), (66, 86)], dk((150, 120, 176), 0.25))
    p._circle(72, 100, 3.5, dk((150, 120, 176), 0.25))
    p.ball(44, 92, f.handr, skin, hl=False)
    p.ball(84, 92, f.handr, skin, hl=False)


@art("magic_archer")
def _magic_archer(p):
    f = Fig("slim")
    cloak = (60, 156, 150)
    p.shadow()
    hood_back(p, f, cloak, extra=5)
    p.shape([(44, 72), (84, 72), (96, 114), (32, 114)], dk(cloak, 0.15))
    legs(p, f, (70, 70, 90))
    torso(p, f, cloak)
    arm(p, f, 0, cloak, SKIN, to=(30, 84))
    p.glow(30, 84, 30, (120, 255, 220), 100)
    bow(p, 30, 84, h=54, col=(110, 240, 210), face_dir=-1, arrow_col=(180, 255, 230),
        string=(180, 255, 230))
    p.ball(30, 84, f.handr, SKIN, hl=False)
    head(p, f, SKIN)
    face(p, f, "dot", None)
    p.line((f.hx - f.hr * 0.75, f.hy + 12), (f.hx + f.hr * 0.75, f.hy + 12), 10, (40, 60, 70))
    hood_front(p, f, cloak, depth=0.36)
    arm(p, f, 1, cloak, SKIN)


@art("night_witch")
def _night_witch(p):
    f = Fig("slim")
    robe_c = (64, 48, 96)
    p.shadow()
    for s in (-1, 1):
        wing(p, 64 + s * 12, 68, s, (40, 30, 60), 1.15, (90, 60, 130))
    robe(p, f, robe_c, trim=(150, 90, 220))
    torso(p, f, robe_c)
    arm(p, f, 0, robe_c, (220, 200, 236))
    hood_back(p, f, (44, 34, 66), extra=4)
    head(p, f, (220, 200, 236))
    face(p, f, "glow", "smile", eyecol=(200, 120, 255))
    hood_front(p, f, (44, 34, 66), extra=4, depth=0.36)
    horns(p, f, (60, 50, 80), size=0.95, rise=1.25)
    p.line((f.hand[1][0] + 2, f.hand[1][1] + 14), (f.hand[1][0] + 2, 36), 4.4, (60, 46, 80))
    p.glow(f.hand[1][0] + 2, 30, 16, (200, 120, 255), 130)
    p.stroke(arcpts(f.hand[1][0] + 2, 34, 12, 10, 120, 300, 10), 5, (200, 150, 255))
    arm(p, f, 1, robe_c, (220, 200, 236))


@art("zappies")
def _zappy(p):
    f = Fig("small")
    suit = (90, 110, 140)
    p.shadow(rx=24)
    p.shape([(76, 62), (96, 58), (98, 98), (78, 100)], DSTEEL)               # backpack
    p.line((88, 58), (88, 30), 3.4, IRON)
    p.glow(88, 26, 16, ELEC, 160)
    p.ball(88, 26, 7, (190, 236, 255))
    legs(p, f, dk(suit, 0.2), boot=(50, 56, 70))
    torso(p, f, suit)
    arm(p, f, 0, suit, SKIN_TAN)
    head(p, f, SKIN_TAN)
    face(p, f, "dot", "grin")
    p.line((f.hx - f.hr, f.hy - 6), (f.hx + f.hr, f.hy - 6), 6, (110, 80, 50))
    for s in (-1, 1):
        p.ball(f.hx + s * 10, f.hy - 6, 7, (255, 220, 80), w=2.2)
    helmet(p, f, (232, 190, 60), depth=0.34, nose=False)
    hx, hy = arm(p, f, 1, suit, SKIN_TAN)
    p.bolt([(hx, hy - 4), (hx + 8, hy - 12), (hx + 2, hy - 16), (hx + 10, hy - 24)],
           FIRE_Y, 2.2, ELEC)


@art("cannon_cart")
def _cannon_cart(p):
    p.shadow(rx=40)
    for x in (36, 92):
        p.ball(x, 102, 12, DWOOD)
        p.ball(x, 102, 4.5, DSTEEL, w=2, hl=False)
    p.shape([(28, 80), (100, 80), (98, 98), (30, 98)], WOOD)
    p.line((40, 72), (102, 58), 18, (66, 66, 82))                            # barrel
    p.oval(104, 57, 6, 10, (66, 66, 82), w=2)
    p._ellipse(105, 57, 3, 6, (24, 24, 32))
    p.ball(44, 72, 12, (66, 66, 82))
    p.shape([(18, 54), (40, 50), (44, 92), (22, 96)], (120, 150, 210))       # shield plate
    p._poly([(22, 58), (36, 55), (38, 66), (24, 70)], lt((120, 150, 210), 0.4))
    for y in (62, 80):
        p.ball(31, y, 2.4, DSTEEL, w=1.4, hl=False)


@art("battle_healer")
def _battle_healer(p):
    f = Fig("slim")
    armor = (246, 238, 220)
    p.shadow()
    p.glow(64, 70, 54, (140, 255, 160), 70)
    hair_back(p, f, BLOND, length=1.25, width=1.12, dy=0.45)
    legs(p, f, (200, 180, 140))
    torso(p, f, armor)
    p.shape([(f.tx - 6, f.ty - 6), (f.tx + 6, f.ty - 6), (f.tx + 6, f.ty - 2), (f.tx + 2, f.ty - 2),
             (f.tx + 2, f.ty + 8), (f.tx - 2, f.ty + 8), (f.tx - 2, f.ty - 2), (f.tx - 6, f.ty - 2)],
            (90, 210, 110), w=1.6)                                           # heal cross
    belt(p, f, GOLD, None)
    for s in (-1, 1):
        p.ball(64 + s * 18, 74, 8, GOLD)
    arm(p, f, 0, armor, SKIN)
    head(p, f, SKIN)
    face(p, f, "dot", "smile", blush=True)
    hair_cap(p, f, BLOND, depth=0.42, bangs=2)
    p.stroke(arcpts(f.hx, f.hy - 4, f.hr + 3, f.hr + 3, 30, 150, 10), 3.6, GOLD)  # circlet
    hammer(p, f.hand[1][0], f.hand[1][1], a=72, L=36, head=GOLD, size=0.9)
    arm(p, f, 1, armor, SKIN)


@art("electro_giant")
def _electro_giant(p):
    f = Fig("big")
    armor = (96, 116, 160)
    p.shadow(rx=40)
    legs(p, f, (70, 80, 110), boot=(46, 52, 70))
    torso(p, f, armor)
    p.ball(f.tx, f.ty - 4, 10, (180, 236, 255))
    p.glow(f.tx, f.ty - 4, 20, ELEC, 130)
    for s in (-1, 1):                                                        # shoulder coils
        p.ball(64 + s * 30, 56, 12, DSTEEL)
        p.line((64 + s * 30, 46), (64 + s * 30, 28), 4, IRON)
        p.glow(64 + s * 30, 24, 14, ELEC, 160)
        p.ball(64 + s * 30, 24, 6, (200, 240, 255))
    for i in (0, 1):
        hx, hy = arm(p, f, i, armor, (90, 110, 150))
        p.glow(hx, hy, 15, ELEC, 120)
    head(p, f, SKIN_TAN)
    face(p, f, "dot", "grin", brows="angry")
    p.line((f.hx - f.hr, f.hy - 5), (f.hx + f.hr, f.hy - 5), 5.5, IRON)
    for s in (-1, 1):
        p.ball(f.hx + s * 8, f.hy - 5, 6, (160, 230, 255), w=2)
    helmet(p, f, DSTEEL, depth=0.36, nose=False)
    p.bolt([(46, 40), (40, 48), (46, 52)], FIRE_Y, 2)
    p.bolt([(82, 40), (88, 48), (82, 52)], FIRE_Y, 2)


@art("goblin_giant")
def _goblin_giant(p):
    f = Fig("big")
    p.shadow(rx=40)
    rf = Fig("small")
    for s in (-1, 1):                                                        # back riders
        with p.at(64 + s * 30, 40, 0.42):
            spear(p, rf.hx + s * 20, rf.hy + 30, a=90 - s * 12, L=56)
            goblin_ears(p, rf)
            head(p, rf, GOB)
            face(p, rf, "dot", "grin")
    legs(p, f, (110, 76, 46), boot=(80, 56, 36))
    torso(p, f, GOB)
    p.shape([(f.tx - 30, f.ty + 2), (f.tx + 30, f.ty + 2), (f.tx + 26, f.ty + 24),
             (f.tx - 26, f.ty + 24)], LEATHER)
    p.line((f.tx - 26, f.ty - 18), (f.tx + 26, f.ty + 4), 5, (110, 70, 40))
    p.line((f.tx + 26, f.ty - 18), (f.tx - 26, f.ty + 4), 5, (110, 70, 40))
    arm(p, f, 0, GOB, GOB)
    goblin_ears(p, f, length=1.2)
    head(p, f, GOB)
    face(p, f, "dot", "grin", brows="angry")
    nose(p, f, dk(GOB, 0.15), 1.5)
    arm(p, f, 1, GOB, GOB)


@art("miner")
def _miner(p):
    f = Fig("normal")
    over = (96, 84, 70)
    p.shadow()
    legs(p, f, (110, 96, 76), boot=(70, 52, 36))
    torso(p, f, over)
    for s in (-1, 1):
        p.line((f.tx + s * 9, f.ty - 16), (f.tx + s * 9, f.ty + 4), 4, (150, 120, 80))
    arm(p, f, 0, (200, 120, 70), SKIN_TAN)
    head(p, f, SKIN_TAN)
    face(p, f, "dot", "grin")
    p._circle(f.hx - 10, f.hy + 10, 2.4, dk(SKIN_TAN, 0.2))                 # dirt smudge
    mustache(p, f, (90, 60, 40), size=0.9, droop=0.5)
    helmet(p, f, (240, 190, 50), depth=0.46, nose=False, band=(180, 130, 30))
    p.ball(f.hx, f.hy - f.hr * 0.55, 6, (255, 250, 200), w=2.2)
    p.glow(f.hx, f.hy - f.hr * 0.55, 14, (255, 250, 180), 140)
    shovel(p, f.hand[1][0], f.hand[1][1], a=66, L=44)
    arm(p, f, 1, (200, 120, 70), SKIN_TAN)


@art("battle_ram")
def _battle_ram(p):
    p.shadow(64, 118, 46, 7)
    f = Fig("normal")
    for x in (34, 86):                                                       # two barbs
        with p.at(x, 66, 0.6):
            hair_back(p, f, BLOND, length=1.0, width=1.15)
            legs(p, f, (130, 88, 54), boot=(90, 60, 40))
            torso(p, f, SKIN_TAN)
            head(p, f, SKIN_TAN)
            face(p, f, "dot", "open", brows="angry")
            mustache(p, f, BLOND, size=1.2, droop=1.3)
            helmet(p, f, STEEL, depth=0.42, nose=False, band=DSTEEL)
            horns(p, f)
    p.line((14, 92), (108, 92), 20, WOOD)                                    # log
    for x in (36, 60, 84):
        p.line((x, 84), (x + 6, 100), 1.6, dk(WOOD, 0.3), ol=None)
    p.oval(14, 92, 6, 10, (226, 180, 120), w=2)
    p.ball(112, 92, 12, DSTEEL)
    for x in (36, 86):
        p.ball(x - 10, 92, 5.5, SKIN_TAN, hl=False)
        p.ball(x + 10, 92, 5.5, SKIN_TAN, hl=False)


@art("royal_guardian")
def _royal_guardian(p):
    f = Fig("normal")
    armor = (196, 204, 222)
    p.shadow()
    spear(p, f.hand[1][0], f.hand[1][1], a=86, L=60, tip=GOLD)
    legs(p, f, dk(armor, 0.2))
    torso(p, f, armor)
    arm(p, f, 1, armor, DSTEEL)
    p.ball(f.hx, f.hy, f.hr, armor)                                          # bucket helm
    p.line((f.hx - f.hr * 0.7, f.hy + 2), (f.hx + f.hr * 0.7, f.hy + 2), 4.4, (30, 30, 44))
    p.line((f.hx, f.hy - 8), (f.hx, f.hy + 14), 3.6, GOLD, ol=None)
    p.stroke([(f.hx, f.hy - f.hr - 2), (f.hx + 8, f.hy - f.hr - 16), (f.hx + 22, f.hy - f.hr - 14)],
             8, (70, 120, 230))
    p.shape([(26, 66), (60, 66), (58, 104), (43, 116), (28, 104)], (70, 110, 210))   # tower shield
    p.line((43, 70), (43, 110), 4, GOLD, ol=None)
    p.line((30, 84), (56, 84), 4, GOLD, ol=None)


@art("goblin_monster")
def _goblin_monster(p):
    f = Fig("big")
    skin = (110, 180, 96)
    p.shadow(rx=40)
    legs(p, f, (70, 60, 80), boot=(40, 34, 46))
    torso(p, f, (80, 70, 96))
    p.line((f.tx - 10, f.ty - 20), (f.tx + 10, f.ty + 10), 2, (190, 190, 200), ol=None)
    arm(p, f, 0, skin, skin)
    goblin_ears(p, f, skin, 1.0)
    head(p, f, skin)
    for s in (-1, 1):                                                        # neck bolts
        p.line((f.hx + s * 14, f.hy + 18), (f.hx + s * 26, f.hy + 20), 5, DSTEEL)
    face(p, f, "dot", "grin", brows="angry")
    hair_cap(p, f, (50, 46, 56), depth=0.34, extra=1.5, bangs=3)
    p.line((f.hx - 10, f.hy - 4), (f.hx + 2, f.hy - 4), 1.6, OUT, ol=None)   # stitches
    for x in (-8, -4, 0):
        p.line((f.hx + x, f.hy - 7), (f.hx + x, f.hy - 1), 1.4, OUT, ol=None)
    arm(p, f, 1, skin, skin)


# ===========================================================================
#  CHAMPIONS  (a little extra detail: capes, crowns, glints)
# ===========================================================================
def champ_glow(p):
    p.glow(64, 70, 58, (255, 220, 110), 55)


@art("mighty_miner")
def _mighty_miner(p):
    f = Fig("bulky")
    over = (60, 110, 150)
    p.shadow(rx=38)
    champ_glow(p)
    legs(p, f, (80, 70, 60), boot=(60, 44, 30))
    torso(p, f, over)
    for s in (-1, 1):
        p.line((f.tx + s * 11, f.ty - 18), (f.tx + s * 11, f.ty + 4), 4.5, (230, 170, 60))
    belt(p, f, (90, 60, 40), GOLD, dy=0.4)
    arm(p, f, 0, (200, 120, 70), SKIN_TAN)
    head(p, f, SKIN_TAN)
    face(p, f, "dot", None, brows="angry")
    beard(p, f, (110, 70, 44), length=0.9)
    mustache(p, f, (130, 84, 50), size=1.05)
    helmet(p, f, (255, 140, 40), depth=0.46, nose=False, band=(200, 90, 20))
    p.ball(f.hx, f.hy - f.hr * 0.55, 6.5, (255, 250, 200), w=2.2)
    p.glow(f.hx, f.hy - f.hr * 0.55, 16, (255, 250, 180), 150)
    # big drill
    hx, hy = f.hand[1]
    p.shape([(hx - 6, hy - 16), (hx + 10, hy - 16), (hx + 36, hy - 4), (hx + 10, hy + 8),
             (hx - 6, hy + 8)], DSTEEL)
    p.shape([(hx + 22, hy - 12), (hx + 46, hy - 4), (hx + 22, hy + 4)], STEEL)
    for i in range(3):
        p.line((hx + 26 + i * 6, hy - 9 + i * 1.5), (hx + 24 + i * 6, hy + 1 - i * 1.2), 1.6,
               DSTEEL, ol=None)
    arm(p, f, 1, (200, 120, 70), SKIN_TAN)


@art("archer_queen")
def _archer_queen(p):
    f = Fig("slim")
    cape = (110, 56, 150)
    p.shadow()
    champ_glow(p)
    p.shape([(42, 64), (86, 64), (104, 116), (24, 116)], cape)
    p._poly([(70, 66), (86, 66), (102, 114), (80, 114)], dk(cape, 0.2))
    hair_back(p, f, (50, 40, 70), length=1.3, width=1.12, dy=0.45)
    legs(p, f, (50, 44, 64), boot=(36, 30, 46))
    torso(p, f, (70, 58, 96))
    belt(p, f, GOLD, None)
    arm(p, f, 0, (70, 58, 96), SKIN_PALE, to=(40, 92))
    head(p, f, SKIN_PALE)
    face(p, f, "dot", "smile", eyecol=(110, 40, 140))
    hair_cap(p, f, (50, 40, 70), depth=0.42, bangs=2)
    crown(p, f, GOLD, w=0.55, h=0.6, dy=-1, gem=(170, 90, 230))
    crossbow(p, 72, 90, col=(80, 50, 110), limb=GOLD, bolt=(200, 160, 255))
    arm(p, f, 1, (70, 58, 96), SKIN_PALE, to=(76, 88))


@art("little_prince")
def _little_prince(p):
    f = Fig("small")
    p.shadow(rx=26)
    champ_glow(p)
    p.shape([(46, 74), (82, 74), (96, 114), (32, 114)], (60, 100, 220))      # cape
    legs(p, f, (240, 240, 245), boot=(110, 70, 40))
    torso(p, f, (70, 120, 230))
    belt(p, f, GOLD, None)
    arm(p, f, 0, (70, 120, 230), SKIN)
    head(p, f, SKIN)
    face(p, f, "big", "smile", blush=True, eyecol=(60, 100, 200))
    hair_cap(p, f, BLOND, depth=0.36, bangs=3)
    crown(p, f, GOLD, w=0.6, h=0.62, dy=-1, gem=(90, 150, 255))
    hx, hy = f.hand[1]
    p.line((hx, hy + 6), (hx + 6, hy - 30), 3.6, GOLD)
    p.ball(hx + 7, hy - 34, 6, (90, 150, 255), w=2)
    arm(p, f, 1, (70, 120, 230), SKIN)


@art("golden_knight")
def _golden_knight(p):
    f = Fig("normal")
    gold = (255, 206, 72)
    p.shadow()
    champ_glow(p)
    p.shape([(44, 66), (84, 66), (98, 116), (30, 116)], (210, 50, 50))       # red cape
    hair_back(p, f, BLOND, length=1.05, width=1.15)
    legs(p, f, dk(gold, 0.2), boot=(150, 110, 30))
    torso(p, f, gold)
    p.oval(f.tx, f.ty - 3, 9, 11, lt(gold, 0.35), ol=None, shade=False)
    belt(p, f, (150, 100, 30), RED)
    arm(p, f, 0, gold, gold)
    head(p, f, SKIN)
    face(p, f, "dot", "smile", brows="flat")
    hair_cap(p, f, BLOND, depth=0.4, bangs=3, bang_len=0.25)
    sword(p, f.hand[1][0], f.hand[1][1], a=74, L=52, blade=(255, 236, 150), guard=RED)
    arm(p, f, 1, gold, gold)


@art("skeleton_king")
def _skeleton_king(p):
    f = Fig("big")
    p.shadow(rx=40)
    champ_glow(p)
    p.shape([(30, 54), (98, 54), (110, 116), (18, 116)], (60, 40, 80))       # dark cape
    p._poly([(70, 56), (98, 56), (108, 114), (78, 114)], (44, 30, 60))
    mace(p, f.hand[1][0], f.hand[1][1], a=74, L=44, head=(80, 80, 96), size=1.2)
    for x in f.lx:
        p.line((x, f.ly - 14), (x, f.ly + 6), 7, BONE)
        p.oval(x + (x - 64) * 0.2, f.ly + 8, 8, 4.5, BONE)
    p.line((f.tx, f.ty - 28), (f.tx, f.ty + 16), 6.5, BONE)
    for i in range(4):
        y = f.ty - 18 + i * 8
        p.stroke(arcpts(f.tx, y + 6, 26 - i * 4, 7, 165, 15, 8), 5, BONE)
    for i in (0, 1):
        p.line((f.ax[i], f.ay - 12), f.hand[i], 7, BONE)
        p.ball(f.hand[i][0], f.hand[i][1], 10, BONE)
    skull(p, f, eyecol=(120, 255, 140))
    p.glow(f.hx, f.hy + 2, 18, (120, 255, 140), 90)
    crown(p, f, GOLD, w=0.75, h=0.75, dy=0, gem=(120, 255, 140))


@art("monk")
def _monk(p):
    f = Fig("bulky")
    robe_c = (232, 120, 52)
    p.shadow(rx=36)
    champ_glow(p)
    robe(p, f, robe_c, trim=(250, 200, 80), flare=1.2)
    torso(p, f, robe_c)
    p.line((f.tx - 24, f.ty - 18), (f.tx + 22, f.ty + 16), 7, dk(robe_c, 0.2))
    for i in range(7):                                                       # prayer beads
        a = 200 + i * 20
        q = (f.tx + 18 * math.cos(math.radians(a)), f.ty - 18 - 12 * math.sin(math.radians(a)))
        p.ball(q[0], q[1] + 2, 3, (130, 80, 40), w=1.4, hl=False)
    arm(p, f, 0, SKIN_TAN, SKIN_TAN)
    head(p, f, SKIN_TAN)
    face(p, f, "closed", None)
    beard(p, f, (236, 236, 240), length=1.3, width=0.8)
    mustache(p, f, (244, 244, 248), size=1.05, droop=1.2)
    p._ellipse(f.hx - 6, f.hy - f.hr * 0.6, 7, 3.5, lt(SKIN_TAN, 0.5))
    arm(p, f, 1, SKIN_TAN, SKIN_TAN)


@art("goblinstein")
def _goblinstein(p):
    f = Fig("small")
    p.shadow(rx=26)
    champ_glow(p)
    legs(p, f, (80, 80, 96), boot=(50, 50, 60))
    p.shape([(46, 82), (82, 82), (88, 112), (40, 112)], (240, 240, 236))     # lab coat
    torso(p, f, (240, 240, 236))
    p.line((f.tx, f.ty - 12), (f.tx, f.ty + 14), 1.6, (190, 190, 190), ol=None)
    arm(p, f, 0, (240, 240, 236), GOB)
    goblin_ears(p, f)
    head(p, f, GOB)
    face(p, f, "dot", "grin", brows="angry")
    hair_cap(p, f, (236, 236, 240), depth=0.28, extra=2.5, bangs=4, bang_len=0.3)
    p.line((f.hx - f.hr, f.hy - f.hr * 0.45), (f.hx + f.hr, f.hy - f.hr * 0.45), 5, (110, 70, 40))
    for s in (-1, 1):
        p.ball(f.hx + s * 10, f.hy - f.hr * 0.45, 7, (140, 230, 160), w=2.2)
    hx, hy = f.hand[1]
    p.line((hx, hy + 8), (hx + 4, hy - 34), 4, IRON)
    p.glow(hx + 5, hy - 38, 16, ELEC, 170)
    p.ball(hx + 5, hy - 38, 6, (200, 240, 255))
    p.bolt([(hx + 5, hy - 44), (hx + 12, hy - 52), (hx + 6, hy - 56)], FIRE_Y, 2)
    arm(p, f, 1, (240, 240, 236), GOB)


@art("boss_bandit")
def _boss_bandit(p):
    f = Fig("slim")
    suit = (80, 50, 100)
    hair = (190, 100, 230)
    p.shadow()
    champ_glow(p)
    p.shape([(42, 66), (86, 66), (100, 116), (28, 116)], (130, 50, 80))     # cape
    p.stroke([(f.hx + 14, f.hy - 20), (f.hx + 34, f.hy - 6), (f.hx + 38, f.hy + 24)], 11, hair)
    legs(p, f, dk(suit, 0.2), boot=(40, 30, 50))
    torso(p, f, suit)
    belt(p, f, GOLD, RED)
    arm(p, f, 0, suit, SKIN, to=(34, 92))
    dagger(p, 34, 92, a=118, L=26, blade=(255, 220, 120))
    p.ball(34, 92, f.handr, SKIN, hl=False)
    head(p, f, SKIN)
    p.line((f.hx - f.hr - 1, f.hy + 2), (f.hx + f.hr + 1, f.hy + 2), 12, GOLD)  # gold mask
    face(p, f, "dot", "smile", eyecol=(60, 20, 60))
    hair_cap(p, f, hair, depth=0.4, bangs=2)
    dagger(p, f.hand[1][0], f.hand[1][1], a=58, L=26, blade=(255, 220, 120))
    arm(p, f, 1, suit, SKIN)


# ===========================================================================
#  BUILDINGS
# ===========================================================================
@art("cannon")
def _cannon(p):
    plinth(p)
    p.shape([(36, 104), (40, 78), (88, 78), (92, 104)], WOOD)
    for x in (48, 64, 80):
        p.line((x, 80), (x, 102), 1.6, dk(WOOD, 0.3), ol=None)
    a, b = (58, 76), (104, 52)
    p.line(a, b, 22, (70, 70, 86))
    p.oval(106, 51, 7, 12, (70, 70, 86), w=2)
    p._ellipse(107, 51, 3.5, 7, (24, 24, 32))
    p.ball(56, 76, 18, (70, 70, 86))
    ring_on(p, a, b, 0.55, 26, GOLD)
    p.ball(56, 76, 6, DSTEEL, w=2, hl=False)


@art("tesla")
def _tesla(p):
    plinth(p)
    p.shape([(40, 106), (46, 64), (82, 64), (88, 106)], (110, 126, 160))
    p.shape([(50, 66), (78, 66), (72, 38), (56, 38)], (150, 166, 200))
    for y in (74, 86, 98):
        p.line((44, y), (84, y), 3, (90, 104, 136), ol=None)
    for y in (46, 54):
        p.oval(64, y, 13, 3.5, (210, 160, 70), w=1.8)
    p.glow(64, 26, 30, ELEC, 160)
    p.ball(64, 26, 13, (180, 236, 255))
    p.ball(64, 26, 6, WHITE, ol=None, hl=False)
    for a in (20, 160, 260):
        q = pol(64, 26, a, 14)
        p.bolt([q, pol(*q, a + 25, 7), pol(*q, a - 10, 14)], (220, 250, 255), 2)


@art("inferno_tower")
def _inferno_tower(p):
    plinth(p, (120, 112, 116))
    p.shape([(36, 106), (42, 46), (86, 46), (92, 106)], (88, 80, 92))
    for y in (60, 76, 92):
        p.line((40, y), (88, y), 2, (60, 54, 66), ol=None)
    for x in (42, 56, 72, 86):
        p.shape([(x - 6, 50), (x - 4, 34), (x + 4, 34), (x + 6, 50)], (110, 100, 116), w=2.2)
    p.glow(64, 30, 34, FIRE, 160)
    p.shape([(50, 44), (54, 22), (60, 32), (64, 6), (70, 30), (76, 20), (78, 44)], FIRE)
    p._poly([(56, 44), (60, 30), (64, 16), (69, 32), (72, 44)], FIRE_Y)
    p.ball(64, 72, 8, (255, 120, 40), w=2)


@art("bomb_tower")
def _bomb_tower(p):
    plinth(p)
    p.oval(64, 64, 30, 10, (150, 144, 136))
    p.shape([(34, 104), (36, 64), (92, 64), (94, 104)], (160, 152, 140))
    for y in (76, 90):
        p.line((36, y), (92, y), 2, (120, 114, 104), ol=None)
    for x in (42, 56, 72, 86):
        p.shape([(x - 6, 66), (x - 5, 52), (x + 5, 52), (x + 6, 66)], (176, 170, 160), w=2.2)
    bomb(p, 64, 40, 16)
    p.shape([(52, 86), (76, 86), (76, 104), (52, 104)], (80, 60, 48))


@art("mortar")
def _mortar(p):
    plinth(p)
    # wooden cradle
    p.shape([(30, 106), (36, 82), (92, 82), (98, 106)], WOOD)
    for x in (46, 64, 82):
        p.line((x, 84), (x + 1, 104), 1.6, dk(WOOD, 0.3), ol=None)
    # squat iron tube, wide at the base, gaping mouth on top
    tube = (76, 78, 96)
    p.shape([(38, 90), (90, 90), (84, 42), (44, 42)], tube)
    p._poly([(46, 88), (56, 88), (54, 46), (48, 46)], lt(tube, 0.22))
    for y, wd in ((78, 50), (56, 42)):
        p.band((64 - wd / 2 - 3, y), (64 + wd / 2 + 3, y), 7, GOLD, w=2)
    p.oval(64, 42, 22, 8, lt(tube, 0.1), w=2.4)
    p._ellipse(64, 42, 15, 5, (22, 22, 30))
    p.ball(64, 92, 9, DSTEEL, w=2, hl=False)                                 # pivot


@art("xbow")
def _xbow(p):
    plinth(p)
    for x0, x1 in ((40, 56), (88, 72)):
        p.line((x0, 108), (x1, 74), 6, DWOOD)
    p.line((64, 108), (64, 76), 6, DWOOD)
    p.shape([(30, 70), (98, 70), (92, 82), (36, 82)], WOOD)
    p.stroke(arcpts(64, 78, 52, 30, 160, 20, 14), 6, IRON)                    # bow limbs
    p.line((14, 68), (114, 68), 1.6, (230, 230, 230), ol=None)
    p.line((64, 92), (64, 16), 8, WOOD)
    p.shape([(58, 22), (64, 6), (70, 22)], STEEL)
    p.ball(64, 76, 6, GOLD, w=2, hl=False)


@art("tombstone")
def _tombstone(p):
    p.shadow(64, 116, 34, 7)
    p.oval(64, 108, 32, 8, (110, 160, 80))
    p.shape([(42, 108), (42, 44)] + arcpts(64, 44, 22, 22, 180, 0, 12) + [(86, 108)],
            (170, 168, 176))
    p._poly([(46, 104), (46, 46), (60, 26), (60, 104)], (190, 188, 196))
    skull_f = Fig("small")
    skull_f.hx, skull_f.hy, skull_f.hr = 64, 64, 12
    p.ball(64, 64, 12, BONE, w=2)
    face(p, skull_f, "socket", None)
    p.stroke([(52, 86), (76, 86)], 3, (120, 118, 126), ol=None)
    p.stroke([(52, 94), (72, 94)], 3, (120, 118, 126), ol=None)
    p.ball(84, 108, 6, (90, 140, 70), hl=False, w=2)


def _hut(p, wall, roof, roof_trim, door=(60, 40, 30)):
    plinth(p, (150, 140, 120))
    p.shape([(34, 106), (36, 66), (92, 66), (94, 106)], wall)
    for y in (78, 92):
        p.line((36, y), (92, y), 1.6, dk(wall, 0.25), ol=None)
    p.shape([(52, 106), (52, 84)] + arcpts(64, 84, 12, 12, 180, 0, 8) + [(76, 106)], door)
    p.shape([(22, 70), (64, 24), (106, 70)], roof)
    for x in (40, 56, 72, 88):
        p.line((x, 66), (64 + (x - 64) * 0.3, 34), 2, dk(roof, 0.25), ol=None)
    p.line((22, 70), (106, 70), 5, roof_trim)


@art("goblin_hut")
def _goblin_hut(p):
    _hut(p, (176, 130, 80), (120, 180, 70), (90, 130, 50))
    spear(p, 100, 104, a=96, L=64)
    p.ball(64, 40, 7, GOB, w=2)


@art("barbarian_hut")
def _barbarian_hut(p):
    _hut(p, (190, 150, 110), (180, 70, 50), (120, 50, 40))
    for s in (-1, 1):
        p.shape([(64 + s * 8, 32), (64 + s * 26, 14), (64 + s * 20, 34)], (250, 244, 222), w=2)
    p.ball(64, 32, 8, STEEL, w=2)


@art("furnace")
def _furnace(p):
    plinth(p)
    p.shape([(34, 106), (38, 52), (90, 52), (94, 106)], (190, 90, 60))
    for y in (64, 76, 88, 100):
        p.line((36, y), (92, y), 1.6, (140, 60, 40), ol=None)
        for x in range(42 + (y % 24) // 2, 92, 14):
            p.line((x, y - 12), (x, y), 1.4, (140, 60, 40), ol=None)
    p.shape([(50, 106), (50, 84)] + arcpts(64, 84, 14, 14, 180, 0, 8) + [(78, 106)], (50, 30, 30))
    p.glow(64, 94, 22, FIRE, 170)
    p.shape([(54, 106), (58, 92), (62, 98), (64, 84), (68, 96), (72, 90), (74, 106)], FIRE, w=1.8)
    p.line((76, 52), (76, 30), 12, (140, 70, 50))
    p.oval(76, 28, 8, 3, (110, 54, 40), w=2)
    with p.layer(130):
        for i, (x, y, r) in enumerate(((80, 18, 6), (86, 8, 4.5))):
            p._circle(x, y, r, (180, 180, 190))


@art("elixir_collector")
def _elixir_collector(p):
    plinth(p)
    p.shape([(38, 106), (40, 92), (88, 92), (90, 106)], (150, 110, 80))
    p.oval(64, 66, 26, 28, (230, 190, 245))                                  # glass tank
    p.oval(64, 74, 22, 18, ELIXIR, ol=None)
    p._ellipse(54, 58, 6, 10, WHITE)
    for y in (42, 92):
        p.oval(64, y, 22, 5, GOLD, w=2)
    p.line((64, 38), (64, 22), 5, DSTEEL)
    p.shape([(64, 4), (72, 18), (64, 24), (56, 18)], ELIXIR)
    p.glow(64, 16, 14, ELIXIR, 120)


# ===========================================================================
#  SPELLS
# ===========================================================================
def spell_bg(p, col):
    p.glow(64, 64, 58, col, 110, steps=7)


@art("zap")
def _zap(p):
    spell_bg(p, ELEC)
    p.ball(64, 64, 30, (90, 170, 255))
    p.ball(64, 64, 18, (200, 240, 255), ol=None, hl=False)
    p.bolt([(70, 26), (52, 62), (68, 64), (56, 102)], FIRE_Y, 6.5)
    for a in (20, 140, 250, 320):
        q = pol(64, 64, a, 30)
        p.bolt([q, pol(*q, a + 20, 10), pol(*q, a - 10, 18)], WHITE, 2.4)


@art("lightning")
def _lightning(p):
    spell_bg(p, (200, 190, 255))
    for x, y, r in ((44, 40, 18), (64, 32, 22), (86, 40, 18), (54, 48, 16), (76, 48, 16)):
        p.ball(x, y, r, (110, 110, 140), hl=False)
    p.bolt([(54, 56), (44, 80), (56, 80), (46, 112)], FIRE_Y, 5, (255, 250, 180))
    p.bolt([(78, 56), (70, 76), (82, 76), (74, 100)], FIRE_Y, 4, (255, 250, 180))


@art("arrows")
def _arrows(p):
    spell_bg(p, (255, 240, 200))
    for dx, dy in ((-26, -8), (0, 0), (26, -8)):
        x, y = 64 + dx, 64 + dy
        p.line((x + 14, y - 34), (x - 8, y + 26), 3.4, WOOD)
        p.shape([(x - 14, y + 22), (x - 2, y + 26), (x - 12, y + 40)], STEEL, w=2)
        for k in (0, 6):
            p.shape([(x + 14 - k * 0.37, y - 34 + k), (x + 22 - k * 0.37, y - 40 + k),
                     (x + 18 - k * 0.37, y - 30 + k)], RED, w=1.6)


@art("fireball")
def _fireball(p):
    spell_bg(p, FIRE)
    p.shape([(30, 30), (50, 50), (44, 30), (64, 46), (66, 26), (78, 52), (96, 80), (70, 96),
             (40, 74)], (255, 120, 40))
    p.ball(70, 74, 24, FIRE)
    p.ball(66, 70, 13, FIRE_Y, ol=None, hl=False)
    p.ball(62, 66, 6, WHITE, ol=None, hl=False)


@art("rocket")
def _rocket(p):
    spell_bg(p, (255, 160, 90))
    a = -45
    c = (64, 60)
    p.glow(40, 36, 20, FIRE, 160)
    p.shape([pol(*c, a + 180, 34), add(pol(*c, a + 180, 46), perp(a, 8)),
             pol(*c, a + 180, 56), add(pol(*c, a + 180, 46), perp(a, -8))], FIRE)
    body = [add(pol(*c, a + 180, 30), perp(a, 11)), add(pol(*c, a, 22), perp(a, 11)),
            pol(*c, a, 42), add(pol(*c, a, 22), perp(a, -11)), add(pol(*c, a + 180, 30), perp(a, -11))]
    p.shape(body, (230, 70, 60))
    p._poly([add(pol(*c, a + 180, 26), perp(a, 7)), add(pol(*c, a, 20), perp(a, 7)),
             add(pol(*c, a, 20), perp(a, 3)), add(pol(*c, a + 180, 26), perp(a, 3))],
            (255, 140, 120))
    for s in (-1, 1):
        q = add(pol(*c, a + 180, 26), perp(a, 11 * s))
        p.shape([q, add(q, perp(a, 10 * s)), add(add(q, perp(a, 6 * s)), vec(a, 14))], DSTEEL,
                w=2)
    p.line(add(pol(*c, a, 4), perp(a, -11)), add(pol(*c, a, 4), perp(a, 11)), 4, WHITE, ol=None)


@art("the_log")
def _the_log(p):
    spell_bg(p, (220, 170, 110))
    p.line((22, 72), (100, 52), 34, WOOD)
    for x in range(30, 96, 12):
        p.line((x, 74 - (x - 22) * 0.256 - 10), (x + 4, 74 - (x - 22) * 0.256 + 10), 1.6,
               dk(WOOD, 0.3), ol=None)
    for x, y in ((40, 52), (62, 46), (84, 40), (46, 90), (70, 84), (92, 76)):
        p.shape([(x - 3, y + 3), (x, y - 7 if y < 70 else y + 9), (x + 3, y + 3)], STEEL, w=1.6)
    p.oval(100, 52, 11, 17, (230, 186, 126))
    p.stroke(arcpts(100, 52, 6, 10, 0, 360, 14), 1.6, (190, 140, 90), ol=None)


@art("rage")
def _rage(p):
    spell_bg(p, (220, 90, 230))
    p.shape([(44, 56), (44, 40), (84, 40), (84, 56), (96, 98), (82, 110), (46, 110), (32, 98)],
            (240, 220, 250))
    p.shape([(38, 84), (90, 84), (96, 98), (82, 110), (46, 110), (32, 98)], (210, 70, 220))
    p._ellipse(48, 72, 4, 12, WHITE)
    p.oval(64, 38, 18, 5, (130, 90, 60), w=2)
    p.shape([(52, 32), (54, 18), (74, 18), (76, 32)], (150, 100, 70))
    f = Fig("small")
    f.hx, f.hy, f.hr = 64, 96, 12
    face(p, f, "dot", "open", brows="angry", dy=-4)


@art("freeze")
def _freeze(p):
    spell_bg(p, ICE)
    for a in range(0, 360, 60):
        q = pol(64, 64, a, 40)
        p.line((64, 64), q, 6, (200, 240, 255))
        for s in (-1, 1):
            m = pol(64, 64, a, 26)
            p.line(m, pol(*m, a + s * 45, 12), 4, (200, 240, 255))
    p.ball(64, 64, 10, WHITE)


@art("poison")
def _poison(p):
    spell_bg(p, (140, 230, 80))
    p.shape([(48, 52), (48, 30), (80, 30), (80, 52), (96, 86)] +
            arcpts(64, 88, 32, 22, 0, -180, 10)[1:-1] + [(32, 86)], (230, 240, 220))
    p.shape([(36, 74), (92, 74), (96, 88)] + arcpts(64, 88, 32, 22, 0, -180, 10)[1:-1] +
            [(32, 88)], (120, 200, 60))
    p.oval(64, 28, 18, 5, (110, 80, 60), w=2)
    p.ball(64, 90, 11, BONE, w=2)
    for s in (-1, 1):
        p._circle(64 + s * 4, 89, 2.4, (60, 120, 40))
    for x, y, r in ((44, 64, 5), (58, 50, 3.5), (82, 62, 4)):
        p.ball(x, y, r, (170, 240, 110), w=1.6)


@art("goblin_barrel")
def _goblin_barrel(p):
    spell_bg(p, (150, 220, 100))
    f = Fig("small")
    with p.at(64, 42, 0.55):
        goblin_ears(p, f)
        head(p, f, GOB)
        face(p, f, "dot", "grin", brows="angry")
    p.oval(64, 84, 32, 30, WOOD)
    for y in (64, 84, 104):
        p.stroke(arcpts(64, y - 6, 31, 6, 200, 340, 10), 4, DSTEEL)
    p.oval(64, 58, 28, 6, dk(WOOD, 0.3), w=2)


@art("barbarian_barrel")
def _barbarian_barrel(p):
    spell_bg(p, (255, 220, 120))
    p.line((22, 74), (106, 74), 40, WOOD)
    for x in (40, 64, 88):
        p.line((x, 54), (x, 94), 4, DSTEEL)
    p.oval(106, 74, 10, 20, (220, 170, 110))
    sword(p, 46, 50, a=60, L=40)
    p.ball(46, 50, 7, SKIN_TAN, hl=False)


@art("snowball")
def _snowball(p):
    spell_bg(p, (220, 240, 255))
    p.ball(64, 66, 34, (244, 250, 255))
    for x, y, r in ((50, 56, 6), (76, 74, 8), (60, 86, 5)):
        p._circle(x, y, r, (214, 230, 245))
    for x, y in ((24, 30), (102, 34), (98, 100), (28, 96)):
        p.spark(x, y, 6, WHITE)


@art("earthquake")
def _earthquake(p):
    spell_bg(p, (200, 150, 90))
    p.shape([(16, 80), (40, 60), (64, 66), (90, 56), (112, 74), (104, 100), (70, 110), (26, 100)],
            (150, 100, 60))
    p._poly([(24, 82), (40, 66), (64, 72), (88, 62), (104, 76), (90, 80), (60, 82), (34, 88)],
            (110, 160, 70))
    p.stroke([(30, 92), (46, 82), (58, 96), (72, 84), (88, 96), (100, 86)], 3.4, (70, 44, 30),
             ol=None)
    for x, y in ((40, 40), (64, 30), (88, 38)):
        p.shape([(x - 7, y + 6), (x - 2, y - 6), (x + 7, y - 2), (x + 4, y + 8)], (170, 120, 70),
                w=2)


@art("tornado")
def _tornado(p):
    spell_bg(p, (200, 210, 230))
    for i, (y, r) in enumerate(((26, 40), (42, 32), (58, 25), (74, 18), (90, 12), (104, 7))):
        x = 64 + math.sin(i * 0.9) * 6
        p.oval(x, y, r, 7, (226, 232, 244) if i % 2 == 0 else (196, 206, 226), w=2.2)
    for x, y in ((24, 60), (102, 70), (34, 100)):
        p.oval(x, y, 4, 2.5, (150, 120, 90), w=1.4)


@art("graveyard")
def _graveyard(p):
    spell_bg(p, (170, 120, 200))
    p.oval(64, 98, 50, 14, (90, 70, 110))
    for x, h in ((36, 30), (90, 26), (62, 40)):
        p.shape([(x - 12, 100), (x - 12, 100 - h)] + arcpts(x, 100 - h, 12, 10, 180, 0, 8) +
                [(x + 12, 100)], (176, 172, 186))
        p.line((x, 100 - h - 4), (x, 100 - h + 12), 2.4, (120, 116, 130), ol=None)
        p.line((x - 6, 100 - h + 2), (x + 6, 100 - h + 2), 2.4, (120, 116, 130), ol=None)
    for i in range(4):                                                       # bony hand
        p.line((50 + i * 5, 112), (47 + i * 6, 96 - (i % 2) * 4), 3, BONE)
    p.oval(56, 114, 10, 5, BONE)


# ===========================================================================
#  FALLBACK (for any card added later without its own art)
# ===========================================================================
def fallback(p, card):
    import colorsys
    key = getattr(card, "key", "unknown")
    h = (sum(ord(c) for c in key) * 37 % 360) / 360.0
    r, g, b = colorsys.hsv_to_rgb(h, 0.55, 0.9)
    col = (int(r * 255), int(g * 255), int(b * 255))
    cat = getattr(card, "category", "troop")
    if cat == "spell":
        spell_bg(p, col)
        p.ball(64, 64, 30, col)
        p.spark(64, 64, 20, WHITE)
    elif cat == "building":
        _hut(p, col, dk(col, 0.25), dk(col, 0.45))
    else:
        f = Fig("normal")
        p.shadow()
        legs(p, f, dk(col, 0.3))
        torso(p, f, col)
        arm(p, f, 0, col, SKIN)
        head(p, f, SKIN)
        face(p, f, "dot", "smile")
        hair_cap(p, f, dk(col, 0.4), depth=0.38, bangs=2)
        arm(p, f, 1, col, SKIN)


# ===========================================================================
#  ENTRY POINTS used by sprites.py
# ===========================================================================
def render_unit(key, card=None):
    """Paint one unit / card at 128x128 (anti-aliased)."""
    p = P()
    fn = ART.get(key)
    if fn is None:
        fallback(p, card)
    else:
        fn(p)
    return pygame.transform.smoothscale(p.surf, (BASE, BASE))


# Where each figure of a squad card goes: (centre x, centre y, scale).
SQUADS = {
    2: [(42, 62, 0.7), (86, 70, 0.7)],
    3: [(38, 52, 0.6), (90, 52, 0.6), (64, 76, 0.64)],
    4: [(38, 46, 0.54), (90, 46, 0.54), (40, 80, 0.56), (88, 80, 0.56)],
    5: [(28, 50, 0.5), (100, 50, 0.5), (64, 36, 0.5), (40, 84, 0.52), (88, 84, 0.52)],
    6: [(28, 44, 0.46), (64, 38, 0.46), (100, 44, 0.46),
        (30, 82, 0.48), (64, 78, 0.48), (98, 82, 0.48)],
    7: [(30, 36, 0.4), (64, 30, 0.4), (98, 36, 0.4), (22, 70, 0.42),
        (106, 70, 0.42), (46, 90, 0.44), (82, 90, 0.44)],
}


def render_squad(unit_surf, count):
    """Card art for multi-unit cards: several copies of the single unit."""
    slots = SQUADS.get(min(count, 7), SQUADS[3])
    out = pygame.Surface((BASE, BASE), pygame.SRCALPHA)
    for x, y, k in sorted(slots, key=lambda s: s[1]):
        size = max(1, int(BASE * k))
        img = pygame.transform.smoothscale(unit_surf, (size, size))
        out.blit(img, (int(x - size / 2), int(y - size / 2)))
    return out
