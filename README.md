# Clash Clone — Singleplayer

A single-player, Clash-Royale-style real-time strategy game built in **Python +
Pygame**. Build an 8-card deck, then battle an AI on a faithful-shaped arena
(18×32 tiles, two lanes, a river with two bridges, and 2 Princess Towers + 1
King Tower per side). All art is original placeholder art — no copyrighted
assets — and it's fully swappable (see below).

---

## Quick start

```bash
pip install -r requirements.txt
python src/main.py
```

(You can also run it from inside `src/` with `python main.py`.)

The first launch generates all the unit sprites into `assets/sprites/`.

## How to play

1. **Battle** from the main menu opens the **Battle Setup** screen. Two
   separate dials control the AI:
   * **AI Intelligence 1–5** (Novice, Casual, Skilled, Expert, Master): how
     well it plays. Keys **1–5** also work.
   * **AI Elixir 0.5x–2.0x**: how fast it gains elixir (its starting elixir
     scales too). **1.0x is a perfectly even fight.** Drag or click the
     slider, use the **−/+** buttons, the arrow keys or the mouse wheel
     (0.05 steps), or the preset buttons.

   Your choices are remembered. Then hit **Start Battle!**
   * **Change AI Deck** opens the AI Deck screen; **Back to Battle Setup**
     returns you straight to the battle screen. Pick from 11 archetype decks
     (Hog Cycle, P.E.K.K.A Bridge, Golem Beatdown, Classic, Log Bait, Miner
     Control, Lava Loon, X-Bow, Sparky GG, MK Bats WB, Royal Giant),
     **Random**, or build your own **Custom** AI deck.
   * **Edit My Deck** opens your deck editor and comes back here too.
2. Click a card in your hand (bottom bar), then click **your side** of the
   arena to deploy it. Right-click (or click the card again) cancels.
3. Elixir refills over time (max 10). It **doubles** in the last minute and
   **triples** in overtime.
4. Destroy more enemy towers than the AI before time runs out. Destroying the
   **King Tower** is an instant win. A tie goes to **overtime** (sudden death).
5. After a match, **Play Again** rematches with the same settings.

### Levels

**Levels** on the main menu are set-piece challenges. The opponent has **no
towers**: scripted waves of enemies march at yours, and your only goal is to
survive them all with your King Tower standing. You can only deploy on your
half. Stars: 3 = no tower lost, 2 = one Princess Tower lost, 1 = both lost.
Your best stars are saved in `progress.json`.

Level rules:

* **Level Deck** – Levels use their own deck (**Edit Level Deck** on the
  Levels screen, saved in `level_deck.json`). With no towers to hit, **win
  conditions are banned**: Giant, Golem, Hog Rider, Balloon, Royal Giant,
  Lava Hound, Battle Ram, Wall Breakers, Skeleton Barrel, Goblin Giant,
  Electro Giant, Elixir Golem, Ice Golem, X-Bow and Mortar are greyed out in
  the editor and can't be played.
* **Marching** – your troops don't stand around waiting. With nothing to
  fight they march up their lane until the spot where the enemy Princess
  Tower would be is within their attack range, then hold there.
* **Crypt Miasma** – the whole enemy half is covered in a faint poison haze.
  Your troops standing in it take 16 damage every second (a Goblin dies on
  the 6th tick), so you can't build an army at the spawn and camp the waves.

The window is 420×800. It can be resized (or maximised) and the game scales
to fit.

Enemy units have **levels**. Card stats count as level 11, and every level
above that adds +10% HP and damage (compounding), as in Clash Royale. Each
unit's level is shown on a badge next to its health bar, and bosses carry a
red **BOSS** tag.

There are **20 levels**, each built around a theme, and they get harder as
you go. The Levels screen scrolls (mouse wheel, drag, arrow keys or the
scrollbar). Each card shows the level's number, waves, enemy levels, your
stars and your win/play record, and the screen opens at the first level you
haven't cleared yet.

