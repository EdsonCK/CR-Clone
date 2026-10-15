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

### Your progress carries over to new versions

Since 1.4.4 your saves (profile, Level stars, records, settings, decks) live
in a folder **outside** the game folder, so a new version picks them up:

| System | Save folder |
|---|---|
| Windows | `%APPDATA%\ClashClone` |
| macOS | `~/Library/Application Support/ClashClone` |
| Linux | `~/.local/share/clash-clone` |

(Settings shows the folder and has an **Open save folder** button; set the
`CLASH_CLONE_SAVE_DIR` environment variable to use another one.)

**Coming from 1.4.3 or older?** Unzip 1.4.4 into the same folder as your old
version (so `clash-clone-v1.4.3` and `clash-clone-v1.4.4` sit side by side)
and start it: the first launch imports your old progress automatically. Or
copy `profile.json`, `progress.json` (and any other `.json` saves) from the
old game folder into the save folder by hand. From now on just unzip new
versions anywhere - nothing to copy.

## What's in it (v1.4)

**New in v1.4.5**: collected rewards pop up and fly to the top bar, champion
abilities have a short wind-up, Champions go in the flex or Hero slot, real
sight ranges for the win conditions, everything but slow units moves 10%
slower, and a round of card fixes (Mortar, Cannon, X-Bow, The Log, Dart
Goblin, Archer Queen, Monk, Tomb Queen). See "v1.4.5 changes".

**New in v1.4.4**: real-game **stat ratios** (towers, Hog Rider and the
staple cards follow the real level-11 numbers exactly, everything else was
rebalanced around them), **grid snapping** for every placement, real
**building sizes** (3x3, the Tesla 2x2), lane-true **pathing**, deck slots
**Evo | Flex | Hero**, and saves that survive updates. See "v1.4.4 changes".

**New in v1.4.3**: **King levels** - card upgrades and achievements give
XP that levels up your King Tower (11-16), with 4 rewards on the way to each
level; Princess Towers follow their Tower Troop, which you upgrade with gold
(up to your King level). **Hero coins** (Heroes) and **gems** join gold and
Evo shards, the **Shop** opens (gold, shards, coins and daily deals for
gems), the Trophy Road runs to **10,000 trophies** (an arena every 500, the
Legendary Arena at 6000, bots get +5% elixir per arena from 5500 and level-16
cards from 5000) and there are 52 achievements. Deck slot 3 is now a **flex
slot** (Evolution or Hero). Plus a big mechanics pass: Balloon / Giant
Skeleton / Bomb Tower death bombs on a fuse, Skeleton Barrel pops on
arrival, Rage hits like a Zap, shields soak a whole hit, heavy troops shrug
off knockback (except The Log), the Electro Giant zaps back only who hit
it, stuns reset targeting, crown tower HP numbers and more - see
"v1.4.3 changes" below.

**New in v1.4**: a tabbed home screen like the real game - **Shop**
(placeholder), **Deck**, **Battle**, **Levels** and **Modes** along the bottom,
with Settings, AI Deck, Records, Last Match and How To Play in the three-bar
menu at the top right. The window is wider (540 x 800) and the arena has
camps, tents and torch pillars in its new side margins. A second menu theme
and a second battle theme alternate. Trophy Road gives **+60 trophies** a
win and its bots play **variations** of 22 archetype decks, with more
Evolutions and Heroes the higher you climb.

## Home screen

* **Shop** - spend gems on gold, Evo shards and Hero coins, and grab the
  three **daily deals** (one is always free; some are paid in gold).
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
* **Top bar** - your King level (the blue badge, with its XP ring: click it
  for the King Tower screen), trophies, gold, gems, Evo shards and Hero coins.

## v1.4.6 changes

* **Monk** +10% hp (889 -> 978), to make up for standing still during his
  Pensive Protection (still 80% damage reduction, 4s).

## v1.4.5 changes

* **Reward animations**: every reward you collect - battle rewards,
  achievements, the Shop, the Trophy Road, King rewards - pops up in the
  middle of the screen, one kind after another (trophies, XP, gold, gems,
  Evo shards, Hero coins), and flies to its counter in the top bar, which
  counts up as it lands. Screens without the top bar (battle result,
  Achievements...) show just the icons and numbers along the top for the
  occasion, fading out 2 seconds after the last one lands.
