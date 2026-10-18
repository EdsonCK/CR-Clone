# Clash Clone — Singleplayer

A single-player, Clash-Royale-style real-time strategy game built in **Python +
Pygame**. Build an 8-card deck, then battle an AI on a faithful-shaped arena
(18×32 tiles, two lanes, a river with two bridges, and 2 Princess Towers + 1
King Tower per side). All art is original placeholder art — no copyrighted
assets — and it's fully swappable (see below).

---

## Quick start

**Windows, nothing installed:** download
[`windows/clash-clone-v1.8.0-windows.zip`](windows/clash-clone-v1.8.0-windows.zip)
from this repository (on GitHub: open the file and click *Download raw
file*), right-click it > *Extract All...*, open the extracted `ClashClone` folder and
double-click **ClashClone.exe**. Python, pygame and everything else are
inside the folder (64-bit Windows 10/11). On the blue *"Windows protected
your PC"* box click *More info* > *Run anyway* (it appears for any unsigned
program). Keep the folder together - make a shortcut rather than moving the
.exe. `READ ME FIRST.txt` in the folder has the details and troubleshooting.

**From source (any OS):**

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

**New in v1.5.1**: deck builder **sorting** (level / elixir / rarity / times
used), **Tournament Standard** (level 11) in Special Battles and 2v2, and a
quieter wave cue. See "v1.5.1 changes".

**New in v1.5.0**: 2v2 has **twin King Towers**, a Tornado can **wake the
King** with an enemy Hog Rider, Poison hits in **8 ticks**, and every sprite
and spell effect got an art pass. See "v1.5.0 changes".

**New in v1.4.9**: **Card Mastery** (3 tasks x 3 tiers for every card),
a **2v2 Battle** mode with an AI teammate, a **Windows .exe** that needs
nothing installed, and smaller achievement rewards. See "v1.4.9 changes".

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
  three **daily deals** (one is always free; some are paid in gold). Hero
  coins buy **Level-Up Potions** (see below).
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

## v1.9.0 changes

* **Chaos Draft** (new special mode): draft your deck from pairs as in Draft,
  then take 3 starting upgrades - a rare, an epic and a legendary (you pick
  one of two, the AI gets the other) - then play a Chaos battle vs the
  Master AI (see Special Modes).
* **Every champion and hero gets its own ability button**: the first sits in
  the right margin, the second in the left one, more stack above them
  (handy when Ascension makes several heroes at once).
* **Tie Breaker** is announced: a big red "Tie Breaker" over the arena (with
  the overtime horn) while everything freezes and the towers drain; the
  result screen waits until a tower falls.
* **Upgraded cards are marked in your hand** (Chaos, Chaos Draft, Endless):
  a thin inlaid inner outline with a gem at each corner, in the colour of
  the rarest upgrade on that card (blue rare, pink-magenta epic, shimmering
  gold-cyan-pink legendary) and a small star for a unique modifier. It sits
  inside the card, so it never looks like an Evo (violet glow outside the
  card) or a Hero (gold HERO label) - and both read at once. The Next
  preview shows it too.
* **Tie Breaker engine**: when overtime ends level on crowns, the match
  pauses for 1 s, then every standing tower drains at the same rate (3 s for
  the lowest one) until the first tower falls - its owner loses (both at
  once: a draw). Nothing else moves meanwhile. Before, the game just ended
  on the spot.
* **Balance**:
  * Mini P.E.K.K.A damage +10% (308 -> 339).
  * P.E.K.K.A damage +20% (325 -> 390).
  * X-Bow -10% health (996 -> 896) and 10% slower hit speed (0.30 -> 0.33 s).
  * Firecracker sight 8 tiles (the real game's value) - placed in front of
    your King at the right moment, your Firecracker baits an enemy one
    whose sparks then fly on into your King and wake it. A lone Firecracker
    on a Princess Tower still never wakes the King (both tested).
  * Ram Rider sight 9.5 tiles (like the Hog Rider) so she spots buildings
    from the bridge.
  * Hero Giant's Heroic Hurl no longer stuns or deals landing damage - he
    just throws the troop to the other lane.
  * Evolved Firecracker's embers are now purple with a dark rim (easier to
    see on the grass).
* **Chaos tweaks**:
  * P.E.K.K.A **Execution** now instantly kills any troop or building (not
    towers) under **75%** hp (was 25%, which barely mattered in a battle).
  * **Stone Walls** (+50% tower max hp) now also fully heals your towers.
  * **Rebuild** is Endless-only now: in Chaos it could end an overtime the
    moment it was picked.

## v1.8.0 changes

* **Unique card modifiers** (Chaos and Endless): every card now also has a
  modifier that changes HOW it plays, not just its numbers - a Lava Hound
  that drops pups as it flies, a Barbarian Hut that spawns Mega Knights, an
  X-Bow firing Wizard fireballs at air and ground, an endless Phoenix... They
  join the upgrade pool next to the stat upgrades, one-time each, with a
  rarity by power (see *Unique modifiers* below for all 123).
* **Fix: melee troops chasing an enemy troop past a building** no longer run
  the long way round: they keep checking which way round is shorter as the
  target moves and switch sides when the other way is clearly shorter
  (worst extra detour in a test grid: 3.1 tiles -> 0.7).
* **Hero Berserker** toned down: her frenzy no longer boosts her damage
  (it used to replace each hit with a 3x-strength "bear claws" hit - now she
  just swings every 0.2 s at her normal damage), the frenzy lasts 4 s like
  the real game, and there's a 0.5 s wind-up when you activate it before she
  moves or attacks.
* **Spawner buildings** (Barbarian Hut, Goblin Hut, Tombstone) send out their
  first wave as soon as they're placed instead of waiting a full spawn
  interval. (Goblin Drill keeps its own timing; troop spawners like the
  Witch are unchanged.)

## v1.7.0 changes

* **Chaos mode** (Modes tab): a 1v1 battle against the Master AI where every
  45 s both sides pick one of two upgrades of the same rarities - rarer as
  the match goes on, two legendaries in overtime, nothing stacks. A
  countdown chip sits next to the match timer; the enemy's picks pop up in
  the arena and fill the right margin. See *Chaos* under *Special Modes*.
* **The AI plays its upgrades**: it reads its own cards through their
  upgraded copies (cost, range, unit count, spell radius...), favours cards
  it has upgraded, lets buffed towers handle small pushes, spends more freely
  with elixir boons and commits to bigger pushes with army boons. With no
  upgrades it plays exactly as before (checked move by move). Tuned in
  Chaos against the plain Master AI with the same upgrades: it wins 58%
  (56 of 96 games).
* **Win-condition card upgrades** for Chaos (Endless still bans those
  cards): Colossus Giant, Titan Golem, Hog Stampede (+1 Hog), Rampage, Bomb
  Bay Balloon, Royal Cannon, Magma Core Lava Hound, Battering Rams,
  Demolition Squad, Bone Bomb, Goblin Siege Tower, Tesla Armor, Golden
  Golem, Glacier, Royal Drove, Bola Master, Runemaster, Toxic Titan, Goblin
  Grove.
* **Endless: Witch nerf** - Coven Mother is now 2x spawn speed (was 3x) and
  one-time (no more 9x Witches).
* **Fix: troops can't be walled in behind the King any more.** A building
  placed against the King and the back wall used to trap troops dropped
  behind the King until it expired (and made an endless Skeleton factory
  with the Witch). Troops now go round the open side, and any ground troop
  that stops making progress for a second plans a way out over the tile
  grid (round buildings and towers, over the bridges). Checked for 432
  troop/building/position combinations.
* **Endless: much gentler long-run scaling** so long runs stay winnable:
  past wave 16 enemies gain +2.5% hp & damage per wave (was +5%) and
  bosses +10% per boss wave (was +22%). A wave-44 boss is now x5.6 its
  level-16 self instead of ~x20 (x3 on wave 30, x7 on wave 50).
