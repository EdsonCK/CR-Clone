"""
============================================================================
  SOURCES.PY  --  The public-domain (CC0) recordings the SFX are built from
============================================================================

Every pack listed here is CC0 ("No Rights Reserved" - public domain):
free to use, change and redistribute, no credit required. We credit the
authors anyway, in assets/sounds/CREDITS.txt (written by render.py).

The packs are NOT stored in the repository (they're ~800 MB). To rebuild
the sounds:   python tools/sfx/render.py --fetch
downloads them once into tools/sfx/_cache (or $SFX_CACHE).

PACKS: key -> (title, author, [download urls]). OpenGameArt pages live at
https://opengameart.org/content/<key>; Kenney's at https://kenney.nl/assets/<name>.
============================================================================
"""

import glob
import os
import urllib.parse
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get("SFX_CACHE") or os.path.join(HERE, "_cache")
AUDIO = (".wav", ".ogg", ".mp3", ".flac")

PACKS = {
    "kenney/impact-sounds": ("Impact Sounds", "Kenney", ["kenney:impact-sounds"]),
    "kenney/rpg-audio": ("RPG Audio", "Kenney", ["kenney:rpg-audio"]),
    "kenney/sci-fi-sounds": ("Sci-fi Sounds", "Kenney", ["kenney:sci-fi-sounds"]),
    "rpg-sound-pack": ("RPG Sound Pack", "artisticdude", [
        "https://opengameart.org/sites/default/files/rpg_sound_pack.zip",
    ]),
    "3-melee-sounds": ("3 Melee sounds", "remaxim", [
        "https://opengameart.org/sites/default/files/melee%20sounds.zip",
        "https://opengameart.org/sites/default/files/ms.mp3",
    ]),
    "swishes-sound-pack": ("Swishes Sound Pack", "artisticdude", [
        "https://opengameart.org/sites/default/files/swishes.zip",
    ]),
    "20-sword-sound-effects-attacks-and-clashes": ("20 Sword Sound Effects (Attacks and Clashes)", "StarNinjas", [
        "https://opengameart.org/sites/default/files/sword_-_starninjas_1.zip",
        "https://opengameart.org/sites/default/files/sword_clash_-_starninjas_0.zip",
    ]),
    "fantasy-weapons-and-apparel-sfx-library": ("Fantasy Weapons and Apparel SFX Library", "Vehicle", [
        "https://opengameart.org/sites/default/files/weapons-apparel.zip",
    ]),
    "medieval-sound-effects-weapon-impacts": ("Medieval sound effects - Weapon impacts", "Ben Jaszczak & Brian Nelson", [
        "https://opengameart.org/sites/default/files/medieval-weapons-impacts.ogg",
        "https://opengameart.org/sites/default/files/medieval_sfx_weapon_on_weapon_1_of_2.7z",
        "https://opengameart.org/sites/default/files/medieval_sfx_weapon_on_weapon_2_of_2.7z",
    ]),
    "battle-sound-effects": ("Battle Sound Effects", "artisticdude", [
        "https://opengameart.org/sites/default/files/battle_sound_effects_0.zip",
    ]),
    "the-free-firearm-sound-library": ("The Free Firearm Sound Library", "Ben Jaszczak et al.", [
        "https://opengameart.org/sites/default/files/Prepared%20SFX%20Library.7z",
        "https://opengameart.org/sites/default/files/ak47.ogg",
    ]),
    "gunshots": ("Gunshots", "kurt", [
        "https://opengameart.org/sites/default/files/22%20Magnum.wav",
        "https://opengameart.org/sites/default/files/22%20Pistol.wav",
        "https://opengameart.org/sites/default/files/Black%20Powder.wav",
        "https://opengameart.org/sites/default/files/Unkown.wav",
    ]),
    "25-cc0-bang-firework-sfx": ("25 CC0 bang / firework SFX", "rubberduck", [
        "https://opengameart.org/sites/default/files/25-CC0-bang-sfx.zip",
    ]),
    "80-cc0-rpg-sfx": ("80 CC0 RPG SFX", "rubberduck", [
        "https://opengameart.org/sites/default/files/80-CC0-RPG-SFX_0.zip",
    ]),
    "80-cc0-creature-sfx": ("80 CC0 creature SFX", "rubberduck", [
        "https://opengameart.org/sites/default/files/80-CC0-creature-SFX_0.zip",
    ]),
    "80-cc0-creture-sfx-2": ("80 CC0 creture SFX #2", "rubberduck", [
        "https://opengameart.org/sites/default/files/80-CC0-creature-sfx-2.zip",
    ]),
    "monster-sound-effects-pack": ("Monster Sound Effects Pack", "Ogrebane", [
        "https://opengameart.org/sites/default/files/monster1.mp3",
        "https://opengameart.org/sites/default/files/monster_sfx_pack.zip",
    ]),
    "big-scary-troll-sounds": ("Big scary troll sounds", "Darsycho", [
        "https://opengameart.org/sites/default/files/scrapped-troll-sounds.ogg",
        "https://opengameart.org/sites/default/files/troll-idle-noises.ogg",
        "https://opengameart.org/sites/default/files/troll-idle-noises_0.ogg",
        "https://opengameart.org/sites/default/files/troll-roars.ogg",
        "https://opengameart.org/sites/default/files/troll-roars_0.ogg",
    ]),
    "magic-spell-sfx": ("Magic Spell SFX", "JaggedStone", [
        "https://opengameart.org/sites/default/files/magical_1.ogg",
        "https://opengameart.org/sites/default/files/magical_1_0.ogg",
        "https://opengameart.org/sites/default/files/magical_2.ogg",
        "https://opengameart.org/sites/default/files/magical_2_1.ogg",
        "https://opengameart.org/sites/default/files/magical_3.ogg",
        "https://opengameart.org/sites/default/files/magical_3_1.ogg",
        "https://opengameart.org/sites/default/files/magical_4.ogg",
        "https://opengameart.org/sites/default/files/magical_4_1.ogg",
        "https://opengameart.org/sites/default/files/magical_5.ogg",
        "https://opengameart.org/sites/default/files/magical_5_1.ogg",
        "https://opengameart.org/sites/default/files/magical_6.ogg",
        "https://opengameart.org/sites/default/files/magical_6_0.ogg",
        "https://opengameart.org/sites/default/files/magical_7.ogg",
        "https://opengameart.org/sites/default/files/magical_7_0.ogg",
    ]),
    "freeze-spell-0": ("Freeze Spell", "artisticdude", [
        "https://opengameart.org/sites/default/files/freeze.wav",
    ]),
    "fire-crackling": ("Fire Crackling", "AntumDeluge", [
        "https://opengameart.org/sites/default/files/fire-1.ogg",
        "https://opengameart.org/sites/default/files/fire-1.wav",
        "https://opengameart.org/sites/default/files/fire-1_0.ogg",
    ]),
    "catching-fire": ("Catching fire", "themightyglider", [
        "https://opengameart.org/sites/default/files/flame.ogg",
        "https://opengameart.org/sites/default/files/flame_0.ogg",
    ]),
    "100-cc0-sfx": ("100 CC0 SFX", "rubberduck", [
        "https://opengameart.org/sites/default/files/100-CC0-SFX_0.zip",
    ]),
    "37-hitspunches": ("37 hits/punches", "Independent.nu", [
        "https://opengameart.org/sites/default/files/hit.mp3",
        "https://opengameart.org/sites/default/files/independent_nu_ljudbank-hits_and_punches.7z",
    ]),
    "10-impactshield-blocks": ("10 Impact/Shield Blocks", "StarNinjas", [
        "https://opengameart.org/sites/default/files/impact_-_starninjas.zip",
    ]),
    "medieval-sound-effects-weapon-textures": ("Medieval sound effects - Weapon Textures", "Ben Jaszczak & Brian Nelson", [
        "https://opengameart.org/sites/default/files/medieval-weapons-textures.ogg",
        "https://opengameart.org/sites/default/files/medieval_sfx_textures_1_of_2.7z",
        "https://opengameart.org/sites/default/files/medieval_sfx_textures_2_of_2.7z",
    ]),
    "fantasy-sound-effects-tinysized-sfx": ("Fantasy Sound Effects (Tinysized SFX)", "Vehicle", [
        "https://opengameart.org/sites/default/files/tinysized.zip",
    ]),
    "50-cc0-sci-fi-sfx": ("50 CC0 Sci-Fi SFX", "rubberduck", [
        "https://opengameart.org/sites/default/files/sci-fi-sfx.zip",
    ]),
    "metal-interactions": ("Metal Interactions", "qubodup", [
        "https://opengameart.org/sites/default/files/metal_interactions.7z",
    ]),
    "air-whoosh": ("Air whoosh", "pyranostudios", [
        "https://opengameart.org/sites/default/files/whoosh2_0.wav",
    ]),
    "energy-drain": ("Energy Drain", "qubodup", [
        "https://opengameart.org/sites/default/files/qubodup-PowerDrain.7z",
        "https://opengameart.org/sites/default/files/qubodup-PowerDrain.ogg",
    ]),
    "tiny-vicious-creature": ("Tiny vicious creature", "Darsycho", [
        "https://opengameart.org/sites/default/files/tiny-vicious-creature.ogg",
        "https://opengameart.org/sites/default/files/tiny-vicious-creature_0.ogg",
    ]),
    "monster-sound-pack-volume-1": ("Monster Sound Pack, Volume 1", "Ogrebane", [
        "https://opengameart.org/sites/default/files/mon.mp3",
        "https://opengameart.org/sites/default/files/monster-sounds-volume-2.zip",
    ]),
    "monster-sound-effects-2": ("Monster Sound Effects 2", "Ogrebane", [
        "https://opengameart.org/sites/default/files/monster2.mp3",
        "https://opengameart.org/sites/default/files/monster_sfx_pack_2.zip",
    ]),
    "ghost-monster-voice-moaning-growling": ("Ghost Monster Voice Moaning & Growling", "qubodup", [
        "https://opengameart.org/sites/default/files/qubodup-GhostMoans.zip",
    ]),
    "spell-sounds": ("Spell sounds", "Augmentality (Brandon Morris)", [
        "https://opengameart.org/sites/default/files/electricspell.ogg",
        "https://opengameart.org/sites/default/files/electricspell2.ogg",
        "https://opengameart.org/sites/default/files/healing.ogg",
        "https://opengameart.org/sites/default/files/teleport.ogg",
    ]),
    "electricity-game-sound-pack": ("Electricity Game Sound Pack", "faxcorp", [
        "https://opengameart.org/sites/default/files/charge.wav",
        "https://opengameart.org/sites/default/files/chargestart.wav",
        "https://opengameart.org/sites/default/files/crackleelectricityloop.wav",
        "https://opengameart.org/sites/default/files/death_1.wav",
        "https://opengameart.org/sites/default/files/deathboom.wav",
        "https://opengameart.org/sites/default/files/groundhit.wav",
        "https://opengameart.org/sites/default/files/hit.wav",
        "https://opengameart.org/sites/default/files/killconfirmed.wav",
        "https://opengameart.org/sites/default/files/powerdown.wav",
        "https://opengameart.org/sites/default/files/powerup.wav",
        "https://opengameart.org/sites/default/files/recharge.wav",
        "https://opengameart.org/sites/default/files/shieldhit.wav",
        "https://opengameart.org/sites/default/files/shieldloop.wav",
        "https://opengameart.org/sites/default/files/snaploop.wav",
        "https://opengameart.org/sites/default/files/teleport_1.wav",
        "https://opengameart.org/sites/default/files/turbo.wav",
    ]),
    "electric-buzz": ("Electric Buzz", "themightyglider", [
        "https://opengameart.org/sites/default/files/buzz.ogg",
        "https://opengameart.org/sites/default/files/buzz_0.ogg",
    ]),
    "electricity-sound-effects-0": ("Electricity Sound Effects", "BMacZero", [
        "https://opengameart.org/sites/default/files/continuousspark.wav",
        "https://opengameart.org/sites/default/files/spark.wav",
    ]),
    "fireball-1": ("Fireball", "Julien Matthey", [
        "https://opengameart.org/sites/default/files/105016_1535323-lq.ogg",
        "https://opengameart.org/sites/default/files/105016__julien-matthey__jm-fx-fireball-01.wav",
    ]),
    "ice-spells": ("Ice spells", "bart", [
        "https://opengameart.org/sites/default/files/ices.mp3",
        "https://opengameart.org/sites/default/files/icespells.zip",
    ]),
    "dragon-flap-0": ("Dragon Flap", "VishwaJai", [
        "https://opengameart.org/sites/default/files/dragonflap.mp3",
        "https://opengameart.org/sites/default/files/dragonflap.wav",
        "https://opengameart.org/sites/default/files/dragonflap_0.mp3",
    ]),
    "bones-rattle": ("Bones rattle", "congusbongus", [
        "https://opengameart.org/sites/default/files/bones_rattle.zip",
    ]),
    "bones-2": ("Bones 2", "AntumDeluge", [
        "https://opengameart.org/sites/default/files/bones-2.ogg",
        "https://opengameart.org/sites/default/files/bones-2.wav",
        "https://opengameart.org/sites/default/files/bones-2_0.ogg",
    ]),
    "skeletonsfxshortpack": ("SkeletonSFXShortPack", "Colodical", [
        "https://opengameart.org/sites/default/files/skeleton1sfx_0.wav",
        "https://opengameart.org/sites/default/files/skeleton2sfx_0.wav",
    ]),
    "zombie-skeleton-monster-voice-effects": ("Zombie / Skeleton / Monster Voice Effects", "ArcadeParty", [
        "https://opengameart.org/sites/default/files/Voice%20Effects%20Zombie-Skeleton-Monster%20Human%20Male.zip",
    ]),
    "100-cc0-metal-and-wood-sfx": ("100 CC0 metal and wood SFX", "rubberduck", [
        "https://opengameart.org/sites/default/files/100-CC0-wood-metal-SFX.zip",
    ]),
    "metal-impact-sounds": ("Metal Impact Sounds", "BMacZero", [
        "https://opengameart.org/sites/default/files/bing1.wav",
        "https://opengameart.org/sites/default/files/bong1.wav",
        "https://opengameart.org/sites/default/files/clink1_0.wav",
        "https://opengameart.org/sites/default/files/clink2.wav",
        "https://opengameart.org/sites/default/files/clink3.wav",
        "https://opengameart.org/sites/default/files/thud2.wav",
        "https://opengameart.org/sites/default/files/thud3.wav",
    ]),
    "goblins-sound-pack": ("Goblins Sound Pack", "artisticdude", [
        "https://opengameart.org/sites/default/files/goblins_0.zip",
    ]),
    "8-wet-squish-slurp-impacts": ("8 wet squish, slurp impacts", "Independent.nu", [
        "https://opengameart.org/sites/default/files/im.mp3",
        "https://opengameart.org/sites/default/files/independent_nu_ljudbank-wet_squish_slurp_impacts.7z",
    ]),
    "63-digital-sound-effects-lasers-phasers-space-etc": ("63 Digital sound effects (lasers, phasers, space etc.)", "Kenney", [
        "https://opengameart.org/sites/default/files/Digital_SFX_Set.zip",
    ]),
    "7-ghast-sounds": ("7 Ghast Sounds", "StarNinjas", [
        "https://opengameart.org/sites/default/files/ghast_-_starninjas.zip",
    ]),
    "female-rpg-voice-starter-pack": ("Female RPG Voice Starter Pack", "cicifyre", [
        "https://opengameart.org/sites/default/files/RPG%20Voice%20Starter%20Pack.zip",
    ]),
    "female-hurt-grunts-groans": ("Female Hurt Grunts & Groans", "Nocturnal_Vanguard", [
        "https://opengameart.org/sites/default/files/female_hurt_grunts_groans_1.ogg",
        "https://opengameart.org/sites/default/files/female_hurt_grunts_groans_1_0.ogg",
    ]),
    "male-gruntyelling-sounds": ("Male Grunt/Yelling sounds", "HaelDB", [
        "https://opengameart.org/sites/default/files/yelling%20sounds.zip",
    ]),
    "5-hit-sounds-dying": ("5 Hit Sounds + Dying", "TinyWorlds", [
        "https://opengameart.org/sites/default/files/5Hit_Sounds.zip",
    ]),
    "witch-cackle": ("Witch Cackle", "AntumDeluge", [
        "https://opengameart.org/sites/default/files/witch_cackle-1.ogg",
        "https://opengameart.org/sites/default/files/witch_cackle-1_0.ogg",
    ]),
    "group-giggling": ("Group giggling", "Nocturnal_Vanguard", [
        "https://opengameart.org/sites/default/files/group_giggling.ogg",
        "https://opengameart.org/sites/default/files/group_giggling_0.ogg",
    ]),
    "evil-laugh": ("Evil Laugh", "AntumDeluge", [
        "https://opengameart.org/sites/default/files/laugh-evil-1.ogg",
        "https://opengameart.org/sites/default/files/laugh-evil-1_0.ogg",
    ]),
    "15-vocal-male-strainhurtpainjump-sounds": ("15 vocal male strain/hurt/pain/jump sounds", "qubodup", [
        "https://opengameart.org/sites/default/files/slightscreams.7z",
        "https://opengameart.org/sites/default/files/sls.mp3",
    ]),
    "grunts-male-death-and-pain": ("grunts of male death and pain", "thebardofblasphemy", [
        "https://opengameart.org/sites/default/files/death%20pain%20grunts.wav",
    ]),
    "hurt-death-sound-effect-for-character": ("Hurt / Death sound effect for character", "Badre-Eddine", [
        "https://opengameart.org/sites/default/files/10.mp3",
        "https://opengameart.org/sites/default/files/11.mp3",
        "https://opengameart.org/sites/default/files/1_8.mp3",
        "https://opengameart.org/sites/default/files/2_3.mp3",
        "https://opengameart.org/sites/default/files/3_2.mp3",
        "https://opengameart.org/sites/default/files/4_1.mp3",
        "https://opengameart.org/sites/default/files/5_1.mp3",
        "https://opengameart.org/sites/default/files/6_1.mp3",
        "https://opengameart.org/sites/default/files/7.mp3",
        "https://opengameart.org/sites/default/files/8.mp3",
        "https://opengameart.org/sites/default/files/9.mp3",
        "https://opengameart.org/sites/default/files/death%20sound%20effect.zip",
    ]),
    "tiny-creatures-sounds": ("Tiny creatures sounds", "fvcalderan", [
        "https://opengameart.org/sites/default/files/battlecry0.ogg",
        "https://opengameart.org/sites/default/files/battlecry1.ogg",
        "https://opengameart.org/sites/default/files/battlecry2.ogg",
        "https://opengameart.org/sites/default/files/laugh.ogg",
    ]),
    "evil-screech-1": ("Evil Screech 1", "Nocturnal_Vanguard", [
        "https://opengameart.org/sites/default/files/evil_screech_1.ogg",
        "https://opengameart.org/sites/default/files/evil_screech_1_0.ogg",
    ]),
    "osare-minotaur-sounds": ("Osare Minotaur Sounds", "Augmentality (Brandon Morris)", [
        "https://opengameart.org/sites/default/files/mino1.wav",
    ]),
}


