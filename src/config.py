"""
============================================================================
  CONFIG.PY  --  Your balancing & playtesting control panel
============================================================================

This is the file to edit if you want to change how the game plays WITHOUT
touching the engine code. Everything here is a "knob" you can turn.

Rules of thumb:
  * Numbers are safe to change. Try small changes and re-run the game.
  * Times are in SECONDS. Speeds are in TILES PER SECOND.
  * "Hit speed" is SECONDS BETWEEN ATTACKS (lower = attacks faster).
  * Distances/ranges are measured in TILES (the arena is a grid of tiles).
  * If something breaks, you probably deleted a comma or a bracket. Undo it.

Card-specific stats (hp, damage, elixir cost of each card) live in `cards.py`.
This file controls the GLOBAL rules of the game and the AI settings.
============================================================================
"""

# ---------------------------------------------------------------------------
# 1. WINDOW & ARENA GEOMETRY
# ---------------------------------------------------------------------------
# The Clash Royale arena is 18 tiles wide and 32 tiles tall. We keep those
# tile counts so the battlefield "feels" the same shape. TILE_SIZE just
# controls how big each tile is drawn on screen (bigger = bigger window).

GAME_VERSION = "1.0.0"  # shown on the menu; bump when you ship a new build

TILE_SIZE   = 18       # pixels per tile. Lower this if the window is too tall.
GRID_COLS   = 18       # arena width  in tiles (Clash Royale standard)
GRID_ROWS   = 32       # arena height in tiles (Clash Royale standard)

FPS         = 60       # frames per second (game smoothness / speed cap)

# The river sits across the middle of the arena. These two rows are water.
RIVER_ROWS  = (15, 16)  # the two middle rows that make up the river

# The two bridges let GROUND troops cross the river. Air troops fly over
# anywhere. These are the tile columns where each bridge is centered.
BRIDGE_COLS = (3, 14)   # left bridge center col, right bridge center col

# How wide the on-screen side/bottom panels are (HUD area for your cards).
HUD_HEIGHT  = 128      # pixels reserved at the bottom for your card hand
TOP_BAR     = 40       # pixels reserved at the top for the timer / score
ARENA_BORDER_X = 48    # decorative (non-placeable) scenery left/right of the
ARENA_BORDER_Y = 28    #   arena and above/below it: stone rim, trees, bushes,
                       #   banners. Purely visual. (window = 420 x 800)
ARENA_BORDER = ARENA_BORDER_Y
SIDE_MARGIN = ARENA_BORDER_X


# ---------------------------------------------------------------------------
# 2. ELIXIR ECONOMY   (the core resource of the game)
# ---------------------------------------------------------------------------
ELIXIR_MAX          = 10.0   # maximum elixir you can bank
ELIXIR_START        = 5.0    # elixir both players start a match with
ELIXIR_PER_SECOND   = 1.0 / 2.8   # base regen: 1 elixir every 2.8s (CR "1x")

# During the match the regen speed ramps up, just like Clash Royale:
DOUBLE_ELIXIR_AT    = 60.0   # seconds REMAINING when 2x elixir kicks in
DOUBLE_ELIXIR_MULT  = 2.0    # regen multiplier during double elixir
TRIPLE_ELIXIR_MULT  = 3.0    # regen multiplier during overtime (3x)


# ---------------------------------------------------------------------------
# 3. MATCH TIMING & VICTORY RULES
# ---------------------------------------------------------------------------
MATCH_LENGTH        = 180.0  # regulation time in seconds (3:00)
OVERTIME_LENGTH     = 120.0  # sudden-death overtime in seconds (2:00)
# In regulation, most-crowns wins; tie -> overtime. In overtime the FIRST
# tower destroyed wins instantly (sudden death). If overtime also ties, the
# tower with the lowest remaining HP% loses (see engine).


# ---------------------------------------------------------------------------
# 4. TOWERS  (the things you're trying to destroy / defend)
# ---------------------------------------------------------------------------
# Each side has 2 Princess Towers (left/right) and 1 King Tower (center back).
# Destroying a Princess Tower = 1 crown. Destroying the King Tower = instant
# win (3 crowns). The King Tower "wakes up" and fires once one of its
# Princess Towers is destroyed OR once it is itself hit.

PRINCESS_TOWER_HP     = 1400
PRINCESS_TOWER_DMG    = 50
PRINCESS_TOWER_RANGE  = 7.5    # tiles
PRINCESS_TOWER_HITSPD = 0.8    # seconds between shots

KING_TOWER_HP         = 2400
KING_TOWER_DMG        = 50
KING_TOWER_RANGE      = 7.0    # tiles
KING_TOWER_HITSPD     = 1.0    # seconds between shots
KING_ACTIVATES_ALLIES = True   # King wakes when a princess tower falls