* **Effects are per side**: Elixir Flow now speeds up only the side that
  took it (it used to change the whole match's elixir rate), and Rebuild
  takes back the crown the fallen tower gave away.

## v1.6.1 changes

* **Level-Up Potion** (Shop, 3 Hero coins): use it on a card from the Cards
  screen and for one real hour that card plays at your King level (pink
  level badge with a countdown) - see *Level-Up Potion* below.
* **Endless: upgrades every 4 waves** (waves 4, 8, 12...) instead of 5.
* **Endless: ranged enemies are fair again.** Boss multipliers and the
  per-wave power growth now add only **health** to ranged enemies (Three
  Musketeers, Wizards, Executioners...) and to enemy spells - they still hit
  as hard as their level, but no longer like a Mini P.E.K.K.A. Melee enemies
  are unchanged.
* **Endless: ~20% fewer troops per wave**, and the extra growth past wave 15
  is halved. Bosses are unchanged.
* **Every upgrade either stacks or is one-time**, and the pick card says
  which ("Stacks - you have x2" / "One-time upgrade"). One-time upgrades
  never come back once taken (Bone Legion, Fireball Breath, Empress
  Ascendant, Twin Souls, Overgrowth, Flawless Mirror, Ascension, Thrift).
  Everything else stacks for real: unit counts add up (+5 Skeletons per
  pick...), repeats add up (Army of the Dead rises 2 more times per pick),
  **Elixir Pump gives +1 elixir per pick** (2, then 3...), Ice Wizard
  freezes 1 s longer per pick, and tower **damage, range and health** boons
  multiply / add each time (Frost and Cannon Towers too). Rapid Fire now
  also speeds up the Dagger Duchess.
* **Range upgrades carry sight**: a Musketeer with double range also spots
  enemies twice as far away and stops twice as far from the enemy spawn.
* **Boons never depend on your deck** - every boon can come up whatever
  you play (only Rebuild waits until a Princess Tower has fallen).
  "Veteran" (+3 levels) comes up a third as often as the other card
  upgrades, so the fun ones show up more.
* **Fix: troops placed behind the King Tower** in Levels and Endless walked
  round the King on the wrong side and switched lanes. They now always go
  round on their own lane's side (checked for every troop and squad
  position behind the King, in Endless and in battles).

## v1.6.0 changes - Endless upgrades

* **Pick an upgrade every 5 waves** (every 4 since v1.6.1). After waves 5, 10, 15... Endless
  Survival pauses and offers two upgrades that last for the rest of the run
  (click one, or press 1 / 2):
  * a **card upgrade** for one of the cards in your deck - every card you
    can play in Endless has at least one (107 in all, see the table below),
    and any card can also roll **Veteran** (+3 levels for that card);
  * a **boon** for your towers or your whole side (20 of them).

  Upgrades stack (pick Royal Training three times and every card is +3
  levels) and some are deliberately overpowered - this is the first step
  towards a Chaos mode. The upgrades you have are listed in the left margin
  (hover for details) and on the end-of-run screen.