* **Champions** may only sit in the flex slot (2) or the Hero slot (3); the
  deck editor moves them there. Their abilities now have a short wind-up
  before they happen (0.25-0.5s, set per champion: Golden Knight and Boss
  Bandit 0.25s ... Skeleton King 0.5s). The **Monk** can't move or attack
  while his Pensive Protection is up.
* **Movement**: every unit except the Slow ones moves 10% slower (Medium
  1.53, Fast 2.07, Very Fast 2.61 tiles/s); the **Tomb Queen** is Slow.
* **Sight ranges** of the win conditions match the real game: Hog Rider and
  Royal Hogs 9.5 tiles, Balloon 7.7, Giant / Goblin Giant / Royal Giant /
  Electro Giant / Rune Giant 7.5, Golem / Elixir Golem 7, Lava Hound, Battle
  Ram and Ram Rider 5.5 - so buildings lure them from as far as they do in
  Clash Royale.
* **Mortar** +25% hp (885 -> 1106) and its first shot comes 0.4s after it
  locks on (was 1s). **Cannon** hp halfway to its real ratio (982 -> 700).
  **X-Bow** halfway to its real ratio (hp 1183 -> 996, damage 29 -> 25).
* **The Log** (99 -> 135 damage), **Dart Goblin** (138 -> 132 hp) and
  **Archer Queen** (454/107 -> 506/114) on their exact real ratios: the Log
  kills Dart Goblin, Goblins and Princess again, and so does a Valkyrie
  swing on a Dart Goblin.

## v1.4.4 changes

* **Real stat ratios.** Every hp and damage number is the real game's
  level-11 stat x 0.506 (before, damage used x0.544 - a 7% mismatch that
  flipped breakpoints like Fireball vs Musketeer). The crown towers are the
  real level-11 Tower Princess (3052 hp, 109 damage -> 1544 / 55) and King
  Tower (4824 -> 2441 / 55), so a Hog Rider takes 16 tower shots and needs
  10 hits on a tower, like in Clash Royale. Pinned to the exact ratio
  (`cards.ANCHORS`): Hog Rider, Knight, Giant, Valkyrie, Musketeer, Archers,
  Goblins, Skeletons, Baby Dragon, Wizard, Fireball, Zap and Arrows - then a
  new balancing run tuned the other cards around them (see "Card balance").
* **By hand**: Musketeer damage -17% (to the real ratio), Mortar damage
  -25%, Little Prince +16% hp, +5% damage and a
  faster ramp (full speed after 4s instead of 5s).
* **Pathing**: a troop with nothing in sight marches down ITS side of the
  arena: its lane's Princess Tower, then the King - it never wanders over
  to the other lane's tower (only an enemy in sight can draw it across).
* **Grid snapping**: every card - troop, building or spell - lands on the
  tile grid (troops / spells / 3x3 buildings on a tile centre, the 2x2
  Tesla on a tile corner); the placement preview shows the exact tiles.
* **Building sizes** as in the real game: every building is 3x3 except the
  Tesla (2x2), drawn on a stone pad showing its tiles. A building can sit
  right against a tower (the exclusion is just the tower's own tiles) but
  takes more room; spawners, the Elixir Collector and the Goblin Cage have
  a bigger hitbox than defensive buildings.
* **Goblinstein's Monster** targets buildings only; **Tornado** has the real
  5.5-tile radius and pulls harder.
* **Deck slots**: slot 1 Evolution, slot 2 **flex** (Evolution or Hero),
  slot 3 Hero - at most 2 Evolutions or 2 Heroes, never 3.
* **Saves** outside the game folder, imported automatically from your old
  version (see Quick start).

## v1.4.3 changes

* **Towers** reach 8.25 tiles (outranging Furnace and Firecracker) and
  2-shot Goblins; their HP is shown as a number.
* **Targeting**: troops prefer an enemy already in their range; when their
  target walks off they follow only if nothing else is in range; a stun
  (Zap, Electro Wizard...) makes them pick again - building-targeters
  still only pick buildings. Troops placed behind the King go straight to
  their lane.
* **Rage** deals a Zap's damage where it lands (so does the Lumberjack's
  dropped Rage): it kills Bats, Skeletons and Spear Goblins.
* **Evo Elite Barbarians** throw their Rage spear (0.72x damage) at ground
  troops, buildings or crown towers 3.5-5 tiles away, every 5s. **Hero Ice
  Wizard**'s Snowman also works on crown towers.
* **Skeleton Barrel** pops the moment it reaches its building (balloon pop,
  falling barrel, 6 Skeletons).
