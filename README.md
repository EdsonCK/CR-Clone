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

1. **Battle** from the main menu opens the **Battle Setup** screen, where you
   pick the AI's **difficulty** (Easy / Medium / Hard — Hard is the original,
   punishing tuning), then hit **Start Battle**.
   * The AI's deck is chosen on the separate **AI Deck** menu (from the main
     menu, or "Change AI Deck" in Battle Setup). Pick from 11 archetype decks
     (Hog Cycle, P.E.K.K.A Bridge, Golem Beatdown, Classic, Log Bait, Miner
     Control, Lava Loon, X-Bow, Sparky GG, MK Bats WB, Royal Giant),
     **Random**, or build your own **Custom** AI deck.
2. Click a card in your hand (bottom bar), then click **your side** of the
   arena to deploy it. Right-click (or click the card again) cancels.
3. Elixir refills over time (max 10). It **doubles** in the last minute and
   **triples** in overtime.
4. Destroy more enemy towers than the AI before time runs out. Destroying the
   **King Tower** is an instant win. A tie goes to **overtime** (sudden death).

The AI is deliberately given an **elixir/tempo advantage** (a simple AI can't
out-skill a real player) — all of that is tunable, see below.

---

## Balancing & playtesting (the part you'll actually edit)

Two files are designed for you to tweak without touching engine code:

### `src/config.py` — global rules & AI difficulty
Heavily commented knobs for:
- Arena size, elixir rates, double/triple-elixir timing, match length.
- Tower HP / damage / range.
- **AI difficulty**: `AI_ELIXIR_MULT`, `AI_ELIXIR_START_BONUS`,
  `AI_REACTION_TIME`, `AI_AGGRESSION`, and more. Turn these **down** to make
  the AI easier, **up** to make it harder. The **Easy / Medium / Hard**
  presets live in the `DIFFICULTIES` dict (Hard = the original tuning); edit
  those to reshape what each difficulty means.
- Global damage/HP/speed multipliers for quick sweeping balance changes.
- Debug toggles: `SHOW_TILE_GRID`, `SHOW_RANGES`.

### `src/cards.py` — the card database
Every card is plain data. Change a number to rebalance a card; copy an entry
and give it a new `key` to add a brand-new card. The file header documents
every field (hp, damage, hit_speed, range, splash, spawners, death effects,
spell fields, etc.).

---

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
  game.py     window, menus, deck builder, rendering, input, main loop
assets/
  sprites/    generated (and user-replaceable) PNGs
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
  (e.g. charge, shields, and ramping damage are simplified). Tune or extend
  them in `engine.py` if you want more fidelity.
- Troops don't physically collide/push each other yet (they can overlap).