* **Endless keeps getting harder** instead of flattening out once enemies
  hit level 16 (wave 16):
  * every wave after that adds **+5% hp and damage** to all enemies
    (+2.5% since v1.7.0)
    (compounding: x2 by wave 30, x3.2 by 40, x5.3 by 50) and the waves keep
    getting **bigger** (extra troops on top of the usual growth);
  * **bosses** grow +22% per boss wave after wave 15 (x2 on wave 20, x2.9 on
    30, x4.3 on 40, x6.4 on 50 - on top of the wave's power); wave 20+ brings
    **two bosses**, wave 35+ a **Boss Rush** of three;
  * from **wave 30, bosses move and attack faster** - +4% per wave, up to
    double speed (shown on the boss banner);
  * big late waves arrive faster so they don't trickle in over the timeout.
* **Bigger Endless rewards**: gold grows with every wave, plus gems every
  10 waves (double past 30), a Hero coin and King XP every 10 waves and an
  Evo shard every 15 (see *Endless Survival*).

### Card upgrades

(* = win condition: Chaos only. In Chaos nothing stacks.)

| Card | Upgrade | What it does | Rarity | In Endless |
|---|---|---|---|---|
| Archer Queen | **Royal Volley** | Shoots twice as fast. | epic | stacks |
| Archers | **Twin Volley** | Archers shoot twice as fast with +2 range. | epic | stacks |
| Arrows | **Arrow Storm** | 2 more volleys at the same spot. | epic | stacks |
| Baby Dragon | **Fireball Breath** | Every breath deals a Fireball's damage. | legendary | one-time |
| Balloon * | **Bomb Bay** | +50% damage; its death bomb is 2.5x stronger. | epic | stacks |
| Bandit | **Gang of Thieves** | +1 Bandit. | epic | stacks |
| Barbarian Barrel | **Barrel of Brutes** | +3 Barbarians in the barrel, double roll damage. | epic | stacks |
| Barbarian Hut | **War Camp** | Spawns Barbarians 2.5x as often. | epic | stacks |
| Barbarians | **Horde of the North** | +4 Barbarians. | epic | stacks |
| Bats | **Bat Cloud** | +7 Bats. | rare | stacks |
| Battle Healer | **Field Medic** | Every swing heals all your troops on the whole arena (not buildings), 50% more per pick. | legendary | stacks |
| Battle Ram * | **Battering Rams** | +50% hp, 2 more Barbarians inside. | rare | stacks |
| Berserker | **Frenzy** | Swings twice as fast and heals 40% of the damage she deals. | epic | stacks |
| Bomb Tower | **Carpet Bombing** | 50% wider blasts, +50% damage. | epic | stacks |
| Bomber | **Mega Bomb** | Bombs deal 2.5x damage over a 30% wider blast. | epic | stacks |
| Boss Bandit | **Kingpin** | Double damage, +50% hp. | epic | stacks |
| Bowler | **Strike!** | Boulders hit 50% harder and knock back 3x as far. | epic | stacks |
| Cannon Cart | **Siege Cart** | Double hp and damage. | epic | stacks |
| Cannon | **Cannon Battery** | Fires twice as fast and lasts twice as long. | epic | stacks |
| Clone | **Twin Souls** | Clones keep half of the original's hp (not 1). | legendary | one-time |
| Dark Prince | **Dark Shockwave** | Wider splash (+1 tile) that knocks enemies back. | epic | stacks |
| Dart Goblin | **Rapid Darts** | Throws 3x as fast. | epic | stacks |
| Earthquake | **Tectonic Shift** | Triple damage, 40% wider. | epic | stacks |
| Electro Dragon | **Storm Dragon** | Lightning chains to 6 more targets over a longer reach. | epic | stacks |
| Electro Giant * | **Tesla Armor** | His counter-zap hits twice as hard over a wider area. | epic | stacks |
| Electro Spirit | **Thunder Spirit** | +1 Electro Spirit; zaps chain to 8 more targets over a longer reach. | epic | stacks |
| Electro Wizard | **Storm Caller** | Zaps 2 more targets at once, +50% hp. | epic | stacks |
| Elite Barbarians | **Endless Rage** | Permanently raged: +35% speed and attack speed, +30% hp. | epic | stacks |
| Elixir Collector | **Elixir Pump** | +1 elixir from every pump (2, then 3...). | legendary | stacks |
| Elixir Golem * | **Golden Golem** | Double hp, and it no longer gives the opponent elixir. | rare | one-time |
| Executioner | **Headsman** | Axe 80% stronger with a 30% wider swing. | epic | stacks |
| Fire Spirit | **Inferno Spirits** | +2 Fire Spirits, +50% blast damage. | epic | stacks |
| Fireball | **Meteor** | Double damage, 40% wider. | epic | stacks |
| Firecracker | **Grand Finale** | Double damage and twice the sparks. | epic | stacks |
| Fisherman | **Master Angler** | Hook recharges 3x as fast, double damage. | epic | stacks |
| Flying Machine | **Gunship** | Shoots twice as fast with double hp. | epic | stacks |
| Freeze | **Ice Age** | Freezes twice as long, 50% wider. | epic | stacks |
| Furnace | **Spirit Forge** | Also spawns an Ice, Electro and Heal Spirit with every Fire Spirit (4x the spirits; more each pick). | legendary | stacks |
| Giant * | **Colossus** | Double hp, +50% damage. | epic | stacks |
| Giant Skeleton | **Doomsday Bomb** | His bomb is 3x stronger and 40% wider. | legendary | stacks |
| Giant Snowball | **Avalanche** | 60% wider and freezes for 1.5 s (more per pick). | epic | stacks |
| Goblin Barrel | **Barrel Bombardment** | +5 Goblins in the barrel. | epic | stacks |
| Goblin Cage | **Goblin Zoo** | Double hp; +2 Brawlers break out. | epic | stacks |
| Goblin Curse | **Hex Storm** | 60% wider and lasts 50% longer. | epic | stacks |
| Goblin Demolisher | **Demolition Expert** | Double damage, 30% wider blasts. | epic | stacks |
| Goblin Drill | **Tunnel Network** | Lasts 2.5x as long, spawns twice as fast. | epic | stacks |
| Goblin Gang | **Goblin Army** | The Gang comes back 2 more times, 6 s apart. | epic | stacks |
| Goblin Giant * | **Goblin Siege Tower** | +2 Spear Goblins on his back (and when he falls), +30% hp. | epic | stacks |
| Goblin Hut | **Goblin Fortress** | +2 Spear Goblins per spawn. | epic | stacks |
| Goblin Machine | **Mark II** | Rocket hits 3x harder, +50% hp. | epic | stacks |
| Goblins | **Goblin Mob** | +3 Goblins. | rare | stacks |
| Goblinstein | **Mad Experiment** | Doctor and Monster: double hp and damage. | epic | stacks |
| Golden Knight | **Golden Glory** | Double hp and damage. | epic | stacks |
| Golem * | **Titan Golem** | +50% hp and 2 more Golemites when it falls. | epic | stacks |
| Graveyard | **Necropolis** | Lasts twice as long over a 30% wider area. | epic | stacks |
| Guards | **Royal Guard** | +3 Guards, shields doubled. | epic | stacks |
| Heal Spirit | **Spring of Life** | Heals 3x as much over a 60% wider area. | epic | stacks |
| Hog Rider * | **Hog Stampede** | +1 Hog Rider. | legendary | stacks |
| Hog Rider * | **Rampage** | Hits 50% faster. | rare | stacks |
| Hunter | **Big Game Hunter** | Double damage and +1.5 range. | epic | stacks |
| Ice Golem * | **Glacier** | +50% hp; its death freezes-slow is far stronger. | rare | stacks |
| Ice Spirit | **Blizzard Spirits** | +2 Ice Spirits, freezing 1.5 s longer. | epic | stacks |
| Ice Wizard | **Absolute Zero** | Freezes what he hits (1 s more per pick) instead of slowing. | legendary | stacks |
| Inferno Dragon | **Twin Infernos** | +1 Inferno Dragon. | epic | stacks |
| Inferno Tower | **Hellfire Core** | Double hp, damage and lifetime. | epic | stacks |
| Knight | **Paladin** | +120% hp; hits knock back and heal him for half the damage. | epic | stacks |
| Lava Hound * | **Magma Core** | +4 Lava Pups when it pops, +30% hp. | epic | stacks |
| Lightning | **Thunderstorm** | Strikes 2 more times at the same spot. | legendary | stacks |
| Little Prince | **Royal Bodyguard** | Double hp and damage. | epic | stacks |
| Lumberjack | **Berserk Axe** | Chops twice as fast. | epic | stacks |
| Magic Archer | **Arcane Arrows** | Arrows deal 2.5x damage. | epic | stacks |
| Mega Knight | **Titan Slam** | His landing deals 4x damage over a wider area. | legendary | stacks |
| Mega Minion | **Mega Mega Minion** | Double hp and damage, hits splash. | epic | stacks |
| Mighty Miner | **Diamond Drill** | Double damage, +50% hp. | epic | stacks |
| Miner | **Iron Miner** | Double hp, triple damage. | epic | stacks |
| Mini P.E.K.K.A | **Pancake Fury** | +50% damage and heals 60% of the damage dealt. | epic | stacks |
| Minion Giant * | **Toxic Titan** | Double hp, +50% damage. | rare | stacks |
| Minion Horde | **Endless Horde** | +3 Minions, and the Horde comes back once more 6 s later. | legendary | stacks |
| Minions | **Minion Squadron** | +3 Minions. | rare | stacks |
| Mirror | **Flawless Mirror** | Mirrored cards cost the same as the original (not +1). | epic | one-time |
| Monk | **Grandmaster** | Double damage, heals 50% of it. | epic | stacks |
| Mortar | **Artillery Barrage** | Fires 3x as fast. | legendary | stacks |
| Mother Witch | **Coven Queen** | Shoots twice as fast; cursed troops stay her Hogs twice as long. | epic | stacks |
| Musketeer | **Musket Squad** | +2 Musketeers every time you play her. | legendary | stacks |
| Musketeer | **Sharpshooter** | Musketeer range +100% (she stops twice as far away). | epic | stacks |
| Night Witch | **Night Terror** | +2 Bats per summon, twice as often. | epic | stacks |
| P.E.K.K.A | **Executioner's Blade** | Double damage and heals 30% of it. | epic | stacks |
| Phoenix | **Eternal Flame** | Double hp and damage. | epic | stacks |
| Poison | **Plague** | Double damage, 45% wider cloud. | epic | stacks |
| Prince | **Royal Lance** | Charge hits twice as hard, +50% hp. | epic | stacks |
| Princess | **Triple Shot** | Shoots 3x as fast. | legendary | stacks |
| Rage | **Bloodlust** | Lasts twice as long over a 50% wider area. | epic | stacks |
| Ram Rider * | **Bola Master** | +50% hp and damage. | rare | stacks |
| Rascals | **Rascal Crew** | +1 Rascal Boy and +2 Rascal Girls. | epic | stacks |
| Rocket | **Warhead** | Double-wide blast, +50% damage. | epic | stacks |
| Ronin | **Sword Saint** | Parries twice as often, +50% damage. | epic | stacks |
| Royal Delivery | **Royal Shipment** | +2 Royal Recruits in the delivery. | epic | stacks |
| Royal Ghost | **Phantom Lord** | Double damage, swing 50% wider. | epic | stacks |
| Royal Giant * | **Royal Cannon** | +2 range, +50% damage. | epic | stacks |
| Royal Hogs * | **Royal Drove** | +2 Royal Hogs. | epic | stacks |
| Royal Recruits | **Royal Legion** | +3 Recruits (up to 12), shields doubled. | epic | stacks |
| Rune Giant * | **Runemaster** | Enchants 2 more allies with double the bonus. | epic | stacks |
| Skeleton Army | **Army of the Dead** | Skeleton Army rises 2 more times at the same spot, 10 s apart. | legendary | stacks |
| Skeleton Barrel * | **Bone Bomb** | +6 Skeletons in the barrel. | rare | stacks |
| Skeleton Dragons | **Bone Wyverns** | +2 Skeleton Dragons. | epic | stacks |
| Skeleton King | **Lich Lord** | +60% hp and a 50% wider slam. | epic | stacks |
| Skeletons | **Bone Legion** | Skeletons always come out Evolved. | legendary | one-time |
| Skeletons | **Skeleton Squad** | +5 Skeletons. | epic | stacks |
| Sparky | **Overcharged** | Sparky charges 60% faster. | legendary | stacks |
| Spear Goblins | **Spear Volley** | +3 Spear Goblins, throwing twice as fast. | epic | stacks |
| Spirit Empress | **Empress Ascendant** | Always her flying form, for 3 elixir. | legendary | one-time |
| Suspicious Bush * | **Goblin Grove** | +3 Goblins burst out of the bush. | rare | stacks |
| Tesla | **Overclocked** | Double damage, 50% faster, +2 range. | epic | stacks |
| The Log | **Mighty Log** | 2.5x damage, 50% wider. | epic | stacks |
| Three Musketeers | **Six Musketeers** | +3 Musketeers for the same 9 elixir. | legendary | stacks |
| Tombstone | **Honor Guard** | Spawns Guards instead of Skeletons (+1 per spawn each extra pick). | epic | stacks |
| Tornado | **Hurricane** | Triple duration and damage, 30% wider pull. | epic | stacks |
| Valkyrie | **Whirlwind** | Spins 60% faster with a 40% wider spin. | epic | stacks |
| Vines | **Overgrowth** | Vines are permanent: they grow straight back where you cast them (your 3 newest patches stay). | legendary | one-time |
| Void | **Black Hole** | 60% wider, with twice the strikes. | epic | stacks |
| Wall Breakers * | **Demolition Squad** | +2 Wall Breakers, +50% blast damage. | rare | stacks |
| Witch | **Coven Mother** | Summons skeletons twice as fast. | legendary | one-time |
| Wizard | **Fire Mage** | Fireballs knock enemies back and splash 30% wider. | epic | stacks |
| X-Bow | **Gatling Bow** | Double damage and hp. | epic | stacks |
| Zap | **Chain Zap** | Zaps 2 more times at the same spot. | epic | stacks |
| Zappies | **Zap Squad** | +3 Zappies. | epic | stacks |

### Boons

| Boon | What it does | Rarity | In Endless |
|---|---|---|---|
| **Elixir Flow** | 1.5x elixir for the rest of the run. | legendary | stacks |
| **Sharpshooter Towers** | Princess Towers deal +75% damage per hit. | epic | stacks |
| **Rapid Fire** | All your towers shoot 50% faster. | epic | stacks |
| **Watchtowers** | All your towers reach 2.5 tiles further. | rare | stacks |
| **Stone Walls** | All your towers get +50% max hp and fully heal. | epic | stacks |
| **Restoration** | All your towers fully heal. | rare | stacks |
| **Rebuild** | Fallen Princess Towers are rebuilt at full hp. | legendary | stacks |
| **Frost Towers** | Tower shots slow enemies by 35% for 1.5 s (each pick slows harder and longer). | rare | stacks |
| **Cannon Towers** | Tower shots splash 1.5 tiles (+1 tile per extra pick). | epic | stacks |
| **King's Wrath** | Your King Tower wakes up now and deals double damage. | rare | stacks |
| **Royal Training** | Every card in your deck +1 level. | epic | stacks |
| **Royal Academy** | Every card in your deck +2 levels. | legendary | stacks |
| **Ascension** | Every card in your deck that has an Evolution evolves, and every one with a Hero becomes one. | legendary | one-time |
| **Battle Hardened** | All your troops and spells: +30% hp and damage. | epic | stacks |
| **Swiftness** | All your troops move and attack 20% faster. | epic | stacks |
| **Thrift** | Every card costs 1 elixir less (min 1). | legendary | one-time |
| **Bounty Hunter** | +0.2 elixir for every enemy you kill. | epic | stacks |
| **War Chest** | +3 elixir at the start of every wave. | epic | stacks |
| **Second Wind** | Your towers heal 20% at the start of every wave. | rare | stacks |
| **Spell Mastery** | Your spells: +30% radius and +50% damage. | epic | stacks |

### Unique modifiers

Every card also has a modifier that changes how it plays (one-time; in Chaos and Endless, * = win condition: Chaos only). Code: src/chaos_mods.py (+ chaos_mods_a/b/c.py), hook points in src/chaos_hooks.py.

| Card | Modifier | What it does | Rarity |
|---|---|---|---|
| Archer Queen | **Triple Draw** | Every shot is 3 arrows at 3 different targets. | epic |
| Archers | **Arrow Rain** | Every 5 s each Archer calls an arrow rain on her target. | epic |
| Arrows | **Paratroopers** | Two Archers parachute in where the volley lands. | epic |
| Baby Dragon | **Dragon Clutch** | 2 Skeleton Dragons hatch when she falls. | epic |
| Balloon * | **Carpet Bomber** | Drops a small bomb every second on whatever it flies over. | legendary |
| Bandit | **Smoke Bomb** | Vanishes (untargetable) for 1.2 s after every hit. | epic |
| Barbarian Barrel | **Barbarian Convoy** | The barrel drops a Barbarian every 1.5 tiles it rolls (3 more). | epic |
| Barbarian Hut | **Mega Barracks** | Spawns a Mega Knight (who lands with his slam) instead of Barbarians. | legendary |
| Barbarians | **War Horn** | When a Barbarian falls, his horn enrages every ally around for 4 s. | epic |
| Bats | **Bat Colony** | Every 4 s each Bat calls another (2 each at most). | epic |
| Battle Healer | **Last Prayer** | When she falls, every friendly troop within 5 tiles is fully healed. | epic |
| Battle Ram * | **Elite Convoy** | Two Elite Barbarians jump out when it breaks (instead of Barbarians). | legendary |
| Berserker | **Feast** | Every kill heals her fully and makes her swing 15% faster (3 times). | rare |
| Bomb Tower | **Cluster Bombs** | Its death bomb scatters 4 more bombs around it. | rare |
| Bomber | **Cluster Bombs** | Every bomb splits into 3 bomblets around it. | epic |
| Boss Bandit | **The Gang** | Two Bandits come with her. | legendary |
| Bowler | **Earthshaker** | Every boulder slows ground troops within 2 tiles by 50% for 2 s. | rare |
| Cannon Cart | **Dig In** | When the cart breaks, the cannon digs in as a Cannon. | epic |
| Cannon | **Rolling Cannon** | When it expires or falls it rolls on as a Cannon Cart. | epic |
| Clone | **Evil Twins** | Also copies the ENEMY troops in the area onto your side (1 hp, up to 6). | legendary |
| Dark Prince | **Dark Leap** | Leaps onto targets 3-5 tiles away with a shield slam (splash). | epic |
| Dart Goblin | **Spark Darts** | Shoots Sparky blasts - 50% slower than his darts. | legendary |
| Earthquake | **Aftershock** | Ends with an aftershock that stuns and hurls troops out of it. | epic |
| Electro Dragon | **Static Aura** | Zaps the nearest enemy within 3.5 tiles every second (0.5 s stun). | epic |
| Electro Giant * | **Storm Giant** | Every 2 s lightning arcs from him to up to 3 enemies within 4 tiles. | legendary |
| Electro Spirit | **Spirit Split** | It splits into 2 more Electro Spirits when it zaps (once). | epic |
| Electro Wizard | **Lightning Field** | Every 2 s lightning arcs to up to 3 enemies within 5 tiles (stun). | legendary |
| Elite Barbarians | **Unstoppable** | Can't be stunned, frozen, slowed or rooted. | epic |
| Elixir Collector | **Overflow** | When it's destroyed or runs dry it spills 3 elixir. | rare |
| Elixir Golem * | **Elixir Reversal** | Its Elixir Blobs pay YOU their elixir instead of the opponent. | legendary |
| Executioner | **Vortex Axe** | His axe drags the enemies it hits toward him. | epic |
| Fire Spirit | **Chain Reaction** | Each blast lights another Fire Spirit - three in a row. | epic |
| Fireball | **Napalm** | The ground burns: 3 more fire bursts, a second apart. | epic |
| Firecracker | **Big Finish** | Goes out with a Fireball-sized blast. | rare |
| Fisherman | **Tidal Wave** | Lands with a wave that throws enemies back and slows them. | rare |
| Flying Machine | **Bombing Run** | Drops a bomb on ground troops below it every 3 s. | epic |
| Freeze | **Shatter** | When the ice breaks, everything that was frozen shatters for heavy damage. | epic |
| Furnace | **Dragon Forge** | Forges a Baby Dragon instead of a Fire Spirit (a bit less often). | legendary |
| Giant * | **Leaping Giant** | Dashes onto targets 3-6 tiles away, and after each punch leaps back to dash in again. | legendary |
| Giant Skeleton | **Bomb Carrier** | Drops a lit bomb behind him every 4 s. | legendary |
| Giant Snowball | **Rolling Snowball** | Keeps rolling on: 3 more slowing hits, 2 tiles apart. | rare |
| Goblin Barrel | **Brawler Barrel** | A Goblin Brawler rolls out with the Goblins. | epic |
| Goblin Cage | **Snap Trap** | Snaps shut on the nearest enemy troop within 2.5 tiles - rooted for 3 s (every 6 s). | epic |
| Goblin Curse | **Goblin Plague** | A Goblin pops out of the cursed ground every second (5 in all). | epic |
| Goblin Demolisher | **Last Resort** | Blows up when destroyed and 3 Goblins scramble out. | epic |
| Goblin Drill | **Tunnel Hop** | When it caves in, it resurfaces once 4 tiles further on. | epic |
| Goblin Gang | **Big Brother** | A Goblin Giant comes with the Gang. | legendary |
| Goblin Giant * | **Rocket Riders** | The Spear Goblins on his back throw 3x as fast with 3x the range. | epic |
| Goblin Hut | **Dart Academy** | Trains Dart Goblins instead of Spear Goblins. | epic |
| Goblin Machine | **Self-Destruct** | Explodes when destroyed and its 2 Goblin pilots jump out. | epic |
| Goblins | **Pickpockets** | Every stab steals 0.08 elixir for you. | rare |
| Goblinstein | **Lightning Rod** | Every 2 s a bolt arcs through 3 enemies near the Doctor. | epic |
| Golden Knight | **Midas Touch** | Every troop he finishes off pays you 1 elixir. | legendary |
| Golem * | **Earthshaker** | Every punch is a quake that damages and slows everything around him. | epic |
| Graveyard | **Bone Lord** | When the Graveyard closes, a Giant Skeleton climbs out of it. | legendary |
| Guards | **Phalanx** | Their shields grow back fully 5 s after breaking. | epic |
| Heal Spirit | **Spirit Ward** | Its burst also shields your troops nearby (150 hp). | rare |
| Hog Rider * | **Hog Wild** | When he falls, 2 Royal Hogs charge on. | epic |
| Hunter | **Net Gun** | Every shot nets its target: rooted for 1 s. | epic |
| Ice Golem * | **Blizzard Golem** | A blizzard swirls around him: enemies within 2.5 tiles are slowed by 40%. | epic |
| Ice Spirit | **Frost Nova** | Bursts into a Frost Nova: freezes everything within 3 tiles for 2 s. | epic |
| Ice Wizard | **Blizzard Aura** | A blizzard swirls round him: slows and chills every enemy troop within 3.5 tiles. | epic |
| Inferno Dragon | **Forked Beam** | The beam forks onto the nearest other enemy, burning both. | legendary |
| Inferno Tower | **Ring of Fire** | A ring of fire burns everything within 3 tiles every second. | epic |
| Knight | **Shield Bash** | Every 3rd swing is a shield bash: stuns 1 s and shoves the target back. | rare |
| Lava Hound * | **Pup Bomber** | Drops 2 Lava Pups every 2 s while it flies. | legendary |
| Lightning | **Lingering Storm** | 5 more strikes, one a second, on random enemies near where it struck. | legendary |
| Little Prince | **Royal Retinue** | A Knight and a Princess march with him. | epic |
| Lumberjack | **Rage Trail** | Spills a Rage puddle where he walks every 3 s. | epic |
| Magic Archer | **Ricochet** | Arrows ricochet to the nearest other enemy within 4 tiles for 60% damage. | epic |
| Mega Knight | **Last Stand** | Slams one last time when he falls: triple damage over a wider area, knocking everything back. | epic |
| Mega Minion | **Heavy Payload** | Every 3rd hit drops a payload: big splash and a stun. | epic |
| Mighty Miner | **Dynamite Trail** | Drops a lit bomb behind him every 3 s. | epic |
| Miner | **Prospector** | Every hit on a tower or building digs up 0.25 elixir. | rare |
| Mini P.E.K.K.A | **Pancake Frenzy** | Every kill enrages him (4 s) and heals him 30%. | epic |
| Minion Giant * | **Flying Hive** | 2 Minions buzz out of him every 3 s (8 at most). | legendary |
| Minion Horde | **Dive Bombers** | Every Minion dive-bombs as it falls (splash damage). | epic |
| Minions | **Swarm Call** | Each Minion that falls sends a Bat in its place. | rare |
| Mirror | **Mirror Image** | Mirror becomes a 1-elixir Clone: copies your troops in the area. | legendary |
| Monk | **Healing Palm** | Every strike heals your troops within 3 tiles for its damage. | epic |
| Mortar | **Barbarian Barrage** | A Barbarian drops wherever a shell lands. | epic |
| Mother Witch | **Pied Piper** | Every 4 s turns the weakest enemy troop within 5 tiles (300 hp or less) into a Hog for her side. | legendary |
| Musketeer | **Headshot** | 1 shot in 4 is a headshot for triple damage. | rare |
| Night Witch | **Bat Storm** | Summons 3 Bats twice as often, and 6 burst out when she falls. | legendary |
| P.E.K.K.A | **Execution** | Instantly kills any troop or building (not towers) left under 75% hp. | legendary |
| Phoenix | **Endless Phoenix** | Every reborn Phoenix lays an egg again - she keeps coming back until an egg is destroyed. | legendary |
| Poison | **Spreading Plague** | Poison grows 15% wider and stronger with every tick. | epic |
| Prince | **Skewer** | A charged hit runs through: everything 2-3 tiles behind the target is hit too. | epic |
| Princess | **Flaming Arrows** | Her arrows set the ground ablaze where they land. | epic |
| Rage | **Eternal Rage** | Rage never ends - casting it again moves it (your last one disappears). | legendary |
| Ram Rider * | **Net Rider** | Throws a Hunter's net every 3 s (roots and drags the nearest troop) and, like an Evo Battle Ram, is charged again after every hit, knocking her target back. | legendary |
| Rascals | **Avenge the Boy** | If the Rascal Boy falls, the Girls are enraged for good. | rare |
| Rocket | **Cluster Rocket** | It splits: 4 mini rockets land around the impact. | legendary |
| Ronin | **Iaido** | Every 5 s he dashes through the nearest enemy, cutting everything on the way for double damage. | epic |
| Royal Delivery | **Royal Surprise** | A random royal (Prince, Dark Prince, Royal Giant, Royal Hogs, Princess, Ghost...) comes in the crate too. | legendary |
| Royal Ghost | **Possession** | Troops he finishes rise again as ghostly allies at half hp (3 per Ghost). | legendary |
| Royal Giant * | **Royal Escort** | A Royal Guard joins him every 6 s (up to 4). | epic |
| Royal Hogs * | **Truffle Bombs** | Each hog bursts like a small bomb when it falls. | epic |
| Royal Recruits | **Random Regiment** | 6 of one completely random troop (6 Skeletons... or 6 Sparkies). | legendary |
| Rune Giant * | **Rune Pillar** | Every 4 s her runes flare: your troops within 4 tiles are raged for 2 s. | epic |
| Skeleton Army | **Restless Dead** | Each Skeleton has a 40% chance to rise once more when it falls. | epic |
| Skeleton Barrel * | **Bone Rain** | Drops a Skeleton every 1.2 s on the way (6 in all) before it bursts. | epic |
| Skeleton Dragons | **Bone Rain** | Every other fireball drops a Skeleton where it lands. | epic |
| Skeleton King | **Lord of Bones** | Raises 2 Skeletons beside him every 3 s (10 at most). | epic |
| Skeletons | **Undying Bones** | Every Skeleton pulls itself back together once when destroyed. | rare |
| Sparky | **Shockwave** | Every blast also stuns everything within 3 tiles for 1.5 s. | legendary |
| Spear Goblins | **Pinning Spears** | Spears pin troops in place for 0.6 s. | rare |
| Spirit Empress | **Spirit Court** | Arrives with one of every spirit (Fire, Ice, Electro and Heal). | epic |
| Suspicious Bush * | **Machine in the Bush** | Can't be damaged until it opens - and a Goblin Machine bursts out. | legendary |
| Tesla | **Storm Coil** | Every 2.5 s it arcs to up to 3 enemies within 6 tiles, stunning them. | epic |
| The Log | **Timber!** | A Lumberjack follows the Log out. | epic |
| Three Musketeers | **Last Stand** | When one Musketeer falls, the others are enraged for 6 s and healed 50%. | epic |
| Tombstone | **Tomb of the Giant** | Breaks open into a Giant Skeleton instead of 4 Skeletons. | legendary |
| Tornado | **Wandering Twister** | Lasts 4x as long and wanders forward down the lane, dragging everything with it. | legendary |
| Valkyrie | **Vortex Spin** | Her spin pulls ground troops within 3.5 tiles into her axe. | epic |
| Vines | **Thorn Field** | Every ground troop that walks into the patch is rooted too. | epic |
| Void | **Event Horizon** | Drags enemy troops toward its centre while it strikes. | epic |
| Wall Breakers * | **Demolition Crew** | Each one leaves a Bomber behind in the rubble. | epic |
| Witch | **Bat Witch** | Summons 4 Bats instead of Skeletons. | rare |
| Wizard | **Wall of Fire** | His fireballs leave burning ground behind. | epic |
| X-Bow | **Fireball Bow** | Shoots Wizard fireballs (splash) at air and ground. | legendary |
| Zap | **Ion Storm** | Zaps 4 more times over 4 s, each 20% wider. | epic |
| Zappies | **Short Circuit** | When a Zappy falls it stuns everything within 2.5 tiles for 2 s. | rare |

## v1.5.4 changes

* **Levels reworked**: every one of the 30 levels has new waves, with the
  same themes, bosses and overall difficulty (re-measured against the old
  waves with the defend-only AI and re-tuned level by level). Waves now:
  * **push down both lanes at once** (Two Hogs, Charge!, Avalanche...),
  * bring their own **support spells**: Rage, Heal Spirit (and Clone, if a
    level asks for it) dropped on the wave's own push once it reaches the
    river,
  * call in **reinforcements** mid-wave ("Reinforcements!" shows on screen),
  * swap in new units that fit the theme (Ice Spirits in the Whiteout,
    marching Furnaces, Royal Ghosts in the Dark Alley, Royal Hogs in the
    Stampede, Suspicious Bushes in the Overgrowth, Rage-enchanted escorts in
    the Rune Forge instead of a Rune Giant every wave...).
* **Wave titles match what spawns**: e.g. "Night Shift" is now "Night
  Raid", "Royal Delivery" is "Special Delivery" (and drops one), "The Monk"
  is "Monk and Prince", "Excavation" is "Gold Rush", "Swarm" in the Dragon
  Roost is "Swarm of Wings". A test checks that swarm-named waves hold no
  heavy units and air-named waves only flyers.
* **Endless Survival names its waves from what's in them** (it used to pick
  a random name, so a "Swarm" could be two Giants): each wave is built
  around a theme - swarm, air, heavies, fast rush, ranged or mixed - and named
  after it; boss waves are named after the boss ("P.E.K.K.A Unleashed").
  Endless waves also split across lanes, bring reinforcements and, from wave
  6, the odd Rage or Heal Spirit.
