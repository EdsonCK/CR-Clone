"""
============================================================================
  UI.PY  --  Shared drawing helpers: outlined text, gradients, buttons
============================================================================
"""

import pygame

import config as cfg


def dk_c(c, n=40):
    return tuple(max(0, v - n) for v in c)


def lt_c(c, n=40):
    return tuple(min(255, v + n) for v in c)


def tile_to_px(x, y):
    return (cfg.ARENA_X0 + x * cfg.TILE_SIZE, cfg.ARENA_Y0 + y * cfg.TILE_SIZE)


def px_to_tile(px, py):
    return ((px - cfg.ARENA_X0) / cfg.TILE_SIZE, (py - cfg.ARENA_Y0) / cfg.TILE_SIZE)


WHITE = (255, 255, 255)
_TEXT_CACHE = {}


def render_text(font, text, color=WHITE, outline=True, outline_col=(0, 0, 0)):
    """Text surface; big text gets a thin black outline (cached)."""
    key = (id(font), text, color, outline, outline_col)
    surf = _TEXT_CACHE.get(key)
    if surf is not None:
        return surf
    base = font.render(text, True, color)
    if not outline:
        surf = base
    else:
        edge = font.render(text, True, outline_col)
        w, h = base.get_width() + 2, base.get_height() + 2
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for dx, dy in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0),
                       (-1, 1), (0, 1), (1, 1)):
            surf.blit(edge, (1 + dx, 1 + dy))
        surf.blit(base, (1, 1))
    if len(_TEXT_CACHE) > 4000:
        _TEXT_CACHE.clear()
    _TEXT_CACHE[key] = surf
    return surf


_GRAD_CACHE = {}


def grad_rect(w, h, top, bottom, radius=10):
    """Rounded rectangle with a vertical gradient (cached surface)."""
    key = (w, h, top, bottom, radius)
    surf = _GRAD_CACHE.get(key)
    if surf is None:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h):
            t = y / max(1, h - 1)
            c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
            pygame.draw.line(surf, c, (0, y), (w, y))
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=radius)
        surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        if len(_GRAD_CACHE) > 400:
            _GRAD_CACHE.clear()
        _GRAD_CACHE[key] = surf
    return surf


BUTTON_STYLES = {
    #           top              bottom           border
    "primary": ((88, 132, 214), (46, 78, 150), (24, 34, 66)),
    "go":      ((108, 200, 96), (52, 138, 58), (22, 60, 26)),
    "gold":    ((250, 206, 92), (196, 140, 40), (90, 60, 14)),
    "dark":    ((70, 78, 100), (42, 48, 64), (16, 18, 26)),
    "danger":  ((226, 98, 88), (160, 52, 48), (70, 20, 18)),
}


class Button:
    def __init__(self, rect, label, cb, style="primary", chunky=False, icon=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.cb = cb
        self.style = style
        self.enabled = True
        self.chunky = chunky          # the home screen's thick 3D buttons
        self.icon = icon              # chunky: fn(surf, cx, cy, size) drawn left of the label

    def _draw_chunky(self, surf, font, top, bot, border, hover, pressed):
        """A thick, glossy 3D button: the face sits on a darker 'side' that
        shows below it and sinks into it when pressed."""
        depth = max(4, self.rect.h // 9)
        rad = min(16, self.rect.h // 3)
        r = self.rect
        side = pygame.Rect(r.x, r.y + depth, r.w, r.h - depth)
        face = pygame.Rect(r.x, r.y + (depth - 1 if pressed else 0), r.w, r.h - depth)
        pygame.draw.rect(surf, (6, 8, 14), side.move(0, 4), border_radius=rad)     # shadow
        pygame.draw.rect(surf, dk_c(bot, 70), side, border_radius=rad)            # thickness
        pygame.draw.rect(surf, border, side, 2, border_radius=rad)
        surf.blit(grad_rect(face.w, face.h, top, bot, rad), face.topleft)
        gl = pygame.Surface((face.w - 10, max(2, face.h // 2 - 2)), pygame.SRCALPHA)
        pygame.draw.rect(gl, (255, 255, 255, 46), gl.get_rect(), border_radius=rad - 3)
        surf.blit(gl, (face.x + 5, face.y + 3))
        pygame.draw.rect(surf, lt_c(top, 46), face.inflate(-6, -6), 1, border_radius=rad - 3)
        pygame.draw.rect(surf, (255, 230, 130) if hover else border, face, 2, border_radius=rad)
        txt = render_text(font, self.label, WHITE if self.enabled else (190, 190, 190))
        x = face.centerx - txt.get_width() // 2
        if self.icon:
            isz = int(face.h * 0.62)
            x += isz // 2 + 4
            self.icon(surf, x - isz // 2 - 8, face.centery, isz)
        surf.blit(txt, (x, face.centery - txt.get_height() // 2))

    def draw(self, surf, font):
        mouse = pygame.mouse.get_pos()
        hover = self.rect.collidepoint(mouse) and self.enabled
        pressed = hover and pygame.mouse.get_pressed()[0]
        top, bot, border = BUTTON_STYLES.get(self.style, BUTTON_STYLES["primary"])
        if not self.enabled:
            top, bot = (80, 82, 90), (56, 58, 66)
        elif hover:
            top, bot = lt_c(top, 18), lt_c(bot, 14)
        if self.chunky:
            self._draw_chunky(surf, font, top, bot, border, hover, pressed)
            return
        r = self.rect.move(0, 2 if pressed else 0)
        # drop shadow (shorter when pressed)
        pygame.draw.rect(surf, (10, 12, 18), self.rect.move(0, 4), border_radius=11)
        surf.blit(grad_rect(r.w, r.h, top, bot, 11), r.topleft)
        # glossy top highlight
        hl = pygame.Rect(r.x + 4, r.y + 3, r.w - 8, max(2, r.h // 3))
        gl = pygame.Surface(hl.size, pygame.SRCALPHA)
        pygame.draw.rect(gl, (255, 255, 255, 38), gl.get_rect(), border_radius=8)
        surf.blit(gl, hl.topleft)
        pygame.draw.rect(surf, (255, 222, 110) if hover else border, r,
                         2, border_radius=11)
        txt = render_text(font, self.label, WHITE if self.enabled else (190, 190, 190))
        surf.blit(txt, (r.centerx - txt.get_width() // 2,
                        r.centery - txt.get_height() // 2))

    click_sound = None      # set by Game: plays the UI click

    def click(self, pos):
        if self.enabled and self.rect.collidepoint(pos):
            if Button.click_sound:
                Button.click_sound()
            self.cb()
            return True
        return False
