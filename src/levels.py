"""
============================================================================
  LEVELS.PY  --  Set-piece challenge levels ("Levels" on the main menu)
============================================================================

In a level the opponent has NO towers. Scripted waves of enemies march at
yours and the only goal is to survive them all with your King Tower
standing. Stars: 3 = no tower lost, 2 = one Princess Tower lost,
1 = both lost (King Tower falling = defeat).

Unit levels
-----------
Card stats in cards.py count as LEVEL 11 (like a tournament-standard card in
Clash Royale). Every level above that adds +10% hp and damage (compounding),
every level below takes 10% off:

    level 11 = x1.00   level 12 = x1.10   level 13 = x1.21   level 14 = x1.33

A spawn can also carry an extra multiplier (`mult`) on top - bosses use it.

Adding a level
--------------
Append a Level(...) to LEVELS. Each Wave lists Spawn entries:

    Spawn(card_key, at=seconds_into_wave, lane="left"|"right"|"mid",
          level=None (wave's level), mult=1.0, place="field"|"back"|"front"|
          "tower")

  place: "field" = out of the lane's crypt gate, "back" = from just inside
         the gate, "front" = near the river (buildings), "tower" = on YOUR
         Princess Tower of that lane (spells like Graveyard).
============================================================================
"""

from dataclasses import dataclass, field
from typing import List, Optional

import cards
from engine import PLAYER, ENEMY, RIVER_TOP

LEVEL_BASE = 11          # the level the stats in cards.py represent
LEVEL_STEP = 0.10        # +10% hp & damage per level


def level_mult(level):
    return (1.0 + LEVEL_STEP) ** (level - LEVEL_BASE)


LANE_X = {"left": 3.5, "right": 14.5, "mid": 9.0}
GATE_Y = {"left": 6.0, "right": 6.0, "mid": 3.0}   # crypt gates (drawn by game.py)
PLACE_Y = {"front": RIVER_TOP - 3.5}                # buildings: near the river


@dataclass
class Spawn:
    key: str
    at: float = 0.0
    lane: str = "left"
    level: Optional[int] = None
    mult: float = 1.0
    place: str = "field"


@dataclass
class Wave:
    name: str
    spawns: List[Spawn]
    level: int = LEVEL_BASE
    bonus_elixir: float = 0.0       # given to the player when the wave starts
    boss: bool = False
    timeout: float = 40.0           # next wave comes anyway after this long


@dataclass
class Level:
    key: str
    name: str
    subtitle: str
    desc: str
    icon: str                       # card key used as the level's picture
    waves: List[Wave]
    start_elixir: float = 6.0
    prep_first: float = 8.0         # seconds before wave 1
    prep: float = 7.0               # seconds between waves
    locked: bool = False


# ===========================================================================
#  THE LEVELS
# ===========================================================================
LEVELS = [
    Level(
        "bone_crypt", "The Bone Crypt", "Level 1",
        "The dead are restless. Hold the line against every kind of "
        "skeleton the crypt can raise - and whatever wakes at the bottom.",
        "giant_skeleton",
        waves=[
            Wave("Rattling Bones", level=11, spawns=[
                Spawn("skeletons", 0, "left"),
                Spawn("skeletons", 5, "right"),
                Spawn("skeletons", 10, "left"),
            ]),
            Wave("Shield Wall", level=11, spawns=[
                Spawn("guards", 0, "left"),
                Spawn("bomber", 2, "left", place="back"),
                Spawn("skeletons", 6, "right"),
            ]),
            Wave("The Horde", level=11, spawns=[
                Spawn("skeleton_army", 0, "right"),
                Spawn("bomber", 4, "right", place="back"),
            ]),
            Wave("Breach!", level=11, spawns=[
                Spawn("wall_breakers", 0, "left"),
                Spawn("wall_breakers", 4, "right"),
                Spawn("skeleton_barrel", 8, "left", place="back"),
            ]),
            Wave("Grave Robbers", level=11, spawns=[
                Spawn("tombstone", 0, "mid", place="front"),
                Spawn("graveyard", 5, "right", place="tower"),
                Spawn("guards", 9, "left"),
            ]),
            Wave("The Bone King", level=12, spawns=[
                Spawn("skeleton_king", 0, "left"),
                Spawn("bomber", 3, "left", place="back"),
                Spawn("skeleton_army", 7, "right"),
            ]),
            Wave("Twin Titans", level=11, boss=True, bonus_elixir=5, timeout=90,
                 spawns=[
                     Spawn("giant_skeleton", 0, "left", mult=2.0),
                     Spawn("giant_skeleton", 10, "right", mult=2.0),
                 ]),
        ]),
    # placeholders so the series shows on the Levels screen
    Level("coming_2", "???", "Level 2", "Coming soon.", "goblin_giant", [], locked=True),
    Level("coming_3", "???", "Level 3", "Coming soon.", "pekka", [], locked=True),
]
LEVELS_BY_KEY = {lv.key: lv for lv in LEVELS}


