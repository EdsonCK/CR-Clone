"""
============================================================================
  CARDDESC.PY  --  One-line "what does it do" for every card (Cards screen)
============================================================================
Short, mechanic-first descriptions. Edit freely; cards without an entry
fall back to an automatic summary built from their stats (describe()).
============================================================================
"""

import cards
import towers

DESC = {
    "skeletons": "Three fast, fragile skeletons. Cheap distraction and cycle.",
    "ice_spirit": "Leaps in and freezes a small area for a second, then it's gone.",
    "fire_spirit": "Leaps in and explodes in a splash of fire. Great vs swarms.",
    "goblins": "Three very fast stabbers. High damage for 2 elixir, die to any splash.",
    "spear_goblins": "Three ranged goblins that can hit air. Cheap chip support.",
    "bats": "Five tiny fliers that bite fast. Melt tanks, pop to any splash.",
    "skeleton_barrel": "A flying barrel heading for buildings; bursts into skeletons when popped.",
    "knight": "Sturdy, cheap melee tank. Solid on defence and behind a push.",
    "archers": "Two ranged archers that hit air and ground.",
    "bomber": "Lobs splash bombs at ground troops. Fragile, deletes swarms.",
    "valkyrie": "Spins her axe all around her: shreds swarms that surround her.",
    "mini_pekka": "Fast, fragile, huge single hits. Kills tanks and win conditions.",
    "musketeer": "Long-range sharpshooter that hits air and ground.",
    "barbarians": "Five tough melee brawlers. Surround tanks and chop them down.",
    "elite_barbarians": "Two fast, heavy hitters. Brutal if left alone, weak to swarms.",
    "wizard": "Throws splash fireballs at air and ground.",
    "witch": "Splash attacker who summons skeletons every few seconds.",
    "pekka": "Slow, armoured juggernaut with enormous single-target hits.",
    "prince": "Charges after a run-up for double damage on the first hit.",
    "dark_prince": "Shielded splash charger: clears small troops in his path.",
    "giant_skeleton": "Big tank that drops a giant bomb when he dies.",
    "lumberjack": "Very fast axeman; drops a Rage spell when he dies.",
    "bandit": "Dashes onto targets 3.5-6 tiles away for double damage, untouchable mid-dash.",
    "giant": "Massive tank that only attacks buildings.",
    "hog_rider": "Very fast building hunter that jumps the river.",
    "royal_giant": "Building-targeting giant that fires his cannon from long range.",
    "balloon": "Flying bomber that only targets buildings. Huge damage, drops a bomb on death.",
    "golem": "The heaviest tank; splits into two Golemites when destroyed.",
    "minions": "Three flying attackers with short range.",
    "minion_horde": "Six minions: a flying swarm that melts anything without splash.",
    "mega_minion": "Armoured flier with heavy hits. Strong air defender.",
    "baby_dragon": "Flying splash attacker. Tanky support for a push.",
    "inferno_dragon": "Flying beam that heats up the longer it burns one target.",
    "dart_goblin": "Fast-shooting, long-range goblin. Fragile.",
    "princess": "Splash archer with huge range: can hit towers from across the river.",
    "electro_wizard": "Zaps two targets per shot, stunning them; zaps the area he lands on.",
    "ice_wizard": "Splash shots that slow enemies; chills the area he lands on.",
    "three_musketeers": "Three Musketeers at once: massive ranged firepower, expensive.",
    "sparky": "Charges up a devastating splash blast every few seconds.",
    "cannon": "Cheap defensive building that shoots ground troops.",
    "tesla": "Defensive zapper that hits air and ground.",
    "inferno_tower": "Beam that ramps up to melt even the biggest tanks.",
    "bomb_tower": "Splash building vs ground; bomb blast when destroyed.",
    "mortar": "Long-range siege building that lobs shells at ground troops and towers.",
    "xbow": "Siege crossbow that can shoot enemy towers from your side of the river.",
    "tombstone": "Spawns skeletons over time and when destroyed. Pulls tanks.",
    "goblin_hut": "Spawns a Spear Goblin every few seconds.",
    "barbarian_hut": "Spawns Barbarians in groups over its lifetime.",
    "furnace": "Walking furnace that shoots and drops a Fire Spirit every 7s.",
    "elixir_collector": "Slowly pumps out extra elixir. Invest now, push later.",
    "zap": "Instant small-area damage and a short stun. Resets Infernos.",
    "the_log": "Rolls forward, damaging and knocking back ground troops.",
    "arrows": "A big rain of arrows that clears swarms.",
    "fireball": "Medium-area fireball with knockback.",
    "rage": "Boosts your troops' move and attack speed in the area.",
    "freeze": "Freezes everything in the area solid for a few seconds.",
    "poison": "Damage over time in a large area; slows enemies inside.",
    "rocket": "Slow, huge single-area damage. Finishes towers.",
    "lightning": "Strikes the 3 strongest targets in the area, with a stun.",
    "skeleton_army": "Fifteen skeletons: shreds single targets, dies to any splash.",
    "guards": "Three shielded skeletons: the shields soak a hit each.",
    "zappies": "Three slow-firing zappers whose shots stun.",
    "hunter": "Shotgun blast: devastating up close, weak at range.",
    "executioner": "Throws an axe that flies out and back, hitting everything on the line.",
    "bowler": "Rolls boulders that knock back everything in their path.",
    "magic_archer": "Piercing arrows that hit every enemy along a long line.",
    "night_witch": "Melee witch that summons bats; more bats when she dies.",
    "flying_machine": "Flying long-range shooter.",
    "electro_dragon": "Flying chain lightning that bounces between targets and stuns.",
    "lava_hound": "Flying tank that targets buildings and bursts into Lava Pups.",
    "mega_knight": "Jumps onto groups and slams them; lands with splash damage.",
    "goblin_giant": "Building-targeting giant with two Spear Goblins on his back.",
    "cannon_cart": "Mobile shielded cannon.",
    "ice_golem": "Cheap tank that targets buildings; chilly death blast slows.",
    "miner": "Tunnels anywhere on the map and pops up to chip.",
    "battle_ram": "Charging ram aimed at buildings; drops two Barbarians.",
    "wall_breakers": "Two explosive skeletons that blow up on buildings.",
    "electro_spirit": "Leaps in and its zap chains between targets, stunning them.",
    "electro_giant": "Building-targeting giant: anything that hits him nearby gets zapped.",
    "battle_healer": "Melee fighter who heals nearby allies with every swing.",
    "elixir_golem": "Cheap splitting tank; the opponent gets elixir for killing the pieces.",
    "goblin_barrel": "Throw three Goblins anywhere - straight onto a tower.",
    "barbarian_barrel": "A rolling barrel that damages, knocks back and drops a Barbarian.",
    "snowball": "Small-area damage, knockback and slow.",
    "earthquake": "Damage over time that crushes buildings.",
    "tornado": "Drags enemies to its centre while damaging them.",
    "graveyard": "Skeletons keep rising in the area for several seconds.",
    "mighty_miner": "CHAMPION: drill ramps up damage; ability burrows to the other lane leaving a bomb.",
    "archer_queen": "CHAMPION: long-range shots; ability cloaks her and doubles her attack speed.",
    "little_prince": "CHAMPION: shoots faster and faster; ability sends in his Guardian.",
    "golden_knight": "CHAMPION: ability chain-dashes through up to 10 enemies.",
    "skeleton_king": "CHAMPION: splash tank; ability raises skeletons from collected souls.",
    "monk": "CHAMPION: 3-hit combos; ability reduces damage and deflects projectiles.",
    "goblinstein": "CHAMPION: the Doctor and his Monster; ability links them with lightning.",
    "boss_bandit": "CHAMPION: dashes like the Bandit; ability teleports her back to dash again.",
    "berserker": "Two-elixir blur of axes that attacks every 0.6s.",
    "firecracker": "Her firework bursts into 5 sparks behind the target; she hops back after each shot.",
    "goblin_gang": "Three Goblins up front and three Spear Goblins behind.",
    "skeleton_dragons": "Two flying bone dragons that spit splash fire.",
    "rascals": "A tanky Rascal Boy with two slingshot Rascal Girls.",
    "royal_recruits": "Six shielded spearmen deployed in a long line across the arena.",
    "royal_delivery": "Your side only: a crate lands after 3s, damaging the area, and a Royal Recruit steps out.",
    "heal_spirit": "Leaps in, damages, and heals your troops around the blast.",
    "suspicious_bush": "Troops can't target it. At the first building it bursts into 2 Bush Goblins.",
    "goblin_cage": "When the cage is destroyed (or expires) the Goblin Brawler breaks out.",
    "goblin_demolisher": "Throws bombs; below half health he lights his fuse and runs at a building.",
    "minion_giant": "Flying, building-targeting giant minion that spits toxin from range.",
    "royal_hogs": "Four building-hunting hogs in a row that jump the river.",
    "mirror": "Replays your last card one level higher, for its cost +1.",
    "goblin_curse": "Damage over time; enemies that die in it come back as YOUR Goblins.",
    "clone": "Copies your troops in the area as 1-HP clones.",
    "vines": "Roots the 3 highest-hp enemies (fliers are pulled down) and damages them.",
    "goblin_drill": "Tunnels anywhere, surfaces with a blast and spawns Goblins until destroyed.",
    "rune_giant": "Building-targeting giant who enchants the 2 nearest allies: every 3rd hit deals bonus damage.",
    "void": "Three strikes in the area; each hits harder the FEWER enemies are inside.",
    "fisherman": "Throws his anchor: drags ground troops to him (or himself to buildings) and slows them.",
    "royal_ghost": "Invisible until he swings; hovers over the river.",
    "mother_witch": "Curses what she hits: cursed troops that die become Cursed Hogs for her side.",
    "phoenix": "Fiery flier; when it falls it explodes and leaves an egg that hatches a new Phoenix.",
    "goblin_machine": "Mech that punches up close and fires rockets at enemies 2.5-5 tiles away.",
    "ram_rider": "Charging ram aimed at buildings; the rider's bolas snare troops (-70% speed).",
    "ronin": "Every 3.5s he parries a melee hit and strikes back for double damage.",
    "spirit_empress": "3 elixir on foot, or 6 elixir riding her flying spirit dragon if you can afford it.",
}

TOWER_DESC = {k: t.desc for k, t in towers.TOWER_TROOPS.items()}


def describe(key):
    """A one-line description for any card key."""
    if key in DESC:
        return DESC[key]
    if key in TOWER_DESC:
        return TOWER_DESC[key]
    c = cards.CARDS.get(key)
    if c is None:
        return ""
    if c.category == "spell":
        return "Spell."
    bits = []
    if c.flying:
        bits.append("flying")
    bits.append({"buildings": "building-targeting", "air_ground": "hits air & ground",
                 "ground": "ground-only"}[c.attacks])
    if c.splash:
        bits.append("splash")
    return (c.category.title() + ": " + ", ".join(bits) + ".")
