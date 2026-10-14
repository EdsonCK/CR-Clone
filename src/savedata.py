"""
============================================================================
  SAVEDATA.PY  --  Where your progress lives (so it survives updates)
============================================================================

Your saves - profile.json (gold, gems, card / King levels, unlocks...),
progress.json (Level stars), records.json, settings.json and your decks -
are kept in a folder OUTSIDE the game folder, so unzipping a new version
never loses them:

    Windows   %APPDATA%\\ClashClone
    macOS     ~/Library/Application Support/ClashClone
    Linux     ~/.local/share/clash-clone   (or $XDG_DATA_HOME/clash-clone)

Set the CLASH_CLONE_SAVE_DIR environment variable to use another folder.

The first time a version with this module runs and that folder has no
profile yet, it IMPORTS your old saves automatically: from this game's own
folder (versions before 1.4.4 saved next to the game), or else from the
newest "clash-clone-v*" folder sitting beside this one (e.g. the previous
version you unzipped into the same place). Settings shows the save folder
and can open it; copy that folder to back your progress up or move it to
another computer.
============================================================================
"""

import glob
import os
import shutil
import sys

GAME_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ("profile.json", "progress.json", "records.json", "settings.json",
         "player_deck.json", "ai_custom_deck.json", "level_deck.json")


def _default_dir():
    env = os.environ.get("CLASH_CLONE_SAVE_DIR")
    if env:
        return env
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "ClashClone")
    if sys.platform == "darwin":
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support",
                            "ClashClone")
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"),
                                                           ".local", "share")
    return os.path.join(base, "clash-clone")


SAVE_DIR = _default_dir()


def path(name):
    """Full path of save file `name` (the save folder is created on demand)."""
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
    except OSError:
        return os.path.join(GAME_DIR, name)       # read-only home: save beside the game
    return os.path.join(SAVE_DIR, name)


def _candidates():
    """Folders that may hold saves from an older version, best first."""
    out = [GAME_DIR]
    parent = os.path.dirname(GAME_DIR)
    others = [d for d in glob.glob(os.path.join(parent, "clash-clone*"))
              if os.path.isdir(d) and os.path.abspath(d) != os.path.abspath(GAME_DIR)]
    # the most recently played one first
    others.sort(key=lambda d: os.path.getmtime(os.path.join(d, "profile.json"))
                if os.path.exists(os.path.join(d, "profile.json")) else 0, reverse=True)
    return out + others


def migrate():
    """Copy old saves into the save folder if it has no profile yet.
    Returns the folder imported from, or None."""
    if os.path.exists(path("profile.json")):
        return None
    for d in _candidates():
        if os.path.exists(os.path.join(d, "profile.json")):
            for name in FILES:
                src = os.path.join(d, name)
                if os.path.exists(src):
                    try:
                        shutil.copy2(src, path(name))
                    except OSError:
                        pass
            return d
    return None


def open_folder():
    """Show the save folder in the system file browser."""
    d = os.path.dirname(path("profile.json"))
    try:
        if sys.platform.startswith("win"):
            os.startfile(d)                        # noqa: (Windows only)
        elif sys.platform == "darwin":
            os.system('open "%s"' % d)
        else:
            os.system('xdg-open "%s" >/dev/null 2>&1 &' % d)
        return True
    except Exception:
        return False
