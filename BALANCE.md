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

## v1.3 rebalance (hybrid run, older cards only)

Power factor applied on top of the v1.2 stats (see README, "v1.3 rebalance").

| Card | Factor | Changes |
|---|---|---|
| archer_queen | x0.88 | hp 484->454; damage 122->115 |
| archers | x1.25 | hp 147->159; damage 57->66 |
| baby_dragon | x0.77 | hp 678->596; damage 85->75 |
| balloon | x0.51 | hp 1139->734; damage 627->495 |
| bandit | x0.88 | hp 503->472; damage 107->101 |
| barbarian_hut | x1.19 | hp 1638->1790; sub_hp_mult 1.26->1.38; sub_dmg_mult 1.26->1.38 |
| bats | x1.14 | hp 31->32; damage 30->33 |
| battle_ram | x1.17 | hp 595->657; damage 118->124; sub_hp_mult 1.14->1.26; sub_dmg_mult 1.08->1.14 |
| boss_bandit | x0.85 | hp 1256->1156; damage 148->136 |
| bowler | x0.86 | hp 1185->1096; damage 183->169 |
| cannon | x1.28 | hp 700->791; damage 120->136 |
| cannon_cart | x0.88 | hp 541->507; shield_hp 396->371; damage 117->110 |
| dark_prince | x0.81 | hp 627->565; shield_hp 166->150; damage 129->116 |
| dart_goblin | x1.13 | hp 132->138; damage 77->83 |
| earthquake | x1.27 | spell_damage 37->47; tower_damage 46->59 |
| electro_giant | x0.87 | hp 1204->1102; damage 88->84 |
| electro_spirit | x1.27 | hp 106->115; damage 53->62 |
| electro_wizard | x1.09 | hp 309->318; damage 84->89; spawn_damage 84->89 |
| elite_barbarians | x0.70 | hp 659->550; damage 226->189 |
| elixir_golem | x1.60 | hp 885->1201; damage 117->138; sub_hp_mult 0.63->0.86; sub_dmg_mult 0.78->0.92 |
| executioner | x0.83 | hp 533->485; damage 90->82 |
| fire_spirit | x1.25 | hp 82->89; damage 162->187; death_damage 162->187 |
| flying_machine | x0.88 | hp 327->313; damage 89->82 |
| giant_skeleton | x0.67 | hp 1651->1353; damage 123->101 |
| goblin_barrel | x1.19 | sub_hp_mult 1.26->1.37; sub_dmg_mult 1.26->1.37 |
| goblin_giant | x0.88 | hp 2132->1957; damage 103->98; sub_hp_mult 0.89->0.82; sub_dmg_mult 0.94->0.90 |
| goblin_hut | x1.28 | hp 1260->1423; sub_hp_mult 1.26->1.42; sub_dmg_mult 1.26->1.42 |
| goblins | x1.28 | hp 93->101; damage 64->75 |
| golden_knight | x0.74 | hp 979->845; damage 119->103 |
| golem | x0.79 | hp 3599->3076; damage 258->237; sub_hp_mult 0.86->0.73; sub_dmg_mult 0.92->0.85 |
| hunter | x1.13 | hp 463->492; damage 32->34 |
| ice_golem | x0.79 | hp 1414->1212; damage 46->42 |
| ice_spirit | x1.13 | hp 82->86; damage 57->62; death_damage 57->62 |
| inferno_dragon | x0.68 | hp 447->369; damage 20->17 |
| inferno_tower | x1.28 | hp 941->1063; damage 24->27 |
| lava_hound | x0.51 | hp 4052->2630; damage 47->37; sub_hp_mult 1.35->0.88; sub_dmg_mult 1.18->0.93 |
| magic_archer | x0.89 | hp 371->356; damage 88->82 |
| mega_knight | x0.73 | hp 1835->1493; damage 138->124; spawn_damage 195->175; dash_damage 195->175 |
| mega_minion | x1.29 | hp 319->349; damage 126->149 |
| mighty_miner | x1.31 | hp 904->1033; damage 21->24 |
| miner | x0.86 | hp 1067->988; damage 89->82 |
| mini_pekka | x0.79 | hp 661->587; damage 350->311 |
| minion_horde | x1.39 | hp 69->81; damage 32->38 |
| minions | x1.22 | hp 89->95; damage 41->47 |
| monk | x0.85 | hp 1020->942; damage 86->79 |
| mortar | x1.20 | hp 807->885; damage 262->287 |
| musketeer | x1.10 | hp 348->360; damage 125->133 |
| night_witch | x0.68 | hp 702->580; damage 188->155; sub_hp_mult 1.25->1.03; sub_dmg_mult 1.25->1.03 |
| pekka | x0.79 | hp 1593->1420; damage 392->349 |
| poison | x1.08 | spell_damage 55->59; tower_damage 22->24 |
| prince | x0.84 | hp 855->783; damage 214->196 |
| princess | x1.10 | hp 104->107; damage 93->99 |
| rocket | x1.14 | spell_damage 582->661; tower_damage 233->265 |
| royal_giant | x0.94 | hp 2363->2268; damage 192->188 |
| skeleton_army | x1.46 | hp 19->22; damage 19->24 |
| skeleton_barrel | x1.26 | hp 420->489; sub_hp_mult 1.35->1.57; sub_dmg_mult 1.18->1.28 |
| skeleton_king | x0.81 | hp 1039->933; damage 131->118 |
| snowball | x1.09 | spell_damage 80->87; tower_damage 32->35 |
| spear_goblins | x1.18 | hp 48->51; damage 27->30 |
| tesla | x1.45 | hp 654->788; damage 108->130 |
| three_musketeers | x1.14 | hp 264->282; damage 93->99 |
| valkyrie | x0.70 | hp 1096->917; damage 157->131 |
| wall_breakers | x1.19 | hp 189->212; damage 212->225; death_damage 212->225 |
| witch | x0.56 | hp 498->372; damage 97->72; sub_hp_mult 1.08->0.81; sub_dmg_mult 1.08->0.81 |
| wizard | x1.05 | hp 371->378; damage 153->158 |
| xbow | x1.31 | hp 1260->1440; damage 33->38 |
| zappies | x1.07 | hp 148->153; damage 51->53 |


