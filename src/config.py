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
This file controls the GLOBAL rules of the game and the AI difficulty.
============================================================================
"""

# ---------------------------------------------------------------------------
# 1. WINDOW & ARENA GEOMETRY
# ---------------------------------------------------------------------------
# The Clash Royale arena is 18 tiles wide and 32 tiles tall. We keep those
# tile counts so the battlefield "feels" the same shape. TILE_SIZE just
# controls how big each tile is drawn on screen (bigger = bigger window).

GAME_VERSION = "0.2.2"  # shown on the menu; bump when you ship a new build

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
HUD_HEIGHT  = 132      # pixels reserved at the bottom for your card hand
TOP_BAR     = 40       # pixels reserved at the top for the timer / score
SIDE_MARGIN = 24       # pixels of empty space on left/right of the arena


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
# 5. AI OPPONENT DIFFICULTY   <<< TUNE THIS FOR FAIR / HARD FIGHTS >>>
# ---------------------------------------------------------------------------
# You correctly pointed out a simple AI can't out-skill a real player, so we
# give it resource & tempo advantages instead of "smarts". Turn these DOWN to
# make the AI easier, UP to make it harder.

AI_ELIXIR_MULT       = 1.5    # AI regenerates elixir this much faster than you
AI_ELIXIR_START_BONUS= 2.0    # extra starting elixir for the AI
AI_REACTION_TIME     = 0.9    # seconds the AI "thinks" before responding to a push
AI_DECISION_INTERVAL = 0.6    # how often (s) the AI re-evaluates what to play
AI_AGGRESSION        = 0.55   # 0 = pure defense, 1 = always pushing
AI_MAX_ELIXIR_HOARD  = 9.0    # AI tries to spend before hitting this much elixir
AI_DEFEND_HP_TRIGGER = 6.5    # AI defends when an enemy troop is within this many
                              #   tiles of one of its towers
AI_SMART_TARGETING   = True   # AI tries to counter your card with a good answer
AI_INTELLIGENCE      = 0      # 0 = basic brain, 1 = smart brain (Master/Insane):
                              #   finisher spells on low towers, bridge pressure,
                              #   support behind tanks, pull placements, better
                              #   counter picks. Set by difficulty presets.

# --- Difficulty presets -----------------------------------------------------
# The pre-match setup screen lets the player pick Easy / Medium / Hard. Picking
# one overwrites the AI_* values above via apply_difficulty(). "Hard" reproduces
# the original tuning. Tweak any number here to taste.
DIFFICULTIES = {
    "Easy": dict(
        AI_ELIXIR_MULT=1.0, AI_ELIXIR_START_BONUS=0.0, AI_REACTION_TIME=2.2,
        AI_DECISION_INTERVAL=1.3, AI_AGGRESSION=0.30, AI_MAX_ELIXIR_HOARD=8.0,
        AI_DEFEND_HP_TRIGGER=5.0, AI_SMART_TARGETING=False),
    "Medium": dict(
        AI_ELIXIR_MULT=1.2, AI_ELIXIR_START_BONUS=1.0, AI_REACTION_TIME=1.4,
        AI_DECISION_INTERVAL=0.9, AI_AGGRESSION=0.45, AI_MAX_ELIXIR_HOARD=8.5,
        AI_DEFEND_HP_TRIGGER=6.0, AI_SMART_TARGETING=True),
    "Hard": dict(   # the original balancing
        AI_ELIXIR_MULT=1.5, AI_ELIXIR_START_BONUS=2.0, AI_REACTION_TIME=0.9,
        AI_DECISION_INTERVAL=0.6, AI_AGGRESSION=0.55, AI_MAX_ELIXIR_HOARD=9.0,
        AI_DEFEND_HP_TRIGGER=6.5, AI_SMART_TARGETING=True, AI_INTELLIGENCE=0),
    "Master": dict(   # smarter brain, only a slight elixir edge
        AI_ELIXIR_MULT=1.2, AI_ELIXIR_START_BONUS=1.0, AI_REACTION_TIME=0.5,
        AI_DECISION_INTERVAL=0.35, AI_AGGRESSION=0.6, AI_MAX_ELIXIR_HOARD=8.5,
        AI_DEFEND_HP_TRIGGER=7.5, AI_SMART_TARGETING=True, AI_INTELLIGENCE=1),
    "Insane": dict(   # smart brain + perfect reactions + big elixir edge
        AI_ELIXIR_MULT=1.6, AI_ELIXIR_START_BONUS=3.0, AI_REACTION_TIME=0.0,
        AI_DECISION_INTERVAL=0.2, AI_AGGRESSION=0.65, AI_MAX_ELIXIR_HOARD=8.5,
        AI_DEFEND_HP_TRIGGER=8.0, AI_SMART_TARGETING=True, AI_INTELLIGENCE=1),
}
DIFFICULTY_DESC = {
    "Easy":   "Fair elixir, slow to react. Good for learning.",
    "Medium": "Small elixir edge, moderate reactions.",
    "Hard":   "Big elixir edge, fast & aggressive (original).",
    "Master": "Smart play, slight elixir edge, 0.5s reactions.",
    "Insane": "Smart play, perfect reactions, huge elixir edge.",
}
DEFAULT_DIFFICULTY = "Hard"


def apply_difficulty(name):
    """Overwrite the module-level AI_* knobs with a difficulty preset."""
    preset = DIFFICULTIES.get(name, DIFFICULTIES[DEFAULT_DIFFICULTY])
    g = globals()
    for k, v in preset.items():
        g[k] = v


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

SHOW_TILE_GRID    = False   # set True to see the tile grid while balancing
SHOW_RANGES       = False   # set True to see attack ranges (debug)


# ---------------------------------------------------------------------------
# 9. DERIVED VALUES  (computed for you -- normally no need to edit)
# ---------------------------------------------------------------------------
ARENA_PX_W = GRID_COLS * TILE_SIZE
ARENA_PX_H = GRID_ROWS * TILE_SIZE
ARENA_X0   = SIDE_MARGIN
ARENA_Y0   = TOP_BAR
WINDOW_W   = ARENA_PX_W + SIDE_MARGIN * 2
WINDOW_H   = TOP_BAR + ARENA_PX_H + HUD_HEIGHT
