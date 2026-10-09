"""
============================================================================
  SPRITES.PY  --  Generate, save & load unit art
============================================================================

On first run (and whenever SPRITE_VERSION changes) this paints one PNG per
card into  assets/sprites/  using the original procedural art in
sprite_art.py. The game then LOADS those PNGs from disk every run.

>>> To use your own art: drop a PNG named <cardkey>.png into assets/sprites/
    (e.g. assets/sprites/knight.png). It is used automatically and never
    overwritten. Card keys are listed in cards.py. Recommended: 128x128 with
    transparency (any square size works - it is scaled to fit).

Multi-unit cards (Archers, Goblins, Skeletons...) get TWO images:
    <key>.png     -> the squad, used for the card in your hand / deck
    <key>__u.png  -> one single unit, used for each troop on the battlefield

In-game size of each unit is controlled by SCALES below.
============================================================================
"""

import os
import json
import pygame

import cards
import sprite_art

_HERE = os.path.dirname(os.path.abspath(__file__))
SPRITE_DIR = os.path.join(os.path.dirname(_HERE), "assets", "sprites")

BASE = sprite_art.BASE  # sprites are painted at 128x128, then scaled to fit

# Bump this whenever the built-in art changes so it regenerates on next run.
# Sprites you add yourself (not in the manifest) are never overwritten.
SPRITE_VERSION = 9

# Main colour of each card. The game uses these to tint effects such as the
# splash (AoE) rings, so they roughly match each card's art.
CARD_COLORS = {
    "skeletons": (225, 225, 210), "skeleton": (225, 225, 210),
    "ice_spirit": (150, 220, 255), "fire_spirit": (255, 120, 40),
    "goblins": (110, 200, 80), "goblin": (110, 200, 80),
    "spear_goblins": (80, 165, 70), "spear_goblin": (80, 165, 70),
    "bats": (150, 110, 190), "skeleton_barrel": (150, 110, 70),
    "knight": (200, 209, 226), "archers": (255, 122, 172),
    "bomber": (95, 95, 105), "valkyrie": (238, 104, 48),
    "mini_pekka": (64, 92, 132), "musketeer": (156, 56, 78),
    "barbarians": (255, 214, 92), "barbarian": (255, 214, 92),
    "elite_barbarians": (110, 126, 160), "wizard": (64, 104, 214),
    "witch": (128, 60, 170), "pekka": (58, 64, 112),
    "prince": (60, 96, 200), "dark_prince": (60, 56, 74),
    "giant_skeleton": (242, 240, 226), "lumberjack": (204, 54, 50),
    "bandit": (170, 90, 210),
    "giant": (232, 120, 50), "hog_rider": (232, 156, 132),
    "royal_giant": (66, 104, 196), "balloon": (214, 54, 54),
    "golem": (132, 126, 146), "golemite": (132, 126, 146),
    "minions": (96, 144, 240), "minion_horde": (96, 144, 240),
    "mega_minion": (70, 90, 190), "baby_dragon": (114, 196, 82),
    "inferno_dragon": (218, 90, 50),
    "dart_goblin": (196, 140, 80), "princess": (250, 128, 180),
    "electro_wizard": (110, 214, 255), "ice_wizard": (150, 206, 240),
    "three_musketeers": (156, 56, 78), "sparky": (255, 226, 96),
    "cannon": (72, 74, 90), "tesla": (110, 214, 255),
    "inferno_tower": (255, 146, 36), "bomb_tower": (160, 152, 140),
    "mortar": (76, 76, 92), "xbow": (182, 120, 62),
    "tombstone": (170, 168, 176), "goblin_hut": (120, 180, 70),
    "barbarian_hut": (180, 70, 50), "furnace": (255, 146, 36),
    "elixir_collector": (226, 84, 222),
    "zap": (110, 214, 255), "the_log": (182, 120, 62),
    "arrows": (215, 215, 215), "fireball": (255, 146, 36),
    "rage": (210, 70, 220), "freeze": (172, 228, 255),
    "poison": (120, 200, 60), "rocket": (230, 70, 60),
    "lightning": (255, 230, 96),
    "skeleton_army": (225, 225, 210), "guards": (196, 70, 60),
    "zappies": (110, 214, 255), "hunter": (110, 120, 76),
    "executioner": (210, 216, 230), "bowler": (150, 120, 176),
    "magic_archer": (110, 240, 210), "night_witch": (200, 120, 255),
    "flying_machine": (182, 120, 62), "electro_dragon": (110, 214, 255),
    "lava_hound": (255, 120, 40), "lava_pup": (255, 146, 36),
    "mega_knight": (70, 76, 104), "goblin_giant": (126, 206, 72),
    "cannon_cart": (120, 150, 210), "ice_golem": (176, 222, 248),
    "miner": (240, 190, 50), "battle_ram": (182, 120, 62),
    "wall_breakers": (228, 64, 58), "bat": (150, 110, 190),
    "goblin_barrel": (126, 206, 72), "barbarian_barrel": (255, 214, 92),
    "snowball": (230, 244, 255), "earthquake": (150, 100, 60),
    "tornado": (200, 210, 230), "graveyard": (170, 120, 200),
    "electro_spirit": (110, 214, 255), "electro_giant": (110, 214, 255),
    "battle_healer": (140, 255, 160),
    "elixir_golem": (232, 104, 230), "elixir_golemite": (232, 104, 230),
    "elixir_blob": (232, 104, 230),
    "mighty_miner": (255, 140, 40), "archer_queen": (110, 56, 150),
    "little_prince": (70, 120, 230), "golden_knight": (255, 206, 72),
    "skeleton_king": (120, 255, 140), "monk": (232, 120, 52),
    "goblinstein": (110, 214, 255), "boss_bandit": (255, 202, 58),
    "royal_guardian": (70, 110, 210), "goblin_monster": (110, 180, 96),
}