* **Balloon, Bomb Tower** (1s) and **Giant Skeleton** (2s) drop a bomb on
  death that explodes after a fuse - time to run.
* **Inferno** Dragon / Tower burn much hotter at full ramp (x9 after ~5s).
* **Stats**: Mini P.E.K.K.A +16% damage, Electro Wizard -25%, Ice Wizard
  -10%, flying Spirit Empress -8%, Valkyrie's spin 1.8 tiles, Guards' HP =
  a Skeleton's (their shields stay).
* **Knockback**: Golem, Giant, Royal Giant, Goblin Giant, Electro Giant,
  P.E.K.K.A, Mega Knight, Lava Hound, Skeleton King, Goblin Machine, Mighty
  Miner, Prince, Tomb Queen and Minion Giant can't be pushed - except by The
  Log. Giant Skeleton and Rune Giant still can.
* **Bandit / Boss Bandit** dash from 3.5-5 tiles (a tower lands one shot on
  the way in, the next one mid-dash); after Getaway Grenade the Boss Bandit
  recovers for 1s before dashing back.
* **Shields** take the whole hit that breaks them (no spill-over), and the
  shield bar shows how much is left.
* **Electro Giant** zaps back only the unit that hit it, and only within
  its reach.
* **Buildings** can't be placed on top of other buildings.
* **AI**: no wasted spell on a tower its troops are about to take anyway;
  X-Bow / Mortar / Hog-style pushes only go down a lane with a tower.

## Earlier versions

* **Trophy Road**: a ranked ladder through 21 arenas (Goblin Stadium ->
  Clash Fest at 10,000). Win trophies, lose some, and your trophy count picks
  the bot: the higher you climb, the smarter it plays and the higher its
  cards. Gold, gems, shards and Hero coins line the road.
* **Tower Troops**: Tower Princess, Cannoneer, Dagger Duchess and Royal Chef
  man your Princess Towers, unlocked along the Trophy Road.
* **Battle** the AI: 5 intelligence levels, a 0.5x-2x elixir handicap
  slider, 22 archetype decks (or random / custom), and an AI card level that
  climbs as you beat it.
* **Levels**: 30 themed wave challenges, unlocked by stars.
* **Special Modes**: Triple Elixir, Sudden Death, Mirror Match, Draft, Rage
  Battle, Random Decks, Double Trouble and **Endless Survival**.
* **Progression**: gold, gems, Evo shards and Hero coins, card levels 11-16,
  King levels 11-16, all 43 **Evolutions** and all 18 **Heroes** of the real
  game (as of the Minion Giant update), 5 saved decks, 52 achievements, a
  Shop and a daily first-win bonus.
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

| Trophies | Arenas (one every 500) | Bot |
|---|---|---|
| 0-999 | Goblin Stadium, Bone Pit | Novice |
| 1000-1999 | Barbarian Bowl, Spell Valley | Casual |
| 2000-3499 | Builder's Workshop, P.E.K.K.A's Playhouse, Royal Arena | Skilled |
| 3500-4999 | Frozen Peak, Jungle Arena, Hog Mountain | Expert |
| 5000+ | Electro Valley, Spooky Town, **Legendary Arena (6000)**, Rascal's Hideout, Serenity Peak, Miner's Mine, Executioner's Kitchen, Royal Crypt, Silent Sanctuary, Dragon Spa, Clash Fest (10,000) | Master |

* A win is **+60 trophies** (+4 per crown you won by), a loss **-20**, a
  draw 0. You never drop below the gate of an arena you've reached.
* The bot's cards are level 11 + 1 per 1000 trophies, but never more than
  **one level above your deck's average** - until 5000 trophies, where they
  are always **level 16**.
* From **5500** trophies every arena gives the bot **+5% elixir** (x1.5 at
  10,000).
* The bot plays a **variation** of one of the 22 archetype decks (sometimes a
  random deck): a few cards may be swapped for on-theme alternatives (a Log
  Bait with a Cannon instead of the Inferno Tower, a Prince instead of the
  Knight...), and which cards are its Evolutions and Hero changes every game.
  It brings no Evolutions or Heroes at the start of the road, then 1 Evo
  (from ~1670 trophies), 1 Evo + its Hero (~3340) and the full 2 Evos + Hero
  from 5000 on. It also brings a Tower Troop you could have unlocked by then.
  The decks and their swaps are `AI_DECK_PRESETS` / `AI_DECK_VARIANTS` in
  `src/cards.py`.
