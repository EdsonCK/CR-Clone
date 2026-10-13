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

## What's in it (v1.4)

**New in v1.4**: a tabbed home screen like the real game - **Shop**
(placeholder), **Deck**, **Battle**, **Levels** and **Modes** along the bottom,
with Settings, AI Deck, Records, Last Match and How To Play in the three-bar
menu at the top right. The window is wider (540 x 800) and the arena has
camps, tents and torch pillars in its new side margins. A second menu theme
and a second battle theme alternate. Trophy Road gives **+60 trophies** a
win and its bots play **variations** of 22 archetype decks, with more
Evolutions and Heroes the higher you climb.

## Home screen

* **Shop** - a placeholder for now (cards are upgraded with the gold you win).
* **Deck** - the deck builder, saved as you go (deck slots 1-5, your Tower
  Troop chip, Clear / Default, and **Cards & Upgrades** for the collection).
* **Battle** - your arena and trophies (click it for the Trophy Road), the
  big **Battle** button (a Trophy Road battle), **Friendly Battle** (pick the
  AI's intelligence, elixir and deck yourself), Achievements, the next road
  reward, the daily first-win bonus and your deck.
* **Levels** - the 30 wave levels and your Level Deck.
* **Modes** - the Special Battles, Endless Survival and the Sandbox.
* **Three-bar menu** (top right) - Settings, AI Deck, Records, Last Match,
  How To Play and Quit. Esc goes back to the Battle tab.

## Earlier versions

* **Trophy Road**: a ranked ladder through 16 arenas (Goblin Stadium ->
  Legendary Arena). Win trophies, lose some, and your trophy count picks the
  bot: the higher you climb, the smarter it plays and the higher its cards.
  Gold and shards line the road.
* **Tower Troops**: Tower Princess, Cannoneer, Dagger Duchess and Royal Chef
  man your Princess Towers, unlocked along the Trophy Road.
* **Battle** the AI: 5 intelligence levels, a 0.5x-2x elixir handicap
  slider, 22 archetype decks (or random / custom), and an AI card level that
  climbs as you beat it.
* **Levels**: 30 themed wave challenges, unlocked by stars.
* **Special Modes**: Triple Elixir, Sudden Death, Mirror Match, Draft, Rage
  Battle, Random Decks, Double Trouble and **Endless Survival**.
* **Progression**: gold and shards, card levels 11-16, all 43 **Evolutions**
  and all 18 **Heroes** of the real game (as of the Minion Giant update), 5
  saved decks, 28 achievements, a daily first-win bonus.
* 123 cards (8 Champions) - the whole roster up to the Minion Giant - each
  with a one-line description, original art, procedural music and a unique
  sound, collisions, path-finding around buildings, card animations and a
  post-match stats screen.

**New in v1.2**: Trophy Road, Tower Troops, Levels 21-30, card descriptions
on the Cards screen, ability call-outs and clearer status markers in battle
(roots, curses, runes), and a smarter AI with the newer cards (Void, Vines,
Rune Giant escorts, Rage/Clone combos; its preset decks now use their Evo
and Hero slots).

## Trophy Road

**Trophy Road** (the Battle tab's **Battle** button; the arena banner opens
the road) is the ranked ladder. You play your current deck against a bot chosen by your
trophy count:

| Trophies | Arenas | Bot |
|---|---|---|
| 0-599 | Goblin Stadium, Bone Pit | Novice |
| 600-1299 | Barbarian Bowl, Spell Valley | Casual |
| 1300-2299 | Builder's Workshop, P.E.K.K.A's Playhouse, Royal Arena | Skilled |
| 2300-3399 | Frozen Peak, Jungle Arena, Hog Mountain | Expert |
| 3400+ | Electro Valley, Spooky Town, Rascal's Hideout, Serenity Peak, Miner's Mine, Legendary Arena (5500) | Master |

* A win is **+60 trophies** (+4 per crown you won by), a loss **-20**, a
  draw 0. You never drop below the gate of an arena you've reached.
* The bot's cards are level 11 + 1 per 1000 trophies (up to 16), but never
  more than **one level above your crown towers**.
* The bot plays a **variation** of one of the 22 archetype decks (sometimes a
  random deck): a few cards may be swapped for on-theme alternatives (a Log
  Bait with a Cannon instead of the Inferno Tower, a Prince instead of the
  Knight...), and which cards are its Evolutions and Hero changes every game.
  It brings no Evolutions or Heroes at the start of the road, then 1 Evo
  (from ~920 trophies), 1 Evo + its Hero (~1830) and the full 2 Evos + Hero
  from 2750 on. It also brings a Tower Troop you could have unlocked by then.
  The decks and their swaps are `AI_DECK_PRESETS` / `AI_DECK_VARIANTS` in
  `src/cards.py`.
* **Road rewards** every 100 trophies (gold, and 3 shards at every new
  arena) are paid once, the first time you reach them. The Trophy Road
  screen shows the whole road and points at your next reward.

Tune it in `src/trophy.py` (arenas, trophies per win/loss, rewards).

## Tower Troops

The troop on your Princess Towers is picked per deck: click the tower chip
at the top right of the deck editor to cycle through the ones you own. Stats
are the real game's ratios against the Tower Princess.

| Troop | Unlock | What it does |
|---|---|---|
| Tower Princess | start | the default: long-range arrows, hits air and ground |
| Cannoneer | 2300 (Frozen Peak) | slow, very heavy cannonballs; a little less HP |
| Dagger Duchess | 3400 (Electro Valley) | a magazine of 8 fast daggers; once it's empty she throws slowly, and reloads one dagger every 0.9s while idle |
| Royal Chef | 4200 (Rascal's Hideout) | cooks a pancake (a dial on the tower) and serves it to your strongest troop for **+1 level**; cooks slower while his towers are fighting |

The AI uses Tower Troops in Trophy Road battles. Mirror Match copies yours.

## How to play

1. **Friendly Battle** on the Battle tab opens the **Battle Setup** screen. Two
   separate dials control the AI:
   * **AI Intelligence 1–5** (Novice, Casual, Skilled, Expert, Master): how
     well it plays. Keys **1–5** also work.
   * **AI Elixir 0.5x–2.0x**: how fast it gains elixir (its starting elixir
     scales too). **1.0x is a perfectly even fight.** Drag or click the
     slider, use the **−/+** buttons, the arrow keys or the mouse wheel
     (0.05 steps), or the preset buttons.

   Your choices are remembered. Then hit **Start Battle!**
   * **Change AI Deck** opens the AI Deck screen; **Back to Battle Setup**
     returns you straight to the battle screen. Pick from 22 archetype decks
     (Hog Cycle, P.E.K.K.A Bridge, Golem Beatdown, Classic, Log Bait, Miner
     Control, Lava Loon, X-Bow, Sparky GG, MK Bats WB, Royal Giant, Recruits
     Hogs, Drill Cycle, Rune Giant Rush, Graveyard Freeze, Mortar Bait,
     Electro Giant, Three Musketeers, Double Prince, Lumberloon, Elixir Golem,
     Champion Cycle), **Random**, or build your own **Custom** AI deck (also
     in the three-bar menu: AI Deck).
   * **Edit My Deck** opens your deck editor and comes back here too.
   * **AI card level**: *Ladder* (the AI's cards start at level 11 and go up
     one level for every 3 wins you get against that intelligence level, up
     to 16) or *Match my level* (the AI uses your towers' level).
2. Click a card in your hand (bottom bar), then click **your side** of the
   arena to deploy it - or drag the card there. Right-click (or click the
   card again) cancels.
3. Elixir refills over time (max 10). It **doubles** in the last minute and
   **triples** in overtime.
4. Destroy more enemy towers than the AI before time runs out. Destroying the
   **King Tower** is an instant win. A tie goes to **overtime** (sudden death).
5. After a match you see your rewards; **Match Stats** shows damage and
   knockouts per card for both sides, elixir spent and wasted, tower damage
   and (in Levels) which wave cost you which tower. **Last Match** on the main
   menu reopens it.

## Progression

Everything is saved in `profile.json` (delete it, or use Settings > Reset
progress, to start over).

* **Gold** - from every win (Battles pay more against smarter AIs, higher
  elixir boosts and for crowns), Level wins and new stars, Special Battles,
  Endless waves, achievements and the **first win of the day** (+60 gold,
  +1 shard). Spend it in **Cards** to upgrade a card: 11->12 costs 100,
  then 250, 600, 1200 and 2500 (to 16). Each level is +10% HP and damage
  (spells and the troops spells drop too).
* **Crown towers** are as strong as your deck: their level is the average
  level of the 8 cards you take into the match.
* **Shards** - first clears and 3-star clears of Levels, a trickle from
  Battle wins (more against smarter AIs), the first win in each Special
  Battle, every 5 Endless waves, and achievements. Spend them on
  **Evolutions** (5 shards) and **Heroes** (8 shards).
* **Cards screen** - filter by type / Evos / Heroes, read what each card
  does, see its stats
  now and at the next level, upgrade, and unlock its Evolution / Hero.
* **Achievements** - 28 milestones across every mode (win 10/50 battles,
  beat Expert/Master at even elixir, clear Level 10/20/30, 30/60/90 stars,
  Endless wave 10/20, 1000/2300/5500 trophies, max a card...). Claim the reward on the Achievements screen;
  the Battle tab (and its Achievements button) shows how many are waiting.
* **Sandbox** (Settings) unlocks every Level, Evolution and Hero for free
  play without touching your saved progress.

## Evolutions & Heroes

Your deck's first two slots are **EVO slots** and the third is the **HERO
slot** (the deck editor labels them; use the < > arrows on a card to move
it).

**Evolutions** - an unlocked Evolution in an EVO slot comes out *evolved*
whenever its charge is full: its card glows purple in your hand, and the
troop gets a purple aura and its extra ability. Playing it normally refills
the charge (1 or 2 plays, shown as pips on the card). As in Clash Royale the
charge starts empty: the first copy you play in a match is the normal card,
and the Evolution only comes out once you've cycled it.

| Card | Cycles | Evolution |
|---|---|---|
| Archers | 2 | +1 range. Power Shot: targets 4-6 tiles away take +25% damage from a piercing arrow. |
| Baby Dragon | 2 | Tailwind (8x9 tiles): enemies 30% slower, allies 30% faster. Lingers 2s after it dies. |
| Barbarians | 1 | +10% HP. Every hit gives them +30% attack and move speed for 5s. |
| Bats | 2 | +50% HP. Every bite heals them twice; they can overheal up to double HP. |
| Battle Ram | 2 | Charging bowls over troops in its path; bounces off buildings to charge again. Leaves 2 Evolved Barbarians. |
| Bomber | 2 | His bomb bounces twice more, 2.5 tiles apart, exploding each time. |
| Cannon | 2 | On deploy, fires a 9-cannonball barrage (5+4 rows) that knocks enemies back. |
| Dart Goblin | 2 | Darts leave poison puddles that get stronger after 4 and 7 darts. |
| Electro Dragon | 1 | After its 3-target chain, the bolt keeps bouncing between troops (33% less damage, no stun). |
| Electro Giant | 2 | Every 6s an energy pulse drains a level from every enemy within 6 tiles (stacks). |
| Elite Barbarians | 1 | Throw Rage-tipped spears at ground units 3.5-5 tiles away, leaving a trail of Rage (5s cooldown). |
| Executioner | 1 | Enemies within 2.5 tiles when he throws take 75% extra axe damage and are knocked back. |
| Firecracker | 2 | Her firework and its sparks leave burning, slowing embers behind them. |
| Furnace | 2 | While attacking she spawns Fire Spirits every 2.4s, to her sides. |
| Giant Snowball | 2 | Rolls 4.5 tiles, carrying the enemies it hit; slows 1s longer. |
| Goblin Barrel | 2 | A second barrel lands on the mirrored tile in the other lane with 3 Decoy Goblins. |
| Goblin Cage | 2 | Drags the nearest ground troop within 3 tiles into the cage and pummels it every second. |
| Goblin Drill | 2 | At 66% and 33% health it resurfaces nearby, leaving a Goblin each time. |
| Goblin Giant | 1 | Below half health, a Goblin jumps off his back every 2.2s. |
| Hunter | 2 | Every 5s nets the closest enemy within 4 tiles, trapping it for 3s (nets pull fliers down). |
| Ice Spirit | 2 | Bigger blast; 3s later the same spot is hit and frozen again. |
| Inferno Dragon | 2 | Keeps its beam heat for 9s after a kill; after 20s of burning a 4th stage doubles the damage. |
| Knight | 2 | Takes 60% less damage while he isn't attacking. |
| Lumberjack | 2 | Longer Rage on death, and his untouchable ghost keeps chopping. |
| Mega Knight | 1 | Every 2nd hit is an uppercut that launches the target 4 tiles toward its own Crown Tower. |
| Minion Horde | 1 | Each Minion's first non-lethal hit makes it invincible and untargetable for 3s (slower, but attacks faster). |
| Mortar | 2 | Fires 1s faster and every shell drops a Goblin. |
| Musketeer | 2 | 3 sniper shots that reach anywhere ahead (6-30 tiles) for 1.8x damage. |
| P.E.K.K.A | 1 | Heals after every kill (more for bigger victims), overhealing up to +50% HP. |
| Princess | 2 | Her first shot (then every 2nd) chills a big area 30% slower; leaves a freezing patch when she falls. |
| Royal Ghost | 2 | Each time he appears he summons 2 invisible Souldiers. |
| Royal Giant | 1 | Each shot's recoil damages enemies within 2.5 tiles and knocks ground troops back 1 tile. |
| Royal Hogs | 2 | They fly in! When they attack or get hurt they crash down, damaging enemies below. |
| Royal Recruits | 1 | Once their shield breaks they charge after 2.5 tiles, hitting for double damage. |
| Skeleton Army | 2 | Led by General Gerry: fallen skeletons fight on as untouchable shadows until he falls. |
| Skeleton Barrel | 2 | +25% HP, bigger blast, and TWO barrels of 7 Skeletons (one dropped at 75% HP). |
| Skeletons | 2 | Every hit summons another Skeleton (up to 8 at once). |
| Tesla | 2 | Every time it pops up, a 6-tile shockwave damages and stuns. |
| Valkyrie | 2 | Each spin conjures a tornado that pulls enemies within 5.5 tiles toward her. |
| Wall Breakers | 2 | They explode when defeated too, and a Runner keeps going to blow up again. |
| Witch | 1 | Heals whenever one of HER skeletons dies, overhealing up to +24% HP. |
| Wizard | 1 | Fire Shield: when it breaks, enemies within 3 tiles take heavy damage and are blown back 3 tiles. |
| Zap | 2 | The zap lingers and strikes a second time, 0.5 tiles wider. |

**Heroes** - an unlocked Hero in the HERO slot is always the Hero version
(gold star). Once it's on the field, the gold button at the bottom-right of
the arena fires its one-time ability for a little elixir. The Hero Goblins'
button lights up once their banner is planted:

| Hero | Ability (cost) | What it does |
|---|---|---|
| Balloon | **Skeletrooper Drop** (2) | Drops a Skeletrooper onto the nearest ground enemy within 6 tiles; it lands hard and fights on. |
| Barbarian Barrel | **Re-Roll** (1) | The Barbarian hops back in his barrel, rolls it again (3 tiles) and heals 50%. |
| Berserker | **Savage Survival** (3) | 4s frenzy: attacks every 0.2s, ultra fast, can't drop below 1 HP (-75% vs Crown Towers). |
| Bowler | **Boulder Barrage** (2) | After a 2.5s wind-up, lobs huge boulders up to 11.5 tiles for 7.3s. |
| Dark Prince | **Dismount** (3) | Leaps off (slam on landing): his Rhino charges on at buildings while he fights on foot. |
| Electro Wizard | **Surging Strikes** (2) | For 3s, zaps and stuns 2 enemies within 5 tiles every 0.5s (-50% vs Crown Towers). |
| Giant | **Heroic Hurl** (2) | Grabs the highest-HP enemy troop within 2 tiles and throws it to the other lane (stunned 2s; ground troops take landing damage). |
| Goblins | **Banner Brigade** (1) | 4 Goblins. When the last one falls their banner stays 5s - use it to call 2 more Goblins. |
| Ice Golem | **Snowstorm** (2) | Three icy blasts around him (4 tiles), each slowing enemies 30%. |
| Ice Wizard | **Frosty Fella** (2) | His next hit on a slowed enemy builds a Snowman behind it that freezes everything nearby. |
| Knight | **Triumphant Taunt** (2) | Taunts every enemy troop and building within 7.5 tiles and raises a 260 shield for 5s. |
| Magic Archer | **Decoy Dodge** (2) | Teleports back leaving a decoy; his next shot is 3 extra-long arrows. |
| Mega Minion | **Warp Strike** (2) | Warps onto the weakest enemy anywhere and smashes it, then returns (after the kill or 3.5s). |
| Mini P.E.K.K.A | **Breakfast Boost** (1) | Eats his pancakes: heals 30% and gains 1 level plus 1 per pancake meter filled (fights fill them faster). |
| Musketeer | **Trusty Turret** (3) | Sets up a sturdy turret 3 tiles ahead for 10s (blasts enemies where it lands). |
| Tombstone | **Rise of the Queen** (5) | The Tombstone crumbles and the Tomb Queen rises - a huge building-hunter that bursts into skeletons. |
| Valkyrie | **Wild Whirlwind** (3) | Dashes up to 5.5 tiles spinning for 3.5s: hits all around 4x a second, takes 15% less damage. |
| Wizard | **Fiery Flight** (1) | Takes off for 5s (+50% speed); his fireballs leave 2s fire tornadoes. |

In Battles the AI brings as many Evolutions and Heroes as you do (from its
own deck), and it uses Hero abilities too.

## Sandbox

**Sandbox** (Modes tab) is a free practice arena (nothing you do there
touches your progress):

* **Place any card for either side** - pick it from the strip at the bottom,
  set the side (You / Enemy), its level (11-16) and whether it comes out as
  its **Evolution** or **Hero**, then click the arena. Elixir is infinite and
  you can place anywhere except the river and on a tower.
* **Time controls** (top bar): Pause/Play (or Space), Step 0.1s, speed
  0.25x / 0.5x / 1x / 2x, and Reset (fresh towers, empty field).
* **AI opponent**: switch an AI on or off at any moment (L1-L5 button sets
  its intelligence); while it's on it plays your AI deck with normal elixir.
* **Inspector**: with no card picked, click any unit or tower to follow its
  live stats - health, damage and hit speed, range (drawn on the arena), its
  target (a line to it), wind-up / charge / stun / freeze / slow / hidden,
  and a building's remaining lifetime. Champions and Heroes get a "Use
  ability" button. Right-click clears the pick and the inspector.

## Placement previews

While you place a **building** its attack range is drawn around it (and the
Mortar's blind spot). While you place a troop or building, every **enemy
building** that could shoot it there lights up red with a pulsing red **!**
above it and its range drawn faintly (flying troops ignore ground-only
buildings like the Cannon and X-Bow).

## Special Modes

Special Battles are 3-minute battles with a twist. The AI's cards are always
**level 12** (so upgrading your cards makes them easier); pick its
intelligence at the top of the screen. Each pays gold, and your first win in
each pays a shard.

| Mode | Twist |
|---|---|
| Triple Elixir | x3 elixir from the start |
| Sudden Death | the whole match is overtime: first tower down wins |
| Mirror Match | the AI plays your deck (and Evolutions) |
| Draft | pick one card from each pair, the AI gets the other, 8 times |
| Rage Battle | every troop is permanently raged |
| Random Decks | random decks for both sides |
| Double Trouble | x2 elixir, double-strength towers, 5 minutes |

**Endless Survival** uses the Levels rules (your Level Deck, no enemy towers,
the miasma) with waves that never end: each wave has a growing elixir budget
spent on stronger and stronger troops (and the odd spell), enemy levels rise
from 11 to 16, and every 5th wave is a boss. You earn gold per wave and a
shard every 5 waves; your best wave is saved.

### Levels

**Levels** (Levels tab) are set-piece challenges. The opponent has **no
towers**: scripted waves of enemies march at yours, and your only goal is to
survive them all with your King Tower standing. You can only deploy on your
half. Stars: 3 = no tower lost, 2 = one Princess Tower lost, 1 = both lost.
Your best stars are saved in `progress.json`. Level 1 is open from the
start and **every 2 stars you earn opens the next level**.

Enemy levels ramp up from **11 on Level 1 to 16 by Level 30** (with a mix of
levels inside each level); each card shows the enemy levels and the card
level it was balanced for ("rec. Lv"). Upgrade your cards to keep up.

Level rules:

* **Level Deck** – Levels use their own deck (**Edit Level Deck** on the
  Levels screen, saved in `level_deck.json`). With no towers to hit, cards
  that **only attack buildings are banned**: Giant, Golem, Hog Rider,
  Balloon, Royal Giant, Lava Hound, Battle Ram, Wall Breakers, Skeleton
  Barrel, Goblin Giant, Electro Giant, Elixir Golem, Ice Golem, Royal Hogs,
  Ram Rider, Rune Giant, Minion Giant and Suspicious Bush are greyed out in
  the editor and can't be played. The X-Bow and Mortar shoot troops too, so
  they're allowed.
* **Marching** – your troops don't stand around waiting. With nothing to
  fight they march up their lane until the spot where the enemy Princess
  Tower would be is within their attack range, then hold there.
* **Crypt Miasma** – the whole enemy half is covered in a faint poison haze.
  Your troops standing in it take 16 damage every second (a Goblin dies on
  the 6th tick), so you can't build an army at the spawn and camp the waves.

The window is 540×800. It can be resized (or maximised) and the game scales
to fit.

Enemy units have **levels**. Card stats count as level 11, and every level
above that adds +10% HP and damage (compounding), as in Clash Royale. Each
unit's level is shown on a badge next to its health bar, and bosses carry a
red **BOSS** tag.

There are **30 levels**, each built around a theme, and they get harder as
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
| 19 | Champions' Arena | a champion every wave; boss: the Hall of Champions (1.38x) |
| 20 | The Final Siege | 8 waves of everything; boss: the Overlords (P.E.K.K.A + Mega Knight + Lava Hound) |
| 21 | Goblin Uprising | Goblin Gang, Drills, Cages, Demolishers, Goblin Curse; boss: the Machine (Goblin Machine + Goblinstein) |
| 22 | Royal Parade | Royal Recruits, Royal Hogs, Royal Delivery, Royal Ghost, Ram Rider; boss: the Royal Guard |
| 23 | Spirit Grove | every spirit, the Phoenix, Spirit Empress; boss: the Empress ascends |
| 24 | Witching Hour | Mother Witch, Night Witch, Goblin Curse, Void; boss: Midnight (the whole coven) |
| 25 | Rascal Alley | Rascals, Firecrackers, Suspicious Bushes, Berserkers; boss: Boss of the Block |
| 26 | The Rune Forge | Rune Giants enchanting their escort; boss: the Master Smith |
| 27 | Fisher's Wharf | Fishermen, Ronin, Hunters, Bowlers, Golden Knight; boss: the Last Duel |
| 28 | Dragon Roost | Skeleton Dragons, Minion Giants, Phoenixes; boss: the Ancient Wyrm (Lava Hound) |
| 29 | Machine Works | Goblin Machines, Sparky, Mortars, X-Bows, Cannon Carts; boss: Prototype X |
| 30 | The Grand Finale | every new card at once; boss: the Empress and Her Court |

Waves can also **cast spells**: Graveyards, Goblin Barrels, Miners and
Earthquakes land on your towers, and Snowball, Freeze, Barbarian Barrel,
Poison, Lightning, Fireball and Rocket are aimed at the thickest clump of
your troops (they wait until you have some on the field). Enemy spells hit
as hard as the wave's level. Siege buildings (X-Bow, Mortar, Bomb Tower,
Inferno Tower, Tesla) can be dug in right at the river - you'll have to cross
into the miasma to knock them out. You get bonus elixir when a boss wave
starts.

**Difficulty.** Every level was playtested by letting the "Expert" AI defend
with decks built from the presets (win conditions
swapped out) **at the level's recommended card level**:

| Level | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Expert clears | 100% | 89% | 86% | 92% | 100% | 64% | 94% | 78% | 97% | 64% |

| Level | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 |
|---|---|---|---|---|---|---|---|---|---|---|
| Expert clears | 58% | 67% | 72% | 67% | 64% | 58% | 69% | 67% | 44% | 31% |

| Level | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 |
|---|---|---|---|---|---|---|---|---|---|---|
| Expert clears | 83% | 89% | 81% | 47% | 69% | 78% | 33% | 56% | 47% | 44% |

(36 runs per level, v1.3.0. Each level has a power factor, `LEVEL_POWER` in
`src/levels.py`, on top of the usual enemy levels - that's the knob to turn
if one feels off.)

Being a level or two above the recommendation makes a level much easier,
being below makes it much harder.

The AI is weakest against air (Sky Raiders, Dragon's Lair) and strongest
against siege buildings, so expect those to feel a little different in your
own hands. Your levels and stars are kept per level key, so old saves carry
over.

New levels are plain data: see the docstring at the top of `src/levels.py`.

### Deck editor

**5 saved deck slots** (the 1-5 tabs at the top; the selected one is your
battle deck). Your 8 cards sit at the top in two rows of four - slots 1-2
are EVO slots, slot 3 the HERO slot; hover a card and use < > to move it.
The info line shows average elixir, the 4-card cycle cost and the average
card level. Below is the full collection.

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
and **Sound** (N key) anywhere; volumes are in Settings. There are two menu
themes and two battle themes (each with its faster final-minute version):
battles alternate between the battle themes, and the menu switches theme
each time you come back from a battle. The
WAVs live in `assets/sounds/`. Drop in your own WAV with the same name
(e.g. `knight_attack.wav`) and it is used and never overwritten.

The Tesla fires an electric crackle (a sharp crack, fizzing sparks and a
low hum) instead of a pitched tone, and it and the Archers are trimmed
quieter (`ATTACK_GAIN` in `sounds.py`). To re-render one sound after changing
it, bump its number in `SOUND_REVS`; only that file is regenerated.

## Settings

Music and sound volume, **game speed** (1x / 1.5x / 2x), **colour-blind team
colours** (blue vs orange), **drag cards to deploy**, **floating damage
numbers**, **screen shake**, **Sandbox** and **Reset progress** (asks twice).

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
* **Path-finding** – ground troops walk around buildings and towers in
  their way (picking a side and sticking to it) instead of sliding along them.
* **Lanes** – a troop with nothing in sight marches down the lane it
  appeared in (the side of the centre line it spawned on) - even right behind
  your King Tower - and only switches once that lane's Princess Tower is
  down. Every unit of a squad decides for itself, so Archers or Wall Breakers
  dropped on the centre line split, and a Skeleton Army mostly follows the
  side you placed it on. Enemies in sight still pull troops across, as in the
  real game.
* **Animations** – every card has a motion style: heavy stompers (Giant,
  Golem, P.E.K.K.A...) dip on each footfall kicking up dust and smash
  overhead; swarms scurry; spirits hop; riders gallop; casters glide, float
  when idle and stretch as they cast; dashers lean into their runs; Valkyrie
  spins with every swing; Balloons sway; dragons and hounds beat heavy
  wings; the Miner burrows up; stunned units wobble; huts rattle before they
  spawn; archers draw before they shoot. Every troop flashes when hit, drops
  in when deployed and leaves a little ghost when it falls. It's all a pose
  on top of each card's normal art, so every unit keeps its exact look.
* **Screen shake** on big spells, slams, heavy deaths and tower kills, and
  optional **damage numbers**.
* **Elixir Collector** – its glass tank visibly fills as the next elixir
  brews; when it's full the tank flashes, a "+1 elixir" pops up with a soft
  chime and it starts filling again.

## Spells & effects

Fireball, Arrows, Rocket, Goblin Barrel and Snowball are **thrown from the
caster's King Tower** and visibly fly in an arc to the target (flight speeds
are in `SPELL_FLIGHT_SPEED` in `config.py`). Every spell has its own
telegraph, impact and lingering look (scorch marks, frost, arrows stuck in
the ground, earthquake cracks, poison haze...). See `src/fx.py`.

Every troop and building has its real-game **first hit speed**: the wind-up
between locking onto a new target and its first hit (Valkyrie 0.1s, Knight
0.5s, Musketeer 0.7s, Golem 1s... the `FIRST_HIT` table in `src/cards.py`;
cards not listed use half their hit speed, `MELEE_FIRST_HIT_FRAC`). A stun
interrupts the attack, so the wind-up starts over - and Sparky has to charge
her whole shot again. Spirits explode on contact and a finished charge hits
on impact.

**Charging** (Prince, Dark Prince, Battle Ram, Ram Rider): they walk at their
normal Medium speed, and after 3 tiles without attacking they charge at Very
Fast speed with a double-damage first hit. Stuns, freezes and knockback
cancel the charge.

**Buildings** lose health over their lifetime - health *is* the clock, so
every point of damage they take shortens the time they have left (the
health bar shows both). They also take a moment to deploy (1s; Mortar and
X-Bow 3.5s, Golem 3s among troops). The Tesla hides underground while idle:
troops can't target it, only spells.

**Siege**: the X-Bow and Mortar lock onto the first ground target in range -
troops or buildings - and stay on it until it dies or leaves range. The
Mortar can't hit anything within 3.5 tiles.

The **Battle Ram** breaks the moment it hits a building, leaving its two
Barbarians; only the Evolved Battle Ram bounces off and keeps ramming.

**Placement**: troops and buildings can't be deployed on a standing crown
tower's tiles, and a building's own 2x2 footprint can't overlap them either
(once one of your Princess Towers falls, its spot is free to build on).
The Log, Barbarian Barrel and Royal Delivery can only be placed where you
could deploy a troop - your own side (plus the pocket once an enemy Princess
Tower is down); every other spell can be cast anywhere. The red tint while a
card is selected shows exactly where it can't go.

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

### v1.3 rebalance (hybrid: engagements propose, full games decide)

The isolated engagements above had two blind spots: champions never get to
use their abilities well in a 30-second 1-v-1 (so they looked overpowered and
were cut too hard), and a support troop standing alone behind its tower never
gets answered by a spell. v1.3 rebalanced the older cards with a hybrid run:

* **Engagements v2** (`tools/balance.py`): both sides can answer with a Zap,
  Arrows or Fireball when it trades well (chip on the tower counts), and
  champions' abilities are timed by the Expert AI.
* **Full games** (`tools/fullgame.py`): 12,000 complete matches between two
  Skilled AIs with random decks per round; a Bradley-Terry model gives every
  card a strength with an error bar, corrected for the cards it shared decks
  with.
* **Decision** (`tools/balance_v2.py`): a card only moves when the full games
  say it's off - in the engagements' direction when both agree, on the full
  games alone when they're clearly off. Cards that are fine in full games
  never move, whatever the engagements say. A buff that measurably did
  nothing in full games (the AI just doesn't use the card well) is capped at
  +35% so it can't turn into a monster in human hands.
* The 28 cards added in v1.1 (real-game stats) were left exactly as they are.

Three rounds cut the spread of card strength by 30% (sd of strength 0.34 ->
0.24). Champions went from 42-61% to 45-55% win rates and single-target
ranged troops average 51% (50% in a 2,400-game check with Expert AIs).
`tools/balance_data/v2/` keeps the final factors (`snap3.json`), the
before/after reports and the per-card changes (`applied.txt`).

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
  ui.py       shared text / gradient / button helpers
  screens.py  Cards, Settings, Match Stats, Achievements screens
  home.py     the tabbed home screen (Shop / Deck / Battle / Levels / Modes)
  sandbox.py  the Training Sandbox
  modes.py    Special Battles, Draft and Endless Survival
  levels.py   the 30 Levels, the wave runner and the Endless generator
  profile_data.py  gold, shards, card levels, unlocks (profile.json)
  evos.py     Evolution & Hero catalogue;  evo_engine.py  what they do
  achievements.py  milestones + daily first-win bonus
  trophy.py   Trophy Road arenas, trophies and rewards;  trophyroad.py  its screen
  towers.py   Tower Troops;  carddesc.py  the one-line card descriptions
assets/
  sprites/    generated (and user-replaceable) PNGs
  sounds/     generated (and user-replaceable) WAVs
tools/
  balance.py        card benchmark & auto-balancer
  apply_balance.py  writes balanced stats into src/cards.py
```

## Cards included (123, including 8 Champions)

Troops, win conditions, air units, buildings, spawners and spells spanning the
whole roster — Knight, Archers, Giant, Hog Rider, P.E.K.K.A, Wizard, Baby
Dragon, Balloon, Golem, Minions, Musketeer, Valkyrie, Prince, Witch, Cannon,
Inferno Tower, Tombstone, Elixir Collector, Zap, Fireball, Rocket, Lightning,
The Log, Freeze, Poison, and many more.

**New in v1.1** - the 28 cards that were still missing, each with its real
mechanic:

| Card | What makes it tick |
|---|---|
| Berserker | 2-elixir blur of axes (0.6s hits) |
| Firecracker | her firework bursts into 5 sparks that fly on through the target; she hops back after each shot |
| Goblin Gang | 3 Goblins up front, 3 Spear Goblins behind |
| Skeleton Dragons | two splash-spitting bone dragons |
| Rascals | a tanky Rascal Boy and two slingshot Rascal Girls |
| Royal Recruits | 6 shielded spearmen deployed in a long line |
| Royal Delivery | your side only: a crate lands 3s later (area damage) and a Royal Recruit steps out |
| Heal Spirit | jumps in, damages, then heals allies around it in 4 pulses |
| Suspicious Bush | can't be targeted by troops; bursts into 2 Bush Goblins at the first building |
| Goblin Cage | when destroyed, the Goblin Brawler breaks out |
| Goblin Demolisher | throws bombs; below half health he lights his fuse and charges a building |
| Minion Giant | flying, building-targeting, spits toxin from range, can't be knocked back |
| Royal Hogs | 4 river-jumping hogs in a row |
| Mirror | replays your last card one level higher for its cost +1 |
| Goblin Curse | damage over time; enemies that die in it come back as YOUR Goblins |
| Clone | copies your troops in the area as 1-HP clones |
| Vines | roots the 3 highest-HP enemies (fliers are dragged down) and damages them |
| Goblin Drill | tunnels anywhere, surfaces with a knockback blast and spawns Goblins |
| Rune Giant | enchants the 2 nearest allies: every 3rd hit deals bonus damage |
| Void | 3 strikes that hit harder the fewer enemies are inside |
| Fisherman | anchor-hooks ground troops to him (or reels himself to buildings), slowing them |
| Royal Ghost | invisible until he swings, hovers over the river |
| Mother Witch | cursed troops that die turn into Cursed Hogs for her side |
| Phoenix | on death: a blast and an egg that hatches into a new Phoenix |
| Goblin Machine | melee punches plus an independent long-range rocket launcher |
| Ram Rider | charging ram; the rider's bolas snare troops (-70% speed) |
| Ronin | parries a melee hit every 3.5s and reflects double damage |
| Spirit Empress | 3 elixir on foot, or 6 elixir riding her spirit dragon if you can afford it |

The **Furnace** is now a walking troop (as in the real game since 2025) that
drops a Fire Spirit every 7 seconds.

## Notes / simplifications

- Some ultra-unique mechanics are approximated to keep the engine readable
  (e.g. shields, dashes and champion abilities are simplified). Tune or extend
  them in `engine.py` if you want more fidelity.
- Collisions are soft (overlaps are pushed apart over a few frames rather
  than being hard walls), and path-finding only steers around the one
  building/tower in the way (no full maze search - the arena doesn't need
  it).
- Evolutions and Heroes follow the real game's mechanics and timings (from
  the Clash Royale wiki), scaled into this game's numbers. A few details are
  simplified: the Evolved Tesla pulses whenever it "pops up" (finds a target
  after being idle) instead of literally hiding underground, Hero abilities
  fire instantly instead of after their short cast animation, and the Hero
  Ice Wizard / Electro Wizard numbers come from their announcement (the wiki
  pages were still empty).
- Animations are procedural poses of each card's single sprite rather than
  hand-drawn frame-by-frame sprite sheets.