# ---------------------------------------------------------------------------
# In-game render size of each unit, as a multiple of the standard unit size
# (1.5 tiles for troops, 2.6 tiles for buildings). Tweak to taste.
# ---------------------------------------------------------------------------
TROOP_SCALE = 1.3          # default for any troop not listed below
BUILDING_SCALE = 1.0       # default for buildings
SCALES = {
    # small fry
    "skeleton": 1.05, "skeletons": 1.05, "skeleton_army": 1.05,
    "goblin": 1.1, "goblins": 1.1, "spear_goblin": 1.1, "spear_goblins": 1.1,
    "dart_goblin": 1.15, "bat": 1.0, "bats": 1.0, "lava_pup": 1.05,
    "ice_spirit": 1.05, "fire_spirit": 1.05, "electro_spirit": 1.05,
    "wall_breakers": 1.1, "guards": 1.15, "zappies": 1.15, "elixir_blob": 1.0,
    "minions": 1.15, "minion_horde": 1.15, "bomber": 1.15,
    # mounted / vehicles (sprite is wider than tall)
    "hog_rider": 1.6, "prince": 1.6, "dark_prince": 1.55, "battle_ram": 1.6,
    "sparky": 1.55, "cannon_cart": 1.45, "flying_machine": 1.45,
    "balloon": 1.6, "skeleton_barrel": 1.35,
    # air
    "mega_minion": 1.35, "baby_dragon": 1.45, "inferno_dragon": 1.45,
    "electro_dragon": 1.5, "lava_hound": 1.85,
    # heavies
    "giant": 1.8, "royal_giant": 1.8, "pekka": 1.8, "mega_knight": 1.85,
    "golem": 1.95, "golemite": 1.35, "giant_skeleton": 1.8,
    "goblin_giant": 1.8, "electro_giant": 1.85, "bowler": 1.65,
    "elixir_golem": 1.55, "elixir_golemite": 1.25, "ice_golem": 1.4,
    "goblin_monster": 1.6, "hunter": 1.4, "executioner": 1.45,
    # champions
    "mighty_miner": 1.5, "archer_queen": 1.45, "little_prince": 1.3,
    "golden_knight": 1.45, "skeleton_king": 1.75, "monk": 1.5,
    "goblinstein": 1.35, "boss_bandit": 1.45,
}