| # | Level | Theme / boss wave |
|---|---|---|
| 1 | The Bone Crypt | every skeleton variant; boss: two Giant Skeletons (2x) |
| 2 | Goblin Ambush | goblins, darts, barrels, huts; boss: two Goblin Giants (1.4x) |
| 3 | The Iron Legion | P.E.K.K.As under a sky of Minions and Bats; boss: two P.E.K.K.As (1.5x) |
| 4 | Frostbite Pass | Ice Spirits, Ice Golems, Ice Wizards, Snowball + Freeze; boss: two Ice Golems (3.5x) |
| 5 | Barbarian Raid | Barbarians, rams, a Barbarian Hut, Barbarian Barrels; boss: the Warband (Elite Barbarians 1.5x) |
| 6 | Sky Raiders | only flyers: Balloons, Flying Machines, dragons; boss: the Lava Hound |
| 7 | The Royal Court | knights, princes, princesses, Royal Giant; boss: the two Princes (1.85x) |
| 8 | Rogues' Den | Bandits, Miners under your towers, Poison; boss: the Boss Bandit (1.7x) |
| 9 | Spark & Storm | Zappies, E-Wizards, E-Dragons, Lightning; boss: twin Sparky + E-Giant (1.25x) |
| 10 | Hog Stampede | Hog Riders and rams straight at your towers; boss: the Stampede (1.55x) |
| 11 | The Pyromancers | Fire Spirits, Wizards, Furnace, Inferno Tower, Fireballs; boss: the Fire Lords (2x) |
| 12 | Graveyard Shift | Witches, Night Witches, Graveyards, Tombstones; boss: the Lich King (1.5x) |
| 13 | The Marksmen | archers, musketeers, Hunter, X-Bow, Archer Queen; boss: Three Musketeers (1.3x) |
| 14 | Miner's Strike | Miners popping up on your towers, Mighty Miners, Cannon Carts; boss: the Mother Lode (1.7x) |
| 15 | Dragon's Lair | Baby, Inferno and Electro Dragons; boss: the Elder Dragons |
| 16 | Siege Engines | X-Bows and Mortars dug in at the river, Bomb Tower; boss: the Fortress (1.5x) |
| 17 | Giants' Causeway | every kind of giant; boss: the Golem King |
| 18 | Splash Zone | Valkyries, Bowlers, Bombers, Executioners; boss: two Mega Knights (1.3x) |
| 19 | Champions' Arena | a champion every wave; boss: the Hall of Champions (1.45x) |
| 20 | The Final Siege | 8 waves of everything; boss: the Overlords (P.E.K.K.A + Mega Knight + Lava Hound) |

Waves can also **cast spells**: Graveyards, Goblin Barrels, Miners and
Earthquakes land on your towers, and Snowball, Freeze, Barbarian Barrel,
Poison, Lightning, Fireball and Rocket are aimed at the thickest clump of
your troops (they wait until you have some on the field). Enemy spells hit
as hard as the wave's level. Siege buildings (X-Bow, Mortar, Bomb Tower,
Inferno Tower, Tesla) can be dug in right at the river - you'll have to cross
into the miasma to knock them out. You get bonus elixir when a boss wave
starts.

**Difficulty.** Every level was playtested by letting the AI defend with
decks built from the presets (win conditions swapped out), 24 runs per level
at "Expert" and 12 at "Skilled":

| Level | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Expert clears | 100% | 92% | 88% | 92% | 75% | 58% | 79% | 71% | 67% | 54% |
| Skilled clears | 75% | 58% | 33% | 92% | 50% | 33% | 42% | 25% | 17% | 8% |

| Level | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 |
|---|---|---|---|---|---|---|---|---|---|---|
| Expert clears | 54% | 58% | 63% | 54% | 54% | 71% | 46% | 42% | 38% | 17% |
| Skilled clears | 8% | 8% | 33% | 25% | 0% | 42% | 8% | 0% | 8% | 0% |