# Tower tile positions are computed from the grid in engine/arena.py so they
# always mirror correctly. Change PRINCESS_TOWER_INSET/KING_INSET to move them.
PRINCESS_TOWER_INSET_X = 3     # cols in from the left/right edge
PRINCESS_TOWER_INSET_Y = 6     # rows in from the top/bottom edge
KING_INSET_Y           = 2     # rows in from the top/bottom edge for the King


# ---------------------------------------------------------------------------
# 5. AI OPPONENT   <<< INTELLIGENCE + ELIXIR, SET SEPARATELY >>>
# ---------------------------------------------------------------------------
# Two independent dials, both picked on the Battle Setup screen:
#
#   * AI INTELLIGENCE (levels 1-5, AI_LEVELS below): how WELL it plays -
#     reaction speed, card choice, placement, spell use, elixir counting...
#   * AI ELIXIR BOOST (0.5x - 2.0x slider): how much elixir it gets. 1.0x is
#     a perfectly even fight. Starting elixir scales too:
#     start bonus = (boost - 1) * AI_START_BONUS_PER_MULT.

AI_ELIXIR_MULT        = 1.0    # current boost (set by the slider)
AI_ELIXIR_MULT_MIN    = 0.5
AI_ELIXIR_MULT_MAX    = 2.0
AI_ELIXIR_MULT_STEP   = 0.05   # slider snaps to this step
AI_START_BONUS_PER_MULT = 2.0  # 2.0x boost -> +2 starting elixir, 0.5x -> -1
AI_ELIXIR_START_BONUS = 0.0    # derived from the boost by apply_ai_settings()
AI_LEVEL              = 3      # current intelligence level (1-5)

# What each intelligence level can do. Every level unlocks the skills of the
# levels below it. Numbers:
#   reaction   - seconds before it responds to a push
#   interval   - seconds between decisions
#   mistakes   - chance a decision is a sloppy/random one
#   jitter     - tiles of random error in where it places cards
#   spell_need - how much elixir value a damage spell must hit, relative to
#                its own cost, before the AI casts it (lower = sharper)
#   defend_at  - it defends when your troops get this close to its towers
AI_LEVELS = {
    1: dict(name="Novice", reaction=2.2, interval=1.4, mistakes=0.35,
            jitter=2.0, spell_need=2.2, defend_at=5.0,
            desc="Slow, sloppy, plays mostly at random."),
    2: dict(name="Casual", reaction=1.4, interval=0.9, mistakes=0.18,
            jitter=1.2, spell_need=1.7, defend_at=6.0,
            desc="Basic counters & spells, simple pushes."),
    3: dict(name="Skilled", reaction=0.9, interval=0.6, mistakes=0.07,
            jitter=0.5, spell_need=1.35, defend_at=6.5,
            desc="Smart counters & placement, support pushes."),
    4: dict(name="Expert", reaction=0.5, interval=0.35, mistakes=0.03,
            jitter=0.2, spell_need=1.15, defend_at=7.5,
            desc="Counts elixir, punishes, counter-pushes."),
    5: dict(name="Master", reaction=0.25, interval=0.2, mistakes=0.0,
            jitter=0.0, spell_need=1.0, defend_at=8.0,
            desc="Everything: exact elixir count, card tracking."),
}
AI_DEFAULT_LEVEL = 3
AI_DEFAULT_ELIXIR = 1.0


def apply_ai_settings(level, elixir_mult):
    """Set the AI's intelligence level and elixir boost for the next match."""
    g = globals()
    g["AI_LEVEL"] = level if level in AI_LEVELS else AI_DEFAULT_LEVEL
    m = min(max(float(elixir_mult), AI_ELIXIR_MULT_MIN), AI_ELIXIR_MULT_MAX)
    g["AI_ELIXIR_MULT"] = round(m, 2)
    g["AI_ELIXIR_START_BONUS"] = round((m - 1.0) * AI_START_BONUS_PER_MULT, 2)


# ---------------------------------------------------------------------------
# 6. DECK & HAND RULES
# ---------------------------------------------------------------------------
DECK_SIZE           = 8      # cards in a deck (Clash Royale standard)
HAND_SIZE           = 4      # cards visible/playable at once
CARD_CYCLE          = True   # played cards go to the back of the queue