* **Road rewards** every 100 trophies (gold; every new arena adds gems and
  3 Evo shards or 3 Hero coins, taking turns) are paid once, the first time
  you reach them. The Trophy Road
  screen shows the whole road and points at your next reward.

Tune it in `src/trophy.py` (arenas, trophies per win/loss, rewards).

## Tower Troops

The troop on your Princess Towers is picked per deck: click the tower chip
at the top right of the deck editor to cycle through the ones you own. Stats
are the real game's ratios against the Tower Princess.

| Troop | Unlock | What it does |
|---|---|---|
| Tower Princess | start | the default: long-range arrows, hits air and ground |
| Cannoneer | 3500 (Frozen Peak) | slow, very heavy cannonballs; a little less HP |
| Dagger Duchess | 5000 (Electro Valley) | a magazine of 8 fast daggers; once it's empty she throws slowly, and reloads one dagger every 0.9s while idle |
| Royal Chef | 6500 (Rascal's Hideout) | cooks a pancake (a dial on the tower) and serves it to your strongest troop for **+1 level**; cooks slower while his towers are fighting |

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

Everything is saved in `profile.json` in your save folder (see Quick start;
use Settings > Reset progress to start over).

* **Gold** - from every win (Battles pay more against smarter AIs, higher
  elixir boosts and for crowns), Level wins and new stars, Special Battles,
  Endless waves, achievements and the **first win of the day** (+60 gold,
  +1 shard). Spend it in **Cards** to upgrade a card: 11->12 costs 100,
  then 250, 600, 1200 and 2500 (to 16). Each level is +10% HP and damage
  (spells and the troops spells drop too).
* **King level** (11-16) is your King Tower's level. Card upgrades give
  **XP** (10, 25, 60, 120 and 250 for the five upgrades - a tenth of the
  gold) and so do achievements. Each level needs twice the XP of the one
  before (360, 720, 1440, 2880, 5760): upgrading 24 cards to level 16 is
  just enough for King level 16. The road to each level pays **4 rewards**
  (gold, Evo shards, Hero coins, then gems and gold for the level-up) -
  see them on the **King Tower** screen (click the blue badge).
* **Princess Towers** are as strong as the **Tower Troop** manning them.
  Tower Troops are upgraded with gold on the King Tower screen (same costs
  as cards, no XP) and can't go above your King level.
* **Evo shards** - first clears and 3-star clears of Levels, Battle wins
  (taking turns with Hero coins), arenas, achievements and King rewards.
  **Evolutions** cost 5.
* **Hero coins** - Battle wins, arenas, every 5 Endless waves, first wins
  in Special Battles, achievements and King rewards. **Heroes** cost 8.
  (Saves from before 1.4.3 keep their shards and get 16 Hero coins, plus
  the XP / coins / gems of achievements already claimed.)
* **Gems** - big achievements (up to 1000 for 10,000 trophies), arenas and
  King level-ups. Spend them in the **Shop**: 1000 gold for 60 gems, an Evo
  shard for 40, a Hero coin for 30 (bigger packs a bit cheaper), plus three
  daily deals.
* **Cards screen** - filter by type / Evos / Heroes, read what each card
  does, see its stats
  now and at the next level, upgrade, and unlock its Evolution / Hero.
* **Achievements** - 52 milestones across every mode (battles, three-crown
  wins, crowns, arenas up to 10,000 trophies, Levels and stars, Endless,
  Special Battles, upgrades, maxed cards, King levels, Tower Troops,
  Evolutions and Heroes, the Shop...). Each pays some mix of gold, Evo
  shards, Hero coins, gems and King XP - the biggest pay the most gems.
  Claim the reward on the Achievements screen;
  the Battle tab (and its Achievements button) shows how many are waiting.
* **Sandbox** (Settings) unlocks every Level, Evolution and Hero for free
  play without touching your saved progress.

## Evolutions & Heroes

Your deck's slot 1 is the **EVO slot**, slot 2 the **flex slot** (an
Evolution OR a Hero) and slot 3 the **HERO slot** (the deck editor labels
them; use the < > arrows on a card to move it) - so a deck brings at most 2
Evolutions or 2 Heroes. A card with both unlocked comes as its Hero in the
flex slot - click its "use EVO" chip to bring the Evolution instead.

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

**Heroes** - an unlocked Hero in the flex slot is the Hero version
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