* **No more banner across the arena** when a wave starts: just the outlined
  title (a bit smaller) and its subtitle over the field.
* **Poison** now lasts its real **8 seconds**: the same 392 damage (152 to
  crown towers) in 8 ticks, **one every second**.

## v1.5.3 changes

* **Champion and Hero ability buttons** moved into the scenery margins left
  and right of the arena (with their names underneath), so no arena tile is
  ever covered. In 2v2 the teammate panel moved up to make room.
* **Ice Golem** hp 1127 -> 736: 75% of the way to its real ratio (real
  level-11 1197 x 0.506 = 606).
* **Princess** (and the Tower Princess): dark hair and a dark blue dress
  with light grey trim and sash.
* **Furnace** looks like the real troop: a knight in full dark plate with a
  glowing visor and flame crest, a fire burning behind vertical bars in the
  middle of his breastplate, and a brazier staff he shoots from.
* **Evolution deploy sound**: a short, soft heroic horn call over a gentle
  timpani tap instead of the harp / glockenspiel flourish - about 8 dB
  quieter.
* **Home screen**: every tab sits on a slowly drifting diagonal
  checkerboard - blue for Battle, green for Deck, purple for the Shop,
  maroon for Modes and burnt orange for Levels - and the Battle tab's
  buttons are thick, glossy 3D buttons (with icons on Battle and
  Achievements). The top bar and tab bar are unchanged.

