"""
============================================================================
  ICONS.PY  --  Currency icons in the style of the real game
============================================================================

Gold, gems, Evo shards, Hero coins, King XP and trophies, modelled on the
real Clash Royale icons:

    xp      a cyan 12-point star with a dark-blue bevel (the King level badge)
    gold    a thick gold coin with a raised inner ring
    gems    a faceted lime-green hexagon
    shards  a skewed purple glass crystal (an Evolution shard)
    coins   a rounded gold diamond with a yellow-green sheen (a Hero coin)
    trophy  a gold cup with looping handles
    potion  a round glass flask of glowing purple brew with a level-up arrow
            (the Level-Up Potion)

Each is drawn 4x larger with flat shapes, given a dark outline, then
smooth-scaled down (so the edges are anti-aliased) and cached by size.
get(kind, r) returns a Surface about 2.5r wide; blit(screen, kind, x, y, r)
draws it centred on (x, y).
============================================================================
"""

import math

import pygame

SS = 4                         # supersampling factor
OUTLINE = (22, 18, 30)
_cache = {}


def _grad(size, top, bottom):
    """A vertical gradient surface."""
    w, h = size
    g = pygame.Surface((1, max(h, 1)), pygame.SRCALPHA)
    for y in range(h):
        f = y / max(h - 1, 1)
        g.set_at((0, y), tuple(int(a + (b - a) * f) for a, b in zip(top, bottom)) + (255,))
    return pygame.transform.scale(g, (w, h))