# ---------------------------------------------------------------------------
# 7. GENERAL COMBAT TUNING (global multipliers, applied on top of cards.py)
# ---------------------------------------------------------------------------
GLOBAL_DAMAGE_MULT   = 1.0   # scale ALL troop damage (1.1 = +10% everywhere)
GLOBAL_HP_MULT       = 1.0   # scale ALL troop hp
GLOBAL_SPEED_MULT    = 1.0   # scale ALL troop move speed
DEPLOY_TIME          = 1.0   # seconds a troop stands still after being placed
# Melee wind-up: after engaging a NEW target a melee unit waits this fraction
# of its hit speed before the first hit lands (a card's `first_hit` overrides
# it with an exact number of seconds). Never shorter than MELEE_FIRST_HIT_MIN.
MELEE_FIRST_HIT_FRAC = 0.5
MELEE_FIRST_HIT_MIN  = 0.3
PROJECTILE_SPEED     = 9.0   # tiles/sec for ranged shots (visual + timing)

# Inferno-style ramping attacks (Inferno Tower / Inferno Dragon).
# Damage multiplier grows by INFERNO_RAMP_RATE per second of continuous
# attacking, capped at INFERNO_MAX_MULT. Lower either to nerf infernos.
INFERNO_RAMP_RATE    = 1.0   # was 1.6 (nerfed)
INFERNO_MAX_MULT     = 5.0   # was 8.0 (nerfed)

# Spell "cast delay": how long after a spell is played before it detonates.
# During this window a target marker is shown (red = enemy, blue = you) so you
# can see a spell coming instead of troops just vanishing. Per-spell overrides
# below; anything not listed uses SPELL_CAST_DELAY.
SPELL_CAST_DELAY     = 0.8
SPELL_CAST_TIMES     = {
    "zap": 0.35, "the_log": 0.2, "arrows": 0.9, "fireball": 0.7,
    "rage": 0.35, "freeze": 0.65, "poison": 0.6, "rocket": 1.0, "lightning": 0.6,
}

# Thrown spells fly from the caster's KING TOWER to the target, so you can see
# where they come from (and Goblin Barrel goblins don't just appear). Values
# are flight speeds in tiles/second; the spell lands when it arrives (never
# sooner than its SPELL_CAST_TIMES entry above).
SPELL_FLIGHT_SPEED   = {
    "fireball": 16.0, "arrows": 19.0, "rocket": 12.0,
    "goblin_barrel": 15.0, "snowball": 17.0,
}

# Named movement speeds (tiles/second). Cards reference these by name so you
# can retune "fast" globally. Clash Royale speed tiers, roughly.
SPEED_SLOW      = 1.1
SPEED_MEDIUM    = 1.7
SPEED_FAST      = 2.3
SPEED_VERY_FAST = 2.9


# ---------------------------------------------------------------------------
# 8. COLORS & VISUALS  (cosmetic only)
# ---------------------------------------------------------------------------
COLOR_BG          = (30, 34, 46)
COLOR_ARENA       = (86, 152, 88)     # grass green
COLOR_ARENA_ALT   = (95, 164, 96)     # checker stripe
COLOR_RIVER       = (70, 150, 200)
COLOR_BRIDGE      = (168, 126, 78)
COLOR_TEAM_PLAYER = (70, 130, 220)    # your units are blue-ish
COLOR_TEAM_ENEMY  = (220, 80, 80)     # enemy units are red-ish
COLOR_TEXT        = (240, 240, 240)
COLOR_ELIXIR      = (200, 70, 190)
COLOR_HUD_BG      = (26, 30, 38)
COLOR_BUTTON      = (60, 90, 140)
COLOR_BUTTON_HOVER= (85, 120, 180)
COLOR_HP_GOOD     = (90, 200, 90)
COLOR_HP_BAD      = (200, 70, 70)

# Sound (toggle in-game with the Music / Sound chips on the main menu, or the
# M and N keys anywhere)
MUSIC_VOLUME      = 0.45    # 0.0 - 1.0
SFX_VOLUME        = 0.75    # 0.0 - 1.0

SHOW_TILE_GRID    = False   # set True to see the tile grid while balancing
SHOW_RANGES       = False   # set True to see attack ranges (debug)


# ---------------------------------------------------------------------------
# 9. DERIVED VALUES  (computed for you -- normally no need to edit)
# ---------------------------------------------------------------------------
ARENA_PX_W = GRID_COLS * TILE_SIZE
ARENA_PX_H = GRID_ROWS * TILE_SIZE
ARENA_X0   = ARENA_BORDER_X
ARENA_Y0   = TOP_BAR + ARENA_BORDER_Y
HUD_Y      = ARENA_Y0 + ARENA_PX_H + ARENA_BORDER_Y   # top of the card hand
WINDOW_W   = ARENA_PX_W + ARENA_BORDER_X * 2
WINDOW_H   = HUD_Y + HUD_HEIGHT