## v1.5.2 changes

* **Music in random order**, in the menus and in battles: a random theme
  each time (never the same one twice in a row) and a new random one when a
  track ends. A brand-new player's first menu track is the original theme;
  after that - and after any update, since your saves are kept - it's
  random from the start.

## v1.5.1 changes

* **Sort your cards** in every deck builder: by level, elixir, rarity or
  times used, with an up/down arrow to flip the order (see *Deck editor*).
* **Tournament Standard in Special Battles and 2v2**: all cards and towers,
  yours included, are level 11 (the AI used to be 12 and you played at
  your own levels).
* **Quieter wave cue** in Levels and Endless: each wave now gets two soft
  war-drum hits and a low horn (a heavier timpani roll for boss waves)
  instead of the full match-start fanfare, mixed well under the music.

## v1.5.0 changes

* **2v2: two King Towers side by side** (each player's own, touching): they
  share one HP pool - a 1v1 King's worth, one health bar across both -
  wake together and each shoots on its own. Your teammate's spells fly from
  its King.
* **King Towers are their real 4x4 size** for hits (they used to be hit
  like a 3x3 Princess Tower). In 2v2 a **Firecracker** shooting a Princess
  Tower from its lane wakes the twin Kings with her sparks; in 1v1 the
  single King stays out of reach, as in the real game.
* **Tornado King activation**: a sleeping King Tower can be targeted when
  it's nearer than its standing Princess Towers (as in the real game), so a
  Tornado that drags a Hog Rider off your Princess Tower onto the King makes
  the Hog hit it and wakes it. The Tornado pulls harder (6 tiles/s, was
  3.4) so this is actually possible: place it on the King's front corner
  (around the tile just inside the King, toward the lane) as the Hog
  arrives. Works in 1v1 and 2v2.
* **Poison**: same total damage (392, 152 to crown towers at level 11) but
  dealt as **8 ticks, one every 0.5 s, over 4 s** (was 49/s for 8 s); the
  cloud pulses on every tick.
* **Spirit Empress** (on her dragon) is not electric any more: a spirit
  blast projectile, no lightning, no stun, new attack sound.
* **Art pass**:
  * every sprite is re-painted with real **cel shading** on all its parts
    (bodies, limbs, weapons, roofs, walls - before only the round parts were
    shaded): a shadow side, a lit rim and soft top-to-bottom form shading;
  * redrawn from scratch: **Hog Rider's hog, Royal Hogs, Cursed Hog, the
    Rhino, Battle Ram, Mortar, Goblin Banner, Bomb Tower, Tombstone,
    Tesla**, and the **Earthquake** and **Arrows** cards;
  * every **spell card** sits on a glowing rune medallion;
  * spells in the arena: **Fireball / Rocket** explode with a white-hot
    flare, flame tongues and a shockwave; **Arrows** rain down as a visible
    volley and stick in the ground; **Earthquake** splits the ground with
    glowing faults and heaving rubble; **Poison** pulses each tick.

## v1.4.9 changes

* **Achievements pay less**: still 52 of them, but each pays about a third
  of the gold (x0.35) and gems (x0.3) and half the Evo shards, Hero coins
  and King XP it used to - all of them together now pay ~19,900 gold,
  ~1,800 gems and ~2,050 XP (was ~57,000 / ~5,900 / ~4,100).
* **Card Mastery** (Cards screen > *Mastery*): win 5 Battles with a card to
  unlock its Mastery (+100 gold), then work on 3 tasks at once, each with 3
  tiers - see *Card Mastery* below.
* **2v2 Battle** (Modes tab): you and an AI teammate against two AIs - see
  *2v2 Battle* below.
* **Windows version**: a ready-to-run `ClashClone.exe` with everything
  included - see *Quick start*.
* The camera nudge on the heaviest hits (added in 1.4.8) is gone - it could
  throw off your timing. (The old shakes - tower destroyed, big spells,
  Mega Knight landing - stay, and Settings > *Screen shake* turns them off.)
* `tests/` holds the regression tests: `python tests/run_all.py`.

## v1.4.8 changes

* **Electric attacks hit the moment they're fired**: Electro Wizard,
  Electro Dragon, Zappies, Goblinstein and the Spirit Empress (in the air)
  no longer throw a slow ball - like Tesla and the Electro Giant's
  counter-zap, the zap lands instantly. Every electric hit draws a new
  lightning bolt (jagged, flickering, glowing, with forks and a flash where
  it lands) that stays pinned to the shooter and the target, so its end is
  always exactly on the target. The **Electro Spirit** and **Electro
  Dragon** chains now ripple outward, **0.2 s per hop**, and the Electro
  Spirit's bolt is thicker. **Sparky**'s blast is now a blue ball of
  lightning that flies 4x faster.
* **Big hits feel big**: Mini P.E.K.K.A (reworked), P.E.K.K.A, Mega Knight,
  Golem, Giant, Prince, Hog Rider, Sparky, Mortar and the other heavy
  hitters get a sub punch, a crack and debris on impact and are louder; the
  very heaviest nudge the camera.
* **All other sounds redone**: every spell's cast and impact (thunder for
  Lightning, a real earthquake, wind for Tornado, the Log rolling, arrow
  volleys...) and the UI clicks are recordings now, and the jingles (match
  start, victory, defeat, crown, King waking, double elixir, overtime,
  abilities, evolutions) are played by a sampled orchestra.