def _fill_grad(surf, pts, top, bottom):
    """Fill polygon `pts` on surf with a vertical gradient (over its bbox)."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, y0 = int(min(xs)), int(min(ys))
    w, h = int(max(xs)) - x0 + 2, int(max(ys)) - y0 + 2
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), [(x - x0, y - y0) for x, y in pts])
    m.blit(_grad((w, h), top, bottom), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surf.blit(m, (x0, y0))


def _circle_grad(surf, c, rad, top, bottom):
    rad = int(rad)
    m = pygame.Surface((rad * 2 + 2, rad * 2 + 2), pygame.SRCALPHA)
    pygame.draw.circle(m, (255, 255, 255, 255), (rad + 1, rad + 1), rad)
    m.blit(_grad(m.get_size(), top, bottom), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surf.blit(m, (c[0] - rad - 1, c[1] - rad - 1))


def _shine(surf, rect, alpha=110):
    """A soft white gloss ellipse."""
    g = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.ellipse(g, (255, 255, 255, alpha), g.get_rect())
    surf.blit(g, rect.topleft)


def _star(c, ro, ri, n, rot=-math.pi / 2):
    pts = []
    for k in range(2 * n):
        a = rot + k * math.pi / n
        rr = ro if k % 2 == 0 else ri
        pts.append((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr))
    return pts


def _poly(c, R, pts):
    return [(c[0] + x * R, c[1] + y * R) for x, y in pts]


# ------------------------------------------------------------------ shapes
def _draw_xp(s, c, R):
    ro, ri = R * 1.0, R * 0.74
    pygame.draw.polygon(s, (24, 74, 140), _star((c[0], c[1] + R * 0.1), ro, ri, 12))   # bevel
    face = _star(c, ro * 0.95, ri * 0.95, 12)
    _fill_grad(s, face, (98, 206, 240), (38, 156, 212))
    _shine(s, pygame.Rect(c[0] - R * 0.5, c[1] - R * 0.66, R * 0.8, R * 0.42), 55)


def _draw_gold(s, c, R):
    side = (c[0] + R * 0.12, c[1] + R * 0.06)
    pygame.draw.circle(s, (176, 96, 16), side, int(R * 0.92))                # thickness
    _circle_grad(s, (c[0] - R * 0.04, c[1]), R * 0.9, (255, 214, 86), (236, 146, 28))
    pygame.draw.circle(s, (206, 118, 18), (c[0] - R * 0.04, c[1]), int(R * 0.66),
                       max(2, int(R * 0.1)))                                   # raised ring
    _circle_grad(s, (c[0] - R * 0.04, c[1]), R * 0.56, (255, 200, 70), (246, 160, 40))
    pygame.draw.arc(s, (255, 244, 190),
                    pygame.Rect(c[0] - R * 0.76, c[1] - R * 0.78, R * 1.4, R * 1.4),
                    math.radians(100), math.radians(190), max(2, int(R * 0.1)))


def _draw_gems(s, c, R):
    outer = [(c[0] + math.cos(math.radians(-90 + 60 * k)) * R,
              c[1] + math.sin(math.radians(-90 + 60 * k)) * R) for k in range(6)]
    inner = [(c[0] + math.cos(math.radians(-90 + 60 * k)) * R * 0.52,
              c[1] - R * 0.04 + math.sin(math.radians(-90 + 60 * k)) * R * 0.52)
             for k in range(6)]
    # facet shades, clockwise from the top-right edge
    shades = [(150, 240, 80), (92, 204, 52), (54, 160, 36), (62, 170, 40),
              (106, 214, 60), (176, 250, 110)]
    for k in range(6):
        q = [outer[k], outer[(k + 1) % 6], inner[(k + 1) % 6], inner[k]]
        pygame.draw.polygon(s, shades[k], q)
    _fill_grad(s, inner, (170, 250, 100), (96, 210, 54))
    _shine(s, pygame.Rect(c[0] - R * 0.42, c[1] - R * 0.5, R * 0.5, R * 0.3), 120)


def _draw_shards(s, c, R):
    outer = _poly(c, R, [(-0.92, -0.62), (0.92, -0.92), (0.58, 0.92), (-0.5, 0.78)])
    inner = _poly(c, R, [(-0.66, -0.44), (0.68, -0.68), (0.44, 0.68), (-0.36, 0.58)])
    pygame.draw.polygon(s, (120, 46, 196), outer)
    _fill_grad(s, outer[:2] + [inner[1], inner[0]], (236, 180, 255), (210, 140, 255))
    pygame.draw.polygon(s, (186, 100, 246), [outer[0], inner[0], inner[3], outer[3]])
    _fill_grad(s, inner, (214, 132, 255), (128, 48, 214))
    gl = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(gl, (255, 255, 255, 80),
                        _poly(c, R, [(-0.5, -0.4), (0.1, -0.56), (-0.24, 0.5), (-0.36, 0.5)]))
    s.blit(gl, (0, 0))
    pygame.draw.circle(s, (255, 255, 255), (int(c[0] + R * 0.5), int(c[1] - R * 0.5)),
                       max(2, int(R * 0.08)))


def _superellipse(c, rx, ry, p=1.35, n=64):
    pts = []
    for k in range(n):
        a = k * 2 * math.pi / n
        ca, sa = math.cos(a), math.sin(a)
        x = math.copysign(abs(ca) ** (2 / p), ca) * rx
        y = math.copysign(abs(sa) ** (2 / p), sa) * ry
        pts.append((c[0] + x, c[1] + y))
    return pts


def _draw_coins(s, c, R):
    pygame.draw.polygon(s, (180, 96, 16), _superellipse((c[0], c[1] + R * 0.08), R * 0.98,
                                                       R * 0.98))          # bevel
    _fill_grad(s, _superellipse(c, R * 0.98, R * 0.98), (255, 196, 70), (236, 134, 28))
    face = _superellipse(c, R * 0.7, R * 0.7)
    _fill_grad(s, face, (255, 246, 90), (150, 226, 96))                       # yellow -> green
    gl = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(gl, (255, 255, 255, 110),
                        [(c[0] - R * 0.5, c[1]), (c[0], c[1] - R * 0.5),
                         (c[0] + R * 0.08, c[1] - R * 0.3), (c[0] - R * 0.3, c[1] + R * 0.08)])
    s.blit(gl, (0, 0))


def _draw_trophy(s, c, R):
    gold_t, gold_b = (255, 226, 96), (222, 148, 30)
    lw = max(3, int(R * 0.2))
    for d in (-1, 1):                                              # handles
        rect = pygame.Rect(0, 0, R * 0.78, R * 0.82)
        rect.center = (c[0] + d * R * 0.62, c[1] - R * 0.38)
        a0, a1 = (math.radians(70), math.radians(290)) if d < 0 else \
            (math.radians(-110), math.radians(110))
        pygame.draw.arc(s, (230, 160, 40), rect, a0, a1, lw)
    bowl = [(c[0] - R * 0.74, c[1] - R * 0.86), (c[0] + R * 0.74, c[1] - R * 0.86),
            (c[0] + R * 0.66, c[1] - R * 0.36), (c[0] + R * 0.4, c[1] + R * 0.04),
            (c[0] + R * 0.12, c[1] + R * 0.18), (c[0] - R * 0.12, c[1] + R * 0.18),
            (c[0] - R * 0.4, c[1] + R * 0.04), (c[0] - R * 0.66, c[1] - R * 0.36)]
    _fill_grad(s, bowl, gold_t, gold_b)
    stem = [(c[0] - R * 0.12, c[1] + R * 0.16), (c[0] + R * 0.12, c[1] + R * 0.16),
            (c[0] + R * 0.2, c[1] + R * 0.6), (c[0] - R * 0.2, c[1] + R * 0.6)]
    _fill_grad(s, stem, (240, 180, 50), (200, 124, 24))
    base = [(c[0] - R * 0.56, c[1] + R * 0.62), (c[0] + R * 0.56, c[1] + R * 0.62),
            (c[0] + R * 0.64, c[1] + R * 0.94), (c[0] - R * 0.64, c[1] + R * 0.94)]
    _fill_grad(s, base, (250, 200, 70), (210, 132, 26))
    pygame.draw.ellipse(s, (255, 236, 150),
                        pygame.Rect(c[0] - R * 0.7, c[1] - R * 0.94, R * 1.4, R * 0.2))
    _shine(s, pygame.Rect(c[0] - R * 0.5, c[1] - R * 0.72, R * 0.24, R * 0.6), 120)


def _draw_potion(s, c, R):
    bx, by, br = c[0], c[1] + R * 0.24, R * 0.7            # the round flask
    # neck + lip + cork
    neck = pygame.Rect(0, 0, R * 0.42, R * 0.5)
    neck.midbottom = (bx, by - br * 0.82)
    pygame.draw.rect(s, (196, 214, 236), neck)
    lip = pygame.Rect(0, 0, R * 0.58, R * 0.16)
    lip.midbottom = (bx, neck.top + R * 0.08)
    pygame.draw.rect(s, (222, 232, 246), lip, border_radius=int(R * 0.06))
    cork = pygame.Rect(0, 0, R * 0.36, R * 0.26)
    cork.midbottom = (bx, lip.top + R * 0.04)
    pygame.draw.rect(s, (150, 96, 50), cork, border_radius=int(R * 0.06))
    pygame.draw.rect(s, (186, 128, 72), cork.inflate(-R * 0.14, -R * 0.12))
    # glass body, then the brew filling its lower two thirds
    _circle_grad(s, (bx, by), br, (214, 226, 246), (160, 176, 210))
    brew = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    _circle_grad(brew, (bx, by), br * 0.86, (236, 130, 255), (118, 34, 196))
    cut = pygame.Rect(0, 0, s.get_width(), int(by - br * 0.34))
    brew.fill((0, 0, 0, 0), cut)
    s.blit(brew, (0, 0))
    pygame.draw.ellipse(s, (246, 176, 255),
                        pygame.Rect(bx - br * 0.74, by - br * 0.42, br * 1.48, br * 0.2))
    # bubbles
    for ox, oy, rr in ((-0.34, 0.1, 0.08), (0.28, 0.3, 0.06), (0.05, 0.52, 0.05)):
        pygame.draw.circle(s, (250, 214, 255), (int(bx + br * ox), int(by + br * oy)),
                           max(2, int(br * rr)))
    # the level-up arrow
    a = _poly((bx, by + br * 0.12), br, [(0, -0.5), (0.36, -0.06), (0.14, -0.06),
                                          (0.14, 0.4), (-0.14, 0.4), (-0.14, -0.06),
                                          (-0.36, -0.06)])
    pygame.draw.polygon(s, (255, 236, 120), a)
    pygame.draw.polygon(s, (170, 96, 20), a, max(2, int(R * 0.05)))
    _shine(s, pygame.Rect(bx - br * 0.66, by - br * 0.74, br * 0.5, br * 0.62), 120)


DRAW = {"xp": _draw_xp, "gold": _draw_gold, "gems": _draw_gems, "shards": _draw_shards,
        "coins": _draw_coins, "trophy": _draw_trophy, "potion": _draw_potion}


def _outline(surf, width):
    """Surround the drawn shape with a dark outline `width` px thick."""
    mask = pygame.mask.from_surface(surf, 10)
    sil = mask.to_surface(setcolor=OUTLINE + (255,), unsetcolor=(0, 0, 0, 0))
    out = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    steps = 16
    for k in range(steps):
        a = k * 2 * math.pi / steps
        out.blit(sil, (round(math.cos(a) * width), round(math.sin(a) * width)))
    out.blit(surf, (0, 0))
    return out


def get(kind, r):
    """The icon `kind` with radius ~r (pixels), as a cached Surface."""
    r = max(3, int(r))
    key = (kind, r)
    img = _cache.get(key)
    if img is None:
        size = int(r * 2.5) + 2
        R = r * SS
        big = pygame.Surface((size * SS, size * SS), pygame.SRCALPHA)
        DRAW[kind](big, (size * SS / 2, size * SS / 2), R)
        big = _outline(big, max(SS, int(R * 0.09)))
        img = pygame.transform.smoothscale(big, (size, size))
        _cache[key] = img
    return img


def blit(screen, kind, x, y, r):
    img = get(kind, r)
    screen.blit(img, (int(x) - img.get_width() // 2, int(y) - img.get_height() // 2))