# ===========================================================================
#  RUNNING A LEVEL
# ===========================================================================
class LevelRun:
    """Drives the waves of one level inside a Match (opponent = ENEMY)."""

    def __init__(self, match, level):
        self.m = match
        self.level = level
        self.wave_idx = -1
        self.state = "prep"         # prep -> wave -> prep -> ... -> won
        self.timer = level.prep_first
        self.wave_t = 0.0
        self.pending = []
        self.banner = None          # (title, subtitle, time_shown)
        self.towers_lost = 0
        match.elixir[PLAYER] = level.start_elixir
        self._show("Defend your towers!", "%d waves" % len(level.waves))

    # ---- info for the HUD ----
    @property
    def wave_number(self):
        return max(0, self.wave_idx + 1)

    @property
    def total_waves(self):
        return len(self.level.waves)

    def next_wave_in(self):
        return self.timer if self.state == "prep" else None

    def current_wave(self):
        if 0 <= self.wave_idx < len(self.level.waves):
            return self.level.waves[self.wave_idx]
        return None

    def stars(self):
        lost = sum(1 for s in ("left", "right")
                   if not self.m.towers[(PLAYER, s)].alive)
        return max(1, 3 - lost)

    def _show(self, title, sub=""):
        self.banner = (title, sub, 0.0)

    # ---- per frame ----
    def update(self, dt):
        m = self.m
        if m.finished:
            return
        if self.banner:
            t, s, age = self.banner
            self.banner = (t, s, age + dt) if age < 3.0 else None
        if self.state == "prep":
            self.timer -= dt
            if self.timer <= 0:
                self._start_wave(self.wave_idx + 1)
        elif self.state == "wave":
            self.wave_t += dt
            while self.pending and self.pending[0].at <= self.wave_t:
                self._spawn(self.pending.pop(0))
            wave = self.current_wave()
            cleared = (not self.pending and not self._enemies_alive()
                       and m.towers[(PLAYER, "king")].alive)
            if cleared or self.wave_t >= wave.timeout:
                if self.wave_idx + 1 >= len(self.level.waves):
                    if cleared:
                        self.state = "won"
                        m.finished = True
                        m.winner = PLAYER
                else:
                    self.state = "prep"
                    self.timer = self.level.prep
                    nxt = self.level.waves[self.wave_idx + 1]
                    if nxt.boss:
                        self._show("Something stirs...", "Boss wave next")

    def _enemies_alive(self):
        m = self.m
        if any(e.team == ENEMY and e.alive and not e.is_tower for e in m.entities):
            return True
        return any(fx.team == ENEMY and fx.kind in ("incoming", "graveyard")
                   for fx in m.effects)

    def _start_wave(self, idx):
        wave = self.level.waves[idx]
        self.wave_idx = idx
        self.state = "wave"
        self.wave_t = 0.0
        self.pending = sorted(wave.spawns, key=lambda s: s.at)
        if wave.bonus_elixir:
            self.m.add_elixir(PLAYER, wave.bonus_elixir)
        title = ("BOSS: " if wave.boss else "Wave %d: " % (idx + 1)) + wave.name
        sub = "units level %d" % wave.level if not wave.boss else "double health & damage"
        if wave.bonus_elixir:
            sub += "   +%d elixir" % wave.bonus_elixir
        self._show(title, sub)
        self.m.emit("wave", "boss" if wave.boss else "wave", 9.0, 8.0, ENEMY)

    def _spawn(self, sp):
        m = self.m
        wave = self.current_wave()
        lv = sp.level if sp.level is not None else wave.level
        mult = level_mult(lv) * sp.mult
        x = LANE_X.get(sp.lane, 9.0)
        c = cards.CARDS[sp.key]
        if sp.place == "tower":
            side = "left" if sp.lane == "left" else "right"
            tw = m.towers[(PLAYER, side)]
            if not tw.alive:
                tw = m.towers[(PLAYER, "king")]
            x, y = tw.x, tw.y
        elif sp.place in PLACE_Y:
            y = PLACE_Y[sp.place]
        else:
            # troops step out of their lane's crypt gate ("back" ones a bit
            # deeper inside, so they arrive later)
            y = GATE_Y.get(sp.lane, 6.0) + (0.4 if sp.place == "back" else 1.0)
        m.team_power[ENEMY] = (mult, mult)
        m.team_level[ENEMY] = lv
        before = set(id(e) for e in m.entities)
        m._deploy(ENEMY, sp.key, x, y)
        if c.category != "spell":
            m.emit("portal", sp.key, x, y, ENEMY)
        for e in m.entities:
            if id(e) not in before and e.team == ENEMY:
                e.boss = sp.mult > 1.0 or wave.boss
        # spells keep the wave's power for anything they raise later
        m.team_power[ENEMY] = (level_mult(wave.level), level_mult(wave.level))
        m.team_level[ENEMY] = wave.level


def new_level_match(level, player_deck):
    """A Match set up for a level: no enemy towers, no clock."""
    from engine import Match
    m = Match(player_deck, cards.DEFAULT_AI_DECK, enemy_towers=False, timed=False)
    return m, LevelRun(m, level)