* **New music**: 2 new menu themes and 2 new battle themes - the menu and
  battles now rotate through 4 each (see *Music & sound*).

## v1.4.7 changes

* **New battle sounds**, made from real public-domain recordings instead of
  synthesis: every unit's **attacks** (with 3 random variants each),
  **impacts** of bombs, fireballs and mortar shells, **deploys** (each unit's
  voice + how it lands), **deaths** (humans, goblins, skeletons, giants,
  machines, buildings...), champion / hero / evolution **abilities**,
  buildings **spawning** units, dashes, slams, portals and a crumbling tower.
  Higher quality too: the sound now runs at 44.1 kHz. See *Music & sound*.
* **Tombstone** sends its skeletons out one at a time, 0.25 s apart, from
  the same spot in front of it - a Tombstone on the centre line no longer
  splits its waves between the two lanes.

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
* **Gems** - big achievements (up to 300 for 10,000 trophies), arenas and
  King level-ups. Spend them in the **Shop**: 1000 gold for 60 gems, an Evo
  shard for 40, a Hero coin for 30 (bigger packs a bit cheaper), plus three
  daily deals.
* **Level-Up Potion** - 3 Hero coins in the Shop (*Hero Coin Items*). Open
  a card on the Cards screen and press **Use Potion**: for the next real
  hour (it keeps counting while the game is closed) that card plays at your
  **King level** in Battles, the Trophy Road, Levels and Endless - not in
  Special Battles / 2v2, which are always level 11. The card's level badge
  turns pink with a potion while it lasts and the Cards screen shows the
  time left; using another potion on it restarts the hour. Cards already
  at your King level can't take one.
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