Every placement **snaps to the tile grid**: the preview shows the exact
tiles the card will land on (1 tile for troops and spells, 3x3 for
buildings, 2x2 for the Tesla), green where it's allowed, red where not.
While you place a **building** its attack range is drawn around it (and the
Mortar's blind spot). While you place a troop or building, every **enemy
building** that could shoot it there lights up red with a pulsing red **!**
above it and its range drawn faintly (flying troops ignore ground-only
buildings like the Cannon and X-Bow).

## Special Modes

Special Battles are 3-minute battles with a twist. The AI's cards are always
**level 12** (so upgrading your cards makes them easier); pick its
intelligence at the top of the screen. Each pays gold, and your first win in
each pays a Hero coin.

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
Hero coin every 5 waves; your best wave is saved.

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

The window is 540×800. It can be resized, maximised or made borderless
fullscreen (F11) and the game scales
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
battle deck). Your 8 cards sit at the top in two rows of four - slot 1 is
the EVO slot, slot 2 the flex slot (Evo or Hero), slot 3 the HERO slot;
hover a card and use < > to move it.
The info line shows average elixir, the 4-card cycle cost and the average
card level. Below is the full collection.

* **Left-click** a card to add it (or remove it if it's already in your deck).
* **Right-click** removes a card (in the collection or in your 8 slots).
* The **mouse wheel** only scrolls; you can also drag the scrollbar.
* Hover a card to see its stats. **Cancel** / Esc leaves without saving.
* Max 1 Champion per deck.

### Champions

A Champion goes in your deck's flex slot (2) or Hero slot (3). Once it's on
the field, the yellow button (bottom-left of the arena) activates its ability
for a little extra elixir, after a short wind-up (0.25-0.5s, depending on the
champion). Each ability can be used
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
numbers**, **screen shake**, **borderless fullscreen** (also **F11** or
**Alt+Enter** anywhere; remembered between launches - the game scales up to
fill your screen, keeping its shape), **Sandbox**, **Reset progress**
(asks twice) and **Open save folder** (the folder is shown below it).

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

### v1.4.4 rebalance (around real-ratio anchors)

v1.4.4 put every hp and damage number on one scale (real level-11 x 0.506),
made the crown towers the real level-11 towers and pinned 13 staple cards
to their exact real ratios (`cards.ANCHORS`: Hog Rider, Knight, Giant,
Valkyrie, Musketeer, Archers, Goblins, Skeletons, Baby Dragon, Wizard,
Fireball, Zap, Arrows). The same hybrid run then tuned the other 104 cards
around them - this time including the v1.1 cards - for 5 rounds; Mortar and
Little Prince were set by hand and left alone.

* The spread of card strength fell from 0.277 to 0.156 (0.18 in an
  independent 6,000-game check of the final stats); champions average 53%,
  single-target ranged troops 50%.
* Biggest cuts: Royal Recruits x0.49, Rascals x0.60, Skeleton Dragons x0.60,
  Spirit Empress x0.58, Golem x0.66, X-Bow x0.67, Witch x0.68, Goblin Gang
  x0.70. Biggest buffs: Electro Giant x1.59, Rune Giant / Cannon x1.54,
  Minion Horde x1.53, Goblin Drill x1.48, Heal Spirit x1.46.
* The balancer now scales mixed squads (Rascals, Goblin Gang) and the
  Spirit Empress' dragon form too (before, their changes never reached the
  units on the field).
* Still off, by design: the anchors play as the real cards do in THIS
  engine - Valkyrie ~62% and Knight ~59% are strong, Hog Rider and Giant
  ~41% weak - and the hand-set cards: Little Prince ~59%, Mortar ~37%.
* Levels were re-tuned to their 1.4.3 difficulty (enemy waves x1.12, plus a
  few per-level corrections): the defend-only AI wins as often as before.

`tools/balance_data/v3/` keeps the final factors (`final_factors.json`),
the before / after / verification reports and the per-card changes
(`applied.txt`).

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
  king.py     King levels: XP curve, reward track;  kingscreen.py  its screen
  shop.py     Shop offers and prices
  sandbox.py  the Training Sandbox
  modes.py    Special Battles, Draft and Endless Survival
  levels.py   the 30 Levels, the wave runner and the Endless generator
  profile_data.py  currencies, card / King / Tower Troop levels, unlocks (profile.json)
  savedata.py the save folder outside the game + importing old saves
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