The AI is weakest against air (Sky Raiders, Dragon's Lair) and strongest
against siege buildings, so expect those to feel a little different in your
own hands. Your levels and stars are kept per level key, so old saves carry
over.

New levels are plain data: see the docstring at the top of `src/levels.py`.

### Deck editor

Your 8 cards sit at the top in two rows of four. Below is the full collection.

* **Left-click** a card to add it (or remove it if it's already in your deck).
* **Right-click** removes a card (in the collection or in your 8 slots).
* The **mouse wheel** only scrolls; you can also drag the scrollbar.
* Hover a card to see its stats. **Cancel** / Esc leaves without saving.
* Max 1 Champion per deck.

### Champions

Once a champion is on the field, the yellow button (bottom-left of the arena)
activates its ability for a little extra elixir. Each ability can be used
**once** per champion deployment. The exception is the Boss Bandit, who gets
**2 uses, 3 seconds apart**.

| Champion | Passive | Ability |
|---|---|---|
| Mighty Miner | Drill ramps up in 3 damage stages on one target | **Explosive Escape**: drops a bomb, burrows to the mirrored spot in the other lane |
| Archer Queen | — | **Cloaking Cape**: invisible + double attack speed |
| Little Prince | Shoots faster the longer he attacks | **Royal Rescue**: the Guardian charges in, knocking enemies back |
| Golden Knight | — | **Dashing Dash**: chain-dashes through up to 10 enemies |
| Skeleton King | Collects souls from nearby deaths | **Soul Summoning**: 6 skeletons + 1 per soul (max 16) |
| Monk | Every 3rd hit is a knockback combo | **Pensive Protection**: −80% damage taken, reflects projectiles |
| Goblinstein | Doctor + Monster deploy together | **Lightning Link**: damaging beam between the two |
| Boss Bandit | Dashes onto targets (3.5–6 tiles), invulnerable mid-dash | **Getaway Grenade** (x2): teleports straight back from her target to a 4.75-tile gap, then dashes straight back in for another double-damage hit (unless another enemy is closer) |

### The AI levels

Every level keeps the skills of the ones below it.

| Level | What it adds |
|---|---|
| 1 Novice | Slow reactions, often plays a random card, sloppy placement |
| 2 Casual | Real counter-picking (air/ground, splash vs swarms, DPS vs tanks), value spells, supports its pushes |
| 3 Skilled | Lets towers handle tiny threats, smart placement (buildings pull tanks to the middle, ranged units behind towers), leads moving targets with spells, finishes low towers, counter-pushes, beatdown pushes, keeps a defence reserve, times champion abilities |
| 4 Expert | Counts your elixir and punishes you when you're low, resets Infernos, cycles to its win condition, and **simulates** its defensive options 4 seconds ahead (assuming both sides keep playing) before choosing one |
| 5 Master | Exact elixir count, remembers your cards, and **simulates every decision** (defence, attack, spells) 10 seconds ahead while assuming you keep playing well |

Benchmarked by having the AIs play each other at 1.0x elixir (both deck
orders, preset decks, v0.3.0 card stats): Casual beats Novice 63%, Skilled
beats Casual 52%, Expert beats Skilled 62%, Master beats Expert 67% (Master
beats Skilled 80%). Elixir is the bigger lever: Master at 1.0x roughly
equals Skilled at 1.15x.

Master "thinks" for about half a second per decision, spread over frames so
the game stays smooth.

v0.5.0 note: with unit collisions in, Expert's old lookahead (which assumed
nobody else acts during its 4-second simulation) stopped paying off and it
fell to a coin flip against Casual. Its rollouts now assume both sides keep
playing, like Master's: in a 24-game check Expert beat Casual 16-8, Skilled
19-4 (1 draw) and Novice 22-2, and Master beat Expert 20-4.

---

## Balancing & playtesting (the part you'll actually edit)

Two files are designed for you to tweak without touching engine code:

### `src/config.py` — global rules & AI difficulty
Heavily commented knobs for:
- Arena size, elixir rates, double/triple-elixir timing, match length.
- Tower HP / damage / range.
- **AI**: `AI_LEVELS` holds each intelligence level's reaction time,
  decision speed, mistake rate, placement accuracy and spell pickiness.
  `AI_ELIXIR_MULT_MIN/MAX/STEP` set the slider's range, and
  `AI_START_BONUS_PER_MULT` sets how much starting elixir the boost adds.
- Global damage/HP/speed multipliers for quick sweeping balance changes.
- Debug toggles: `SHOW_TILE_GRID`, `SHOW_RANGES`.

### `src/cards.py` — the card database
Every card is plain data. Change a number to rebalance a card; copy an entry
and give it a new `key` to add a brand-new card. The file header documents
every field (hp, damage, hit_speed, range, splash, spawners, death effects,
spell fields, etc.).

---

## Music & sound

All music and sound effects are **synthesised from scratch** in
`src/sounds.py` (oscillators, filtered noise, plucked strings). There are no
samples and nothing copyrighted. That includes:

* menu music, battle music, and a faster track for the last minute;
* victory / defeat jingles and announcements (double elixir, overtime, the
  final 10-second countdown, the King waking up);
* UI clicks, card select / deselect, and an "invalid placement" buzz;
* a **unique deploy sound and attack sound for every card**, plus a cast
  and impact sound for every spell.

Sounds are panned left/right by where they happen. Toggle **Music** (M key)
and **Sound** (N key) on the main menu; volumes are in `config.py`. The
WAVs live in `assets/sounds/`. Drop in your own WAV with the same name
(e.g. `knight_attack.wav`) and it is used and never overwritten.

The Tesla fires an electric crackle (a sharp crack, fizzing sparks and a
low hum) instead of a pitched tone, and it and the Archers are trimmed
quieter (`ATTACK_GAIN` in `sounds.py`). To re-render one sound after changing
it, bump its number in `SOUND_REVS`; only that file is regenerated.

## Battlefield feel

* **Collisions** – units have a body size and a weight (`MASS` / `BIG_R` in
  `src/engine.py`; a card's `mass` field overrides it). Ground units push
  ground units and air units push air units, friend or foe: a Giant shoulders
  through Skeletons, a Skeleton Army spreads into a crowd instead of one
  stacked skeleton (and 15 of them can nudge a Knight), and nothing moves a
  building or tower - troops walk around them. Squads queue up to cross the
  narrow bridges.
* **River banks** – ground troops (except Hog Rider's vault and jumpers) can't
  be pushed or knocked into the river; they slide along the bank to a bridge.
* **Animations** – troops bob and waddle as they walk, breathe when idle,
  lean back before a melee swing and lunge into it (with a quick swoosh),
  kick back when they shoot, flash white when hit and drop in when deployed;
  flyers hover, beat their wings and cast a shadow; buildings recoil when
  they fire. It's all a light pose on top of each card's normal art, so every
  unit keeps its exact look.
* **Elixir Collector** – its glass tank visibly fills as the next elixir
  brews; when it's full the tank flashes, a "+1 elixir" pops up with a soft
  chime and it starts filling again.

## Spells & effects

Fireball, Arrows, Rocket, Goblin Barrel and Snowball are **thrown from the
caster's King Tower** and visibly fly in an arc to the target (flight speeds
are in `SPELL_FLIGHT_SPEED` in `config.py`). Every spell has its own
telegraph, impact and lingering look (scorch marks, frost, arrows stuck in
the ground, earthquake cracks, poison haze...). See `src/fx.py`.

Melee troops wind up for **half** their hit speed after engaging a new
target before their first hit lands (`MELEE_FIRST_HIT_FRAC` in `config.py`;
a card's `first_hit` field overrides it - Balloon, Golem and Golemites use
1.0s). Ranged troops fire straight away, spirits explode on contact, and a
finished charge hits on impact.

## Swapping in your own art

Every card has its own original, hand-built art (in `src/sprite_art.py`),
painted into `assets/sprites/<cardkey>.png` (128×128 with transparency).
Squad cards also get a `<cardkey>__u.png` showing one unit, which is what's
drawn for each troop on the battlefield.

To replace any unit's art, drop a PNG with the matching card key into
`assets/sprites/` (any square size, transparent background) — it will be
used automatically and never overwritten. Card keys are the `key` field in
`src/cards.py` (e.g. `knight.png`, `hog_rider.png`, `fireball.png`). Delete a
sprite to have the game repaint the built-in art. In-game unit sizes live in
the `SCALES` table at the top of `src/sprites.py`.

---

## Card balance (tools/)

All card stats were balanced with an automated benchmark,
`tools/balance.py`. Its docstring explains it in full. In short:

* Every card meets every other card in a real arena with towers, in both
  roles (attacking at the bridge and defending at the tower), in
  **equal-elixir** engagements: the cheaper side deploys extra copies.
* Each engagement is scored as an elixir trade plus tower damage. A card's
  performance is the average over the whole pool (weighted toward cards of
  similar cost, with the most extreme 10% trimmed off each end), so no card
  is balanced around one counter.
* Damage spells are judged on their best 40% of targets (how they're used).
* Each round tunes every card's power (hp/damage split by role) against a
  **frozen snapshot** of all the others. The results are saved separately
  and only applied when the round ends.

`tools/balance_data/` holds the benchmark results, and `BALANCE.md` lists
every stat change.

## Project layout

```
src/
  main.py     entry point
  config.py   <-- balancing knobs & AI difficulty (edit me)
  cards.py    <-- card database (edit me)
  engine.py   arena, entities, combat, spells, towers, match simulation
  ai.py       the single-player opponent
  sprites.py  saves/loads unit art, in-game unit sizes
  sprite_art.py  the original card art (one function per card)
  sounds.py   procedural music & sound effects
  fx.py       particles & spell visuals
  game.py     window, menus, deck builder, rendering, input, main loop
assets/
  sprites/    generated (and user-replaceable) PNGs
  sounds/     generated (and user-replaceable) WAVs
tools/
  balance.py        card benchmark & auto-balancer
  apply_balance.py  writes balanced stats into src/cards.py
```

## Cards included (95, including 8 Champions)

Troops, win conditions, air units, buildings, spawners and spells spanning the
classic roster — Knight, Archers, Giant, Hog Rider, P.E.K.K.A, Wizard, Baby
Dragon, Balloon, Golem, Minions, Musketeer, Valkyrie, Prince, Witch, Cannon,
Inferno Tower, Tombstone, Elixir Collector, Zap, Fireball, Rocket, Lightning,
The Log, Freeze, Poison, and many more. (No evolutions, heroes, or alternate
game modes yet — base cards only, as requested.)

## Notes / simplifications

- Some ultra-unique mechanics are approximated to keep the engine readable
  (e.g. charge, shields, dashes and champion abilities are simplified). Tune or extend
  them in `engine.py` if you want more fidelity.
- Collisions are soft (overlaps are pushed apart over a few frames rather
  than being hard walls), and units path straight to their target or the
  nearest bridge rather than true path-finding around obstacles.
