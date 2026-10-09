# Card balance (v0.3.0)

Every card was benchmarked with `tools/balance.py` (see its docstring for
the full method) and tuned over several frozen-snapshot rounds. A card's
**performance** is its average elixir gain per engagement against the
whole card pool (equal-elixir fights, both attacking and defending, weighted
toward similar-cost cards, extremes trimmed). Damage spells are scored on
their best 40% of targets. 0 = a perfectly fair card.

Method: 5 damped rounds against frozen snapshots (max ±35-50% per card per round), then one targeted pass on the 4 cards that were still far above fair (Inferno Dragon, Little Prince, Sparky, Electro Giant). Total change per card is limited to x0.2-x1.6 power. ⚠ marks cards pinned at that limit: the over-0 ones are mechanic-driven (Inferno Dragon's ramp vs towers), the under-0 ones (huts, Furnace, X-Bow, Lava Hound, Skeleton Barrel, spirits, Goblin Barrel, Graveyard) earn most of their value outside a single engagement - slow value, tanking for other cards, cycling - so they were buffed only up to the cap rather than inflated further.

| Card | Cost | Before | After | Power | Stat changes |
|---|---|---|---|---|---|
| Archer Queen | 5 | -0.12 | +0.61 | x0.94 | HP 500 → 484, dmg 126 → 122 |
| Archers | 3 | -1.46 | +0.19 | x1.58 ⚠ | HP 125 → 147, dmg 42 → 57 |
| Arrows | 3 | -0.52 | -0.03 | x1.33 | dmg 115 → 153, tower dmg 46 → 61 |
| Baby Dragon | 4 | +1.65 | +0.78 | x0.72 | HP 800 → 678, dmg 100 → 85 |
| Balloon | 5 | -0.69 | +0.34 | x1.13 | HP 1050 → 1139, dmg 600 → 627 |
| Bandit | 3 | +8.38 | +0.87 | x0.45 | HP 750 → 503, dmg 160 → 107 |
| Barbarian Barrel | 2 | +1.27 | +0.02 | x0.58 | dmg 120 → 70, tower dmg 48 → 28, spawned units HP x0.76 / dmg x0.76 |
| Barbarian Hut | 7 | -13.99 | -6.70 | x1.59 ⚠ | HP 1300 → 1638, spawned units HP x1.26 / dmg x1.26 |
| Barbarians | 5 | +0.19 | +0.76 | x0.93 | HP 262 → 253, dmg 88 → 85 |
| Bats | 2 | -0.76 | +0.24 | x0.88 | HP 32 → 31, dmg 32 → 30 |
| Battle Healer | 4 | -4.97 | -1.36 | x1.59 ⚠ | HP 810 → 1021, dmg 70 → 88, heal 55 → 69 |
| Battle Ram | 4 | -0.81 | +0.35 | x1.23 | HP 520 → 595, dmg 110 → 118, spawned units HP x1.14 / dmg x1.08 |
| Bomb Tower | 4 | -0.05 | +0.25 | x0.83 | HP 1050 → 957, dmg 180 → 164 |
| Bomber | 2 | -0.62 | +0.27 | x1.17 | HP 130 → 137, dmg 110 → 122 |
| Boss Bandit | 6 | +11.29 | +1.25 | x0.55 | HP 1700 → 1256, dmg 200 → 148 |
| Bowler | 5 | -3.50 | -0.36 | x1.59 ⚠ | HP 940 → 1185, dmg 145 → 183 |
| Cannon | 3 | -0.58 | +0.19 | x0.89 | HP 742 → 700, dmg 127 → 120 |
| Cannon Cart | 5 | +0.74 | +0.55 | x0.81 | HP 600 → 541, shield 440 → 396, dmg 130 → 117 |
| Dark Prince | 4 | +0.90 | +0.65 | x0.85 | HP 680 → 627, shield 180 → 166, dmg 140 → 129 |
| Dart Goblin | 3 | -1.17 | +0.26 | x1.47 | HP 115 → 132, dmg 60 → 77 |
| Earthquake | 3 | -0.16 | -0.06 | x1.04 | dmg 36 → 37, tower dmg 44 → 46 |
| Electro Dragon | 5 | -0.57 | +0.54 | x0.85 | HP 640 → 591, dmg 100 → 92 |
| Electro Giant | 7 | +15.73 | +0.26 | x0.33 | HP 2500 → 1204, dmg 130 → 88 |
| Electro Spirit | 1 | -4.53 | -3.71 | x1.59 ⚠ | HP 90 → 106, dmg 39 → 53 |
| Electro Wizard | 4 | +0.16 | +0.42 | x0.76 | HP 340 → 309, dmg 100 → 84, landing dmg 100 → 84 |
| Elite Barbarians | 6 | -6.35 | +0.94 | x1.58 ⚠ | HP 524 → 659, dmg 180 → 226 |
| Elixir Golem | 3 | +8.51 | +0.56 | x0.49 | HP 1400 → 885, dmg 150 → 117, spawned units HP x0.63 / dmg x0.78 |
| Executioner | 5 | +2.05 | +0.46 | x0.67 | HP 650 → 533, dmg 110 → 90 |
| Fire Spirit | 1 | -2.50 | -1.57 | x1.59 ⚠ | HP 70 → 82, dmg 120 → 162, death dmg 120 → 162 |
| Fireball | 4 | +0.43 | +0.20 | x0.86 | dmg 340 → 294, tower dmg 110 → 95 |
| Flying Machine | 4 | -0.00 | +0.50 | x0.89 | HP 340 → 327, dmg 96 → 89 |
| Furnace | 4 | -7.11 | -5.41 | x1.59 ⚠ | HP 600 → 756, spawned units HP x1.26 / dmg x1.26 |
| Giant | 5 | -5.01 | +0.75 | x1.56 ⚠ | HP 2200 → 2936, dmg 120 → 140 |
| Giant Skeleton | 6 | +1.39 | +0.63 | x0.69 | HP 2100 → 1651, dmg 140 → 123 |
| Goblin Barrel | 3 | -4.90 | -3.46 | x1.59 ⚠ | spawned units HP x1.26 / dmg x1.26 |
| Goblin Giant | 6 | +3.21 | +1.37 | x0.83 | HP 2400 → 2132, dmg 110 → 103, spawned units HP x0.89 / dmg x0.94 |
| Goblin Hut | 5 | -7.40 | -4.03 | x1.59 ⚠ | HP 1000 → 1260, spawned units HP x1.26 / dmg x1.26 |
| Goblins | 2 | -2.65 | -1.33 | x1.59 ⚠ | HP 79 → 93, dmg 47 → 64 |
| Goblinstein | 5 | +8.57 | +0.92 | x0.40 | HP 900 → 570, dmg 110 → 70, spawned units HP x0.63 / dmg x0.63 |
| Golden Knight | 4 | +6.67 | +0.80 | x0.49 | HP 1400 → 979, dmg 170 → 119 |
| Golem | 8 | +2.69 | +0.96 | x0.79 | HP 4200 → 3599, dmg 280 → 258, spawned units HP x0.86 / dmg x0.92 |
| Graveyard | 5 | -5.07 | -3.08 | x1.59 ⚠ | spawned units HP x1.26 / dmg x1.26 |
| Guards | 3 | -2.31 | +0.43 | x1.54 | HP 75 → 87, shield 150 → 175, dmg 60 → 80 |
| Hog Rider | 4 | -2.49 | +0.53 | x1.31 | HP 1000 → 1195, dmg 175 → 193 |
| Hunter | 4 | +3.48 | +0.58 | x0.51 | HP 650 → 463, dmg 45 → 32 |
| Ice Golem | 2 | -0.71 | +0.34 | x1.29 | HP 1200 → 1414, dmg 42 → 46 |
| Ice Spirit | 1 | -4.57 | -4.11 | x1.59 ⚠ | HP 70 → 82, dmg 42 → 57, death dmg 42 → 57 |
| Ice Wizard | 3 | -1.71 | -0.11 | x1.59 ⚠ | HP 310 → 365, dmg 55 → 74, landing dmg 70 → 95 |
| Inferno Dragon | 4 | +24.83 | +4.18 | x0.20 ⚠ | HP 1000 → 447, dmg 45 → 20 |
| Inferno Tower | 5 | +2.80 | +1.03 | x0.35 | HP 1600 → 941, dmg 40 → 24 |
| Knight | 3 | -3.23 | -0.25 | x1.59 ⚠ | HP 690 → 871, dmg 79 → 100 |
| Lava Hound | 7 | -14.41 | -6.67 | x1.59 ⚠ | HP 3000 → 4052, dmg 40 → 47, spawned units HP x1.35 / dmg x1.18 |
| Lightning | 6 | -0.10 | +0.10 | x1.00 | - |
| Little Prince | 3 | +7.39 | +0.92 | x0.20 ⚠ | HP 560 → 250, dmg 60 → 27 |
| Lumberjack | 4 | +2.03 | +0.52 | x0.73 | HP 660 → 564, dmg 175 → 149, spawned units HP x0.85 / dmg x0.85 |
| Magic Archer | 4 | -1.44 | +0.28 | x1.28 | HP 340 → 371, dmg 75 → 88 |
| Mega Knight | 7 | +7.02 | +1.55 | x0.55 | HP 2700 → 1835, dmg 170 → 138, landing dmg 240 → 195, jump dmg 240 → 195 |
| Mega Minion | 3 | +0.17 | +0.48 | x0.76 | HP 350 → 319, dmg 150 → 126 |
| Mighty Miner | 4 | +8.05 | +1.20 | x0.42 | HP 1400 → 904, dmg 32 → 21 |
| Miner | 3 | -1.88 | +0.47 | x1.40 | HP 900 → 1067, dmg 75 → 89 |
| Mini P.E.K.K.A | 4 | -1.73 | +0.29 | x1.06 | HP 642 → 661, dmg 340 → 350 |
| Minion Horde | 5 | +0.93 | +0.54 | x0.59 | HP 90 → 69, dmg 42 → 32 |
| Minions | 3 | -0.82 | +0.25 | x0.96 | HP 90 → 89, dmg 42 → 41 |
| Monk | 5 | +11.02 | +0.96 | x0.38 | HP 1900 → 1020, dmg 120 → 86 |
| Mortar | 4 | +0.38 | +0.57 | x1.02 | HP 800 → 807, dmg 260 → 262 |
| Musketeer | 4 | +0.09 | +0.31 | x1.07 | HP 340 → 348, dmg 120 → 125 |
| Night Witch | 4 | -3.53 | +0.25 | x1.57 ⚠ | HP 560 → 702, dmg 150 → 188, spawned units HP x1.25 / dmg x1.25 |
| P.E.K.K.A | 7 | +9.68 | +1.40 | x0.47 | HP 2600 → 1593, dmg 510 → 392 |
| Poison | 4 | -0.07 | +0.13 | x1.00 | - |
| Prince | 5 | +1.89 | +0.98 | x0.76 | HP 980 → 855, dmg 245 → 214 |
| Princess | 3 | +2.66 | +0.34 | x0.54 | HP 130 → 104, dmg 140 → 93 |
| Rocket | 6 | +0.50 | +0.20 | x0.83 | dmg 700 → 582, tower dmg 280 → 233 |
| Royal Giant | 6 | -2.49 | +1.67 | x1.20 | HP 2100 → 2363, dmg 180 → 192 |
| Skeleton Army | 3 | +2.77 | +1.01 | x0.35 | HP 32 → 19, dmg 32 → 19 |
| Skeleton Barrel | 3 | -5.59 | -5.01 | x1.59 ⚠ | HP 310 → 420, spawned units HP x1.35 / dmg x1.18 |
| Skeleton King | 4 | +10.11 | +0.97 | x0.43 | HP 1800 → 1039, dmg 176 → 131 |
| Skeletons | 1 | -1.26 | -0.46 | x1.59 ⚠ | HP 32 → 38, dmg 32 → 43 |
| Giant Snowball | 2 | -0.01 | +0.01 | x1.00 | - |
| Sparky | 6 | +17.47 | +0.02 | x0.24 ⚠ | HP 1200 → 587, dmg 1050 → 513 |
| Spear Goblins | 2 | +1.20 | +0.22 | x0.77 | HP 52 → 48, dmg 32 → 27 |
| Tesla | 4 | +0.73 | +0.49 | x0.67 | HP 800 → 654, dmg 132 → 108 |
| The Log | 2 | +0.28 | +0.13 | x0.89 | dmg 120 → 106, tower dmg 48 → 43 |
| Three Musketeers | 9 | +6.90 | +1.03 | x0.60 | HP 340 → 264, dmg 120 → 93 |
| Tombstone | 3 | -2.52 | -1.25 | x1.59 ⚠ | HP 400 → 504, spawned units HP x1.26 / dmg x1.26 |
| Valkyrie | 4 | -3.51 | +0.53 | x1.55 ⚠ | HP 880 → 1096, dmg 126 → 157 |
| Wall Breakers | 2 | -2.77 | -0.64 | x1.59 ⚠ | HP 140 → 189, dmg 180 → 212, death dmg 180 → 212 |
| Witch | 5 | -2.34 | +0.37 | x1.17 | HP 460 → 498, dmg 90 → 97, spawned units HP x1.08 / dmg x1.08 |
| Wizard | 5 | -1.91 | +0.47 | x1.29 | HP 340 → 371, dmg 130 → 153 |
| X-Bow | 6 | -7.52 | -4.07 | x1.59 ⚠ | HP 1000 → 1260, dmg 26 → 33 |
| Zap | 2 | +0.01 | +0.04 | x1.00 | - |
| Zappies | 4 | -1.30 | +0.34 | x1.11 | HP 140 → 148, dmg 48 → 51 |

Spread of card performance (standard deviation): **5.78 → 1.77** elixir.