## v1.4.4 rebalance (real-ratio anchors, hybrid run, all cards)

All hp / damage are real level-11 stats x 0.506; the towers and 13 anchors
(Hog Rider, Knight, Giant, Valkyrie, Musketeer, Archers, Goblins, Skeletons,
Baby Dragon, Wizard, Fireball, Zap, Arrows) sit exactly on that ratio and
were not tuned, nor were Mortar (damage -25% by hand) and Little Prince
(+16% hp, +5% damage, faster ramp, by hand). Win rates are full-game win
rates (Bradley-Terry, random decks): before = the first measurement of the
run, after = an independent 6,000-game check of the final stats.

| Card | Win rate before | after | Power | Stat changes |
|---|---|---|---|---|
| balloon | 57% | 55% | x0.84 | hp 734->656; damage 460->433 |
| bandit | 52% | 49% | x0.89 | hp 472->445; damage 94->89 |
| barbarian_barrel | 48% | 48% | x1.12 | spell_damage 65->73; tower_damage 26->29; sub_hp_mult 0.76->0.80; sub_dmg_mult 0.76->0.80 |
| barbarian_hut | 47% | 51% | x1.11 | hp 1790->1889; sub_hp_mult 1.38->1.46; sub_dmg_mult 1.38->1.46 |
| barbarians | 51% | 48% | x0.80 | hp 253->226; damage 79->71 |
| bats | 46% | 47% | x1.17 | hp 32->34; damage 31->34 |
| battle_healer | 52% | 52% | x0.89 | hp 1021->961; damage 82->77; heal_on_attack 69->65 |
| battle_ram | 49% | 49% | x0.88 | hp 657->606; damage 115->110; sub_hp_mult 1.26->1.16; sub_dmg_mult 1.14->1.09 |
| berserker | 52% | 50% | x0.96 | hp 453->444; damage 51->50 |
| bomb_tower | 54% | 52% | x0.91 | hp 957->915; damage 153->146 |
| boss_bandit | 46% | 51% | x1.14 | hp 1156->1233; damage 126->134 |
| bowler | 55% | 52% | x0.91 | hp 1096->1046; damage 157->150 |
| cannon | 44% | 50% | x1.54 | hp 791->982; damage 126->156 |
| cannon_cart | 54% | 51% | x0.86 | hp 507->470; shield_hp 371->344; damage 102->95 |
| clone | 47% | 43% | x1.18 | (no stat fields) |
| dark_prince | 54% | 55% | x0.86 | hp 565->525; shield_hp 150->139; damage 108->100 |
| electro_dragon | 54% | 53% | x0.93 | hp 591->570; damage 86->83 |
| electro_giant | 31% | 41% | x1.59 | hp 1102->1490; damage 78->92 |
| electro_spirit | 45% | 48% | x1.18 | hp 115->122; damage 58->65 |
| electro_wizard | 44% | 44% | x1.20 | hp 318->339; damage 62->70; spawn_damage 83->93 |
| elite_barbarians | 51% | 47% | x0.86 | hp 550->511; damage 176->163 |
| elixir_golem | 38% | 56% | x1.21 | hp 1201->1362; damage 128->137; sub_hp_mult 0.86->0.98; sub_dmg_mult 0.92->0.98 |
| executioner | 52% | 53% | x0.92 | hp 485->464; damage 76->73 |
| fire_spirit | 45% | 47% | x1.31 | hp 89->98; damage 174->207; death_damage 174->207 |
| firecracker | 47% | 50% | x1.12 | hp 154->160; damage 33->36 |
| flying_machine | 50% | 54% | x1.12 | hp 313->326; damage 76->82 |
| goblin_barrel | 47% | 57% | x1.05 | sub_hp_mult 1.37->1.41; sub_dmg_mult 1.37->1.41 |
| goblin_cage | 45% | 46% | x1.23 | hp 395->438; sub_hp_mult 1.00->1.11; sub_dmg_mult 1.00->1.11 |
| goblin_curse | 55% | 51% | x0.82 | spell_damage 18->15; tower_damage 5->4 |
| goblin_demolisher | 61% | 52% | x0.69 | hp 658->548; damage 94->78 |
| goblin_drill | 34% | 43% | x1.48 | hp 664->807; spawn_damage 43->52; sub_hp_mult 1.29->1.57; sub_dmg_mult 1.38->1.68 |
| goblin_gang | 63% | 55% | x0.70 | hp 88->73; damage 51->43; sub_hp_mult 1.29->1.08; sub_dmg_mult 1.38->1.15 |
| goblin_giant | 55% | 45% | x0.80 | hp 1957->1693; damage 91->84; sub_hp_mult 0.82->0.71; sub_dmg_mult 0.90->0.83 |
| goblin_machine | 56% | 50% | x0.80 | hp 1088->973; damage 107->96 |
| golden_knight | 57% | 56% | x0.82 | hp 845->766; damage 96->87 |
| golem | 67% | 57% | x0.66 | hp 3076->2358; damage 220->191; sub_hp_mult 0.73->0.56; sub_dmg_mult 0.85->0.74 |
| graveyard | 54% | 57% | x0.82 | sub_hp_mult 1.26->1.14; sub_dmg_mult 1.26->1.14 |
| guards | 53% | 56% | x0.89 | hp 38->37; shield_hp 175->168; damage 74->69 |
| heal_spirit | 43% | 43% | x1.46 | hp 109->124; damage 56->72; death_damage 56->72 |
| ice_golem | 50% | 50% | x0.89 | hp 1212->1127; damage 39->38 |
| ice_spirit | 43% | 44% | x1.35 | hp 86->96; damage 58->70; death_damage 58->70 |
| lava_hound | 61% | 52% | x0.74 | hp 2630->2157; damage 34->31; sub_hp_mult 0.88->0.72; sub_dmg_mult 0.93->0.84 |
| lightning | 54% | 56% | x0.90 | spell_damage 521->467; tower_damage 209->187 |
| lumberjack | 57% | 49% | x0.74 | hp 564->484; damage 139->119; sub_hp_mult 0.85->0.73; sub_dmg_mult 0.85->0.73 |
| mega_knight | 53% | 56% | x0.85 | hp 1493->1373; damage 115->106; spawn_damage 163->150; dash_damage 163->150 |
| mega_minion | 47% | 51% | x1.11 | hp 349->362; damage 139->149 |
| mighty_miner | 48% | 47% | x0.97 | hp 1033->1017 |
| miner | 55% | 51% | x0.84 | hp 988->906; damage 76->70 |
| mini_pekka | 50% | 47% | x0.84 | hp 587->539; damage 335->308 |
| minion_giant | 48% | 49% | x1.02 | hp 919->930; damage 96->97 |
| minion_horde | 40% | 50% | x1.53 | hp 81->100; damage 35->43 |
| minions | 42% | 45% | x1.27 | hp 95->103; damage 44->51 |
| mirror | 40% | 40% | x1.60 | (no stat fields) |
| monk | 49% | 54% | x0.89 | hp 942->889; damage 73->69 |
| mother_witch | 46% | 53% | x1.17 | hp 268->283; damage 67->74 |
| phoenix | 55% | 52% | x0.92 | hp 532->511; damage 110->106; sub_hp_mult 1.00->0.96; sub_dmg_mult 1.00->0.96 |
| poison | 52% | 49% | x0.89 | spell_damage 55->49; tower_damage 22->19 |
| prince | 51% | 48% | x0.90 | hp 783->743; damage 182->173 |
| princess | 50% | 47% | x0.88 | hp 107->102; damage 92->84 |
| ram_rider | 48% | 50% | x0.98 | hp 894->881; damage 126->125; sub_hp_mult 1.00->0.99; sub_dmg_mult 1.00->0.99 |
| rascals | 72% | 55% | x0.60 | hp 403->312; damage 79->61; sub_hp_mult 1.00->0.77; sub_dmg_mult 1.00->0.77 |
| ronin | 53% | 48% | x0.78 | hp 900->794; damage 188->166 |
| royal_ghost | 56% | 50% | x0.72 | hp 612->520; damage 132->112 |
| royal_giant | 54% | 48% | x0.83 | hp 2268->2002; damage 175->164 |
| royal_hogs | 43% | 49% | x1.25 | hp 424->490; damage 37->40 |
| royal_recruits | 69% | 50% | x0.49 | hp 277->195; shield_hp 121->85; damage 67->47 |
| rune_giant | 35% | 50% | x1.54 | hp 1347->1786; damage 60->70 |
| skeleton_army | 46% | 42% | x1.14 | hp 22->23; damage 22->24 |
| skeleton_barrel | 46% | 57% | x1.18 | hp 489->544; sub_hp_mult 1.57->1.75; sub_dmg_mult 1.28->1.36 |
| skeleton_dragons | 65% | 46% | x0.60 | hp 283->219; damage 82->63 |
| skeleton_king | 52% | 49% | x0.84 | hp 933->853; damage 110->101 |
| snowball | 47% | 48% | x1.09 | spell_damage 81->88; tower_damage 33->36 |
| spear_goblins | 42% | 54% | x1.28 | hp 51->56; damage 28->33 |
| spirit_empress | 62% | 46% | x0.58 | hp 567->432; damage 162->123 |
| spirit_empress_air | - | - | x0.58 | hp 910->693; damage 144->110 |
| tesla | 55% | 50% | x0.92 | hp 788->756; damage 121->116 |
| three_musketeers | 50% | 50% | x0.92 | hp 282->270; damage 92->88 |
| vines | 47% | 53% | x1.19 | spell_damage 77->92; tower_damage 20->24 |
| void | 46% | 46% | x1.08 | (no stat fields) |
| witch | 57% | 49% | x0.68 | hp 372->325; damage 67->52; sub_hp_mult 0.81->0.71; sub_dmg_mult 0.81->0.63 |
| xbow | 58% | 50% | x0.67 | hp 1440->1183; damage 35->29 |