## Card Mastery

Open a card on the **Cards** screen and press **Mastery** (a red dot - and a
gold star on the card's tile - means rewards are waiting).

* **Unlock**: win **5 Battles** with the card in your deck: +100 gold.
* Then the card has **3 tasks running at the same time**, each with
  **3 tiers**:

| Task | Opens | What it asks |
|---|---|---|
| 1 | when Mastery unlocks | win Battles with the card in your deck (10 / 30 / 75) |
| 2 | at card **level 13** | deal damage with it - or, for win conditions (Hog Rider, Golem, Goblin Barrel...), damage to Crown Towers |
| 3 | at card **level 15** | destroy enemy troops with it - or, for cards that rarely kill anything, play it |

* **Rewards**: every task's tier 1 pays **500 gold**, tier 2 **1000 gold**
  and tier 3 **100 gems** (9 tiers per card: 4,500 gold + 300 gems, plus
  the 100 gold for unlocking). Claim them on the Mastery page; the stars
  show how many of the 9 you have.
* The damage / troop / play goals are sized per card from what it really
  does in an average match (`src/mastery_data.py`, measured by
  `tools/mastery_calib.py` over 3000 AI games), so every card takes about as
  long: tier 3 is ~75 wins or ~150-180 matches' worth of that card. Fully
  mastering a card takes a long time even if you play it every game.
* What counts: Battles (Trophy Road and Friendly), Special Battles and 2v2
  - not Levels, Endless or the Sandbox. A task only gathers progress while
  it's open (so level the card up!), and a squad / spawner counts what its
  members and spawns do.

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
| Firecracker | 2 | Her firework and its sparks leave purple, burning, slowing embers behind them. |
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
| Giant | **Heroic Hurl** (2) | Grabs the highest-HP enemy troop within 2 tiles and throws it to the other lane (no damage, no stun - it just has to walk back). |
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

Special Battles (and 2v2) are 3-minute battles with a twist, played at
**Tournament Standard**: every card and every tower - yours, the AIs' and
your teammate's - is **level 11**, whatever your own levels are, so only
decks and play decide. Pick the AI's intelligence at the top of the screen. Each pays gold, and your first win in
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
| 2v2 Battle | you + an AI teammate against two AIs (below) |
| Chaos | always vs the Master AI; both sides pick an upgrade every 45 s (below) |
| Chaos Draft | Draft, then 3 starting upgrades each, then Chaos (below) |

### Chaos

A normal 1v1 battle (3:00 + overtime, Tournament Standard level 11) that is
**always against the Master AI** (the intelligence picker doesn't apply),
where every **45 seconds** both sides get an upgrade from the Endless
catalogue:

* The game pauses and you're offered **two upgrades** - a card upgrade for a
  card in your deck and/or a boon for your towers or your whole side. The AI
  is offered two of **the same rarities** from its own deck and takes one
  straight away (a toast in the arena says what it took; it's also shown
  on your pick screen).
* **Rarity climbs** through the match: the first offer is rare + rare,
  rare + epic or epic + epic; later offers lean epic and legendary, and the
  last possible offer (in overtime) is always **two legendaries**.
* **Nothing stacks**: an upgrade, once taken, leaves that side's pool.
* Odds per offer (rare / epic / legendary for each of the two options):
  offer 1 50 / 50 / 0 (so 25% rare + rare, 50% rare + epic, 25% epic +
  epic), offer 2 38 / 46 / 16, offer 3 25 / 42 / 33, offer 4 12 / 39 / 49,
  offer 5 0 / 35 / 65, offer 6 (overtime, 4:30) always legendary +
  legendary.
* **How the AI picks** (chaos.ai_score): rarity first, then what suits its
  deck and the board - upgrades for its win condition and its expensive
  cards, building on a card it has already upgraded, Elixir Flow / +2
  levels / Thrift highly; Restoration when its towers are hurt, King's Wrath and tower boosts more once it has lost a tower,
  Ascension by how many Evo / Hero cards it has.
* Win-condition cards have upgrades here too (Endless doesn't allow them).
* Endless-only boons are left out: War Chest, Second Wind and Rebuild
  (Rebuild could end an overtime instantly).
* A purple chip next to the match timer counts down to the next upgrade
  (it pulses in the last 5 s and says FINAL before the last one).
* Your upgrades are listed in the left scenery margin and the AI's in the
  right one (hover either for details); both show on the result screen.
* Rewards: a Master-AI special-battle payout plus 5 gold per upgrade you
  took; your first Chaos win adds a Hero coin and 10 gems.

### Chaos Draft

Draft meets Chaos, always against the **Master AI** at Tournament Standard
(level 11 for both sides):

1. **Draft your deck**: pick one card of each pair, the AI gets the other,
   until both have 8.
2. **Three starting upgrades** before the clock starts: pick 1 is two
   rares, pick 2 two epics, pick 3 two legendaries (card upgrades for your
   drafted deck and/or boons). The one you leave **goes to the AI** - or,
   if it's for a card the AI doesn't have, an upgrade of the same rarity
   for one of its own cards. The pick screen shows what the enemy got.
3. **A Chaos battle**: from there it plays exactly like Chaos (an upgrade
   offer every 45 s), with the 3 starting upgrades already in both lists.

Rewards and records work like Chaos (the starting upgrades count toward the
per-upgrade gold); both sides' upgrades are on the result screen.

### 2v2 Battle

Played like the real game's 2v2: four players, **each with their own deck,
hand of 4, next card and elixir bar** (normal elixir speed, double elixir in
the last minute, overtime as usual). The two players of a team share their
towers (two Princess Towers and twin Kings), crowns and the clock, and both can deploy anywhere on their
side of the arena. Everything a player plays - and everything it spawns -
is theirs: champions' ability buttons, Evolution charge, Mirror and damage
stats are per player.

* **Twin King Towers**: each side has two King Towers side by side (each
  player's own) sharing one HP pool, waking together and both shooting.
* **Your teammate** is an AI with its own deck (picked at random from the
  AI decks, named in its panel), at the intelligence chosen at the top of
  the Modes tab, with cards at your deck's level and as many Evolutions /
  Heroes as you bring. Its hand, next card and elixir show in the panel
  right of your half of the arena, and an **"Ally"** marker pops up where it
  plays. It sees your troops as its own, so it won't pile onto a push you
  already answered.
* **The two enemies** are AIs at that same intelligence with level-12 cards
  (like every Special Battle) and different decks.
* No trophies; it pays like the other Special Battles and counts for Card
  Mastery. The Match Stats screen splits You / Ally / Enemies.

**Endless Survival** uses the Levels rules (your Level Deck, no enemy towers,
the miasma) with waves that never end: each wave has a growing elixir budget
spent on stronger and stronger troops (and the odd spell), enemy levels rise
from 11 to 16, and every 5th wave is a boss. Each wave is built around a
theme (a swarm, flyers, heavies, a fast rush, ranged troops or a mix) and
named after what's in it; it may come down one lane, split across both or
call in reinforcements halfway. Rewards grow the deeper you go: wave n pays
8 + n gold (plus 25 gold every 5 waves - wave 10 is worth 185 gold, wave 30
855), every 10 waves adds 5 gems (10 past wave 30), a Hero coin and 5 King
XP, every 15 waves an Evo shard, and each new personal-best 5-wave mark a
Hero coin. Your best wave is saved. After every 4th wave the game pauses
and you **pick one of two upgrades** for the rest of the run - hover the
"Upgrades" panel in the left margin to see the ones you've taken.

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
into the miasma to knock them out. Waves also **support their own push**:
a Rage or Heal Spirit lands on their troops once they reach the river (kill
the push early and it never comes), many waves come down **both lanes at
once**, and some call in **reinforcements** halfway through. You get bonus
elixir when a boss wave starts.

**Difficulty.** Every level was playtested by letting the "Skilled" AI (level 3) defend
with decks built from the presets (win conditions
swapped out) **at the level's recommended card level**:

| Level | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Skilled AI clears | 98% | 88% | 71% | 100% | 98% | 75% | 79% | 38% | 96% | 69% |

| Level | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 |
|---|---|---|---|---|---|---|---|---|---|---|
| Skilled AI clears | 17% | 85% | 60% | 4% | 54% | 27% | 77% | 6% | 19% | 58% |

| Level | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 |
|---|---|---|---|---|---|---|---|---|---|---|
| Skilled AI clears | 73% | 90% | 100% | 10% | 44% | 49% | 6% | 71% | 50% | 69% |

(48 runs per level - 6 decks x 8 games - v1.5.4; the reworked waves were
tuned to the same difficulty as the old ones. Each level has a power factor, `LEVEL_POWER` in
`src/levels.py`, on top of the usual enemy levels - that's the knob to turn
if one feels off. `python tools/level_tune.py [level keys]` replays them and
prints each level's win rate and average stars; `--scale` tries a power
factor before you commit to it.)

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
* **Sort** the collection (bar above it, in every deck builder - battle
  decks, the Level Deck and the custom AI deck) by **Level**, **Elixir**,
  **Rarity** or **Used** (how many times you've played the card in matches,
  counted from v1.5.1). The arrow button flips the order (down = high to
  low, up = low to high); tapping the chosen sort again flips it too. Level
  and Used sorts show the value on each card. Your choice is remembered.

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

**Battle sounds are real recordings.** Every unit's attacks, every splash
impact (bombs, fireballs, mortar shells), every deploy, death, champion /
hero / evolution ability, every spawner (Tombstone, huts, Witch...), every
spell's cast and impact and the UI clicks are built from public-domain
(**CC0**) recordings - swords, bows, muskets, cannons, thunder, wind, an
earthquake, creature and human voices, foley - processed and layered with
numpy, sometimes with synthesised layers on top (electric zaps, fizzing
fuses, magic shimmers). The packs and their authors are listed in
`assets/sounds/CREDITS.txt`.

* each of those sounds has **3 variants** (`<name>_1..3.ogg`) and the game
  picks one at random every time (a tiny 8-bit random generator, never the
  same variant twice in a row), so repeated swings don't sound like a loop;
* each unit has its own mix (a Knight and a Barbarian both swing swords, but
  sound different), and the heaviest hitters (P.E.K.K.A, Mini P.E.K.K.A,
  Mega Knight, Golem, Giant, Prince, Sparky...) get extra weight: a sub
  punch, a crack and debris on impact, louder - the very biggest also nudge
  the camera;
* a match loads the sounds its two decks can need on a background thread
  as it starts (about 1 ms per file), so nothing is read from disk mid-fight.

**Jingles** (match start, victory, defeat, crowns, the King waking up,
double elixir, overtime, abilities, evolutions) are played by a small
**sampled orchestra** - brass, strings, harp, glockenspiel, timpani, snare
from the CC0 VSCO-2 CE library (`tools/sfx/orch.py`, written out in
`tools/sfx/compose.py`).

**Music:** the menu and battles each have **4 themes, played in random
order** - a random one each time you open the menu or start a battle, and
another random one whenever a track finishes (never the same one twice in a
row; the double-elixir "final" version follows the battle theme playing).
On the very first launch (no save data yet) the menu opens with the
original theme; every launch after that - updates included - is random from
the start. Themes 1-2 are synthesised by `src/sounds.py`; the new
themes 3-4 are:

| | menu | battle |
|---|---|---|
| 3 | "Medieval: Minstrel Dance" - RandomMind (CC0 recording) | "Battle Theme A" - cynicmusic (CC0 recording) |
| 4 | "Arena Gates" - composed for the sampled orchestra | "Siege of the Bridge" - composed for the sampled orchestra |

Every battle theme has a faster final-minute version.

Sounds are panned left/right by where they happen. Toggle **Music** (M key)
and **Sound** (N key) anywhere; volumes are in Settings.

**Your own sounds:** drop a WAV into `assets/sounds/` named after the sound
without the number - e.g. `knight_attack.wav` replaces all three Knight
attack variants, `giant_deploy.wav` the Giant's deploy, `die_goblin.wav`
every goblin death, `victory.wav` the victory jingle. It is used and never
overwritten.

**Rebuilding the recorded sounds** (only if you want to change them):
`tools/sfx/` holds the recipes. `pip install numpy scipy soundfile py7zr`,
then `python tools/sfx/render.py --fetch` downloads the CC0 packs and the
orchestral samples once (~2 GB, kept out of the repo) and renders every
sound effect in ~15 s; `python tools/sfx/music.py` builds music themes 3-4
and the jingles. `python tools/sfx/render.py knight` re-renders just one
unit, and `--sheet out.png` draws spectrograms to check them by eye.
Attacks are in `tools/sfx/attack.py`, everything else in
`tools/sfx/events.py`.

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
  sounds.py   sound loading / playback + procedural music & UI sounds
  fx.py       particles & spell visuals
  game.py     window, menus, deck builder, rendering, input, main loop
  ui.py       shared text / gradient / button helpers
  screens.py  Cards, Settings, Match Stats, Achievements screens
  home.py     the tabbed home screen (Shop / Deck / Battle / Levels / Modes)
  king.py     King levels: XP curve, reward track;  kingscreen.py  its screen
  shop.py     Shop offers and prices
  sandbox.py  the Training Sandbox
  modes.py    Special Battles, Draft, 2v2 and Endless Survival
  mastery.py  Card Mastery rules;  masteryscreen.py  its page;
              mastery_data.py  per-card averages that size the goals
  levels.py   the 30 Levels, the wave runner and the Endless generator
  endless_upgrades.py  Endless upgrade catalogue;  endless_ui.py  the pick screen
  chaos.py    Chaos battles (offers, rarities, AI picks);  chaos_mods*.py  the
              unique card modifiers;  chaos_hooks.py  their engine hook points
  profile_data.py  currencies, card / King / Tower Troop levels, unlocks (profile.json)
  savedata.py the save folder outside the game + importing old saves
  evos.py     Evolution & Hero catalogue;  evo_engine.py  what they do
  achievements.py  milestones + daily first-win bonus
  trophy.py   Trophy Road arenas, trophies and rewards;  trophyroad.py  its screen
  towers.py   Tower Troops;  carddesc.py  the one-line card descriptions
assets/
  sprites/    generated (and user-replaceable) PNGs
  sounds/     recorded battle sounds (.ogg) + generated WAVs (all user-replaceable)
tools/
  balance.py        card benchmark & auto-balancer
  apply_balance.py  writes balanced stats into src/cards.py
  sfx/              builds the recorded battle sounds (see Music & sound)
  mastery_calib.py  measures what each card does per match -> mastery_data.py
  windows/          Windows build: ClashClone.spec (PyInstaller), build_windows.bat,
                    READ ME FIRST.txt (goes into the Windows zip)
tests/
  run_all.py        runs every test_*.py (headless, throw-away save folder)
.github/workflows/windows-build.yml   builds the Windows zip on GitHub
                    (Actions tab > Build Windows > Run workflow)
```

### Tests

`python tests/run_all.py` runs the 12 regression tests (about 40 s): pathing,
mechanics, placement, electric attacks, every Evolution and Hero, deck
slots, the home screen, rewards, sounds, music, Card Mastery and 2v2. Add
`-v` to see their output, or a word to run only some (`run_all.py 2v2`).
They never touch your real saves.

### Building the Windows version

The Windows zip in `windows/` (currently v1.8.0) was built with PyInstaller
6.10 and pygame 2.6.1 on Python 3.11 (64-bit). To rebuild it after changing the code: on Windows install
Python 3.11 from python.org and double-click `tools\windows\build_windows.bat`
(result: `dist\ClashClone\ClashClone.exe`), or run the *Build Windows*
workflow on GitHub and download the zip from the run's Artifacts.

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