def page(key):
    if key.startswith("kenney/"):
        return "https://kenney.nl/assets/" + key.split("/", 1)[1]
    return "https://opengameart.org/content/" + key


def pack_dir(key):
    if key.startswith("kenney/"):
        return os.path.join(CACHE, "kenney", key.split("/", 1)[1])
    return os.path.join(CACHE, "oga", key)


_INDEX = {}


def _index(key):
    if key not in _INDEX:
        files = {}
        for p in glob.glob(os.path.join(pack_dir(key), "**", "*"), recursive=True):
            if p.lower().endswith(AUDIO) and "__MACOSX" not in p:
                files.setdefault(os.path.basename(p).lower(), p)
        _INDEX[key] = files
    return _INDEX[key]


def find(key, name):
    """Path of file `name` (case-insensitive basename) in pack `key`."""
    files = _index(key)
    p = files.get(name.lower())
    if p is None:
        raise FileNotFoundError("%s: %s (run render.py --fetch)" % (key, name))
    return p


def listing(key):
    return sorted(_index(key))


# ---------------------------------------------------------------- download
def _get(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "clash-clone-sfx/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        while True:
            b = r.read(1 << 16)
            if not b:
                break
            f.write(b)


def _kenney_zip(name):
    html = urllib.request.urlopen(urllib.request.Request(
        "https://kenney.nl/assets/" + name, headers={"User-Agent": "Mozilla/5.0"}),
        timeout=60).read().decode("utf8", "replace")
    import re
    m = re.search(r"https://kenney\.nl/media/pages/assets/[^\"]*\.zip", html)
    if not m:
        raise RuntimeError("no download link on kenney.nl/assets/" + name)
    return m.group(0)


def _extract(path):
    d = os.path.dirname(path)
    base = os.path.basename(path)
    if path.endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            z.extractall(os.path.join(d, "x_" + base[:-4]))
    elif path.endswith(".7z"):
        import py7zr                                  # pip install py7zr
        with py7zr.SevenZipFile(path) as z:
            z.extractall(os.path.join(d, "x7_" + base[:-3]))


def fetch(only=None, log=print):
    """Download + unpack every pack that isn't in the cache yet."""
    for key, (title, author, urls) in PACKS.items():
        if only and key not in only:
            continue
        d = pack_dir(key)
        if os.path.isdir(d) and os.listdir(d):
            continue
        os.makedirs(d, exist_ok=True)
        log("fetching %s (%s)" % (title, author))
        for u in urls:
            if u.startswith("kenney:"):
                u = _kenney_zip(u.split(":", 1)[1])
                dest = os.path.join(d, "pack.zip")
                _get(u, dest)
                with zipfile.ZipFile(dest) as z:
                    z.extractall(d)
                continue
            name = urllib.parse.unquote(os.path.basename(u))
            dest = os.path.join(d, name)
            _get(u, dest)
            _extract(dest)
        _INDEX.pop(key, None)