def render_scale(key):
    """In-game size multiplier for a unit sprite."""
    if key in SCALES:
        return SCALES[key]
    card = cards.CARDS.get(key)
    if card is not None and card.category == "building":
        return BUILDING_SCALE
    return TROOP_SCALE


def _build_sprite(card, force_count=None):
    """Paint a card. force_count=1 paints a single unit of a squad card."""
    unit = sprite_art.render_unit(card.key, card)
    count = force_count if force_count is not None else card.count
    if card.category == "troop" and count > 1:
        return sprite_art.render_squad(unit, count)
    return unit


_cache = {}
_raw_cache = {}


def _manifest_path():
    return os.path.join(SPRITE_DIR, ".spritegen.json")


def ensure_sprites():
    """Generate built-in sprite PNGs.

    Rules:
      * missing files are always created;
      * files the game generated (tracked in .spritegen.json) are refreshed
        when SPRITE_VERSION changes, so art improvements show up;
      * any PNG you added yourself (not in the manifest) is NEVER overwritten.
        To keep a custom sprite forever, remove its key from .spritegen.json.
    """
    os.makedirs(SPRITE_DIR, exist_ok=True)
    if not pygame.font.get_init():
        pygame.font.init()

    mp = _manifest_path()
    manifest_missing = not os.path.exists(mp)
    man = {}
    if not manifest_missing:
        try:
            with open(mp) as f:
                man = json.load(f)
        except Exception:
            man = {}
    old_version = man.get("version")
    generated = set(man.get("generated", []))

    created = 0
    now_generated = set()
    jobs = []
    for key, card in cards.CARDS.items():
        jobs.append((key, card, None))
        if card.category == "troop" and card.count > 1:
            jobs.append((key + "__u", card, 1))
    for name, card, fcount in jobs:
        path = os.path.join(SPRITE_DIR, name + ".png")
        exists = os.path.exists(path)
        if not exists:
            regen = True
        elif manifest_missing:
            regen = True
        elif old_version != SPRITE_VERSION and name in generated:
            regen = True
        else:
            regen = False
        if regen:
            pygame.image.save(_build_sprite(card, force_count=fcount), path)
            created += 1
            now_generated.add(name)
        elif exists and (name in generated or manifest_missing):
            now_generated.add(name)

    try:
        with open(mp, "w") as f:
            json.dump({"version": SPRITE_VERSION,
                       "generated": sorted(now_generated)}, f, indent=0)
    except Exception:
        pass
    _cache.clear()
    _raw_cache.clear()
    return created


def _load_raw(key):
    if key in _raw_cache:
        return _raw_cache[key]
    base = key[:-3] if key.endswith("__u") else key
    fcount = 1 if key.endswith("__u") else None
    path = os.path.join(SPRITE_DIR, key + ".png")
    card = cards.CARDS.get(base, cards.CARDS["skeleton"])
    surf = None
    if os.path.exists(path):
        try:
            surf = pygame.image.load(path)
            try:
                surf = surf.convert_alpha()
            except pygame.error:
                pass                      # no display yet - use as loaded
        except Exception:
            surf = None
    if surf is None:
        surf = _build_sprite(card, force_count=fcount)
    _raw_cache[key] = surf
    return surf


def unit_sprite_key(card_key):
    """Sprite name for ONE deployed unit of a card (single figure for
    multi-count cards; the plain card art otherwise)."""
    c = cards.CARDS.get(card_key)
    if c is not None and c.category == "troop" and c.count > 1:
        return card_key + "__u"
    return card_key


def get_sprite(key, size):
    """Return the sprite for `key` scaled to (size x size)."""
    size = max(1, int(size))
    ck = (key, size)
    if ck in _cache:
        return _cache[ck]
    raw = _load_raw(key)
    scaled = pygame.transform.smoothscale(raw, (size, size))
    _cache[ck] = scaled
    return scaled
